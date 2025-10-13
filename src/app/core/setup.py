from collections.abc import AsyncGenerator, Callable
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Any

import anyio
import fastapi
from fastapi.routing import APIRoute
import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from ..api.dependencies import get_current_superuser
from ..core.utils.rate_limit import rate_limiter
from ..middleware.client_cache_middleware import ClientCacheMiddleware
from ..models import *  # noqa: F403
from .config import (
    AppSettings,
    ClientSideCacheSettings,
    CORSSettings,
    DatabaseSettings,
    EnvironmentOption,
    EnvironmentSettings,
    RedisCacheSettings,
    RedisQueueSettings,
    RedisRateLimiterSettings,
    settings,
)
from .db.database import Base
from .db.database import async_engine as engine
from .db.database import local_session
from .utils import cache, queue

from ..core.permissions import permission_root, flatten_permissions, PermissionNames


# -------------- database --------------
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# -------------- cache --------------
async def create_redis_cache_pool() -> None:
    cache.pool = redis.ConnectionPool.from_url(settings.REDIS_CACHE_URL)
    cache.client = redis.Redis.from_pool(cache.pool)  # type: ignore


async def close_redis_cache_pool() -> None:
    if cache.client is not None:
        await cache.client.aclose()  # type: ignore


# -------------- queue --------------
async def create_redis_queue_pool() -> None:
    queue.pool = await create_pool(RedisSettings(host=settings.REDIS_QUEUE_HOST, port=settings.REDIS_QUEUE_PORT))


async def close_redis_queue_pool() -> None:
    if queue.pool is not None:
        await queue.pool.aclose()  # type: ignore


# -------------- rate limit --------------
async def create_redis_rate_limit_pool() -> None:
    rate_limiter.initialize(settings.REDIS_RATE_LIMIT_URL)  # type: ignore


async def close_redis_rate_limit_pool() -> None:
    if rate_limiter.client is not None:
        await rate_limiter.client.aclose()  # type: ignore


def custom_generate_unique_id(route: APIRoute) -> str:
    """
    格式：{tag}_{function_name}
    """
    
    # 1. 获取 Tag（主资源）
    tag = route.tags[0] if route.tags else "default"
    
    # 2. 获取函数名（操作动词 + 子资源）
    function_name = route.name
    
    # 3. 组合并清理
    operation_id = f"{tag}_{function_name}".lower().replace('-', '_').replace(' ', '_')
    
    return operation_id

# -------------- application --------------
async def set_threadpool_tokens(number_of_tokens: int = 100) -> None:
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = number_of_tokens


def lifespan_factory(
    settings: (
        DatabaseSettings
        | RedisCacheSettings
        | AppSettings
        | ClientSideCacheSettings
        | RedisQueueSettings
        | RedisRateLimiterSettings
        | EnvironmentSettings
    ),
    create_tables_on_start: bool = True,
) -> Callable[[FastAPI], _AsyncGeneratorContextManager[Any]]:
    """Factory to create a lifespan async context manager for a FastAPI app."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        from asyncio import Event

        initialization_complete = Event()
        app.state.initialization_complete = initialization_complete

        await set_threadpool_tokens()

        try:
            if isinstance(settings, RedisCacheSettings):
                await create_redis_cache_pool()

            if isinstance(settings, RedisQueueSettings):
                await create_redis_queue_pool()

            if isinstance(settings, RedisRateLimiterSettings):
                await create_redis_rate_limit_pool()

            if create_tables_on_start:
                await create_tables()

            initialization_complete.set()

            yield

        finally:
            if isinstance(settings, RedisCacheSettings):
                await close_redis_cache_pool()

            if isinstance(settings, RedisQueueSettings):
                await close_redis_queue_pool()

            if isinstance(settings, RedisRateLimiterSettings):
                await close_redis_rate_limit_pool()

    return lifespan


# -------------- application --------------
async def seed_initial_rbac() -> None:
    async with local_session() as db:
        # Create default roles if not exist
        from ..models.role import Role
        from ..models.permission import Permission
        from ..models.user import User
        from ..models.user_role import UserRole
        from ..core.permissions import PermissionNames
        
        # Ensure an admin role exists
        admin_role = await db.execute(
            """SELECT * FROM role WHERE name = 'admin' AND is_active = true LIMIT 1"""
        )
        admin = admin_role.scalar_one_or_none()
        
        if admin is None:
            # Insert admin role
            await db.execute(
                """
                INSERT INTO role (name, description, is_active, created_at, updated_at)
                VALUES ('admin', 'System Administrator', true, now(), now())
                """
            )
            await db.commit()
            admin_role = await db.execute(
                """SELECT * FROM role WHERE name = 'admin' LIMIT 1"""
            )
            admin = admin_role.scalar_one()
        
        # Grant permissions to admin role (id fetched from row)
        # Using ORM bulk operations for clarity
        admin_id = admin.id if hasattr(admin, 'id') else admin[0]
        existing_perms = await db.execute(
            """SELECT permission_name FROM permission WHERE role_id = :role_id""",
            {"role_id": admin_id},
        )
        existing = {row[0] for row in existing_perms.all()}
        needed = [
            PermissionNames.USER_MANAGE,
            PermissionNames.USER_READ,
            PermissionNames.USER_CREATE,
            PermissionNames.USER_UPDATE,
            PermissionNames.USER_DELETE,
            PermissionNames.ROLE_MANAGE,
            PermissionNames.ROLE_READ,
            PermissionNames.ROLE_CREATE,
            PermissionNames.ROLE_UPDATE,
            # Removed ROLE_ASSIGN and ROLE_REVOKE
            PermissionNames.ROOT,
            # ensure delete role permission seeded
            getattr(PermissionNames, 'ROLE_DELETE', PermissionNames.ROLE_UPDATE),
        ]
        to_create = [
            Permission(permission_name=perm, role_id=admin_id) for perm in needed if perm not in existing
        ]
        if to_create:
            db.add_all(to_create)
            await db.commit()
        
        # Optionally assign admin role to superusers
        superusers = await db.execute(
            """SELECT id FROM "user" WHERE is_superuser = true"""
        )
        su_ids = [row[0] for row in superusers.all()]
        if su_ids:
            # Fetch existing links to avoid duplicates
            existing_links = await db.execute(
                """SELECT user_id FROM user_role WHERE role_id = :role_id AND user_id = ANY(:uids)""",
                {"role_id": admin_id, "uids": su_ids},
            )
            existing_user_ids = {row[0] for row in existing_links.all()}
            new_links = [UserRole(user_id=uid, role_id=admin_id) for uid in su_ids if uid not in existing_user_ids]
            if new_links:
                db.add_all(new_links)
                await db.commit()

def create_application(
    router: APIRouter,
    settings: (
        DatabaseSettings
        | RedisCacheSettings
        | AppSettings
        | ClientSideCacheSettings
        | RedisQueueSettings
        | RedisRateLimiterSettings
        | EnvironmentSettings
        | CORSSettings
    ),
    create_tables_on_start: bool = True,
    lifespan: Callable[[FastAPI], _AsyncGeneratorContextManager[Any]] | None = None,
    **kwargs: Any,
) -> FastAPI:
    """Creates and configures a FastAPI application based on the provided settings.

    This function initializes a FastAPI application and configures it with various settings
    and handlers based on the type of the `settings` object provided.

    Parameters
    ----------
    router : APIRouter
        The APIRouter object containing the routes to be included in the FastAPI application.

    settings
        An instance representing the settings for configuring the FastAPI application.
        It determines the configuration applied:

        - AppSettings: Configures basic app metadata like name, description, contact, and license info.
        - DatabaseSettings: Adds event handlers for initializing database tables during startup.
        - RedisCacheSettings: Sets up event handlers for creating and closing a Redis cache pool.
        - ClientSideCacheSettings: Integrates middleware for client-side caching.
        - RedisQueueSettings: Sets up event handlers for creating and closing a Redis queue pool.
        - RedisRateLimiterSettings: Sets up event handlers for creating and closing a Redis rate limiter pool.
        - EnvironmentSettings: Conditionally sets documentation URLs and integrates custom routes for API documentation
          based on the environment type.

    create_tables_on_start : bool
        A flag to indicate whether to create database tables on application startup.
        Defaults to True.

    **kwargs
        Additional keyword arguments passed directly to the FastAPI constructor.

    Returns
    -------
    FastAPI
        A fully configured FastAPI application instance.

    The function configures the FastAPI application with different features and behaviors
    based on the provided settings. It includes setting up database connections, Redis pools
    for caching, queue, and rate limiting, client-side caching, and customizing the API documentation
    based on the environment settings.
    """
    # --- before creating application ---
    if isinstance(settings, AppSettings):
        to_update = {
            "title": settings.APP_NAME,
            "description": settings.APP_DESCRIPTION,
            "contact": {"name": settings.CONTACT_NAME, "email": settings.CONTACT_EMAIL},
            "license_info": {"name": settings.LICENSE_NAME},
        }
        kwargs.update(to_update)

    if isinstance(settings, EnvironmentSettings):
        kwargs.update({"docs_url": None, "redoc_url": None, "openapi_url": None})

    # Use custom lifespan if provided, otherwise use default factory
    if lifespan is None:
        lifespan = lifespan_factory(settings, create_tables_on_start=create_tables_on_start)

    application = FastAPI(lifespan=lifespan, generate_unique_id_function=custom_generate_unique_id, **kwargs)
    application.include_router(router)

    # Seed initial RBAC after tables creation in non-production environments
    if isinstance(settings, DatabaseSettings):
        # Seeding should happen after app startup completes; use background task
        @application.on_event("startup")
        async def _seed_rbac() -> None:
            try:
                await seed_initial_rbac()
            except Exception:
                # Avoid crashing app if seeding fails; you can check logs
                pass

    if isinstance(settings, ClientSideCacheSettings):
        application.add_middleware(ClientCacheMiddleware, max_age=settings.CLIENT_CACHE_MAX_AGE)

    # Enable CORS only if origins are provided via environment
    if isinstance(settings, CORSSettings):
        origins = settings.CORS_ORIGINS
        if isinstance(origins, list) and origins:
            application.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
    if isinstance(settings, EnvironmentSettings):
        if settings.ENVIRONMENT != EnvironmentOption.PRODUCTION:
            docs_router = APIRouter()
            if settings.ENVIRONMENT != EnvironmentOption.LOCAL:
                docs_router = APIRouter(dependencies=[Depends(get_current_superuser)])

            @docs_router.get("/docs", include_in_schema=False)
            async def get_swagger_documentation() -> fastapi.responses.HTMLResponse:
                return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/redoc", include_in_schema=False)
            async def get_redoc_documentation() -> fastapi.responses.HTMLResponse:
                return get_redoc_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/openapi.json", include_in_schema=False)
            async def openapi() -> dict[str, Any]:
                out: dict = get_openapi(title=application.title, version=application.version, routes=application.routes)
                return out

            application.include_router(docs_router)

    return application

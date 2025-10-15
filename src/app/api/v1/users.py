from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Request
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_superuser, get_current_user, require_permission
from ...core.decorators.unit_of_work import transactional
from ...core.permissions import PermissionNames
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import DuplicateValueException, NotFoundException
from ...core.security import blacklist_token, get_password_hash, oauth2_scheme
from ...crud.crud_rate_limit import crud_rate_limits
from ...crud.crud_tier import crud_tiers
from ...crud.crud_users import crud_users
from ...schemas.tier import TierRead
from ...schemas.user import UserCreate, UserCreateInternal, UserRead, UserTierUpdate, UserUpdate

router = APIRouter(tags=["users"])

# 当前路由仅允许具有 USER_CREATE 权限的用户访问
# 仅处理用户模型相关字段（角色分配请使用专门接口）
@router.post("/user",dependencies=[Depends(require_permission(PermissionNames.USER_CREATE))], response_model=UserRead, status_code=201)
@transactional()
async def write_user(
    request: Request, user: UserCreate, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> UserRead:
    email_row = await crud_users.exists(db=db, email=user.email)
    if email_row:
        raise DuplicateValueException("Email is already registered")

    username_row = await crud_users.exists(db=db, username=user.username)
    if username_row:
        raise DuplicateValueException("Username not available")

    user_internal_dict = user.model_dump()
    user_internal_dict["hashed_password"] = get_password_hash(password=user_internal_dict["password"])
    del user_internal_dict["password"]

    user_internal = UserCreateInternal(**user_internal_dict)
    
    # Create user (transaction managed by decorator)
    created_user = await crud_users.create(db=db, object=user_internal, commit=False)

    # Fetch the created user with all data (outside transaction for read-only operation)
    user_read = await crud_users.get(db=db, id=created_user.id, schema_to_select=UserRead)
    if user_read is None:
        raise NotFoundException("Created user not found")

    return cast(UserRead, user_read)



@router.get("/users",dependencies=[Depends(require_permission(PermissionNames.USER_READ))], response_model=PaginatedListResponse[UserRead])
async def read_users(
    request: Request, db: Annotated[AsyncSession, Depends(async_get_db)], page: int = 1, items_per_page: int = 10
) -> dict:
    users_data = await crud_users.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        is_deleted=False,
    )

    response: dict[str, Any] = paginated_response(crud_data=users_data, page=page, items_per_page=items_per_page)
    return response


@router.get("/user/me/", response_model=UserRead)
async def read_users_me(request: Request, current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    return current_user



@router.get("/user/{username}",dependencies=[Depends(require_permission(PermissionNames.USER_READ))], response_model=UserRead)
async def read_user(request: Request, username: str, db: Annotated[AsyncSession, Depends(async_get_db)]) -> UserRead:
    db_user = await crud_users.get(db=db, username=username, is_deleted=False, schema_to_select=UserRead)
    if db_user is None:
        raise NotFoundException("User not found")

    return cast(UserRead, db_user)



@router.patch("/user/{user_id}", response_model=UserRead,dependencies=[Depends(require_permission(PermissionNames.USER_UPDATE))])
@transactional()
async def patch_user(
    user_id: int, values: UserUpdate, current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
) -> UserRead:
    user_current = await crud_users.get(db=db, id=user_id)
    if not user_current:
        raise NotFoundException("User not found")

    if values.username != user_current.username:
        existing_username = await crud_users.exists(db=db, username=values.username)
        if existing_username:
            raise DuplicateValueException("Username not available")

    if values.email != user_current.email:
        existing_email = await crud_users.exists(db=db, email=values.email)
        if existing_email:
            raise DuplicateValueException("Email is already registered")

    # Update user (transaction managed by decorator)
    updated_user = await crud_users.update(db=db, object=values, id=user_id, commit=False)
    return cast(UserRead, updated_user)


@router.delete("/user/{user_id}",dependencies=[Depends(require_permission(PermissionNames.USER_DELETE))])
@transactional()
async def erase_user(
    user_id: int, current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, id=user_id)
    if not db_user:
        raise NotFoundException("User not found")

    # Delete user (transaction managed by decorator)
    await crud_users.delete(db=db, id=user_id, commit=False)
    return {"message": "User deleted"}


@router.delete("/db_user/{username}", dependencies=[Depends(get_current_superuser), Depends(require_permission(PermissionNames.USER_DELETE))])
@transactional()
async def erase_db_user(
    request: Request,
    username: str,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    token: str = Depends(oauth2_scheme),
) -> dict[str, str]:
    db_user = await crud_users.exists(db=db, username=username)
    if not db_user:
        raise NotFoundException("User not found")

    # Delete user and blacklist token (transaction managed by decorator)
    await crud_users.db_delete(db=db, username=username)
    await blacklist_token(token=token, db=db)
    return {"message": "User deleted from the database"}


@router.get("/user/{username}/rate_limits", dependencies=[Depends(get_current_superuser)])
async def read_user_rate_limits(
    request: Request, username: str, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, Any]:
    db_user = await crud_users.get(db=db, username=username, schema_to_select=UserRead)
    if db_user is None:
        raise NotFoundException("User not found")

    db_user = cast(UserRead, db_user)
    user_dict = db_user.model_dump()
    if db_user.tier_id is None:
        user_dict["tier_rate_limits"] = []
        return user_dict

    db_tier = await crud_tiers.get(db=db, id=db_user.tier_id, schema_to_select=TierRead)
    if db_tier is None:
        raise NotFoundException("Tier not found")

    db_tier = cast(TierRead, db_tier)
    db_rate_limits = await crud_rate_limits.get_multi(db=db, tier_id=db_tier.id)

    user_dict["tier_rate_limits"] = db_rate_limits["data"]

    return user_dict


@router.get("/user/{username}/tier")
async def read_user_tier(
    request: Request, username: str, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict | None:
    db_user = await crud_users.get(db=db, username=username, schema_to_select=UserRead)
    if db_user is None:
        raise NotFoundException("User not found")

    db_user = cast(UserRead, db_user)
    if db_user.tier_id is None:
        return None

    db_tier = await crud_tiers.get(db=db, id=db_user.tier_id, schema_to_select=TierRead)
    if not db_tier:
        raise NotFoundException("Tier not found")

    db_tier = cast(TierRead, db_tier)

    user_dict = db_user.model_dump()
    tier_dict = db_tier.model_dump()

    for key, value in tier_dict.items():
        user_dict[f"tier_{key}"] = value

    return user_dict


@router.patch("/user/{user_id}/tier", response_model=UserRead,dependencies=[Depends(require_permission(PermissionNames.USER_UPDATE))])
@transactional()
async def patch_user_tier(
    user_id: int, user_tier: UserTierUpdate, current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
) -> UserRead:
    # Check if user exists
    db_user = await crud_users.get(db=db, id=user_id)
    if not db_user:
        raise NotFoundException("User not found")

    # Check if tier exists
    tier = await crud_tiers.get(db=db, id=user_tier.tier_id)
    if not tier:
        raise NotFoundException("Tier not found")

    # Update user tier (transaction managed by decorator)
    updated_user = await crud_users.update(db=db, object=user_tier, id=user_id, commit=False)
    return cast(UserRead, updated_user)

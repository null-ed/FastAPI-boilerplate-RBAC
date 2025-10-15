from typing import Annotated, cast, List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...api.dependencies import require_permission
from ...core.decorators.unit_of_work import transactional
from ...core.permissions import PermissionNames
from ...core.db.database import async_get_db
from ...crud.crud_roles import crud_roles
from ...models.permission_map import PermissionMap
from ...schemas.role import (
    RoleCreate,
    RoleCreateInternal,
    RoleRead,
    RoleUpdate,
    RoleUpdateInternal,
)

router = APIRouter(prefix="/role", tags=["roles"])


@router.post("/", dependencies=[Depends(require_permission(PermissionNames.ROLE_CREATE))], response_model=RoleRead, status_code=201)
@transactional()
async def create_role(
    request: Request, role_in: RoleCreate, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> RoleRead:
    # Check duplicate name
    existing = await crud_roles.exists(db=db, name=role_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="The role with this name already exists in the system.")

    # Create role (transaction managed by decorator)
    created = await crud_roles.create(db=db, object=RoleCreateInternal(**role_in.model_dump()), commit=False)
    role_read = await crud_roles.get(db=db, id=created.id, schema_to_select=RoleRead)
    if role_read is None:
        raise HTTPException(status_code=404, detail="Created role not found")
    role_read = cast(RoleRead, role_read)

    # Simplified: do not handle permissions here
    return role_read


@router.get("/", dependencies=[Depends(require_permission(PermissionNames.ROLE_READ))], response_model=List[RoleRead])
async def list_roles(request: Request, db: Annotated[AsyncSession, Depends(async_get_db)]) -> List[RoleRead]:
    data = await crud_roles.get_multi(db=db)
    return cast(List[RoleRead], data["data"])


@router.get("/{role_id}", dependencies=[Depends(require_permission(PermissionNames.ROLE_READ))], response_model=RoleRead)
async def read_role(request: Request, role_id: int, db: Annotated[AsyncSession, Depends(async_get_db)]) -> RoleRead:
    role = await crud_roles.get(db=db, id=role_id, schema_to_select=RoleRead)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return cast(RoleRead, role)


@router.put("/{role_id}", dependencies=[Depends(require_permission(PermissionNames.ROLE_UPDATE))], response_model=RoleRead)
@transactional()
async def update_role(
    request: Request, role_id: int, role_in: RoleUpdate, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> RoleRead:
    role = await crud_roles.get(db=db, id=role_id, schema_to_select=RoleRead)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    # Duplicate name check
    if role_in.name is not None:
        existing = await crud_roles.get(db=db, name=role_in.name, schema_to_select=RoleRead)
        if existing and cast(RoleRead, existing).id != cast(RoleRead, role).id:
            raise HTTPException(status_code=400, detail="The role with this name already exists in the system.")

    # Update role (transaction managed by decorator)
    await crud_roles.update(db=db, object=RoleUpdateInternal(**role_in.model_dump(exclude_unset=True), updated_at=None), id=role_id, commit=False)

    updated = await crud_roles.get(db=db, id=role_id, schema_to_select=RoleRead)
    if updated is None:
        raise HTTPException(status_code=404, detail="Role not found after update")
    return cast(RoleRead, updated)


@router.delete("/{role_id}", dependencies=[Depends(require_permission(PermissionNames.ROLE_DELETE))])
@transactional()
async def delete_role(request: Request, role_id: int, db: Annotated[AsyncSession, Depends(async_get_db)]) -> dict[str, str]:
    role = await crud_roles.get(db=db, id=role_id, schema_to_select=RoleRead)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    # Delete role's permissions and user-role links (transaction managed by decorator)
    from ...models.user_role import UserRole

    # Remove UserRole links
    links = await db.execute(select(UserRole).where(UserRole.role_id == role_id))
    for link in links.scalars().all():
        await db.delete(link)

    # Remove permissions (PermissionMap rows for this role)
    perms_q = await db.execute(select(PermissionMap).where(PermissionMap.role_id == role_id))
    for perm in perms_q.scalars().all():
        await db.delete(perm)

    # Delete role
    await crud_roles.db_delete(db=db, id=role_id, commit=False)
    return {"message": "Role deleted"}


# Roles router simplified: permission assignment handled in permissions router
from typing import Annotated, Any, cast, List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...api.dependencies import get_current_superuser, require_permission
from ...core.permissions import PermissionNames
from ...core.db.database import async_get_db
from ...crud.crud_roles import crud_roles
from ...crud.crud_permissions import assign_permission_to_role, remove_permission_from_role, list_role_permissions
from ...schemas.role import (
    RoleCreate,
    RoleCreateInternal,
    RoleRead,
    RoleUpdate,
    RoleUpdateInternal,
    RolePermissionsRead,
    PermissionAssign,
)

router = APIRouter(prefix="/role", tags=["roles"])


@router.post("/", dependencies=[Depends(require_permission(PermissionNames.ROLE_CREATE))], response_model=RolePermissionsRead, status_code=201)
async def create_role(
    request: Request, role_in: RoleCreate, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> RolePermissionsRead:
    # Check duplicate name
    existing = await crud_roles.get(db=db, name=role_in.name, schema_to_select=RoleRead)
    if existing:
        raise HTTPException(status_code=400, detail="The role with this name already exists in the system.")

    created = await crud_roles.create(db=db, object=RoleCreateInternal(**role_in.model_dump()))
    role_read = await crud_roles.get(db=db, id=created.id, schema_to_select=RoleRead)
    if role_read is None:
        raise HTTPException(status_code=404, detail="Created role not found")
    role_read = cast(RoleRead, role_read)

    # Assign permissions if provided
    if role_in.permission_names:
        for perm in role_in.permission_names:
            await assign_permission_to_role(db, role_id=role_read.id, permission_name=perm)

    perms = await list_role_permissions(db, role_id=role_read.id)
    return RolePermissionsRead(**role_read.model_dump(), permissions=perms)


@router.get("/", dependencies=[Depends(require_permission(PermissionNames.ROLE_READ))], response_model=List[RoleRead])
async def list_roles(request: Request, db: Annotated[AsyncSession, Depends(async_get_db)]) -> List[RoleRead]:
    data = await crud_roles.get_multi(db=db)
    return cast(List[RoleRead], data["data"])


@router.get("/{role_id}", dependencies=[Depends(require_permission(PermissionNames.ROLE_READ))], response_model=RolePermissionsRead)
async def read_role(request: Request, role_id: int, db: Annotated[AsyncSession, Depends(async_get_db)]) -> RolePermissionsRead:
    role = await crud_roles.get(db=db, id=role_id, schema_to_select=RoleRead)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    role = cast(RoleRead, role)
    perms = await list_role_permissions(db, role_id=role.id)
    return RolePermissionsRead(**role.model_dump(), permissions=perms)


@router.put("/{role_id}", dependencies=[Depends(require_permission(PermissionNames.ROLE_UPDATE))], response_model=RolePermissionsRead)
async def update_role(
    request: Request, role_id: int, role_in: RoleUpdate, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> RolePermissionsRead:
    role = await crud_roles.get(db=db, id=role_id, schema_to_select=RoleRead)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    # Duplicate name check
    if role_in.name is not None:
        existing = await crud_roles.get(db=db, name=role_in.name, schema_to_select=RoleRead)
        if existing and cast(RoleRead, existing).id != cast(RoleRead, role).id:
            raise HTTPException(status_code=400, detail="The role with this name already exists in the system.")

    await crud_roles.update(db=db, object=RoleUpdateInternal(**role_in.model_dump(exclude_unset=True), updated_at=None), id=role_id)

    # Update permissions if provided
    if role_in.permission_names is not None:
        # Remove all existing permissions for role
        current_perms = await list_role_permissions(db, role_id=role_id)
        for p in current_perms:
            await remove_permission_from_role(db, role_id=role_id, permission_name=p)
        # Add new ones
        for p in role_in.permission_names:
            await assign_permission_to_role(db, role_id=role_id, permission_name=p)

    updated = await crud_roles.get(db=db, id=role_id, schema_to_select=RoleRead)
    if updated is None:
        raise HTTPException(status_code=404, detail="Role not found after update")
    updated = cast(RoleRead, updated)
    perms = await list_role_permissions(db, role_id=updated.id)
    return RolePermissionsRead(**updated.model_dump(), permissions=perms)


@router.delete("/{role_id}", dependencies=[Depends(require_permission(PermissionNames.ROLE_DELETE))])
async def delete_role(request: Request, role_id: int, db: Annotated[AsyncSession, Depends(async_get_db)]) -> dict[str, str]:
    role = await crud_roles.get(db=db, id=role_id, schema_to_select=RoleRead)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    # Delete role's permissions and user-role links
    from ...models.user_role import UserRole
    from ...models.permission import Permission

    # Remove UserRole links
    links = await db.execute(select(UserRole).where(UserRole.role_id == role_id))
    for link in links.scalars().all():
        await db.delete(link)

    # Remove permissions
    perms_q = await db.execute(select(Permission).where(Permission.role_id == role_id))
    for perm in perms_q.scalars().all():
        await db.delete(perm)

    await crud_roles.db_delete(db=db, id=role_id)
    return {"message": "Role deleted"}


# Permission assignment endpoints removed
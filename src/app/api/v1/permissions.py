from fastapi import APIRouter, Depends
from typing import Any, List, Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import require_permission, get_current_user
from ...core.decorators.unit_of_work import transactional
from ...core.db.database import async_get_db
from ...core.permissions import PermissionNames, permission_tree, flatten_permissions, permission_root
from ...core.exceptions.http_exceptions import NotFoundException
from ...crud.crud_roles import crud_roles
from ...crud.crud_permission_maps import assign_permissions_to_role
from ...schemas.role import RolePermissionsAssign

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("/", dependencies=[Depends(require_permission(PermissionNames.ROLE_READ))])
async def read_permissions() -> List[str]:
    """Retrieve all available permissions (flattened)."""
    from ...core.permissions import permission_root

    return flatten_permissions(permission_root)


@router.get("/tree", dependencies=[Depends(require_permission(PermissionNames.ROLE_READ))])
async def read_permissions_tree() -> Any:
    """Retrieve permissions as a tree structure for frontend display."""
    return permission_tree()


@router.put("/role/{role_id}", dependencies=[Depends(require_permission(PermissionNames.ROLE_UPDATE))])
@transactional()
async def grant_role_permissions(
    role_id: int,
    perms_in: RolePermissionsAssign,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, Any]:
    """Replace a role's permissions with the provided list.

    - Verifies the role exists
    - Validates permission names against the known permission registry
    - Replaces all role permissions in a single transaction
    """
    # Ensure role exists
    role = await crud_roles.get(db=db, id=role_id)
    if not role:
        raise NotFoundException("Role not found")

    # Normalize and validate permission names
    incoming_names = perms_in.permission_names or []
    allowed = set(flatten_permissions(permission_root))
    for name in incoming_names:
        if name not in allowed:
            raise NotFoundException(f"Permission not found: {name}")

    # Replace permissions
    await assign_permissions_to_role(db, role_id, incoming_names)

    return {"role_id": role_id, "permission_names": incoming_names}
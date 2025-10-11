from fastapi import APIRouter, Depends
from typing import Any, List

from ..dependencies import require_permission
from ...core.permissions import PermissionNames, permission_tree, flatten_permissions

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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.permission_map import PermissionMap


async def assign_permissions_to_role(db: AsyncSession, role_id: int, permission_names: list[str] | None) -> None:
    """Replace all permissions for a role with the provided list.

    - Removes existing PermissionMap rows for the role
    - Adds new PermissionMap rows for each permission in the deduplicated list
    - Treats None or empty list as removing all permissions
    """
    # Remove existing permissions
    existing_q = await db.execute(select(PermissionMap).where(PermissionMap.role_id == role_id))
    for row in existing_q.scalars().all():
        await db.delete(row)

    # Add new permissions (deduplicated)
    unique_permissions = list(set(permission_names or []))
    for perm_name in unique_permissions:
        db.add(PermissionMap(permission_name=perm_name, role_id=role_id))

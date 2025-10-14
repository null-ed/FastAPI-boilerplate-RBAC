from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..models.permission_map import PermissionMap



async def assign_permission_to_role(db: AsyncSession, role_id: int, permission_name: str) -> None:
    existing = await db.execute(
        select(PermissionMap).where(PermissionMap.role_id == role_id, PermissionMap.permission_name == permission_name)
    )
    if existing.scalar_one_or_none():
        return
    db.add(PermissionMap(permission_name=permission_name, role_id=role_id))


async def remove_permission_from_role(db: AsyncSession, role_id: int, permission_name: str) -> bool:
    q = await db.execute(
        select(PermissionMap).where(PermissionMap.role_id == role_id, PermissionMap.permission_name == permission_name)
    )
    perm = q.scalar_one_or_none()
    if not perm:
        return False
    await db.delete(perm)
    return True

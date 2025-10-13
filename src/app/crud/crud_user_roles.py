from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.user_role import UserRole


async def assign_role_to_user(db: AsyncSession, user_id: int, role_id: int) -> None:
    existing = await db.execute(select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id))
    if existing.scalar_one_or_none():
        return
    db.add(UserRole(user_id=user_id, role_id=role_id))


async def remove_role_from_user(db: AsyncSession, user_id: int, role_id: int) -> bool:
    q = await db.execute(select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id))
    link = q.scalar_one_or_none()
    if not link:
        return False
    await db.delete(link)
    return True


async def list_user_roles(db: AsyncSession, user_id: int) -> list[int]:
    q = await db.execute(select(UserRole.role_id).where(UserRole.user_id == user_id))
    return [row[0] for row in q.all()]
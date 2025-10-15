from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.user_role import UserRole


async def assign_role_to_user(db: AsyncSession, user_id: int, role_ids: list[int] | None) -> None:
    # 删除用户的所有角色关联
    links_q = await db.execute(select(UserRole).where(UserRole.user_id == user_id))
    for link in links_q.scalars().all():
        await db.delete(link)

    # 处理传入角色ID列表（None 或 空 列表不授予任何角色）
    unique_role_ids = list(set(role_ids or []))
    for rid in unique_role_ids:
        db.add(UserRole(user_id=user_id, role_id=rid))

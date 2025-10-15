from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import require_permission, get_current_user
from ...core.decorators.unit_of_work import transactional
from ...core.permissions import PermissionNames
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import NotFoundException
from ...crud.crud_users import crud_users
from ...crud.crud_roles import crud_roles
from ...crud.crud_user_roles import assign_role_to_user
from ...schemas.user import UserRolesAssign


router = APIRouter(prefix="/user_roles", tags=["user_roles"])


@router.put("/{user_id}", dependencies=[Depends(require_permission(PermissionNames.USER_UPDATE))])
@transactional()
async def grant_user_roles(
    user_id: int,
    roles_in: UserRolesAssign,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, Any]:
    # 确认用户存在
    db_user = await crud_users.get(db=db, id=user_id)
    if not db_user:
        raise NotFoundException("User not found")

    # 处理传入角色ID列表（None 视为空列表）
    role_ids = roles_in.role_ids or []

    # 校验角色是否存在
    for rid in role_ids:
        role = await crud_roles.get(db=db, id=rid)
        if role is None:
            raise NotFoundException(f"Role not found: {rid}")

    # 替换用户角色（在同一事务中删除并重新授予）
    await assign_role_to_user(db, user_id, role_ids)

    return {"user_id": user_id, "role_ids": role_ids}
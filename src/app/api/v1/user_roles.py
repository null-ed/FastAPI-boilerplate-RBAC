from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import require_permission
from ...core.permissions import PermissionNames
from ...core.db.database import async_get_db
from ...crud.crud_user_roles import assign_role_to_user, remove_role_from_user

router = APIRouter(prefix="/user-roles", tags=["user_roles"])


# User-role assignment endpoints removed
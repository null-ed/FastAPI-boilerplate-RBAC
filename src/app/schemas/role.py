from datetime import datetime
from typing import Annotated, List

from pydantic import BaseModel, ConfigDict, Field

from ..core.schemas import TimestampSchema


class RoleBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=50, examples=["admin"])]
    description: Annotated[str | None, Field(default=None, examples=["System Administrator"])]


class Role(TimestampSchema, RoleBase):
    is_active: bool = True


class RoleRead(RoleBase):
    id: int
    is_active: bool
    created_at: datetime


class RoleCreate(RoleBase):
    model_config = ConfigDict(extra="forbid")

    is_active: bool = True
    permission_names: List[str] | None = None


class RoleCreateInternal(RoleCreate):
    pass


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    permission_names: List[str] | None = None


class RoleUpdateInternal(RoleUpdate):
    updated_at: datetime


class RoleDelete(BaseModel):
    pass


class RolePermissionsRead(RoleRead):
    permissions: List[str] = []


class PermissionAssign(BaseModel):
    permission_name: Annotated[str, Field(min_length=2, max_length=100, examples=["user:read"])]
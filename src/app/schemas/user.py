from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema


class UserBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=30, examples=["User Userson"])]
    username: Annotated[str, Field(min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"])]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]
    phone_number: Annotated[
        str | None,
        Field(
            pattern=r"^\+?[0-9]{7,15}$",
            examples=["13123456789", "+12025550123"],
            default=None,
        ),
    ]


class User(TimestampSchema, UserBase, UUIDSchema, PersistentDeletion):
    hashed_password: str
    is_superuser: bool = False
    tier_id: int | None = None


class UserRead(BaseModel):
    id: int

    name: Annotated[str, Field(min_length=2, max_length=30, examples=["User Userson"])]
    username: Annotated[str, Field(min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"])]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]
    phone_number: Annotated[
        str | None,
        Field(
            examples=["13123456789", "+12025550123"],
            default=None,
        ),
    ]
    tier_id: int | None


class UserCreate(UserBase):
    model_config = ConfigDict(extra="forbid")

    password: Annotated[str, Field(pattern=r"^.{8,}|[0-9]+|[A-Z]+|[a-z]+|[^a-zA-Z0-9]+$", examples=["Str1ngst!"])]


class UserCreateInternal(UserBase):
    hashed_password: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str | None, Field(min_length=2, max_length=30, examples=["User Userberg"], default=None)]
    username: Annotated[
        str | None, Field(min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userberg"], default=None)
    ]
    email: Annotated[EmailStr | None, Field(examples=["user.userberg@example.com"], default=None)]
    phone_number: Annotated[
        str | None,
        Field(
            pattern=r"^\+?[0-9]{7,15}$",
            examples=["13123456789", "+12025550123"],
            default=None,
        ),
    ]


class UserUpdateInternal(UserUpdate):
    updated_at: datetime


class UserTierUpdate(BaseModel):
    tier_id: int


class UserDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime


class UserRestoreDeleted(BaseModel):
    is_deleted: bool


# Schema for assigning roles: replace user's roles with provided list
class UserRolesAssign(BaseModel):
    role_ids: Annotated[list[int] | None, Field(default=None)]

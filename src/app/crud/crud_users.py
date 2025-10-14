from .custom_fastcrud import FastCRUDNoCommit

from ..models.user import User
from ..schemas.user import UserCreateInternal, UserDelete, UserRead, UserUpdate, UserUpdateInternal

CRUDUser = FastCRUDNoCommit[User, UserCreateInternal, UserUpdate, UserUpdateInternal, UserDelete, UserRead]
crud_users = CRUDUser(User)

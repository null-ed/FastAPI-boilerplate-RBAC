from .custom_fastcrud import FastCRUDNoCommit

from ..models.role import Role
from ..schemas.role import RoleCreateInternal, RoleDelete, RoleRead, RoleUpdate, RoleUpdateInternal

CRUDRole = FastCRUDNoCommit[Role, RoleCreateInternal, RoleUpdate, RoleUpdateInternal, RoleDelete, RoleRead]
crud_roles = CRUDRole(Role)
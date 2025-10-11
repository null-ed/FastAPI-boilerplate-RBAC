from fastcrud import FastCRUD

from ..models.role import Role
from ..schemas.role import RoleCreateInternal, RoleDelete, RoleRead, RoleUpdate, RoleUpdateInternal

CRUDRole = FastCRUD[Role, RoleCreateInternal, RoleUpdate, RoleUpdateInternal, RoleDelete, RoleRead]
crud_roles = CRUDRole(Role)
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


class PermissionNames:
    # Root/system level
    ROOT = "root"

    # User domain permissions
    USER_MANAGE = "user:manage"
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Role domain permissions
    ROLE_MANAGE = "role:manage"
    ROLE_READ = "role:read"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_ASSIGN = "role:assign"
    ROLE_REVOKE = "role:revoke"
    ROLE_DELETE = "role:delete"


@dataclass
class PermissionNode:
    """Permission tree node used for frontend presentation and grouping.

    name: permission identifier string (from PermissionNames)
    display_name: human-friendly name for UI
    children: nested permissions or groups
    """

    name: str
    display_name: str | None = None
    children: List[PermissionNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "children": [child.to_dict() for child in self.children],
        }


# ----- Build permission tree -----
permission_user_manage = PermissionNode(
    PermissionNames.USER_MANAGE,
    display_name="用户管理",
    children=[
        PermissionNode(PermissionNames.USER_CREATE, display_name="创建用户"),
        PermissionNode(PermissionNames.USER_READ, display_name="查看用户"),
        PermissionNode(PermissionNames.USER_UPDATE, display_name="更新用户"),
        PermissionNode(PermissionNames.USER_DELETE, display_name="删除用户"),
    ],
)

permission_role_manage = PermissionNode(
    PermissionNames.ROLE_MANAGE,
    display_name="角色管理",
    children=[
        PermissionNode(PermissionNames.ROLE_CREATE, display_name="创建角色"),
        PermissionNode(PermissionNames.ROLE_READ, display_name="查看角色"),
        PermissionNode(PermissionNames.ROLE_UPDATE, display_name="更新角色"),
        PermissionNode(PermissionNames.ROLE_ASSIGN, display_name="分配角色权限"),
        PermissionNode(PermissionNames.ROLE_REVOKE, display_name="撤销角色权限"),
        PermissionNode(PermissionNames.ROLE_DELETE, display_name="删除角色"),
    ],
)

permission_root = PermissionNode(
    PermissionNames.ROOT,
    display_name="系统权限",
    children=[permission_user_manage, permission_role_manage],
)


# ----- Utilities -----

def flatten_permissions(root: PermissionNode) -> List[str]:
    """Collect all permission names from the tree (preorder)."""
    names: List[str] = []

    def _walk(node: PermissionNode) -> None:
        names.append(node.name)
        for child in node.children:
            _walk(child)

    _walk(root)
    return names


def permission_tree() -> Dict[str, Any]:
    """Return tree structure for frontend."""
    return permission_root.to_dict()
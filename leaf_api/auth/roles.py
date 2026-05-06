"""Role definitions and permissions"""

from typing import TypedDict, Dict, List


class _RoleData(TypedDict):
    permissions: List[str]
    visible_fields: Dict[str, List[str]]


ROLES: Dict[str, _RoleData] = {
    "admin": {
        "permissions": ["read", "write", "delete"],
        "visible_fields": {
            "Order": ["id", "customer_id", "product_id", "quantity", "status", "total_price", "cost", "created_at", "updated_at"],
            "Customer": ["id", "name", "email", "phone", "status", "created_at", "updated_at"],
            "Product": ["id", "name", "description", "price", "cost", "stock_quantity", "status", "created_at", "updated_at"],
        },
    },
    "user": {
        "permissions": ["read", "write"],
        "visible_fields": {
            "Order": ["id", "customer_id", "product_id", "quantity", "status", "total_price", "created_at"],
            "Customer": ["id", "name", "email", "phone", "status"],
            "Product": ["id", "name", "description", "price", "stock_quantity"],
        },
    },
    "public": {
        "permissions": ["read"],
        "visible_fields": {
            "Order": ["id", "status"],
            "Customer": ["id", "name"],
            "Product": ["id", "name", "price"],
        },
    },
}

DEFAULT_ROLE = "public"


def get_role_permissions(role: str) -> List[str]:
    """Get permissions for a role"""
    return ROLES.get(role, ROLES[DEFAULT_ROLE])["permissions"]


def get_visible_fields(role: str, resource_type: str) -> list:
    """Get visible fields for a role and resource type"""
    role_data = ROLES.get(role, ROLES[DEFAULT_ROLE])
    return role_data["visible_fields"].get(resource_type, [])


def has_permission(role: str, permission: str) -> bool:
    """Check if role has permission"""
    return permission in get_role_permissions(role)

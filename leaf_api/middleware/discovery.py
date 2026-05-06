"""HEAD request handler and API discovery logic"""

from typing import Any, Dict, List, Mapping, Optional
from flask import request, jsonify, Response
from leaf_api.middleware.cache import CacheManager
from leaf_api.auth.roles import get_visible_fields
from shared.constants import HEADER_X_RESOURCE_TYPE, HEADER_X_HAS_CHILDREN


class DiscoveryHandler:
    """Handles HEAD requests for API discovery"""

    @staticmethod
    def build_discovery_response(
        resource_type: str,
        description: str,
        schema: Dict,
        children: Optional[List[str]] = None,
        user_role: str = "public",
        permissions: Optional[List[str]] = None,
    ) -> Dict:
        """Build response body for HEAD requests"""
        response_data = {
            "description": description,
            "schema": schema,
            "_meta": {
                "role": user_role,
                "permissions": permissions or [],
            },
        }

        if children:
            response_data["_links"] = {
                "children": children,
            }

        return response_data

    @staticmethod
    def get_immediate_children(path: str, resource_map: Dict) -> List[str]:
        """Get list of immediate child paths for a given endpoint"""
        if path not in resource_map:
            return []

        resource_info = resource_map[path]
        return resource_info.get("children", [])

    @staticmethod
    def apply_cache_headers(
        response: Response, content: Dict, ttl: int = 3600
    ) -> Response:
        """Apply ETag and cache headers to response"""
        etag = CacheManager.generate_etag(content)
        CacheManager.set_cache_headers(response.headers, etag, ttl)
        response.headers["X-Cached"] = "false"
        return response

    @staticmethod
    def should_return_304(request_headers: Any, current_etag: str) -> bool:
        """Check if request has matching ETag for 304 response"""
        return CacheManager.should_return_304(request_headers, current_etag)


# Resource discovery map - defines what each endpoint returns
RESOURCE_DISCOVERY_MAP = {
    "/": {
        "type": "root",
        "description": "Root API endpoint listing available resources",
        "children": ["/orders", "/customers", "/products"],
    },
    "/orders": {
        "type": "collection",
        "resource_type": "Order",
        "description": "Collection of customer orders",
        "schema_generator": "OrderSchemaGenerator",
        "children": [],  # Dynamic - populated from DB
    },
    "/customers": {
        "type": "collection",
        "resource_type": "Customer",
        "description": "Collection of customers",
        "schema_generator": "CustomerSchemaGenerator",
        "children": [],  # Dynamic - populated from DB
    },
    "/products": {
        "type": "collection",
        "resource_type": "Product",
        "description": "Collection of products",
        "schema_generator": "ProductSchemaGenerator",
        "children": [],  # Dynamic - populated from DB
    },
}

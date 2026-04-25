"""Order resource schema generation"""

from typing import Dict, Any, Optional
from leaf_api.models.order import Order
from leaf_api.schemas.utils import apply_role_filter, apply_query_filters


class OrderSchemaGenerator:
    """Generate JSON schemas for Order resource using SQLModel"""

    @staticmethod
    def get_collection_schema(
        user_role: str = "public", query_params: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Get schema for orders collection"""
        # Get base schema from SQLModel
        schema = Order.model_json_schema()

        # Apply role-based filtering
        schema = apply_role_filter(schema, user_role, "Order")

        # Apply query parameter filters
        schema = apply_query_filters(schema, query_params or {})

        return schema

    @staticmethod
    def get_detail_schema(
        user_role: str = "public", query_params: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Get schema for a specific order detail"""
        # Same as collection schema for orders
        return OrderSchemaGenerator.get_collection_schema(user_role, query_params)

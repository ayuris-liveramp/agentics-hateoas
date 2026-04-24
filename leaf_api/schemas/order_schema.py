"""Order resource schema generator"""

from typing import Dict, Any
from leaf_api.schemas.base_schema import JSONSchemaBuilder


class OrderSchemaGenerator:
    """Generate JSON schemas for Order resource"""

    @staticmethod
    def get_collection_schema(user_role: str = "public", query_params: Dict[str, Any] = None) -> Dict:
        """Get schema for orders collection"""
        builder = JSONSchemaBuilder(
            "Order",
            "A customer order for products",
        )

        # Add properties
        builder.add_property("id", "integer", "Order ID", required=True)
        builder.add_property("customer_id", "integer", "Customer ID", required=True)
        builder.add_property("product_id", "integer", "Product ID", required=True)
        builder.add_property("quantity", "integer", "Quantity ordered", required=True, minimum=1)
        builder.add_property("status", "string", "Order status", required=True, enum=["pending", "confirmed", "shipped", "delivered", "cancelled"])
        builder.add_property("total_price", "number", "Total order price", required=True, minimum=0)
        builder.add_property("created_at", "string", "Order creation timestamp", format="date-time")
        builder.add_property("updated_at", "string", "Last order update timestamp", format="date-time")

        # Admin-only fields
        if user_role == "admin":
            builder.add_property("cost", "number", "Order cost (admin only)", minimum=0)

        # Apply filters
        builder.apply_role_filters(user_role)
        builder.apply_query_filters(query_params or {})

        return builder.build()

    @staticmethod
    def get_detail_schema(user_role: str = "public", query_params: Dict[str, Any] = None) -> Dict:
        """Get schema for a specific order detail"""
        # Same as collection schema for orders
        return OrderSchemaGenerator.get_collection_schema(user_role, query_params)

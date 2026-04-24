"""Product resource schema generator"""

from typing import Dict, Any
from leaf_api.schemas.base_schema import JSONSchemaBuilder


class ProductSchemaGenerator:
    """Generate JSON schemas for Product resource"""

    @staticmethod
    def get_collection_schema(user_role: str = "public", query_params: Dict[str, Any] = None) -> Dict:
        """Get schema for products collection"""
        builder = JSONSchemaBuilder(
            "Product",
            "A product available for ordering",
        )

        # Add properties
        builder.add_property("id", "integer", "Product ID", required=True)
        builder.add_property("name", "string", "Product name", required=True, minLength=1)
        builder.add_property("description", "string", "Product description")
        builder.add_property("price", "number", "Product price", required=True, minimum=0)
        builder.add_property("stock_quantity", "integer", "Available stock", required=True, minimum=0)
        builder.add_property("status", "string", "Product status", required=True, enum=["active", "discontinued", "draft"])
        builder.add_property("created_at", "string", "Product creation timestamp", format="date-time")
        builder.add_property("updated_at", "string", "Last product update timestamp", format="date-time")

        # Admin-only fields
        if user_role == "admin":
            builder.add_property("cost", "number", "Product cost (admin only)", minimum=0)

        # Apply filters
        builder.apply_role_filters(user_role)
        builder.apply_query_filters(query_params or {})

        return builder.build()

    @staticmethod
    def get_detail_schema(user_role: str = "public", query_params: Dict[str, Any] = None) -> Dict:
        """Get schema for a specific product detail"""
        # Same as collection schema for products
        return ProductSchemaGenerator.get_collection_schema(user_role, query_params)

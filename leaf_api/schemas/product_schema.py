"""Product resource schema generation"""

from typing import Dict, Any, Optional
from leaf_api.models.product import Product
from leaf_api.schemas.utils import apply_role_filter, apply_query_filters


class ProductSchemaGenerator:
    """Generate JSON schemas for Product resource using SQLModel"""

    @staticmethod
    def get_collection_schema(
        user_role: str = "public", query_params: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Get schema for products collection"""
        # Get base schema from SQLModel
        schema = Product.model_json_schema()

        # Apply role-based filtering
        schema = apply_role_filter(schema, user_role, "Product")

        # Apply query parameter filters
        schema = apply_query_filters(schema, query_params or {})

        return schema

    @staticmethod
    def get_detail_schema(
        user_role: str = "public", query_params: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Get schema for a specific product detail"""
        # Same as collection schema for products
        return ProductSchemaGenerator.get_collection_schema(user_role, query_params)

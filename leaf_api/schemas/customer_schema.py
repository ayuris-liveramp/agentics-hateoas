"""Customer resource schema generator"""

from typing import Dict, Any
from leaf_api.schemas.base_schema import JSONSchemaBuilder


class CustomerSchemaGenerator:
    """Generate JSON schemas for Customer resource"""

    @staticmethod
    def get_collection_schema(user_role: str = "public", query_params: Dict[str, Any] = None) -> Dict:
        """Get schema for customers collection"""
        builder = JSONSchemaBuilder(
            "Customer",
            "A customer entity with contact information",
        )

        # Add properties
        builder.add_property("id", "integer", "Customer ID", required=True)
        builder.add_property("name", "string", "Customer name", required=True, minLength=1)
        builder.add_property("email", "string", "Customer email address", required=True, format="email")
        builder.add_property("phone", "string", "Customer phone number")
        builder.add_property("status", "string", "Customer account status", required=True, enum=["active", "inactive", "suspended"])
        builder.add_property("created_at", "string", "Customer creation timestamp", format="date-time")
        builder.add_property("updated_at", "string", "Last customer update timestamp", format="date-time")

        # Apply filters
        builder.apply_role_filters(user_role)
        builder.apply_query_filters(query_params or {})

        return builder.build()

    @staticmethod
    def get_detail_schema(user_role: str = "public", query_params: Dict[str, Any] = None) -> Dict:
        """Get schema for a specific customer detail"""
        # Same as collection schema for customers
        return CustomerSchemaGenerator.get_collection_schema(user_role, query_params)

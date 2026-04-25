"""Utilities for JSON schema generation and filtering"""

from typing import Dict, Any, Optional
from leaf_api.auth.roles import get_visible_fields


def apply_role_filter(
    schema: Dict[str, Any], role: str, resource_type: str
) -> Dict[str, Any]:
    """
    Filter schema properties and required fields based on user role.

    Args:
        schema: JSON schema dictionary
        role: User role (e.g., 'admin', 'user', 'public')
        resource_type: Resource type (e.g., 'Customer', 'Product', 'Order')

    Returns:
        Modified schema with filtered properties and required fields
    """
    schema_copy = schema.copy()

    # Get visible fields for this role and resource type
    visible_fields = get_visible_fields(role, resource_type)

    if not visible_fields:
        # If no fields are visible for this role, return empty schema
        return schema_copy

    # Filter properties to only visible fields
    if "properties" in schema_copy:
        schema_copy["properties"] = {
            k: v for k, v in schema_copy["properties"].items()
            if k in visible_fields
        }

    # Filter required fields to only those that are visible
    if "required" in schema_copy:
        schema_copy["required"] = [
            f for f in schema_copy["required"] if f in visible_fields
        ]

    return schema_copy


def apply_query_filters(
    schema: Dict[str, Any], query_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Apply dynamic constraints to schema based on query parameters.

    Supports:
    - positive_only: Add minimum: 0 to numeric fields
    - detailed: Include timestamp fields
    - summary: Only include required fields
    - include_examples: Add example values

    Args:
        schema: JSON schema dictionary
        query_params: Query parameters dictionary

    Returns:
        Modified schema with applied constraints
    """
    if not query_params:
        return schema

    schema_copy = schema.copy()

    # positive_only: constraint numeric fields to be >= 0
    if query_params.get("positive_only") == "true":
        if "properties" in schema_copy:
            for prop_name, prop_def in schema_copy["properties"].items():
                if prop_def.get("type") in ["integer", "number"]:
                    prop_def["minimum"] = 0

    # detailed: add timestamp fields if not present
    if query_params.get("detailed") == "true":
        if "properties" in schema_copy:
            if "created_at" not in schema_copy["properties"]:
                schema_copy["properties"]["created_at"] = {
                    "type": "string",
                    "format": "date-time",
                    "description": "Resource creation timestamp",
                }
            if "updated_at" not in schema_copy["properties"]:
                schema_copy["properties"]["updated_at"] = {
                    "type": "string",
                    "format": "date-time",
                    "description": "Last update timestamp",
                }

    # summary: include only required fields
    if query_params.get("summary") == "true":
        if "properties" in schema_copy and "required" in schema_copy:
            schema_copy["properties"] = {
                k: v for k, v in schema_copy["properties"].items()
                if k in schema_copy["required"]
            }

    # include_examples: add example values (basic implementation)
    if query_params.get("include_examples") == "true":
        schema_copy["examples"] = _generate_examples(schema_copy)

    return schema_copy


def _generate_examples(schema: Dict[str, Any]) -> list:
    """Generate example values based on schema properties"""
    example = {}
    if "properties" in schema:
        for prop_name, prop_def in schema["properties"].items():
            prop_type = prop_def.get("type")
            if prop_type == "string":
                example[prop_name] = f"example_{prop_name}"
            elif prop_type == "integer":
                example[prop_name] = 1
            elif prop_type == "number":
                example[prop_name] = 1.0
            elif prop_type == "boolean":
                example[prop_name] = True
    return [example] if example else []

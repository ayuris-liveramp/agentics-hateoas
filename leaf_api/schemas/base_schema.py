"""Base JSON schema builder for resources"""

from typing import Dict, Any, List, Optional
from leaf_api.auth.roles import ROLES, get_visible_fields


class JSONSchemaBuilder:
    """Build JSON schemas with role-based filtering and query parameter constraints"""

    def __init__(self, resource_type: str, description: str):
        self.resource_type = resource_type
        self.schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": resource_type,
            "description": description,
            "properties": {},
            "required": [],
        }

    def add_property(
        self,
        name: str,
        prop_type: str,
        description: str,
        required: bool = False,
        **kwargs,
    ) -> "JSONSchemaBuilder":
        """Add a property to the schema"""
        prop_def = {
            "type": prop_type,
            "description": description,
        }

        # Add additional constraints from kwargs
        for key, value in kwargs.items():
            if key in ["minimum", "maximum", "minLength", "maxLength", "enum", "format", "pattern"]:
                prop_def[key] = value

        self.schema["properties"][name] = prop_def

        if required:
            if name not in self.schema["required"]:
                self.schema["required"].append(name)

        return self

    def apply_role_filters(self, role: str) -> "JSONSchemaBuilder":
        """Filter properties based on user role"""
        visible_fields = get_visible_fields(role, self.resource_type)

        # Keep only visible fields
        filtered_properties = {
            k: v for k, v in self.schema["properties"].items() if k in visible_fields
        }

        # Update required fields
        filtered_required = [f for f in self.schema["required"] if f in visible_fields]

        self.schema["properties"] = filtered_properties
        self.schema["required"] = filtered_required

        return self

    def apply_query_filters(self, query_params: Dict[str, Any]) -> "JSONSchemaBuilder":
        """Apply constraints based on query parameters"""
        if not query_params:
            return self

        # positive_only: constraint numeric fields to be >= 0
        if query_params.get("positive_only") == "true":
            for prop_name, prop_def in self.schema["properties"].items():
                if prop_def.get("type") in ["integer", "number"]:
                    prop_def["minimum"] = 0

        # detailed: add timestamp fields if not present
        if query_params.get("detailed") == "true":
            if "created_at" not in self.schema["properties"]:
                self.schema["properties"]["created_at"] = {
                    "type": "string",
                    "format": "date-time",
                    "description": "Resource creation timestamp",
                }
            if "updated_at" not in self.schema["properties"]:
                self.schema["properties"]["updated_at"] = {
                    "type": "string",
                    "format": "date-time",
                    "description": "Last update timestamp",
                }

        # summary: include only required fields
        if query_params.get("summary") == "true":
            summary_properties = {
                k: v
                for k, v in self.schema["properties"].items()
                if k in self.schema["required"]
            }
            self.schema["properties"] = summary_properties

        # include_examples: add example values (populated per schema)
        if query_params.get("include_examples") == "true":
            self.schema["examples"] = self._generate_examples()

        return self

    def _generate_examples(self) -> List[Dict]:
        """Generate example values based on schema properties"""
        # This is a simple example generator - can be extended per schema
        example = {}
        for prop_name, prop_def in self.schema["properties"].items():
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

    def add_constraint(
        self, property_name: str, constraint_name: str, constraint_value: Any
    ) -> "JSONSchemaBuilder":
        """Add a constraint to a specific property"""
        if property_name in self.schema["properties"]:
            self.schema["properties"][property_name][constraint_name] = constraint_value
        return self

    def build(self) -> Dict:
        """Return the built schema"""
        return self.schema

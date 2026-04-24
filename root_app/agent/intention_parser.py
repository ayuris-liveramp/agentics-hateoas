"""Parser for Accept-Intention headers"""

from typing import Dict, Optional
from root_app.crawler.graph_builder import APIGraph


class IntentionParser:
    """Parses Accept-Intention headers to filter API graph by agent intent"""

    # Valid actions for intent filtering
    VALID_ACTIONS = ["create", "read", "update", "delete", "list"]
    VALID_DETAIL_LEVELS = ["full", "summary", "minimal"]

    @staticmethod
    def parse_header(header_value: str) -> Dict[str, Optional[str]]:
        """
        Parse Accept-Intention header

        Format: action=create, resource=order, details=full

        Returns:
            Dictionary with parsed intention components
        """
        if not header_value:
            return {"action": None, "resource": None, "details": "full"}

        intention = {"action": None, "resource": None, "details": "full"}

        # Split by comma and parse key=value pairs
        parts = header_value.split(",")
        for part in parts:
            part = part.strip()
            if "=" not in part:
                continue

            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()

            if key == "action" and value in IntentionParser.VALID_ACTIONS:
                intention["action"] = value
            elif key == "resource":
                intention["resource"] = value
            elif key == "details" and value in IntentionParser.VALID_DETAIL_LEVELS:
                intention["details"] = value

        return intention

    @staticmethod
    def filter_graph_by_intention(graph: APIGraph, intention: Dict) -> APIGraph:
        """
        Filter graph to include only resources matching the intention

        Returns:
            New APIGraph with filtered resources
        """
        if not any(intention.values()):
            # No intention filters, return full graph
            return graph

        filtered_graph = APIGraph()

        # Copy API metadata
        for api in graph.root_apis:
            filtered_graph.add_api(api["url"], api)

        # Filter resources by resource type (intention["resource"])
        resource_filter = intention.get("resource")
        detail_level = intention.get("details", "full")

        for path in graph.get_all_paths():
            resource = graph.get_resource(path)
            if not resource:
                continue

            # Check if resource matches filter
            if resource_filter:
                # Match by resource type in description or metadata
                resource_type = resource.get("resource_type") or ""
                if resource_type and resource_filter.lower() not in resource_type.lower():
                    # Also check description
                    description = resource.get("description") or ""
                    if resource_filter.lower() not in description.lower():
                        continue

            # Apply detail level filtering
            filtered_resource = IntentionParser._apply_detail_level(resource, detail_level)

            filtered_graph.add_resource(path, filtered_resource)

            # Add edges for children in filtered graph
            for child in graph.get_children(path):
                if child in [p for p in [path for path, _ in [(p, graph.get_resource(p)) for p in graph.get_all_paths()]]]:
                    filtered_graph.add_edge(path, child)

        return filtered_graph

    @staticmethod
    def _apply_detail_level(resource: Dict, detail_level: str) -> Dict:
        """Apply detail level filtering to resource"""
        if detail_level == "minimal":
            # Return only basic info
            return {
                "path": resource.get("path"),
                "description": resource.get("description"),
            }
        elif detail_level == "summary":
            # Return description and basic schema
            return {
                "path": resource.get("path"),
                "description": resource.get("description"),
                "children": resource.get("children", []),
            }
        else:  # full
            return resource

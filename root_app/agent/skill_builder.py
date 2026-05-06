"""Builds skill descriptions from API graph"""

import json
from typing import Any, Dict, List, Optional
from root_app.crawler.graph_builder import APIGraph


class SkillBuilder:
    """Converts API graph to markdown skill format for LLM agents"""

    @staticmethod
    def build_skill_markdown(graph: APIGraph, intention: Optional[Dict] = None) -> str:
        """
        Convert API graph to markdown skill format

        Returns:
            Markdown string describing available API skills
        """
        if not graph.root_apis:
            return "# No APIs Discovered\n\nNo APIs have been discovered yet."

        markdown_parts = []

        # Header
        markdown_parts.append("# Available API Skills\n")

        # API overview
        for api in graph.root_apis:
            markdown_parts.append(f"## {api.get('title', 'API')}\n")
            if api.get("description"):
                markdown_parts.append(f"{api.get('description')}\n")
            if api.get("version"):
                markdown_parts.append(f"**Version:** {api.get('version')}\n")
            markdown_parts.append(f"**Base URL:** {api.get('url')}\n\n")

        # Resource skills
        resources = SkillBuilder._get_sorted_resources(graph)
        if resources:
            markdown_parts.append("## Available Resources\n\n")

            for path, resource in resources:
                markdown_parts.append(SkillBuilder._format_resource_skill(path, resource))

        # Summary
        graph_summary = graph.get_graph_summary()
        markdown_parts.append("---\n\n")
        markdown_parts.append("## Discovery Summary\n\n")
        markdown_parts.append(f"- Total Resources: {graph_summary['total_nodes']}\n")
        markdown_parts.append(f"- Container Resources: {graph_summary['container_nodes']}\n")
        markdown_parts.append(f"- Leaf Resources: {graph_summary['leaf_nodes']}\n")

        return "\n".join(markdown_parts)

    @staticmethod
    def _get_sorted_resources(graph: APIGraph) -> List[tuple]:
        """Get resources sorted by path"""
        resources = []
        for path in graph.get_all_paths():
            resource = graph.get_resource(path)
            if resource:
                resources.append((path, resource))

        # Sort by path depth and name
        return sorted(resources, key=lambda x: (x[0].count("/"), x[0]))

    @staticmethod
    def _format_resource_skill(path: str, resource: Dict) -> str:
        """Format a single resource as a skill section"""
        parts = []

        # Resource heading
        resource_type = (resource.get("resource_type") or "Resource").title()
        parts.append(f"### {resource_type}: {path}\n")

        # Description
        if resource.get("description"):
            parts.append(f"{resource.get('description')}\n")

        # Schema
        if resource.get("schema"):
            parts.append("\n**Schema:**\n")
            parts.append("```json\n")
            parts.append(json.dumps(resource.get("schema"), indent=2))
            parts.append("\n```\n")

        # Properties from schema
        schema = resource.get("schema", {})
        if "properties" in schema:
            parts.append("\n**Properties:**\n")
            for prop_name, prop_def in schema.get("properties", {}).items():
                prop_type = prop_def.get("type", "unknown")
                prop_desc = prop_def.get("description", "")
                parts.append(f"- `{prop_name}` ({prop_type}): {prop_desc}\n")

        # Children
        children = resource.get("children", [])
        if children:
            parts.append("\n**Related Resources:**\n")
            for child in children:
                parts.append(f"- {child}\n")

        # Permissions
        permissions = resource.get("permissions", [])
        if permissions:
            parts.append(f"\n**Permissions:** {', '.join(permissions)}\n")

        parts.append("\n")

        return "".join(parts)

    @staticmethod
    def build_intention_specific_skill(
        graph: APIGraph, intention: Dict
    ) -> str:
        """
        Build skill markdown filtered by intention

        Returns:
            Filtered skill markdown based on agent intention
        """
        from root_app.agent.intention_parser import IntentionParser

        filtered_graph = IntentionParser.filter_graph_by_intention(graph, intention)
        return SkillBuilder.build_skill_markdown(filtered_graph)

"""Response formatting for agent queries"""

import json
from typing import Dict, Any


class ResponseFormatter:
    """Formats responses for agent HEAD requests"""

    @staticmethod
    def format_discovery_response(
        skill_markdown: str,
        intention: Dict = None,
        graph_summary: Dict = None,
    ) -> Dict[str, Any]:
        """
        Format a discovery response for agents

        Returns:
            Dictionary with skill content and metadata
        """
        return {
            "skill_description": skill_markdown,
            "intention": intention or {},
            "graph_summary": graph_summary or {},
            "format": "markdown",
        }

    @staticmethod
    def to_json(response_data: Dict) -> str:
        """Convert response to JSON string"""
        return json.dumps(response_data, indent=2)

    @staticmethod
    def to_markdown(response_data: Dict) -> str:
        """Convert response to markdown format"""
        markdown_parts = []

        if response_data.get("skill_description"):
            markdown_parts.append(response_data["skill_description"])

        if response_data.get("graph_summary"):
            summary = response_data["graph_summary"]
            markdown_parts.append("\n---\n\n## API Graph Summary\n\n")
            markdown_parts.append(f"- Total Endpoints: {summary.get('total_nodes', 0)}\n")
            markdown_parts.append(f"- Total APIs: {summary.get('total_apis', 0)}\n")

        return "".join(markdown_parts)

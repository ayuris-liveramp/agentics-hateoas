"""Tests for agent interface and skill generation"""

import pytest
import json
from root_app.agent.intention_parser import IntentionParser
from root_app.agent.skill_builder import SkillBuilder
from root_app.agent.response_formatter import ResponseFormatter


class TestIntentionParser:
    def test_parse_intention_header(self):
        """Test parsing Accept-Intention header"""
        header = "action=create, resource=order, details=full"
        intention = IntentionParser.parse_header(header)

        assert intention["action"] == "create"
        assert intention["resource"] == "order"
        assert intention["details"] == "full"

    def test_parse_intention_partial(self):
        """Test parsing partial intention header"""
        header = "action=read, resource=customer"
        intention = IntentionParser.parse_header(header)

        assert intention["action"] == "read"
        assert intention["resource"] == "customer"
        assert intention["details"] == "full"  # default

    def test_parse_intention_empty(self):
        """Test parsing empty intention header"""
        intention = IntentionParser.parse_header("")

        assert intention["action"] is None
        assert intention["resource"] is None
        assert intention["details"] == "full"

    def test_parse_intention_invalid_action(self):
        """Test parsing with invalid action"""
        header = "action=invalid, resource=order"
        intention = IntentionParser.parse_header(header)

        # Invalid action should be ignored
        assert intention["action"] is None
        assert intention["resource"] == "order"

    def test_filter_graph_by_intention(self, sample_api_graph):
        """Test filtering graph by intention"""
        intention = {"action": "read", "resource": "order", "details": "full"}
        filtered = IntentionParser.filter_graph_by_intention(sample_api_graph, intention)

        # Graph should still have some nodes
        assert len(filtered.get_all_paths()) > 0


class TestSkillBuilder:
    def test_build_skill_markdown_empty_graph(self):
        """Test building skill markdown with empty graph"""
        from root_app.crawler.graph_builder import APIGraph

        graph = APIGraph()
        markdown = SkillBuilder.build_skill_markdown(graph)

        assert "No APIs Discovered" in markdown

    def test_build_skill_markdown_with_graph(self, sample_api_graph):
        """Test building skill markdown with populated graph"""
        markdown = SkillBuilder.build_skill_markdown(sample_api_graph)

        assert "Available API Skills" in markdown
        assert "Test API" in markdown
        assert "Discovery Summary" in markdown

    def test_build_skill_markdown_includes_resources(self, sample_api_graph):
        """Test skill markdown includes discovered resources"""
        markdown = SkillBuilder.build_skill_markdown(sample_api_graph)

        assert "Available Resources" in markdown
        assert "/orders" in markdown
        assert "/customers" in markdown

    def test_build_skill_markdown_includes_summary(self, sample_api_graph):
        """Test skill markdown includes graph summary"""
        markdown = SkillBuilder.build_skill_markdown(sample_api_graph)

        assert "Total Resources:" in markdown
        assert "Container Resources:" in markdown
        assert "Leaf Resources:" in markdown

    def test_get_sorted_resources(self, sample_api_graph):
        """Test resources are sorted by path"""
        resources = SkillBuilder._get_sorted_resources(sample_api_graph)

        # Resources should be sorted
        paths = [r[0] for r in resources]
        assert paths == sorted(paths, key=lambda x: (x.count("/"), x))


class TestResponseFormatter:
    def test_format_discovery_response(self, sample_api_graph):
        """Test formatting discovery response"""
        skill_markdown = "# Test Skills\n\n## Resource 1"
        intention = {"action": "read"}
        summary = sample_api_graph.get_graph_summary()

        response = ResponseFormatter.format_discovery_response(
            skill_markdown=skill_markdown,
            intention=intention,
            graph_summary=summary,
        )

        assert response["skill_description"] == skill_markdown
        assert response["intention"] == intention
        assert "total_nodes" in response["graph_summary"]
        assert response["format"] == "markdown"

    def test_to_json(self):
        """Test converting response to JSON"""
        response_data = {
            "skill_description": "# Skills",
            "intention": {"action": "read"},
        }

        json_str = ResponseFormatter.to_json(response_data)
        parsed = json.loads(json_str)

        assert parsed["skill_description"] == "# Skills"
        assert parsed["intention"]["action"] == "read"

    def test_to_markdown(self, sample_api_graph):
        """Test converting response to markdown"""
        skill_markdown = "# Available Skills\n\n- Skill 1\n- Skill 2"
        summary = sample_api_graph.get_graph_summary()

        response_data = ResponseFormatter.format_discovery_response(
            skill_markdown=skill_markdown,
            graph_summary=summary,
        )

        markdown = ResponseFormatter.to_markdown(response_data)

        assert "Available Skills" in markdown
        assert "API Graph Summary" in markdown
        assert "Total Endpoints:" in markdown

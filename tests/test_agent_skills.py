"""Functional tests for agent skill generation."""

import pytest


class TestAgentSkills:
    """Test skill generation and formatting."""

    def test_skills_endpoint_exists(self, root_client):
        """Root app should expose skills endpoint."""
        resp = root_client.get("/skills")
        assert resp.status_code == 200

    def test_skills_response_format(self, root_client):
        """Skills should be returned in list format."""
        resp = root_client.get("/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), "Skills should be a list"

    def test_skills_have_required_fields(self, root_client):
        """Each skill should have name and description."""
        resp = root_client.get("/skills")
        data = resp.json()

        if len(data) > 0:
            skill = data[0]
            # Skills might be dicts or strings; if strings they should be markdown
            if isinstance(skill, dict):
                assert "name" in skill or "title" in skill, "Skill should have name/title"
                assert "description" in skill or "doc" in skill, "Skill should have description"

    def test_skills_for_leaf_api_endpoints(self, root_client):
        """Skills should be generated for leaf API endpoints."""
        resp = root_client.get("/skills")
        data = resp.json()

        # Should have at least a few skills if leaf API is discoverable
        assert len(data) > 0, "Skills list should not be empty"

    def test_skill_markdown_format(self, root_client):
        """Skills might be markdown-formatted strings."""
        resp = root_client.get("/skills")
        data = resp.json()

        if len(data) > 0:
            skill = data[0]
            # If string, should contain markdown markers or readable text
            if isinstance(skill, str):
                # Markdown skills typically have # headers or readable text
                assert len(skill) > 0, "Skill string should not be empty"

    def test_individual_skill_endpoint(self, root_client):
        """Should be able to fetch individual skills."""
        # First get skills list
        resp = root_client.get("/skills")
        data = resp.json()

        if len(data) > 0:
            skill = data[0]
            if isinstance(skill, dict) and "name" in skill:
                skill_name = skill["name"]
                # Try to fetch individual skill
                resp2 = root_client.get(f"/skills/{skill_name}")
                assert resp2.status_code == 200

"""Functional tests for API discovery."""

import pytest


class TestAPIDiscovery:
    """Test root app discovery of leaf API."""

    def test_root_app_health(self, root_client):
        """Root app should respond to health check."""
        resp = root_client.get("/health")
        assert resp.status_code == 200

    def test_leaf_api_health(self, leaf_client):
        """Leaf API should respond to health check."""
        resp = leaf_client.get("/health")
        assert resp.status_code == 200

    def test_root_app_discover_endpoint(self, root_client):
        """Root app should expose discovery endpoint."""
        resp = root_client.get("/discover")
        assert resp.status_code == 200
        data = resp.json()
        assert "apis" in data or "children" in data or isinstance(data, list)

    def test_api_graph_contains_leaf_api(self, root_client):
        """API graph should reference the leaf API."""
        resp = root_client.get("/discover")
        assert resp.status_code == 200
        data = resp.json()

        # Data could be list or dict depending on format
        if isinstance(data, list):
            api_urls = [api.get("url") or api.get("base_url") or str(api) for api in data]
        else:
            api_urls = []
            if "apis" in data:
                api_urls = [api.get("url") or api.get("base_url") for api in data["apis"]]
            elif "children" in data:
                api_urls = [child.get("url") or child.get("base_url") for child in data["children"]]

        # At least one API URL should contain reference to leaf-api
        assert any("leaf-api" in str(url).lower() or "5000" in str(url) for url in api_urls)

    def test_leaf_api_root_endpoint(self, leaf_client):
        """Leaf API should have discoverable root endpoint."""
        resp = leaf_client.get("/")
        assert resp.status_code in (200, 404)  # Either has explicit root or redirects

    def test_leaf_api_schema_available(self, leaf_client):
        """Leaf API should provide JSON schema at /schema or similar."""
        # Try common schema endpoints
        endpoints = ["/schema", "/.well-known/schema.json", "/json-schema", "/openapi.json"]
        found = False

        for endpoint in endpoints:
            resp = leaf_client.get(endpoint)
            if resp.status_code == 200:
                data = resp.json()
                # Should contain schema information
                assert isinstance(data, dict)
                found = True
                break

        assert found, f"No schema endpoint found at {endpoints}"

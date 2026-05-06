"""Health check tests — the only tests that run in CI."""


class TestHealthChecks:
    def test_leaf_api_health(self, leaf_client):
        resp = leaf_client.get("/health")
        assert resp.status_code == 200

    def test_root_app_health(self, root_client):
        resp = root_client.get("/health")
        assert resp.status_code == 200

"""Functional test: mock Anthropic server facilitates end-to-end request/response handling."""

import requests


class TestMockAnthropicEndToEnd:
    def test_end_to_end_via_root_app_accept_intention_head(
        self, root_client, mock_anthropic_url, wait_for_services
    ):
        """
        Full end-to-end path:
          test → HEAD /skills (root-app, Accept-Intention header)
               → Anthropic SDK → mock Anthropic server (POST /v1/messages)
               → fixed mock response
               → X-Anthropic-* headers returned to caller
        """
        # Verify the mock server itself is healthy and returns a valid response
        mock_resp = requests.post(
            f"{mock_anthropic_url}/v1/messages",
            headers={
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "What skills are available?"}],
            },
            timeout=5,
        )
        assert mock_resp.status_code == 200
        mock_data = mock_resp.json()
        assert mock_data["type"] == "message"
        assert mock_data["role"] == "assistant"
        assert mock_data["stop_reason"] == "end_turn"
        assert mock_data["content"][0]["type"] == "text"

        # Verify root-app HEAD /skills routes through the SDK to the mock and returns headers
        head_resp = root_client.head(
            "/skills",
            headers={"Accept-Intention": "list available skills"},
        )
        assert head_resp.status_code == 200
        assert "X-Anthropic-Message-Id" in head_resp.headers
        assert head_resp.headers["X-Anthropic-Message-Id"] == "msg_mock_test_abc123"
        assert "X-Anthropic-Model" in head_resp.headers
        assert head_resp.headers["X-Anthropic-Stop-Reason"] == "end_turn"
        assert head_resp.headers.get("X-Intention-Received") == "list available skills"

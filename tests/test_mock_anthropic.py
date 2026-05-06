"""Functional test: mock Anthropic server facilitates end-to-end request/response handling."""

import base64
import requests

SKILL_PROMPT = "create a new product and order it"


class TestMockAnthropicEndToEnd:
    def test_end_to_end_accept_intention_returns_skill_payload(
        self, root_client, mock_anthropic_url, wait_for_services
    ):
        """
        Full end-to-end path:
          test → HEAD / (root-app, Accept-Intention: create a new product and order it)
               → Anthropic SDK → mock Anthropic server (POST /v1/messages)
               → markdown skill payload (POST /products + POST /orders)
               → X-Skill-Payload header (base64) returned to caller
        """
        # Verify mock returns markdown skill for the specific prompt
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
                "messages": [{"role": "user", "content": SKILL_PROMPT}],
            },
            timeout=5,
        )
        assert mock_resp.status_code == 200
        mock_data = mock_resp.json()
        assert mock_data["type"] == "message"
        assert mock_data["role"] == "assistant"
        assert mock_data["stop_reason"] == "end_turn"
        skill_text = mock_data["content"][0]["text"]
        assert "POST /products" in skill_text
        assert "POST /orders" in skill_text

        # Verify root-app HEAD / routes through SDK to mock and surfaces the skill payload
        head_resp = root_client.head(
            "/",
            headers={"Accept-Intention": SKILL_PROMPT},
        )
        assert head_resp.status_code == 200
        assert "X-Skill-Payload" in head_resp.headers
        skill_payload = base64.b64decode(head_resp.headers["X-Skill-Payload"]).decode()
        assert "POST /products" in skill_payload
        assert "POST /orders" in skill_payload
        assert head_resp.headers["X-Anthropic-Message-Id"] == "msg_mock_test_abc123"
        assert head_resp.headers.get("X-Anthropic-Stop-Reason") == "end_turn"

"""Mock Anthropic API server for functional testing within docker-compose network."""
from flask import Flask, request, jsonify

app = Flask(__name__)

SKILL_PROMPT = "create a new product and order it"

SKILL_MARKDOWN = """\
# Skill: Create Product and Place Order

Use this skill to add a product to the catalogue and immediately place an order for it.

## Step 1 — Create a product

    POST /products
    Content-Type: application/json

    {
      "name": "Widget",
      "price": 9.99,
      "stock": 100
    }

A `201 Created` response includes the new product `id`.

## Step 2 — Place an order

    POST /orders
    Content-Type: application/json

    {
      "product_id": "<id from step 1>",
      "quantity": 1
    }

A `201 Created` response includes the full order record.
"""


@app.route("/v1/messages", methods=["POST"])
def create_message():
    api_key = request.headers.get("x-api-key", "")
    if not api_key:
        return jsonify({
            "type": "error",
            "error": {"type": "authentication_error", "message": "Missing x-api-key header"},
        }), 401

    anthropic_version = request.headers.get("anthropic-version", "")
    if not anthropic_version:
        return jsonify({
            "type": "error",
            "error": {"type": "invalid_request_error", "message": "Missing anthropic-version header"},
        }), 400

    body = request.get_json(force=True, silent=True) or {}
    model = body.get("model", "claude-sonnet-4-6")
    messages = body.get("messages", [])

    response_text = "Mock Anthropic response: intention acknowledged."
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str) and content.strip().lower() == SKILL_PROMPT:
            response_text = SKILL_MARKDOWN
            break

    return jsonify({
        "id": "msg_mock_test_abc123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": response_text}],
        "model": model,
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": len(response_text.split())},
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "mock-anthropic"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)

"""Mock Anthropic API server for functional testing within docker-compose network."""
from flask import Flask, request, jsonify

app = Flask(__name__)


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

    return jsonify({
        "id": "msg_mock_test_abc123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Mock Anthropic response: intention acknowledged."}],
        "model": model,
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 6},
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "mock-anthropic"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)

"""Root application factory"""

import os
from flask import Flask, jsonify
from root_app.config import config


def create_app(config_name: str = None) -> Flask:
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config.get(config_name, config["default"]))

    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    # Register blueprints (will be implemented in Phase 3 & 4)
    with app.app_context():
        from root_app.routes import health

        app.register_blueprint(health.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5001, debug=True)

"""Flask application factory and initialization"""

import os
from flask import Flask, jsonify
from leaf_api.config import config
from leaf_api.models import db
from leaf_api.auth.jwt_handler import JWTHandler


def create_app(config_name: str = None) -> Flask:
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config.get(config_name, config["default"]))

    # Initialize database
    db.init_app(app)

    # Initialize JWT handler
    app.jwt_handler = JWTHandler(
        public_key_path=app.config["JWT_PUBLIC_KEY_PATH"],
        private_key_path=app.config["JWT_PRIVATE_KEY_PATH"],
    )

    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    # Create database tables and register blueprints
    with app.app_context():
        db.create_all()

        # Import and register blueprints
        from leaf_api.resources import root, orders, customers, products

        app.register_blueprint(root.bp)
        app.register_blueprint(orders.bp)
        app.register_blueprint(customers.bp)
        app.register_blueprint(products.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

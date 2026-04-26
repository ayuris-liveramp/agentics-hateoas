"""Flask application factory and initialization"""

import os
import time
from flask import Flask, jsonify
from sqlalchemy.exc import OperationalError
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
        # Retry database connection with exponential backoff
        max_retries = 30
        retry_delay = 1  # Start with 1 second
        for attempt in range(max_retries):
            try:
                db.create_all()
                break
            except OperationalError as e:
                if attempt < max_retries - 1:
                    app.logger.warning(
                        f"Database connection attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    # Exponential backoff with cap at 5 seconds
                    retry_delay = min(retry_delay * 1.5, 5)
                else:
                    app.logger.error(f"Failed to connect to database after {max_retries} attempts")
                    raise

        # Import and register blueprints
        from leaf_api.resources import root, orders, customers, products
        from leaf_api.routes import health

        app.register_blueprint(health.bp)
        app.register_blueprint(root.bp)
        app.register_blueprint(orders.bp)
        app.register_blueprint(customers.bp)
        app.register_blueprint(products.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

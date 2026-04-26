"""Health check endpoints"""

from datetime import datetime
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from leaf_api.models import db

bp = Blueprint("health", __name__)


@bp.route("/health", methods=["GET"])
def health():
    """Liveness check endpoint - indicates the service is running"""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


@bp.route("/health/ready", methods=["GET"])
def health_ready():
    """Readiness check endpoint - indicates the service is ready to handle requests"""
    try:
        # Check database connectivity and schema
        with current_app.app_context():
            # Verify required tables exist by attempting to query them
            required_tables = ["customers", "products", "orders"]

            for table_name in required_tables:
                try:
                    db.session.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
                except Exception as e:
                    return jsonify({
                        "status": "not_ready",
                        "reason": f"Table '{table_name}' not found or inaccessible",
                        "timestamp": datetime.utcnow().isoformat()
                    }), 503

            db.session.commit()

        return jsonify({
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "not_ready",
            "reason": f"Database error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 503

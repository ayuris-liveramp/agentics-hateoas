"""WSGI entry point for production deployment"""

import os
from leaf_api.app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    app.run()

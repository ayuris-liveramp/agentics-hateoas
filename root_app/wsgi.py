"""WSGI entry point for root app production deployment"""

import os
from root_app.app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    app.run(port=5001)

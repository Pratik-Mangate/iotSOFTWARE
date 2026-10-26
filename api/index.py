import os
import sys
from urllib.parse import parse_qs

# Add parent directory to sys.path for Vercel serverless execution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import db
import model_service
from aap import app

# Ensure database schema is initialized on serverless container startup
try:
    db.init_db()
except Exception as e:
    print(f"[Vercel Init] db.init_db warning: {e}")

# Pre-load ONNX model into memory
try:
    model_service.load_model()
except Exception as e:
    print(f"[Vercel Init] model_service.load_model warning: {e}")


class VercelPathMiddleware:
    """WSGI middleware to ensure correct PATH_INFO under Vercel rewrites."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        params = parse_qs(query_string)

        if "path" in params and params["path"]:
            subpath = params["path"][0].strip("/")
            environ["PATH_INFO"] = f"/{subpath}" if subpath else "/"
        elif environ.get("HTTP_X_MATCHED_PATH"):
            environ["PATH_INFO"] = environ["HTTP_X_MATCHED_PATH"].split("?")[0]
        elif environ.get("PATH_INFO", "").startswith("/api/index"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)


# Wrap Flask's WSGI application with the middleware
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

if __name__ == "__main__":
    app.run()

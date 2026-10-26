import os
import sys

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
        # 1. Prefer HTTP_X_MATCHED_PATH which Vercel populates on rewrites
        matched = environ.get("HTTP_X_MATCHED_PATH")
        if matched:
            environ["PATH_INFO"] = matched.split("?")[0]
        else:
            # 2. If Vercel passed /api/index prefix in PATH_INFO, strip it
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith("/api/index"):
                remainder = path_info[len("/api/index"):]
                environ["PATH_INFO"] = remainder if remainder else "/"

        return self.wsgi_app(environ, start_response)


# Wrap Flask's WSGI application with the middleware
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

if __name__ == "__main__":
    app.run()

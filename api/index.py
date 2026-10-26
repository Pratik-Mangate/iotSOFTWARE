import os
import sys

# Add parent directory to sys.path for Vercel serverless execution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aap import app

# Vercel serverless function entrypoint
if __name__ == "__main__":
    app.run()

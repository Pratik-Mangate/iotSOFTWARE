"""
Configuration module for Skin Monitor Dashboard.
Centralizes all configurable settings with sensible defaults.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask settings
FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

# Environment detection
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

# Upload settings
if IS_VERCEL:
    UPLOAD_FOLDER = "/tmp/uploads"
    INSTANCE_DIR = "/tmp/instance"
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB payload ceiling on Vercel
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", 10)) * 1024 * 1024  # 10 MB default

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

# Model settings
ONNX_MODEL_PATH = os.environ.get(
    "ONNX_MODEL_PATH",
    os.path.join(BASE_DIR, "models", "skindisnet_model.onnx"),
)
PTH_MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    os.path.join(BASE_DIR, "models", "skindisnet_groupbalanced_best.pth"),
)
MODEL_PATH = ONNX_MODEL_PATH

# Database settings
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(INSTANCE_DIR, "history.db"),
)

# IoT Environmental Sensor Settings (Raspberry Pi 3 + DHT11 & Supabase PostgreSQL)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
SENSOR_API_TOKEN = os.environ.get("SENSOR_API_TOKEN", "").strip()
EXPECTED_DEVICE_ID = os.environ.get("EXPECTED_DEVICE_ID", "skin-monitor-pi").strip()
SENSOR_STALE_SECONDS = int(os.environ.get("SENSOR_STALE_SECONDS", 60))
SENSOR_HISTORY_LIMIT = int(os.environ.get("SENSOR_HISTORY_LIMIT", 100))


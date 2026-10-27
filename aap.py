"""
Skin Monitor Dashboard – Flask Application
===========================================
AI-based skin disease classification web app with image upload,
inference, and prediction history.

Entry point:  python aap.py
"""
import base64
import io
import json
import os
import uuid
import hmac
import math
from datetime import datetime, timezone

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from PIL import Image
from werkzeug.utils import secure_filename

import config
import db
import model_service
import clinical_protocols
import sensor_db

# ── Flask app ────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-skin-monitor-secret-key")
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER

os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)


@app.context_processor
def inject_global_context():
    """Make model status and metadata globally available across all templates."""
    return {
        "model_available": model_service.is_available(),
        "class_count": len(model_service.get_class_names()),
    }


# ── Helpers ──────────────────────────────────────────────────────────────
def _allowed_file(filename):
    """Check extension against the allow-list."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


def _save_upload(file_storage):
    """
    Validate, sanitise, and save an uploaded image.

    Returns (saved_filename, pil_image) or raises ValueError.
    """
    if file_storage is None or file_storage.filename == "":
        raise ValueError("No image file was selected.")

    orig_name = secure_filename(file_storage.filename)
    if not orig_name:
        raise ValueError("The filename is invalid.")

    if not _allowed_file(orig_name):
        raise ValueError(
            f"Unsupported file type. Allowed: {', '.join(sorted(config.ALLOWED_EXTENSIONS))}."
        )

    # Generate a unique filename to prevent collisions
    ext = orig_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(config.UPLOAD_FOLDER, unique_name)

    file_storage.save(save_path)

    # Validate that the file is actually a readable image
    try:
        img = Image.open(save_path)
        img.verify()  # check integrity
        img = Image.open(save_path)  # re-open after verify
    except Exception:
        os.remove(save_path)
        raise ValueError("The uploaded file is not a valid image or is corrupted.")

    # Reject empty / tiny files
    if os.path.getsize(save_path) < 100:
        os.remove(save_path)
        raise ValueError("The uploaded file appears to be empty or too small.")

    return unique_name, img


def _image_to_base64(pil_image):
    """Convert PIL image to compact base64 JPEG data URL for self-contained persistence."""
    try:
        buf = io.BytesIO()
        rgb_img = pil_image.convert("RGB")
        rgb_img.thumbnail((450, 450), Image.Resampling.LANCZOS)
        rgb_img.save(buf, format="JPEG", quality=82)
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception as exc:
        print(f"[_image_to_base64] Conversion warning: {exc}")
        return ""


# ── Routes ───────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/api/index")
@app.route("/api/index/")
def index():
    return render_template(
        "index.html",
        model_available=model_service.is_available(),
        recent_history=db.get_history()[:5],
        total_cases=len(db.get_history()),
        class_names=model_service.get_class_names(),
    )


@app.route("/debug-env")
def debug_env():
    data = {
        "PATH_INFO": request.environ.get("PATH_INFO"),
        "RAW_URI": request.environ.get("RAW_URI"),
        "REQUEST_URI": request.environ.get("REQUEST_URI"),
        "HTTP_X_MATCHED_PATH": request.environ.get("HTTP_X_MATCHED_PATH"),
        "HTTP_X_NOW_ROUTE_MATCHES": request.environ.get("HTTP_X_NOW_ROUTE_MATCHES"),
        "HTTP_X_FORWARDED_URI": request.environ.get("HTTP_X_FORWARDED_URI"),
        "headers": {k: v for k, v in request.headers.items() if "auth" not in k.lower() and "cookie" not in k.lower()}
    }
    return json.dumps(data, indent=2), 200, {"Content-Type": "application/json"}


@app.route("/analyze")
def analyze():
    """Image upload / camera capture page."""
    return render_template(
        "analyze.html",
        model_available=model_service.is_available(),
    )


@app.route("/predict", methods=["POST"])
def predict():
    """Accept image upload, run inference, return result page."""
    try:
        # Check both the standard file input and the mobile camera capture input
        file = request.files.get("skin_image")
        if not file or not file.filename:
            file = request.files.get("camera_image")
        filename, pil_image = _save_upload(file)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("analyze"))

    # If model is unavailable, still show the uploaded image
    if not model_service.is_available():
        flash(
            "AI model is currently unavailable. "
            + (model_service.get_error() or "Please place the model file in models/."),
            "warning",
        )
        return render_template(
            "result.html",
            image_file=filename,
            result=None,
            model_available=False,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

    # Run inference
    try:
        result = model_service.predict(pil_image)
    except Exception as exc:
        flash(f"Inference error: {exc}", "error")
        return render_template(
            "result.html",
            image_file=filename,
            result=None,
            model_available=True,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Generate persistent base64 thumbnail for self-contained image persistence
    b64_data = _image_to_base64(pil_image)

    # Persist to history with image_data
    record_id = db.save_prediction(
        image_file=filename,
        predicted=result["predicted"],
        confidence=result["confidence"],
        top3_json=json.dumps(result["top3"]),
        image_data=b64_data,
    )

    treatment_protocol = clinical_protocols.get_protocol(result["predicted"])

    return render_template(
        "result.html",
        record_id=record_id,
        image_file=filename,
        image_data=b64_data,
        result=result,
        treatment_protocol=treatment_protocol,
        model_available=True,
        timestamp=timestamp,
        all_protocols=clinical_protocols.PROTOCOLS,
    )


@app.route("/result/<record_id>")
def view_result(record_id):
    """View an archived diagnostic report with its full clinical protocol."""
    try:
        int_id = int(record_id)
        target = db.get_record(int_id)
    except (ValueError, TypeError):
        int_id = None
        target = None

    if not target and int_id is not None:
        for r in db.get_history():
            if r["id"] == int_id:
                target = r
                break

    if target:
        try:
            top3 = json.loads(target["top3"]) if target.get("top3") else []
        except Exception:
            top3 = []

        result = {
            "predicted": target["predicted"],
            "confidence": target["confidence"],
            "top3": top3,
        }
        treatment_protocol = clinical_protocols.get_protocol(target["predicted"])

        return render_template(
            "result.html",
            record_id=target["id"],
            image_file=target["image_file"],
            image_data=target.get("image_data"),
            result=result,
            treatment_protocol=treatment_protocol,
            model_available=True,
            timestamp=target["timestamp"],
            all_protocols=clinical_protocols.PROTOCOLS,
        )

    # Resilient fallback for serverless container rotation on Vercel:
    # Render result.html with client_lookup_id so client-side localStorage restores
    # the entire diagnostic case, photo, and prescription protocol instantly!
    return render_template(
        "result.html",
        client_lookup_id=record_id,
        record_id=record_id,
        result=None,
        model_available=True,
        timestamp="",
        all_protocols=clinical_protocols.PROTOCOLS,
    )


@app.route("/history")
def history():
    """Show full prediction history."""
    records = db.get_history()
    # parse top3 JSON for template
    for r in records:
        try:
            r["top3_parsed"] = json.loads(r.get("top3") or "[]")
        except Exception:
            r["top3_parsed"] = []
    return render_template(
        "history.html",
        records=records,
        all_protocols=clinical_protocols.PROTOCOLS,
    )


@app.route("/history/clear", methods=["POST"])
def clear_history():
    """Delete all history records and uploaded images."""
    db.clear_history()
    # Remove uploaded images
    for f in os.listdir(config.UPLOAD_FOLDER):
        fpath = os.path.join(config.UPLOAD_FOLDER, f)
        try:
            if os.path.isfile(fpath):
                os.remove(fpath)
        except OSError:
            pass
    flash("History and uploaded images cleared.", "success")
    return redirect(url_for("history"))


@app.route("/about")
def about():
    """Project information page."""
    return render_template(
        "about.html",
        model_available=model_service.is_available(),
        class_names=model_service.get_class_names(),
    )


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve an uploaded image safely."""
    safe = secure_filename(filename)
    return send_from_directory(config.UPLOAD_FOLDER, safe)


# ── IoT Environmental Sensor Endpoints (Raspberry Pi 3 + DHT11) ───────────

@app.route("/api/sensor", methods=["POST"])
def post_sensor_reading():
    """
    Accept authenticated environmental sensor readings from Raspberry Pi 3.
    Persists data to Supabase PostgreSQL with server-generated UTC timestamp.
    """
    # 1. Verify server configuration
    if not config.SENSOR_API_TOKEN:
        return jsonify({
            "status": "error",
            "message": "Server configuration missing: SENSOR_API_TOKEN is not set.",
        }), 503

    # 2. Authenticate request using constant-time comparison
    auth_header = request.headers.get("X-API-Token", "")
    if not auth_header or not hmac.compare_digest(auth_header.encode("utf-8"), config.SENSOR_API_TOKEN.encode("utf-8")):
        return jsonify({
            "status": "error",
            "message": "Unauthorized: Invalid or missing X-API-Token header.",
        }), 401

    # 3. Payload size and type enforcement
    if request.content_length and request.content_length > 16384:
        return jsonify({
            "status": "error",
            "message": "Payload too large (maximum 16 KB).",
        }), 400

    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Content-Type must be application/json.",
        }), 400

    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Malformed JSON payload.",
        }), 400

    # 4. Required fields check
    for field in ("device_id", "temperature", "humidity"):
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"Missing required field: '{field}'.",
            }), 400

    device_id = data["device_id"]
    temp = data["temperature"]
    hum = data["humidity"]

    # 5. Validate device_id
    if not isinstance(device_id, str) or not device_id.strip():
        return jsonify({
            "status": "error",
            "message": "Field 'device_id' must be a non-empty string.",
        }), 400

    if config.EXPECTED_DEVICE_ID and device_id.strip() != config.EXPECTED_DEVICE_ID:
        return jsonify({
            "status": "error",
            "message": f"Unauthorized device: expected '{config.EXPECTED_DEVICE_ID}', received '{device_id}'.",
        }), 400

    # 6. Validate temperature & humidity numeric types (strictly rejecting booleans, NaN, Inf)
    if isinstance(temp, bool) or not isinstance(temp, (int, float)):
        return jsonify({
            "status": "error",
            "message": "Field 'temperature' must be a numeric value.",
        }), 400

    if isinstance(hum, bool) or not isinstance(hum, (int, float)):
        return jsonify({
            "status": "error",
            "message": "Field 'humidity' must be a numeric value.",
        }), 400

    if math.isnan(temp) or math.isinf(temp) or math.isnan(hum) or math.isinf(hum):
        return jsonify({
            "status": "error",
            "message": "Sensor readings must be finite numeric values (no NaN or Infinity).",
        }), 400

    # 7. Physical range validation
    # Ambient human/clinical environment: -40°C to 80°C
    if not (-40.0 <= temp <= 80.0):
        return jsonify({
            "status": "error",
            "message": f"Temperature value {temp}°C is out of physically reasonable range (-40°C to 80°C).",
        }), 400

    # Relative humidity: 0% to 100%
    if not (0.0 <= hum <= 100.0):
        return jsonify({
            "status": "error",
            "message": f"Humidity value {hum}% is out of valid range (0% to 100%).",
        }), 400

    # 8. Check persistent database configuration
    if not sensor_db.is_configured():
        return jsonify({
            "status": "error",
            "message": "Server database unconfigured: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing.",
        }), 503

    # 9. Server-generated UTC timestamp
    recorded_at = datetime.now(timezone.utc).isoformat()

    # 10. Persist to Supabase PostgreSQL
    try:
        record = sensor_db.insert_reading(
            device_id=device_id.strip(),
            temperature=float(temp),
            humidity=float(hum),
            recorded_at=recorded_at,
        )
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": "Failed to persist sensor reading to database.",
        }), 502

    return jsonify({
        "status": "success",
        "message": "Sensor reading recorded successfully.",
        "data": {
            "device_id": device_id.strip(),
            "temperature": round(float(temp), 2),
            "humidity": round(float(hum), 2),
            "recorded_at": recorded_at,
        },
    }), 201


@app.route("/api/sensor/latest", methods=["GET"])
def get_sensor_latest():
    """
    Return the latest stored environmental sensor telemetry.
    Computes freshness status (online, stale, offline, waiting_for_sensor).
    Safe for public dashboard polling (exposes no secrets).
    """
    if not sensor_db.is_configured():
        return jsonify({
            "status": "unconfigured",
            "device_id": config.EXPECTED_DEVICE_ID,
            "temperature": None,
            "humidity": None,
            "recorded_at": None,
            "age_seconds": None,
            "is_stale": True,
            "message": "Supabase environmental database credentials are not configured.",
        }), 200

    reading = sensor_db.get_latest_reading(config.EXPECTED_DEVICE_ID)

    if not reading:
        return jsonify({
            "status": "waiting_for_sensor",
            "device_id": config.EXPECTED_DEVICE_ID,
            "temperature": None,
            "humidity": None,
            "recorded_at": None,
            "age_seconds": None,
            "is_stale": True,
            "message": "Waiting for sensor telemetry from Raspberry Pi 3...",
        }), 200

    # Calculate data freshness
    age_seconds = None
    is_stale = True
    status = "offline"
    rec_time_str = reading.get("recorded_at")

    if rec_time_str:
        try:
            # Handle ISO timestamps with Z or timezone offset
            ts_clean = rec_time_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_seconds = max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))

            if age_seconds <= config.SENSOR_STALE_SECONDS:
                status = "online"
                is_stale = False
                msg = "Sensor online and actively transmitting."
            elif age_seconds <= 300:
                status = "stale"
                is_stale = True
                msg = f"Sensor telemetry is stale (last received {age_seconds}s ago)."
            else:
                status = "offline"
                is_stale = True
                msg = f"Raspberry Pi appears offline (last seen {age_seconds}s ago)."
        except Exception:
            status = "stale"
            is_stale = True
            msg = "Could not parse sensor timestamp."
    else:
        msg = "Sensor record has no timestamp."

    return jsonify({
        "status": status,
        "device_id": reading.get("device_id", config.EXPECTED_DEVICE_ID),
        "temperature": reading.get("temperature"),
        "humidity": reading.get("humidity"),
        "recorded_at": rec_time_str,
        "age_seconds": age_seconds,
        "is_stale": is_stale,
        "message": msg,
    }), 200


@app.route("/api/sensor/history", methods=["GET"])
def get_sensor_history():
    """
    Return recent environmental history (last 24 hours, capped at limit).
    """
    if not sensor_db.is_configured():
        return jsonify({
            "status": "unconfigured",
            "count": 0,
            "readings": [],
            "message": "Supabase environmental database credentials are not configured.",
        }), 200

    hours = request.args.get("hours", default=24, type=int)
    limit = request.args.get("limit", default=100, type=int)

    records = sensor_db.get_history(
        device_id=config.EXPECTED_DEVICE_ID,
        hours=min(max(1, hours), 72),
        limit=min(max(1, limit), config.SENSOR_HISTORY_LIMIT),
    )

    clean_records = []
    for r in records:
        clean_records.append({
            "temperature": r.get("temperature"),
            "humidity": r.get("humidity"),
            "recorded_at": r.get("recorded_at"),
        })

    return jsonify({
        "status": "success",
        "device_id": config.EXPECTED_DEVICE_ID,
        "count": len(clean_records),
        "readings": clean_records,
    }), 200


# ── Error handlers ───────────────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(413)
def too_large(e):
    max_mb = config.MAX_CONTENT_LENGTH // (1024 * 1024)
    flash(f"File too large. Maximum upload size is {max_mb} MB.", "error")
    return redirect(url_for("analyze"))


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Internal server error."), 500


def _get_local_ip():
    """Detect the local Wi-Fi / LAN IP address."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ── Startup ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.init_db()
    model_service.load_model()
    local_ip = _get_local_ip()

    print("\n" + "=" * 60)
    print("  Skin Monitor Dashboard")
    print("=" * 60)
    print(f"  Laptop URL : http://127.0.0.1:{config.FLASK_PORT}")
    print(f"  Phone URL  : http://{local_ip}:{config.FLASK_PORT}  (Connect phone to same Wi-Fi)")
    print()
    if model_service.is_available():
        print("  [OK] AI model loaded successfully.")
    else:
        print("  [!]  AI model not loaded yet.")
        err = model_service.get_error() or "Place skindisnet_model.onnx in models/ directory."
        for line in err.split("\n"):
            print(f"       {line}")
    print("=" * 60 + "\n")

    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )

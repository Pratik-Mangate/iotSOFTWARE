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
from datetime import datetime, timezone

from flask import (
    Flask,
    flash,
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

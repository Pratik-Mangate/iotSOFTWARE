"""
Tests for the Skin Monitor Dashboard Flask application.

Run with:   python -m pytest tests/ -v
"""
import io
import json
import os
import sys
import tempfile
import shutil

import pytest

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image

import config


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_dirs(tmp_path, monkeypatch):
    """
    Redirect uploads and database to temp dirs so tests
    never pollute the real project.
    """
    upload_dir = str(tmp_path / "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    db_path = str(tmp_path / "history.db")

    monkeypatch.setattr(config, "UPLOAD_FOLDER", upload_dir)
    monkeypatch.setattr(config, "DATABASE_PATH", db_path)
    monkeypatch.setattr(config, "INSTANCE_DIR", str(tmp_path))


@pytest.fixture
def app():
    """Create and configure the Flask test app."""
    import aap
    import db as db_module

    aap.app.config["TESTING"] = True
    aap.app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER

    db_module.init_db()

    yield aap.app


@pytest.fixture
def client(app):
    return app.test_client()


def _make_image(fmt="JPEG", size=(100, 100)):
    """Return BytesIO containing a valid image."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(128, 64, 32))
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf


# ── Dashboard ────────────────────────────────────────────────────────────

def test_dashboard_get(client):
    """GET / should return 200."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Skin Monitor Dashboard" in resp.data


# ── Analyze page ─────────────────────────────────────────────────────────

def test_analyze_get(client):
    """GET /analyze should return 200."""
    resp = client.get("/analyze")
    assert resp.status_code == 200
    assert b"Analyze Skin Image" in resp.data


# ── Upload / Predict ─────────────────────────────────────────────────────

def test_predict_valid_image(client):
    """POST /predict with a valid JPEG should succeed (redirect or 200)."""
    data = {"skin_image": (_make_image(), "test_skin.jpg")}
    resp = client.post("/predict", data=data, content_type="multipart/form-data")
    # Either renders result.html or redirects
    assert resp.status_code in (200, 302)


def test_predict_missing_file(client):
    """POST /predict with no file should redirect with error flash."""
    resp = client.post("/predict", data={}, content_type="multipart/form-data")
    assert resp.status_code == 302  # redirect to /analyze


def test_predict_empty_filename(client):
    """POST /predict with empty filename should redirect with error."""
    data = {"skin_image": (io.BytesIO(b""), "")}
    resp = client.post("/predict", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302


def test_predict_unsupported_type(client):
    """POST /predict with a .txt file should reject."""
    data = {"skin_image": (io.BytesIO(b"not an image"), "test.txt")}
    resp = client.post("/predict", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302


def test_predict_invalid_image_content(client):
    """POST /predict with .jpg extension but garbage content should reject."""
    data = {"skin_image": (io.BytesIO(b"garbage data 1234"), "fake.jpg")}
    resp = client.post("/predict", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302


def test_predict_png_image(client):
    """POST /predict with a valid PNG should succeed."""
    data = {"skin_image": (_make_image(fmt="PNG"), "skin.png")}
    resp = client.post("/predict", data=data, content_type="multipart/form-data")
    assert resp.status_code in (200, 302)


# ── History ──────────────────────────────────────────────────────────────

def test_history_get_empty(client):
    """GET /history should return 200 with empty state."""
    resp = client.get("/history")
    assert resp.status_code == 200


def test_history_after_prediction(client):
    """After a prediction, history should contain a record."""
    import db as db_module
    db_module.save_prediction("test.jpg", "Eczema", 0.85, "[]")
    resp = client.get("/history")
    assert resp.status_code == 200
    assert b"Eczema" in resp.data


def test_history_clear(client):
    """POST /history/clear should remove records."""
    import db as db_module
    db_module.save_prediction("test.jpg", "Scabies", 0.5, "[]")
    resp = client.post("/history/clear", follow_redirects=True)
    assert resp.status_code == 200
    records = db_module.get_history()
    assert len(records) == 0


# ── About ────────────────────────────────────────────────────────────────

def test_about_get(client):
    """GET /about should return 200."""
    resp = client.get("/about")
    assert resp.status_code == 200
    assert b"About This Project" in resp.data


# ── Error handling ───────────────────────────────────────────────────────

def test_404(client):
    """Requesting a non-existent page should return 404."""
    resp = client.get("/nonexistent-route")
    assert resp.status_code == 404


# ── Model availability ──────────────────────────────────────────────────

def test_model_unavailable_doesnt_crash(client):
    """Dashboard and analyze should work even without a model loaded."""
    for endpoint in ["/", "/analyze", "/about"]:
        resp = client.get(endpoint)
        assert resp.status_code == 200


# ── Oversized upload ────────────────────────────────────────────────────

def test_oversized_upload(client, app):
    """Uploading a file larger than MAX_CONTENT_LENGTH should be rejected."""
    app.config["MAX_CONTENT_LENGTH"] = 1024  # 1 KB for test
    big_data = b"x" * 2048
    data = {"skin_image": (io.BytesIO(big_data), "big.jpg")}
    resp = client.post("/predict", data=data, content_type="multipart/form-data")
    assert resp.status_code in (302, 413)


# ── Upload filename security ────────────────────────────────────────────

def test_path_traversal_filename(client):
    """A malicious filename with path traversal should be sanitised."""
    data = {"skin_image": (_make_image(), "../../../etc/passwd.jpg")}
    resp = client.post("/predict", data=data, content_type="multipart/form-data")
    # Should not crash or expose files
    assert resp.status_code in (200, 302)


# ── Camera capture input fallback ───────────────────────────────────────

def test_predict_camera_image_fallback(client):
    """POST /predict with camera_image field should succeed."""
    data = {"camera_image": (_make_image(), "phone_photo.jpg")}
    resp = client.post("/predict", data=data, content_type="multipart/form-data")
    assert resp.status_code in (200, 302)


# ── Clinical treatment protocol tests ───────────────────────────────────

def test_clinical_protocols_coverage():
    """All 6 target diseases must have full clinical protocols."""
    import clinical_protocols
    classes = [
        "Atopic Dermatitis",
        "Contact Dermatitis",
        "Eczema",
        "Scabies",
        "Seborrheic Dermatitis",
        "Tinea Corporis"
    ]
    for c in classes:
        proto = clinical_protocols.get_protocol(c)
        assert proto is not None, f"Missing protocol for {c}"
        assert len(proto["rx_first_line"]) > 0
        assert len(proto["non_pharma_measures"]) > 0
        assert len(proto["contraindications"]) > 0
        assert len(proto["urgent_referral"]) > 0


def test_view_result_with_protocol(client):
    """GET /result/<id> should render assessment report and Rx guidance."""
    import db as db_module
    # Create test image in upload folder
    test_img = os.path.join(config.UPLOAD_FOLDER, "test_scabies.jpg")
    img = Image.new("RGB", (224, 224), color="red")
    img.save(test_img, "JPEG")

    db_module.save_prediction("test_scabies.jpg", "Scabies", 0.88, json.dumps([{"class": "Scabies", "confidence": 0.88}]))
    records = db_module.get_history()
    case_id = records[0]["id"]

    resp = client.get(f"/result/{case_id}")
    assert resp.status_code == 200
    assert b"Diagnostic Assessment Report" in resp.data
    assert b"Treatment Protocol &amp; Prescription Guidance: Scabies Infestation" in resp.data
    assert b"Permethrin 5% Dermal Cream" in resp.data
    assert b"Simultaneous Household Treatment" in resp.data


def test_view_result_client_fallback_when_db_missing(client):
    """GET /result/<nonexistent_id> should not crash or redirect, but provide client restoration container."""
    resp = client.get("/result/99999")
    assert resp.status_code == 200
    assert b"client-restoration-area" in resp.data
    assert b'data-lookup-id="99999"' in resp.data
    assert b"all-clinical-protocols" in resp.data


def test_history_embeds_server_payload(client):
    """GET /history should render server-records-payload script for client hydration."""
    import db as db_module
    db_module.save_prediction(
        "test.jpg",
        "Eczema",
        0.91,
        json.dumps([{"class": "Eczema", "confidence": 0.91}]),
        image_data="data:image/jpeg;base64,mockbase64data"
    )
    resp = client.get("/history")
    assert resp.status_code == 200
    assert b"server-records-payload" in resp.data
    assert b"data:image/jpeg;base64,mockbase64data" in resp.data
    assert b"case-thumb" in resp.data



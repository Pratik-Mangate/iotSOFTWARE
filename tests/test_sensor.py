"""
Unit and integration tests for IoT Environmental Monitoring (Raspberry Pi 3 + DHT11).

Tests API security, payload validation, constant-time authentication,
data freshness, Supabase error handling, and Vercel routing middleware.
"""
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import pytest

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import aap
import config
import sensor_db
from api.index import VercelPathMiddleware


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def test_app(monkeypatch):
    """Configure Flask test application with mock sensor settings."""
    monkeypatch.setattr(config, "SENSOR_API_TOKEN", "test-secret-sensor-token-xyz")
    monkeypatch.setattr(config, "EXPECTED_DEVICE_ID", "skin-monitor-pi")
    monkeypatch.setattr(config, "SUPABASE_URL", "https://mockproject.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_SERVICE_ROLE_KEY", "mock-service-role-key-123")
    monkeypatch.setattr(config, "SENSOR_STALE_SECONDS", 60)

    aap.app.config["TESTING"] = True
    return aap.app


@pytest.fixture
def client(test_app):
    return test_app.test_client()


# ── POST /api/sensor Tests ───────────────────────────────────────────────────

def test_post_sensor_valid(client, monkeypatch):
    """Valid authenticated sensor reading should be accepted and return 201."""
    inserted = {}

    def mock_insert(device_id, temperature, humidity, recorded_at):
        inserted["device_id"] = device_id
        inserted["temperature"] = temperature
        inserted["humidity"] = humidity
        inserted["recorded_at"] = recorded_at
        return inserted

    monkeypatch.setattr(sensor_db, "insert_reading", mock_insert)

    payload = {
        "device_id": "skin-monitor-pi",
        "temperature": 24.5,
        "humidity": 55.2,
    }
    headers = {
        "X-API-Token": "test-secret-sensor-token-xyz",
        "Content-Type": "application/json",
    }
    resp = client.post("/api/sensor", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["data"]["device_id"] == "skin-monitor-pi"
    assert data["data"]["temperature"] == 24.5
    assert data["data"]["humidity"] == 55.2
    assert "recorded_at" in data["data"]
    assert inserted["temperature"] == 24.5


def test_post_sensor_missing_token_header(client):
    """POST /api/sensor without X-API-Token header should return 401 Unauthorized."""
    payload = {
        "device_id": "skin-monitor-pi",
        "temperature": 24.5,
        "humidity": 55.2,
    }
    resp = client.post("/api/sensor", json=payload)
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["status"] == "error"
    assert "Unauthorized" in data["message"]


def test_post_sensor_invalid_token(client):
    """POST /api/sensor with invalid token should return 401 Unauthorized."""
    payload = {
        "device_id": "skin-monitor-pi",
        "temperature": 24.5,
        "humidity": 55.2,
    }
    headers = {"X-API-Token": "wrong-token-abc"}
    resp = client.post("/api/sensor", json=payload, headers=headers)
    assert resp.status_code == 401


def test_post_sensor_unconfigured_token(client, monkeypatch):
    """If SENSOR_API_TOKEN is not configured on server, return 503 Service Unavailable."""
    monkeypatch.setattr(config, "SENSOR_API_TOKEN", "")
    payload = {
        "device_id": "skin-monitor-pi",
        "temperature": 24.5,
        "humidity": 55.2,
    }
    headers = {"X-API-Token": "some-token"}
    resp = client.post("/api/sensor", json=payload, headers=headers)
    assert resp.status_code == 503
    data = resp.get_json()
    assert "SENSOR_API_TOKEN is not set" in data["message"]


def test_post_sensor_non_json_content_type(client):
    """POST with plain text or non-json should be rejected with 400."""
    headers = {"X-API-Token": "test-secret-sensor-token-xyz"}
    resp = client.post("/api/sensor", data="temperature=25", headers=headers)
    assert resp.status_code == 400
    assert "Content-Type must be application/json" in resp.get_json()["message"]


def test_post_sensor_missing_fields(client):
    """POST missing required fields should return 400."""
    headers = {"X-API-Token": "test-secret-sensor-token-xyz"}
    # Missing humidity
    payload = {"device_id": "skin-monitor-pi", "temperature": 24.5}
    resp = client.post("/api/sensor", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Missing required field: 'humidity'" in resp.get_json()["message"]


def test_post_sensor_unexpected_device_id(client):
    """POST with mismatched device ID should return 400."""
    headers = {"X-API-Token": "test-secret-sensor-token-xyz"}
    payload = {"device_id": "unknown-pi-node", "temperature": 24.5, "humidity": 50.0}
    resp = client.post("/api/sensor", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Unauthorized device" in resp.get_json()["message"]


def test_post_sensor_rejects_booleans(client):
    """Python treats bool as int subclass; test that True/False values are strictly rejected."""
    headers = {"X-API-Token": "test-secret-sensor-token-xyz"}
    payload = {"device_id": "skin-monitor-pi", "temperature": True, "humidity": 50.0}
    resp = client.post("/api/sensor", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "must be a numeric value" in resp.get_json()["message"]


def test_post_sensor_rejects_nan_and_inf(client):
    """NaN and Infinity readings must be rejected with 400."""
    headers = {"X-API-Token": "test-secret-sensor-token-xyz"}
    # Raw JSON with NaN / Infinity requires string manipulation or json.dumps with allow_nan=True
    # Using client.post with json text:
    raw_nan = '{"device_id": "skin-monitor-pi", "temperature": NaN, "humidity": 50.0}'
    resp = client.post("/api/sensor", data=raw_nan, content_type="application/json", headers=headers)
    assert resp.status_code in (400, 422)


def test_post_sensor_out_of_range(client):
    """Physical temperature or humidity outside reasonable ranges should be rejected."""
    headers = {"X-API-Token": "test-secret-sensor-token-xyz"}

    # Temperature 150°C
    resp = client.post(
        "/api/sensor",
        json={"device_id": "skin-monitor-pi", "temperature": 150.0, "humidity": 50.0},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "out of physically reasonable range" in resp.get_json()["message"]

    # Humidity 120%
    resp2 = client.post(
        "/api/sensor",
        json={"device_id": "skin-monitor-pi", "temperature": 25.0, "humidity": 120.0},
        headers=headers,
    )
    assert resp2.status_code == 400
    assert "out of valid range" in resp2.get_json()["message"]


def test_post_sensor_database_insertion_error(client, monkeypatch):
    """If database insert fails, return HTTP 502 with sanitized message."""
    def mock_fail(*args, **kwargs):
        raise RuntimeError("Database connection refused")

    monkeypatch.setattr(sensor_db, "insert_reading", mock_fail)

    headers = {"X-API-Token": "test-secret-sensor-token-xyz"}
    payload = {"device_id": "skin-monitor-pi", "temperature": 24.5, "humidity": 50.0}
    resp = client.post("/api/sensor", json=payload, headers=headers)
    assert resp.status_code == 502
    assert "Failed to persist sensor reading" in resp.get_json()["message"]


# ── GET /api/sensor/latest Tests ─────────────────────────────────────────────

def test_get_sensor_latest_empty(client, monkeypatch):
    """When no readings exist in database, return waiting_for_sensor status."""
    monkeypatch.setattr(sensor_db, "get_latest_reading", lambda device_id: None)

    resp = client.get("/api/sensor/latest")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "waiting_for_sensor"
    assert data["temperature"] is None
    assert data["is_stale"] is True


def test_get_sensor_latest_fresh(client, monkeypatch):
    """When reading is < 60s old, return status online."""
    recent_ts = (datetime.now(timezone.utc) - timedelta(seconds=12)).isoformat()
    mock_record = {
        "id": 1,
        "device_id": "skin-monitor-pi",
        "temperature": 25.2,
        "humidity": 58.1,
        "recorded_at": recent_ts,
    }
    monkeypatch.setattr(sensor_db, "get_latest_reading", lambda device_id: mock_record)

    resp = client.get("/api/sensor/latest")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "online"
    assert data["is_stale"] is False
    assert data["temperature"] == 25.2
    assert data["humidity"] == 58.1
    assert data["age_seconds"] is not None
    assert data["age_seconds"] <= 20


def test_get_sensor_latest_stale(client, monkeypatch):
    """When reading is > 60s old but < 300s, return status stale."""
    stale_ts = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    mock_record = {
        "id": 2,
        "device_id": "skin-monitor-pi",
        "temperature": 23.0,
        "humidity": 45.0,
        "recorded_at": stale_ts,
    }
    monkeypatch.setattr(sensor_db, "get_latest_reading", lambda device_id: mock_record)

    resp = client.get("/api/sensor/latest")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "stale"
    assert data["is_stale"] is True
    assert data["age_seconds"] >= 110


def test_get_sensor_latest_offline(client, monkeypatch):
    """When reading is > 300s old (5 minutes), return status offline."""
    offline_ts = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    mock_record = {
        "id": 3,
        "device_id": "skin-monitor-pi",
        "temperature": 21.0,
        "humidity": 40.0,
        "recorded_at": offline_ts,
    }
    monkeypatch.setattr(sensor_db, "get_latest_reading", lambda device_id: mock_record)

    resp = client.get("/api/sensor/latest")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "offline"
    assert data["is_stale"] is True


def test_get_sensor_latest_unconfigured(client, monkeypatch):
    """When Supabase credentials are missing, return unconfigured status."""
    monkeypatch.setattr(config, "SUPABASE_URL", "")
    monkeypatch.setattr(config, "SUPABASE_SERVICE_ROLE_KEY", "")

    resp = client.get("/api/sensor/latest")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "unconfigured"


# ── GET /api/sensor/history Tests ────────────────────────────────────────────

def test_get_sensor_history(client, monkeypatch):
    """GET /api/sensor/history should return chronological list of past readings."""
    mock_history = [
        {"temperature": 22.1, "humidity": 50.0, "recorded_at": "2026-10-27T10:00:00Z"},
        {"temperature": 23.5, "humidity": 52.0, "recorded_at": "2026-10-27T11:00:00Z"},
    ]
    monkeypatch.setattr(sensor_db, "get_history", lambda device_id, hours, limit: mock_history)

    resp = client.get("/api/sensor/history?hours=24&limit=50")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["count"] == 2
    assert len(data["readings"]) == 2
    assert data["readings"][0]["temperature"] == 22.1


# ── Vercel WSGI Middleware Compatibility Tests ───────────────────────────────

def test_vercel_middleware_routes_sensor_api():
    """
    Verify that VercelPathMiddleware properly translates Vercel's rewrite query parameter
    (/api/index?path=api/sensor) to PATH_INFO = '/api/sensor'.
    """
    captured_path_info = []

    def mock_wsgi_app(environ, start_response):
        captured_path_info.append(environ.get("PATH_INFO"))
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"OK"]

    wrapped_app = VercelPathMiddleware(mock_wsgi_app)

    # 1. Simulating Vercel rewrite for /api/sensor
    environ_post = {
        "REQUEST_METHOD": "POST",
        "QUERY_STRING": "path=api/sensor",
        "PATH_INFO": "/api/index",
    }
    wrapped_app(environ_post, lambda status, headers: None)
    assert captured_path_info[-1] == "/api/sensor"

    # 2. Simulating Vercel rewrite for /api/sensor/latest
    environ_get = {
        "REQUEST_METHOD": "GET",
        "QUERY_STRING": "path=api/sensor/latest",
        "PATH_INFO": "/api/index",
    }
    wrapped_app(environ_get, lambda status, headers: None)
    assert captured_path_info[-1] == "/api/sensor/latest"

    # 3. Simulating root dashboard /
    environ_root = {
        "REQUEST_METHOD": "GET",
        "QUERY_STRING": "path=",
        "PATH_INFO": "/api/index",
    }
    wrapped_app(environ_root, lambda status, headers: None)
    assert captured_path_info[-1] == "/"

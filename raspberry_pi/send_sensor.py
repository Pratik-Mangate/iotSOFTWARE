#!/usr/bin/env python3
"""
DermaScan IoT — Raspberry Pi 3 + DHT11 Environmental Telemetry Sender
=====================================================================

Monitors ambient clinical examination room temperature and humidity,
validating real sensor measurements and transmitting authenticated telemetry
to the deployed DermaScan cloud backend on Vercel over HTTPS.

Wiring Guide (DHT11 3-pin module -> Raspberry Pi 3 GPIO):
---------------------------------------------------------
  DHT11 Pin 1 (VCC / +)   --> Raspberry Pi Physical Pin 1 (3.3V DC Power)
  DHT11 Pin 2 (DATA / OUT)--> Raspberry Pi Physical Pin 7 (GPIO4 / BCM 4)
  DHT11 Pin 3 (GND / -)   --> Raspberry Pi Physical Pin 6 (Ground)

Requirements on Raspberry Pi OS:
--------------------------------
  sudo apt-get update
  sudo apt-get install -y python3-pip python3-venv libgpiod2
  python3 -m venv .venv
  source .venv/bin/activate
  pip install adafruit-circuitpython-dht requests python-dotenv

Usage:
------
  export SENSOR_API_TOKEN="your_secure_api_token"
  python send_sensor.py
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
import urllib.error
import urllib.request

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DermaSensorSender")

# Optional dotenv support if installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Hardware Adafruit CircuitPython DHT import check
DHT_AVAILABLE = False
try:
    import board
    import adafruit_dht
    DHT_AVAILABLE = True
except (ImportError, NotImplementedError) as exc:
    logger.warning(
        f"CircuitPython DHT hardware library not available on this platform ({exc}). "
        "Hardware readings require Raspberry Pi OS with 'adafruit-circuitpython-dht' and 'libgpiod2'."
    )

# ── Configuration (Loaded from Environment Variables) ──────────────────────
SERVER_URL = os.environ.get(
    "SERVER_URL",
    "https://iot-software.vercel.app/api/sensor",
).strip()

SENSOR_API_TOKEN = os.environ.get("SENSOR_API_TOKEN", "").strip()
DEVICE_ID = os.environ.get("DEVICE_ID", "skin-monitor-pi").strip()
INTERVAL_SECONDS = int(os.environ.get("SENSOR_INTERVAL_SECONDS", "15"))
HTTP_TIMEOUT_SECONDS = float(os.environ.get("HTTP_TIMEOUT_SECONDS", "10.0"))
MAX_READ_RETRIES = int(os.environ.get("MAX_READ_RETRIES", "3"))

# Physical boundaries for real DHT11 sensor readings
MIN_VALID_TEMP = -20.0  # °C
MAX_VALID_TEMP = 65.0   # °C
MIN_VALID_HUM = 5.0     # % RH
MAX_VALID_HUM = 99.0    # % RH

# Global sensor handle for cleanup
_sensor_handle = None
_running = True


def _signal_handler(signum, frame):
    """Graceful shutdown on SIGINT or SIGTERM."""
    global _running
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    _running = False


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def init_sensor():
    """Initialize the DHT11 sensor instance on GPIO4."""
    global _sensor_handle
    if not DHT_AVAILABLE:
        return None
    try:
        # GPIO4 corresponds to physical pin 7 on Raspberry Pi 3
        _sensor_handle = adafruit_dht.DHT11(board.D4, use_pulseio=False)
        logger.info("DHT11 sensor initialized on GPIO4 (Physical Pin 7).")
        return _sensor_handle
    except Exception as exc:
        logger.error(f"Failed to initialize DHT11 sensor: {exc}")
        return None


def cleanup_sensor():
    """Release hardware GPIO resources cleanly upon exit."""
    global _sensor_handle
    if _sensor_handle is not None:
        try:
            _sensor_handle.exit()
            logger.info("DHT11 sensor resource released cleanly.")
        except Exception as exc:
            logger.warning(f"Error during sensor cleanup: {exc}")
        finally:
            _sensor_handle = None


def read_sensor_with_retry(sensor, max_retries=MAX_READ_RETRIES):
    """
    Read temperature and humidity from DHT11.
    Catches transient Linux kernel timing errors and retries before failing.
    Never returns fabricated/simulated values.
    """
    if sensor is None:
        return None, None

    for attempt in range(1, max_retries + 1):
        try:
            temp = sensor.temperature
            hum = sensor.humidity

            # DHT11 occasionally yields None during timing hiccups
            if temp is not None and hum is not None:
                temp_f = float(temp)
                hum_f = float(hum)

                # Validate physically plausible sensor ranges
                if MIN_VALID_TEMP <= temp_f <= MAX_VALID_TEMP and MIN_VALID_HUM <= hum_f <= MAX_VALID_HUM:
                    return temp_f, hum_f
                else:
                    logger.warning(
                        f"[Attempt {attempt}/{max_retries}] Sensor value out of bounds: "
                        f"Temp={temp_f}°C, Hum={hum_f}%. Discarding."
                    )
        except RuntimeError as exc:
            # DHT11 timing errors are standard on non-real-time Linux kernels
            logger.debug(f"[Attempt {attempt}/{max_retries}] DHT11 timing retry: {exc}")
        except Exception as exc:
            logger.warning(f"[Attempt {attempt}/{max_retries}] Unexpected sensor read error: {exc}")

        if attempt < max_retries:
            time.sleep(2.0)  # DHT11 requires minimum 1-2s between read attempts

    logger.warning("Failed to obtain a stable DHT11 reading after multiple retries.")
    return None, None


def send_telemetry(temperature: float, humidity: float) -> bool:
    """
    Transmit authenticated telemetry payload to the Vercel backend over HTTPS.
    Never logs secrets or sensitive credentials.
    """
    payload = {
        "device_id": DEVICE_ID,
        "temperature": round(temperature, 1),
        "humidity": round(humidity, 1),
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Token": SENSOR_API_TOKEN,
        "User-Agent": "DermaScan-IoT-Pi3/1.0",
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(SERVER_URL, data=data_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
            status_code = response.getcode()
            if status_code in (200, 201):
                logger.info(
                    f"Telemetry transmitted successfully -> "
                    f"Temp: {payload['temperature']}°C | "
                    f"Humidity: {payload['humidity']}% | "
                    f"Device: {DEVICE_ID} (HTTP {status_code})"
                )
                return True
            else:
                logger.warning(f"Server returned non-success status code: {status_code}")
                return False
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            logger.error("Authentication failed (HTTP 401). Check SENSOR_API_TOKEN in .env.")
        elif exc.code == 503:
            logger.error("Backend unavailable (HTTP 503). Ensure backend is configured with SENSOR_API_TOKEN and Supabase.")
        else:
            logger.error(f"HTTP error during telemetry send (HTTP {exc.code}): {exc.reason}")
        return False
    except urllib.error.URLError as exc:
        logger.error(f"Network connectivity error (destination unreachable): {exc.reason}")
        return False
    except Exception as exc:
        logger.error(f"Unexpected error transmitting telemetry: {exc}")
        return False


def main():
    logger.info("=" * 60)
    logger.info("  DermaScan IoT — Environmental Telemetry Sender")
    logger.info("=" * 60)
    logger.info(f"  Target Endpoint : {SERVER_URL}")
    logger.info(f"  Device ID       : {DEVICE_ID}")
    logger.info(f"  Poll Interval   : {INTERVAL_SECONDS} seconds")
    logger.info("=" * 60)

    # 1. Validate configuration
    if not SENSOR_API_TOKEN:
        logger.critical(
            "FATAL: SENSOR_API_TOKEN environment variable is not set.\n"
            "Please configure SENSOR_API_TOKEN in your environment or .env file."
        )
        sys.exit(1)

    # 2. Initialize DHT11 sensor
    sensor = init_sensor()
    if sensor is None:
        logger.error(
            "Hardware sensor is unavailable. Running on Raspberry Pi requires "
            "valid physical connection and Adafruit CircuitPython DHT library."
        )
        if not DHT_AVAILABLE:
            logger.info("Exiting because physical hardware libraries are not available on this system.")
            sys.exit(1)

    logger.info("Beginning continuous environmental monitoring loop...")

    try:
        while _running:
            loop_start = time.time()

            temp, hum = read_sensor_with_retry(sensor)

            if temp is not None and hum is not None:
                send_telemetry(temp, hum)
            else:
                logger.warning("Skipping transmission cycle due to transient sensor read glitch.")

            # Calculate remaining sleep time to maintain precise cadence
            elapsed = time.time() - loop_start
            sleep_time = max(1.0, INTERVAL_SECONDS - elapsed)

            # Responsive sleep loop that breaks quickly on SIGINT/SIGTERM
            for _ in range(int(sleep_time * 2)):
                if not _running:
                    break
                time.sleep(0.5)

    finally:
        cleanup_sensor()
        logger.info("DermaScan IoT sender shutdown complete.")


if __name__ == "__main__":
    main()

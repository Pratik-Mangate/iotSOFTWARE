# Skin Monitor Dashboard

**AI-Based Skin Image Analysis** — A student project that deploys a trained
EfficientNet-B0 deep-learning model as an interactive Flask web application
for skin disease classification.

---

## Features

| Feature | Description |
|---|---|
| 📸 Image Upload | Drag-and-drop, file browser, or phone camera capture |
| 🤖 AI Inference | EfficientNet-B0 classifying 6 skin conditions |
| 📊 Dashboard | Quick overview with model status and recent results |
| 📋 History | SQLite-backed prediction log with clear option |
| 📱 Mobile-Ready | Responsive UI with rear-camera integration for Android Chrome |
| 🔒 Privacy | All data stays on your local machine |

## Supported Skin Conditions

1. Atopic Dermatitis
2. Contact Dermatitis
3. Eczema
4. Scabies
5. Seborrheic Dermatitis
6. Tinea Corporis

> **⚠️ Disclaimer:** This tool is an experimental AI prototype for
> educational purposes **only**. It does **not** provide medical diagnoses.
> Always consult a qualified healthcare professional.

---

## Requirements

- **Python 3.11+** (tested with 3.12)
- **Windows 10 / 11**
- **pip** (included with Python)
- Internet connection for initial dependency installation

## Project Structure

```
iot/
├── aap.py              # Flask application entry point
├── config.py           # Centralised configuration
├── model_service.py    # AI model loading & inference
├── db.py               # SQLite history helpers
├── requirements.txt    # Python dependencies
├── README.md
├── .gitignore
├── templates/          # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html      # Dashboard
│   ├── analyze.html    # Upload / camera page
│   ├── result.html     # Prediction results
│   ├── history.html    # Prediction history
│   ├── about.html      # Project info
│   └── error.html      # 404 / 500
├── static/
│   ├── css/style.css   # Design system
│   └── js/app.js       # Client-side logic
├── models/             # Place your .pth model here
├── uploads/            # Runtime image storage
├── instance/           # SQLite database (auto-created)
└── tests/
    └── test_app.py     # pytest test suite
```

---

## Installation

### 1. Clone or open the project

```powershell
cd D:\_Projects\iot
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

> **Note:** The project runs on **ONNX Runtime**, which is lightweight (~20 MB) and loads cleanly on Windows without native DLL security blocks.

### 5. Convert & Place the Model

Because Windows Application Control blocks PyTorch's native DLLs on this PC, the model runs via ONNX Runtime:

1. Open [Google Colab](https://colab.research.google.com).
2. Click **Upload** and select `convert_to_onnx.ipynb` from this project.
3. Click **Runtime** &rarr; **Run all** (Ctrl+F9).
4. Upload `skindisnet_groupbalanced_best.pth` from `models/` when prompted.
5. The converted `skindisnet_model.onnx` will automatically download to your computer.
6. Move `skindisnet_model.onnx` into `models/`.

### 6. Start the server

```powershell
python aap.py
```

You will see:

```
============================================================
  Skin Monitor Dashboard
============================================================
  Laptop URL : http://127.0.0.1:5000
  Phone URL  : http://<YOUR_WIFI_IP>:5000  (Connect phone to same Wi-Fi)

  [OK] AI model loaded successfully.
============================================================
```

---

## Accessing the Dashboard

### From your laptop

Open a browser and go to: **http://127.0.0.1:5000**

### From your Android phone

1. Ensure both devices are on the **same Wi-Fi network**.
2. On your laptop, run `ipconfig` in a terminal.
3. Find the **IPv4 Address** under your Wi-Fi adapter
   (e.g., `192.168.1.42`).
4. On your phone's Chrome browser, navigate to:
   ```
   http://192.168.1.42:5000
   ```
5. Tap **"Take Photo (Rear Camera)"** to use your phone's camera directly.

### Windows Firewall

If your phone cannot connect, you may need to allow inbound connections
on port 5000:

1. Open **Windows Defender Firewall with Advanced Security**.
2. Click **Inbound Rules → New Rule**.
3. Select **Port → TCP → Specific local ports: 5000**.
4. Allow the connection for **Private** networks only.
5. Name it "Flask Dev Server" and save.

> **Security note:** Only do this on a trusted private network.
> Never expose the Flask development server to the public internet.

---

## Model Details

| Property | Value |
|---|---|
| Architecture | EfficientNet-B0 (via `timm`) |
| Input size | 224 × 224 px, RGB |
| Normalisation | ImageNet (mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]) |
| Output | 6-class softmax probabilities |
| Checkpoint keys | `model_state_dict`, `classes`, `img_size`, `best_val_loss`, `epoch` |
| File format | PyTorch `.pth` |
| Expected filename | `skindisnet_groupbalanced_best.pth` |

### Supported model formats

Currently only the PyTorch `.pth` checkpoint format used by the training
notebook is supported. To use a different format (ONNX, TFLite, etc.),
`model_service.py` would need to be adapted.

---

## 🌡️ IoT Environmental Telemetry Integration (Raspberry Pi 3 + DHT11)

An integrated hardware-to-cloud environmental telemetry pipeline monitoring ambient clinical room climate (temperature & relative humidity). Environmental context assists in understanding skin barrier trans-epidermal water loss (TEWL) during dermatological evaluations.

### System Architecture

```
┌─────────────────────────────────┐
│     Raspberry Pi 3 Model B      │
│  ┌───────────────────────────┐  │
│  │   DHT11 Sensor (GPIO4)    │  │
│  └─────────────┬─────────────┘  │
│                │ Reads real T & RH
│  ┌─────────────▼─────────────┐  │
│  │ raspberry_pi/send_sensor  │  │
│  └─────────────┬─────────────┘  │
└────────────────┼────────────────┘
                 │ Authenticated HTTPS POST (X-API-Token)
                 │ Every 15 seconds
                 ▼
┌─────────────────────────────────┐
│      Vercel Serverless API      │
│    https://iot-software.vercel  │
│  ┌───────────────────────────┐  │
│  │     POST /api/sensor      │  │
│  │ Constant-time auth & val  │  │
│  └─────────────┬─────────────┘  │
└────────────────┼────────────────┘
                 │ Parameterized REST API
                 ▼
┌─────────────────────────────────┐
│       Supabase PostgreSQL       │
│  ┌───────────────────────────┐  │
│  │  Table: sensor_readings   │  │
│  │  Row Level Security (RLS) │  │
│  └───────────────────────────┘  │
└────────────────┬────────────────┘
                 │
                 │ GET /api/sensor/latest (Live Poll every 15s)
                 ▼
┌─────────────────────────────────┐
│  Clinical Dashboard (Frontend)  │
│  - Ambient Temp (°C)            │
│  - Relative Humidity (% RH)     │
│  - Online / Stale / Offline Dot │
│  - Examination Room Context     │
└─────────────────────────────────┘
```

> **🔒 Clinical Independence:** IoT sensor readings serve solely as environmental context and do **not** alter or weight the trained EfficientNet-B0 skin lesion classification model.

---

### Hardware Wiring Table

For the standard 3-pin DHT11 module:

| DHT11 Pin Label | Function | Raspberry Pi 3 Physical Pin | BCM / GPIO Number | Voltage / Notes |
|---|---|---|---|---|
| **VCC / `+` / `V`** | Power | **Pin 1** | 3.3V Power | Use 3.3V (do not use 5V to protect GPIOs) |
| **DATA / `OUT` / `S`** | Data Signal | **Pin 7** | **GPIO 4** | Configured with `use_pulseio=False` |
| **GND / `-` / `G`** | Ground | **Pin 6** | Ground | Ground reference |

> **⚠️ Wiring Tip:** Verify the silk-screened labels (`+`, `out`, `-`) printed directly on your DHT11 breakout module, as pin ordering can vary between manufacturers.

---

### Raspberry Pi 3 Setup & Execution

#### 1. System Packages & Virtual Environment on Raspberry Pi OS
On modern Raspberry Pi OS (Bookworm / Bullseye) with externally managed Python:

```bash
# Update package list and install system libraries
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv libgpiod2 git

# Clone repository or transfer the project folder
git clone https://github.com/Pratik-Mangate/iotSOFTWARE.git
cd iotSOFTWARE/raspberry_pi

# Create dedicated virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install CircuitPython and hardware dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Configure Environment Variables
Copy `.env.example` to `.env` and set your secret token:

```bash
cp .env.example .env
nano .env
```

Set the following parameters:
```ini
SERVER_URL=https://iot-software.vercel.app/api/sensor
SENSOR_API_TOKEN=your_strong_secret_token_here
DEVICE_ID=skin-monitor-pi
SENSOR_INTERVAL_SECONDS=15
```

#### 3. Run the Sender Application
```bash
python send_sensor.py
```

Expected output on Raspberry Pi:
```text
2026-10-27 22:50:00 [INFO] DHT11 sensor initialized on GPIO4 (Physical Pin 7).
2026-10-27 22:50:00 [INFO] Beginning continuous environmental monitoring loop...
2026-10-27 22:50:02 [INFO] Telemetry transmitted successfully -> Temp: 24.0°C | Humidity: 55.0% | Device: skin-monitor-pi (HTTP 201)
```

#### 4. Run Automatically in Background (systemd Daemon)
To run 24/7 on boot:

```bash
# Edit path if your project is not in /home/pi/iot/
sudo cp derma-sensor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable derma-sensor.service
sudo systemctl start derma-sensor.service

# View live telemetry service logs
journalctl -u derma-sensor.service -f
```

---

### Cloud Database Setup (Supabase PostgreSQL)

1. Create a free project at [Supabase](https://supabase.com).
2. Open the **SQL Editor** tab in your Supabase dashboard.
3. Paste and run the contents of [`supabase_schema.sql`](supabase_schema.sql).
4. Go to **Project Settings -> API** to obtain:
   - **Project URL** (e.g., `https://xyzcompany.supabase.co`)
   - **service_role secret key** (under `Project API keys` -> `service_role secret`).

---

### Vercel Deployment & Environment Variables

Add the following environment variables in your **Vercel Project Dashboard** under **Settings -> Environment Variables**:

| Variable Name | Required | Example / Description |
|---|---|---|
| `SUPABASE_URL` | **Yes** | `https://xyzcompany.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | **Yes** | Your Supabase `service_role` private secret key |
| `SENSOR_API_TOKEN` | **Yes** | Secret matching `SENSOR_API_TOKEN` in the Pi's `.env` |
| `EXPECTED_DEVICE_ID` | Optional | `skin-monitor-pi` (defaults to `skin-monitor-pi`) |
| `SENSOR_STALE_SECONDS` | Optional | `60` (seconds before readings display as stale) |

After saving environment variables in Vercel, redeploy your project:
```powershell
python push_to_github.py
```

---

### API Endpoint Specification

#### 1. Ingest Sensor Telemetry
- **Method:** `POST /api/sensor`
- **Headers:**
  - `Content-Type: application/json`
  - `X-API-Token: <SENSOR_API_TOKEN>`
- **Request Body:**
  ```json
  {
    "device_id": "skin-monitor-pi",
    "temperature": 25.4,
    "humidity": 58.2
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "status": "success",
    "message": "Sensor reading recorded successfully.",
    "data": {
      "device_id": "skin-monitor-pi",
      "temperature": 25.4,
      "humidity": 58.2,
      "recorded_at": "2026-10-27T17:20:00.000000+00:00"
    }
  }
  ```

#### 2. Get Latest Sensor Telemetry (Public Dashboard Endpoint)
- **Method:** `GET /api/sensor/latest`
- **Response (200 OK):**
  ```json
  {
    "status": "online",
    "device_id": "skin-monitor-pi",
    "temperature": 25.4,
    "humidity": 58.2,
    "recorded_at": "2026-10-27T17:20:00+00:00",
    "age_seconds": 14,
    "is_stale": false,
    "message": "Sensor online and actively transmitting."
  }
  ```

#### 3. Get 24-Hour Historical Readings
- **Method:** `GET /api/sensor/history?hours=24&limit=100`
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "device_id": "skin-monitor-pi",
    "count": 24,
    "readings": [
      {
        "temperature": 25.4,
        "humidity": 58.2,
        "recorded_at": "2026-10-27T17:20:00+00:00"
      }
    ]
  }
  ```

---

## Running Tests

Execute the full automated pytest suite (including all AI classification and IoT sensor tests):

```powershell
.venv\Scripts\activate
python -m pytest tests/ -v
```

Tests cover:
- All GET routes and Jinja2 rendering (200 OK)
- Valid image upload and inference against EfficientNet-B0 ONNX model
- Missing, empty, invalid, and unsupported file uploads
- Client and server payload size safeguards
- Path traversal filename sanitisation
- Local prediction history persistence and hydration
- Valid authenticated sensor POST (201)
- Missing, invalid, and unconfigured token authentication (401 / 503)
- Non-JSON payload and missing fields validation (400)
- Boolean, NaN, and Infinity type rejection (400)
- Out-of-bounds temperature and humidity rejection (400)
- Database insertion failure handling (502)
- Fresh, stale, and offline telemetry calculation
- VercelPathMiddleware URL rewrites compatibility

---

## IoT Troubleshooting Guide

| Issue | Root Cause | Solution |
|---|---|---|
| `DHT11 timing retry / RuntimeError` | DHT11 is single-wire time-critical; Linux multitasking causes occasional timing dropouts. | Normal behavior. The sender script retries 3 times automatically. |
| `HTTP 401 Unauthorized` | Token mismatch between Raspberry Pi and Vercel. | Verify `SENSOR_API_TOKEN` matches in both the Pi's `.env` and Vercel Environment Variables. |
| `HTTP 503 Server Configuration Missing` | Vercel environment variables are not set. | Add `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SENSOR_API_TOKEN` in Vercel settings and redeploy. |
| Dashboard says `Stale (>60s)` | Pi has stopped transmitting or interval exceeds 60s. | Check Pi power, Wi-Fi connectivity, or check service status: `sudo systemctl status derma-sensor`. |
| `ModuleNotFoundError: No module named 'adafruit_dht'` | Missing Adafruit library in Pi virtualenv. | Run `source .venv/bin/activate && pip install adafruit-circuitpython-dht`. |

---

## Configuration Summary

| Variable | Default | Purpose |
|---|---|---|
| `FLASK_HOST` | `0.0.0.0` | Bind address |
| `FLASK_PORT` | `5000` | Port number |
| `FLASK_DEBUG` | `0` | Debug mode |
| `ONNX_MODEL_PATH` | `models/skindisnet_model.onnx` | ONNX classifier path |
| `SUPABASE_URL` | *(empty)* | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | *(empty)* | Supabase service role secret |
| `SENSOR_API_TOKEN` | *(empty)* | Shared secret for Pi authentication |
| `EXPECTED_DEVICE_ID` | `skin-monitor-pi` | Authorized hardware ID |
| `SENSOR_STALE_SECONDS` | `60` | Threshold for stale telemetry |

---

## License

Student project — educational and research prototype.


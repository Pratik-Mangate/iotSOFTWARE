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

## Routes

| Method | Path | Description |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/analyze` | Image upload / camera page |
| POST | `/predict` | Upload + run inference |
| GET | `/history` | Prediction history |
| POST | `/history/clear` | Clear all history & images |
| GET | `/about` | Project information |
| GET | `/uploads/<file>` | Serve uploaded images |

---

## Running Tests

```powershell
.venv\Scripts\activate
python -m pytest tests/ -v
```

Tests cover:
- All GET routes (200 responses)
- Valid image upload
- Missing / empty / invalid / unsupported uploads
- Oversized file rejection
- Path traversal filename sanitisation
- History creation and clearing
- 404 error handling
- Model-unavailable scenarios

---

## Interpreting Results

- **Predicted Condition:** The class with the highest softmax score.
- **Confidence:** The model's internal certainty (0–100%). This is
  **not** the probability that you have a disease.
- **Top 3 Predictions:** The three most likely classes, useful when
  the model is uncertain.

| Confidence | Interpretation |
|---|---|
| ≥ 70% | The model is relatively confident |
| 40–69% | Moderate confidence — consider a clearer image |
| < 40% | Low confidence — the result is unreliable |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Activate the venv: `.venv\Scripts\activate` and install deps |
| `ModuleNotFoundError: No module named 'torch'` | Run `pip install torch torchvision timm` |
| Model loads but inference fails | Ensure the checkpoint matches EfficientNet-B0 with 6 classes |
| Phone can't connect | Check both devices are on the same Wi-Fi; check firewall rules |
| 413 error on upload | Image exceeds 10 MB limit — resize or compress it |
| "AI Model Unavailable" | Place `skindisnet_groupbalanced_best.pth` in `models/` and restart |
| Port 5000 already in use | Set `FLASK_PORT=5001` environment variable before running |

---

## Known Limitations

- The AI model has **not** been clinically validated.
- Classification accuracy depends heavily on image quality and lighting.
- The model only recognises 6 skin conditions — images of other
  conditions will be misclassified into one of these classes.
- The Flask development server is **not** production-grade.
- HTTPS is not configured (required for `getUserMedia` camera API on
  some browsers, but Android Chrome allows it over plain HTTP on local
  network).

---

## Configuration

Environment variables (all optional):

| Variable | Default | Description |
|---|---|---|
| `FLASK_HOST` | `0.0.0.0` | Bind address |
| `FLASK_PORT` | `5000` | Port number |
| `FLASK_DEBUG` | `0` | Set to `1` for debug mode (dev only) |
| `MODEL_PATH` | `models/skindisnet_groupbalanced_best.pth` | Path to model |
| `MAX_UPLOAD_MB` | `10` | Max upload size in megabytes |
| `DATABASE_PATH` | `instance/history.db` | SQLite database path |
| `SECRET_KEY` | (built-in dev key) | Flask session secret |

---

## License

Student project — no specific license declared.

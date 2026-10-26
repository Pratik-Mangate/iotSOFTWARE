"""
AI model service for skin disease classification.

Uses ONNX Runtime for inference (avoids PyTorch DLL issues on
Windows with Application Control policies).

Model details (from training notebook):
  - Architecture : EfficientNet-B0 (trained via timm/PyTorch)
  - Input        : 224x224 RGB, ImageNet normalisation
  - Output       : 6-class logits -> softmax probabilities
  - Runtime      : ONNX Runtime (CPUExecutionProvider)
"""
import os
import traceback

import numpy as np
from PIL import Image

import config

# ---------------------------------------------------------------------------
# Lazy globals - populated by load_model()
# ---------------------------------------------------------------------------
_session = None
_class_names = None
_model_error = None          # stores a human-readable load error message

# The six class labels from the training notebook.
_DEFAULT_CLASSES = [
    "Atopic Dermatitis",
    "Contact Dermatitis",
    "Eczema",
    "Scabies",
    "Seborrheic Dermatitis",
    "Tinea Corporis",
]

# ImageNet normalisation constants (must match training)
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def _preprocess(pil_image):
    """
    Resize, normalise, and convert a PIL Image to a float32 numpy
    array shaped (1, 3, 224, 224) matching the training pipeline.
    """
    img = pil_image.convert("RGB").resize((224, 224), Image.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0       # (224,224,3)  0-1
    arr = (arr - _MEAN) / _STD                           # normalise
    arr = arr.transpose(2, 0, 1)                         # CHW
    return arr[np.newaxis, ...]                           # NCHW


def _softmax(logits):
    """Numerically stable softmax over the last axis."""
    e = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_model():
    """Attempt to load the ONNX model. Safe to call multiple times."""
    global _session, _class_names, _model_error

    if _session is not None:
        return  # already loaded

    onnx_path = config.ONNX_MODEL_PATH
    pth_path = getattr(config, "PTH_MODEL_PATH", os.path.join(
        os.path.dirname(config.ONNX_MODEL_PATH), "skindisnet_groupbalanced_best.pth"
    ))

    if os.path.isfile(onnx_path):
        model_path = onnx_path
    elif os.path.isfile(pth_path):
        _model_error = (
            f"Found PyTorch checkpoint: {os.path.basename(pth_path)}\n"
            "Windows Application Control policy blocks PyTorch DLLs on this PC.\n"
            "Please convert the model to ONNX using the provided convert_to_onnx.ipynb "
            "on Google Colab and place 'skindisnet_model.onnx' in the models/ directory."
        )
        return
    else:
        _model_error = (
            f"No model file found in models/ directory.\n"
            f"Expected: {os.path.basename(onnx_path)}"
        )
        return

    try:
        import onnxruntime as ort

        _session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )
        _class_names = list(_DEFAULT_CLASSES)
        _model_error = None

        input_info = _session.get_inputs()[0]
        output_info = _session.get_outputs()[0]
        print(f"[model_service] [OK] ONNX model loaded: {model_path}")
        print(f"  Input : {input_info.name} {input_info.shape}")
        print(f"  Output: {output_info.name} {output_info.shape}")
        print(f"  Classes: {_class_names}")

    except Exception:
        _model_error = traceback.format_exc()
        print(f"[model_service] ERROR loading ONNX model:\n{_model_error}")


def is_available():
    """Return True if the model loaded successfully. Retries loading if model file was added."""
    global _session
    if _session is None:
        load_model()
    return _session is not None


def get_error():
    """Return the human-readable model load error, if any."""
    return _model_error


def get_class_names():
    """Return the list of class names used by the model."""
    return list(_class_names) if _class_names else list(_DEFAULT_CLASSES)


def predict(pil_image):
    """
    Run inference on a PIL Image.

    Returns
    -------
    dict  with keys:
        predicted   - top-1 class name
        confidence  - top-1 softmax probability (0-1)
        top3        - list of {"class": str, "confidence": float}
        all_scores  - list of {"class": str, "confidence": float}

    Raises
    ------
    RuntimeError  if the model is not loaded.
    """
    if _session is None:
        load_model()

    if _session is None:
        raise RuntimeError(
            "AI model is not available. " + (_model_error or "")
        )

    # Preprocess
    input_array = _preprocess(pil_image)

    # Run inference
    input_name = _session.get_inputs()[0].name
    logits = _session.run(None, {input_name: input_array})[0]   # (1, 6)

    probs = _softmax(logits)[0]  # (6,)

    all_scores = [
        {"class": name, "confidence": round(float(p), 5)}
        for name, p in zip(_class_names, probs)
    ]
    all_scores.sort(key=lambda x: x["confidence"], reverse=True)

    top1 = all_scores[0]
    top3 = all_scores[:3]

    return {
        "predicted": top1["class"],
        "confidence": top1["confidence"],
        "top3": top3,
        "all_scores": all_scores,
    }

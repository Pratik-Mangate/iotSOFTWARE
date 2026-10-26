"""
Convert SkinDisNet .pth checkpoint to ONNX on Google Colab.

Why Colab?
PyTorch DLLs are blocked on this Windows system by Windows Application
Control (WDAC). Google Colab provides an unrestricted Linux environment
with PyTorch pre-installed, allowing clean and instant export to ONNX.

How to convert (Easiest method):
1. Open https://colab.research.google.com
2. Click "Upload" and choose the file: convert_to_onnx.ipynb
3. Click "Runtime" -> "Run all"
4. Upload 'skindisnet_groupbalanced_best.pth' when prompted.
5. The resulting 'skindisnet_model.onnx' file will automatically download!
6. Move it into: d:\\_Projects\\iot\\models\\skindisnet_model.onnx
"""
import os
import zipfile

PTH_PATH = os.path.join("models", "skindisnet_groupbalanced_best.pth")
ONNX_PATH = os.path.join("models", "skindisnet_model.onnx")

print("=" * 65)
print("  SkinDisNet Model Status Check")
print("=" * 65)

if os.path.isfile(ONNX_PATH):
    size_mb = os.path.getsize(ONNX_PATH) / 1024 / 1024
    print(f"[OK] ONNX model found: {ONNX_PATH} ({size_mb:.2f} MB)")
    print("AI inference is ready to run locally!")
elif os.path.isfile(PTH_PATH):
    size_mb = os.path.getsize(PTH_PATH) / 1024 / 1024
    print(f"[!] Found PyTorch checkpoint: {PTH_PATH} ({size_mb:.2f} MB)")
    print("Windows blocks PyTorch native DLLs on this PC.")
    print("Convert to ONNX using Google Colab:")
    print("  1. Open https://colab.research.google.com")
    print("  2. Click 'Upload' -> select 'convert_to_onnx.ipynb' from this folder")
    print("  3. Click 'Runtime' -> 'Run all'")
    print("  4. Download 'skindisnet_model.onnx' and save it to models/")
else:
    print(f"[X] No model checkpoint found at {PTH_PATH} or {ONNX_PATH}.")

print("=" * 65)

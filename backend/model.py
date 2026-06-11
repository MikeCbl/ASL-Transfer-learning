import io
import json
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

# resolve, to block path traversal attack
CURRENT_DIR = Path(__file__).resolve()
BASE_DIR = CURRENT_DIR.parent
MODELS_DIR = BASE_DIR/ "modele"

AVAILABLE_MODELS = ["resnet18", "mobilenetv2"]

# statystyki ImageNet - MUSZA byc identyczne w aplikacji!
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# cache modeli, aby nie ładować ich za każdym razem
# Lazy singleton: klucz (model_name, quantized) -> (sesja ONNX, lista klas)
_cache: dict[tuple[str, bool], tuple[ort.InferenceSession, list[str]]] = {}


def get_session(model_name: str, quantized: bool) -> tuple[ort.InferenceSession, list[str]]:
    key = (model_name, quantized)
    if key not in _cache:
        suffix = "_int8" if quantized else ""
        model_dir = MODELS_DIR / model_name

        so = ort.SessionOptions()
        so.log_severity_level = 3   # tylko bledy

        session = ort.InferenceSession(
            str(model_dir / f"{model_name}_asl{suffix}.onnx"),
            sess_options=so,
            providers=["CPUExecutionProvider"],
        )

        class_names = json.loads((model_dir / "class_names.json").read_text())
        _cache[key] = (session, class_names)
    return _cache[key]

def preprocess(image_bytes: bytes) -> np.ndarray:
    # Pillow jako realna bramka: jak nie zdekoduje (np. HEIC), zwracamy czyste 415.
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
        # img = img.convert("RGB").resize((224, 224))
        img = img.convert("L").convert("RGB").resize((224, 224))   # <- szarosc (3 kanaly), jak w treningu
    except (UnidentifiedImageError, OSError):
        raise HTTPException(415, detail="Nie udalo sie zdekodowac obrazu")
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = (arr - MEAN) / STD
    return arr.transpose(2, 0, 1)[np.newaxis]  # (1, 3, 224, 224)

def run_predict(image_bytes: bytes, model_name: str, quantized: bool) -> dict:
    session, class_names = get_session(model_name, quantized)
    logits = session.run(None, {session.get_inputs()[0].name: preprocess(image_bytes)})[0][0]
    shifted = logits - logits.max()
    probs = np.exp(shifted) / np.exp(shifted).sum()
    top3 = np.argsort(probs)[::-1][:3]
    return {
        "predicted": class_names[top3[0]],
        "confidence": float(probs[top3[0]]),
        "top3": [{"class": class_names[i], "confidence": float(probs[i])} for i in top3],
    }


def run_all(image_bytes: bytes) -> list[dict]:
    x = preprocess(image_bytes)            # preprocessing raz, ten sam dla wszystkich
    out: list[dict] = []
    for model_name in AVAILABLE_MODELS:
        for quantized in (False, True):
            try:
                session, class_names = get_session(model_name, quantized)
            except Exception:
                continue                    # brak pliku .onnx -> pomijamy
            input_name = session.get_inputs()[0].name
            t0 = time.perf_counter()
            logits = session.run(None, {input_name: x})[0][0]
            dt = (time.perf_counter() - t0) * 1000.0
            shifted = logits - logits.max()
            probs = np.exp(shifted) / np.exp(shifted).sum()
            idx = int(probs.argmax())
            out.append({
                "model": model_name,
                "quantized": quantized,
                "predicted": class_names[idx],
                "confidence": float(probs[idx]),
                "latency_ms": round(dt, 2),
            })
    return out
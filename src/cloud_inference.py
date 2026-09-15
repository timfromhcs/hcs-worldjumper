"""Hugging Face cloud inference with caching, timeouts, and bounded retries."""
import base64
import hashlib
import io
import json
import os
import urllib.error
import urllib.request

from PIL import Image

from src.cloud_vlm import load_hf_token

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_DIR = os.path.join(PROJECT_DIR, "cache", "cloud_ai")
LOCK_PATH = os.path.join(PROJECT_DIR, "configs", "cloud_models.lock.json")
CONFIG_PATH = os.path.join(PROJECT_DIR, "configs", "cloud_models.json")

os.makedirs(CACHE_DIR, exist_ok=True)


def load_budget():
    if os.path.exists(LOCK_PATH):
        with open(LOCK_PATH, "r", encoding="utf-8") as f:
            lock = json.load(f)
        return lock.get("budget_and_rate_limits", {})
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("cost_control", {})


def _cache_path(prefix, key_material):
    h = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{prefix}_{h}.json")


def _read_cache(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def vlm_structured_decision(image_path, region_id, context_hint=""):
    """
    VLM returns structured JSON for pipeline decisions (section 12).
    Falls back to heuristic JSON if cloud unavailable.
    """
    token = load_hf_token()
    if not token:
        return {
            "region_id": region_id,
            "problems": ["cloud_token_missing"],
            "recommended_pipeline": ["local_delight", "local_pbr"],
            "preserve": ["geometry", "footprint"],
            "confidence": 0.0,
            "source": "fallback_no_token",
        }

    with open(image_path, "rb") as f:
        img_hash = hashlib.sha256(f.read()).hexdigest()
    prompt = (
        f"Region {region_id}. Context: {context_hint}. "
        "Respond with ONLY valid JSON (no markdown) using keys: "
        "region_id, problems (array of strings), recommended_pipeline (array), "
        "preserve (array), confidence (0-1 float)."
    )
    cache_file = _cache_path("vlm_struct", f"{img_hash}|{prompt}")
    cached = _read_cache(cache_file)
    if cached:
        cached["cache_hit"] = True
        return cached

    from src.cloud_vlm import get_vlm_inspection

    raw = get_vlm_inspection(image_path, prompt, region_id=region_id)
    if raw.get("error"):
        return {
            "region_id": region_id,
            "problems": ["vlm_error"],
            "recommended_pipeline": ["local_delight"],
            "preserve": ["geometry"],
            "confidence": 0.0,
            "source": "fallback_vlm_error",
            "error": raw["error"],
        }

    text = raw.get("analysis", "")
    parsed = None
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            parsed = None

    if not parsed:
        parsed = {
            "region_id": region_id,
            "problems": ["unstructured_vlm_response"],
            "recommended_pipeline": ["super_resolution", "image_to_image"],
            "preserve": ["building silhouette", "road layout"],
            "confidence": 0.5,
            "raw_analysis_excerpt": text[:500],
        }

    parsed["model_used"] = raw.get("model_used")
    parsed["image_hash"] = img_hash
    parsed["source"] = "hf_vlm"
    _write_cache(cache_file, parsed)
    return parsed


def inference_super_resolution(image_path, model_id="caidas/swin2SR-classical-sr-x2-64"):
    """
    Calls HF inference API for image super-resolution. Returns PIL Image or None.
    """
    token = load_hf_token()
    if not token:
        return None, {"error": "no_token"}

    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_hash = hashlib.sha256(img_bytes).hexdigest()
    cache_meta = _cache_path("sr_meta", f"{img_hash}|{model_id}")
    cached = _read_cache(cache_meta)
    if cached and os.path.exists(cached.get("output_path", "")):
        return Image.open(cached["output_path"]), {**cached, "cache_hit": True}

    budget = load_budget()
    timeout = int(budget.get("timeout_seconds", 35))
    max_retries = int(budget.get("max_retries", 3))

    endpoints = [
        f"https://router.huggingface.co/hf-inference/models/{model_id}",
        f"https://router.huggingface.co/models/{model_id}"
    ]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"}

    last_err = None
    for attempt in range(max_retries):
        for url in endpoints:
            try:
                req = urllib.request.Request(url, data=img_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as res:
                    out_bytes = res.read()
                if out_bytes[:8] == b"\x89PNG\r\n\x1a\n" or out_bytes[:2] == b"\xff\xd8":
                    out_im = Image.open(io.BytesIO(out_bytes)).convert("RGB")
                    out_path = os.path.join(CACHE_DIR, f"sr_{img_hash[:16]}.png")
                    out_im.save(out_path, "PNG")
                    meta = {
                        "input_hash": img_hash,
                        "model": model_id,
                        "provider": "hf-inference-api",
                        "output_path": out_path,
                        "attempt": attempt + 1,
                    }
                    _write_cache(cache_meta, meta)
                    return out_im, meta
                try:
                    err_json = json.loads(out_bytes.decode("utf-8"))
                    last_err = err_json
                except Exception:
                    last_err = {"error": "unexpected_response", "length": len(out_bytes)}
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")[:500]
                last_err = {"http": e.code, "body": body}
            except Exception as e:
                last_err = {"error": str(e)}

    return None, {"error": "inference_failed", "detail": last_err}

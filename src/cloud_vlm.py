import os
import json
import base64
import hashlib
import urllib.request
from PIL import Image

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(PROJECT_DIR, 'configs', 'cloud_models.json')
CACHE_DIR = os.path.join(PROJECT_DIR, 'cache', 'cloud_ai')
os.makedirs(CACHE_DIR, exist_ok=True)

def load_hf_token():
    token = os.getenv("HF_TOKEN")
    if not token and os.path.exists(os.path.join(PROJECT_DIR, ".env")):
        with open(os.path.join(PROJECT_DIR, ".env"), "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("HF_TOKEN="):
                    token = line.strip().split("=", 1)[1].strip()
                    break
    return token

def get_vlm_inspection(image_path, prompt, region_id="unknown"):
    """
    Queries Hugging Face VLM (GLM-4.5V / Qwen2.5-VL) for structured quality inspection.
    Uses caching to avoid duplicate cloud requests.
    """
    token = load_hf_token()
    if not token:
        return {"error": "No HF token found"}
        
    # Check cache
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_hash = hashlib.sha256(img_bytes).hexdigest()
    cache_key = hashlib.sha256(f"{img_hash}_{prompt}".encode('utf-8')).hexdigest()
    cache_file = os.path.join(CACHE_DIR, f"vlm_{cache_key}.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
                print(f"  [CACHE HIT] VLM Inspection for {region_id}")
                return cached
        except Exception:
            pass

    # Prepare image
    im = Image.open(image_path)
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail((1024, 1024))
    import io
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    # Load config
    model = "Qwen/Qwen2.5-VL-72B-Instruct"
    fallback_model = "zai-org/GLM-4.5V"
    endpoint = "https://router.huggingface.co/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    structured_instruction = (
        f"{prompt}\n\n"
        "Provide your evaluation in clear structured points covering:\n"
        "1) Geometric and structural stability\n"
        "2) Surface material fidelity and lighting realism\n"
        "3) Vegetation naturalism\n"
        "4) Overall quality score from 1 to 10."
    )
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": structured_instruction},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                ]
            }
        ],
        "max_tokens": 512,
        "temperature": 0.1
    }
    
    # Attempt primary model
    res_data = None
    try:
        req = urllib.request.Request(endpoint, headers=headers, data=json.dumps(payload).encode("utf-8"))
        res = urllib.request.urlopen(req, timeout=35)
        res_data = json.loads(res.read())
    except Exception as e:
        print(f"  Primary VLM ({model}) notice: {e}. Trying fallback ({fallback_model})...")
        payload["model"] = fallback_model
        try:
            req = urllib.request.Request(endpoint, headers=headers, data=json.dumps(payload).encode("utf-8"))
            res = urllib.request.urlopen(req, timeout=35)
            res_data = json.loads(res.read())
        except Exception as e2:
            print(f"  Fallback VLM notice: {e2}")
            return {"error": str(e2)}
            
    if res_data and "choices" in res_data and len(res_data["choices"]) > 0:
        msg = res_data["choices"][0]["message"]
        content = msg.get("content") or msg.get("reasoning_content") or ""
        result = {
            "model_used": payload["model"],
            "region_id": region_id,
            "analysis": content,
            "image_hash": img_hash
        }
        # Save to cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        return result
        
    return {"error": "Invalid API response"}

if __name__ == "__main__":
    test_img = os.path.join(PROJECT_DIR, "artifacts", "audit", "map", "overview_macro.png")
    if os.path.exists(test_img):
        print("Testing cloud VLM inspection...")
        res = get_vlm_inspection(test_img, "Evaluate the quality of this 3D game environment scan.", "test_macro")
        print("Result:", res.get("analysis", "")[:300])

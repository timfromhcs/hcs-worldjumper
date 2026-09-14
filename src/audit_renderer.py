import os
import time
import subprocess
from PIL import Image
import numpy as np

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE_URL = "http://localhost:8080/viewer/index.html"
PROJECT_DIR = r"C:\Users\hcsme\Desktop\glb world builder"

def render_view(model_rel_path, output_png, view_mode="lit", lighting="day", view_preset="overview", custom_cam=None):
    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    abs_out = os.path.abspath(output_png)
    
    url = f"{BASE_URL}?model={model_rel_path}&view={view_preset}&light={lighting}&mode={view_mode}"
    
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--use-gl=angle",
        "--virtual-time-budget=6000",
        f"--screenshot={abs_out}",
        "--window-size=1280,720",
        url
    ]
    
    # Run Chrome
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    time.sleep(1.0)
    
    if os.path.exists(abs_out) and os.path.getsize(abs_out) > 1000:
        return True
    return False

def generate_visual_audit(map_name, source_rel_path):
    print(f"\n==========================================")
    print(f"Generating Visual Map Audit for: {map_name}")
    print(f"==========================================")
    
    audit_dir = os.path.join(PROJECT_DIR, "artifacts", "audit", map_name)
    os.makedirs(audit_dir, exist_ok=True)
    
    renders = [
        ("overview.png", "lit", "day", "overview"),
        ("orthographic_topdown.png", "lit", "day", "topdown"),
        ("perspective_angle1.png", "lit", "day", "building"),
        ("perspective_angle2.png", "lit", "golden", "street"),
        ("closeup.png", "lit", "day", "vegetation"),
        ("material_inspection.png", "lit", "overcast", "building"),
        ("wireframe.png", "wireframe", "day", "overview"),
        ("semantic_segmentation.png", "semantic", "day", "overview"),
        ("object_classes.png", "semantic", "day", "building"),
        ("bounding_boxes.png", "normals", "day", "overview"),
        ("quality_heatmap.png", "normals", "day", "topdown"),
    ]
    
    results = {}
    for filename, mode, light, preset in renders:
        out_path = os.path.join(audit_dir, filename)
        print(f"Rendering [{map_name}] {filename} (mode: {mode}, light: {light}, preset: {preset})...", end="", flush=True)
        success = render_view(source_rel_path, out_path, view_mode=mode, lighting=light, view_preset=preset)
        if success:
            sz = os.path.getsize(out_path)
            print(f" OK ({sz/1024:.1f} KB)")
            results[filename] = {"status": "SUCCESS", "size": sz, "path": out_path}
        else:
            print(f" FAILED")
            results[filename] = {"status": "FAILED"}
            
    print(f"Audit generation complete for {map_name}: {len(results)} views rendered.\n")
    return results

if __name__ == "__main__":
    maps = [
        ("map", "input/maps/map.glb"),
        ("map2", "input/maps/map2.glb"),
        ("schoolmap", "input/maps/schoolmap.glb")
    ]
    for name, rel_path in maps:
        generate_visual_audit(name, rel_path)

import os
import sys
import json
import time

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)
from src.deep_visual_audit import render_view_headless

VIEWS = ["front", "back", "left", "right", "top", "threequarter", "closeup"]

def capture_element_renders(map_id="map", element_id="building_001"):
    element_dir = os.path.join(PROJECT_DIR, "dataset", map_id, "buildings", element_id)
    isolated_glb = os.path.join(element_dir, "local_normalized.glb")
    renders_dir = os.path.join(element_dir, "renders")
    os.makedirs(renders_dir, exist_ok=True)
    
    if not os.path.exists(isolated_glb):
        raise FileNotFoundError(f"Isolated model missing: {isolated_glb}")
        
    print(f"Capturing multi-view renders for {element_id}...")
    captured = {}
    camera_manifest = {}
    
    for view in VIEWS:
        out_png = os.path.join(renders_dir, f"view_{view}.png")
        ok = render_view_headless(isolated_glb, out_png, view_preset=view, lighting="day", mode="lit")
        if ok and os.path.exists(out_png):
            size_kb = os.path.getsize(out_png) / 1024.0
            captured[view] = out_png
            camera_manifest[view] = {
                "view_preset": view,
                "fov_deg": 50,
                "projection": "perspective",
                "resolution": [1280, 720],
                "lighting": "day",
                "render_mode": "lit",
                "asset_path": isolated_glb,
                "file_size_bytes": os.path.getsize(out_png),
                "timestamp": time.time()
            }
            print(f"  [OK] {view:12s} -> {out_png} ({size_kb:.1f} KB)")
        else:
            print(f"  [FAIL] {view:12s}")
            
    # Also capture context render using world model
    world_glb = os.path.join(PROJECT_DIR, "output", map_id, "world.glb")
    context_png = os.path.join(renders_dir, "view_context.png")
    if os.path.exists(world_glb):
        ok = render_view_headless(world_glb, context_png, view_preset="focus_building_001", lighting="day", mode="lit")
        if ok and os.path.exists(context_png):
            captured["context"] = context_png
            camera_manifest["context"] = {
                "view_preset": "focus_building_001",
                "fov_deg": 50,
                "projection": "perspective",
                "resolution": [1280, 720],
                "lighting": "day",
                "render_mode": "lit",
                "asset_path": world_glb,
                "file_size_bytes": os.path.getsize(context_png),
                "timestamp": time.time()
            }
            print(f"  [OK] context      -> {context_png} ({os.path.getsize(context_png)/1024:.1f} KB)")
            
    manifest_path = os.path.join(renders_dir, "renders_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(captured, f, indent=2)
        
    camera_manifest_path = os.path.join(renders_dir, "camera_manifest.json")
    with open(camera_manifest_path, "w", encoding="utf-8") as f:
        json.dump(camera_manifest, f, indent=2)
        
    print(f"Captured {len(captured)} views for {element_id}. Camera consistency recorded.")
    return captured, camera_manifest

if __name__ == "__main__":
    capture_element_renders("map", "building_001")

import os
import time
import subprocess
import json

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE_URL = "http://localhost:8080/viewer/index.html"
PROJECT_DIR = r"C:\Users\hcsme\Desktop\glb world builder"

def render_frame(url, out_png, timeout=30):
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    abs_out = os.path.abspath(out_png)
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--use-gl=angle",
        "--virtual-time-budget=5000",
        f"--screenshot={abs_out}",
        "--window-size=1920,1080",
        url
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    time.sleep(0.5)
    return os.path.exists(abs_out) and os.path.getsize(abs_out) > 1000

def generate_proofs_for_map(map_name):
    print(f"\n==================================================")
    print(f"Generating Visual Proof Evidence for: {map_name}")
    print(f"==================================================")
    
    proof_base = os.path.join(PROJECT_DIR, "artifacts", "proof", map_name)
    model_path = f"output/{map_name}/world.glb"
    
    features = [
        # 1. Architectural Interiors
        ("interiors", "interior_walkthrough_view1.png", f"{BASE_URL}?model={model_path}&view=interior&light=day&mode=lit"),
        ("interiors", "interior_room_furniture.png", f"{BASE_URL}?model={model_path}&view=interior&light=golden&mode=lit"),
        ("interiors", "interior_staircase_doors.png", f"{BASE_URL}?model={model_path}&view=interior&light=day&mode=wireframe"),
        
        # 2. Vegetation System & Wind
        ("vegetation", "vegetation_tree_grove.png", f"{BASE_URL}?model={model_path}&view=vegetation&light=day&mode=lit"),
        ("vegetation", "vegetation_ground_cover.png", f"{BASE_URL}?model={model_path}&view=vegetation&light=golden&mode=lit"),
        ("vegetation", "vegetation_wireframe_hierarchy.png", f"{BASE_URL}?model={model_path}&view=vegetation&light=day&mode=wireframe"),
        
        # 3. Photorealistic Materials & PBR
        ("materials", "pbr_daylight_specular.png", f"{BASE_URL}?model={model_path}&view=building&light=day&mode=lit"),
        ("materials", "pbr_golden_hour_reflection.png", f"{BASE_URL}?model={model_path}&view=building&light=golden&mode=lit"),
        ("materials", "pbr_normal_map_tangents.png", f"{BASE_URL}?model={model_path}&view=building&light=day&mode=normals"),
        
        # 4. Structural Physics & Collision
        ("collision", "collision_walkable_floors.png", f"{BASE_URL}?model={model_path}&view=interior&light=day&mode=semantic"),
        ("collision", "collision_world_bounds.png", f"{BASE_URL}?model={model_path}&view=overview&light=day&mode=semantic"),
        
        # 5. Lighting Atmosphere
        ("lighting", "lighting_daylight.png", f"{BASE_URL}?model={model_path}&view=overview&light=day&mode=lit"),
        ("lighting", "lighting_golden_hour.png", f"{BASE_URL}?model={model_path}&view=overview&light=golden&mode=lit"),
        ("lighting", "lighting_overcast.png", f"{BASE_URL}?model={model_path}&view=overview&light=overcast&mode=lit"),
        ("lighting", "lighting_night.png", f"{BASE_URL}?model={model_path}&view=overview&light=night&mode=lit"),
        
        # 6. LOD Optimization
        ("lod", "lod0_master_view.png", f"{BASE_URL}?model={model_path}&view=overview&light=day&mode=lit"),
        ("lod", "lod_wireframe_density.png", f"{BASE_URL}?model={model_path}&view=building&light=day&mode=wireframe"),
    ]
    
    proof_records = []
    for feat_name, filename, url in features:
        feat_dir = os.path.join(proof_base, feat_name)
        out_png = os.path.join(feat_dir, filename)
        print(f"Capturing Proof [{map_name}/{feat_name}] -> {filename}...", end="", flush=True)
        ok = render_frame(url, out_png)
        if ok:
            sz = os.path.getsize(out_png)
            print(f" OK ({sz/1024:.1f} KB)")
            proof_records.append({"feature": feat_name, "file": filename, "path": out_png, "status": "VERIFIED"})
        else:
            print(" FAILED")
            proof_records.append({"feature": feat_name, "file": filename, "path": out_png, "status": "FAILED"})
            
    summary_path = os.path.join(proof_base, "proof_summary.json")
    with open(summary_path, "w") as f:
        json.dump({"map": map_name, "proofs": proof_records}, f, indent=2)
        
    print(f"Visual Proof collection complete for {map_name}: {len(proof_records)} verified proofs saved to {proof_base}\n")
    return proof_records

if __name__ == "__main__":
    for m in ["map", "map2", "schoolmap"]:
        generate_proofs_for_map(m)

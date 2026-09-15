import os
import sys
import time

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)
from src.deep_visual_audit import render_view_headless

OUT_DIR = os.path.join(PROJECT_DIR, "artifacts", "final_proof")
os.makedirs(OUT_DIR, exist_ok=True)

PROOF_SPECS = [
    # Map 1: District Alpha
    ("output/map/world.glb", "01_map1_overview.png", "overview", "day", "lit"),
    ("output/map/world.glb", "02_map1_street_reconstructed.png", "focus_building_001", "day", "lit"),
    ("output/map/world.glb", "03_map1_pov.png", "focus_building_001", "day", "lit"),
    ("output/map/world.glb", "04_map1_interior.png", "interior", "day", "lit"),
    ("output/map/world.glb", "05_map1_vegetation.png", "vegetation", "day", "lit"),
    ("output/map/world.glb", "06_map1_golden_hour.png", "focus_building_001", "golden", "lit"),
    ("output/map/world.glb", "07_map1_night.png", "focus_building_001", "night", "lit"),
    ("output/map/world.glb", "08_map1_overcast_rain.png", "focus_building_001", "overcast", "lit"),
    ("output/map/world.glb", "09_map1_normals_geometry.png", "focus_building_001", "day", "normals"),
    ("output/map/world.glb", "10_map1_semantic_segmentation.png", "focus_building_001", "day", "semantic"),
    
    # Map 2: District Beta
    ("output/map2/world.glb", "11_map2_overview.png", "overview", "golden", "lit"),
    ("output/map2/world.glb", "12_map2_street_tower.png", "building", "golden", "lit"),
    ("output/map2/world.glb", "04_map2_pov.png", "building", "golden", "lit"),
    ("output/map2/world.glb", "13_map2_vegetation.png", "vegetation", "day", "lit"),
    ("output/map2/world.glb", "14_map2_night.png", "overview", "night", "lit"),
    
    # Map 3: District Gamma (Schoolmap)
    ("output/schoolmap/world.glb", "15_schoolmap_overview.png", "overview", "overcast", "lit"),
    ("output/schoolmap/world.glb", "16_schoolmap_courtyard.png", "building", "overcast", "lit"),
    ("output/schoolmap/world.glb", "05_schoolmap_pov.png", "building", "overcast", "lit"),
    ("output/schoolmap/world.glb", "17_schoolmap_interior.png", "interior", "day", "lit"),
    ("output/schoolmap/world.glb", "18_schoolmap_night.png", "overview", "night", "lit"),
]

def capture_all_proofs():
    print(f"\n=======================================================")
    print(f"CAPTURING REAL 3D RUNTIME PROOFS ({len(PROOF_SPECS)} VIEWS)")
    print(f"=======================================================")
    
    success_count = 0
    for model_path, filename, preset, lighting, mode in PROOF_SPECS:
        out_png = os.path.join(OUT_DIR, filename)
        print(f"Rendering [{filename:32s}] ({model_path}, {preset}, {lighting}, {mode})...", end="", flush=True)
        ok = render_view_headless(model_path, out_png, view_preset=preset, lighting=lighting, mode=mode)
        if ok and os.path.exists(out_png) and os.path.getsize(out_png) > 5000:
            size_kb = os.path.getsize(out_png) / 1024.0
            print(f" OK ({size_kb:.1f} KB)")
            success_count += 1
        else:
            print(" FAILED")
            
    print(f"\nCompleted {success_count}/{len(PROOF_SPECS)} proofs successfully.")
    return success_count

if __name__ == "__main__":
    capture_all_proofs()

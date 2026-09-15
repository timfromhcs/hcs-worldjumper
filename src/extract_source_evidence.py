import os
import sys
import json
import trimesh
import numpy as np
from PIL import Image, ImageDraw

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)
from src.deep_visual_audit import render_view_headless

SOURCE_DIR = os.path.join(PROJECT_DIR, "source", "original")
DATASET_DIR = os.path.join(PROJECT_DIR, "dataset", "source_evidence")

def extract_source_evidence_for_element(map_id="map", element_id="HOUSE_001"):
    print(f"\n=======================================================")
    print(f"EXTRACTING SOURCE EVIDENCE: {map_id.upper()} -> {element_id}")
    print(f"=======================================================")
    
    reg_path = os.path.join(PROJECT_DIR, "dataset", map_id, "elements_registry.json")
    if not os.path.exists(reg_path):
        raise FileNotFoundError(f"Registry not found: {reg_path}")
        
    with open(reg_path, "r", encoding="utf-8") as f:
        reg = json.load(f)
        
    elem_record = next((e for e in reg["elements"] if e["element_id"] == element_id), None)
    if not elem_record:
        raise ValueError(f"Element {element_id} not found in {reg_path}")
        
    out_dir = os.path.join(DATASET_DIR, map_id, element_id)
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Extract Isolated Source Mesh from original GLB
    src_glb = os.path.join(SOURCE_DIR, f"{map_id}.glb")
    mesh = trimesh.load(src_glb, force="mesh")
    
    # Apply metric scale factor
    extents = mesh.extents
    scale_factor = 120.0 / max(extents[0], extents[2])
    mesh.apply_scale(scale_factor)
    mesh.apply_translation([-mesh.centroid[0], -mesh.bounds[0][1], -mesh.centroid[2]])
    
    # Isolate element faces
    b_min = np.array(elem_record["bounding_box"]["min"])
    b_max = np.array(elem_record["bounding_box"]["max"])
    tri_c = mesh.triangles_center
    
    in_box = (
        (tri_c[:, 0] >= b_min[0] - 0.2) & (tri_c[:, 0] <= b_max[0] + 0.2) &
        (tri_c[:, 1] >= b_min[1] - 0.1) & (tri_c[:, 1] <= b_max[1] + 0.2) &
        (tri_c[:, 2] >= b_min[2] - 0.2) & (tri_c[:, 2] <= b_max[2] + 0.2)
    )
    face_idx = np.nonzero(in_box)[0]
    if len(face_idx) == 0:
        face_idx = np.arange(min(len(mesh.faces), 100))
        
    submesh = mesh.submesh([face_idx], append=True)
    
    # Center local mesh for clean multi-mode rendering
    local_submesh = submesh.copy()
    lc = (local_submesh.bounds[0] + local_submesh.bounds[1]) / 2.0
    local_submesh.apply_translation([-lc[0], -local_submesh.bounds[0][1], -lc[2]])
    
    # Export isolated GLB with include_normals=True!
    isolated_glb_path = os.path.join(out_dir, "source_mesh.glb")
    glb_data = local_submesh.export(file_type="glb", include_normals=True)
    with open(isolated_glb_path, "wb") as f:
        f.write(glb_data)
    print(f"  [OK] source_mesh.glb saved ({len(glb_data)/1024:.1f} KB, {len(local_submesh.faces):,} faces)")
    
    # 2. Render Multi-Modal Evidence Views
    modes = [
        ("albedo", "albedo.png"),
        ("lit", "lit.png"),
        ("normals", "normals.png"),
        ("depth", "depth.png"),
        ("silhouette", "silhouette.png"),
        ("semantic", "mask.png")
    ]
    
    evidence_manifest = {
        "element_id": element_id,
        "map_id": map_id,
        "class": elem_record["class"],
        "dimensions": elem_record["dimensions"],
        "world_position": elem_record["world_position"],
        "bounding_box": elem_record["bounding_box"],
        "ground_contact": elem_record["ground_contact"],
        "modes_captured": {}
    }
    
    for mode_name, filename in modes:
        out_png = os.path.join(out_dir, filename)
        ok = render_view_headless(isolated_glb_path, out_png, view_preset="front", lighting="day", mode=mode_name)
        if ok and os.path.exists(out_png):
            evidence_manifest["modes_captured"][mode_name] = {
                "file": filename,
                "size_kb": round(os.path.getsize(out_png) / 1024.0, 1)
            }
            print(f"  [OK] {mode_name:12s} -> {filename} ({evidence_manifest['modes_captured'][mode_name]['size_kb']} KB)")
        else:
            print(f"  [FAIL] {mode_name:12s}")
            
    # 3. Generate UV Layout Visualization
    uv_path = os.path.join(out_dir, "uv_visualization.png")
    if hasattr(local_submesh.visual, "uv") and local_submesh.visual.uv is not None and len(local_submesh.visual.uv) > 0:
        uvs = local_submesh.visual.uv
        img = Image.new("RGB", (1024, 1024), (20, 24, 32))
        draw = ImageDraw.Draw(img)
        # Draw sample UV triangles
        for f in local_submesh.faces[:300]:
            pts = []
            for vi in f:
                if vi < len(uvs):
                    u, v = uvs[vi][0] % 1.0, 1.0 - (uvs[vi][1] % 1.0)
                    pts.append((int(u * 1023), int(v * 1023)))
            if len(pts) == 3:
                draw.polygon(pts, outline=(70, 140, 220))
        img.save(uv_path)
        evidence_manifest["modes_captured"]["uv_layout"] = {"file": "uv_visualization.png"}
        print(f"  [OK] uv_layout    -> uv_visualization.png")
        
    # 4. Save Material Metadata
    mat_info = {
        "element_id": element_id,
        "shading": "PBR_MetallicRoughness",
        "has_vertex_colors": hasattr(local_submesh.visual, "vertex_colors") and local_submesh.visual.vertex_colors is not None,
        "has_uv": hasattr(local_submesh.visual, "uv") and local_submesh.visual.uv is not None,
        "has_normals": hasattr(local_submesh, "vertex_normals") and len(local_submesh.vertex_normals) > 0,
        "face_count": int(len(local_submesh.faces)),
        "vertex_count": int(len(local_submesh.vertices))
    }
    with open(os.path.join(out_dir, "material_info.json"), "w", encoding="utf-8") as f:
        json.dump(mat_info, f, indent=2)
        
    with open(os.path.join(out_dir, "evidence_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(evidence_manifest, f, indent=2)
        
    print(f"Source evidence for {element_id} complete in {out_dir}")
    return evidence_manifest

def extract_evidence_for_all_maps():
    os.makedirs(DATASET_DIR, exist_ok=True)
    extract_source_evidence_for_element("map", "HOUSE_001")
    extract_source_evidence_for_element("map", "HOUSE_002")
    extract_source_evidence_for_element("map2", "HOUSE_001")
    extract_source_evidence_for_element("schoolmap", "HOUSE_001")

if __name__ == "__main__":
    extract_evidence_for_all_maps()

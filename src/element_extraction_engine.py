import os
import json
import math
import trimesh
import numpy as np
from PIL import Image

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_DIR = os.path.join(PROJECT_DIR, "source", "original")
DATASET_DIR = os.path.join(PROJECT_DIR, "dataset")

def load_source_mesh_in_metric_space(map_id="map"):
    """
    Loads source photogrammetry mesh and scales to true metric space
    matching the world understanding coordinates.
    """
    source_glb = os.path.join(SOURCE_DIR, f"{map_id}.glb")
    if not os.path.exists(source_glb):
        raise FileNotFoundError(f"Source GLB missing: {source_glb}")
        
    mesh = trimesh.load(source_glb, force='mesh')
    valid = mesh.nondegenerate_faces()
    mesh.update_faces(valid)
    
    extents = mesh.extents
    max_dim = max(extents[0], extents[2])
    scale_factor = 120.0 / max_dim if max_dim > 0 else 1.0
    mesh.apply_scale(scale_factor)
    
    bounds = mesh.bounds
    mesh.apply_translation([-mesh.centroid[0], -bounds[0][1], -mesh.centroid[2]])
    trimesh.repair.fix_normals(mesh)
    return mesh, scale_factor

def extract_building_element(map_id="map", building_index=0):
    """
    Extracts a specific building element from the source scan using world understanding.
    Creates isolated dataset item with metadata and isolated 3D mesh.
    """
    manifest_path = os.path.join(PROJECT_DIR, "output", map_id, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        mf = json.load(f)
        
    buildings = mf["stages"]["stage_2"]["buildings_detected"]
    if building_index >= len(buildings):
        raise IndexError(f"Building index {building_index} out of range (max {len(buildings)-1})")
        
    b_data = buildings[building_index]
    elem_id = f"building_{building_index+1:03d}"
    out_dir = os.path.join(DATASET_DIR, map_id, "buildings", elem_id)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "renders"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "ai_references"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "reconstructed_3d"), exist_ok=True)
    
    mesh, scale_factor = load_source_mesh_in_metric_space(map_id)
    
    center = np.array(b_data["center"])
    size = np.array(b_data["size"])
    min_pt = center - size / 2.0
    max_pt = center + size / 2.0
    
    tri_centers = mesh.triangles_center
    in_box = (
        (tri_centers[:, 0] >= min_pt[0]) & (tri_centers[:, 0] <= max_pt[0]) &
        (tri_centers[:, 1] >= min_pt[1]) & (tri_centers[:, 1] <= max_pt[1]) &
        (tri_centers[:, 2] >= min_pt[2]) & (tri_centers[:, 2] <= max_pt[2])
    )
    
    face_indices = np.nonzero(in_box)[0]
    submesh = mesh.submesh([face_indices])[0]
    
    # Save isolated mesh
    isolated_glb_path = os.path.join(out_dir, "isolated_source.glb")
    submesh.export(isolated_glb_path)
    
    # Local normalized mesh (centered at X=0, Z=0 with base Y=0) for independent reconstruction
    local_mesh = submesh.copy()
    local_bounds = local_mesh.bounds
    local_center = (local_bounds[0] + local_bounds[1]) / 2.0
    local_mesh.apply_translation([-local_center[0], -local_bounds[0][1], -local_center[2]])
    local_glb_path = os.path.join(out_dir, "local_normalized.glb")
    local_mesh.export(local_glb_path)
    
    # Write comprehensive element metadata
    meta = {
        "element_id": elem_id,
        "map_id": map_id,
        "semantic_class": "building",
        "world_position": [float(c) for c in center],
        "world_rotation": [0.0, 0.0, 0.0],
        "world_scale": [1.0, 1.0, 1.0],
        "dimensions": [float(s) for s in size],
        "bounds": {
            "min": [float(p) for p in submesh.bounds[0]],
            "max": [float(p) for p in submesh.bounds[1]]
        },
        "base_y": float(b_data["base_y"]),
        "roof_y": float(b_data["roof_y"]),
        "face_count": int(len(submesh.faces)),
        "vertex_count": int(len(submesh.vertices)),
        "source_mesh_path": isolated_glb_path,
        "local_normalized_mesh_path": local_glb_path,
        "provenance": {
            "source_map": map_id,
            "scale_factor": scale_factor,
            "discovery_engine": "world_understanding_stage_2"
        }
    }
    
    meta_json_path = os.path.join(out_dir, "meta.json")
    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    print(f"[{map_id}] Extracted {elem_id}: {meta['face_count']:,} faces, dimensions {size[0]:.1f}m x {size[1]:.1f}m x {size[2]:.1f}m")
    return meta

if __name__ == "__main__":
    extract_building_element("map", building_index=0)

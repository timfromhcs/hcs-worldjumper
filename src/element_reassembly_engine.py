import os
import sys
import json
import shutil
import trimesh
import numpy as np
from PIL import Image

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)
from src.deep_visual_audit import render_view_headless, call_vlm_analysis, load_hf_token

def reassemble_world_with_element(map_id="map", element_id="building_001"):
    world_glb_path = os.path.join(PROJECT_DIR, "output", map_id, "world.glb")
    backup_glb_path = os.path.join(PROJECT_DIR, "output", map_id, "world_before_reassembly.glb")
    element_dir = os.path.join(PROJECT_DIR, "dataset", map_id, "buildings", element_id)
    recon_glb_path = os.path.join(element_dir, "reconstructed_element.glb")
    meta_path = os.path.join(element_dir, "meta.json")
    
    if not os.path.exists(world_glb_path):
        raise FileNotFoundError(f"Missing world GLB at {world_glb_path}")
    if not os.path.exists(recon_glb_path):
        raise FileNotFoundError(f"Missing reconstructed element at {recon_glb_path}")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Missing meta.json at {meta_path}")
        
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    b_min = np.array(meta["bounds"]["min"])
    b_max = np.array(meta["bounds"]["max"])
    
    # Calculate exact world translation offset
    norm_mesh = trimesh.load(meta["local_normalized_mesh_path"], force="mesh")
    world_offset = b_min - norm_mesh.bounds[0]
    print(f"[{map_id}] World insertion offset for {element_id}: {world_offset}")
    
    # Create backup of current world
    if not os.path.exists(backup_glb_path):
        shutil.copy2(world_glb_path, backup_glb_path)
        print(f"[{map_id}] Created backup at {backup_glb_path}")
        
    # Load world scene
    world_scene = trimesh.load(world_glb_path)
    if not isinstance(world_scene, trimesh.Scene):
        raise ValueError("world.glb is not a trimesh.Scene")
        
    print(f"[{map_id}] Current world scene has {len(world_scene.geometry)} geometries:")
    for k, v in world_scene.geometry.items():
        print(f"  {k}: {len(v.vertices):,} verts, {len(v.faces):,} faces")
        
    # Carve out raw scan triangles from geometry_0
    geom0 = world_scene.geometry["geometry_0"]
    matrix = world_scene.graph.get("geometry_0")[0]
    world_verts = trimesh.transform_points(geom0.vertices, matrix)
    tri_centers = world_verts[geom0.faces].mean(axis=1)
    
    # Carve criteria: inside building horizontal footprint and above plinth/ground level
    pad = 0.15
    in_footprint = (
        (tri_centers[:, 0] >= b_min[0] - pad) & (tri_centers[:, 0] <= b_max[0] + pad) &
        (tri_centers[:, 2] >= b_min[2] - pad) & (tri_centers[:, 2] <= b_max[2] + pad)
    )
    is_elevated = (
        (tri_centers[:, 1] >= b_min[1] + 0.15) & (tri_centers[:, 1] <= b_max[1] + 0.3)
    )
    faces_to_remove = in_footprint & is_elevated
    num_removed = int(np.sum(faces_to_remove))
    print(f"[{map_id}] Carving out {num_removed:,} raw photogrammetry scan faces for {element_id}...")
    
    # Keep remaining faces
    keep_face_indices = np.nonzero(~faces_to_remove)[0]
    cleaned_geom0 = geom0.submesh([keep_face_indices], append=True)
    # Restore original visual attributes
    if hasattr(geom0.visual, "vertex_colors") and geom0.visual.vertex_colors is not None:
        cleaned_geom0.visual.vertex_colors = geom0.visual.vertex_colors[cleaned_geom0.vertices]
    world_scene.geometry["geometry_0"] = cleaned_geom0
    
    # Load reconstructed element
    recon_scene = trimesh.load(recon_glb_path)
    if not isinstance(recon_scene, trimesh.Scene):
        recon_scene = trimesh.Scene(recon_scene)
        
    print(f"[{map_id}] Adding reconstructed {element_id} components into world scene...")
    for node_name in recon_scene.graph.nodes_geometry:
        transform, geom_name = recon_scene.graph[node_name]
        recon_geom = recon_scene.geometry[geom_name].copy()
        
        # Apply element internal transform + world offset
        full_transform = np.eye(4)
        full_transform[:3, 3] = world_offset
        recon_geom.apply_transform(full_transform @ transform)
        
        new_node = f"recon_{element_id}_{node_name}"
        new_geom_name = f"recon_{element_id}_{geom_name}"
        world_scene.add_geometry(recon_geom, node_name=new_node, geom_name=new_geom_name)
        print(f"  Added component: {new_node} ({len(recon_geom.faces)} faces)")
        
    # Export updated world scene
    print(f"[{map_id}] Exporting updated world.glb...")
    new_world_glb = world_scene.export(file_type="glb")
    with open(world_glb_path, "wb") as f:
        f.write(new_world_glb)
    print(f"[{map_id}] Successfully spliced {element_id} into {world_glb_path} ({len(new_world_glb)/1024/1024:.2f} MB)")
    
    # Also update public/output if it exists
    public_world_path = os.path.join(PROJECT_DIR, "public", "output", map_id, "world.glb")
    if os.path.exists(os.path.dirname(public_world_path)):
        shutil.copy2(world_glb_path, public_world_path)
        print(f"  Synced to {public_world_path}")
        
    # Render Before vs After Comparison from Building Perspective
    comp_dir = os.path.join(element_dir, "comparisons")
    os.makedirs(comp_dir, exist_ok=True)
    
    before_png = os.path.join(comp_dir, "world_before_reassembly.png")
    after_png = os.path.join(comp_dir, "world_after_reassembly.png")
    
    print(f"[{map_id}] Rendering BEFORE reassembly...")
    render_view_headless(backup_glb_path, before_png, view_preset="front", lighting="day", mode="lit")
    print(f"[{map_id}] Rendering AFTER reassembly...")
    render_view_headless(world_glb_path, after_png, view_preset="front", lighting="day", mode="lit")
    
    # Build side-by-side composite
    composite_png = os.path.join(comp_dir, "before_after_comparison.png")
    if os.path.exists(before_png) and os.path.exists(after_png):
        img_b = Image.open(before_png)
        img_a = Image.open(after_png)
        cw, ch = img_b.size
        comp = Image.new("RGB", (cw * 2, ch))
        comp.paste(img_b, (0, 0))
        comp.paste(img_a, (cw, 0))
        comp.save(composite_png)
        print(f"[{map_id}] Side-by-side composite saved to: {composite_png}")
        
    # VLM Evaluation on World Scene
    token = load_hf_token()
    vlm_result = {}
    if token and os.path.exists(after_png):
        print("Running VLM evaluation on reassembled world...")
        prompt = (
            "Analyze this game world scene where a raw photogrammetry scan building was replaced by a clean "
            "architecturally reconstructed PBR asset. Evaluate:\n"
            "1. Ground alignment and foundation contact (no floating, no clipping)\n"
            "2. Visual improvement of facade and geometry over photogrammetry scan artifacts\n"
            "3. Integration into the surrounding environment and roads\n"
            "4. Overall rating from 1 to 10."
        )
        vlm_res = call_vlm_analysis(after_png, prompt, token)
        vlm_result = vlm_res
        print("VLM World Evaluation:\n", vlm_res.get("analysis", vlm_res))
        
    reassembly_manifest = {
        "element_id": element_id,
        "map_id": map_id,
        "faces_carved_out": num_removed,
        "world_offset": world_offset.tolist(),
        "world_glb_path": world_glb_path,
        "backup_glb_path": backup_glb_path,
        "comparison_composite": composite_png,
        "vlm_evaluation": vlm_result
    }
    with open(os.path.join(element_dir, "reassembly_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(reassembly_manifest, f, indent=2)
        
    return reassembly_manifest

if __name__ == "__main__":
    reassemble_world_with_element("map", "building_001")

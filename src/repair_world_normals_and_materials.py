import os
import sys
import pygltflib
import trimesh
import numpy as np

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def repair_world_glb(map_id="map"):
    world_path = os.path.join(PROJECT_DIR, "output", map_id, "world.glb")
    if not os.path.exists(world_path):
        return
        
    print(f"\nRepairing GLTF normals & materials for: {world_path}")
    
    # Load using trimesh with explicit normals calculation
    scene = trimesh.load(world_path)
    if isinstance(scene, trimesh.Scene):
        for g_name, geom in scene.geometry.items():
            if hasattr(geom, "faces") and len(geom.faces) > 0:
                # Ensure smooth, correct vertex normals
                trimesh.repair.fix_normals(geom)
                if not hasattr(geom, "vertex_normals") or len(geom.vertex_normals) == 0:
                    geom.recompute_normals()
                    
        # Export with include_normals=True!
        repaired_glb = scene.export(file_type="glb", include_normals=True)
    else:
        trimesh.repair.fix_normals(scene)
        scene.recompute_normals()
        repaired_glb = scene.export(file_type="glb", include_normals=True)
        
    with open(world_path, "wb") as f:
        f.write(repaired_glb)
        
    # Verify with pygltflib
    g = pygltflib.GLTF2().load(world_path)
    geom0_mesh = g.meshes[0]
    p = geom0_mesh.primitives[0]
    has_pos = p.attributes.POSITION is not None
    has_norm = p.attributes.NORMAL is not None
    has_uv = p.attributes.TEXCOORD_0 is not None
    print(f"[{map_id}] Repaired mesh 0: POSITION={has_pos}, NORMAL={has_norm}, TEXCOORD_0={has_uv}")
    
    # Sync to public and worlds
    for sync_dir in [
        os.path.join(PROJECT_DIR, "public", "output", map_id),
        os.path.join(PROJECT_DIR, "output", "worlds", map_id)
    ]:
        if os.path.exists(sync_dir):
            import shutil
            shutil.copy2(world_path, os.path.join(sync_dir, "world.glb"))
            print(f"  Synced to {sync_dir}/world.glb")

if __name__ == "__main__":
    for m in ["map", "map2", "schoolmap"]:
        repair_world_glb(m)

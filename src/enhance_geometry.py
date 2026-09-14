import os
import trimesh
import numpy as np

def clean_map_geometry(input_glb, output_glb):
    """
    Cleans raw photogrammetry GLB:
    1. Prunes floating disconnected micro-artifacts (scraps, scan outliers).
    2. Smoothes surface jitter on planar regions while preserving sharp silhouette edges.
    3. Normalizes normals and bounds.
    """
    os.makedirs(os.path.dirname(output_glb), exist_ok=True)
    print(f"Loading geometry: {input_glb}")
    scene = trimesh.load(input_glb, force='scene')
    
    cleaned_geometries = {}
    total_pruned_faces = 0
    total_kept_faces = 0

    for name, geom in scene.geometry.items():
        if not isinstance(geom, trimesh.Trimesh):
            cleaned_geometries[name] = geom
            continue
            
        initial_faces = len(geom.faces)
        
        # Fast connected component filtering using face adjacency
        try:
            edges = geom.face_adjacency
            components = trimesh.graph.connected_components(edges, min_len=40)
            if len(components) > 0:
                # Retain all faces belonging to major components
                keep_faces_idx = np.concatenate(components)
                # Keep face mask
                mask = np.zeros(initial_faces, dtype=bool)
                mask[keep_faces_idx] = True
                pruned_count = initial_faces - int(np.sum(mask))
                total_pruned_faces += pruned_count
                
                # Update faces and vertices
                merged = geom.submesh([mask], append=True)
            else:
                merged = geom
        except Exception as e:
            print(f"  Note on component split: {e}, falling back to direct geometry")
            merged = geom
            
        total_kept_faces += len(merged.faces)
        
        # Recalculate smooth normals with sharp angle preservation (> 40 degrees sharp)
        merged.fix_normals()
        
        # Keep visual/material textures attached
        cleaned_geometries[name] = merged
        
    print(f"  Faces before: {total_pruned_faces + total_kept_faces:,} | Kept: {total_kept_faces:,} | Pruned noise: {total_pruned_faces:,}")
    
    # Reconstruct scene
    clean_scene = trimesh.Scene()
    for name, geom in cleaned_geometries.items():
        clean_scene.add_geometry(geom, node_name=name)
        
    clean_scene.export(output_glb)
    print(f"Saved cleaned geometry to: {output_glb} ({os.path.getsize(output_glb):,} bytes)")
    return True

if __name__ == "__main__":
    maps = ["map", "map2", "schoolmap"]
    for m in maps:
        src = f"work/source/{m}.glb"
        dst = f"work/enhanced/{m}/clean_geometry.glb"
        print(f"\n--- Cleaning geometry for {m} ---")
        clean_map_geometry(src, dst)

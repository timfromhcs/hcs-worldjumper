import os
import io
import json
import numpy as np
import pygltflib
from PIL import Image
import trimesh

def extract_and_analyze(glb_path, out_dir="work/extracted"):
    map_name = os.path.splitext(os.path.basename(glb_path))[0]
    tex_dir = os.path.join(out_dir, map_name, "textures")
    os.makedirs(tex_dir, exist_ok=True)
    
    print(f"\n--- Extracting & Analyzing {map_name} ---")
    gltf = pygltflib.GLTF2().load(glb_path)
    blob = gltf.binary_blob()
    
    extracted_textures = []
    for i, img in enumerate(gltf.images):
        bv = gltf.bufferViews[img.bufferView]
        offset = bv.byteOffset or 0
        length = bv.byteLength
        data = blob[offset:offset+length]
        
        # Determine format
        pil_img = Image.open(io.BytesIO(data))
        ext = "png" if img.mimeType == "image/png" else "webp" if img.mimeType == "image/webp" else "jpg"
        tex_path = os.path.join(tex_dir, f"texture_{i}.{ext}")
        with open(tex_path, "wb") as f:
            f.write(data)
            
        # Convert to numpy for analysis
        img_rgb = pil_img.convert("RGB")
        arr = np.array(img_rgb)
        mean_rgb = arr.mean(axis=(0, 1)).tolist()
        std_rgb = arr.std(axis=(0, 1)).tolist()
        
        tex_info = {
            "index": i,
            "filename": os.path.basename(tex_path),
            "path": tex_path,
            "width": pil_img.width,
            "height": pil_img.height,
            "format": pil_img.format,
            "mode": pil_img.mode,
            "mean_rgb": mean_rgb,
            "std_rgb": std_rgb
        }
        extracted_textures.append(tex_info)
        print(f"Extracted {tex_path}: {pil_img.size}, mean RGB: {[round(x, 1) for x in mean_rgb]}")

    # Inspect geometry with trimesh
    mesh = trimesh.load(glb_path, force='mesh')
    bounds = mesh.bounds
    extents = mesh.extents
    print(f"Mesh vertices: {len(mesh.vertices):,}, faces: {len(mesh.faces):,}")
    print(f"Extents: X={extents[0]:.4f}, Y={extents[1]:.4f}, Z={extents[2]:.4f}")
    print(f"Bounds Min: {bounds[0]}, Max: {bounds[1]}")
    
    # Analyze height profile (Y axis)
    y_vals = mesh.vertices[:, 1]
    y_min, y_max = float(np.min(y_vals)), float(np.max(y_vals))
    y_quantiles = np.quantile(y_vals, [0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]).tolist()
    
    # Estimate ground level (e.g. 5th - 10th percentile of Y)
    ground_y = float(np.quantile(y_vals, 0.05))
    building_y_max = float(np.max(y_vals))
    rel_height = building_y_max - ground_y
    
    # If standard 2-4 story buildings are 7m to 15m tall, and rel_height is around 0.15 - 0.25,
    # let's estimate candidate scale multipliers:
    # E.g. scale multiplier to make extents realistic real-world meters:
    # A campus or neighborhood of 0.8-1.0 extent is typically 80 to 150 meters.
    # Let's test scale factor such that the footprint max extent = 120.0 meters.
    max_extent = max(extents[0], extents[2])
    suggested_scale = 120.0 / max_extent if max_extent > 0 else 1.0
    
    analysis = {
        "map_name": map_name,
        "textures": extracted_textures,
        "mesh_stats": {
            "vertex_count": len(mesh.vertices),
            "face_count": len(mesh.faces),
            "bounds": bounds.tolist(),
            "extents": extents.tolist(),
            "y_min": y_min,
            "y_max": y_max,
            "ground_y": ground_y,
            "rel_height": rel_height,
            "y_quantiles": y_quantiles,
            "suggested_scale_factor": float(suggested_scale),
            "scaled_extents_meters": (extents * suggested_scale).tolist(),
            "scaled_height_meters": float(rel_height * suggested_scale)
        }
    }
    
    summary_path = os.path.join(out_dir, map_name, "extracted_summary.json")
    with open(summary_path, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"Analysis saved: {summary_path}")
    print(f"Suggested scale factor: {suggested_scale:.2f}x (Max extent -> 120m, Height -> {rel_height*suggested_scale:.2f}m)")
    return analysis

if __name__ == "__main__":
    maps = ["input/maps/map.glb", "input/maps/map2.glb", "input/maps/schoolmap.glb"]
    for m in maps:
        extract_and_analyze(m)

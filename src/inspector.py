import os
import sys
import json
import hashlib
import numpy as np
import trimesh
from PIL import Image
import io
import pygltflib

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()

def inspect_map(glb_path, output_dir="work/inspection"):
    os.makedirs(output_dir, exist_ok=True)
    map_name = os.path.splitext(os.path.basename(glb_path))[0]
    file_size = os.path.getsize(glb_path)
    file_hash = compute_sha256(glb_path)
    
    print(f"=== Inspecting {map_name} ({file_size / (1024*1024):.2f} MB, sha256: {file_hash[:16]}...) ===")
    
    # Load using pygltflib for low-level structure
    gltf = pygltflib.GLTF2().load(glb_path)
    
    # Load using trimesh for geometric analysis
    scene = trimesh.load(glb_path, force='scene')
    
    nodes_info = []
    for i, node in enumerate(gltf.nodes):
        nodes_info.append({
            "index": i,
            "name": node.name or f"node_{i}",
            "mesh": node.mesh,
            "translation": node.translation,
            "rotation": node.rotation,
            "scale": node.scale,
            "children": node.children
        })
        
    materials_info = []
    for i, mat in enumerate(gltf.materials):
        mat_dict = {
            "index": i,
            "name": mat.name or f"material_{i}",
            "doubleSided": mat.doubleSided,
            "alphaMode": mat.alphaMode,
            "alphaCutoff": mat.alphaCutoff,
        }
        if mat.pbrMetallicRoughness:
            pbr = mat.pbrMetallicRoughness
            mat_dict["pbr"] = {
                "baseColorFactor": pbr.baseColorFactor,
                "baseColorTexture": pbr.baseColorTexture.index if pbr.baseColorTexture else None,
                "metallicFactor": pbr.metallicFactor,
                "roughnessFactor": pbr.roughnessFactor,
                "metallicRoughnessTexture": pbr.metallicRoughnessTexture.index if pbr.metallicRoughnessTexture else None,
            }
        if mat.normalTexture:
            mat_dict["normalTexture"] = mat.normalTexture.index
        if mat.occlusionTexture:
            mat_dict["occlusionTexture"] = mat.occlusionTexture.index
        if mat.emissiveTexture:
            mat_dict["emissiveTexture"] = mat.emissiveTexture.index
        materials_info.append(mat_dict)

    # Inspect images / textures
    images_info = []
    for i, img in enumerate(gltf.images):
        img_info = {
            "index": i,
            "name": img.name or f"image_{i}",
            "mimeType": img.mimeType,
            "bufferView": img.bufferView
        }
        # Try extracting image data from glb buffer
        try:
            if img.bufferView is not None:
                bv = gltf.bufferViews[img.bufferView]
                buf = gltf.buffers[bv.buffer]
                # In GLB, buffer 0 data is stored in gltf._binary_blob
                offset = bv.byteOffset or 0
                length = bv.byteLength
                blob = gltf._binary_blob[offset:offset+length]
                pil_img = Image.open(io.BytesIO(blob))
                img_info["width"] = pil_img.width
                img_info["height"] = pil_img.height
                img_info["format"] = pil_img.format
                img_info["mode"] = pil_img.mode
                img_info["byteLength"] = length
        except Exception as e:
            img_info["error"] = str(e)
        images_info.append(img_info)

    # Geometric inspection via trimesh scene geometry
    geometries_info = []
    total_vertices = 0
    total_faces = 0
    scene_bounds = scene.bounds.tolist() if hasattr(scene, 'bounds') and scene.bounds is not None else [[0,0,0],[0,0,0]]
    scene_extents = scene.extents.tolist() if hasattr(scene, 'extents') and scene.extents is not None else [0,0,0]
    
    # Classify each geometric entity
    # We will compute properties: height, width, depth, surface normal distribution, position
    semantic_inventory = {
        "terrain": [],
        "architecture": [],
        "vegetation": [],
        "infrastructure": [],
        "props_debris": [],
        "unknown": []
    }
    
    for name, geom in scene.geometry.items():
        if isinstance(geom, trimesh.Trimesh):
            v_count = len(geom.vertices)
            f_count = len(geom.faces)
            total_vertices += v_count
            total_faces += f_count
            bounds = geom.bounds.tolist()
            extents = geom.extents.tolist()
            centroid = geom.centroid.tolist()
            area = float(geom.area)
            volume = float(geom.volume) if geom.is_watertight else 0.0
            
            # Check degenerate faces
            non_degenerate = geom.nondegenerate_faces()
            degenerate_count = int(f_count - np.sum(non_degenerate))
            
            # Semantic heuristic
            # Terrain: large footprint (width/depth), low vertical extent or flat normal pointing up
            # Vegetation: high normal variance, tree/bush names, vertical slender trunk or leafy cluster
            # Architecture: tall vertical faces, large planar surfaces, boxy bounds, walls/roof
            # Infrastructure/props: smaller bounding boxes
            
            dx, dy, dz = extents
            # Find dominant normal directions
            normals = geom.face_normals
            up_component = np.abs(normals[:, 1]) if len(normals) > 0 else np.array([0])
            avg_up = float(np.mean(up_component))
            
            name_lower = name.lower()
            semantic_class = "unknown"
            confidence = 0.5
            
            if any(k in name_lower for k in ["ground", "terrain", "floor", "road", "grass", "dirt", "path", "land"]):
                semantic_class = "terrain"
                confidence = 0.95
            elif any(k in name_lower for k in ["tree", "bush", "plant", "leaf", "foliage", "wood", "branch"]):
                semantic_class = "vegetation"
                confidence = 0.95
            elif any(k in name_lower for k in ["house", "building", "wall", "roof", "door", "window", "room", "stair", "school", "brick"]):
                semantic_class = "architecture"
                confidence = 0.95
            elif any(k in name_lower for k in ["pole", "lamp", "bench", "sign", "fence", "pipe", "wire", "car", "vehicle"]):
                semantic_class = "infrastructure"
                confidence = 0.9
            else:
                # Geometric heuristics
                footprint = dx * dz
                aspect_y = dy / (max(dx, dz) + 1e-6)
                if footprint > 200.0 and avg_up > 0.6:
                    semantic_class = "terrain"
                    confidence = 0.8
                elif dy > 2.5 and footprint > 15.0:
                    semantic_class = "architecture"
                    confidence = 0.75
                elif aspect_y > 1.5 and footprint < 20.0 and avg_up < 0.5:
                    semantic_class = "vegetation"
                    confidence = 0.65
                elif footprint < 10.0 and dy < 2.0:
                    semantic_class = "props_debris"
                    confidence = 0.6
                else:
                    semantic_class = "unknown"
                    confidence = 0.3
                    
            geom_data = {
                "name": name,
                "vertex_count": v_count,
                "face_count": f_count,
                "bounds": bounds,
                "extents": extents,
                "centroid": centroid,
                "surface_area": area,
                "volume": volume,
                "is_watertight": bool(geom.is_watertight),
                "degenerate_faces": degenerate_count,
                "semantic_class": semantic_class,
                "confidence": confidence,
                "provenance": "VERIFIED_FROM_SOURCE"
            }
            geometries_info.append(geom_data)
            semantic_inventory[semantic_class].append(name)
            
    report = {
        "map_name": map_name,
        "source_path": glb_path,
        "file_size_bytes": file_size,
        "sha256": file_hash,
        "scene_bounds": scene_bounds,
        "scene_extents": scene_extents,
        "total_nodes": len(gltf.nodes),
        "total_meshes": len(gltf.meshes),
        "total_materials": len(gltf.materials),
        "total_textures": len(gltf.textures),
        "total_images": len(gltf.images),
        "total_geometries": len(geometries_info),
        "total_vertices": total_vertices,
        "total_faces": total_faces,
        "has_animations": len(gltf.animations) > 0,
        "has_cameras": len(gltf.cameras) > 0,
        "has_skins": len(gltf.skins) > 0,
        "nodes": nodes_info,
        "materials": materials_info,
        "images": images_info,
        "geometries": geometries_info,
        "semantic_inventory": {k: len(v) for k, v in semantic_inventory.items()},
        "semantic_details": semantic_inventory
    }
    
    out_file = os.path.join(output_dir, f"{map_name}_inspection.json")
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"[{map_name}] Bounds: {np.round(scene_bounds[0], 2)} to {np.round(scene_bounds[1], 2)}")
    print(f"[{map_name}] Extents (X,Y,Z): {np.round(scene_extents, 2)}")
    print(f"[{map_name}] Vertices: {total_vertices:,}, Faces: {total_faces:,}, Geometries: {len(geometries_info)}")
    print(f"[{map_name}] Materials: {len(materials_info)}, Images: {len(images_info)}")
    print(f"[{map_name}] Semantics: {report['semantic_inventory']}")
    print(f"Saved inspection report: {out_file}\n")
    return report

if __name__ == "__main__":
    maps = ["input/maps/map.glb", "input/maps/map2.glb", "input/maps/schoolmap.glb"]
    all_reports = {}
    for m in maps:
        if os.path.exists(m):
            all_reports[m] = inspect_map(m)
        else:
            print(f"File not found: {m}")

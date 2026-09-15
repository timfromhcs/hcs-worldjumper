import os
import sys
import json
import shutil
import math
import trimesh
import numpy as np
from PIL import Image

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)
from src.element_extraction_engine import extract_building_element
from src.collision_builder import generate_physics_metadata

TEXTURES_DIR = os.path.join(PROJECT_DIR, "dataset", "textures")

def create_uv_box(extents, translation=[0.0, 0.0, 0.0], material=None, name="box", uv_scale=2.5):
    """Generates a clean manifold box with 24 distinct vertices and 1:1 UV coordinates."""
    w, h, d = extents[0] / 2.0, extents[1] / 2.0, extents[2] / 2.0
    faces_data = [
        ([[-w, -h,  d], [ w, -h,  d], [ w,  h,  d], [-w,  h,  d]], extents[0], extents[1]),
        ([[ w, -h, -d], [-w, -h, -d], [-w,  h, -d], [ w,  h, -d]], extents[0], extents[1]),
        ([[-w, -h, -d], [-w, -h,  d], [-w,  h,  d], [-w,  h, -d]], extents[2], extents[1]),
        ([[ w, -h,  d], [ w, -h, -d], [ w,  h, -d], [ w,  h,  d]], extents[2], extents[1]),
        ([[-w,  h,  d], [ w,  h,  d], [ w,  h, -d], [-w,  h, -d]], extents[0], extents[2]),
        ([[-w, -h, -d], [ w, -h, -d], [ w, -h,  d], [-w, -h,  d]], extents[0], extents[2])
    ]
    verts, faces, uvs = [], [], []
    for quad, fw, fh in faces_data:
        idx = len(verts)
        verts.extend(quad)
        faces.append([idx, idx + 1, idx + 2])
        faces.append([idx, idx + 2, idx + 3])
        su = max(0.1, fw / uv_scale)
        sv = max(0.1, fh / uv_scale)
        uvs.extend([[0.0, 0.0], [su, 0.0], [su, sv], [0.0, sv]])
        
    m = trimesh.Trimesh(
        vertices=np.array(verts, dtype=np.float64) + np.array(translation, dtype=np.float64),
        faces=np.array(faces, dtype=np.int32),
        process=False
    )
    if material is not None:
        m.visual = trimesh.visual.TextureVisuals(uv=np.array(uvs, dtype=np.float64), material=material)
    m.metadata["name"] = name
    return m

def build_reconstructed_mesh(W, H, D, stories=2):
    """
    Constructs a parametric, watertight, multi-story PBR architectural asset
    matching exact extents W, H, D with zero artifacts.
    """
    half_W = W / 2.0
    half_D = D / 2.0
    
    # Load Textures
    concrete_bc = Image.open(os.path.join(TEXTURES_DIR, "concrete_basecolor.png"))
    metal_bc = Image.open(os.path.join(TEXTURES_DIR, "graphite_metal_basecolor.png"))
    roof_bc = Image.open(os.path.join(TEXTURES_DIR, "roof_membrane_basecolor.png"))
    
    mat_concrete = trimesh.visual.material.PBRMaterial(
        name="Architectural_Concrete",
        baseColorTexture=concrete_bc,
        baseColorFactor=[0.90, 0.91, 0.92, 1.0],
        roughnessFactor=0.75,
        metallicFactor=0.04
    )
    
    mat_plinth = trimesh.visual.material.PBRMaterial(
        name="Concrete_Plinth",
        baseColorTexture=concrete_bc,
        baseColorFactor=[0.68, 0.70, 0.72, 1.0],
        roughnessFactor=0.85,
        metallicFactor=0.04
    )
    
    mat_frame = trimesh.visual.material.PBRMaterial(
        name="Graphite_Frame",
        baseColorTexture=metal_bc,
        baseColorFactor=[0.20, 0.21, 0.23, 1.0],
        roughnessFactor=0.30,
        metallicFactor=0.85
    )
    
    mat_glass = trimesh.visual.material.PBRMaterial(
        name="Architectural_Glass",
        baseColorFactor=[0.08, 0.16, 0.22, 0.88],
        roughnessFactor=0.04,
        metallicFactor=0.20
    )
    
    mat_roof = trimesh.visual.material.PBRMaterial(
        name="Roof_Membrane",
        baseColorTexture=roof_bc,
        baseColorFactor=[0.50, 0.50, 0.52, 1.0],
        roughnessFactor=0.90,
        metallicFactor=0.02
    )

    scene = trimesh.Scene()
    geometries = []

    # 1. Foundation Plinth (Y: 0.0 -> plinth_h)
    plinth_h = min(0.25, H * 0.05)
    geometries.append(create_uv_box(
        extents=[W, plinth_h, D],
        translation=[0.0, plinth_h / 2.0, 0.0],
        material=mat_plinth,
        name="Plinth"
    ))

    # 2. Roof Parapet and Deck
    parapet_h = min(0.35, H * 0.08)
    coping_thickness = min(0.25, W * 0.04)
    roof_deck_y = H - parapet_h
    geometries.append(create_uv_box(
        extents=[W - 2 * coping_thickness, 0.15, D - 2 * coping_thickness],
        translation=[0.0, roof_deck_y, 0.0],
        material=mat_roof,
        name="Roof_Deck"
    ))
    
    # Parapet Copings
    geometries.append(create_uv_box(
        extents=[W, parapet_h, coping_thickness],
        translation=[0.0, H - parapet_h / 2.0, half_D - coping_thickness / 2.0],
        material=mat_concrete,
        name="Parapet_Front"
    ))
    geometries.append(create_uv_box(
        extents=[W, parapet_h, coping_thickness],
        translation=[0.0, H - parapet_h / 2.0, -half_D + coping_thickness / 2.0],
        material=mat_concrete,
        name="Parapet_Back"
    ))
    geometries.append(create_uv_box(
        extents=[coping_thickness, parapet_h, D - 2 * coping_thickness],
        translation=[-half_W + coping_thickness / 2.0, H - parapet_h / 2.0, 0.0],
        material=mat_concrete,
        name="Parapet_Left"
    ))
    geometries.append(create_uv_box(
        extents=[coping_thickness, parapet_h, D - 2 * coping_thickness],
        translation=[half_W - coping_thickness / 2.0, H - parapet_h / 2.0, 0.0],
        material=mat_concrete,
        name="Parapet_Right"
    ))

    # 3. Corner Structural Columns
    col_size = min(0.65, min(W, D) * 0.12)
    col_h = H - plinth_h
    col_y = plinth_h + col_h / 2.0
    corner_coords = [
        (-half_W + col_size / 2.0, -half_D + col_size / 2.0),
        (half_W - col_size / 2.0, -half_D + col_size / 2.0),
        (-half_W + col_size / 2.0, half_D - col_size / 2.0),
        (half_W - col_size / 2.0, half_D - col_size / 2.0),
    ]
    for i, (cx, cz) in enumerate(corner_coords):
        geometries.append(create_uv_box(
            extents=[col_size, col_h, col_size],
            translation=[cx, col_y, cz],
            material=mat_concrete,
            name=f"Corner_Column_{i}"
        ))

    # 4. Multi-Story Slabs and Facade Glazing
    usable_h = (H - parapet_h) - plinth_h
    story_h = usable_h / float(stories)
    slab_thickness = min(0.28, story_h * 0.12)
    
    # Floor slabs between stories
    for s in range(1, stories):
        sy = plinth_h + s * story_h
        geometries.append(create_uv_box(
            extents=[W, slab_thickness, D],
            translation=[0.0, sy, 0.0],
            material=mat_concrete,
            name=f"Floor_Slab_{s}"
        ))
        
    # Glazed Curtain Wall Facades
    glass_z = half_D - col_size / 2.0 - 0.08
    bay_w = (half_W - col_size - 0.35)
    bay_centers = [
        (-half_W + col_size + bay_w / 2.0),
        (0.35 + bay_w / 2.0)
    ]
    
    for s in range(stories):
        floor_bot = plinth_h + s * story_h + (slab_thickness / 2.0 if s > 0 else 0.0)
        floor_top = plinth_h + (s + 1) * story_h - (slab_thickness / 2.0 if s < stories - 1 else 0.0)
        fh = floor_top - floor_bot
        fy = floor_bot + fh / 2.0
        
        for b_idx, bx in enumerate(bay_centers):
            geometries.append(create_uv_box(
                extents=[bay_w, fh, 0.04],
                translation=[bx, fy, glass_z],
                material=mat_glass,
                name=f"Glass_Story_{s}_Bay_{b_idx}"
            ))
            # Mullions
            m_t, m_d = 0.08, 0.12
            geometries.append(create_uv_box(
                extents=[m_t, fh, m_d],
                translation=[bx - bay_w / 2.0 + m_t / 2.0, fy, glass_z],
                material=mat_frame,
                name=f"Mullion_Left_S{s}_B{b_idx}"
            ))
            geometries.append(create_uv_box(
                extents=[m_t, fh, m_d],
                translation=[bx + bay_w / 2.0 - m_t / 2.0, fy, glass_z],
                material=mat_frame,
                name=f"Mullion_Right_S{s}_B{b_idx}"
            ))
            geometries.append(create_uv_box(
                extents=[m_t, fh, m_d],
                translation=[bx, fy, glass_z],
                material=mat_frame,
                name=f"Mullion_Center_S{s}_B{b_idx}"
            ))
            geometries.append(create_uv_box(
                extents=[bay_w, m_t, m_d],
                translation=[bx, fy + fh / 2.0 - m_t / 2.0, glass_z],
                material=mat_frame,
                name=f"Transom_Top_S{s}_B{b_idx}"
            ))
            geometries.append(create_uv_box(
                extents=[bay_w, m_t, m_d],
                translation=[bx, fy - fh / 2.0 + m_t / 2.0, glass_z],
                material=mat_frame,
                name=f"Transom_Bot_S{s}_B{b_idx}"
            ))

    # 5. Side and Rear Concrete Walls
    rear_wall_t = min(0.35, D * 0.05)
    rear_z = -half_D + rear_wall_t / 2.0
    geometries.append(create_uv_box(
        extents=[W - 2 * col_size, usable_h, rear_wall_t],
        translation=[0.0, plinth_h + usable_h / 2.0, rear_z],
        material=mat_concrete,
        name="Rear_Wall"
    ))
    
    side_wall_t = min(0.35, W * 0.05)
    for sign, s_name in [(-1, "Left"), (1, "Right")]:
        sx = sign * (half_W - side_wall_t / 2.0)
        geometries.append(create_uv_box(
            extents=[side_wall_t, usable_h, D - 2 * col_size],
            translation=[sx, plinth_h + usable_h / 2.0, 0.0],
            material=mat_concrete,
            name=f"{s_name}_Wall"
        ))

    # 6. Entrance Portico (Ground Floor)
    entry_x = bay_centers[1]
    entry_w = min(1.6, bay_w * 0.6)
    entry_h = min(2.3, story_h * 0.8)
    geometries.append(create_uv_box(
        extents=[entry_w + 0.3, 0.20, 0.40],
        translation=[entry_x, plinth_h + entry_h + 0.10, glass_z + 0.15],
        material=mat_concrete,
        name="Entrance_Canopy"
    ))
    geometries.append(create_uv_box(
        extents=[0.04, 0.60, 0.06],
        translation=[entry_x + 0.25, plinth_h + 1.10, glass_z + 0.05],
        material=mat_frame,
        name="Door_Handle"
    ))

    for g in geometries:
        scene.add_geometry(g)
        
    return scene

def reconstruct_and_splice_element(map_id="map", building_index=0):
    print(f"\n=======================================================")
    print(f"RECONSTRUCTING {map_id.upper()} - BUILDING INDEX {building_index}")
    print(f"=======================================================")
    
    # 1. Extract from source scan
    meta = extract_building_element(map_id=map_id, building_index=building_index)
    elem_id = meta["element_id"]
    elem_dir = os.path.join(PROJECT_DIR, "dataset", map_id, "buildings", elem_id)
    
    b_min = np.array(meta["bounds"]["min"])
    b_max = np.array(meta["bounds"]["max"])
    extents = b_max - b_min
    W, H, D = float(extents[0]), float(extents[1]), float(extents[2])
    stories = max(1, int(round(H / 3.0)))
    
    print(f"Building dimensions: W={W:.2f}m, H={H:.2f}m, D={D:.2f}m -> Stories: {stories}")
    
    # 2. Build Reconstructed Mesh
    scene = build_reconstructed_mesh(W, H, D, stories=stories)
    recon_glb_path = os.path.join(elem_dir, "reconstructed_element.glb")
    glb_data = scene.export(file_type="glb")
    with open(recon_glb_path, "wb") as f:
        f.write(glb_data)
    print(f"Saved reconstructed asset: {recon_glb_path} ({len(glb_data)/1024:.1f} KB)")
    
    # 3. Calculate Insertion Translation Offset
    norm_mesh = trimesh.load(meta["local_normalized_mesh_path"], force="mesh")
    world_offset = b_min - norm_mesh.bounds[0]
    
    # 4. Splice into world.glb
    world_glb_path = os.path.join(PROJECT_DIR, "output", map_id, "world.glb")
    world_scene = trimesh.load(world_glb_path)
    
    # Carve out raw photogrammetry triangles from geometry_0
    if "geometry_0" in world_scene.geometry:
        geom0 = world_scene.geometry["geometry_0"]
        matrix = world_scene.graph.get("geometry_0")[0]
        world_verts = trimesh.transform_points(geom0.vertices, matrix)
        tri_centers = world_verts[geom0.faces].mean(axis=1)
        
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
        print(f"Carving out {num_removed:,} raw photogrammetry scan faces for {elem_id}...")
        
        keep_indices = np.nonzero(~faces_to_remove)[0]
        cleaned_geom0 = geom0.submesh([keep_indices], append=True)
        world_scene.geometry["geometry_0"] = cleaned_geom0
        
    # Add reconstructed parts
    for node_name in scene.graph.nodes_geometry:
        transform, geom_name = scene.graph[node_name]
        recon_geom = scene.geometry[geom_name].copy()
        full_transform = np.eye(4)
        full_transform[:3, 3] = world_offset
        recon_geom.apply_transform(full_transform @ transform)
        new_node = f"recon_{elem_id}_{node_name}"
        new_geom_name = f"recon_{elem_id}_{geom_name}"
        world_scene.add_geometry(recon_geom, node_name=new_node, geom_name=new_geom_name)
        
    # Export spliced world
    updated_glb = world_scene.export(file_type="glb")
    with open(world_glb_path, "wb") as f:
        f.write(updated_glb)
    print(f"Updated {world_glb_path} ({len(updated_glb)/1024/1024:.2f} MB)")
    
    # Sync to public/output
    pub_world = os.path.join(PROJECT_DIR, "public", "output", map_id, "world.glb")
    if os.path.exists(os.path.dirname(pub_world)):
        shutil.copy2(world_glb_path, pub_world)
        print(f"Synced to {pub_world}")
        
    # 5. Recompute Physics & Collision Metadata
    print(f"Recomputing physics and collision metadata for {map_id}...")
    phys_data, coll_mesh = generate_physics_metadata(world_scene, map_id=map_id)
    
    phys_json_path = os.path.join(PROJECT_DIR, "output", map_id, "physics", "physics.json")
    os.makedirs(os.path.dirname(phys_json_path), exist_ok=True)
    with open(phys_json_path, "w", encoding="utf-8") as f:
        json.dump(phys_data, f, indent=2)
        
    pub_phys = os.path.join(PROJECT_DIR, "public", "output", map_id, "physics", "physics.json")
    if os.path.exists(os.path.dirname(pub_phys)):
        shutil.copy2(phys_json_path, pub_phys)
        
    print(f"Physics metadata saved: {phys_data['collision_stats']}")
    return elem_id

if __name__ == "__main__":
    # Run key landmark buildings across all 3 maps
    reconstruct_and_splice_element("map", building_index=1)
    reconstruct_and_splice_element("map2", building_index=0)
    reconstruct_and_splice_element("schoolmap", building_index=0)

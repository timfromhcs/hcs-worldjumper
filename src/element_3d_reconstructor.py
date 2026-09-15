import os
import sys
import json
import trimesh
import numpy as np
from PIL import Image

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)
from src.deep_visual_audit import render_view_headless, call_vlm_analysis, load_hf_token

TEXTURES_DIR = os.path.join(PROJECT_DIR, "dataset", "textures")

def create_uv_box(extents, translation=[0.0, 0.0, 0.0], material=None, name="box", uv_scale=2.5):
    """Create a clean, manifold box with 24 distinct vertices and 1:1 UV coordinates."""
    w, h, d = extents[0] / 2.0, extents[1] / 2.0, extents[2] / 2.0
    faces_data = [
        # Front (+Z)
        ([[-w, -h,  d], [ w, -h,  d], [ w,  h,  d], [-w,  h,  d]], extents[0], extents[1]),
        # Back (-Z)
        ([[ w, -h, -d], [-w, -h, -d], [-w,  h, -d], [ w,  h, -d]], extents[0], extents[1]),
        # Left (-X)
        ([[-w, -h, -d], [-w, -h,  d], [-w,  h,  d], [-w,  h, -d]], extents[2], extents[1]),
        # Right (+X)
        ([[ w, -h,  d], [ w, -h, -d], [ w,  h, -d], [ w,  h,  d]], extents[2], extents[1]),
        # Top (+Y)
        ([[-w,  h,  d], [ w,  h,  d], [ w,  h, -d], [-w,  h, -d]], extents[0], extents[2]),
        # Bottom (-Y)
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

def reconstruct_building_element(map_id="map", element_id="building_001"):
    element_dir = os.path.join(PROJECT_DIR, "dataset", map_id, "buildings", element_id)
    meta_path = os.path.join(element_dir, "meta.json")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Missing meta.json at {meta_path}")
        
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    bounds_min = np.array(meta["bounds"]["min"])
    bounds_max = np.array(meta["bounds"]["max"])
    
    # Target normalized extents
    extents = bounds_max - bounds_min
    W = float(extents[0])  # ~10.644 m (X)
    H = float(extents[1])  # ~5.366 m  (Y)
    D = float(extents[2])  # ~11.876 m (Z)
    
    half_W = W / 2.0
    half_D = D / 2.0
    
    print(f"Reconstructing {element_id} with exact extents: W={W:.3f}m, H={H:.3f}m, D={D:.3f}m")
    
    # Load Textures
    concrete_bc = Image.open(os.path.join(TEXTURES_DIR, "concrete_basecolor.png"))
    metal_bc = Image.open(os.path.join(TEXTURES_DIR, "graphite_metal_basecolor.png"))
    roof_bc = Image.open(os.path.join(TEXTURES_DIR, "roof_membrane_basecolor.png"))
    
    # -------------------------------------------------------------------------
    # Realistic PBR Materials Definition
    # -------------------------------------------------------------------------
    mat_concrete = trimesh.visual.material.PBRMaterial(
        name="Architectural_Concrete",
        baseColorTexture=concrete_bc,
        baseColorFactor=[0.92, 0.93, 0.94, 1.0],
        roughnessFactor=0.75,
        metallicFactor=0.04
    )
    
    mat_concrete_plinth = trimesh.visual.material.PBRMaterial(
        name="Concrete_Plinth",
        baseColorTexture=concrete_bc,
        baseColorFactor=[0.70, 0.72, 0.74, 1.0],
        roughnessFactor=0.85,
        metallicFactor=0.04
    )
    
    mat_graphite_frame = trimesh.visual.material.PBRMaterial(
        name="Graphite_Frame",
        baseColorTexture=metal_bc,
        baseColorFactor=[0.22, 0.23, 0.25, 1.0],
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

    # 1. Foundation / Plinth (Y: 0.0 -> 0.25)
    plinth_h = 0.25
    plinth = create_uv_box(
        extents=[W, plinth_h, D],
        translation=[0.0, plinth_h / 2.0, 0.0],
        material=mat_concrete_plinth,
        name="Plinth",
        uv_scale=2.0
    )
    geometries.append(plinth)

    # 2. Main Floor Slabs & Roof Parapet
    floor_slab_y = 2.65
    floor_slab_h = 0.30
    slab_mid = create_uv_box(
        extents=[W, floor_slab_h, D],
        translation=[0.0, floor_slab_y, 0.0],
        material=mat_concrete,
        name="Intermediate_Slab",
        uv_scale=2.0
    )
    geometries.append(slab_mid)
    
    # Roof slab and perimeter parapet (Top Y reaches exactly H = 5.366)
    parapet_h = 0.35
    roof_deck_y = H - parapet_h
    roof_deck = create_uv_box(
        extents=[W - 0.5, 0.15, D - 0.5],
        translation=[0.0, roof_deck_y, 0.0],
        material=mat_roof,
        name="Roof_Deck",
        uv_scale=3.0
    )
    geometries.append(roof_deck)
    
    # Roof Parapet Perimeter Coping (Front, Back, Left, Right)
    coping_thickness = 0.25
    geometries.append(create_uv_box(
        extents=[W, parapet_h, coping_thickness],
        translation=[0.0, H - parapet_h / 2.0, half_D - coping_thickness / 2.0],
        material=mat_concrete,
        name="Parapet_Front",
        uv_scale=2.0
    ))
    geometries.append(create_uv_box(
        extents=[W, parapet_h, coping_thickness],
        translation=[0.0, H - parapet_h / 2.0, -half_D + coping_thickness / 2.0],
        material=mat_concrete,
        name="Parapet_Back",
        uv_scale=2.0
    ))
    geometries.append(create_uv_box(
        extents=[coping_thickness, parapet_h, D - 2 * coping_thickness],
        translation=[-half_W + coping_thickness / 2.0, H - parapet_h / 2.0, 0.0],
        material=mat_concrete,
        name="Parapet_Left",
        uv_scale=2.0
    ))
    geometries.append(create_uv_box(
        extents=[coping_thickness, parapet_h, D - 2 * coping_thickness],
        translation=[half_W - coping_thickness / 2.0, H - parapet_h / 2.0, 0.0],
        material=mat_concrete,
        name="Parapet_Right",
        uv_scale=2.0
    ))

    # 3. Structural Concrete Columns (Corners & Main Divides)
    col_size = 0.65
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
            name=f"Corner_Column_{i}",
            uv_scale=1.5
        ))

    # Central dividing architectural shear wall
    geometries.append(create_uv_box(
        extents=[0.70, col_h, col_size],
        translation=[0.0, col_y, half_D - col_size / 2.0],
        material=mat_concrete,
        name="Front_Center_Column",
        uv_scale=1.5
    ))

    # 4. Solid Structural Side and Rear Walls
    rear_wall_t = 0.35
    rear_z = -half_D + rear_wall_t / 2.0
    geometries.append(create_uv_box(
        extents=[W - 2 * col_size, floor_slab_y - plinth_h, rear_wall_t],
        translation=[0.0, plinth_h + (floor_slab_y - plinth_h) / 2.0, rear_z],
        material=mat_concrete,
        name="Rear_Wall_Ground",
        uv_scale=2.0
    ))
    geometries.append(create_uv_box(
        extents=[W - 2 * col_size, (H - parapet_h) - (floor_slab_y + floor_slab_h / 2.0), rear_wall_t],
        translation=[0.0, floor_slab_y + floor_slab_h / 2.0 + ((H - parapet_h) - (floor_slab_y + floor_slab_h / 2.0)) / 2.0, rear_z],
        material=mat_concrete,
        name="Rear_Wall_Upper",
        uv_scale=2.0
    ))

    # Left and Right Facade Wall Panels
    side_wall_t = 0.35
    for sign, name in [(-1, "Left"), (1, "Right")]:
        sx = sign * (half_W - side_wall_t / 2.0)
        geometries.append(create_uv_box(
            extents=[side_wall_t, floor_slab_y - plinth_h, D - 2 * col_size],
            translation=[sx, plinth_h + (floor_slab_y - plinth_h) / 2.0, 0.0],
            material=mat_concrete,
            name=f"{name}_Wall_Ground",
            uv_scale=2.0
        ))
        geometries.append(create_uv_box(
            extents=[side_wall_t, (H - parapet_h) - (floor_slab_y + floor_slab_h / 2.0), D - 2 * col_size],
            translation=[sx, floor_slab_y + floor_slab_h / 2.0 + ((H - parapet_h) - (floor_slab_y + floor_slab_h / 2.0)) / 2.0, 0.0],
            material=mat_concrete,
            name=f"{name}_Wall_Upper",
            uv_scale=2.0
        ))

    # 5. Front Facade Floor-to-Ceiling Glazing & Aluminum Mullions (Curtain Wall)
    glass_z = half_D - col_size / 2.0 - 0.10
    bay_w = (half_W - col_size - 0.35)
    bay_centers = [
        (-half_W + col_size + bay_w / 2.0),
        (0.35 + bay_w / 2.0)
    ]
    
    for bay_idx, bx in enumerate(bay_centers):
        # Ground Floor Glass
        gf_y_bot = plinth_h
        gf_y_top = floor_slab_y - floor_slab_h / 2.0
        gf_h = gf_y_top - gf_y_bot
        gf_y = gf_y_bot + gf_h / 2.0
        
        # Upper Floor Glass
        uf_y_bot = floor_slab_y + floor_slab_h / 2.0
        uf_y_top = H - parapet_h
        uf_h = uf_y_top - uf_y_bot
        uf_y = uf_y_bot + uf_h / 2.0
        
        geometries.append(create_uv_box(
            extents=[bay_w, gf_h, 0.04],
            translation=[bx, gf_y, glass_z],
            material=mat_glass,
            name=f"Glass_Ground_Bay_{bay_idx}"
        ))
        geometries.append(create_uv_box(
            extents=[bay_w, uf_h, 0.04],
            translation=[bx, uf_y, glass_z],
            material=mat_glass,
            name=f"Glass_Upper_Bay_{bay_idx}"
        ))
        
        # Aluminum Mullion Frames
        mullion_t = 0.08
        mullion_d = 0.12
        for floor_y, fh, f_name in [(gf_y, gf_h, "GF"), (uf_y, uf_h, "UF")]:
            geometries.append(create_uv_box(
                extents=[mullion_t, fh, mullion_d],
                translation=[bx - bay_w / 2.0 + mullion_t / 2.0, floor_y, glass_z],
                material=mat_graphite_frame,
                name=f"Mullion_Left_{f_name}_{bay_idx}",
                uv_scale=1.0
            ))
            geometries.append(create_uv_box(
                extents=[mullion_t, fh, mullion_d],
                translation=[bx + bay_w / 2.0 - mullion_t / 2.0, floor_y, glass_z],
                material=mat_graphite_frame,
                name=f"Mullion_Right_{f_name}_{bay_idx}",
                uv_scale=1.0
            ))
            geometries.append(create_uv_box(
                extents=[mullion_t, fh, mullion_d],
                translation=[bx, floor_y, glass_z],
                material=mat_graphite_frame,
                name=f"Mullion_Center_{f_name}_{bay_idx}",
                uv_scale=1.0
            ))
            geometries.append(create_uv_box(
                extents=[bay_w, mullion_t, mullion_d],
                translation=[bx, floor_y + fh / 2.0 - mullion_t / 2.0, glass_z],
                material=mat_graphite_frame,
                name=f"Transom_Top_{f_name}_{bay_idx}",
                uv_scale=1.0
            ))
            geometries.append(create_uv_box(
                extents=[bay_w, mullion_t, mullion_d],
                translation=[bx, floor_y - fh / 2.0 + mullion_t / 2.0, glass_z],
                material=mat_graphite_frame,
                name=f"Transom_Bottom_{f_name}_{bay_idx}",
                uv_scale=1.0
            ))

    # 6. Entrance Portico & Details
    entry_x = bay_centers[1]
    entry_w = 1.6
    entry_h = 2.2
    entry_y = plinth_h + entry_h / 2.0
    geometries.append(create_uv_box(
        extents=[entry_w + 0.3, 0.20, 0.40],
        translation=[entry_x, plinth_h + entry_h + 0.10, glass_z + 0.15],
        material=mat_concrete,
        name="Entrance_Canopy",
        uv_scale=1.0
    ))
    geometries.append(create_uv_box(
        extents=[0.15, entry_h + 0.20, 0.40],
        translation=[entry_x - entry_w / 2.0 - 0.075, entry_y + 0.10, glass_z + 0.15],
        material=mat_concrete,
        name="Entrance_Post_Left",
        uv_scale=1.0
    ))
    geometries.append(create_uv_box(
        extents=[0.15, entry_h + 0.20, 0.40],
        translation=[entry_x + entry_w / 2.0 + 0.075, entry_y + 0.10, glass_z + 0.15],
        material=mat_concrete,
        name="Entrance_Post_Right",
        uv_scale=1.0
    ))
    geometries.append(create_uv_box(
        extents=[0.04, 0.60, 0.06],
        translation=[entry_x + 0.25, plinth_h + 1.10, glass_z + 0.05],
        material=mat_graphite_frame,
        name="Door_Handle",
        uv_scale=0.5
    ))

    # 7. Assemble Scene
    for g in geometries:
        scene.add_geometry(g)

    # 8. Bounds Validation
    scene_bounds = scene.bounds
    s_min = scene_bounds[0]
    s_max = scene_bounds[1]
    s_extents = s_max - s_min
    
    print(f"Constructed Scene Bounds:")
    print(f"  Min: {s_min}")
    print(f"  Max: {s_max}")
    print(f"  Extents: {s_extents}")
    print(f"  Target Extents: [{W:.3f}, {H:.3f}, {D:.3f}]")

    # Export Reconstructed GLB
    reconstructed_glb_path = os.path.join(element_dir, "reconstructed_element.glb")
    glb_data = scene.export(file_type="glb")
    with open(reconstructed_glb_path, "wb") as f:
        f.write(glb_data)
        
    print(f"Reconstructed asset saved to: {reconstructed_glb_path} ({len(glb_data)/1024:.1f} KB)")
    
    # 9. Render Multi-View Comparisons of Reconstructed Element
    reconstruction_renders_dir = os.path.join(element_dir, "reconstruction_renders")
    os.makedirs(reconstruction_renders_dir, exist_ok=True)
    
    recon_views = ["front", "threequarter", "closeup", "top", "left"]
    captured_recon = {}
    
    print("Capturing multi-view renders for reconstructed asset...")
    for v in recon_views:
        out_png = os.path.join(reconstruction_renders_dir, f"recon_{v}.png")
        ok = render_view_headless(reconstructed_glb_path, out_png, view_preset=v, lighting="day", mode="lit")
        if ok and os.path.exists(out_png):
            captured_recon[v] = out_png
            print(f"  [OK] {v:12s} -> {out_png} ({os.path.getsize(out_png)/1024:.1f} KB)")
        else:
            print(f"  [FAIL] {v:12s}")
            
    # Save summary manifest
    summary = {
        "element_id": element_id,
        "map_id": map_id,
        "target_extents": [W, H, D],
        "reconstructed_extents": s_extents.tolist(),
        "reconstructed_bounds": {
            "min": s_min.tolist(),
            "max": s_max.tolist()
        },
        "reconstructed_glb_path": reconstructed_glb_path,
        "captured_renders": captured_recon
    }
    with open(os.path.join(element_dir, "reconstruction_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary

if __name__ == "__main__":
    reconstruct_building_element("map", "building_001")

import os
import sys
import json
import math
import hashlib
import trimesh
import numpy as np

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATASET_DIR = os.path.join(PROJECT_DIR, "dataset")
SOURCE_DIR = os.path.join(PROJECT_DIR, "source", "original")

def generate_element_id(prefix, index):
    return f"{prefix}_{index+1:03d}"

def build_map_elements_dataset(map_id="map"):
    print(f"\n=======================================================")
    print(f"BUILDING COMPREHENSIVE ELEMENT DATASET FOR: {map_id.upper()}")
    print(f"=======================================================")
    
    manifest_path = os.path.join(PROJECT_DIR, "output", map_id, "manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest missing: {manifest_path}")
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        mf = json.load(f)
        
    # Get Stage 1 & 2 info
    s1 = mf["stages"]["stage_1"]
    s2 = mf["stages"]["stage_2"]
    world_bounds = s1["bounds"]
    extents = s1["extents"]
    scale_factor = s1.get("scale_factor_applied", 1.0)
    
    buildings_detected = s2.get("buildings_detected", [])
    print(f"[{map_id}] Processing {len(buildings_detected)} detected buildings...")
    
    map_dataset_dir = os.path.join(DATASET_DIR, map_id)
    os.makedirs(map_dataset_dir, exist_ok=True)
    
    elements_registry = []
    
    # -------------------------------------------------------------------------
    # 1. BUILDINGS & ARCHITECTURAL ELEMENTS (with Subcomponent Hierarchy)
    # -------------------------------------------------------------------------
    for i, b in enumerate(buildings_detected):
        elem_id = generate_element_id("HOUSE", i)
        center = b["center"]
        size = b["size"]
        base_y = b.get("base_y", center[1] - size[1] / 2.0)
        roof_y = b.get("roof_y", center[1] + size[1] / 2.0)
        
        # Dimensions
        W, H, D = float(size[0]), float(size[1]), float(size[2])
        stories = max(1, int(round(H / 3.0)))
        
        # Determine quadrant / region
        min_x, max_x = world_bounds[0][0], world_bounds[1][0]
        min_z, max_z = world_bounds[0][2], world_bounds[1][2]
        reg_x = "E" if center[0] >= (min_x + max_x) / 2.0 else "W"
        reg_z = "N" if center[2] >= (min_z + max_z) / 2.0 else "S"
        region_id = f"region_{reg_z}{reg_x}"
        
        # Importance score based on height, volume, and face count
        volume = W * H * D
        faces = b.get("face_count", 1000)
        importance = min(1.0, (volume / 2000.0) * 0.4 + (faces / 3000.0) * 0.4 + (H / 15.0) * 0.2)
        
        # Subcomponent Hierarchy
        hierarchy = {
            "root": elem_id,
            "components": [
                {
                    "name": f"{elem_id}_plinth",
                    "type": "foundation",
                    "elevation_range": [base_y, base_y + 0.25],
                    "material_type": "concrete_plinth"
                },
                {
                    "name": f"{elem_id}_facade_walls",
                    "type": "structural_shell",
                    "elevation_range": [base_y + 0.25, roof_y],
                    "material_type": "architectural_concrete"
                },
                {
                    "name": f"{elem_id}_floors",
                    "type": "horizontal_slabs",
                    "story_count": stories,
                    "material_type": "reinforced_concrete"
                },
                {
                    "name": f"{elem_id}_curtain_glazing",
                    "type": "windows",
                    "elevation_range": [base_y + 0.25, roof_y - 0.35],
                    "material_type": "architectural_glass"
                },
                {
                    "name": f"{elem_id}_mullions",
                    "type": "window_frames",
                    "material_type": "graphite_aluminum"
                },
                {
                    "name": f"{elem_id}_entrance",
                    "type": "door_portico",
                    "elevation_range": [base_y, base_y + 2.3],
                    "material_type": "portal_canopy"
                },
                {
                    "name": f"{elem_id}_roof",
                    "type": "parapet_deck",
                    "elevation_range": [roof_y - 0.35, roof_y],
                    "material_type": "bitumen_membrane"
                },
                {
                    "name": f"{elem_id}_interior",
                    "type": "room_layout",
                    "stories": stories,
                    "material_type": "interior_plaster"
                }
            ]
        }
        
        elem_record = {
            "element_id": elem_id,
            "map_id": map_id,
            "class": "building",
            "source_node": f"building_node_{i}",
            "source_mesh": f"building_mesh_{i}",
            "source_material": "photogrammetry_diffuse",
            "source_texture": "atlas_0",
            "world_position": [float(center[0]), float(center[1]), float(center[2])],
            "world_rotation": [0.0, 0.0, 0.0],
            "world_scale": [1.0, 1.0, 1.0],
            "dimensions": [W, H, D],
            "bounding_box": {
                "min": [float(center[0] - W/2.0), float(base_y), float(center[2] - D/2.0)],
                "max": [float(center[0] + W/2.0), float(roof_y), float(center[2] + D/2.0)]
            },
            "ground_contact": {
                "base_y": float(base_y),
                "is_grounded": True,
                "clearance": 0.0
            },
            "semantic_context": {
                "district": "urban_modular",
                "estimated_stories": stories,
                "building_typology": "commercial_residential",
                "neighbor_count": len(buildings_detected)
            },
            "hierarchy": hierarchy,
            "region": region_id,
            "visibility": "high" if importance > 0.4 else "medium",
            "importance": round(float(importance), 3)
        }
        elements_registry.append(elem_record)
        
    # -------------------------------------------------------------------------
    # 2. TREES & VEGETATION CLUSTERS (with Hierarchy)
    # -------------------------------------------------------------------------
    # Generate structured tree elements distributed across the world open spaces
    span_x = world_bounds[1][0] - world_bounds[0][0]
    span_z = world_bounds[1][2] - world_bounds[0][2]
    
    # 20 representative tree clusters per map
    np.random.seed(101 if map_id == "map" else (202 if map_id == "map2" else 303))
    tree_count = 18
    for t_idx in range(tree_count):
        elem_id = generate_element_id("TREE", t_idx)
        # Avoid building footprints
        valid_pos = False
        attempts = 0
        tx, tz = 0.0, 0.0
        while not valid_pos and attempts < 30:
            tx = world_bounds[0][0] + span_x * (0.15 + 0.70 * np.random.rand())
            tz = world_bounds[0][2] + span_z * (0.15 + 0.70 * np.random.rand())
            attempts += 1
            # Check collision with buildings
            in_b = False
            for b in buildings_detected:
                if abs(tx - b["center"][0]) < (b["size"][0]/2.0 + 3.0) and abs(tz - b["center"][2]) < (b["size"][2]/2.0 + 3.0):
                    in_b = True
                    break
            if not in_b:
                valid_pos = True
                
        tree_h = 4.5 + np.random.rand() * 4.0
        tree_w = 2.5 + np.random.rand() * 2.5
        base_ground_y = 0.5 + np.random.rand() * 0.5
        
        tree_record = {
            "element_id": elem_id,
            "map_id": map_id,
            "class": "tree",
            "source_node": f"tree_node_{t_idx}",
            "source_mesh": "procedural_foliage",
            "source_material": "organic_pbr",
            "source_texture": "bark_and_leaf",
            "world_position": [float(tx), float(base_ground_y + tree_h/2.0), float(tz)],
            "world_rotation": [0.0, float(np.random.rand() * 360.0), 0.0],
            "world_scale": [1.0, 1.0, 1.0],
            "dimensions": [float(tree_w), float(tree_h), float(tree_w)],
            "bounding_box": {
                "min": [float(tx - tree_w/2.0), float(base_ground_y), float(tz - tree_w/2.0)],
                "max": [float(tx + tree_w/2.0), float(base_ground_y + tree_h), float(tz + tree_w/2.0)]
            },
            "ground_contact": {
                "base_y": float(base_ground_y),
                "is_grounded": True,
                "clearance": 0.0
            },
            "semantic_context": {
                "vegetation_type": "deciduous_temperate",
                "foliage_density": "high",
                "wind_responsive": True
            },
            "hierarchy": {
                "root": elem_id,
                "components": [
                    {"name": f"{elem_id}_trunk", "type": "wood_trunk", "material": "bark_pbr"},
                    {"name": f"{elem_id}_branches", "type": "branch_structure", "material": "branch_wood"},
                    {"name": f"{elem_id}_canopy", "type": "foliage_crown", "material": "leaf_subsurface"}
                ]
            },
            "region": f"region_{'N' if tz >= 0 else 'S'}{'E' if tx >= 0 else 'W'}",
            "visibility": "medium",
            "importance": 0.35
        }
        elements_registry.append(tree_record)
        
    # -------------------------------------------------------------------------
    # 3. VEHICLES & CIVIC STREET PROPS (with Hierarchy)
    # -------------------------------------------------------------------------
    # Representative vehicles parked along street corridors
    car_count = 6
    for c_idx in range(car_count):
        elem_id = generate_element_id("CAR", c_idx)
        cx = world_bounds[0][0] + span_x * (0.25 + 0.10 * c_idx)
        cz = world_bounds[0][2] + span_z * 0.22
        car_w, car_h, car_d = 2.1, 1.6, 4.6
        ground_y = 0.52
        
        car_record = {
            "element_id": elem_id,
            "map_id": map_id,
            "class": "vehicle",
            "source_node": f"car_node_{c_idx}",
            "source_mesh": "sedan_vehicle",
            "source_material": "automotive_metallic",
            "source_texture": "car_paint",
            "world_position": [float(cx), float(ground_y + car_h/2.0), float(cz)],
            "world_rotation": [0.0, 90.0 if c_idx % 2 == 0 else -90.0, 0.0],
            "world_scale": [1.0, 1.0, 1.0],
            "dimensions": [car_w, car_h, car_d],
            "bounding_box": {
                "min": [float(cx - car_w/2.0), float(ground_y), float(cz - car_d/2.0)],
                "max": [float(cx + car_w/2.0), float(ground_y + car_h), float(cz + car_d/2.0)]
            },
            "ground_contact": {
                "base_y": float(ground_y),
                "is_grounded": True,
                "clearance": 0.0
            },
            "semantic_context": {
                "vehicle_type": "civilian_sedan",
                "context": "street_parking"
            },
            "hierarchy": {
                "root": elem_id,
                "components": [
                    {"name": f"{elem_id}_chassis", "type": "bodywork", "material": "car_paint_clearcoat"},
                    {"name": f"{elem_id}_windows", "type": "automotive_glass", "material": "tinted_glass"},
                    {"name": f"{elem_id}_wheels", "type": "rubber_rims", "wheel_count": 4, "material": "vulcanized_rubber"},
                    {"name": f"{elem_id}_lights", "type": "headlights_taillights", "material": "emissive_polycarbonate"}
                ]
            },
            "region": f"region_{'N' if cz >= 0 else 'S'}{'E' if cx >= 0 else 'W'}",
            "visibility": "medium",
            "importance": 0.30
        }
        elements_registry.append(car_record)
        
    # Street Lamps
    lamp_count = 8
    for l_idx in range(lamp_count):
        elem_id = generate_element_id("LAMP", l_idx)
        lx = world_bounds[0][0] + span_x * (0.2 + 0.08 * l_idx)
        lz = world_bounds[0][2] + span_z * 0.18
        lamp_h = 4.8
        ground_y = 0.50
        
        lamp_record = {
            "element_id": elem_id,
            "map_id": map_id,
            "class": "street_prop",
            "source_node": f"lamp_node_{l_idx}",
            "source_mesh": "civic_lamp_post",
            "source_material": "cast_iron",
            "source_texture": "dark_metal",
            "world_position": [float(lx), float(ground_y + lamp_h/2.0), float(lz)],
            "world_rotation": [0.0, 0.0, 0.0],
            "world_scale": [1.0, 1.0, 1.0],
            "dimensions": [0.6, lamp_h, 0.6],
            "bounding_box": {
                "min": [float(lx - 0.3), float(ground_y), float(lz - 0.3)],
                "max": [float(lx + 0.3), float(ground_y + lamp_h), float(lz + 0.3)]
            },
            "ground_contact": {
                "base_y": float(ground_y),
                "is_grounded": True,
                "clearance": 0.0
            },
            "semantic_context": {
                "prop_type": "street_lighting",
                "light_color_temp": 3000,
                "luminous_flux": 8000
            },
            "hierarchy": {
                "root": elem_id,
                "components": [
                    {"name": f"{elem_id}_base", "type": "ground_anchor", "material": "cast_iron"},
                    {"name": f"{elem_id}_pole", "type": "vertical_mast", "material": "powdercoated_steel"},
                    {"name": f"{elem_id}_luminaire", "type": "light_fixture", "material": "warm_led"}
                ]
            },
            "region": f"region_{'N' if lz >= 0 else 'S'}{'E' if lx >= 0 else 'W'}",
            "visibility": "medium",
            "importance": 0.25
        }
        elements_registry.append(lamp_record)

    # Save Map Elements Registry
    out_file = os.path.join(map_dataset_dir, "elements_registry.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "map_id": map_id,
            "element_count": len(elements_registry),
            "categories": {
                "buildings": len(buildings_detected),
                "trees": tree_count,
                "vehicles": car_count,
                "street_props": lamp_count
            },
            "world_bounds": world_bounds,
            "elements": elements_registry
        }, f, indent=2)
        
    print(f"[{map_id}] Registered {len(elements_registry)} semantic elements in {out_file}")
    return elements_registry

def generate_master_dataset():
    master_index = {}
    total_elements = 0
    for m in ["map", "map2", "schoolmap"]:
        registry = build_map_elements_dataset(m)
        master_index[m] = {
            "element_count": len(registry),
            "registry_path": f"dataset/{m}/elements_registry.json"
        }
        total_elements += len(registry)
        
    master_file = os.path.join(DATASET_DIR, "master_elements_index.json")
    with open(master_file, "w", encoding="utf-8") as f:
        json.dump({
            "project": "HCS WorldJumper",
            "total_elements_cataloged": total_elements,
            "maps": master_index
        }, f, indent=2)
        
    print(f"\n=======================================================")
    print(f"MASTER DATASET GENERATED: {total_elements} total elements across 3 maps")
    print(f"Saved to: {master_file}")
    print(f"=======================================================")

if __name__ == "__main__":
    generate_master_dataset()

import os
import trimesh
import numpy as np

def create_procedural_tree(height=8.5, canopy_radius=3.8):
    """
    Synthesizes a realistic procedural game tree:
    - Tapered wood trunk with secondary branches
    - Multi-cluster volumetric leaf canopy with organic vertex noise
    - Realistic natural bark and foliage coloration
    """
    # 1. Main Trunk
    trunk_h = height * 0.42
    trunk = trimesh.creation.cylinder(radius=0.28, height=trunk_h, sections=12)
    trunk.apply_translation([0, trunk_h/2.0, 0])
    trunk.visual.vertex_colors = [88, 62, 44, 255] # Natural bark brown
    
    # Secondary branches reaching out
    branches = [trunk]
    branch_specs = [
        (trunk_h * 0.75, 1.8, 0.35, 0.14),
        (trunk_h * 0.85, -1.6, -0.40, 0.12),
        (trunk_h * 0.95, 0.2, 1.5, 0.13),
    ]
    for by, bx, bz, br in branch_specs:
        b_len = np.sqrt(bx*bx + bz*bz)
        b_cyl = trimesh.creation.cylinder(radius=br, height=b_len, sections=8)
        # Point toward (bx, bz)
        angle = np.arctan2(bz, bx)
        rot_y = trimesh.transformations.rotation_matrix(angle, [0, 1, 0])
        rot_z = trimesh.transformations.rotation_matrix(-0.45, [0, 0, 1])
        b_cyl.apply_transform(rot_z)
        b_cyl.apply_transform(rot_y)
        b_cyl.apply_translation([bx*0.5, by, bz*0.5])
        b_cyl.visual.vertex_colors = [80, 56, 38, 255]
        branches.append(b_cyl)
        
    # 2. Organic Foliage Clusters distributed around branches
    canopy_parts = []
    cluster_offsets = [
        (0.0, trunk_h * 1.0, 0.0, canopy_radius * 0.85, [42, 85, 38, 255]), # Central core
        (1.4, trunk_h * 0.95, 0.6, canopy_radius * 0.65, [48, 92, 42, 255]),
        (-1.2, trunk_h * 1.05, -0.8, canopy_radius * 0.62, [52, 98, 45, 255]),
        (0.3, trunk_h * 1.15, 1.2, canopy_radius * 0.58, [55, 105, 48, 255]),
        (-0.5, trunk_h * 1.35, 0.2, canopy_radius * 0.70, [62, 115, 52, 255]), # Upper crest
        (0.0, trunk_h * 1.65, 0.0, canopy_radius * 0.45, [70, 128, 58, 255]), # Sunlit crown
    ]
    
    for cx, cy, cz, radius, color in cluster_offsets:
        sphere = trimesh.creation.icosphere(subdivisions=2, radius=radius)
        noise = np.random.normal(0, radius * 0.14, sphere.vertices.shape)
        sphere.vertices += noise
        sphere.vertices[:, 1] *= 0.85 # Gentle droop
        sphere.apply_translation([cx, cy, cz])
        sphere.visual.vertex_colors = color
        canopy_parts.append(sphere)
        
    tree = trimesh.util.concatenate(branches + canopy_parts)
    return tree

def create_ground_grass_cluster(radius=1.2):
    """Generates natural wild grass and bush tufts for ground micro-detail."""
    blades = []
    num_cards = 5
    for i in range(num_cards):
        angle = i * (np.pi / num_cards)
        box = trimesh.creation.box(extents=[radius * 0.8, 0.45, 0.02])
        rot = trimesh.transformations.rotation_matrix(angle, [0, 1, 0])
        box.apply_transform(rot)
        box.apply_translation([0, 0.22, 0])
        box.visual.vertex_colors = [72, 130, 48, 255]
        blades.append(box)
    return trimesh.util.concatenate(blades)

def find_vegetation_candidate_locations(scene, num_trees=18):
    """
    Identifies natural tree and foliage positions across the terrain.
    Finds perimeter areas, parks, sidewalks, and open courtyards.
    """
    bounds = scene.bounds
    min_x, min_y, min_z = bounds[0]
    max_x, max_y, max_z = bounds[1]
    
    dx = max_x - min_x
    dz = max_z - min_z
    
    locations = []
    np.random.seed(42)
    
    # Extract collision mesh to find true ground terrain elevation
    from src.collision_builder import extract_collision_mesh, ray_mesh_intersect
    col_mesh = extract_collision_mesh(scene)

    attempts = 0
    while len(locations) < num_trees and attempts < num_trees * 4:
        attempts += 1
        side = np.random.choice(["north", "south", "east", "west", "courtyard"])
        if side == "north":
            x = np.random.uniform(min_x + dx*0.05, max_x - dx*0.05)
            z = np.random.uniform(max_z - dz*0.25, max_z - dz*0.05)
        elif side == "south":
            x = np.random.uniform(min_x + dx*0.05, max_x - dx*0.05)
            z = np.random.uniform(min_z + dz*0.05, min_z + dz*0.25)
        elif side == "east":
            x = np.random.uniform(max_x - dx*0.25, max_x - dx*0.05)
            z = np.random.uniform(min_z + dz*0.1, max_z - dz*0.1)
        elif side == "west":
            x = np.random.uniform(min_x + dx*0.05, min_x + dx*0.25)
            z = np.random.uniform(min_z + dz*0.1, max_z - dz*0.1)
        else:
            x = np.random.uniform(min_x + dx*0.35, min_x + dx*0.65)
            z = np.random.uniform(min_z + dz*0.35, min_z + dz*0.65)

        ground_y = min_y + 0.1
        if col_mesh is not None:
            origin = np.array([x, max_y + 5.0, z])
            locs_hit, face_idxs, _ = ray_mesh_intersect(col_mesh, origin, np.array([0.0, -1.0, 0.0]))
            if len(locs_hit) > 0:
                # Filter for walkable surfaces (Ny >= 0.6) and reject roofs above 60% building height
                valid_hits = []
                for hit_p, f_i in zip(locs_hit, face_idxs):
                    n = col_mesh.face_normals[f_i]
                    if n[1] >= 0.6 and hit_p[1] <= min_y + (max_y - min_y) * 0.6:
                        valid_hits.append(hit_p[1])
                if valid_hits:
                    ground_y = float(np.min(valid_hits))
                else:
                    continue  # Hit a steep wall or high roof, skip candidate
            else:
                continue

        h = float(np.random.uniform(6.5, 11.0))
        r = float(np.random.uniform(2.8, 4.5))
        locations.append((float(x), float(ground_y), float(z), h, r))
        
    return locations

def enhance_vegetation_for_scene(scene, num_trees=22):
    """Synthesizes high-fidelity 3D trees and grass patches."""
    locs = find_vegetation_candidate_locations(scene, num_trees=num_trees)
    trees = []
    
    for x, y, z, h, r in locs:
        tree = create_procedural_tree(height=h, canopy_radius=r)
        tree.apply_translation([x, y, z])
        trees.append(tree)
        
        # Add ground grass/shrub under tree
        grass = create_ground_grass_cluster(radius=r * 0.9)
        grass.apply_translation([x, y, z])
        trees.append(grass)
        
    merged_veg = trimesh.util.concatenate(trees)
    return merged_veg

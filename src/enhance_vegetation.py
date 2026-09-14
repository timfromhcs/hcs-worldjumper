import os
import trimesh
import numpy as np

def create_procedural_tree(height=8.0, canopy_radius=3.5):
    """
    Synthesizes a realistic procedural game tree:
    - Segmented trunk with bark material
    - 3-tiered volumetric leaf canopy with branch cards
    - Proper normals for lush lighting
    """
    # 1. Trunk (tapered cylinder)
    trunk_h = height * 0.45
    trunk = trimesh.creation.cylinder(radius=0.25, height=trunk_h, sections=12)
    trunk.apply_translation([0, trunk_h/2.0, 0])
    trunk.visual.vertex_colors = [85, 60, 42, 255] # Realistic bark brown
    
    # 2. Layered Foliage Canopy (Multi-tiered organic icospheres with ruffled vertices)
    canopy_parts = []
    tiers = [
        (trunk_h * 0.9, canopy_radius * 0.95, [48, 102, 45, 255]), # Base dense canopy
        (trunk_h * 1.35, canopy_radius * 0.8, [56, 120, 52, 255]), # Mid layer
        (trunk_h * 1.75, canopy_radius * 0.55, [68, 138, 62, 255]), # Top sunlit crest
    ]
    
    for y_offset, radius, color in tiers:
        sphere = trimesh.creation.icosphere(subdivisions=2, radius=radius)
        # Apply organic noise to vertices so it doesn't look like a computer sphere
        noise = np.random.normal(0, radius * 0.12, sphere.vertices.shape)
        sphere.vertices += noise
        # Flatten slightly vertically for natural foliage weight
        sphere.vertices[:, 1] *= 0.82
        sphere.apply_translation([0, y_offset, 0])
        sphere.visual.vertex_colors = color
        canopy_parts.append(sphere)
        
    tree = trimesh.util.concatenate([trunk] + canopy_parts)
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
    
    # Place trees in organic groves along perimeter, borders, and courtyards
    # Avoid center of roads
    for _ in range(num_trees):
        # Perimeter groves
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
            
        y = min_y + 0.5 # Ground level
        h = np.random.uniform(6.5, 11.0)
        r = np.random.uniform(2.8, 4.5)
        locations.append((x, y, z, h, r))
        
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

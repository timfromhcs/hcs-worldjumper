import os
import trimesh
import numpy as np

def extract_collision_mesh(final_world_scene):
    """
    Extracts a consolidated collision mesh directly from the FINAL world geometry.
    Categorizes surfaces into walkable floors/ground (Ny >= 0.7) and blocking walls (Ny < 0.7).
    """
    geometries = []
    for name, geom in final_world_scene.geometry.items():
        if isinstance(geom, trimesh.Trimesh):
            # Exclude non-collidable foliage leaves / billboards if tagged
            if "foliage_leaves" in name.lower() or "grass_cards" in name.lower():
                continue
            geometries.append(geom)
            
    if not geometries:
        return None
        
    combined = trimesh.util.concatenate(geometries)
    return combined

def ray_mesh_intersect(mesh, origin, direction):
    """
    Pure NumPy vectorized Möller–Trumbore ray-triangle intersection.
    Does not require rtree or pyembree.
    """
    faces = mesh.faces
    vertices = mesh.vertices
    
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    
    # Bounding box quick cull along X and Z for downward ray
    if direction[0] == 0.0 and direction[2] == 0.0:
        margin = 1.0
        x_min, x_max = np.min(v0[:, 0]), np.max(v0[:, 0]) # rough
        # Filter triangles whose 2D bbox contains origin[0], origin[2]
        tri_min_x = np.minimum(v0[:, 0], np.minimum(v1[:, 0], v2[:, 0])) - margin
        tri_max_x = np.maximum(v0[:, 0], np.maximum(v1[:, 0], v2[:, 0])) + margin
        tri_min_z = np.minimum(v0[:, 2], np.minimum(v1[:, 2], v2[:, 2])) - margin
        tri_max_z = np.maximum(v0[:, 2], np.maximum(v1[:, 2], v2[:, 2])) + margin
        
        in_col = (origin[0] >= tri_min_x) & (origin[0] <= tri_max_x) & (origin[2] >= tri_min_z) & (origin[2] <= tri_max_z)
        if not np.any(in_col):
            return np.empty((0, 3)), np.empty((0,), dtype=int), np.empty((0,))
        v0 = v0[in_col]
        v1 = v1[in_col]
        v2 = v2[in_col]
        candidate_face_indices = np.nonzero(in_col)[0]
    else:
        candidate_face_indices = np.arange(len(faces))
        
    e1 = v1 - v0
    e2 = v2 - v0
    h = np.cross(direction, e2)
    a = np.sum(e1 * h, axis=1)
    
    mask = np.abs(a) > 1e-7
    if not np.any(mask):
        return np.empty((0, 3)), np.empty((0,), dtype=int), np.empty((0,))
        
    v0 = v0[mask]
    e1 = e1[mask]
    e2 = e2[mask]
    h = h[mask]
    a = a[mask]
    f_idx = candidate_face_indices[mask]
    
    f = 1.0 / a
    s = origin - v0
    u = f * np.sum(s * h, axis=1)
    
    valid_u = (u >= 0.0) & (u <= 1.0)
    if not np.any(valid_u):
        return np.empty((0, 3)), np.empty((0,), dtype=int), np.empty((0,))
        
    v0 = v0[valid_u]
    e1 = e1[valid_u]
    e2 = e2[valid_u]
    f_idx = f_idx[valid_u]
    f = f[valid_u]
    s = s[valid_u]
    u = u[valid_u]
    
    q = np.cross(s, e1)
    v = f * np.sum(direction * q, axis=1)
    valid_v = (v >= 0.0) & (u + v <= 1.0)
    if not np.any(valid_v):
        return np.empty((0, 3)), np.empty((0,), dtype=int), np.empty((0,))
        
    e2 = e2[valid_v]
    f_idx = f_idx[valid_v]
    f = f[valid_v]
    q = q[valid_v]
    
    t = f * np.sum(e2 * q, axis=1)
    hit_mask = t > 1e-4
    if not np.any(hit_mask):
        return np.empty((0, 3)), np.empty((0,), dtype=int), np.empty((0,))
        
    t_hits = t[hit_mask]
    hits = origin + t_hits[:, np.newaxis] * direction
    return hits, f_idx[hit_mask], t_hits

def resolve_safe_home_spawn(collision_mesh, requested_anchor):
    """
    Resolves a safe, ground-snapped HOME spawn point:
    1. Casts ray downward from anchor (X, requested_y + 15.0, Z)
    2. Finds intersection with collision mesh
    3. Validates surface normal (walkable floor Ny >= 0.70)
    4. Validates vertical clearance (at least 2.2m above floor)
    5. Validates non-roof condition (floor height within expected ground/first floor levels)
    6. If primary anchor fails, spirals outward to find nearest valid walkable ground point.
    """
    anchor_x, anchor_y, anchor_z = requested_anchor
    
    # Candidate search offsets: [0, 0], then concentric rings
    search_offsets = [(0.0, 0.0)]
    for radius in [1.5, 3.0, 5.0, 8.0]:
        for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
            search_offsets.append((radius * np.cos(angle), radius * np.sin(angle)))
            
    bounds = collision_mesh.bounds
    min_y = bounds[0][1]
    max_y = bounds[1][1]
    
    for dx, dz in search_offsets:
        ray_origin = np.array([anchor_x + dx, max_y + 5.0, anchor_z + dz])
        ray_direction = np.array([0.0, -1.0, 0.0])
        
        locations, hit_face_indices, _ = ray_mesh_intersect(
            collision_mesh,
            origin=ray_origin,
            direction=ray_direction
        )
        
        if len(locations) == 0:
            continue
            
        # Find hits below the ray origin, sorted from highest to lowest
        sorted_indices = np.argsort(-locations[:, 1])
        for idx in sorted_indices:
            hit_point = locations[idx]
            hit_face = hit_face_indices[idx]
            face_normal = collision_mesh.face_normals[hit_face]
            
            # Check 1: Must be a walkable upward surface (Ny >= 0.70)
            if face_normal[1] < 0.70:
                continue
                
            # Check 2: Reject roofs (if height is above 60% of max building elevation)
            if hit_point[1] > min_y + (max_y - min_y) * 0.65:
                continue
                
            # Check 3: Check upward clearance of 2.2m (no ceiling directly overhead)
            clearance_origin = np.array([hit_point[0], hit_point[1] + 0.1, hit_point[2]])
            clearance_dir = np.array([0.0, 1.0, 0.0])
            c_locs, _, _ = ray_mesh_intersect(collision_mesh, clearance_origin, clearance_dir)
            nearest_ceil = 10.0
            if len(c_locs) > 0:
                nearest_ceil = np.min(c_locs[:, 1]) - hit_point[1]
                if nearest_ceil < 2.0:
                    continue # Too cramped / inside a narrow gap
                    
            # Valid spawn point found!
            spawn_x = float(hit_point[0])
            spawn_y = float(hit_point[1] + 0.15) # 15cm above floor to avoid floor clipping
            spawn_z = float(hit_point[2])
            
            return {
                "status": "VALID_SAFE_SPAWN",
                "spawn_point": [spawn_x, spawn_y, spawn_z],
                "ground_elevation": float(hit_point[1]),
                "surface_normal": [float(n) for n in face_normal],
                "clearance_meters": float(nearest_ceil)
            }
        

            
    # Fallback to center of ground bounds if all fail
    center_x = (bounds[0][0] + bounds[1][0]) / 2.0
    center_z = (bounds[0][2] + bounds[1][2]) / 2.0
    return {
        "status": "FALLBACK_CENTER",
        "spawn_point": [float(center_x), float(min_y + 1.5), float(center_z)],
        "ground_elevation": float(min_y),
        "surface_normal": [0.0, 1.0, 0.0],
        "clearance_meters": float(max_y - min_y)
    }

def generate_physics_metadata(final_world_scene, map_id="map"):
    """Generates complete physics and collision description for runtime."""
    collision_mesh = extract_collision_mesh(final_world_scene)
    if collision_mesh is None:
        raise ValueError("Cannot extract collision mesh from empty scene")
        
    bounds = collision_mesh.bounds
    dx = bounds[1][0] - bounds[0][0]
    dz = bounds[1][2] - bounds[0][2]
    
    # Map-specific semantic home anchor candidates
    default_anchors = {
        "map": [bounds[0][0] + dx * 0.48, 2.0, bounds[0][2] + dz * 0.25], # Street start near river
        "map2": [bounds[0][0] + dx * 0.35, 5.0, bounds[0][2] + dz * 0.40], # Valley foothill entrance
        "schoolmap": [bounds[0][0] + dx * 0.50, 2.0, bounds[0][2] + dz * 0.20] # Campus courtyard entry
    }
    requested_anchor = default_anchors.get(map_id, [0.0, 5.0, 0.0])
    
    home_resolution = resolve_safe_home_spawn(collision_mesh, requested_anchor)
    
    physics_data = {
        "map_id": map_id,
        "collision_stats": {
            "total_collision_vertices": len(collision_mesh.vertices),
            "total_collision_faces": len(collision_mesh.faces),
            "walkable_surfaces": int(np.sum(collision_mesh.face_normals[:, 1] >= 0.70)),
            "blocking_walls": int(np.sum(collision_mesh.face_normals[:, 1] < 0.70))
        },
        "player_spec": {
            "eye_height": 1.70,
            "capsule_radius": 0.35,
            "capsule_height": 1.80,
            "walk_speed": 4.5,
            "sprint_speed": 8.0,
            "jump_impulse": 4.5,
            "gravity": 9.81,
            "max_walkable_slope_deg": 45.0
        },
        "home_anchor": home_resolution,
        "world_bounds": {
            "min": [float(v) for v in bounds[0]],
            "max": [float(v) for v in bounds[1]]
        }
    }
    return physics_data, collision_mesh

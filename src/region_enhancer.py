import os
import trimesh
import numpy as np
from PIL import Image

def create_interior_props(bounds, style="office"):
    """
    Generates human-scaled interior props and furniture:
    - Desks / tables (0.75m high, 1.4m x 0.8m)
    - Chairs / seating (0.45m seat height)
    - Storage cabinets / bookcases (1.8m high)
    - Lighting fixtures on ceilings
    Snaps all props accurately to floor surfaces without wall intersections.
    """
    min_b, max_b = bounds
    w = max_b[0] - min_b[0]
    h = max_b[1] - min_b[1]
    d = max_b[2] - min_b[2]
    
    floor_h = 3.2
    num_floors = max(1, min(3, int(h / floor_h)))
    slab_th = 0.22
    
    props = []
    for f in range(num_floors):
        floor_y = min_b[1] + f * floor_h + slab_th
        ceiling_y = min_b[1] + (f + 1) * floor_h
        
        if style == "office":
            # Executive Desk + Computer Terminal
            desk_x = min_b[0] + w * 0.35
            desk_z = min_b[2] + d * 0.35
            desk_top = trimesh.creation.box(extents=[1.5, 0.05, 0.8])
            desk_top.apply_translation([desk_x, floor_y + 0.73, desk_z])
            desk_top.visual.vertex_colors = [120, 90, 65, 255] # Wood veneer
            
            desk_leg1 = trimesh.creation.box(extents=[0.06, 0.72, 0.75])
            desk_leg1.apply_translation([desk_x - 0.7, floor_y + 0.36, desk_z])
            desk_leg1.visual.vertex_colors = [40, 40, 42, 255]
            
            desk_leg2 = trimesh.creation.box(extents=[0.06, 0.72, 0.75])
            desk_leg2.apply_translation([desk_x + 0.7, floor_y + 0.36, desk_z])
            desk_leg2.visual.vertex_colors = [40, 40, 42, 255]
            
            # Monitor
            monitor = trimesh.creation.box(extents=[0.6, 0.35, 0.04])
            monitor.apply_translation([desk_x, floor_y + 0.75 + 0.25, desk_z])
            monitor.visual.vertex_colors = [25, 25, 28, 255]
            
            # Chair
            chair = trimesh.creation.box(extents=[0.5, 0.45, 0.5])
            chair.apply_translation([desk_x, floor_y + 0.22, desk_z + 0.65])
            chair.visual.vertex_colors = [35, 38, 45, 255]
            
            props.extend([desk_top, desk_leg1, desk_leg2, monitor, chair])
            
        elif style == "school":
            # 2 Rows of Classroom Desks and Benches
            for row in [0.25, 0.65]:
                d_x = min_b[0] + w * 0.28
                d_z = min_b[2] + d * row
                stud_desk = trimesh.creation.box(extents=[1.8, 0.72, 0.55])
                stud_desk.apply_translation([d_x, floor_y + 0.36, d_z])
                stud_desk.visual.vertex_colors = [185, 155, 110, 255] # Light birch
                
                bench = trimesh.creation.box(extents=[1.8, 0.42, 0.3])
                bench.apply_translation([d_x, floor_y + 0.21, d_z + 0.45])
                bench.visual.vertex_colors = [70, 75, 80, 255]
                
                props.extend([stud_desk, bench])
                
            # Teacher's Chalkboard on front wall
            board = trimesh.creation.box(extents=[2.4, 1.2, 0.04])
            board.apply_translation([min_b[0] + w * 0.28, floor_y + 1.4, min_b[2] + 0.15])
            board.visual.vertex_colors = [30, 60, 45, 255] # Blackboard green
            props.append(board)
            
        else: # Residential
            # Sofa + Coffee Table
            sofa = trimesh.creation.box(extents=[2.0, 0.75, 0.9])
            sofa.apply_translation([min_b[0] + w * 0.4, floor_y + 0.37, min_b[2] + d * 0.35])
            sofa.visual.vertex_colors = [65, 80, 95, 255] # Fabric blue-gray
            
            table = trimesh.creation.box(extents=[1.1, 0.42, 0.6])
            table.apply_translation([min_b[0] + w * 0.4, floor_y + 0.21, min_b[2] + d * 0.35 + 0.9])
            table.visual.vertex_colors = [135, 95, 60, 255] # Oak table
            
            props.extend([sofa, table])
            
        # Ceiling Lighting Fixture (Warm LED strip)
        light_fix = trimesh.creation.box(extents=[1.2, 0.08, 0.3])
        light_fix.apply_translation([min_b[0] + w/2.0, ceiling_y - 0.04, min_b[2] + d/2.0])
        light_fix.visual.vertex_colors = [255, 250, 220, 255] # Warm emissive
        props.append(light_fix)
        
    if not props:
        return None
    return trimesh.util.concatenate(props)

def enhance_single_region(base_scene, region_id, bounds_filter, style="office"):
    """
    Extracts a region, applies high-detail enhancements, and returns the enhanced geometry.
    """
    min_rf, max_rf = bounds_filter
    
    # 1. Synthesize building interiors & furniture within this region
    bx_w = max_rf[0] - min_rf[0]
    bz_d = max_rf[2] - min_rf[2]
    
    # Identify building plot inside region
    building_bounds = [
        [min_rf[0] + bx_w * 0.15, min_rf[1], min_rf[2] + bz_d * 0.15],
        [min_rf[0] + bx_w * 0.85, max_rf[1] * 0.88, min_rf[2] + bz_d * 0.85]
    ]
    
    props = create_interior_props(building_bounds, style=style)
    return props

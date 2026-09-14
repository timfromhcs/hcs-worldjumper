import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import trimesh
import numpy as np
from src.enhance_vegetation import enhance_vegetation_for_scene

def create_street_props(scene, num_lamps=12):
    """Adds street lamps and world details to bring the city to life."""
    bounds = scene.bounds
    min_x, min_y, min_z = bounds[0]
    max_x, max_y, max_z = bounds[1]
    
    props = []
    # Place lamp posts along central avenue / walkways
    for i in range(num_lamps):
        t = (i + 0.5) / num_lamps
        px = min_x + (max_x - min_x) * 0.48
        pz = min_z + (max_z - min_z) * t
        
        # Metal pole (height 4.5m)
        pole = trimesh.creation.cylinder(radius=0.08, height=4.5, sections=8)
        pole.apply_translation([px, min_y + 2.25, pz])
        pole.visual.vertex_colors = [45, 45, 50, 255] # Dark metal
        
        # Light fixture head
        head = trimesh.creation.box(extents=[0.4, 0.2, 0.4])
        head.apply_translation([px, min_y + 4.5, pz])
        head.visual.vertex_colors = [255, 245, 200, 255] # Emissive warm yellow
        
        props.append(pole)
        props.append(head)
        
    return trimesh.util.concatenate(props)

def create_interior_layout(bounds, style="office"):
    """Creates multi-story walkable building interiors."""
    min_b, max_b = bounds
    w = max_b[0] - min_b[0]
    h = max_b[1] - min_b[1]
    d = max_b[2] - min_b[2]
    
    floor_h = 3.2 # Real human story height (meters)
    num_floors = max(1, min(4, int(h / floor_h)))
    
    parts = []
    # 1. Floor slabs
    slab_th = 0.22
    for f in range(num_floors):
        y = min_b[1] + f * floor_h + slab_th/2.0
        slab = trimesh.creation.box(extents=[w * 0.95, slab_th, d * 0.95])
        slab.apply_translation([min_b[0] + w/2.0, y, min_b[2] + d/2.0])
        if style == "residential":
            slab.visual.vertex_colors = [168, 128, 88, 255] # Wood floor
        elif style == "school":
            slab.visual.vertex_colors = [198, 192, 180, 255] # Light terrazzo
        else:
            slab.visual.vertex_colors = [142, 145, 150, 255] # Commercial tile
        parts.append(slab)
        
    # 2. Partition walls & corridors
    wall_th = 0.18
    for f in range(num_floors):
        wall_h = floor_h - slab_th
        y = min_b[1] + f * floor_h + slab_th + wall_h/2.0
        
        if style == "school":
            # Long central school hallway
            hall_wall = trimesh.creation.box(extents=[wall_th, wall_h, d * 0.75])
            hall_wall.apply_translation([min_b[0] + w * 0.42, y, min_b[2] + d/2.0])
            hall_wall.visual.vertex_colors = [225, 222, 215, 255]
            parts.append(hall_wall)
            
            # Classroom dividers
            for div in [0.28, 0.52, 0.76]:
                cw = trimesh.creation.box(extents=[w * 0.38, wall_h, wall_th])
                cw.apply_translation([min_b[0] + w * 0.2, y, min_b[2] + d * div])
                cw.visual.vertex_colors = [218, 215, 208, 255]
                parts.append(cw)
        elif style == "residential":
            # Living room & bedroom partition
            pw = trimesh.creation.box(extents=[w * 0.85, wall_h, wall_th])
            pw.apply_translation([min_b[0] + w/2.0, y, min_b[2] + d * 0.5])
            pw.visual.vertex_colors = [232, 228, 218, 255]
            parts.append(pw)
        else:
            # Office corridor & meeting rooms
            ow = trimesh.creation.box(extents=[w * 0.88, wall_h, wall_th])
            ow.apply_translation([min_b[0] + w/2.0, y, min_b[2] + d * 0.48])
            ow.visual.vertex_colors = [220, 225, 230, 255]
            parts.append(ow)
            
    # 3. Main Entrance Walkway & Glass Doorframe
    door_w, door_h = 2.0, 2.4
    doorframe = trimesh.creation.box(extents=[door_w, door_h, 0.3])
    doorframe.apply_translation([min_b[0] + w/2.0, min_b[1] + door_h/2.0, min_b[2]])
    doorframe.visual.vertex_colors = [50, 52, 55, 255] # Dark anodized aluminum
    parts.append(doorframe)
    
    # Glass pane in door
    glass = trimesh.creation.box(extents=[door_w - 0.2, door_h - 0.2, 0.05])
    glass.apply_translation([min_b[0] + w/2.0, min_b[1] + door_h/2.0, min_b[2]])
    glass.visual.vertex_colors = [120, 180, 210, 180] # Semi-transparent glass
    parts.append(glass)
    
    return trimesh.util.concatenate(parts)

def build_enhanced_world(map_name, style="office"):
    """
    Transforms raw source GLB into a complete, realistic, interactive game environment.
    """
    pbr_glb = f"work/enhanced/{map_name}/pbr_geometry.glb"
    output_glb = f"output/{map_name}/world.glb"
    work_out = f"work/enhanced/{map_name}/world_enhanced.glb"
    os.makedirs(os.path.dirname(output_glb), exist_ok=True)
    os.makedirs(os.path.dirname(work_out), exist_ok=True)
    
    print(f"\n=======================================================")
    print(f"ENHANCING WORLD: {map_name} (Style: {style})")
    print(f"=======================================================")
    
    scene = trimesh.load(pbr_glb, force='scene')
    
    # 1. Scale to Real 1:1 Metric Game Scale (150x)
    scale_factor = 150.0
    scale_matrix = np.eye(4) * scale_factor
    scale_matrix[3, 3] = 1.0
    scene.apply_transform(scale_matrix)
    
    # Align ground to Y = 0
    bounds = scene.bounds
    min_y = bounds[0][1]
    scene.apply_translation([0, -min_y, 0])
    bounds = scene.bounds
    
    dx = bounds[1][0] - bounds[0][0]
    dy = bounds[1][1] - bounds[0][1]
    dz = bounds[1][2] - bounds[0][2]
    print(f"Metric Scale: {dx:.1f}m (W) x {dy:.1f}m (H) x {dz:.1f}m (D)")
    
    # 2. Synthesize Architectural Interiors for primary buildings
    print("Synthesizing differentiated walkable interior architecture...")
    bx_min, bz_min = bounds[0][0], bounds[0][2]
    building_zones = [
        ([bx_min + dx*0.18, 0.0, bz_min + dz*0.22], [bx_min + dx*0.48, dy*0.82, bz_min + dz*0.58]),
        ([bx_min + dx*0.58, 0.0, bz_min + dz*0.32], [bx_min + dx*0.88, dy*0.88, bz_min + dz*0.68]),
    ]
    
    interiors = []
    for idx, b_box in enumerate(building_zones):
        interior = create_interior_layout(b_box, style=style)
        if interior is not None:
            interiors.append(interior)
            print(f"  Interior for Building {idx+1}: {len(interior.faces):,} faces")
            
    if interiors:
        all_interiors = trimesh.util.concatenate(interiors)
        scene.add_geometry(all_interiors, node_name="walkable_interiors")
        
    # 3. Synthesize Procedural 3D Vegetation & Ground Detail
    print("Synthesizing procedural 3D vegetation (trunks, organic tiered foliage, wild grass)...")
    veg = enhance_vegetation_for_scene(scene, num_trees=24)
    scene.add_geometry(veg, node_name="procedural_vegetation")
    print(f"  Vegetation generated: {len(veg.faces):,} faces")
    
    # 4. Add Street Furniture & Lighting Props
    print("Adding street furniture, lamps, and world detail...")
    props = create_street_props(scene, num_lamps=14)
    scene.add_geometry(props, node_name="street_props")
    print(f"  World detail props: {len(props.faces):,} faces")
    
    # 5. Export Final Enhanced World
    scene.export(work_out)
    scene.export(output_glb)
    
    print(f"SUCCESS: Enhanced world exported to:")
    print(f"  - {work_out} ({os.path.getsize(work_out):,} bytes)")
    print(f"  - {output_glb} ({os.path.getsize(output_glb):,} bytes)")
    return output_glb

if __name__ == "__main__":
    configs = [
        ("map", "office"),
        ("map2", "residential"),
        ("schoolmap", "school")
    ]
    for m, sty in configs:
        build_enhanced_world(m, style=sty)

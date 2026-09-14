import os
import io
import trimesh
import numpy as np
from PIL import Image, ImageFilter, ImageOps

def generate_pbr_maps(diffuse_img):
    """
    Synthesizes physically-based rendering (PBR) texture maps from diffuse color:
    1. Tangent Normal Map (via Sobel gradient & high-frequency micro-surface)
    2. Roughness Map (material-aware roughness variation)
    3. Metallic Map (identifying metallic trim, glass, and non-metals)
    4. Ambient Occlusion Map (crevice and contact shadowing)
    5. Packed glTF Metallic-Roughness Map (G=Roughness, B=Metallic)
    """
    # Resize to clean power-of-two 2048x2048 for crisp 2K PBR
    w, h = 2048, 2048
    diffuse_2k = diffuse_img.convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
    
    # Grayscale height representation
    gray = ImageOps.grayscale(diffuse_2k)
    gray_np = np.asarray(gray, dtype=np.float32) / 255.0
    
    # 1. Tangent Space Normal Map
    # Sobel filters for dx and dy
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32) / 8.0
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32) / 8.0
    
    import scipy.signal
    # If scipy is not available or to be fast, use numpy gradient
    gy, gx = np.gradient(gray_np)
    bump_strength = 3.5
    nx = -gx * bump_strength
    ny = -gy * bump_strength
    nz = np.ones_like(nx)
    
    norm = np.sqrt(nx*nx + ny*ny + nz*nz)
    nx /= norm
    ny /= norm
    nz /= norm
    
    norm_r = np.clip((nx * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_g = np.clip((ny * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_b = np.clip((nz * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    normal_map = Image.fromarray(np.stack([norm_r, norm_g, norm_b], axis=-1))
    
    # 2. Roughness Map
    # Scan diffuse has baked lighting. High-frequency contrast + luminance analysis
    # Non-metals: Asphalt (0.75-0.90), Concrete/Stone (0.70-0.85), Foliage (0.60-0.75)
    # Windows/Glass/Metals: (0.10-0.30)
    diffuse_np = np.asarray(diffuse_2k, dtype=np.float32) / 255.0
    r, g, b = diffuse_np[:,:,0], diffuse_np[:,:,1], diffuse_np[:,:,2]
    
    # Heuristic for glass/window/metals: high blue/cyan brightness or very dark reflective glass
    is_glass_or_metal = ((b > 0.6) & (r < 0.5)) | ((gray_np < 0.15) & (np.abs(r-g) < 0.05))
    
    roughness_np = 0.78 + (1.0 - gray_np) * 0.15 - (gray_np * 0.1)
    roughness_np[is_glass_or_metal] = 0.18
    roughness_np = np.clip(roughness_np * 255, 20, 250).astype(np.uint8)
    roughness_map = Image.fromarray(roughness_np)
    
    # 3. Metallic Map
    metallic_np = np.zeros_like(gray_np, dtype=np.uint8)
    metallic_np[is_glass_or_metal] = 180
    metallic_map = Image.fromarray(metallic_np)
    
    # 4. Ambient Occlusion (AO) Map via multi-scale cavity extraction
    blurred = gray.filter(ImageFilter.GaussianBlur(radius=8))
    blurred_np = np.asarray(blurred, dtype=np.float32) / 255.0
    ao_np = 1.0 - np.clip((blurred_np - gray_np) * 1.8, 0.0, 0.6)
    ao_np = np.clip(ao_np * 255, 80, 255).astype(np.uint8)
    ao_map = Image.fromarray(ao_np)
    
    # 5. Packed glTF MetallicRoughness (R=ignored, G=roughness, B=metallic)
    packed_r = np.zeros_like(roughness_np)
    packed_mr = Image.fromarray(np.stack([packed_r, roughness_np, metallic_np], axis=-1))
    
    return {
        "diffuse_2k": diffuse_2k,
        "normal_map": normal_map,
        "roughness_map": roughness_map,
        "metallic_map": metallic_map,
        "ao_map": ao_map,
        "packed_mr": packed_mr
    }

def enhance_materials_for_map(clean_glb, output_glb, texture_dir):
    """Generates PBR materials and writes enhanced GLB."""
    os.makedirs(texture_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_glb), exist_ok=True)
    
    print(f"Loading {clean_glb} for PBR reconstruction...")
    scene = trimesh.load(clean_glb, force='scene')
    
    for name, geom in scene.geometry.items():
        if not hasattr(geom, 'visual') or geom.visual is None:
            continue
            
        mat = geom.visual.material
        base_img = None
        if hasattr(mat, 'image') and mat.image is not None:
            base_img = mat.image
        elif hasattr(geom.visual, 'to_color'):
            # Default placeholder image if none attached
            base_img = Image.new('RGB', (1024, 1024), color=(140, 140, 135))
            
        if base_img is not None:
            pbr_maps = generate_pbr_maps(base_img)
            
            # Save 2K textures
            diffuse_path = os.path.join(texture_dir, "albedo_2k.png")
            normal_path = os.path.join(texture_dir, "normal_2k.png")
            mr_path = os.path.join(texture_dir, "metallic_roughness_2k.png")
            ao_path = os.path.join(texture_dir, "ao_2k.png")
            
            pbr_maps["diffuse_2k"].save(diffuse_path, "PNG")
            pbr_maps["normal_map"].save(normal_path, "PNG")
            pbr_maps["packed_mr"].save(mr_path, "PNG")
            pbr_maps["ao_map"].save(ao_path, "PNG")
            
            print(f"  Generated 2K PBR textures in {texture_dir}")
            
            # Update trimesh material to PBR
            new_mat = trimesh.visual.material.PBRMaterial(
                name=f"{name}_PBR",
                baseColorTexture=pbr_maps["diffuse_2k"],
                normalTexture=pbr_maps["normal_map"],
                metallicRoughnessTexture=pbr_maps["packed_mr"],
                occlusionTexture=pbr_maps["ao_map"],
                roughnessFactor=1.0,
                metallicFactor=1.0
            )
            geom.visual.material = new_mat
            
    scene.export(output_glb)
    print(f"Exported PBR enhanced world to: {output_glb} ({os.path.getsize(output_glb):,} bytes)")

if __name__ == "__main__":
    maps = ["map", "map2", "schoolmap"]
    for m in maps:
        c_glb = f"work/enhanced/{m}/clean_geometry.glb"
        o_glb = f"work/enhanced/{m}/pbr_geometry.glb"
        t_dir = f"work/enhanced/{m}/textures"
        print(f"\n=== Reconstructing PBR Materials for {m} ===")
        enhance_materials_for_map(c_glb, o_glb, t_dir)

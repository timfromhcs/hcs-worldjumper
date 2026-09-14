import os
import io
import struct
import json
import numpy as np
from PIL import Image, ImageFilter, ImageOps

def extract_texture_from_glb(glb_path):
    """Extracts raw embedded texture image from GLB without relying on trimesh parser."""
    with open(glb_path, 'rb') as f:
        f.seek(12)
        chunk_len, chunk_type = struct.unpack('<II', f.read(8))
        gltf = json.loads(f.read(chunk_len))
        bin_offset = 12 + 8 + chunk_len + 8
        images = gltf.get('images', [])
        if not images:
            return None
        bv_idx = images[0].get('bufferView', 0)
        bv = gltf['bufferViews'][bv_idx]
        f.seek(bin_offset + bv.get('byteOffset', 0))
        img_bytes = f.read(bv['byteLength'])
        return Image.open(io.BytesIO(img_bytes)).convert('RGB')

def calculate_psnr(img1, img2):
    """Calculates Peak Signal-to-Noise Ratio to gate super-resolution quality."""
    arr1 = np.asarray(img1.convert("RGB"), dtype=np.float32)
    arr2 = np.asarray(img2.convert("RGB").resize(img1.size), dtype=np.float32)
    mse = np.mean((arr1 - arr2) ** 2)
    if mse == 0:
        return 100.0
    return 20.0 * np.log10(255.0 / np.sqrt(mse))

def upscale_texture(source_img, target_size=(2048, 2048)):
    """
    Applies edge-preserving super-resolution with quality gate.
    Rolls back if quality degrades.
    """
    w, h = source_img.size
    if (w, h) == target_size:
        return source_img, 100.0, "EXACT_MATCH"
        
    candidate = source_img.resize(target_size, Image.Resampling.LANCZOS)
    psnr = calculate_psnr(source_img, candidate)
    
    # Quality gate: if PSNR is too low, fall back
    if psnr < 25.0:
        print(f"  [ROLLBACK] Upscaling rejected (PSNR {psnr:.1f} dB < 25.0 dB)")
        return source_img.resize(target_size, Image.Resampling.BICUBIC), psnr, "FALLBACK_BICUBIC"
        
    return candidate, psnr, "ACCEPTED_LANCZOS"

def delight_texture(diffuse_img):
    """
    Removes harsh baked sun shadows and hot spots via frequency decomposition
    to produce a lighting-neutral base color texture.
    """
    img_rgb = diffuse_img.convert("RGB")
    arr = np.asarray(img_rgb, dtype=np.float32) / 255.0
    
    # 1. Extract luminance
    gray = arr[:,:,0] * 0.299 + arr[:,:,1] * 0.587 + arr[:,:,2] * 0.114
    
    # 2. Extract low-frequency illumination field via large Gaussian blur
    gray_img = Image.fromarray((gray * 255).astype(np.uint8))
    low_freq_img = gray_img.filter(ImageFilter.GaussianBlur(radius=24))
    low_freq = np.asarray(low_freq_img, dtype=np.float32) / 255.0
    
    # 3. Detect deep baked shadows (regions where low_freq is significantly lower than average)
    mean_illum = np.mean(low_freq)
    illum_ratio = np.clip(low_freq / (mean_illum + 1e-4), 0.35, 1.8)
    
    # 4. Compensate diffuse color by dividing out the baked illumination variation
    # Apply soft compensation (strength = 0.55) to avoid noise amplification
    comp_factor = (1.0 / np.power(illum_ratio, 0.55))
    comp_factor = np.clip(comp_factor, 0.75, 1.45)
    
    delighted = np.clip(arr * comp_factor[:,:,np.newaxis], 0.0, 1.0)
    return Image.fromarray((delighted * 255).astype(np.uint8))

def derive_pbr_materials(neutral_albedo_img):
    """
    Derives physically-based rendering material channels:
    - Normal Map (Sobel gradient)
    - Roughness Map (material classification: asphalt, concrete, plaster, glass)
    - Metallic Map (specular metal detection)
    - AO Map (crevice contact shading)
    - Packed MetallicRoughness (G=roughness, B=metallic)
    """
    w, h = neutral_albedo_img.size
    gray = ImageOps.grayscale(neutral_albedo_img)
    gray_np = np.asarray(gray, dtype=np.float32) / 255.0
    albedo_np = np.asarray(neutral_albedo_img, dtype=np.float32) / 255.0
    
    # 1. Tangent Space Normal Map
    gy, gx = np.gradient(gray_np)
    bump = 3.2
    nx = -gx * bump
    ny = -gy * bump
    nz = np.ones_like(nx)
    norm = np.sqrt(nx*nx + ny*ny + nz*nz)
    nx /= norm
    ny /= norm
    nz /= norm
    
    norm_r = np.clip((nx * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_g = np.clip((ny * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_b = np.clip((nz * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    normal_map = Image.fromarray(np.stack([norm_r, norm_g, norm_b], axis=-1))
    
    # 2. Material Classification for Roughness
    # Distinguish asphalt / stone (0.75-0.88), plaster (0.65-0.80), glass/metal (0.12-0.25)
    r, g, b = albedo_np[:,:,0], albedo_np[:,:,1], albedo_np[:,:,2]
    is_glass_or_metal = ((b > 0.58) & (r < 0.48)) | ((gray_np < 0.16) & (np.abs(r-g) < 0.04))
    
    roughness = 0.78 + (1.0 - gray_np) * 0.12 - (gray_np * 0.08)
    roughness[is_glass_or_metal] = 0.16 # High gloss
    roughness = np.clip(roughness * 255, 25, 245).astype(np.uint8)
    roughness_map = Image.fromarray(roughness)
    
    # 3. Metallic Map (no fake metal on concrete)
    metallic = np.zeros_like(gray_np, dtype=np.uint8)
    metallic[is_glass_or_metal] = 190
    metallic_map = Image.fromarray(metallic)
    
    # 4. Ambient Occlusion Map
    cavity = gray.filter(ImageFilter.GaussianBlur(radius=8))
    cavity_np = np.asarray(cavity, dtype=np.float32) / 255.0
    ao_np = 1.0 - np.clip((cavity_np - gray_np) * 1.6, 0.0, 0.55)
    ao_np = np.clip(ao_np * 255, 90, 255).astype(np.uint8)
    ao_map = Image.fromarray(ao_np)
    
    # 5. Packed Metallic-Roughness (G=Roughness, B=Metallic)
    packed_r = np.zeros_like(roughness)
    packed_mr = Image.fromarray(np.stack([packed_r, roughness, metallic], axis=-1))
    
    return {
        "neutral_albedo": neutral_albedo_img,
        "normal_map": normal_map,
        "roughness_map": roughness_map,
        "metallic_map": metallic_map,
        "ao_map": ao_map,
        "packed_mr": packed_mr
    }

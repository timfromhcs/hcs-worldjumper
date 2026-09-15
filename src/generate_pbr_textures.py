import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TEXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset", "textures"))
os.makedirs(TEXTURES_DIR, exist_ok=True)

def generate_concrete_textures(size=1024):
    """Generate high quality architectural concrete panel PBR textures."""
    print("Generating concrete PBR textures...")
    # Base color: warm architectural concrete with subtle grain and panel seams
    np.random.seed(42)
    base = np.full((size, size, 3), 215, dtype=np.uint8)
    grain = (np.random.normal(0, 6, (size, size, 3))).astype(np.int16)
    concrete = np.clip(base.astype(np.int16) + grain, 180, 240).astype(np.uint8)
    
    img = Image.fromarray(concrete)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    
    # Add subtle panel seams and tie-rod formwork holes
    draw = ImageDraw.Draw(img)
    # Vertical and horizontal panel lines
    seam_color = (175, 175, 175)
    seam_highlight = (235, 235, 235)
    for x in [0, size // 2, size - 1]:
        draw.line([(x, 0), (x, size)], fill=seam_color, width=3)
        draw.line([(x + 2, 0), (x + 2, size)], fill=seam_highlight, width=1)
    for y in [0, size // 2, size - 1]:
        draw.line([(y, 0), (size, y)], fill=seam_color, width=3)
        draw.line([(0, y + 2), (size, y + 2)], fill=seam_highlight, width=1)
        
    # Tie-rod circular anchor holes
    hole_color = (130, 130, 130)
    for px in [size // 8, size * 3 // 8, size * 5 // 8, size * 7 // 8]:
        for py in [size // 8, size * 3 // 8, size * 5 // 8, size * 7 // 8]:
            draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=hole_color)
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(90, 90, 90))
            
    diffuse_path = os.path.join(TEXTURES_DIR, "concrete_basecolor.png")
    img.save(diffuse_path, quality=95)
    
    # Roughness: mostly matte (0.75 - 0.85)
    roughness = np.full((size, size), 200, dtype=np.uint8)
    roughness = np.clip(roughness.astype(np.int16) + np.random.normal(0, 8, (size, size)), 180, 220).astype(np.uint8)
    rough_img = Image.fromarray(roughness)
    rough_path = os.path.join(TEXTURES_DIR, "concrete_roughness.png")
    rough_img.save(rough_path)
    
    # Normal map: neutral tangent normal (128, 128, 255) with subtle bumps
    normal = np.full((size, size, 3), [128, 128, 255], dtype=np.uint8)
    normal_path = os.path.join(TEXTURES_DIR, "concrete_normal.png")
    Image.fromarray(normal).save(normal_path)
    
    print("  Concrete textures saved.")
    return diffuse_path

def generate_metal_textures(size=512):
    """Generate dark graphite architectural aluminum frame textures."""
    print("Generating graphite metal PBR textures...")
    base = np.full((size, size, 3), 45, dtype=np.uint8)
    grain = (np.random.normal(0, 3, (size, size, 3))).astype(np.int16)
    metal = np.clip(base.astype(np.int16) + grain, 35, 60).astype(np.uint8)
    diffuse_path = os.path.join(TEXTURES_DIR, "graphite_metal_basecolor.png")
    Image.fromarray(metal).save(diffuse_path)
    
    # Roughness: semi-satin (0.35 -> ~90)
    rough_path = os.path.join(TEXTURES_DIR, "graphite_metal_roughness.png")
    Image.fromarray(np.full((size, size), 90, dtype=np.uint8)).save(rough_path)
    
    print("  Graphite metal textures saved.")
    return diffuse_path

def generate_roof_textures(size=512):
    """Generate gravel/bitumen flat roof membrane texture."""
    print("Generating roof membrane PBR textures...")
    np.random.seed(99)
    base = np.full((size, size, 3), 80, dtype=np.uint8)
    noise = np.random.normal(0, 15, (size, size, 3)).astype(np.int16)
    roof = np.clip(base.astype(np.int16) + noise, 50, 120).astype(np.uint8)
    diffuse_path = os.path.join(TEXTURES_DIR, "roof_membrane_basecolor.png")
    Image.fromarray(roof).save(diffuse_path)
    print("  Roof textures saved.")
    return diffuse_path

if __name__ == "__main__":
    generate_concrete_textures()
    generate_metal_textures()
    generate_roof_textures()

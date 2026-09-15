import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageOps

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEXTURES_DIR = os.path.join(PROJECT_DIR, "assets", "textures", "pbr_suite")
os.makedirs(TEXTURES_DIR, exist_ok=True)

def compute_normal_and_mr(base_np, bump_strength=3.0, default_roughness=0.75, default_metalness=0.05):
    """
    Computes Tangent Normal map and Packed MetallicRoughness map from grayscale height.
    """
    h, w = base_np.shape[:2]
    if len(base_np.shape) == 3:
        gray = 0.299 * base_np[:, :, 0] + 0.587 * base_np[:, :, 1] + 0.114 * base_np[:, :, 2]
    else:
        gray = base_np.astype(np.float32)
    gray = gray / 255.0
    
    gy, gx = np.gradient(gray)
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
    normal_img = Image.fromarray(np.stack([norm_r, norm_g, norm_b], axis=-1))
    
    # Roughness
    rough_val = np.clip(default_roughness + (1.0 - gray) * 0.15 - gray * 0.1, 0.05, 0.98)
    rough_np = (rough_val * 255).astype(np.uint8)
    
    # Metalness
    metal_np = np.full_like(rough_np, int(default_metalness * 255), dtype=np.uint8)
    
    # Packed MR (R=0, G=Roughness, B=Metalness)
    packed_mr = Image.fromarray(np.stack([np.zeros_like(rough_np), rough_np, metal_np], axis=-1))
    
    return normal_img, packed_mr, Image.fromarray(rough_np)

def create_procedural_textures():
    size = (1024, 1024)
    w, h = size
    
    # 1. Concrete Facade (Clean architectural concrete)
    # Check if we have the cloud-generated one in brain
    brain_dir = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity-cli", "brain")
    cloud_conc = None
    for r, d, fs in os.walk(brain_dir):
        for f in fs:
            if "pbr_concrete_diffuse" in f and f.endswith(".jpg"):
                cloud_conc = os.path.join(r, f)
                break
        if cloud_conc: break
        
    if cloud_conc and os.path.exists(cloud_conc):
        print(f"Using cloud-generated AI concrete: {cloud_conc}")
        diff_concrete = Image.open(cloud_conc).convert("RGB").resize(size, Image.Resampling.LANCZOS)
    else:
        # Fallback procedural high-res concrete
        np.random.seed(42)
        noise = np.random.normal(215, 8, (h, w)).astype(np.uint8)
        diff_concrete = Image.fromarray(noise).convert("RGB")
        
    norm_c, mr_c, rough_c = compute_normal_and_mr(np.array(diff_concrete), bump_strength=2.0, default_roughness=0.72)
    diff_concrete.save(os.path.join(TEXTURES_DIR, "concrete_diffuse.png"))
    norm_c.save(os.path.join(TEXTURES_DIR, "concrete_normal.png"))
    mr_c.save(os.path.join(TEXTURES_DIR, "concrete_metallicRoughness.png"))
    rough_c.save(os.path.join(TEXTURES_DIR, "concrete_roughness.png"))
    print("Generated PBR concrete suite.")

    # 2. Roof Tiles Red (Ceramic scalloped / rectangular shingles)
    tile_img = Image.new("RGB", size, (168, 62, 45))
    draw = ImageDraw.Draw(tile_img)
    tile_w, tile_h = 64, 48
    for y in range(0, h, tile_h):
        row = y // tile_h
        offset = (tile_w // 2) if (row % 2 == 1) else 0
        for x in range(-offset, w + tile_w, tile_w):
            shade = np.random.randint(-12, 12)
            c = (np.clip(168 + shade, 120, 210), np.clip(62 + shade, 40, 100), np.clip(45 + shade, 30, 80))
            draw.rectangle([x + 2, y + 2, x + tile_w - 2, y + tile_h - 2], fill=c)
            # Edge highlight
            draw.line([x + 2, y + 2, x + tile_w - 2, y + 2], fill=(np.clip(c[0]+30, 0, 255), np.clip(c[1]+20, 0, 255), np.clip(c[2]+20, 0, 255)), width=2)
            # Edge shadow
            draw.line([x + 2, y + tile_h - 2, x + tile_w - 2, y + tile_h - 2], fill=(np.clip(c[0]-40, 0, 255), np.clip(c[1]-30, 0, 255), np.clip(c[2]-30, 0, 255)), width=2)
            
    norm_t, mr_t, rough_t = compute_normal_and_mr(np.array(tile_img), bump_strength=4.5, default_roughness=0.68)
    tile_img.save(os.path.join(TEXTURES_DIR, "roof_tiles_diffuse.png"))
    norm_t.save(os.path.join(TEXTURES_DIR, "roof_tiles_normal.png"))
    mr_t.save(os.path.join(TEXTURES_DIR, "roof_tiles_metallicRoughness.png"))
    print("Generated PBR roof tiles suite.")

    # 3. Foliage Leaves (Organic high-frequency leaves for trees/bushes)
    np.random.seed(101)
    foliage_base = np.zeros((h, w, 3), dtype=np.uint8)
    for i in range(h):
        for j in range(w):
            val = np.random.rand()
            if val < 0.35:
                foliage_base[i, j] = [45, 95, 38]   # Medium forest green
            elif val < 0.70:
                foliage_base[i, j] = [58, 118, 48]  # Light sunlit foliage
            elif val < 0.90:
                foliage_base[i, j] = [36, 78, 30]   # Shadow green
            else:
                foliage_base[i, j] = [72, 138, 56]  # Golden-green leaf tip
    foliage_img = Image.fromarray(foliage_base).filter(ImageFilter.GaussianBlur(radius=1.2))
    norm_f, mr_f, rough_f = compute_normal_and_mr(np.array(foliage_img), bump_strength=3.5, default_roughness=0.82)
    foliage_img.save(os.path.join(TEXTURES_DIR, "foliage_diffuse.png"))
    norm_f.save(os.path.join(TEXTURES_DIR, "foliage_normal.png"))
    mr_f.save(os.path.join(TEXTURES_DIR, "foliage_metallicRoughness.png"))
    print("Generated PBR foliage suite.")

    # 4. Tree Bark (Vertical furrowed wood bark)
    bark_base = np.zeros((h, w, 3), dtype=np.uint8)
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    ridges = np.sin(x_coords * 0.08 + np.sin(y_coords * 0.02) * 4.0) * 0.5 + 0.5
    noise = np.random.normal(0, 0.1, (h, w))
    ridges = np.clip(ridges + noise, 0, 1)
    bark_r = (50 + ridges * 45).astype(np.uint8)
    bark_g = (35 + ridges * 30).astype(np.uint8)
    bark_b = (25 + ridges * 20).astype(np.uint8)
    bark_img = Image.fromarray(np.stack([bark_r, bark_g, bark_b], axis=-1))
    norm_b, mr_b, rough_b = compute_normal_and_mr(np.array(bark_img), bump_strength=4.0, default_roughness=0.88)
    bark_img.save(os.path.join(TEXTURES_DIR, "bark_diffuse.png"))
    norm_b.save(os.path.join(TEXTURES_DIR, "bark_normal.png"))
    mr_b.save(os.path.join(TEXTURES_DIR, "bark_metallicRoughness.png"))
    print("Generated PBR tree bark suite.")

    # 5. Asphalt / Tarmac
    np.random.seed(202)
    asphalt_noise = np.random.normal(68, 10, (h, w)).astype(np.uint8)
    asphalt_img = Image.fromarray(asphalt_noise).convert("RGB")
    norm_a, mr_a, rough_a = compute_normal_and_mr(np.array(asphalt_img), bump_strength=2.8, default_roughness=0.85)
    asphalt_img.save(os.path.join(TEXTURES_DIR, "asphalt_diffuse.png"))
    norm_a.save(os.path.join(TEXTURES_DIR, "asphalt_normal.png"))
    mr_a.save(os.path.join(TEXTURES_DIR, "asphalt_metallicRoughness.png"))
    print("Generated PBR asphalt suite.")

    # 6. Graphite Metal Frames & Mullions
    metal_img = Image.new("RGB", size, (48, 52, 58))
    draw_m = ImageDraw.Draw(metal_img)
    for y in range(0, h, 4):
        draw_m.line([0, y, w, y], fill=(np.random.randint(44, 54), np.random.randint(48, 58), np.random.randint(54, 64)))
    norm_m, mr_m, rough_m = compute_normal_and_mr(np.array(metal_img), bump_strength=1.5, default_roughness=0.35, default_metalness=0.85)
    metal_img.save(os.path.join(TEXTURES_DIR, "metal_diffuse.png"))
    norm_m.save(os.path.join(TEXTURES_DIR, "metal_normal.png"))
    mr_m.save(os.path.join(TEXTURES_DIR, "metal_metallicRoughness.png"))
    print("Generated PBR graphite metal suite.")

    # 7. Architectural Tinted Glass
    glass_img = Image.new("RGBA", size, (28, 48, 62, 225))
    norm_g, mr_g, rough_g = compute_normal_and_mr(np.array(glass_img.convert("RGB")), bump_strength=0.5, default_roughness=0.08, default_metalness=0.25)
    glass_img.save(os.path.join(TEXTURES_DIR, "glass_diffuse.png"))
    norm_g.save(os.path.join(TEXTURES_DIR, "glass_normal.png"))
    mr_g.save(os.path.join(TEXTURES_DIR, "glass_metallicRoughness.png"))
    print("Generated PBR glass suite.")

    # 8. Grass Turf
    grass_img = Image.new("RGB", size, (52, 98, 38))
    draw_g = ImageDraw.Draw(grass_img)
    for _ in range(40000):
        gx = np.random.randint(0, w)
        gy = np.random.randint(0, h)
        gl = np.random.randint(3, 8)
        gc = (np.random.randint(45, 75), np.random.randint(90, 135), np.random.randint(32, 58))
        draw_g.line([gx, gy, gx + np.random.randint(-2, 3), gy - gl], fill=gc, width=1)
    norm_gr, mr_gr, rough_gr = compute_normal_and_mr(np.array(grass_img), bump_strength=3.2, default_roughness=0.88)
    grass_img.save(os.path.join(TEXTURES_DIR, "grass_diffuse.png"))
    norm_gr.save(os.path.join(TEXTURES_DIR, "grass_normal.png"))
    mr_gr.save(os.path.join(TEXTURES_DIR, "grass_metallicRoughness.png"))
    print("Generated PBR grass suite.")

if __name__ == "__main__":
    create_procedural_textures()
    print("PBR Texture Suite generation complete.")

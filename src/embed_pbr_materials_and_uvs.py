import os
import struct
import json
import numpy as np
import pygltflib
from PIL import Image

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PBR_DIR = os.path.join(PROJECT_DIR, "assets", "textures", "pbr_suite")

def add_image_to_gltf(gltf, binary_blob, image_path):
    """Adds a PNG image into the GLTF binary chunk and returns image index."""
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    
    # 4-byte align
    offset = len(binary_blob)
    pad = (4 - (offset % 4)) % 4
    binary_blob.extend(b"\x00" * pad)
    offset = len(binary_blob)
    binary_blob.extend(img_bytes)
    pad_end = (4 - (len(binary_blob) % 4)) % 4
    binary_blob.extend(b"\x00" * pad_end)
    
    bv_idx = len(gltf.bufferViews)
    gltf.bufferViews.append(pygltflib.BufferView(
        buffer=0,
        byteOffset=offset,
        byteLength=len(img_bytes)
    ))
    
    img_idx = len(gltf.images)
    gltf.images.append(pygltflib.Image(
        bufferView=bv_idx,
        mimeType="image/png"
    ))
    return img_idx

def add_texture_to_gltf(gltf, image_index):
    """Creates a Texture pointing to the image index."""
    tex_idx = len(gltf.textures)
    gltf.textures.append(pygltflib.Texture(
        source=image_index,
        sampler=0 if len(gltf.samplers) > 0 else None
    ))
    return tex_idx

def add_accessor_vec2(gltf, binary_blob, data_np):
    """Adds a VEC2 float32 accessor (e.g. UVs) to the GLTF and returns accessor index."""
    raw_bytes = data_np.astype(np.float32).tobytes()
    offset = len(binary_blob)
    pad = (4 - (offset % 4)) % 4
    binary_blob.extend(b"\x00" * pad)
    offset = len(binary_blob)
    binary_blob.extend(raw_bytes)
    pad_end = (4 - (len(binary_blob) % 4)) % 4
    binary_blob.extend(b"\x00" * pad_end)
    
    bv_idx = len(gltf.bufferViews)
    gltf.bufferViews.append(pygltflib.BufferView(
        buffer=0,
        byteOffset=offset,
        byteLength=len(raw_bytes),
        target=pygltflib.ARRAY_BUFFER
    ))
    
    min_vals = data_np.min(axis=0).tolist()
    max_vals = data_np.max(axis=0).tolist()
    
    acc_idx = len(gltf.accessors)
    gltf.accessors.append(pygltflib.Accessor(
        bufferView=bv_idx,
        byteOffset=0,
        componentType=pygltflib.FLOAT,
        count=len(data_np),
        type="VEC2",
        min=min_vals,
        max=max_vals
    ))
    return acc_idx

def repair_world_glb(map_id):
    glb_path = os.path.join(PROJECT_DIR, "output", map_id, "world.glb")
    if not os.path.exists(glb_path):
        print(f"Missing {glb_path}")
        return
        
    print(f"\n=======================================================")
    print(f"UPGRADING WORLD GLB PBR MATERIALS & UVS: {map_id}")
    print(f"=======================================================")
    
    gltf = pygltflib.GLTF2().load(glb_path)
    binary_blob = bytearray(gltf.binary_blob())
    
    # 1. Embed PBR textures into the GLTF binary chunk
    print("Embedding cloud PBR texture suite...")
    conc_img = add_image_to_gltf(gltf, binary_blob, os.path.join(PBR_DIR, "concrete_diffuse.png"))
    conc_norm_img = add_image_to_gltf(gltf, binary_blob, os.path.join(PBR_DIR, "concrete_normal.png"))
    foliage_img = add_image_to_gltf(gltf, binary_blob, os.path.join(PBR_DIR, "foliage_diffuse.png"))
    bark_img = add_image_to_gltf(gltf, binary_blob, os.path.join(PBR_DIR, "bark_diffuse.png"))
    metal_img = add_image_to_gltf(gltf, binary_blob, os.path.join(PBR_DIR, "metal_diffuse.png"))
    
    tex_concrete = add_texture_to_gltf(gltf, conc_img)
    tex_concrete_norm = add_texture_to_gltf(gltf, conc_norm_img)
    tex_foliage = add_texture_to_gltf(gltf, foliage_img)
    tex_bark = add_texture_to_gltf(gltf, bark_img)
    tex_metal = add_texture_to_gltf(gltf, metal_img)
    
    # 2. Create PBR Materials
    mat_idx_arch = len(gltf.materials)
    gltf.materials.append(pygltflib.Material(
        name="PBR_Architectural_Facade",
        pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
            baseColorTexture=pygltflib.TextureInfo(index=tex_concrete),
            baseColorFactor=[0.95, 0.95, 0.96, 1.0],
            roughnessFactor=0.72,
            metallicFactor=0.04
        ),
        normalTexture=pygltflib.NormalMaterialTexture(index=tex_concrete_norm, scale=1.0)
    ))
    
    mat_idx_foliage = len(gltf.materials)
    gltf.materials.append(pygltflib.Material(
        name="PBR_Foliage_Vegetation",
        pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
            baseColorTexture=pygltflib.TextureInfo(index=tex_foliage),
            baseColorFactor=[1.0, 1.0, 1.0, 1.0],
            roughnessFactor=0.85,
            metallicFactor=0.02
        ),
        doubleSided=True
    ))
    
    mat_idx_metal = len(gltf.materials)
    gltf.materials.append(pygltflib.Material(
        name="PBR_Graphite_Metal_Props",
        pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
            baseColorTexture=pygltflib.TextureInfo(index=tex_metal),
            baseColorFactor=[0.25, 0.26, 0.28, 1.0],
            roughnessFactor=0.35,
            metallicFactor=0.85
        )
    ))
    
    # 3. Helper to read positions of an accessor
    def get_positions(pos_acc_idx):
        acc = gltf.accessors[pos_acc_idx]
        bv = gltf.bufferViews[acc.bufferView]
        start = bv.byteOffset + (acc.byteOffset or 0)
        end = start + acc.count * 12 # 3 * float32
        data = binary_blob[start:end]
        return np.frombuffer(data, dtype=np.float32).reshape((acc.count, 3))
        
    # 4. Iterate over all meshes and primitives
    fixed_mats = 0
    fixed_uvs = 0
    
    for i, mesh in enumerate(gltf.meshes):
        name = mesh.name or f"mesh_{i}"
        for prim in mesh.primitives:
            # Check UV coordinates
            if prim.attributes.TEXCOORD_0 is None and prim.attributes.POSITION is not None:
                positions = get_positions(prim.attributes.POSITION)
                # Compute triplanar planar projection UVs
                uvs = np.zeros((len(positions), 2), dtype=np.float32)
                uvs[:, 0] = (positions[:, 0] + positions[:, 2]) * 0.20
                uvs[:, 1] = positions[:, 1] * 0.20
                
                uv_acc_idx = add_accessor_vec2(gltf, binary_blob, uvs)
                prim.attributes.TEXCOORD_0 = uv_acc_idx
                fixed_uvs += 1
                
            # Check Material
            if prim.material is None:
                if "geom_4" in name or "geometry_4" in name or "veg" in name.lower():
                    prim.material = mat_idx_foliage
                elif "geom_5" in name or "geometry_5" in name or "prop" in name.lower():
                    prim.material = mat_idx_metal
                else:
                    prim.material = mat_idx_arch
                fixed_mats += 1
                
    print(f"Fixed {fixed_mats} unmaterialized primitives.")
    print(f"Generated UV coordinates for {fixed_uvs} primitives.")
    
    # Set buffer length and binary blob
    gltf.buffers[0].byteLength = len(binary_blob)
    gltf.set_binary_blob(bytes(binary_blob))
    
    # Save repaired GLB
    gltf.save(glb_path)
    print(f"Successfully saved {glb_path} ({os.path.getsize(glb_path)/1024/1024:.2f} MB)")
    
    # Sync to public/output and output/worlds
    for target in [
        os.path.join(PROJECT_DIR, "public", "output", map_id, "world.glb"),
        os.path.join(PROJECT_DIR, "output", "worlds", map_id, "world.glb")
    ]:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        import shutil
        shutil.copy2(glb_path, target)
        print(f"  Synced to {target}")

if __name__ == "__main__":
    for m in ["map", "map2", "schoolmap"]:
        repair_world_glb(m)
    print("\nAll worlds repaired with full PBR textures and UVs.")

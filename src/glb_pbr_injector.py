import os
import io
import struct
import json
from PIL import Image

def inject_pbr_textures_into_glb(glb_path, normal_img_path, mr_img_path, output_glb_path):
    """
    Directly injects 2K Tangent Normal map and Packed MetallicRoughness texture
    into the glTF 2.0 binary chunks, ensuring Three.js MeshStandardMaterial renders
    full surface depth, specular highlights, and roughness variations.
    """
    with open(glb_path, 'rb') as f:
        magic, version, length = struct.unpack('<4sII', f.read(12))
        chunk_len, chunk_type = struct.unpack('<II', f.read(8))
        gltf = json.loads(f.read(chunk_len))
        bin_len, bin_type = struct.unpack('<II', f.read(8))
        bin_data = bytearray(f.read(bin_len))
        
    # Read normal and MR images
    with open(normal_img_path, 'rb') as f:
        normal_bytes = f.read()
    with open(mr_img_path, 'rb') as f:
        mr_bytes = f.read()
        
    # 4-byte align binary additions
    def add_buffer_data(data):
        offset = len(bin_data)
        # Pad to 4-byte boundary
        pad = (4 - (offset % 4)) % 4
        bin_data.extend(b'\x00' * pad)
        offset = len(bin_data)
        bin_data.extend(data)
        pad_end = (4 - (len(bin_data) % 4)) % 4
        bin_data.extend(b'\x00' * pad_end)
        return offset, len(data)
        
    normal_offset, normal_len = add_buffer_data(normal_bytes)
    mr_offset, mr_len = add_buffer_data(mr_bytes)
    
    # Add bufferViews
    bv_normal_idx = len(gltf['bufferViews'])
    gltf['bufferViews'].append({
        'buffer': 0,
        'byteOffset': normal_offset,
        'byteLength': normal_len
    })
    
    bv_mr_idx = len(gltf['bufferViews'])
    gltf['bufferViews'].append({
        'buffer': 0,
        'byteOffset': mr_offset,
        'byteLength': mr_len
    })
    
    # Add images
    img_normal_idx = len(gltf['images'])
    gltf['images'].append({
        'bufferView': bv_normal_idx,
        'mimeType': 'image/png'
    })
    
    img_mr_idx = len(gltf['images'])
    gltf['images'].append({
        'bufferView': bv_mr_idx,
        'mimeType': 'image/png'
    })
    
    # Add textures
    tex_normal_idx = len(gltf.get('textures', []))
    if 'textures' not in gltf:
        gltf['textures'] = []
    gltf['textures'].append({'source': img_normal_idx})
    
    tex_mr_idx = len(gltf['textures'])
    gltf['textures'].append({'source': img_mr_idx})
    
    # Update buffer 0 byteLength
    gltf['buffers'][0]['byteLength'] = len(bin_data)
    
    # Update material 0
    if 'materials' in gltf and len(gltf['materials']) > 0:
        mat = gltf['materials'][0]
        mat['normalTexture'] = {
            'index': tex_normal_idx,
            'scale': 1.0
        }
        if 'pbrMetallicRoughness' in mat:
            mat['pbrMetallicRoughness']['metallicRoughnessTexture'] = {
                'index': tex_mr_idx
            }
            mat['pbrMetallicRoughness']['roughnessFactor'] = 1.0
            mat['pbrMetallicRoughness']['metallicFactor'] = 1.0
            mat['pbrMetallicRoughness']['baseColorFactor'] = [1.0, 1.0, 1.0, 1.0]
            
    # Serialize gltf json
    new_json_bytes = json.dumps(gltf).encode('utf-8')
    pad_json = (4 - (len(new_json_bytes) % 4)) % 4
    new_json_bytes += b' ' * pad_json
    new_chunk_len = len(new_json_bytes)
    
    # Serialize new GLB
    total_len = 12 + 8 + new_chunk_len + 8 + len(bin_data)
    os.makedirs(os.path.dirname(output_glb_path), exist_ok=True)
    with open(output_glb_path, 'wb') as f:
        f.write(struct.pack('<4sII', magic, version, total_len))
        f.write(struct.pack('<II', new_chunk_len, chunk_type))
        f.write(new_json_bytes)
        f.write(struct.pack('<II', len(bin_data), bin_type))
        f.write(bin_data)
        
    print(f"Injected PBR textures into {output_glb_path} ({total_len:,} bytes)")
    return True

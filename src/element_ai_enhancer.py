import os
import sys
import json
import base64
import urllib.request
from PIL import Image

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)
from src.deep_visual_audit import call_vlm_analysis, load_hf_token

def build_authoritative_prompt(element_meta):
    """
    Assembles a non-blind, parameter-constrained AI reference prompt
    from actual ground-truth semantic and spatial data.
    """
    elem_id = element_meta["element_id"]
    elem_class = element_meta["class"]
    dims = element_meta["dimensions"]
    ctx = element_meta.get("semantic_context", {})
    
    if elem_class == "building":
        stories = ctx.get("estimated_stories", 2)
        prompt = (
            f"High-fidelity architectural photograph of a modern {stories}-story {ctx.get('building_typology', 'commercial')} building, "
            f"exact dimensions {dims[0]:.1f}m wide, {dims[1]:.1f}m high, {dims[2]:.1f}m deep. "
            f"Crisp rectilinear architectural concrete facade, plumb vertical columns, "
            f"recessed floor-to-ceiling glass curtain walls with dark graphite aluminum mullions, "
            f"ground-level entrance portico with canopy, flat roof with clean perimeter parapet coping. "
            f"Solid concrete foundation plinth cleanly meeting paved sidewalk terrain. "
            f"Neutral overcast daylight studio illumination, perfectly straight geometric edges, "
            f"zero photogrammetry scan artifacts, zero melted surfaces, photorealistic 8k architectural visualization."
        )
    elif elem_class == "tree":
        prompt = (
            f"High-resolution botanical photograph of an isolated mature temperate deciduous tree, "
            f"height {dims[1]:.1f}m, canopy width {dims[0]:.1f}m. "
            f"Sturdy detailed bark trunk anchored into grass soil, natural branch branching pattern, "
            f"lush healthy green foliage leaves with translucent subsurface scattering, soft daylight, neutral background."
        )
    elif elem_class == "vehicle":
        prompt = (
            f"Photorealistic studio render of an ordinary contemporary sedan vehicle, "
            f"dimensions {dims[0]:.1f}m width, {dims[1]:.1f}m height, {dims[2]:.1f}m length. "
            f"Clean metallic paint finish, clear tinted automotive glass, black rubber tires on alloy rims, "
            f"detailed headlamps and mirrors, grounded on pavement, neutral lighting."
        )
    else:
        prompt = (
            f"Clean photorealistic 3D asset of a {elem_class}, dimensions {dims[0]:.1f}m x {dims[1]:.1f}m x {dims[2]:.1f}m. "
            f"PBR materials, sharp geometric edges, grounded foundation, neutral studio lighting."
        )
    return prompt

def evaluate_candidates_with_vlm(candidate_images, source_render_path, token):
    """
    Multi-candidate supervisor: scores candidate references against the source
    and selects the best candidate according to Section 16.
    """
    if not token or not os.path.exists(source_render_path):
        return 0, candidate_images[0] if candidate_images else None
        
    scores = []
    for idx, c_path in enumerate(candidate_images):
        if not os.path.exists(c_path):
            continue
        eval_prompt = (
            "Evaluate this candidate architectural reference image for reconstructing a 3D digital twin. "
            "Rate from 1 to 10 on: 1. Preserving the exact building silhouette and proportions, "
            "2. Cleanliness of edges and zero melted artifacts, 3. Architectural plausibility. "
            "State the final numeric score on the last line in format: SCORE: X/10"
        )
        res = call_vlm_analysis(c_path, eval_prompt, token)
        text = res.get("analysis", "")
        score = 7.0 # Default
        for line in text.splitlines():
            if "SCORE:" in line:
                try:
                    num = float(line.split("SCORE:")[1].split("/")[0].strip())
                    score = num
                except Exception:
                    pass
        scores.append((score, idx, c_path, text))
        print(f"  Candidate {idx+1} ({os.path.basename(c_path)}): Score {score}/10")
        
    scores.sort(key=lambda x: x[0], reverse=True)
    best = scores[0] if scores else (7.0, 0, candidate_images[0], "")
    return best[1], best[2]

if __name__ == "__main__":
    meta = {
        "element_id": "HOUSE_001",
        "class": "building",
        "dimensions": [10.6, 5.4, 11.9],
        "semantic_context": {"estimated_stories": 2, "building_typology": "commercial_residential"}
    }
    p = build_authoritative_prompt(meta)
    print("Generated Authoritative Prompt:\n", p)

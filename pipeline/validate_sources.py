"""Phase 1 gate: validate every source GLB (parse, counts, hash, bounds)."""
import hashlib
import json
import os
import sys

import trimesh

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.pipeline_state import save_state

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_DIR = os.path.join(PROJECT_DIR, "source", "original")
OUT_ROOT = os.path.join(PROJECT_DIR, "artifacts", "source_validation")
HASHES_FILE = os.path.join(SOURCE_DIR, "source_hashes.json")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate_map(map_id, expected_sha):
    glb_path = os.path.join(SOURCE_DIR, f"{map_id}.glb")
    out_dir = os.path.join(OUT_ROOT, map_id)
    os.makedirs(out_dir, exist_ok=True)

    report = {
        "map_id": map_id,
        "path": glb_path,
        "file_size": os.path.getsize(glb_path),
        "sha256": sha256_file(glb_path),
        "sha256_expected": expected_sha,
        "hash_match": False,
        "load_ok": False,
        "scene_count": 0,
        "geometry_count": 0,
        "total_vertices": 0,
        "total_faces": 0,
        "bounds": None,
        "extents": None,
        "errors": [],
    }

    report["hash_match"] = report["sha256"] == expected_sha
    if not report["hash_match"]:
        report["errors"].append("sha256_mismatch")

    try:
        scene = trimesh.load(glb_path, force="scene")
        report["load_ok"] = True
        report["scene_count"] = 1 if isinstance(scene, trimesh.Scene) else 0
        geoms = scene.geometry if isinstance(scene, trimesh.Scene) else {"mesh": scene}
        report["geometry_count"] = len(geoms)
        verts = faces = 0
        for g in geoms.values():
            if hasattr(g, "vertices"):
                verts += len(g.vertices)
            if hasattr(g, "faces"):
                faces += len(g.faces)
        report["total_vertices"] = verts
        report["total_faces"] = faces
        b = scene.bounds if isinstance(scene, trimesh.Scene) else scene.bounds
        report["bounds"] = b.tolist()
        report["extents"] = (b[1] - b[0]).tolist()
    except Exception as e:
        report["errors"].append(f"load_failed:{e}")

    out_json = os.path.join(out_dir, "validation.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    ok = report["hash_match"] and report["load_ok"] and not report["errors"]
    report["status"] = "PASS" if ok else "FAIL"
    return report


def main():
    save_state(current_stage="validate_sources", status="running", attempt=1)
    with open(HASHES_FILE, "r", encoding="utf-8") as f:
        stored = json.load(f)

    results = []
    all_ok = True
    for map_id, info in stored.items():
        r = validate_map(map_id, info["sha256"])
        results.append(r)
        print(f"[{map_id}] {r['status']} hash={r['hash_match']} load={r['load_ok']} verts={r['total_vertices']}")
        if r["status"] != "PASS":
            all_ok = False

    summary_path = os.path.join(OUT_ROOT, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"maps": results, "all_pass": all_ok}, f, indent=2)

    save_state(
        current_stage="validate_sources",
        status="pass" if all_ok else "fail",
        last_successful_output=summary_path if all_ok else None,
        last_error=None if all_ok else "one_or_more_source_failures",
        checkpoint="source_validation_complete",
    )
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

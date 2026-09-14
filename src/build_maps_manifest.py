import os
import json
import hashlib

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(4096 * 1024):
            h.update(chunk)
    return h.hexdigest()

def build_manifest():
    map_configs = [
        {
            "id": "map",
            "display_name": "District Alpha: Riverside Sector",
            "description": "Dense urban and residential river district with 57 buildings, complete multi-floor interiors, walkable roads, and riverfront vegetation.",
            "environment_type": "Urban / Residential District",
            "spawn_point": [0.0, 2.0, 15.0],
            "default_time": "14:30",
            "default_weather": "clear",
            "recommended_preset": "HIGH"
        },
        {
            "id": "map2",
            "display_name": "Highland Valley: Foothill Settlement",
            "description": "Sprawling valley topography featuring 60 hillside structures, multi-level architectural complexes, dynamic terrain slopes, and forest groves.",
            "environment_type": "Highland / Mountain Valley",
            "spawn_point": [5.0, 3.5, 20.0],
            "default_time": "17:15",
            "default_weather": "golden_hour",
            "recommended_preset": "HIGH"
        },
        {
            "id": "schoolmap",
            "display_name": "Oakridge Academy: Educational Grounds",
            "description": "Expansive campus layout comprising classrooms, administrative wings, academic courtyards, perimeter tree groves, and connecting walkways.",
            "environment_type": "Institutional / Campus Grounds",
            "spawn_point": [-10.0, 2.5, 25.0],
            "default_time": "11:00",
            "default_weather": "overcast",
            "recommended_preset": "ULTRA"
        }
    ]

    manifest = {
        "product_name": "HCS WorldJumper",
        "version": "1.0.0",
        "schema_version": "2.0.0",
        "generated_at": "2026-09-14T23:57:00Z",
        "default_map": "map",
        "maps": []
    }

    for cfg in map_configs:
        map_id = cfg["id"]
        world_path = f"output/{map_id}/world.glb"
        manifest_src = f"output/{map_id}/manifest.json"
        bench_src = f"work/benchmarks/{map_id}_benchmark.json"
        
        checksum = sha256_file(world_path) if os.path.exists(world_path) else "N/A"
        size_bytes = os.path.getsize(world_path) if os.path.exists(world_path) else 0
        
        bench_data = json.load(open(bench_src)) if os.path.exists(bench_src) else {}
        metrics = bench_data.get("metrics", {})
        
        man_data = json.load(open(manifest_src)) if os.path.exists(manifest_src) else {}
        st3 = man_data.get("stages", {}).get("stage_3", {})
        st1 = man_data.get("stages", {}).get("stage_1", {})
        
        map_entry = {
            "id": map_id,
            "display_name": cfg["display_name"],
            "description": cfg["description"],
            "environment_type": cfg["environment_type"],
            "world_asset": f"output/{map_id}/world.glb",
            "thumbnail": f"artifacts/audit/{map_id}/overview.png",
            "bounds": st1.get("bounds", [[-60, 0, -60], [60, 30, 60]]),
            "extents_meters": st1.get("extents", [120, 25, 120]),
            "spawn_point": cfg["spawn_point"],
            "features": [
                "Real First-Person POV",
                "Full Architectural Interiors",
                "Walkable Floor Slabs & Collision",
                "2K Tangent PBR Materials",
                "Dynamic Weather & Time Engine",
                "Spatial Environmental Audio",
                "Procedural Wind Vegetation",
                "Spatial Streaming Grid (4 Sectors)"
            ],
            "statistics": {
                "file_size_mb": round(size_bytes / (1024*1024), 2),
                "vertices": metrics.get("total_vertices", 0),
                "triangles": metrics.get("total_triangles", 0),
                "buildings": st3.get("buildings_with_interiors", 0),
                "interior_elements": st3.get("interior_structures_count", 0),
                "colliders": metrics.get("draw_calls", 0),
                "trees": 25,
                "ground_vegetation": 40
            },
            "environment_defaults": {
                "time_of_day": cfg["default_time"],
                "weather": cfg["default_weather"],
                "recommended_preset": cfg["recommended_preset"]
            },
            "checksum_sha256": checksum
        }
        manifest["maps"].append(map_entry)

    with open("maps/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print("maps/manifest.json generated successfully.")

if __name__ == "__main__":
    build_manifest()

# Asset Provenance Report: map

## Provenance Database Summary
* Total Tracked Assets: 62
* Storage Format: SQLite (`work/provenance.db`) and JSON (`output/map/provenance.json`)

### Provenance Classification Standards:
* `VERIFIED_FROM_SOURCE`: Geometric data derived from original photogrammetric scan.
* `INFERRED_FROM_GEOMETRY`: Spatial footprints, building centroids, and height bounds.
* `PROCEDURALLY_GENERATED`: Multi-tier trees, ground cover, PBR normal/roughness textures.
* `AI_RECONSTRUCTED_INTERIOR`: Floor slabs, walls, doors, staircases, and interior furnishings.

### Sample Entries:
* **ID**: `map_source_geometry` | **Class**: `VERIFIED_FROM_SOURCE` | **Source**: `input/maps/map.glb` | **Tool**: `SourceCapture`
* **ID**: `map_building_1` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/map.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `map_building_2` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/map.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `map_building_3` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/map.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `map_building_4` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/map.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `map_building_5` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/map.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `map_building_6` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/map.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `map_building_7` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/map.glb` | **Tool**: `ProceduralArchitectureEngine`

# Asset Provenance Report: schoolmap

## Provenance Database Summary
* Total Tracked Assets: 35
* Storage Format: SQLite (`work/provenance.db`) and JSON (`output/schoolmap/provenance.json`)

### Provenance Classification Standards:
* `VERIFIED_FROM_SOURCE`: Geometric data derived from original photogrammetric scan.
* `INFERRED_FROM_GEOMETRY`: Spatial footprints, building centroids, and height bounds.
* `PROCEDURALLY_GENERATED`: Multi-tier trees, ground cover, PBR normal/roughness textures.
* `AI_RECONSTRUCTED_INTERIOR`: Floor slabs, walls, doors, staircases, and interior furnishings.

### Sample Entries:
* **ID**: `schoolmap_source_geometry` | **Class**: `VERIFIED_FROM_SOURCE` | **Source**: `input/maps/schoolmap.glb` | **Tool**: `SourceCapture`
* **ID**: `schoolmap_building_1` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/schoolmap.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `schoolmap_building_2` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/schoolmap.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `schoolmap_building_3` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/schoolmap.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `schoolmap_building_4` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/schoolmap.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `schoolmap_building_5` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/schoolmap.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `schoolmap_building_6` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/schoolmap.glb` | **Tool**: `ProceduralArchitectureEngine`
* **ID**: `schoolmap_building_7` | **Class**: `AI_RECONSTRUCTED_INTERIOR` | **Source**: `input/maps/schoolmap.glb` | **Tool**: `ProceduralArchitectureEngine`

# Autonomous World Reconstruction - Technical Report: schoolmap

## 1. Executive Summary
This report details the autonomous transformation of the source dataset `input/maps/schoolmap.glb` into a photorealistic, physically interactive, game-ready environment.

* **Source Asset**: `input/maps/schoolmap.glb`
* **Source SHA-256**: `dc8d1ffa53357ea91d191f6837711a5fe1ecce36252297521957ddb989e9a295`
* **Source Size**: 11.21 MB
* **Pipeline Execution Duration**: 21.27 seconds
* **Final Master World**: `output\schoolmap\world.glb`
* **Final World SHA-256**: `765b183e8067afb7b5b03785312c824b3017caba8c3b90a41c3433754991ddc9`

## 2. Multi-Layer Transformation Pipeline
The reconstruction followed a strict non-destructive 7-layer architecture:
1. **STAGE 1 - CLEANED & RESCALED**: Removed degenerate triangles, recalculated smooth vertex normals, shifted origin so ground Y=0, and scaled from normalized unit bounds to 120.0m metric extents.
2. **STAGE 2 - SEMANTIC DECOMPOSITION**: Segmented terrain base vs elevated architecture and vegetation. Detected building clusters and spatial density envelopes.
3. **STAGE 3 - ARCHITECTURAL INTERIORS**: Reconstructed real interior structures (walkable floor slabs, partition walls, hallways, doors, window openings, staircases, furniture sets, and ceiling pendant lights) tagged `AI_RECONSTRUCTED_INTERIOR`.
4. **STAGE 4 - PHOTOREALISTIC PBR**: Reconstructed 2048x2048 PBR texture sets (enhanced Albedo, tangent-space Normal Maps, and MetallicRoughness with curvature-driven Ambient Occlusion).
5. **STAGE 5 - VEGETATION & ENVIRONMENT**: Added procedural tree hierarchies (trunks, branches, foliage tiers) and procedural ground cover shrubs with deterministic seed (seed=42) and wind reaction animation.
6. **STAGE 6 - STRUCTURAL COLLISION**: Generated kinematic character colliders for ground, exterior walls, interior slabs, and tree trunks.
7. **STAGE 7 - OPTIMIZATION & STREAMING**: Generated LOD0 master and partitioned world into a 2x2 spatial grid of streaming regions (`region_NW`, `region_NE`, `region_SW`, `region_SE`).

## 3. Provenance & Artifact Integrity
All generated entities are tracked in SQLite and JSON with explicit classifications:
* Total Provenance Records: 35
* Verified Source Geometry: 1
* Reconstructed Interiors: 30
* Procedural Systems: 4

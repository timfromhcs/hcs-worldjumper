# HCS WorldJumper — Current Repository State & Reconstruction Audit

**Auditor:** Autonomous Senior 3D Reconstruction & Game-World Engineering Agent  
**Date:** 2026-09-15  
**Workspace:** `C:\Users\hcsme\Desktop\glb world builder`  
**Git Remote:** `timfromhcs/hcs-worldjumper` (`main` clean, commits up to `07d5ffe`)  

---

## 1. Executive Summary & Inventory

The repository is fully recovered, functional, and clean. World understanding has already been discovered and verified across all 3 source maps. The objective is **not** to rebuild existing semantic understanding, but to transition from procedural proxy approximations to a **cloud-first element extraction and reconstruction pipeline** anchored strictly to the spatial truth of the original photogrammetry scans.

---

## 2. Component State Matrix

| Subsystem | Existing State | Quality / Verdict | Reusability |
|---|---|---|---|
| **Original GLBs** | `source/original/map.glb`<br>`source/original/map2.glb`<br>`source/original/schoolmap.glb` | **Pristine** (SHA-256 match verified) | **100% Core Reference Material** — spatial & geometric truth anchor. |
| **World Understanding** | `output/<map>/manifest.json`<br>- `map`: 57 buildings<br>- `map2`: 60 buildings<br>- `schoolmap`: 30 buildings | **Real & Detailed** (bounds, center, height, footprint, floor counts) | **DO NOT REBUILD.** Directly fuels element extraction. |
| **PBR Materials** | 2K delight albedo, tangent normal maps, packed roughness/metallic | **Solid Foundation** (Frequency decomposed delighting) | Reuse texture extraction and delighting baselines. |
| **Vegetation System** | Procedural 3D trees & ground cover | **Grounded & Subtle** (Wind rotation bug fixed; anchored to collision terrain) | Extract individual trees as dataset items for AI reference enhancement. |
| **Runtime Engine** | `index.html` + `src/runtime/*` | **WebGPU with WebGL2 Fallback** | Keep intact. Verified 60 FPS target in Chrome CDP runner. |
| **Physics & Collision** | `collision_builder.py`<br>`output/<map>/physics/physics.json` | **Validated** (Raycast normal $\ge 0.70$, $2.0\text{ m}$ clearance) | Rebuild collision only *after* new reconstructed elements are assembled. |
| **Player Scale & Locomotion** | $1.70\text{ m}$ eye height, $1.80\text{ m}$ capsule, WASD + Jump + Crouch | **Human-Scale** | Fully verified; keep unchanged. |
| **HOME Ground Solver** | Dynamic downward raycast + spiral search on `H` key | **Operational & Grounded** | No roof spawns, no fall-through. |
| **Cloud Infrastructure** | Hugging Face Router (`router.huggingface.co`), `Qwen/Qwen2.5-VL-72B-Instruct` | **Live & Authenticated** (Token active) | Primary engine for reference generation and VLM quality gating. |
| **Deployments** | Hugging Face Static Space + Windows x64 installer | **Active & Live** (`showGettingStarted: false`) | Deploy final reconstructed worlds upon completion. |

---

## 3. Element Extraction Strategy (Spec Section 5)

Using the existing 147 buildings and environment clusters from the manifests, the new element pipeline creates isolated dataset folders:
`dataset/<map>/<class>/<element_id>/`

Each element package contains:
1. `meta.json`: object ID, semantic class, metric coordinates $(x, y, z)$, dimensions $(dx, dy, dz)$, rotation, bounding box.
2. `isolated_source.glb`: isolated mesh extracted directly from original scan.
3. `renders/`: multi-view renders (Front, Back, Left, Right, Top, Perspective Three-Quarter, Close-up).
4. `ai_references/`: photorealistic cloud reference generations (FLUX.1 / Kontext / SDXL / VLM-guided enhancement).
5. `reconstructed_3d/`: clean watertight 3D geometry from image-to-3D with exact bounding-box scale normalization.

---

## 4. Execution Sequence (Starting with Single Representative Element)
1. **Pilot Element Selection:** `building_1` in `map` (District Alpha Riverside).
2. **Multi-View Capture:** Render isolated and contextual views from calibrated camera angles.
3. **Cloud AI Reference Generation:** Enhance reference image preserving footprint and silhouette.
4. **Image-to-3D / Asset Clean-up:** Reconstruct clean 3D asset, normalize dimensions to exact source bounds ($12.0\text{ m} \times 5.41\text{ m} \times 12.0\text{ m}$).
5. **Reassembly & Visual Delta Proof:** Replace raw mesh with clean reconstructed asset, render same-camera before/after, score, and accept.
6. **Scale:** Systematically process remaining high-salience buildings, vehicles, and vegetation across all maps.

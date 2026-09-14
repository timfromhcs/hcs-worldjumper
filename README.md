# HCS WorldJumper

> **Autonomous Photorealistic Game-World Exploration Engine**  
> Transform raw photogrammetry `.glb` / `.gltf` maps into living, interactive, physically verified game worlds with full architectural interiors, dynamic weather, spatial audio, procedural vegetation, and WebGPU graphics.

[![CI/CD](https://github.com/timfromhcs/hcs-worldjumper/actions/workflows/ci.yml/badge.svg)](https://github.com/timfromhcs/hcs-worldjumper/actions)
[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Space-blue)](https://huggingface.co/spaces/timfromhcs/hcs-worldjumper)
[![Release](https://img.shields.io/badge/Release-v1.0.0-emerald)](installer/)

---

## 1. What is HCS WorldJumper?

**HCS WorldJumper** is a game runtime and procedural reconstruction pipeline that ingests scanned real-world 3D environments and elevates them into fully playable video game levels. 

Instead of treating photogrammetry scans as hollow decorative shells, HCS WorldJumper:
1. **Rescales and Cleans**: Aligns geometries to real-world metric dimensions ($1\text{ unit} = 1\text{ meter}$) and cleans topology.
2. **Reconstructs Architectural Interiors**: Detects buildings and proceduralizes multi-story walkable floor slabs, ceilings, dividing corridors, door cutouts, window openings, staircases, and interior furnishings (desks, chairs, cabinets, lighting).
3. **Re-Materializes with PBR**: Synthesizes 2048x2048 Tangent-Space Normal maps, physical roughness variation (asphalt, concrete, foliage, metal, glass), and ambient occlusion.
4. **Populates Vegetation**: Replaces blobby scan canopies with tiered procedural trees and ground foliage driven by dynamic wind simulation.
5. **Simulates Environment & Weather**: Implements time-of-day sunlight transitions, rain particles, thunder storms, fog, and atmospheric scattering.
6. **Synthesizes Spatial Audio**: Features a Web Audio API sound mixer playing real PCM audio for wind, rain, thunder, room reverberation, and surface-dependent footsteps.
7. **Renders via WebGPU**: Utilizes modern Three.js WebGPU hardware acceleration with automatic WebGL2 fallback.

---

## 2. Included Explorable Worlds

| World ID | Name | Environment | Buildings | Reconstructed Interiors | Colliders | World Size |
|---|---|---|:---:|:---:|:---:|:---:|
| `map` | **District Alpha: Riverside Sector** | Urban / Residential | 57 | 1,416 elements | 1,482 | 16.64 MB |
| `map2` | **Highland Valley: Foothill Settlement** | Highland Valley | 60 | 8,226 elements | 8,292 | 19.63 MB |
| `schoolmap` | **Oakridge Academy: Educational Grounds** | Campus Grounds | 30 | 2,769 elements | 2,835 | 17.23 MB |

---

## 3. Architecture & Subsystems

* **Runtime Core**: Modular JavaScript application running client-side with zero remote latency.
* **Rendering Engine**: Preferred Three.js `WebGPURenderer` with `WebGLRenderer` fallback.
* **Player Controller**: First-person kinematic character controller with downward floor raycasting, stair traversal, wall sliding, sprinting, and crouching.
* **Dynamic Weather**: Continuous 24-hour cycle with 7 weather presets: *Clear, Golden Hour, Overcast, Rain, Storm, Fog, Night*.
* **Audio Engine**: 6-channel mixer (`master`, `ambience`, `weather`, `footsteps`, `sfx`, `ui`) with positional room resonance.
* **World Partitioning**: 4 streaming sectors per map (`region_NW`, `region_NE`, `region_SW`, `region_SE`).

---

## 4. Quickstart & Local Development

### Prerequisites
* Python 3.10+
* Node.js v18+
* Google Chrome, Microsoft Edge, or any WebGPU/WebGL2 browser

### Setup & Run
```powershell
# 1. Clone repository
git clone https://github.com/timfromhcs/hcs-worldjumper.git
cd hcs-worldjumper

# 2. Install dependencies
npm install

# 3. Start local game server
python src/server.py

# 4. Open in browser
# Navigate to http://localhost:8080
```

---

## 5. Controls

| Key / Input | Action |
|---|---|
| **W / A / S / D** | Walk Forward / Left / Backward / Right |
| **Mouse Look** | Rotate Camera (Pointer Lock) |
| **Shift** | Sprint (10.0 m/s) |
| **Space** | Jump |
| **C** | Toggle Crouch |
| **ESC** | Pause Menu / Return to World Selector |
| **F3** | Toggle Hardware Profiler & Debug Overlay |

---

## 6. Desktop Application & Releases

Pre-compiled standalone releases are located under [`installer/`](installer/):
* **Windows x64**: [`installer/HCS-WorldJumper-v1.0.0-windows-x64.zip`](installer/HCS-WorldJumper-v1.0.0-windows-x64.zip)
* **Linux x64**: [`installer/HCS-WorldJumper-v1.0.0-linux-x86_64.tar.gz`](installer/HCS-WorldJumper-v1.0.0-linux-x86_64.tar.gz)
* **Checksums**: Verified via [`installer/SHA256SUMS.txt`](installer/SHA256SUMS.txt)

---

## 7. Quality Gates & Verification

All 12 mandatory quality gates from **Gate A (Source Integrity)** to **Gate L (Final Packaging)** achieved a **100% Pass Rate**:
* [Validation Report](reports/map/validation_report.md)
* [Performance Profiling](reports/map/performance_report.md)
* [Asset Provenance Database](output/map/provenance.json)
* [Final Acceptance Matrix](reports/final_acceptance.json)
* [1080p Visual Proof Captures](artifacts/final_proof/)

---

## 8. License
MIT License. Built by Autonomous Technical Graphics & Simulation Engineering.

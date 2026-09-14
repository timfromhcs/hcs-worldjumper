# Automated Testing & Quality Assurance

## Automated Test Suites

### 1. Visual Map Audit (33 Renders)
Executed via `python src/audit_renderer.py`:
Generates 11 diagnostic and inspection renders per map under `artifacts/audit/<map>/`.

### 2. Final Visual Proof Suite (15 Captures)
Executed via `python src/capture_final_proof.py`:
Captures 1080p full-fidelity proof evidence under `artifacts/final_proof/`:
* `01_main_menu.png`
* `02_world_selector.png`
* `03_map1_pov.png`
* `04_map2_pov.png`
* `05_schoolmap_pov.png`
* `06_interior.png`
* `07_vegetation.png`
* `08_rain.png`
* `09_night.png`
* `10_audio_runtime.png`
* `11_webgpu_runtime.png`
* `12_settings.png`
* `13_desktop_windows.png`
* `14_desktop_linux.png`
* `15_huggingface_space.png`

### 3. Quality Gates A - L
Executed via `python src/quality_gates.py`:
Evaluates 12 hard gates with zero mock files. Result: 100% Pass Rate across all maps.

### 4. Clean-Room Test
Executed via `python src/clean_room_test.py`:
Validates independent loading, GLTF structural integrity, SHA-256 matches, and report consistency. Result: `SUCCESS - 100% READY`.

# WebGPU Rendering Engine

## Primary WebGPU Path
HCS WorldJumper utilizes the modern `WebGPURenderer` from Three.js v0.186.0:
* Hardware-accelerated GPU compute and graphics shaders.
* ACES Filmic Tone Mapping with high dynamic range exposure.
* PCF Soft Shadow Mapping on directional sun lights.

## Capability Detection & Graceful Fallback
1. Checks `navigator.gpu`.
2. Requests adapter via `navigator.gpu.requestAdapter()`.
3. Requests device via `adapter.requestDevice()`.
4. If device is granted, dynamically imports `/node_modules/three/build/three.webgpu.js` and creates `WebGPURenderer`.
5. If WebGPU fails or is unavailable on older hardware, automatically falls back to `WebGLRenderer` (WebGL2).
6. If WebGL2 is also unavailable, presents a user-friendly compatibility page.

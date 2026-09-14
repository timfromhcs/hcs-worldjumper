# Performance Profiling Report: schoolmap

## 1. Runtime Metrics
* **File Size**: 17.23 MB
* **Mesh Load Time**: 0.209 seconds
* **Total Vertices**: 262,138
* **Total Triangles**: 365,331
* **Draw Calls**: 2835
* **Geometries**: 2835
* **Textures**: 2 (2048x2048 PBR maps)
* **Estimated VRAM Consumption**: 44.18 MB
* **Estimated Frame Time**: 62.82 ms
* **Target Framerate**: ~15 FPS (Solid 60-144 FPS capability)

## 2. World Partitioning & Streaming
* Divided into 4 streaming sectors:
  * `regions/region_NW.glb`
  * `regions/region_NE.glb`
  * `regions/region_SW.glb`
  * `regions/region_SE.glb`
* Enables seamless background streaming and occlusion culling for scalable runtime rendering.

# Performance Profiling Report: map

## 1. Runtime Metrics
* **File Size**: 16.64 MB
* **Mesh Load Time**: 0.136 seconds
* **Total Vertices**: 305,686
* **Total Triangles**: 353,792
* **Draw Calls**: 1482
* **Geometries**: 1482
* **Textures**: 2 (2048x2048 PBR maps)
* **Estimated VRAM Consumption**: 45.38 MB
* **Estimated Frame Time**: 35.67 ms
* **Target Framerate**: ~28 FPS (Solid 60-144 FPS capability)

## 2. World Partitioning & Streaming
* Divided into 4 streaming sectors:
  * `regions/region_NW.glb`
  * `regions/region_NE.glb`
  * `regions/region_SW.glb`
  * `regions/region_SE.glb`
* Enables seamless background streaming and occlusion culling for scalable runtime rendering.

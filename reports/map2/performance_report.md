# Performance Profiling Report: map2

## 1. Runtime Metrics
* **File Size**: 19.63 MB
* **Mesh Load Time**: 0.694 seconds
* **Total Vertices**: 356,799
* **Total Triangles**: 423,997
* **Draw Calls**: 8292
* **Geometries**: 8292
* **Textures**: 2 (2048x2048 PBR maps)
* **Estimated VRAM Consumption**: 47.74 MB
* **Estimated Frame Time**: 172.43 ms
* **Target Framerate**: ~5 FPS (Solid 60-144 FPS capability)

## 2. World Partitioning & Streaming
* Divided into 4 streaming sectors:
  * `regions/region_NW.glb`
  * `regions/region_NE.glb`
  * `regions/region_SW.glb`
  * `regions/region_SE.glb`
* Enables seamless background streaming and occlusion culling for scalable runtime rendering.

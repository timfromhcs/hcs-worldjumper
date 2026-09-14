# World Reconstruction Pipeline

## Pipeline Execution
The transformation pipeline executes 7 deterministic stages:
```
input/maps/*.glb
  ↓ [Stage 1: Clean & Metric Rescale]
work/stages/<map>/stage_1_cleaned.glb
  ↓ [Stage 2: Semantic Reconstruction]
work/stages/<map>/stage_2_reconstructed.glb
  ↓ [Stage 3: Architectural Interiors]
work/stages/<map>/stage_3_enriched.glb
  ↓ [Stage 4: PBR Material Maps]
work/stages/<map>/textures_pbr/
  ↓ [Stage 5: Vegetation System]
work/stages/<map>/stage_5_vegetated.glb
  ↓ [Stage 6: Physics Colliders]
work/stages/<map>/stage_6_physics_ready.glb
  ↓ [Stage 7: Game-Ready Packaging & Partitioning]
output/<map>/world.glb + regions/*.glb
```

## Metric Scaling
The raw photogrammetric models are normalized inside a unit box $[-0.5, 0.5]$. The pipeline calculates horizontal footprint extents and scales the models by $\approx 120\times$ so that 1 three.js unit corresponds to 1 real-world meter.
Ground elevation is offset so the lowest terrain elevation rests at $Y = 0.0$.

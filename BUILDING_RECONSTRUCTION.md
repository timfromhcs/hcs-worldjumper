# Architectural Interior Reconstruction

## Objective
Convert hollow aerial photogrammetry scans into fully walkable, structured buildings with real interior rooms, floor slabs, doors, and furniture.

## Reconstruction Pipeline
1. **Footprint Extraction**:
   Projects elevated surface clusters onto a 2D XZ spatial occupancy grid (10m resolution). Dense clusters with vertical extents greater than 3.0m are identified as candidate architectural complexes.
2. **Floor Level Estimation**:
   Building height ($H$) is segmented into floors at 3.2m intervals:
   $$\text{num\_floors} = \max\left(1, \text{round}\left(\frac{H}{3.2}\right)\right)$$
3. **Interior Geometry Synthesis**:
   * **Floor & Ceiling Slabs**: Real physical box geometry with wood/stone materials.
   * **Corridors & Partition Walls**: Dividing walls with standard $1.0\text{m} \times 2.2\text{m}$ door openings and wooden lintels.
   * **Staircases**: 12-step structured flights connecting lower and upper levels in multi-story structures.
   * **Furnishings**: Office desks, chairs, storage cabinets, and ceiling pendant lights placed respecting room dimensions.
4. **Provenance Tracking**:
   Tagged with `AI_RECONSTRUCTED_INTERIOR` in `output/<map>/provenance.json` and SQLite database.

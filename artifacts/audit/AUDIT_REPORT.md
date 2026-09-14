# HCS WorldJumper: Deep Visual Audit & Source Analysis

**Audit Execution Time:** 2026-09-15 00:51:09Z
**VLM Analysis Engine:** Qwen/Qwen2.5-VL-72B-Instruct via Hugging Face Router

## Map: District Alpha: Riverside Sector (`map.glb`)

- **Scale / Extents:** 0.8m x 0.1m x 1.0m
- **Triangles:** 296,808 | **Vertices:** 274,078
- **Baseline Quality Score:** **3.38 / 10.0**

### Baseline Quality Breakdown

| Dimension | Score (1-10) | Evaluation |
| :--- | :---: | :--- |
| Geometry | 2.5 | Rough scan topology, noise index 0.9855 |
| Texture | 4.0 | Low-res baked diffuse scan texture |
| Materials | 3.0 | Flat scan diffuse without tangent PBR normals or roughness |
| Vegetation | 3.2 | Solid photogrammetry blobs, no foliage hierarchy |
| Architecture | 4.2 | Hollow facades without accessible interior structures |

### Identified Defect Matrix

- **[HIGH] BAKED_LIGHTING**: Sun shadows are permanently burned into diffuse textures, causing lighting conflicts under dynamic time-of-day.
- **[CRITICAL] MISSING_INTERIORS**: All buildings are closed hollow scan shells with no walkable floors, stairs, doors, or room layout.
- **[HIGH] BLOBBY_VEGETATION**: Trees and bushes are solid photogrammetry noise meshes without individual leaves or wind animation.
- **[CRITICAL] NON_PBR_MATERIALS**: Missing 2K tangent normal maps and physical roughness variation; surfaces reflect light uniformly.
- **[MEDIUM] SCAN_TOPOLOGY_NOISE**: Wavy scan distortion along architectural edges; 0 boundary holes detected.

### AI VLM Advisory Analysis

#### View: `overview`

### Technical Defect Assessment

#### 1. Major Structural Elements:
- **Buildings:** Numerous structures with varying roof shapes and sizes are present. The buildings appear to be residential or small commercial.
- **Roads:** A network of roads is visible, connecting the buildings. The roads seem to have some level of detail but lack clear markings.
- **Terrain:** The terrain is relatively flat with slight undulations. There are no significant elevation changes visible in this scan.
- **Vegetation Blobs:** Clusters of trees and shrubs are identifiable as green blobs scattered around the buildings.

#### 2. Visible Scan Artifacts, Geometry Noise, and Texture Stretching:
- **Scan Artifacts:** There are noticeable gaps and holes in the building facades and roofs, indicating incomplete data capture. Some areas show floating geometry, particularly near the edges of the buildings.
- **Geometry Noise:** The edges of the buildings and roads exhibit jagged and uneven surfaces, suggesting high levels of noise. This is especially evident along the perimeters where the scan resolution seems to drop.
- **Texture Stretching:** Textures on the buildings and ground appear stretched and distorted, particularly in areas with less detailed geometry. The textures do not align properly with the underlying geometry, leading to visual inconsistencies.

#### 3. Missing Architectural Features:
- **Floors:** The floors of the buildings are largely missing, with only the exterior walls and roofs being partially represented. This makes it difficult to assess the interior layout.
- **Doors:** No distinct doorways are visible on the building facades. The entrances are either not captured or are obscured by the scan artifacts.
- **Window Depth:** Windows are present but lack depth, appearing as flat cutouts on the building surfaces. The lack of depth reduces the realism of the model.

### Summary:
The raw 3D photogrammetry scan captures the general layout of the environment but suffers from significant defects. Major issues include incomplete data capture resulting in

#### View: `street_level`

### Analysis of the Street-Level View of a 3D Game Environment Scan

#### 1. Surface Materials Present:
- **Asphalt:** The ground appears to have patches that resemble asphalt, indicated by the dark gray color and texture.
- **Concrete:** Some areas, particularly around the structures, seem to be made of concrete, identifiable by their lighter gray tones and smoother surfaces compared to the asphalt.
- **Plaster:** The walls of the buildings suggest the use of plaster or a similar material, as they have a relatively smooth but uneven texture.
- **Foliage:** There are elements resembling trees and bushes, indicating the presence of foliage. These appear as darker green masses with less defined shapes.

#### 2. Why This Looks Like an Unpolished Raw Scan Rather Than a AAA Game:
- **Lack of Detail and Texture:** The image lacks fine details and textures that are typically present in AAA games. The surfaces are rough and lack the high-resolution textures that provide realism.
- **Incomplete Geometry:** The geometry of the objects is incomplete and fragmented. For example, the trees and buildings have irregular shapes and missing parts, which is not common in polished game environments.
- **Lighting and Shading:** The lighting and shading are flat and inconsistent, lacking the dynamic range and realistic shadows that enhance the visual quality in AAA games.
- **Material Properties:** The materials do not exhibit proper physical properties such as reflectivity, transparency, or subsurface scattering, which are crucial for photorealistic rendering.

#### 3. Specific Visual Recommendations for PBR Material Reconstruction and Interior Synthesis:
- **PBR Material Reconstruction:**
  - **Asphalt:** Use a high-resolution asphalt texture with detailed cracks and wear patterns. Apply appropriate roughness and metallic values to simulate the real-world appearance.
  - **Concrete:** Introduce a concrete texture with visible seams, stains, and weathering effects. Adjust the roughness to give it a slightly gritty look.
  - **Pl

---

## Map: Highland Valley: Foothill Settlement (`map2.glb`)

- **Scale / Extents:** 1.0m x 0.3m x 0.8m
- **Triangles:** 285,291 | **Vertices:** 270,711
- **Baseline Quality Score:** **3.38 / 10.0**

### Baseline Quality Breakdown

| Dimension | Score (1-10) | Evaluation |
| :--- | :---: | :--- |
| Geometry | 2.5 | Rough scan topology, noise index 0.9622 |
| Texture | 4.0 | Low-res baked diffuse scan texture |
| Materials | 3.0 | Flat scan diffuse without tangent PBR normals or roughness |
| Vegetation | 3.2 | Solid photogrammetry blobs, no foliage hierarchy |
| Architecture | 4.2 | Hollow facades without accessible interior structures |

### Identified Defect Matrix

- **[HIGH] BAKED_LIGHTING**: Sun shadows are permanently burned into diffuse textures, causing lighting conflicts under dynamic time-of-day.
- **[CRITICAL] MISSING_INTERIORS**: All buildings are closed hollow scan shells with no walkable floors, stairs, doors, or room layout.
- **[HIGH] BLOBBY_VEGETATION**: Trees and bushes are solid photogrammetry noise meshes without individual leaves or wind animation.
- **[CRITICAL] NON_PBR_MATERIALS**: Missing 2K tangent normal maps and physical roughness variation; surfaces reflect light uniformly.
- **[MEDIUM] SCAN_TOPOLOGY_NOISE**: Wavy scan distortion along architectural edges; 0 boundary holes detected.

### AI VLM Advisory Analysis

#### View: `overview`

### Technical Defect Assessment

#### 1. Major Structural Elements:
- **Buildings:** Several structures are visible, including houses with distinct roofs and walls. The buildings appear to be residential in nature.
- **Roads/Paths:** There are visible pathways connecting the buildings, but no major roads are present.
- **Terrain:** The terrain is uneven, with varying elevations and slopes. A significant portion appears to be grassy land.
- **Vegetation Blobs:** Trees and shrubs are scattered throughout the area, represented as green blobs.

#### 2. Visible Scan Artifacts, Geometry Noise, and Texture Stretching:
- **Scan Artifacts:** There are floating fragments near the left side of the image, likely due to incomplete data capture or processing errors.
- **Geometry Noise:** The edges of the terrain and building structures exhibit some roughness and irregularities, indicating potential noise in the geometry.
- **Texture Stretching:** The textures on the ground and some building surfaces appear stretched or distorted, particularly noticeable on the sloped areas and the sides of the buildings.

#### 3. Missing Architectural Features:
- **Floors:** The floors of the buildings are not clearly defined; they seem to blend into the ground level without distinct separation.
- **Doors:** No visible doorways are present on the buildings, which may be due to the angle of the scan or missing data.
- **Window Depth:** Windows lack depth and detail, appearing as flat surfaces rather than three-dimensional openings.

### Summary:
The raw 3D photogrammetry scan captures the essential structural elements of the environment but suffers from several defects. Floating fragments and geometry noise indicate issues with data completeness and processing. Texture stretching affects the visual quality, while missing architectural details like floors, doors, and window depth suggest limitations in the scan's resolution and angle coverage. Further refinement and post-processing will be necessary to address these issues.

#### View: `street_level`

### Analysis of the Street-Level View of a 3D Game Environment Scan

#### 1. Surface Materials Present:
- **Foliage:** The scene contains various types of greenery, including grassy areas and trees. The grass appears to be uniformly colored, suggesting a lack of detailed texturing.
- **Concrete/Stone:** The structures in the image seem to be made of stone or concrete, as indicated by their grayish color and rough texture. The pathways also appear to be made of similar materials.
- **Plaster/Mud:** Some of the buildings have walls that look like they might be made of plaster or mud, giving them a more rustic appearance.
- **Asphalt:** There is no clear indication of asphalt surfaces in this image.

#### 2. Why This Looks Like an Unpolished Raw Scan Rather Than a AAA Game:
- **Texture Quality:** The textures used in the scene are quite basic and lack detail. In a AAA game, you would expect high-resolution textures with detailed normal maps and other advanced texturing techniques.
- **Lighting and Shading:** The lighting in the scene is flat and lacks depth. AAA games typically use sophisticated lighting models to create realistic shadows, reflections, and ambient occlusion.
- **Model Detail:** The models of the buildings and objects are relatively simple and lack fine details. High-end games often feature highly detailed models with intricate designs.
- **Environment Design:** The overall design of the environment seems rudimentary. AAA games usually have carefully crafted environments with attention to environmental storytelling and immersion.

#### 3. Specific Visual Recommendations for PBR Material Reconstruction and Interior Synthesis:
- **PBR Material Reconstruction:**
  - **Foliage:** Use physically-based rendering (PBR) shaders to create more realistic grass and trees. Incorporate detailed albedo, normal, and roughness maps to enhance the texture. Consider using a procedural approach for the grass to add variety and realism.
  - **Concrete/Stone:**

---

## Map: Oakridge Academy: Educational Grounds (`schoolmap.glb`)

- **Scale / Extents:** 1.0m x 0.2m x 0.7m
- **Triangles:** 292,109 | **Vertices:** 219,706
- **Baseline Quality Score:** **3.38 / 10.0**

### Baseline Quality Breakdown

| Dimension | Score (1-10) | Evaluation |
| :--- | :---: | :--- |
| Geometry | 2.5 | Rough scan topology, noise index 0.9104 |
| Texture | 4.0 | Low-res baked diffuse scan texture |
| Materials | 3.0 | Flat scan diffuse without tangent PBR normals or roughness |
| Vegetation | 3.2 | Solid photogrammetry blobs, no foliage hierarchy |
| Architecture | 4.2 | Hollow facades without accessible interior structures |

### Identified Defect Matrix

- **[HIGH] BAKED_LIGHTING**: Sun shadows are permanently burned into diffuse textures, causing lighting conflicts under dynamic time-of-day.
- **[CRITICAL] MISSING_INTERIORS**: All buildings are closed hollow scan shells with no walkable floors, stairs, doors, or room layout.
- **[HIGH] BLOBBY_VEGETATION**: Trees and bushes are solid photogrammetry noise meshes without individual leaves or wind animation.
- **[CRITICAL] NON_PBR_MATERIALS**: Missing 2K tangent normal maps and physical roughness variation; surfaces reflect light uniformly.
- **[MEDIUM] SCAN_TOPOLOGY_NOISE**: Wavy scan distortion along architectural edges; 0 boundary holes detected.

### AI VLM Advisory Analysis

#### View: `overview`

### Technical Defect Assessment

#### 1. Major Structural Elements:
- **Buildings:** The primary structure is a multi-winged building with distinct sections, including a central wing flanked by two side wings. The roof appears to be sloped with visible ridges.
- **Roads/Terrain:** There is no clear indication of roads; however, the terrain includes a flat ground plane surrounding the building.
- **Vegetation Blobs:** Sparse green areas suggest patches of grass or low vegetation around the building.

#### 2. Visible Scan Artifacts, Geometry Noise, and Texture Stretching:
- **Scan Artifacts:** The edges of the building and the terrain exhibit jagged and uneven surfaces, indicating potential scan inaccuracies or insufficient data points.
- **Geometry Noise:** The roof and walls show irregularities and bumps that do not align with typical architectural features, suggesting noise in the geometry.
- **Texture Stretching:** The textures on the building's facade appear stretched and inconsistent, particularly noticeable on the windows and doors, which lack sharp definition.

#### 3. Missing Architectural Features:
- **Floors:** The interior floors are not visible, likely due to the absence of scans from inside the building.
- **Doors:** Specific door details are missing or poorly defined, making it difficult to discern their exact locations and sizes.
- **Window Depth:** The windows lack depth, appearing as flat planes rather than recessed openings, which affects the realism of the model.

### Summary:
The raw 3D photogrammetry scan captures the basic structure of the building but suffers from significant defects. The geometry exhibits noise and artifacts, while textures are stretched and inconsistent. Key architectural features such as floors, detailed doors, and window depth are absent or poorly represented. Further processing, including noise reduction, texture refinement, and manual detailing, will be necessary to enhance the quality and accuracy of the model.

#### View: `street_level`

### 1. Surface Materials Present

- **Asphalt**: The dark gray, textured surface in the foreground appears to be asphalt, likely representing a road or driveway.
- **Concrete**: The lighter gray areas around the building's foundation and possibly the sidewalk seem to be made of concrete.
- **Plaster**: The walls of the building have a smooth texture that suggests they are covered with plaster. Some areas show signs of wear and discoloration, indicating weathering or damage.
- **Foliage**: There are patches of green grass and some plants near the building, indicating the presence of foliage.

### 2. Why This Looks Like an Unpolished Raw Scan Rather Than a AAA Game

- **Texture Quality**: The textures appear low-resolution and lack detail, which is typical of raw scans. AAA games usually have high-resolution textures with detailed normal maps and other enhancements.
- **Lighting and Shading**: The lighting is flat and lacks the dynamic range and realism seen in AAA games. Shadows and highlights are not well-defined, and there is no evidence of advanced lighting techniques like global illumination or real-time shadows.
- **Material Properties**: The materials lack the complexity and variation found in physically-based rendering (PBR) materials used in AAA games. For example, the walls do not show realistic reflections, roughness variations, or other properties that would make them look more lifelike.
- **Modeling and Geometry**: The geometry of the scene, especially the edges and corners, appears rough and not finely tuned. AAA games typically have more refined and optimized geometry.

### 3. Specific Visual Recommendations for PBR Material Reconstruction and Interior Synthesis

#### PBR Material Reconstruction:
- **Wall Materials**:
  - Use high-resolution PBR textures for the plaster walls. Incorporate roughness maps to simulate the wear and tear visible on the walls.
  - Add subtle noise to the albedo map to create a more realistic appearance of the plaster.
  - Include a

---


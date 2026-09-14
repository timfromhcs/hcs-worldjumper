# Dynamic Environment & Weather System

## Time of Day Engine
The engine models a continuous 24-hour sun cycle:
* Solar elevation: Calculated trigonometrically based on time of day.
* Color temperature: Shifts dynamically from warm sunrise (3200K) to crisp midday (6500K), golden sunset (2800K), and moonlight (10000K).
* Soft Shadows: PCF filtered shadow projections shifting in direction and length with the sun.

## Weather States
1. **Clear**: Bright sun, sharp shadows, deep blue skies.
2. **Golden Hour**: Long shadows, orange atmospheric scattering.
3. **Overcast**: Soft diffuse lighting, reduced contrast, grey skies.
4. **Rain**: 3,000 falling particle streaks cycling around the player, darkening sky, rain audio.
5. **Storm**: Dark tempest skies, rain particles, thunder claps, and random directional lightning flashes.
6. **Fog**: Exponential squared fog density obscuring distant objects.
7. **Night**: Low-light moonlight, warm emissive interior lamps and street lighting.

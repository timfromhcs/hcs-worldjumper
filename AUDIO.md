# Environmental Audio Engine

## Architecture
Built using the HTML5 Web Audio API, HCS WorldJumper features a multi-channel sound mixer:
* `master`: Global volume control.
* `ambience`: Wind loops and indoor acoustic reverberation.
* `weather`: Rain showers, howling wind gusts, and randomized rolling thunder.
* `footsteps`: Real surface-reactive footsteps:
  * `concrete`: Crisp high-frequency tap.
  * `wood`: Resonant acoustic hollow step.
  * `grass`: Soft rustling footsteps.
* `ui`: Crisp clicks and map transition whooshes.

## Audio Assets
All audio files are real 16-bit 44.1kHz PCM WAV assets stored under `assets/audio/`:
* `ambience_outdoor.wav`
* `ambience_indoor.wav`
* `weather_rain.wav`
* `weather_wind.wav`
* `weather_thunder.wav`
* `footstep_concrete.wav`
* `footstep_wood.wav`
* `footstep_grass.wav`
* `ui_click.wav`
* `ui_transition.wav`

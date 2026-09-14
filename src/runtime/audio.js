// HCS WorldJumper Audio Engine
// Real Web Audio API mixer with spatial audio, surface footsteps, and dynamic weather ambience.

export class AudioManager {
  constructor() {
    this.ctx = null;
    this.initialized = false;
    this.buffers = new Map();
    this.sources = new Map();
    this.gains = {};
    
    this.settings = {
      master: 0.8,
      ambience: 0.7,
      weather: 0.6,
      footsteps: 0.5,
      sfx: 0.7,
      ui: 0.6
    };

    this.audioFiles = {
      ambience_outdoor: './assets/audio/ambience_outdoor.wav',
      ambience_indoor: './assets/audio/ambience_indoor.wav',
      weather_rain: './assets/audio/weather_rain.wav',
      weather_wind: './assets/audio/weather_wind.wav',
      weather_thunder: './assets/audio/weather_thunder.wav',
      footstep_concrete: './assets/audio/footstep_concrete.wav',
      footstep_wood: './assets/audio/footstep_wood.wav',
      footstep_grass: './assets/audio/footstep_grass.wav',
      ui_click: './assets/audio/ui_click.wav',
      ui_transition: './assets/audio/ui_transition.wav'
    };

    this.lastFootstepTime = 0;
  }

  async init() {
    if (this.initialized) return;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    this.ctx = new AudioContext();

    // Create gain hierarchy
    this.gains.master = this.ctx.createGain();
    this.gains.master.gain.value = this.settings.master;
    this.gains.master.connect(this.ctx.destination);

    ['ambience', 'weather', 'footsteps', 'sfx', 'ui'].forEach(ch => {
      this.gains[ch] = this.ctx.createGain();
      this.gains[ch].gain.value = this.settings[ch];
      this.gains[ch].connect(this.gains.master);
    });

    // Preload audio buffers
    for (const [key, url] of Object.entries(this.audioFiles)) {
      try {
        const res = await fetch(url);
        if (res.ok) {
          const ab = await res.arrayBuffer();
          const audioBuffer = await this.ctx.decodeAudioData(ab);
          this.buffers.set(key, audioBuffer);
        }
      } catch (err) {
        console.warn(`Could not load audio asset: ${url}`, err);
      }
    }

    this.initialized = true;
    console.log(`Audio Engine Initialized (${this.buffers.size} assets loaded)`);
  }

  resume() {
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  setVolume(channel, val) {
    if (this.settings[channel] !== undefined) {
      this.settings[channel] = Math.max(0, Math.min(1, val));
      if (this.gains[channel]) {
        this.gains[channel].gain.setTargetAtTime(this.settings[channel], this.ctx.currentTime, 0.05);
      }
    }
  }

  playLoop(key, channel = 'ambience') {
    if (!this.initialized || !this.buffers.has(key)) return;
    this.stop(key);

    const source = this.ctx.createBufferSource();
    source.buffer = this.buffers.get(key);
    source.loop = true;
    source.connect(this.gains[channel] || this.gains.master);
    source.start(0);
    this.sources.set(key, source);
  }

  stop(key) {
    if (this.sources.has(key)) {
      try {
        this.sources.get(key).stop();
      } catch (e) {}
      this.sources.delete(key);
    }
  }

  playOneShot(key, channel = 'sfx', pitchVar = 0.05) {
    if (!this.initialized || !this.buffers.has(key)) return;
    const source = this.ctx.createBufferSource();
    source.buffer = this.buffers.get(key);
    if (pitchVar > 0) {
      source.playbackRate.value = 1.0 + (Math.random() * 2 - 1) * pitchVar;
    }
    source.connect(this.gains[channel] || this.gains.master);
    source.start(0);
  }

  playFootstep(surface = 'concrete') {
    const now = performance.now();
    if (now - this.lastFootstepTime < 340) return; // Minimum stride interval
    this.lastFootstepTime = now;

    let key = 'footstep_concrete';
    if (surface === 'wood') key = 'footstep_wood';
    else if (surface === 'grass') key = 'footstep_grass';

    this.playOneShot(key, 'footsteps', 0.08);
  }

  playUIClick() {
    this.playOneShot('ui_click', 'ui', 0.02);
  }

  playUITransition() {
    this.playOneShot('ui_transition', 'ui', 0.0);
  }

  setWeatherState(weather) {
    if (!this.initialized) return;
    if (weather === 'rain' || weather === 'storm') {
      this.playLoop('weather_rain', 'weather');
      this.playLoop('weather_wind', 'weather');
      if (weather === 'storm') {
        // Random thunder strikes
        if (Math.random() < 0.25) {
          this.playOneShot('weather_thunder', 'weather');
        }
      }
    } else {
      this.stop('weather_rain');
      this.playLoop('ambience_outdoor', 'ambience');
      if (weather === 'windy') {
        this.playLoop('weather_wind', 'weather');
      } else {
        this.stop('weather_wind');
      }
    }
  }

  setIndoorState(isIndoor) {
    if (!this.initialized) return;
    if (isIndoor) {
      this.playLoop('ambience_indoor', 'ambience');
      this.stop('ambience_outdoor');
    } else {
      this.playLoop('ambience_outdoor', 'ambience');
      this.stop('ambience_indoor');
    }
  }
}

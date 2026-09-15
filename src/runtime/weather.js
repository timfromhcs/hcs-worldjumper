// HCS WorldJumper Environment & Weather Engine
// Manages dynamic sun position, atmospheric scattering, lighting transitions,
// rain particles, lightning flash effects, and vegetation wind animation.

import * as THREE from 'three';

export class WeatherSystem {
  constructor(scene, audioManager) {
    this.scene = scene;
    this.audio = audioManager;

    this.timeOfDay = 14.0; // 0.0 - 24.0 hours
    this.timeScale = 0.05; // Progression speed
    this.currentWeather = 'clear'; // 'clear', 'golden', 'overcast', 'rain', 'storm', 'fog', 'night'
    this.windSpeed = 2.5;
    this.windIntensity = 0.08;

    // Lights
    this.sunLight = null;
    this.hemiLight = null;
    this.ambientLight = null;

    // Particle system
    this.rainParticles = null;
    this.rainCount = 3000;
    this.rainGeometry = null;

    // Lightning
    this.lightningFlash = 0;

    this.initLights();
    this.initRain();
  }

  initLights() {
    this.hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.9);
    this.hemiLight.position.set(0, 300, 0);
    this.scene.add(this.hemiLight);

    this.sunLight = new THREE.DirectionalLight(0xfffaed, 2.8);
    this.sunLight.position.set(120, 180, 100);
    this.sunLight.castShadow = true;
    this.sunLight.shadow.mapSize.width = 2048;
    this.sunLight.shadow.mapSize.height = 2048;
    this.sunLight.shadow.camera.near = 10;
    this.sunLight.shadow.camera.far = 450;
    const d = 120;
    this.sunLight.shadow.camera.left = -d;
    this.sunLight.shadow.camera.right = d;
    this.sunLight.shadow.camera.top = d;
    this.sunLight.shadow.camera.bottom = -d;
    this.sunLight.shadow.bias = -0.0004;
    this.scene.add(this.sunLight);

    this.ambientLight = new THREE.AmbientLight(0x222233, 0.4);
    this.scene.add(this.ambientLight);
  }

  initRain() {
    const rainGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(this.rainCount * 3);
    for (let i = 0; i < this.rainCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 120;
      positions[i * 3 + 1] = Math.random() * 40;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 120;
    }
    rainGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const rainMat = new THREE.PointsMaterial({
      color: 0x99bbdd,
      size: 0.15,
      transparent: true,
      opacity: 0.65
    });

    this.rainParticles = new THREE.Points(rainGeo, rainMat);
    this.rainParticles.visible = false;
    this.scene.add(this.rainParticles);
  }

  setWeather(weather) {
    this.currentWeather = weather;
    if (this.audio) {
      this.audio.setWeatherState(weather);
    }

    if (weather === 'rain' || weather === 'storm') {
      this.rainParticles.visible = true;
      this.windIntensity = (weather === 'storm') ? 0.18 : 0.12;
      this.windSpeed = (weather === 'storm') ? 4.5 : 3.0;
    } else {
      this.rainParticles.visible = false;
      this.windIntensity = (weather === 'fog') ? 0.03 : 0.08;
      this.windSpeed = 2.5;
    }

    this.applyAtmosphere();
  }

  setTimeOfDay(hour) {
    this.timeOfDay = Math.max(0, Math.min(24, hour));
    this.applyAtmosphere();
  }

  applyAtmosphere() {
    const w = this.currentWeather;
    const t = this.timeOfDay;

    let skyColor = 0x87ceeb;
    let fogDensity = 0.0025;
    let sunColor = 0xfffaed;
    let sunIntensity = 2.5;
    let hemiIntensity = 0.9;
    let ambientIntensity = 0.35;

    // Time of day sun elevation
    const sunAngle = ((t - 6) / 12) * Math.PI; // 6h=0, 12h=PI/2, 18h=PI
    const sunY = Math.sin(sunAngle) * 200;
    const sunX = Math.cos(sunAngle) * 200;
    this.sunLight.position.set(sunX, Math.max(10, sunY), 100);

    const isNight = (t < 5.5 || t > 19.5);
    const isSunset = (t >= 17.5 && t <= 19.5) || (t >= 5.5 && t <= 7.0);

    if (w === 'storm') {
      skyColor = 0x181c24;
      fogDensity = 0.012;
      sunColor = 0x556677;
      sunIntensity = 0.6;
      ambientIntensity = 0.2;
    } else if (w === 'rain') {
      skyColor = 0x5c6d7e;
      fogDensity = 0.008;
      sunColor = 0xb0c4de;
      sunIntensity = 1.2;
      ambientIntensity = 0.4;
    } else if (w === 'fog') {
      skyColor = 0xc5cbd3;
      fogDensity = 0.022;
      sunColor = 0xeaeaea;
      sunIntensity = 1.0;
      ambientIntensity = 0.6;
    } else if (isNight || w === 'night') {
      skyColor = 0x050813;
      fogDensity = 0.005;
      sunColor = 0x335588;
      sunIntensity = 0.35;
      hemiIntensity = 0.2;
      ambientIntensity = 0.12;
    } else if (isSunset || w === 'golden') {
      skyColor = 0xf97316;
      fogDensity = 0.004;
      sunColor = 0xff8833;
      sunIntensity = 3.2;
      hemiIntensity = 0.7;
      ambientIntensity = 0.45;
    }

    // Apply flash if storm lightning
    if (this.lightningFlash > 0) {
      sunIntensity += this.lightningFlash * 8.0;
      sunColor = 0xddeeff;
      this.lightningFlash = Math.max(0, this.lightningFlash - 0.1);
    }

    this.scene.background = new THREE.Color(skyColor);
    if (!this.scene.fog) {
      this.scene.fog = new THREE.FogExp2(skyColor, fogDensity);
    } else {
      this.scene.fog.color.setHex(skyColor);
      this.scene.fog.density = fogDensity;
    }

    this.sunLight.color.setHex(sunColor);
    this.sunLight.intensity = sunIntensity;
    this.hemiLight.intensity = hemiIntensity;
    this.ambientLight.intensity = ambientIntensity;
  }

  update(delta, playerPos, worldModel) {
    // Time progression
    this.timeOfDay = (this.timeOfDay + delta * this.timeScale) % 24.0;
    
    // Random lightning in storm
    if (this.currentWeather === 'storm' && Math.random() < 0.008) {
      this.lightningFlash = 1.0;
      if (this.audio) {
        setTimeout(() => this.audio.playOneShot('weather_thunder', 'weather'), 300);
      }
    }

    this.applyAtmosphere();

    // Update rain particles around player
    if (this.rainParticles && this.rainParticles.visible && playerPos) {
      const posAttr = this.rainParticles.geometry.attributes.position;
      const arr = posAttr.array;
      for (let i = 0; i < this.rainCount; i++) {
        arr[i * 3 + 1] -= delta * 35.0; // Fall speed
        if (arr[i * 3 + 1] < playerPos.y - 5.0) {
          arr[i * 3 + 1] = playerPos.y + 35.0;
          arr[i * 3] = playerPos.x + (Math.random() - 0.5) * 80;
          arr[i * 3 + 2] = playerPos.z + (Math.random() - 0.5) * 80;
        }
      }
      posAttr.needsUpdate = true;
    }

    // Update procedural vegetation wind swaying (subtle, restrained movement)
    if (worldModel) {
      const t = performance.now() * 0.001;
      worldModel.traverse((child) => {
        if (child.isMesh && (child.name.includes('tree') || child.name.includes('bush') || child.name.includes('leaf') || child.name.includes('grass'))) {
          // Bounding sphere check: compound forest meshes must never be rotated as a single object around (0,0,0)
          if (!child.geometry.boundingSphere) {
            child.geometry.computeBoundingSphere();
          }
          if (child.geometry.boundingSphere && child.geometry.boundingSphere.radius > 6.0) {
            // Compound multi-tree mesh: keep fixed in place to prevent flying trees
            return;
          }
          // Very subtle wind sway for individual localized elements (max ~0.8 degrees)
          const subtleIntensity = Math.min(0.015, this.windIntensity * 0.12);
          const sway = Math.sin(t * this.windSpeed + child.position.x * 0.4) * subtleIntensity;
          child.rotation.z = (child.userData.baseRotZ || 0) + sway;
          child.rotation.x = (child.userData.baseRotX || 0) + Math.cos(t * this.windSpeed * 0.8 + child.position.z * 0.4) * (sway * 0.4);
        }
      });
    }
  }
}

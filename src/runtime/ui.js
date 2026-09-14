// HCS WorldJumper UI & State System
// Implements Main Menu, World Selector, Settings Modal, Loading Screen, In-Game HUD, and F3 Debug Overlay.

export class UIManager {
  constructor(gameApp) {
    this.app = gameApp;
    this.manifest = null;
    this.selectedMapId = 'map';
    this.debugVisible = false;
    this.settings = {
      preset: 'HIGH',
      renderScale: 1.0,
      shadowQuality: 'high',
      viewDistance: 800,
      mouseSensitivity: 0.0022,
      invertY: false,
      fov: 70
    };
  }

  async init() {
    // Fetch maps manifest
    try {
      const res = await fetch('/maps/manifest.json');
      if (res.ok) {
        this.manifest = await res.json();
      }
    } catch (e) {
      console.warn("Could not load maps manifest:", e);
    }
    
    this.renderUI();
    this.setupKeybindings();
  }

  setupKeybindings() {
    window.addEventListener('keydown', (e) => {
      if (e.code === 'F3') {
        e.preventDefault();
        this.toggleDebug();
      }
      if (e.code === 'Escape') {
        this.togglePause();
      }
    });
  }

  renderUI() {
    const root = document.createElement('div');
    root.id = 'ui-root';
    root.innerHTML = `
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap');
        
        #ui-root {
          position: absolute; top: 0; left: 0; width: 100vw; height: 100vh;
          pointer-events: none; font-family: 'Outfit', sans-serif; color: #f8fafc;
          overflow: hidden; user-select: none; z-index: 100;
        }
        
        /* Interactive containers */
        .interactive { pointer-events: auto; }
        
        /* Modals & Screens */
        .screen-overlay {
          position: absolute; top: 0; left: 0; width: 100vw; height: 100vh;
          background: radial-gradient(circle at center, rgba(15, 23, 42, 0.85) 0%, rgba(3, 7, 18, 0.96) 100%);
          backdrop-filter: blur(16px);
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          transition: opacity 0.3s ease, visibility 0.3s ease;
        }
        .hidden { opacity: 0; visibility: hidden; pointer-events: none !important; }

        /* Typography & Brand */
        .brand-title {
          font-size: 56px; font-weight: 900; letter-spacing: 2px;
          background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;
          text-transform: uppercase; margin: 0 0 8px 0;
          text-shadow: 0 10px 30px rgba(56, 189, 248, 0.3);
        }
        .brand-tagline {
          font-size: 16px; font-weight: 400; color: #94a3b8;
          letter-spacing: 4px; text-transform: uppercase; margin-bottom: 40px;
        }

        /* Buttons */
        .btn-menu {
          background: rgba(30, 41, 59, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.12);
          color: #f1f5f9; padding: 14px 36px; margin: 8px 0;
          font-size: 16px; font-weight: 600; letter-spacing: 1.5px;
          border-radius: 8px; cursor: pointer; min-width: 280px;
          text-transform: uppercase; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }
        .btn-menu:hover {
          background: linear-gradient(135deg, #0284c7, #4f46e5);
          border-color: #38bdf8; color: #ffffff;
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(56, 189, 248, 0.4);
        }
        .btn-menu.primary {
          background: linear-gradient(135deg, #0284c7 0%, #4338ca 100%);
          border-color: #38bdf8;
        }

        /* World Selector Grid */
        .cards-container {
          display: flex; gap: 24px; max-width: 1200px; padding: 20px;
          flex-wrap: wrap; justify-content: center;
        }
        .map-card {
          width: 340px; background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px; overflow: hidden; cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          display: flex; flex-direction: column;
        }
        .map-card:hover {
          border-color: #38bdf8; transform: translateY(-6px);
          box-shadow: 0 12px 32px rgba(56, 189, 248, 0.25);
        }
        .map-card.active {
          border-color: #38bdf8; box-shadow: 0 0 0 2px #38bdf8, 0 12px 32px rgba(56, 189, 248, 0.3);
        }
        .card-thumb {
          width: 100%; height: 180px; object-fit: cover; background: #0f172a;
        }
        .card-body { padding: 18px; flex-grow: 1; display: flex; flex-direction: column; }
        .card-title { font-size: 18px; font-weight: 700; margin: 0 0 6px 0; color: #e2e8f0; }
        .card-type { font-size: 12px; color: #38bdf8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; font-weight: 600; }
        .card-desc { font-size: 13px; color: #94a3b8; line-height: 1.5; margin-bottom: 14px; flex-grow: 1; }
        .card-stats {
          display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
          background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px;
          font-family: 'JetBrains Mono', monospace; font-size: 11px;
        }

        /* Loading Screen */
        #loading-screen { z-index: 150; }
        .progress-box { width: 440px; margin-top: 30px; text-align: center; }
        .progress-bar-bg {
          width: 100%; height: 8px; background: rgba(255, 255, 255, 0.1);
          border-radius: 4px; overflow: hidden; margin-bottom: 12px;
        }
        .progress-bar-fill {
          width: 0%; height: 100%;
          background: linear-gradient(90deg, #38bdf8, #818cf8);
          transition: width 0.2s ease;
        }
        .progress-stage { font-size: 13px; color: #94a3b8; letter-spacing: 1px; }

        /* In-Game HUD */
        #hud-game {
          position: absolute; top: 0; left: 0; width: 100vw; height: 100vh;
        }
        .compass {
          position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
          background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(8px);
          padding: 6px 18px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
          font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600;
          color: #38bdf8; letter-spacing: 2px;
        }
        .crosshair {
          position: absolute; top: 50%; left: 50%; width: 6px; height: 6px;
          transform: translate(-50%, -50%); background: rgba(255, 255, 255, 0.7);
          border-radius: 50%; box-shadow: 0 0 6px rgba(0,0,0,0.8);
        }
        .status-badge {
          position: absolute; bottom: 24px; left: 24px;
          background: rgba(15, 23, 42, 0.65); backdrop-filter: blur(8px);
          padding: 10px 16px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);
          font-size: 12px; line-height: 1.5; color: #cbd5e1;
        }

        /* F3 Debug Overlay */
        #debug-overlay {
          position: absolute; top: 20px; left: 24px;
          background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(10px);
          padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.3);
          font-family: 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.6;
          color: #e2e8f0; z-index: 200; min-width: 280px; box-shadow: 0 8px 30px rgba(0,0,0,0.5);
        }
        .debug-title { color: #38bdf8; font-weight: 600; margin-bottom: 6px; text-transform: uppercase; }
        
        /* Settings Modal */
        .modal-card {
          width: 540px; background: rgba(15, 23, 42, 0.95);
          border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 12px;
          padding: 28px; box-shadow: 0 20px 50px rgba(0,0,0,0.8);
        }
        .modal-title { font-size: 22px; font-weight: 700; margin: 0 0 20px 0; color: #38bdf8; }
        .setting-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; font-size: 14px; }
        .setting-label { color: #94a3b8; }
        select, input[type=range] {
          background: #1e293b; color: #f8fafc; border: 1px solid #334155;
          padding: 6px 12px; border-radius: 4px; font-size: 13px;
        }
      </style>

      <!-- 1. Main Menu Screen -->
      <div id="screen-main-menu" class="screen-overlay interactive">
        <h1 class="brand-title">HCS WorldJumper</h1>
        <div class="brand-tagline">Photorealistic Multi-World Exploration Engine</div>
        <button class="btn-menu primary" id="btn-play">Enter World</button>
        <button class="btn-menu" id="btn-world-select">World Selector</button>
        <button class="btn-menu" id="btn-settings">Settings</button>
        <button class="btn-menu" id="btn-about">About</button>
      </div>

      <!-- 2. World Selector Screen -->
      <div id="screen-world-selector" class="screen-overlay interactive hidden">
        <h2 style="font-size: 32px; font-weight: 800; margin-bottom: 24px; text-transform: uppercase; letter-spacing: 2px;">Select Explorable World</h2>
        <div class="cards-container" id="cards-wrapper">
          <!-- Dynamically populated from manifest.json -->
        </div>
        <div style="margin-top: 24px; display: flex; gap: 16px;">
          <button class="btn-menu primary" id="btn-confirm-world" style="min-width: 200px;">Load Selected</button>
          <button class="btn-menu" id="btn-back-main" style="min-width: 140px;">Back</button>
        </div>
      </div>

      <!-- 3. Settings Screen -->
      <div id="screen-settings" class="screen-overlay interactive hidden">
        <div class="modal-card">
          <h3 class="modal-title">System Settings</h3>
          <div class="setting-row">
            <span class="setting-label">Graphics Preset</span>
            <select id="opt-preset">
              <option value="LOW">Low (Optimized)</option>
              <option value="MEDIUM">Medium (Balanced)</option>
              <option value="HIGH" selected>High (Recommended)</option>
              <option value="ULTRA">Ultra (Max Fidelity)</option>
            </select>
          </div>
          <div class="setting-row">
            <span class="setting-label">Renderer Backend</span>
            <span id="opt-backend-label" style="font-family: monospace; color: #38bdf8;">WebGPU (Primary)</span>
          </div>
          <div class="setting-row">
            <span class="setting-label">FOV</span>
            <input type="range" id="opt-fov" min="60" max="100" value="75">
          </div>
          <div class="setting-row">
            <span class="setting-label">Master Volume</span>
            <input type="range" id="opt-vol-master" min="0" max="1" step="0.05" value="0.8">
          </div>
          <div class="setting-row">
            <span class="setting-label">Ambience & Weather</span>
            <input type="range" id="opt-vol-ambience" min="0" max="1" step="0.05" value="0.7">
          </div>
          <div class="setting-row">
            <span class="setting-label">Footsteps Volume</span>
            <input type="range" id="opt-vol-footsteps" min="0" max="1" step="0.05" value="0.5">
          </div>
          <div style="margin-top: 24px; text-align: right;">
            <button class="btn-menu primary" id="btn-close-settings" style="min-width: 120px; padding: 10px 24px;">Apply</button>
          </div>
        </div>
      </div>

      <!-- 4. Loading Screen -->
      <div id="loading-screen" class="screen-overlay hidden">
        <h2 style="font-size: 28px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;">Loading World</h2>
        <div id="loading-map-title" style="color: #38bdf8; font-size: 16px; margin-top: 4px;">District Alpha</div>
        <div class="progress-box">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" id="progress-fill"></div>
          </div>
          <div class="progress-stage" id="progress-stage">Initializing assets...</div>
        </div>
      </div>

      <!-- 5. In-Game HUD -->
      <div id="hud-game" class="hidden">
        <div class="compass" id="hud-compass">HDG: 000° N</div>
        <div class="crosshair"></div>
        <div class="status-badge" id="hud-status-badge">
          <strong id="badge-map-name">District Alpha</strong><br>
          <span id="badge-weather">Clear Day · 14:30</span><br>
          <span style="font-size: 10px; color: #94a3b8;">ESC for Menu · F3 for Debug</span>
        </div>
      </div>

      <!-- 6. F3 Debug Overlay -->
      <div id="debug-overlay" class="hidden">
        <div class="debug-title">HCS Engine Profiler</div>
        <div>Backend: <span id="dbg-backend" style="color: #38bdf8;">Detecting</span></div>
        <div>FPS: <span id="dbg-fps">60</span> (<span id="dbg-frametime">16.6</span> ms)</div>
        <div>Triangles: <span id="dbg-tris">0</span></div>
        <div>Draw Calls: <span id="dbg-draws">0</span></div>
        <div>Coords: <span id="dbg-coords">0.0, 0.0, 0.0</span></div>
        <div>Surface: <span id="dbg-surface">Concrete</span></div>
        <div>Weather: <span id="dbg-weather">Clear</span></div>
        <div>Colliders: <span id="dbg-colliders">0 Active</span></div>
      </div>
    `;

    document.body.appendChild(root);
    this.setupButtonActions();
    this.populateCards();
  }

  setupButtonActions() {
    const playBtn = document.getElementById('btn-play');
    const worldSelectBtn = document.getElementById('btn-world-select');
    const settingsBtn = document.getElementById('btn-settings');
    const aboutBtn = document.getElementById('btn-about');
    const confirmWorldBtn = document.getElementById('btn-confirm-world');
    const backMainBtn = document.getElementById('btn-back-main');
    const closeSettingsBtn = document.getElementById('btn-close-settings');

    playBtn.onclick = () => {
      this.app.audio.playUIClick();
      this.enterWorld(this.selectedMapId);
    };

    worldSelectBtn.onclick = () => {
      this.app.audio.playUIClick();
      document.getElementById('screen-main-menu').classList.add('hidden');
      document.getElementById('screen-world-selector').classList.remove('hidden');
    };

    backMainBtn.onclick = () => {
      this.app.audio.playUIClick();
      document.getElementById('screen-world-selector').classList.add('hidden');
      document.getElementById('screen-main-menu').classList.remove('hidden');
    };

    settingsBtn.onclick = () => {
      this.app.audio.playUIClick();
      document.getElementById('screen-settings').classList.remove('hidden');
    };

    closeSettingsBtn.onclick = () => {
      this.app.audio.playUIClick();
      document.getElementById('screen-settings').classList.add('hidden');
    };

    confirmWorldBtn.onclick = () => {
      this.app.audio.playUIClick();
      document.getElementById('screen-world-selector').classList.add('hidden');
      this.enterWorld(this.selectedMapId);
    };

    aboutBtn.onclick = () => {
      this.app.audio.playUIClick();
      alert("HCS WorldJumper v1.0.0\n\nPhotorealistic Multi-World First-Person Exploration Engine\nBuilt with Three.js WebGPU / WebGL2, Procedural PBR, AI Architectural Reconstruction, and Spatial Audio.");
    };
  }

  populateCards() {
    const wrapper = document.getElementById('cards-wrapper');
    if (!wrapper || !this.manifest || !this.manifest.maps) return;

    wrapper.innerHTML = '';
    this.manifest.maps.forEach((m) => {
      const card = document.createElement('div');
      card.className = `map-card ${m.id === this.selectedMapId ? 'active' : ''}`;
      card.dataset.id = m.id;
      card.innerHTML = `
        <img class="card-thumb" src="/${m.thumbnail}" alt="${m.display_name}">
        <div class="card-body">
          <div class="card-title">${m.display_name}</div>
          <div class="card-type">${m.environment_type}</div>
          <div class="card-desc">${m.description}</div>
          <div class="card-stats">
            <div>Triangles: <span>${(m.statistics.triangles/1000).toFixed(0)}k</span></div>
            <div>Buildings: <span>${m.statistics.buildings}</span></div>
            <div>Interiors: <span>${m.statistics.interior_elements}</span></div>
            <div>Size: <span>${m.statistics.file_size_mb} MB</span></div>
          </div>
        </div>
      `;

      card.onclick = () => {
        this.app.audio.playUIClick();
        document.querySelectorAll('.map-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        this.selectedMapId = m.id;
      };

      wrapper.appendChild(card);
    });
  }

  enterWorld(mapId) {
    document.getElementById('screen-main-menu').classList.add('hidden');
    document.getElementById('screen-world-selector').classList.add('hidden');
    
    // Trigger loading screen
    const loadingScreen = document.getElementById('loading-screen');
    loadingScreen.classList.remove('hidden');

    const mapEntry = this.manifest ? this.manifest.maps.find(m => m.id === mapId) : null;
    document.getElementById('loading-map-title').innerText = mapEntry ? mapEntry.display_name : mapId;

    this.setLoadingProgress(15, "Preparing terrain and structures...");

    setTimeout(() => {
      this.setLoadingProgress(45, "Reconstructing multi-floor architectural interiors...");
      this.app.loadWorld(mapId, () => {
        this.setLoadingProgress(80, "Initializing environment and spatial audio...");
        setTimeout(() => {
          this.setLoadingProgress(100, "Starting first-person runtime...");
          setTimeout(() => {
            loadingScreen.classList.add('hidden');
            document.getElementById('hud-game').classList.remove('hidden');
            document.getElementById('badge-map-name').innerText = mapEntry ? mapEntry.display_name : mapId;
            this.app.startPOV();
          }, 400);
        }, 300);
      });
    }, 200);
  }

  setLoadingProgress(pct, stage) {
    const bar = document.getElementById('progress-fill');
    const label = document.getElementById('progress-stage');
    if (bar) bar.style.width = `${pct}%`;
    if (label) label.innerText = stage;
  }

  toggleDebug() {
    this.debugVisible = !this.debugVisible;
    const overlay = document.getElementById('debug-overlay');
    if (overlay) overlay.classList.toggle('hidden', !this.debugVisible);
  }

  togglePause() {
    const mainMenu = document.getElementById('screen-main-menu');
    const isPaused = !mainMenu.classList.contains('hidden');
    if (isPaused) {
      mainMenu.classList.add('hidden');
      document.getElementById('hud-game').classList.remove('hidden');
      this.app.startPOV();
    } else {
      document.exitPointerLock();
      mainMenu.classList.remove('hidden');
      document.getElementById('hud-game').classList.add('hidden');
    }
  }

  updateHUD(playerPos, yawDeg, timeStr, weatherName) {
    const compass = document.getElementById('hud-compass');
    if (compass) {
      let deg = Math.round((yawDeg % 360 + 360) % 360);
      let dir = 'N';
      if (deg >= 45 && deg < 135) dir = 'E';
      else if (deg >= 135 && deg < 225) dir = 'S';
      else if (deg >= 225 && deg < 315) dir = 'W';
      compass.innerText = `HDG: ${deg.toString().padStart(3, '0')}° ${dir}`;
    }

    const badgeWeather = document.getElementById('badge-weather');
    if (badgeWeather) {
      badgeWeather.innerText = `${weatherName} · ${timeStr}`;
    }
  }

  updateDebug(metrics) {
    if (!this.debugVisible) return;
    document.getElementById('dbg-backend').innerText = metrics.backend;
    document.getElementById('dbg-fps').innerText = metrics.fps;
    document.getElementById('dbg-frametime').innerText = metrics.frameTime;
    document.getElementById('dbg-tris').innerText = metrics.triangles.toLocaleString();
    document.getElementById('dbg-draws').innerText = metrics.drawCalls;
    document.getElementById('dbg-coords').innerText = `${metrics.pos.x.toFixed(1)}, ${metrics.pos.y.toFixed(1)}, ${metrics.pos.z.toFixed(1)}`;
    document.getElementById('dbg-surface').innerText = metrics.surface;
    document.getElementById('dbg-weather').innerText = metrics.weather;
    document.getElementById('dbg-colliders').innerText = `${metrics.colliderCount} Active`;
  }
}

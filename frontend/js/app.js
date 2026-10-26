/**
 * Main Application Entrypoint for AirChord
 */

import { settingsManager } from "./settings.js";
import { audioEngine } from "./audio-engine.js";
import { guitarSampler } from "./guitar-sampler.js";
import { wsClient } from "./websocket.js";
import { CameraController } from "./camera.js";
import { instrumentCoordinator } from "./instrument.js";
import { uiRenderer } from "./ui.js";

class AirChordApp {
  constructor() {
    this.videoEl = document.getElementById("webcam-video");
    this.cameraPlaceholder = document.getElementById("camera-placeholder");
    this.btnToggleCamera = document.getElementById("btn-toggle-camera");
    this.btnHeroStart = document.getElementById("btn-hero-start");
    this.btnCameraText = document.getElementById("btn-camera-text");
    this.btnRecalibrate = document.getElementById("btn-recalibrate");
    this.btnToggleDiag = document.getElementById("btn-toggle-diag");
    this.cameraSelect = document.getElementById("camera-select");
    this.volumeSlider = document.getElementById("master-volume-slider");

    this.camera = new CameraController(this.videoEl, {
      width: 480,
      height: 360,
      fps: 18,
      quality: 0.65
    });

    this.chordsList = [];
    this.isRunning = false;
  }

  async init() {
    console.log("Initializing AirChord v2.0...");
    this.bindNavigation();
    this.bindControls();
    this.bindWebSocket();
    await this.loadInitialData();
    this.syncSettingsUI();
  }

  async loadInitialData() {
    try {
      const resp = await fetch("/api/chords");
      if (resp.ok) {
        const data = await resp.json();
        this.chordsList = data.chords || [];
        this.populateChordSelects();
      }
    } catch (e) {
      console.warn("Could not load chord list from backend:", e);
    }
  }

  bindNavigation() {
    const navBtns = document.querySelectorAll(".nav-btn");
    navBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const targetTab = btn.getAttribute("data-tab");
        navBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        document.querySelectorAll(".view-section").forEach(view => {
          view.classList.remove("active");
        });
        const activeView = document.getElementById(`view-${targetTab}`);
        if (activeView) activeView.classList.add("active");
      });
    });
  }

  bindControls() {
    // Start / Stop buttons
    this.btnToggleCamera.addEventListener("click", () => this.togglePlaying());
    if (this.btnHeroStart) {
      this.btnHeroStart.addEventListener("click", () => this.togglePlaying());
    }

    // Diagnostics toggle
    this.btnToggleDiag.addEventListener("click", () => {
      const isEnabled = uiRenderer.toggleDiagnostics();
      this.btnToggleDiag.classList.toggle("btn-primary", isEnabled);
      this.btnToggleDiag.classList.toggle("btn-secondary", !isEnabled);
    });

    // Volume control
    if (this.volumeSlider) {
      const st = settingsManager.get();
      this.volumeSlider.value = st.master_volume;
      this.volumeSlider.addEventListener("input", (e) => {
        const vol = parseFloat(e.target.value);
        audioEngine.setVolume(vol);
        settingsManager.save({ master_volume: vol });
      });
    }

    // Recalibrate button
    if (this.btnRecalibrate) {
      this.btnRecalibrate.addEventListener("click", () => {
        wsClient.sendJson("calibration.start");
        uiRenderer.setStatus("warning", "Calibrating...");
        setTimeout(() => {
          uiRenderer.setStatus("active", "Tracking");
        }, 800);
      });
    }

    // Modal close
    const btnModalClose = document.getElementById("btn-modal-close");
    if (btnModalClose) {
      btnModalClose.addEventListener("click", () => uiRenderer.closeModal());
    }

    // Settings save & reset
    const btnSaveSettings = document.getElementById("btn-save-settings");
    if (btnSaveSettings) {
      btnSaveSettings.addEventListener("click", () => this.saveSettingsFromForm());
    }

    const btnResetSettings = document.getElementById("btn-reset-settings");
    if (btnResetSettings) {
      btnResetSettings.addEventListener("click", () => {
        settingsManager.reset();
        this.syncSettingsUI();
        uiRenderer.showModal("Settings Reset", "Default settings have been restored.");
      });
    }
  }

  bindWebSocket() {
    wsClient.on("session.ready", (msg) => {
      console.log("[WS] Session Ready. Chords loaded:", msg.chords?.length);
      uiRenderer.setStatus("active", "Tracking");
      if (this.btnRecalibrate) this.btnRecalibrate.disabled = false;
    });

    wsClient.on("tracking.update", (msg) => {
      const st = settingsManager.get();
      uiRenderer.updateHandBadges(msg.chord_hand, msg.strum_hand, st);
      uiRenderer.updateDiagnostics(msg);

      if (uiRenderer.diagnosticsEnabled) {
        uiRenderer.resizeCanvas(this.videoEl.videoWidth || 480, this.videoEl.videoHeight || 360);
        uiRenderer.drawLandmarks(msg.chord_hand, msg.strum_hand);
      }
    });

    wsClient.on("chord.changed", (msg) => {
      const chordDef = {
        id: msg.chord_id,
        name: msg.chord_name,
        root: msg.chord_name.split(" ")[0],
        quality: msg.chord_name.includes("Minor") ? "Minor" : "Major",
        finger_count: msg.finger_count
      };
      instrumentCoordinator.setChord(chordDef);
      uiRenderer.updateChord(instrumentCoordinator.activeChord);
    });

    wsClient.on("strum.detected", (msg) => {
      instrumentCoordinator.handleStrum(msg);
      uiRenderer.triggerStrumFeedback(msg.direction);
    });

    wsClient.on("error", (msg) => {
      console.error("[WS] Error from server:", msg);
      uiRenderer.setStatus("error", "Error");
      uiRenderer.showModal("Tracking Warning", msg.message || "An error occurred with hand tracking.");
    });

    wsClient.on("close", () => {
      if (this.isRunning) {
        uiRenderer.setStatus("warning", "Disconnected");
      }
    });
  }

  async togglePlaying() {
    if (this.isRunning) {
      await this.stopPlaying();
    } else {
      await this.startPlaying();
    }
  }

  async startPlaying() {
    try {
      uiRenderer.setStatus("warning", "Starting Audio...");

      // 1. Initialize Audio Engine & Guitar Sampler on user interaction
      await audioEngine.init(parseFloat(this.volumeSlider?.value || 0.85));
      if (!guitarSampler.isLoaded) {
        uiRenderer.setStatus("warning", "Loading Sounds...");
        await guitarSampler.loadManifestAndSamples();
      }

      // 2. Connect WebSocket to Python backend
      uiRenderer.setStatus("warning", "Connecting Backend...");
      if (!wsClient.isConnected) {
        await wsClient.connect();
      }

      // 3. Start Camera
      uiRenderer.setStatus("warning", "Starting Camera...");
      const selectedDev = this.cameraSelect ? this.cameraSelect.value : null;
      await this.camera.start(selectedDev);

      // Populate device dropdown if empty
      const devices = await this.camera.getDevices();
      if (this.cameraSelect && this.cameraSelect.options.length <= 1) {
        this.cameraSelect.innerHTML = `<option value="">Default Camera</option>`;
        devices.forEach(dev => {
          const opt = document.createElement("option");
          opt.value = dev.deviceId;
          opt.textContent = dev.label || `Camera ${this.cameraSelect.options.length}`;
          this.cameraSelect.appendChild(opt);
        });
      }

      // 4. Update UI State
      this.isRunning = true;
      instrumentCoordinator.isPlaying = true;
      if (this.cameraPlaceholder) this.cameraPlaceholder.style.display = "none";
      if (this.btnCameraText) this.btnCameraText.textContent = "Stop Playing";
      this.btnToggleCamera.classList.remove("btn-primary");
      this.btnToggleCamera.classList.add("btn-danger");

      // Notify server of current settings
      const st = settingsManager.get();
      wsClient.sendJson("session.start", { settings: st });

    } catch (err) {
      console.error("Failed to start AirChord session:", err);
      this.stopPlaying();

      let errorMsg = err.message || "Unknown camera or audio error.";
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        errorMsg = "Camera access was denied. Please grant webcam permissions in your browser settings to play.";
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        errorMsg = "No webcam device was found on this system. Please connect a webcam and reload.";
      }
      uiRenderer.showModal("Camera / Setup Error", errorMsg);
      uiRenderer.setStatus("error", "Error");
    }
  }

  async stopPlaying() {
    this.isRunning = false;
    instrumentCoordinator.isPlaying = false;
    this.camera.stop();
    uiRenderer.clearCanvas();

    if (this.cameraPlaceholder) this.cameraPlaceholder.style.display = "flex";
    if (this.btnCameraText) this.btnCameraText.textContent = "Start Playing";
    this.btnToggleCamera.classList.add("btn-primary");
    this.btnToggleCamera.classList.remove("btn-danger");
    if (this.btnRecalibrate) this.btnRecalibrate.disabled = true;

    uiRenderer.setStatus("", "Idle");
  }

  populateChordSelects() {
    const selects = document.querySelectorAll(".chord-map-select");
    selects.forEach(sel => {
      sel.innerHTML = "";
      this.chordsList.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = `${c.name} (${c.quality})`;
        sel.appendChild(opt);
      });
    });
    this.syncSettingsUI();
  }

  syncSettingsUI() {
    const st = settingsManager.get();
    const chordHandEl = document.getElementById("setting-chord-hand");
    const strumHandEl = document.getElementById("setting-strum-hand");
    const sensEl = document.getElementById("setting-sensitivity");
    const stabEl = document.getElementById("setting-stability");
    const cdEl = document.getElementById("setting-cooldown");

    if (chordHandEl) chordHandEl.value = st.chord_hand;
    if (strumHandEl) strumHandEl.value = st.strum_hand;
    if (sensEl) sensEl.value = st.strum_sensitivity;
    if (stabEl) stabEl.value = st.gesture_stability_ms;
    if (cdEl) cdEl.value = st.strum_cooldown_ms;

    // Chord map selects
    for (let i = 1; i <= 5; i++) {
      const sel = document.getElementById(`map-finger-${i}`);
      if (sel && st.chord_mappings[String(i)]) {
        sel.value = st.chord_mappings[String(i)];
      }
      const hint = document.getElementById(`hint-chord-${i}`);
      if (hint && st.chord_mappings[String(i)]) {
        const mappedId = st.chord_mappings[String(i)];
        const found = this.chordsList.find(c => c.id === mappedId);
        hint.textContent = found ? found.name : mappedId;
      }
    }
  }

  saveSettingsFromForm() {
    const chordHandEl = document.getElementById("setting-chord-hand");
    const strumHandEl = document.getElementById("setting-strum-hand");
    const sensEl = document.getElementById("setting-sensitivity");
    const stabEl = document.getElementById("setting-stability");
    const cdEl = document.getElementById("setting-cooldown");

    const chordMappings = {};
    for (let i = 1; i <= 5; i++) {
      const sel = document.getElementById(`map-finger-${i}`);
      if (sel) {
        chordMappings[String(i)] = sel.value;
      }
    }

    const updated = settingsManager.save({
      chord_hand: chordHandEl ? chordHandEl.value : "Left",
      strum_hand: strumHandEl ? strumHandEl.value : "Right",
      strum_sensitivity: sensEl ? parseFloat(sensEl.value) : 1.0,
      gesture_stability_ms: stabEl ? parseInt(stabEl.value, 10) : 140,
      strum_cooldown_ms: cdEl ? parseInt(cdEl.value, 10) : 120,
      chord_mappings: chordMappings
    });

    if (wsClient.isConnected) {
      wsClient.sendJson("settings.update", { settings: updated });
    }

    this.syncSettingsUI();
    uiRenderer.showModal("Settings Saved", "Your updated configuration has been saved and applied.");
  }
}

// Start application when DOM is ready
window.addEventListener("DOMContentLoaded", () => {
  const app = new AirChordApp();
  app.init();
});

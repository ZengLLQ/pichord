/**
 * AirChord Settings Management with LocalStorage persistence and versioning.
 */

const STORAGE_KEY = "airchord_user_settings_v2";

export const DEFAULT_SETTINGS = {
  version: 2,
  chord_hand: "Left",
  strum_hand: "Right",
  strum_sensitivity: 1.0,
  min_movement_threshold: 0.065,
  gesture_stability_ms: 140,
  strum_cooldown_ms: 120,
  master_volume: 0.85,
  chord_mappings: {
    "1": "c-major",
    "2": "g-major",
    "3": "d-major",
    "4": "e-minor",
    "5": "a-minor"
  },
  selected_camera_id: null,
  diagnostics_enabled: false
};

class SettingsManager {
  constructor() {
    this.settings = this.load();
  }

  load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { ...DEFAULT_SETTINGS };

      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || parsed.version !== 2) {
        console.warn("Settings version mismatch or invalid format; loading defaults.");
        return { ...DEFAULT_SETTINGS };
      }

      return {
        ...DEFAULT_SETTINGS,
        ...parsed,
        chord_mappings: {
          ...DEFAULT_SETTINGS.chord_mappings,
          ...(parsed.chord_mappings || {})
        }
      };
    } catch (e) {
      console.error("Failed to read settings from localStorage:", e);
      return { ...DEFAULT_SETTINGS };
    }
  }

  save(newSettings) {
    this.settings = {
      ...this.settings,
      ...newSettings,
      version: 2
    };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.settings));
    } catch (e) {
      console.error("Failed to persist settings to localStorage:", e);
    }
    return this.settings;
  }

  reset() {
    this.settings = { ...DEFAULT_SETTINGS };
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.error("Failed to clear settings from localStorage:", e);
    }
    return this.settings;
  }

  get() {
    return this.settings;
  }
}

export const settingsManager = new SettingsManager();

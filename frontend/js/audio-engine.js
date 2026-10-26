/**
 * Web Audio API Engine Controller
 */

export class AudioEngine {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.isInitialized = false;
  }

  async init(initialVolume = 0.85) {
    if (this.isInitialized && this.ctx) {
      if (this.ctx.state === "suspended") {
        await this.ctx.resume();
      }
      return;
    }

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
      throw new Error("Web Audio API is not supported in this browser.");
    }

    this.ctx = new AudioContextClass({ latencyHint: "interactive" });
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.setValueAtTime(initialVolume, this.ctx.currentTime);
    this.masterGain.connect(this.ctx.destination);

    if (this.ctx.state === "suspended") {
      await this.ctx.resume();
    }

    this.isInitialized = true;
  }

  setVolume(volume) {
    const safeVolume = Math.max(0, Math.min(1, volume));
    if (this.masterGain && this.ctx) {
      // Smooth gain transition to avoid clicks
      this.masterGain.gain.cancelScheduledValues(this.ctx.currentTime);
      this.masterGain.gain.setTargetAtTime(safeVolume, this.ctx.currentTime, 0.02);
    }
  }

  getContext() {
    return this.ctx;
  }

  getMasterGain() {
    return this.masterGain;
  }
}

export const audioEngine = new AudioEngine();

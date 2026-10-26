/**
 * Guitar Sampler: loads, caches, and plays acoustic guitar audio buffers.
 */

import { audioEngine } from "./audio-engine.js";

export class GuitarSampler {
  constructor() {
    this.buffers = new Map(); // key: `${chordId}_${direction}` -> AudioBuffer
    this.manifest = null;
    this.isLoaded = false;
    this.activeNodes = [];
  }

  async loadManifestAndSamples(manifestUrl = "/assets/audio/manifest.json") {
    try {
      const resp = await fetch(manifestUrl);
      if (!resp.ok) {
        throw new Error(`Failed to fetch audio manifest: ${resp.statusText}`);
      }
      this.manifest = await resp.json();

      const ctx = audioEngine.getContext();
      if (!ctx) {
        throw new Error("AudioContext is not initialized yet.");
      }

      const loadPromises = [];

      for (const chord of this.manifest.chords) {
        // Load downstroke
        if (chord.down) {
          loadPromises.push(
            this._loadBuffer(ctx, `${chord.id}_down`, `/assets${chord.down}`)
          );
        }
        // Load upstroke
        if (chord.up) {
          loadPromises.push(
            this._loadBuffer(ctx, `${chord.id}_up`, `/assets${chord.up}`)
          );
        }
      }

      await Promise.all(loadPromises);
      this.isLoaded = true;
      console.log(`[Sampler] Loaded ${this.buffers.size} guitar samples.`);
      return true;
    } catch (e) {
      console.error("[Sampler] Error loading guitar samples:", e);
      throw e;
    }
  }

  async _loadBuffer(ctx, key, url) {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status} fetching ${url}`);
      }
      const arrayBuffer = await res.arrayBuffer();
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
      this.buffers.set(key, audioBuffer);
    } catch (err) {
      console.warn(`[Sampler] Could not load sample ${url}:`, err);
    }
  }

  playChord(chordId, direction = "down", speedMultiplier = 1.0) {
    const ctx = audioEngine.getContext();
    const masterGain = audioEngine.getMasterGain();
    if (!ctx || !masterGain) return false;

    const normalizedDir = direction.toLowerCase() === "up" ? "up" : "down";
    const sampleKey = `${chordId}_${normalizedDir}`;
    let buffer = this.buffers.get(sampleKey);

    // Fallback to opposite direction if specific one missing
    if (!buffer) {
      const altKey = `${chordId}_${normalizedDir === "down" ? "up" : "down"}`;
      buffer = this.buffers.get(altKey);
    }

    if (!buffer) {
      console.warn(`[Sampler] No audio buffer found for chord: ${chordId} (${direction})`);
      return false;
    }

    // Polyphony control: clean up finished nodes
    this.activeNodes = this.activeNodes.filter(n => n.isPlaying);

    // If more than 6 active voices playing, gently fade oldest
    if (this.activeNodes.length >= 6) {
      const oldest = this.activeNodes.shift();
      if (oldest && oldest.gainNode) {
        oldest.gainNode.gain.setTargetAtTime(0, ctx.currentTime, 0.03);
      }
    }

    const source = ctx.createBufferSource();
    source.buffer = buffer;

    // Dynamics / velocity based on speed
    const strokeGain = ctx.createGain();
    const gainFactor = Math.min(1.2, Math.max(0.6, 0.7 + (speedMultiplier * 0.3)));
    strokeGain.gain.setValueAtTime(gainFactor, ctx.currentTime);

    source.connect(strokeGain);
    strokeGain.connect(masterGain);

    const voice = {
      source,
      gainNode: strokeGain,
      isPlaying: true
    };

    source.onended = () => {
      voice.isPlaying = false;
      try {
        source.disconnect();
        strokeGain.disconnect();
      } catch (_) {}
    };

    source.start(ctx.currentTime);
    this.activeNodes.push(voice);
    return true;
  }
}

export const guitarSampler = new GuitarSampler();

/**
 * Instrument State Coordinator
 */

import { guitarSampler } from "./guitar-sampler.js";

export class InstrumentCoordinator {
  constructor() {
    this.activeChord = {
      id: "c-major",
      name: "C Major",
      root: "C",
      quality: "Major",
      fingerCount: 1,
      hint: "1 Finger: Index Raised"
    };

    this.chordHandState = null;
    this.strumHandState = null;
    this.isPlaying = false;
  }

  setChord(chordDef) {
    if (!chordDef) return;
    this.activeChord = {
      id: chordDef.id,
      name: chordDef.name,
      root: chordDef.root,
      quality: chordDef.quality,
      fingerCount: chordDef.finger_count,
      hint: chordDef.description || `${chordDef.finger_count} Fingers`
    };
  }

  handleStrum(strumEvent) {
    if (!this.isPlaying) return;

    const chordId = strumEvent.active_chord_id || this.activeChord.id;
    const direction = strumEvent.direction || "down";
    const speed = strumEvent.speed || 1.0;

    guitarSampler.playChord(chordId, direction, speed);
  }
}

export const instrumentCoordinator = new InstrumentCoordinator();

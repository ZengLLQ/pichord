/**
 * UI Renderer and Canvas Overlay Manager
 */

export class UIRenderer {
  constructor() {
    this.canvas = document.getElementById("overlay-canvas");
    this.ctx = this.canvas ? this.canvas.getContext("2d") : null;

    // DOM Elements
    this.statusPill = document.getElementById("status-pill");
    this.statusText = document.getElementById("status-text");

    this.chordNameDisplay = document.getElementById("chord-name-display");
    this.chordQualityDisplay = document.getElementById("chord-quality-display");
    this.chordHintDisplay = document.getElementById("chord-hint-display");

    this.indicatorDown = document.getElementById("indicator-down");
    this.indicatorUp = document.getElementById("indicator-up");

    this.badgeChordHand = document.getElementById("badge-chord-hand");
    this.badgeStrumHand = document.getElementById("badge-strum-hand");
    this.roleChordDetail = document.getElementById("role-chord-detail");
    this.roleStrumDetail = document.getElementById("role-strum-detail");

    this.diagPanel = document.getElementById("diagnostics-panel");
    this.diagFps = document.getElementById("diag-fps");
    this.diagLatency = document.getElementById("diag-latency");
    this.diagHands = document.getElementById("diag-hands");
    this.diagFingers = document.getElementById("diag-fingers");

    this.modalDialog = document.getElementById("modal-dialog");
    this.modalTitle = document.getElementById("modal-title");
    this.modalBody = document.getElementById("modal-body");

    this.diagnosticsEnabled = false;
  }

  setStatus(state, label) {
    if (!this.statusPill || !this.statusText) return;
    this.statusPill.className = `status-pill ${state}`;
    this.statusText.textContent = label;
  }

  updateChord(chord) {
    if (!chord) return;
    if (this.chordNameDisplay) {
      this.chordNameDisplay.textContent = chord.root || chord.name.split(" ")[0];
      // Subtle pulse animation
      this.chordNameDisplay.style.transform = "scale(1.08)";
      setTimeout(() => {
        if (this.chordNameDisplay) this.chordNameDisplay.style.transform = "scale(1)";
      }, 150);
    }
    if (this.chordQualityDisplay) {
      this.chordQualityDisplay.textContent = chord.quality || "";
    }
    if (this.chordHintDisplay) {
      this.chordHintDisplay.textContent = `${chord.fingerCount} Finger${chord.fingerCount > 1 ? "s" : ""}: ${chord.name}`;
    }
  }

  triggerStrumFeedback(direction) {
    const isUp = direction.toLowerCase() === "up";
    const indicator = isUp ? this.indicatorUp : this.indicatorDown;

    if (indicator) {
      indicator.classList.add("pulse");
      setTimeout(() => {
        indicator.classList.remove("pulse");
      }, 200);
    }
  }

  updateHandBadges(chordHandState, strumHandState, settings) {
    const chordHandName = settings.chord_hand || "Left";
    const strumHandName = settings.strum_hand || "Right";

    const chordTitleEl = document.getElementById("role-chord-hand-name");
    const strumTitleEl = document.getElementById("role-strum-hand-name");
    if (chordTitleEl) chordTitleEl.textContent = `${chordHandName} Hand`;
    if (strumTitleEl) strumTitleEl.textContent = `${strumHandName} Hand`;

    if (this.badgeChordHand) {
      if (chordHandState) {
        this.badgeChordHand.classList.add("active");
        this.roleChordDetail.textContent = `Tracking (${chordHandState.finger_count ?? 0} fingers)`;
      } else {
        this.badgeChordHand.classList.remove("active");
        this.roleChordDetail.textContent = "Searching for hand...";
      }
    }

    if (this.badgeStrumHand) {
      if (strumHandState) {
        this.badgeStrumHand.classList.add("active");
        this.roleStrumDetail.textContent = "Ready to strum";
      } else {
        this.badgeStrumHand.classList.remove("active");
        this.roleStrumDetail.textContent = "Searching for hand...";
      }
    }
  }

  updateDiagnostics(data) {
    if (!this.diagnosticsEnabled) return;
    if (this.diagFps) this.diagFps.textContent = `${data.fps || 0.0}`;
    if (this.diagLatency) this.diagLatency.textContent = `${data.latency_ms || 0.0} ms`;
    if (this.diagHands) this.diagHands.textContent = `${data.hands_detected || 0}`;
    if (this.diagFingers && data.chord_hand) {
      this.diagFingers.textContent = `${data.chord_hand.finger_count || 0}`;
    }
  }

  toggleDiagnostics(forced) {
    this.diagnosticsEnabled = forced !== undefined ? forced : !this.diagnosticsEnabled;
    if (this.diagPanel) {
      if (this.diagnosticsEnabled) {
        this.diagPanel.classList.add("open");
      } else {
        this.diagPanel.classList.remove("open");
        this.clearCanvas();
      }
    }
    return this.diagnosticsEnabled;
  }

  resizeCanvas(width, height) {
    if (this.canvas && (this.canvas.width !== width || this.canvas.height !== height)) {
      this.canvas.width = width;
      this.canvas.height = height;
    }
  }

  clearCanvas() {
    if (this.ctx && this.canvas) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }

  drawLandmarks(chordHand, strumHand) {
    if (!this.ctx || !this.canvas) return;
    this.clearCanvas();

    const w = this.canvas.width;
    const h = this.canvas.height;

    const drawHand = (hand, color) => {
      if (!hand || !hand.landmarks) return;
      const lms = hand.landmarks;

      // Draw bones
      const connections = [
        [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
        [0, 5], [5, 6], [6, 7], [7, 8],       // Index
        [0, 9], [9, 10], [10, 11], [11, 12],   // Middle
        [0, 13], [13, 14], [14, 15], [15, 16], // Ring
        [0, 17], [17, 18], [18, 19], [19, 20], // Pinky
        [5, 9], [9, 13], [13, 17]             // Palm base
      ];

      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 2;
      this.ctx.beginPath();
      for (const [i, j] of connections) {
        if (lms[i] && lms[j]) {
          this.ctx.moveTo(lms[i][0] * w, lms[i][1] * h);
          this.ctx.lineTo(lms[j][0] * w, lms[j][1] * h);
        }
      }
      this.ctx.stroke();

      // Draw joints
      this.ctx.fillStyle = "#ffffff";
      for (const pt of lms) {
        this.ctx.beginPath();
        this.ctx.arc(pt[0] * w, pt[1] * h, 3, 0, 2 * Math.PI);
        this.ctx.fill();
      }
    };

    if (chordHand) drawHand(chordHand, "rgba(200, 241, 105, 0.7)"); // Lime for chord hand
    if (strumHand) drawHand(strumHand, "rgba(59, 130, 246, 0.7)");  // Blue for strum hand
  }

  showModal(title, message) {
    if (!this.modalDialog) return;
    if (this.modalTitle) this.modalTitle.textContent = title;
    if (this.modalBody) this.modalBody.textContent = message;
    this.modalDialog.showModal();
  }

  closeModal() {
    if (this.modalDialog && this.modalDialog.open) {
      this.modalDialog.close();
    }
  }
}

export const uiRenderer = new UIRenderer();

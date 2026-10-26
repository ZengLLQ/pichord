/**
 * Webcam Controller and Frame Streaming Engine.
 */

import { wsClient } from "./websocket.js";

export class CameraController {
  constructor(videoElement, options = {}) {
    this.video = videoElement;
    this.stream = null;
    this.isRunning = false;

    // Configurable inference size
    this.targetWidth = options.width || 480;
    this.targetHeight = options.height || 360;
    this.targetFps = options.fps || 18;
    this.jpegQuality = options.quality || 0.65;

    // Offscreen canvas for frame extraction & resizing
    this.canvas = document.createElement("canvas");
    this.canvas.width = this.targetWidth;
    this.canvas.height = this.targetHeight;
    this.ctx = this.canvas.getContext("2d", { willReadFrequently: true });

    this.timerId = null;
    this.inFlight = false;
    this.frameSeq = 0;
  }

  async getDevices() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.filter(d => d.kind === "videoinput");
    } catch (e) {
      console.warn("Could not enumerate video devices:", e);
      return [];
    }
  }

  async start(deviceId = null) {
    if (this.isRunning) return;

    const constraints = {
      audio: false,
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: "user"
      }
    };

    if (deviceId) {
      constraints.video.deviceId = { exact: deviceId };
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.stream;

      await new Promise((resolve) => {
        this.video.onloadedmetadata = () => {
          this.video.play();
          resolve();
        };
      });

      this.isRunning = true;
      this.frameSeq = 0;
      this.inFlight = false;

      // Start frame capture loop
      const intervalMs = Math.round(1000 / this.targetFps);
      this.timerId = setInterval(() => this._captureAndSendFrame(), intervalMs);
      return true;
    } catch (err) {
      this.stop();
      throw err;
    }
  }

  _captureAndSendFrame() {
    if (!this.isRunning || !wsClient.isConnected) return;
    if (this.inFlight) {
      // Discard / skip frame if previous frame is still in transit
      return;
    }

    if (this.video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;

    this.inFlight = true;
    const seq = ++this.frameSeq;
    const timestampMs = Math.round(performance.now());

    // Draw video frame to offscreen canvas scaled to targetWidth x targetHeight
    this.ctx.drawImage(this.video, 0, 0, this.targetWidth, this.targetHeight);

    this.canvas.toBlob(
      (blob) => {
        if (!blob || !this.isRunning) {
          this.inFlight = false;
          return;
        }

        blob.arrayBuffer().then((buffer) => {
          wsClient.sendFrame(new Uint8Array(buffer), seq, timestampMs);
          this.inFlight = false;
        }).catch(() => {
          this.inFlight = false;
        });
      },
      "image/jpeg",
      this.jpegQuality
    );
  }

  stop() {
    this.isRunning = false;
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    if (this.video) {
      this.video.srcObject = null;
    }
    this.inFlight = false;
  }
}

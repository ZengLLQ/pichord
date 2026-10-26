/**
 * WebSocket client for AirChord backend real-time stream.
 */

export class WebSocketClient {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.listeners = new Map();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  emit(event, data) {
    const list = this.listeners.get(event);
    if (list) {
      list.forEach(cb => cb(data));
    }
  }

  connect() {
    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/play`;

      this.ws = new WebSocket(wsUrl);
      this.ws.binaryType = "arraybuffer";

      this.ws.onopen = () => {
        this.isConnected = true;
        this.emit("open");
        resolve();
      };

      this.ws.onclose = (e) => {
        this.isConnected = false;
        this.emit("close", e);
      };

      this.ws.onerror = (err) => {
        this.emit("error", err);
        reject(err);
      };

      this.ws.onmessage = (event) => {
        if (typeof event.data === "string") {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type) {
              this.emit(msg.type, msg);
            }
          } catch (e) {
            console.error("[WS] Error parsing JSON message:", e);
          }
        }
      };
    });
  }

  sendJson(type, payload = {}) {
    if (!this.isConnected || !this.ws) return;
    const msg = JSON.stringify({ type, ...payload });
    this.ws.send(msg);
  }

  sendFrame(jpegBlobOrUint8, seq, timestampMs) {
    if (!this.isConnected || !this.ws) return;

    // Pack: [4-byte header length] + [JSON header UTF-8] + [JPEG bytes]
    const headerStr = JSON.stringify({ seq, timestamp_ms: timestampMs });
    const encoder = new TextEncoder();
    const headerBytes = encoder.encode(headerStr);
    const headerLen = headerBytes.length;

    const jpegBytes = jpegBlobOrUint8 instanceof Uint8Array
      ? jpegBlobOrUint8
      : new Uint8Array(jpegBlobOrUint8);

    const totalLen = 4 + headerLen + jpegBytes.length;
    const packet = new Uint8Array(totalLen);
    const view = new DataView(packet.buffer);

    // Write 4-byte header length (big-endian)
    view.setUint32(0, headerLen, false);

    // Copy header
    packet.set(headerBytes, 4);

    // Copy JPEG payload
    packet.set(jpegBytes, 4 + headerLen);

    this.ws.send(packet.buffer);
  }

  disconnect() {
    if (this.ws) {
      try {
        this.sendJson("session.stop");
        this.ws.close();
      } catch (_) {}
      this.ws = null;
    }
    this.isConnected = false;
  }
}

export const wsClient = new WebSocketClient();

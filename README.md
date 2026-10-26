# 🎸 AirChord — Virtual Guitar Controller (Version 2)
> **Python-Powered, Browser-Based Virtual Guitar Using Real-Time Computer Vision**

AirChord transforms any standard webcam into a hands-free virtual guitar instrument. One hand selects chords through finger count gestures, while the other performs air-strumming to trigger authentic acoustic guitar audio in real time.

---

## 🌟 Key Features

- **Real-Time Dual-Hand Computer Vision:** Python backend powered by OpenCV and MediaPipe Hand Landmarker Tasks Vision.
- **Intelligent Hand Role Assignment:** Automatically assigns chord selection and strumming roles with spatial consistency and instant role-swapping (Right-handed or Southpaw).
- **Geometric Chord Recognition:** Robust finger extension classification invariant to scale, distance, and tilt, with temporal hysteresis (140 ms window) for glitch-free transitions.
- **Velocity-Driven Strumming Engine:** State machine tracking vertical wrist velocity, stroke displacement thresholds, direction detection (downstrokes vs upstrokes), and a 120 ms anti-bounce cooldown.
- **Low-Latency Browser Audio:** Local Web Audio API playback using authentic recorded guitar chord samples (`.wav`).
- **Binary WebSocket Protocol:** High-throughput binary frame streaming (480×360 JPEG) and compact JSON tracking events. Discards stale in-flight frames to prevent latency buildup.
- **Dark, Restrained Modern UI:** Built with semantic HTML5, modern CSS3 variables (`#0B0D0F`, `#14171B`, `#C8F169`), and vanilla ES modules. No Node.js build pipeline required.
- **Privacy by Design:** Zero cloud API dependencies; all computer vision inference runs locally on your machine.

---

## 🏗️ Architecture Pipeline

```
Webcam Capture (Browser)
   │
   ▼
Canvas Resizing (480 × 360 JPEG)
   │
   ▼ Binary WebSocket
FastAPI WebSocket Receiver (/ws/play)
   │
   ▼ Offloaded Worker Thread
MediaPipe Hand Landmarker (Video Mode)
   │
   ├── Landmark Smoother (Exponential Moving Average)
   ├── Hand Role Assignment (Chord Hand vs Strum Hand)
   ├── Geometric Finger Classifier (1 to 5 Fingers)
   ├── Gesture Classifier (Temporal Stability Window)
   └── Strum Motion State Machine (Vertical Velocity & Displacement)
   │
   ▼ Compact JSON
Browser Event Dispatcher
   │
   ├── Web Audio API (AudioBufferSourceNode + GainNode)
   ├── Acoustic Guitar Sample Playback (Downstroke / Upstroke)
   └── Canvas Landmark Overlay & Dynamic HUD Feedback
```

---

## 📋 Default Gesture & Chord Mapping

Gestures are intuitive control mappings designed for webcam reliability:

| Gesture | Finger Configuration | Default Chord | Audio Asset |
|---|---|---|---|
| **1 Finger** | Index finger raised | **C Major** | `c-major-down.wav` / `up.wav` |
| **2 Fingers** | Index + Middle (Peace sign) | **G Major** | `g-major-down.wav` / `up.wav` |
| **3 Fingers** | Index + Middle + Ring | **D Major** | `d-major-down.wav` / `up.wav` |
| **4 Fingers** | Four fingers raised (thumb folded) | **E Minor** | `e-minor-down.wav` / `up.wav` |
| **5 Fingers** | Open palm (all fingers spread) | **A Minor** | `a-minor-down.wav` / `up.wav` |

*Note: You can customize any gesture-to-chord mapping in the in-app **Settings** tab.*

---

## 🖐️ Strumming Motion Controls

- **Downstroke:** Briskly move your strumming hand downward through the air.
- **Upstroke:** Flick your strumming hand upward through the air.
- **Sensitivity & Thresholds:** Easily adjustable in Settings (default requires ~0.70 normalized speed and >6.5% screen height displacement).

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python:** 3.11 or compatible (3.11.x recommended).
- **Webcam:** Any built-in or external USB webcam.
- **Modern Browser:** Chrome, Edge, Safari, or Firefox with Web Audio API support.

### 1. Setup Virtual Environment

Using `uv` (recommended):
```bash
uv venv .venv --python 3.11
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux
```

Or using standard Python `venv`:
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

For development and test tooling:
```bash
pip install -r requirements-dev.txt
```

### 3. Verify / Download MediaPipe Vision Model

AirChord includes the `hand_landmarker.task` model inside `models/`. If missing, download it automatically:
```bash
python scripts/download_model.py
```

### 4. Run the Server

Preferred startup command:
```bash
python run.py
```

Or using Uvicorn directly:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 5. Play AirChord

1. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000
   ```
2. Click **Start Playing**.
3. Grant camera permissions when prompted by your browser.
4. Position both hands in view of the webcam:
   - Your **Left Hand** controls chords (raise 1 to 5 fingers).
   - Your **Right Hand** strums vertically through the air.
5. Enjoy real acoustic guitar playback!

---

## ⚙️ Configuration & Customization

Through the **Settings** view in the browser, you can configure:

1. **Hand Roles:** Swap roles if you are left-handed (Southpaw mode).
2. **Gesture-to-Chord Mappings:** Remap any finger count (1–5) to any supported chord.
3. **Strum Sensitivity:** Scale detection sensitivity up or down.
4. **Gesture Stability Window:** Tune the hysteresis window (80–300 ms).
5. **Strum Cooldown:** Set the refractory period between strums (60–250 ms).
6. **Master Volume:** Adjust or mute master output gain.
7. **Diagnostics Overlay:** View live FPS, inference latency, detected hands, and landmark skeleton overlays.

All settings are safely validated and persisted in `localStorage`.

---

## 🧪 Automated Testing

AirChord includes a comprehensive unit and integration test suite:

```bash
pytest -v
```

### Test Coverage Highlights

- **`test_finger_classifier.py`:** Tests finger extension geometry (1–5 fingers, closed fist, rotated hand orientations, missing/corrupt landmarks).
- **`test_chord_mappings.py`:** Tests default mappings, custom mapping validation, invalid chord IDs, and reset-to-defaults.
- **`test_landmark_smoother.py`:** Tests exponential moving average dampening, time-gap resets, and tracking reinitialization.
- **`test_strum_detector.py`:** Tests downstroke and upstroke detection, jitter rejection, displacement thresholds, cooldown intervals, and chord association.
- **`test_api.py`:** Tests `/api/health`, `/api/ready`, `/api/chords`, `/api/settings`, and static asset serving.
- **`test_websocket.py`:** Tests `/ws/play` handshake, binary frame packing/unpacking, tracking updates, and disconnection cleanup.

### Linting & Formatting

```bash
ruff check .
ruff format .
```

---

## 🔒 Privacy & Security

- **Local Inference:** Video frames are sent directly to your local FastAPI server (`127.0.0.1`) and never uploaded to any external third-party cloud.
- **No Database / No Accounts:** No registration, database, cookies, or tracking telemetry.
- **Local Network Default:** The server binds to `127.0.0.1` by default to prevent unintended exposure on public networks.

---

## 🎵 Asset Attribution & Licensing

- **Code:** Licensed under the [MIT License](LICENSE).
- **Computer Vision Model:** `hand_landmarker.task` is licensed by Google LLC under the Apache License 2.0.
- **Guitar Samples:** Bundled `.wav` acoustic chord recordings (C Major, G Major, D Major, E Minor, A Minor) formatted and cataloged in `frontend/assets/audio/manifest.json`.

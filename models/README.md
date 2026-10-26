# MediaPipe Hand Landmarker Model

This directory holds the `hand_landmarker.task` model bundle used by Google MediaPipe Tasks Vision.

## Model Details

- **Model name:** MediaPipe Hand Landmarker (Float16)
- **Artifact:** `hand_landmarker.task`
- **Source:** Google MediaPipe Models Repository
- **URL:** `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`
- **Output:** 21 3D hand landmarks per hand, normalized coordinates (x, y, z), and handedness classification ("Left" / "Right")
- **License:** Apache License 2.0 (Google LLC)

## Installation

Run the automated download script:

```bash
python scripts/download_model.py
```

To force re-downloading:

```bash
python scripts/download_model.py --force
```

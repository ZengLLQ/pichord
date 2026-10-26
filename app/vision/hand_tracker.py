import threading
from pathlib import Path
from typing import List, Optional

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from app.vision.models import DetectedHand, Point3D


class HandTracker:
    """Wrapper around MediaPipe HandLandmarker in VIDEO running mode."""

    def __init__(
        self,
        model_path: Path,
        num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self.model_path = Path(model_path)
        self.num_hands = num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_presence_confidence = min_presence_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self._detector: Optional[vision.HandLandmarker] = None
        self._lock = threading.Lock()
        self._last_timestamp_ms: int = -1

    def is_ready(self) -> bool:
        return self._detector is not None

    def initialize(self) -> None:
        with self._lock:
            if self._detector is not None:
                return

            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"MediaPipe hand landmarker model not found at: {self.model_path.resolve()}. "
                    "Run scripts/download_model.py to download it."
                )

            base_options = python.BaseOptions(model_asset_path=str(self.model_path.resolve()))
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=self.num_hands,
                min_hand_detection_confidence=self.min_detection_confidence,
                min_hand_presence_confidence=self.min_presence_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )
            self._detector = vision.HandLandmarker.create_from_options(options)
            self._last_timestamp_ms = -1

    def detect(self, rgb_frame: np.ndarray, timestamp_ms: int) -> List[DetectedHand]:
        """Detect hands in an RGB numpy frame (H, W, 3).

        Requires VIDEO running mode with strictly monotonically increasing timestamps.
        """
        if self._detector is None:
            self.initialize()

        with self._lock:
            if self._detector is None:
                return []

            # Enforce strictly increasing timestamps for MediaPipe VIDEO mode
            if timestamp_ms <= self._last_timestamp_ms:
                timestamp_ms = self._last_timestamp_ms + 1
            self._last_timestamp_ms = timestamp_ms

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection_result = self._detector.detect_for_video(mp_image, timestamp_ms)

            detected_hands: List[DetectedHand] = []
            if not detection_result.hand_landmarks:
                return detected_hands

            num_detected = len(detection_result.hand_landmarks)
            for i in range(num_detected):
                raw_landmarks = detection_result.hand_landmarks[i]
                points = [
                    Point3D(x=float(lm.x), y=float(lm.y), z=float(lm.z)) for lm in raw_landmarks
                ]

                # MediaPipe handedness
                handedness = "Right"
                score = 0.8
                if detection_result.handedness and i < len(detection_result.handedness):
                    top_category = detection_result.handedness[i][0]
                    handedness = top_category.category_name
                    score = float(top_category.score)

                detected_hands.append(
                    DetectedHand(landmarks=points, handedness=handedness, score=score)
                )

            return detected_hands

    def close(self) -> None:
        with self._lock:
            if self._detector is not None:
                try:
                    self._detector.close()
                except Exception:
                    pass
                self._detector = None
                self._last_timestamp_ms = -1

from typing import Dict, List

from app.vision.models import Point3D


class LandmarkSmoother:
    """Exponential Moving Average (EMA) smoother for 21 3D landmarks per hand role."""

    def __init__(self, alpha: float = 0.65, max_gap_ms: int = 300):
        self.alpha = max(0.1, min(alpha, 1.0))
        self.max_gap_ms = max_gap_ms
        self._history: Dict[str, List[Point3D]] = {}
        self._last_timestamp: Dict[str, int] = {}

    def set_alpha(self, alpha: float) -> None:
        self.alpha = max(0.1, min(alpha, 1.0))

    def smooth(self, hand_key: str, landmarks: List[Point3D], timestamp_ms: int) -> List[Point3D]:
        """Smooth landmarks for a given hand track ('chord' or 'strum')."""
        if not landmarks:
            return landmarks

        last_time = self._last_timestamp.get(hand_key)
        prev_landmarks = self._history.get(hand_key)

        # Reset if too much time has elapsed or no history
        if (
            last_time is None
            or prev_landmarks is None
            or (timestamp_ms - last_time) > self.max_gap_ms
        ):
            self._history[hand_key] = [Point3D(x=p.x, y=p.y, z=p.z) for p in landmarks]
            self._last_timestamp[hand_key] = timestamp_ms
            return landmarks

        smoothed: List[Point3D] = []
        for curr, prev in zip(landmarks, prev_landmarks):
            sx = self.alpha * curr.x + (1.0 - self.alpha) * prev.x
            sy = self.alpha * curr.y + (1.0 - self.alpha) * prev.y
            sz = self.alpha * curr.z + (1.0 - self.alpha) * prev.z
            smoothed.append(Point3D(x=sx, y=sy, z=sz))

        self._history[hand_key] = smoothed
        self._last_timestamp[hand_key] = timestamp_ms
        return smoothed

    def reset_hand(self, hand_key: str) -> None:
        self._history.pop(hand_key, None)
        self._last_timestamp.pop(hand_key, None)

    def reset_all(self) -> None:
        self._history.clear()
        self._last_timestamp.clear()

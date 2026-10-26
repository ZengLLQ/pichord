from typing import Optional

from app.vision.models import Point3D


class MotionSnapshot:
    def __init__(
        self,
        y: float,
        velocity_y: float,
        raw_velocity_y: float,
        displacement_y: float,
        timestamp_ms: int,
        dt_s: float,
    ):
        self.y = y
        self.velocity_y = velocity_y  # positive = down, negative = up (in normalized screen coords)
        self.raw_velocity_y = raw_velocity_y
        self.displacement_y = displacement_y
        self.timestamp_ms = timestamp_ms
        self.dt_s = dt_s


class MotionAnalyzer:
    """Analyzes the vertical trajectory of the strumming hand wrist over time."""

    def __init__(self, velocity_smoothing: float = 0.5):
        self.velocity_smoothing = velocity_smoothing
        self.prev_y: Optional[float] = None
        self.interval_start_y: Optional[float] = None
        self._prev_timestamp_ms: Optional[int] = None
        self._smoothed_velocity_y: float = 0.0
        self._has_velocity: bool = False
        self._stroke_start_y: Optional[float] = None

    def reset(self) -> None:
        self.prev_y = None
        self.interval_start_y = None
        self._prev_timestamp_ms = None
        self._smoothed_velocity_y = 0.0
        self._has_velocity = False
        self._stroke_start_y = None

    def mark_stroke_start(self, y: float) -> None:
        self._stroke_start_y = y

    def update(self, wrist: Point3D, timestamp_ms: int) -> Optional[MotionSnapshot]:
        curr_y = wrist.y

        if self.prev_y is None or self._prev_timestamp_ms is None:
            self.prev_y = curr_y
            self.interval_start_y = curr_y
            self._prev_timestamp_ms = timestamp_ms
            self._stroke_start_y = curr_y
            self._smoothed_velocity_y = 0.0
            self._has_velocity = False
            return MotionSnapshot(
                y=curr_y,
                velocity_y=0.0,
                raw_velocity_y=0.0,
                displacement_y=0.0,
                timestamp_ms=timestamp_ms,
                dt_s=0.0,
            )

        dt_ms = timestamp_ms - self._prev_timestamp_ms
        if dt_ms <= 0:
            dt_ms = 1  # guard against divide by zero

        dt_s = dt_ms / 1000.0

        # Raw velocity (normalized units per second)
        raw_velocity_y = (curr_y - self.prev_y) / dt_s

        # Apply smoothing to velocity: first valid delta sets it directly
        if self._has_velocity:
            self._smoothed_velocity_y = (
                self.velocity_smoothing * raw_velocity_y
                + (1.0 - self.velocity_smoothing) * self._smoothed_velocity_y
            )
        else:
            self._smoothed_velocity_y = raw_velocity_y
            self._has_velocity = True

        self.interval_start_y = self.prev_y
        if self._stroke_start_y is None:
            self._stroke_start_y = self.interval_start_y

        displacement_y = curr_y - self._stroke_start_y

        self.prev_y = curr_y
        self._prev_timestamp_ms = timestamp_ms

        return MotionSnapshot(
            y=curr_y,
            velocity_y=self._smoothed_velocity_y,
            raw_velocity_y=raw_velocity_y,
            displacement_y=displacement_y,
            timestamp_ms=timestamp_ms,
            dt_s=dt_s,
        )

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.strumming.motion_analyzer import MotionAnalyzer
from app.vision.models import Point3D


class MotionState(str, Enum):
    IDLE = "IDLE"
    DOWNSTROKE_TRACKING = "DOWNSTROKE_TRACKING"
    UPSTROKE_TRACKING = "UPSTROKE_TRACKING"
    ACCEPTED = "ACCEPTED"
    COOLDOWN = "COOLDOWN"
    RE_ARMING = "RE_ARMING"


class StrumEvent(BaseModel):
    seq: int
    direction: str  # "down" or "up"
    speed: float
    displacement: float
    active_chord_id: str
    timestamp_ms: int
    confidence: float


class StrumDetector:
    """State-machine based strumming motion detector."""

    def __init__(
        self,
        min_speed: float = 0.70,
        min_displacement: float = 0.065,
        cooldown_ms: int = 120,
        sensitivity: float = 1.0,
    ):
        self.base_min_speed = min_speed
        self.base_min_displacement = min_displacement
        self.cooldown_ms = cooldown_ms
        self.sensitivity = max(0.5, min(sensitivity, 2.0))

        self.motion_analyzer = MotionAnalyzer()
        self.state = MotionState.IDLE

        self._event_seq: int = 0
        self._stroke_start_time_ms: int = 0
        self._accepted_time_ms: int = 0
        self._peak_speed: float = 0.0
        self._active_direction: Optional[str] = None

    @property
    def effective_min_speed(self) -> float:
        # Higher sensitivity = lower threshold needed
        return self.base_min_speed / self.sensitivity

    @property
    def effective_min_displacement(self) -> float:
        return self.base_min_displacement / self.sensitivity

    def set_tuning(
        self,
        sensitivity: Optional[float] = None,
        min_displacement: Optional[float] = None,
        cooldown_ms: Optional[int] = None,
    ) -> None:
        if sensitivity is not None:
            self.sensitivity = max(0.5, min(sensitivity, 2.0))
        if min_displacement is not None:
            self.base_min_displacement = max(0.02, min(min_displacement, 0.20))
        if cooldown_ms is not None:
            self.cooldown_ms = max(50, min(cooldown_ms, 300))

    def reset(self) -> None:
        self.motion_analyzer.reset()
        self.state = MotionState.IDLE
        self._stroke_start_time_ms = 0
        self._accepted_time_ms = 0
        self._peak_speed = 0.0
        self._active_direction = None

    def update(
        self,
        wrist: Optional[Point3D],
        timestamp_ms: int,
        active_chord_id: str,
        hand_confidence: float = 0.8,
    ) -> Optional[StrumEvent]:
        if wrist is None:
            # Strumming hand lost: reset motion tracking
            self.reset()
            return None

        # Check tracking confidence: low-confidence tracking should not trigger strums
        if hand_confidence < 0.35:
            return None

        snapshot = self.motion_analyzer.update(wrist, timestamp_ms)
        if snapshot is None:
            return None

        vy = snapshot.velocity_y
        speed = abs(vy)

        # 1. State: COOLDOWN
        if self.state == MotionState.COOLDOWN:
            if (timestamp_ms - self._accepted_time_ms) >= self.cooldown_ms:
                self.state = MotionState.RE_ARMING
                return None
            else:
                return None

        # 2. State: RE_ARMING
        if self.state == MotionState.RE_ARMING:
            # Re-arm once hand speed drops below recovery threshold
            if speed < (self.effective_min_speed * 0.40):
                self.state = MotionState.IDLE
                self.motion_analyzer.mark_stroke_start(wrist.y)
            return None

        # 3. State: IDLE
        if self.state == MotionState.IDLE:
            if vy >= self.effective_min_speed:
                # Downward movement candidate
                self.state = MotionState.DOWNSTROKE_TRACKING
                self._active_direction = "down"
                self._stroke_start_time_ms = timestamp_ms
                self._peak_speed = speed
                start_y = (
                    self.motion_analyzer.interval_start_y
                    if self.motion_analyzer.interval_start_y is not None
                    else wrist.y
                )
                self.motion_analyzer.mark_stroke_start(start_y)
            elif vy <= -self.effective_min_speed:
                # Upward movement candidate
                self.state = MotionState.UPSTROKE_TRACKING
                self._active_direction = "up"
                self._stroke_start_time_ms = timestamp_ms
                self._peak_speed = speed
                start_y = (
                    self.motion_analyzer.interval_start_y
                    if self.motion_analyzer.interval_start_y is not None
                    else wrist.y
                )
                self.motion_analyzer.mark_stroke_start(start_y)
            return None

        # 4. State: DOWNSTROKE_TRACKING
        if self.state == MotionState.DOWNSTROKE_TRACKING:
            self._peak_speed = max(self._peak_speed, speed)
            disp = snapshot.displacement_y  # positive = down

            if disp >= self.effective_min_displacement:
                # Valid Downstroke Accepted!
                self._event_seq += 1
                self.state = MotionState.COOLDOWN
                self._accepted_time_ms = timestamp_ms

                conf = min(1.0, 0.7 + 0.3 * (self._peak_speed / max(1.0, self.effective_min_speed)))
                return StrumEvent(
                    seq=self._event_seq,
                    direction="down",
                    speed=round(self._peak_speed, 3),
                    displacement=round(disp, 4),
                    active_chord_id=active_chord_id,
                    timestamp_ms=timestamp_ms,
                    confidence=round(conf, 3),
                )

            # Check if stroke stopped moving down or reversed without reaching displacement threshold
            if (timestamp_ms - self._stroke_start_time_ms) > 400 or snapshot.raw_velocity_y <= 0:
                self.state = MotionState.IDLE
                self.motion_analyzer.mark_stroke_start(wrist.y)
                return None

        # 5. State: UPSTROKE_TRACKING
        if self.state == MotionState.UPSTROKE_TRACKING:
            self._peak_speed = max(self._peak_speed, speed)
            disp = -snapshot.displacement_y  # positive = up

            if disp >= self.effective_min_displacement:
                # Valid Upstroke Accepted!
                self._event_seq += 1
                self.state = MotionState.COOLDOWN
                self._accepted_time_ms = timestamp_ms

                conf = min(1.0, 0.7 + 0.3 * (self._peak_speed / max(1.0, self.effective_min_speed)))
                return StrumEvent(
                    seq=self._event_seq,
                    direction="up",
                    speed=round(self._peak_speed, 3),
                    displacement=round(disp, 4),
                    active_chord_id=active_chord_id,
                    timestamp_ms=timestamp_ms,
                    confidence=round(conf, 3),
                )

            # Check if stroke stopped moving up or reversed without reaching displacement threshold
            if (timestamp_ms - self._stroke_start_time_ms) > 400 or snapshot.raw_velocity_y >= 0:
                self.state = MotionState.IDLE
                self.motion_analyzer.mark_stroke_start(wrist.y)
                return None

        return None

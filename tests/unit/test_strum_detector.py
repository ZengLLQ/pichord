import pytest

from app.strumming.strum_detector import MotionState, StrumDetector
from app.vision.models import Point3D


@pytest.fixture
def detector():
    return StrumDetector(min_speed=0.60, min_displacement=0.06, cooldown_ms=100, sensitivity=1.0)


def test_downstroke_detection(detector):
    # Sequence of frames moving downward rapidly
    # t=0: y=0.40
    evt0 = detector.update(Point3D(x=0.5, y=0.40), timestamp_ms=0, active_chord_id="c-major")
    assert evt0 is None
    assert detector.state == MotionState.IDLE

    # t=50ms: y=0.45 (speed = 0.05 / 0.05 = 1.0 > 0.6)
    evt1 = detector.update(Point3D(x=0.5, y=0.45), timestamp_ms=50, active_chord_id="c-major")
    assert evt1 is None
    assert detector.state == MotionState.DOWNSTROKE_TRACKING

    # t=100ms: y=0.52 (disp = 0.52 - 0.40 = 0.12 >= 0.06)
    evt2 = detector.update(Point3D(x=0.5, y=0.52), timestamp_ms=100, active_chord_id="c-major")
    assert evt2 is not None
    assert evt2.direction == "down"
    assert evt2.active_chord_id == "c-major"
    assert evt2.displacement >= 0.06
    assert detector.state == MotionState.COOLDOWN


def test_upstroke_detection(detector):
    # Sequence of frames moving upward rapidly
    # t=0: y=0.60
    evt0 = detector.update(Point3D(x=0.5, y=0.60), timestamp_ms=0, active_chord_id="g-major")
    assert evt0 is None

    # t=50ms: y=0.53 (speed = -1.4, upward)
    evt1 = detector.update(Point3D(x=0.5, y=0.53), timestamp_ms=50, active_chord_id="g-major")
    assert evt1 is None
    assert detector.state == MotionState.UPSTROKE_TRACKING

    # t=100ms: y=0.45 (disp = 0.60 - 0.45 = 0.15 >= 0.06)
    evt2 = detector.update(Point3D(x=0.5, y=0.45), timestamp_ms=100, active_chord_id="g-major")
    assert evt2 is not None
    assert evt2.direction == "up"
    assert evt2.active_chord_id == "g-major"
    assert detector.state == MotionState.COOLDOWN


def test_jitter_rejection_insufficient_speed(detector):
    # Very slow drift: 0.01 units over 100ms (speed = 0.1 < 0.6)
    detector.update(Point3D(x=0.5, y=0.40), timestamp_ms=0, active_chord_id="c-major")
    evt1 = detector.update(Point3D(x=0.5, y=0.41), timestamp_ms=100, active_chord_id="c-major")
    evt2 = detector.update(Point3D(x=0.5, y=0.42), timestamp_ms=200, active_chord_id="c-major")
    assert evt1 is None
    assert evt2 is None
    assert detector.state == MotionState.IDLE


def test_insufficient_displacement_rejection(detector):
    # Fast twitch but tiny displacement: moves by only 0.01
    detector.update(Point3D(x=0.5, y=0.40), timestamp_ms=0, active_chord_id="c-major")
    detector.update(Point3D(x=0.5, y=0.42), timestamp_ms=20, active_chord_id="c-major")
    # Quick return to 0.40 without crossing 0.06 threshold
    evt = detector.update(Point3D(x=0.5, y=0.40), timestamp_ms=40, active_chord_id="c-major")
    assert evt is None
    assert detector.state == MotionState.IDLE


def test_cooldown_and_re_arming(detector):
    # 1. Trigger downstroke
    detector.update(Point3D(x=0.5, y=0.40), timestamp_ms=0, active_chord_id="c-major")
    detector.update(Point3D(x=0.5, y=0.45), timestamp_ms=40, active_chord_id="c-major")
    evt = detector.update(Point3D(x=0.5, y=0.50), timestamp_ms=80, active_chord_id="c-major")
    assert evt is not None
    assert detector.state == MotionState.COOLDOWN

    # 2. Movement during cooldown (< 100ms after accept at t=80) is ignored
    evt_cool = detector.update(Point3D(x=0.5, y=0.45), timestamp_ms=120, active_chord_id="c-major")
    assert evt_cool is None
    assert detector.state == MotionState.COOLDOWN

    # 3. Cooldown expires at t=190 (> 80 + 100 = 180), enters RE_ARMING
    detector.update(Point3D(x=0.5, y=0.45), timestamp_ms=190, active_chord_id="c-major")
    assert detector.state == MotionState.RE_ARMING

    # 4. Stationary frame re-arms to IDLE
    detector.update(Point3D(x=0.5, y=0.45), timestamp_ms=230, active_chord_id="c-major")
    assert detector.state == MotionState.IDLE

    # 5. Now next upstroke triggers clean event
    detector.update(Point3D(x=0.5, y=0.38), timestamp_ms=270, active_chord_id="e-minor")
    evt_next = detector.update(Point3D(x=0.5, y=0.30), timestamp_ms=310, active_chord_id="e-minor")
    assert evt_next is not None
    assert evt_next.direction == "up"
    assert evt_next.active_chord_id == "e-minor"


def test_tracking_loss_resets(detector):
    detector.update(Point3D(x=0.5, y=0.40), timestamp_ms=0, active_chord_id="c-major")
    detector.update(Point3D(x=0.5, y=0.45), timestamp_ms=40, active_chord_id="c-major")
    assert detector.state == MotionState.DOWNSTROKE_TRACKING

    # Hand disappears
    evt = detector.update(None, timestamp_ms=80, active_chord_id="c-major")
    assert evt is None
    assert detector.state == MotionState.IDLE

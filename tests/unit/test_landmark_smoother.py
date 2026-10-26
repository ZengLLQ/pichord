from app.vision.landmark_smoother import LandmarkSmoother
from app.vision.models import Point3D


def test_smoother_initialization():
    smoother = LandmarkSmoother(alpha=0.5)
    pts = [Point3D(x=0.5, y=0.5, z=0.0)]
    smoothed = smoother.smooth("chord", pts, timestamp_ms=100)
    # First frame initializes without distortion
    assert smoothed[0].x == 0.5
    assert smoothed[0].y == 0.5


def test_smoother_dampens_noise():
    smoother = LandmarkSmoother(alpha=0.5)
    # Frame 1
    smoother.smooth("chord", [Point3D(x=0.5, y=0.5)], timestamp_ms=100)
    # Frame 2 with jump to 0.7
    res = smoother.smooth("chord", [Point3D(x=0.7, y=0.5)], timestamp_ms=130)

    # Expected: 0.5 * 0.7 + 0.5 * 0.5 = 0.6
    assert abs(res[0].x - 0.6) < 1e-4


def test_smoother_resets_on_time_gap():
    smoother = LandmarkSmoother(alpha=0.5, max_gap_ms=200)
    smoother.smooth("chord", [Point3D(x=0.2, y=0.2)], timestamp_ms=100)

    # Frame 2 after 500ms gap (> max_gap_ms 200)
    res = smoother.smooth("chord", [Point3D(x=0.8, y=0.8)], timestamp_ms=600)
    # Should reset to new point directly rather than blending stale 0.2
    assert res[0].x == 0.8
    assert res[0].y == 0.8


def test_smoother_reset_all():
    smoother = LandmarkSmoother(alpha=0.5)
    smoother.smooth("chord", [Point3D(x=0.2, y=0.2)], timestamp_ms=100)
    smoother.reset_all()

    # Next frame should behave as fresh initial frame
    res = smoother.smooth("chord", [Point3D(x=0.9, y=0.9)], timestamp_ms=120)
    assert res[0].x == 0.9

import math
from typing import List

from app.vision.models import LandmarkIndex as LIdx
from app.vision.models import Point3D


def create_mock_hand(
    thumb: bool = False,
    index: bool = False,
    middle: bool = False,
    ring: bool = False,
    pinky: bool = False,
    wrist_x: float = 0.5,
    wrist_y: float = 0.8,
    angle_deg: float = 0.0,
) -> List[Point3D]:
    """Generates a geometrically realistic 21-landmark mock hand with specified finger extensions."""
    # Base canonical coordinates relative to wrist at (0, 0)
    pts = [Point3D(x=0.0, y=0.0, z=0.0) for _ in range(21)]

    # Wrist
    pts[LIdx.WRIST] = Point3D(x=0.0, y=0.0, z=0.0)

    # Scale: wrist to middle MCP = 0.20
    # MCPs
    pts[LIdx.THUMB_CMC] = Point3D(x=-0.05, y=-0.06, z=0.0)
    pts[LIdx.THUMB_MCP] = Point3D(x=-0.09, y=-0.11, z=0.0)
    pts[LIdx.INDEX_MCP] = Point3D(x=-0.05, y=-0.19, z=0.0)
    pts[LIdx.MIDDLE_MCP] = Point3D(x=0.0, y=-0.21, z=0.0)
    pts[LIdx.RING_MCP] = Point3D(x=0.05, y=-0.19, z=0.0)
    pts[LIdx.PINKY_MCP] = Point3D(x=0.09, y=-0.16, z=0.0)

    # Thumb
    if thumb:
        # Abducted and extended outward
        pts[LIdx.THUMB_IP] = Point3D(x=-0.14, y=-0.15, z=0.0)
        pts[LIdx.THUMB_TIP] = Point3D(x=-0.19, y=-0.19, z=0.0)
    else:
        # Folded tucked into palm near index MCP
        pts[LIdx.THUMB_IP] = Point3D(x=-0.07, y=-0.13, z=0.01)
        pts[LIdx.THUMB_TIP] = Point3D(x=-0.04, y=-0.16, z=0.02)

    # Index
    if index:
        pts[LIdx.INDEX_PIP] = Point3D(x=-0.05, y=-0.28, z=0.0)
        pts[LIdx.INDEX_DIP] = Point3D(x=-0.05, y=-0.35, z=0.0)
        pts[LIdx.INDEX_TIP] = Point3D(x=-0.05, y=-0.41, z=0.0)
    else:
        pts[LIdx.INDEX_PIP] = Point3D(x=-0.05, y=-0.23, z=-0.02)
        pts[LIdx.INDEX_DIP] = Point3D(x=-0.05, y=-0.20, z=-0.04)
        pts[LIdx.INDEX_TIP] = Point3D(x=-0.05, y=-0.17, z=-0.05)

    # Middle
    if middle:
        pts[LIdx.MIDDLE_PIP] = Point3D(x=0.0, y=-0.31, z=0.0)
        pts[LIdx.MIDDLE_DIP] = Point3D(x=0.0, y=-0.39, z=0.0)
        pts[LIdx.MIDDLE_TIP] = Point3D(x=0.0, y=-0.46, z=0.0)
    else:
        pts[LIdx.MIDDLE_PIP] = Point3D(x=0.0, y=-0.25, z=-0.02)
        pts[LIdx.MIDDLE_DIP] = Point3D(x=0.0, y=-0.22, z=-0.04)
        pts[LIdx.MIDDLE_TIP] = Point3D(x=0.0, y=-0.19, z=-0.05)

    # Ring
    if ring:
        pts[LIdx.RING_PIP] = Point3D(x=0.05, y=-0.28, z=0.0)
        pts[LIdx.RING_DIP] = Point3D(x=0.05, y=-0.35, z=0.0)
        pts[LIdx.RING_TIP] = Point3D(x=0.05, y=-0.41, z=0.0)
    else:
        pts[LIdx.RING_PIP] = Point3D(x=0.05, y=-0.23, z=-0.02)
        pts[LIdx.RING_DIP] = Point3D(x=0.05, y=-0.20, z=-0.04)
        pts[LIdx.RING_TIP] = Point3D(x=0.05, y=-0.17, z=-0.05)

    # Pinky
    if pinky:
        pts[LIdx.PINKY_PIP] = Point3D(x=0.09, y=-0.23, z=0.0)
        pts[LIdx.PINKY_DIP] = Point3D(x=0.09, y=-0.29, z=0.0)
        pts[LIdx.PINKY_TIP] = Point3D(x=0.09, y=-0.34, z=0.0)
    else:
        pts[LIdx.PINKY_PIP] = Point3D(x=0.09, y=-0.19, z=-0.02)
        pts[LIdx.PINKY_DIP] = Point3D(x=0.09, y=-0.17, z=-0.04)
        pts[LIdx.PINKY_TIP] = Point3D(x=0.09, y=-0.15, z=-0.05)

    # Apply rotation around wrist if specified
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    transformed: List[Point3D] = []
    for p in pts:
        rx = p.x * cos_a - p.y * sin_a + wrist_x
        ry = p.x * sin_a + p.y * cos_a + wrist_y
        transformed.append(Point3D(x=rx, y=ry, z=p.z))

    return transformed

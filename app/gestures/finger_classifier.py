import math
from typing import List

from pydantic import BaseModel

from app.vision.models import LandmarkIndex as LIdx
from app.vision.models import Point3D


class FingerClassificationResult(BaseModel):
    thumb: bool
    index: bool
    middle: bool
    ring: bool
    pinky: bool
    extended_count: int
    confidence: float

    def as_list(self) -> List[bool]:
        return [self.thumb, self.index, self.middle, self.ring, self.pinky]


class FingerClassifier:
    """Robust geometric classifier to detect whether each finger is extended or folded."""

    def classify(
        self, landmarks: List[Point3D], handedness: str = "Right"
    ) -> FingerClassificationResult:
        if len(landmarks) < 21:
            return FingerClassificationResult(
                thumb=False,
                index=False,
                middle=False,
                ring=False,
                pinky=False,
                extended_count=0,
                confidence=0.0,
            )

        wrist = landmarks[LIdx.WRIST]
        middle_mcp = landmarks[LIdx.MIDDLE_MCP]
        index_mcp = landmarks[LIdx.INDEX_MCP]
        pinky_mcp = landmarks[LIdx.PINKY_MCP]

        # Invariant hand scale: distance between wrist and middle MCP
        scale = wrist.distance_to(middle_mcp)
        if scale < 1e-4:
            return FingerClassificationResult(
                thumb=False,
                index=False,
                middle=False,
                ring=False,
                pinky=False,
                extended_count=0,
                confidence=0.0,
            )

        # Classify the 4 long fingers
        index_ext, index_conf = self._classify_long_finger(
            landmarks, LIdx.INDEX_MCP, LIdx.INDEX_PIP, LIdx.INDEX_DIP, LIdx.INDEX_TIP, scale, wrist
        )
        middle_ext, middle_conf = self._classify_long_finger(
            landmarks,
            LIdx.MIDDLE_MCP,
            LIdx.MIDDLE_PIP,
            LIdx.MIDDLE_DIP,
            LIdx.MIDDLE_TIP,
            scale,
            wrist,
        )
        ring_ext, ring_conf = self._classify_long_finger(
            landmarks, LIdx.RING_MCP, LIdx.RING_PIP, LIdx.RING_DIP, LIdx.RING_TIP, scale, wrist
        )
        pinky_ext, pinky_conf = self._classify_long_finger(
            landmarks, LIdx.PINKY_MCP, LIdx.PINKY_PIP, LIdx.PINKY_DIP, LIdx.PINKY_TIP, scale, wrist
        )

        # Classify the thumb
        thumb_ext, thumb_conf = self._classify_thumb(
            landmarks, scale, wrist, index_mcp, pinky_mcp, handedness
        )

        fingers = [thumb_ext, index_ext, middle_ext, ring_ext, pinky_ext]
        count = sum(1 for f in fingers if f)
        avg_conf = (thumb_conf + index_conf + middle_conf + ring_conf + pinky_conf) / 5.0

        return FingerClassificationResult(
            thumb=thumb_ext,
            index=index_ext,
            middle=middle_ext,
            ring=ring_ext,
            pinky=pinky_ext,
            extended_count=count,
            confidence=round(avg_conf, 3),
        )

    def _classify_long_finger(
        self,
        landmarks: List[Point3D],
        mcp_idx: int,
        pip_idx: int,
        dip_idx: int,
        tip_idx: int,
        scale: float,
        wrist: Point3D,
    ) -> tuple[bool, float]:
        mcp = landmarks[mcp_idx]
        pip = landmarks[pip_idx]
        dip = landmarks[dip_idx]
        tip = landmarks[tip_idx]

        dist_wrist_tip = wrist.distance_to(tip)
        dist_wrist_pip = wrist.distance_to(pip)
        dist_wrist_dip = wrist.distance_to(dip)
        dist_mcp_tip = mcp.distance_to(tip)
        dist_mcp_pip = mcp.distance_to(pip)

        # Check 1: Tip is further from wrist than PIP and DIP
        tip_past_pip = dist_wrist_tip > dist_wrist_pip * 1.08
        tip_past_dip = dist_wrist_tip > dist_wrist_dip * 1.02

        # Check 2: Extension ratio from MCP
        extended_ratio = dist_mcp_tip > dist_mcp_pip * 1.35

        # Check 3: Vector straightness between (PIP - MCP) and (TIP - PIP)
        v1 = (pip.x - mcp.x, pip.y - mcp.y, pip.z - mcp.z)
        v2 = (tip.x - pip.x, tip.y - pip.y, tip.z - pip.z)
        len1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2)
        len2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2 + v2[2] ** 2)

        cosine = 1.0
        if len1 > 1e-4 and len2 > 1e-4:
            cosine = (v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]) / (len1 * len2)

        straight = cosine > 0.45

        # Combined decision
        is_extended = tip_past_pip and (tip_past_dip or extended_ratio) and straight
        conf = 0.9 if is_extended else 0.85
        if not is_extended and tip_past_pip:
            conf = 0.65  # borderline case

        return is_extended, conf

    def _classify_thumb(
        self,
        landmarks: List[Point3D],
        scale: float,
        wrist: Point3D,
        index_mcp: Point3D,
        pinky_mcp: Point3D,
        handedness: str,
    ) -> tuple[bool, float]:
        thumb_tip = landmarks[LIdx.THUMB_TIP]
        thumb_ip = landmarks[LIdx.THUMB_IP]
        thumb_mcp = landmarks[LIdx.THUMB_MCP]

        dist_tip_index_mcp = thumb_tip.distance_to(index_mcp)
        dist_tip_pinky_mcp = thumb_tip.distance_to(pinky_mcp)
        dist_tip_wrist = thumb_tip.distance_to(wrist)
        dist_ip_wrist = thumb_ip.distance_to(wrist)
        dist_tip_mcp = thumb_tip.distance_to(thumb_mcp)
        dist_ip_mcp = thumb_ip.distance_to(thumb_mcp)

        # Thumb extension primarily involves abduction from the palm
        abducted = (dist_tip_index_mcp > 0.52 * scale) and (dist_tip_pinky_mcp > 0.65 * scale)
        extended_from_joint = dist_tip_mcp > dist_ip_mcp * 1.15
        tip_past_ip = dist_tip_wrist > dist_ip_wrist * 1.02

        is_extended = abducted and (extended_from_joint or tip_past_ip)
        conf = 0.85 if is_extended else 0.80
        return is_extended, conf

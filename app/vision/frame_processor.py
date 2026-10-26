import time
from typing import Optional

import cv2
import numpy as np
from pydantic import BaseModel

from app.gestures.chord_mappings import ChordMappings
from app.gestures.finger_classifier import FingerClassifier
from app.gestures.gesture_classifier import GestureClassifier
from app.schemas.chords import ChordDefinition
from app.schemas.messages import HandRoleState
from app.strumming.strum_detector import StrumDetector, StrumEvent
from app.vision.hand_assignment import HandAssignment
from app.vision.hand_tracker import HandTracker
from app.vision.landmark_smoother import LandmarkSmoother
from app.vision.models import LandmarkIndex as LIdx


class FrameProcessingResult(BaseModel):
    seq: int
    active_chord_id: str
    chord_changed: bool
    new_chord: Optional[ChordDefinition] = None
    strum_event: Optional[StrumEvent] = None
    chord_hand_state: Optional[HandRoleState] = None
    strum_hand_state: Optional[HandRoleState] = None
    hands_detected: int = 0
    latency_ms: float = 0.0


class FrameProcessor:
    """End-to-end vision frame pipeline."""

    def __init__(
        self,
        hand_tracker: HandTracker,
        chord_mappings: ChordMappings,
        chord_hand: str = "Left",
        strum_hand: str = "Right",
        smoothing_alpha: float = 0.65,
        gesture_stability_ms: int = 140,
        strum_min_speed: float = 0.70,
        strum_min_displacement: float = 0.065,
        strum_cooldown_ms: int = 120,
    ):
        self.hand_tracker = hand_tracker
        self.chord_mappings = chord_mappings

        self.smoother = LandmarkSmoother(alpha=smoothing_alpha)
        self.hand_assignment = HandAssignment(chord_hand=chord_hand, strum_hand=strum_hand)
        self.finger_classifier = FingerClassifier()
        self.gesture_classifier = GestureClassifier(
            chord_mappings, stability_ms=gesture_stability_ms
        )
        self.strum_detector = StrumDetector(
            min_speed=strum_min_speed,
            min_displacement=strum_min_displacement,
            cooldown_ms=strum_cooldown_ms,
        )

    def process_frame(
        self, jpeg_bytes: bytes, seq: int, timestamp_ms: int
    ) -> FrameProcessingResult:
        start_time = time.perf_counter()

        # 1. Decode JPEG
        np_arr = np.frombuffer(jpeg_bytes, np.uint8)
        bgr_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if bgr_image is None:
            raise ValueError("Failed to decode JPEG frame.")

        # 2. Convert to RGB
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

        # 3. Detect hands using MediaPipe HandTracker
        raw_hands = self.hand_tracker.detect(rgb_image, timestamp_ms)
        hands_detected = len(raw_hands)

        # 4. Role assignment
        assigned_chord_hand, assigned_strum_hand = self.hand_assignment.assign_roles(raw_hands)

        # 5. Process Chord Hand
        chord_hand_state: Optional[HandRoleState] = None
        chord_changed = False
        new_chord: Optional[ChordDefinition] = None

        if assigned_chord_hand:
            # Smooth landmarks
            smoothed_lms = self.smoother.smooth(
                "chord", assigned_chord_hand.landmarks, timestamp_ms
            )
            finger_res = self.finger_classifier.classify(
                smoothed_lms, assigned_chord_hand.handedness
            )
            active_chord, chord_changed = self.gesture_classifier.update(finger_res, timestamp_ms)
            if chord_changed:
                new_chord = active_chord

            wrist = smoothed_lms[LIdx.WRIST]
            chord_hand_state = HandRoleState(
                role="chord",
                handedness=assigned_chord_hand.handedness,
                wrist_x=round(wrist.x, 4),
                wrist_y=round(wrist.y, 4),
                confidence=round(assigned_chord_hand.score, 3),
                finger_count=finger_res.extended_count,
                extended_fingers=finger_res.as_list(),
                landmarks=[[round(p.x, 3), round(p.y, 3), round(p.z, 3)] for p in smoothed_lms],
            )
        else:
            # Retain current chord even if hand temporarily out of frame
            self.smoother.reset_hand("chord")
            active_chord, _ = self.gesture_classifier.update(None, timestamp_ms)

        current_active_chord_id = (
            self.gesture_classifier.current_chord.id
            if self.gesture_classifier.current_chord
            else "c-major"
        )

        # 6. Process Strum Hand
        strum_hand_state: Optional[HandRoleState] = None
        strum_event: Optional[StrumEvent] = None

        if assigned_strum_hand:
            smoothed_strum_lms = self.smoother.smooth(
                "strum", assigned_strum_hand.landmarks, timestamp_ms
            )
            wrist_strum = smoothed_strum_lms[LIdx.WRIST]

            strum_event = self.strum_detector.update(
                wrist=wrist_strum,
                timestamp_ms=timestamp_ms,
                active_chord_id=current_active_chord_id,
                hand_confidence=assigned_strum_hand.score,
            )

            strum_hand_state = HandRoleState(
                role="strum",
                handedness=assigned_strum_hand.handedness,
                wrist_x=round(wrist_strum.x, 4),
                wrist_y=round(wrist_strum.y, 4),
                confidence=round(assigned_strum_hand.score, 3),
                landmarks=[
                    [round(p.x, 3), round(p.y, 3), round(p.z, 3)] for p in smoothed_strum_lms
                ],
            )
        else:
            self.smoother.reset_hand("strum")
            self.strum_detector.reset()

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return FrameProcessingResult(
            seq=seq,
            active_chord_id=current_active_chord_id,
            chord_changed=chord_changed,
            new_chord=new_chord,
            strum_event=strum_event,
            chord_hand_state=chord_hand_state,
            strum_hand_state=strum_hand_state,
            hands_detected=hands_detected,
            latency_ms=round(latency_ms, 2),
        )

    def reset(self) -> None:
        self.smoother.reset_all()
        self.hand_assignment.reset()
        self.gesture_classifier.reset()
        self.strum_detector.reset()

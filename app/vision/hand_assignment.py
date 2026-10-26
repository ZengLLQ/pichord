from typing import List, Optional, Tuple

from app.vision.models import DetectedHand
from app.vision.models import LandmarkIndex as LIdx


class HandAssignment:
    """Assigns detected hands to Chord and Strum roles reliably across frames."""

    def __init__(self, chord_hand: str = "Left", strum_hand: str = "Right", mirrored: bool = True):
        self.chord_hand_preference = chord_hand  # "Left" or "Right" (anatomical)
        self.strum_hand_preference = strum_hand  # "Right" or "Left"
        self.mirrored = mirrored

        # Tracked centers for role consistency
        self._last_chord_wrist_x: Optional[float] = None
        self._last_strum_wrist_x: Optional[float] = None

    def configure_roles(self, chord_hand: str, strum_hand: str) -> None:
        self.chord_hand_preference = chord_hand
        self.strum_hand_preference = strum_hand
        self.reset()

    def reset(self) -> None:
        self._last_chord_wrist_x = None
        self._last_strum_wrist_x = None

    def assign_roles(
        self, hands: List[DetectedHand]
    ) -> Tuple[Optional[DetectedHand], Optional[DetectedHand]]:
        """Assign hands to (chord_hand, strum_hand).

        Takes 0, 1, or 2 detected hands.
        """
        if not hands:
            return None, None

        if len(hands) == 1:
            hand = hands[0]
            # If only 1 hand is present:
            # Check handedness label or spatial position
            wrist_x = hand.landmarks[LIdx.WRIST].x

            # Check if this matches chord preference
            matches_chord = hand.handedness == self.chord_hand_preference

            # Proximity fallback if we had previous tracks
            if self._last_chord_wrist_x is not None and self._last_strum_wrist_x is not None:
                dist_chord = abs(wrist_x - self._last_chord_wrist_x)
                dist_strum = abs(wrist_x - self._last_strum_wrist_x)
                if dist_chord < dist_strum:
                    hand.role = "chord"
                    self._last_chord_wrist_x = wrist_x
                    return hand, None
                else:
                    hand.role = "strum"
                    self._last_strum_wrist_x = wrist_x
                    return None, hand

            if matches_chord:
                hand.role = "chord"
                self._last_chord_wrist_x = wrist_x
                return hand, None
            else:
                hand.role = "strum"
                self._last_strum_wrist_x = wrist_x
                return None, hand

        # If 2 hands are present:
        hand_a, hand_b = hands[0], hands[1]
        ax = hand_a.landmarks[LIdx.WRIST].x
        bx = hand_b.landmarks[LIdx.WRIST].x

        # Identify which is on the left and right side of the screen
        left_screen_hand = hand_a if ax < bx else hand_b
        right_screen_hand = hand_b if ax < bx else hand_a

        # If user plays standard (Left=Chord, Right=Strum) in mirrored camera:
        # Physical left hand is on left side of screen
        # Physical right hand is on right side of screen
        if self.chord_hand_preference == "Left":
            chord_hand = left_screen_hand
            strum_hand = right_screen_hand
        else:
            chord_hand = right_screen_hand
            strum_hand = left_screen_hand

        chord_hand.role = "chord"
        strum_hand.role = "strum"

        self._last_chord_wrist_x = chord_hand.landmarks[LIdx.WRIST].x
        self._last_strum_wrist_x = strum_hand.landmarks[LIdx.WRIST].x

        return chord_hand, strum_hand

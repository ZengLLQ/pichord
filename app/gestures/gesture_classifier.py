from typing import Optional, Tuple

from app.gestures.chord_mappings import ChordMappings
from app.gestures.finger_classifier import FingerClassificationResult
from app.schemas.chords import ChordDefinition


class GestureClassifier:
    """Applies temporal stability / hysteresis to finger count to produce stable chords."""

    def __init__(self, chord_mappings: ChordMappings, stability_ms: int = 140):
        self.chord_mappings = chord_mappings
        self.stability_ms = stability_ms

        self.current_chord: Optional[ChordDefinition] = chord_mappings.get_chord_for_fingers(
            1
        )  # Default: C Major
        self.current_finger_count: int = 1

        self.candidate_finger_count: Optional[int] = None
        self.candidate_since_ms: int = 0

    def set_stability_ms(self, stability_ms: int) -> None:
        self.stability_ms = max(50, min(stability_ms, 500))

    def update(
        self, finger_result: Optional[FingerClassificationResult], timestamp_ms: int
    ) -> Tuple[Optional[ChordDefinition], bool]:
        """Update with a new frame classification.

        Returns:
            Tuple[Optional[ChordDefinition], bool]: (active_chord, has_chord_changed)
        """
        if finger_result is None or finger_result.extended_count == 0:
            # When tracking is temporarily lost or all fingers folded, preserve last stable chord
            return self.current_chord, False

        count = finger_result.extended_count

        # If detected count is the same as current stable count, reset candidate
        if count == self.current_finger_count:
            self.candidate_finger_count = None
            return self.current_chord, False

        # If this is a new candidate, start candidate timer
        if count != self.candidate_finger_count:
            self.candidate_finger_count = count
            self.candidate_since_ms = timestamp_ms
            return self.current_chord, False

        # If candidate has persisted for >= stability_ms, accept chord switch
        elapsed = timestamp_ms - self.candidate_since_ms
        if elapsed >= self.stability_ms:
            new_chord = self.chord_mappings.get_chord_for_fingers(count)
            if new_chord and (self.current_chord is None or new_chord.id != self.current_chord.id):
                self.current_chord = new_chord
                self.current_finger_count = count
                self.candidate_finger_count = None
                return self.current_chord, True

        return self.current_chord, False

    def reset(self) -> None:
        self.candidate_finger_count = None
        self.candidate_since_ms = 0

from typing import Dict, List, Optional

from app.schemas.chords import DEFAULT_CHORDS, ChordDefinition


class ChordMappings:
    """Manages chord definitions and mappings from finger count to chord."""

    def __init__(self, custom_mapping: Optional[Dict[str, str]] = None):
        self._chords_by_id: Dict[str, ChordDefinition] = {
            chord.id: chord for chord in DEFAULT_CHORDS
        }
        self._mapping: Dict[int, str] = {
            1: "c-major",
            2: "g-major",
            3: "d-major",
            4: "e-minor",
            5: "a-minor",
        }
        if custom_mapping:
            self.apply_custom_mapping(custom_mapping)

    @property
    def all_chords(self) -> List[ChordDefinition]:
        return list(self._chords_by_id.values())

    def get_chord_by_id(self, chord_id: str) -> Optional[ChordDefinition]:
        return self._chords_by_id.get(chord_id)

    def get_chord_for_fingers(self, finger_count: int) -> Optional[ChordDefinition]:
        chord_id = self._mapping.get(finger_count)
        if chord_id:
            return self._chords_by_id.get(chord_id)
        return None

    def apply_custom_mapping(self, mapping_dict: Dict[str, str]) -> bool:
        """Validate and apply a custom finger-count -> chord_id mapping."""
        validated: Dict[int, str] = {}
        for k, v in mapping_dict.items():
            try:
                count = int(k)
            except ValueError:
                return False
            if count < 1 or count > 5:
                return False
            if v not in self._chords_by_id:
                return False
            validated[count] = v

        # Update valid keys
        self._mapping.update(validated)
        return True

    def reset_to_defaults(self) -> None:
        self._mapping = {
            1: "c-major",
            2: "g-major",
            3: "d-major",
            4: "e-minor",
            5: "a-minor",
        }

    def get_current_mapping(self) -> Dict[str, str]:
        return {str(k): v for k, v in sorted(self._mapping.items())}

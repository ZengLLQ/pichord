import pytest

from app.gestures.chord_mappings import ChordMappings


@pytest.fixture
def mappings():
    return ChordMappings()


def test_default_mappings(mappings):
    c1 = mappings.get_chord_for_fingers(1)
    assert c1 is not None
    assert c1.id == "c-major"

    c2 = mappings.get_chord_for_fingers(2)
    assert c2 is not None
    assert c2.id == "g-major"

    c3 = mappings.get_chord_for_fingers(3)
    assert c3 is not None
    assert c3.id == "d-major"

    c4 = mappings.get_chord_for_fingers(4)
    assert c4 is not None
    assert c4.id == "e-minor"

    c5 = mappings.get_chord_for_fingers(5)
    assert c5 is not None
    assert c5.id == "a-minor"


def test_unknown_gesture_counts(mappings):
    assert mappings.get_chord_for_fingers(0) is None
    assert mappings.get_chord_for_fingers(6) is None
    assert mappings.get_chord_for_fingers(-1) is None


def test_custom_mapping_application(mappings):
    custom = {"1": "a-minor", "2": "c-major"}
    success = mappings.apply_custom_mapping(custom)
    assert success is True
    assert mappings.get_chord_for_fingers(1).id == "a-minor"
    assert mappings.get_chord_for_fingers(2).id == "c-major"
    # Unchanged finger 3
    assert mappings.get_chord_for_fingers(3).id == "d-major"


def test_custom_mapping_invalid_chord_id(mappings):
    custom = {"1": "non-existent-chord"}
    success = mappings.apply_custom_mapping(custom)
    assert success is False
    # Should not have changed
    assert mappings.get_chord_for_fingers(1).id == "c-major"


def test_custom_mapping_invalid_finger_count(mappings):
    custom = {"9": "c-major"}
    success = mappings.apply_custom_mapping(custom)
    assert success is False


def test_reset_to_defaults(mappings):
    mappings.apply_custom_mapping({"1": "g-major"})
    assert mappings.get_chord_for_fingers(1).id == "g-major"

    mappings.reset_to_defaults()
    assert mappings.get_chord_for_fingers(1).id == "c-major"

import pytest

from app.gestures.finger_classifier import FingerClassifier
from tests.fixtures.mock_landmarks import create_mock_hand


@pytest.fixture
def classifier():
    return FingerClassifier()


def test_classify_one_finger_index_only(classifier):
    # 1 finger: index extended
    hand = create_mock_hand(thumb=False, index=True, middle=False, ring=False, pinky=False)
    res = classifier.classify(hand)
    assert res.index is True
    assert res.middle is False
    assert res.ring is False
    assert res.pinky is False
    assert res.extended_count == 1


def test_classify_two_fingers_peace(classifier):
    # 2 fingers: index and middle extended
    hand = create_mock_hand(thumb=False, index=True, middle=True, ring=False, pinky=False)
    res = classifier.classify(hand)
    assert res.index is True
    assert res.middle is True
    assert res.ring is False
    assert res.pinky is False
    assert res.extended_count == 2


def test_classify_three_fingers(classifier):
    # 3 fingers: index, middle, ring extended
    hand = create_mock_hand(thumb=False, index=True, middle=True, ring=True, pinky=False)
    res = classifier.classify(hand)
    assert res.index is True
    assert res.middle is True
    assert res.ring is True
    assert res.pinky is False
    assert res.extended_count == 3


def test_classify_four_fingers(classifier):
    # 4 fingers: index, middle, ring, pinky extended
    hand = create_mock_hand(thumb=False, index=True, middle=True, ring=True, pinky=True)
    res = classifier.classify(hand)
    assert res.index is True
    assert res.middle is True
    assert res.ring is True
    assert res.pinky is True
    assert res.thumb is False
    assert res.extended_count == 4


def test_classify_five_fingers_open_palm(classifier):
    # 5 fingers: all extended
    hand = create_mock_hand(thumb=True, index=True, middle=True, ring=True, pinky=True)
    res = classifier.classify(hand)
    assert res.thumb is True
    assert res.index is True
    assert res.middle is True
    assert res.ring is True
    assert res.pinky is True
    assert res.extended_count == 5


def test_classify_folded_fist(classifier):
    # Closed fist
    hand = create_mock_hand(thumb=False, index=False, middle=False, ring=False, pinky=False)
    res = classifier.classify(hand)
    assert res.extended_count == 0


def test_classify_different_wrist_orientations(classifier):
    # Hand rotated 30 degrees clockwise
    hand_rot_30 = create_mock_hand(
        thumb=False, index=True, middle=True, ring=False, pinky=False, angle_deg=30.0
    )
    res_30 = classifier.classify(hand_rot_30)
    assert res_30.index is True
    assert res_30.middle is True
    assert res_30.extended_count == 2

    # Hand rotated 30 degrees counter-clockwise
    hand_rot_neg30 = create_mock_hand(
        thumb=False, index=True, middle=True, ring=False, pinky=False, angle_deg=-30.0
    )
    res_neg30 = classifier.classify(hand_rot_neg30)
    assert res_neg30.index is True
    assert res_neg30.middle is True
    assert res_neg30.extended_count == 2


def test_classify_invalid_or_missing_landmarks(classifier):
    # Empty list
    res = classifier.classify([])
    assert res.extended_count == 0
    assert res.confidence == 0.0

    # Incomplete list (< 21 points)
    hand = create_mock_hand()[:15]
    res2 = classifier.classify(hand)
    assert res2.extended_count == 0
    assert res2.confidence == 0.0

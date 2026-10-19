import numpy as np
import pytest

from sim_designer.models import FaceBox, Landmark
from sim_designer.vision.face_detector import FaceDetector
from sim_designer.vision.landmarks import UnavailableLandmarkProvider


def test_face_detector_accepts_rgb_and_returns_no_face_for_blank_image() -> None:
    detector = FaceDetector()
    assert detector.detect(np.zeros((240, 320, 3), dtype=np.uint8)) == []


def test_face_detector_rejects_invalid_array() -> None:
    with pytest.raises(ValueError):
        FaceDetector().detect(np.zeros((20, 20), dtype=np.uint8))


def test_unavailable_landmark_provider_explains_degraded_mode() -> None:
    provider = UnavailableLandmarkProvider("optional backend absent")
    result = provider.detect(np.zeros((30, 30, 3), dtype=np.uint8), FaceBox(1, 1, 10, 10))
    assert result.points == ()
    assert result.message == "optional backend absent"


def test_landmark_dataclass_keeps_normalized_values() -> None:
    point = Landmark(0.25, 0.75, 1.0)
    assert (point.x, point.y, point.confidence) == (0.25, 0.75, 1.0)

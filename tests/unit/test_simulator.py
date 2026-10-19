"""Synthetic ground truth, renderer, extraction, and adapter safety contracts."""

import numpy as np
import pytest
from pydantic import ValidationError

from sim_designer.adapters.base import (AdapterError, CASState, DragAction, FEATURE_NAMES,
                                        FaceParameters, StateResult)
from sim_designer.adapters.fake import FakeCASAdapter
from sim_designer.adapters.real import RealCASAdapter
from sim_designer.capture.cas_detector import detect_simulator_state
from sim_designer.models import Landmark
from sim_designer.simulator.geometry import face_landmarks, random_face
from sim_designer.simulator.renderer import control_point, render_face
from sim_designer.vision.features import extract_features
from sim_designer.vision.similarity import compare_faces


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_model_values(value: float) -> None:
    with pytest.raises(ValidationError):
        FaceParameters(face_width=value)


@pytest.mark.parametrize("seed", range(5))
def test_landmark_extraction_roundtrip_and_scale_translation(seed: int) -> None:
    face = random_face(seed)
    points = face_landmarks(face)
    assert all(0 <= p.x <= 1 and 0 <= p.y <= 1 for p in points.values())
    transformed = {name: Landmark(p.x * 0.7 + 0.1, p.y * 0.6 + 0.2, p.confidence)
                   for name, p in points.items()}
    assert extract_features(points).model_dump() == pytest.approx(face.model_dump())
    assert extract_features(transformed).model_dump() == pytest.approx(face.model_dump())


@pytest.mark.parametrize("feature", FEATURE_NAMES)
def test_each_parameter_changes_render_and_extracted_feature(feature: str) -> None:
    baseline = FaceParameters()
    changed = FaceParameters(**{feature: 0.9})
    assert not np.array_equal(render_face(baseline, size=256), render_face(changed, size=256))
    result = extract_features(face_landmarks(changed))
    assert getattr(result, feature) == pytest.approx(0.9)
    for other in FEATURE_NAMES:
        if other != feature:
            assert getattr(result, other) == pytest.approx(0.5)


def test_missing_occluded_and_degenerate_landmarks() -> None:
    points = face_landmarks(FaceParameters())
    with pytest.raises(ValueError, match="Missing"):
        extract_features({})
    points["nose_tip"] = Landmark(0.5, 0.5, 0.1)
    with pytest.raises(ValueError, match="confidence"):
        extract_features(points)
    points = face_landmarks(FaceParameters())
    points["unit_x"] = points["origin"]
    with pytest.raises(ValueError, match="Degenerate"):
        extract_features(points)


@pytest.mark.parametrize("state", list(CASState))
def test_simulator_state_detection(state: CASState) -> None:
    image = render_face(FaceParameters(), state, 128)
    assert detect_simulator_state(image).state == state
    image[:4, :4] = 0
    assert detect_simulator_state(image).state == CASState.UNKNOWN


def test_drag_checkpoint_and_state_rejection() -> None:
    adapter = FakeCASAdapter(size=128)
    checkpoint = adapter.create_checkpoint()
    image = adapter.capture().image
    action = DragAction(feature="nose_width", start=control_point("nose_width"), dx=0.03)
    adapter.execute_drag(action)
    assert adapter.face.nose_width == pytest.approx(0.56)
    adapter.state = CASState.POPUP
    with pytest.raises(AdapterError, match="recognized CAS"):
        adapter.execute_drag(action)
    adapter.restore_checkpoint(checkpoint)
    assert adapter.face == checkpoint.face
    assert adapter.state == checkpoint.state
    assert np.array_equal(adapter.capture().image, image)
    with pytest.raises(AdapterError) as error:
        adapter.restore_checkpoint(checkpoint.model_copy(update={"backend": "real"}))
    assert error.value.code == "CHECKPOINT_MISMATCH"


def test_similarity_groups_weights_and_signed_errors() -> None:
    current = FaceParameters()
    target = FaceParameters(nose_width=0.9)
    result = compare_faces(current, target)
    assert result.per_feature["nose_width"] == pytest.approx(0.4)
    assert result.per_group["nose"] == pytest.approx(0.2)
    assert result.error == pytest.approx(0.04)
    assert compare_faces(current, current).score == 1
    weights = {"face_outline": 1, "eyes": 1, "nose": 0, "mouth": 1, "jaw_chin": 1}
    assert compare_faces(current, target, weights).score == 1
    with pytest.raises(ValueError):
        compare_faces(current, target, {k: 0 for k in weights})


def test_real_adapter_never_succeeds_silently() -> None:
    real = RealCASAdapter()
    assert real.get_state().state == CASState.UNKNOWN
    action = DragAction(feature="face_width", start=(0.5, 0.5), dx=0.01)
    for operation in (real.capture, real.get_face_features, real.create_checkpoint,
                      lambda: real.restore_checkpoint(FakeCASAdapter().create_checkpoint()),
                      lambda: real.execute_drag(action)):
        with pytest.raises(AdapterError) as error:
            operation()
        assert error.value.as_dict()["code"]
    real.automation_enabled = real.calibration_verified = True
    with pytest.raises(AdapterError) as error:
        real.execute_drag(action)
    assert error.value.code == "FOCUS_REQUIRED"
    real = RealCASAdapter(focus_reader=lambda: True,
                          state_reader=lambda: StateResult(state=CASState.CAS, confidence=1,
                                                           reason="Injected test state"))
    real.automation_enabled = real.calibration_verified = True
    with pytest.raises(AdapterError) as error:
        real.execute_drag(action)
    assert error.value.code == "UNSUPPORTED"

"""Geometry extraction with a documented synthetic landmark schema."""

import math

from sim_designer.adapters.base import FaceParameters
from sim_designer.models import Landmark


def extract_features(points: dict[str, Landmark]) -> FaceParameters:
    """Recover parameters from named landmarks, invariant to translation/scaling.

    This schema belongs to Fake CAS. MediaPipe indices are not interchangeable.
    Missing, occluded, or degenerate points cause an explicit error.
    """
    required = {"origin", "unit_x", "unit_y", "crown", "face_bottom", "face_left",
                "face_right", "left_eye_center", "right_eye_center", "left_eye_left",
                "left_eye_right", "left_eye_top", "left_eye_bottom", "nose_top",
                "nose_tip", "nose_left", "nose_right", "mouth_left", "mouth_right",
                "lip_top", "lip_bottom", "jaw_left", "jaw_right", "chin"}
    if not required <= points.keys():
        raise ValueError(f"Missing landmarks: {sorted(required - points.keys())}")
    if any(p.confidence < 0.5 or not all(math.isfinite(v) for v in (p.x, p.y, p.confidence))
           for name, p in points.items() if name in required):
        raise ValueError("Landmarks are non-finite or low confidence")
    sx = (points["unit_x"].x - points["origin"].x) / 0.1
    sy = (points["unit_y"].y - points["origin"].y) / 0.1
    if sx <= 1e-8 or sy <= 1e-8:
        raise ValueError("Degenerate landmark coordinate basis")

    def dx(left: str, right: str) -> float:
        return (points[right].x - points[left].x) / sx

    def dy(top: str, bottom: str) -> float:
        return (points[bottom].y - points[top].y) / sy

    ew = dx("left_eye_left", "left_eye_right")
    if ew <= 1e-8:
        raise ValueError("Degenerate eye width")
    raw = {
        "face_width": (dx("face_left", "face_right") - 0.42) / 0.18,
        "face_length": (dy("crown", "face_bottom") - 0.62) / 0.12,
        "eye_spacing": (dx("left_eye_center", "right_eye_center") - 0.16) / 0.10,
        "eye_width": (ew - 0.08) / 0.05,
        "eye_height": (dy("left_eye_top", "left_eye_bottom") - 0.025) / 0.035,
        "eye_tilt": (dy("left_eye_right", "left_eye_left") / ew + 0.2) / 0.4,
        "nose_width": (dx("nose_left", "nose_right") - 0.045) / 0.05,
        "nose_length": (dy("nose_top", "nose_tip") - 0.10) / 0.08,
        "mouth_width": (dx("mouth_left", "mouth_right") - 0.13) / 0.12,
        "lip_fullness": (dy("lip_top", "lip_bottom") - 0.015) / 0.045,
        "jaw_width": (dx("jaw_left", "jaw_right") - 0.20) / 0.18,
        "chin_length": (dy("face_bottom", "chin") - 0.015) / 0.04,
    }
    if any(v < -1e-6 or v > 1 + 1e-6 for v in raw.values()):
        raise ValueError("Landmarks are outside the synthetic face model domain")
    return FaceParameters(**{name: min(1.0, max(0.0, value)) for name, value in raw.items()})

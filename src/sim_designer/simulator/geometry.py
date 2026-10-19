"""Synthetic named landmarks. These are ground truth, not image ML inference."""

import numpy as np

from sim_designer.adapters.base import FaceParameters
from sim_designer.models import Landmark


def face_landmarks(face: FaceParameters) -> dict[str, Landmark]:
    """Generate normalized 2D landmarks from the twelve face parameters."""
    points: dict[str, Landmark] = {}

    def put(name: str, x: float, y: float) -> None:
        points[name] = Landmark(x, y, 1.0)

    put("origin", 0.5, 0.5)
    put("unit_x", 0.6, 0.5)
    put("unit_y", 0.5, 0.6)
    width = 0.42 + 0.18 * face.face_width
    length = 0.62 + 0.12 * face.face_length
    put("crown", 0.5, 0.12)
    put("face_bottom", 0.5, 0.12 + length)
    put("face_left", 0.5 - width / 2, 0.45)
    put("face_right", 0.5 + width / 2, 0.45)
    spacing = 0.16 + 0.10 * face.eye_spacing
    ew = 0.08 + 0.05 * face.eye_width
    eh = 0.025 + 0.035 * face.eye_height
    tilt = -0.2 + 0.4 * face.eye_tilt
    for label, cx in (("left", 0.5 - spacing / 2), ("right", 0.5 + spacing / 2)):
        put(f"{label}_eye_center", cx, 0.36)
        put(f"{label}_eye_left", cx - ew / 2, 0.36 + tilt * ew / 2)
        put(f"{label}_eye_right", cx + ew / 2, 0.36 - tilt * ew / 2)
        put(f"{label}_eye_top", cx, 0.36 - eh / 2)
        put(f"{label}_eye_bottom", cx, 0.36 + eh / 2)
    tip_y = 0.40 + 0.10 + 0.08 * face.nose_length
    nw = 0.045 + 0.05 * face.nose_width
    put("nose_top", 0.5, 0.40)
    put("nose_tip", 0.5, tip_y)
    put("nose_left", 0.5 - nw / 2, tip_y)
    put("nose_right", 0.5 + nw / 2, tip_y)
    mw = 0.13 + 0.12 * face.mouth_width
    lh = 0.015 + 0.045 * face.lip_fullness
    put("mouth_left", 0.5 - mw / 2, 0.65)
    put("mouth_right", 0.5 + mw / 2, 0.65)
    put("lip_top", 0.5, 0.65 - lh / 2)
    put("lip_bottom", 0.5, 0.65 + lh / 2)
    jw = 0.20 + 0.18 * face.jaw_width
    put("jaw_left", 0.5 - jw / 2, 0.72)
    put("jaw_right", 0.5 + jw / 2, 0.72)
    put("chin", 0.5, 0.12 + length + 0.015 + 0.04 * face.chin_length)
    return points


def random_face(seed: int) -> FaceParameters:
    """Generate reproducible synthetic data without files or a network."""
    rng = np.random.default_rng(seed)
    return FaceParameters(**{name: float(rng.uniform(0.15, 0.85))
                             for name in FaceParameters.model_fields})

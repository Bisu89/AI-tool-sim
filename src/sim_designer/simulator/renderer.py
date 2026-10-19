"""OpenCV 2D renderer; output is RGB and has no desktop dependencies."""

import cv2
import numpy as np

from sim_designer.adapters.base import CASState, FEATURE_NAMES, FaceParameters
from sim_designer.simulator.geometry import face_landmarks

STATE_COLORS = {CASState.CAS: (40, 210, 100), CASState.POPUP: (230, 70, 70),
                CASState.MENU: (230, 180, 40), CASState.UNKNOWN: (100, 100, 100)}


def control_point(feature: str) -> tuple[float, float]:
    """Virtual control strip coordinates; these are never real CAS coordinates."""
    return (0.9, 0.08 + FEATURE_NAMES.index(feature) * 0.07)


def render_face(face: FaceParameters, state: CASState = CASState.CAS,
                size: int = 640) -> np.ndarray:
    """Render a stylized synthetic face plus a simulator-only state marker."""
    if not 128 <= size <= 2048:
        raise ValueError("Renderer size must be in [128, 2048]")
    image = np.full((size, size, 3), (27, 32, 43), dtype=np.uint8)
    points = face_landmarks(face)

    def p(name: str) -> tuple[int, int]:
        point = points[name]
        return round(point.x * size), round(point.y * size)

    outline = np.array([p(name) for name in ("crown", "face_right", "jaw_right", "chin",
                                            "jaw_left", "face_left")], dtype=np.int32)
    cv2.fillPoly(image, [outline], (225, 185, 160), lineType=cv2.LINE_AA)
    cv2.polylines(image, [outline], True, (160, 115, 100), 2, cv2.LINE_AA)
    for side in ("left", "right"):
        eye = np.array([p(f"{side}_eye_{name}") for name in ("left", "top", "right", "bottom")])
        cv2.fillPoly(image, [eye], (245, 243, 235), lineType=cv2.LINE_AA)
        cv2.polylines(image, [eye], True, (60, 45, 40), 2, cv2.LINE_AA)
        cv2.circle(image, p(f"{side}_eye_center"), max(2, size // 100), (55, 43, 34), -1)
    cv2.polylines(image, [np.array([p(n) for n in ("nose_top", "nose_left", "nose_tip", "nose_right")])],
                  False, (145, 100, 90), 2, cv2.LINE_AA)
    lips = np.array([p(n) for n in ("mouth_left", "lip_top", "mouth_right", "lip_bottom")])
    cv2.fillPoly(image, [lips], (165, 65, 85), lineType=cv2.LINE_AA)
    for name in FEATURE_NAMES:
        x, y = control_point(name)
        cv2.circle(image, (round(x * size), round(y * size)), max(2, size // 150), (80, 155, 220), -1)
    image[: max(4, size // 32), : max(4, size // 32)] = STATE_COLORS[state]
    cv2.putText(image, f"FAKE CAS / {state.value}", (size // 20, size // 24),
                cv2.FONT_HERSHEY_SIMPLEX, size / 1600, (230, 235, 245), 1, cv2.LINE_AA)
    if state in (CASState.POPUP, CASState.MENU):
        cv2.rectangle(image, (size // 4, size // 3), (size * 3 // 4, size * 2 // 3), (75, 85, 105), -1)
        cv2.putText(image, state.value, (size // 3, size // 2), cv2.FONT_HERSHEY_SIMPLEX,
                    size / 600, (255, 255, 255), 2)
    return image

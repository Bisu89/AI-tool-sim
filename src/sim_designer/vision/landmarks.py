"""Optional MediaPipe Face Mesh landmark provider with graceful degradation."""

from typing import Protocol

import numpy as np

from sim_designer.models import FaceBox, Landmark, LandmarkResult


class LandmarkProvider(Protocol):
    """Backend-independent facial landmark interface."""

    def detect(self, rgb_image: np.ndarray, face: FaceBox | None = None) -> LandmarkResult: ...


class MediaPipeLandmarkProvider:
    """Landmarks from MediaPipe Face Mesh; optional dependency and not CAS validated."""

    def __init__(self) -> None:
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError("MediaPipe is unavailable; install with .[landmarks].") from exc
        solutions = getattr(mp, "solutions", None)
        if solutions is None or not hasattr(solutions, "face_mesh"):
            raise RuntimeError("This MediaPipe build does not expose solutions.face_mesh.")
        self._mesh = solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1,
                                                  refine_landmarks=True, min_detection_confidence=0.5)

    def detect(self, rgb_image: np.ndarray, face: FaceBox | None = None) -> LandmarkResult:
        """Return 2D normalized points; optional face crop limits unrelated detections."""
        image = rgb_image
        ox = oy = 0
        if face is not None:
            ox, oy = face.x, face.y
            image = rgb_image[face.y:face.y + face.height, face.x:face.x + face.width]
        if image.size == 0:
            return LandmarkResult((), 0.0, "mediapipe", "Face crop is empty.")
        result = self._mesh.process(image)
        if not result.multi_face_landmarks:
            return LandmarkResult((), 0.0, "mediapipe", "No landmarks detected.")
        height, width = rgb_image.shape[:2]
        crop_h, crop_w = image.shape[:2]
        points = tuple(Landmark(min(1.0, max(0.0, (lm.x * crop_w + ox) / width)),
                                min(1.0, max(0.0, (lm.y * crop_h + oy) / height)),
                                float(getattr(lm, "presence", 1.0) or 1.0))
                       for lm in result.multi_face_landmarks[0].landmark)
        return LandmarkResult(points, 1.0, "mediapipe")

    def close(self) -> None:
        """Release MediaPipe graph resources."""
        self._mesh.close()


class UnavailableLandmarkProvider:
    """Explicit degraded-mode provider used when optional model import fails."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def detect(self, rgb_image: np.ndarray, face: FaceBox | None = None) -> LandmarkResult:
        return LandmarkResult((), 0.0, "unavailable", self.reason)

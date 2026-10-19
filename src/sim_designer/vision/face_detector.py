"""OpenCV Haar cascade face detection, suitable for degraded/local MVP use."""

import cv2
import numpy as np

from sim_designer.models import FaceBox


class FaceDetector:
    """Detect frontal faces using OpenCV's bundled cascade (not game-specific)."""

    def __init__(self, min_face_size: int = 40) -> None:
        self.min_face_size = min_face_size
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier(cascade_path)
        if self._cascade.empty():
            raise RuntimeError(f"OpenCV face cascade could not be loaded: {cascade_path}")

    def detect(self, rgb_image: np.ndarray) -> list[FaceBox]:
        """Return face boxes; Haar detection does not provide calibrated confidence."""
        if rgb_image.ndim != 3 or rgb_image.shape[2] != 3 or rgb_image.size == 0:
            raise ValueError("Expected a non-empty RGB image with three channels.")
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
        boxes = self._cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                               minSize=(self.min_face_size, self.min_face_size))
        return [FaceBox(int(x), int(y), int(w), int(h)) for x, y, w, h in boxes]

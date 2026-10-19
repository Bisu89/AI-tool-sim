"""Aspect-preserving image viewer with optional face and landmark overlays."""

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from sim_designer.models import FaceBox, Landmark


class ImageViewer(QWidget):
    """Paint an RGB image and analysis overlays without modifying the source."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.setAutoFillBackground(True)
        self._image: np.ndarray | None = None
        self._faces: list[FaceBox] = []
        self._landmarks: tuple[Landmark, ...] = ()
        self._show_overlay = True

    def set_frame(self, image: np.ndarray | None, faces: list[FaceBox] | None = None,
                  landmarks: tuple[Landmark, ...] = ()) -> None:
        self._image = image
        self._faces = faces or []
        self._landmarks = landmarks
        self.update()

    def set_overlay_visible(self, visible: bool) -> None:
        self._show_overlay = visible
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#17191f"))
        if self._image is None:
            painter.setPen(QColor("#aab0bd"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Load a reference image or capture a screen")
            return
        h, w = self._image.shape[:2]
        qimage = QImage(self._image.data, w, h, self._image.strides[0], QImage.Format.Format_RGB888).copy()
        target = qimage.size()
        target.scale(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        x = (self.width() - target.width()) // 2
        y = (self.height() - target.height()) // 2
        painter.drawImage(x, y, qimage.scaled(target, Qt.AspectRatioMode.IgnoreAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))
        if self._show_overlay:
            sx, sy = target.width() / w, target.height() / h
            painter.translate(x, y)
            painter.scale(sx, sy)
            painter.setPen(QPen(QColor("#44e0b3"), max(1.0, 2.0 / sx)))
            for face in self._faces:
                painter.drawRect(face.x, face.y, face.width, face.height)
            painter.setPen(QPen(QColor("#ffcf5a"), max(1.0, 3.0 / sx)))
            for point in self._landmarks:
                painter.drawPoint(round(point.x * w), round(point.y * h))

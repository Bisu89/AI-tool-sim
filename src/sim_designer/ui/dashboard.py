"""Observation-only dashboard for reference images and game screen captures."""

import logging
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import (QCheckBox, QFileDialog, QHBoxLayout, QLabel, QMainWindow,
                               QDialog, QMessageBox, QPushButton, QRubberBand, QSplitter,
                               QVBoxLayout, QWidget)

from sim_designer.capture.screen_capture import CaptureError, ScreenCapture
from sim_designer.models import FaceBox, ImageFrame, Landmark
from sim_designer.ui.image_viewer import ImageViewer
from sim_designer.vision.face_detector import FaceDetector
from sim_designer.vision.landmarks import (LandmarkProvider, MediaPipeLandmarkProvider,
                                         UnavailableLandmarkProvider)

log = logging.getLogger(__name__)


class RegionSelector(QDialog):
    """Fullscreen drag selector over a primary monitor screenshot."""

    def __init__(self, image: QImage, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Select capture region — Esc to cancel")
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._image = image
        self._start = None
        self.region: tuple[int, int, int, int] | None = None
        self._band = QRubberBand(QRubberBand.Shape.Rectangle, self)

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.drawImage(self.rect(), self._image)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 70))

    def mousePressEvent(self, event: object) -> None:
        self._start = event.position().toPoint()
        self._band.setGeometry(QRect(self._start, self._start))
        self._band.show()

    def mouseMoveEvent(self, event: object) -> None:
        if self._start is not None:
            self._band.setGeometry(QRect(self._start, event.position().toPoint()).normalized())

    def mouseReleaseEvent(self, event: object) -> None:
        if self._start is not None:
            rect = self._band.geometry()
            self.region = (rect.x(), rect.y(), rect.width(), rect.height())
            self.accept()

    def keyPressEvent(self, event: object) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


def load_rgb(path: str | Path) -> np.ndarray:
    """Load an image with OpenCV while handling Unicode Windows paths."""
    raw = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


class Dashboard(QMainWindow):
    """Main screen for selecting a reference image and viewing captured CAS."""

    def __init__(self, detector: FaceDetector | None = None,
                 landmark_provider: LandmarkProvider | None = None,
                 capture: ScreenCapture | None = None) -> None:
        super().__init__()
        self.setWindowTitle("AI Sim Designer — CAS Face Autopilot (Observation mode)")
        self.resize(1200, 760)
        self.detector = detector or FaceDetector()
        self.capture = capture or ScreenCapture()
        if landmark_provider is None:
            try:
                landmark_provider = MediaPipeLandmarkProvider()
            except RuntimeError as exc:
                landmark_provider = UnavailableLandmarkProvider(str(exc))
                log.warning("Landmark backend unavailable: %s", exc)
        self.landmark_provider = landmark_provider
        self.reference: np.ndarray | None = None
        self.reference_path: Path | None = None

        self.reference_view = ImageViewer()
        self.capture_view = ImageViewer()
        self.reference_status = QLabel("No reference image loaded")
        self.capture_status = QLabel("No screen capture yet")
        load_button = QPushButton("Load reference image")
        load_button.clicked.connect(self.choose_reference)
        capture_button = QPushButton("Capture primary monitor")
        capture_button.clicked.connect(self.capture_primary)
        region_button = QPushButton("Capture selected region")
        region_button.clicked.connect(self.capture_region)
        overlay = QCheckBox("Show face / landmark overlay")
        overlay.setChecked(True)
        overlay.toggled.connect(self._set_overlay)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Reference image"))
        left_layout.addWidget(self.reference_view, 1)
        left_layout.addWidget(self.reference_status)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("Game / screen capture"))
        right_layout.addWidget(self.capture_view, 1)
        right_layout.addWidget(self.capture_status)
        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([1, 1])
        controls = QHBoxLayout()
        for button in (load_button, capture_button, region_button):
            controls.addWidget(button)
        controls.addWidget(overlay)
        controls.addStretch(1)
        mode_label = QLabel("OBSERVATION ONLY — no game input automation")
        mode_label.setStyleSheet("color: #b87918; font-weight: bold")
        root = QVBoxLayout()
        root.addWidget(mode_label)
        root.addLayout(controls)
        root.addWidget(split, 1)
        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    def _set_overlay(self, visible: bool) -> None:
        self.reference_view.set_overlay_visible(visible)
        self.capture_view.set_overlay_visible(visible)

    def choose_reference(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Choose face reference", "",
                                                  "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if filename:
            try:
                self._show_image(load_rgb(filename), "reference", Path(filename))
            except (OSError, RuntimeError, ValueError) as exc:
                self._show_error(f"Could not load or analyze the selected image: {exc}")

    def capture_primary(self) -> None:
        try:
            self._show_frame(self.capture.capture())
        except (CaptureError, RuntimeError, ValueError) as exc:
            self._show_error(str(exc))

    def capture_region(self) -> None:
        """Let the user drag a rectangle on a desktop screenshot for capture."""
        try:
            import mss
            with mss.MSS() as sct:
                available = sct.monitors[1:]
                monitor = dict(next((m for m in available if m.get("is_primary")), available[0]))
                shot = np.asarray(sct.grab(monitor))
            rgb = np.ascontiguousarray(shot[:, :, :3][:, :, ::-1])
            h, w = rgb.shape[:2]
            qimage = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888).copy()
            selector = RegionSelector(qimage, self)
            selector.showFullScreen()
            result = selector.exec()
            region = selector.region if result == QDialog.DialogCode.Accepted else None
            if region and region[2] > 1 and region[3] > 1:
                scale_x = monitor["width"] / max(1, selector.width())
                scale_y = monitor["height"] / max(1, selector.height())
                x, y, width, height = region
                region = (monitor["left"] + round(x * scale_x),
                          monitor["top"] + round(y * scale_y),
                          max(1, round(width * scale_x)), max(1, round(height * scale_y)))
                self._show_frame(self.capture.capture(region))
        except (CaptureError, OSError, IndexError, RuntimeError, ValueError) as exc:
            self._show_error(f"Could not select/capture screen region: {exc}")

    def _show_frame(self, frame: ImageFrame) -> None:
        self._show_image(frame.image, "capture", metadata=frame)

    def _show_image(self, image: np.ndarray, target: str, path: Path | None = None,
                    metadata: ImageFrame | None = None) -> None:
        faces: list[FaceBox] = self.detector.detect(image)
        landmarks: tuple[Landmark, ...] = ()
        messages = [f"{len(faces)} face(s) detected" if faces else "No face detected"]
        if faces:
            result = self.landmark_provider.detect(image, faces[0])
            landmarks = result.points
            messages.append(f"{len(landmarks)} landmarks · {result.backend}" if landmarks
                            else (result.message or "Landmarks unavailable"))
        viewer = self.reference_view if target == "reference" else self.capture_view
        status = self.reference_status if target == "reference" else self.capture_status
        viewer.set_frame(image, faces, landmarks)
        if target == "reference":
            self.reference, self.reference_path = image, path
            label = path.name if path else "Reference"
        else:
            label = "Screen capture"
            if metadata:
                label += f" · {metadata.width}×{metadata.height} · {metadata.captured_at:%H:%M:%S UTC}"
        status.setText(f"{label} — " + " · ".join(messages))
        log.info("Displayed %s: %s", target, ", ".join(messages))

    def _show_error(self, message: str) -> None:
        log.error("UI operation failed: %s", message)
        QMessageBox.warning(self, "AI Sim Designer", message)

    def closeEvent(self, event: object) -> None:
        """Release native capture and optional landmark resources."""
        self.capture.close()
        close_provider = getattr(self.landmark_provider, "close", None)
        if close_provider is not None:
            close_provider()
        super().closeEvent(event)

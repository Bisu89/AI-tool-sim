"""Offline dashboard; all synthetic interaction uses an injected fake adapter."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel,
                               QMainWindow, QMessageBox, QPushButton, QSpinBox, QSplitter,
                               QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)

from sim_designer.adapters.base import AdapterError, CASState, DragAction, FEATURE_NAMES
from sim_designer.adapters.fake import FakeCASAdapter
from sim_designer.calibration.calibration_manager import CalibrationManager
from sim_designer.config import SimulatorSettings
from sim_designer.planner.optimizer import Optimizer
from sim_designer.session.history import SessionHistory
from sim_designer.simulator.geometry import face_landmarks, random_face
from sim_designer.simulator.renderer import control_point, render_face
from sim_designer.ui.image_viewer import ImageViewer


class SimulatorViewer(ImageViewer):
    """Horizontal drags on virtual blue controls emit actions within this widget."""

    drag_requested = Signal(str, float)

    def __init__(self) -> None:
        super().__init__()
        self._press: tuple[str, float] | None = None

    def _position(self, event: object) -> tuple[float, float]:
        side = min(self.width(), self.height())
        pos = event.position()
        return ((pos.x() - (self.width() - side) / 2) / side,
                (pos.y() - (self.height() - side) / 2) / side)

    def mousePressEvent(self, event: object) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            x, y = self._position(event)
            for feature in FEATURE_NAMES:
                cx, cy = control_point(feature)
                if (x - cx) ** 2 + (y - cy) ** 2 < 0.035 ** 2:
                    self._press = (feature, x)
                    break

    def mouseReleaseEvent(self, event: object) -> None:
        if self._press is not None:
            feature, x = self._press
            self._press = None
            dx = self._position(event)[0] - x
            if abs(dx) > 1e-5:
                self.drag_requested.emit(feature, dx)


class SimulatorDashboard(QMainWindow):
    """One timer tick executes at most one bounded simulated drag."""

    def __init__(self, adapter: FakeCASAdapter | None = None,
                 settings: SimulatorSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or SimulatorSettings()
        self.adapter = adapter or FakeCASAdapter(size=self.settings.render_size)
        self.target = random_face(self.settings.seed)
        self.profiles = []
        self.saved_checkpoint = None
        self.optimizer = self._new_optimizer()
        self.setWindowTitle("AI Sim Designer | OFFLINE Fake CAS Simulator")
        self.resize(1360, 900)
        self.timer = QTimer(self)
        self.timer.setInterval(self.settings.tick_ms)
        self.timer.timeout.connect(self._tick)
        self.reference_view = ImageViewer()
        self.current_view = SimulatorViewer()
        self.current_view.drag_requested.connect(self._manual_drag)
        self.status_label = QLabel()
        self.table = QTableWidget(len(FEATURE_NAMES), 4)
        self.table.setHorizontalHeaderLabels(["Feature", "Current", "Target", "Signed error"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(130)
        self.seed = QSpinBox()
        self.seed.setRange(0, 1000000)
        self.seed.setValue(self.settings.seed)
        self.state_combo = QComboBox()
        self.state_combo.addItems([state.value for state in CASState])
        self.state_combo.currentTextChanged.connect(self._set_state)
        overlay = QCheckBox("Landmark overlay (synthetic ground truth)")
        overlay.setChecked(True)
        overlay.toggled.connect(self.reference_view.set_overlay_visible)
        overlay.toggled.connect(self.current_view.set_overlay_visible)
        self.arm_box = QCheckBox("Enable simulated drags")
        self.arm_box.toggled.connect(lambda enabled: None if enabled else self.pause())
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Target seed"))
        controls.addWidget(self.seed)
        self._button(controls, "New session", self.new_session)
        self._button(controls, "Calibrate all", self.calibrate)
        controls.addWidget(self.arm_box)
        controls.addWidget(QLabel("Fake state"))
        controls.addWidget(self.state_combo)
        actions = QHBoxLayout()
        for title, callback in (("Start / Resume", self.start), ("One planned drag", self.single_step),
                                ("Pause", self.pause), ("STOP (Ctrl+Shift+S)", self.stop),
                                ("Checkpoint", self.checkpoint), ("Restore checkpoint", self.restore_checkpoint),
                                ("Restore best", self.restore_best), ("Export session", self.export_session),
                                ("Load session", self.load_session)):
            self._button(actions, title, callback)
        views = QSplitter(Qt.Orientation.Horizontal)
        for title, viewer in (("Synthetic target", self.reference_view),
                              ("Current face | blue controls follow table order; drag horizontally", self.current_view)):
            panel = QWidget()
            layout = QVBoxLayout(panel)
            layout.addWidget(QLabel(title))
            layout.addWidget(viewer)
            views.addWidget(panel)
        content = QSplitter(Qt.Orientation.Horizontal)
        content.addWidget(views)
        content.addWidget(self.table)
        content.setSizes([930, 400])
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addWidget(QLabel("OFFLINE SIMULATOR | synthetic geometry | exact fake rollback"))
        layout.addLayout(controls)
        layout.addLayout(actions)
        layout.addWidget(overlay)
        layout.addWidget(self.status_label)
        layout.addWidget(content, 1)
        layout.addWidget(self.log)
        self.setCentralWidget(root)
        self.shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut.activated.connect(self.stop)
        self.refresh()

    def _new_optimizer(self) -> Optimizer:
        return Optimizer(self.adapter, self.target, self.profiles,
                         max_steps=self.settings.max_steps, tolerance=self.settings.tolerance,
                         max_step=self.settings.max_step, weights=self.settings.weights)

    @staticmethod
    def _button(layout: QHBoxLayout, title: str, callback: object) -> None:
        button = QPushButton(title)
        button.clicked.connect(callback)
        layout.addWidget(button)

    def _error(self, exc: Exception) -> None:
        self.log.append(str(exc))
        QMessageBox.warning(self, "Simulator", str(exc))

    def refresh(self) -> None:
        self.reference_view.set_frame(render_face(self.target, size=self.settings.render_size),
                                      landmarks=tuple(face_landmarks(self.target).values()))
        points = tuple(self.adapter.get_landmarks().values()) if self.adapter.state == CASState.CAS else ()
        self.current_view.set_frame(self.adapter.capture().image, landmarks=points)
        state = self.adapter.get_state()
        current, target = self.adapter.face.model_dump(), self.target.model_dump()
        for row, name in enumerate(FEATURE_NAMES):
            for column, text in enumerate((name, f"{current[name]:.4f}", f"{target[name]:.4f}",
                                            f"{target[name] - current[name]:+.4f}")):
                self.table.setItem(row, column, QTableWidgetItem(text))
        self.status_label.setText(f"{state.state.value} ({state.confidence:.0%}) | {self.optimizer.status} | "
                                  f"steps {self.optimizer.steps}/{self.optimizer.max_steps} | "
                                  f"best score {self.optimizer.history.best_score:.5f} | "
                                  f"calibrated {len(self.profiles)}/{len(FEATURE_NAMES)}")

    def _set_state(self, value: str) -> None:
        self.adapter.state = CASState(value)
        self.refresh()

    def new_session(self) -> None:
        self.timer.stop()
        self.arm_box.setChecked(False)
        self.adapter = FakeCASAdapter(size=self.settings.render_size)
        self.target = random_face(self.seed.value())
        self.profiles = []
        self.saved_checkpoint = None
        self.optimizer = self._new_optimizer()
        self.state_combo.setCurrentText("CAS")
        self.log.clear()
        self.log.append("New offline session; calibration and explicit enablement required")
        self.refresh()

    def calibrate(self) -> None:
        self.pause()
        try:
            manager = CalibrationManager(self.settings.probe_dx, self.settings.max_step)
            profiles = manager.calibrate_all(self.adapter)
            self.profiles = profiles
            self.optimizer.profiles = profiles
            self.log.append("12 measured probes complete; exact baseline restored")
        except (AdapterError, ValueError) as exc:
            self._error(exc)
        self.refresh()

    def _prepare(self) -> bool:
        if not self.arm_box.isChecked():
            self.log.append("Enable simulated drags before starting")
            return False
        if self.optimizer.status in ("IDLE", "PAUSED"):
            self.optimizer.start()
        elif self.optimizer.status != "RUNNING":
            self.log.append("Run finished; create a new session or load a saved session")
            return False
        return True

    def start(self) -> None:
        if self._prepare():
            self.timer.start()
        self.refresh()

    def _tick(self) -> None:
        self.optimizer.step()
        entry = self.optimizer.history.entries[-1]
        self.log.append(f"{self.optimizer.status}: {entry.event} | score {entry.score:.5f} {entry.detail}")
        if self.optimizer.status != "RUNNING":
            self.timer.stop()
        self.refresh()

    def single_step(self) -> None:
        self.timer.stop()
        if self._prepare():
            self._tick()
            self.pause()

    def _manual_drag(self, feature: str, dx: float) -> None:
        self.timer.stop()
        if self._prepare():
            try:
                self.optimizer.step(DragAction(feature=feature, start=control_point(feature), dx=dx))
            except ValueError as exc:
                self._error(exc)
            self.pause()

    def pause(self) -> None:
        self.timer.stop()
        self.optimizer.pause()
        self.refresh()

    def stop(self) -> None:
        self.timer.stop()
        self.optimizer.stop()
        self.log.append("Stopped. Start a new session to run again.")
        self.refresh()

    def checkpoint(self) -> None:
        self.saved_checkpoint = self.adapter.create_checkpoint()
        self.log.append("Exact simulator checkpoint saved in memory")

    def restore_checkpoint(self) -> None:
        if self.saved_checkpoint is None:
            self.log.append("Create a checkpoint first")
            return
        self.pause()
        try:
            self.optimizer.restore(self.saved_checkpoint)
            self.state_combo.setCurrentText(self.adapter.state.value)
        except (AdapterError, ValueError) as exc:
            self._error(exc)
        self.refresh()

    def restore_best(self) -> None:
        self.pause()
        self.optimizer.restore_best()
        self.state_combo.setCurrentText(self.adapter.state.value)
        self.refresh()

    def export_session(self) -> None:
        self.pause()
        try:
            self.optimizer.history.current = self.adapter.create_checkpoint()
            path = self.optimizer.history.export(self.settings.session_directory)
            for profile in self.profiles:
                CalibrationManager.save(profile, self.settings.calibration_directory)
            self.log.append(f"Session saved: {path}; profiles saved separately")
        except OSError as exc:
            self._error(exc)

    def load_session(self) -> None:
        self.pause()
        filename, _ = QFileDialog.getOpenFileName(self, "Load offline session", "", "JSON (*.json)")
        if not filename:
            return
        try:
            history = SessionHistory.load(Path(filename))
            adapter = FakeCASAdapter(size=self.settings.render_size)
            optimizer = Optimizer.resume(adapter, history, [], max_steps=self.settings.max_steps,
                                         tolerance=self.settings.tolerance, max_step=self.settings.max_step,
                                         weights=self.settings.weights)
            self.adapter, self.optimizer = adapter, optimizer
            self.target = history.target
            self.profiles = []
            self.saved_checkpoint = None
            self.arm_box.setChecked(False)
            self.state_combo.setCurrentText(adapter.state.value)
            self.log.append("Session loaded paused. Recalibrate and enable simulated drags to resume.")
        except (OSError, ValueError, AdapterError) as exc:
            self._error(exc)
        self.refresh()

    def closeEvent(self, event: object) -> None:
        self.timer.stop()
        self.optimizer.stop()
        super().closeEvent(event)

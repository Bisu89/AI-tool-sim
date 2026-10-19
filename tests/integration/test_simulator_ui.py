"""Qt events are delivered in-process; no real desktop input is generated."""

from pathlib import Path

from PySide6.QtCore import QPoint, Qt

from sim_designer.adapters.base import CASState
from sim_designer.config import SimulatorSettings
from sim_designer.ui.simulator_dashboard import SimulatorDashboard


def test_dashboard_workflow_and_stop(qtbot, tmp_path: Path, monkeypatch) -> None:
    window = SimulatorDashboard(settings=SimulatorSettings(render_size=128,
                                session_directory=tmp_path / "sessions",
                                calibration_directory=tmp_path / "profiles"))
    qtbot.addWidget(window)
    window.show()
    window.activateWindow()
    qtbot.waitExposed(window)
    qtbot.wait(10)
    assert window.optimizer.status == "IDLE"
    window.single_step()
    assert window.optimizer.steps == 0
    window.calibrate()
    assert len(window.profiles) == 12
    window.arm_box.setChecked(True)
    window.single_step()
    assert window.optimizer.steps == 1
    assert window.optimizer.status == "PAUSED"
    window.checkpoint()
    face = window.adapter.face
    window.single_step()
    window.restore_checkpoint()
    assert window.adapter.face == face
    window.export_session()
    assert len(list((tmp_path / "sessions").glob("*.json"))) == 1
    assert len(list((tmp_path / "profiles").glob("*.json"))) == 12
    saved = next((tmp_path / "sessions").glob("*.json"))
    monkeypatch.setattr("sim_designer.ui.simulator_dashboard.QFileDialog.getOpenFileName",
                        lambda *args: (str(saved), "JSON (*.json)"))
    window.load_session()
    assert window.adapter.face == face
    assert window.optimizer.status == "PAUSED"
    assert not window.arm_box.isChecked()
    assert window.profiles == []
    window.calibrate()
    window.arm_box.setChecked(True)
    window.start()
    qtbot.keyClick(window, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
    qtbot.waitUntil(lambda: window.optimizer.status == "STOPPED", timeout=1000)
    assert not window.timer.isActive()
    window.new_session()
    assert not window.arm_box.isChecked()
    window.state_combo.setCurrentText("POPUP")
    assert window.adapter.get_state().state == CASState.POPUP


def test_virtual_mouse_drag_routes_through_guard(qtbot) -> None:
    window = SimulatorDashboard(settings=SimulatorSettings(render_size=128))
    qtbot.addWidget(window)
    window.show()
    window.calibrate()
    window.arm_box.setChecked(True)
    widget = window.current_view
    side = min(widget.width(), widget.height())
    x = (widget.width() - side) / 2 + side * 0.9
    y = (widget.height() - side) / 2 + side * 0.08
    start = QPoint(round(x), round(y))
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=start)
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=start + QPoint(max(1, round(side * 0.02)), 0))
    assert window.optimizer.steps == 1
    assert any(entry.action is not None for entry in window.optimizer.history.entries)

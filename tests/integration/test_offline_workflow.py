"""End-to-end offline calibration, optimizer, persistence, and isolation."""

from pathlib import Path
import subprocess
import sys

import pytest

from sim_designer.adapters.base import AdapterError, CASState, FEATURE_NAMES, FaceParameters
from sim_designer.adapters.fake import FakeCASAdapter
from sim_designer.calibration.calibration_manager import CalibrationManager, CalibrationProfile
from sim_designer.control.safety_guard import SafetyGuard
from sim_designer.planner.adjustment_planner import propose_action
from sim_designer.planner.optimizer import Optimizer
from sim_designer.session.history import SessionHistory
from sim_designer.simulator.geometry import random_face
from sim_designer.vision.similarity import compare_faces


def setup_run(**kwargs) -> Optimizer:
    adapter = FakeCASAdapter(size=128)
    profiles = CalibrationManager().calibrate_all(adapter)
    return Optimizer(adapter, random_face(7), profiles, **kwargs)


def test_calibration_measures_response_restores_and_roundtrips(tmp_path: Path) -> None:
    adapter = FakeCASAdapter(size=128)
    original = adapter.face
    manager = CalibrationManager()
    for profile in manager.calibrate_all(adapter):
        assert profile.response == pytest.approx(2)
        assert profile.tested
        # A small geometric change may rasterize to identical pixels at 128px.
        assert len(profile.before_image_sha256) == len(profile.after_image_sha256) == 64
        assert profile.observed[profile.feature] != profile.baseline[profile.feature]
        assert manager.load(manager.save(profile, tmp_path)) == profile
        assert adapter.face == original
    extreme = FakeCASAdapter(FaceParameters(**{name: 1 for name in FEATURE_NAMES}), size=128)
    assert all(p.response == pytest.approx(2) for p in manager.calibrate_all(extreme))


def test_corrupt_evidence_is_rejected() -> None:
    profile = CalibrationManager().calibrate(FakeCASAdapter(size=128), "face_width")
    data = profile.model_dump()
    data["response"] *= -1
    with pytest.raises(ValueError, match="disagrees"):
        CalibrationProfile.model_validate(data)


@pytest.mark.parametrize("reason", ["unarmed", "draft", "layout", "popup", "stop", "distance"])
def test_safety_gates_leave_face_unchanged(reason: str) -> None:
    run = setup_run()
    proposal = propose_action(run.evaluate(), run.profiles, "fake", "fake-cas-v1")
    action, profile = proposal
    guard = SafetyGuard()
    if reason != "unarmed":
        guard.arm()
    if reason == "draft":
        profile = profile.model_copy(update={"tested": False})
    elif reason == "layout":
        profile = profile.model_copy(update={"layout": "another-layout"})
    elif reason == "popup":
        run.adapter.state = CASState.POPUP
    elif reason == "stop":
        guard.stop()
    elif reason == "distance":
        action = action.model_copy(update={"dx": 0.08})
    before = run.adapter.face
    with pytest.raises(AdapterError):
        guard.execute(run.adapter, action, profile)
    assert run.adapter.face == before


@pytest.mark.parametrize("seed", range(4))
def test_optimizer_converges_and_keeps_best(seed: int) -> None:
    run = setup_run()
    run.target = random_face(seed)
    # Use a fresh history matching the chosen target.
    run = Optimizer(run.adapter, run.target, run.profiles)
    assert run.run() == "CONVERGED"
    assert run.steps <= run.max_steps
    scores = [entry.score for entry in run.history.entries if entry.event != "rollback"]
    assert scores == sorted(scores)
    assert run.history.best_score == pytest.approx(max(scores))
    assert run.evaluate().error <= run.tolerance
    assert not run.guard.enabled


def test_missing_calibration_pause_stop_and_step_limit() -> None:
    adapter = FakeCASAdapter(size=128)
    run = Optimizer(adapter, random_face(1))
    assert run.run() == "NO_SAFE_ACTION"
    assert run.steps == 0
    run = setup_run(max_steps=1)
    run.start()
    run.pause()
    assert run.step() == "PAUSED"
    assert run.steps == 0
    run.start()
    run.step()
    assert run.step() == "STEP_LIMIT"
    run = setup_run()
    run.start()
    run.stop()
    before = run.adapter.face
    assert run.step() == "STOPPED"
    assert run.adapter.face == before
    with pytest.raises(AdapterError):
        run.start()


def test_bad_response_rolls_back_and_stops() -> None:
    run = setup_run()
    checkpoint = run.adapter.create_checkpoint()
    original_execute = run.adapter.execute_drag

    def reversed_response(action) -> None:
        original_execute(action.model_copy(update={"dx": -action.dx}))

    run.adapter.execute_drag = reversed_response
    run.start()
    assert run.step() == "REGRESSION"
    assert run.adapter.face == checkpoint.face
    assert run.history.entries[-1].event == "rollback"
    assert run.history.best.face == checkpoint.face


def test_popup_during_run_blocks_without_action() -> None:
    run = setup_run()
    run.start()
    original = run.adapter.face
    run.adapter.state = CASState.POPUP
    assert run.step() == "BLOCKED"
    assert run.adapter.face == original
    assert run.steps == 0


def test_loading_popup_checkpoint_stays_paused_and_blocked() -> None:
    run = setup_run()
    run.adapter.state = CASState.POPUP
    run.history.current = run.adapter.create_checkpoint()
    resumed = Optimizer.resume(FakeCASAdapter(size=128), run.history, [])
    assert resumed.status == "PAUSED"
    assert resumed.adapter.state == CASState.POPUP
    resumed.start()
    assert resumed.step() == "BLOCKED"


def test_weights_guide_planner_and_corrupt_best_score_is_rejected() -> None:
    adapter = FakeCASAdapter(size=128)
    profiles = CalibrationManager().calibrate_all(adapter)
    weights = {"face_outline": 0, "eyes": 0, "nose": 1, "mouth": 0, "jaw_chin": 0}
    errors = compare_faces(adapter.face, FaceParameters(face_width=1, nose_width=0.6), weights)
    action, _ = propose_action(errors, profiles, adapter.backend, adapter.layout)
    assert action.feature == "nose_width"
    run = setup_run()
    data = run.history.model_dump()
    data["best_score"] = 0
    with pytest.raises(ValueError, match="Best checkpoint"):
        SessionHistory.model_validate(data)


def test_session_export_resume_exact_restore_and_unique_writes(tmp_path: Path) -> None:
    run = setup_run()
    run.start()
    run.step()
    run.pause()
    first = run.history.export(tmp_path)
    content = first.read_bytes()
    second = run.history.export(tmp_path)
    assert first != second and first.read_bytes() == content
    loaded = SessionHistory.load(first)
    adapter = FakeCASAdapter(size=128)
    resumed = Optimizer.resume(adapter, loaded, run.profiles)
    assert resumed.status == "PAUSED" and not resumed.guard.enabled
    assert adapter.face == run.adapter.face
    assert resumed.steps == run.steps
    assert resumed.run() == "CONVERGED"
    adapter.execute_drag(propose_action(compare_faces(adapter.get_face_features(), FaceParameters()),
                                       run.profiles, adapter.backend, adapter.layout)[0])
    resumed.restore_best()
    assert adapter.face == resumed.history.best.face


def test_headless_entrypoint_without_desktop_or_network_imports() -> None:
    code = '''
import builtins
import socket
original = builtins.__import__
def restricted(name, *args, **kwargs):
    if name.split('.')[0] in ('mss', 'pyautogui', 'pynput', 'PySide6', 'mediapipe'):
        raise AssertionError('Forbidden simulator dependency: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = restricted
socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(AssertionError('Network access'))
socket.socket = lambda *a, **k: (_ for _ in ()).throw(AssertionError('Network socket'))
from sim_designer.main import main
raise SystemExit(main(['--headless', '--seed', '7']))
'''
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"CONVERGED"' in result.stdout

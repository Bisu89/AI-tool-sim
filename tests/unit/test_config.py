from pathlib import Path

import pytest
from pydantic import ValidationError

from sim_designer.config import AppSettings, SimulatorSettings, load_settings


def test_default_settings_are_valid() -> None:
    settings = AppSettings()
    assert settings.vision.min_face_size == 40
    assert settings.capture.default_region is None


def test_load_yaml_settings(tmp_path: Path) -> None:
    path = tmp_path / "app.yaml"
    path.write_text("vision:\n  min_face_size: 64\n", encoding="utf-8")
    assert load_settings(path).vision.min_face_size == 64


def test_invalid_face_size_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("vision:\n  min_face_size: 2\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_settings(path)


def test_simulator_rejects_inconsistent_limits_and_weights() -> None:
    with pytest.raises(ValidationError, match="probe"):
        SimulatorSettings(probe_dx=0.04, max_step=0.02)
    with pytest.raises(ValidationError):
        SimulatorSettings(weights={"nose": 1})

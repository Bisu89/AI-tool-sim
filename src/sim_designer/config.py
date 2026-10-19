"""Validated application configuration loading."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaptureSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_region: tuple[int, int, int, int] | None = None


class VisionSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    min_face_size: int = Field(default=40, ge=20, le=2000)
    enable_landmarks: bool = True


class SimulatorSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    seed: int = Field(default=7, ge=0)
    render_size: int = Field(default=640, ge=128, le=2048)
    max_steps: int = Field(default=120, ge=1, le=10000)
    max_step: float = Field(default=0.04, gt=0, le=0.05)
    probe_dx: float = Field(default=0.02, gt=0, le=0.05)
    tolerance: float = Field(default=0.002, ge=0, lt=1)
    tick_ms: int = Field(default=100, ge=10, le=5000)
    session_directory: Path = Path("data/sessions")
    calibration_directory: Path = Path("data/calibrations")
    weights: dict[str, float] = Field(default_factory=lambda: {
        "face_outline": 1, "eyes": 1, "nose": 1, "mouth": 1, "jaw_chin": 1})

    @model_validator(mode="after")
    def check_limits(self) -> "SimulatorSettings":
        from sim_designer.adapters.base import FaceParameters
        from sim_designer.vision.similarity import compare_faces
        if self.probe_dx > self.max_step:
            raise ValueError("Calibration probe cannot exceed the drag safety limit")
        compare_faces(FaceParameters(), FaceParameters(), self.weights)
        return self


class RealCASSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_window_title: str = "The Sims 4"
    layout_version: str = "unverified"
    automation_enabled: bool = False


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    logging: dict[str, str] = Field(default_factory=lambda: {"level": "INFO"})
    capture: CaptureSettings = Field(default_factory=CaptureSettings)
    vision: VisionSettings = Field(default_factory=VisionSettings)
    simulator: SimulatorSettings = Field(default_factory=SimulatorSettings)
    real: RealCASSettings = Field(default_factory=RealCASSettings)


def load_settings(path: Path | None = None) -> AppSettings:
    """Load YAML settings, using safe defaults when no file is provided."""
    if path is None:
        path = Path(__file__).resolve().parents[2] / "configs" / "app.yaml"
    if not path.exists():
        return AppSettings()
    with path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}
    return AppSettings.model_validate(raw)

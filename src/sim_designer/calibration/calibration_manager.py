"""Probe simulator controls, measure response, and restore the exact baseline."""

from pathlib import Path
from uuid import uuid4

from pydantic import Field, model_validator

from sim_designer.adapters.base import (AdapterError, CASAdapter, CASState, FEATURE_NAMES,
                                        DragAction, ValueModel)
from sim_designer.simulator.renderer import control_point


class CalibrationProfile(ValueModel):
    backend: str
    layout: str
    render_size: int = Field(ge=128, le=2048)
    feature: str
    start: tuple[float, float]
    probe_dx: float = Field(ge=-0.05, le=0.05)
    measured_delta: float
    response: float
    max_step: float = Field(gt=0, le=0.05)
    confidence: float = Field(ge=0, le=1)
    tested: bool = False
    baseline: dict[str, float]
    observed: dict[str, float]
    before_image_sha256: str
    after_image_sha256: str

    @model_validator(mode="after")
    def validate_evidence(self) -> "CalibrationProfile":
        if abs(self.probe_dx) < 1e-8:
            raise ValueError("Calibration probe must be nonzero")
        if self.feature not in FEATURE_NAMES:
            raise ValueError("Invalid calibration feature")
        if self.tested:
            from sim_designer.adapters.base import FaceParameters
            before = FaceParameters(**self.baseline).model_dump()
            after = FaceParameters(**self.observed).model_dump()
            delta = after[self.feature] - before[self.feature]
            if abs(delta - self.measured_delta) > 1e-8 or abs(self.response * self.probe_dx - delta) > 1e-8:
                raise ValueError("Calibration response disagrees with measured evidence")
            if abs(self.response) < 1e-6:
                raise ValueError("Calibration probe had no measurable effect")
            if any(abs(after[name] - before[name]) > 1e-7 for name in FEATURE_NAMES if name != self.feature):
                raise ValueError("Cross-coupled calibration is unsupported by this planner")
        return self


class CalibrationManager:
    def __init__(self, probe_dx: float = 0.02, max_step: float = 0.04) -> None:
        if not 0 < probe_dx <= max_step <= 0.05:
            raise ValueError("Expected 0 < probe <= max_step <= 0.05")
        self.probe_dx, self.max_step = probe_dx, max_step

    def calibrate(self, adapter: CASAdapter, feature: str) -> CalibrationProfile:
        """Only the simulator supports reversible calibration probes currently."""
        import hashlib

        if adapter.backend != "fake":
            raise AdapterError("UNSUPPORTED", "Automatic calibration probes are simulator-only")
        state = adapter.get_state()
        if state.state != CASState.CAS or state.confidence < 0.95:
            raise AdapterError("UNSAFE_STATE", "Calibration requires recognized CAS")
        checkpoint = adapter.create_checkpoint()
        before = adapter.get_face_features().model_dump()
        probe = -self.probe_dx if before[feature] > 0.9 else self.probe_dx
        before_hash = hashlib.sha256(adapter.capture().image.tobytes()).hexdigest()
        try:
            adapter.execute_drag(DragAction(feature=feature, start=control_point(feature), dx=probe))
            after = adapter.get_face_features().model_dump()
            after_hash = hashlib.sha256(adapter.capture().image.tobytes()).hexdigest()
        finally:
            adapter.restore_checkpoint(checkpoint)
        delta = after[feature] - before[feature]
        return CalibrationProfile(backend=adapter.backend, layout=adapter.layout,
                                  render_size=checkpoint.render_size, feature=feature,
                                  start=control_point(feature), probe_dx=probe,
                                  measured_delta=delta, response=delta / probe,
                                  max_step=self.max_step, confidence=1.0, tested=True,
                                  baseline=before, observed=after,
                                  before_image_sha256=before_hash, after_image_sha256=after_hash)

    def calibrate_all(self, adapter: CASAdapter) -> list[CalibrationProfile]:
        return [self.calibrate(adapter, feature) for feature in FEATURE_NAMES]

    @staticmethod
    def save(profile: CalibrationProfile, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{profile.feature}-{uuid4().hex}.json"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(profile.model_dump_json(indent=2))
        return path

    @staticmethod
    def load(path: Path) -> CalibrationProfile:
        return CalibrationProfile.model_validate_json(path.read_text(encoding="utf-8"))

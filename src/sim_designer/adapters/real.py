"""Unverified real adapter scaffold. No real mouse driver is implemented."""

from collections.abc import Callable

from sim_designer.adapters.base import (AdapterError, CASState, Checkpoint, DragAction,
                                        FaceParameters, StateResult)
from sim_designer.models import ImageFrame
from sim_designer.config import RealCASSettings


class RealCASAdapter:
    backend = "real"
    layout = "unverified"

    def __init__(self, capture: Callable[[], ImageFrame] | None = None,
                 state_reader: Callable[[], StateResult] | None = None,
                 focus_reader: Callable[[], bool] | None = None,
                 settings: RealCASSettings | None = None) -> None:
        self.settings = settings or RealCASSettings()
        self.layout = self.settings.layout_version
        self._capture = capture
        self._state_reader = state_reader
        self._focus_reader = focus_reader
        self.automation_enabled = self.settings.automation_enabled
        self.calibration_verified = False

    def get_state(self) -> StateResult:
        if self._state_reader is not None:
            return self._state_reader()
        return StateResult(state=CASState.UNKNOWN, confidence=0,
                           reason="Real CAS recognition has not been verified")

    def capture(self) -> ImageFrame:
        if self._capture is None:
            raise AdapterError("CAPTURE_UNAVAILABLE", "No real capture service was configured")
        return self._capture()

    def execute_drag(self, action: DragAction) -> None:
        if not self.automation_enabled or not self.calibration_verified:
            raise AdapterError("AUTOMATION_LOCKED", "Real automation requires explicit enablement and verified calibration")
        if self._focus_reader is None or not self._focus_reader():
            raise AdapterError("FOCUS_REQUIRED", "The expected real game window must be verified in focus")
        state = self.get_state()
        if state.state != CASState.CAS or state.confidence < 0.95:
            raise AdapterError("UNSAFE_STATE", "Real CAS state is not sufficiently verified")
        raise AdapterError("UNSUPPORTED", "Real input execution is not implemented or game-tested")

    def get_face_features(self) -> FaceParameters:
        raise AdapterError("UNSUPPORTED", "Real feature extraction is not configured")

    def create_checkpoint(self) -> Checkpoint:
        raise AdapterError("UNSUPPORTED", "Exact real CAS checkpoints are not available")

    def restore_checkpoint(self, checkpoint: Checkpoint) -> None:
        raise AdapterError("UNSUPPORTED", "Real CAS restoration requires manual recovery")

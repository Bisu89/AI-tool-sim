"""Offline CAS adapter with exact rollback and no operating-system input calls."""

from datetime import datetime, timezone

from sim_designer.adapters.base import (AdapterError, CASState, Checkpoint, DragAction,
                                        FaceParameters, StateResult)
from sim_designer.capture.cas_detector import detect_simulator_state
from sim_designer.models import ImageFrame, Landmark
from sim_designer.simulator.geometry import face_landmarks
from sim_designer.simulator.renderer import control_point, render_face
from sim_designer.vision.features import extract_features


class FakeCASAdapter:
    backend = "fake"
    layout = "fake-cas-v1"

    def __init__(self, face: FaceParameters | None = None, size: int = 640) -> None:
        if not 128 <= size <= 2048:
            raise ValueError("Simulator size must be in [128, 2048]")
        self.face = face or FaceParameters()
        self.state = CASState.CAS
        self.size = size

    def capture(self) -> ImageFrame:
        image = render_face(self.face, self.state, self.size)
        return ImageFrame(image, self.size, self.size, datetime.now(timezone.utc), "fake-cas")

    def get_state(self) -> StateResult:
        return detect_simulator_state(self.capture().image)

    def get_landmarks(self) -> dict[str, Landmark]:
        if self.state != CASState.CAS:
            raise AdapterError("FACE_UNAVAILABLE", "Face landmarks are hidden outside CAS")
        return face_landmarks(self.face)

    def get_face_features(self) -> FaceParameters:
        return extract_features(self.get_landmarks())

    def execute_drag(self, action: DragAction) -> None:
        if self.get_state().state != CASState.CAS:
            raise AdapterError("UNSAFE_STATE", "Cannot drag outside a recognized CAS state")
        if action.start != control_point(action.feature) or action.dy != 0:
            raise AdapterError("INVALID_CONTROL", "Drag must use the synthetic horizontal control")
        values = self.face.model_dump()
        values[action.feature] = min(1.0, max(0.0, values[action.feature] + 2.0 * action.dx))
        self.face = FaceParameters(**values)

    def create_checkpoint(self) -> Checkpoint:
        return Checkpoint(layout=self.layout, face=self.face, state=self.state, render_size=self.size)

    def restore_checkpoint(self, checkpoint: Checkpoint) -> None:
        if checkpoint.backend != self.backend or checkpoint.layout != self.layout:
            raise AdapterError("CHECKPOINT_MISMATCH", "Checkpoint belongs to a different backend/layout")
        self.face, self.state = checkpoint.face, checkpoint.state
        self.size = checkpoint.render_size

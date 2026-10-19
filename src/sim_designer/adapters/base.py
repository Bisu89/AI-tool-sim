"""Shared CAS contracts and validated, serializable domain values."""

from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sim_designer.models import ImageFrame


class ValueModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class FaceParameters(ValueModel):
    """All twelve simulator shape parameters have domain [0, 1]."""

    face_width: float = Field(default=0.5, ge=0, le=1)
    face_length: float = Field(default=0.5, ge=0, le=1)
    eye_spacing: float = Field(default=0.5, ge=0, le=1)
    eye_width: float = Field(default=0.5, ge=0, le=1)
    eye_height: float = Field(default=0.5, ge=0, le=1)
    eye_tilt: float = Field(default=0.5, ge=0, le=1)
    nose_width: float = Field(default=0.5, ge=0, le=1)
    nose_length: float = Field(default=0.5, ge=0, le=1)
    mouth_width: float = Field(default=0.5, ge=0, le=1)
    lip_fullness: float = Field(default=0.5, ge=0, le=1)
    jaw_width: float = Field(default=0.5, ge=0, le=1)
    chin_length: float = Field(default=0.5, ge=0, le=1)


FEATURE_NAMES = tuple(FaceParameters.model_fields)


class CASState(str, Enum):
    CAS = "CAS"
    POPUP = "POPUP"
    MENU = "MENU"
    UNKNOWN = "UNKNOWN"


class StateResult(ValueModel):
    state: CASState
    confidence: float = Field(ge=0, le=1)
    reason: str


class DragAction(ValueModel):
    """A signed, normalized drag from a calibrated virtual control point."""

    feature: str
    start: tuple[float, float]
    dx: float = Field(ge=-0.1, le=0.1)
    dy: float = Field(default=0, ge=-0.1, le=0.1)

    @model_validator(mode="after")
    def check_action(self) -> "DragAction":
        if self.feature not in FEATURE_NAMES:
            raise ValueError("Unknown face feature")
        if any(not 0 <= value <= 1 for value in self.start):
            raise ValueError("Drag start must be normalized")
        if not (0 <= self.start[0] + self.dx <= 1 and 0 <= self.start[1] + self.dy <= 1):
            raise ValueError("Drag endpoint is outside the image")
        return self


class Checkpoint(ValueModel):
    backend: str = "fake"
    layout: str
    face: FaceParameters
    state: CASState
    render_size: int = Field(default=640, ge=128, le=2048)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AdapterError(RuntimeError):
    """Unsupported or rejected operations are errors, never successful no-ops."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class CASAdapter(Protocol):
    backend: str
    layout: str

    def get_state(self) -> StateResult: ...
    def capture(self) -> ImageFrame: ...
    def execute_drag(self, action: DragAction) -> None: ...
    def get_face_features(self) -> FaceParameters: ...
    def create_checkpoint(self) -> Checkpoint: ...
    def restore_checkpoint(self, checkpoint: Checkpoint) -> None: ...

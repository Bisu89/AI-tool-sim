"""Session history with exclusive writes and validated JSON reload."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sim_designer.adapters.base import Checkpoint, DragAction, FaceParameters, ValueModel


class HistoryEntry(ValueModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event: str
    score: float = Field(ge=0, le=1)
    face: FaceParameters
    action: DragAction | None = None
    detail: str = ""


class SessionHistory(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: int = Field(default=1, ge=1, le=1)
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    status: str = "IDLE"
    weights: dict[str, float] = Field(default_factory=lambda: {
        "face_outline": 1, "eyes": 1, "nose": 1, "mouth": 1, "jaw_chin": 1})
    target: FaceParameters
    current: Checkpoint
    best: Checkpoint
    best_score: float = Field(ge=0, le=1)
    entries: list[HistoryEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_best(self) -> "SessionHistory":
        from sim_designer.vision.similarity import compare_faces
        measured = compare_faces(self.best.face, self.target, self.weights).score
        if abs(measured - self.best_score) > 1e-7:
            raise ValueError("Best checkpoint does not match the recorded score")
        return self

    def export(self, directory: Path) -> Path:
        """Never overwrite an existing session export."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"session-{self.session_id}-{uuid4().hex}.json"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(self.model_dump_json(indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "SessionHistory":
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

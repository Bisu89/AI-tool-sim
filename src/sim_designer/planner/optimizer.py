"""Bounded evaluate/propose/execute/capture/evaluate loop with exact fake rollback."""

from sim_designer.adapters.base import AdapterError, CASAdapter, Checkpoint, DragAction, FaceParameters
from sim_designer.calibration.calibration_manager import CalibrationProfile
from sim_designer.control.safety_guard import SafetyGuard
from sim_designer.planner.adjustment_planner import propose_action
from sim_designer.session.history import HistoryEntry, SessionHistory
from sim_designer.vision.similarity import SimilarityResult, compare_faces


class Optimizer:
    """Step-based controller suitable for a Qt timer or a headless offline run."""

    def __init__(self, adapter: CASAdapter, target: FaceParameters,
                 profiles: list[CalibrationProfile] | None = None,
                 max_steps: int = 120, tolerance: float = 0.002,
                 max_step: float = 0.04, weights: dict[str, float] | None = None) -> None:
        if max_steps < 1 or not 0 <= tolerance < 1:
            raise ValueError("Invalid optimizer stopping limits")
        self.adapter, self.target = adapter, target
        self.profiles = profiles or []
        self.max_steps, self.tolerance = max_steps, tolerance
        self.weights = weights
        self.guard = SafetyGuard(max_step)
        self.steps = 0
        self.status = "IDLE"
        checkpoint = adapter.create_checkpoint()
        initial = compare_faces(checkpoint.face, target, weights)
        self.history = SessionHistory(target=target, current=checkpoint, best=checkpoint,
                                      best_score=initial.score, weights=weights or {
                                          "face_outline": 1, "eyes": 1, "nose": 1, "mouth": 1, "jaw_chin": 1})
        self._record("initial", initial)

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        self._status = value
        if hasattr(self, "history"):
            self.history.status = value

    def evaluate(self) -> SimilarityResult:
        return compare_faces(self.adapter.get_face_features(), self.target, self.weights)

    def _record(self, event: str, result: SimilarityResult,
                action: DragAction | None = None, detail: str = "") -> None:
        self.history.current = self.adapter.create_checkpoint()
        self.history.entries.append(HistoryEntry(event=event, score=result.score,
                                                face=self.history.current.face,
                                                action=action, detail=detail))

    def start(self) -> None:
        if self.status not in ("IDLE", "PAUSED"):
            raise AdapterError("RUN_FINISHED", "Start a new run after a terminal state")
        self.guard.arm()
        self.status = "RUNNING"

    def pause(self) -> None:
        if self.status == "RUNNING":
            self.guard.enabled = False
            self.status = "PAUSED"

    def stop(self) -> None:
        self.guard.stop()
        self.status = "STOPPED"

    def _finish(self, status: str) -> str:
        self.status = status
        self.guard.enabled = False
        return status

    def step(self, manual_action: DragAction | None = None) -> str:
        if self.status != "RUNNING":
            return self.status
        try:
            before = self.evaluate()
            if before.error <= self.tolerance and manual_action is None:
                return self._finish("CONVERGED")
            if self.steps >= self.max_steps:
                return self._finish("STEP_LIMIT")
            proposal = propose_action(before, self.profiles, self.adapter.backend,
                                      self.adapter.layout, self.guard.max_step)
            if manual_action is not None:
                profile = next((p for p in self.profiles if p.feature == manual_action.feature), None)
                proposal = (manual_action, profile) if profile is not None else None
            if proposal is None:
                return self._finish("NO_SAFE_ACTION")
            action, profile = proposal
            checkpoint = self.adapter.create_checkpoint()
            self.guard.execute(self.adapter, action, profile)
            self.steps += 1
            self.adapter.capture()
            after = self.evaluate()
            self._record("action", after, action)
            if after.error > before.error + 1e-8:
                self.adapter.restore_checkpoint(checkpoint)
                self._record("rollback", self.evaluate(), detail="Worse result; restored exact simulator checkpoint")
                self.status = "REGRESSION"
            elif after.score > self.history.best_score:
                self.history.best_score = after.score
                self.history.best = self.adapter.create_checkpoint()
            if self.status == "RUNNING" and after.error <= self.tolerance:
                self.status = "CONVERGED"
        except (AdapterError, ValueError) as exc:
            self.guard.enabled = False
            self.status = "BLOCKED"
            # Do not call vision again in an unknown/popup state.
            self.history.current = self.adapter.create_checkpoint()
            self.history.entries.append(HistoryEntry(event="blocked", score=self.history.entries[-1].score,
                                                     face=self.history.current.face, detail=str(exc)))
        if self.status != "RUNNING":
            self.guard.enabled = False
        return self.status

    def run(self) -> str:
        self.start()
        while self.status == "RUNNING":
            self.step()
        return self.status

    def restore_best(self) -> None:
        self.restore(self.history.best, "restore_best")

    def restore(self, checkpoint: Checkpoint, event: str = "restore_checkpoint") -> None:
        if self.status == "RUNNING":
            self.pause()
        self.adapter.restore_checkpoint(checkpoint)
        self._record(event, compare_faces(checkpoint.face, self.target, self.weights),
                     detail="Exact simulator restoration; score from synthetic geometry")

    @classmethod
    def resume(cls, adapter: CASAdapter, history: SessionHistory,
               profiles: list[CalibrationProfile], **kwargs: object) -> "Optimizer":
        """Load a fake session paused; explicit start is still required."""
        if adapter.backend != "fake":
            raise AdapterError("UNSUPPORTED", "Session restoration is simulator-only")
        adapter.restore_checkpoint(history.current)
        kwargs["weights"] = history.weights
        optimizer = cls(adapter, history.target, profiles, **kwargs)
        optimizer.history = history.model_copy(deep=True)
        optimizer.status = "PAUSED"
        optimizer.steps = sum(entry.event == "action" for entry in history.entries)
        return optimizer

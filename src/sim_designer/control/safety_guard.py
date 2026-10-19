"""Every optimizer action passes through a fresh adapter state check."""

import math

from sim_designer.adapters.base import AdapterError, CASAdapter, CASState, DragAction
from sim_designer.calibration.calibration_manager import CalibrationProfile


class SafetyGuard:
    def __init__(self, max_step: float = 0.04) -> None:
        if not 0 < max_step <= 0.05:
            raise ValueError("Safety step limit must be in (0, 0.05]")
        self.max_step = max_step
        self.enabled = False
        self.killed = False

    def arm(self) -> None:
        if self.killed:
            raise AdapterError("STOPPED", "Create a new run after an emergency stop")
        self.enabled = True

    def stop(self) -> None:
        self.enabled = False
        self.killed = True

    def execute(self, adapter: CASAdapter, action: DragAction,
                profile: CalibrationProfile) -> None:
        if not self.enabled or self.killed:
            raise AdapterError("AUTOMATION_LOCKED", "Automation is disabled or stopped")
        if adapter.backend != "fake":
            raise AdapterError("REAL_LOCKED", "This execution service only supports the simulator")
        # Revalidate serialized evidence, including profiles copied by callers.
        try:
            action = DragAction.model_validate(action.model_dump())
            profile = CalibrationProfile.model_validate(profile.model_dump())
        except ValueError as exc:
            raise AdapterError("INVALID_EVIDENCE", str(exc)) from exc
        if (not profile.tested or profile.confidence < 0.95 or profile.backend != adapter.backend
                or profile.layout != adapter.layout or profile.feature != action.feature
                or profile.start != action.start):
            raise AdapterError("CALIBRATION_REQUIRED", "A matching tested calibration is required")
        if math.hypot(action.dx, action.dy) > min(self.max_step, profile.max_step) + 1e-10:
            raise AdapterError("STEP_LIMIT", "Drag exceeds the configured distance limit")
        state = adapter.get_state()
        if state.state != CASState.CAS or state.confidence < 0.95:
            raise AdapterError("UNSAFE_STATE", state.reason)
        adapter.execute_drag(action)

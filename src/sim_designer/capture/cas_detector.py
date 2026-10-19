"""Conservative state recognition for synthetic simulator images only."""

import numpy as np

from sim_designer.adapters.base import CASState, StateResult
from sim_designer.simulator.renderer import STATE_COLORS


def detect_simulator_state(image: np.ndarray) -> StateResult:
    """Recognize the exact synthetic marker; this is not a real CAS detector."""
    if image.ndim == 3 and image.shape[2] == 3 and min(image.shape[:2]) >= 4:
        marker = image[:4, :4]
        for state, color in STATE_COLORS.items():
            if np.all(marker == color):
                confidence = 0.0 if state == CASState.UNKNOWN else 1.0
                return StateResult(state=state, confidence=confidence,
                                   reason="Exact simulator marker; synthetic images only")
    return StateResult(state=CASState.UNKNOWN, confidence=0, reason="No simulator marker")

"""One-action proposals based only on measured calibration responses."""

from sim_designer.adapters.base import DragAction
from sim_designer.calibration.calibration_manager import CalibrationProfile
from sim_designer.vision.similarity import SimilarityResult


def propose_action(errors: SimilarityResult, profiles: list[CalibrationProfile],
                   backend: str, layout: str, max_step: float = 0.04) -> tuple[DragAction, CalibrationProfile] | None:
    """Return one bounded action, or None (NO_SAFE_ACTION)."""
    valid = {p.feature: p for p in profiles if p.tested and p.confidence >= 0.95
             and p.backend == backend and p.layout == layout and abs(p.response) > 1e-6}
    candidates = [name for name in valid if errors.weighted_feature_errors.get(name, 0) > 1e-10]
    if not candidates:
        return None
    feature = max(candidates, key=lambda name: errors.weighted_feature_errors[name])
    profile = valid[feature]
    limit = min(max_step, profile.max_step)
    dx = max(-limit, min(limit, errors.per_feature[feature] / profile.response))
    return DragAction(feature=feature, start=profile.start, dx=dx), profile

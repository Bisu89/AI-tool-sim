"""Weighted synthetic geometry error; not a probability of likeness."""

from pydantic import Field

from sim_designer.adapters.base import FaceParameters, ValueModel

FEATURE_GROUPS = {"face_outline": ("face_width", "face_length"),
                  "eyes": ("eye_spacing", "eye_width", "eye_height", "eye_tilt"),
                  "nose": ("nose_width", "nose_length"),
                  "mouth": ("mouth_width", "lip_fullness"),
                  "jaw_chin": ("jaw_width", "chin_length")}


class SimilarityResult(ValueModel):
    score: float = Field(ge=0, le=1)
    error: float = Field(ge=0, le=1)
    per_feature: dict[str, float]
    per_group: dict[str, float]
    weighted_feature_errors: dict[str, float]
    confidence: float = 1.0


def compare_faces(current: FaceParameters, target: FaceParameters,
                  weights: dict[str, float] | None = None) -> SimilarityResult:
    """Compare model-domain parameters with signed target-minus-current errors."""
    import math

    weights = weights if weights is not None else {group: 1.0 for group in FEATURE_GROUPS}
    if set(weights) != set(FEATURE_GROUPS) or any(not math.isfinite(v) or v < 0 for v in weights.values()):
        raise ValueError("Weights must define every feature group with finite nonnegative values")
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("At least one similarity weight must be positive")
    a, b = current.model_dump(), target.model_dump()
    signed = {name: b[name] - a[name] for name in a}
    groups = {group: sum(abs(signed[name]) for name in names) / len(names)
              for group, names in FEATURE_GROUPS.items()}
    error = sum(groups[group] * weight for group, weight in weights.items()) / total
    priorities = {name: abs(signed[name]) * weights[group] / len(names) / total
                  for group, names in FEATURE_GROUPS.items() for name in names}
    return SimilarityResult(score=1 - error, error=error, per_feature=signed, per_group=groups,
                            weighted_feature_errors=priorities)

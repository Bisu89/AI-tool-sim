"""Small typed value objects shared by capture and vision modules."""

from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass(frozen=True)
class ImageFrame:
    """Captured or loaded RGB image and its origin metadata."""

    image: np.ndarray
    width: int
    height: int
    captured_at: datetime
    source: str
    region: tuple[int, int, int, int] | None = None


@dataclass(frozen=True)
class FaceBox:
    """Face rectangle in source image pixels."""

    x: int
    y: int
    width: int
    height: int
    confidence: float | None = None


@dataclass(frozen=True)
class Landmark:
    """A normalized facial landmark, in [0, 1] image coordinates."""

    x: float
    y: float
    confidence: float


@dataclass(frozen=True)
class LandmarkResult:
    """Landmark provider output; points are empty when unavailable."""

    points: tuple[Landmark, ...]
    confidence: float
    backend: str
    message: str | None = None

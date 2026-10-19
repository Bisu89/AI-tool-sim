# Limitations and implementation status

## Current offline simulator

| Capability | Status and scope |
|---|---|
| Twelve-parameter face, renderer, landmarks | Implemented; synthetic ground truth |
| Feature extraction, normalization, similarity | Implemented; analytic landmark schema only |
| CAS state recognition | Implemented for exact simulator markers only |
| Calibration, guarded drag, planning | Implemented and tested offline |
| Iterative optimization | Implemented; one bounded action per step, finite step limit |
| Checkpoints and regression rollback | Exact for fake face, state, and render size only |
| JSON history and session resume | Implemented; load paused, explicit recalibration in UI |
| Simulator dashboard | Automated Qt tests; manual usability still needs review |
| RealCASAdapter | Scaffold; structured errors, no real input executor |

Simulator parameters are independent and their drag responses are linear until
clipped to [0, 1]. Real CAS may be nonlinear, coupled, pose-sensitive, or
irreversible. Calibration from the fake backend must not be reused for the game.
Analytic landmarks are not detected from a synthetic raster; extracting features
from photos or rendered Sims still requires a suitable landmark backend/schema.
Pixel quantization can hide small geometric changes in low-resolution captures.
The synthetic marker does not recognize actual game UI. Export stores geometry
and metadata for reconstruction, not full screenshots or personal images.

## Original observation mode / real game status

| Capability | Status |
|---|---|
| Local reference image loading | Implemented; needs Windows UI smoke test |
| MSS screen / region capture | Implemented; needs Windows display smoke test |
| OpenCV face boxes | Implemented; not validated on Sims CAS |
| MediaPipe landmarks | Optional; backend availability and Sims results unverified |
| Landmark overlay | Implemented; needs Windows UI smoke test |
| Feature similarity score | Planned; no calibrated likeness score exists |
| CAS state detection and calibration | Planned; no tested profiles exist |
| Mouse / keyboard automation | Not implemented; no CAS controls are issued |
| Game integration | Not tested |

2D landmarks do not recover 3D shape, and rendered faces, lighting, pose, hair,
or custom content can make landmark detection fail. A visual score must not be
interpreted as a probability of identity or likeness without separate calibration.

# CAS calibration

## Simulator calibration (implemented)

Click Calibrate all or inject `CalibrationManager` into an offline workflow.
For each of twelve virtual controls, the manager records the baseline features
and image SHA-256, creates an exact checkpoint, executes one small normalized
horizontal probe, records the observed features and image SHA-256, and restores
the checkpoint in a finally block. Near the upper parameter bound the probe
direction reverses to avoid clipping. The measured response is feature change
divided by signed probe distance. Zero response or unexpected changes in other
features invalidate the supported independent-control calibration model.

Profiles contain backend, layout version, render size, feature, normalized start,
probe, measured delta, response, maximum step, confidence, tested status and
before/after evidence. Draft, low-confidence, wrong-backend or wrong-layout
profiles do not authorize optimizer actions. JSON loads validate the measurement
against the stored response. Exported profiles are synthetic and cannot authorize
real game input. Small probes may change geometry without changing raster pixels
at low resolution; calibration measures landmarks, not pixel difference.

## Real CAS calibration (planned, unverified)

No real CAS drag zones or verified game profiles are shipped. Future real
calibration must record the tested game build, CAS layout, desktop and game
window bounds, control region, measured response, limits, and verification.
A draft must never enable automation. Popup, menu, unknown state, loss of focus,
or insufficient confidence must block every action. Do not infer a real CAS state
from the synthetic marker used in the simulator.

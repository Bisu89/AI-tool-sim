# Offline Fake CAS Simulator

## Run

From the repository root with dependencies already installed:

```powershell
py -3.11 -m sim_designer.main
py -3.11 -m sim_designer.main --headless --seed 7
py -3.11 -m sim_designer.main --headless --output output
```

No game, administrator access, download, camera, desktop capture, or physical
input driver is needed at runtime. The headless mode also avoids Qt and MediaPipe.
The original screen viewer remains available via `--mode observe`.

## Workflow

1. Choose a seed and create a new session to generate a deterministic target.
2. Calibrate all virtual controls. Each measured probe restores its baseline.
3. Enable simulated drags. Execute one planned drag, start the timed optimizer,
   or drag a blue virtual control horizontally. Controls follow table order.
4. Pause or Stop; Ctrl+Shift+S stops while this application has focus. A stopped
   run cannot restart until a new session is created or a saved session is loaded.
5. Exercise rejection using POPUP, MENU, or UNKNOWN in the state dropdown.
6. Save/restore an in-memory checkpoint, restore the best observed face, or export
   JSON history. Exported filenames are unique and never replace earlier exports.
7. Load a session paused; recalibrate and explicitly enable simulated input to
   continue. Configuration still supplies step limits; saved similarity weights
   are preserved during resumption. Action counts carry over across resumption.

`configs/app.yaml` controls render size, seed, probe distance, step size, step
limit, tolerance, timer interval, weights, and persistence directories.
The CLI accepts `--config`, `--seed`, and an explicit `--output` directory.
Without `--output`, headless execution prints a summary without writing files.

## Model and landmark schema

All twelve parameters are finite numbers in [0, 1]. The following ranges describe
normalized canvas geometry, not real human anatomy or The Sims 4 controls.

| Parameter | Geometry mapping |
|---|---|
| face_width | width = 0.42 + 0.18p |
| face_length | crown-to-base length = 0.62 + 0.12p |
| eye_spacing | center distance = 0.16 + 0.10p |
| eye_width | horizontal width = 0.08 + 0.05p |
| eye_height | vertical aperture = 0.025 + 0.035p |
| eye_tilt | signed corner slope = -0.20 + 0.40p |
| nose_width | nostril width = 0.045 + 0.05p |
| nose_length | bridge-to-tip distance = 0.10 + 0.08p |
| mouth_width | width = 0.13 + 0.12p |
| lip_fullness | vertical thickness = 0.015 + 0.045p |
| jaw_width | width = 0.20 + 0.18p |
| chin_length | extension below face base = 0.015 + 0.04p |

Named landmarks include an origin and two axis scale markers. Extraction uses
relative distances normalized by this basis, so translation and axis scaling
preserve features. Missing, non-finite, low-confidence, degenerate or out-of-domain
landmarks are rejected. These landmarks come directly from geometry; no claim
is made that a model detected them in the rendered image. MediaPipe landmarks
use another schema and cannot be fed into this extractor unchanged.

## Virtual controls and calibration

Only the simulator defines twelve virtual controls at normalized x=0.9 and
y=0.08+0.07i, in model field order. A horizontal drag changes the corresponding
parameter by 2*dx, clamped to [0, 1]. The planner learns this response from actual
probe measurements; it does not hard-code the gain. Calibration is reversible
only in the fake backend. Small probes can leave identical raster images due to
pixel quantization; their analytic geometry still changes.

The state detector reads an exact simulator-only corner marker. Tampered or
missing markers yield UNKNOWN. RealCASAdapter never uses this as game evidence.

## Optimization, history, and failure behavior

The geometric error is a weighted mean of absolute feature errors within five
groups: outline, eyes, nose, mouth, and jaw/chin. Score is 1-error, not a likeness
probability. The planner prioritizes calibrated features by their weighted
contribution and proposes one bounded signed action. The guard rechecks explicit
enablement, backend/layout, measurement evidence, control start, distance and
recognized CAS state before execution.

Runs stop on convergence, step limit, missing safe actions, blocked state,
explicit Stop, or regression. A regression records the attempted face, restores
the exact prior fake face/state/render size, records rollback and stops. Failure
after a drag blocks the run without claiming an unverified restoration. Best
checkpoints remain separate from the current face. Checkpoints do not rewind
the action history; restores are recorded as events.

JSON includes schema version, session ID, target, weights, run status, current
and best checkpoints, best score, timestamps and actions. It stores geometry for
reconstruction rather than personal images or screenshots. Loaded best scores
are checked against stored geometry. A loaded session is always paused. Profiles
are exported separately and UI resumption requires fresh calibration.

## Real adapter boundary

`CASAdapter` defines get_state, capture, execute_drag, get_face_features,
create_checkpoint and restore_checkpoint. FakeCASAdapter implements all six.
RealCASAdapter accepts injected capture, state, focus readers and real settings,
but has no physical input executor. Unsupported methods raise `AdapterError`
with a code and message (`as_dict()` provides a structured payload).
Changing its enablement/calibration flags does not implement real dragging.
Real game calibration, recognition, feature extraction, focus handling and
rollback remain UNVERIFIED and require future testing in The Sims 4.

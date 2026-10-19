# AI Sim Designer — CAS Face Autopilot

## Offline Fake CAS Simulator (default)

The application now starts in a fully local simulator. It needs no running game,
administrator privileges, screen capture, MediaPipe model, network, or physical
mouse automation. Existing installed Python dependencies are sufficient to run;
installing dependencies on a new machine still requires packages to be available.

```powershell
py -3.11 -m sim_designer.main
py -3.11 -m sim_designer.main --headless --seed 7
py -3.11 -m sim_designer.main --headless --output output
```

The GUI shows a seeded synthetic target alongside a parameterized fake face.
Click **Calibrate all**, enable **Enable simulated drags**, then use **One planned
drag** or **Start / Resume**. Blue controls can also be dragged horizontally
inside the canvas; they follow the feature table order. Oversized drags are
rejected. A drag making the score worse is rolled back and the run stops.

Use Pause, Stop (Ctrl+Shift+S while this app has focus), Checkpoint, Restore
checkpoint, or Restore best. Change the Fake state dropdown to exercise popup,
menu, and unknown-state rejection. New session resets calibration and automation.
Export session writes a unique JSON file and calibration profiles to configured
directories. Load session restores the fake state paused; recalibrate and enable
simulated drags before resuming. Stop requires a new or loaded session to run again.

All twelve parameters are in [0, 1]. Landmarks are analytic ground truth from
the simulator geometry, not landmarks inferred from a raster or a photograph.
The geometric score is not a probability of likeness. Exact rollback applies
only to this simulator. RealCASAdapter is an unverified scaffold that never
executes physical input. See [Simulator guide](docs/SIMULATOR.md) and
[current feature list](docs/FEATURES.md).

## Original screen viewer (optional)

Use `py -3.11 -m sim_designer.main --mode observe` to open the original viewer.
The following capture workflow concerns this optional mode.

Local Windows desktop MVP for comparing a reference face image with a user
selected screen capture. The current milestone is **observation only**: it can
load images, capture the primary monitor or a selected rectangle, detect face
boxes, and display optional facial landmarks. It does not control The Sims 4.

## Requirements

- Windows 10/11 and Python 3.11 (64-bit recommended).
- Desktop session available for PySide6 and MSS.
- The Sims 4 is optional for development and has not been integration-tested.

## Install and run

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_dev.ps1
.\scripts\run_app.ps1
```

Or install with `py -3.11 -m pip install -e ".[dev,landmarks]"` and run with
`py -3.11 -m sim_designer.main --mode observe`. The landmark package is optional; without it,
the app stays usable for captures and face boxes and reports degraded mode.

## Workflow

1. Load a face reference image.
2. Bring the game to the desired screen and choose **Capture primary monitor**,
   or select a region. Captures are displayed in memory and are not saved.
3. Review the face boxes and optional landmark overlay. No image is modified.

Use windowed or borderless mode for convenient capture. Stop and inspect the
screen manually if an unexpected dialog or game state is present.

## Diagnostics and tests

- `py -3.11 scripts/check_environment.py` — report installed packages.
- `py -3.11 scripts/diagnose_screen.py` — inspect monitor bounds and capture.
- `py -3.11 -m pytest` — run game-independent unit tests.

See [Testing](docs/TESTING.md), [Troubleshooting](docs/TROUBLESHOOTING.md), and
[Limitations](docs/LIMITATIONS.md). No tests against a running game are claimed.

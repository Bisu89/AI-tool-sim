# Troubleshooting

- **At work without the game:** use the default simulator or
  `py -3.11 -m sim_designer.main --headless`. Neither needs screen capture.
- **NO_SAFE_ACTION:** calibrate the virtual controls before starting a run.
- **Run will not start:** enable simulated drags. After Stop, regression, or a
  terminal result, create a new session or load a saved session.
- **BLOCKED after popup/menu:** use New session or restore/load a valid CAS
  checkpoint; starting again requires a fresh run or resumed session.
- **Qt tests in a restricted session:** set `QT_QPA_PLATFORM=offscreen` and put
  pytest temporary files inside the workspace with `--basetemp=.pytest-tmp-check`.
- **Landmarks versus pixels:** synthetic landmarks are analytic. A tiny change
  may not visibly move a pixel at low resolution.

The following items concern the optional legacy observer mode.

- **Wrong Python version:** use `py -3.11`; the bare `python` command may point
  to another installed interpreter.
- **Missing dependencies:** run `py -3.11 -m pip install -e ".[dev,landmarks]"`.
- **No landmarks:** install the optional extra; face boxes still work in degraded
  mode. MediaPipe results on Sims faces are not guaranteed.
- **Capture denied or blank:** run `py -3.11 scripts/diagnose_screen.py`, check
  Windows display permissions, and use a windowed/borderless game mode.
- **No face detected:** try a clear, front-facing image with adequate face size
  and lighting. Haar detection is not robust to every angle or rendered face.

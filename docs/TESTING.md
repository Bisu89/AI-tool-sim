# Testing

## Offline simulator automated suite

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
py -3.11 -m pytest --basetemp=.pytest-tmp-check
py -3.11 -m sim_designer.main --headless --seed 7
```

Unit tests cover all twelve parameter domains, landmark roundtrips and
translation/scaling normalization, per-parameter rendering changes, malformed or
occluded landmarks, weighted geometry errors, synthetic state recognition, exact
checkpoint restoration, configuration, and structured real-adapter rejection.

Offline integration tests cover measured calibration and JSON roundtrip,
rejection of corrupt measurements, safety gates, missing calibration, convergence,
pause/stop/step limits, regression rollback, popup interruption, unique exports,
and session resumption. Qt tests use in-process widget events for calibration,
single action, virtual canvas dragging, checkpoint restore, export and Stop.
They never generate operating-system mouse input. A separate process runs the
headless entry point with desktop/model imports and network sockets forbidden.

These are simulator integration tests. They are not game integration tests.
Headless Qt tests do not establish usability on every Windows DPI configuration.

## Legacy observation checks

Install test dependencies with `py -3.11 -m pip install -e ".[dev]"`, then run
`py -3.11 -m pytest`. Unit tests use generated blank images and do not need the
game, camera, personal images, or a display server. The Qt dashboard and MSS
capture need manual smoke checks on Windows using `py -3.11 -m sim_designer.main`
and `py -3.11 scripts/diagnose_screen.py`.

No The Sims 4 game integration tests are included or claimed as passed. Landmark
backend availability depends on installing the optional `landmarks` extra.

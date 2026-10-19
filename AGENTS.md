# Development rules

- Keep image capture, vision, and Qt presentation in separate modules.
- Public APIs need type hints; safety-sensitive or user-facing behavior needs clear errors.
- Observation is the default. Milestone 1 must not automate mouse or keyboard input.
- Never assume CAS layout, screen coordinates, or that a game window is focused.
- Do not claim game integration has been tested unless tested in The Sims 4.
- Run `py -3.11 -m pytest` for unit tests and `py -3.11 -m sim_designer.main` to launch.
- Keep user images and session data local; do not overwrite source images.
- The default application is now the offline Fake CAS Simulator. Run it headless
  with `py -3.11 -m sim_designer.main --headless`; observer mode is explicit.
- Simulator adapters, geometry, calibration, planner and UI must not import MSS,
  PyAutoGUI, pynput, MediaPipe or desktop input drivers. Qt widget events may be
  delivered in-process by tests. No physical mouse movement is allowed.
- `CASAdapter` is the dependency boundary. RealCASAdapter remains unsupported
  for input and exact restoration even if callers change its safety flags.
- Analytic simulator landmarks are ground truth, not raster image detection.
- Exact checkpoints and automatic regression rollback are simulator-only.
- For headless Qt tests set `QT_QPA_PLATFORM=offscreen` and use a workspace
  pytest base directory: `py -3.11 -m pytest --basetemp=.pytest-tmp-check`.

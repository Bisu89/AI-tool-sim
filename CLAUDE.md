# AI Sim Designer development notes

The default entry point now opens the offline Fake CAS Simulator. The original
viewer is `--mode observe`; `--headless` runs synthetic calibration and bounded
optimization without Qt or desktop access. See `docs/SIMULATOR.md` for contracts,
geometry, state detection, persistence, and the exact-versus-real rollback boundary.
Use injected `CASAdapter` implementations. No physical input drivers are present
in the simulator; RealCASAdapter is an unverified, locked scaffold.

## Original observation milestone

This Windows Python 3.11 project separates capture (`capture`), face/landmark
analysis (`vision`), and Qt UI (`ui`). The current milestone is observation only:
no mouse automation, CAS coordinate assumptions, or claims of game validation.
Install with `py -3.11 -m pip install -e '.[dev,landmarks]'`; run via
`py -3.11 -m sim_designer.main`. See `docs/ARCHITECTURE.md` and `AGENTS.md`.

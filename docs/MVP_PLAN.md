# MVP plan

Offline development now implements a synthetic version of milestones 2-4:
measured calibration, guarded single actions, bounded optimization, session
history, and exact fake rollback. Acceptance is covered by unit and offline Qt
integration tests. This does not advance real-game verification. The remaining
milestones below refer to the real The Sims 4 integration.

1. **Capture + Landmark Viewer (current):** local reference loading, MSS monitor
   and region capture, face boxes, optional landmarks, Qt dashboard, diagnostics,
   and unit tests. Acceptance excludes game-specific claims.
2. **CAS calibration (planned):** identify UI anchors on real tested builds and
   record measured, user-confirmed calibration profiles.
3. **Single action (planned):** safety-checked one-drag proposal and explicit
   confirmation, followed by capture and evaluation.
4. **Iterative optimizer (planned):** one action per round, bounded steps,
   checkpoints, stop controls, and measured best result.

Risks include 3D-to-2D mismatch, variable CAS layouts, image landmark failure on
stylized/custom-content faces, and desktop focus or scaling changes. Automation
must remain unavailable until calibration and safety gates are implemented.

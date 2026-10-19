# Architecture

## Current offline simulator

```text
CLI / SimulatorDashboard -> Optimizer -> CASAdapter protocol
                              |             |-- FakeCASAdapter -> geometry + OpenCV renderer
                              |             `-- RealCASAdapter (unsupported real input)
                              |-- CalibrationManager (measured reversible fake probes)
                              |-- SafetyGuard (enablement / state / calibration / step limits)
                              |-- Adjustment planner (one action using measured response)
                              `-- SessionHistory (JSON + exact fake checkpoints)
```

The default simulator never imports MSS, MediaPipe, physical input drivers, or
the legacy dashboard. The headless CLI also avoids Qt. Synthetic landmarks flow
through `vision.features.extract_features` and weighted `vision.similarity` into
the planner. Landmark-derived features are separate from renderer pixel values.
The UI owns widgets and a timer; the optimizer owns sequencing and stopping.
The fake adapter owns state and exact restoration. All persistence destinations
come from configuration or an explicit CLI output directory; writes are unique.

RealCASAdapter accepts optional injected capture, state and focus readers. It
returns UNKNOWN without recognition, refuses unverified input, and raises
structured `AdapterError` errors for unsupported operations. Even after safety
checks pass, real execution is explicitly unsupported. It is not used by the
simulator. See [SIMULATOR.md](SIMULATOR.md) for the normalized control model.

## Original observation workflow

```text
Qt dashboard -> ScreenCapture (MSS) -> ImageFrame -> FaceDetector (OpenCV)
                                           `------> LandmarkProvider (optional MediaPipe)
```

`capture` owns screen acquisition and capture metadata. `vision` owns face and
landmark inference and does not control the desktop. `ui` presents images and
overlays. The provider protocol allows another landmark backend without changing
the dashboard contract. Configuration is parsed and validated by Pydantic.

The application uses OpenCV's contrib distribution because MediaPipe 0.10.x
depends on it; installing both `opencv-python` and `opencv-contrib-python` would
place two distributions over the same `cv2` module. The landmark extra is pinned
to MediaPipe 0.10.x because the current provider uses its `solutions.face_mesh`
API. The configured dependency ranges were installed and imported on Python 3.11.

Milestone 1 has no path from the UI or vision code to mouse/keyboard automation.
Haar cascade boxes are detections without a calibrated confidence score. The
optional MediaPipe Face Mesh backend produces image-space landmarks, but its
results on rendered Sims and likeness scoring are unvalidated.

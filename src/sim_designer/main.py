"""Default offline simulator entry point with lazy desktop dependencies."""

import argparse
import json
from pathlib import Path

from sim_designer.adapters.fake import FakeCASAdapter
from sim_designer.calibration.calibration_manager import CalibrationManager
from sim_designer.config import load_settings
from sim_designer.logging_config import configure_logging
from sim_designer.planner.optimizer import Optimizer
from sim_designer.simulator.geometry import random_face


def main(argv: list[str] | None = None) -> int:
    """Run a headless offline experiment, simulator UI, or legacy observer."""
    parser = argparse.ArgumentParser(description="Offline CAS simulator or legacy screen viewer")
    parser.add_argument("--mode", choices=("simulator", "observe"), default="simulator")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output", type=Path, help="Directory for a unique JSON session report")
    args = parser.parse_args(argv)
    if args.headless and args.mode != "simulator":
        parser.error("--headless requires --mode simulator")
    if args.seed is not None and args.seed < 0:
        parser.error("--seed must be nonnegative")
    settings = load_settings(args.config)
    configure_logging(settings.logging.get("level", "INFO"))
    if args.seed is not None:
        settings.simulator.seed = args.seed
    sim = settings.simulator
    if args.headless:
        adapter = FakeCASAdapter(size=sim.render_size)
        profiles = CalibrationManager(sim.probe_dx, sim.max_step).calibrate_all(adapter)
        optimizer = Optimizer(adapter, random_face(sim.seed), profiles, max_steps=sim.max_steps,
                              max_step=sim.max_step, tolerance=sim.tolerance, weights=sim.weights)
        status = optimizer.run()
        result = {"backend": "fake", "status": status, "steps": optimizer.steps,
                  "score": optimizer.history.best_score, "error": optimizer.evaluate().error}
        if args.output:
            result["report"] = str(optimizer.history.export(args.output))
        print(json.dumps(result, indent=2))
        return 0 if status == "CONVERGED" else 1
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    if args.mode == "simulator":
        from sim_designer.ui.simulator_dashboard import SimulatorDashboard
        window = SimulatorDashboard(settings=sim)
    else:
        from sim_designer.ui.dashboard import Dashboard
        from sim_designer.vision.face_detector import FaceDetector
        from sim_designer.vision.landmarks import UnavailableLandmarkProvider
        provider = None if settings.vision.enable_landmarks else UnavailableLandmarkProvider("Disabled in configuration")
        window = Dashboard(detector=FaceDetector(settings.vision.min_face_size), landmark_provider=provider)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

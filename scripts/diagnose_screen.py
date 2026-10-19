"""List MSS monitor rectangles and attempt a non-persistent capture."""

from sim_designer.capture.screen_capture import ScreenCapture


def main() -> int:
    try:
        capture = ScreenCapture()
        for index, monitor in enumerate(capture.monitors, start=1):
            print(f"Monitor {index}: {monitor}")
        frame = capture.capture()
        print(f"Capture OK: {frame.width}x{frame.height} ({frame.source})")
    except (RuntimeError, OSError) as exc:
        print(f"Screen capture unavailable: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

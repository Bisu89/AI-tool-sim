import numpy as np
import pytest

from sim_designer.capture.screen_capture import CaptureError, ScreenCapture


def test_capture_rejects_nonpositive_region_before_accessing_screen() -> None:
    with pytest.raises(CaptureError, match="positive"):
        ScreenCapture.__new__(ScreenCapture).capture((0, 0, 0, 100))


def test_capture_uses_monitor_marked_primary() -> None:
    class FakeMSS:
        monitors = [
            {"left": -100, "top": 0, "width": 200, "height": 100},
            {"left": -100, "top": 0, "width": 100, "height": 100, "is_primary": False},
            {"left": 0, "top": 0, "width": 100, "height": 100, "is_primary": True},
        ]

        def grab(self, region: dict[str, int]) -> np.ndarray:
            self.region = region
            return np.zeros((region["height"], region["width"], 4), dtype=np.uint8)

    fake = FakeMSS()
    capture = ScreenCapture.__new__(ScreenCapture)
    capture._mss = fake
    frame = capture.capture()
    assert frame.region == (0, 0, 100, 100)
    assert frame.image.shape == (100, 100, 3)

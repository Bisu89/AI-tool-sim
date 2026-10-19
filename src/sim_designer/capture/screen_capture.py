"""MSS-backed screen capture without fixed desktop coordinates."""

from datetime import datetime, timezone

import mss
import numpy as np

from sim_designer.models import ImageFrame


class CaptureError(RuntimeError):
    """Raised when a requested screen region cannot be captured."""


class ScreenCapture:
    """Capture a monitor or an explicitly selected screen rectangle."""

    def __init__(self) -> None:
        self._mss = mss.MSS()

    @property
    def monitors(self) -> list[dict[str, int]]:
        """Return monitor rectangles, excluding MSS's aggregate virtual monitor."""
        return [dict(m) for m in self._mss.monitors[1:]]

    def capture(self, region: tuple[int, int, int, int] | None = None) -> ImageFrame:
        """Capture a (left, top, width, height) region, or the primary monitor."""
        if region is None:
            available = self._mss.monitors[1:]
            if not available:
                raise CaptureError("No screen monitor is available.")
            monitor = next((m for m in available if m.get("is_primary")), available[0])
            box = {key: int(monitor[key]) for key in ("left", "top", "width", "height")}
        else:
            left, top, width, height = region
            if width <= 0 or height <= 0:
                raise CaptureError("Capture region must have positive width and height.")
            box = {"left": left, "top": top, "width": width, "height": height}
        try:
            shot = self._mss.grab(box)
        except (mss.exception.ScreenShotError, OSError) as exc:
            raise CaptureError(f"Could not capture screen region: {exc}") from exc
        bgra = np.asarray(shot)
        rgb = np.ascontiguousarray(bgra[:, :, :3][:, :, ::-1])
        return ImageFrame(rgb, rgb.shape[1], rgb.shape[0], datetime.now(timezone.utc),
                          "screen", (box["left"], box["top"], box["width"], box["height"]))

    def close(self) -> None:
        """Release MSS resources when the dashboard closes."""
        self._mss.close()

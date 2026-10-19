"""Report Python and optional application dependency availability."""

from importlib.metadata import PackageNotFoundError, version
import sys


PACKAGES = ("numpy", "opencv-contrib-python", "mss", "PySide6", "pydantic", "PyYAML", "mediapipe", "pytest")


def main() -> int:
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    failed = sys.version_info[:2] != (3, 11)
    for package in PACKAGES:
        try:
            print(f"{package}: {version(package)}")
        except PackageNotFoundError:
            print(f"{package}: not installed")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())

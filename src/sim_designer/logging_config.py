"""Consistent local logging setup."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure standard output logging with a safe fallback level."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

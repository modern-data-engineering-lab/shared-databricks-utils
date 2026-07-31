"""Logging wrapper for consistent, notebook-safe logging in Databricks."""

from __future__ import annotations

import logging
import sys

_DEFAULT_FORMAT = "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def get_logger(
    name: str,
    level: int | str = logging.INFO,
    *,
    fmt: str = _DEFAULT_FORMAT,
    datefmt: str = _DEFAULT_DATEFMT,
) -> logging.Logger:
    """Return a configured ``logging.Logger`` writing to stdout.

    Safe to call repeatedly with the same ``name`` (e.g. from a re-run notebook cell) without
    accumulating duplicate handlers or duplicate log lines.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
        logger.addHandler(handler)

    logger.propagate = False
    return logger

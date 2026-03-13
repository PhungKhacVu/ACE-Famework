"""Simple logging helper compatible with all Python environments."""
import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Return a named logger with a sensible default format.

    The logger writes to *stdout* so output is captured cleanly in
    a-Shell / a-Shell mini on iPhone.
    """
    from app.config import LOG_LEVEL

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    effective_level = level or LOG_LEVEL
    logger.setLevel(getattr(logging, effective_level.upper(), logging.INFO))
    return logger

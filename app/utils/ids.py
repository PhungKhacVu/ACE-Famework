"""Utility helpers."""

from __future__ import annotations

import uuid


def new_id() -> str:
    """Generate a short unique identifier."""
    return uuid.uuid4().hex[:12]

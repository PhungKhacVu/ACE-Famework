"""Bullet ranking helpers."""

from __future__ import annotations

from typing import List

from app.schemas.bullet import Bullet


def rank_bullets(bullets: List[Bullet], top_n: int = 5) -> List[Bullet]:
    """Return the top-n bullets sorted by helpfulness score descending."""
    return sorted(bullets, key=lambda b: b.score, reverse=True)[:top_n]

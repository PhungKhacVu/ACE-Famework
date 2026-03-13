"""
Ranking utilities — cosine similarity computed with stdlib only.

No numpy / scipy required, making this compatible with a-Shell on iPhone.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import List, Tuple

from app.schemas.bullet import Bullet


# ---------------------------------------------------------------------------
# Text vectorisation (bag-of-words, very lightweight)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Lower-case, strip punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return [t for t in text.split() if len(t) > 1]


def _bow_vector(tokens: List[str], vocab: List[str]) -> List[float]:
    """Build a bag-of-words TF vector aligned to *vocab*."""
    counts = Counter(tokens)
    total = sum(counts.values()) or 1
    return [counts.get(w, 0) / total for w in vocab]


# ---------------------------------------------------------------------------
# Core similarity function
# ---------------------------------------------------------------------------

def cosine_similarity(text_a: str, text_b: str) -> float:
    """
    Compute the cosine similarity between two strings.

    Returns a float in [0.0, 1.0] (1.0 = identical content).
    Uses bag-of-words TF vectors over a shared vocabulary.
    """
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    vocab = list(set(tokens_a) | set(tokens_b))
    vec_a = _bow_vector(tokens_a, vocab)
    vec_b = _bow_vector(tokens_b, vocab)

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# Bullet ranking helpers
# ---------------------------------------------------------------------------

def rank_bullets(
    bullets: List[Bullet],
    query: str = "",
    alpha: float = 0.5,
) -> List[Tuple[Bullet, float]]:
    """
    Rank bullets by a weighted combination of relevance + score.

    Parameters
    ----------
    bullets : list of Bullet
        Candidate bullets to rank.
    query : str
        The task text used to compute relevance.
    alpha : float
        Weight for semantic relevance vs. helpfulness score.
        0 → pure score-based; 1 → pure relevance-based.

    Returns
    -------
    Sorted list of (Bullet, combined_score) tuples, best first.
    """
    if not bullets:
        return []

    results: List[Tuple[Bullet, float]] = []
    for b in bullets:
        rel = cosine_similarity(query, b.content) if query else 0.5
        # Normalise score to [0, 1] range using a sigmoid-like transform
        raw_score = b.score
        norm_score = 1.0 / (1.0 + math.exp(-raw_score * 0.5))
        combined = alpha * rel + (1.0 - alpha) * norm_score
        results.append((b, combined))

    results.sort(key=lambda x: x[1], reverse=True)
    return results

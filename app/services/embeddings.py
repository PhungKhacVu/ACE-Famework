"""Simple vector-free similarity via token-overlap (Jaccard).

A real implementation would use sentence-transformers or an embedding API.
This default keeps the project dependency-free.
"""

from __future__ import annotations

import re
from typing import List


def _tokenize(text: str) -> set:
    return set(re.findall(r"\w+", text.lower()))


def jaccard_similarity(a: str, b: str) -> float:
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta and not tb:
        return 1.0
    union = ta | tb
    intersection = ta & tb
    return len(intersection) / len(union)


def cosine_similarity_vectors(v1: List[float], v2: List[float]) -> float:
    """Cosine similarity between two equal-length numeric vectors."""
    try:
        import numpy as np  # type: ignore

        a = np.array(v1, dtype=float)
        b = np.array(v2, dtype=float)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
    except ImportError:
        # Fallback pure-python implementation
        dot = sum(x * y for x, y in zip(v1, v2))
        norm_a = sum(x ** 2 for x in v1) ** 0.5
        norm_b = sum(y ** 2 for y in v2) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

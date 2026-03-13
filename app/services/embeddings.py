"""Simple local embedding service using character n-gram hashing (no ML model required)."""

from __future__ import annotations

import math
from collections import Counter


def _char_ngrams(text: str, n: int = 3) -> list[str]:
    text = text.lower()
    return [text[i : i + n] for i in range(len(text) - n + 1)]


def embed(text: str, dim: int = 64) -> list[float]:
    """Produce a fixed-length embedding vector via n-gram hashing trick."""
    ngrams = _char_ngrams(text)
    counts: Counter[int] = Counter()
    for ng in ngrams:
        h = hash(ng) % dim
        counts[h] += 1
    vec = [float(counts.get(i, 0)) for i in range(dim)]
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    if len(a) != len(b):
        raise ValueError("Vectors must have the same length.")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)

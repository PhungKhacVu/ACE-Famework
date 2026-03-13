"""Ranking helpers for bullet retrieval."""

from __future__ import annotations

from app.schemas.bullet import Bullet
from app.services.embeddings import cosine_similarity, embed


def rank_bullets(
    query: str,
    bullets: list[Bullet],
    top_k: int = 5,
    domain: str | None = None,
) -> list[Bullet]:
    """Return top-k bullets ranked by semantic similarity to the query."""
    if not bullets:
        return []

    query_emb = embed(query)
    scored: list[tuple[float, Bullet]] = []

    for b in bullets:
        if domain and b.domain not in (domain, "general"):
            continue
        emb = b.embedding or embed(b.content)
        b.embedding = emb
        sim = cosine_similarity(query_emb, emb)
        # Incorporate net_score as a secondary signal
        score = 0.7 * sim + 0.3 * max(0.0, min(1.0, b.net_score))
        scored.append((score, b))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored[:top_k]]

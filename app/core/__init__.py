"""Core package."""
from .merge_engine import MergeEngine
from .ranking import cosine_similarity, rank_bullets

__all__ = ["MergeEngine", "Pipeline", "cosine_similarity", "rank_bullets"]


def __getattr__(name):
    if name == "Pipeline":
        from .pipeline import Pipeline
        return Pipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

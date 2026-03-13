"""Evaluation helpers – score generated answers vs. ground truth."""

from __future__ import annotations

from typing import List

from app.services.embeddings import jaccard_similarity
from app.utils.logger import get_logger

logger = get_logger(__name__)


def exact_match(prediction: str, ground_truth: str) -> float:
    return 1.0 if prediction.strip().lower() == ground_truth.strip().lower() else 0.0


def token_overlap_f1(prediction: str, ground_truth: str) -> float:
    import re

    pred_tokens = set(re.findall(r"\w+", prediction.lower()))
    gt_tokens = set(re.findall(r"\w+", ground_truth.lower()))
    if not gt_tokens:
        return 0.0
    precision = len(pred_tokens & gt_tokens) / max(len(pred_tokens), 1)
    recall = len(pred_tokens & gt_tokens) / len(gt_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def jaccard_score(prediction: str, ground_truth: str) -> float:
    return jaccard_similarity(prediction, ground_truth)


def evaluate_batch(
    predictions: List[str],
    ground_truths: List[str],
) -> dict:
    """Return aggregate metrics for a list of prediction/ground-truth pairs."""
    if len(predictions) != len(ground_truths):
        raise ValueError("predictions and ground_truths must have the same length")

    scores = [
        {
            "exact_match": exact_match(p, g),
            "f1": token_overlap_f1(p, g),
            "jaccard": jaccard_score(p, g),
        }
        for p, g in zip(predictions, ground_truths)
    ]

    n = len(scores)
    summary = {
        "n": n,
        "avg_exact_match": sum(s["exact_match"] for s in scores) / n,
        "avg_f1": sum(s["f1"] for s in scores) / n,
        "avg_jaccard": sum(s["jaccard"] for s in scores) / n,
        "per_example": scores,
    }
    logger.info(
        "Evaluation: n=%d  avg_f1=%.3f  avg_jaccard=%.3f",
        n,
        summary["avg_f1"],
        summary["avg_jaccard"],
    )
    return summary

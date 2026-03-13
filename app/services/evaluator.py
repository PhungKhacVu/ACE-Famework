"""Simple evaluation helper."""

from __future__ import annotations

from app.schemas.task import TaskInput, TaskResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


def evaluate(tasks: list[TaskInput], results: list[TaskResult]) -> dict:
    """Compare results against ground truth and return basic metrics."""
    if not tasks or not results:
        return {"accuracy": 0.0, "count": 0}

    result_map = {r.task_id: r for r in results}
    correct = 0
    total = 0

    for task in tasks:
        if task.ground_truth is None:
            continue
        result = result_map.get(task.id)
        if result is None:
            continue
        total += 1
        # Simple exact / substring match (mock evaluation)
        if task.ground_truth.lower() in result.answer.lower():
            correct += 1

    accuracy = correct / total if total else 0.0
    logger.info("Evaluation: %d/%d correct (%.1f%%)", correct, total, accuracy * 100)
    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "avg_confidence": (
            sum(r.confidence for r in results) / len(results) if results else 0.0
        ),
    }

"""
ACE Pipeline — orchestrates Generator → Reflector → Curator → MergeEngine.

This is the main entry point for running a single task or a batch of tasks
through the full ACE adaptation cycle.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

from app.schemas.task import TaskInput
from app.schemas.result import TaskResult
from app.agents.generator import Generator
from app.agents.reflector import Reflector
from app.agents.curator import Curator
from app.agents.llm_service import LLMService
from app.core.merge_engine import MergeEngine
from app.storage.playbook_store import PlaybookStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Pipeline:
    """
    Runs the full ACE adaptation cycle for one or more tasks.

    Parameters
    ----------
    store : PlaybookStore
        The playbook storage backend.
    llm_provider : str, optional
        Override the LLM provider ("mock", "openai", "ollama").
    similarity_threshold : float
        Passed through to MergeEngine for deduplication.
    max_bullets : int
        Hard cap on playbook size.
    top_k_bullets : int
        Number of bullets the Generator retrieves from the playbook.
    """

    def __init__(
        self,
        store: Optional[PlaybookStore] = None,
        llm_provider: Optional[str] = None,
        similarity_threshold: float = 0.85,
        max_bullets: int = 200,
        top_k_bullets: int = 5,
    ) -> None:
        from app.config import PLAYBOOK_FILE, SIMILARITY_THRESHOLD, MAX_BULLETS

        self.store = store or PlaybookStore(PLAYBOOK_FILE)
        llm = LLMService(provider=llm_provider)

        self.generator = Generator(llm=llm, top_k_bullets=top_k_bullets)
        self.reflector = Reflector(llm=llm)
        self.curator = Curator(llm=llm)
        self.merge_engine = MergeEngine(
            store=self.store,
            similarity_threshold=similarity_threshold or SIMILARITY_THRESHOLD,
            max_bullets=max_bullets or MAX_BULLETS,
        )

    # ------------------------------------------------------------------
    # Single task
    # ------------------------------------------------------------------

    def run_task(self, task: TaskInput, adapt: bool = True) -> TaskResult:
        """
        Run the full pipeline for a single task.

        Parameters
        ----------
        task : TaskInput
        adapt : bool
            If True (default), run the Reflector + Curator + Merge steps
            to update the playbook after generation.

        Returns
        -------
        TaskResult
        """
        logger.info("=== Pipeline: task=%s domain=%s ===", task.id, task.domain)

        # Retrieve relevant bullets from the playbook
        bullets = self.store.search(task.instruction, domain=task.domain)

        # 1. Generate
        result = self.generator.run(task, bullets)

        if not adapt:
            return result

        # 2. Reflect
        result = self.reflector.run(task, result)

        # 3. Curate
        delta = self.curator.run(task, result)

        # 4. Merge
        merge_summary = self.merge_engine.apply(delta)
        logger.info("Merge complete: %s", merge_summary)

        # Persist updated playbook
        self.store.save()

        return result

    # ------------------------------------------------------------------
    # Batch
    # ------------------------------------------------------------------

    def run_batch(
        self,
        tasks: List[TaskInput],
        adapt: bool = True,
        output_path: Optional[str] = None,
    ) -> List[TaskResult]:
        """
        Run the pipeline on a list of tasks.

        Parameters
        ----------
        tasks : list of TaskInput
        adapt : bool
            Whether to run adaptation after each task.
        output_path : str, optional
            If provided, write results as JSON array to this path.

        Returns
        -------
        list of TaskResult
        """
        results: List[TaskResult] = []
        for i, task in enumerate(tasks, 1):
            logger.info("Batch %d/%d", i, len(tasks))
            result = self.run_task(task, adapt=adapt)
            results.append(result)

        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                json.dump([r.to_dict() for r in results], fh, ensure_ascii=False, indent=2)
            logger.info("Results written to %s", output_path)

        return results

    # ------------------------------------------------------------------
    # Evaluation helper
    # ------------------------------------------------------------------

    def evaluate(self, results: List[TaskResult]) -> dict:
        """
        Compute basic evaluation metrics over a list of TaskResults.

        Returns
        -------
        dict with keys: total, correct, incorrect, unknown, accuracy
        """
        total = len(results)
        correct = sum(1 for r in results if r.correct is True)
        incorrect = sum(1 for r in results if r.correct is False)
        unknown = total - correct - incorrect
        accuracy = correct / total if total > 0 else 0.0
        avg_confidence = (
            sum(r.confidence for r in results) / total if total > 0 else 0.0
        )
        return {
            "total": total,
            "correct": correct,
            "incorrect": incorrect,
            "unknown": unknown,
            "accuracy": round(accuracy, 4),
            "avg_confidence": round(avg_confidence, 4),
        }

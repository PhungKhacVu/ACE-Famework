"""ACE pipeline – orchestrates Generator → Reflector → Curator → Merge."""

from __future__ import annotations

from app.agents.curator import CuratorAgent
from app.agents.generator import GeneratorAgent
from app.agents.reflector import ReflectorAgent
from app.core.merge_engine import MergeEngine
from app.core.ranking import rank_bullets
from app.schemas.result import AdaptationResult
from app.schemas.task import TaskInput, TaskResult
from app.services.llm import BaseLLMService
from app.storage.playbook_store import PlaybookStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ACEPipeline:
    """Full ACE pipeline: generate → reflect → curate → merge."""

    def __init__(self, llm: BaseLLMService, store: PlaybookStore) -> None:
        self._store = store
        self._generator = GeneratorAgent(llm)
        self._reflector = ReflectorAgent(llm)
        self._curator = CuratorAgent(llm)
        self._merger = MergeEngine(store)

    # ------------------------------------------------------------------
    # Single-task execution (generation only, no adaptation)
    # ------------------------------------------------------------------

    def run_task(self, task: TaskInput, top_k: int = 5) -> TaskResult:
        """Generate an answer for a task using current playbook bullets."""
        bullets = rank_bullets(
            task.description,
            self._store.all(),
            top_k=top_k,
            domain=task.domain,
        )
        logger.info("Running task %s (%d bullets available)", task.id, len(bullets))
        result = self._generator.run(task, bullets)
        logger.info("Task %s → confidence=%.2f", task.id, result.confidence)
        return result

    # ------------------------------------------------------------------
    # Online adaptation (single task: generate + reflect + curate + merge)
    # ------------------------------------------------------------------

    def adapt_online(self, task: TaskInput, top_k: int = 5) -> TaskResult:
        """Run a task and adapt the playbook from the outcome immediately."""
        result = self.run_task(task, top_k=top_k)
        self._adapt_from_result(task, result)
        self._store.save()
        return result

    # ------------------------------------------------------------------
    # Offline adaptation (batch: reflect + curate + merge, no generation)
    # ------------------------------------------------------------------

    def adapt_offline(
        self,
        tasks: list[TaskInput],
        results: list[TaskResult],
    ) -> AdaptationResult:
        """Adapt playbook from a batch of pre-generated task results."""
        summary = AdaptationResult(tasks_processed=len(tasks))
        result_map = {r.task_id: r for r in results}

        for task in tasks:
            result = result_map.get(task.id)
            if result is None:
                logger.warning("No result found for task %s; skipping.", task.id)
                continue
            counts = self._adapt_from_result(task, result)
            summary.bullets_added += counts.get("added", 0)
            summary.bullets_updated += counts.get("updated", 0)
            summary.bullets_merged += counts.get("merged", 0)
            summary.task_results.append(result)

        self._store.save()
        logger.info(
            "Offline adaptation complete: +%d added, %d merged",
            summary.bullets_added,
            summary.bullets_merged,
        )
        return summary

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _adapt_from_result(
        self, task: TaskInput, result: TaskResult
    ) -> dict[str, int]:
        reflection = self._reflector.run(task, result)
        deltas = self._curator.run(reflection)
        if not deltas:
            return {"added": 0, "updated": 0, "merged": 0}
        return self._merger.merge(deltas)

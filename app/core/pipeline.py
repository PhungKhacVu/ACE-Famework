"""ACE pipeline – orchestrates Generator → Reflector → Curator → Merge.

Supports two modes:
- **offline adaptation**: run many tasks to build up the playbook
- **online adaptation**: run one task at inference time and adapt immediately
"""

from __future__ import annotations

from typing import List

from app.agents.curator import CuratorAgent
from app.agents.generator import GeneratorAgent
from app.agents.reflector import ReflectorAgent
from app.core.merge_engine import MergeEngine
from app.schemas.result import AgentOutput, TaskResult
from app.schemas.task import TaskInput
from app.services.llm import BaseLLMProvider
from app.storage.playbook_store import PlaybookStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ACEPipeline:
    """Full ACE pipeline with in-process agents and a local playbook store."""

    def __init__(
        self,
        store: PlaybookStore,
        provider: BaseLLMProvider | None = None,
    ) -> None:
        self._store = store
        self._generator = GeneratorAgent(provider=provider)
        self._reflector = ReflectorAgent(provider=provider)
        self._curator = CuratorAgent(provider=provider)
        self._merge = MergeEngine(store=store)

    # ------------------------------------------------------------------
    # Single-task processing
    # ------------------------------------------------------------------

    def run_task(self, task: TaskInput) -> TaskResult:
        """Process one task through the full pipeline and update the playbook."""
        logger.info("=== ACE Pipeline: task %s ===", task.id)

        bullets = self._store.all()
        bullet_ids = [b.id for b in bullets]

        # Generator
        gen_out: AgentOutput = self._generator.run(task, bullets)

        # Reflector
        ref_out: AgentOutput = self._reflector.run(task, gen_out.content)

        # Curator
        cur_out, delta = self._curator.run(task, ref_out.metadata, bullet_ids)

        # Merge
        merge_summary = self._merge.merge(delta)
        self._store.save()

        result = TaskResult(
            task_id=task.id,
            final_answer=gen_out.content,
            agent_outputs=[gen_out, ref_out, cur_out],
            bullets_used=bullet_ids[:5],
            metadata={"merge": merge_summary},
        )
        logger.info("Task %s complete. merge=%s", task.id, merge_summary)
        return result

    # ------------------------------------------------------------------
    # Batch modes
    # ------------------------------------------------------------------

    def offline_adaptation(self, tasks: List[TaskInput]) -> List[TaskResult]:
        """Run all tasks to adapt the playbook (no streaming, results collected)."""
        logger.info("Offline adaptation: %d tasks", len(tasks))
        results = []
        for task in tasks:
            results.append(self.run_task(task))
        logger.info(
            "Offline adaptation complete. Playbook now has %d bullets.",
            self._store.count(),
        )
        return results

    def online_adaptation(self, task: TaskInput) -> TaskResult:
        """Run one task at inference time and adapt immediately."""
        logger.info("Online adaptation for task: %s", task.id)
        return self.run_task(task)

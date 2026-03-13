"""Pipeline: orchestrates Generator → Reflector → Curator → MergeEngine."""
from __future__ import annotations
from typing import List
from app.schemas import TaskInput, TaskResult
from app.agents.generator import GeneratorAgent
from app.agents.reflector import ReflectorAgent
from app.agents.curator import CuratorAgent
from app.core.merge_engine import MergeEngine
from app.storage import PlaybookStore


class ACEPipeline:
    """End-to-end ACE pipeline for a single task."""

    def __init__(
        self,
        store: PlaybookStore | None = None,
        llm=None,
    ):
        self.store = store or PlaybookStore()
        self.generator = GeneratorAgent(llm=llm)
        self.reflector = ReflectorAgent(llm=llm)
        self.curator = CuratorAgent(llm=llm)
        self.merge_engine = MergeEngine()

    def run(self, task: TaskInput) -> TaskResult:
        """Run the full pipeline for *task* and persist updated playbook."""
        # Build playbook context string from top bullets
        bullets = self.store.load()
        context = "\n".join(
            f"- {b.text}" for b in sorted(bullets, key=lambda x: -x.confidence)[:5]
        )

        # Agent chain
        result = self.generator.run(task, playbook_context=context)
        result = self.reflector.run(result, task)
        result = self.curator.run(result, task)

        # Merge new bullets back into the playbook
        updated = self.merge_engine.merge(bullets, result.delta_bullets)
        self.store.save(updated)

        return result

    def run_batch(self, tasks: List[TaskInput]) -> List[TaskResult]:
        """Run the pipeline for a list of tasks sequentially."""
        return [self.run(t) for t in tasks]

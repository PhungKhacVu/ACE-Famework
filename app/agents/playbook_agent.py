"""Playbook agent: executes each step in a playbook sequentially."""

from __future__ import annotations

from datetime import datetime, timezone

from app.agents.base import BaseAgent
from app.schemas import Message, Playbook, Step, Task, TaskStatus


class PlaybookAgent(BaseAgent):
    """Executes each step of a playbook in order, accumulating context."""

    def run_playbook(self, task: Task, playbook: Playbook) -> Task:
        """Drive the task through every step of the playbook."""
        task.status = TaskStatus.RUNNING
        task.playbook_id = playbook.id

        # System context
        system_msg = Message(
            role="system",
            content=f"You are ACE executing playbook '{playbook.name}'. Goal: {task.goal}",
        )
        task.messages.append(system_msg)

        for step in playbook.steps:
            task = self._execute_step(task, step)
            if task.status == TaskStatus.FAILED:
                return task

        task.status = TaskStatus.DONE
        task.updated_at = datetime.now(timezone.utc).isoformat()
        return task

    def run(self, task: Task) -> Task:
        """Fallback: treat goal as single prompt (no playbook)."""
        from app.agents.simple_agent import SimpleAgent

        return SimpleAgent(self.llm).run(task)

    def _execute_step(self, task: Task, step: Step) -> Task:
        user_msg = Message(
            role="user",
            content=f"[Step: {step.name}] {step.instruction}",
        )
        task.messages.append(user_msg)
        try:
            reply = self.llm.chat(task.messages)
            task.messages.append(Message(role="assistant", content=reply))
            task.result = reply
        except Exception as exc:
            task.messages.append(Message(role="assistant", content=f"[error] {exc}"))
            task.result = f"[error] {exc}"
            task.status = TaskStatus.FAILED
        return task

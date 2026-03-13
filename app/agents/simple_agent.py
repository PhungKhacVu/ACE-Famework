"""Simple single-step agent: sends goal to LLM, records reply."""

from __future__ import annotations

from datetime import datetime, timezone

from app.agents.base import BaseAgent
from app.schemas import Message, Task, TaskStatus


class SimpleAgent(BaseAgent):
    """Sends the task goal as a user message and records the LLM reply."""

    def run(self, task: Task) -> Task:
        task.status = TaskStatus.RUNNING
        user_msg = Message(role="user", content=task.goal)
        task.messages.append(user_msg)

        try:
            reply = self.llm.chat(task.messages)
            task.messages.append(Message(role="assistant", content=reply))
            task.result = reply
            task.status = TaskStatus.DONE
        except Exception as exc:
            task.messages.append(
                Message(role="assistant", content=f"[error] {exc}")
            )
            task.result = f"[error] {exc}"
            task.status = TaskStatus.FAILED

        task.updated_at = datetime.now(timezone.utc).isoformat()
        return task

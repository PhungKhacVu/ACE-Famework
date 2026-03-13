"""Task result schema."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.utils.ids import new_id


class AgentOutput(BaseModel):
    """Raw output from a single agent step."""

    agent: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """The full result of running one task through the ACE pipeline."""

    id: str = Field(default_factory=new_id)
    task_id: str
    final_answer: str
    agent_outputs: List[AgentOutput] = Field(default_factory=list)
    bullets_used: List[str] = Field(default_factory=list)
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

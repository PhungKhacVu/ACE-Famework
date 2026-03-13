"""Task input schema."""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.utils.ids import new_id


class TaskInput(BaseModel):
    """A task that the ACE pipeline will process."""

    id: str = Field(default_factory=new_id)
    description: str
    context: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ground_truth: Optional[str] = None

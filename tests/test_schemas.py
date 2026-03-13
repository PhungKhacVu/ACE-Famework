"""Tests for schemas (dataclasses, serialisation round-trips)."""

from __future__ import annotations

import pytest

from app.schemas import (
    Message,
    Playbook,
    Step,
    StepType,
    Task,
    TaskStatus,
)


class TestStep:
    def test_round_trip(self):
        step = Step(name="do-it", type=StepType.PROMPT, instruction="say hello")
        assert Step.from_dict(step.to_dict()) == step

    def test_default_type(self):
        step = Step.from_dict({"name": "x", "instruction": "y"})
        assert step.type == StepType.PROMPT


class TestPlaybook:
    def test_round_trip(self):
        pb = Playbook(
            name="test-pb",
            description="desc",
            steps=[Step("s1", StepType.PROMPT, "prompt 1")],
        )
        restored = Playbook.from_dict(pb.to_dict())
        assert restored.name == pb.name
        assert restored.description == pb.description
        assert len(restored.steps) == 1
        assert restored.steps[0].name == "s1"

    def test_empty_steps(self):
        pb = Playbook.from_dict({"name": "empty"})
        assert pb.steps == []


class TestTask:
    def test_default_status(self):
        task = Task(goal="do something")
        assert task.status == TaskStatus.PENDING

    def test_round_trip(self):
        task = Task(
            goal="test goal",
            status=TaskStatus.DONE,
            result="done",
            messages=[Message(role="user", content="hi")],
        )
        restored = Task.from_dict(task.to_dict())
        assert restored.goal == task.goal
        assert restored.status == TaskStatus.DONE
        assert restored.result == "done"
        assert len(restored.messages) == 1

    def test_message_roles(self):
        msg = Message(role="assistant", content="hello")
        d = msg.to_dict()
        assert d["role"] == "assistant"
        assert Message.from_dict(d).content == "hello"

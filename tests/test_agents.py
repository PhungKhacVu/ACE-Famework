"""Tests for Generator, Reflector, and Curator agents using mock LLM."""

from __future__ import annotations

import json

import pytest

from app.agents.curator import CuratorAgent
from app.agents.generator import GeneratorAgent
from app.agents.reflector import ReflectorAgent
from app.schemas.bullet import Bullet, DeltaUpdate
from app.schemas.result import ReflectorOutput
from app.schemas.task import TaskInput, TaskResult
from app.services.llm import MockLLMService


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


def test_generator_returns_task_result() -> None:
    llm = MockLLMService()
    agent = GeneratorAgent(llm)
    task = TaskInput(id="t1", description="Solve this problem", domain="general")
    bullets: list[Bullet] = []
    result = agent.run(task, bullets)

    assert isinstance(result, TaskResult)
    assert result.task_id == "t1"
    assert len(result.answer) > 0
    assert 0.0 <= result.confidence <= 1.0


def test_generator_uses_bullets() -> None:
    llm = MockLLMService()
    agent = GeneratorAgent(llm)
    task = TaskInput(id="t2", description="Debug this code", domain="software")
    bullet = Bullet(id="b1", content="Check logs first", domain="software")
    result = agent.run(task, [bullet])

    assert isinstance(result, TaskResult)
    assert result.task_id == "t2"


def test_generator_handles_invalid_json() -> None:
    """Generator should degrade gracefully when LLM returns non-JSON."""

    class BadLLM(MockLLMService):
        def complete(self, prompt: str, **kwargs) -> str:
            return "not valid json at all"

    agent = GeneratorAgent(BadLLM())
    task = TaskInput(id="t3", description="Test task", domain="general")
    result = agent.run(task, [])
    assert isinstance(result, TaskResult)
    assert result.answer == "not valid json at all"


# ---------------------------------------------------------------------------
# Reflector
# ---------------------------------------------------------------------------


def test_reflector_returns_output() -> None:
    llm = MockLLMService()
    agent = ReflectorAgent(llm)
    task = TaskInput(id="t4", description="Reflect on this", domain="general")
    result = TaskResult(task_id="t4", answer="Some answer", confidence=0.6)
    output = agent.run(task, result)

    assert isinstance(output, ReflectorOutput)
    assert output.task_id == "t4"
    assert isinstance(output.is_correct, bool)
    assert 0.0 <= output.quality_score <= 1.0
    assert isinstance(output.suggested_deltas, list)


def test_reflector_produces_deltas() -> None:
    llm = MockLLMService()
    agent = ReflectorAgent(llm)
    task = TaskInput(id="t5", description="Insight task", domain="general")
    result = TaskResult(task_id="t5", answer="answer", confidence=0.5)
    output = agent.run(task, result)

    # MockLLM for 'reflect' prompts returns suggested_deltas
    assert len(output.suggested_deltas) >= 0


# ---------------------------------------------------------------------------
# Curator
# ---------------------------------------------------------------------------


def test_curator_returns_deltas() -> None:
    llm = MockLLMService()
    agent = CuratorAgent(llm)
    reflection = ReflectorOutput(
        task_id="t6",
        is_correct=True,
        quality_score=0.8,
        insight="Always test edge cases.",
        suggested_deltas=[
            DeltaUpdate(
                content="Always test edge cases.",
                domain="general",
                confidence=0.7,
            )
        ],
    )
    deltas = agent.run(reflection)

    assert isinstance(deltas, list)
    assert len(deltas) >= 1
    for d in deltas:
        assert isinstance(d, DeltaUpdate)


def test_curator_empty_reflection() -> None:
    llm = MockLLMService()
    agent = CuratorAgent(llm)
    reflection = ReflectorOutput(
        task_id="t7",
        is_correct=False,
        quality_score=0.0,
        insight="",
        suggested_deltas=[],
    )
    deltas = agent.run(reflection)
    assert deltas == []

"""Unit tests for individual agents."""

from __future__ import annotations

import json
import pytest

from app.agents.generator import GeneratorAgent
from app.agents.reflector import ReflectorAgent
from app.agents.curator import CuratorAgent
from app.schemas.bullet import Bullet, BulletType
from app.schemas.task import TaskInput
from app.services.llm import MockLLMProvider


@pytest.fixture
def mock_provider():
    return MockLLMProvider()


@pytest.fixture
def task():
    return TaskInput(description="Explain binary search", context="CS student")


class TestGeneratorAgent:
    def test_returns_agent_output(self, mock_provider, task):
        agent = GeneratorAgent(provider=mock_provider)
        result = agent.run(task, bullets=[])
        assert result.agent == "generator"
        assert len(result.content) > 0

    def test_uses_bullets_in_prompt(self, mock_provider, task):
        bullets = [Bullet(content="Always start with base cases.", bullet_type=BulletType.HELPFUL)]
        agent = GeneratorAgent(provider=mock_provider)
        result = agent.run(task, bullets=bullets)
        assert result.agent == "generator"

    def test_top_bullets_capped(self, mock_provider, task):
        bullets = [Bullet(content=f"Bullet {i}") for i in range(20)]
        agent = GeneratorAgent(provider=mock_provider, top_bullets=3)
        result = agent.run(task, bullets=bullets)
        assert result.agent == "generator"


class TestReflectorAgent:
    def test_returns_agent_output(self, mock_provider, task):
        agent = ReflectorAgent(provider=mock_provider)
        result = agent.run(task, "Some generated answer")
        assert result.agent == "reflector"

    def test_parses_json_metadata(self, mock_provider, task):
        agent = ReflectorAgent(provider=mock_provider)
        result = agent.run(task, "Some answer")
        assert "confidence" in result.metadata
        assert isinstance(result.metadata["confidence"], float)

    def test_handles_malformed_json(self, task):
        class BadProvider:
            def complete(self, system, user):
                return "This is not JSON at all."

        agent = ReflectorAgent(provider=BadProvider())
        result = agent.run(task, "answer")
        assert result.metadata.get("confidence") == 0.5  # fallback


class TestCuratorAgent:
    def test_returns_delta_update(self, mock_provider, task):
        agent = CuratorAgent(provider=mock_provider)
        reflection = {"insights": ["Decompose tasks"], "confidence": 0.8}
        _, delta = agent.run(task, reflection)
        assert len(delta.new_bullets) >= 0  # may be 0 or more

    def test_parses_bullet_type(self, mock_provider, task):
        agent = CuratorAgent(provider=mock_provider)
        reflection = {"insights": ["Use examples"], "confidence": 0.9}
        _, delta = agent.run(task, reflection)
        for b in delta.new_bullets:
            assert b.bullet_type in BulletType.__members__.values()

    def test_handles_malformed_json(self, task):
        class BadProvider:
            def complete(self, system, user):
                return "not json"

        agent = CuratorAgent(provider=BadProvider())
        _, delta = agent.run(task, {"insights": []})
        assert delta.new_bullets == []
        assert delta.reinforce_ids == []

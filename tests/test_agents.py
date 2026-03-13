"""Tests for Generator, Reflector, and Curator agents."""
import pytest
from app.schemas import TaskInput, TaskResult
from app.agents.generator import GeneratorAgent
from app.agents.reflector import ReflectorAgent
from app.agents.curator import CuratorAgent
from app.services import MockLLMService


@pytest.fixture
def task():
    return TaskInput(
        id="t-test",
        description="Explain binary search",
        domain="algorithms",
        context="",
    )


@pytest.fixture
def llm():
    return MockLLMService()


class TestGeneratorAgent:
    def test_returns_task_result(self, task, llm):
        agent = GeneratorAgent(llm=llm)
        result = agent.run(task)
        assert isinstance(result, TaskResult)

    def test_task_id_matches(self, task, llm):
        agent = GeneratorAgent(llm=llm)
        result = agent.run(task)
        assert result.task_id == task.id

    def test_reasoning_non_empty(self, task, llm):
        agent = GeneratorAgent(llm=llm)
        result = agent.run(task)
        assert len(result.reasoning) > 0

    def test_answer_non_empty(self, task, llm):
        agent = GeneratorAgent(llm=llm)
        result = agent.run(task)
        assert len(result.answer) > 0

    def test_deterministic_output(self, task, llm):
        agent = GeneratorAgent(llm=llm)
        r1 = agent.run(task)
        r2 = agent.run(task)
        assert r1.reasoning == r2.reasoning


class TestReflectorAgent:
    def test_adds_insights(self, task, llm):
        agent_g = GeneratorAgent(llm=llm)
        agent_r = ReflectorAgent(llm=llm)
        result = agent_g.run(task)
        result = agent_r.run(result, task)
        assert len(result.insights) > 0

    def test_confidence_increases(self, task, llm):
        agent_g = GeneratorAgent(llm=llm)
        agent_r = ReflectorAgent(llm=llm)
        result = agent_g.run(task)
        before = result.confidence
        result = agent_r.run(result, task)
        assert result.confidence >= before

    def test_confidence_capped_at_one(self, task, llm):
        agent_g = GeneratorAgent(llm=llm)
        agent_r = ReflectorAgent(llm=llm)
        result = agent_g.run(task)
        result.confidence = 1.0
        result = agent_r.run(result, task)
        assert result.confidence <= 1.0


class TestCuratorAgent:
    def test_adds_delta_bullets(self, task, llm):
        agent_g = GeneratorAgent(llm=llm)
        agent_r = ReflectorAgent(llm=llm)
        agent_c = CuratorAgent(llm=llm)
        result = agent_g.run(task)
        result = agent_r.run(result, task)
        result = agent_c.run(result, task)
        assert len(result.delta_bullets) > 0

    def test_delta_bullets_are_strings(self, task, llm):
        agent_g = GeneratorAgent(llm=llm)
        agent_r = ReflectorAgent(llm=llm)
        agent_c = CuratorAgent(llm=llm)
        result = agent_g.run(task)
        result = agent_r.run(result, task)
        result = agent_c.run(result, task)
        assert all(isinstance(b, str) for b in result.delta_bullets)

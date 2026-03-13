"""Tests for LLM services and agents."""

from __future__ import annotations

import pytest

from app.agents.simple_agent import SimpleAgent
from app.agents.playbook_agent import PlaybookAgent
from app.schemas import Message, Playbook, Step, StepType, Task, TaskStatus
from app.services.llm import MockLLMBackend, get_llm_backend


class TestMockLLMBackend:
    def test_hello_keyword(self):
        llm = MockLLMBackend()
        msgs = [Message(role="user", content="hello there")]
        reply = llm.chat(msgs)
        assert "ACE" in reply

    def test_help_keyword(self):
        llm = MockLLMBackend()
        msgs = [Message(role="user", content="I need help")]
        reply = llm.chat(msgs)
        assert "commands" in reply.lower()

    def test_unknown_prompt(self):
        llm = MockLLMBackend()
        msgs = [Message(role="user", content="random gibberish xyz")]
        reply = llm.chat(msgs)
        assert "mock" in reply.lower()

    def test_empty_messages(self):
        llm = MockLLMBackend()
        reply = llm.chat([])
        assert isinstance(reply, str)

    def test_get_llm_backend_mock(self):
        backend = get_llm_backend("mock")
        assert isinstance(backend, MockLLMBackend)

    def test_get_llm_backend_unknown(self):
        with pytest.raises(ValueError, match="Unknown LLM backend"):
            get_llm_backend("openai")


class TestSimpleAgent:
    def test_run_sets_status_done(self):
        agent = SimpleAgent(MockLLMBackend())
        task = Task(goal="say hello")
        result = agent.run(task)
        assert result.status == TaskStatus.DONE
        assert result.result != ""

    def test_run_adds_messages(self):
        agent = SimpleAgent(MockLLMBackend())
        task = Task(goal="ask something")
        result = agent.run(task)
        roles = [m.role for m in result.messages]
        assert "user" in roles
        assert "assistant" in roles


class TestPlaybookAgent:
    def _make_playbook(self) -> Playbook:
        return Playbook(
            name="test-pb",
            steps=[
                Step("step1", StepType.PROMPT, "say hello"),
                Step("step2", StepType.PROMPT, "summarize"),
            ],
        )

    def test_run_playbook_done(self):
        agent = PlaybookAgent(MockLLMBackend())
        task = Task(goal="test playbook goal")
        pb = self._make_playbook()
        result = agent.run_playbook(task, pb)
        assert result.status == TaskStatus.DONE
        assert result.playbook_id == pb.id

    def test_run_playbook_messages_count(self):
        agent = PlaybookAgent(MockLLMBackend())
        task = Task(goal="run it")
        pb = self._make_playbook()
        result = agent.run_playbook(task, pb)
        # system + (user+assistant) * 2 steps = 5
        assert len(result.messages) == 5

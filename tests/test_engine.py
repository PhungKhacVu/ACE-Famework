"""Tests for ACEEngine."""
from __future__ import annotations

import pytest

from app.agents.mock_llm import MockLLM
from app.core.engine import ACEEngine
from app.schemas import Playbook


@pytest.fixture()
def simple_playbook() -> Playbook:
    return Playbook(
        id="test-pb",
        name="Test Playbook",
        description="Unit test playbook",
        steps=[
            {"id": "s1", "description": "Step one", "prompt": "Do step one"},
            {"id": "s2", "description": "Step two", "prompt": "Do step two"},
        ],
    )


def test_run_returns_all_steps(simple_playbook):
    engine = ACEEngine()
    result = engine.run(simple_playbook)
    assert result["playbook_id"] == "test-pb"
    assert len(result["results"]) == 2
    assert all(r["ok"] for r in result["results"])


def test_run_with_custom_llm(simple_playbook):
    llm = MockLLM({"[L4-Executive] Do step one": "Custom response"})
    engine = ACEEngine(llm=llm, layer="executive")
    result = engine.run(simple_playbook)
    assert result["results"][0]["response"] == "Custom response"


def test_metadata_counts(simple_playbook):
    engine = ACEEngine()
    result = engine.run(simple_playbook)
    assert result["metadata"]["total_steps"] == 2
    assert result["metadata"]["successful"] == 2


def test_empty_playbook():
    pb = Playbook(id="empty", name="Empty", description="", steps=[])
    engine = ACEEngine()
    result = engine.run(pb)
    assert result["results"] == []
    assert result["metadata"]["total_steps"] == 0


def test_invalid_layer():
    with pytest.raises(ValueError, match="Unknown layer"):
        ACEEngine(layer="nonexistent")


def test_layer_prefix_in_response():
    pb = Playbook(
        id="p",
        name="P",
        description="",
        steps=[{"id": "s1", "description": "d", "prompt": "hello"}],
    )
    engine = ACEEngine(layer="aspirational")
    result = engine.run(pb)
    assert "[L1-Aspirational]" in result["results"][0]["response"]


def test_mock_llm_batch():
    llm = MockLLM()
    responses = llm.batch(["a", "b"])
    assert len(responses) == 2
    assert "a" in responses[0]
    assert "b" in responses[1]

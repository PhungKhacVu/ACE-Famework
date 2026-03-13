"""ACE Engine — orchestrates playbook execution across cognitive layers.

The ACE (Autonomous Cognitive Entity) framework models six layers:

  1. Aspirational    — mission & ethics
  2. Global Strategy — long-range planning
  3. Agent Model     — self-knowledge
  4. Executive       — task decomposition
  5. Cognitive Ctrl  — moment-to-moment decisions
  6. Task            — direct action / tool use

In this local-first MVP each layer is represented by a single prompt
prefix that is prepended to each playbook step before it is sent to the
LLM (or the :class:`~app.agents.mock_llm.MockLLM` during testing).
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.mock_llm import MockLLM
from app.schemas import Playbook, RunResult, StepResult

# Layer prompt prefixes — kept short so the mock LLM output stays readable
_LAYER_PREFIXES: Dict[str, str] = {
    "aspirational": "[L1-Aspirational]",
    "global_strategy": "[L2-GlobalStrategy]",
    "agent_model": "[L3-AgentModel]",
    "executive": "[L4-Executive]",
    "cognitive_ctrl": "[L5-CognitiveCtrl]",
    "task": "[L6-Task]",
}


class ACEEngine:
    """Run a :class:`~app.schemas.Playbook` step-by-step using an LLM.

    Parameters
    ----------
    llm:
        Language model instance.  Defaults to :class:`~app.agents.mock_llm.MockLLM`.
    layer:
        Which ACE layer is executing.  Controls the prompt prefix applied to
        every step.  Defaults to ``"task"`` (Layer 6).
    """

    def __init__(self, llm: MockLLM | None = None, layer: str = "task") -> None:
        self._llm = llm or MockLLM()
        if layer not in _LAYER_PREFIXES:
            raise ValueError(
                f"Unknown layer '{layer}'. Valid layers: {list(_LAYER_PREFIXES)}"
            )
        self._prefix = _LAYER_PREFIXES[layer]

    def run(self, playbook: Playbook) -> RunResult:
        """Execute every step in *playbook* and return aggregated results."""
        results: List[StepResult] = []
        for step in playbook.get("steps", []):
            prompt = f"{self._prefix} {step['prompt']}"
            try:
                response = self._llm.chat(prompt)
                results.append(StepResult(step_id=step["id"], response=response, ok=True))
            except Exception as exc:  # noqa: BLE001
                results.append(
                    StepResult(step_id=step["id"], response=str(exc), ok=False)
                )

        metadata: Dict[str, Any] = {
            "layer": self._prefix,
            "total_steps": len(playbook.get("steps", [])),
            "successful": sum(1 for r in results if r["ok"]),
        }
        return RunResult(
            playbook_id=playbook["id"],
            results=results,
            metadata=metadata,
        )

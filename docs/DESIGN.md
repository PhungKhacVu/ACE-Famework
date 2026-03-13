# ACE Framework – Design Document

## Overview

ACE (Autonomous Cognitive Engine) is a **local-first**, **zero-dependency** Python
framework for agentic workflows. It is designed to run on any device that has Python 3.9+
including **a-Shell** and **a-Shell mini** on iPhone/iPad.

---

## Goals

| Goal | Detail |
|------|--------|
| **Local-first** | No cloud service required; runs fully offline |
| **Zero runtime deps** | Pure Python stdlib; only pytest for tests |
| **a-Shell friendly** | Works inside a-Shell / a-Shell mini on iOS |
| **Mock LLM** | Ships with a deterministic mock; swap for real API later |
| **Playbook-driven** | Reusable JSON playbooks for structured workflows |
| **Testable** | Full pytest suite; all core logic unit-tested |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                    CLI (app/cli.py)              │
│    ace run | ace task list | ace playbook …      │
└────────────────────┬────────────────────────────┘
                     │
              ┌──────▼──────┐
              │  ACEEngine  │  (app/core/engine.py)
              └──┬──────┬───┘
          ┌──────┘      └──────┐
   ┌──────▼──────┐    ┌────────▼───────┐
   │   Agents    │    │    Storage     │
   │ SimpleAgent │    │ PlaybookStore  │
   │PlaybookAgent│    │  TaskStore     │
   └──────┬──────┘    └────────────────┘
          │
   ┌──────▼──────┐
   │ LLM Service │  MockLLMBackend (default)
   └─────────────┘
```

---

## Data Model

### Playbook
A reusable, ordered list of **Steps**. Stored as JSON in `data/playbooks/`.

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "steps": [
    { "name": "string", "type": "prompt|tool|condition", "instruction": "string" }
  ],
  "created_at": "ISO-8601"
}
```

### Task
A concrete run of a goal (with or without a playbook). Stored as JSON in `data/tasks/`.

```json
{
  "id": "uuid",
  "playbook_id": "uuid | ''",
  "goal": "string",
  "status": "pending | running | done | failed",
  "messages": [{ "role": "user|assistant|system", "content": "string" }],
  "result": "string",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

---

## Extending ACE

### Adding a real LLM backend

1. Create `app/services/my_llm.py` implementing `LLMBackend.chat()`.
2. Register it in `get_llm_backend()` in `app/services/llm.py`.
3. Set `ACE_LLM_BACKEND=my_llm` in the environment.

### Adding a new agent

1. Subclass `BaseAgent` in `app/agents/`.
2. Implement `run(task) -> Task`.
3. Wire it in `ACEEngine.run_task()` or via a CLI flag.

---

## Running on a-Shell

```sh
pip install pytest          # only if you want to run tests
cd ~/ACE-Famework
python -m app.cli run "hello"
python -m app.cli task list
python -m app.cli playbook import data/playbooks/sample_playbook.json
```

No extra packages needed beyond Python 3.9+.

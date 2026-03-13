# ACE-Famework

> **Autonomous Cognitive Engine** – a local-first, zero-dependency Python framework
> for agentic workflows. Runs on any machine with Python 3.9+, including
> **a-Shell / a-Shell mini** on iPhone & iPad.

---

## Quick Start

```sh
# 1. Clone
git clone https://github.com/PhungKhacVu/ACE-Famework.git
cd ACE-Famework

# 2. (Optional) Install test runner
pip install pytest

# 3. Run a task using the mock LLM (no API key needed)
python -m app.cli run "hello"

# 4. Run with a sample playbook
python -m app.cli playbook import data/playbooks/sample_playbook.json
python -m app.cli playbook list
python -m app.cli run "run the hello-world playbook" --playbook pb-sample-001

# 5. View results
python -m app.cli task list
python -m app.cli task show <task-id>
```

---

## Features

| Feature | Detail |
|---------|--------|
| **Local-first** | Runs 100% offline; no cloud API required |
| **Zero runtime deps** | Pure Python stdlib (3.9+) |
| **Mock LLM** | Deterministic replies for testing; swap for real LLM later |
| **Playbook store** | Reusable JSON playbooks for structured multi-step workflows |
| **Task store** | Every run is persisted as JSON in `data/tasks/` |
| **CLI** | `ace run`, `ace task`, `ace playbook` sub-commands |
| **pytest suite** | Full unit-test coverage of all core modules |
| **a-Shell ready** | Tested design for a-Shell / a-Shell mini on iOS |

---

## Project Structure

```
ACE-Famework/
├── app/
│   ├── cli.py               # argparse CLI entry-point
│   ├── config.py            # Config dataclass (env vars / JSON file)
│   ├── schemas.py           # Task, Playbook, Step, Message dataclasses
│   ├── core/
│   │   └── engine.py        # ACEEngine – orchestrates everything
│   ├── agents/
│   │   ├── base.py          # BaseAgent ABC
│   │   ├── simple_agent.py  # Single-prompt agent
│   │   └── playbook_agent.py# Multi-step playbook agent
│   ├── services/
│   │   └── llm.py           # LLMBackend interface + MockLLMBackend
│   └── storage/
│       ├── playbook_store.py# JSON playbook persistence
│       └── task_store.py    # JSON task persistence
├── data/
│   ├── playbooks/           # Playbook JSON files
│   └── tasks/               # Task JSON files (auto-created)
├── tests/                   # pytest unit tests
├── docs/
│   └── DESIGN.md            # Architecture & design notes
├── pyproject.toml
└── requirements.txt         # pytest only
```

---

## CLI Reference

```sh
# Run a task (mock LLM, no playbook)
python -m app.cli run "your goal here"

# Run a task using a stored playbook
python -m app.cli run "your goal" --playbook <playbook-id>

# List / inspect tasks
python -m app.cli task list
python -m app.cli task show <task-id>
python -m app.cli task show <task-id> --messages

# Manage playbooks
python -m app.cli playbook list
python -m app.cli playbook import path/to/playbook.json
python -m app.cli playbook show <playbook-id>
python -m app.cli playbook delete <playbook-id>
```

---

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `ACE_DATA_DIR` | `data/` | Directory for JSON storage |
| `ACE_LLM_BACKEND` | `mock` | LLM backend (`mock` built-in) |
| `ACE_MAX_STEPS` | `10` | Max steps per playbook run |

You can also pass `--config path/to/config.json` to any command.

---

## Running Tests

```sh
# install pytest (only needed once)
pip install pytest

# run all tests
pytest

# run a specific file
pytest tests/test_engine.py -v
```

---

## Playbook Format

```json
{
  "id": "my-playbook-id",
  "name": "my-playbook",
  "description": "What this playbook does",
  "steps": [
    {
      "name": "step-name",
      "type": "prompt",
      "instruction": "Instruction sent to the LLM for this step"
    }
  ]
}
```

See `data/playbooks/sample_playbook.json` for a working example.

---

## Extending ACE

See [docs/DESIGN.md](docs/DESIGN.md) for the full architecture and extension guide.
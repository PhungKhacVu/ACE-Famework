# ACE Framework – Adaptive Continual Experience

> A local-first Python MVP of the ACE framework: an adaptive learning system where a pipeline of agents continuously improves a shared **playbook** of actionable insights from task experience.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Project Structure](#project-structure)
5. [CLI Commands](#cli-commands)
6. [Configuration](#configuration)
7. [Running Tests](#running-tests)
8. [Extending with a Real LLM](#extending-with-a-real-llm)
9. [Docs](#docs)

---

## Overview

ACE (Adaptive Continual Experience) is an agent framework that learns from task executions and stores reusable knowledge as **bullets** in a persistent playbook. The system has three agents:

| Agent | Role |
|-------|------|
| **Generator** | Produces an answer for a task using relevant playbook bullets |
| **Reflector** | Evaluates the answer and extracts lessons (insights + delta updates) |
| **Curator** | Distils raw insights into clean, generalizable playbook bullets |

A **Merge Engine** integrates the new bullets into the playbook with semantic deduplication, preserving helpful/harmful counters and confidence scores.

---

## Architecture

```
TaskInput
    │
    ▼
┌─────────────┐    top-k bullets     ┌──────────────┐
│  Generator  │◄────────────────────│ PlaybookStore │
└─────────────┘                      └──────────────┘
    │                                        ▲
    │ TaskResult                             │ merge()
    ▼                                        │
┌─────────────┐   ReflectorOutput   ┌──────────────┐
│  Reflector  │──────────────────►  │   Curator    │──► DeltaUpdates
└─────────────┘                     └──────────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ MergeEngine  │
                                    └──────────────┘
```

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/PhungKhacVu/ACE-Famework.git
cd ACE-Famework

# 2. Create a virtual environment (Python 3.11+)
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the example env file (optional – mock mode works without any config)
cp .env.example .env

# 5. Run a sample task
python -m app.cli run-task --input data/sample_tasks.json

# 6. Run online adaptation (generates + adapts playbook immediately)
python -m app.cli adapt-online --input data/sample_tasks.json

# 7. Show playbook
python -m app.cli show-playbook

# 8. Evaluate
python -m app.cli evaluate --input data/sample_tasks.json
```

---

## Project Structure

```
ACE-Famework/
├── app/
│   ├── agents/          # Generator, Reflector, Curator
│   ├── core/            # Pipeline, MergeEngine, Ranking
│   ├── schemas/         # Pydantic models (Bullet, Task, Result)
│   ├── services/        # LLM abstraction, Embeddings, Evaluator
│   ├── storage/         # PlaybookStore (local JSON)
│   ├── utils/           # Logger, ID helpers
│   ├── cli.py           # Typer CLI entry points
│   ├── main.py          # Programmatic API
│   └── config.py        # Environment-based configuration
├── data/
│   ├── sample_tasks.json
│   └── seed_playbook.json
├── docs/
│   └── ACE_Overview.md
├── tests/
│   ├── conftest.py
│   ├── test_playbook_store.py
│   ├── test_merge_engine.py
│   ├── test_agents.py
│   └── test_pipeline.py
├── .env.example
├── pyproject.toml
└── requirements.txt
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `python -m app.cli run-task` | Generate answers (no playbook modification) |
| `python -m app.cli adapt-online` | Generate + immediately adapt per task |
| `python -m app.cli adapt-offline` | Generate all, then adapt batch |
| `python -m app.cli show-playbook` | Display ranked playbook bullets |
| `python -m app.cli evaluate` | Compare results against ground truth |

All commands accept `--input` / `-i` for task JSON and `--playbook` / `-p` for a custom playbook path.

---

## Configuration

Copy `.env.example` to `.env` and set:

| Variable | Default | Description |
|----------|---------|-------------|
| `ACE_LLM_PROVIDER` | `mock` | `mock` / `openai` / `ollama` |
| `ACE_PLAYBOOK_PATH` | `data/playbook.json` | Playbook storage path |
| `ACE_SIM_THRESHOLD` | `0.85` | Deduplication similarity threshold |
| `ACE_LOG_LEVEL` | `INFO` | Log verbosity |
| `OPENAI_API_KEY` | – | Required when provider = `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Required when provider = `ollama` |

---

## Running Tests

```bash
# Install dev dependencies (included in requirements.txt)
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

All tests use the **mock** LLM provider and temporary file storage – no API keys or network access required.

---

## Extending with a Real LLM

Set `ACE_LLM_PROVIDER=openai` and `OPENAI_API_KEY=sk-...` in your `.env` file.  
Or set `ACE_LLM_PROVIDER=ollama` with a running Ollama instance.

The `BaseLLMService` interface in `app/services/llm.py` makes it easy to add custom providers.

---

## Docs

See the [`docs/`](docs/) directory for framework design documentation.
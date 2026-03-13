# ACE Framework – Adaptive Cognition Engineering

A **local-first Python MVP** for the ACE (Adaptive Cognition Engineering) framework. Runs entirely on your machine with no API keys required by default.

## What is ACE?

ACE is a framework for building agents that continuously improve through a **Generator → Reflector → Curator → Merge** pipeline:

1. **Generator** – produces an initial answer using playbook bullets as prior knowledge  
2. **Reflector** – analyses the answer and extracts actionable insights  
3. **Curator** – converts insights into structured `DeltaUpdate` objects  
4. **Merge Engine** – integrates delta updates into the playbook with deduplication  

The playbook is a local JSON file containing `Bullet` objects that accumulate helpful/harmful knowledge over time.

---

## Quick Start

### 1. Prerequisites

- Python 3.10+

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify the CLI works

```bash
python -m app.cli --help
```

---

## Usage

### Run a single task

```bash
python -m app.cli run-task --description "How do I sort a list in Python?"
```

### Offline adaptation (batch of tasks)

```bash
python -m app.cli adapt-offline --tasks-file data/sample_tasks.json
```

### Online adaptation (single task, real-time)

```bash
python -m app.cli adapt-online --description "Explain recursion with an example"
```

### Show the current playbook

```bash
python -m app.cli show-playbook
```

### Evaluate against ground truth

```bash
python -m app.cli evaluate --tasks-file data/sample_tasks.json
```

### Run with a specific LLM provider

```bash
# Default: mock (no API key required)
python -m app.cli run-task --description "..." --provider mock

# OpenAI (requires OPENAI_API_KEY env var)
OPENAI_API_KEY=sk-... python -m app.cli run-task --description "..." --provider openai

# Ollama (requires local Ollama server)
python -m app.cli run-task --description "..." --provider ollama
```

---

## Run Tests

```bash
pytest
```

Or with coverage:

```bash
pytest --cov=app
```

---

## Project Structure

```
ACE-Famework/
├── pyproject.toml          # Project metadata and build config
├── requirements.txt        # Python dependencies
├── README.md
├── app/
│   ├── cli.py              # CLI entrypoint (typer)
│   ├── config.py           # Config from environment variables
│   ├── schemas/
│   │   ├── bullet.py       # Bullet, DeltaUpdate models
│   │   ├── task.py         # TaskInput model
│   │   └── result.py       # TaskResult, AgentOutput models
│   ├── agents/
│   │   ├── generator.py    # Generator agent
│   │   ├── reflector.py    # Reflector agent
│   │   └── curator.py      # Curator agent
│   ├── core/
│   │   ├── pipeline.py     # ACEPipeline orchestrator
│   │   ├── merge_engine.py # Bullet merge + deduplication
│   │   └── ranking.py      # Bullet ranking helpers
│   ├── storage/
│   │   ├── playbook_store.py  # Local JSON playbook store
│   │   └── files.py           # Atomic JSON read/write
│   ├── services/
│   │   ├── llm.py          # LLM abstraction (mock/openai/ollama)
│   │   ├── embeddings.py   # Similarity functions
│   │   └── evaluator.py    # Evaluation metrics
│   └── utils/
│       ├── logger.py       # Structured logging
│       └── ids.py          # UUID generation
├── data/
│   ├── playbook.json           # Local playbook storage
│   ├── sample_tasks.json       # Sample tasks for offline adaptation
│   └── sample_ground_truth.json
├── tests/
│   ├── test_merge_engine.py
│   ├── test_playbook_store.py
│   ├── test_agents.py
│   └── test_pipeline.py
└── docs/
    └── ACE_Overview.md
```

---

## Configuration

All settings can be overridden with environment variables:

| Variable | Default | Description |
|---|---|---|
| `ACE_LLM_PROVIDER` | `mock` | LLM provider: `mock`, `openai`, `ollama` |
| `OPENAI_API_KEY` | _(empty)_ | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3` | Ollama model name |
| `ACE_PLAYBOOK_PATH` | `data/playbook.json` | Path to playbook JSON file |
| `ACE_DEDUP_THRESHOLD` | `0.85` | Jaccard similarity threshold for deduplication |

---

## Architecture

```
TaskInput
    │
    ▼
GeneratorAgent ──(playbook bullets)──► answer
    │
    ▼
ReflectorAgent ──(answer)──► insights + confidence
    │
    ▼
CuratorAgent ──(insights)──► DeltaUpdate
    │
    ▼
MergeEngine ──► PlaybookStore (JSON) ──► TaskResult
```

---

## License

MIT

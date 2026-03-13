# ACE Framework

A **free, local-first Adaptive Cognition Engine** — a lightweight Python framework
that improves through experience by maintaining a self-updating playbook of
heuristics. Runs fully offline on any Python 3.9+ environment, including
**a-Shell / a-Shell mini on iPhone**.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/PhungKhacVu/ACE-Famework.git
cd ACE-Famework

# 2. No install required for core — but add pytest for tests
pip install pytest

# 3. Run tests
python -m pytest tests/ -v

# 4. Show the playbook
python -m app.cli show-playbook

# 5. Run tasks (generate answers using mock LLM)
python -m app.cli run-task --input data/sample_tasks.json --no-adapt

# 6. Run full adaptation (learn from tasks and grow the playbook)
python -m app.cli adapt --input data/sample_tasks.json
```

---

## Project Structure

```
ACE-Famework/
├── app/
│   ├── agents/
│   │   ├── curator.py        # Curator: insights → DeltaUpdate
│   │   ├── generator.py      # Generator: task + bullets → answer
│   │   ├── llm_service.py    # LLM abstraction (mock/openai/ollama)
│   │   └── reflector.py      # Reflector: output → insights + confidence
│   ├── core/
│   │   ├── merge_engine.py   # Merge DeltaUpdates into the playbook
│   │   ├── pipeline.py       # Orchestrates the full ACE cycle
│   │   └── ranking.py        # Cosine similarity (stdlib only)
│   ├── schemas/
│   │   ├── bullet.py         # Bullet + DeltaUpdate dataclasses
│   │   ├── result.py         # TaskResult dataclass
│   │   └── task.py           # TaskInput dataclass
│   ├── storage/
│   │   └── playbook_store.py # JSON-backed playbook storage
│   ├── utils/
│   │   ├── ids.py            # UUID generation
│   │   └── logger.py         # Logging helper
│   ├── cli.py                # CLI entry point
│   └── config.py             # Environment-based configuration
├── data/
│   ├── playbook.json         # Seeded playbook (edit freely)
│   ├── sample_tasks.json     # Example tasks
│   └── sample_ground_truth.json
├── tests/
│   ├── test_agents.py
│   ├── test_merge_engine.py
│   ├── test_pipeline.py
│   └── test_playbook_store.py
├── docs/
│   ├── ACE_Framework_Concepts.md  # Design explanation
│   ├── MOBILE_GUIDE.md            # a-Shell / iPhone guide
│   └── SETUP.md                   # Detailed setup instructions
├── .env.example
└── requirements.txt
```

---

## CLI Reference

```bash
# All commands accept --playbook and --provider flags
python -m app.cli --help

# Show top bullets in the playbook
python -m app.cli show-playbook [--limit 20] [--domain coding]

# Run tasks (generation only, no learning)
python -m app.cli run-task --input data/sample_tasks.json --no-adapt

# Run full adaptation loop (generates answers + learns)
python -m app.cli adapt --input data/sample_tasks.json

# Search the playbook
python -m app.cli search-playbook --query "error handling" [--domain coding]

# Add a bullet manually
python -m app.cli add-bullet --content "Your heuristic here" [--domain general]

# Evaluate results
python -m app.cli evaluate --input data/sample_tasks.json
python -m app.cli evaluate --results /path/to/results.json
```

---

## LLM Providers

| Provider | Setup | Notes |
|----------|-------|-------|
| `mock` (default) | none | Fully offline, deterministic — great for testing |
| `openai` | Set `OPENAI_API_KEY` | Any OpenAI-compatible API |
| `ollama` | Run Ollama locally | Free, local model (e.g. Llama 3) |

```bash
# Use Ollama
python -m app.cli adapt --input data/sample_tasks.json --provider ollama
```

---

## Configuration

Copy `.env.example` to `.env` and source it:

```bash
cp .env.example .env
source .env  # or: set -a && source .env && set +a
```

Key variables: `ACE_LLM_PROVIDER`, `OPENAI_API_KEY`, `OLLAMA_BASE_URL`,
`ACE_SIMILARITY_THRESHOLD`, `ACE_MAX_BULLETS`, `ACE_LOG_LEVEL`.

---

## Documentation

- [Setup Guide](docs/SETUP.md) — step-by-step instructions
- [Mobile Guide](docs/MOBILE_GUIDE.md) — a-Shell / iPhone specific guide
- [ACE Concepts](docs/ACE_Framework_Concepts.md) — design & architecture

---

## Design Goals

- ✅ **Free** — no paid APIs required
- ✅ **Local-first** — runs fully offline with mock provider
- ✅ **Lightweight** — stdlib only, no numpy/ML frameworks
- ✅ **Mobile-friendly** — works on a-Shell / a-Shell mini (iPhone)
- ✅ **Testable** — 51 unit tests, runs in < 1 second
- ✅ **Extensible** — swap LLM provider without changing application code
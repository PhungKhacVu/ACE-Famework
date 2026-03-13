# ACE Framework — Local-First Agentic Context Engineering MVP

A **fully offline, zero-cost** implementation of the ACE (Agentic Context Engineering) framework.  
Runs on any Python 3.9+ device — including **iPhone with a-Shell / a-Shell mini** — with no API keys,
no cloud services, and no paid accounts required.

---

## What Is ACE?

ACE is a self-improving agent framework. Instead of answering once and forgetting, each agent run:

1. **Generates** a reasoned answer using playbook context
2. **Reflects** to extract actionable insights
3. **Curates** insights into candidate playbook bullets
4. **Merges** the bullets back into a local JSON playbook

Over time the playbook accumulates knowledge that makes future answers better.

```
Task → Generator → Reflector → Curator → MergeEngine → Playbook (updated)
         ↑___________________________________________________|
```

---

## Project Structure

```
ACE-Famework/
├── README.md
├── requirements.txt          # only: pytest
├── pyproject.toml
├── bootstrap.sh              # one-command setup for a-Shell
├── app/
│   ├── cli.py                # CLI entrypoint  (python -m app.cli)
│   ├── config.py             # env-based config
│   ├── schemas/              # Bullet, TaskInput, TaskResult dataclasses
│   ├── agents/               # Generator, Reflector, Curator
│   │   ├── generator.py
│   │   ├── reflector.py
│   │   └── curator.py
│   ├── core/
│   │   ├── merge_engine.py   # Jaccard-similarity dedup + merge
│   │   └── pipeline.py       # full agent chain
│   ├── services/             # MockLLMService (offline, deterministic)
│   └── storage/
│       └── playbook_store.py # JSON file persistence
├── data/
│   ├── playbook.json         # persisted bullets (auto-created)
│   └── sample_tasks.json     # 3 sample tasks to run
├── tests/                    # 32 pytest tests (all pass)
│   ├── test_merge_engine.py
│   ├── test_playbook_store.py
│   ├── test_agents.py
│   └── test_pipeline.py
└── docs/
    └── ACE_Framework_Analysis.md
```

---

## Quick Start (Desktop / Linux / macOS)

```bash
# Clone
git clone https://github.com/PhungKhacVu/ACE-Famework.git
cd ACE-Famework

# Install the only dependency (pytest, for running tests)
pip install pytest

# Run tests
pytest tests/ -v

# Run sample tasks
python -m app.cli run-task --input data/sample_tasks.json

# Show the resulting playbook
python -m app.cli show-playbook
```

---

## Setup on iPhone — a-Shell / a-Shell mini (Step-by-Step)

> **a-Shell** and **a-Shell mini** are free iOS terminal apps that include Python 3.
> Everything below works completely offline after the initial `git clone`.

### Step 1 — Install a-Shell

Open the App Store and search for **a-Shell** (free) or **a-Shell mini** (free, lighter).  
Install either one.

### Step 2 — Open a-Shell and clone the repo

Tap the app to open a terminal, then paste these commands **one line at a time**:

```sh
cd ~
```

```sh
git clone https://github.com/PhungKhacVu/ACE-Famework.git
```

```sh
cd ACE-Famework
```

### Step 3 — Bootstrap (installs pytest and runs everything)

```sh
sh bootstrap.sh
```

This single command will:
- Upgrade pip
- Install `pytest`
- Run all 32 tests (should show **32 passed**)
- Run the 3 sample tasks through the pipeline
- Display the resulting playbook

### Step 4 — Manual commands (copy-paste each line separately)

**Run the sample tasks:**
```sh
python -m app.cli run-task --input data/sample_tasks.json
```

**Show current playbook bullets:**
```sh
python -m app.cli show-playbook
```

**Clear the playbook and start fresh:**
```sh
python -m app.cli clear-playbook
```

**Run all tests:**
```sh
python -m pytest tests/ -v
```

**Run just one test file:**
```sh
python -m pytest tests/test_merge_engine.py -v
```

### Step 5 — Create your own tasks

Create a custom task file directly in a-Shell:

```sh
cat > data/my_tasks.json << 'EOF'
[
  {
    "id": "my-task-1",
    "description": "How do I manage files efficiently in a-Shell?",
    "domain": "mobile-dev",
    "context": "Using a-Shell on iPhone 15"
  }
]
EOF
```

Then run it:
```sh
python -m app.cli run-task --input data/my_tasks.json
```

---

## CLI Reference

```
python -m app.cli [--playbook PATH] <command>

Commands:
  run-task       --input PATH    Run tasks from a JSON file through the ACE pipeline
  show-playbook                  Display all playbook bullets sorted by confidence
  clear-playbook                 Remove all bullets from the playbook

Options:
  --playbook PATH   Path to the playbook JSON file (default: data/playbook.json)
```

### Examples

```sh
# Use a custom playbook location
python -m app.cli --playbook /tmp/my_playbook.json run-task --input data/sample_tasks.json

# Check help
python -m app.cli --help
python -m app.cli run-task --help
```

---

## Configuration (Environment Variables)

All settings have sensible defaults so the app works with zero configuration.

| Variable | Default | Description |
|---|---|---|
| `ACE_DATA_DIR` | `data/` | Directory for data files |
| `ACE_PLAYBOOK_PATH` | `data/playbook.json` | Path to the playbook file |
| `ACE_LLM_PROVIDER` | `mock` | LLM backend (`mock` = offline, no API key) |
| `ACE_MERGE_THRESHOLD` | `0.85` | Jaccard similarity threshold for deduplication |

### Set an env variable in a-Shell

```sh
export ACE_MERGE_THRESHOLD=0.7
python -m app.cli run-task --input data/sample_tasks.json
```

---

## How It Works

### 1. Mock LLM (default — fully offline)

The built-in `MockLLMService` uses a small template pool selected deterministically by hashing
the input. This means:
- **No internet required**
- **No API key required**
- **Fully reproducible** — the same task always produces the same output
- All tests pass in CI and on device without any configuration

### 2. Deduplication (Jaccard Similarity)

The MergeEngine compares new bullet candidates to existing playbook bullets using
**word-level Jaccard similarity** (pure Python, no numpy needed):

```
similarity = |words_A ∩ words_B| / |words_A ∪ words_B|
```

If similarity ≥ threshold (default 0.85): update existing bullet  
If similarity < threshold: insert as new bullet

### 3. Playbook JSON Format

```json
[
  {
    "id": "...",
    "text": "Always decompose complex tasks before acting",
    "helpful_count": 5,
    "harmful_count": 1,
    "confidence": 0.83,
    "tags": [],
    "created_at": 1700000000.0,
    "updated_at": 1700000100.0
  }
]
```

You can edit `data/playbook.json` directly in a text editor (or `vi` in a-Shell).

---

## Extending the Framework

### Plug in a Real LLM (e.g., Ollama running locally on a Mac)

Set these environment variables before running:

```sh
export ACE_LLM_PROVIDER=openai
export ACE_LLM_BASE_URL=http://192.168.1.100:11434/v1
export ACE_LLM_API_KEY=ollama
export ACE_LLM_MODEL=llama3
```

> See `docs/ACE_Framework_Analysis.md` for a full Ollama integration example.

### Add New Agent Behaviour

1. Add a method to `MockLLMService` in `app/services/__init__.py`
2. Create a new agent in `app/agents/`
3. Insert it into the pipeline chain in `app/core/pipeline.py`

---

## Running Tests

```sh
# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_merge_engine.py -v
python -m pytest tests/test_playbook_store.py -v
python -m pytest tests/test_agents.py -v
python -m pytest tests/test_pipeline.py -v
```

Expected output: **32 passed**

---

## Free & Local — Why This Stack

| Requirement | Solution |
|---|---|
| No API costs | Built-in mock LLM (pure Python) |
| No cloud | JSON file storage on local disk |
| No heavy deps | Zero runtime dependencies (stdlib only) |
| Works on iPhone | Compatible with a-Shell Python 3.9+ |
| Reproducible tests | Deterministic mock, no network calls |
| Easy to extend | Clear interfaces, small files |

---

## Troubleshooting

**`python` not found in a-Shell**  
→ a-Shell uses `python` (not `python3`). Try: `python --version`

**`git clone` fails**  
→ Check your internet connection. After cloning, the rest works offline.

**`pip install pytest` is slow**  
→ Normal on first run. Subsequent runs use the cache and are instant.

**`ModuleNotFoundError: No module named 'app'`**  
→ Make sure you run commands from the repo root (`cd ACE-Famework`)

**`Permission denied: data/playbook.json`**  
→ Run `chmod 644 data/playbook.json` or use `--playbook /tmp/playbook.json`

---

## Documentation

- [`docs/ACE_Framework_Analysis.md`](docs/ACE_Framework_Analysis.md) — Architecture deep-dive and extension guide (Vietnamese + English)

---

## License

This project is open source. See the repository for details.
# Setup Guide — ACE Framework

## Requirements

- Python 3.9 or later (3.11+ recommended)
- No external packages required for offline/mock mode
- `pytest` only needed to run tests

## Step 1 — Clone the repo

```bash
git clone https://github.com/PhungKhacVu/ACE-Famework.git
cd ACE-Famework
```

## Step 2 — (Optional) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS / a-Shell
# Windows: .venv\Scripts\activate
```

## Step 3 — Install dependencies

For offline/mock mode (default), **no packages are required**.

To run the test suite:
```bash
pip install pytest
```

To use the OpenAI or Ollama providers, no extra packages are needed either — the code uses Python's built-in `urllib`.

## Step 4 — Run the CLI

All commands are run from the project root with:

```bash
python -m app.cli <command> [options]
```

### Show current playbook

```bash
python -m app.cli show-playbook
```

### Run tasks (generate answers only)

```bash
python -m app.cli run-task --input data/sample_tasks.json --no-adapt
```

### Run full adaptation cycle (learn from tasks)

```bash
python -m app.cli adapt --input data/sample_tasks.json
```

### Search the playbook

```bash
python -m app.cli search-playbook --query "error handling"
```

### Add a bullet manually

```bash
python -m app.cli add-bullet --content "Always test edge cases" --domain coding
```

### Evaluate results

```bash
# Re-run tasks and evaluate
python -m app.cli evaluate --input data/sample_tasks.json

# Evaluate pre-saved results
python -m app.cli run-task --input data/sample_tasks.json --output /tmp/results.json
python -m app.cli evaluate --results /tmp/results.json
```

## Step 5 — Run tests

```bash
python -m pytest tests/ -v
```

Expected: **51 tests pass** in < 1 second.

## Step 6 — Configure (optional)

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

Key settings:

| Variable | Default | Description |
|---|---|---|
| `ACE_LLM_PROVIDER` | `mock` | `mock` / `openai` / `ollama` |
| `OPENAI_API_KEY` | *(empty)* | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | Model name |
| `OLLAMA_MODEL` | `llama3` | Ollama model name |
| `ACE_PLAYBOOK_FILE` | `data/playbook.json` | Playbook path |
| `ACE_SIMILARITY_THRESHOLD` | `0.85` | Dedup threshold |
| `ACE_MAX_BULLETS` | `200` | Max playbook size |
| `ACE_LOG_LEVEL` | `INFO` | Log verbosity |

## Troubleshooting

**`ModuleNotFoundError: No module named 'app'`**
→ Run from the project root directory (`cd ACE-Famework`).

**`FileNotFoundError: data/playbook.json`**
→ The playbook file is created automatically on first `adapt` run, or use `data/playbook.json` which comes pre-seeded.

**Tests fail with import errors**
→ Make sure you are running `python -m pytest` (not just `pytest`) from the project root.

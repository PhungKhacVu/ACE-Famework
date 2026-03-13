# ACE Framework — Local-First MVP

**ACE** (Autonomous Cognitive Entity) is a layered AI agent framework that
runs entirely on your device — no cloud, no API key, no subscription.

```
python -m app.cli run hello-ace
```

---

## Features

| Feature | Status |
|---------|--------|
| Python local-first CLI | ✅ |
| Zero runtime dependencies | ✅ |
| Mock LLM for offline testing | ✅ |
| JSON playbook store | ✅ |
| 6 ACE cognitive layers | ✅ |
| pytest unit tests (27) | ✅ |
| a-Shell / iPhone instructions | ✅ |

---

## Quick Start

```sh
# Clone
git clone https://github.com/PhungKhacVu/ACE-Famework
cd ACE-Famework

# List playbooks
python -m app.cli list

# Show a playbook
python -m app.cli show hello-ace

# Run a playbook (uses built-in MockLLM — fully offline)
python -m app.cli run hello-ace

# Run under a specific ACE layer
python -m app.cli run hello-ace --layer executive

# Run tests
pip install pytest
python -m pytest tests/ -v
```

---

## Project Layout

```
ACE-Famework/
├── app/
│   ├── cli.py              # Entry point: python -m app.cli
│   ├── config.py           # Path configuration (env-overrideable)
│   ├── schemas.py          # TypedDict data models
│   ├── agents/
│   │   └── mock_llm.py     # Deterministic mock LLM (no API key)
│   ├── core/
│   │   └── engine.py       # ACE 6-layer engine
│   ├── services/
│   │   └── playbook.py     # Playbook CRUD service
│   └── storage/
│       └── json_store.py   # JSON-backed key/value store
├── data/
│   └── playbooks/
│       └── sample.json     # Sample "Hello ACE" playbook
├── tests/                  # pytest test suite (27 tests)
├── docs/
│   └── mobile-shell.md     # 📱 iPhone / a-Shell setup guide
├── pyproject.toml
└── requirements.txt
```

---

## ACE Cognitive Layers

The engine wraps each playbook step with the appropriate layer prefix:

| # | Layer | Key focus |
|---|-------|-----------|
| 1 | Aspirational | Mission & ethics |
| 2 | Global Strategy | Long-range planning |
| 3 | Agent Model | Self-knowledge |
| 4 | Executive | Task decomposition |
| 5 | Cognitive Control | Moment-to-moment decisions |
| 6 | Task | Direct action / tool use |

Run a playbook under any layer:

```sh
python -m app.cli run hello-ace --layer aspirational
python -m app.cli run hello-ace --layer cognitive_ctrl
```

---

## Custom Playbooks

Drop a JSON file into `data/playbooks/`:

```json
{
  "id": "my-plan",
  "name": "My Plan",
  "description": "A custom playbook",
  "steps": [
    {
      "id": "step-1",
      "description": "Define objective",
      "prompt": "What is the most important thing to do right now?"
    }
  ]
}
```

Then run:

```sh
python -m app.cli run my-plan
```

---

## Configuration

| Environment variable | Default | Purpose |
|----------------------|---------|---------|
| `ACE_DATA_DIR` | `./data` | Root directory for playbooks and store |

---

## 📱 iPhone / a-Shell Setup

Running on an iPhone with [a-Shell](https://holzschu.github.io/a-Shell_iOS/)
or **a-Shell mini** (free)?  See the step-by-step guide:

👉 **[docs/mobile-shell.md](docs/mobile-shell.md)**

Minimal copy-paste setup for iPhone:

```sh
lg2 clone https://github.com/PhungKhacVu/ACE-Famework ~/ACE-Famework
cd ~/ACE-Famework
python -m app.cli list
python -m app.cli run hello-ace
```

No internet connection required after cloning. Works in airplane mode. 🛫

---

## Running Tests

```sh
pip install pytest        # one-time
python -m pytest tests/ -v
```

Expected: **27 passed**.

---

## License

MIT

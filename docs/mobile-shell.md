# Running ACE Framework on iPhone with a-Shell / a-Shell mini

This guide gives you **copy-pasteable commands** to set up and run the ACE
Framework CLI directly on an iPhone using [a-Shell](https://holzschu.github.io/a-Shell_iOS/)
or **a-Shell mini** (free, no subscription required).

---

## Prerequisites

| App | Price | Download |
|-----|-------|----------|
| a-Shell | Free (IAP for extras) | [App Store](https://apps.apple.com/app/id1469754761) |
| a-Shell mini | **Free** | [App Store](https://apps.apple.com/app/id1543900761) |

Both apps ship with **Python 3** and **pip** built-in. No external computer
is needed.

---

## 1 · Install git (one-time)

a-Shell includes a lightweight `lg2` (libgit2-based) git wrapper. Enable the
full `git` alias:

```sh
# Inside a-Shell / a-Shell mini
lg2 clone https://github.com/PhungKhacVu/ACE-Famework ~/ACE-Famework
```

If `lg2` is not available, use `pickPackage` to install it:

```sh
pickPackage lg2
```

---

## 2 · Clone the repository

```sh
lg2 clone https://github.com/PhungKhacVu/ACE-Famework ~/ACE-Famework
cd ~/ACE-Famework
```

---

## 3 · Install Python dependencies

ACE Framework has **zero runtime dependencies** — only `pytest` is needed for
testing. The CLI runs with the built-in Python 3.

```sh
# Install pytest (only needed if you want to run tests)
pip install pytest
```

> **Tip for a-Shell mini:** `pip` works the same way. If you see a permission
> error, try `pip install --user pytest`.

---

## 4 · Verify the installation

```sh
python -m app.cli --help
```

Expected output:

```
usage: ace [-h] {list,show,run} ...

ACE Framework — local-first autonomous cognitive entity CLI

positional arguments:
  {list,show,run}
    list           List all available playbooks
    show           Show a playbook (human-readable by default)
    run            Run a playbook through the ACE engine
```

---

## 5 · Run your first playbook

```sh
# List available playbooks
python -m app.cli list
```
```
┌────────────────────────────────────────────────────┐
│  ACE Framework — Playbooks                         │
└────────────────────────────────────────────────────┘
  ID                        Name                  Steps
  ────────────────────────  ────────────────────  ─────────
  hello-ace                 Hello ACE             3 step(s)
```

```sh
# Inspect the sample playbook (human-readable)
python -m app.cli show hello-ace

# Inspect as raw JSON (machine-readable / pipe-friendly)
python -m app.cli show hello-ace --json

# Run it (uses the built-in mock LLM — no internet, no API key)
python -m app.cli run hello-ace
```
```
┌────────────────────────────────────────────────────┐
│  Running: hello-ace  [task]                        │
└────────────────────────────────────────────────────┘
  ✓ Step 1/3: step-1
    → [MockLLM] Acknowledged: ...
  ✓ Step 2/3: step-2
    → [MockLLM] Acknowledged: ...
  ✓ Step 3/3: step-3
    → [MockLLM] Acknowledged: ...
  ────────────────────────────────────────────────────
  Results: 3/3 successful
```

Run under a specific ACE layer (e.g. Executive, Layer 4):

```sh
python -m app.cli run hello-ace --layer executive
```

Available layers: `aspirational`, `global_strategy`, `agent_model`,
`executive`, `cognitive_ctrl`, `task` (default).

Add `--json` to get a machine-readable JSON result (useful for piping):

```sh
python -m app.cli run hello-ace --json | python -m json.tool
```

---

## 6 · Run the test suite

```sh
python -m pytest tests/ -v
```

All 33 tests should pass in under 1 second.

---

## 7 · Create your own playbook

Playbook files live in `data/playbooks/`. Create a new JSON file:

```sh
cat > data/playbooks/my-plan.json << 'EOF'
{
  "id": "my-plan",
  "name": "My Plan",
  "description": "Custom playbook created on iPhone",
  "steps": [
    {
      "id": "step-1",
      "description": "Clarify objective",
      "prompt": "What is the single most important objective right now?"
    },
    {
      "id": "step-2",
      "description": "Next action",
      "prompt": "What is the very next physical action I can take?"
    }
  ]
}
EOF
```

Then run it:

```sh
python -m app.cli run my-plan
```

---

## 8 · Offline / airplane mode

The ACE Framework is **fully local-first**. After the initial `lg2 clone` you
need no network connection:

- No API keys required.
- The built-in `MockLLM` generates deterministic responses — perfect for
  planning and testing workflows without internet.
- All data is stored locally under `data/store/`.

---

## 9 · Tips for a-Shell / a-Shell mini

| Tip | Command |
|-----|---------|
| Navigate home | `cd ~` |
| List files | `ls -la` |
| Edit a file | `ed filename` or paste content with `cat > file << 'EOF'` |
| Set environment variable | `export ACE_DATA_DIR=/path/to/data` |
| Suppress colours (e.g. for piping) | `NO_COLOR=1 python -m app.cli list` |
| Get raw JSON output | `python -m app.cli run hello-ace --json` |
| Pretty-print JSON output | `python -m app.cli run hello-ace --json \| python -m json.tool` |
| Share output | Tap-and-hold → Copy in a-Shell |

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'`

Make sure you are inside the repo directory:

```sh
cd ~/ACE-Famework
python -m app.cli list
```

### `pip: command not found`

```sh
python -m pip install pytest
```

### `lg2: command not found`

```sh
pickPackage lg2
```

---

## Summary — Minimal Setup (copy-paste block)

```sh
# 1. Clone
lg2 clone https://github.com/PhungKhacVu/ACE-Famework ~/ACE-Famework

# 2. Enter repo
cd ~/ACE-Famework

# 3. Run (no install needed!)
python -m app.cli list
python -m app.cli run hello-ace
```

That's it — local-first, free, works offline. 🎉

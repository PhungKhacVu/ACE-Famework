# ACE Framework — Concepts & Design

## What is ACE?

**ACE (Adaptive Cognition Engine)** is a local-first framework for building AI agents that improve through experience. Unlike static AI systems, an ACE agent maintains a **playbook** — a growing collection of heuristics (bullets) — and updates it after every task.

## Core Loop

```
Task Input
    │
    ▼
┌─────────────┐
│  Generator  │◄── Playbook Bullets (retrieved by search)
└─────────────┘
    │ (output + reasoning trace)
    ▼
┌─────────────┐
│  Reflector  │◄── Ground truth (if available)
└─────────────┘
    │ (insights + confidence)
    ▼
┌─────────────┐
│   Curator   │
└─────────────┘
    │ (DeltaUpdate: new bullets + counter adjustments)
    ▼
┌──────────────┐
│ MergeEngine  │
└──────────────┘
    │ (deduplicated, counter-updated playbook)
    ▼
┌──────────────┐
│ PlaybookStore│ (persisted to disk as JSON)
└──────────────┘
```

## Key Concepts

### Bullet
A bullet is the fundamental unit of the ACE playbook — a concise, actionable heuristic such as:

> "Break complex problems into smaller, well-defined sub-problems before attempting to solve them."

Each bullet tracks:
- `helpful_count` — how often it led to correct answers
- `harmful_count` — how often it led to wrong answers
- `confidence` = `helpful / (helpful + harmful)`
- `score` = `helpful - harmful`

### DeltaUpdate
The output of the Curator agent. Contains:
- `new_bullets` — freshly distilled heuristics
- `helpful_ids` — IDs of existing bullets that helped (increment their counter)
- `harmful_ids` — IDs of existing bullets that hurt (increment their harmful counter)

### MergeEngine
Applies a DeltaUpdate to the PlaybookStore:
1. Deduplicates new bullets using cosine similarity (bag-of-words)
2. Updates helpful/harmful counters
3. Prunes lowest-scoring bullets if the store exceeds the cap

### Generator
Retrieves the top-k most relevant bullets for a task (by keyword similarity + score), builds a structured prompt, calls the LLM, and parses the response.

### Reflector
Analyses the Generator's output. Compares it to ground truth when available, assigns confidence, and distils insights for the Curator.

### Curator
Transforms Reflector insights into a DeltaUpdate — new bullets + counter adjustments.

## Provider Architecture

The LLM layer is fully abstracted. Three providers are supported:

| Provider | Requires | Use when |
|----------|---------|----------|
| `mock`   | nothing | testing, offline demo, a-Shell |
| `openai` | `OPENAI_API_KEY` | using OpenAI or compatible API |
| `ollama` | local Ollama server | running a local model (e.g. Llama 3) |

Set via environment variable: `ACE_LLM_PROVIDER=mock`

## Design Principles

1. **Local-first** — runs fully offline with the mock provider
2. **Free** — no paid APIs required for the core functionality
3. **Lightweight** — stdlib only (no numpy, no heavy ML frameworks)
4. **Mobile-friendly** — works in a-Shell / a-Shell mini on iPhone
5. **Incremental** — the playbook grows and improves with each task
6. **Transparent** — every step produces human-readable reasoning traces

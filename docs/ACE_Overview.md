# ACE Framework Overview

## Core Concepts

### Bullet
A `Bullet` is the fundamental unit of knowledge in the playbook. Each bullet has:
- `content` – the knowledge statement
- `bullet_type` – `helpful`, `harmful`, or `neutral`
- `helpful_count` / `harmful_count` – usage counters
- `confidence` – initial confidence (0–1)
- `tags` – categorical labels
- `score` – derived helpfulness ratio (helpful / total)

### DeltaUpdate
A `DeltaUpdate` is produced by the Curator agent and contains:
- `new_bullets` – new bullets to add to the playbook
- `reinforce_ids` – IDs of existing bullets to increment `helpful_count`
- `penalise_ids` – IDs of existing bullets to increment `harmful_count`

### Pipeline
The pipeline runs four stages for each task:
1. **Generator** – retrieves top-ranked bullets, prompts LLM
2. **Reflector** – reviews the generator output, extracts insights
3. **Curator** – converts insights to a `DeltaUpdate`
4. **Merge Engine** – applies the delta, deduplicates via Jaccard similarity

### Adaptation Modes
- **Offline** – batch process many tasks to build up the playbook before deployment
- **Online** – process tasks at inference time, immediately adapting the playbook

## LLM Providers

| Provider | Description |
|---|---|
| `mock` | Deterministic responses for local dev/testing |
| `openai` | OpenAI API (requires `OPENAI_API_KEY`) |
| `ollama` | Local Ollama server (e.g. llama3) |

## Similarity & Deduplication

The merge engine uses **Jaccard token-overlap similarity** to detect near-duplicate bullets. The threshold is configurable via `ACE_DEDUP_THRESHOLD` (default: 0.85).

For production use, replace `jaccard_similarity` in `app/services/embeddings.py` with sentence-transformer embeddings or an embedding API for semantic similarity.

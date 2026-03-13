# ACE Framework – Design Overview

## What is ACE?

**ACE (Adaptive Continual Experience)** is a framework for building AI agents that learn continuously from task execution. Unlike static RAG or one-shot prompting systems, ACE maintains a living **playbook** of actionable insights that improves with every task.

---

## Core Concepts

### Bullet
The atomic unit of the playbook. Each bullet captures a reusable insight:
- `content` – the actionable lesson
- `domain` – knowledge area (software, general, productivity…)
- `confidence` – how reliable this bullet is (0–1)
- `helpful_count` / `harmful_count` – feedback counters
- `net_score` – composite ranking signal

### DeltaUpdate
A proposed change from the Curator agent to the playbook. May add a new bullet or update an existing one.

### Playbook
A persistent collection of bullets stored locally as JSON. Supports domain filtering and ranking by net score.

---

## Agent Roles

### Generator
- Receives a `TaskInput` and top-k ranked bullets from the playbook
- Calls the LLM to produce a structured `TaskResult`
- Does not modify the playbook

### Reflector
- Receives the `TaskInput` and `TaskResult`
- Evaluates correctness and quality
- Produces insights and `DeltaUpdate` proposals

### Curator
- Receives `ReflectorOutput`
- Cleans, generalises, and deduplicates the proposed deltas
- Returns a refined list of `DeltaUpdate` objects

---

## Merge Engine

The `MergeEngine` integrates `DeltaUpdate` objects into the playbook:

1. Embed the new delta content
2. Find the most similar existing bullet via cosine similarity
3. If similarity ≥ threshold: **merge** (blend confidence, add counters)
4. Otherwise: **add** as a new bullet

---

## Adaptation Modes

### Online Adaptation
Generate → Reflect → Curate → Merge after **each task** individually.  
Best for real-time interactive scenarios.

### Offline Adaptation
Generate all tasks first, then batch-reflect, curate, and merge.  
Best for training/evaluation runs.

---

## Local-First Design Principles

- All storage uses local JSON files (no database required)
- Default LLM provider is `mock` (no API keys needed)
- Embeddings use a character n-gram hashing trick (no ML model download)
- All components are independently testable

---

## Extension Points

| Component | How to extend |
|-----------|--------------|
| LLM provider | Subclass `BaseLLMService` in `app/services/llm.py` |
| Storage | Replace `PlaybookStore` with SQLite/Postgres adapter |
| Embeddings | Swap `app/services/embeddings.py` with sentence-transformers |
| Evaluation | Extend `app/services/evaluator.py` with domain metrics |

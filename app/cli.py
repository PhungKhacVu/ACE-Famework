"""ACE Framework CLI entrypoint.

Usage:
    python -m app.cli --help
    python -m app.cli run-task --description "How do I sort a list in Python?"
    python -m app.cli adapt-offline --tasks-file data/sample_tasks.json
    python -m app.cli adapt-online  --description "Explain recursion"
    python -m app.cli show-playbook
    python -m app.cli evaluate --tasks-file data/sample_tasks.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from app.config import config
from app.core.pipeline import ACEPipeline
from app.schemas.task import TaskInput
from app.services.evaluator import evaluate_batch
from app.services.llm import get_llm_provider
from app.storage.playbook_store import PlaybookStore
from app.utils.logger import get_logger

logger = get_logger(__name__)
app = typer.Typer(
    name="ace",
    help="ACE Framework – Adaptive Cognition Engineering (local-first MVP)",
    add_completion=False,
)


def _build_pipeline(provider_name: Optional[str]) -> ACEPipeline:
    provider = get_llm_provider(provider_name)
    store = PlaybookStore()
    return ACEPipeline(store=store, provider=provider)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("run-task")
def run_task(
    description: str = typer.Option(..., help="Task description to process"),
    context: Optional[str] = typer.Option(None, help="Optional extra context"),
    provider: Optional[str] = typer.Option(None, help="LLM provider: mock|openai|ollama"),
    playbook: Optional[str] = typer.Option(None, help="Path to playbook JSON file"),
) -> None:
    """Run a single task through the ACE pipeline."""
    if playbook:
        config.PLAYBOOK_PATH = playbook
    task = TaskInput(description=description, context=context)
    pipeline = _build_pipeline(provider)
    result = pipeline.run_task(task)
    typer.echo("\n=== RESULT ===")
    typer.echo(f"Answer: {result.final_answer}")
    typer.echo(f"Bullets used: {len(result.bullets_used)}")
    typer.echo(f"Merge summary: {result.metadata.get('merge', {})}")


@app.command("adapt-offline")
def adapt_offline(
    tasks_file: str = typer.Option(
        "data/sample_tasks.json", help="Path to tasks JSON file"
    ),
    provider: Optional[str] = typer.Option(None, help="LLM provider: mock|openai|ollama"),
    playbook: Optional[str] = typer.Option(None, help="Path to playbook JSON file"),
) -> None:
    """Run offline adaptation on a batch of tasks."""
    if playbook:
        config.PLAYBOOK_PATH = playbook
    tasks_path = Path(tasks_file)
    if not tasks_path.exists():
        typer.echo(f"Tasks file not found: {tasks_file}", err=True)
        raise typer.Exit(code=1)

    raw = json.loads(tasks_path.read_text(encoding="utf-8"))
    tasks = [TaskInput(**t) for t in raw]
    typer.echo(f"Loaded {len(tasks)} tasks from {tasks_file}")

    pipeline = _build_pipeline(provider)
    results = pipeline.offline_adaptation(tasks)

    typer.echo(f"\nCompleted {len(results)} tasks.")
    typer.echo(f"Playbook now has {pipeline._store.count()} bullets.")


@app.command("adapt-online")
def adapt_online(
    description: str = typer.Option(..., help="Task description"),
    context: Optional[str] = typer.Option(None, help="Optional context"),
    provider: Optional[str] = typer.Option(None, help="LLM provider: mock|openai|ollama"),
    playbook: Optional[str] = typer.Option(None, help="Path to playbook JSON file"),
) -> None:
    """Run online (real-time) adaptation for a single task."""
    if playbook:
        config.PLAYBOOK_PATH = playbook
    task = TaskInput(description=description, context=context)
    pipeline = _build_pipeline(provider)
    result = pipeline.online_adaptation(task)
    typer.echo("\n=== ONLINE RESULT ===")
    typer.echo(f"Answer: {result.final_answer}")
    typer.echo(f"Merge: {result.metadata.get('merge', {})}")


@app.command("show-playbook")
def show_playbook(
    playbook: Optional[str] = typer.Option(None, help="Path to playbook JSON file"),
    top: int = typer.Option(20, help="Number of top bullets to show"),
) -> None:
    """Display the current playbook bullets."""
    if playbook:
        config.PLAYBOOK_PATH = playbook
    store = PlaybookStore()
    bullets = store.top_bullets(top)
    if not bullets:
        typer.echo("Playbook is empty.")
        return
    typer.echo(f"\n=== PLAYBOOK ({store.count()} total, showing top {len(bullets)}) ===")
    for i, b in enumerate(bullets, 1):
        typer.echo(
            f"{i:3}. [{b.bullet_type.value:7}] score={b.score:.2f}  {b.content[:80]}"
        )


@app.command("evaluate")
def evaluate(
    tasks_file: str = typer.Option(
        "data/sample_tasks.json", help="Path to tasks JSON with ground_truth fields"
    ),
    provider: Optional[str] = typer.Option(None, help="LLM provider: mock|openai|ollama"),
    playbook: Optional[str] = typer.Option(None, help="Path to playbook JSON file"),
) -> None:
    """Evaluate pipeline answers against ground-truth labels."""
    if playbook:
        config.PLAYBOOK_PATH = playbook
    tasks_path = Path(tasks_file)
    if not tasks_path.exists():
        typer.echo(f"Tasks file not found: {tasks_file}", err=True)
        raise typer.Exit(code=1)

    raw = json.loads(tasks_path.read_text(encoding="utf-8"))
    tasks = [TaskInput(**t) for t in raw]
    ground_truths = [t.ground_truth or "" for t in tasks]

    if not any(ground_truths):
        typer.echo("No ground_truth fields found in tasks file.", err=True)
        raise typer.Exit(code=1)

    pipeline = _build_pipeline(provider)
    predictions = [pipeline.run_task(t).final_answer for t in tasks]

    metrics = evaluate_batch(predictions, ground_truths)
    typer.echo("\n=== EVALUATION METRICS ===")
    typer.echo(f"N tasks    : {metrics['n']}")
    typer.echo(f"Avg F1     : {metrics['avg_f1']:.4f}")
    typer.echo(f"Avg Jaccard: {metrics['avg_jaccard']:.4f}")
    typer.echo(f"Exact Match: {metrics['avg_exact_match']:.4f}")


if __name__ == "__main__":
    app()

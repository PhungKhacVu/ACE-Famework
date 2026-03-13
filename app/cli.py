"""CLI entry points using Typer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from app.config import config
from app.core.pipeline import ACEPipeline
from app.schemas.task import TaskInput
from app.services.evaluator import evaluate
from app.services.llm import get_llm_service
from app.storage.playbook_store import PlaybookStore
from app.utils.logger import get_logger

logger = get_logger(__name__)
app = typer.Typer(name="ace", help="ACE Framework – local-first CLI")


def _load_tasks(path: Path) -> list[TaskInput]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [TaskInput(**t) for t in raw]
    return [TaskInput(**raw)]


def _make_pipeline(playbook_path: Optional[Path] = None) -> ACEPipeline:
    store_path = playbook_path or config.PLAYBOOK_PATH
    store = PlaybookStore(store_path)
    llm = get_llm_service()
    return ACEPipeline(llm, store)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("run-task")
def run_task(
    input: Path = typer.Option(
        Path("data/sample_tasks.json"), "--input", "-i", help="Path to task JSON file"
    ),
    playbook: Optional[Path] = typer.Option(
        None, "--playbook", "-p", help="Path to playbook JSON file"
    ),
    top_k: int = typer.Option(5, "--top-k", help="Number of bullets to retrieve"),
) -> None:
    """Generate answers for tasks without modifying the playbook."""
    tasks = _load_tasks(input)
    pipeline = _make_pipeline(playbook)
    typer.echo(f"Running {len(tasks)} task(s)…")
    for task in tasks:
        result = pipeline.run_task(task, top_k=top_k)
        typer.echo(f"\n[Task {task.id}] {task.description}")
        typer.echo(f"  Answer     : {result.answer}")
        typer.echo(f"  Confidence : {result.confidence:.2f}")


@app.command("adapt-online")
def adapt_online(
    input: Path = typer.Option(
        Path("data/sample_tasks.json"), "--input", "-i", help="Path to task JSON file"
    ),
    playbook: Optional[Path] = typer.Option(
        None, "--playbook", "-p", help="Path to playbook JSON file"
    ),
) -> None:
    """Generate answers and immediately adapt the playbook from each outcome."""
    tasks = _load_tasks(input)
    pipeline = _make_pipeline(playbook)
    typer.echo(f"Online adaptation for {len(tasks)} task(s)…")
    for task in tasks:
        result = pipeline.adapt_online(task)
        typer.echo(f"\n[Task {task.id}] {task.description}")
        typer.echo(f"  Answer     : {result.answer}")
        typer.echo(f"  Confidence : {result.confidence:.2f}")
    typer.echo(f"\nPlaybook size: {pipeline._store.count()} bullet(s)")


@app.command("adapt-offline")
def adapt_offline(
    input: Path = typer.Option(
        Path("data/sample_tasks.json"), "--input", "-i", help="Path to task JSON file"
    ),
    playbook: Optional[Path] = typer.Option(
        None, "--playbook", "-p", help="Path to playbook JSON file"
    ),
) -> None:
    """Batch adaptation: generate all answers first, then adapt the playbook."""
    tasks = _load_tasks(input)
    pipeline = _make_pipeline(playbook)
    typer.echo(f"Generating answers for {len(tasks)} task(s)…")
    results = [pipeline.run_task(t) for t in tasks]
    typer.echo("Adapting playbook offline…")
    summary = pipeline.adapt_offline(tasks, results)
    typer.echo(
        f"\nAdaptation complete: {summary.bullets_added} added, "
        f"{summary.bullets_merged} merged, {summary.bullets_updated} updated."
    )
    typer.echo(f"Playbook size: {pipeline._store.count()} bullet(s)")


@app.command("show-playbook")
def show_playbook(
    playbook: Optional[Path] = typer.Option(
        None, "--playbook", "-p", help="Path to playbook JSON file"
    ),
    domain: Optional[str] = typer.Option(None, "--domain", "-d"),
    top: int = typer.Option(20, "--top", help="Number of bullets to display"),
) -> None:
    """Display the top bullets in the playbook."""
    store_path = playbook or config.PLAYBOOK_PATH
    store = PlaybookStore(store_path)
    bullets = store.top(n=top, domain=domain)
    if not bullets:
        typer.echo("Playbook is empty.")
        return
    typer.echo(f"\n{'='*60}")
    typer.echo(f"  ACE Playbook  ({store.count()} total bullets)")
    typer.echo(f"{'='*60}")
    for i, b in enumerate(bullets, 1):
        typer.echo(
            f"\n{i:>3}. [{b.domain}] {b.content}\n"
            f"     conf={b.confidence:.2f}  ✓{b.helpful_count}  ✗{b.harmful_count}"
            f"  score={b.net_score:.3f}"
        )


@app.command("evaluate")
def evaluate_cmd(
    input: Path = typer.Option(
        Path("data/sample_tasks.json"), "--input", "-i", help="Path to task JSON file"
    ),
    playbook: Optional[Path] = typer.Option(
        None, "--playbook", "-p", help="Path to playbook JSON file"
    ),
) -> None:
    """Evaluate task results against ground truth."""
    tasks = _load_tasks(input)
    pipeline = _make_pipeline(playbook)
    results = [pipeline.run_task(t) for t in tasks]
    metrics = evaluate(tasks, results)
    typer.echo(f"\nEvaluation results:")
    typer.echo(f"  Accuracy         : {metrics['accuracy']:.1%}")
    typer.echo(f"  Correct          : {metrics.get('correct', 0)}/{metrics.get('total', 0)}")
    typer.echo(f"  Avg. confidence  : {metrics.get('avg_confidence', 0):.2f}")


if __name__ == "__main__":
    app()

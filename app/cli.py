"""
ACE Framework CLI — compatible with a-Shell / a-Shell mini on iPhone.

Usage (run from the project root):
    python -m app.cli run-task --input data/sample_tasks.json
    python -m app.cli adapt    --input data/sample_tasks.json
    python -m app.cli show-playbook
    python -m app.cli evaluate --input data/sample_tasks.json
    python -m app.cli add-bullet --content "Always check edge cases"
    python -m app.cli search-playbook --query "error handling"
"""
from __future__ import annotations

import argparse
import json
import sys

from app.config import PLAYBOOK_FILE


def _make_store(playbook: str):
    from app.storage.playbook_store import PlaybookStore
    store = PlaybookStore(playbook)
    store.load()
    return store


def _make_pipeline(store, provider: str):
    from app.core.pipeline import Pipeline
    return Pipeline(store=store, llm_provider=provider)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_run_task(args):
    """Run pipeline on tasks (generation only, no adaptation)."""
    store = _make_store(args.playbook)
    pipeline = _make_pipeline(store, args.provider)

    from app.schemas.task import TaskInput
    tasks = TaskInput.load_json(args.input)
    print(f"Running {len(tasks)} task(s) (adapt={not args.no_adapt}) ...")

    results = pipeline.run_batch(tasks, adapt=not args.no_adapt, output_path=args.output)
    for r in results:
        print(f"\n{'='*60}")
        print(f"Task : {r.task_id}")
        print(f"Output:\n{r.output}")
        if r.reflection:
            print(f"Reflection:\n{r.reflection}")
        print(f"Confidence: {r.confidence:.2f}  |  Correct: {r.correct}")
    print(f"\nDone. Playbook now has {len(store)} bullets.")


def cmd_adapt(args):
    """Run full pipeline (generation + adaptation) on a batch of tasks."""
    args.no_adapt = False
    cmd_run_task(args)


def cmd_show_playbook(args):
    """Display current playbook bullets."""
    store = _make_store(args.playbook)
    bullets = store.top(args.limit, domain=args.domain or None)
    if not bullets:
        print("Playbook is empty.")
        return
    print(f"Top {len(bullets)} bullets (of {len(store)} total):\n")
    for i, b in enumerate(bullets, 1):
        stars = "+" * b.helpful_count + "-" * b.harmful_count
        print(f"{i:3}. [{b.domain}] {b.content}")
        print(f"      score={b.score:+.0f}  conf={b.confidence:.2f}  ({stars or 'no data'})")


def cmd_evaluate(args):
    """Evaluate results from a previous run or re-run on tasks."""
    if args.results:
        # Load pre-computed results
        with open(args.results, encoding="utf-8") as fh:
            raw = json.load(fh)
        from app.schemas.result import TaskResult
        results = [TaskResult(**r) for r in raw]
    else:
        # Re-run tasks without adaptation
        store = _make_store(args.playbook)
        pipeline = _make_pipeline(store, args.provider)
        from app.schemas.task import TaskInput
        tasks = TaskInput.load_json(args.input)
        results = pipeline.run_batch(tasks, adapt=False)

    store = _make_store(args.playbook)
    pipeline = _make_pipeline(store, args.provider)
    metrics = pipeline.evaluate(results)

    print("\n=== Evaluation Metrics ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")


def cmd_add_bullet(args):
    """Manually add a bullet to the playbook."""
    from app.schemas.bullet import Bullet
    from app.utils.ids import new_id
    store = _make_store(args.playbook)
    bullet = Bullet(
        id=new_id(),
        content=args.content,
        domain=args.domain,
        source="manual",
    )
    store.add(bullet)
    store.save()
    print(f"Added bullet {bullet.id}: {bullet.content!r} (domain={bullet.domain})")


def cmd_search_playbook(args):
    """Search the playbook for bullets matching a query."""
    store = _make_store(args.playbook)
    bullets = store.search(args.query, domain=args.domain or None, top_k=args.limit)
    if not bullets:
        print("No matching bullets found.")
        return
    print(f"Top {len(bullets)} results for {args.query!r}:\n")
    for i, b in enumerate(bullets, 1):
        print(f"{i}. [{b.domain}] {b.content}")
        print(f"   score={b.score:+.0f}  conf={b.confidence:.2f}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ace",
        description="ACE Framework — local-first adaptive cognition engine",
    )
    parser.add_argument(
        "--playbook",
        default=PLAYBOOK_FILE,
        help=f"Path to playbook JSON file (default: {PLAYBOOK_FILE})",
    )
    parser.add_argument(
        "--provider",
        default="mock",
        choices=["mock", "openai", "ollama"],
        help="LLM provider (default: mock — runs fully offline)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # run-task
    p_run = sub.add_parser("run-task", help="Run pipeline on tasks")
    p_run.add_argument("--input", required=True, help="JSON file with tasks")
    p_run.add_argument("--output", help="Write results to this JSON file")
    p_run.add_argument("--no-adapt", action="store_true", help="Skip adaptation step")
    p_run.set_defaults(func=cmd_run_task)

    # adapt
    p_adapt = sub.add_parser("adapt", help="Run full pipeline with adaptation")
    p_adapt.add_argument("--input", required=True, help="JSON file with tasks")
    p_adapt.add_argument("--output", help="Write results to this JSON file")
    p_adapt.set_defaults(func=cmd_adapt)

    # show-playbook
    p_show = sub.add_parser("show-playbook", help="Show playbook bullets")
    p_show.add_argument("--limit", type=int, default=20, help="Max bullets to show")
    p_show.add_argument("--domain", help="Filter by domain")
    p_show.set_defaults(func=cmd_show_playbook)

    # evaluate
    p_eval = sub.add_parser("evaluate", help="Evaluate task results")
    p_eval.add_argument("--input", help="JSON file with tasks (for re-running)")
    p_eval.add_argument("--results", help="JSON file with pre-computed results")
    p_eval.set_defaults(func=cmd_evaluate)

    # add-bullet
    p_add = sub.add_parser("add-bullet", help="Manually add a bullet to the playbook")
    p_add.add_argument("--content", required=True, help="Bullet text")
    p_add.add_argument("--domain", default="general", help="Bullet domain")
    p_add.set_defaults(func=cmd_add_bullet)

    # search-playbook
    p_search = sub.add_parser("search-playbook", help="Search the playbook")
    p_search.add_argument("--query", required=True, help="Search query")
    p_search.add_argument("--domain", help="Filter by domain")
    p_search.add_argument("--limit", type=int, default=5, help="Max results")
    p_search.set_defaults(func=cmd_search_playbook)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

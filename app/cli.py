"""CLI entrypoint for the ACE framework.

Usage (from the repo root):
    python -m app.cli --help
    python -m app.cli run-task --input data/sample_tasks.json
    python -m app.cli show-playbook
    python -m app.cli clear-playbook

All commands work offline with no API key (uses built-in mock LLM).
"""
from __future__ import annotations
import argparse
import json
import os
import sys

# Ensure the repo root is on sys.path so `app` is importable when the
# script is run directly (e.g. `python app/cli.py`) as well as via
# `python -m app.cli`.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.schemas import TaskInput
from app.core.pipeline import ACEPipeline
from app.storage import PlaybookStore


# ---------------------------------------------------------------------------
# Sub-command implementations
# ---------------------------------------------------------------------------

def cmd_run_task(args: argparse.Namespace) -> None:
    """Run one or more tasks through the full ACE pipeline."""
    store = PlaybookStore(args.playbook)
    pipeline = ACEPipeline(store=store)

    with open(args.input, "r", encoding="utf-8") as f:
        raw = json.load(f)

    tasks = [TaskInput.from_dict(t) for t in raw]

    print(f"Running {len(tasks)} task(s) through the ACE pipeline …\n")
    for task in tasks:
        result = pipeline.run(task)
        print(f"Task      : {task.description[:80]}")
        print(f"Answer    : {result.answer}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Insights  : {result.insights}")
        print(f"New bullets added/updated: {len(result.delta_bullets)}")
        print("-" * 60)

    bullets = store.load()
    print(f"\nPlaybook now contains {len(bullets)} bullet(s).")
    print(f"Saved to: {store.path}")


def cmd_show_playbook(args: argparse.Namespace) -> None:
    """Print all bullets currently in the playbook."""
    store = PlaybookStore(args.playbook)
    bullets = store.load()

    if not bullets:
        print("Playbook is empty.")
        return

    bullets_sorted = sorted(bullets, key=lambda b: -b.confidence)
    print(f"Playbook — {len(bullets_sorted)} bullet(s)\n")
    for i, b in enumerate(bullets_sorted, 1):
        print(f"{i:3}. [{b.confidence:.2f}] {b.text}")
        print(f"       helpful={b.helpful_count}  harmful={b.harmful_count}")


def cmd_clear_playbook(args: argparse.Namespace) -> None:
    """Clear all bullets from the playbook."""
    store = PlaybookStore(args.playbook)
    store.clear()
    print(f"Playbook cleared: {store.path}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    default_playbook = os.path.join(
        os.path.dirname(__file__), "..", "data", "playbook.json"
    )

    parser = argparse.ArgumentParser(
        prog="ace",
        description="ACE Framework — local-first Agentic Context Engineering MVP",
    )
    parser.add_argument(
        "--playbook",
        default=default_playbook,
        metavar="PATH",
        help="Path to the playbook JSON file (default: data/playbook.json)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # run-task
    p_run = sub.add_parser("run-task", help="Run tasks through the ACE pipeline")
    p_run.add_argument(
        "--input",
        required=True,
        metavar="PATH",
        help="Path to a JSON file containing a list of task objects",
    )
    p_run.set_defaults(func=cmd_run_task)

    # show-playbook
    p_show = sub.add_parser("show-playbook", help="Display current playbook bullets")
    p_show.set_defaults(func=cmd_show_playbook)

    # clear-playbook
    p_clear = sub.add_parser("clear-playbook", help="Clear all bullets from the playbook")
    p_clear.set_defaults(func=cmd_clear_playbook)

    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

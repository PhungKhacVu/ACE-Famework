"""ACE command-line interface – pure stdlib argparse."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import Config
from app.core.engine import ACEEngine
from app.schemas import Playbook, Step, StepType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_engine(args: argparse.Namespace) -> ACEEngine:
    if hasattr(args, "config") and args.config:
        config = Config.from_file(Path(args.config))
    else:
        config = Config.from_env()
    return ACEEngine(config)


def _print_task(task) -> None:
    print(f"Task ID   : {task.id}")
    print(f"Status    : {task.status.value}")
    print(f"Goal      : {task.goal}")
    print(f"Result    : {task.result or '(no result yet)'}")
    print(f"Created   : {task.created_at}")
    print(f"Updated   : {task.updated_at}")
    if task.messages:
        print(f"Messages  : {len(task.messages)}")


def _print_playbook(pb) -> None:
    print(f"Playbook  : {pb.name}  [{pb.id}]")
    print(f"Desc      : {pb.description or '(none)'}")
    print(f"Steps     : {len(pb.steps)}")
    for i, step in enumerate(pb.steps, 1):
        print(f"  {i}. [{step.type.value}] {step.name}: {step.instruction}")


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------


def cmd_run(args: argparse.Namespace) -> int:
    engine = _make_engine(args)
    playbook_id = args.playbook or ""
    print(f"Running task: {args.goal!r}")
    task = engine.run_task(goal=args.goal, playbook_id=playbook_id)
    print()
    _print_task(task)
    return 0 if task.status.value == "done" else 1


def cmd_task_list(args: argparse.Namespace) -> int:
    engine = _make_engine(args)
    tasks = engine.list_tasks()
    if not tasks:
        print("No tasks found.")
        return 0
    for task in tasks:
        print(f"  [{task.status.value:7s}] {task.id[:8]}…  {task.goal[:60]}")
    return 0


def cmd_task_show(args: argparse.Namespace) -> int:
    engine = _make_engine(args)
    try:
        task = engine.get_task(args.id)
    except FileNotFoundError:
        print(f"Task not found: {args.id}", file=sys.stderr)
        return 1
    _print_task(task)
    if args.messages:
        print("\n--- Messages ---")
        for msg in task.messages:
            print(f"[{msg.role}] {msg.content}")
    return 0


def cmd_playbook_list(args: argparse.Namespace) -> int:
    engine = _make_engine(args)
    playbooks = engine.list_playbooks()
    if not playbooks:
        print("No playbooks found.")
        return 0
    for pb in playbooks:
        print(f"  {pb.id[:8]}…  {pb.name}")
    return 0


def cmd_playbook_show(args: argparse.Namespace) -> int:
    engine = _make_engine(args)
    try:
        pb = engine.get_playbook(args.id)
    except FileNotFoundError:
        print(f"Playbook not found: {args.id}", file=sys.stderr)
        return 1
    _print_playbook(pb)
    return 0


def cmd_playbook_import(args: argparse.Namespace) -> int:
    """Import a playbook from a JSON file."""
    engine = _make_engine(args)
    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    pb = Playbook.from_dict(data)
    engine.save_playbook(pb)
    print(f"Playbook '{pb.name}' imported with id {pb.id}")
    return 0


def cmd_playbook_delete(args: argparse.Namespace) -> int:
    engine = _make_engine(args)
    removed = engine.delete_playbook(args.id)
    if removed:
        print(f"Deleted playbook {args.id}")
        return 0
    print(f"Playbook not found: {args.id}", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ace",
        description="ACE – Autonomous Cognitive Engine (local-first CLI)",
    )
    parser.add_argument(
        "--config", metavar="FILE", help="Path to JSON config file (optional)"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- run ---
    p_run = sub.add_parser("run", help="Run a task (optionally with a playbook)")
    p_run.add_argument("goal", help="The task goal / prompt")
    p_run.add_argument(
        "--playbook", metavar="ID", default="", help="Playbook ID to use"
    )
    p_run.set_defaults(func=cmd_run)

    # --- task ---
    p_task = sub.add_parser("task", help="Manage tasks")
    task_sub = p_task.add_subparsers(dest="task_command", required=True)

    p_task_list = task_sub.add_parser("list", help="List all tasks")
    p_task_list.set_defaults(func=cmd_task_list)

    p_task_show = task_sub.add_parser("show", help="Show task details")
    p_task_show.add_argument("id", help="Task ID")
    p_task_show.add_argument(
        "--messages", action="store_true", help="Show full message history"
    )
    p_task_show.set_defaults(func=cmd_task_show)

    # --- playbook ---
    p_pb = sub.add_parser("playbook", help="Manage playbooks")
    pb_sub = p_pb.add_subparsers(dest="pb_command", required=True)

    p_pb_list = pb_sub.add_parser("list", help="List all playbooks")
    p_pb_list.set_defaults(func=cmd_playbook_list)

    p_pb_show = pb_sub.add_parser("show", help="Show playbook details")
    p_pb_show.add_argument("id", help="Playbook ID")
    p_pb_show.set_defaults(func=cmd_playbook_show)

    p_pb_import = pb_sub.add_parser("import", help="Import a playbook from JSON file")
    p_pb_import.add_argument("file", help="Path to playbook JSON file")
    p_pb_import.set_defaults(func=cmd_playbook_import)

    p_pb_delete = pb_sub.add_parser("delete", help="Delete a playbook")
    p_pb_delete.add_argument("id", help="Playbook ID")
    p_pb_delete.set_defaults(func=cmd_playbook_delete)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

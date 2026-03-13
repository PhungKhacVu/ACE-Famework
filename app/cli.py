"""ACE Framework CLI.

Usage (after ``pip install -e .`` or just running from repo root)::

    python -m app.cli --help
    python -m app.cli list
    python -m app.cli run <playbook-id>
    python -m app.cli run <playbook-id> --layer executive
"""
from __future__ import annotations

import argparse
import json
import sys

from app.config import PLAYBOOKS_DIR, STORE_DIR
from app.core.engine import ACEEngine
from app.services.playbook import PlaybookService


def _get_service() -> PlaybookService:
    return PlaybookService(store_dir=STORE_DIR, playbooks_dir=PLAYBOOKS_DIR)


def cmd_list(args: argparse.Namespace) -> int:
    svc = _get_service()
    playbooks = svc.list()
    if not playbooks:
        print("No playbooks found.")
        return 0
    for pb in playbooks:
        steps = len(pb.get("steps", []))
        print(f"  {pb['id']:30s}  {pb.get('name', '')}  ({steps} step(s))")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    svc = _get_service()
    pb = svc.get(args.id)
    if pb is None:
        print(f"Playbook '{args.id}' not found.", file=sys.stderr)
        return 1
    print(json.dumps(pb, ensure_ascii=False, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    svc = _get_service()
    pb = svc.get(args.id)
    if pb is None:
        print(f"Playbook '{args.id}' not found.", file=sys.stderr)
        return 1
    engine = ACEEngine(layer=args.layer)
    result = engine.run(pb)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ace",
        description="ACE Framework — local-first autonomous cognitive entity CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    sub.add_parser("list", help="List all available playbooks")

    # show
    show_p = sub.add_parser("show", help="Print a playbook as JSON")
    show_p.add_argument("id", help="Playbook ID")

    # run
    run_p = sub.add_parser("run", help="Run a playbook through the ACE engine")
    run_p.add_argument("id", help="Playbook ID")
    run_p.add_argument(
        "--layer",
        default="task",
        choices=[
            "aspirational",
            "global_strategy",
            "agent_model",
            "executive",
            "cognitive_ctrl",
            "task",
        ],
        help="ACE layer to execute under (default: task)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "list": cmd_list,
        "show": cmd_show,
        "run": cmd_run,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)
    sys.exit(handler(args))


if __name__ == "__main__":
    main()

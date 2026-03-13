"""ACE Framework CLI.

Usage (after ``pip install -e .`` or just running from repo root)::

    python -m app.cli --help
    python -m app.cli list
    python -m app.cli run <playbook-id>
    python -m app.cli run <playbook-id> --layer executive
    python -m app.cli show <playbook-id> --json
"""
from __future__ import annotations

import argparse
import json
import sys

from app.config import PLAYBOOKS_DIR, STORE_DIR
from app.core.engine import ACEEngine
from app.services.playbook import PlaybookService
from app.ui import banner, bold, cyan, dim, green, red, separator, table, yellow


def _get_service() -> PlaybookService:
    return PlaybookService(store_dir=STORE_DIR, playbooks_dir=PLAYBOOKS_DIR)


def cmd_list(args: argparse.Namespace) -> int:
    svc = _get_service()
    playbooks = svc.list()
    banner("ACE Framework — Playbooks")
    if not playbooks:
        print(dim("  No playbooks found."))
        return 0
    rows = [
        (pb["id"], pb.get("name", ""), f"{len(pb.get('steps', []))} step(s)")
        for pb in playbooks
    ]
    table(
        headers=["ID", "Name", "Steps"],
        rows=rows,
        col_widths=[24, 20, 9],
    )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    svc = _get_service()
    pb = svc.get(args.id)
    if pb is None:
        print(f"Playbook '{args.id}' not found.", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        print(json.dumps(pb, ensure_ascii=False, indent=2))
        return 0

    banner(f"Playbook: {pb['id']}")
    print(f"  {bold('Name:')}        {pb.get('name', '')}")
    print(f"  {bold('Description:')} {pb.get('description', '')}")
    steps = pb.get("steps", [])
    print(f"  {bold('Steps')} ({len(steps)}):")
    for i, step in enumerate(steps, 1):
        marker = cyan(f"  [{i}]")
        desc = step.get("description", step.get("id", ""))
        print(f"{marker} {step['id']} — {desc}")
        print(dim(f"       Prompt: {step.get('prompt', '')}"))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    svc = _get_service()
    pb = svc.get(args.id)
    if pb is None:
        print(f"Playbook '{args.id}' not found.", file=sys.stderr)
        return 1

    engine = ACEEngine(layer=args.layer)
    result = engine.run(pb)

    if getattr(args, "json", False):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    steps = pb.get("steps", [])
    total = len(steps)
    banner(f"Running: {pb['id']}  [{args.layer}]")

    for i, step_result in enumerate(result["results"], 1):
        if step_result["ok"]:
            icon = green("✓")
            status = ""
        else:
            icon = red("✗")
            status = red(" (failed)")
        step_label = f"{bold(f'Step {i}/{total}:')} {step_result['step_id']}{status}"
        print(f"  {icon} {step_label}")
        response = step_result["response"]
        if len(response) > 80:
            response = response[:77] + "…"
        print(dim(f"    → {response}"))

    separator()
    successful = result["metadata"]["successful"]
    summary = f"  Results: {successful}/{total} successful"
    if successful == total:
        print(green(summary))
    elif successful == 0:
        print(red(summary))
    else:
        print(yellow(summary))

    return 0 if successful == total else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ace",
        description="ACE Framework — local-first autonomous cognitive entity CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    sub.add_parser("list", help="List all available playbooks")

    # show
    show_p = sub.add_parser("show", help="Show a playbook (human-readable by default)")
    show_p.add_argument("id", help="Playbook ID")
    show_p.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of the formatted view",
    )

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
    run_p.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON result instead of the formatted view",
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

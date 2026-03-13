"""Tests for the CLI (app.cli)."""
from __future__ import annotations

import json

import pytest

from app.cli import build_parser, cmd_list, cmd_run, cmd_show


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Namespace:
    """Minimal argparse.Namespace stub."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

def test_list_no_playbooks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path))
    # Re-import to pick up env change
    import importlib
    import app.config
    importlib.reload(app.config)

    from app.services.playbook import PlaybookService
    svc = PlaybookService(
        store_dir=tmp_path / "store",
        playbooks_dir=tmp_path / "playbooks",
    )
    # Patch _get_service inside cli module
    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_list(_Namespace())
    assert rc == 0
    captured = capsys.readouterr()
    assert "No playbooks found" in captured.out


def test_list_with_playbook(tmp_path, monkeypatch, capsys):
    from app.services.playbook import PlaybookService
    svc = PlaybookService(
        store_dir=tmp_path / "store",
        playbooks_dir=tmp_path / "playbooks",
    )
    svc.save({"id": "demo", "name": "Demo PB", "description": "", "steps": []})

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_list(_Namespace())
    assert rc == 0
    captured = capsys.readouterr()
    assert "demo" in captured.out


# ---------------------------------------------------------------------------
# cmd_show
# ---------------------------------------------------------------------------

def test_show_existing(tmp_path, monkeypatch, capsys):
    from app.services.playbook import PlaybookService
    svc = PlaybookService(
        store_dir=tmp_path / "store",
        playbooks_dir=tmp_path / "playbooks",
    )
    svc.save({"id": "pb1", "name": "PB1", "description": "", "steps": []})

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_show(_Namespace(id="pb1"))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["id"] == "pb1"


def test_show_missing(tmp_path, monkeypatch, capsys):
    from app.services.playbook import PlaybookService
    svc = PlaybookService(
        store_dir=tmp_path / "store",
        playbooks_dir=tmp_path / "playbooks",
    )

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_show(_Namespace(id="nope"))
    assert rc == 1


# ---------------------------------------------------------------------------
# cmd_run
# ---------------------------------------------------------------------------

def test_run_existing(tmp_path, monkeypatch, capsys):
    from app.services.playbook import PlaybookService
    svc = PlaybookService(
        store_dir=tmp_path / "store",
        playbooks_dir=tmp_path / "playbooks",
    )
    svc.save({
        "id": "r1",
        "name": "Run PB",
        "description": "",
        "steps": [{"id": "s1", "description": "d", "prompt": "go"}],
    })

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_run(_Namespace(id="r1", layer="task"))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["playbook_id"] == "r1"
    assert len(data["results"]) == 1


def test_run_missing(tmp_path, monkeypatch):
    from app.services.playbook import PlaybookService
    svc = PlaybookService(
        store_dir=tmp_path / "store",
        playbooks_dir=tmp_path / "playbooks",
    )

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_run(_Namespace(id="gone", layer="task"))
    assert rc == 1


# ---------------------------------------------------------------------------
# Parser smoke-test
# ---------------------------------------------------------------------------

def test_parser_run_defaults():
    parser = build_parser()
    args = parser.parse_args(["run", "my-pb"])
    assert args.id == "my-pb"
    assert args.layer == "task"


def test_parser_run_layer():
    parser = build_parser()
    args = parser.parse_args(["run", "my-pb", "--layer", "executive"])
    assert args.layer == "executive"

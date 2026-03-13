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


def _svc(tmp_path):
    """Create and return a PlaybookService instance using temporary directories."""
    from app.services.playbook import PlaybookService
    return PlaybookService(
        store_dir=tmp_path / "store",
        playbooks_dir=tmp_path / "playbooks",
    )


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

def test_list_no_playbooks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path))
    # Re-import to pick up env change
    import importlib
    import app.config
    importlib.reload(app.config)

    svc = _svc(tmp_path)
    # Patch _get_service inside cli module
    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_list(_Namespace())
    assert rc == 0
    captured = capsys.readouterr()
    assert "No playbooks found" in captured.out


def test_list_with_playbook(tmp_path, monkeypatch, capsys):
    svc = _svc(tmp_path)
    svc.save({"id": "demo", "name": "Demo PB", "description": "", "steps": []})

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_list(_Namespace())
    assert rc == 0
    captured = capsys.readouterr()
    assert "demo" in captured.out


def test_list_shows_header(tmp_path, monkeypatch, capsys):
    """cmd_list should display a banner and column headers."""
    svc = _svc(tmp_path)
    svc.save({"id": "pb-a", "name": "Alpha", "description": "", "steps": [{
        "id": "s1", "description": "d", "prompt": "p",
    }]})

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_list(_Namespace())
    assert rc == 0
    out = capsys.readouterr().out
    assert "Playbooks" in out  # banner
    assert "ID" in out         # column header
    assert "Name" in out
    assert "Steps" in out
    assert "pb-a" in out
    assert "1 step(s)" in out


# ---------------------------------------------------------------------------
# cmd_show  (human-readable default; --json for raw JSON)
# ---------------------------------------------------------------------------

def test_show_existing_pretty(tmp_path, monkeypatch, capsys):
    """Default cmd_show output is human-readable (not raw JSON)."""
    svc = _svc(tmp_path)
    svc.save({
        "id": "pb1",
        "name": "PB1",
        "description": "A test playbook",
        "steps": [{"id": "s1", "description": "Do it", "prompt": "do it"}],
    })

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_show(_Namespace(id="pb1"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "pb1" in out
    assert "PB1" in out
    assert "A test playbook" in out
    assert "s1" in out


def test_show_existing_json(tmp_path, monkeypatch, capsys):
    """cmd_show --json outputs parseable JSON."""
    svc = _svc(tmp_path)
    svc.save({"id": "pb1", "name": "PB1", "description": "", "steps": []})

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_show(_Namespace(id="pb1", json=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["id"] == "pb1"


def test_show_missing(tmp_path, monkeypatch, capsys):
    svc = _svc(tmp_path)

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_show(_Namespace(id="nope"))
    assert rc == 1


# ---------------------------------------------------------------------------
# cmd_run  (human-readable default; --json for raw JSON)
# ---------------------------------------------------------------------------

def test_run_existing_pretty(tmp_path, monkeypatch, capsys):
    """Default cmd_run output is human-readable progress format."""
    svc = _svc(tmp_path)
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
    assert "r1" in out          # playbook id in banner
    assert "task" in out        # layer in banner
    assert "s1" in out          # step id
    assert "1/1" in out         # step counter
    assert "1/1 successful" in out  # summary


def test_run_existing_json(tmp_path, monkeypatch, capsys):
    """cmd_run --json outputs parseable JSON."""
    svc = _svc(tmp_path)
    svc.save({
        "id": "r1",
        "name": "Run PB",
        "description": "",
        "steps": [{"id": "s1", "description": "d", "prompt": "go"}],
    })

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_run(_Namespace(id="r1", layer="task", json=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["playbook_id"] == "r1"
    assert len(data["results"]) == 1


def test_run_missing(tmp_path, monkeypatch):
    svc = _svc(tmp_path)

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_run(_Namespace(id="gone", layer="task"))
    assert rc == 1


def test_run_all_steps_succeed_returns_zero(tmp_path, monkeypatch, capsys):
    """All-successful run returns exit code 0."""
    svc = _svc(tmp_path)
    svc.save({
        "id": "ok",
        "name": "OK",
        "description": "",
        "steps": [
            {"id": "a", "description": "da", "prompt": "pa"},
            {"id": "b", "description": "db", "prompt": "pb"},
        ],
    })

    import app.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_get_service", lambda: svc)

    rc = cmd_run(_Namespace(id="ok", layer="task"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "2/2 successful" in out


# ---------------------------------------------------------------------------
# Parser smoke-tests
# ---------------------------------------------------------------------------

def test_parser_run_defaults():
    parser = build_parser()
    args = parser.parse_args(["run", "my-pb"])
    assert args.id == "my-pb"
    assert args.layer == "task"
    assert args.json is False


def test_parser_run_layer():
    parser = build_parser()
    args = parser.parse_args(["run", "my-pb", "--layer", "executive"])
    assert args.layer == "executive"


def test_parser_run_json_flag():
    parser = build_parser()
    args = parser.parse_args(["run", "my-pb", "--json"])
    assert args.json is True


def test_parser_show_json_flag():
    parser = build_parser()
    args = parser.parse_args(["show", "my-pb", "--json"])
    assert args.json is True


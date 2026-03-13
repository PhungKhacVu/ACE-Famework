"""Tests for the CLI."""

from __future__ import annotations

import json
import pytest

from app.cli import build_parser, main
from app.config import Config
from app.core.engine import ACEEngine
from app.schemas import Playbook, Step, StepType


@pytest.fixture()
def cli_engine(tmp_path, monkeypatch):
    """Set env vars so the CLI uses a temp data dir."""
    monkeypatch.setenv("ACE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ACE_LLM_BACKEND", "mock")
    return tmp_path


class TestCLIParsing:
    def test_run_required_args(self):
        parser = build_parser()
        args = parser.parse_args(["run", "my goal"])
        assert args.goal == "my goal"
        assert args.playbook == ""

    def test_run_with_playbook(self):
        parser = build_parser()
        args = parser.parse_args(["run", "goal", "--playbook", "pb-123"])
        assert args.playbook == "pb-123"

    def test_task_list(self):
        parser = build_parser()
        args = parser.parse_args(["task", "list"])
        assert args.task_command == "list"

    def test_playbook_list(self):
        parser = build_parser()
        args = parser.parse_args(["playbook", "list"])
        assert args.pb_command == "list"


class TestCLICommands:
    def test_run_command_success(self, cli_engine):
        exit_code = main(["run", "hello world"])
        assert exit_code == 0

    def test_task_list_empty(self, cli_engine):
        exit_code = main(["task", "list"])
        assert exit_code == 0

    def test_task_list_after_run(self, cli_engine):
        main(["run", "test task"])
        exit_code = main(["task", "list"])
        assert exit_code == 0

    def test_task_show_not_found(self, cli_engine):
        exit_code = main(["task", "show", "no-such-id"])
        assert exit_code == 1

    def test_playbook_list_empty(self, cli_engine):
        exit_code = main(["playbook", "list"])
        assert exit_code == 0

    def test_playbook_import_and_show(self, cli_engine, tmp_path):
        pb = Playbook(
            name="cli-test-pb",
            steps=[Step("s1", StepType.PROMPT, "do something")],
        )
        pb_file = tmp_path / "pb.json"
        pb_file.write_text(json.dumps(pb.to_dict()), encoding="utf-8")
        exit_code = main(["playbook", "import", str(pb_file)])
        assert exit_code == 0
        exit_code = main(["playbook", "show", pb.id])
        assert exit_code == 0

    def test_playbook_import_missing_file(self, cli_engine):
        exit_code = main(["playbook", "import", "/no/such/file.json"])
        assert exit_code == 1

    def test_playbook_delete(self, cli_engine, tmp_path):
        pb = Playbook(name="del-pb")
        pb_file = tmp_path / "del.json"
        pb_file.write_text(json.dumps(pb.to_dict()), encoding="utf-8")
        main(["playbook", "import", str(pb_file)])
        exit_code = main(["playbook", "delete", pb.id])
        assert exit_code == 0
        exit_code = main(["playbook", "delete", pb.id])
        assert exit_code == 1

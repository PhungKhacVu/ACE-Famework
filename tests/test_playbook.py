"""Tests for PlaybookService."""
from __future__ import annotations

import json

import pytest

from app.services.playbook import PlaybookService


@pytest.fixture()
def svc(tmp_path):
    playbooks_dir = tmp_path / "playbooks"
    playbooks_dir.mkdir()
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    return PlaybookService(store_dir=store_dir, playbooks_dir=playbooks_dir)


@pytest.fixture()
def svc_with_seed(tmp_path):
    playbooks_dir = tmp_path / "playbooks"
    playbooks_dir.mkdir()
    (playbooks_dir / "demo.json").write_text(
        json.dumps(
            {
                "id": "demo",
                "name": "Demo",
                "description": "Seed playbook",
                "steps": [],
            }
        )
    )
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    return PlaybookService(store_dir=store_dir, playbooks_dir=playbooks_dir)


def test_empty_list(svc):
    assert svc.list() == []


def test_save_and_get(svc):
    pb = {"id": "p1", "name": "Test", "description": "", "steps": []}
    svc.save(pb)
    assert svc.get("p1") == pb


def test_delete(svc):
    svc.save({"id": "del", "name": "", "description": "", "steps": []})
    assert svc.delete("del") is True
    assert svc.get("del") is None


def test_delete_missing(svc):
    assert svc.delete("ghost") is False


def test_seed_loading(svc_with_seed):
    pbs = svc_with_seed.list()
    assert len(pbs) == 1
    assert pbs[0]["id"] == "demo"


def test_seed_not_duplicated(svc_with_seed):
    svc_with_seed.list()
    svc_with_seed.list()  # second call — seeds should not be re-added
    assert len(svc_with_seed.list()) == 1

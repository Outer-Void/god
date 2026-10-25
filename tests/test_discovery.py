from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from god import index, query
from god.errors import ErrorCode, GodError
from tests.conftest import capability, project, run, run_json


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    project(
        tmp_path / "alpha",
        "alpha",
        [
            capability("repo.build", version="2.1.0", side_effects="write"),
            capability("repo.lint", labels={"tier": "fast"}),
        ],
    )
    project(tmp_path / "group" / "beta", "beta", [capability("docs.render", side_effects="none")])
    (tmp_path / "group" / "node_modules" / "dep" / ".blux").mkdir(parents=True)  # skipped directory
    project(tmp_path / "group" / "node_modules" / "dep", "dep-proj", [capability("dep.thing")])
    return tmp_path


def test_discover_finds_projects_and_filters(tree: Path) -> None:
    idx = index.build([tree])
    assert [p["project_id"] for p in idx.projects] == ["alpha", "beta"]
    doc = query.discover(idx)
    assert [c["capability_id"] for c in doc["capabilities"]] == ["docs.render", "repo.build", "repo.lint"]
    assert [c["capability_id"] for c in query.discover(idx, query="repo.*")["capabilities"]] == [
        "repo.build",
        "repo.lint",
    ]
    assert [c["capability_id"] for c in query.discover(idx, query="lint")["capabilities"]] == ["repo.lint"]
    assert [c["capability_id"] for c in query.discover(idx, max_side_effects="read")["capabilities"]] == [
        "docs.render",
        "repo.lint",
    ]
    assert [c["capability_id"] for c in query.discover(idx, labels={"tier": "fast"})["capabilities"]] == ["repo.lint"]
    assert [c["capability_id"] for c in query.discover(idx, project="beta")["capabilities"]] == ["docs.render"]
    first = doc["capabilities"][1]
    assert first["project_root"] == str(tree / "alpha") and first["provider"]["kind"] == "subprocess"


def test_discovery_is_deterministic(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    a = run_json(["capabilities", "-r", str(tree / "alpha"), "-r", str(tree / "group"), "--no-cache"], capsys)
    b = run_json(["capabilities", "-r", str(tree / "group"), "-r", str(tree / "alpha") + "/", "--no-cache"], capsys)
    assert a == b  # root order and spelling do not matter
    overlapping = run_json(["capabilities", "-r", str(tree), "-r", str(tree / "group"), "--no-cache"], capsys)[1]
    assert len(overlapping["capabilities"]) == 3  # a project under two roots is found once


def test_describe_capability_and_project(tree: Path) -> None:
    idx = index.build([tree])
    doc = query.describe_capability(idx, "repo.build")
    assert doc["capability"]["version"] == "2.1.0" and doc["project"]["project_id"] == "alpha"
    proj = query.describe_project(idx, "beta")
    assert proj["project"]["root"] == str(tree / "group" / "beta")
    assert proj["policy"] == {"policy_id": "beta-p", "default_effect": "deny", "rules": []}
    assert query.describe_project(idx, str(tree / "alpha"))["project"]["project_id"] == "alpha"
    with pytest.raises(GodError) as exc:
        query.describe_capability(idx, "nope.nothing")
    assert exc.value.code is ErrorCode.NOT_FOUND


def test_symlinked_directories_are_not_followed(tmp_path: Path) -> None:
    outside = project(tmp_path / "outside", "outside", [capability("out.side")])
    (tmp_path / "root").mkdir()
    (tmp_path / "root" / "link").symlink_to(outside)
    assert index.build([tmp_path / "root"]).projects == []


def test_missing_root_is_an_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, doc = run_json(["capabilities", "-r", str(tmp_path / "nope")], capsys)
    assert code == 3 and doc["error"]["code"] == "ROOT_NOT_FOUND"


def test_cli_text_and_exit_codes(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(["capabilities", "repo.*", "-r", str(tree)], capsys)
    assert code == 0 and "repo.build" in out and "docs.render" not in out
    code, out, _ = run(["project", str(tree / "alpha")], capsys)
    assert code == 0 and out.startswith("alpha (standalone)")
    code, _, err = run(["capability", "nope.x", "-r", str(tree)], capsys)
    assert code == 1 and "NOT_FOUND" in err
    assert run(["check", str(tree)], capsys)[0] == 0
    assert run([], capsys)[0] == 2
    assert run(["version"], capsys)[0] == 0


def test_god_roots_environment(tree: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOD_ROOTS", f"{tree / 'alpha'}{os.pathsep}{tree / 'group'}")
    code, doc = run_json(["capabilities"], capsys)
    assert code == 0 and doc["index"]["roots"] == sorted([str(tree / "alpha"), str(tree / "group")])


def test_index_records_contain_no_secrets_from_outside_blux(tree: Path) -> None:
    (tree / "alpha" / ".env").write_text("TOKEN=do-not-read")
    idx = index.build([tree], cache_path=tree / "cache.json")
    assert "do-not-read" not in json.dumps(idx.records) + (tree / "cache.json").read_text()

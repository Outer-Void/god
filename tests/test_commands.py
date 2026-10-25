from __future__ import annotations

import os
from pathlib import Path

import pytest

from god import commands, index
from tests.conftest import canary, capability, project


def test_path_order_shadowing_and_warnings(tmp_path: Path) -> None:
    marker = tmp_path / "ran"
    first, second = tmp_path / "first", tmp_path / "second"
    canary(first, "tool", marker)
    canary(second, "tool", marker)
    canary(second, "only-second", marker)
    (second / "not-executable").write_text("data")
    (second / "subdir").mkdir()
    (first / "link").symlink_to(second / "only-second")
    value = os.pathsep.join([str(first), str(second), str(first), "relative/bin", ""])
    doc = commands.discover(path_value=value)
    by_name = {c["name"]: c for c in doc["commands"]}
    assert sorted(by_name) == ["link", "only-second", "tool"]
    assert by_name["tool"]["path"] == str(first / "tool") and by_name["tool"]["shadows"] == [str(second / "tool")]
    assert by_name["link"]["resolves_to"] == str(second / "only-second")
    assert doc["shadowed"] == 1
    assert [w["issue"] for w in doc["warnings"]] == ["path-relative", "path-empty-entry"]
    assert not marker.exists()


def test_pattern(tmp_path: Path) -> None:
    for name in ("lrc", "lrc-dev", "dat"):
        canary(tmp_path / "bin", name, tmp_path / "ran")
    doc = commands.discover(pattern="lrc*", path_value=str(tmp_path / "bin"))
    assert [c["name"] for c in doc["commands"]] == ["lrc", "lrc-dev"]


def test_declared_entrypoints(tmp_path: Path) -> None:
    canary(tmp_path / "bin", "present", tmp_path / "ran")
    project(
        tmp_path / "p",
        "entry-proj",
        [
            capability("e.found", entrypoint="present blux-capability e.found"),
            capability("e.missing", entrypoint="absent-tool run"),
            capability("e.path", entrypoint="/usr/bin/env python3 x.py"),
            capability("e.quote", entrypoint="present 'unterminated"),
        ],
    )
    doc = commands.discover(path_value=str(tmp_path / "bin"), index=index.build([tmp_path / "p"]))
    status = {d["capability_id"]: d["status"] for d in doc["declared"]}
    assert status == {"e.found": "found", "e.missing": "missing", "e.path": "path", "e.quote": "unparseable"}
    assert not (tmp_path / "ran").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions")
def test_unreadable_path_dirs_are_skipped(tmp_path: Path) -> None:
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0)
    try:
        assert commands.discover(path_value=str(locked))["commands"] == []
    finally:
        locked.chmod(0o755)

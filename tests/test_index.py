"""Cache invalidation (docs/INDEX.md)."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from god import index, projects
from tests.conftest import capability, project


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    project(tmp_path / "roots" / "a", "proj-a", [capability("a.one")])
    project(tmp_path / "roots" / "b", "proj-b", [capability("b.one")])
    return tmp_path / "roots"


def cache(tree: Path) -> Path:
    return tree.parent / "index.json"


def stats(tree: Path, **kw: object) -> dict[str, object]:
    return index.build([tree], cache_path=cache(tree), **kw).cache  # type: ignore[arg-type]


def test_second_run_is_all_hits(tree: Path) -> None:
    first = stats(tree)
    assert (first["hits"], first["reloaded"], first["rebuilt"], first["reason"]) == (0, 2, True, "absent")
    assert stats(tree) == {"hits": 2, "reloaded": 0, "removed": 0, "rebuilt": False, "reason": None}


def test_editing_a_file_reloads_only_that_project(tree: Path) -> None:
    stats(tree)
    caps = tree / "a" / ".blux" / "capabilities.yaml"
    doc = json.loads(caps.read_text())
    doc["capabilities"][0]["version"] = "1.0.1"
    caps.write_text(json.dumps(doc))
    s = stats(tree)
    assert (s["hits"], s["reloaded"]) == (1, 1)
    assert stats(tree)["reloaded"] == 0  # and the new record was cached
    idx = index.build([tree], cache_path=cache(tree))
    assert next(p for p in idx.projects if p["project_id"] == "proj-a")["capabilities"][0]["version"] == "1.0.1"


def test_change_detection_without_size_change(tree: Path) -> None:
    stats(tree)
    caps = tree / "b" / ".blux" / "capabilities.yaml"
    text = caps.read_text()
    caps.write_text(text.replace("b.one", "b.two"))  # same length
    st = caps.stat()
    os.utime(caps, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))
    s = stats(tree)
    assert (s["hits"], s["reloaded"]) == (1, 1)


def test_adding_a_file_to_blux_reloads(tree: Path) -> None:
    stats(tree)
    (tree / "a" / ".blux" / "notes.txt").write_text("x")
    assert stats(tree)["reloaded"] == 1


def test_new_and_removed_projects(tree: Path) -> None:
    stats(tree)
    project(tree / "c", "proj-c", [capability("c.one")])
    shutil.rmtree(tree / "a")
    s = stats(tree)
    assert (s["hits"], s["reloaded"], s["removed"]) == (1, 1, 1)
    ids = [p["project_id"] for p in index.build([tree], cache_path=cache(tree)).projects]
    assert ids == ["proj-b", "proj-c"]


def test_a_fixed_manifest_stops_being_a_problem(tree: Path) -> None:
    manifest = tree / "a" / ".blux" / "manifest.yaml"
    good = manifest.read_text()
    manifest.write_text("broken: [\n")
    assert len(index.build([tree], cache_path=cache(tree)).problems) == 1
    manifest.write_text(good)
    assert index.build([tree], cache_path=cache(tree)).problems == []


@pytest.mark.parametrize("corruption", ["not json", '{"contract": "god.index", "version": 7}', "[]"])
def test_unreadable_cache_is_rebuilt(tree: Path, corruption: str) -> None:
    cache(tree).write_text(corruption)
    s = stats(tree)
    assert s["rebuilt"] is True and s["reloaded"] == 2
    assert json.loads(cache(tree).read_text())["contract"] == "god.index"


def test_generator_change_discards_the_cache(tree: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stats(tree)
    real = projects.sdk_info
    monkeypatch.setattr(projects, "sdk_info", lambda: {**real(), "version": "0.1.99"})
    s = stats(tree)
    assert (s["reason"], s["reloaded"]) == ("generator-changed", 2)


def test_refresh_ignores_the_cache(tree: Path) -> None:
    stats(tree)
    s = stats(tree, refresh=True)
    assert (s["reason"], s["reloaded"]) == ("refresh", 2)


def test_entries_for_other_roots_are_kept(tree: Path) -> None:
    other = project(tree.parent / "elsewhere", "far", [capability("far.one")])
    index.build([other], cache_path=cache(tree))
    stats(tree)
    entries = json.loads(cache(tree).read_text())["entries"]
    assert str(other) in entries and len(entries) == 3


def test_cached_answer_equals_fresh_answer(tree: Path) -> None:
    stats(tree)
    cached = index.build([tree], cache_path=cache(tree)).records
    fresh = index.build([tree]).records
    assert cached == fresh

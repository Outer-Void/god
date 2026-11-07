"""OV-51: GOD on malformed input. One hostile project or a damaged cache must never stop discovery.

Each test failed on ad6f0c4:
- a named pipe in .blux/ blocked `god check` for ever (the SDK opened it);
- a symbolic link in .blux/ was followed out of the project;
- deeply nested YAML raised RecursionError and ended the whole scan with a traceback;
- a damaged entry in the index cache crashed every later query (AttributeError, KeyError, TypeError).
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

import pytest

from god import index
from tests.conftest import capability, project


def _within(seconds: float, fn: Any) -> Any:
    box: list[Any] = []

    def target() -> None:
        try:
            box.append(fn())
        except BaseException as exc:  # returned to the test
            box.append(exc)

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(seconds)
    assert box, f"did not finish within {seconds} s"
    assert not isinstance(box[0], BaseException), repr(box[0])
    return box[0]


def _problems(roots: Path) -> dict[str, dict[str, Any]]:
    idx = _within(30, lambda: index.build([roots]))
    assert sorted(p["project_id"] for p in idx.projects) == ["good"]  # every other project is still found
    return {Path(p["root"]).name: p for p in idx.problems}


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="needs named pipes")
def test_pipes_links_and_deep_nesting_are_problems_not_hangs_or_crashes(tmp_path: Path) -> None:
    roots = tmp_path / "roots"
    project(roots / "good", "good", [capability("good.x")])
    project(roots / "pipe", "pipe", [capability("pipe.x")])
    (roots / "pipe" / ".blux" / "policy.yaml").unlink()
    os.mkfifo(roots / "pipe" / ".blux" / "policy.yaml")
    project(roots / "link", "link", [capability("link.x")])
    secret = tmp_path / "outside.yaml"
    (roots / "link" / ".blux" / "capabilities.yaml").rename(secret)
    os.symlink(secret, roots / "link" / ".blux" / "capabilities.yaml")
    project(roots / "deep", "deep", [capability("deep.x")])
    (roots / "deep" / ".blux" / "manifest.yaml").write_text("[" * 100_000)

    problems = _problems(roots)
    assert sorted(problems) == ["deep", "link", "pipe"]
    for name, file in (("pipe", "policy.yaml"), ("link", "capabilities.yaml")):
        assert (problems[name]["code"], problems[name]["file"]) == ("MALFORMED_INPUT", file)
        assert problems[name]["details"]["reason"] == "not_a_regular_file"
    assert problems["deep"]["code"] == "MALFORMED_INPUT"
    assert problems["deep"]["details"]["reason"] == "nesting_too_deep"


@pytest.fixture
def cached(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    roots = tmp_path / "roots"
    project(roots / "a", "proj-a", [capability("a.one")])
    cache = tmp_path / "index.json"
    fresh = index.build([roots], cache_path=cache)
    return roots, cache, {"projects": fresh.projects, "problems": fresh.problems}


DAMAGE = {
    "entry is a string": lambda e: "x",
    "entry is a list": lambda e: [],
    "record missing": lambda e: {"sig": e["sig"]},
    "record is a string": lambda e: {**e, "record": "x"},
    "record emptied": lambda e: {**e, "record": {"kind": "project"}},
    "record edited": lambda e: {**e, "record": {**e["record"], "capabilities": []}},
    "record for another root": lambda e: {**e, "record": {**e["record"], "root": "/elsewhere"}},
}


@pytest.mark.parametrize("damage", sorted(DAMAGE))
def test_a_damaged_cache_entry_is_re_read_not_trusted(cached: tuple[Path, Path, dict[str, Any]], damage: str) -> None:
    roots, cache, fresh = cached
    doc = json.loads(cache.read_text())
    key = next(iter(doc["entries"]))
    doc["entries"][key] = DAMAGE[damage](doc["entries"][key])
    cache.write_text(json.dumps(doc))
    idx = index.build([roots], cache_path=cache)
    assert {"projects": idx.projects, "problems": idx.problems} == fresh
    assert (idx.cache["hits"], idx.cache["reloaded"]) == (0, 1)
    assert index.build([roots], cache_path=cache).cache["hits"] == 1  # repaired on disk

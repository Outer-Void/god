from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

from god import blux_adapter
from tests.conftest import ROOT, call, capability, project

CTX = {
    "operation_id": "op_01J0000000000000000000000A",
    "parent_operation_id": "op_01J0000000000000000000000B",
    "session_id": "ses_01J0000000000000000000000A",
    "project_id": "god",
}


@pytest.fixture
def roots(tmp_path: Path) -> list[str]:
    project(tmp_path / "p", "provider", [capability("svc.run", version="2.0.0", side_effects="write")])
    return [str(tmp_path)]


def test_every_capability_answers(roots: list[str], tmp_path: Path) -> None:
    cases: list[tuple[str, dict[str, Any], str]] = [
        ("capability.discover", {"roots": roots, "query": "svc.*"}, "god.capabilities"),
        ("capability.describe", {"roots": roots, "capability_id": "svc.run"}, "god.capability"),
        ("capability.compat", {"roots": roots, "capability_id": "svc.run", "version_range": "^2"}, "god.compatibility"),
        ("project.describe", {"roots": roots, "project": "provider"}, "god.project"),
        ("command.discover", {"roots": roots, "path": "", "declared": True}, "god.commands"),
        ("registry.index", {"roots": roots, "index": str(tmp_path / "idx.json")}, "god.index-summary"),
    ]
    assert sorted(c for c, _, _ in cases) == sorted(blux_adapter.CAPABILITIES)
    for cid, payload, contract in cases:
        code, doc = call(cid, payload, CTX)
        assert code == 0, (cid, doc)
        assert doc["contract"] == contract
        assert doc["linkage"] == {**CTX, "capability_id": cid, "system": "blux"}
    assert (tmp_path / "idx.json").is_file()


def test_read_capabilities_never_write_a_cache(
    roots: list[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOD_INDEX", str(tmp_path / "must-not-exist.json"))
    for cid in ("capability.discover", "project.describe"):
        call(cid, {"roots": roots, "project": "provider"} if cid == "project.describe" else {"roots": roots}, CTX)
    assert not (tmp_path / "must-not-exist.json").exists()


def test_findings_are_results_and_lookups_are_errors(roots: list[str], tmp_path: Path) -> None:
    (Path(roots[0]) / "broken" / ".blux").mkdir(parents=True)
    (Path(roots[0]) / "broken" / ".blux" / "manifest.yaml").write_text("[")
    code, doc = call("capability.discover", {"roots": roots}, CTX)
    assert code == 0 and doc["problems"][0]["issue"] == "malformed-yaml"
    code, doc = call("capability.describe", {"roots": roots, "capability_id": "no.such"}, CTX)
    assert code == 1 and doc["error"]["code"] == "NOT_FOUND"
    code, doc = call("capability.discover", {"roots": [str(tmp_path / "missing")]}, CTX)
    assert code == 1 and doc["error"]["code"] == "ROOT_NOT_FOUND"


@pytest.mark.parametrize(
    ("cid", "payload"),
    [
        ("capability.discover", {"plugin": "x"}),
        ("capability.discover", {"roots": "not-a-list"}),
        ("capability.discover", {"roots": []}),
        ("capability.describe", {}),
        ("capability.discover", {"max_side_effects": "maybe"}),
        ("command.discover", {"declared": "yes"}),
        ("registry.index", {"refresh": 1}),
    ],
)
def test_bad_input(cid: str, payload: dict[str, Any]) -> None:
    code, doc = call(cid, payload)
    assert code == 1 and doc["error"]["code"] == "INVALID_INPUT"


def test_malformed_requests_and_internal_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    for raw in (b"nope", b"[]", b'{"input": []}', b'{"capability_id": "project.describe", "input": {}}'):
        out = io.StringIO()
        assert blux_adapter.main("capability.discover", io.BytesIO(raw), out) == 1
        assert json.loads(out.getvalue())["error"]["code"] == "INVALID_INPUT"

    def boom(*_: object) -> None:
        raise RuntimeError("bug")

    monkeypatch.setattr(blux_adapter, "_dispatch", boom)
    code, doc = call("capability.discover", {})
    assert code == 1 and doc["error"]["code"] == "INTERNAL_ERROR"


def test_own_dot_blux_is_valid_and_honest() -> None:
    from blux_sdk import dot_blux

    p = dot_blux.load(ROOT)
    assert p.project_id == "god" and p.manifest["role"] == "integrated"
    caps = {c.capability_id: c for c in p.capabilities()}
    assert sorted(caps) == sorted(blux_adapter.CAPABILITIES)
    assert {cid for cid, c in caps.items() if c.side_effects != "read"} == {"registry.index"}
    for c in caps.values():
        assert c.provider["entrypoint"] == f"god blux-capability {c.capability_id}"


def test_god_describes_itself(capsys: pytest.CaptureFixture[str]) -> None:
    code, doc = call("project.describe", {"roots": [str(ROOT)], "project": "god"})
    assert code == 0 and len(doc["capabilities"]) == len(blux_adapter.CAPABILITIES)

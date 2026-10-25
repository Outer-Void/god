from __future__ import annotations

import io
import json
import stat
import sys
from pathlib import Path
from typing import Any

import pytest

from god import blux_adapter
from god.cli import main

ROOT = Path(__file__).resolve().parent.parent


def capability(
    cid: str,
    *,
    version: str = "1.0.0",
    side_effects: str = "read",
    entrypoint: str | None = None,
    contract_versions: list[str] | None = None,
    labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "contract": "blux.capability",
        "contract_version": "1.0",
        "capability_id": cid,
        "version": version,
        "summary": f"{cid} for tests",
        "contract_versions": contract_versions or ["1.0"],
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "side_effects": side_effects,
        "required_permissions": [],
        "idempotent": True,
        "timeout_ms": 1000,
        "provider": {"repository": "Outer-Void/fake", "kind": "subprocess", "entrypoint": entrypoint or f"fake {cid}"},
    }
    if labels:
        doc["labels"] = labels
    return doc


def project(root: Path, project_id: str, caps: list[dict[str, Any]], *, role: str = "standalone") -> Path:
    """Write a valid .blux/ (JSON is valid YAML)."""
    d = root / ".blux"
    d.mkdir(parents=True, exist_ok=True)
    manifest = {
        "contract": "blux.project",
        "contract_version": "1.0",
        "project_id": project_id,
        "name": project_id.title(),
        "role": role,
        "capabilities": "capabilities.yaml",
        "policy": "policy.yaml",
    }
    (d / "manifest.yaml").write_text(json.dumps(manifest))
    (d / "capabilities.yaml").write_text(
        json.dumps({"contract": "blux.capability-set", "contract_version": "1.0", "capabilities": caps})
    )
    policy = {
        "contract": "blux.policy",
        "contract_version": "1.0",
        "policy_id": f"{project_id}-p",
        "default_effect": "deny",
        "rules": [],
    }
    (d / "policy.yaml").write_text(json.dumps(policy))
    return root


def canary(bindir: Path, name: str, marker: Path) -> Path:
    """An executable that records it was run. GOD must never run it."""
    bindir.mkdir(parents=True, exist_ok=True)
    exe = bindir / name
    exe.write_text(f"#!{sys.executable}\nopen({str(marker)!r}, 'a').write('ran\\n')\nprint('help text')\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return exe


def run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(argv)
    out, err = capsys.readouterr()
    return code, out, err


def run_json(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, Any]]:
    code, out, _ = run([*argv, "--json"], capsys)
    return code, json.loads(out)


def call(
    capability_id: str, payload: dict[str, Any], context: dict[str, Any] | None = None
) -> tuple[int, dict[str, Any]]:
    out = io.StringIO()
    raw = json.dumps({"capability_id": capability_id, "input": payload, "context": context or {"operation_id": "op_x"}})
    code = blux_adapter.main(capability_id, io.BytesIO(raw.encode()), out)
    lines = out.getvalue().splitlines()
    assert len(lines) == 1
    return code, json.loads(lines[0])


@pytest.fixture(autouse=True)
def _private_cache(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOD_INDEX", str(tmp_path_factory.mktemp("cache") / "index.json"))
    monkeypatch.delenv("GOD_ROOTS", raising=False)

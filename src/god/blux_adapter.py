"""BLUX capability adapter (`god blux-capability <capability_id>`), BLUX ADR-0009 subprocess protocol.

stdin:  {"capability_id": str, "input": {...}, "context": {"operation_id": ..., ...}}
stdout: exactly one JSON object
  exit 0  the capability's output (god.capabilities, god.capability, god.project, god.commands,
          god.compatibility or god.index-summary). Finding nothing, malformed manifests and duplicates are
          results: they are reported in the document.
  exit 1  {"error": {"code", "message", "details"}}: GOD could not answer (bad input, unknown id, missing root).

Through BLUX the read capabilities never use or write the index cache: every answer is a fresh scan, so the
declared side effect (`read`) is exact. Only registry.index writes, and only GOD's own cache file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import IO, Any

from god import commands, index, query
from god.errors import ErrorCode, GodError

MAX_REQUEST_BYTES = 1024 * 1024
CONTEXT_KEYS = ("operation_id", "parent_operation_id", "session_id", "project_id", "capability_id")
ALLOWED = {
    "capability.discover": {"roots", "query", "project", "max_side_effects", "provider_kind", "labels"},
    "capability.describe": {"roots", "capability_id", "project"},
    "capability.compat": {"roots", "capability_id", "project", "version_range", "contract_version"},
    "project.describe": {"roots", "project"},
    "command.discover": {"roots", "pattern", "path", "declared"},
    "registry.index": {"roots", "refresh", "index"},
}
CAPABILITIES = tuple(ALLOWED)


def _fail(code: str, message: str, details: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    return 1, {"error": {"code": code, "message": message, "details": details or {}}}


def _str(inp: dict[str, Any], key: str, *, required: bool = False) -> str | None:
    value = inp.get(key)
    if value is None:
        if required:
            raise GodError(ErrorCode.INVALID_INPUT, f"{key} is required.")
        return None
    if not isinstance(value, str) or not value or len(value) > 4096 or "\x00" in value:
        raise GodError(ErrorCode.INVALID_INPUT, f"{key} must be a non-empty string.")
    return value


def _roots(inp: dict[str, Any]) -> list[str]:
    roots = inp.get("roots", ["."])
    if not isinstance(roots, list) or not roots or len(roots) > 64 or not all(isinstance(r, str) and r for r in roots):
        raise GodError(ErrorCode.INVALID_INPUT, "roots must be a non-empty list of directory paths.")
    return roots


def _dispatch(capability_id: str, inp: dict[str, Any]) -> dict[str, Any]:
    if capability_id == "command.discover":
        declared = inp.get("declared", False)
        if not isinstance(declared, bool):
            raise GodError(ErrorCode.INVALID_INPUT, "declared must be a boolean.")
        idx = index.build(_roots(inp)) if declared else None
        path_value = inp["path"] if isinstance(inp.get("path"), str) else None
        return commands.discover(pattern=_str(inp, "pattern"), path_value=path_value, index=idx)
    if capability_id == "registry.index":
        refresh = inp.get("refresh", False)
        if not isinstance(refresh, bool):
            raise GodError(ErrorCode.INVALID_INPUT, "refresh must be a boolean.")
        target = _str(inp, "index")
        idx = index.build(
            _roots(inp), cache_path=Path(target) if target else index.default_index_path(), refresh=refresh
        )
        return {**query.header("index-summary", idx), "problems": idx.problems, "duplicates": query.duplicates(idx)}
    idx = index.build(_roots(inp))
    if capability_id == "capability.discover":
        labels = inp.get("labels")
        if labels is not None and not (isinstance(labels, dict) and all(isinstance(v, str) for v in labels.values())):
            raise GodError(ErrorCode.INVALID_INPUT, "labels must map names to strings.")
        return query.discover(
            idx,
            query=_str(inp, "query"),
            project=_str(inp, "project"),
            max_side_effects=_str(inp, "max_side_effects"),
            provider_kind=_str(inp, "provider_kind"),
            labels=labels,
        )
    if capability_id == "capability.describe":
        return query.describe_capability(
            idx, str(_str(inp, "capability_id", required=True)), project=_str(inp, "project")
        )
    if capability_id == "capability.compat":
        return query.compat(
            idx,
            str(_str(inp, "capability_id", required=True)),
            version_range=_str(inp, "version_range"),
            contract_version=_str(inp, "contract_version"),
            project=_str(inp, "project"),
        )
    return query.describe_project(idx, str(_str(inp, "project", required=True)))


def handle(capability_id: str, raw: bytes) -> tuple[int, dict[str, Any]]:
    if capability_id not in ALLOWED:
        return _fail("INVALID_INPUT", f"Unknown capability {capability_id!r}.")
    if len(raw) > MAX_REQUEST_BYTES:
        return _fail("INVALID_INPUT", "Request too large.")
    try:
        req = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _fail("INVALID_INPUT", "Request is not JSON.")
    if not isinstance(req, dict) or not isinstance(req.get("input"), dict):
        return _fail("INVALID_INPUT", "Request must be an object with an input object.")
    if req.get("capability_id") not in (None, capability_id):
        return _fail("INVALID_INPUT", "capability_id does not match the invoked capability.")
    inp: dict[str, Any] = req["input"]
    unknown = sorted(set(inp) - ALLOWED[capability_id])
    if unknown:
        return _fail("INVALID_INPUT", f"Unknown input keys: {', '.join(unknown)}.", {"unknown": unknown})
    try:
        doc = _dispatch(capability_id, inp)
    except GodError as exc:
        return _fail(exc.code.value, exc.message, exc.details)
    raw_ctx = req.get("context")
    ctx: dict[str, Any] = raw_ctx if isinstance(raw_ctx, dict) else {}
    link: dict[str, Any] = {k: ctx.get(k) if isinstance(ctx.get(k), str) else None for k in CONTEXT_KEYS}
    doc["linkage"] = {**link, "capability_id": capability_id, "system": "blux"}
    return 0, doc


def main(capability_id: str, stdin: IO[bytes] | None = None, stdout: IO[str] | None = None) -> int:
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout
    try:
        code, doc = handle(capability_id, stdin.read(MAX_REQUEST_BYTES + 1))
    except Exception as exc:  # noqa: BLE001 - the protocol must always answer with one document
        code, doc = _fail("INTERNAL_ERROR", "Internal GOD error.", {"exception_type": type(exc).__name__})
    stdout.write(json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    stdout.flush()
    return code

"""Reading one project's `.blux/` through the canonical BLUX SDK (blux_sdk.dot_blux).

GOD never interprets `.blux/` itself: manifest, capability set and policy are validated by the SDK's
schemas (contract v1), so GOD agrees with the BLUX runtime about what is valid. A project the SDK rejects
becomes a *problem* record with the SDK's error code, never an exception.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

from god.errors import ErrorCode, GodError

DOT_BLUX = ".blux"

try:
    from blux_sdk import dot_blux as _dot_blux
    from blux_sdk.errors import BluxError as _BluxError

    SDK_ERROR: str | None = None
except ImportError as exc:  # pragma: no cover - exercised by test_sdk_missing via a subprocess
    _dot_blux = None  # type: ignore[assignment]
    _BluxError = Exception  # type: ignore[assignment,misc]
    SDK_ERROR = str(exc)


def require_sdk() -> None:
    if SDK_ERROR is not None:
        raise GodError(
            ErrorCode.SDK_UNAVAILABLE,
            "GOD reads .blux/ through blux-sdk, which is not installed (pip install blux-sdk; see README).",
            details={"import_error": SDK_ERROR[:200]},
        )


def sdk_info() -> dict[str, Any]:
    require_sdk()
    from importlib import metadata

    from blux_sdk.versions import SUPPORTED_CONTRACT_VERSIONS

    try:
        version = metadata.version("blux-sdk")
    except metadata.PackageNotFoundError:
        version = "unknown"
    return {"name": "blux-sdk", "version": version, "contract_versions": list(SUPPORTED_CONTRACT_VERSIONS)}


def signature(root: Path) -> dict[str, list[int]]:
    """Cheap change detector for a project's .blux/: size, mtime, ctime and inode of every file in it, and of
    the directory itself (so adding, removing or renaming a file is a change too)."""
    sig: dict[str, list[int]] = {}
    d = root / DOT_BLUX
    try:
        st = d.lstat()
    except OSError:
        return sig
    sig["."] = [st.st_mtime_ns, st.st_ctime_ns, st.st_ino, 0]
    try:
        names = sorted(os.listdir(d))
    except OSError:
        return sig
    for name in names:
        try:
            fst = (d / name).lstat()
        except OSError:
            continue
        sig[name] = [fst.st_size, fst.st_mtime_ns, fst.st_ctime_ns, fst.st_ino]
    return sig


def _canonical(doc: Any) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _classify(code: str, details: dict[str, Any]) -> str:
    reason = details.get("reason")
    errors = details.get("errors") or []
    if code == "MALFORMED_INPUT":
        return {"invalid_yaml": "malformed-yaml", "too_large": "too-large"}.get(str(reason), "malformed")
    if code in ("UNSUPPORTED_CONTRACT_VERSION", "MALFORMED_CONTRACT_VERSION"):
        return "unsupported-contract-version"
    if code == "INVALID_ENVELOPE" and str(details.get("message", "")).startswith("Missing"):
        return "missing-file"
    if code == "SCHEMA_VALIDATION_FAILED" and any(e.get("keyword") == "unique" for e in errors):
        return "duplicate-capability"
    if code == "SCHEMA_VALIDATION_FAILED":
        return "schema-invalid"
    return "invalid"


def load(root: Path) -> dict[str, Any]:
    """{"kind": "project", ...} or {"kind": "problem", ...} for ROOT (a directory containing .blux/)."""
    require_sdk()
    root = Path(os.path.abspath(root))
    try:
        st = (root / DOT_BLUX).lstat()
        if not stat.S_ISDIR(st.st_mode):
            return _problem(root, "INVALID_ENVELOPE", ".blux is not a directory (symlinks are not followed).", {})
        project = _dot_blux.load(root)
    except _BluxError as exc:
        details = dict(getattr(exc, "details", {}) or {})
        message = str(getattr(exc, "message", exc))
        details.setdefault("message", message)
        return _problem(root, str(exc.code.value), message, details)
    except OSError as exc:
        return _problem(root, "IO_ERROR", f"Cannot read .blux/: {exc.strerror}.", {"errno": exc.errno})

    manifest, capset, policy = project.manifest, project.capability_set, project.policy
    capabilities = [c.to_document() for c in project.capabilities()]
    fingerprint = hashlib.sha256(_canonical([manifest, capset, policy]).encode("utf-8")).hexdigest()
    return {
        "kind": "project",
        "root": str(root),
        "project_id": manifest["project_id"],
        "name": manifest["name"],
        "description": manifest.get("description", ""),
        "role": manifest["role"],
        "repository": manifest.get("repository"),
        "labels": manifest.get("labels", {}),
        "contract_version": manifest["contract_version"],
        "files": {"capabilities": manifest["capabilities"], "policy": manifest["policy"]},
        "fingerprint": fingerprint,
        "capabilities": sorted(capabilities, key=lambda c: c["capability_id"]),
        "policy": policy,
    }


def _problem(root: Path, code: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    details = {k: v for k, v in details.items() if k != "message"}
    if isinstance(details.get("line"), int):
        message = f"{message.rstrip('.')} (line {details['line']})."
    return {
        "kind": "problem",
        "root": str(root),
        "code": code,
        "issue": _classify(code, {**details, "message": message}),
        "message": message[:500],
        "file": details.get("file"),
        "details": details,
    }

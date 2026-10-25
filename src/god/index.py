"""The local registry index and its invalidation (docs/INDEX.md).

Every query rescans the roots for `.blux/` directories (a cheap, directory-only walk). A project's cached
record is reused only if the stat signature of its `.blux/` (every file's size, mtime, ctime and inode, plus
the directory's) is unchanged; otherwise it is re-read through the SDK. Projects that disappeared are
dropped. The whole cache is discarded when GOD's or the SDK's version (or the supported contract versions)
differ from the ones that wrote it, or when it is unreadable. `refresh` ignores the cache entirely.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from god import __version__, projects
from god.errors import ErrorCode, GodError
from god.scan import find_projects, normalize_roots

INDEX_CONTRACT = "god.index"
MAX_INDEX_BYTES = 128 * 1024 * 1024


def default_index_path() -> Path:
    env = os.environ.get("GOD_INDEX")
    if env:
        return Path(env)
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return Path(base) / "god" / "index.json"


@dataclass
class Index:
    roots: list[Path]
    records: list[dict[str, Any]]
    cache: dict[str, Any] = field(default_factory=dict)

    @property
    def projects(self) -> list[dict[str, Any]]:
        return [r for r in self.records if r["kind"] == "project"]

    @property
    def problems(self) -> list[dict[str, Any]]:
        return [r for r in self.records if r["kind"] == "problem"]

    def summary(self) -> dict[str, Any]:
        return {
            "roots": [str(r) for r in self.roots],
            "projects": len(self.projects),
            "problems": len(self.problems),
            "cache": self.cache,
        }


def _generator() -> dict[str, Any]:
    return {"god": __version__, "sdk": projects.sdk_info()}


def _read_cache(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        if path.stat().st_size > MAX_INDEX_BYTES:
            return None, "too-large"
        doc = json.loads(path.read_bytes())
    except FileNotFoundError:
        return None, "absent"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "unreadable"
    if not isinstance(doc, dict) or doc.get("contract") != INDEX_CONTRACT or doc.get("version") != 1:
        return None, "wrong-format"
    if doc.get("generator") != _generator():
        return None, "generator-changed"
    if not isinstance(doc.get("entries"), dict):
        return None, "wrong-format"
    return doc, None


def _write_cache(path: Path, entries: dict[str, Any]) -> None:
    doc = {"contract": INDEX_CONTRACT, "version": 1, "generator": _generator(), "entries": entries}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".index-", dir=path.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
        os.replace(tmp, path)
    except OSError as exc:
        with contextlib.suppress(OSError, UnboundLocalError):
            os.unlink(tmp)
        raise GodError(ErrorCode.IO_ERROR, f"Cannot write the index {path}: {exc.strerror}.") from None


def _under(path: str, roots: list[Path]) -> bool:
    p = Path(path)
    return any(p == r or p.is_relative_to(r) for r in roots)


def build(roots: list[str] | list[Path], *, cache_path: Path | None = None, refresh: bool = False) -> Index:
    """Index the roots. With cache_path, reuse and update that cache (see the module docstring)."""
    projects.require_sdk()
    root_paths = normalize_roots([str(r) for r in roots])
    cached_entries: dict[str, Any] = {}
    reason = "disabled" if cache_path is None else ("refresh" if refresh else None)
    if cache_path is not None and not refresh:
        doc, reason = _read_cache(cache_path)
        if doc is not None:
            cached_entries = doc["entries"]
    hits = reloaded = 0

    found = find_projects(root_paths)
    fresh: dict[str, Any] = {}
    for d in found:
        key = str(d)
        sig = projects.signature(d)
        entry = cached_entries.get(key)
        if entry is not None and entry.get("sig") == sig:
            hits += 1
            fresh[key] = entry
        else:
            reloaded += 1
            fresh[key] = {"sig": sig, "record": projects.load(d)}
    stale = [k for k in cached_entries if _under(k, root_paths) and k not in fresh]
    stats: dict[str, Any] = {
        "hits": hits,
        "reloaded": reloaded,
        "removed": len(stale),
        "rebuilt": reason is not None,
        "reason": reason,
    }

    if cache_path is not None:
        merged = {k: v for k, v in cached_entries.items() if not _under(k, root_paths)}
        merged.update(fresh)
        _write_cache(cache_path, merged)
    records = [fresh[k]["record"] for k in sorted(fresh)]
    return Index(root_paths, records, stats)

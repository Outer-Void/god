"""command.discover: what is on PATH, statically. GOD 1.x ran every program on PATH with ten different help
and version flags to scrape their output; GOD 2 never executes anything. It lists names, the path that wins,
the paths it shadows, and whether the executables that capabilities declare as entrypoints resolve."""

from __future__ import annotations

import fnmatch
import os
import shlex
import stat
import sys
from pathlib import Path
from typing import Any

from god.errors import ErrorCode, GodError
from god.index import Index
from god.query import header

MAX_COMMANDS = 100_000
IS_WINDOWS = sys.platform == "win32"


def _pathext() -> list[str]:
    return [e.lower() for e in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if e]


def _is_executable(entry: os.DirEntry[str]) -> bool:
    try:
        st = entry.stat()  # follows a symlink to check the target is a regular file; never runs it
    except OSError:
        return False
    if not stat.S_ISREG(st.st_mode):
        return False
    if IS_WINDOWS:
        return Path(entry.name).suffix.lower() in _pathext()
    return bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)) and os.access(entry.path, os.X_OK)


def _name(file_name: str) -> str:
    if IS_WINDOWS:
        stem, ext = os.path.splitext(file_name)
        if ext.lower() in _pathext():
            return stem.lower()
    return file_name


def scan_path(path_value: str) -> tuple[dict[str, list[str]], list[dict[str, Any]]]:
    """{name: [winning path, shadowed paths...]} in PATH order, and warnings about PATH itself."""
    found: dict[str, list[str]] = {}
    warnings: list[dict[str, Any]] = []
    seen_dirs: set[str] = set()
    for raw in path_value.split(os.pathsep):
        if not raw:
            warnings.append(
                {"issue": "path-empty-entry", "message": "PATH has an empty entry (means the current directory)."}
            )
            continue
        if not os.path.isabs(raw):
            warnings.append(
                {
                    "issue": "path-relative",
                    "entry": raw,
                    "message": f"PATH entry {raw!r} is relative to the current directory.",
                }
            )
        d = os.path.abspath(raw)
        if d in seen_dirs:
            continue
        seen_dirs.add(d)
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError:
            continue
        for e in entries:
            if _is_executable(e):
                found.setdefault(_name(e.name), []).append(e.path)
                if len(found) > MAX_COMMANDS:
                    raise GodError(ErrorCode.LIMIT_EXCEEDED, f"More than {MAX_COMMANDS} commands on PATH.")
    return found, warnings


def discover(
    *, pattern: str | None = None, path_value: str | None = None, index: Index | None = None
) -> dict[str, Any]:
    path_value = os.environ.get("PATH", "") if path_value is None else path_value
    found, warnings = scan_path(path_value)
    commands = []
    for name in sorted(found):
        if pattern and not fnmatch.fnmatchcase(name, pattern):
            continue
        paths = found[name]
        item: dict[str, Any] = {"name": name, "path": paths[0], "shadows": paths[1:]}
        real = os.path.realpath(paths[0])
        if real != paths[0]:
            item["resolves_to"] = real
        commands.append(item)
    declared = []
    if index is not None:
        for p in index.projects:
            for c in p["capabilities"]:
                prov = c["provider"]
                if prov.get("kind") != "subprocess":
                    continue
                entry = {
                    "capability_id": c["capability_id"],
                    "project_id": p["project_id"],
                    "entrypoint": prov.get("entrypoint"),
                }
                try:
                    argv = shlex.split(prov.get("entrypoint") or "")
                except ValueError:
                    argv = []
                if not argv:
                    declared.append({**entry, "status": "unparseable"})
                    continue
                exe = argv[0]
                entry["executable"] = exe
                if os.path.isabs(exe) or os.sep in exe:
                    declared.append({**entry, "status": "path", "message": "Entrypoint names a path, not a command."})
                    continue
                hit = found.get(_name(exe) if IS_WINDOWS else exe)
                declared.append({**entry, "status": "found", "path": hit[0]} if hit else {**entry, "status": "missing"})
        declared.sort(key=lambda d: (d["capability_id"], d["project_id"]))
    return {
        **header("commands", index),
        "query": {"pattern": pattern, "path_entries": len(path_value.split(os.pathsep)) if path_value else 0},
        "commands": commands,
        "shadowed": sum(1 for c in commands if c["shadows"]),
        "declared": declared,
        "warnings": warnings,
    }

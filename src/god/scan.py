"""Finding projects: every directory under the roots that contains `.blux/manifest.yaml`.

Bounded and read-only: symlinked directories are not followed, VCS, dependency and cache directories are
skipped, depth and directory count are capped. The walk is sorted, so the same tree gives the same order.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from god.errors import ErrorCode, GodError

MAX_DEPTH = 6
MAX_DIRS = 200_000
SKIP = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".tox",
        "build",
        "dist",
        "site-packages",
        ".lrc",
    }
)


def normalize_roots(roots: list[str] | list[Path]) -> list[Path]:
    out: list[Path] = []
    for r in roots:
        p = Path(os.path.abspath(os.path.expanduser(str(r))))
        if not p.is_dir():
            raise GodError(ErrorCode.ROOT_NOT_FOUND, f"Root {r} is not a directory.", details={"root": str(r)})
        if p not in out:
            out.append(p)
    return sorted(out)


def find_projects(roots: list[Path], *, max_depth: int = MAX_DEPTH) -> list[Path]:
    found: set[Path] = set()
    seen_dirs = 0

    def walk(d: Path, depth: int) -> None:
        nonlocal seen_dirs
        seen_dirs += 1
        if seen_dirs > MAX_DIRS:
            raise GodError(ErrorCode.LIMIT_EXCEEDED, f"More than {MAX_DIRS} directories under the roots.")
        try:
            manifest = (d / ".blux" / "manifest.yaml").lstat()
            if stat.S_ISREG(manifest.st_mode):
                found.add(d)
        except OSError:
            pass
        if depth >= max_depth:
            return
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError:
            return
        for e in entries:
            if e.name in SKIP or (e.name.startswith(".") and e.name != ".blux"):
                continue
            if e.name == ".blux":
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    walk(Path(e.path), depth + 1)
            except OSError:
                continue

    for root in roots:
        walk(root, 0)
    return sorted(found)

"""GOD owns discovery, not orchestration (docs/AUDIT-1.0.md). These tests pin the isolation defects of GOD 1.x
shut: it ran every program on PATH, routed into other tools, and configured logging on import."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import god
from tests.conftest import ROOT, call, canary, capability, project, run

SOURCES = sorted((ROOT / "src" / "god").rglob("*.py"))


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_god_never_spawns_processes() -> None:
    # GOD 1.x ran each PATH program up to ten times (`--help`, `-h`, `help`, `-v`, `version` ...), with the
    # caller's environment, 32 at a time. `shutdown -h`, `rm help` and anything reading stdin were possible.
    for path in SOURCES:
        bad = _imports(path) & {"subprocess", "multiprocessing", "pty", "concurrent.futures"}
        assert not bad, f"{path.name} imports {bad}"
        text = path.read_text()
        for call_name in ("os.system", "os.popen", "os.exec", "os.spawn", "os.startfile"):
            assert call_name not in text, f"{path.name} uses {call_name}"


def test_god_is_not_a_runtime_or_a_policy_engine() -> None:
    for path in SOURCES:
        imported = _imports(path)
        assert not {m for m in imported if m.split(".")[0] in ("blux_runtime", "blux_cli", "lrc", "dat")}, path.name
        assert not {
            m
            for m in imported
            if m.startswith("blux_sdk") and m not in ("blux_sdk", "blux_sdk.errors", "blux_sdk.versions")
        }
    # The SDK is reached only through dot_blux (projects.py) and version helpers: no envelopes, no execution.
    assert "execution_request" not in "".join(p.read_text() for p in SOURCES)


@pytest.mark.parametrize("argv", [["commands"], ["commands", "--declared"], ["capabilities"], ["check"]])
def test_discovered_programs_are_never_run(tmp_path: Path, capsys: pytest.CaptureFixture[str], argv: list[str]) -> None:
    marker = tmp_path / "ran.txt"
    bindir = tmp_path / "bin"
    for name in ("shutdown", "rm", "fake", "god-canary"):
        canary(bindir, name, marker)
    project(tmp_path / "proj", "canary-proj", [capability("canary.run", entrypoint="god-canary --go")])
    extra = ["--path", str(bindir)] if argv[0] == "commands" else []
    code, out, _ = run([*argv, *extra, "-r", str(tmp_path / "proj")], capsys)
    assert code == 0, out
    code, doc = call("command.discover", {"path": str(bindir), "declared": True, "roots": [str(tmp_path / "proj")]})
    assert code == 0 and {c["name"] for c in doc["commands"]} >= {"shutdown", "rm", "god-canary"}
    assert doc["declared"][0]["status"] == "found"
    assert not marker.exists(), "GOD executed a discovered program"


@pytest.mark.parametrize("old", ["build", "search", "info", "stats", "blux", "completion"])
def test_gods_1x_commands_are_removed_loudly(old: str, capsys: pytest.CaptureFixture[str]) -> None:
    code, _, err = run([old, "x"], capsys)
    assert code == 2 and "removed in 2.0" in err


def test_import_has_no_side_effects() -> None:
    code = (
        "import logging, sys, god, god.cli, god.blux_adapter;"
        "assert not logging.getLogger().handlers, 'configured logging';"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in ('typer', 'rich', 'click', 'blux_runtime'));"
        "assert not bad, bad"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr


def test_one_version() -> None:
    # 1.x: help said v1.0.0, the package 1.0.1, the tag v1.0.0, and a test asserted 1.0.0.
    meta = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    proc = subprocess.run([sys.executable, "-m", "god", "--version"], capture_output=True, text=True, cwd=ROOT)
    assert meta == god.__version__ and proc.stdout.strip() == f"god {meta}"


def test_no_top_level_src_package() -> None:
    # 1.x shipped src/__init__.py, which made `import src` a thing.
    assert not (ROOT / "src" / "__init__.py").exists()


def test_every_module_imports_on_its_own() -> None:
    for path in SOURCES:
        if path.name == "__main__.py":
            continue
        mod = "god." + path.relative_to(ROOT / "src" / "god").with_suffix("").as_posix().replace("/", ".")
        mod = mod.removesuffix(".__init__")
        proc = subprocess.run([sys.executable, "-c", f"import {mod}"], capture_output=True, text=True, cwd=ROOT)
        assert proc.returncode == 0, f"{mod}: {proc.stderr}"


def test_missing_sdk_is_an_explicit_error(tmp_path: Path) -> None:
    blocker = tmp_path / "blux_sdk"
    blocker.mkdir()
    (blocker / "__init__.py").write_text("raise ImportError('blocked for the test')\n")
    env = {**os.environ, "PYTHONPATH": f"{tmp_path}{os.pathsep}{ROOT / 'src'}"}
    proc = subprocess.run(
        [sys.executable, "-m", "god", "capabilities", "--no-cache", "--json"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    assert proc.returncode == 3 and '"SDK_UNAVAILABLE"' in proc.stdout

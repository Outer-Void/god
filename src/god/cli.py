#!/usr/bin/env python3
"""
GOD CLI v1.0.0 - Professional Grade Global Operations Deity.
Enhanced with security, performance, and enterprise features.
"""

from __future__ import annotations

import html as html_module
import importlib
import json
import logging
import os
import platform
import shutil
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

# ============================================================================
# CONFIGURATION
# ============================================================================
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("god.cli")

console = Console(force_terminal=True, highlight=False)

app = typer.Typer(
    name="god",
    help="🚀 GOD v1.0.0 - Global Operations Deity\nProfessional-grade global help indexer with BLUX integration.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================
class OutputFormat(str, Enum):
    md = "md"
    json = "json"
    console = "console"
    html = "html"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CommandResult:
    name: str
    path: str
    success: bool
    output: str
    error: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    help_flag: str = ""
    version: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    category: str = "unknown"
    last_modified: Optional[float] = None
    file_size: Optional[int] = None

    def to_json(self) -> Dict[str, Any]:
        d = asdict(self)
        d["risk_level"] = self.risk_level.value
        d["last_modified"] = (
            datetime.fromtimestamp(self.last_modified).isoformat() if self.last_modified else None
        )
        return d


# ============================================================================
# SECURITY AUDIT
# ============================================================================
class SecurityAudit:
    """Enhanced security audit for commands."""

    CRITICAL_COMMANDS = {
        "rm",
        "dd",
        "mkfs",
        "fdisk",
        "parted",
        "lvremove",
        "vgremove",
        "pvremove",
        "cryptsetup",
        "wipefs",
        "shred",
        "debugfs",
        "chown",
        "chmod",
        "mount",
        "umount",
    }

    HIGH_RISK_COMMANDS = {
        "iptables",
        "systemctl",
        "service",
        "kill",
        "pkill",
        "killall",
        "init",
        "telinit",
        "shutdown",
        "reboot",
        "halt",
        "poweroff",
    }

    MEDIUM_RISK_COMMANDS = {
        "sudo",
        "su",
        "passwd",
        "useradd",
        "userdel",
        "groupadd",
        "groupdel",
    }

    @classmethod
    def assess_risk(cls, name: str, path: str) -> RiskLevel:
        """Comprehensive risk assessment."""
        name_lower = name.lower()
        path_lower = path.lower()

        # Critical commands
        if name_lower in cls.CRITICAL_COMMANDS:
            return RiskLevel.CRITICAL

        # High risk commands
        if name_lower in cls.HIGH_RISK_COMMANDS:
            return RiskLevel.HIGH

        # Medium risk commands
        if name_lower in cls.MEDIUM_RISK_COMMANDS:
            return RiskLevel.MEDIUM

        # System directories indicate elevated privileges
        system_dirs = ["/sbin", "/usr/sbin", "/system", "/windows/system32"]
        if any(sd in path_lower for sd in system_dirs):
            return RiskLevel.MEDIUM

        return RiskLevel.LOW


# ============================================================================
# COMMAND PROCESSOR
# ============================================================================
class CommandProcessor:
    """Professional command processor with parallel execution."""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.help_flags = ["--help", "-h", "/?", "-help", "help"]
        self.version_flags = ["--version", "-V", "-v", "/version", "version"]

    def _get_file_info(self, path: Path) -> Tuple[Optional[float], Optional[int]]:
        """Get file metadata safely."""
        try:
            stat_info = path.stat()
            return stat_info.st_mtime, stat_info.st_size
        except (OSError, ValueError):
            return None, None

    def _is_executable(self, path: Path) -> bool:
        """Enhanced executable detection."""
        try:
            if not path.exists():
                return False

            st = path.stat()
            if not stat.S_ISREG(st.st_mode):
                return False

            system = platform.system().lower()
            if system == "windows":
                return path.suffix.lower() in (".exe", ".bat", ".cmd", ".ps1", ".com")
            else:
                return os.access(str(path), os.X_OK)
        except (OSError, ValueError, PermissionError) as e:
            logger.debug(f"Executable check failed for {path}: {e}")
            return False

    def _path_executables(self) -> Dict[str, Path]:
        """Enhanced PATH scanning with better filtering."""
        seen: Dict[str, Path] = {}
        path_env = os.environ.get("PATH", "")
        path_dirs = [
            Path(d).expanduser().resolve() for d in path_env.split(os.pathsep) if d.strip()
        ]

        for path_dir in path_dirs:
            if not path_dir.is_dir():
                continue
            try:
                for child in path_dir.iterdir():
                    if child.name in seen:
                        continue
                    if self._is_executable(child):
                        seen[child.name] = child
            except (PermissionError, OSError) as e:
                logger.warning(f"Could not scan directory {path_dir}: {e}")
                continue

        return seen

    def _run_capture(self, cmd: List[str], timeout: float) -> Tuple[int, str, str, float]:
        """Enhanced command execution with better error handling."""
        start = time.time()
        env = os.environ.copy()
        env.setdefault("LC_ALL", "C")
        env.setdefault("LANG", "C")

        try:
            p = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
                text=True,
                encoding="utf-8",
                errors="ignore",
                env=env,
            )
            return p.returncode, p.stdout, p.stderr, time.time() - start
        except subprocess.TimeoutExpired:
            return 124, "", "[timeout]", time.time() - start
        except Exception as e:
            logger.error(f"Command execution failed for {cmd}: {e}")
            return 125, "", f"[error: {e}]", time.time() - start

    def _extract_help(self, bin_path: Path, timeout: float) -> Tuple[str, str, float, int, str]:
        """Enhanced help extraction with multiple flag attempts."""
        for flag in self.help_flags:
            code, out, err, t = self._run_capture([str(bin_path), flag], timeout)
            text = out or err
            if text and len(text.strip()) > 10 and not text.startswith("["):
                return flag, text, t, code, err
        return "", "[No help output captured]", 0.0, 0, ""

    def _extract_version(self, bin_path: Path, timeout: float) -> str:
        """Enhanced version extraction."""
        for flag in self.version_flags:
            _, out, err, _ = self._run_capture([str(bin_path), flag], timeout)
            text = (out or err).strip()
            if text and not text.startswith("[") and len(text) > 0:
                # Return first line, truncated to reasonable length
                return text.splitlines()[0][:200]
        return ""

    def _categorize(self, name: str, help_text: str) -> str:
        """Enhanced command categorization."""
        CATEGORIES = {
            "devops": {"docker", "kubectl", "terraform", "ansible", "helm", "vagrant", "k8s"},
            "network": {
                "curl",
                "wget",
                "ssh",
                "ping",
                "dig",
                "ip",
                "netstat",
                "nmap",
                "nc",
                "telnet",
            },
            "system": {"systemctl", "ps", "top", "mount", "kill", "journalctl", "htop", "df", "du"},
            "files": {"ls", "cp", "mv", "rm", "find", "chmod", "tar", "zip", "rsync", "gzip"},
            "development": {"git", "npm", "pip", "python", "node", "go", "make", "cargo", "java"},
            "text": {"grep", "sed", "awk", "cat", "less", "head", "tail", "vim", "nano", "echo"},
            "security": {"ssh", "gpg", "openssl", "certutil", "security", "keytool"},
        }

        # Check exact name match first
        for cat, keys in CATEGORIES.items():
            if name in keys:
                return cat

        # Check help text for keywords
        hl = (help_text or "").lower()
        for cat, keys in CATEGORIES.items():
            if any(k in hl for k in keys):
                return cat

        return "unknown"

    def process_single(self, name: str, path: Path, timeout: float) -> CommandResult:
        """Process a single command with enhanced metadata."""
        last_modified, file_size = self._get_file_info(path)
        flag, help_out, t_help, code, err = self._extract_help(path, timeout)
        ver = self._extract_version(path, timeout)
        risk = SecurityAudit.assess_risk(name, str(path))
        cat = self._categorize(name, help_out)

        return CommandResult(
            name=name,
            path=str(path),
            success=bool(help_out and not help_out.startswith("[No help")),
            output=help_out,
            error=err,
            exit_code=code,
            execution_time=t_help,
            help_flag=flag,
            version=ver,
            risk_level=risk,
            category=cat,
            last_modified=last_modified,
            file_size=file_size,
        )

    def process_batch(self, commands: Dict[str, Path], timeout: float) -> List[CommandResult]:
        """Process commands in parallel for better performance."""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_cmd = {
                executor.submit(self.process_single, name, path, timeout): name
                for name, path in commands.items()
            }

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Processing commands...", total=len(commands))

                for future in as_completed(future_to_cmd):
                    name = future_to_cmd[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Failed to process {name}: {e}")
                        results.append(
                            CommandResult(
                                name=name,
                                path=str(commands[name]),
                                success=False,
                                output="",
                                error=str(e),
                                risk_level=RiskLevel.LOW,
                                category="unknown",
                            )
                        )
                    progress.update(task, advance=1)

        return results


# ============================================================================
# OUTPUT RENDERERS
# ============================================================================
def _risk_color(risk: RiskLevel) -> str:
    """Get color for risk level badge."""
    colors = {
        RiskLevel.LOW: "green",
        RiskLevel.MEDIUM: "yellow",
        RiskLevel.HIGH: "orange",
        RiskLevel.CRITICAL: "red",
    }
    return colors.get(risk, "gray")


def _render_md(results: List[CommandResult], title: str) -> str:
    """Render results as Markdown."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# {title}",
        "",
        f"**Generated**: {ts} | **Platform**: {platform.system()} | **Total**: {len(results)} | **Successful**: {sum(1 for r in results if r.success)}",
        "",
    ]

    for r in sorted(results, key=lambda x: x.name):
        risk_badge = f"![{r.risk_level.value}](https://img.shields.io/badge/risk-{r.risk_level.value}-{_risk_color(r.risk_level)})"
        lines += [
            f"## {r.name} {risk_badge}",
            f"- **Path**: `{r.path}`",
            f"- **Category**: {r.category}",
            f"- **Version**: {r.version or 'N/A'}",
            f"- **Execution Time**: {r.execution_time:.2f}s",
            f"- **Success**: {'✅' if r.success else '❌'}",
            "",
            "### Help Output",
            "",
            "```",
            r.output.strip(),
            "```",
            "",
        ]

    return "\n".join(lines)


def _render_json(results: List[CommandResult]) -> str:
    """Render results as JSON."""
    payload = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "platform": platform.system(),
            "total": len(results),
            "successful": sum(1 for r in results if r.success),
            "risk_summary": {
                "low": sum(1 for r in results if r.risk_level == RiskLevel.LOW),
                "medium": sum(1 for r in results if r.risk_level == RiskLevel.MEDIUM),
                "high": sum(1 for r in results if r.risk_level == RiskLevel.HIGH),
                "critical": sum(1 for r in results if r.risk_level == RiskLevel.CRITICAL),
            },
        },
        "commands": [r.to_json() for r in results],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _render_console(results: List[CommandResult], title: str) -> None:
    """Render results to console."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Command", style="bold")
    table.add_column("Category")
    table.add_column("Risk", justify="center")
    table.add_column("Version", style="dim")
    table.add_column("Success", justify="center")

    for r in sorted(results, key=lambda x: x.name)[:50]:
        risk_color = {
            RiskLevel.LOW: "green",
            RiskLevel.MEDIUM: "yellow",
            RiskLevel.HIGH: "red",
            RiskLevel.CRITICAL: "bold red",
        }.get(r.risk_level, "white")

        table.add_row(
            r.name,
            r.category,
            f"[{risk_color}]{r.risk_level.value.upper()}[/{risk_color}]",
            (r.version or "N/A")[:20],
            "✅" if r.success else "❌",
        )

    console.print(table)
    if len(results) > 50:
        console.print(f"[dim]Showing 50 of {len(results)} commands[/dim]")


def _render_html(results: List[CommandResult], title: str) -> str:
    """Render results as HTML."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(results)
    success = sum(1 for r in results if r.success)
    risk_counts = {
        "low": sum(1 for r in results if r.risk_level == RiskLevel.LOW),
        "medium": sum(1 for r in results if r.risk_level == RiskLevel.MEDIUM),
        "high": sum(1 for r in results if r.risk_level == RiskLevel.HIGH),
        "critical": sum(1 for r in results if r.risk_level == RiskLevel.CRITICAL),
    }

    rows = []
    for r in sorted(results, key=lambda x: x.name):
        risk_class = f"risk-{r.risk_level.value}"
        rows.append(
            "<tr>"
            f"<td><strong>{html_module.escape(r.name)}</strong></td>"
            f"<td><code>{html_module.escape(r.path)}</code></td>"
            f'<td class="{risk_class}">{html_module.escape(r.risk_level.value.upper())}</td>'
            f"<td>{html_module.escape(r.category)}</td>"
            f"<td>{html_module.escape(r.version or 'N/A')}</td>"
            f"<td>{'✅' if r.success else '❌'}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html_module.escape(title)}</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #0a6;
            border-bottom: 2px solid #0a6;
            padding-bottom: 10px;
        }}
        .meta {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card strong {{
            display: block;
            font-size: 1.5em;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        .risk-low {{ color: #28a745; font-weight: 600; }}
        .risk-medium {{ color: #ffc107; font-weight: 600; }}
        .risk-high {{ color: #fd7e14; font-weight: 600; }}
        .risk-critical {{ color: #dc3545; font-weight: 700; }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>{html_module.escape(title)}</h1>

    <div class="meta">
        <p><strong>Generated:</strong> {html_module.escape(ts)}</p>
        <p><strong>Platform:</strong> {html_module.escape(platform.system())}</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            Total Commands <strong>{total}</strong>
        </div>
        <div class="stat-card">
            Successful <strong>{success}</strong>
        </div>
        <div class="stat-card">
            Low Risk <strong style="color: #28a745;">{risk_counts['low']}</strong>
        </div>
        <div class="stat-card">
            Medium Risk <strong style="color: #ffc107;">{risk_counts['medium']}</strong>
        </div>
        <div class="stat-card">
            High Risk <strong style="color: #fd7e14;">{risk_counts['high']}</strong>
        </div>
        <div class="stat-card">
            Critical Risk <strong style="color: #dc3545;">{risk_counts['critical']}</strong>
        </div>
    </div>

    <h2>Command Index</h2>
    <table>
        <thead>
            <tr>
                <th>Command</th>
                <th>Path</th>
                <th>Risk</th>
                <th>Category</th>
                <th>Version</th>
                <th>Success</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</body>
</html>"""
    return html


# ============================================================================
# BLUX INTEGRATION
# ============================================================================
BLUX_BIN_ALIASES: Dict[str, Tuple[str, Optional[str], List[str]]] = {
    "q": ("bluxq_cli", None, ["bluxq", "bq"]),
    "dat": ("outervoid.dat", None, ["dat"]),
    "lrc": ("outervoid.lrc", None, ["lrc"]),
    "scan": ("outervoid.dat_scan", None, ["dat-scan", "dat_scan"]),
}

blux = typer.Typer(name="blux", help="BLUX ecosystem integration (soft routes)")
app.add_typer(blux, name="blux")


def _import_typer_app(mod_name: str, attr: Optional[str] = None):
    """Safely import a typer app."""
    try:
        mod = importlib.import_module(mod_name)
        return getattr(mod, attr) if attr else mod
    except Exception as e:
        logger.debug(f"Failed to import {mod_name}: {e}")
        return None


def _run_fallback(binaries: List[str], argv: List[str]) -> int:
    """Run fallback binary if import fails."""
    for b in binaries:
        prog = shutil.which(b)
        if prog:
            p = subprocess.run([prog] + argv, text=True)
            return p.returncode
    console.print(f"[red]❌ No fallback binary found for: {', '.join(binaries)}[/red]")
    return 127


def _mount_blux_route(route: str, module: str, attr: Optional[str], fallbacks: List[str]):
    """Mount a BLUX route."""

    @blux.command(route)
    def _route_cmd(args: List[str] = typer.Argument(None, allow_dash=True)):
        argv = args or []
        app_or_mod = _import_typer_app(module, attr)

        if app_or_mod is not None and hasattr(app_or_mod, "app"):
            return app_or_mod.app()
        if app_or_mod is not None and callable(getattr(app_or_mod, "main", None)):
            return app_or_mod.main()
        return _run_fallback(fallbacks, argv)


for r, (mod, attr, falls) in BLUX_BIN_ALIASES.items():
    _mount_blux_route(r, mod, attr, falls)


# ============================================================================
# CLI COMMANDS
# ============================================================================
@app.command("build")
def build_cmd(
    out: str = typer.Option("docs/help.md", "--out", "-o", help="Output file path"),
    fmt: OutputFormat = typer.Option(OutputFormat.md, "--format", "-f", help="Output format"),
    timeout: float = typer.Option(2.0, "--timeout", help="Per-command timeout (seconds)"),
    limit: int = typer.Option(0, "--limit", help="Limit number of commands (0 = unlimited)"),
    max_workers: int = typer.Option(None, "--max-workers", help="Max parallel workers"),
):
    """Build unified help documentation by scanning PATH executables."""
    processor = CommandProcessor(max_workers=max_workers)
    exes = processor._path_executables()
    names = sorted(exes.keys())

    if limit and limit > 0:
        names = names[:limit]
        console.print(f"[dim]Limiting to {limit} commands[/dim]")

    console.print(f"[bold]Found {len(names)} executable commands[/bold]")
    results = processor.process_batch({n: exes[n] for n in names}, timeout)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    title = "GOD — Global Help Index"

    if fmt == OutputFormat.md:
        Path(out).write_text(_render_md(results, title), encoding="utf-8")
        console.print(f"[green]✓ Wrote Markdown:[/green] {out}")
    elif fmt == OutputFormat.html:
        Path(out).write_text(_render_html(results, title), encoding="utf-8")
        console.print(f"[green]✓ Wrote HTML:[/green] {out}")
    elif fmt == OutputFormat.json:
        Path(out).write_text(_render_json(results), encoding="utf-8")
        console.print(f"[green]✓ Wrote JSON:[/green] {out}")
    else:
        _render_console(results, title)


@app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="Search query (command name or help text)"),
    timeout: float = typer.Option(2.0, "--timeout", help="Per-command timeout"),
    names_only: bool = typer.Option(False, "--names-only", help="Only match command names"),
    max_workers: int = typer.Option(4, "--max-workers", help="Max parallel workers"),
):
    """Enhanced search across PATH command help text."""
    processor = CommandProcessor(max_workers=max_workers)
    exes = processor._path_executables()
    names = sorted(exes.keys())
    hits: List[str] = []

    if names_only:
        hits = [n for n in names if query.lower() in n.lower()]
    else:
        console.print(f"[dim]Searching through {len(names)} commands...[/dim]")
        results = processor.process_batch({n: exes[n] for n in names}, timeout)
        hits = [
            r.name
            for r in results
            if query.lower() in r.output.lower() or query.lower() in r.name.lower()
        ]

    if hits:
        console.print(f"[green]Found {len(hits)} matches:[/green]")
        for h in hits[:50]:
            console.print(f"[cyan]{h}[/cyan] — {exes[h]}")
        if len(hits) > 50:
            console.print(f"[dim]... and {len(hits) - 50} more[/dim]")
    else:
        console.print("[yellow]No matches found.[/yellow]")


@app.command("stats")
def stats_cmd():
    """Enhanced statistics about available PATH commands."""
    processor = CommandProcessor()
    exes = processor._path_executables()

    table = Table(title="GOD CLI Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Total Commands", str(len(exes)))

    # Risk assessment
    risks = {}
    for name, path in exes.items():
        risk = SecurityAudit.assess_risk(name, str(path))
        risks[risk] = risks.get(risk, 0) + 1

    for risk_level in RiskLevel:
        count = risks.get(risk_level, 0)
        color = {
            RiskLevel.LOW: "green",
            RiskLevel.MEDIUM: "yellow",
            RiskLevel.HIGH: "red",
            RiskLevel.CRITICAL: "bold red",
        }[risk_level]
        table.add_row(f" {risk_level.value.title()} Risk", f"[{color}]{count}[/{color}]")

    console.print(table)


@app.command("info")
def info_cmd(
    command: str = typer.Argument(..., help="Command name to get info about"),
    timeout: float = typer.Option(3.0, "--timeout", help="Command timeout"),
):
    """Enhanced detailed information about a specific command."""
    processor = CommandProcessor()
    exes = processor._path_executables()
    p = exes.get(command)

    if not p:
        console.print(f"[red]❌ Command not found on PATH:[/red] {command}")
        raise typer.Exit(1)

    result = processor.process_single(command, p, timeout)

    risk_color = {
        RiskLevel.LOW: "green",
        RiskLevel.MEDIUM: "yellow",
        RiskLevel.HIGH: "red",
        RiskLevel.CRITICAL: "bold red",
    }[result.risk_level]

    panel = Panel.fit(
        f"[bold cyan]{result.name}[/bold cyan]\n"
        f"[white]Path:[/white] {result.path}\n"
        f"[white]Category:[/white] {result.category}\n"
        f"[white]Risk Level:[/white] [{risk_color}]{result.risk_level.value.upper()}[/{risk_color}]\n"
        f"[white]Version:[/white] {result.version or 'N/A'}\n"
        f"[white]Execution Time:[/white] {result.execution_time:.2f}s\n"
        f"[white]Success:[/white] {'✅' if result.success else '❌'}\n"
        f"[white]Help Flag:[/white] {result.help_flag or 'N/A'}",
        title="Command Information",
        border_style="cyan",
    )
    console.print(panel)

    if result.output and not result.output.startswith("[No help"):
        console.print("\n[bold]Help Output:[/bold]")
        console.print(Panel(result.output, border_style="blue"))


def version_callback(value: bool):
    """Handle version flag."""
    if value:
        try:
            import importlib.metadata as _md

            v = _md.version("god-cli")
        except Exception:
            try:
                from god import version as v
            except Exception:
                v = "1.0.0"
        console.print(f"🚀 [bold cyan]GOD v{v}[/bold cyan] - Professional Grade")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", help="Show version and exit", callback=version_callback
    ),
    ctx: typer.Context = typer.Context,
):
    """GOD CLI - Global Operations Deity."""
    if ctx.invoked_subcommand is None:
        if version:
            # Version is handled by the callback
            return
        else:
            # Show help if no command provided
            console.print("[yellow]No command provided. Use --help to see available commands.[/yellow]")
            raise typer.Exit(1)


@app.command("completion")
def completion_cmd(shell: str = typer.Argument("bash", help="bash|zsh|fish|powershell")):
    """Generate shell completion script."""
    try:
        from click.shell_completion import get_completion_script

        prog_name = "god"
        echo = get_completion_script(prog_name, shell)
        console.print(echo)
    except Exception as e:
        console.print(f"[yellow]Completion not available ({e}).[/yellow]")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def _ensure_utf8_stdio() -> None:
    """Enhanced UTF-8 support for Windows."""
    try:
        if os.name == "nt":
            import io

            if sys.stdout and not sys.stdout.encoding.lower().startswith("utf"):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            if sys.stderr and not sys.stderr.encoding.lower().startswith("utf"):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception as e:
        logger.debug(f"UTF-8 setup failed: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main_cli():
    """Enhanced main entry point with professional error handling."""
    _ensure_utf8_stdio()

    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation cancelled by user[/yellow]")
        sys.exit(130)
    except typer.Exit as e:
        sys.exit(e.exit_code)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        console.print("[dim]Check logs for details[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main_cli()

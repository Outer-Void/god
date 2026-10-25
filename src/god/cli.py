"""`god` command line (docs/USAGE.md)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from god import __version__, blux_adapter, commands, index, query
from god.errors import EXIT_CHECK_FAILED, EXIT_FAILURE, EXIT_OK, EXIT_USAGE, ErrorCode, GodError

REMOVED = {
    "build": "it ran every program on PATH with help/version flags",
    "search": "it ran every program on PATH to search their help text",
    "info": "it ran the program to scrape its help",
    "stats": "its 'risk levels' were a hard-coded name list",
    "blux": "routing to other tools is BLUX's job (`blux run ...`); GOD only discovers",
    "completion": "it depended on typer",
}


def _roots_default() -> list[str]:
    env = os.environ.get("GOD_ROOTS")
    return [r for r in env.split(os.pathsep) if r] if env else ["."]


def _index_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-r", "--root", action="append", dest="roots", metavar="DIR", help="directory to search (repeatable)"
    )
    p.add_argument("--index", type=Path, help="index cache file (default: $GOD_INDEX or ~/.cache/god/index.json)")
    p.add_argument("--no-cache", action="store_true", help="scan without reading or writing the index cache")
    p.add_argument("--json", action="store_true", help="print the JSON document")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="god",
        description="Discover BLUX projects, capabilities and commands. GOD never runs what it finds.",
        epilog="Exit codes: 0 ok, 1 check failed or nothing matched, 2 usage, 3 failed. "
        "Roots default to $GOD_ROOTS (path-separated) or the current directory.",
    )
    parser.add_argument("--version", action="version", version=f"god {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("index", help="index the roots (registry.index)")
    p.add_argument("roots_pos", nargs="*", metavar="ROOT")
    p.add_argument("--refresh", action="store_true", help="ignore the cache and re-read every project")
    _index_args(p)

    p = sub.add_parser("capabilities", aliases=["caps"], help="list capabilities (capability.discover)")
    p.add_argument("query", nargs="?", help="capability id, glob (repo.*) or substring")
    p.add_argument("--project", help="only this project id or root")
    p.add_argument("--max-side-effects", choices=query.SIDE_EFFECTS)
    p.add_argument("--kind", dest="provider_kind", help="provider kind (subprocess, python, ...)")
    p.add_argument("--label", action="append", default=[], metavar="KEY=VALUE")
    _index_args(p)

    p = sub.add_parser("capability", help="describe one capability (capability.describe)")
    p.add_argument("capability_id")
    p.add_argument("--project")
    _index_args(p)

    p = sub.add_parser("project", help="describe one project (project.describe)")
    p.add_argument("project", help="project id, or a directory containing .blux/")
    _index_args(p)

    p = sub.add_parser("compat", help="which providers satisfy a version range (capability.compat)")
    p.add_argument("capability_id")
    p.add_argument("--range", dest="version_range", metavar="RANGE", help="e.g. '^2.0.0' or '>=1.4 <3'")
    p.add_argument("--contract", dest="contract_version", metavar="MAJOR.MINOR", help="caller's contract version")
    p.add_argument("--project")
    _index_args(p)

    p = sub.add_parser("commands", help="list commands on PATH, statically (command.discover)")
    p.add_argument("pattern", nargs="?", help="glob on command names")
    p.add_argument("--path", dest="path_value", help="PATH value to inspect (default: $PATH)")
    p.add_argument("--declared", action="store_true", help="also check capability entrypoints from the roots")
    _index_args(p)

    p = sub.add_parser("check", help="report malformed .blux/ and duplicates; exit 1 if any")
    p.add_argument("roots_pos", nargs="*", metavar="ROOT")
    _index_args(p)

    sub.add_parser("version", help="print versions")
    p = sub.add_parser("blux-capability")  # BLUX ADR-0009 entrypoint; not for people
    p.add_argument("capability_id", choices=blux_adapter.CAPABILITIES)
    return parser


def _index(args: argparse.Namespace, *, refresh: bool = False) -> index.Index:
    roots = (getattr(args, "roots_pos", None) or []) + (args.roots or []) or _roots_default()
    cache = None if args.no_cache else (args.index or index.default_index_path())
    return index.build(roots, cache_path=cache, refresh=refresh)


def _print_json(doc: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n")


def _problems(doc: dict[str, Any]) -> None:
    for p in doc.get("problems", []):
        where = f" ({p['file']})" if p.get("file") else ""
        print(f"  problem   {p['root']}{where}: {p['issue']}: {p['message']}")
    for d in doc.get("duplicates", []):
        print(f"  duplicate {d['issue']}: {d['message']}")


def _text(kind: str, doc: dict[str, Any]) -> None:
    if kind == "capabilities":
        for c in doc["capabilities"]:
            amb = "  (ambiguous)" if c["ambiguous"] else ""
            print(
                f"{c['capability_id']:<24} {c['version']:<8} {c['side_effects']:<11} {c['project_id']:<14} "
                f"{c['summary']}{amb}"
            )
        _problems(doc)
    elif kind == "capability":
        c, p = doc["capability"], doc["project"]
        print(f"{c['capability_id']} {c['version']} ({p['project_id']}, {p['root']})")
        print(f"  {c['summary']}")
        print(f"  side effects: {c['side_effects']}; permissions: {', '.join(c['required_permissions']) or 'none'}")
        print(f"  provider: {c['provider'].get('kind')} {c['provider'].get('entrypoint', '')}")
        print(f"  contract versions: {', '.join(c['contract_versions'])}; timeout {c['timeout_ms']} ms")
    elif kind == "project":
        p = doc["project"]
        print(f"{p['project_id']} ({p['role']}): {p['name']}  {p['root']}")
        if p["description"]:
            print(f"  {p['description']}")
        for c in doc["capabilities"]:
            print(f"  {c['capability_id']:<22} {c['version']:<8} {c['side_effects']}")
        pol = doc["policy"]
        print(f"  policy {pol['policy_id']}: default {pol['default_effect']}, {len(pol['rules'])} rule(s)")
    elif kind == "compatibility":
        print(f"{doc['verdict'].upper()}: {doc['request']['capability_id']}")
        for m in doc["matches"]:
            print(f"  match     {m['project_id']} {m['version']} (contract {m['contract_version']})")
        for r in doc["rejected"]:
            print(f"  rejected  {r['project_id']} {r['version']}: " + "; ".join(x["message"] for x in r["reasons"]))
    elif kind == "commands":
        for c in doc["commands"]:
            extra = f"  (shadows {len(c['shadows'])})" if c["shadows"] else ""
            print(f"{c['name']:<28} {c['path']}{extra}")
        for d in doc["declared"]:
            print(f"  entrypoint {d['capability_id']:<22} {d.get('executable', '?'):<14} {d['status']}")
        for w in doc["warnings"]:
            print(f"  warning   {w['message']}")
    elif kind in ("index-summary", "check"):
        s = doc["index"]
        c = s["cache"]
        cache = (
            "no cache"
            if c.get("reason") == "disabled"
            else f"cache: {c['hits']} hit(s), {c['reloaded']} reloaded, {c['removed']} removed"
        )
        verdict = f"{doc['verdict'].upper()}: " if "verdict" in doc else ""
        print(
            f"{verdict}{s['projects']} project(s), {s['problems']} problem(s) under {', '.join(s['roots'])} ({cache})"
        )
        _problems(doc)


def _run(args: argparse.Namespace) -> int:
    cmd = "capabilities" if args.command == "caps" else args.command
    if cmd == "version":
        from god.projects import sdk_info

        try:
            sdk = sdk_info()
            print(f"god {__version__} (blux-sdk {sdk['version']}, contract {', '.join(sdk['contract_versions'])})")
        except GodError:
            print(f"god {__version__} (blux-sdk not installed)")
        return EXIT_OK
    if cmd == "project" and os.path.isdir(os.path.join(os.path.expanduser(args.project), ".blux")) and not args.roots:
        doc = query.describe_project_dir(Path(args.project))
        kind = "project"
    elif cmd == "commands":
        idx = _index(args) if args.declared else None
        doc, kind = commands.discover(pattern=args.pattern, path_value=args.path_value, index=idx), "commands"
    else:
        idx = _index(args, refresh=getattr(args, "refresh", False))
        if cmd == "index":
            doc = {**query.header("index-summary", idx), "problems": idx.problems, "duplicates": query.duplicates(idx)}
            kind = "index-summary"
        elif cmd == "check":
            doc, kind = query.check(idx), "check"
        elif cmd == "capabilities":
            labels = {}
            for pair in args.label:
                k, eq, v = pair.partition("=")
                if not eq:
                    raise GodError(ErrorCode.INVALID_INPUT, f"--label needs KEY=VALUE, got {pair!r}.")
                labels[k] = v
            doc = query.discover(
                idx,
                query=args.query,
                project=args.project,
                max_side_effects=args.max_side_effects,
                provider_kind=args.provider_kind,
                labels=labels,
            )
            kind = "capabilities"
        elif cmd == "capability":
            doc, kind = query.describe_capability(idx, args.capability_id, project=args.project), "capability"
        elif cmd == "project":
            doc, kind = query.describe_project(idx, args.project), "project"
        else:
            doc = query.compat(
                idx,
                args.capability_id,
                version_range=args.version_range,
                contract_version=args.contract_version,
                project=args.project,
            )
            kind = "compatibility"
    if args.json:
        _print_json(doc)
    else:
        _text(kind, doc)
    failed = (kind == "check" and doc["verdict"] == "fail") or (
        kind == "compatibility" and doc["verdict"] != "compatible"
    )
    return EXIT_CHECK_FAILED if failed else EXIT_OK


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in REMOVED:
        print(f"god: `god {argv[0]}` was removed in 2.0: {REMOVED[argv[0]]}. See `god --help`.", file=sys.stderr)
        return EXIT_USAGE
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_USAGE
    if args.command is None:
        parser.print_help()
        return EXIT_USAGE
    if args.command == "blux-capability":
        return blux_adapter.main(args.capability_id)
    try:
        return _run(args)
    except GodError as exc:
        if getattr(args, "json", False):
            _print_json({"error": exc.to_dict()})
        else:
            print(f"god: {exc.code.value}: {exc.message}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        return EXIT_FAILURE

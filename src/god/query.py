"""Discovery queries over an index: capability.discover, capability.describe, project.describe,
capability.compat. Read-only views; nothing here runs a capability or evaluates a policy."""

from __future__ import annotations

import fnmatch
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from god import __version__, projects
from god.errors import ErrorCode, GodError
from god.index import Index
from god.semver import Range, RangeError, Version

SIDE_EFFECTS = ("none", "read", "write", "external", "destructive")


def header(kind: str, index: Index | None) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "contract": f"god.{kind}",
        "version": 1,
        "tool": {"name": "god", "version": __version__},
        "sdk": projects.sdk_info(),
    }
    if index is not None:
        doc["index"] = index.summary()
    doc["linkage"] = None
    return doc


def duplicates(index: Index) -> list[dict[str, Any]]:
    """Two checkouts of one project_id, and one capability_id provided by different projects. BLUX refuses to
    register a capability id twice, so either makes the set of roots ambiguous."""
    issues: list[dict[str, Any]] = []
    by_project: dict[str, list[str]] = defaultdict(list)
    for p in index.projects:
        by_project[p["project_id"]].append(p["root"])
    for pid, roots in sorted(by_project.items()):
        if len(roots) > 1:
            issues.append(
                {
                    "issue": "duplicate-project",
                    "project_id": pid,
                    "roots": sorted(roots),
                    "message": f"project_id {pid!r} is declared by {len(roots)} directories.",
                }
            )
    by_cap: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in index.projects:
        for c in p["capabilities"]:
            by_cap[c["capability_id"]].append(
                {"project_id": p["project_id"], "root": p["root"], "version": c["version"]}
            )
    for cid, providers in sorted(by_cap.items()):
        if len({x["project_id"] for x in providers}) > 1:
            issues.append(
                {
                    "issue": "duplicate-capability",
                    "capability_id": cid,
                    "providers": sorted(providers, key=lambda x: (x["project_id"], x["root"])),
                    "message": f"{cid} is provided by {len({x['project_id'] for x in providers})} different projects.",
                }
            )
    return issues


def _summary(project: dict[str, Any], cap: dict[str, Any]) -> dict[str, Any]:
    provider = cap["provider"]
    return {
        "capability_id": cap["capability_id"],
        "version": cap["version"],
        "summary": cap["summary"],
        "side_effects": cap["side_effects"],
        "required_permissions": cap["required_permissions"],
        "contract_versions": cap["contract_versions"],
        "provider": {k: provider[k] for k in sorted(provider)},
        "labels": cap.get("labels", {}),
        "project_id": project["project_id"],
        "project_root": project["root"],
    }


def discover(
    index: Index,
    *,
    query: str | None = None,
    project: str | None = None,
    max_side_effects: str | None = None,
    provider_kind: str | None = None,
    labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    if max_side_effects is not None and max_side_effects not in SIDE_EFFECTS:
        raise GodError(ErrorCode.INVALID_INPUT, f"max_side_effects must be one of {', '.join(SIDE_EFFECTS)}.")
    out = []
    for p in index.projects:
        if project is not None and project not in (p["project_id"], p["root"]):
            continue
        for c in p["capabilities"]:
            if query and not fnmatch.fnmatchcase(c["capability_id"], query) and query not in c["capability_id"]:
                continue
            if max_side_effects and SIDE_EFFECTS.index(c["side_effects"]) > SIDE_EFFECTS.index(max_side_effects):
                continue
            if provider_kind and c["provider"].get("kind") != provider_kind:
                continue
            if labels and any(c.get("labels", {}).get(k) != v for k, v in labels.items()):
                continue
            out.append(_summary(p, c))
    out.sort(key=lambda s: (s["capability_id"], s["project_id"], s["project_root"]))
    counts: dict[str, int] = defaultdict(int)
    for s in out:
        counts[s["capability_id"]] += 1
    for s in out:
        s["ambiguous"] = counts[s["capability_id"]] > 1
    return {
        **header("capabilities", index),
        "query": {
            "query": query,
            "project": project,
            "max_side_effects": max_side_effects,
            "provider_kind": provider_kind,
            "labels": labels or {},
        },
        "capabilities": out,
        "duplicates": duplicates(index),
        "problems": index.problems,
    }


def _providers(index: Index, capability_id: str, project: str | None) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    hits: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for p in index.projects:
        if project is not None and project not in (p["project_id"], p["root"]):
            continue
        hits.extend((p, c) for c in p["capabilities"] if c["capability_id"] == capability_id)
    return hits


def describe_capability(index: Index, capability_id: str, *, project: str | None = None) -> dict[str, Any]:
    hits = _providers(index, capability_id, project)
    if not hits:
        raise GodError(
            ErrorCode.NOT_FOUND,
            f"No project under the roots provides {capability_id}.",
            details={"capability_id": capability_id, "roots": [str(r) for r in index.roots]},
        )
    if len(hits) > 1:
        raise GodError(
            ErrorCode.AMBIGUOUS,
            f"{capability_id} is provided by {len(hits)} projects; pass a project id or root.",
            details={"providers": [{"project_id": p["project_id"], "root": p["root"]} for p, _ in hits]},
        )
    p, c = hits[0]
    return {
        **header("capability", index),
        "capability": c,
        "project": _project_summary(p),
    }


def _project_summary(p: dict[str, Any]) -> dict[str, Any]:
    return {k: p[k] for k in ("project_id", "name", "description", "role", "repository", "root", "fingerprint")}


def _find_project(index: Index, ref: str) -> dict[str, Any]:
    as_path = os.path.abspath(os.path.expanduser(ref))
    hits = [p for p in index.projects if ref == p["project_id"] or as_path == p["root"]]
    if not hits:
        problem = [r for r in index.problems if r["root"] == as_path]
        details: dict[str, Any] = {"project": ref}
        if problem:
            details["problem"] = problem[0]
        raise GodError(ErrorCode.NOT_FOUND, f"No valid project {ref!r} under the roots.", details=details)
    if len(hits) > 1:
        raise GodError(
            ErrorCode.AMBIGUOUS,
            f"project_id {ref!r} is declared by {len(hits)} directories; pass a path.",
            details={"roots": [p["root"] for p in hits]},
        )
    return hits[0]


def describe_project(index: Index, ref: str) -> dict[str, Any]:
    p = _find_project(index, ref)
    policy = p["policy"]
    return {
        **header("project", index),
        "project": {
            **_project_summary(p),
            "labels": p["labels"],
            "contract_version": p["contract_version"],
            "files": p["files"],
        },
        "capabilities": [_summary(p, c) for c in p["capabilities"]],
        # Declared policy, reported as written. GOD never evaluates it: authorization is the BLUX runtime's job.
        "policy": {
            "policy_id": policy["policy_id"],
            "default_effect": policy["default_effect"],
            "rules": policy["rules"],
        },
    }


def describe_project_dir(path: Path) -> dict[str, Any]:
    """project.describe for one directory, without indexing anything else (malformed: a problem record)."""
    record = projects.load(path)
    if record["kind"] == "problem":
        raise GodError(
            ErrorCode.NOT_FOUND, f"{path} has no valid .blux/: {record['message']}", details={"problem": record}
        )
    index = Index([Path(record["root"])], [record], {"rebuilt": True, "reason": "single-project"})
    return describe_project(index, record["root"])


def compat(
    index: Index,
    capability_id: str,
    *,
    version_range: str | None = None,
    contract_version: str | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    from blux_sdk.errors import BluxError
    from blux_sdk.versions import CONTRACT_VERSION, negotiate, parse_version

    client = contract_version or CONTRACT_VERSION
    try:
        parse_version(client)
        wanted = Range.parse(version_range) if version_range else None
    except (RangeError, BluxError) as exc:
        raise GodError(ErrorCode.INVALID_INPUT, str(getattr(exc, "message", exc))) from None
    matches, rejected = [], []
    for p, c in _providers(index, capability_id, project):
        reasons = []
        try:
            v = Version.parse(c["version"])
            if wanted is not None and not wanted.matches(v):
                reasons.append({"reason": "version", "message": f"{c['version']} does not satisfy {wanted.text}."})
        except RangeError as exc:
            reasons.append({"reason": "version-unparseable", "message": str(exc)})
        try:
            agreed: str | None = negotiate(c["contract_versions"], [client])
        except BluxError:
            agreed = None
            reasons.append(
                {
                    "reason": "contract",
                    "message": f"Offers contract versions {c['contract_versions']}, caller speaks {client}.",
                }
            )
        entry = {"project_id": p["project_id"], "project_root": p["root"], "version": c["version"]}
        if reasons:
            rejected.append({**entry, "reasons": reasons})
        else:
            matches.append({**entry, "contract_version": agreed})
    if not matches and not rejected:
        raise GodError(ErrorCode.NOT_FOUND, f"No project under the roots provides {capability_id}.")
    key = lambda e: (e["project_id"], e["project_root"])  # noqa: E731
    return {
        **header("compatibility", index),
        "request": {"capability_id": capability_id, "version_range": version_range, "contract_version": client},
        "verdict": "compatible" if matches else "incompatible",
        "matches": sorted(matches, key=key),
        "rejected": sorted(rejected, key=key),
    }


def check(index: Index) -> dict[str, Any]:
    dups = duplicates(index)
    return {
        **header("check", index),
        "verdict": "fail" if (index.problems or dups) else "pass",
        "problems": index.problems,
        "duplicates": dups,
    }

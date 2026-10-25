"""Malformed manifests and duplicates are findings: every other project is still discovered."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from god import index, query
from god.errors import ErrorCode, GodError
from tests.conftest import capability, project, run


def _broken(root: Path, files: dict[str, str]) -> None:
    project(root, root.name, [capability(f"{root.name}.x")])
    for name, text in files.items():
        if text == "<delete>":
            (root / ".blux" / name).unlink()
        else:
            (root / ".blux" / name).write_text(text)


MANIFEST = json.dumps(
    {
        "contract": "blux.project",
        "contract_version": "1.0",
        "project_id": "p-x",
        "name": "X",
        "role": "standalone",
        "capabilities": "capabilities.yaml",
        "policy": "policy.yaml",
    }
)

CASES = [
    ("malformed-yaml", {"manifest.yaml": "contract: blux.project\nproject_id: [oops\n"}),
    ("malformed", {"manifest.yaml": "- just\n- a list\n"}),
    ("malformed", {"manifest.yaml": "contract: blux.project\nwhen: 2026-10-25\n"}),  # YAML date: not JSON
    ("invalid", {"manifest.yaml": '{"contract": "blux.capability", "contract_version": "1.0"}'}),
    ("unsupported-contract-version", {"manifest.yaml": MANIFEST.replace('"1.0"', '"1.1"', 1)}),
    ("unsupported-contract-version", {"manifest.yaml": MANIFEST.replace('"1.0"', '"one"', 1)}),
    ("schema-invalid", {"manifest.yaml": MANIFEST.replace('"standalone"', '"sidecar"')}),
    ("schema-invalid", {"manifest.yaml": MANIFEST.replace('"capabilities.yaml"', '"../../etc/passwd"')}),
    ("missing-file", {"policy.yaml": "<delete>"}),
    (
        "duplicate-capability",
        {
            "capabilities.yaml": json.dumps(
                {
                    "contract": "blux.capability-set",
                    "contract_version": "1.0",
                    "capabilities": [capability("d.x"), capability("d.x")],
                }
            )
        },
    ),
    ("malformed", {"capabilities.yaml": "\xff\xfe not utf-8"}),
]


@pytest.mark.parametrize(("issue", "files"), CASES, ids=[f"{i}-{n}" for n, (i, _) in enumerate(CASES)])
def test_malformed_project_is_a_problem_not_a_crash(tmp_path: Path, issue: str, files: dict[str, str]) -> None:
    project(tmp_path / "good", "good", [capability("good.x")])
    bad = tmp_path / "bad"
    _broken(bad, files)
    if "\xff" in next(iter(files.values())):
        (bad / ".blux" / next(iter(files))).write_bytes(b"\xff\xfe not utf-8")
    idx = index.build([tmp_path])
    assert [p["project_id"] for p in idx.projects] == ["good"]
    (problem,) = idx.problems
    assert problem["root"] == str(bad) and problem["issue"] == issue, problem
    assert problem["code"] and problem["message"]


def test_oversized_document_is_rejected(tmp_path: Path) -> None:
    _broken(tmp_path / "huge", {"capabilities.yaml": "x: " + "a" * (17 * 1024 * 1024)})
    (problem,) = index.build([tmp_path]).problems
    assert problem["code"] == "MALFORMED_INPUT"


def test_blux_symlink_is_not_followed(tmp_path: Path) -> None:
    real = project(tmp_path / "real", "real-one", [capability("r.x")])
    (tmp_path / "linked").mkdir()
    (tmp_path / "linked" / ".blux").symlink_to(real / ".blux")
    idx = index.build([tmp_path / "linked"])
    assert idx.projects == [] or all(p["root"] != str(tmp_path / "linked") for p in idx.projects)


def test_duplicates(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project(tmp_path / "a", "same", [capability("x.one")])
    project(tmp_path / "b", "same", [capability("x.one")])  # two checkouts of one project
    project(tmp_path / "c", "other", [capability("x.one", version="9.0.0")])  # a different project claims it
    idx = index.build([tmp_path])
    dups = query.duplicates(idx)
    assert [d["issue"] for d in dups] == ["duplicate-project", "duplicate-capability"]
    assert {p["project_id"] for p in dups[1]["providers"]} == {"same", "other"}
    assert all(c["ambiguous"] for c in query.discover(idx)["capabilities"])
    with pytest.raises(GodError) as exc:
        query.describe_capability(idx, "x.one")
    assert exc.value.code is ErrorCode.AMBIGUOUS and len(exc.value.details["providers"]) == 3
    assert query.describe_capability(idx, "x.one", project="other")["capability"]["version"] == "9.0.0"
    with pytest.raises(GodError):
        query.describe_project(idx, "same")
    code, out, _ = run(["check", str(tmp_path)], capsys)
    assert code == 1 and "duplicate-project" in out and "duplicate-capability" in out


def test_check_reports_problems_with_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _broken(tmp_path / "bad", {"manifest.yaml": "a: [\n"})
    code, out, _ = run(["check", str(tmp_path), "--no-cache"], capsys)
    assert code == 1 and "malformed-yaml" in out and "(line" in out

"""Version compatibility: semver ranges and contract-version negotiation."""

from __future__ import annotations

from pathlib import Path

import pytest

from god import index, query
from god.errors import GodError
from god.semver import Range, RangeError, Version
from tests.conftest import capability, project, run


@pytest.mark.parametrize(
    ("spec", "yes", "no"),
    [
        ("1.2.3", ["1.2.3"], ["1.2.4", "1.2.3-rc.1"]),
        ("^1.2.3", ["1.2.3", "1.9.0"], ["2.0.0", "1.2.2", "2.0.0-rc.1"]),
        ("^0.2.3", ["0.2.9"], ["0.3.0"]),
        ("^0.0.3", ["0.0.3"], ["0.0.4"]),
        ("~1.2.3", ["1.2.9"], ["1.3.0"]),
        (">=1.4 <3", ["1.4.0", "2.9.9"], ["1.3.9", "3.0.0"]),
        (">2", ["3.0.0"], ["2.9.9"]),
        ("<=2.1", ["2.1.9"], ["2.2.0"]),
        ("1.*", ["1.0.0", "1.99.0"], ["2.0.0"]),
        ("1.2.*", ["1.2.7"], ["1.3.0"]),
        ("*", ["0.0.1", "99.0.0"], []),
        ("^1 || ^3", ["1.5.0", "3.0.0"], ["2.0.0"]),
        (">=2.0.0-rc.1 <2.0.0", ["2.0.0-rc.2"], ["2.0.0", "2.0.1-rc.1"]),
    ],
)
def test_ranges(spec: str, yes: list[str], no: list[str]) -> None:
    r = Range.parse(spec)
    for v in yes:
        assert r.matches(Version.parse(v)), (spec, v)
    for v in no:
        assert not r.matches(Version.parse(v)), (spec, v)


def test_precedence() -> None:
    order = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
    ]
    assert sorted(order, key=Version.parse) == order  # semver.org section 11


@pytest.mark.parametrize("bad", ["", "abc", "1.2.3.4", ">=", "^x", "|| 1.0.0", "01.2.3"])
def test_bad_ranges(bad: str) -> None:
    with pytest.raises(RangeError):
        Range.parse(bad)


@pytest.fixture
def providers(tmp_path: Path) -> Path:
    project(tmp_path / "old", "old-impl", [capability("svc.run", version="1.4.0")])
    project(tmp_path / "new", "new-impl", [capability("svc.run", version="2.1.0", contract_versions=["1.0", "1.1"])])
    project(tmp_path / "next", "next-impl", [capability("svc.run", version="3.0.0-rc.1", contract_versions=["1.1"])])
    return tmp_path


def test_compat_lookup(providers: Path) -> None:
    idx = index.build([providers])
    doc = query.compat(idx, "svc.run", version_range="^2.0.0")
    assert doc["verdict"] == "compatible" and [m["project_id"] for m in doc["matches"]] == ["new-impl"]
    assert doc["matches"][0]["contract_version"] == "1.0"
    reasons = {r["project_id"]: [x["reason"] for x in r["reasons"]] for r in doc["rejected"]}
    assert reasons == {"old-impl": ["version"], "next-impl": ["version", "contract"]}
    two = query.compat(idx, "svc.run", contract_version="1.1")
    assert [m["project_id"] for m in two["matches"]] == ["new-impl", "next-impl"]
    assert {m["contract_version"] for m in two["matches"]} == {"1.1"}
    none = query.compat(idx, "svc.run", version_range=">=4")
    assert none["verdict"] == "incompatible" and len(none["rejected"]) == 3
    with pytest.raises(GodError):
        query.compat(idx, "svc.run", contract_version="two")
    with pytest.raises(GodError):
        query.compat(idx, "svc.missing")


def test_compat_cli_exit_codes(providers: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(["compat", "svc.run", "--range", "^1", "-r", str(providers)], capsys)[0] == 0
    assert run(["compat", "svc.run", "--range", "^9", "-r", str(providers)], capsys)[0] == 1
    assert run(["compat", "svc.run", "--range", "nope", "-r", str(providers)], capsys)[0] == 3


def test_compat_against_the_running_sdk(providers: Path) -> None:
    from blux_sdk.versions import CONTRACT_VERSION

    doc = query.compat(index.build([providers]), "svc.run")
    assert doc["request"]["contract_version"] == CONTRACT_VERSION

"""Semantic versions (semver.org 2.0.0) and ranges, for version compatibility lookup.

Range grammar: comparator sets separated by `||`; a set is space-separated comparators that must all hold.
Comparators: `1.2.3` / `=1.2.3` / `==1.2.3`, `>=`, `>`, `<=`, `<`, `^1.2.3`, `~1.2.3`, `1.2.*`, `1.*`, `*`.
`^` allows changes that do not modify the left-most non-zero component; `~` allows patch changes.
Prereleases only match comparators that name a prerelease of the same MAJOR.MINOR.PATCH (as in npm).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
COMPARATOR = re.compile(r"^(>=|<=|==|=|>|<|\^|~)?(.+)$")
PARTIAL = re.compile(r"^(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?$")
WILDCARD = re.compile(r"^(0|[1-9]\d*)(?:\.(0|[1-9]\d*|\*))?(?:\.\*)?$|^\*$")


class RangeError(ValueError):
    pass


@total_ordering
@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    pre: tuple[int | str, ...] = ()

    @classmethod
    def parse(cls, text: str) -> Version:
        m = SEMVER.match(text.strip())
        if not m:
            raise RangeError(f"{text!r} is not a semantic version (MAJOR.MINOR.PATCH).")
        pre = tuple(int(p) if p.isdigit() else p for p in m.group(4).split(".")) if m.group(4) else ()
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)), pre)

    @property
    def core(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        if self.core != other.core:
            return self.core < other.core
        if not self.pre or not other.pre:
            return bool(self.pre) and not other.pre  # a prerelease sorts before its release
        for a, b in zip(self.pre, other.pre, strict=False):
            if a == b:
                continue
            if isinstance(a, int) and isinstance(b, int):
                return a < b
            if isinstance(a, int) != isinstance(b, int):
                return isinstance(a, int)  # numeric identifiers sort before alphanumeric ones
            return str(a) < str(b)
        return len(self.pre) < len(other.pre)

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return base + ("-" + ".".join(str(p) for p in self.pre) if self.pre else "")


@dataclass(frozen=True)
class _Bound:
    op: str
    version: Version

    def holds(self, v: Version) -> bool:
        return {
            ">=": v >= self.version,
            ">": v > self.version,
            "<=": v <= self.version,
            "<": v < self.version,
            "=": v == self.version,
        }[self.op]


def _partial(op: str, major: int, minor: int | None) -> list[_Bound]:
    """`>=3`, `<2.1`, `^1`, `~1.4` ...: a partial version stands for every version it is a prefix of."""
    low = Version(major, minor or 0, 0)
    high = Version(major + 1, 0, 0) if minor is None else Version(major, minor + 1, 0)
    if op == ">=":
        return [_Bound(">=", low)]
    if op == ">":
        return [_Bound(">=", high)]
    if op == "<":
        return [_Bound("<", low)]
    if op == "<=":
        return [_Bound("<", high)]
    if op == "^" and major == 0 and minor is not None:
        return [_Bound(">=", low), _Bound("<", high)]
    if op == "^":
        return [_Bound(">=", low), _Bound("<", Version(major + 1, 0, 0))]
    return [_Bound(">=", low), _Bound("<", high)]  # ~ and =


def _expand(token: str) -> list[_Bound]:
    m = COMPARATOR.match(token)
    if not m:
        raise RangeError(f"Bad comparator {token!r}.")
    op, rest = m.group(1) or "", m.group(2)
    wild = WILDCARD.match(rest)
    if wild and op == "" and ("*" in rest or rest.count(".") < 2):
        if rest == "*":
            return []
        major = int(wild.group(1))
        minor = wild.group(2)
        if minor is None or minor == "*":
            return [_Bound(">=", Version(major, 0, 0)), _Bound("<", Version(major + 1, 0, 0))]
        return [_Bound(">=", Version(major, int(minor), 0)), _Bound("<", Version(major, int(minor) + 1, 0))]
    partial = PARTIAL.match(rest)
    if partial and op in (">=", ">", "<=", "<", "^", "~", "="):
        return _partial(op, int(partial.group(1)), None if partial.group(2) is None else int(partial.group(2)))
    v = Version.parse(rest)
    if op in ("", "=", "=="):
        return [_Bound("=", v)]
    if op == "^":
        if v.major > 0:
            upper = Version(v.major + 1, 0, 0)
        elif v.minor > 0:
            upper = Version(0, v.minor + 1, 0)
        else:
            upper = Version(0, 0, v.patch + 1)
        return [_Bound(">=", v), _Bound("<", upper)]
    if op == "~":
        return [_Bound(">=", v), _Bound("<", Version(v.major, v.minor + 1, 0))]
    return [_Bound(op, v)]


@dataclass(frozen=True)
class Range:
    text: str
    sets: tuple[tuple[_Bound, ...], ...]

    @classmethod
    def parse(cls, text: str) -> Range:
        if not text.strip() or len(text) > 256:
            raise RangeError("Empty or overlong version range.")
        sets = []
        for part in text.split("||"):
            tokens = part.split()
            if not tokens:
                raise RangeError(f"Empty alternative in range {text!r}.")
            bounds: list[_Bound] = []
            for t in tokens:
                bounds.extend(_expand(t))
            sets.append(tuple(bounds))
        return cls(text.strip(), tuple(sets))

    def matches(self, v: Version) -> bool:
        for bounds in self.sets:
            if not all(b.holds(v) for b in bounds):
                continue
            if v.pre and not any(b.version.pre and b.version.core == v.core for b in bounds):
                continue
            return True
        return False

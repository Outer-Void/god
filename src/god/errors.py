"""Failures and exit codes (docs/USAGE.md#exit-codes).

A malformed manifest or a duplicate capability is something GOD *found*: it is reported in `problems`, never
raised. An error means GOD could not look (bad input, unreadable index, missing SDK).
"""

from __future__ import annotations

import enum
from typing import Any

EXIT_OK = 0
EXIT_CHECK_FAILED = 1  # `god check` found problems, or a lookup matched nothing
EXIT_USAGE = 2
EXIT_FAILURE = 3


class ErrorCode(enum.StrEnum):
    INVALID_INPUT = "INVALID_INPUT"
    ROOT_NOT_FOUND = "ROOT_NOT_FOUND"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    INDEX_INVALID = "INDEX_INVALID"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    SDK_UNAVAILABLE = "SDK_UNAVAILABLE"
    IO_ERROR = "IO_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class GodError(Exception):
    def __init__(self, code: ErrorCode, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details: dict[str, Any] = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code.value, "message": self.message, "details": self.details}

    @property
    def exit_code(self) -> int:
        return EXIT_CHECK_FAILED if self.code in (ErrorCode.NOT_FOUND, ErrorCode.AMBIGUOUS) else EXIT_FAILURE

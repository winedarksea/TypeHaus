"""Shared Finding model — the one structured failure surface (→ 12 §Checks framework).

Used by the dialect linter, the resolver, and every checks tier so that build errors,
`haus check`, and pytest all speak the same language and point at source.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class Severity(Enum):
    ERROR = "error"
    WARN = "warn"


class Result(Enum):
    """Tri-state rule result (#32): a rule that cannot evaluate is UNKNOWN, never a pass."""

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class SourceLoc(BaseModel):
    model_config = ConfigDict(frozen=True)

    file: str
    line: int
    column: int = 0

    def __str__(self) -> str:
        return f"{self.file}:{self.line}"


class Finding(BaseModel):
    """A single structured finding that points at source (→ 12)."""

    model_config = ConfigDict(frozen=True)

    severity: Severity
    check_id: str
    message: str
    element_tags: tuple[str, ...] = ()
    code_ref: str | None = None
    source_loc: SourceLoc | None = None
    fix_hint: str | None = None
    result: Result = Result.FAIL

    def render(self) -> str:
        loc = f" ({self.source_loc})" if self.source_loc else ""
        tags = f" [{', '.join(self.element_tags)}]" if self.element_tags else ""
        sev = self.severity.value.upper()
        hint = f"\n    hint: {self.fix_hint}" if self.fix_hint else ""
        return f"{sev} {self.check_id}: {self.message}{tags}{loc}{hint}"


def element_error(check_id: str, message: str, tag: str) -> Finding:
    """The resolver's single-element hard failure: ERROR severity, FAIL result.

    Lives here rather than in one resolver module so sibling modules (envelope, stairs)
    share it without importing each other.
    """
    return Finding(severity=Severity.ERROR, check_id=check_id, message=message,
                   element_tags=(tag,), result=Result.FAIL)

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
    """Rule verdict (#32): a rule that cannot evaluate is UNKNOWN, never a pass.

    ``NOT_APPLICABLE`` is the fourth *verdict* — "the condition this rule governs does not
    exist in this building" — and is deliberately not an UNKNOWN. #32's contract is intact:
    a rule that could not evaluate still reports UNKNOWN and is still never counted as a
    pass; N/A is a different sentence, and one that must be **earned**. A check may only
    return it where the model positively establishes absence ("no masonry guard anywhere in
    the plan"). "No dryer is modeled" in a house that has a laundry is a real gap — UNKNOWN.
    """

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class Authority(Enum):
    """*Where the verdict's authority comes from* — orthogonal to the verdict itself.

    "An engineer owns this" is not a fourth answer alongside pass/fail/can't-tell: once a
    retaining wall is computed the verdict is PASS or FAIL like any other, and what differs
    is that the governing authority is ACI 318 via this engine's own calculation rather than
    IRC Table R404.1.2(8). Folding it into :class:`Result` would leave nowhere to say "the
    column check on PT-SG-FCOL came out at 1.34 — this post is undersized", so it rides
    beside the result, mirroring the severity-vs-result split argued for below.
    """

    PRESCRIPTIVE = "prescriptive"
    ENGINEERED = "engineered"


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
    authority: Authority = Authority.PRESCRIPTIVE
    #: When ``authority`` is ENGINEERED, the engineering-register item id this verdict came
    #: from — ``"<kind>/<element-tag>"``, e.g. ``"retaining_wall/W-SG-E2"``. It is what a
    #: seal in ``engineering.toml`` has to cover, and it is deliberately *not* ``code_ref``:
    #: an engineered finding still cites the standard it was computed against (ACI 318-19
    #: §13.3), and one field cannot hold both without one of them lying.
    engineering_item: str | None = None

    def render(self) -> str:
        """One line, leading with the *result* — the thing a reader is scanning for.

        Severity is a routing decision (does this stop the build?), not the verdict, and
        leading with it rendered all 716 of catlin's passing checks as ``WARN``. The
        severity is appended only when it is ERROR, which is the only case that changes
        what the reader has to do about the finding.
        """
        loc = f" ({self.source_loc})" if self.source_loc else ""
        tags = f" [{', '.join(self.element_tags)}]" if self.element_tags else ""
        sev = " (error)" if self.severity is Severity.ERROR else ""
        auth = " [engineered]" if self.authority is Authority.ENGINEERED else ""
        hint = f"\n    hint: {self.fix_hint}" if self.fix_hint else ""
        return (f"{self.result.value.upper()}{sev} {self.check_id}{auth}: "
                f"{self.message}{tags}{loc}{hint}")


def element_error(check_id: str, message: str, tag: str) -> Finding:
    """The resolver's single-element hard failure: ERROR severity, FAIL result.

    Lives here rather than in one resolver module so sibling modules (envelope, stairs)
    share it without importing each other.
    """
    return Finding(severity=Severity.ERROR, check_id=check_id, message=message,
                   element_tags=(tag,), result=Result.FAIL)


# The general-purpose four below are ``checks/_authoring.py``'s actual implementation —
# re-exported from there for every checks-tier module. They live in this module, rather
# than in ``checks/``, for the same reason ``element_error`` does: ``typehaus.checks``'s
# package __init__ eagerly imports the whole checks tree (registering every check), which
# reaches back into ``typehaus.resolve`` (e.g. ``checks.mep.hvac`` -> ``resolve.mep`` ->
# ``resolve.placeables``). A resolver or source-loader module that needs one of these and
# imported it from ``typehaus.checks`` would import the checks package mid-init and cycle;
# importing from here, a leaf module with no checks/resolve dependency of its own, does not.


def passed(cid: str, msg: str, tags: tuple[str, ...] = (), code: str | None = None) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   code_ref=code, result=Result.PASS)


def failed(cid: str, msg: str, tags: tuple[str, ...] = (), code: str | None = None,
           fix: str | None = None) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=cid, message=msg, element_tags=tags,
                   code_ref=code, fix_hint=fix, result=Result.FAIL)


def unknown(cid: str, reason: str, tags: tuple[str, ...] = (), code: str | None = None,
            fix: str | None = None) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=f"UNKNOWN — {reason}",
                   element_tags=tags, code_ref=code, fix_hint=fix, result=Result.UNKNOWN)


def not_applicable(cid: str, reason: str, tags: tuple[str, ...] = (),
                   code: str | None = None) -> Finding:
    """The governed condition is absent from this building — a verdict, not a gap.

    Earned, never assumed: see :class:`Result`. There is no ``fix`` parameter on purpose —
    if there is something to fix, the finding is not N/A.
    """
    return Finding(severity=Severity.WARN, check_id=cid, message=f"N/A — {reason}",
                   element_tags=tags, code_ref=code, result=Result.NOT_APPLICABLE)


def advisory(cid: str, msg: str, tags: tuple[str, ...], result: Result, code: str | None = None,
             fix: str | None = None, severity: Severity = Severity.WARN,
             authority: Authority = Authority.PRESCRIPTIVE) -> Finding:
    return Finding(severity=severity, check_id=cid, message=msg, element_tags=tags,
                   code_ref=code, fix_hint=fix, result=result, authority=authority)

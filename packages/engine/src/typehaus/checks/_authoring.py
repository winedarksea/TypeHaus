"""Shared Finding constructors for the checks tiers (→ 12 §Checks framework).

Every check module used to hand-roll its own ``_pass``/``_fail``/``_unknown``/``_advisory``
trio — the same four ``Finding(...)`` shapes, reconstructed independently in dozens of
modules under ``checks/``, ``resolve/``, and ``source/``. That duplication is what this
module retires: one place builds a Finding, everything else calls it.

Four shapes cover every call site found in the tree:

* ``passed``   — WARN severity, PASS result. A check succeeded; WARN is the general
  severity for check output, reserved severity ERROR is for hard blockers only.
* ``failed``   — ERROR severity, FAIL result. A hard blocker — `permit.py`'s integrity
  gate treats any ERROR-severity finding as blocking, regardless of check_id.
* ``unknown``  — WARN severity, UNKNOWN result, message auto-prefixed "UNKNOWN — ". The
  tri-state contract (#32): a rule that cannot evaluate reports UNKNOWN, never a pass.
* ``not_applicable`` — WARN severity, NOT_APPLICABLE result, message auto-prefixed
  "N/A — ". A *verdict*, not a gap: the condition this rule governs does not exist in this
  building. It must be earned from positive evidence of absence — see :class:`Result`.
* ``advisory`` — the general form, for the handful of call sites that need a result/severity
  combination the three named helpers don't cover (most commonly WARN severity paired with
  a FAIL result: an advisory finding that should show up as a failure without tripping the
  permit gate, which keys off ERROR severity alone).

The actual implementation lives in :mod:`typehaus.findings` (see the comment there) — this
module exists so every checks-tier module can import these from a stable, checks-flavored
path without needing to know that. ``resolve/`` and ``source/`` modules that need the same
four import straight from :mod:`typehaus.findings`, because importing this module (a
submodule of ``typehaus.checks``, whose package ``__init__`` eagerly imports the entire
checks tree) from a module the checks tree itself imports would be a circular import — this
package is the leaf side of the checks -> resolve dependency, never the other way.
"""

from __future__ import annotations

from typehaus.engineering.item import Status
from typehaus.engineering.registry import records_of
from typehaus.findings import (
    Authority,
    Finding,
    Result,
    Severity,
    advisory,
    failed,
    not_applicable,
    passed,
    unknown,
)


def structural_advisory(cid: str, msg: str, tags: tuple[str, ...], result: Result,
                        fix_hint: str | None = None) -> Finding:
    """A structural finding prefixed to say out loud that a prescriptive table lookup is not
    an engineered design. Five ``checks/structural/`` modules each defined this identically —
    the one thing distinguishing it from plain ``advisory`` is the message prefix, not a
    different Finding shape."""
    return advisory(cid, f"[advisory, not engineering] {msg}", tags, result, fix=fix_hint)


def engineered(ctx, cid: str, item: str, msg: str, tags: tuple[str, ...],
               code: str | None = None, fix: str | None = None,
               authored: str | None = None, *, defer: bool = False) -> Finding:
    """Delegate one requirement to the engineering suite, and report what came back.

    This is the generalisation of the ``engineering_spec`` short-circuit — from free text a
    reader has to take on faith to a computed result they can argue with. That mechanism is
    thinner than it looks: ``engineering_spec`` is consulted in exactly one place in the
    whole repo (``checks/structural/foundation.py``), while ``structural.frost_depth``
    hard-codes ``Result.UNKNOWN`` for a wall its own message calls "outside the prescriptive
    path (IRC R404.4) ... belongs to that engineered design" — the textbook case for
    delegation, unable to use it.

    Five states, and the last two are the migration guarantee:

    ==================================  =========  ========  ==================================
    ``ctx.engineering[item]``           result     severity  what the reader is told
    ==================================  =========  ========  ==================================
    computed, every ratio <= 1          PASS       WARN      the governing limit state and d/c
    computed, something over            FAIL       ERROR     which limit state, and by how much
    calc exists, an input is missing    UNKNOWN    WARN      *which* input to author
    no calc registered for the kind     UNKNOWN    WARN      "an engineer's design governs"
    no calc, but an authored spec       PASS       WARN      quotes it, and says **authored**
    ==================================  =========  ========  ==================================

    **Adopting this framework moves no gate.** An item with nothing behind it is exactly as
    blocking as the UNKNOWN it replaced. What changes is that the finding now carries a name
    for the missing work — an item id a signoff can cover — instead of a paragraph of prose
    that no register can point at.

    ``authored`` is a house's own ``engineering_spec``/``header_spec`` string. It passes,
    because a house that has been to an engineer and wrote down what they said should not be
    blocked by this engine's failure to reproduce them — but the message says *authored*,
    never *computed*, so nobody mistakes a quotation for a calculation.

    ``defer=True`` is for a check that hands its question to an engineered design **without
    grading the limit states that design is computed against**. ``structural.frost_depth``
    is the case: it shares ``retaining_wall/<tag>`` with
    ``structural.foundation_unbalanced_fill`` — one design, one stamp, two checks — but its
    own subject is frost cover, and the item's calculation grades sliding, overturning and
    bearing. Without this, a wall that fails *sliding* would be reported as a frost failure,
    and a rule would be calling a wall non-compliant on evidence about something else. A
    deferred finding is UNKNOWN whatever the calculation found, says what the calculation
    found so the reader is not sent looking, and never opens the gate on its own.
    """
    record = records_of(ctx)[item]
    tags = tuple(tags) or record.element_tags
    if defer:
        return _deferred(record, cid, item, msg, tags, code, fix)
    if record.status is Status.OK:
        return Finding(severity=Severity.WARN, check_id=cid,
                       message=f"{msg} — engineered: {record.describe()}",
                       element_tags=tags, code_ref=code or record.basis or None,
                       result=Result.PASS, authority=Authority.ENGINEERED,
                       engineering_item=item)
    if record.status is Status.OVER:
        governing = record.governing
        if governing is None:
            detail = record.summary
        elif governing.is_safety_factor:
            # A safety factor is reported as itself. "Over by 162%" is arithmetically true
            # of the ratio and tells a reader nothing they can act on; "FS 0.57 against the
            # 1.50 required" is the sentence an engineer would write down.
            detail = (f"{governing.name} reaches FS {governing.capacity:.2f} against the "
                      f"{governing.demand:.2f} required ({governing.citation})")
        else:
            detail = (f"{governing.name} is over by {(governing.ratio - 1.0) * 100:.0f}% "
                      f"({record.describe()})")
        return Finding(severity=Severity.ERROR, check_id=cid,
                       message=f"{msg} — engineered design does not check: {detail}",
                       element_tags=tags, code_ref=code or record.basis or None,
                       fix_hint=fix, result=Result.FAIL, authority=Authority.ENGINEERED,
                       engineering_item=item)
    if record.status is Status.INCOMPLETE:
        missing = ", ".join(record.missing) or "an input the calculation needs"
        return Finding(severity=Severity.WARN, check_id=cid,
                       message=f"UNKNOWN — {msg}; the engineered check for `{item}` could "
                               f"not finish: {missing} is missing",
                       element_tags=tags, code_ref=code or record.basis or None,
                       fix_hint=fix or f"author {missing}",
                       result=Result.UNKNOWN, authority=Authority.ENGINEERED,
                       engineering_item=item)
    if authored:
        return Finding(severity=Severity.WARN, check_id=cid,
                       message=f"{msg} — an engineered design is AUTHORED (not computed by "
                               f"this engine) for `{item}`: {authored}",
                       element_tags=tags, code_ref=code, result=Result.PASS,
                       authority=Authority.ENGINEERED, engineering_item=item)
    return Finding(severity=Severity.WARN, check_id=cid,
                   message=f"UNKNOWN — {msg}; an engineer's design governs `{item}`, and "
                           f"this engine computes none",
                   element_tags=tags, code_ref=code,
                   fix_hint=fix or f"seal `{item}` in engineering.toml, or author an "
                                   f"engineering_spec for it",
                   result=Result.UNKNOWN, authority=Authority.ENGINEERED,
                   engineering_item=item)


def _deferred(record, cid: str, item: str, msg: str, tags: tuple[str, ...],
              code: str | None, fix: str | None) -> Finding:
    """``engineered(..., defer=True)`` — hand the question over without adopting a verdict.

    Always UNKNOWN, and that is the honest state: this rule's own subject is settled by a
    design nobody has sealed yet. What it *does* carry is the item id, so the outstanding
    work is nameable and one seal can answer this line and the line that computed it.
    """
    if record.status is Status.OK:
        where = (f"this engine's own screening of `{item}` checks out "
                 f"({record.describe()}), which is a draft, not a seal")
    elif record.status is Status.OVER:
        where = (f"and this engine's own screening of `{item}` does not check "
                 f"({record.describe()}) — see that item, not this line, for the defect")
    elif record.status is Status.INCOMPLETE:
        where = (f"and this engine's screening of `{item}` could not finish "
                 f"({', '.join(record.missing) or 'an input is missing'})")
    else:
        where = f"and this engine computes nothing for `{item}`"
    return Finding(
        severity=Severity.WARN, check_id=cid,
        message=f"UNKNOWN — {msg}; an engineer's design governs `{item}`, {where}",
        element_tags=tags, code_ref=code,
        fix_hint=fix or f"seal `{item}` in engineering.toml",
        result=Result.UNKNOWN, authority=Authority.ENGINEERED, engineering_item=item,
    )


__all__ = ["Authority", "advisory", "engineered", "failed", "not_applicable",
           "passed", "structural_advisory", "unknown"]

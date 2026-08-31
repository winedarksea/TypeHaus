"""Declared permit-submittal gate (M3 WP3.8).

The checklist itself is *not* here: it is declared by the jurisdiction profile
(:mod:`typehaus.checks.jurisdiction`), and this module only turns registry results into it.
While the list lived here it drifted from the registry — two registered R401.3 checks were
on no line of it — and a second jurisdiction would have meant an `if profile == ...` here.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.jurisdiction import JurisdictionProfile
from typehaus.checks.registry import CheckReport
from typehaus.engineering.fingerprint import Freshness
from typehaus.engineering.register import EngineeringRegister, Signoff
from typehaus.findings import Authority, Finding, Result, Severity


@dataclass(frozen=True)
class PermitChecklistItem:
    """One transparent, narrowly-scoped permit-submittal requirement."""

    label: str
    result: Result
    detail: str
    check_ids: tuple[str, ...]
    # Mirrors PermitItemSpec.blocking — see the reasoning there. A non-blocking item is
    # evaluated and printed exactly like any other; it just does not hold the gate shut.
    blocking: bool = True
    # Derived from the matched findings, never declared by the profile: whether *this*
    # house's geometry puts the requirement outside the prescriptive path is a fact about
    # 7 feet of unbalanced fill here and 3 feet next door, so a jurisdiction profile cannot
    # know it in advance and PermitItemSpec deliberately gains nothing.
    authority: Authority = Authority.PRESCRIPTIVE
    # The engineering item ids behind this line, when it is ENGINEERED — what a seal in
    # engineering.toml has to cover for the final gate to open.
    engineering_items: tuple[str, ...] = ()
    # How the seals on those items stand *right now*. The worst of them, since one stale
    # item on a line of four is a stale line. None on a prescriptive item, which has no
    # seal to be fresh or otherwise.
    seal: Freshness | None = None
    # Who sealed it, for the sheet's credit line. Only set when every item on this line is
    # covered by one and the same signoff — the common case, and the only one a single
    # credit line can honestly letter.
    signoff: Signoff | None = None

    @property
    def sealed(self) -> bool:
        """Whether this line satisfies the *final* gate.

        A prescriptive item needs no seal and so always does. An engineered one needs a
        signoff that is FRESH: not merely present. UNPINNED is deliberately not enough — a
        stamp with no fingerprint behind it cannot go stale, so it says nothing at all
        about the model in front of the reader, and treating it as final would make the
        seal a decoration.

        **And a FAILing line is never sealed, however fresh the stamp.** ``freshness()``
        answers "does this signoff still describe this model", which is a question about
        the *fingerprint* and not about the answer — so a signoff pinned to a wall the
        engine computes at FS 0.80 is perfectly fresh and perfectly wrong. Without this
        clause a ``[[signoff]]`` over a red item opens ``haus print --sealed``, which is
        the one thing the final gate exists to prevent. It mirrors what
        ``_authoring.engineered()`` already does by making its ``authored`` branch
        unreachable under ``Status.OVER``: an engineer's stamp can cover a calculation
        this engine cannot do, and it cannot cover one this engine did and failed.
        """
        if self.result is Result.FAIL:
            return False
        if self.authority is not Authority.ENGINEERED:
            return True
        return self.seal is Freshness.FRESH


#: The two verdicts that leave nothing outstanding on a permit line.
_GATE_OK = frozenset({Result.PASS, Result.NOT_APPLICABLE})


@dataclass(frozen=True)
class PermitChecklist:
    """The gate intentionally covers only checks this engine actually evaluates."""

    profile_name: str
    items: tuple[PermitChecklistItem, ...]

    @property
    def ok(self) -> bool:
        """The **draft** gate — semantics unchanged, plus N/A.

        An engineered item satisfies this on its own local calculation alone: that is
        exactly the requirement that draft approval permits a permit-ready printoff. The
        seal is the *separate*, final gate — see :attr:`sealed`.

        N/A satisfies it because a requirement whose governed condition does not exist in
        this building has nothing left to answer.
        """
        return all(item.result in _GATE_OK for item in self.items if item.blocking)

    @property
    def sealed(self) -> bool:
        """The **final** gate: :attr:`ok`, *and* every engineered item FRESH-sealed.

        Strictly stronger than :attr:`ok`, and separate from it on purpose. ``haus print``
        goes on gating at :attr:`ok` — a draft approval is exactly what permits a
        permit-ready printoff, and holding the printer hostage until a PE has signed would
        make the engine useless for the months before one does. ``haus print --sealed`` is
        the submittal gate.
        """
        # Every engineered item, blocking or not. A requirement in the staging lane is
        # still a requirement a professional has to sign; "not yet gating" is a statement
        # about this engine's confidence in its own rule, not about whether a 10-foot
        # cantilever retaining wall needs a stamp before anyone pours it.
        return self.ok and not self.unsealed

    @property
    def unsealed(self) -> tuple[PermitChecklistItem, ...]:
        """Engineered items still waiting on a fresh professional seal."""
        return tuple(item for item in self.engineered if not item.sealed)

    @property
    def stale_seals(self) -> tuple[PermitChecklistItem, ...]:
        """Items sealed once, whose model or calculation has moved since."""
        return tuple(item for item in self.items if item.seal is Freshness.STALE)

    @property
    def engineered(self) -> tuple[PermitChecklistItem, ...]:
        """Items whose verdict rests on an engineered design rather than a prescriptive table."""
        return tuple(item for item in self.items if item.authority is Authority.ENGINEERED)

    @property
    def under_review(self) -> tuple[PermitChecklistItem, ...]:
        """Items that are encoded and running but not yet gating."""
        return tuple(item for item in self.items if not item.blocking)


def evaluate_permit_checklist(report: CheckReport,
                              profile: JurisdictionProfile | str) -> PermitChecklist:
    """Turn the registry results into the profile's gate without hiding unknowns.

    Advisory, building-science, and engineered-header results stay in the full report but
    do not make a false claim that a prescriptive permit review evaluated them.

    ``profile`` accepts a name for callers that still pass one; the profile object is the
    real input, since it carries the checklist.

    Note that :attr:`PermitChecklist.ok` is strict — an UNKNOWN blocks, because "we could not
    evaluate this" is not a permit-ready answer. The checks-as-tests plugin deliberately
    takes the looser view (UNKNOWN passes) for the day-to-day inner loop; see its docstring.
    """
    if isinstance(profile, str):
        from typehaus.checks.code.mn_residential.profile import get_profile

        profile = get_profile(profile)
    items = [_item_from_findings(spec.label, spec.check_ids, report.findings,
                                 blocking=spec.blocking, report=report)
             for spec in profile.permit_items]
    items.append(_integrity_item(report.findings, profile.permit_check_ids()))
    return PermitChecklist(profile_name=profile.name, items=tuple(items))


def _item_from_findings(label: str, check_ids: tuple[str, ...], findings: list[Finding],
                        *, blocking: bool = True,
                        report: CheckReport | None = None) -> PermitChecklistItem:
    matched = [finding for finding in findings if finding.check_id in check_ids]
    failed = [finding for finding in matched if finding.result is Result.FAIL]
    unknown = [finding for finding in matched if finding.result is Result.UNKNOWN]
    na = [finding for finding in matched if finding.result is Result.NOT_APPLICABLE]
    authority = (Authority.ENGINEERED
                 if any(x.authority is Authority.ENGINEERED for x in matched)
                 else Authority.PRESCRIPTIVE)
    items = tuple(sorted({x.engineering_item for x in matched if x.engineering_item}))

    seal, signoff = _seal_state(items, report)

    def _item(result: Result, detail: str) -> PermitChecklistItem:
        return PermitChecklistItem(label, result, detail, check_ids, blocking, authority,
                                   items, seal, signoff)

    # Precedence: FAIL beats UNKNOWN beats all-N/A beats PASS. N/A only wins when *every*
    # matched finding is N/A — one real result on the line means the requirement did apply.
    if failed:
        return _item(Result.FAIL, failed[0].message)
    if unknown:
        return _item(Result.UNKNOWN, unknown[0].message)
    if not matched:
        # Distinct from "every matched finding is N/A" on purpose: no findings at all means
        # nobody looked, which is not the same claim as "this does not apply here".
        return _item(Result.UNKNOWN, "no evaluable model input")
    if len(na) == len(matched):
        return _item(Result.NOT_APPLICABLE, na[0].message)
    return _item(Result.PASS, f"{len(matched)} evaluated result(s) pass")


#: Worst-first. One stale item on a line of four makes the whole line stale, and an
#: unsealed one outranks an unpinned one because it is the further from done.
_SEAL_ORDER = (Freshness.UNSEALED, Freshness.STALE, Freshness.UNPINNED, Freshness.FRESH)


def _seal_state(items: tuple[str, ...],
                report: CheckReport | None) -> tuple[Freshness | None, Signoff | None]:
    """How the seals on one permit line's engineering items stand right now."""
    if not items or report is None:
        return None, None
    register: EngineeringRegister = report.engineering_register
    states: list[Freshness] = []
    signoffs: set[str] = set()
    found: Signoff | None = None
    for item in items:
        record = report.engineering[item]
        state, signoff = register.freshness(record)
        states.append(state)
        if signoff is not None:
            signoffs.add(signoff.id)
            found = signoff
    worst = min(states, key=_SEAL_ORDER.index)
    # One credit line can only name one engineer. Two signoffs on a line is a real and
    # legitimate arrangement; it just is not something a single "sealed by" can letter.
    return worst, (found if len(signoffs) == 1 else None)


def _integrity_item(findings: list[Finding],
                    covered: frozenset[str] = frozenset()) -> PermitChecklistItem:
    """The catch-all line: model errors that no other checklist item answers.

    ``covered`` matters more than it looks. This used to sweep up *every* ERROR-severity
    finding, which was harmless while every CODE check passed and became a real bug the
    moment one did not: a check on a deliberately non-gating item still emits an
    ERROR-severity FAIL, that error landed here, and this item is always blocking — so the
    staging lane silently blocked the gate anyway. A finding that already has a line of its
    own is reported there, once.
    """
    relevant = [finding for finding in findings
                if finding.check_id not in covered
                and (finding.severity is Severity.ERROR
                     or finding.check_id == "integrity.condition_coverage")]
    if relevant:
        return PermitChecklistItem(
            "Resolved-model and transition integrity", Result.FAIL, relevant[0].message,
            ("integrity.*",),
        )
    return PermitChecklistItem(
        "Resolved-model and transition integrity", Result.PASS,
        "no blocking model errors or uncovered boundary conditions", ("integrity.*",),
    )

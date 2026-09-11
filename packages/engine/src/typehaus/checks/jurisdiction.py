"""What a jurisdiction *is*, as data (→ 12 §checks/code).

The profile is the coverage authority: it names its own permit items, and every CODE-tier
check must either appear in one or be listed in ``permit_exclusions`` with a reason.
``tests/test_permit_coverage.py`` enforces exactly that, which is what makes the coverage
statement a claim rather than a hope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - a type-only edge, and the runtime import would cycle
    from typehaus.checks.code.mn_energy import PrescriptiveEnvelope


@dataclass(frozen=True)
class PermitItemSpec:
    """One line of a jurisdiction's permit checklist, and the checks that answer it."""

    label: str
    check_ids: tuple[str, ...]
    # The citation(s) this line rests on, for the printed cover sheet.
    code_refs: tuple[str, ...] = ()
    # Does this line gate the permit set? A non-blocking item is printed and evaluated like
    # any other, but does not hold up `haus permit-check` or `haus print`.
    #
    # This exists because UNKNOWN blocks exactly as hard as FAIL — correctly, since "we could
    # not evaluate this" is not a permit-ready answer — and a newly encoded rule normally
    # starts UNKNOWN against a house authored before it existed. Without a way to say "this
    # rule is real, is running, and is not yet gating", the only options when adding a rule
    # are to brick the reference house's print pipeline or to leave the rule off the
    # checklist entirely, and the second is the drift this profile mechanism exists to stop.
    #
    # An item flips to blocking in the commit that makes the house pass it. It is a staging
    # lane, not a parking lot: `tests/test_permit_coverage.py` pins how many items may sit
    # in it, so the count can only shrink.
    blocking: bool = True


@dataclass(frozen=True)
class InspectionSpec:
    """One inspection a jurisdiction requires, as data — beside :class:`PermitItemSpec`.

    A permit item asks "does the *drawing set* answer this rule"; an inspection asks "may
    the next trade start". They share the check registry and nothing else, which is why
    this is a second spec rather than a field on the first.

    Nothing here is a date or a duration. ``after`` is a partial order over inspections,
    ``gates`` names the trades that may not start until this one passes, and when either
    of those is satisfied is a fact about the site that only the owner can enter.
    """

    id: str
    label: str
    #: Who inspects. ``"report"`` is a third-party test result filed with the AHJ (a blower
    #: door), ``"owner"`` a hold the owner placed on themselves — neither is an AHJ visit,
    #: and calling both "building" would put a phone number on something nobody calls.
    authority: str
    #: Inspections that must be resolved before this one is requested.
    after: tuple[str, ...] = ()
    #: Trades (``emit.trades.TRADES``) that may not start until this passes.
    gates: tuple[str, ...] = ()
    #: Registry check ids whose findings must fold to PASS/N/A — same precedence as
    #: ``permit.py``: FAIL beats UNKNOWN beats all-N/A beats PASS.
    check_ids: tuple[str, ...] = ()
    #: Documents and physical items that must be on site, ticked by hand. The model cannot
    #: know whether the permit card is stapled to a stud.
    on_site: tuple[str, ...] = ()
    code_refs: tuple[str, ...] = ()
    #: Which build milestone this inspection sits in
    #: (:data:`typehaus.schedule.milestones.MILESTONES`). Declared rather than derived:
    #: the slab inspection and the braced-wall inspection both gate a trade in the
    #: weathertight slice, and only one of them happens in that phase of the build. No rule
    #: over ``after`` and ``gates`` separates them, so a rule that tried would be a guess
    #: dressed as a derivation. Empty inherits from ``after``, then falls to the first.
    milestone: str = ""
    #: Key into :mod:`typehaus.schedule.applicability`. ``None`` means the inspection always
    #: applies. A key whose evidence is inconclusive leaves the inspection listed as
    #: "applicability unknown" — N/A is earned, never assumed.
    applies_when: str | None = None


@dataclass(frozen=True)
class JurisdictionProfile:
    """A versioned code profile (→ 12 §checks/code)."""

    name: str
    edition: str
    effective_date: str
    irc_base: str
    coverage_statement: str
    # The NEC edition the electrical rules rest on, where it differs from the cycle
    # ``edition``/``irc_base`` name. Empty when the profile makes no electrical claim.
    nec_base: str = ""
    frost_depth_in: float | None = None
    # Presumptive load-bearing value of the soil (IRC Table R401.4.1). Footing *sizing* is
    # meaningless without it — required area is tributary load divided by this — so the
    # footing check reports UNKNOWN rather than a silent pass when a profile omits it.
    soil_bearing_psf: float | None = None
    # Unified soil classification of the backfill (IRC Table R405.1 group names: "GW", "GP",
    # "GM", "SW", "SC", "ML", "CL", ...). It selects the equivalent-fluid lateral pressure
    # column — 30, 45 or 60 psf/ft — that IRC Table R404.1.2(1) is published against. Absent,
    # the unbalanced-fill check reports UNKNOWN: the three columns give wall thicknesses two
    # steps apart, so guessing one is choosing an answer, not defaulting.
    soil_class: str | None = None
    # The permit checklist this jurisdiction gates on, in print order.
    permit_items: tuple[PermitItemSpec, ...] = ()
    # The inspections this jurisdiction requires, in the order its rule states them.
    # Empty on a profile that makes no inspection claim — `haus inspections` then says
    # so rather than printing a plausible list nobody adopted.
    inspections: tuple[InspectionSpec, ...] = ()
    # (check_id, reason) for registered checks this profile deliberately does not put on the
    # checklist. An unlisted, unreferenced check is a coverage hole, not a choice. The
    # coverage test gates CODE-tier ids; a check from another tier may be listed here too,
    # to say out loud that it runs and is not a permit line.
    permit_exclusions: tuple[tuple[str, str], ...] = ()
    # The prescriptive envelope table this jurisdiction's climate zone imposes. ``None``
    # means the profile states none, and the energy check reports UNKNOWN rather than
    # silently applying Minnesota's numbers.
    climate: PrescriptiveEnvelope | None = field(default=None)
    # The licensure certification a sealing professional must letter onto each sheet they
    # are responsible for (Minn. R. 1800.4200 subp. 3-4 in Minnesota). It is the
    # jurisdiction's own wording, verbatim, which is why it is data on the profile and not a
    # string in the sheet writer: a profile that states none prints none, rather than
    # printing Minnesota's sentence over another state's set.
    seal_certification: str | None = None

    def permit_check_ids(self) -> frozenset[str]:
        return frozenset(cid for item in self.permit_items for cid in item.check_ids)

    def inspection(self, inspection_id: str) -> InspectionSpec | None:
        for spec in self.inspections:
            if spec.id == inspection_id:
                return spec
        return None

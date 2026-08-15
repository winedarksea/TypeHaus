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
class JurisdictionProfile:
    """A versioned code profile (→ 12 §checks/code)."""

    name: str
    edition: str
    effective_date: str
    irc_base: str
    coverage_statement: str
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
    # (check_id, reason) for registered CODE-tier checks this profile deliberately does not
    # put on the checklist. An unlisted, unreferenced check is a coverage hole, not a choice.
    permit_exclusions: tuple[tuple[str, str], ...] = ()
    # The prescriptive envelope table this jurisdiction's climate zone imposes. ``None``
    # means the profile states none, and the energy check reports UNKNOWN rather than
    # silently applying Minnesota's numbers.
    climate: "PrescriptiveEnvelope | None" = field(default=None)

    def permit_check_ids(self) -> frozenset[str]:
        return frozenset(cid for item in self.permit_items for cid in item.check_ids)

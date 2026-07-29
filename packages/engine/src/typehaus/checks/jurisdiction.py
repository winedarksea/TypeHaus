"""What a jurisdiction *is*, as data (→ 12 §checks/code).

A profile used to be a handful of scalars (frost depth, soil bearing) while the things that
actually vary between jurisdictions lived hardcoded elsewhere: the permit checklist was a
hand-written list in ``checks/permit.py``, and the climate table sat in ``mn_energy.py``
under a Minnesota-specific name. Adding a second jurisdiction meant editing those modules,
and the checklist had already drifted out of sync with the registry — ``code.R401_3_grading``
and ``code.R401_3_impervious`` were registered checks no permit item ever referenced.

So the profile becomes the coverage authority: it names its own permit items, and every
CODE-tier check must either appear in one or be listed in ``permit_exclusions`` with a
reason. ``tests/test_permit_coverage.py`` enforces exactly that, which is what makes the
coverage statement a claim rather than a hope.
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

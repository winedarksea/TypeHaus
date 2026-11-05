"""Resolved duct parts and supports, derived off the house's ``DuctStandard`` (decision #114).

Records, not solids: each carries a point and an axis, and ``resolve/duct_part_solids.py``
draws them. Kept out of ``resolve/model.py`` for its length; ``ResolvedModel`` holds the lists.
Elbows stay ``resolve/mep_fittings.FittingRecord``s; these are everything else on a run.
"""

from __future__ import annotations

from dataclasses import dataclass

Point3 = tuple[float, float, float]


@dataclass(frozen=True)
class ResolvedDuctPart:
    """One part on a duct run (→ resolve/duct_parts.py).

    ``kind`` is a ``DuctPartKind``. ``size`` is the run's section as ordered (``4in``,
    ``18x8``); ``branch`` the branch, outlet or neck face. ``axis`` is the unit direction the
    part lies along, away from ``point`` into the run. ``other`` names what the run meets:
    the branch run, the plenum, the equipment or the terminal. ``product_ref`` None with
    ``fabricated`` False and ``integral`` False is a part the standard has no row for:
    ``gap`` says why, and ``mep.duct_terminations`` grades it UNKNOWN.
    """

    kind: str
    run_tag: str
    storey: str
    size: str
    point: Point3
    axis: Point3
    branch: str | None = None
    other: str | None = None
    port: str | None = None
    product_ref: str | None = None
    fabricated: bool = False
    integral: bool = False
    length_m: float | None = None
    width_m: float | None = None
    height_m: float | None = None
    gap: str | None = None

    @property
    def billed(self) -> bool:
        """Whether this record is a row somebody orders or makes."""
        return not self.integral and (self.product_ref is not None or self.fabricated)


@dataclass(frozen=True)
class ResolvedDuctSupport:
    """One hanger on a duct run (→ resolve/duct_supports.py).

    ``hangs_from`` is the member or deck it is fastened to; None with ``gap`` set is a
    support with nothing overhead, graded by ``mep.duct_supports``. ``drop_m`` is the strap
    or rod length from that member down to the duct's top.
    """

    run_tag: str
    storey: str
    size: str
    point: Point3
    hanger: str
    spacing_m: float
    product_ref: str | None = None
    hangs_from: str | None = None
    drop_m: float = 0.0
    width_m: float | None = None
    thickness_m: float | None = None
    gap: str | None = None

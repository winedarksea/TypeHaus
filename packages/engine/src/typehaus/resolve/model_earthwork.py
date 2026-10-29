"""Resolved earthwork records: the wall drain columns and the over-dig around them.

Both are billed by ``takeoff/excavation.py`` off these records; their solids only draw.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedWallColumn:
    """The stone column standing beside one bed (``FootingBedding.wall_column``)."""

    bed_tag: str
    wall_tag: str
    aggregate: str
    width_m: float
    z0_m: float  # the lowest stone: the excavation floor beside the bed, or a footing top
    top_m: float
    #: The strip grade the wall is backfilled against; the cap closes the column under it.
    grade_m: float
    volume_m3: float
    #: Soil-side face plus the top, where the fabric is authored; 0 otherwise.
    geotextile_m2: float
    #: The column's top-face plan area.
    plan_area_m2: float
    #: How far the stone reaches square past the host footing's outer edge, and the top of
    #: that footing: IRC R405.1's 12" and 6" are measured off these.
    beyond_footing_m: float = 0.0
    footing_top_m: float = 0.0


@dataclass(frozen=True)
class ResolvedExcavation:
    """One hole's volumes, all in bank or placed cubic metres as named."""

    uid: str
    tag: str
    hosts: tuple[str, ...]
    floor_m: float
    top_m: float
    cut_bank_m3: float
    #: Everything backfilled outside the structure: native lifts plus the cap.
    fill_m3: float
    cap_m3: float
    #: Drain-column stone placed with the backfill (also in ``model.wall_columns``).
    column_m3: float
    swell: float
    shrink: float
    cap_material: str
    lift_m: float

    @property
    def native_m3(self) -> float:
        return self.fill_m3 - self.cap_m3

    @property
    def bank_for_fill_m3(self) -> float:
        """Spoil, measured in the bank, that compacts to the fill."""
        return self.fill_m3 / (1.0 - self.shrink)

    @property
    def haul_off_loose_m3(self) -> float:
        """What leaves the site, bulked: cut not reused as fill."""
        return max(self.cut_bank_m3 - self.bank_for_fill_m3, 0.0) * (1.0 + self.swell)

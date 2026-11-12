"""Finished floor area: the CFA less unfinished rooms and floor under 5'-0" of head.

CFA (:mod:`resolve.conditioned_area`) is the energy code's measure: everything inside the
thermal envelope. An assessor, appraiser or listing counts something smaller, the ANSI Z765
"finished area": space finished like the rest of the house, with sloped-ceiling floor under
5'-0" left out, and above and below grade reported apart. This derives that reading from
the CFA, so the two share one measuring line:

* **The structural face, not Z765's exterior finish face.** The two differ by the
  outsulation and cladding, the same gap CFA already leaves out (``BASIS``).
* **A room is unfinished on positive evidence:** no floor finish AND ``Room.unpainted``.
  Bare deck under bare gypsum is unfinished space. A sealed-concrete mechanical room has a
  finish, so it stays in.
* **Floor under 5'-0" of clear head is cut**, the same line R304.3 and
  :func:`roof_geometry.room_head_limited_area_m2` use (``MIN_COUNTABLE_HEAD_M``).
* **Below grade** is a storey whose floor is at least ``BELOW_GRADE_MARGIN_M`` under the
  site grade datum. Checks read the same rule.

Oracled by ``houses/catlin/notes/finished_floor_area.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.resolve.conditioned_area import SF_PER_M2

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.model.plan import PlanModel
    from typehaus.resolve.model import ResolvedModel

# How far under the grade datum a floor must sit to be below grade. Two feet, not zero: a
# slab-on-grade main floor is normally authored a few inches below the datum, and calling
# that a basement would put every house's ground floor under R310.1's escape rule.
BELOW_GRADE_MARGIN_M = 0.6

BASIS = ("ANSI Z765-style finished area: the conditioned floor area (structural face, not "
         "Z765's exterior finish face) less unfinished rooms (no floor finish, unpainted) "
         "and floor under 5'-0\" of clear head")


def storey_below_grade(plan: PlanModel, storey) -> bool | None:
    """Is the storey's floor below the site grade datum? ``None`` when no grade is stated."""
    grade = plan.project.site.grade
    if grade is None:
        return None
    return storey.elevation.meters + BELOW_GRADE_MARGIN_M <= grade.meters


def room_is_unfinished(room) -> bool:
    """No floor finish and bare (unpainted) faces: unfinished space, on positive evidence."""
    return room.floor_finish is None and bool(getattr(room, "unpainted", False))


@dataclass(frozen=True)
class StoreyFinishedArea:
    storey: str
    below_grade: bool | None
    conditioned_m2: float  # the CFA row this starts from
    unfinished_m2: float
    low_head_m2: float  # finished floor under 5'-0" of head
    unfinished_rooms: tuple[str, ...]

    @property
    def area_m2(self) -> float:
        return max(self.conditioned_m2 - self.unfinished_m2 - self.low_head_m2, 0.0)

    @property
    def area_ft2(self) -> float:
        return self.area_m2 * SF_PER_M2


@dataclass(frozen=True)
class FinishedFloorArea:
    storeys: tuple[StoreyFinishedArea, ...]
    basis: str = BASIS

    @property
    def area_m2(self) -> float:
        return sum(row.area_m2 for row in self.storeys)

    @property
    def above_grade_m2(self) -> float:
        return sum(row.area_m2 for row in self.storeys if row.below_grade is False)

    @property
    def below_grade_m2(self) -> float:
        return sum(row.area_m2 for row in self.storeys if row.below_grade is True)

    @property
    def excluded_rooms(self) -> tuple[str, ...]:
        return tuple(tag for row in self.storeys for tag in row.unfinished_rooms)


def _low_head_region(model: ResolvedModel, region, elevation_m: float):
    """The part of ``region`` a roof rakes below 5'-0" of clear head."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all
    from typehaus.resolve.roof_geometry import (
        MIN_COUNTABLE_HEAD_M,
        roof_headroom_region,
        roof_structure_plumb_depth_m,
    )

    cuts = []
    for roof in model.roofs:
        if not roof.footprint:
            continue
        under = region.intersection(Polygon(roof.footprint))
        if under.is_empty or under.area <= 1e-9:
            continue
        clear = roof_headroom_region(
            roof, elevation_m, MIN_COUNTABLE_HEAD_M + roof_structure_plumb_depth_m(model, roof))
        low = under if clear.is_empty else under.difference(clear)
        if not low.is_empty and low.area > 1e-9:
            cuts.append(low)
    return union_all(cuts) if cuts else None


def _storey_row(model: ResolvedModel, cfa_row, storey) -> StoreyFinishedArea:
    from shapely.geometry import Polygon

    from typehaus.model.enums import FloorOpeningPurpose
    from typehaus.resolve.overlay import difference, union_all

    region = cfa_row.polygon
    wells = [Polygon([p.xy_m for p in e.outline])
             for e in model.plan.storey_elements(storey.tag)
             if e.element_kind == "FloorOpening" and e.purpose is FloorOpeningPurpose.STAIR]
    if wells:
        region = difference(region, union_all(wells))
    rooms = [r for r in model.rooms if r.storey == storey.tag and len(r.clear_face) >= 3]
    authored = {e.tag: e for e in model.plan.storey_elements(storey.tag)
                if e.element_kind == "Room"}
    cold = [r for r in rooms if r.tag in authored and room_is_unfinished(authored[r.tag])]
    unfinished_m2 = 0.0
    if cold:
        cut = union_all([Polygon(r.clear_face) for r in cold]).intersection(region)
        unfinished_m2 = cut.area
        region = difference(region, cut)
    low = _low_head_region(model, region, storey.elevation.meters)
    return StoreyFinishedArea(
        storey=storey.tag, below_grade=storey_below_grade(model.plan, storey),
        conditioned_m2=cfa_row.area_m2, unfinished_m2=unfinished_m2,
        low_head_m2=0.0 if low is None else low.area,
        unfinished_rooms=tuple(sorted(r.tag for r in cold)))


def finished_floor_area(model: ResolvedModel) -> FinishedFloorArea:
    """The model's finished floor area, storey by storey, off its CFA."""
    from typehaus.resolve.conditioned_area import conditioned_floor_area

    storeys = {s.tag: s for s in model.plan.storeys}
    rows = tuple(_storey_row(model, row, storeys[row.storey])
                 for row in conditioned_floor_area(model).storeys)
    return FinishedFloorArea(rows)

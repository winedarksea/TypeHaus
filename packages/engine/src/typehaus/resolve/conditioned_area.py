"""Conditioned floor area (CFA): each conditioned storey measured to its structural face.

The energy code's "conditioned floor area" is a building measure, not a room sum. Rooms stop
at the finish face, which leaves every wall out; an exterior-dimension measure counts the
outsulation and the cladding, which enclose no floor. The owner's reading (2026-10-31), and
the one this derives:

* **To the outer face of the structure** — studs plus sheathing, or the concrete of a
  foundation wall. Layers outboard of it (ccSPF, XPS/EPS, vent gap, girts, cladding) are not
  floor area. A rafter plate with no skin of its own reaches the sheathing of the wall it
  bears on, so a hot-roofed attic runs to the same line as the storey below.
* **A volume counts once, at its lowest floor.** A ``STAIR`` floor opening (a stair well, a
  hall open to the roof) is deducted on the storey it is cut in. A ``CHASE`` is boxed and
  decked over or carries a fixture, and a ``HATCH`` has a lid: both stay floor.
* **Only conditioned space.** The envelope is :mod:`resolve.envelope_geometry`'s, so a
  porch, deck, garage or sunken court (unconditioned Rooms, or structures with no Room)
  never enters; an unconditioned Room inside the footprint is cut back out.

Cached on the model's :class:`EnvelopeGeometry`, so it is invalidated with it.
Oracled by ``houses/catlin/notes/conditioned_floor_area.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from typehaus.model.enums import FloorOpeningPurpose, LayerFunction

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel, ResolvedWall

SF_PER_M2 = 10.763910416709722

# The layers a structural face is measured over. Everything else is lining or outboard.
_STRUCTURAL_FUNCTIONS = frozenset({LayerFunction.STRUCTURE.value, LayerFunction.SHEATHING.value})
# How far past its own body a skinless bearing course (a rafter plate) reaches the storey
# below's structure: the 1/2" sheathing it stands inboard of, with slop. Only that storey's
# region is added, so a setback is never crossed.
_PLATE_REACH_M = 0.0254

BASIS = ("conditioned storeys measured to the outer face of the structure (studs + "
         "sheathing, or foundation concrete), excluding outboard insulation, girts and "
         "cladding; stair wells and open-to-below voids deducted on the storey above")


@dataclass(frozen=True)
class StoreyConditionedArea:
    storey: str
    gross_m2: float  # footprint to the structural face
    deducted_m2: float  # STAIR openings inside it
    deductions: tuple[str, ...]
    polygon: object = field(repr=False, compare=False)

    @property
    def area_m2(self) -> float:
        return self.gross_m2 - self.deducted_m2

    @property
    def area_ft2(self) -> float:
        return self.area_m2 * SF_PER_M2


@dataclass(frozen=True)
class ConditionedFloorArea:
    storeys: tuple[StoreyConditionedArea, ...]
    basis: str = BASIS

    @property
    def area_m2(self) -> float:
        return sum(storey.area_m2 for storey in self.storeys)

    @property
    def area_ft2(self) -> float:
        return self.area_m2 * SF_PER_M2


def _structural_part(wall: ResolvedWall):
    """The wall's structure and sheathing layers; the lining inboard is filled as a hole."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    parts = [Polygon(layer.polygon) for layer in wall.depth_layers()
             if layer.function in _STRUCTURAL_FUNCTIONS and not layer.is_cavity
             and len(layer.polygon) >= 3]
    parts = [part for part in parts if part.area > 0]
    return union_all(parts) if parts else None


def _storey_region(model: ResolvedModel, envelope, storey: str, below):
    """The storey's conditioned footprint to its structural face, before deductions."""
    from shapely.geometry import Polygon

    from typehaus.resolve.envelope_geometry import _fill_holes, _wall_body, carries_a_weather_skin
    from typehaus.resolve.overlay import difference, intersection, union_all

    rooms = [r for r in model.rooms if r.storey == storey and len(r.clear_face) >= 3]
    parts = [Polygon(r.clear_face) for r in rooms if r.conditioned]
    if not parts:
        return None
    # Skinned and foundation walls give their structure; partitions are filled as holes. A
    # skinless course (a rafter plate, a porch guard teed in) encloses nothing: it reaches
    # only the structure of the storey below it.
    plates = []
    for wall in model.walls:
        if wall.storey != storey or not envelope.bounds_conditioned_space(wall):
            continue
        if carries_a_weather_skin(wall) or wall.is_foundation:
            part = _structural_part(wall)
            if part is not None:
                parts.append(part)
        elif (body := _wall_body(wall)) is not None:
            plates.append(body.buffer(_PLATE_REACH_M))
    if plates and below is not None:
        parts.append(intersection(below, union_all(plates)))
    region = _fill_holes(union_all(parts))
    cold = [Polygon(r.clear_face) for r in rooms if not r.conditioned]
    return difference(region, union_all(cold)) if cold else region


def _build(model: ResolvedModel) -> ConditionedFloorArea:
    from shapely.geometry import Polygon

    from typehaus.resolve.envelope_geometry import envelope_geometry
    from typehaus.resolve.overlay import intersection, union_all

    envelope = envelope_geometry(model)
    rows: list[StoreyConditionedArea] = []
    below = None
    for storey in sorted(model.plan.storeys, key=lambda s: s.elevation.meters):
        region = _storey_region(model, envelope, storey.tag, below)
        if region is None or region.is_empty:
            continue
        wells = [element for element in model.plan.storey_elements(storey.tag)
                 if element.element_kind == "FloorOpening"
                 and element.purpose is FloorOpeningPurpose.STAIR]
        cut = [Polygon([p.xy_m for p in well.outline]) for well in wells]
        deducted = intersection(region, union_all(cut)).area if cut else 0.0
        rows.append(StoreyConditionedArea(
            storey.tag, region.area, deducted,
            tuple(sorted(well.tag for well in wells)), region))
        below = region
    return ConditionedFloorArea(tuple(rows))


def conditioned_floor_area(model: ResolvedModel) -> ConditionedFloorArea:
    """The model's CFA, built once per envelope derivation."""
    from typehaus.resolve.envelope_geometry import envelope_geometry

    envelope = envelope_geometry(model)
    if envelope.conditioned_area is None:
        envelope.conditioned_area = _build(model)
    return envelope.conditioned_area

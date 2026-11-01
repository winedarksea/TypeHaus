"""A framed wall stands on the subfloor, not on the joists (decision #110).

The storey datum is the TOP OF JOISTS and stays so. A crew stands every wall on the sheet
that rides above it, so the bottom plate sits a subfloor up, and a bearing wall's double top
plate is cut to meet the joist soffit over it: ``3/4 + 1 1/2 + 102 7/8 + 3 = 108 1/8"`` on
a 120" storey with 11 7/8" joists. The stud is whatever closes that stack — derived here,
never typed.

Only the FRAMING moves. ``ResolvedWall.plate_seat_z_m`` is the frame base
(:attr:`ResolvedWall.frame_base_z_m`); the sill/band datum (``base_ref_z_m``) and the body
stay on the storey datum, so windows, backing bands and the skin do not move. A floor-level
interior door is the exception, because its rough opening is framed up from the subfloor:
its ``sill_m`` becomes the seat (:func:`door_sill_m`), and since its RO height is derived
from the finished floor (``door_floor_finish``) its head stays where it was.

:func:`deck_top_under` mirrors ``partition_top.deck_underside_over``: plan only (decks,
storey elevations, subfloor thicknesses), so it runs before openings resolve.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from shapely.geometry import LineString, Polygon

from typehaus.model.refs import ToRoof
from typehaus.quantities import inch
from typehaus.resolve.layer_bands import reband_for_platform
from typehaus.resolve.layout_lines import lines_by_wall
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.overlay import union_all
from typehaus.resolve.partition import (
    bearing_ref_tags,
    framing_top_z_m,
    runs_full_storey_height,
    takes_a_deflection_gap,
)
from typehaus.resolve.partition_top import deck_underside_over
from typehaus.resolve.topology import site_grade_elevation_m_from_plan

# A deck is the wall's floor when its top stands this close above the datum: a sheet on the
# joists (3/4"), a cast cap. A tub platform or a pad inside the storey is not (the same
# window ``door_floor_finish`` reads a door's floor through).
_DECK_ABOVE_M = inch(4).meters
_DECK_BELOW_M = inch(1 / 16).meters
_MIN_OVERLAP_M2 = 1e-4


def _plate_face(wall: ResolvedWall) -> Any:
    """The bottom plate's plan footprint: the structure layer, else the axis at its depth."""
    rings = [Polygon(layer.polygon) for layer in wall.layers
             if layer.function == "structure" and len(layer.polygon) >= 3]
    rings = [ring if ring.is_valid else ring.buffer(0) for ring in rings]
    if rings:
        return union_all(rings)
    return LineString(wall.axis).buffer(max(wall.thickness_m, 1e-3) / 2.0, cap_style=2)


def _deck_tops(plan: Any, storey: Any) -> list[tuple[Polygon | None, float]]:
    """``(outline or None for the whole storey, top)`` per deck a wall could stand on."""
    from typehaus.resolve.envelope import _slab_elevations

    out: list[tuple[Polygon | None, float]] = []
    for element in plan.storey_elements(storey.tag):
        if element.element_kind == "FloorSystem":
            if element.subfloor is None:
                continue
            top = ((element.top_elevation or storey.elevation).meters
                   + element.subfloor.thickness.meters)
            ring = element.subfloor_outline or element.outline
        elif element.element_kind == "Slab":
            top = _slab_elevations(element, storey.elevation.meters)[1]
            ring = element.outline
        else:
            continue
        outline = Polygon([p.xy_m for p in ring]) if len(ring) >= 3 else None
        if outline is not None and not outline.is_valid:
            outline = outline.buffer(0)
        out.append((outline, top))
    return out


def deck_top_under(model: ResolvedModel, wall: ResolvedWall) -> float | None:
    """The top of the deck ``wall``'s bottom plate stands on, or ``None`` if it is not raised.

    The **maximum** across the decks under the plate, where :func:`deck_underside_over`
    takes the minimum: a plate is flat and bears on the highest thing under it, and the
    low reading would put it inside the other deck. ``None`` where no deck lifts the plate
    off the datum (a slab-on-grade storey, or no deck under the wall) — never a guess.
    """
    storey = next((s for s in model.plan.storeys if s.tag == wall.storey), None)
    if storey is None:
        return None
    datum = wall.base_ref_z_m
    face = _plate_face(wall)
    tops = [top for outline, top in _deck_tops(model.plan, storey)
            if datum - _DECK_BELOW_M <= top <= datum + _DECK_ABOVE_M
            and (outline is None or outline.intersection(face).area > _MIN_OVERLAP_M2)]
    if not tops or max(tops) <= datum + _DECK_BELOW_M:
        return None
    return max(tops)


def _seats_on_deck(model: ResolvedModel, wall: ResolvedWall) -> bool:
    """Framed, storey-based walls only: an authored base (the attic's ``RAFTER_PLATE`` at
    240 3/4", a stud wall on a curb) already says what it stands on; a pour, ICF or masonry
    wall has no plate."""
    from typehaus.resolve.framing.solver import frames_as_members, structure_layer

    if wall.is_foundation:
        return False
    authored = model.plan.by_tag(wall.tag)
    if getattr(authored, "base_elevation", None) is not None:
        return False
    return frames_as_members(structure_layer(model.plan, wall.assembly))


def _bears_under_deck(model: ResolvedModel, wall: ResolvedWall,
                      bearing_refs: frozenset[str]) -> float | None:
    """The joist soffit a full-height, flat-topped, non-partition wall's plate meets.

    A partition stops 3/4" short of it (``partition_top``) and a raked wall follows the roof;
    neither is this pass's. Never lowers a plate.
    """
    if isinstance(getattr(model.plan.by_tag(wall.tag), "top", None), ToRoof):
        return None
    if takes_a_deflection_gap(model, wall, bearing_refs):
        return None
    if not runs_full_storey_height(model, wall):
        return None
    soffit = deck_underside_over(model, wall)
    if soffit is None or soffit < framing_top_z_m(wall) - 1e-9:
        return None
    storey = next(s for s in model.plan.storeys if s.tag == wall.storey)
    ceiling = storey.elevation.meters + storey.default_ceiling_height.meters
    # The plate closes the storey's own gap to the joists, not a void over a short wall.
    if soffit - ceiling > _DECK_ABOVE_M:
        return None
    return soffit


def apply_plate_seats(model: ResolvedModel) -> None:
    """Stand every framed platform wall on its subfloor; cut bearing studs to the soffit.

    Runs after ``extend_walls_to_platform`` and before openings resolve, which read the seat
    for a floor-level door's sill. ``replace`` keeps ``plate_top_z_m`` from the lift.
    """
    bearing_refs = bearing_ref_tags(model.plan)
    grade_m = site_grade_elevation_m_from_plan(model.plan)
    lines = lines_by_wall(model.layout_lines)
    for index, wall in enumerate(model.walls):
        if not _seats_on_deck(model, wall):
            continue
        seat = deck_top_under(model, wall)
        if seat is None:
            continue
        seated = replace(wall, plate_seat_z_m=seat)
        soffit = _bears_under_deck(model, seated, bearing_refs)
        if soffit is not None:
            z1 = max(seated.z1_m, soffit)
            seated = replace(
                seated, z1_m=z1, plate_top_z_m=soffit,
                layers=reband_for_platform(seated, seated.z0_m, z1, grade_m,
                                           lines.get(wall.tag), plate_top=soffit,
                                           plate_base=seated.plate_base_z_m))
        model.walls[index] = seated


def door_sill_m(plan: Any, element: Any, wall: ResolvedWall, sill_m: float) -> float:
    """A floor-level interior door's rough opening starts at the subfloor, not the joist top.

    ``sill_m`` is measured from the sill datum; a door authored at 0 on a seated wall is
    framed up from the plate's underside, so its sill is the seat. Raised and dropped sills
    are the author's and stay. So does an EXTERIOR door's: its sill pan, threshold and
    landing are coordinated by the door's installation (R311.3), off the datum.
    """
    if element.element_kind != "Door" or abs(sill_m) > 1e-9:
        return sill_m
    door_type = next((t for t in plan.library.door_types if t.tag == element.type_ref), None)
    if door_type is None or door_type.exterior:
        return sill_m
    return wall.frame_base_z_m - wall.base_ref_z_m

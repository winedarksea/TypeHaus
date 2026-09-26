"""The floor a room's finish actually covers: clear face, less its zones, less the deck voids.

Every consumer used to start from ``clear_face`` and cut deck openings on its own, and each
got it wrong: the viewer holed every room with every well on the storey (a flush well is
uncuttable, an outside one bridges into the neighbour), and the GLB and takeoff cut none,
so RM-S-HALL billed ~70 sf of LVP over its stair. Derived once here; everyone reads it.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import replace
from typing import Any

from shapely.geometry import Polygon

from typehaus.resolve.model import FinishPart, ResolvedModel, ResolvedRoom
from typehaus.resolve.overlay import difference, union_all
from typehaus.resolve.room_floor import SLAB_MATCH_TOLERANCE_M, room_floor_elevation

# Voids grow by this before the cut: a well authored flush with a room edge misregisters by
# ~0.25 mm, which would otherwise leave a sliver strip of finish along the well.
_VOID_GROWTH_M = 1e-3
# Parts under 1 cm2 are overlay noise, not floor anyone lays.
_MIN_PART_M2 = 1e-4


def level_voids(model: ResolvedModel, structural: float) -> list[Polygon]:
    """Deck voids of every floor whose deck top sits at ``structural`` (within tolerance)."""
    return [Polygon(ring) for floor in model.floors
            if abs(floor.deck_z1_m - structural) < SLAB_MATCH_TOLERANCE_M
            for ring in floor.deck_voids if len(ring) >= 3]


def _ring(coords: Iterable[Sequence[float]]) -> list[tuple[float, float]]:
    return [(x, y) for x, y in list(coords)[:-1]]


def finish_parts(geometry: Any) -> tuple[FinishPart, ...]:
    """``(outline, holes)`` for each polygon piece of ``geometry`` above the noise floor."""
    parts: list[FinishPart] = []
    for piece in getattr(geometry, "geoms", (geometry,)):
        if piece.geom_type != "Polygon" or piece.area < _MIN_PART_M2:
            continue
        parts.append((_ring(piece.exterior.coords),
                      tuple(_ring(hole.coords) for hole in piece.interiors)))
    return tuple(parts)


def _valid(ring: Sequence[tuple[float, float]]) -> Polygon:
    polygon = Polygon(ring)
    return polygon if polygon.is_valid else polygon.buffer(0)


def with_field_finish(model: ResolvedModel, room: ResolvedRoom,
                      face: Polygon | None = None) -> ResolvedRoom:
    """``room`` with ``field_finish``/``field_area_m2`` set and its zones cut by the voids.

    ``face`` is the clear cell when the caller has it (it keeps any interior rings the
    ``clear_face`` ring drops, so an uncut room's field area equals ``area_m2``).
    """
    if len(room.clear_face) < 3:
        return room
    face = face if face is not None else _valid(room.clear_face)
    voids = level_voids(model, room_floor_elevation(model, room))
    cut = (union_all([void.buffer(_VOID_GROWTH_M, join_style="mitre") for void in voids])
           if voids else None)
    zones = []
    for zone in room.finish_zones:
        net = _valid(zone.outline)
        if cut is not None:
            net = difference(net, cut)
        parts = finish_parts(net)
        zones.append(replace(zone, parts=parts,
                             area_m2=sum(_area(part) for part in parts)))
    field = face
    blocked = [_valid(zone.outline) for zone in room.finish_zones if len(zone.outline) >= 3]
    if cut is not None:
        blocked.append(cut)
    if blocked:
        field = difference(face, union_all(blocked))
    parts = () if field.is_empty else finish_parts(field)
    return replace(room, finish_zones=tuple(zones), field_finish=parts,
                   field_area_m2=sum(_area(part) for part in parts))


def _area(part: FinishPart) -> float:
    outline, holes = part
    return float(Polygon(outline, holes=[list(hole) for hole in holes]).area)

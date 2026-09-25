"""Paint no assembly authors: exposed gypsum facing a used room.

Paint is authored as a ``latex-paint`` coating layer where an assembly carries one. Where it
does not, the gypsum is still painted in reality and this bills it: the STC presets keep
paint out of a tested core (``library/assemblies/``), and no deck's ``ceiling_below``
carries any.

A gypsum layer is *exposed* when it ends a stack, so nothing is outboard of it, and it bills
only the part of its face that bounds a ``Room`` that is not UNCONDITIONED. A chase, a cavity
or the outdoors takes no paint. A stack ending in a coating (paint, primer) is authored and
left alone, so nothing bills twice.

Also bills a coating AUTHORED as a deck's ``ceiling_below`` or a room's ``ceiling_lining``:
``sheet_goods`` walks those stacks as sheets and skips coatings, so it is billed here by
area instead. A roof's lining coating is already in ``envelope_layers``' ``roof ceiling``.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from shapely.geometry import Point, Polygon
from shapely.prepared import prep

from typehaus.model.enums import LayerFunction, Occupancy
from typehaus.model.spatial import Room
from typehaus.resolve.ceiling_over import ceiling_decks_over
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_M2_TO_FT2 = 10.7639104
#: What derived paint bills as — the library's interior latex, priced by the house's row.
PAINT = "latex-paint"
#: A sample stands this far off the gypsum face, into whatever it faces.
_PROBE_M = 0.0254
#: Sample spacing along a face; a short wall still takes three.
_STATION_M = 0.15
#: A wall and a room share a storey band only if they overlap by more than this, so a
#: basement wall does not paint the room over it.
_MIN_Z_OVERLAP_M = 0.3


def derived_paint_rows(model: ResolvedModel,
                       wall_net_m2: dict[str, float]) -> list[dict[str, object]]:
    """``envelope_layers``-shaped rows: derived paint by scope, plus authored ceiling coats."""
    from typehaus.takeoff.envelope import wall_layer_net_area_m2

    rooms = _used_rooms(model)
    areas: dict[tuple[str, str], float] = defaultdict(float)
    for wall in model.walls:
        layers = [layer for layer in wall.layers if not layer.is_cavity]
        for row in _end_rows(layers):
            gypsum = [layer for layer in row if _is_gypsum(model, layer.material_ref)]
            if not gypsum:
                continue
            fraction = _facing_fraction(wall, row, rooms)
            if fraction <= 0.0:
                continue
            net = wall_net_m2.get(wall.tag, 0.0)
            areas[("wall (derived)", PAINT)] += fraction * sum(
                wall_layer_net_area_m2(model, wall, layer, net) for layer in gypsum)

    by_tag = {room.tag: room for room in model.rooms}
    decked: dict[str, bool] = {}
    for ceiling in model.ceilings:
        room = by_tag.get(ceiling.room_ref)
        if room is None or not ceiling.layers or not _used(room):
            continue
        face = ceiling.layers[0]
        area = abs(Polygon(ceiling.outline).area)
        if _is_gypsum(model, face.material_ref):
            areas[("ceiling (derived)", PAINT)] += area
        elif _is_coating(model, face.material_ref) and _sheet_billed(model, room, decked):
            areas[("ceiling", face.material_ref)] += area

    return [
        {"scope": scope, "function": LayerFunction.FINISH.value, "material": material,
         "thickness_in": 0.0, "net_area_sqft": round(area * _M2_TO_FT2, 1),
         "also_in_sheet_goods": False}
        for (scope, material), area in sorted(areas.items()) if area > 0.0
    ]


def _material(model: ResolvedModel, ref: str) -> Any:
    return model.plan.library.material(ref) if ref else None


def _is_gypsum(model: ResolvedModel, ref: str) -> bool:
    return getattr(_material(model, ref), "gypsum_type", None) is not None


def _is_coating(model: ResolvedModel, ref: str) -> bool:
    return bool(getattr(_material(model, ref), "coating", False))


def _used(room: Any) -> bool:
    return bool(room.occupancy != Occupancy.UNCONDITIONED.value)


def _sheet_billed(model: ResolvedModel, room: Any, decked: dict[str, bool]) -> bool:
    """True where ``sheet_goods`` walks this ceiling's stack: a room lining or a deck's."""
    if room.tag not in decked:
        plan_room = model.plan.by_tag(room.tag)
        decked[room.tag] = bool(
            (isinstance(plan_room, Room) and plan_room.ceiling_lining)
            or ceiling_decks_over(model.plan, room.storey, Polygon(room.clear_face)))
    return decked[room.tag]


def _used_rooms(model: ResolvedModel) -> list[tuple[Polygon, Any, float, float]]:
    """``(face, prepared face, z0, z1)`` per used room, over its storey's ceiling height."""
    storeys = {storey.tag: storey for storey in model.plan.storeys}
    out = []
    for room in model.rooms:
        storey = storeys.get(room.storey)
        if storey is None or not _used(room) or len(axis_ring(room)) < 3:
            continue
        face = axis_polygon(room)  # which room a face looks into is an ownership question
        z0 = storey.elevation.meters
        out.append((face, prep(face), z0, z0 + storey.default_ceiling_height.meters))
    return out


def _end_rows(layers: list[Any]) -> list[list[Any]]:
    """The layer row at each end of a stack; a slotted row is every region of it."""
    if not layers:
        return []

    def row(end: Any) -> list[Any]:
        return [end] if end.slot is None else [x for x in layers if x.slot == end.slot]

    first, last = row(layers[0]), row(layers[-1])
    return [first] if last[0] is first[0] else [first, last]


def _facing_fraction(wall: ResolvedWall, row: list[Any],
                     rooms: list[tuple[Polygon, Any, float, float]]) -> float:
    """Share of the row's outer face that looks into a used room, sampled along the axis.

    The probe stands 1" off the outer face and is tested against each room's AXIS cell, so
    the room on this side contains it at every station, corners included, and the one
    across the wall does not.
    """
    (x0, y0), (x1, y1) = wall.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if run <= 0.0:
        return 0.0
    dx, dy = (x1 - x0) / run, (y1 - y0) / run
    nx, ny = -dy, dx
    offsets = [(x - x0) * nx + (y - y0) * ny for layer in row for x, y in layer.polygon]
    if not offsets:
        return 0.0
    side = 1.0 if sum(offsets) / len(offsets) > 0.0 else -1.0
    reach = max(side * offset for offset in offsets) + _PROBE_M
    top = max(wall.top_z0_m or wall.z1_m, wall.top_z1_m or wall.z1_m)
    pad = reach + _PROBE_M
    box = (min(x0, x1) - pad, min(y0, y1) - pad, max(x0, x1) + pad, max(y0, y1) + pad)
    near = [(face, prepared) for face, prepared, z0, z1 in rooms
            if min(top, z1) - max(wall.z0_m, z0) > _MIN_Z_OVERLAP_M
            and face.bounds[0] <= box[2] and face.bounds[2] >= box[0]
            and face.bounds[1] <= box[3] and face.bounds[3] >= box[1]]
    if not near:
        return 0.0
    count = max(3, int(run / _STATION_M))
    hits = 0
    for i in range(count):
        t = (i + 0.5) / count * run
        probe = Point(x0 + dx * t + nx * side * reach, y0 + dy * t + ny * side * reach)
        if any(prepared.contains(probe) for _, prepared in near):
            hits += 1
    return hits / count

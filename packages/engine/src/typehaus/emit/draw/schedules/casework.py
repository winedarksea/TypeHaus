"""A-607 — casework and countertops (I1-106): the build-up a cabinet installer and a slab
yard read, off the same records ``haus countertops`` cuts from.

Tops come from ``takeoff/stone_pieces.fabricated_pieces`` (size, cutouts, holes, support)
and the resolved slab (overhang, cantilever); heights are above the room's FINISHED floor
(``room_finished_floor_elevation``), the datum every "36 AFF" in a casework note means.
Casework is, in each room holding a top, every countertop host, every fixed floor cabinet
(``FurnitureType.work_surface`` stated) and every wall-hung storage box; loose furniture and
closet fit-outs elsewhere are not on this sheet.
"""

from __future__ import annotations

from collections import Counter

from typehaus.emit.draw.schedules.paged_tables import PagedTable, wrap_cells
from typehaus.emit.draw.schedules.structural import _write_paged
from typehaus.resolve.model import ResolvedModel

_M_TO_IN = 1.0 / 0.0254
_DASH = "-"
#: A storage box whose bottom stands this far over its floor is wall-hung, not loose.
_HUNG_IN = 12.0


def _in(value_m: float | None) -> str:
    from typehaus.takeoff.stone_pieces import inches_text

    return _DASH if value_m is None else inches_text(round(value_m * _M_TO_IN * 16) / 16)


def has_casework_schedule(model: ResolvedModel) -> bool:
    return bool(model.countertops)


def _types(model: ResolvedModel) -> dict:
    lib = model.plan.library
    return {t.tag: t for name in ("furniture_types", "fixture_types", "appliance_types")
            for t in getattr(lib, name)}


def _floors(model: ResolvedModel) -> dict[str, float]:
    """Room tag -> finished-floor elevation (m)."""
    from typehaus.resolve.room_floor import room_finished_floor_elevation

    return {room.tag: room_finished_floor_elevation(model, room) for room in model.rooms}


def countertop_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    """Tag, room, material, thickness, L x D, top/underside AFF, overhang, support, openings."""
    from typehaus.resolve.geometry_countertops import countertop_top_z
    from typehaus.takeoff.stone_pieces import fabricated_pieces

    floors = _floors(model)
    # A milled top (ash, poplar) is not a slab-yard piece; it still has a row here.
    pieces = {piece.tag: piece for piece in fabricated_pieces(model) if piece.kind == "top"}
    materials = {item.tag: item for item in model.plan.library.materials}
    rows = []
    for top in sorted(model.countertops, key=lambda item: item.tag):
        piece = pieces.get(top.tag)
        z1 = countertop_top_z(model, top)
        floor = floors.get(top.room or "")
        aff = None if z1 is None or floor is None else z1 - floor
        cantilever = (f"{_in(top.unsupported_overhang_m)} on {top.support}"
                      if top.unsupported_overhang_m > top.overhang_m + 1e-6 else _DASH)
        labels = Counter([c.label for c in piece.cutouts]
                         + [f"{_in(h.diameter_in / _M_TO_IN)} {h.purpose}"
                            for h in piece.holes]) if piece is not None else Counter()
        openings = "; ".join(f"{n} x {text}" if n > 1 else text for text, n in labels.items())
        material = getattr(materials.get(top.material_ref), "name", top.material_ref)
        support = piece.support if piece is not None else ""
        rows.append((top.tag, top.room or top.storey, material,
                     _in(top.thickness_m), f"{_in(top.length_m)} x {_in(top.depth_m)}",
                     _in(aff), _in(None if aff is None else aff - top.thickness_m),
                     _in(top.overhang_m), cantilever, support or _DASH,
                     openings or _DASH))
    return tuple(rows)


def casework_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    """One row per box: tag, room, type, W x D x H, bottom/top AFF, the top it carries."""
    types, floors = _types(model), _floors(model)
    under = {host: top.tag for top in model.countertops for host in top.hosts}
    rooms = {top.room for top in model.countertops}
    rows = []
    for obj in model.canvas_objects:
        kind = types.get(obj.type_ref or "")
        floor = floors.get(obj.room or "")
        if kind is None or floor is None or obj.body_z0_m is None or obj.room not in rooms:
            continue
        hung = (getattr(kind, "storage", False)
                and (obj.body_z0_m - floor) * _M_TO_IN > _HUNG_IN)
        fixed = obj.kind == "Furniture" and getattr(kind, "work_surface", None) is not None
        if obj.tag not in under and not (obj.kind == "Furniture" and (fixed or hung)):
            continue
        width, depth = (d.meters for d in kind.footprint)
        size = f"{_in(width)} x {_in(depth)} x {_in(kind.height.meters)}"
        top = None if obj.body_z1_m is None else obj.body_z1_m - floor
        rows.append((obj.room or obj.storey, obj.tag, kind.name, size,
                     _in(obj.body_z0_m - floor), _in(top), under.get(obj.tag, _DASH)))
    rows.sort(key=lambda r: (r[0], r[6] == _DASH, r[6], r[1]))
    return tuple((tag, room, name, size, z0, z1, top)
                 for room, tag, name, size, z0, z1, top in rows)


def casework_tables(model: ResolvedModel) -> list[PagedTable]:
    return [
        PagedTable("COUNTERTOP SCHEDULE (HEIGHTS ABOVE FINISHED FLOOR)",
                   ("Tag", "Room", "Material", "Thick.", "L x D", "Top", "Underside",
                    "Front ovh.", "Cantilever", "Support", "Cutouts / holes"),
                   wrap_cells(countertop_rows(model), {2: 20, 9: 26, 10: 26})),
        PagedTable("CASEWORK SCHEDULE (HEIGHTS ABOVE FINISHED FLOOR)",
                   ("Tag", "Room", "Type", "W x D x H", "Bottom", "Top", "Under top"),
                   wrap_cells(casework_rows(model), {2: 28})),
    ]


def write_casework_schedule(pdf, model: ResolvedModel, number: str, name: str, *,
                            page: int = 0) -> None:
    _write_paged(pdf, model, number, name, casework_tables(model), page)

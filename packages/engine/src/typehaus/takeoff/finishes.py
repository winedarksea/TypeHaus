"""Floor finishes by the square foot — the other half of making a finish real.

``Room.floor_finish`` renders now (``ui/src/three/builders/structure.ts::buildRoomFloor``,
``emit/gltf/palette.py::_room_floor_color``). This is what makes it *orderable*: one row per
finish, house-wide, resolved against the ``library/materials.py`` entries the finish strings
name — the same single definition the viewer and the export read, so a finish cannot look
right and bill wrong.

Two things this does that a bare ``sum(room.area_m2)`` would not:

* **Waste.** Plank and tile are cut to the room, and bare polygon area under-orders every
  time. The row shape follows ``sheet_goods_takeoff``'s precedent — a net area and an
  order quantity beside it — rather than inventing a second convention.
* **UNKNOWN rows.** A room whose finish is unauthored, or whose finish names no library
  material, gets an explicit row naming the rooms. Silently billing zero is how a typo'd
  finish string survives: it renders as bare deck and bills as nothing, and neither says so.
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.resolve.model import ResolvedModel

_M2_TO_FT2 = 10.7639104

# Per-finish waste, as a fraction of net area. These are ordering allowances, not physics:
# a finish cut to a room's shape needs more material than the room's polygon.
#
# Tile carries the most: every perimeter cut is scrap, and a box is written off for
# breakage on any real job. Sealed concrete carries none — it is a sealer measured by
# coverage rate, not a covering cut to fit, so there is nothing to waste at an edge.
_WASTE: dict[str, float] = {
    "carpet": 0.10,
    "oak": 0.10,
    "lvp": 0.10,
    "rubber": 0.10,
    "tile": 0.15,
    "sealed-concrete": 0.0,
}
_DEFAULT_WASTE = 0.10

# The layer a finish implies under it. ``Material`` has no field for this — adding one would
# mean a schema change for a fact only an estimator needs — so the relationship lives here,
# beside the waste factors it keeps company with. Each companion must exist in the library
# or its row reports UNKNOWN like any other missing material.
_COMPANIONS: dict[str, str] = {
    "carpet": "carpet-pad",
    "lvp": "lvp-underlayment",
}


def _order_area(net_ft2: float, waste: float) -> float:
    """Net area plus waste, rounded up to the whole square foot an estimator orders in."""
    return float(math.ceil(net_ft2 * (1.0 + waste) - 1e-9))


def floor_finish_rows(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per floor finish, house-wide, plus the companion layers each implies.

    Covers every storey — rooms are resolved house-wide, and a finishes schedule that
    stopped at one floor would be missing most of the order. In-room ``FinishZone``
    overrides bill as their own material and are subtracted from the room's field finish,
    so a tile inlay is not paid for twice.
    """
    materials = {material.tag: material for material in model.plan.library.materials}
    areas: dict[str, float] = defaultdict(float)
    rooms_by_finish: dict[str, list[str]] = defaultdict(list)
    unfinished: list[str] = []

    for room in model.rooms:
        zone_area = sum(zone.area_m2 for zone in room.finish_zones)
        for zone in room.finish_zones:
            areas[zone.material_ref] += zone.area_m2
            rooms_by_finish[zone.material_ref].append(room.tag)
        field_area = max(room.area_m2 - zone_area, 0.0)
        if not room.floor_finish:
            if field_area > 0.0:
                unfinished.append(room.tag)
                areas["\0unfinished"] += field_area
            continue
        areas[room.floor_finish] += field_area
        rooms_by_finish[room.floor_finish].append(room.tag)

    rows: list[dict[str, object]] = []
    for finish in sorted(key for key in areas if key != "\0unfinished"):
        net_ft2 = areas[finish] * _M2_TO_FT2
        material = materials.get(finish)
        waste = _WASTE.get(finish, _DEFAULT_WASTE)
        rows.append({
            "finish": finish,
            "material": material.name if material is not None else "UNKNOWN",
            "known": material is not None,
            # A coating (sealer, stain) bills by coverage area and has no plane of its own —
            # the renderers skip drawing it, and this flag is what says the row is a coating
            # rather than a covering laid over the deck.
            "coating": bool(material is not None and material.coating),
            "net_area_sqft": round(net_ft2, 1),
            "waste_pct": round(waste * 100.0, 1),
            "order_area_sqft": _order_area(net_ft2, waste),
            "rooms": sorted(set(rooms_by_finish[finish])),
        })
        companion = _COMPANIONS.get(finish)
        if companion is None:
            continue
        companion_material = materials.get(companion)
        rows.append({
            "finish": companion,
            "material": (companion_material.name if companion_material is not None
                         else "UNKNOWN"),
            "known": companion_material is not None,
            "coating": False,
            "net_area_sqft": round(net_ft2, 1),
            # A pad or underlayment is roll goods laid under the covering: it is cut to the
            # room the same way, so it carries the covering's own waste.
            "waste_pct": round(waste * 100.0, 1),
            "order_area_sqft": _order_area(net_ft2, waste),
            "rooms": sorted(set(rooms_by_finish[finish])),
            "under": finish,
        })

    if unfinished:
        rows.append({
            "finish": None,
            "material": "UNKNOWN",
            "known": False,
            "coating": False,
            "net_area_sqft": round(areas["\0unfinished"] * _M2_TO_FT2, 1),
            "waste_pct": 0.0,
            "order_area_sqft": 0.0,
            "rooms": sorted(set(unfinished)),
        })
    return rows

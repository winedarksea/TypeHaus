"""Interior trim by the lineal foot: base runs and door casings (→ resolve/interior_trim.py).

The ``room_perimeter_lf`` a trim lump was always waiting for. One row per (kind, room,
material). ``kind`` is ``baseboard`` / ``door casing`` for boards, ``tile base`` /
``flash cove`` for a base the floor trade makes from the floor itself.

``item`` is the price key: the board's stock tag for a board, ``tile-base`` / ``flash-cove``
otherwise, since those are billed by the trade per LF whatever the floor is. ``material``
stays the true material. A custom-milled board is listed again as rough stock in
``hardwood`` (``haus millwork``), which is an unpriced view, so nothing bills twice.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.model import ResolvedModel

_FT = 0.3048
_KIND = {"trim": "baseboard", "tile": "tile base", "integral_cove": "flash cove"}
_ITEM = {"tile": "tile-base", "integral_cove": "flash-cove"}


def interior_trim_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    names = {m.tag: m.name for m in model.plan.library.materials}
    length: dict[tuple, float] = defaultdict(float)
    pieces: dict[tuple, int] = defaultdict(int)
    inside: dict[tuple, int] = defaultdict(int)
    outside: dict[tuple, int] = defaultdict(int)
    tags: dict[tuple, list[str]] = defaultdict(list)
    for run in model.base_runs:
        key = (_KIND.get(run.kind, run.kind), run.room, run.material_ref,
               _ITEM.get(run.kind, run.material_ref))
        length[key] += run.length_m
        pieces[key] += 1
        # Each corner joins two pieces; counting only the end that arrives counts it once.
        inside[key] += run.end_corner == "inside"
        outside[key] += run.end_corner == "outside"
        tags[key].append(run.room)
    for casing in model.door_casings:
        key = ("door casing", casing.room, casing.material_ref, casing.material_ref)
        length[key] += sum(piece.length_m for piece in casing.pieces)
        pieces[key] += len(casing.pieces)
        tags[key].extend((casing.room, casing.opening_ref))
    return [{
        "kind": kind, "room": room, "material": material, "item": item,
        "description": f"{kind.capitalize()}, {names.get(material, material)} — {room}",
        "length_ft": round(length[key] / _FT, 2),
        "pieces": pieces[key],
        "inside_corners": inside[key], "outside_corners": outside[key],
        # Plan elements — the room, and each cased door — so a row lands on its storey's
        # work package; the derived BASE-/CASING- records are not plan elements.
        "tags": sorted(set(tags[key])),
    } for key in sorted(length) for kind, room, material, item in (key,)]

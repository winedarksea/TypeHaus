"""Interior trim by the lineal foot: base runs and door casings (→ resolve/interior_trim.py).

The ``room_perimeter_lf`` a trim lump was always waiting for. One row per (kind, room,
material). ``kind`` is ``baseboard`` / ``door casing`` for boards, ``tile base`` /
``flash cove`` for a base the floor trade makes from the floor itself, ``resilient base`` for
a set-on rubber cove base.

``item`` is the price key: the board's stock tag for a board, ``tile-base`` / ``flash-cove`` /
``resilient-base``
otherwise, since those are billed by the trade per LF whatever the floor is. ``material``
stays the true material. A custom-milled board is listed again as rough stock in
``hardwood`` (``haus millwork``), which is an unpriced view, so nothing bills twice.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.doors import door_installation_rows

_FT = 0.3048
_KIND = {"trim": "baseboard", "tile": "tile base", "integral_cove": "flash cove",
         "resilient_base": "resilient base"}
_ITEM = {"tile": "tile-base", "integral_cove": "flash-cove", "resilient_base": "resilient-base"}


def interior_trim_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    names = {m.tag: m.name for m in model.plan.library.materials}
    length: dict[tuple, float] = defaultdict(float)
    pieces: dict[tuple, int] = defaultdict(int)
    inside: dict[tuple, int] = defaultdict(int)
    outside: dict[tuple, int] = defaultdict(int)
    tags: dict[tuple, list[str]] = defaultdict(list)
    cuts: dict[tuple, list[dict]] = defaultdict(list)
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
    for band in model.panelings:
        for board in band.trim_pieces:
            # Stock width is part of the price key: 1x3 battens and 1x4 rails are
            # different purchased boards even when the species and finish match.
            item = board.material_ref
            key = (board.kind, band.room, board.material_ref, item)
            length[key] += board.length_m
            pieces[key] += 1
            tags[key].extend((band.room, band.tag))
            cuts[key].append({"length_in": round(board.length_m / 0.0254, 3),
                              "width_in": round(board.width_m / 0.0254, 3),
                              "thickness_in": round(board.thickness_m / 0.0254, 3)})
    rows = [{
        "kind": kind, "room": room, "material": material, "item": item,
        "description": f"{kind.capitalize()}, {names.get(material, material)} — {room}",
        "length_ft": round(length[key] / _FT, 2),
        "pieces": pieces[key],
        "inside_corners": inside[key], "outside_corners": outside[key],
        # Plan elements — the room, and each cased door — so a row lands on its storey's
        # work package; the derived BASE-/CASING- records are not plan elements.
        "tags": sorted(set(tags[key])),
        **({"cut_pieces": cuts[key]} if cuts[key] else {}),
    } for key in sorted(length) for kind, room, material, item in (key,)]
    return rows + door_installation_rows(model)

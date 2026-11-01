"""Interior trim by the lineal foot: base runs and door casings (→ resolve/interior_trim.py).

The ``room_perimeter_lf`` a trim lump was always waiting for. One row per (kind, room,
material). ``kind`` is ``baseboard`` / ``door casing`` for boards, ``tile base`` /
``flash cove`` for a base the floor trade makes from the floor itself, ``resilient base`` for
a set-on rubber cove base, ``stair skirt`` for a skirted flight's raked boards (its ``room``
the stair), ``base joint`` for the sealant bead at the toe of any base whose
floor names a ``Material.base_joint_ref`` (billed by the LF of base, keyed by the sealant),
``door jamb rip`` / ``door jamb extension`` for a stock jamb cut down to, or built out to, a
non-stock wall (``DoorSizing.jamb_depth_m``; item ``door-jamb-rip`` / ``door-jamb-extension``).

``item`` is the price key: the board's stock tag for a board, ``tile-base`` / ``flash-cove`` /
``resilient-base``
otherwise, since those are billed by the trade per LF whatever the floor is. ``material``
stays the true material. A custom-milled board is listed again as rough stock in
``hardwood`` (``haus millwork``), which is an unpriced view, so nothing bills twice.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.doors import door_installation_rows

_FT = 0.3048
_KIND = {"trim": "baseboard", "tile": "tile base", "integral_cove": "flash cove",
         "resilient_base": "resilient base"}
_ITEM = {"tile": "tile-base", "integral_cove": "flash-cove", "resilient_base": "resilient-base"}


def interior_trim_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    materials = {m.tag: m for m in model.plan.library.materials}
    names = {tag: m.name for tag, m in materials.items()}
    floors = {room.tag: room.floor_finish for room in model.rooms}
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
        joint = getattr(materials.get(floors.get(run.room) or ""), "base_joint_ref", None)
        if joint:
            key = ("base joint", run.room, joint, joint)
            length[key] += run.length_m
            pieces[key] += 1
            tags[key].append(run.room)
    for casing in model.door_casings:
        key = ("door casing", casing.room, casing.material_ref, casing.material_ref)
        length[key] += sum(piece.length_m for piece in casing.pieces)
        pieces[key] += len(casing.pieces)
        tags[key].extend((casing.room, casing.opening_ref))
    for stair in model.stairs:
        for board in (m for m in stair.members if m.category == "stair_skirt"):
            # Billed by the raked blank, long point to long point.
            key = ("stair skirt", stair.tag, board.material, board.material)
            length[key] += board.cut_length_m
            pieces[key] += 1
            tags[key].append(stair.tag)
            cuts[key].append({"length_in": round(board.cut_length_m / 0.0254, 3),
                              "width_in": round(cross_section(board.profile).depth_m / 0.0254, 3),
                              "thickness_in": round(board.plan_width_m / 0.0254, 3)})
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
    _jamb_rows(model, length, pieces, tags, cuts)
    stock = _skirt_stock(model, cuts)
    rows = [{
        "kind": kind, "room": room, "material": material, "item": item,
        "description": f"{kind.capitalize()}, {names.get(material, material)}"
                       + (f" — {room}" if room else ""),
        "length_ft": round(length[key] / _FT, 2),
        "pieces": pieces[key],
        "inside_corners": inside[key], "outside_corners": outside[key],
        # Plan elements — the room, and each cased door — so a row lands on its storey's
        # work package; the derived BASE-/CASING- records are not plan elements.
        "tags": sorted(set(tags[key])),
        **({"cut_pieces": cuts[key]} if cuts[key] else {}),
        **stock.get(key, {}),
    } for key in sorted(length) for kind, room, material, item in (key,)]
    return rows + door_installation_rows(model)


def _jamb_rows(model: ResolvedModel, length, pieces, tags, cuts) -> None:
    """A stock jamb ripped to a shallower wall, or extended to a deeper one: legs + head."""
    from typehaus.resolve.door_floor_finish import trim_standard_of

    standard = trim_standard_of(model.plan)
    if standard is None:
        return
    # The painted base stock, as an exterior door's interior extension is.
    material = standard.base_material_ref or standard.material_ref
    for opening in model.openings:
        sizing = opening.sizing
        if sizing is None:
            continue
        a = sizing.jamb_allowance_m
        run = 2 * (sizing.rough_h_m - sizing.floor_finish_m - a) + sizing.rough_w_m - 2 * a
        for kind, width in (("door jamb rip", sizing.jamb_rip_m),
                            ("door jamb extension", sizing.jamb_extension_m)):
            if width <= 1e-6:
                continue
            key = (kind, None, material, kind.replace(" ", "-"))
            length[key] += run
            pieces[key] += 3
            tags[key].append(opening.tag)
            cuts[key].append({"length_in": round(run / 0.0254, 3),
                              "width_in": round(width / 0.0254, 3)})


def _skirt_stock(model: ResolvedModel, cuts) -> dict[tuple, dict[str, object]]:
    """The boards each skirt row's raked blanks are cut from (``TrimStandard.stocks``)."""
    from typehaus.resolve.door_floor_finish import trim_standard_of
    from typehaus.takeoff.stock_packing import boards_for

    standard = trim_standard_of(model.plan)
    out = {}
    for key, pieces in cuts.items():
        stock = standard.stock_length_for(key[2]) if standard is not None else None
        if key[0] != "stair skirt" or stock is None:
            continue
        boards, _board_in, _splices = boards_for([p["length_in"] for p in pieces],
                                                stock.inches)
        out[key] = {"stock_length_in": round(stock.inches, 3), "stock_boards": boards}
    return out

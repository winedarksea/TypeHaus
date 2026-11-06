"""The room finish schedule, the wall tile, and the trim pack.

Flooring and tile read one room finish schedule: net area per room and finish (each sub
adds its own waste; the model's own waste fraction is stated beside it), what goes under
it, and the base. The trim pack packs base and casing into the house's ``TrimStandard``
stock length through ``stock_packing.boards_for``, the packer the stair skirt already uses.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.quantities import M_PER_IN
from typehaus.takeoff.bid_summaries import SummaryInputs, SummaryTable, ft, sqft

#: Interior trim kinds outside the finish carpenter's pack: the exterior door approach and
#: casing go with the door, the toe sealant with the floor.
_NOT_TRIM = ("exterior door approach", "exterior door casing", "base joint")


def millwork_summary(inputs: SummaryInputs) -> list[SummaryTable]:
    from typehaus.takeoff.summary_openings import hardware_sets, interior_door_schedule

    return [interior_door_schedule(inputs), trim_pack(inputs), hardware_sets(inputs)]


def flooring_summary(inputs: SummaryInputs) -> list[SummaryTable]:
    return [room_finish_schedule(inputs)]


def tile_summary(inputs: SummaryInputs) -> list[SummaryTable]:
    return [room_finish_schedule(inputs), wall_tile(inputs)]


def room_finish_schedule(inputs: SummaryInputs) -> SummaryTable:
    model = inputs.model
    materials = {m.tag: m for m in model.plan.library.materials}
    order = {s.tag: i for i, s in enumerate(model.plan.storeys)}
    base: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for run in model.base_runs:
        base[run.room][run.material_ref] += run.piece.length_m
    rows = []
    for room in sorted(model.rooms, key=lambda r: (order.get(r.storey, 99), r.tag)):
        parts = ([(room.floor_finish, room.field_area_m2)] if room.floor_finish else [])
        parts += [(zone.material_ref, zone.area_m2) for zone in room.finish_zones]
        for index, (finish, area) in enumerate(parts):
            material = materials.get(finish)
            waste = getattr(material, "floor_waste_fraction", None)
            under = ", ".join(_name(materials, ref)
                              for ref in getattr(material, "floor_companion_refs", ()) or ())
            room_base = base.get(room.tag, {}) if index == 0 else {}
            rows.append((room.tag, room.storey, _name(materials, finish), sqft(area),
                         f"{round(waste * 100):g}%" if waste else "—", under or "—",
                         ", ".join(_name(materials, ref) for ref in sorted(room_base)) or "—",
                         ft(sum(room_base.values()))))
    return SummaryTable(
        "room-finishes", "Room finish schedule",
        ("Room", "Storey", "Floor finish", "Net SF", "Model waste", "Under", "Base", "Base LF"),
        tuple(rows),
        ("Net SF is the finished field, net of cabinets and voids; add your own waste. Model "
         "waste is what the estimate orders. A second line in a room is an inlay or zone.",
         "Tile size and grout are in the finish name; pattern and waterproofing method are "
         "not modelled — state what you priced."))


def wall_tile(inputs: SummaryInputs) -> SummaryTable:
    from typehaus.emit.trade_rules import material_trade

    model = inputs.model
    materials = {m.tag: m for m in model.plan.library.materials}
    areas: dict[tuple[str, str], float] = defaultdict(float)
    for paneling in model.panelings:
        if material_trade(paneling.material_ref) == "tile":
            areas[(paneling.room or "—", paneling.material_ref)] += paneling.area_m2
    return SummaryTable("wall-tile", "Wall tile", ("Room", "Tile", "Net SF"),
                        tuple((room, _name(materials, ref), sqft(area))
                              for (room, ref), area in sorted(areas.items())),
                        ("Net of openings. Shower walls without modelled tile are in the "
                         "owner's wall-tile allowance.",))


def trim_pack(inputs: SummaryInputs) -> SummaryTable:
    from typehaus.resolve.door_floor_finish import trim_standard_of
    from typehaus.takeoff.interior_trim import interior_trim_takeoff
    from typehaus.takeoff.stock_packing import boards_for

    model = inputs.model
    materials = {m.tag: m for m in model.plan.library.materials}
    standard = trim_standard_of(model.plan)
    totals: dict[tuple[str, str], list] = defaultdict(lambda: [0.0, 0, 0, 0, None])
    for row in interior_trim_takeoff(model):
        kind = str(row["kind"])
        if kind in _NOT_TRIM:
            continue
        entry = totals[(kind, str(row["material"]))]
        entry[0] += float(row["length_ft"])
        entry[1] += int(row.get("pieces") or 0)
        entry[2] += int(row.get("inside_corners") or 0)
        entry[3] += int(row.get("outside_corners") or 0)
        if row.get("stock_boards"):
            entry[4] = (int(row["stock_boards"]), float(row["stock_length_in"]))
    # Base boards and casing are cut from stock here; the skirt packs itself already.
    cuts: dict[tuple[str, str], list[float]] = defaultdict(list)
    for run in model.base_runs:
        if run.kind == "trim":
            cuts[("baseboard", run.material_ref)].append(run.piece.length_m / M_PER_IN)
    for casing in model.door_casings:
        cuts[("door casing", casing.material_ref)].extend(
            piece.length_m / M_PER_IN for piece in casing.pieces)
    for key, lengths in cuts.items():
        stock = standard.stock_length_for(key[1]) if standard is not None else None
        if key in totals and lengths and stock is not None:
            boards, length_in, _splices = boards_for(lengths, stock.inches)
            totals[key][4] = (boards, length_in)
    rows = []
    for (kind, material), (lf, pieces, inside, outside, stock) in sorted(totals.items()):
        boards, length_in = stock if stock is not None else ("—", None)
        rows.append((kind, _name(materials, material), round(lf, 1),
                     f"{length_in / 12:g}'" if length_in else "—", boards, pieces,
                     inside, outside))
    return SummaryTable(
        "trim-pack", "Trim pack", ("Item", "Material", "LF", "Stock", "Sticks", "Cut pieces",
                                   "Inside corners", "Outside corners"), tuple(rows),
        ("Sticks are the cut pieces packed into the house's stock length, splices where a "
         "wall is longer than a stick; no other waste.",))


def _name(materials: dict, ref: str | None) -> str:
    material = materials.get(ref or "")
    return material.name if material is not None else (ref or "—")

"""The roofer's five numbers, the siding sub's squares by elevation, the board hanger's
sheets by storey.

Wall areas are ``envelope.wall_layer_areas`` — the same per-wall yields
``envelope_layer_takeoff`` sums — so a split always adds back to the BOM's total. Roof
lengths are the resolved edge runs in 3D, less any run another roof continues across.
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.quantities import M_PER_FT, M_PER_IN
from typehaus.takeoff.bid_summaries import SummaryInputs, SummaryTable, ft, sqft
from typehaus.takeoff.labels import _fraction_in

_FACINGS = ("north", "east", "south", "west")
#: Ceiling-height bands a drywall sub prices by: lifts and scaffold start over 9' and 10'.
_BANDS = ((9.0, "up to 9'"), (10.0, "9' to 10'"), (math.inf, "over 10'"))


def roofing_summary(inputs: SummaryInputs) -> list[SummaryTable]:
    from typehaus.resolve.roof_edge_geometry import (
        abutted_run_keys,
        roof_edge_runs,
        roof_ridge_run,
    )

    model = inputs.model
    pitches = {e.tag: e.pitch for e in model.plan.all_elements() if e.element_kind == "Roof"}
    rows, weighted = [], defaultdict(float)
    totals = [0.0] * 4
    for roof in sorted(model.roofs, key=lambda r: r.tag):
        seams = abutted_run_keys(model, roof)
        eave = rake = 0.0
        for run in roof_edge_runs(roof):
            if run.key in seams:
                continue
            length = math.dist((*run.p0, run.z0_m), (*run.p1, run.z1_m))
            eave, rake = (eave + length, rake) if run.is_eave else (eave, rake + length)
        ridge_run = roof_ridge_run(roof)
        ridge = math.dist(ridge_run.p0, ridge_run.p1) if ridge_run is not None else 0.0
        pitch = pitches.get(roof.tag)
        pitch_text = f"{pitch.rise / pitch.run * 12:g}/12" if pitch is not None else "—"
        area = sqft(roof.surface_area_m2)
        weighted[pitch_text] += area
        for index, value in enumerate((area, eave, rake, ridge)):
            totals[index] += value
        rows.append((roof.tag, roof.form, pitch_text, area, round(area / 100, 2), ft(eave),
                     ft(rake), ft(ridge), 0.0, 0.0))
    if rows:
        predominant = max(sorted(weighted), key=lambda p: weighted[p])
        rows.append(("Total", "", f"{predominant} predominant", round(totals[0], 1),
                     round(totals[0] / 100, 2), ft(totals[1]), ft(totals[2]), ft(totals[3]),
                     0.0, 0.0))
    return [SummaryTable(
        "roof-geometry", "Roof geometry",
        ("Roof", "Form", "Pitch", "Sloped SF", "Squares", "Eave LF", "Rake LF", "Ridge LF",
         "Hip LF", "Valley LF"), tuple(rows),
        ("Sloped area is the deck out to the fascia, net of nothing. Rake length is measured "
         "up the slope. The roof vocabulary is gable and shed, so there are no hips or "
         "valleys; an edge where one roof continues into another is not counted.",))]


def siding_summary(inputs: SummaryInputs) -> list[SummaryTable]:
    model = inputs.model
    names = _material_names(model)
    areas: dict[tuple[str, str], float] = defaultdict(float)
    for wall, layer, (_scope, function, material, _t), area in _wall_layers(model):
        if function == "cladding":
            areas[(names.get(material, material), _facing(wall, layer))] += area
    rows = [(material, facing, sqft(area), round(sqft(area) / 100, 2))
            for (material, facing), area in sorted(
                areas.items(), key=lambda kv: (kv[0][0], _FACINGS.index(kv[0][1])))]
    total = sqft(sum(areas.values()))
    if rows:
        rows.append(("Total", "", total, round(total / 100, 2)))
    trim = [(line.description, line.quantity, line.unit)
            for group in getattr(inputs.packages.get("siding"), "groups", ())
            for line in group.lines if line.section in ("edge_trim", "cladding_trim")]
    return [
        SummaryTable("elevations", "Cladding by elevation", ("Material", "Elevation",
                     "Net SF", "Squares"), tuple(rows),
                     ("Net of openings; elevations are the drawing set's (plan north), "
                      "named for the way the wall faces.",)),
        SummaryTable("trim", "Trim and accessories", ("Item", "Quantity", "Unit"),
                     tuple(trim), ("Corners, starter, opening trim, base flashing, soffit "
                                   "and fascia as the detailed BOM bills them.",)),
    ]


def drywall_summary(inputs: SummaryInputs) -> list[SummaryTable]:
    from typehaus.resolve.drywall_led import drywall_standard
    from typehaus.resolve.sheet_stock import (
        layer_sheet_length_in,
        order_sheet_length_in,
        sheet_label,
        sheets_for,
        wall_layer,
    )
    from typehaus.takeoff.ceiling_areas import ceiling_area_m2, ceiling_pieces

    model = inputs.model
    plan = model.plan
    gypsum = {m.tag for m in plan.library.materials if getattr(m, "gypsum_type", None)}
    names = _material_names(model)
    order = {s.tag: i for i, s in enumerate(plan.storeys)}
    board: dict[tuple[str, str, str, float, float], float] = defaultdict(float)
    for wall, layer, (_scope, _f, material, thickness), area in _wall_layers(model):
        if material in gypsum:
            length = order_sheet_length_in(layer_sheet_length_in(
                wall_layer(plan, plan.by_tag(wall.tag), layer.name)))
            board[(wall.storey, "walls", material, thickness, length)] += area
    ceiling_areas: dict[str, float] = defaultdict(float)
    for ceiling in model.ceilings:
        ceiling_areas[ceiling.room_ref] += ceiling_area_m2(model, ceiling)
    # The BOM's own walk, so a hall no Room claims is board here too.
    for piece in ceiling_pieces(model):
        for layer in piece.layers:
            if layer.material_ref in gypsum:
                board[(piece.storey, "ceilings", layer.material_ref, layer.thickness.meters,
                       order_sheet_length_in(layer_sheet_length_in(layer)))] += piece.area_m2
    rows = []
    for (storey, surface, material, thickness, length), area in sorted(
            board.items(), key=lambda kv: (order.get(kv[0][0], 99), *kv[0][1:])):
        rows.append((storey, surface, names.get(material, material),
                     _fraction_in(thickness / M_PER_IN), sqft(area),
                     sheets_for(sqft(area), length), sheet_label(length)))
    total = sqft(sum(board.values()))
    rows.append(("Total", "", "", "", total, sum(int(row[5]) for row in rows), ""))

    bands: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    for room in model.rooms:
        if room.tag not in ceiling_areas:
            continue
        height = room.clear_height_m
        band = ("sloped (follows the roof)" if height is None else
                next(label for limit, label in _BANDS if height / M_PER_FT <= limit + 1e-6))
        bands[band][0] += 1
        bands[band][1] += ceiling_areas[room.tag]
    labels = [label for _limit, label in _BANDS] + ["sloped (follows the roof)"]
    standard, _findings = drywall_standard(plan)
    level = getattr(standard, "finish_level", None)
    return [
        SummaryTable("board", "Board by storey", ("Storey", "Surface", "Board", "Thickness",
                     "Net SF", "Sheets", "Sheet"), tuple(rows),
                     (f"Finish level: Level {level} (GA-214)." if level is not None else
                      "Finish level: not stated in the model; say which level you priced.",
                      "Net of openings, no waste. Sheets are area divided by sheet size.")),
        SummaryTable("ceiling-heights", "Ceiling heights",
                     ("Height", "Rooms", "Ceiling SF"),
                     tuple((label, int(bands[label][0]), sqft(bands[label][1]))
                           for label in labels if label in bands)),
    ]


def _wall_layers(model):
    from typehaus.takeoff.envelope import wall_layer_areas

    return wall_layer_areas(model)


def _material_names(model) -> dict[str, str]:
    return {m.tag: m.name for m in model.plan.library.materials}


def _facing(wall, layer) -> str:
    """Plan-north compass name of the side ``layer`` is on: the elevation it is drawn in."""
    from typehaus.resolve.geometry import wall_frame

    (x0, y0), _tangent, (nx, ny), _length = wall_frame(wall)
    layers = wall.depth_layers()

    def offset(ring) -> float:
        return sum((px - x0) * nx + (py - y0) * ny for px, py in ring) / max(len(ring), 1)

    sign = 1.0 if offset(layer.polygon) >= offset(layers[0].polygon) else -1.0
    angle = math.atan2(nx * sign, ny * sign)  # clockwise from plan north
    return _FACINGS[int((angle + math.pi / 4) // (math.pi / 2)) % 4]

"""Every envelope layer by the square foot, not just the sheathing.

``sheet_goods_takeoff`` bills exactly one layer function — SHEATHING — because that is what
comes in 4x8 sheets. Everything else in a wall or roof stack was resolved, drawn, and
thermally modelled, and then never ordered: the insulation, the drywall, the cladding, the
WRB. On this house that is most of the envelope by both area and cost.

This is deliberately a *second* section rather than an extension of ``sheet_goods``: a sheet
count is the right unit for plywood and the wrong one for a roll of housewrap or a lift of
mineral wool, and folding them together would force one unit onto products that are not
bought that way. Sheathing therefore appears in both, once as sheets and once as area, and
the sheathing rows here carry ``also_in_sheet_goods`` so a total cannot double-count it by
accident.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.model.enums import LayerFunction, TrimKind
from typehaus.resolve.accessories import (
    BUG_SCREEN_MATERIAL,
    rainscreen_cavity_m,
    screens_rainscreen_base,
)
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedWall

_M2_TO_FT2 = 10.7639104
_M_TO_FT = 3.280839895

# Layer functions that are a purchased covering with an area. STRUCTURE is deliberately
# absent and is *not* unbilled: a framed structure layer bills as members in `framing`, and
# a monolithic one (a pour, a masonry course) bills by area and cubic yards in
# `takeoff/wall_structure.py` — concrete is bought by the yard, not the square foot. That
# missing pointer is what let a whole basement's worth of concrete reach no order for
# months. AIRGAP and FURRING are not billable *here* either, for opposite reasons: an air
# gap is nothing at all, and furring is lineal-foot strapping, which the framing cut list
# now carries as real ``strapping`` members — laid out by `resolve/framing/furring.py` for
# every FURRING layer with a FramingSpec, monolithic walls included. That last clause is
# the whole point of the pass: until it existed the claim on this line was simply false,
# and W-B-CS's liner strapping over concrete was ordered by nobody.
_BILLABLE = (
    LayerFunction.INSULATION,
    LayerFunction.SHEATHING,
    LayerFunction.CLADDING,
    LayerFunction.MEMBRANE,
    LayerFunction.FINISH,
)


def wall_net_areas_m2(model: ResolvedModel) -> dict[str, float]:
    """Tag -> gross wall face (run x mean top height) less its openings, clamped at 0.

    Shared by :func:`envelope_layer_takeoff` and
    :func:`typehaus.takeoff.wall_structure.wall_structure_takeoff` so the covering and the
    thing it covers are measured off exactly the same face — a wall cannot bill 200 sf of
    drywall over 190 sf of concrete.
    """
    openings_by_wall: dict[str, float] = defaultdict(float)
    for opening in model.openings:
        openings_by_wall[opening.host_wall] += opening.width_m * opening.height_m

    areas: dict[str, float] = {}
    for wall in model.walls:
        run = length(sub(wall.axis[1], wall.axis[0]))
        mean_top = ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2.0
        gross = run * (mean_top - wall.z0_m)
        areas[wall.tag] = max(0.0, gross - openings_by_wall[wall.tag])
    return areas


def wall_layer_net_area_m2(model: ResolvedModel, wall: ResolvedWall,
                           layer: ResolvedLayer, wall_net_m2: float) -> float:
    """The net face one layer of ``wall`` actually covers.

    A full-height layer covers the whole wall face, which is ``wall_net_m2`` and needs no
    second calculation. A layer with a ``Layer.extent`` — a protection panel above grade,
    a splash course at the base — covers ``run x band height`` less only the openings that
    fall *inside its band*. Billing the wall's whole face for it would order the panel for
    every buried foot of foam it never reaches, which is the exact failure this exists to
    stop: catlin's parge coat was claimed full height over 9' of basement wall.

    The opening clip is the same one ``resolve/paneling.py`` runs for a wainscot band —
    intersect the opening's rectangle with the band and subtract — because it is the same
    question asked of a different band.
    """
    if not getattr(layer, "is_banded", False):
        return wall_net_m2
    band_z0, band_z1 = layer.band(wall)
    mean_top = ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2.0
    band_z1 = min(band_z1, mean_top)
    if band_z1 - band_z0 <= 0.0:
        return 0.0
    run: float = length(sub(wall.axis[1], wall.axis[0]))
    area = run * (band_z1 - band_z0)
    for opening in model.openings:
        if opening.host_wall != wall.tag:
            continue
        overlap = (min(band_z1, wall.z0_m + opening.sill_m + opening.height_m)
                   - max(band_z0, wall.z0_m + opening.sill_m))
        if overlap > 0.0:
            area -= opening.width_m * overlap
    return max(0.0, area)


def envelope_layer_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Net square feet per (scope, layer function, material, thickness).

    Wall areas are net of their openings, the same deduction ``sheet_goods_takeoff`` makes,
    so a wall that is mostly glass does not order a wall's worth of drywall.
    """
    areas: dict[tuple[str, str, str, float], float] = defaultdict(float)
    net_areas = wall_net_areas_m2(model)

    for wall in model.walls:
        net = net_areas[wall.tag]
        scope = "foundation wall" if wall.is_foundation else "wall"
        for layer in wall.layers:
            covered = wall_layer_net_area_m2(model, wall, layer, net)
            # A cavity layer shares the structure layer's polygon and adds no depth; billing
            # it as its own area would order insulation for a wall band twice.
            if getattr(layer, "is_cavity", False):
                areas[(scope, "insulation (cavity)", layer.material_ref,
                       layer.thickness_m)] += covered
                continue
            try:
                function = LayerFunction(layer.function)
            except ValueError:
                continue
            if function in _BILLABLE:
                areas[(scope, function.value, layer.material_ref,
                       layer.thickness_m)] += covered

    for roof in model.roofs:
        assembly = model.plan.library.resolve_assembly(roof.assembly)
        if assembly is None:
            continue
        for layer in assembly.layers:
            if layer.function in _BILLABLE:
                areas[("roof", layer.function.value, layer.material_ref,
                       layer.thickness.meters)] += roof.surface_area_m2

    return [
        {"scope": scope, "function": function, "material": material,
         "thickness_in": round(thickness / 0.0254, 3),
         "net_area_sqft": round(area * _M2_TO_FT2, 1),
         # Sheathing is the one function `sheet_goods_takeoff` also bills, in sheets. Flagged
         # so a caller summing both sections knows where the overlap is.
         "also_in_sheet_goods": function == LayerFunction.SHEATHING.value}
        for (scope, function, material, thickness), area in sorted(areas.items())
    ]


def bug_screen_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of rainscreen base vent/insect strip, grouped by cavity depth.

    The strip is stock extrusion cut to the cavity it closes, so the buying decision is
    "how many feet of the 3/4" section and how many of the 1/2"" — hence the grouping. It is
    billed off the *walls*, the same predicate the resolver derives the geometry from
    (:func:`typehaus.resolve.accessories.screens_rainscreen_base`), rather than off the emitted
    solids: the solid sweep in ``structural_solids_takeoff`` counts it too, but in cubic
    feet, which is not a unit anyone orders a vent strip in.
    """
    runs: dict[float, dict[str, object]] = {}
    for wall in model.walls:
        if not screens_rainscreen_base(model, wall):
            continue
        key = round(rainscreen_cavity_m(wall.depth_layers()) or 0.0, 4)
        row = runs.get(key)
        if row is None:
            row = runs[key] = {"category": TrimKind.BUG_SCREEN.value,
                               "material": BUG_SCREEN_MATERIAL,
                               "cavity_depth_in": round(key / 0.0254, 3),
                               "count": 0, "length_m": 0.0, "tags": []}
        row["count"] = int(row["count"]) + 1
        row["length_m"] = float(row["length_m"]) + length(sub(wall.axis[1], wall.axis[0]))
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(wall.tag)
    return [
        {"category": row["category"], "material": row["material"],
         "cavity_depth_in": row["cavity_depth_in"], "count": int(row["count"]),
         "length_ft": round(float(row["length_m"]) * _M_TO_FT, 1),
         "tags": sorted(row["tags"])}
        for row in (runs[key] for key in sorted(runs))
    ]

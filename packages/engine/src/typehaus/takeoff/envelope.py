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

A roof contributes rows on **two** planes and they are not interchangeable. Scope ``roof``
is the deck: sloped, and run out to the fascia, which is how roofing and underlayment are
bought. Scope ``roof ceiling`` is the plane under it — the assembly's ``default_lining``
and any layer's ``CavityFill`` — which stops at the bearing wall and, on a truss, lies flat.
Billing the second off the first is a 30% overstatement on catlin's garage alone.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.model.enums import LayerFunction, TrimKind
from typehaus.resolve.accessories import (
    BUG_SCREEN_MATERIAL,
    rainscreen_cavity_m,
    screens_rainscreen_base,
)
from typehaus.resolve.geometry import length, polygon_area, sub
from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedWall
from typehaus.resolve.roof_geometry import roof_ceiling_area_m2

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
#: Solid categories whose assembly layers bill here. Horizontal solids, all of them: their
#: STRUCTURE bills by the cubic yard in ``structural_solids`` and everything else by area.
_LAYERED_SOLID_SCOPES = ("slab", "footing", "pad")

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
    so a wall that is mostly glass does not order a wall's worth of drywall. Scopes are
    ``wall`` / ``foundation wall``, the roof's two planes (``roof`` the sloped deck,
    ``roof ceiling`` the plane under it), and the horizontal solids — ``slab``, ``footing``,
    ``pad`` — net of their openings.
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
        # Two planes, two areas. ``surface_area_m2`` is the sloped deck out to the fascia,
        # which is what the roofing, the deck and the underlayment are bought by. The
        # ceiling and its insulation stop at the bearing wall and, on a truss, lie flat —
        # that is ``roof_ceiling_area_m2``. None only when the roof resolves no bearing
        # line, which ``resolve_roof`` already rejects as an integrity ERROR, so a roof
        # that reaches this loop has one.
        ceiling_m2 = roof_ceiling_area_m2(model, roof)
        for roof_layer in assembly.layers:
            if roof_layer.function in _BILLABLE:
                areas[("roof", roof_layer.function.value, roof_layer.material_ref,
                       roof_layer.thickness.meters)] += roof.surface_area_m2
            # Cavity fill hangs off the STRUCTURE layer, which is never ``_BILLABLE`` — so
            # this cannot live inside the branch above, and for months it lived nowhere at
            # all: every rafter batt and every blown attic in the model reached no order.
            # Billed on the ceiling plane, not the deck, and with the wall path's exact
            # ``insulation (cavity)`` function so one material reads the same in both.
            fill = roof_layer.cavity
            if fill is not None and ceiling_m2 is not None:
                depth = fill.thickness if fill.thickness is not None else roof_layer.thickness
                areas[("roof ceiling", "insulation (cavity)", fill.material_ref,
                       depth.meters)] += ceiling_m2
        # ``default_lining`` is the ceiling: the gypsum under the chords, and whatever
        # finish is authored over it. Walls have picked their lining up since
        # ``resolve_wall`` began stacking ``default_lining + layers`` (resolve/topology.py);
        # roofs never went through that path, so a roof's lining was thermally modelled,
        # drawn in section, graded by the Glaser walk — and ordered by nobody.
        if ceiling_m2 is not None:
            for lining_layer in assembly.default_lining:
                if lining_layer.function in _BILLABLE:
                    areas[("roof ceiling", lining_layer.function.value,
                           lining_layer.material_ref,
                           lining_layer.thickness.meters)] += ceiling_m2

    # Slabs had the identical hole ``wall_structure.py`` names in so many words: a slab is a
    # ``ResolvedSolid``, ``structural_solids_takeoff`` bills its gross volume as concrete, and
    # every *other* layer of its assembly — below-slab XPS, an EPS stay-in-place deck form,
    # the furring rib, the gypsum thermal barrier under it — reached no order at all. Billed
    # on the plan outline net of its floor openings, which is the same net area
    # ``structural_solids_takeoff`` extrudes, so the covering and the pour cannot disagree
    # about how big the slab is. STRUCTURE stays out for the wall path's reason: concrete is
    # bought by the yard, and ``structural_solids`` already bills it.
    #
    # ``footing`` and ``pad`` are here for the same reason and were added the day a footing
    # could carry an assembly at all (2026-08-22). ``Footing`` had no assembly, no material
    # and no reinforcement, so there was never a non-structural layer on one to bill; the
    # moment there is — a frost-protected shallow footing bearing on 2" of 40 psi XPS — the
    # foam under it has to reach an order, and the slab loop was the only place that knew how
    # to bill a horizontal solid's covering.
    for solid in model.solids:
        if solid.category not in _LAYERED_SOLID_SCOPES or solid.assembly is None:
            continue
        assembly = model.plan.library.resolve_assembly(solid.assembly)
        if assembly is None:
            continue
        scope = solid.category
        net_m2 = max(0.0, abs(polygon_area(list(solid.outline)))
                     - sum(abs(polygon_area(list(void))) for void in solid.voids))
        for slab_layer in assembly.layers:
            if slab_layer.function in _BILLABLE:
                areas[(scope, slab_layer.function.value, slab_layer.material_ref,
                       slab_layer.thickness.meters)] += net_m2
            fill = slab_layer.cavity
            if fill is not None:
                depth = fill.thickness if fill.thickness is not None else slab_layer.thickness
                areas[(scope, "insulation (cavity)", fill.material_ref,
                       depth.meters)] += net_m2
        for lining_layer in assembly.default_lining:
            if lining_layer.function in _BILLABLE:
                areas[(scope, lining_layer.function.value, lining_layer.material_ref,
                       lining_layer.thickness.meters)] += net_m2

    return [
        {"scope": scope, "function": function, "material": material,
         "thickness_in": round(thickness / 0.0254, 3),
         "net_area_sqft": round(area * _M2_TO_FT2, 1),
         # Sheathing is the one function `sheet_goods_takeoff` also bills, in sheets. Flagged
         # so a caller summing both sections knows where the overlap is — but only for the
         # scopes that section actually walks. It walks walls, roofs and floor systems; it
         # has never walked a slab, so a slab's base course is billed here and nowhere else,
         # and flagging it as an overlap would point a reader at a row that does not exist.
         "also_in_sheet_goods": (function == LayerFunction.SHEATHING.value
                                 and scope != "slab")}
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

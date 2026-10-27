"""Authored edge runs — fascia, gutter, flashing, glazing trim — and downspouts as solids.

Split out of ``accessories.py``; the same plain :class:`ResolvedSolid` prisms in the shared IR.
"""

from __future__ import annotations

import math

from typehaus.model.enums import TrimKind
from typehaus.resolve.geometry import circle_outline, rect_between
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.round_solids import PIPE_FACETS as _PIPE_FACETS
from typehaus.resolve.trim_bands import drip_edge_bands, open_channel_bands

# Trim ``TrimKind`` values collapse onto a small render/IFC category set.
_TRIM_CATEGORY = {
    "fascia": "fascia",
    # The vented eave panel, not the dropped box ``resolve/soffits.py`` mints as "soffit":
    # one is the siding contractor's trim, the other the drywaller's ceiling.
    "soffit": "eave_soffit",
    "gutter": "gutter",
    "downspout": "downspout",
    "drip_flashing": "flashing",
    "wrb_counterflashing": "flashing",
    # A beam cap is formed metal like the flashing family, but it caps an exposed beam in a
    # wall plane and is the siding contractor's, not the roofer's — the BOM has always
    # billed it under ``_SIDING_EDGE_TRIM``. Collapsed onto "flashing" it rode the roofing
    # trade and the sunken-garden caps showed under Roof in the viewer, so it keeps its own
    # label and its own trade, exactly as the wall corner below does.
    "beam_cap": "beam_cap",
    # A wall corner closure is formed metal like the flashing family but it is the siding
    # contractor's, not the roofer's, so it keeps its own label and rides the siding trade.
    "wall_corner": "wall_corner",
    "movement_joint": "movement_joint",  # the mason's sealant joint, not formed metal
    # The glazing extrusions share the edge-run shape but not the flashing category: they
    # are an aluminium order billed by the lineal foot, and the take-off groups on this.
    "glazing_channel": "glazing_trim",
    "glazing_bar": "glazing_trim",
}


def resolve_edge_run(model: ResolvedModel, el, storey: str) -> None:
    path = [p.xy_m for p in el.path]
    if len(path) < 2:
        return
    category = _TRIM_CATEGORY.get(el.kind.value, "flashing")
    section = getattr(el, "section", None)
    if section is not None:
        if section.fit_to_brace_sill or section.profile == "ventilated_hood":
            return  # fitted after the brace and all connector geometry exist
        if el.vertical:
            raise ValueError(f"{el.tag}: formed sections require a horizontal plan run")
        from typehaus.resolve.flashing_caps import formed_run_mesh
        from typehaus.resolve.flashing_solids import flashing_solid

        for i, (a, b) in enumerate(zip(path[:-1], path[1:], strict=True)):
            model.solids.append(flashing_solid(
                uid=f"{el.uid}-{i:02d}", tag=f"{el.tag}-{i + 1}", storey=storey,
                category=category, mesh=formed_run_mesh(el, a, b), material=el.material,
                host_ref=el.host_ref or el.tag, billed_elsewhere=False))
        return
    top = el.top_elevation.meters
    z0 = top - el.depth.meters
    half = el.thickness.meters / 2.0
    # Two of the kinds are *formed* metal, not extruded stock, and the boxes-only solid IR
    # can only say so by composing the section out of bands (see :mod:`.trim_bands`). The
    # rest are genuinely one band and fall through to the plain extrusion below.
    recipe = _BANDED_SECTIONS.get(el.kind)
    if recipe is not None:
        _resolve_banded_run(model, el, storey, path, category, top, half,
                            recipe(2.0 * half, el.depth.meters))
        return
    for i, (a, b) in enumerate(zip(path[:-1], path[1:], strict=True)):
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-{i:02d}", tag=f"{el.tag}-{i + 1}", storey=storey,
            category=category, outline=rect_between(a, b, -half, half), z0_m=z0, z1_m=top,
            material=el.material,
        ))


#: Which edge-run kinds resolve as a composed section rather than as one extruded band.
#: A gutter is an open-top U, not the solid billet of aluminium a single bar would draw —
#: nothing rain could fall *into*. A drip edge is a bent angle: a flat leg lapped
#: under the roofing and a turn-down that throws the water clear. Both are the same recipes
#: the roof's *derived* trim uses, so an authored run and a derived one cannot drift into
#: different-looking metal on the same house.
_BANDED_SECTIONS = {
    TrimKind.GUTTER: open_channel_bands,
    TrimKind.DRIP_FLASHING: drip_edge_bands,
}


def _resolve_banded_run(model: ResolvedModel, el, storey: str, path, category: str,
                        top: float, half: float, bands) -> None:
    """Lay a composed section's bands across the ``[-half, +half]`` span the bar occupied.

    The run stays exactly where it was authored; only its cross-section stops being solid.
    """
    for key, offset, band_t, bottom_drop, top_drop in bands:
        left, right = _cross_span(half, offset, band_t, el.back_side)
        for i, (a, b) in enumerate(zip(path[:-1], path[1:], strict=True)):
            model.solids.append(ResolvedSolid(
                uid=f"{el.uid}-{i:02d}-{key}", tag=f"{el.tag}-{i + 1}-{key.upper()}",
                storey=storey, category=category,
                outline=rect_between(a, b, left, right),
                z0_m=top - bottom_drop, z1_m=top - top_drop,
                material=el.material,
            ))


def resolve_downspout(model: ResolvedModel, el, storey: str) -> None:
    """The leader as a round prism from the gutter outlet down to its discharge.

    Faceted exactly like the vent riser (``accessories._resolve_vent``) so the two read as the same
    kind of round metal on the elevation rather than one being smooth and the other a prism.
    """
    z0, z1 = el.bottom_elevation.meters, el.top_elevation.meters
    if z1 - z0 <= 0.0:
        return
    radius = el.diameter.meters / 2.0
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-00", tag=el.tag, storey=storey, category="downspout",
        outline=circle_outline(el.position.xy_m, radius, _PIPE_FACETS),
        z0_m=z0, z1_m=z1, material=el.material))
    # The gooseneck: one pipe diameter under the trough floor, outlet to drop, run past
    # both centres by a radius so it covers the two elbows.
    if el.outlet is not None and el.outlet.xy_m != el.position.xy_m:
        a, b = el.outlet.xy_m, el.position.xy_m
        length = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-01", tag=f"{el.tag}-OFFSET", storey=storey, category="downspout",
            outline=rect_between((a[0] - ux * radius, a[1] - uy * radius),
                                 (b[0] + ux * radius, b[1] + uy * radius), -radius, radius),
            z0_m=z1 - 2.0 * radius, z1_m=z1, material=el.material))


def _cross_span(half: float, offset: float, band_t: float,
                back_side: str) -> tuple[float, float]:
    """A band's ``[left, right]`` offsets, given where its inboard end sits.

    The band recipes measure offsets from the section's *inboard* end. ``rect_between``
    measures from the path's left-hand normal, so when the building is on the left the two
    frames run in opposite directions and the offsets have to be mirrored — not merely
    relabelled.
    """
    if back_side == "left":
        right = half - offset
        return right - band_t, right
    left = -half + offset
    return left, left + band_t

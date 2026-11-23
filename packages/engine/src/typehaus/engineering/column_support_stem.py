"""The wall a fixed column stands on, below the joint: the stem, the footing, the E-W
cantilever and the soil's prop through the porch (``column_support``'s later rows).

Split out of ``column_support`` (file size); arithmetic unchanged.
"""

from __future__ import annotations

import math

from typehaus.engineering.column_stem import (
    SOIL_LOAD_FACTOR,
    StemDemand,
    reinforced_flexure_lb_in_per_ft,
    spread_width_in,
    stem_states,
)
from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.pier_basis import _Pier
from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.retaining_basis import _BAR

#: IRC R301.5 / Table R301.5 note f — the guard's concentrated load, lb.
GUARD_LOAD_LB = 200.0


def pour_extents_in(ctx: EngineeringContext, wall_tag: str, pier: _Pier
                     ) -> tuple[float, float, float, float] | None:
    """``(to the far end, to the near end, chain start, chain end)`` along the wall's axis, in
    inches: the pour a column stands on runs through every concrete wall that continues it in a
    straight line (W-SG-W1 and W2 are one pour), so a 45 deg spread stops at the END of that
    chain, not at the wall element's own end. Positions are along the first wall's axis."""
    from typehaus.model.elements import Wall
    from typehaus.resolve.assembly_material import assembly_structure_material

    walls = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, Wall)
             and assembly_structure_material(ctx.plan, e.assembly) == "concrete"}
    first = walls.get(wall_tag)
    if first is None:
        return None

    def end(node: str) -> tuple[float, float] | None:
        el = ctx.plan.by_tag(node)
        return el.position.xy_m if el is not None and hasattr(el, "position") else None

    a0, a1 = end(first.start_node), end(first.end_node)
    if a0 is None or a1 is None:
        return None
    length = math.dist(a0, a1)
    ux, uy = (a1[0] - a0[0]) / length, (a1[1] - a0[1]) / length
    points = [a0, a1]
    changed = True
    chain = {wall_tag}
    while changed:
        changed = False
        for tag, other in walls.items():
            if tag in chain:
                continue
            p0, p1 = end(other.start_node), end(other.end_node)
            if p0 is None or p1 is None or math.dist(p0, p1) <= 0.0:
                continue
            vx, vy = (p1[0] - p0[0]), (p1[1] - p0[1])
            norm = math.hypot(vx, vy)
            collinear = abs(vx * uy - vy * ux) / norm < 0.02
            off_axis = abs((p0[0] - a0[0]) * uy - (p0[1] - a0[1]) * ux)
            touches = any(math.dist(q, r) < 0.01 for q in (p0, p1) for r in points)
            if collinear and off_axis < 0.02 and touches:
                chain.add(tag)
                points += [p0, p1]
                changed = True
    ts = [((x - a0[0]) * ux + (y - a0[1]) * uy) / 0.0254 for x, y in points]
    post = ctx.plan.by_tag(pier.tag)
    px, py = post.position.xy_m
    at = ((px - a0[0]) * ux + (py - a0[1]) * uy) / 0.0254
    return at - min(ts), max(ts) - at, min(ts), max(ts)


def stem_rows(ctx: EngineeringContext, pier: _Pier, wall_tag: str, dowel, wall_fc: float,  # type: ignore[no-untyped-def]
               clear_in: float, demand: StemDemand | None, inputs: list[Quantity],
               extents: dict[str, tuple[float, float]]) -> list[LimitState]:
    """The stem below the dowels and the footing under the column, spreads stopped at the
    pour's ends. ``extents`` collects each column's ``(to one end, to the other)``."""
    if demand is None or dowel.embedment is None:
        return []
    ends = pour_extents_in(ctx, wall_tag, pier)
    if ends is None:
        return []
    near, far = ends[0], ends[1]
    extents[pier.tag] = (near, far)
    states, quantities = stem_states(
        tag=pier.tag, fc_psi=wall_fc, thickness_in=2.0 * clear_in,
        column_width_in=pier.diameter_in, embedment_in=float(dowel.embedment.inches),
        north_in=near, south_in=far, demand=demand)
    inputs += quantities
    footing = _footing_row(ctx, pier, near, far)
    if footing is not None:
        states.append(footing)
    return states


def _footing_row(ctx: EngineeringContext, pier: _Pier, near_in: float, far_in: float
                 ) -> LimitState | None:
    """The column's service load spread through the stem at 45 deg onto the strip footing,
    against the site soil's allowable pressure (B-05 (3)): the INCREMENT the column adds, not
    the wall's own load, which `retaining_wall/<tag>` grades. The spread stops at the pour's
    ends."""
    from typehaus.engineering.soil import presumptive

    soil = presumptive(getattr(ctx, "soil_class", None), basis=getattr(ctx, "soil_basis", None))
    if soil is None or not pier.footing_width_in:
        return None
    spread_in = spread_width_in(pier.diameter_in / 2.0, pier.base_thickness_in, near_in, far_in)
    pressure = pier.service_lb / (pier.footing_width_in / 12.0 * spread_in / 12.0)
    return LimitState(
        f"{pier.tag}: footing bearing under the column point", pressure,
        soil.allowable_bearing_psf, "psf",
        f"the column's {pier.service_lb:,.0f} lb service load spread at 45 deg through the "
        f"{pier.base_thickness_in:.0f}\" stem over {spread_in:.0f}\" (stopped at the pour's "
        f"ends) of a {pier.footing_width_in:g}\" footing, against the presumptive allowable "
        f"of the site's soil class — the increment alone; the wall's own load is "
        f"`retaining_wall/<tag>`'s")


def _unbalanced_fill_m(ctx: EngineeringContext, wall) -> float | None:  # type: ignore[no-untyped-def]
    """The backfill the wall retains, as `structural.foundation_unbalanced_fill` reads it:
    authored, else from the site grade (or the wall top, if lower) down to the wall's bottom —
    a conservative proxy for a wall whose grade falls away."""
    if getattr(wall, "unbalanced_fill", None) is not None:
        return wall.unbalanced_fill.meters
    grade = getattr(ctx.plan.project.site, "grade", None)
    top, bottom = getattr(wall, "top_elevation", None), getattr(wall, "bottom_elevation", None)
    if grade is None or top is None or bottom is None:
        return None
    return max(0.0, min(grade.meters, top.meters) - bottom.meters)


def cantilever_row(ctx: EngineeringContext, wall_tag: str, piers: list[_Pier], flexible,  # type: ignore[no-untyped-def]
                    wall_fc: float, thickness_in: float, extents: dict[str, tuple[float, float]],
                    inputs: list[Quantity], missing: list[str]) -> list[LimitState]:
    """The stem as the cantilever it is under E-W wind (see ``column_stem``): its columns'
    ``M + V H`` over the union of their spreads, plus the retained soil, against the wall's own
    bars on the earth face."""
    from typehaus.engineering import deck_post as dp
    from typehaus.engineering.soil import presumptive

    wall = ctx.plan.by_tag(wall_tag)
    fill = _unbalanced_fill_m(ctx, wall)
    reinforcement = getattr(wall, "reinforcement", None)
    vertical = next((e for e in getattr(reinforcement, "bars", ()) or ()
                     if e.role == "vertical" and e.spacing is not None), None)
    soil = presumptive(getattr(ctx, "soil_class", None), basis=getattr(ctx, "soil_basis", None))
    if fill is None or vertical is None or soil is None or not extents:
        missing.append(f"{wall_tag}: its authored unbalanced_fill, its vertical bars "
                       f"(a spacing) and the site soil class, for the stem as a cantilever")
        return []
    height = piers[0].base_thickness_in
    total_moment = 0.0
    spans: list[tuple[float, float]] = []
    parts: list[str] = []
    for pier in piers:
        if pier.tag not in extents:
            continue
        near, far = extents[pier.tag]
        at = near                          # position along the pour from its near end
        reach = pier.diameter_in / 2.0 + height
        spans.append((max(at - reach, 0.0), min(at + reach, near + far)))
        axial = 1.2 * pier.dead_unplanted_lb
        delta = max(dp._sway_magnifier(pier, axial)[1], flexible(axial) if flexible else 1.0)
        mu = (pier.wind_ew_base_moment_lb_ft * dp.STRENGTH_FROM_ASD_WIND
              + pier.guard_base_moment_lb_ft) * delta * 12.0
        vu = pier.wind_ew_base_shear_lb * dp.STRENGTH_FROM_ASD_WIND + GUARD_LOAD_LB
        base = mu + vu * height
        total_moment += base
        parts.append(f"{pier.tag} M {mu / 12.0:,.0f} lb-ft + V {vu:,.0f} lb x "
                     f"{height / 12.0:.2f}' = {base / 12.0:,.0f}")
    spans.sort()
    union = 0.0
    top = -math.inf
    for lo, hi in spans:
        union += max(hi - max(lo, top), 0.0)
        top = max(top, hi)
    union_ft = union / 12.0
    h_fill = fill / 0.3048
    # The retained soil is PROPPED: it pushes INWARD on both stems (opposite ways), so the porch
    # spanning between them takes each one's top reaction against the other; only the E-W wind,
    # which pushes both the same way, has no prop. Propped (fixed base, pinned top) triangular
    # load: base moment q H^2 / 15 with q = efp H, i.e. efp H^3 / 15; top reaction efp H^2 / 10.
    # The pressure is the COURT'S own, from its single soil-basis source (read, not copied).
    from typehaus.engineering.retaining_system_cases import court_soil_basis, soil_inputs

    basis = court_soil_basis(ctx, soil)
    efp_value = basis["at_rest_efp"]
    soil_per_ft = SOIL_LOAD_FACTOR * efp_value * h_fill ** 3 / 15.0
    prop_lb_per_ft = SOIL_LOAD_FACTOR * efp_value * h_fill ** 2 / 10.0
    wind_per_ft = total_moment / 12.0 / union_ft
    area = _BAR[vertical.bar][0] * 12.0 / float(vertical.spacing.inches)
    cover = float(getattr(reinforcement, "cover", None).inches) if getattr(
        reinforcement, "cover", None) is not None else 3.0
    capacity = reinforced_flexure_lb_in_per_ft(
        wall_fc, thickness_in, cover, _BAR[vertical.bar][1], area) / 12.0
    inputs += [Quantity(f"{wall_tag}.ew_base_moment", total_moment / 12.0, "lb-ft", 1.0),
               Quantity(f"{wall_tag}.ew_spread_ft", union_ft, "ft", 0.05),
               Quantity(f"{wall_tag}.soil_moment_per_ft", soil_per_ft, "lb-ft/ft", 1.0),
               Quantity(f"{wall_tag}.soil_prop_per_ft", prop_lb_per_ft, "lb/ft", 1.0),
               *soil_inputs(ctx, soil)]
    states = [LimitState(
        f"{wall_tag}: stem as a cantilever under E-W wind and the retained soil",
        wind_per_ft + soil_per_ft, capacity, "lb-ft/ft",
        f"E-W wind pushes all four columns, and so both stems, the same way: the porch "
        f"diaphragm cannot prop one against the other, so each stem is a cantilever from its "
        f"footing under 1.2D + 1.0W + L_g + 1.6H, while the SOIL, which pushes inward on both "
        f"stems, is propped by the porch between them. Columns ({'; '.join(parts)}) lb-ft over "
        f"{union_ft:.1f}' of 45 deg spread stopped at the pour's ends = {wind_per_ft:,.0f} "
        f"lb-ft/ft, plus the PROPPED retained soil {SOIL_LOAD_FACTOR} x {efp_value:g} psf/ft "
        f"(the court's own at-rest basis, `court_soil_basis`: {basis['state']}) x "
        f"{h_fill:.2f}'^3 / 15 = {soil_per_ft:,.0f} lb-ft/ft over the unbalanced fill as "
        f"`structural.foundation_unbalanced_fill` reads it (from the site grade); the soil's "
        f"top reaction {prop_lb_per_ft:,.0f} lb/ft factored goes into the porch floor, "
        f""
        f"against phi M_n {capacity:,.0f} lb-ft/ft of #{vertical.bar} "
        f"@ {float(vertical.spacing.inches):g}\" on the earth face at d = "
        f"{thickness_in - cover - _BAR[vertical.bar][1] / 2.0:.2f}\" (a single curtain, "
        f"assumed on the retained face); the wind and the soil are taken adding, the case that "
        f"governs")]
    prop_service = efp_value * h_fill ** 2 / 10.0
    states += _porch_strut_rows(ctx, wall_tag, prop_service, inputs, missing)
    return states


def _porch_strut_rows(ctx: EngineeringContext, wall_tag: str, prop_lb_per_ft: float,
                      inputs: list[Quantity], missing: list[str]) -> list[LimitState]:
    """Where the soil's prop goes: through the porch, in COMPRESSION, not through the anchors.

    The soil pushes W1 and E1 INWARD (toward each other), so each stem's head presses on its
    ledger, the ledger on the joist ends, and the joists carry the thrust across the porch as
    struts to the other ledger and stem. The ledger bears flat on the wall's court face and
    each joist end bears on the ledger's face (the hanger only seats it), so the load is direct
    bearing and the ledger's Titen HD anchors and the LUS210SS fasteners take NONE of it: the
    anchors keep gravity shear (Simpson letter L-A-THDSSLDGR23, `structural.deck_ledger`) and
    would see tension only if the soil's thrust reversed, which a retained wall does not do.
    The porch's composite plank is not a strut and is not relied on.

    Graded at SERVICE against ASD values (NDS): the joist end's bearing on the ledger face,
    Fc-perp of the porch's southern pine No. 2 (`library/member_grades`); and the joist as a
    column, reported as the E_min' below which it would buckle (this record holds no E_min)."""
    from typehaus.engineering.deck_tributary import joist_span_ft
    from typehaus.library.member_grades import SOUTHERN_PINE_NO2_2X12_WET as grade
    from typehaus.model.floors import FloorSystem
    from typehaus.model.structure import Beam
    from typehaus.resolve.framing.profiles import cross_section

    deck = next((d for d in ctx.plan.all_elements() if isinstance(d, FloorSystem)
                 and d.service == "deck"
                 and any(getattr(ctx.plan.by_tag(r), "ledger_on", None) == wall_tag
                         for r in d.joists.bearing_refs or ()
                         if isinstance(ctx.plan.by_tag(r), Beam))), None)
    span_ft = joist_span_ft(ctx, deck) if deck is not None else None
    if deck is None or span_ft is None:
        missing.append(f"the porch deck whose ledger is on {wall_tag}, to carry the soil's prop")
        return []
    section = cross_section(deck.joists.member)
    width_in, depth_in = section.width_m / 0.0254, section.depth_m / 0.0254
    spacing_ft = float(deck.joists.spacing.inches) / 12.0
    per_joist = prop_lb_per_ft * spacing_ft
    bearing = per_joist / (width_in * depth_in)
    span_in = span_ft * 12.0
    strong = width_in * depth_in ** 3 / 12.0
    e_needed = per_joist * 3.0 * span_in ** 2 / (math.pi ** 2 * strong)
    inputs += [Quantity(f"{wall_tag}.prop_per_joist", per_joist, "lb", 1.0),
               Quantity(f"{wall_tag}.joist_span", span_ft, "ft", 0.01)]
    return [LimitState(
        f"{wall_tag}: soil prop, joist end bearing on the ledger", bearing, grade.fc_perp_psi,
        "psi",
        f"NDS ASD, the {prop_lb_per_ft:,.0f} lb/ft SERVICE prop (efp H^2 / 10) x {spacing_ft:g}' "
        f"= {per_joist:,.0f} lb on each {width_in:g}\" x {depth_in:g}\" joist end bearing "
        f"directly on the ledger's face, Fc-perp {grade.fc_perp_psi:,.0f} psi "
        f"({grade.source.split(':')[0]}, wet service). The thrust is COMPRESSION through ledger "
        f"and joists: the ledger anchors and the LUS210SS fasteners carry none of it. The joist "
        f"as a column ({span_ft:.2f}' strong-axis, the plank bracing the weak axis) buckles only "
        f"if E_min' falls below {e_needed:,.0f} psi at a factor of 3 (this record holds no "
        f"E_min; the apparent E is {grade.e_psi:,.0f}); the plank is not a strut")]

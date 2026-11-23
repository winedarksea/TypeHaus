"""A fixed-base cast column's joint onto a foundation-wall top — ``column_support/<wall tag>``.

Until 2026-09-20 this was a ``deferred.py`` kind: ``deck_post`` computes each column's base
moment ON THE COLUMN, and the concrete that receives it — a basement wall answered by IRC
Table R404.1.2(8), which publishes no surcharge column — was graded by nobody. One record
per wall, four states per column standing on it, each an envelope over ASCE 7-16 §2.3.1 at
the same (Pu, magnified Mu) pairs ``deck_post`` grades the column on:

* **bearing on the wall top**, ACI 318-19 §22.8.3, on the COMPRESSION BLOCK. The base sits
  far outside the kern (e = Mu/Pu against D/8 for a circle), so the load arrives on a
  circular segment, not the gross section. The block is ``deck_post._pm_point``'s at that
  Pu; the force on it is the dowel couple's compression. ``√(A2/A1)`` is read off the wall's
  own width and is 1.0 where the round is as wide as the stem.
* **dowel tension across the joint**, per bar, φ 0.90.
* **shear friction across the cold joint**, §22.9, μ from the authored
  ``BarSpec.joint_surface``; the tension the couple spends is deducted from Avf.
* **dowel development into the stem**, ``deck_post._dowel_anchorage`` — the same state the
  column's own record prints, against the authored ``BarSpec.embedment``.

**Oracle.** ``houses/catlin/notes/balcony_moment_columns.md`` §11, hand-worked in a separate
pass; ``tests/test_column_support_calc.py`` reproduces it.
"""

from __future__ import annotations

import dataclasses
import math

from typehaus.engineering.column_stem import (
    SOIL_LOAD_FACTOR,
    StemDemand,
    reinforced_flexure_lb_in_per_ft,
    spread_width_in,
    stem_states,
)
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Scope,
    Status,
    item_id,
)
from typehaus.engineering.pier_basis import _Pier, cast_piers
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.retaining_basis import _BAR, PRESUMPTIVE_FC_PSI, REINFORCEMENT_FY_PSI
from typehaus.wind import ASD_WIND_FACTOR

KIND = "column_support"
#: 2: 2026-11-23 (review B-04/B-05/B-08): the joint is graded on the flexible base's delta, the
#: dowel development is §25.4.2.4's general equation, and the stem below the joint, the head
#: prop, the strut and the footing under the column point are rows, not exclusions.
BASIS_VERSION = "2"
BASIS = ("ACI 318-19 §22.8.3 (bearing), §22.9 (shear friction), §25.4.2.4 (development), "
         "§14.5.2.1 (the stem, plain concrete)")

#: ACI 318-19 Table 21.2.2: bearing 0.65, shear 0.75, tension-controlled 0.90.
PHI_BEARING = 0.65
PHI_SHEAR = 0.75
PHI_TENSION = 0.90
#: IRC R301.5 / Table R301.5 note f — the guard's concentrated load, lb.
GUARD_LOAD_LB = 200.0
#: ACI 318-19 Table 22.9.4.2, normalweight (λ 1.0).
MU_ROUGHENED = 1.0
MU_NOT_ROUGHENED = 0.6

oracled_by(KIND, Oracle(note="balcony_moment_columns.md", section="§11",
                        test="tests/test_column_support_calc.py"))


@keys(KIND)
def column_support_keys(ctx: EngineeringContext) -> list[str]:
    """Every wall with a cast, fixed-base column standing on its top.

    Read off ``cast_piers``' own ``shared_wall_footing`` flag — set exactly when a concrete
    post inherits a concrete wall as its base — and scoped to a column with a base moment:
    a leaning column hands its wall a vertical load and nothing else.
    """
    return sorted({pier_wall(ctx, pier) for pier in _moment_columns(ctx)} - {None})


def pier_wall(ctx: EngineeringContext, pier: _Pier) -> str | None:
    return getattr(ctx.plan.by_tag(pier.tag), "supported_by", None)


def _moment_columns(ctx: EngineeringContext) -> list[_Pier]:
    return [p for p in cast_piers(ctx) if p.shared_wall_footing and p.lateral_system]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    by_wall: dict[str, list[_Pier]] = {}
    for pier in _moment_columns(ctx):
        wall = pier_wall(ctx, pier)
        if wall:
            by_wall.setdefault(wall, []).append(pier)
    return [_one(ctx, wall, sorted(piers, key=lambda p: p.tag))
            for wall, piers in sorted(by_wall.items())]


def _clear_side_in(ctx: EngineeringContext, pier: _Pier, wall_tag: str) -> float | None:
    """The least distance from the column centre to either face of the wall's structure
    layer, inches — the radius of the largest concentric circle on the wall top (A2)."""
    from typehaus.resolve.rebar.walls import structure_layer

    wall = ctx.model.wall(wall_tag)
    post = ctx.plan.by_tag(pier.tag)
    layer = structure_layer(wall) if wall is not None else None
    if layer is None or post is None:
        return None
    (ax, ay), (bx, by) = wall.axis
    length = math.hypot(bx - ax, by - ay) or 1.0
    nx, ny = -(by - ay) / length, (bx - ax) / length
    ts = [(x - ax) * nx + (y - ay) * ny for x, y in layer.polygon]
    tc = (post.position.x.meters - ax) * nx + (post.position.y.meters - ay) * ny
    return round(min(max(ts) - tc, tc - min(ts)) / 0.0254, 3)  # 1/1000" — a flush round reads 6.000


def _shear_asd_lb(pier: _Pier) -> tuple[float, float]:
    """``(wind, guard)`` ASD base shear, lb. The deck path builds the wind moment as
    ``V x column height`` (``pier_basis._base_moments``), so that factorisation is exact; a
    roof-borne column records its own shear and arm, which is read instead."""
    from typehaus.engineering.roof_moment import base_shear_of

    guard = GUARD_LOAD_LB if pier.guard_base_moment_lb_ft > 0.0 else 0.0
    if pier.wind_head_shear_lb:       # the bands' own total: the shaft's wind is below the head
        return pier.wind_head_shear_lb + pier.wind_shaft_shear_lb, guard
    recorded = base_shear_of(pier.tag)
    if not guard and recorded is not None:
        return recorded[0], 0.0
    height_ft = pier.height_in / 12.0
    return (pier.wind_base_moment_lb_ft / height_ft if height_ft else 0.0), guard


def _couple(mu_lb_in: float, pu_lb: float, radius_in: float, fc_psi: float,
            offsets: tuple[float, ...]) -> tuple[float, float, int]:
    """``(C, T, bars in tension)``: the compression on the block and the dowel tension that
    balance (Pu, Mu), T at the centroid of the dowels below the centre. Compression dowels
    are not credited, which puts every pound of compression on the concrete.

    The block is the one THIS force produces, ``0.85 f'c`` over the segment of area
    ``C / 0.85 f'c`` (iterated), not the column's P-M block: a smaller force bears on a
    shallower segment whose centroid is further out, which lengthens the lever. (Taking the
    P-M point's own block, a different force's, overstated the tension, review 2026-11-23.)
    Where no tension is needed, C = Pu."""
    from typehaus.engineering import deck_post as dp

    tension = [-o for o in offsets if o < -1e-9]
    lever = sum(tension) / len(tension)
    compression = pu_lb
    for _ in range(60):
        area = min(compression / (0.85 * fc_psi), math.pi * radius_in ** 2 * 0.999)
        lo, hi = 0.0, 2.0 * radius_in
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if dp._segment(radius_in, mid)[0] < area:
                lo = mid
            else:
                hi = mid
        ybar = dp._segment(radius_in, 0.5 * (lo + hi))[1]
        updated = (mu_lb_in + pu_lb * lever) / (ybar + lever)
        if abs(updated - compression) < 0.01:
            compression = updated
            break
        compression = 0.5 * (compression + updated)      # damped: the block and C chase each other
    pull = compression - pu_lb
    if pull <= 0.0:
        return pu_lb, 0.0, len(tension)
    return compression, pull, len(tension)


def _column_states(ctx: EngineeringContext, pier: _Pier, wall_tag: str,
                   missing: list[str], inputs: list[Quantity],
                   extents: dict[str, tuple[float, float]]) -> list[LimitState]:
    from typehaus.engineering import deck_post as dp

    cage = dp.cage_for(pier)
    dowel = dp.dowel_entry(pier)
    if cage is None or dowel is None or dowel.bar not in _BAR:
        missing.append(f"{pier.tag}: a structured cage with a `dowels` BarSpec row")
        return []
    col_fc = dp._fc_psi(pier)
    wall_fc = pier.base_fc_psi or PRESUMPTIVE_FC_PSI
    cover = dp._cover_in(pier)
    radius = pier.diameter_in / 2.0
    dowel_db, dowel_area = _BAR[dowel.bar][1], _BAR[dowel.bar][0]
    # Dowels sit one bar inside the verticals (resolve/rebar's contact lap), one per vertical.
    ring = (radius - cover - cage.tie_diameter_in - cage.bar_diameter_in / 2.0
            - (cage.bar_diameter_in + dowel_db) / 2.0)
    count = cage.count
    layouts = tuple(tuple(ring * math.cos(start + 2.0 * math.pi * i / count)
                          for i in range(count)) for start in (0.0, math.pi / count))

    clear = _clear_side_in(ctx, pier, wall_tag)
    if clear is None:
        missing.append(f"{pier.tag}: {wall_tag}'s resolved structure layer")
        return []
    root_a2_a1 = min(2.0, max(1.0, clear / radius))
    rough = dowel.joint_surface == "roughened"
    mu = MU_ROUGHENED if rough else MU_NOT_ROUGHENED
    fc_sf = min(col_fc, wall_fc)
    area = math.pi * radius ** 2
    vn_max = (min(0.2 * fc_sf, 480.0 + 0.08 * fc_sf, 1600.0) if rough
              else min(0.2 * fc_sf, 800.0)) * area
    wind_v, guard_v = _shear_asd_lb(pier)
    wind_mu = pier.wind_base_moment_lb_ft * dp.STRENGTH_FROM_ASD_WIND
    guard_mu = pier.guard_base_moment_lb_ft * dp.GUARD_LOAD_FACTOR

    from typehaus.engineering.base_rotation import flexible_magnifier

    flexible = flexible_magnifier(ctx, pier)
    worst: dict[str, tuple[float, float, float, object, str]] = {}
    stem_demand: StemDemand | None = None
    for case in dp._combinations(pier, wind_mu, guard_mu):
        # The joint sits on a base that turns: the flexible delta where the spring forms,
        # the rigid base's (k 2.1) otherwise. The larger governs; it is the flexible one.
        delta = max(dp._sway_magnifier(pier, case.axial_lb)[1],
                    flexible(case.axial_lb) if flexible else 1.0)
        mu_in = case.moment_lb_ft * delta * 12.0
        _phi_mn, _phi, c = dp._pm_point(pier, cage, cover, case.axial_lb)
        block, ybar = dp._segment(radius, min(dp._beta_1(col_fc) * c, 2.0 * radius))
        couples = [_couple(mu_in, case.axial_lb, radius, col_fc, offs) for offs in layouts]
        comp = max(k[0] for k in couples)
        pull = max(k[1] for k in couples)
        per_bar = max(k[1] / k[2] for k in couples)
        factors = dict(case.factors)
        vu = factors.get("W", 0.0) / ASD_WIND_FACTOR * wind_v + factors.get("L", 0.0) * guard_v
        if stem_demand is None or mu_in > stem_demand.mu_lb_in:
            stem_demand = StemDemand(case.label, mu_in, vu)
        bearing_cap = PHI_BEARING * 0.85 * wall_fc * block * root_a2_a1
        sf_cap = min(mu * (PHI_SHEAR * count * dowel_area * REINFORCEMENT_FY_PSI - pull),
                     PHI_SHEAR * vn_max)
        how = (f"Pu {case.axial_lb:,.0f} lb, Mu {mu_in / 12.0:,.0f} lb-ft (δ {delta:.3f}), "
               f"e {mu_in / case.axial_lb if case.axial_lb else 0.0:.1f}\"")
        for name, demand, capacity in (
                ("bearing", comp, bearing_cap),
                ("tension", per_bar, PHI_TENSION * dowel_area * REINFORCEMENT_FY_PSI),
                ("shear", vu, sf_cap)):
            ratio = demand / capacity if capacity > 0 else math.inf
            if name not in worst or ratio > worst[name][0]:
                worst[name] = (ratio, demand, capacity, case,
                               how + (f", c {c:.3f}\", block {block:.2f} in2 at "
                                      f"{ybar:.3f}\"" if name == "bearing" else ""))

    def graded(key: str, label: str, unit: str, citation: str) -> LimitState:
        _r, demand, capacity, case, how = worst[key]
        return LimitState(f"{pier.tag}: {label}", demand, capacity, unit,
                          f"{citation} — governed by ASCE 7-16 §2.3.1 {case.label}: {how}",
                          combination=f"ASCE 7-16 §2.3.1 {case.label}",
                          combination_factors=case.factors)

    states = [
        graded("bearing", "bearing on the wall top", "lb",
               f"ACI 318-19 §22.8.3.2 φ {PHI_BEARING:.2f} × 0.85 f'c {wall_fc:,.0f} psi × the "
               f"compression block × √(A2/A1) {root_a2_a1:.2f} (the wall top clears "
               f"{clear:.2f}\" each side of a {radius:.2f}\" radius); C from the dowel couple, "
               f"compression dowels not credited"),
        graded("tension", "dowel tension across the joint", "lb",
               f"φ {PHI_TENSION:.2f} As fy per #{dowel.bar} dowel, the worse of the two "
               f"orientations of a {count}-bar ring of radius {ring:.3f}\""),
        graded("shear", "shear friction across the cold joint", "lb",
               f"ACI 318-19 §22.9.4.2 φ {PHI_SHEAR:.2f} μ {mu:.1f}λ "
               f"({'the authored 1/4-in. roughening' if rough else 'not intentionally roughened'})"
               f" × (Avf fy less the couple's tension), capped by §22.9.4.4 at "
               f"{PHI_SHEAR * vn_max:,.0f} lb; wind at 1.0W plus the {guard_v:.0f} lb guard "
               f"load, compression not credited"),
    ]
    anchorage = dp._dowel_anchorage(pier, cage, col_fc)
    if anchorage is None:
        missing.append(f"{pier.tag}: `BarSpec.embedment` on its `dowels` row")
    else:
        states.append(dataclasses.replace(anchorage,
                                          name=f"{pier.tag}: dowel development into the stem"))
    states += _stem_rows(ctx, pier, wall_tag, dowel, wall_fc, clear, stem_demand, inputs,
                         extents)
    states.append(LimitState(f"{pier.tag}: footprint on the wall top", radius, clear, "in",
                             "the column's radius against the clear wall top each side of "
                             "its centre — a round wider than the stem overhangs its face",
                             is_detailing=True))
    inputs += [
        Quantity(f"{pier.tag}.sqrt_A2_A1", root_a2_a1, "", 0.01),
        Quantity(f"{pier.tag}.shear_friction_mu", mu, "", None),
        Quantity(f"{pier.tag}.dowel_embedment",
                 float(dowel.embedment.inches) if dowel.embedment else 0.0, "in", 0.125),
        Quantity(f"{pier.tag}.wall_fc", wall_fc, "psi", 1.0),
        Quantity(f"{pier.tag}.column_fc", col_fc, "psi", 1.0),
        Quantity(f"{pier.tag}.column_cover", cover, "in", 0.125),
        Quantity(f"{pier.tag}.wall_cover", pier.base_cover_in or 0.0, "in", 0.125),
        Quantity(f"{pier.tag}.stem_height", pier.base_thickness_in, "in", 0.125),
        Quantity(f"{pier.tag}.dowel_bar", float(dowel.bar), "", None),
        Quantity(f"{pier.tag}.dowel_count", float(count), "", None),
        Quantity(f"{pier.tag}.wind_base_moment", pier.wind_base_moment_lb_ft, "lb-ft", 1.0),
        Quantity(f"{pier.tag}.guard_base_moment", pier.guard_base_moment_lb_ft, "lb-ft", 1.0),
        Quantity(f"{pier.tag}.factored_axial", pier.factored_lb, "lb", 1.0),
    ]
    return states


def _pour_extents_in(ctx: EngineeringContext, wall_tag: str, pier: _Pier
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


def _stem_rows(ctx: EngineeringContext, pier: _Pier, wall_tag: str, dowel, wall_fc: float,  # type: ignore[no-untyped-def]
               clear_in: float, demand: StemDemand | None, inputs: list[Quantity],
               extents: dict[str, tuple[float, float]]) -> list[LimitState]:
    """The stem below the dowels and the footing under the column, spreads stopped at the
    pour's ends. ``extents`` collects each column's ``(to one end, to the other)``."""
    if demand is None or dowel.embedment is None:
        return []
    ends = _pour_extents_in(ctx, wall_tag, pier)
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


def _cantilever_row(ctx: EngineeringContext, wall_tag: str, piers: list[_Pier], flexible,  # type: ignore[no-untyped-def]
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




def _one(ctx: EngineeringContext, wall_tag: str, piers: list[_Pier]) -> EngineeringRecord:
    missing: list[str] = []
    inputs: list[Quantity] = []
    states: list[LimitState] = []
    extents: dict[str, tuple[float, float]] = {}
    for pier in piers:
        states += _column_states(ctx, pier, wall_tag, missing, inputs, extents)
    wall_fc = next((p.base_fc_psi for p in piers if p.base_fc_psi), PRESUMPTIVE_FC_PSI)
    clear = _clear_side_in(ctx, piers[0], wall_tag)
    if clear is not None:
        from typehaus.engineering.base_rotation import flexible_magnifier

        flexible = flexible_magnifier(ctx, piers[0])
        states += _cantilever_row(ctx, wall_tag, piers, flexible, wall_fc, 2.0 * clear,
                                  extents, inputs, missing)
    tags = ", ".join(p.tag for p in piers)
    notes = (
        f"{wall_tag} is a basement wall graded prescriptively by IRC Table R404.1.2(8), "
        f"which publishes no surcharge column; this record grades the JOINT each of "
        f"{tags} makes with its top, at the same §2.3.1 (Pu, magnified Mu) pairs "
        f"`deck_post/<column>` grades the column on.",
        "BEARING is graded on the compression block, not the gross section: the base is far "
        "outside the kern (D/8 on a circle), so the round bears on a circular segment. The "
        "block is the column's own at each Pu (`deck_post._pm_point`); the force on it is "
        "the compression of the couple the dowels close. √(A2/A1) is taken off the wall's "
        "width and is 1.0 where the round is as wide as the stem — ACI's confinement "
        "credit needs concrete beside the column, and there is none.",
        "DOWELS: one per vertical, one bar inside the cage (contact lap). Both orientations "
        "of the ring are run — a bar on the tension axis loads one dowel on a longer lever, "
        "two straddling it share a shorter one — and each state takes the worse.",
        "SHEAR FRICTION: μ 1.0λ only where the dowel row authors "
        "`joint_surface=\"roughened\"` (ACI's intentional 1/4-in. amplitude); otherwise "
        "0.6λ. The couple's dowel tension is deducted from Avf, and no clamping from the "
        "axial load is credited.",
        "THE STEM (review B-05 / D-R3, verifier 2026-11-23). Below the dowels the head moment "
        "AND its shear's lever (M_u + V_u x over the embedment) are taken down the wall in "
        "plain concrete over the column's width plus a 45 deg spread, stopped at the pour's ends "
        "(W-SG-W1/W2 are one pour; the rear column stands 23\" from the north end). The "
        "dowels, developed over the authored embedment, reinforce the head.",
        "WHAT CARRIES THE E-W LATERAL: under E-W wind all four columns push BOTH stems the same "
        "way, so the porch diaphragm cannot prop each stem against the other. The load goes to "
        "the ground through the stems as cantilevers from their footings (the "
        "\"stem as a cantilever\" row: each column's M + V H over its spread, plus the retained "
        "soil's PROPPED at-rest moment, against the wall's own bars), and the footings take the "
        "base shear (the court's sliding cases now read the balcony's E-W wind, 1,348 lb ASD, "
        "live). The soil is propped because it pushes INWARD on both stems, opposite ways, so "
        "the porch floor spanning between them takes each stem's top reaction against the "
        "other's: that is Table R404.1.2(8)'s standard top-support assumption. THE SOIL'S PROP "
        "IS COMPRESSION: each stem presses on its ledger, the ledger on the joist ends, and the "
        "joists carry it across the porch as struts to the other ledger and stem (the "
        "\"soil prop, joist end bearing\" row: direct bearing on the ledger face, Fc-perp, the "
        "joist's buckling E_min' reported). The ledger's Titen HD anchors, the LUS210SS "
        "fasteners and the plank carry NONE of it: the anchors keep the gravity shear the "
        "Simpson letter L-A-THDSSLDGR23 grades (`structural.deck_ledger`) and would see tension "
        "only if the soil's thrust reversed. That needs the porch framed before backfill and "
        "the two sides backfilled together (`AN-SG-BACKFILL` (b), L1's sequence): a one-sided "
        "stage would load the far stem through the strut. No column prop rides it. A drawing "
        "note, `AN-SG-LEDGER-DOWELS`, keeps the ledger's Titen HD anchors off the dowels.",
        "DOWEL TENSION on the conservative C_f 1.80 for every wind band, the guard taken "
        "concurrently with full design wind and the one-bar couple on the block that force "
        "itself produces. It was OWNER-ACCEPTED at 0.92 (2026-11-23) when the porch curtains were "
        "a wind band; with the curtains stowed (owner basis) it is well under that, and it comes "
        "back to the owner only if it rises above 0.92.",
        "FOOTPRINT: the 12\" round is flush with both faces of the 12\" stem, so the row reads "
        "1.000 and allows no placement tolerance — a detailing row, not a margin. The column "
        "form is set from the stem's own face lines (`AN-SG-PLACEMENTS`); a round set off-centre "
        "overhangs a face by the offset, and none is accepted.",
        "FOOTING under the column point, and the joint's torsion: the footing row above is "
        "the increment the column adds; the torque through the joint is `column_head_joint`'s "
        "(about 3% of the cracking threshold) and rides the same shear-friction dowels.",
        "NOT GRADED here: (1) ROTATIONAL RESTRAINT of the foundation is "
        f"`base_rotation/<column>` for {tags}; (2) the stem's in-plane (N-S) wind, which runs "
        "along the wall's strong axis.",
    )
    over = any(not state.ok for state in states)
    status = Status.INCOMPLETE if missing else (Status.OVER if over else Status.OK)
    governing = max((s for s in states if not s.is_detailing), key=lambda s: s.ratio,
                    default=None)
    summary = (f"{wall_tag}: the wall-top joint under {tags}"
               + (f", d/c {governing.ratio:.2f} on {governing.name}" if governing else ""))
    return EngineeringRecord(
        item_id=item_id(KIND, wall_tag), kind=KIND, key=wall_tag,
        basis_version=BASIS_VERSION, basis=BASIS, status=status, summary=summary,
        inputs=tuple(inputs), limit_states=tuple(states), missing=tuple(missing),
        notes=notes, element_tags=(wall_tag, *(p.tag for p in piers)),
        scope=Scope.SCREENING)

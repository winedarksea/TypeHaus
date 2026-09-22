"""Where a break's thrust goes on the house side — the wall rows and the court's, free body
§11i (basis 6); the lateral path through the slab is :mod:`thermal_break_path`.

The house is taken rigid (the upper bound on force). Load factor 1.0 on T (ACI 318-19
§5.3.6, ASCE 7-16 §2.3.4). Capacities are the most generous the model supports — the whole
wall panel — so an OVER is a lower bound on the real ratio.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.thermal_break_demand import integrate
from typehaus.engineering.thermal_break_geometry import Board, z_extent

REQUIRED_FS = 1.5
#: ACI 318-19 Table 21.2.1 (shear) and Table 21.2.2 (tension-controlled flexure).
PHI_SHEAR, PHI_FLEXURE = 0.75, 0.90
#: ESR-2555's F2 is perpendicular to the plate — the direction a thrust into the wall takes.
SILL_ANCHOR_DIRECTION = "lateral_f2_lb"
_IN = 1.0 / 0.0254


def _wall(ctx, tag):
    return next((w for w in ctx.model.walls if w.tag == tag), None)


def _core_in(ctx, tag) -> float:
    from typehaus.model.enums import LayerFunction

    el = ctx.plan.by_tag(tag)
    assembly = ctx.plan.library.resolve_assembly(getattr(el, "assembly", "") or "")
    return sum(ly.thickness.inches for ly in getattr(assembly, "layers", ())
               if ly.function is LayerFunction.STRUCTURE)


def _length_in(wall) -> float:
    (x0, y0), (x1, y1) = wall.axis
    return math.hypot(x1 - x0, y1 - y0) * _IN


def wall_patch(ctx, board: Board, pressure) -> dict | None:
    """``pressure(z)`` psi — closing plus the locked-in pour — on the house wall's concrete,
    simply supported footing to floor, and on whatever stands above its top (the band)."""
    wall = _wall(ctx, board.house_tag)
    ext = z_extent(ctx, board.house_tag)
    if wall is None or ext is None:
        return None
    lo, hi = max(board.bottom_in, ext[0]), min(board.top_in, ext[1])
    span, length = ext[1] - ext[0], board.length_in
    force, first = (v * length for v in integrate(pressure, lo, hi))
    band = integrate(pressure, max(ext[1], board.bottom_in), board.top_in)[0] * length
    top = (first + force * (lo - ext[0])) / span
    bottom = force - top
    moment = 0.0
    for k in range(1, 200):
        a = ext[0] + span * k / 200.0
        f, m = (v * length for v in integrate(pressure, lo, min(a, hi)))
        # Moment at a about the loads below it: f acts at lo + m/f.
        moment = max(moment, bottom * (a - ext[0]) - (f * (a - lo) - m if a > lo else 0.0))
    return dict(wall=wall, on_wall=force, band=band, span=span, moment=moment,
                bottom_reaction=bottom, top_reaction=top)


def _wall_steel(ctx, tag):
    from typehaus.engineering.retaining_basis import bar_for_roles
    from typehaus.model.rebar import BARS

    el = ctx.plan.by_tag(tag)
    spec = getattr(el, "reinforcement", None)
    parsed = bar_for_roles(spec, ("vertical",))
    cover = getattr(getattr(spec, "cover", None), "inches", None)
    if parsed is None or cover is None:
        return None
    return parsed, BARS[parsed[0]], cover


def house_wall_rows(ctx, board: Board, patch: dict, states, missing, inputs) -> None:
    from typehaus.engineering.retaining_basis import REINFORCEMENT_FY_PSI
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    wall, tag = patch["wall"], board.house_tag
    steel = _wall_steel(ctx, tag)
    fc = fc_psi(concrete_spec_for(ctx.plan, ctx.plan.by_tag(tag)))
    h = _core_in(ctx, tag)
    if steel is None or fc is None or not h:
        missing.append(f"{tag}'s vertical bar and cover, its mix f'c and STRUCTURE layer — "
                       f"the house wall rows")
        return
    (bar, spacing), section, cover = steel
    length = _length_in(wall)
    d = h - cover - section.diameter_in / 2.0
    area = section.area_in2 * length / spacing
    a = area * REINFORCEMENT_FY_PSI / (0.85 * fc * length)
    phi_mn = PHI_FLEXURE * area * REINFORCEMENT_FY_PSI * (d - a / 2.0)
    inputs += [Quantity("wall_thrust", patch["on_wall"], "lb", 1.0),
               Quantity("wall_span", patch["span"], "in", 0.01)]
    states.append(LimitState(
        "house wall flexure", patch["moment"], phi_mn, "lb-in",
        f"1.0T: {patch['on_wall']:,.0f} lb (closing + locked-in pour) on {tag}'s "
        f"{patch['span']:.2f}\" span, simply supported, maximum moment integrated; "
        f"vs the WHOLE {length:.1f}\" panel, #{bar} @ {spacing:.0f}\": As {area:.4f} in2, "
        f"d {d:.4f}\", a {a:.4f}\", phi 0.90 (ACI 318-19 §22.3); soil left out",
        combination="1.0T"))
    vc = PHI_SHEAR * 2.0 * math.sqrt(fc) * length * d
    states.append(LimitState(
        "house wall shear", max(patch["bottom_reaction"], patch["top_reaction"]), vc, "lb",
        f"one-way at the support, phi 0.75 x 2 sqrt(f'c) b d over the whole {length:.1f}\" "
        f"(ACI 318-19 §22.5.5.1); punching retired — the patch runs support to support",
        combination="1.0T"))
    _floor_line(ctx, board, patch, states, missing)


def _floor_line(ctx, board: Board, patch: dict, states, missing) -> None:
    """The wall's top reaction plus the band above it, into the sill anchorage."""
    from typehaus.hardware.catalog import allowable_for_model

    wall = patch["wall"]
    core = next((ly for ly in wall.depth_layers() if ly.function == "structure"), None)
    xs = [p[0] * _IN for p in core.polygon]
    ys = [p[1] * _IN for p in core.polygon]
    top = wall.z1_m * _IN
    anchors, capacity = [], 0.0
    for s in ctx.model.solids:
        if not s.category.startswith("connector"):
            continue
        parts = s.tag.split("~")
        allow = allowable_for_model(parts[1]) if len(parts) > 2 else None
        value = getattr(allow, SILL_ANCHOR_DIRECTION, None) if allow is not None else None
        if value is None or not (s.z0_m * _IN - 6.0 <= top <= s.z1_m * _IN + 6.0):
            continue
        cx = sum(p[0] for p in s.outline) / len(s.outline) * _IN
        cy = sum(p[1] for p in s.outline) / len(s.outline) * _IN
        across, along = (cy, cx) if board.ax == 1 else (cx, cy)
        a_lo, a_hi = (min(ys), max(ys)) if board.ax == 1 else (min(xs), max(xs))
        l_lo, l_hi = (min(xs), max(xs)) if board.ax == 1 else (min(ys), max(ys))
        if a_lo < across < a_hi and l_lo - 1.0 <= along <= l_hi + 1.0:
            anchors.append(parts[1])
            capacity += value
    demand = patch["top_reaction"] + patch["band"]
    if not anchors:
        missing.append(f"a sill anchorage with a published perpendicular value on "
                       f"{board.house_tag}'s top — the floor line's {demand:,.0f} lb")
        return
    states.append(LimitState(
        "house floor-line reaction", demand, capacity, "lb",
        f"top reaction {patch['top_reaction']:,.0f} + the board above the wall top "
        f"{patch['band']:,.0f} lb; vs {len(anchors)} x {anchors[0]} F2 (perpendicular, "
        f"ICC-ES ESR-2555 Table 1, at its C_D 1.6 and SG 0.50 — generous for an SPF sill)",
        combination="1.0T"))


def court_sliding(ctx, ref: str, total: float, free_bodies: dict, states, missing) -> None:
    """The thrust's reaction pushes the court away from the house, against its soil.

    Where the thrust overcomes the retained soil it is an FS on base friction; where it does
    not, nothing pushes the court away and an FS has no meaning (it printed as infinite), so
    the row is graded as a FORCE — net push against friction / 1.5, the same ratio the FS row
    reads whenever the net is positive (free body §11j)."""
    body = free_bodies.get(ref)
    if not body:
        missing.append(f"loop {ref}'s free body — the court's resistance to the thrust")
        return
    rows = [(float(pcf), soil_push, friction, total - soil_push)
            for pcf, (soil_push, friction) in body.items()]
    # The worst unit weight is the largest net against friction; ties break on the lower pcf.
    pcf, soil_push, friction, net = max(rows, key=lambda r: (r[3] / r[2], -r[0]))
    basis = (f"sum of every board's thrust on loop {ref} {total:,.0f} lb less the retained "
             f"soil's {soil_push:,.0f} lb at {pcf:.0f} pcf, against base friction "
             f"{friction:,.0f} lb; passive not credited")
    if net > 0:
        states.append(LimitState("court sliding under break thrust", REQUIRED_FS,
                                 friction / net, "", basis, is_safety_factor=True))
        return
    states.append(LimitState(
        "court sliding under break thrust", 0.0, friction / REQUIRED_FS, "lb",
        f"{basis}. The net is {net:,.0f} lb — the thrust never overcomes the soil, so nothing "
        f"pushes the court away: graded as a force, net push 0 against friction / "
        f"{REQUIRED_FS}"))

"""Where a break's thrust goes — the house rows and the court's, free body §11d.

``F = min(E·δ/t, σ_y) × A`` with the house taken rigid: the upper bound on force, so the
conservative side of every row here. Load factor 1.0 on T (ACI 318-19 §5.3.6, ASCE 7-16
§2.3.4). Capacities are the most generous the model supports — the whole wall panel, a
concrete-only dead load — so an OVER is a lower bound on the real ratio.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.thermal_break_board import CONCRETE_PCF
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


def wall_patch(ctx, board: Board, sigma: float) -> dict | None:
    """The thrust on the house wall's concrete and on whatever stands above its top."""
    wall = _wall(ctx, board.house_tag)
    ext = z_extent(ctx, board.house_tag)
    if wall is None or ext is None:
        return None
    lo, hi = max(board.bottom_in, ext[0]), min(board.top_in, ext[1])
    on_wall = sigma * board.length_in * max(0.0, hi - lo)
    band = sigma * board.length_in * max(0.0, board.top_in - ext[1])
    span = ext[1] - ext[0]
    full = (hi - lo) >= span - 0.5
    moment = on_wall * span / (8.0 if full else 4.0)
    return dict(wall=wall, on_wall=on_wall, band=band, span=span, full=full, moment=moment,
                bottom_reaction=on_wall / 2.0)


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
    load = "uniform over the span, wL/8" if patch["full"] else "short patch, taken at midspan"
    states.append(LimitState(
        "house wall flexure", patch["moment"], phi_mn, "lb-in",
        f"1.0T: {patch['on_wall']:,.0f} lb on {tag}'s {patch['span']:.2f}\" span ({load}); "
        f"vs the WHOLE {length:.1f}\" panel, #{bar} @ {spacing:.0f}\": As {area:.4f} in2, "
        f"d {d:.4f}\", a {a:.4f}\", phi 0.90 (ACI 318-19 §22.3); soil left out",
        combination="1.0T"))
    vc = PHI_SHEAR * 2.0 * math.sqrt(fc) * length * d
    states.append(LimitState(
        "house wall shear", patch["bottom_reaction"], vc, "lb",
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
    demand = patch["bottom_reaction"] + patch["band"]
    if not anchors:
        missing.append(f"a sill anchorage with a published perpendicular value on "
                       f"{board.house_tag}'s top — the floor line's {demand:,.0f} lb")
        return
    states.append(LimitState(
        "house floor-line reaction", demand, capacity, "lb",
        f"top reaction {patch['bottom_reaction']:,.0f} + the board above the wall top "
        f"{patch['band']:,.0f} lb; vs {len(anchors)} x {anchors[0]} F2 (perpendicular, "
        f"ICC-ES ESR-2555 Table 1, at its C_D 1.6 and SG 0.50 — generous for an SPF sill)",
        combination="1.0T"))


def footing_dead_load(ctx, tags: list[str]) -> tuple[float, float, list[str]]:
    """``(lb, bearing length in, basis)``: each footing and the wall it carries, CONCRETE ONLY
    — a lower bound, the safe side for sliding (framing, floors and roof left off)."""
    total, length, parts = 0.0, 0.0, []
    for tag in tags:
        f = ctx.plan.by_tag(tag)
        solid = next(s for s in ctx.model.solids if s.tag == tag and s.category == "footing")
        xs = [p[0] * _IN for p in solid.outline]
        ys = [p[1] * _IN for p in solid.outline]
        run = max(max(xs) - min(xs), max(ys) - min(ys))
        vol = (max(xs) - min(xs)) * (max(ys) - min(ys)) * (solid.z1_m - solid.z0_m) * _IN
        lb = CONCRETE_PCF * vol / 1728.0
        wall = _wall(ctx, f.under)
        if wall is not None:
            lb += CONCRETE_PCF * _core_in(ctx, f.under) * (wall.z1_m - wall.z0_m) * _IN * \
                _length_in(wall) / 1728.0
        total += lb
        length += run
        parts.append(f"{tag} {lb:,.1f}")
    return total, length, parts


def footing_rows(ctx, board: Board, tags, thrusts, states, missing, inputs) -> None:
    """Sliding and eccentric bearing of the house strip the board bears on.

    ``thrusts`` is ``[(lb, height above the bearing plane in, what)]``.
    """
    from typehaus.engineering.soil import presumptive

    soil = presumptive(getattr(ctx, "soil_class", None))
    if soil is None or not tags:
        missing.append("a soil class and the house footings the board bears on — sliding")
        return
    q_a = getattr(ctx.plan.project.site, "soil_bearing_psf", None) or soil.allowable_bearing_psf
    dead, length, parts = footing_dead_load(ctx, tags)
    h = sum(lb for lb, _z, _w in thrusts)
    moment = sum(lb * z for lb, z, _w in thrusts)
    width = min(ctx.plan.by_tag(t).width.inches for t in tags)
    fs = soil.friction_coefficient * dead / h if h else float("inf")
    what = " + ".join(f"{w} {lb:,.0f}" for lb, _z, w in thrusts)
    inputs += [Quantity("house_dead_load", dead, "lb", 1.0),
               Quantity("house_thrust", h, "lb", 1.0)]
    states.append(LimitState(
        "house footing sliding", REQUIRED_FS, fs, "",
        f"mu {soil.friction_coefficient} (IBC Table 1806.2) x D {dead:,.1f} lb (concrete only: "
        f"{'; '.join(parts)}) / H {h:,.0f} lb ({what})", is_safety_factor=True))
    e_max = (width - dead / (q_a / 144.0 * length)) / 2.0
    states.append(LimitState(
        "house footing bearing", moment / dead, e_max, "in",
        f"e = {moment:,.0f} lb-in / D; Meyerhof B' = B - 2e must carry D at q_a {q_a:,.0f} psf "
        f"over {length:.1f}\" of strip {width:.1f}\" wide"))


def court_sliding(ctx, ref: str, total: float, free_bodies: dict, states, missing) -> None:
    """The thrust's reaction pushes the court away from the house, against its soil."""
    body = free_bodies.get(ref)
    if not body:
        missing.append(f"loop {ref}'s free body — the court's resistance to the thrust")
        return
    rows = [(float(pcf), soil_push, friction, total - soil_push)
            for pcf, (soil_push, friction) in body.items()]
    pcf, soil_push, friction, net = min(
        rows, key=lambda r: r[2] / r[3] if r[3] > 0 else float("inf"))
    fs = friction / net if net > 0 else float("inf")
    states.append(LimitState(
        "court sliding under break thrust", REQUIRED_FS, fs, "",
        f"sum of every board's thrust on loop {ref} {total:,.0f} lb less the retained soil's "
        f"{soil_push:,.0f} lb at {pcf:.0f} pcf, against base friction {friction:,.0f} lb; "
        f"passive not credited", is_safety_factor=True))

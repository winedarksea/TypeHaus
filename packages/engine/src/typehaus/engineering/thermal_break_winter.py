"""Winter: the court contracting on its base, the joint open — free body §11m.2.

The court shrinks 80 °F below its set temperature and slides on its bed toward its own
neutral point. Nothing crosses the open joint, so no board carries anything and the compliant
layer's cap does not enter. What the section of a side line carries is bounded, rigid-plastic,
by what its SOUTH part can mobilise: the loop's base friction less the retained soil pushing
it the same way, ``T = F − 0.9·(K_a/K_0)·H`` shared by the side lines (the soil relaxes to
active as the loop moves off it; 0.9 because it resists, ASCE 7-16 §2.3.1). Two sections:

* each side run, cracked: the bars continuous along it, φ As fy (ACI 318-19 §21.2.2);
* each joint between two runs that NO bar crosses: plain concrete, the footing alone at its
  thickness less 2" (§14.5.1.7) against φ 5 √f'c (§14.5.2.1, the only tension stress
  Chapter 14 lets plain concrete carry — read here for a direct tension, flagged).
"""

from __future__ import annotations

import math

from typehaus.engineering.item import LimitState, Quantity

_IN = 1.0 / 0.0254
PHI_TENSION = 0.90
PHI_PLAIN = 0.60
#: ASCE 7-16 §2.3.1: H counteracting the primary load, permanent.
H_RESISTING_FACTOR = 0.9
SOIL_DEDUCTION_IN = 2.0


def _runs(ctx, structure: set[str], ax: int) -> dict[float, list]:
    """Court walls running along ``ax``, grouped into lines by their cross coordinate:
    ``{across: [(lo, hi, wall tag, footing tag)]}`` sorted along the line."""
    from typehaus.model.structure import Footing

    under = {f.under: f.tag for f in ctx.plan.all_elements()
             if isinstance(f, Footing) and f.under}
    lines: dict[float, list] = {}
    for w in ctx.model.walls:
        if w.tag not in structure or w.tag not in under:
            continue
        (x0, y0), (x1, y1) = w.axis
        d = (x1 - x0, y1 - y0)
        if abs(d[ax]) <= abs(d[1 - ax]):
            continue
        a, b = sorted(((x0, y0)[ax] * _IN, (x1, y1)[ax] * _IN))
        key = round((x0, y0)[1 - ax] * _IN, 1)
        lines.setdefault(key, []).append((a, b, w.tag, under[w.tag]))
    return {k: sorted(v) for k, v in lines.items()}


def _crossing_area(ctx, hosts: set[str] | None, ax: int, at: float,
                   across: tuple[float, float]) -> tuple[float, int]:
    """``(in², count)`` of bars whose path crosses the plane ``ax = at`` inside ``across``;
    ``hosts`` limits the rebar sets read (None: every set)."""
    from typehaus.model.rebar import BARS

    area, count = 0.0, 0
    for rs in ctx.model.rebar:
        if hosts is not None and rs.host_tag not in hosts:
            continue
        for bar in rs.bars:
            along = [p[ax] * _IN for p in bar.path]
            side = [p[1 - ax] * _IN for p in bar.path]
            if min(along) < at < max(along) and across[0] <= min(side) and \
                    max(side) <= across[1]:
                area, count = area + BARS[bar.bar].area_in2, count + 1
    return area, count


def _width(solid, ax: int) -> float:
    vals = [p[1 - ax] * _IN for p in solid.outline]
    return max(vals) - min(vals)


def _footing(ctx, tag):
    return next((s for s in ctx.model.solids if s.tag == tag and s.category == "footing"),
                None)


def winter_rows(ctx, board, free_bodies: dict, soil, states, missing, inputs,
                notes) -> None:
    """The two tension rows for ``board``'s loop, graded at the governing soil weight."""
    from typehaus.engineering.retaining_basis import REINFORCEMENT_FY_PSI
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    body = free_bodies.get(board.loop_ref) if board.loop_ref else None
    if not body or soil is None or not soil.at_rest_efp_psf_per_ft:
        return
    relax = H_RESISTING_FACTOR * soil.active_efp_psf_per_ft / soil.at_rest_efp_psf_per_ft
    pcf, h, friction = max(((float(k), h, f) for k, (h, f) in body.items()),
                           key=lambda r: (r[2] - relax * r[1], -r[0]))
    lines = _runs(ctx, board.structure, board.ax)
    if not lines:
        missing.append(f"the side lines of loop {board.loop_ref} — the court's winter tension")
        return
    total = max(0.0, friction - relax * h)
    demand = total / len(lines)
    inputs += [Quantity("winter_tension", demand, "lb", 1.0)]
    head = (f"80 °F below set, the joint open: loop {board.loop_ref}'s base friction "
            f"{friction:,.0f} lb less {relax:.2f} x its retained soil {h:,.0f} lb "
            f"(K_a/K_0 {soil.active_efp_psf_per_ft:.0f}/{soil.at_rest_efp_psf_per_ft:.0f}, "
            f"x0.9 resisting) at {pcf:.0f} pcf = {total:,.0f} lb over {len(lines)} side lines")
    runs, joints = [], []
    for members in lines.values():
        for lo, hi, wall, foot in members:
            solid = _footing(ctx, foot)
            if solid is None:
                continue
            band = [p[1 - board.ax] * _IN for p in solid.outline]
            area, n = _crossing_area(ctx, {wall, foot}, board.ax, (lo + hi) / 2.0,
                                     (min(band) - 1.0, max(band) + 1.0))
            runs.append((area, n, wall, foot))
        for (_l0, h0, w0, f0), (l1, _h1, w1, f1) in zip(members, members[1:], strict=False):
            if abs(h0 - l1) > 1.0:
                continue
            solids = [s for s in (_footing(ctx, f0), _footing(ctx, f1)) if s is not None]
            band = [p[1 - board.ax] * _IN for s in solids for p in s.outline]
            area, _n = _crossing_area(ctx, None, board.ax, h0, (min(band) - 1.0,
                                                                max(band) + 1.0))
            if area == 0.0:
                joints.append((h0, w0, w1, f0, f1, solids))
    if runs:
        area, n, wall, foot = min(runs)
        inputs.append(Quantity("winter_tension_steel", area, "in2", 0.0001))
        states.append(LimitState(
            "court winter tension, side run", demand,
            PHI_TENSION * area * REINFORCEMENT_FY_PSI, "lb",
            f"{head}. The weakest run, {wall} on {foot}: {n} bars continuous along it, As "
            f"{area:.3f} in², phi 0.90 x fy {REINFORCEMENT_FY_PSI:,.0f} (cracked, concrete "
            f"not credited). Rigid-plastic upper bound; valid while the friction NORTH of the "
            f"run is no more than {total:,.0f} lb (free body §11m.2)", combination="1.0T"))
    graded = []
    for at, w0, w1, f0, f1, solids in joints:
        fc = min(fc_psi(concrete_spec_for(ctx.plan, ctx.plan.by_tag(t))) or 0.0
                 for t in (f0, f1))
        width = min(_width(s, board.ax) for s in solids)
        depth = min((s.z1_m - s.z0_m) * _IN for s in solids) - SOIL_DEDUCTION_IN
        cap = PHI_PLAIN * 5.0 * math.sqrt(fc) if fc else 0.0
        graded.append((demand / (width * depth) / cap if cap else math.inf,
                       at, w0, w1, f0, f1, fc, width, depth, cap))
    if not graded:
        return
    _r, at, w0, w1, f0, f1, fc, width, depth, cap = max(graded)
    inputs.append(Quantity("winter_joint_section", width * depth, "in2", 0.01))
    notes.append(f"WINTER JOINT (free body §11m.2): no bar crosses the {w0}|{w1} joint at "
                 f"{at:.1f}\" — each element's bars stop at its own end cover — so the line "
                 f"is plain there. It holds as one pour; a construction joint at it would "
                 f"need bars lapped through.")
    states.append(LimitState(
        "court winter tension, unreinforced joint", demand / (width * depth), cap, "psi",
        f"{head}; at the {f0}|{f1} joint ({at:.1f}\") no bar crosses: the footing alone, "
        f"{width:.0f}\" x {depth:.0f}\" (thickness less 2\", ACI 318-19 §14.5.1.7), phi 0.60 "
        f"x 5 sqrt(f'c {fc:,.0f}) (§14.5.2.1, read for a direct tension); the stem (a later "
        f"placement) and the base friction's eccentricity not credited",
        combination="1.0T"))

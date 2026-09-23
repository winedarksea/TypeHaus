"""The near footing line in PLAN — free body §11m.1.

The thrust the house wall does not send to its floor line lands on the house's footing line
along the joint. That line is a beam bending about its VERTICAL axis on a Winkler bed — the
slab's perimeter break, ``k = E·depth/t`` per inch — and on point springs wherever a
perpendicular footing chain bears on its inner face and runs unbroken to the far line
(``E_c A / L``). Both are compression only (a gap opens, nothing is bonded), solved by an
active set. The line is PLAIN: ACI 318-19 §14.5.2.1 flexure and §14.5.5.1 shear, on the
thickness less 2" (§14.5.1.7). Left out, each on the safe side for these rows: the line's
own base friction, the passive soil behind it, and the house walls standing on it.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import LimitState, Quantity

_IN = 1.0 / 0.0254
#: Element length, in (load edges and supports are nodes too).
MESH_IN = 0.5
#: How close two concrete faces must be to bear, in.
CONTACT_IN = 0.5
#: ACI 318-19 §19.2.2.1, normal-weight concrete.
EC_PER_ROOT_FC = 57_000.0
PHI_PLAIN = 0.60
#: ACI 318-19 §14.5.1.7: a plain footing's thickness is taken 2" less for strength.
SOIL_DEDUCTION_IN = 2.0
#: The Highload family's E/σ (1,400/40, 2,200/60, 3,700/100 psi; free body §11i) — the
#: modulus of a slab break whose sheet is not stated, flagged ESTIMATED.
E_PER_PSI_ESTIMATE = 35.0


def _span(solid, ax: int) -> tuple[float, float]:
    vals = [p[ax] * _IN for p in solid.outline]
    return min(vals), max(vals)


def _footings(ctx) -> dict:
    from typehaus.model.structure import Footing

    solids = {s.tag: s for s in ctx.model.solids if s.category == "footing"}
    return {f.tag: solids[f.tag] for f in ctx.plan.all_elements()
            if isinstance(f, Footing) and f.tag in solids}


def near_line(ctx, facing: list[str], ax: int, toward: float):
    """``(tags, lo, hi, inner, supports)``: the facing footings grown along the joint by any
    collinear footing that butts them, and each perpendicular chain that bears on the inner
    face and reaches the far line — ``[(station, stiffness, tags)]``."""
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    pool = _footings(ctx)
    line = {t: pool[t] for t in facing if t in pool}
    if not line:
        return None
    across = (min(_span(s, ax)[0] for s in line.values()),
              max(_span(s, ax)[1] for s in line.values()))
    grew = True
    while grew:
        grew = False
        lo = min(_span(s, 1 - ax)[0] for s in line.values())
        hi = max(_span(s, 1 - ax)[1] for s in line.values())
        for tag, s in pool.items():
            a, n = _span(s, 1 - ax), _span(s, ax)
            if tag not in line and abs(n[0] - across[0]) < CONTACT_IN \
                    and abs(n[1] - across[1]) < CONTACT_IN \
                    and (abs(a[0] - hi) < CONTACT_IN or abs(a[1] - lo) < CONTACT_IN):
                line[tag], grew = s, True
    lo = min(_span(s, 1 - ax)[0] for s in line.values())
    hi = max(_span(s, 1 - ax)[1] for s in line.values())
    inner = across[1] if toward > 0 else across[0]

    def runs_across(s):
        a, n = _span(s, 1 - ax), _span(s, ax)
        return (n[1] - n[0]) > (a[1] - a[0])

    def near(n):
        return n[0] if toward > 0 else n[1]

    rest = [s for t, s in pool.items() if t not in line]
    walls = [s for s in rest if not runs_across(s) and (near(_span(s, ax)) - inner) * toward > 0]
    if not walls:
        return list(line), lo, hi, inner, []
    far = min(near(_span(s, ax)) * toward for s in walls) * toward
    supports = []
    for s in (s for s in rest if runs_across(s)):
        a0, a1 = _span(s, 1 - ax)
        n0, n1 = _span(s, ax)
        if not (n0 - CONTACT_IN <= inner <= n1 + CONTACT_IN) or a1 <= lo or a0 >= hi:
            continue
        chain = sorted((_span(o, ax), o.tag) for o in rest if runs_across(o)
                       and abs(_span(o, 1 - ax)[0] - a0) < CONTACT_IN
                       and abs(_span(o, 1 - ax)[1] - a1) < CONTACT_IN)
        reach, used = inner, []
        for (c0, c1), tag in (chain if toward > 0 else chain[::-1]):
            if toward > 0 and c0 <= reach + CONTACT_IN and c1 > reach:
                reach, used = c1, used + [tag]
            elif toward < 0 and c1 >= reach - CONTACT_IN and c0 < reach:
                reach, used = c0, used + [tag]
        fc = fc_psi(concrete_spec_for(ctx.plan, ctx.plan.by_tag(s.tag)))
        if (reach - far) * toward < -CONTACT_IN or fc is None:
            continue            # stops short of the far line (a gap, a door): not a strut
        area = (a1 - a0) * (s.z1_m - s.z0_m) * _IN
        k = EC_PER_ROOT_FC * math.sqrt(fc) * area / abs(far - inner)
        supports.append(((max(a0, lo) + min(a1, hi)) / 2.0, k, tuple(used)))
    return list(line), lo, hi, inner, sorted(set(supports))


def solve(xs, ei, k_bed, springs, q):
    """Hermite beam elements on nodes ``xs``; per-element bed ``k_bed[e]`` and load ``q[e]``
    (lb/in) lumped at the nodes; ``springs {node: k}``. ``(v, moment, shear)`` — deflection
    per node and the largest |moment| and |shear| over the elements. Half-band 3."""
    n, bw = len(xs), 3
    size = 2 * n
    a = [[0.0] * (2 * bw + 1) for _ in range(size)]
    f = [0.0] * size
    for e in range(n - 1):
        h = xs[e + 1] - xs[e]
        c = ei / h ** 3
        ke = ((12, 6 * h, -12, 6 * h), (6 * h, 4 * h * h, -6 * h, 2 * h * h),
              (-12, -6 * h, 12, -6 * h), (6 * h, 2 * h * h, -6 * h, 4 * h * h))
        dofs = (2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3)
        for i in range(4):
            for j in range(4):
                a[dofs[i]][dofs[j] - dofs[i] + bw] += c * ke[i][j]
        for node in (e, e + 1):
            a[2 * node][bw] += k_bed[e] * h / 2.0
            f[2 * node] += q[e] * h / 2.0
    for node, k in springs.items():
        a[2 * node][bw] += k
    for i in range(size):
        for r in range(i + 1, min(size, i + bw + 1)):
            factor = a[r][i - r + bw] / a[i][bw]
            if factor:
                for col in range(i, min(size, i + bw + 1)):
                    a[r][col - r + bw] -= factor * a[i][col - i + bw]
                f[r] -= factor * f[i]
    u = [0.0] * size
    for i in range(size - 1, -1, -1):
        u[i] = (f[i] - sum(a[i][col - i + bw] * u[col]
                           for col in range(i + 1, min(size, i + bw + 1)))) / a[i][bw]
    v, th = u[0::2], u[1::2]
    moment = shear = 0.0
    for e in range(n - 1):
        h, dv = xs[e + 1] - xs[e], v[e + 1] - v[e]
        m1 = ei / h ** 2 * (6 * dv - 4 * h * th[e] - 2 * h * th[e + 1])
        m2 = ei / h ** 2 * (-6 * dv + 2 * h * th[e] + 4 * h * th[e + 1])
        s = ei / h ** 3 * (-12 * dv + 6 * h * (th[e] + th[e + 1]))
        # A lumped element's shear is its mid value; its ends differ by the net line load.
        net = abs(q[e] - k_bed[e] * (v[e] + v[e + 1]) / 2.0) * h / 2.0
        moment, shear = max(moment, abs(m1), abs(m2)), max(shear, abs(s) + net)
    return v, moment, shear


def share(ctx, found, loads, bed, edge: tuple[float, float]) -> dict:
    """Solve the near line under ``loads`` [(lo, hi, lb/in)] on a compression-only bed
    ``bed`` lb/in² over ``edge`` and compression-only struts."""
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    tags, lo, hi, _inner, supports = found
    pool = _footings(ctx)
    line = [pool[t] for t in tags]
    along = 1 if _span(line[0], 1)[1] - _span(line[0], 1)[0] > \
        _span(line[0], 0)[1] - _span(line[0], 0)[0] else 0
    width = min(_span(s, 1 - along)[1] - _span(s, 1 - along)[0] for s in line)
    depth = min((s.z1_m - s.z0_m) * _IN for s in line)
    fc = min(fc_psi(concrete_spec_for(ctx.plan, ctx.plan.by_tag(t))) or 0.0 for t in tags)
    ei = EC_PER_ROOT_FC * math.sqrt(fc) * depth * width ** 3 / 12.0
    steps = int(round((hi - lo) / MESH_IN))
    marks = {lo + i * (hi - lo) / steps for i in range(steps + 1)}
    marks |= {x for a, b, _ in loads for x in (a, b) if lo <= x <= hi}
    marks |= {s[0] for s in supports}
    xs = sorted({round(x, 6) for x in marks})
    nodes = {s[0]: min(range(len(xs)), key=lambda i, x=s[0]: abs(xs[i] - x)) for s in supports}

    mids = [(xs[e] + xs[e + 1]) / 2.0 for e in range(len(xs) - 1)]
    q = [sum(w for a, b, w in loads if a <= x <= b) for x in mids]
    on_edge = [bed if edge[0] <= x <= edge[1] else 0.0 for x in mids]
    off, live = set(), list(supports)
    for _ in range(40):
        k_bed = [0.0 if e in off else k for e, k in enumerate(on_edge)]
        v, moment, shear = solve(xs, ei, k_bed, {nodes[s[0]]: s[1] for s in live}, q)
        new_off = {e for e in range(len(mids)) if v[e] + v[e + 1] < 0.0}
        kept = [s for s in supports if v[nodes[s[0]]] >= 0.0]
        if new_off == off and kept == live:
            break
        off, live = new_off, kept
    reactions = {s[0]: s[1] * v[nodes[s[0]]] for s in live}
    peak = max(range(len(xs)), key=lambda i: v[i])
    return dict(tags=tags, lo=lo, hi=hi, width=width, depth=depth, fc=fc, ei=ei, bed=bed,
                load=sum((b - a) * w for a, b, w in loads), reactions=reactions,
                struts=[s for s in supports], peak_in=v[peak], peak_at=xs[peak],
                moment=moment, shear=shear,
                lifted=sum(xs[e + 1] - xs[e] for e in off if on_edge[e]))


def line_rows(result: dict, brk, edge_e: float, estimated: bool, psi_cap: tuple[float, str],
              *, states, inputs) -> None:
    """Plan flexure and shear of the plain line, and the break's peak stress."""
    b = result["depth"] - SOIL_DEDUCTION_IN
    h, root = result["width"], math.sqrt(result["fc"])
    phi_mn = PHI_PLAIN * 5.0 * root * b * h ** 2 / 6.0
    phi_vn = PHI_PLAIN * 4.0 / 3.0 * root * b * h
    struts = ", ".join(f"{'+'.join(t)} at {x:.1f}\"" for x, _k, t in result["struts"]) or "none"
    carried = ", ".join(f"{x:.1f}\" {r:,.0f} lb" for x, r in result["reactions"].items()) \
        or "none bear — the line's ends lift off them"
    inputs += [Quantity("near_line_width", h, "in", 0.01),
               Quantity("near_line_fc", result["fc"], "psi", 1.0),
               Quantity("slab_edge_modulus", edge_e, "psi", 1.0)]
    basis = (f"{'+'.join(result['tags'])} ({result['lo']:.0f}..{result['hi']:.0f}\", "
             f"{h:.0f}\" x {result['depth']:.0f}\" plain, f'c {result['fc']:,.0f}) under "
             f"{result['load']:,.0f} lb, a beam in plan on the slab break's bed "
             f"{result['bed']:,.1f} lb/in² (E {edge_e:,.0f}"
             f"{' ESTIMATED' if estimated else ''} x {result['edge_depth']:g}\" / "
             f"{brk.thickness.inches:g}\") and struts "
             f"[{struts}], both compression only; struts carrying: {carried}")
    states.append(LimitState(
        "house near-line plan flexure", result["moment"], phi_mn, "lb-in",
        f"{basis}. phi 0.60 x 5 sqrt(f'c) x {b:g}\" x {h:g}\"²/6 (ACI 318-19 §14.5.2.1, "
        f"thickness less 2\" per §14.5.1.7); base friction, passive and the walls on it "
        f"not credited", combination="1.0T"))
    states.append(LimitState(
        "house near-line plan shear", result["shear"], phi_vn, "lb",
        f"the same line: phi 0.60 x 4/3 sqrt(f'c) x {b:g}\" x {h:g}\" (ACI 318-19 §14.5.5.1)",
        combination="1.0T"))
    peak = edge_e * result["peak_in"] / brk.thickness.inches
    cap, how = psi_cap
    states.append(LimitState(
        "house slab-edge peak " + ("sustained load" if brk.sustained_load_fraction and
                                   brk.psi is not None else "bearing"),
        peak, cap, "psi",
        f"the break's largest stress on the near line (free body §11m.1): E {edge_e:,.0f} x "
        f"{result['peak_in']:.5f}\" / {brk.thickness.inches:g}\" at {result['peak_at']:.1f}\"; "
        f"vs {how}"))

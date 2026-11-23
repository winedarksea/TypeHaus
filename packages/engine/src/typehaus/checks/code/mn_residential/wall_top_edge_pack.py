"""A stair well's edge pack as the wall-top restraint (Minn. R. 1309.0404, Table R404.1(1) fn. f).

Footnote f asks for "full depth 2-inch blocking or approved equivalent" in the first three joist
spaces. Where a floor opening fills them (catlin ``FO-M-STAIR`` against ``W-B-N2``) no block
can stand, so the doubled trimmer along the wall takes the wall-top reaction as a HORIZONTAL
beam: its flat face is the beam's depth. Graded here, oracled by hand in
``notes/main_floor_truss_basis.md`` §4a:

* bending and shear in plank (face) orientation, ICC-ES ESR-1387 Table 1 and fn. 7 — no
  repetitive-member credit, the plies are taken as one thickness;
* the ties from the sill to the pack, the authored ``Connector``s that name the floor and
  the wall, at their catalog lateral;
* the end reactions, returned to the caller to add to the neighbouring runs' end stations.

Deflection is printed, not graded: Table R404.1(1) states no limit for the restraint.
"""

from __future__ import annotations

import math

from typehaus.joints.wall_top import along_wall
from typehaus.resolve.framing.profiles import cross_section

_M_PER_IN = 0.0254
_M_PER_FT = 0.3048
#: NDS Table 2.3.2: soil pressure is a permanent load, C_D 0.9.
_CD = 0.9
#: How far from the wall face the pack's ply may stand: footnote f's three joist spaces.
_REACH_IN = 48.0

#: ESR-1387 Table 1, Microllam LVL 2.0E-2600Fb WS, FACE/PLANK ORIENTATION, dry: Fb 2,690,
#: Fv 190 psi; E 2.0e6 (both orientations). Fn. 7: C_V = (1.75/t)^0.136 <= 1 for plank Fb
#: (t = member thickness, in.). Read 2026-11-23 from the report's own PDF.
_PLANK_FB_PSI, _PLANK_FV_PSI, _E_PSI = 2690.0, 190.0, 2.0e6
_SOURCE = "ESR-1387 Table 1 (Microllam 2.0E-2600Fb WS plank) + fn. 7"


def edge_pack_lines(ctx, run, reaction_plf: float, connectors, tie_capacity_lb) -> tuple:
    """Grade the trimmer pack of ``run``'s floor along ``run.wall_tag`` as the restraint.
    ``tie_capacity_lb`` is the caller's catalog read (``foundation_wall_top``). Returns
    ``(ok lines, short lines)``."""
    head = f"{run.floor_tag} parallel"
    wall = ctx.model.wall(run.wall_tag)
    floor = next((f for f in ctx.model.floors if f.tag == run.floor_tag), None)
    pack = _pack(wall, floor) if floor is not None and wall is not None else []
    if not pack:
        return [], [f"{head}: UNKNOWN — a floor opening fills the first three joist "
                    "spaces and no trimmer pack stands along the wall to take its "
                    "restraint; an approved-equivalent design"]
    profile = pack[0].profile
    if profile.split()[-1:] != ["LVL"]:
        return [], [f"{head}: UNKNOWN — the edge pack is {profile}, and only "
                    f"Microllam LVL's plank values are held ({_SOURCE})"]
    section = cross_section(profile)
    t_in = len(pack) * section.width_m / _M_PER_IN
    d_in = section.depth_m / _M_PER_IN
    alongs = [along_wall(wall, p)[0] for m in pack for p in (m.p0, m.p1)]
    lo, hi = min(alongs), max(alongs)
    span_ft = (hi - lo) / _M_PER_FT
    w = reaction_plf
    moment_lb_in = w * span_ft ** 2 / 8.0 * 12.0
    shear_lb = w * span_ft / 2.0
    modulus = d_in * t_in ** 2 / 6.0  # in^3; the bending plane is the pack's thickness
    cv = min(1.0, (1.75 / t_in) ** 0.136)
    fb, fb_allow = moment_lb_in / modulus, _PLANK_FB_PSI * cv * _CD
    fv, fv_allow = 1.5 * shear_lb / (t_in * d_in), _PLANK_FV_PSI * _CD
    inertia = d_in * t_in ** 3 / 12.0
    w_in = w / 12.0
    delta = (5 * w_in * (span_ft * 12.0) ** 4 / (384 * _E_PSI * inertia)
             + 28.8 * w * span_ft ** 2 / (_E_PSI * d_in * t_in))
    lines = [f"{head}: edge pack {len(pack)}-ply {profile} ({t_in:.2f}\" thick) spans "
             f"{span_ft:.2f} ft flat under {w:.0f} plf: M {moment_lb_in / 12:.0f} lb-ft, "
             f"fb {fb:.0f} / {fb_allow:.0f} psi (d/c {fb / fb_allow:.2f}), "
             f"fv {fv:.0f} / {fv_allow:.0f} psi (d/c {fv / fv_allow:.2f}), "
             f"delta {delta:.2f}\" = L/{span_ft * 12 / delta:.0f} ({_SOURCE})"]
    short = []
    if fb > fb_allow or fv > fv_allow:
        short.append(f"{head}: the edge pack is over its plank capacity")
    demand = w * span_ft
    along = [(along_wall(wall, xy)[0], part, connects) for xy, part, connects, _laid, _under
             in connectors]
    floors = {f.tag for f in ctx.model.floors} - {run.floor_tag}

    def tied(wanted, lo_m, hi_m, need_lb, what):
        """The ties named by ``wanted`` in ``lo_m..hi_m`` against ``need_lb``."""
        mine = [part for at, part, connects in along if lo_m - 1e-6 <= at <= hi_m + 1e-6
                and wanted(connects)]
        capacity = 0.0
        for part in mine:
            each, why = tie_capacity_lb(part, profile)
            if each is None:
                return f"{head}: UNKNOWN — {why}", True
            capacity += each
        if capacity + 1e-6 < need_lb:
            return (f"{head}: {need_lb:.0f} lb {what} against {len(mine)} tie(s), "
                    f"{capacity:.0f} lb"), True
        return (f"{head}: {len(mine)} ties x {capacity / len(mine):.0f} lb = {capacity:.0f} lb "
                f"against {need_lb:.0f} lb {what}, d/c {need_lb / capacity:.2f}"), False

    reach = 12.0 * _M_PER_IN
    checks = [(lambda c: {run.floor_tag, run.wall_tag} <= c, lo, hi, demand,
               f"wall-top load into the pack (ties naming {run.floor_tag} and {run.wall_tag})")]
    checks += [(lambda c: run.floor_tag in c and bool(c & floors), at - reach, at + reach,
                shear_lb, f"end reaction into the neighbouring floor at {at / _M_PER_FT:.1f} ft "
                "(ties naming both floors)") for at in (lo, hi)]
    for wanted, a, b, need, what in checks:
        line, bad = tied(wanted, a, b, need, what)
        (short if bad else lines).append(line)
    return lines, short


def _pack(wall, floor) -> list:
    """The trimmers parallel to the wall nearest it, touching ply to ply."""
    cands = []
    for m in floor.members:
        if m.category != "trimmer":
            continue
        a, off_a = along_wall(wall, m.p0)
        b, off_b = along_wall(wall, m.p1)
        if abs(off_a - off_b) > 1e-6 or abs(a - b) < 1e-6:
            continue
        if off_a <= _REACH_IN * _M_PER_IN + wall.thickness_m / 2.0:
            cands.append((off_a, m))
    if not cands:
        return []
    cands.sort(key=lambda c: c[0])
    pack, edge = [cands[0][1]], cands[0][0]
    for off, member in cands[1:]:
        gap = off - edge
        ply = cross_section(member.profile).width_m
        if math.isclose(gap, ply, abs_tol=_M_PER_IN / 16) and member.profile == pack[0].profile:
            pack.append(member)
            edge = off
    return pack

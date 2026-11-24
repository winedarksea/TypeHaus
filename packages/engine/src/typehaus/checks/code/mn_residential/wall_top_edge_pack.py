"""A stair well's edge pack as the wall-top restraint (Minn. R. 1309.0404, Table R404.1(1) fn. f).

Footnote f asks for "full depth 2-inch blocking or approved equivalent" in the first three joist
spaces. Where a floor opening fills them (catlin ``FO-M-STAIR`` against ``W-B-N2``) no block
can stand, so the doubled trimmer along the wall takes the wall-top reaction as a HORIZONTAL
beam: its flat face is the beam's depth. Graded here, oracled by hand in
``notes/main_floor_truss_basis.md`` §4a:

* bending and shear in plank (face) orientation, ICC-ES ESR-1387 Table 1 and fn. 7. **Plies
  loaded flatwise do not act compositely** (the load is perpendicular to their glue-free
  interface; ESR-1387's 3.5" column is one billet), so S = n b t_ply^2 / 6 and C_V is the
  ply's, never the stack's;
* the plies' own fastening, which hands the outside ply's load to the others: TJ-9000 July
  2026 p.28 L17, "Maximum Uniform Load Applied to Either Outside Member", read from the
  ``JoistReinforcement.fastening`` the plan authors;
* the ties from the sill to the pack, the authored ``Connector``s that name the floor and the
  wall, at their catalog lateral through the fastener the plan's connector schedule installs
  (``connector_schedules``: A35Z takes SD9112 screws, the row's own), reduced by the species of
  BOTH members the tie joins (the sill's, and the pack's or the neighbouring floor's);
* the end reactions into the neighbouring floors, on the ties that name both floors.

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
#: (t = member thickness, in.): 1.0 for one 1.75" ply. Read 2026-11-23 from the report's PDF.
_PLANK_FB_PSI, _PLANK_FV_PSI, _E_PSI = 2690.0, 190.0, 2.0e6
_SOURCE = "ESR-1387 Table 1 (Microllam 2.0E-2600Fb WS plank) + fn. 7"

#: TJ-9000 (July 2026) p.28 L17, Simpson SDW22, one face, 2 rows: max uniform load on either
#: outside member, plf at 100% stress, by assembly (A: 3 1/2" wide 2-ply, 3 3/8" screw; B: 5 1/4"
#: wide 3-ply, 5" screw) and on-centre spacing. Fn. 3: 24" values double at 12".
_SDW22 = {2: {24.0: 800.0, 19.2: 1000.0, 16.0: 1200.0},
          3: {24.0: 450.0, 19.2: 565.0, 16.0: 675.0}}
_SDW22_SCREW = {2: '3 3/8"', 3: '5"'}
_PLY_SOURCE = "TJ-9000 July 2026 p.28 L17, Simpson SDW22, 2 rows, one face"


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
    if profile.split()[-1:] != ["LVL"] or any(m.profile != profile for m in pack):
        held = ", ".join(sorted({m.profile for m in pack}))
        return [], [f"{head}: UNKNOWN — the edge pack is {held}, and only 1.75\" Microllam LVL "
                    f"plies' plank values are held ({_SOURCE})"]
    section = cross_section(profile)
    plies = len(pack)
    t_in = section.width_m / _M_PER_IN  # ONE ply: the plies do not act as a single section
    d_in = section.depth_m / _M_PER_IN
    alongs = [along_wall(wall, p)[0] for m in pack for p in (m.p0, m.p1)]
    lo, hi = min(alongs), max(alongs)
    span_ft = (hi - lo) / _M_PER_FT
    w = reaction_plf
    moment_lb_in = w * span_ft ** 2 / 8.0 * 12.0
    shear_lb = w * span_ft / 2.0
    modulus = plies * d_in * t_in ** 2 / 6.0  # in^3: n separate plies bent flat
    cv = min(1.0, (1.75 / t_in) ** 0.136)
    fb, fb_allow = moment_lb_in / modulus, _PLANK_FB_PSI * cv * _CD
    fv, fv_allow = 1.5 * shear_lb / (plies * t_in * d_in), _PLANK_FV_PSI * _CD
    inertia = plies * d_in * t_in ** 3 / 12.0
    delta = (5 * (w / 12.0) * (span_ft * 12.0) ** 4 / (384 * _E_PSI * inertia)
             + 28.8 * w * span_ft ** 2 / (_E_PSI * d_in * plies * t_in))
    lines = [f"{head}: edge pack {plies} x {profile} plies, not composite, spans {span_ft:.2f} ft "
             f"flat under {w:.0f} plf: M {moment_lb_in / 12:.0f} lb-ft, S {modulus:.2f} in^3, "
             f"fb {fb:.0f} / {fb_allow:.0f} psi (d/c {fb / fb_allow:.2f}), "
             f"fv {fv:.0f} / {fv_allow:.0f} psi (d/c {fv / fv_allow:.2f}), "
             f"delta {delta:.2f}\" = L/{span_ft * 12 / delta:.0f}, no limit in the row "
             f"({_SOURCE})"]
    short = []
    if fb > fb_allow or fv > fv_allow:
        short.append(f"{head}: the edge pack is over its plank capacity")
    # The outside ply takes the whole load; its fastening hands it to the others.
    line, bad = _ply_fastening(ctx, run, plies, w, lo, hi, head)
    (short if bad else lines).append(line)
    along = [(along_wall(wall, xy)[0], part, connects) for xy, part, connects, _laid, _under
             in connectors]
    floors = {f.tag for f in ctx.model.floors} - {run.floor_tag}
    demand = w * span_ft
    sill_factor, sill_words = _sill(ctx.model, run.wall_tag)

    def tied(wanted, lo_m, hi_m, need_lb, what, other_profile):
        """The ties named by ``wanted`` in ``lo_m..hi_m`` against ``need_lb``."""
        mine = [(part, connects) for at, part, connects in along
                if lo_m - 1e-6 <= at <= hi_m + 1e-6 and wanted(connects)]
        capacity, rows = 0.0, set()
        for part, connects in mine:
            other = other_profile(connects)
            each, why = tie_capacity_lb(part, profile)
            if each is None:
                return f"{head}: UNKNOWN — {why}", True
            if other is None:
                each *= min(1.0, sill_factor)  # the sill's species (pack side already in `each`)
            else:
                far, why = tie_capacity_lb(part, other)
                each = min(each, far if far is not None else 0.0)
            capacity += each
            rows.add(_fastener_row(part))
        if None in rows or any(r.startswith("UNKNOWN") for r in rows):
            return f"{head}: UNKNOWN — {sorted(r for r in rows if r)}", True
        tag = "; ".join(sorted(rows))
        if capacity + 1e-6 < need_lb:
            return (f"{head}: {need_lb:.0f} lb {what} against {len(mine)} tie(s), "
                    f"{capacity:.0f} lb ({tag})"), True
        return (f"{head}: {len(mine)} ties = {capacity:.0f} lb against {need_lb:.0f} lb {what}, "
                f"d/c {need_lb / capacity:.2f} ({tag})"), False

    def neighbour_profile(connects):
        for tag in connects:
            if tag in floors:
                return next((m.profile for f in ctx.model.floors if f.tag == tag
                             for m in f.members if m.category == "joist"), None)
        return None

    reach = 12.0 * _M_PER_IN
    checks = [(lambda c: {run.floor_tag, run.wall_tag} <= c, lo, hi, demand,
               f"wall-top load into the pack (ties naming {run.floor_tag} and {run.wall_tag}; "
               f"{sill_words})", lambda c: None)]
    checks += [(lambda c: run.floor_tag in c and bool(c & floors), at - reach, at + reach,
                shear_lb, f"end reaction into the neighbouring floor at {at / _M_PER_FT:.1f} ft "
                "(ties naming both floors, at the lesser species of the two)",
                neighbour_profile) for at in (lo, hi)]
    for wanted, a, b, need, what, other in checks:
        line, bad = tied(wanted, a, b, need, what, other)
        (short if bad else lines).append(line)
    return lines, short


def _ply_fastening(ctx, run, plies: int, load_plf: float, lo: float, hi: float, head: str):
    """``(line, short)``: the authored ply fastening against TJ-9000 L17's row."""
    spec = ctx.plan.by_tag(run.floor_tag)
    entry = next((r.fastening for r in getattr(spec, "reinforcements", ())
                  if getattr(r, "fastening", None) is not None), None)
    table = _SDW22.get(plies)
    if entry is None:
        return f"{head}: UNKNOWN — the {plies} plies' fastening is not authored", True
    if table is None or entry.fastener != "screw" or entry.faces != "one" or entry.rows != 2:
        return (f"{head}: UNKNOWN — only 2 rows of SDW22 screws on one face have a TJ-9000 L17 "
                f"row here ({plies} plies, {entry.rows} rows of {entry.fastener}, "
                f"{entry.faces} face)"), True
    spacing = round(entry.spacing.meters / _M_PER_IN, 1)
    base = table.get(spacing)
    if base is None:
        return f"{head}: UNKNOWN — L17 has no {spacing}\" o.c. column", True
    capacity = base * _CD
    text = (f"{head}: plies' SDW22 {_SDW22_SCREW[plies]} screws, 2 rows one face at "
            f"{spacing:g}\": {base:.0f} x {_CD} = {capacity:.0f} plf against {load_plf:.0f} plf "
            f"on the outside ply, d/c {load_plf / capacity:.2f} ({_PLY_SOURCE})")
    return text, load_plf > capacity + 1e-9


def _fastener_row(part: str) -> str:
    """The fastener the plan's connector schedule installs, against the row the catalog grades.
    ``""`` where the part has no schedule (the allowable's own fasteners stand)."""
    from typehaus.hardware.catalog import hardware_by_model
    from typehaus.library.hardware.connector_schedules import CONNECTOR_FASTENERS

    schedule = CONNECTOR_FASTENERS.get(part)
    item = hardware_by_model(part)
    row = getattr(getattr(item, "allowable", None), "fasteners", "") or ""
    if schedule is None:
        return f"{part}: {row}" if row else ""
    models = sorted({model for _count, model, _where in schedule.fasteners})
    if not all(model in row for model in models):
        return f"UNKNOWN: {part} installs {', '.join(models)} but its row is {row!r}"
    return f"{part} with {', '.join(models)} screws, the row's own ({row})"


def _sill(model, wall_tag: str) -> tuple[float, str]:
    """``(species factor, words)`` of the sill plate the wall's floors tie to: SG >= 0.50
    (ESR-3096 s.3.2.2) reads the DF/SP column unreduced; anything else the SPF/HF 0.86."""
    ret = next((r for r in model.construction_returns
                if r.applies_to == "wall:framed_on_concrete" and r.element_tags
                and r.element_tags[0] == wall_tag), None)
    material = getattr(ret, "material_ref", None)
    if material and "syp" in material:
        return 1.0, f"sill {material}, southern pine SG >= 0.50"
    return 0.86, f"sill {material or 'unstated'} read as SPF/HF, x 0.86"


def _pack(wall, floor) -> list:
    """The plies parallel to the wall nearest it, touching face to face: the trimmers and
    any sistered ply (``JoistReinforcement``) laid against them."""
    cands = []
    for m in floor.members:
        if m.category not in ("trimmer", "sister_joist"):
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
        if math.isclose(gap, ply, abs_tol=_M_PER_IN / 4) and member.profile == pack[0].profile:
            pack.append(member)
            edge = off
    return pack

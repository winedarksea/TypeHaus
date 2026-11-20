"""Every cast-in STHD against the ESR-2920 Table 1 row its concrete is read at.

A published table is a prescriptive read: the row applies when the strap is installed the
way the report tested it (Figure 1, §4.2). Read off the placed strap
(``ResolvedModel.embedded_straps`` via ``resolve/strap_holdowns.py``), per strap:

* **stem** — the concrete ahead of the cast-in strap along its spoon, from its entry to the
  far face: the 8" row where that is >= 8", the 6" row where >= 6", else no row. Figure 1
  casts the strap at a face with the spoon across the stem; a strap entering inside the
  core has more concrete behind it than that, never less.
* **jog** — a strap cast at one face and offset over the pour top to framing elsewhere is
  UNKNOWN: no figure prints it (``esr2920.JOG_RULE``), and the jog straightens under load.
* **embedment** — pour top to the toe >= le, and the pour below the top (with a footing
  only where it is ``cast_with_wall``) at least le: no cold joint within it (C-C-2026 p. 66).
* **clear span** — pour top to the first nailed vertical <= 17" for an RJ; a standard strap
  is read over Figure 1's one 2x sill, and more is UNKNOWN (``esr2920.max_clear_span_in``).
* **location** — midwall where both ends are >= 1.5 le off (fn. 7), else corner where the
  concrete turns, else endwall; corner and endwall need 1/2" end distance (Figure 1).
* **rebar** — a No. 4 or larger bar 3-5" below the top passing the strap, 2 le each side
  (midwall) or past it (corner, endwall), and a corner's return leg (§4.2, Figure 1).
* **spacing** — straps on parallel lines 3 le apart (fn. 7); a perpendicular pair resists
  the two plan directions IRC R602.10.1 grades separately.
* **f'c** >= 2,500 psi (§3.2.5).

Capacity is the cracked Wind/SDC A&B column (fn. 6: detached dwellings through SDC C), the
lowest of every size an unsized family could be bought as. Demand, where this model states
one: a braced wall panel's ``hold_down_ref`` needs 800 lb (IRC Figure R602.10.7).
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed, unknown
from typehaus.hardware import esr2920 as esr
from typehaus.quantities import M_PER_IN

_ID = "structural.strap_hold_down_embedment"
_CODE = "ICC-ES ESR-2920 Table 1, Figure 1, §3.2.5, §4.2 (IRC R104.11)"
_TOL_IN = 1.0 / 16.0
_BAR_TOL_IN = 0.5


def _intervals(bars, origin, axis, across, half_m, top_z_m) -> list[tuple[float, float]]:
    """In-band bar runs lying along ``axis`` within ``half_m`` of the line through ``origin``."""
    from typehaus.resolve.rebar.strap_bars import in_band

    out = []
    for bar in bars:
        if not in_band(bar, top_z_m):
            continue
        for a, b in zip(bar.path, bar.path[1:], strict=False):
            ua = (a[0] - origin[0]) * axis[0] + (a[1] - origin[1]) * axis[1]
            ub = (b[0] - origin[0]) * axis[0] + (b[1] - origin[1]) * axis[1]
            na = (a[0] - origin[0]) * across[0] + (a[1] - origin[1]) * across[1]
            nb = (b[0] - origin[0]) * across[0] + (b[1] - origin[1]) * across[1]
            if abs(na) <= half_m and abs(nb) <= half_m and abs(ub - ua) > 1e-6:
                out.append((min(ua, ub), max(ua, ub)))
    out.sort()
    merged: list[list[float]] = []
    for lo, hi in out:
        if merged and lo <= merged[-1][1] + 0.25 * M_PER_IN:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return [(lo, hi) for lo, hi in merged]


def _reach(intervals, at_m: float, tol_m: float) -> tuple[float, float] | None:
    return next(((lo, hi) for lo, hi in intervals if lo - tol_m <= at_m <= hi + tol_m), None)


def _turn(site, end, bars) -> tuple[float, float]:
    """``(|u| to the corner m, return leg in)`` of the bar where ``end`` turns a corner."""
    d, c = site.strap.along_xy, site.centre_xy
    offs = [(p[0] - c[0]) * d[0] + (p[1] - c[1]) * d[1] for p in end.turn_core]
    u_turn = (min(offs) + max(offs)) / 2.0
    corner = (c[0] + d[0] * u_turn, c[1] + d[1] * u_turn)
    width = max(abs(o - u_turn) for o in offs)
    leg = _reach(_intervals(bars, corner, end.turn_to, d, width, site.top_z_m), 0.0, width)
    return abs(u_turn), (leg[1] / M_PER_IN if leg is not None else 0.0)


def _rebar(site, bars, le_in: float, location: str, size: str) -> str | None:
    """``None`` when Figure 1's bar is there, else what is missing. A bar turning a corner
    counts its return toward the 2 le on that side."""
    s, d, c = site.strap.spoon_xy, site.strap.along_xy, site.centre_xy
    half = (site.behind_in + site.ahead_in) / 2.0 * M_PER_IN
    span = _reach(_intervals(bars, c, d, s, half, site.top_z_m), 0.0, 0.0)
    if span is None:
        return (f"no No. {esr.MIN_BAR} bar {esr.BAR_BAND_IN[0]:g}-{esr.BAR_BAND_IN[1]:g} in "
                f"below the top passes it")
    want = esr.REBAR_LE * le_in
    got = {-1.0: -span[0] / M_PER_IN, 1.0: span[1] / M_PER_IN}
    legs = {}
    for end in site.ends:
        legs[end.sign] = 0.0
        if end.turn_to is not None:
            to_corner, leg_in = _turn(site, end, bars)
            if got[end.sign] * M_PER_IN >= to_corner - _BAR_TOL_IN * M_PER_IN:
                legs[end.sign] = leg_in
    near = min(site.ends, key=lambda e: e.distance_in)
    sides = (-1.0, 1.0) if location == "midwall" else (-near.sign,)
    short = [f"{got[k] + legs[k]:.1f} in" for k in sides
             if got[k] + legs[k] < want - _BAR_TOL_IN]
    if short:
        return f"its bar runs {', '.join(short)} past it, under the {want:.0f} in (2 le)"
    leg_want = esr.CORNER_LEG_IN.get(size) or want
    if location == "corner" and legs[near.sign] < leg_want - _BAR_TOL_IN:
        return (f"its corner return is {legs[near.sign]:.1f} in, under Figure 1's "
                f"{leg_want:.0f} in leg")
    return None


def _location(site, le_in: float) -> tuple[str, float]:
    near = min(site.ends, key=lambda e: e.distance_in)
    if near.distance_in >= esr.MIDWALL_END_LE * le_in - _TOL_IN:
        return "midwall", near.distance_in
    return ("corner" if near.turn_to is not None else "endwall"), near.distance_in


def _demands(model) -> dict[str, float]:
    """``tag -> lb`` this model states for a strap: a braced panel's end hold-down."""
    from typehaus.checks.structural._r602_bracing_table import MIN_END_HOLDOWN_LB
    from typehaus.model.braced_wall import BracedWallPanel

    return {el.hold_down_ref: MIN_END_HOLDOWN_LB for el in model.plan.all_elements()
            if isinstance(el, BracedWallPanel) and el.hold_down_ref}


def _grade(model, site, bars, demand: float | None, sites) -> Finding:
    from typehaus.resolve.concrete import concrete_spec_for
    from typehaus.resolve.connector_geometry.embedded_straps import first_stud_z_m

    strap = site.strap
    tags = (strap.tag, strap.core_tag)
    sizes = esr.sizes(strap.part)
    if not sizes:
        return unknown(_ID, f"{strap.tag}: {strap.part} is not an ESR-2920 Table 1 model",
                       tags, code=_CODE)
    problems: list[str] = []
    stem = next((t for t in esr.STEM_THICKNESSES_IN if site.ahead_in >= t - _TOL_IN), None)
    if stem is None or site.behind_in < -_TOL_IN:
        problems.append(f"{site.ahead_in:.2f} in of concrete ahead of the strap; Table 1 "
                        f"starts at a 6 in stem with the strap cast at a face")
    le = max(esr.TABLE_1[(6, s)].le_in for s in sizes)
    toe_z = strap.line_z_m - strap.embedment_in * M_PER_IN
    provided = (site.top_z_m - toe_z) / M_PER_IN
    if provided < le - _TOL_IN:
        problems.append(f"{provided:.2f} in embedded below the pour top, under le {le:g} in")
    pour = (site.top_z_m - site.pour_bottom_z_m) / M_PER_IN
    if pour < le - _TOL_IN:
        problems.append(f"the pour is {pour:.2f} in deep to its cold joint, under le {le:g} in "
                        f"({esr.COLD_JOINT_RULE})")
    lo_proj = max(esr.SPOON_PROJECTION_IN[s][0] for s in sizes)
    if strap.projection_in < lo_proj - _TOL_IN:
        problems.append(f"the spoon is bent to {strap.projection_in:.2f} in, short of "
                        f"Figure 1's {lo_proj:g} in")
    framed = model.wall(strap.framed_tag) if strap.framed_tag else None
    first = first_stud_z_m(framed, strap.leaf_xy) if framed is not None else None
    clear = (first - site.top_z_m) / M_PER_IN if first is not None else None
    unread: list[str] = []
    if clear is not None and clear > esr.max_clear_span_in(strap.part) + _TOL_IN:
        if esr.is_rim_joist(strap.part):
            problems.append(f"{clear:.2f} in unnailed from the pour top to the first stud, over "
                            f"the RJ's {esr.RJ_CLEAR_SPAN_MAX_IN:g} in")
        else:
            unread.append(f"{clear:.2f} in unnailed to the first stud: Figure 1 draws a "
                          f"standard strap over one 2x sill, and only the RJ prints a clear "
                          f"span ({esr.RJ_CLEAR_SPAN_MAX_IN:g} in)")
    if strap.jog_in > _TOL_IN:
        unread.append(f"offset {strap.jog_in:.2f} in over the pour top to its leaf: "
                      f"{esr.JOG_RULE}")
    location, end_in = _location(site, le)
    if location != "midwall" and end_in < esr.MIN_END_DISTANCE_IN - _TOL_IN:
        problems.append(f"{end_in:.2f} in end distance, under Figure 1's 1/2 in")
    missing = _rebar(site, bars, le, location, max(sizes, key=lambda s: esr.TABLE_1[(6, s)].le_in))
    if missing:
        problems.append(missing)
    for other in sites:
        if other is site:
            continue
        o = other.strap
        parallel = abs(o.spoon_xy[0] * strap.spoon_xy[0] + o.spoon_xy[1] * strap.spoon_xy[1])
        gap = ((o.entry_xy[0] - strap.entry_xy[0]) ** 2
               + (o.entry_xy[1] - strap.entry_xy[1]) ** 2) ** 0.5 / M_PER_IN
        if parallel > 0.9 and gap < esr.SPACING_LE * le - _TOL_IN and \
                abs(other.top_z_m - site.top_z_m) < M_PER_IN:
            problems.append(f"{gap:.1f} in from {o.tag}, under 3 le = {esr.SPACING_LE * le:g} in")
    mix = concrete_spec_for(model.plan, model.plan.by_tag(strap.core_tag))
    if mix is not None and mix.fc_psi < esr.MIN_FC_PSI:
        problems.append(f"f'c {mix.fc_psi:,.0f} psi, under {esr.MIN_FC_PSI:,.0f}")
    span = f", {clear:.2f} in clear to the first stud" if clear is not None else ""
    behind = round(site.behind_in, 2) + 0.0  # no "-0.00"
    where = (f"{strap.tag} ({strap.part}) in {strap.core_tag}: {behind:.2f} in "
             f"behind / {site.ahead_in:.2f} in ahead, {provided:.2f} in embedded{span}, "
             f"{location} ({end_in:.1f} in to the end)")
    if problems:
        return failed(_ID, f"{where} — " + "; ".join(problems), tags, code=_CODE,
                      fix="cast the strap plumb under its framing in a stem Table 1 covers, "
                          "set its embedment line on the pour top, size the RJ across a band, "
                          "or lay the Figure 1 bar")
    cap = min(esr.allowable(s, stem, location, cracked=True) for s in sizes)
    load = (f"; {demand:,.0f} lb required (IRC Figure R602.10.7), ratio {demand / cap:.3f}"
            if demand is not None else "; this model states no demand on it")
    if mix is None:
        return unknown(_ID, f"{where}; its pour states no f'c (§3.2.5 needs 2,500 psi)", tags,
                       code=_CODE, fix="author a ConcreteSpec on the core's assembly")
    if clear is None:
        return unknown(_ID, f"{where}; no stud of {strap.framed_tag or 'a framed wall'} stands "
                            f"within 12 in of the leaf to read its clear span", tags,
                       code=_CODE, fix="name the framed wall in connects")
    if unread:
        return unknown(_ID, f"{where}; " + "; ".join(unread), tags, code=_CODE,
                       fix="frame so the leaf rises plumb from a Figure 1 entry, use the RJ, "
                           "or hold the manufacturer's written acceptance of this installation")
    if demand is not None and demand > cap:
        return failed(_ID, f"{where}: {cap:,.0f} lb allowable{load}", tags, code=_CODE,
                      fix="a larger STHD, or a second device")
    return passed(_ID, f"{where}: the {stem} in row, {cap:,.0f} lb allowable (cracked, wind/"
                       f"SDC A&B){load}", tags, code=_CODE)


@check(Tier.STRUCTURAL, _ID)
def strap_hold_down_embedment(ctx: CheckContext) -> list[Finding]:
    """Each cast-in STHD meets the ESR-2920 Table 1 installation it is rated at."""
    from typehaus.model.structure import Connector
    from typehaus.resolve.strap_holdowns import strap_sites

    model = ctx.model
    if getattr(model, "plan", None) is None:
        return []
    placed = {s.tag for s in getattr(model, "embedded_straps", ())}
    authored = [el for el in model.plan.all_elements()
                if isinstance(el, Connector) and esr.is_strap_holdown(el.size)]
    if not placed and not authored:
        return [not_applicable(_ID, "no cast-in strap hold-down (STHD/LSTHD) is placed or "
                                    "derived in this plan", code=_CODE)]
    sites = strap_sites(model)
    bars = [b for rs in model.rebar for b in rs.bars]
    demands = _demands(model)
    out = [_grade(model, site, bars, demands.get(site.strap.tag), sites) for site in sites]
    graded = {site.strap.tag for site in sites}
    for el in authored:
        if el.tag not in graded:
            out.append(unknown(_ID, f"{el.tag} ({el.size}) has no placed geometry in a "
                                    f"foundation core to read", (el.tag,), code=_CODE,
                               fix="connect it to the foundation wall it is cast in"))
    return out

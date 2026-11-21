"""Every bolted hold-down (an HTT) on its cast-in SSTB, against the two rows it is read at.

Two published rows, the lesser governing (``hardware/anchor_holdowns.py``):

* **hold-down** — C-C-2026 p. 63, the SPF/HF column of its nail row; it nails to the wide
  face of a vertical member at least 1 1/2 x 3 1/2, the rod CL off that face, the tie's
  width on the face and its height on the member.
* **anchor** — C-C-2026 p. 43, the SSTB's 6" stem-wall row: core at least the row's stem,
  1 3/4" from either face, middle at 1.5 l_e from the end (fn. 5) else corner or end at 5"
  or more, the embedment line on the pour top and the pour at least l_e deep, one #4 bar
  3-5" below the top 2 l_e each side (a 16" return at a corner), 3 l_e between bolts on one
  line, f'c 2,500 psi.

Demand where this model states one: a braced panel's ``hold_down_ref``, 800 lb (IRC Figure
R602.10.7). ICF is read as the stem, as the STHD check reads it.
"""

from __future__ import annotations

import math

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed, unknown
from typehaus.hardware import anchor_holdowns as hd
from typehaus.quantities import M_PER_IN

_ID = "structural.anchor_rod_hold_down"
_CODE = "Simpson C-C-2026 p. 63 (HTT) and p. 43 (SSTB at stem wall) (IRC R104.11)"
_TOL_IN = 1.0 / 16.0
_SAME_ROD_M = 0.25 * M_PER_IN
_VERTICALS = frozenset({"stud", "king", "corner", "jack"})


def _member(model, framed_tag, rod, seat_z, row) -> tuple[object | None, str | None]:
    """The vertical the tie nails to: its face CL off the rod, the tie on it."""
    from typehaus.resolve.framing.profiles import cross_section

    wall = model.wall(framed_tag) if framed_tag else None
    if wall is None:
        return None, f"names no framed wall to nail to ({framed_tag or 'none'})"
    for m in wall.members:
        if m.category not in _VERTICALS or m.orient is None or math.dist(m.p0, rod) > 0.3:
            continue
        cs = cross_section(m.profile)
        ol = math.hypot(*m.orient)
        u = (m.orient[0] / ol, m.orient[1] / ol)
        p = (-u[1], u[0])
        rel = (rod[0] - m.p0[0], rod[1] - m.p0[1])
        along, across = rel[0] * u[0] + rel[1] * u[1], rel[0] * p[0] + rel[1] * p[1]
        gap_in = (abs(along) - cs.width_m / 2.0) / M_PER_IN
        if abs(gap_in - row.cl_in) > 0.125:
            continue
        if (abs(across) / M_PER_IN + row.width_in / 2.0
                > cs.depth_m / 2.0 / M_PER_IN + _TOL_IN):
            return m, "the tie overhangs the member face"
        if cs.width_m / M_PER_IN < row.member_in[0] - _TOL_IN or \
                cs.depth_m / M_PER_IN < row.member_in[1] - _TOL_IN:
            return m, f"a {m.profile} is under the {row.member_in[0]:g} x " \
                      f"{row.member_in[1]:g} in minimum member"
        if m.z0_m > seat_z + 0.5 * M_PER_IN or m.z1_m < seat_z + row.height_in * M_PER_IN:
            return m, "the member does not span the tie's height"
        return m, None
    return None, f"no stud of {framed_tag} has a face {row.cl_in:g} in off the rod"


def _rebar(site, bars, le_in: float, location: str, turning) -> str | None:
    from typehaus.checks.structural.strap_holdown_embedment import _intervals, _reach, _turn

    s, d, c = site.strap.spoon_xy, site.strap.along_xy, site.centre_xy
    half = (site.behind_in + site.ahead_in) / 2.0 * M_PER_IN
    span = _reach(_intervals(bars, c, d, s, half, site.top_z_m), 0.0, 0.0)
    if span is None:
        return f"no #4 bar {hd.BAR_BAND_IN[0]:g}-{hd.BAR_BAND_IN[1]:g} in below the top passes it"
    want = hd.BAR_LE * le_in
    got = {-1.0: -span[0] / M_PER_IN, 1.0: span[1] / M_PER_IN}
    if location == "middle":
        short = [f"{got[k]:.1f}" for k in (-1.0, 1.0) if got[k] < want - 0.5]
        return f"its bar runs {', '.join(short)} in past it, under 2 le = {want:.2f} in" \
            if short else None
    far = -turning.sign
    if got[far] < want - 0.5:
        return f"its bar runs {got[far]:.1f} in inboard, under 2 le = {want:.2f} in"
    if location == "corner":
        _, leg = _turn(site, turning, bars)
        if leg < hd.CORNER_RETURN_IN - 0.5:
            return f"its corner return is {leg:.1f} in, under {hd.CORNER_RETURN_IN:g} in"
    return None


def _grade(model, element, anchor, sites, bars, demand) -> Finding:
    from typehaus.hardware.catalog import allowable_for_model
    from typehaus.resolve.concrete import concrete_spec_for

    row = hd.HOLDOWNS[element.size]
    tags = (element.tag, anchor.strap.tag, anchor.strap.core_tag)
    hold = allowable_for_model(element.size)
    if hold is None or hold.uplift_lb is None:
        return unknown(_ID, f"{element.tag}: {element.size} carries no published row", tags,
                       code=_CODE)
    problems: list[str] = []
    seat_z = element.elevation.meters if element.elevation is not None else anchor.top_z_m
    _, member_problem = _member(model, anchor.strap.framed_tag, anchor.strap.point_xy,
                                seat_z, row)
    if member_problem:
        problems.append(member_problem)
    srow = hd.SSTB_STEM[anchor.strap.part]
    thick = anchor.behind_in + anchor.ahead_in
    if thick < srow.stem_in - _TOL_IN:
        problems.append(f"a {thick:.2f} in core, under the {srow.stem_in:g} in stem row")
    edge = min(anchor.behind_in, anchor.ahead_in)
    if edge < hd.MIN_EDGE_IN - _TOL_IN:
        problems.append(f"{edge:.2f} in to the concrete face, under {hd.MIN_EDGE_IN:g} in")
    near = min(anchor.ends, key=lambda e: e.distance_in)
    location, column = hd.location(near.distance_in, near.turn_to is not None, srow.le_in)
    if location != "middle" and near.distance_in < hd.MIN_END_IN - _TOL_IN:
        problems.append(f"{near.distance_in:.2f} in to the end, under {hd.MIN_END_IN:g} in")
    if abs(anchor.strap.line_z_m - anchor.top_z_m) > _TOL_IN * M_PER_IN:
        problems.append("its embedment line is not on the pour top")
    pour = (anchor.top_z_m - anchor.pour_bottom_z_m) / M_PER_IN
    if pour < srow.le_in - _TOL_IN:
        problems.append(f"the pour is {pour:.2f} in deep, under le {srow.le_in:g} in")
    missing = _rebar(anchor, bars, srow.le_in, location, near)
    if missing:
        problems.append(missing)
    for other in sites:
        if other is anchor:
            continue
        parallel = abs(other.strap.along_xy[0] * anchor.strap.along_xy[0]
                       + other.strap.along_xy[1] * anchor.strap.along_xy[1]) > 0.9
        gap = math.dist(other.strap.point_xy, anchor.strap.point_xy) / M_PER_IN
        if parallel and gap < hd.SPACING_LE * srow.le_in - _TOL_IN:
            problems.append(f"{gap:.1f} in from {other.strap.tag}, under 3 le")
    mix = concrete_spec_for(model.plan, model.plan.by_tag(anchor.strap.core_tag))
    if mix is not None and mix.fc_psi < hd.MIN_FC_PSI:
        problems.append(f"f'c {mix.fc_psi:,.0f} psi, under {hd.MIN_FC_PSI:,.0f}")
    where = (f"{element.tag} ({element.size}) on {anchor.strap.tag} ({anchor.strap.part}) in "
             f"{anchor.strap.core_tag}: {anchor.behind_in:.2f} / {anchor.ahead_in:.2f} in to "
             f"the faces, {location} ({near.distance_in:.1f} in to the end), {pour:.1f} in "
             f"of pour")
    if problems:
        return failed(_ID, f"{where} — " + "; ".join(problems), tags, code=_CODE,
                      fix="set the rod 1-3/4 in or more off both faces on a stud face, "
                          "5 in from an end, and lay the p. 43 bar")
    if mix is None:
        return unknown(_ID, f"{where}; its pour states no f'c (2,500 psi needed)", tags,
                       code=_CODE)
    cap = min(hold.uplift_lb, srow.wind[column])
    load = (f"; {demand:,.0f} lb required (IRC Figure R602.10.7), ratio {demand / cap:.3f}"
            if demand is not None else "; this model states no demand on it")
    reading = (f"{element.size} {hold.uplift_lb:,.0f} lb (SPF/HF), {anchor.strap.part} "
               f"{srow.wind[column]:,.0f} lb ({location}): {cap:,.0f} lb governs")
    if demand is not None and demand > cap:
        return failed(_ID, f"{where}: {reading}{load}", tags, code=_CODE,
                      fix="a larger hold-down or anchor row")
    return passed(_ID, f"{where}: {reading}{load}", tags, code=_CODE)


@check(Tier.STRUCTURAL, _ID)
def anchor_rod_hold_down(ctx: CheckContext) -> list[Finding]:
    """Each bolted hold-down meets its own row and its anchor's stem-wall row."""
    from typehaus.checks.structural.strap_holdown_embedment import _demands
    from typehaus.model.enums import ConnectorKind
    from typehaus.resolve.anchor_holdowns import anchor_sites

    model = ctx.model
    if getattr(model, "plan", None) is None:
        return []
    holdowns = [el for el in model.plan.all_elements()
                if getattr(el, "kind", None) is ConnectorKind.HOLD_DOWN
                and (el.size or "") in hd.HOLDOWNS and el.position is not None]
    if not holdowns:
        return [not_applicable(_ID, "no bolted hold-down (HTT) is authored in this plan",
                               code=_CODE)]
    sites = anchor_sites(model)
    bars = [b for rs in model.rebar for b in rs.bars]
    demands = _demands(model)
    out = []
    for el in holdowns:
        anchor = next((s for s in sites
                       if math.dist(s.strap.point_xy, el.position.xy_m) <= _SAME_ROD_M), None)
        if anchor is None:
            out.append(unknown(_ID, f"{el.tag} ({el.size}): no cast-in anchor with a "
                                    f"published stem-wall row stands under its seat",
                               (el.tag,), code=_CODE,
                               fix="author the SSTB at the hold-down's rod centre"))
            continue
        out.append(_grade(model, el, anchor, sites, bars, demands.get(el.tag)))
    return out

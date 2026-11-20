"""The No. 4 bar an STHD's Table 1 load is tested with (ESR-2920 §3.2.6, §4.2, Figure 1).

One bar 3-5" below the top of the foundation, 2 x le each side of the strap; near an end
that turns a corner, an L round it with the Figure 1 return leg. Laid only where the host's
own bars put none in that band past the strap, at the band's middle (4"), on the core's
mid-thickness, with the pour's cover at its ends.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.model.rebar import BARS
from typehaus.quantities import M_PER_IN
from typehaus.resolve.concrete import concrete_spec_for
from typehaus.resolve.rebar.records import ResolvedBar, ResolvedRebarSet
from typehaus.resolve.strap_holdowns import (
    BAR_BAND_IN,
    EMBEDDED_WIDTH_IN,
    MIN_BAR,
    REBAR_LE,
    StrapSite,
    strap_sites,
)


def in_band(bar: ResolvedBar, top_z_m: float) -> bool:
    lo, hi = BAR_BAND_IN
    return bar.bar >= MIN_BAR and not bar.closed and all(
        lo - 1e-6 <= (top_z_m - p[2]) / M_PER_IN <= hi + 1e-6 for p in bar.path)


def passes(bar: ResolvedBar, site: StrapSite) -> bool:
    """The bar crosses the strap's station inside its core's thickness."""
    s, d, c = site.strap.spoon_xy, site.strap.along_xy, site.centre_xy
    half = (site.behind_in + site.ahead_in) / 2.0 * M_PER_IN
    for a, b in zip(bar.path, bar.path[1:], strict=False):
        ua = (a[0] - c[0]) * d[0] + (a[1] - c[1]) * d[1]
        ub = (b[0] - c[0]) * d[0] + (b[1] - c[1]) * d[1]
        if min(ua, ub) <= 0.0 <= max(ua, ub) and ua != ub:
            t = -ua / (ub - ua)
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if abs((x - c[0]) * s[0] + (y - c[1]) * s[1]) <= half:
                return True
    return False


def _path(site: StrapSite, le_in: float, cover_m: float, z: float) -> list:
    c, d = site.centre_xy, site.strap.along_xy
    want = REBAR_LE * le_in * M_PER_IN
    reach = {}
    turn = None
    for end in site.ends:
        avail = (end.distance_in + EMBEDDED_WIDTH_IN / 2.0) * M_PER_IN - cover_m
        reach[end.sign] = max(min(want, avail), 0.0)
        if avail < want and end.turn_to is not None and turn is None:
            turn = end
    pts = [(c[0] + d[0] * u, c[1] + d[1] * u) for u in (-reach[-1.0], reach[1.0])]
    if turn is not None:
        leg_in = site.corner_leg_in or REBAR_LE * le_in
        t = turn.turn_to
        offs = [((p[0] - c[0]) * d[0] + (p[1] - c[1]) * d[1]) for p in turn.turn_core]
        u_turn = (min(offs) + max(offs)) / 2.0
        corner = (c[0] + d[0] * u_turn, c[1] + d[1] * u_turn)
        span = max((p[0] - corner[0]) * t[0] + (p[1] - corner[1]) * t[1]
                   for p in turn.turn_core) - cover_m
        leg = (corner[0] + t[0] * min(leg_in * M_PER_IN, span),
               corner[1] + t[1] * min(leg_in * M_PER_IN, span))
        pts = [pts[1], corner, leg] if turn.sign < 0 else [pts[0], corner, leg]
    return [(x, y, z) for x, y in pts]


def strap_bars(model, sets: list[ResolvedRebarSet]) -> list[ResolvedRebarSet]:
    """``sets`` with a derived STHD bar added to each strap's core that lacks one."""
    from typehaus.resolve.rebar.build import cover_m

    plan = model.plan
    added: dict[str, list[ResolvedBar]] = {}
    for site in strap_sites(model):
        le_in = site.le_in
        host = site.strap.core_tag
        if le_in is None:
            continue
        pool = [b for rs in sets for b in rs.bars] + added.get(host, [])
        if any(in_band(b, site.top_z_m) and passes(b, site) for b in pool):
            continue
        element = plan.by_tag(host)
        mix = concrete_spec_for(plan, element)
        z = site.top_z_m - sum(BAR_BAND_IN) / 2.0 * M_PER_IN
        path = _path(site, le_in, cover_m(plan, element), z)
        length = sum(math.dist(a, b) for a, b in zip(path, path[1:], strict=False))
        if length <= 0.0:
            continue
        mine = added.setdefault(host, [])
        mine.append(ResolvedBar(
            key=f"{host}/sthd/{len(mine) + 1:03d}", role="horizontal", bar=MIN_BAR,
            coating=(mix.bar_coating if mix is not None else None) or "", spacing_in=None,
            path=tuple(path), closed=False, diameter_m=BARS[MIN_BAR].diameter_in * M_PER_IN,
            placed_length_m=length,
            note=f"ESR-2920 §4.2: the {site.strap.part} bar for {site.strap.tag}"))
    out = []
    for rs in sets:
        extra = added.pop(rs.host_tag, None)
        out.append(replace(rs, bars=rs.bars + tuple(extra)) if extra else rs)
    for host, bars in added.items():
        wall = model.wall(host)
        out.append(ResolvedRebarSet(wall.uid, host, plan.by_tag(host).element_kind,
                                    wall.storey, "foundation wall", tuple(bars)))
    return out

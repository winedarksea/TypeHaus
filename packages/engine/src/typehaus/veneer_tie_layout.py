"""Where an anchored wythe's ties land: on studs, never into a concrete stretch (F-02).

A leaf beside :mod:`typehaus.veneer_ties` (same measurement, same model). Table R703.8.4(1)
publishes WOOD-STUD backing only, so the ties stand on the studs of the framed backing and the
stretches of the wythe in front of concrete are tied from their neighbours, not into the pour
(decision 10: none into the 3.5" concrete ends).

**Stations.** Every full-height stud, king or jack of a framed backing, projected on the
wythe's axis (a double king or jack is one station). **Tributary** of a station: half the
gap to its neighbour, or the whole strip to a wythe end or an opening's edge. A tie carries at
most ``area / row spacing`` of width (2.67 sf over 24" rows is 16.0"). **Openings** over 16" in
either dimension take ties within 12" of each jamb (R703.8.4.1.1, 2021 and 2024).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.veneer_ties import TIE_SPACING_V_IN, WytheReach

_IN = 0.0254
_STUD_KINDS = ("stud", "king", "jack")
_MERGE_IN = 2.0
#: R703.8.4.1.1: an opening over this in either dimension takes perimeter ties, within 12".
OPENING_TIE_MIN_IN = 16.0
OPENING_TIE_REACH_IN = 12.0


@dataclass(frozen=True)
class ConcreteStrip:
    wall: str
    length_in: float
    #: wythe end it stands at ("start"/"end" of the wythe's axis) and the first stud tie's reach
    end: str
    to_first_tie_in: float


@dataclass(frozen=True)
class OpeningTies:
    tag: str
    width_in: float
    height_in: float
    #: nearest station outboard of each jamb: gap from the jamb edge (in), None if none
    near_in: tuple[float | None, float | None]

    @property
    def applies(self) -> bool:
        return max(self.width_in, self.height_in) > OPENING_TIE_MIN_IN + 1e-6

    @property
    def met(self) -> bool:
        return all(g is not None and g <= OPENING_TIE_REACH_IN + 1e-6 for g in self.near_in)


@dataclass(frozen=True)
class TieLayout:
    wythe: str
    length_in: float
    stations_in: tuple[float, ...]
    backing_walls: tuple[str, ...]
    #: widest tributary of any station (in), and the station it is at
    widest_in: float
    widest_at_in: float
    allowed_in: float
    strips: tuple[ConcreteStrip, ...]
    openings: tuple[OpeningTies, ...]

    @property
    def met(self) -> bool:
        return (self.widest_in <= self.allowed_in + 1e-6
                and all(o.met for o in self.openings if o.applies))


def _is_framed(wall: Any) -> bool:
    return any(m.category in _STUD_KINDS for m in wall.members)


def layout(model: Any, wythe: Any, reach: WytheReach, area_sf: float) -> TieLayout | None:
    (ax, ay), (bx, by) = wythe.axis
    length = math.hypot(bx - ax, by - ay)
    u = ((bx - ax) / length, (by - ay) / length)

    def along(p) -> float:
        return ((p[0] - ax) * u[0] + (p[1] - ay) * u[1]) / _IN

    brick = next(ly for ly in wythe.layers if ly.function == "structure" and ly.polygon)
    us = [along(p) for p in brick.polygon]
    u0, u1 = max(0.0, min(us)), min(length / _IN, max(us))
    height = wythe.z1_m - wythe.z0_m

    stations: list[float] = []
    strips: list[tuple[str, float, float]] = []
    for tag in reach.backings:
        wall = model.wall(tag)
        if _is_framed(wall):
            for m in wall.members:
                if (m.category in _STUD_KINDS and m.z0_m <= wythe.z0_m + 0.15
                        and m.z1_m >= wythe.z1_m - 0.5 * height):
                    s = along(m.p0)
                    if u0 - 1e-6 <= s <= u1 + 1e-6:
                        stations.append(s)
        else:
            pts = [along(p) for ly in wall.layers if ly.polygon for p in ly.polygon]
            lo, hi = max(u0, min(pts)), min(u1, max(pts))
            if hi - lo > 1e-6:
                strips.append((wall.tag, lo, hi))
    if not stations:
        return None
    merged: list[float] = []
    for s in sorted(stations):
        if not merged or s - merged[-1] > _MERGE_IN:
            merged.append(s)
    openings = []
    for op in model.openings:
        if op.host_wall != wythe.tag:
            continue
        mid, half = op.center_along_m / _IN, op.width_m / _IN / 2.0
        openings.append((op.tag, mid - half, mid + half, op.width_m / _IN, op.height_m / _IN))

    widest, widest_at = 0.0, 0.0
    for i, s in enumerate(merged):
        extent = []
        for side, nxt in ((-1, merged[i - 1] if i else None),
                          (1, merged[i + 1] if i + 1 < len(merged) else None)):
            if nxt is None:
                extent.append(abs(s - (u0 if side < 0 else u1)))
                continue
            a, b = sorted((s, nxt))
            span = b - a
            hit = [(lo, hi) for _t, lo, hi, _w, _h in openings if a < lo and hi < b]
            if hit:
                lo, hi = hit[0]
                extent.append((s - hi) if side < 0 else (lo - s))
            else:
                extent.append(span / 2.0)
        width = sum(extent)
        if width > widest:
            widest, widest_at = width, s
    allowed = area_sf * 144.0 / TIE_SPACING_V_IN
    rows = []
    for tag, lo, hi, w, h in openings:
        west = min((lo - s for s in merged if s <= lo + 1e-6), default=None)
        east = min((s - hi for s in merged if s >= hi - 1e-6), default=None)
        west = None if west is None else max(west, 0.0)
        east = None if east is None else max(east, 0.0)
        rows.append(OpeningTies(tag, w, h, (west, east)))
    out = []
    for tag, lo, hi in strips:
        at_start = lo <= u0 + 1e-6
        first = (min(merged) - u0) if at_start else (u1 - max(merged))
        out.append(ConcreteStrip(tag, hi - lo, "start" if at_start else "end", first))
    return TieLayout(wythe.tag, (u1 - u0), tuple(round(s - u0, 3) for s in merged),
                     tuple(reach.backings), widest, widest_at - u0, allowed, tuple(out),
                     tuple(rows))

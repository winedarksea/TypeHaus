"""Where an anchored wythe's ties land: on studs, never into a concrete stretch (F-02).

A leaf beside :mod:`typehaus.veneer_ties` (same measurement, same model). Table R703.8.4(1)
publishes WOOD-STUD backing only, so the ties stand on the studs of the framed backing and the
stretches of the wythe in front of concrete are tied from their neighbours, not into the pour
(decision 10: none into the 3.5" concrete ends).

**Stations.** Every full-height stud, king or jack of a framed backing, projected on the
wythe's axis (a double king or jack is one station). **Tributary** of a station: half the
gap to its neighbour, or the whole strip to a wythe end or an opening's edge. A tie carries at
most ``area / row spacing`` of width (2.67 sf over 24" rows is 16.0").

**Openings** over 16" in either dimension take ties around the WHOLE perimeter, within 12" of
the opening and at most 3 ft o.c. (R703.8.4.1.1, 2021 and 2024): each jamb, and the head and
sill bands. A head or sill tie lands on a stud, jack, king or CRIPPLE standing in that band (a
door's head cripples are the head ties' backing); the band over a lintel starts at the angle's
top. **Rows** are bed joints (a 2 2/3" course module off the base), at most 24" apart and
within 24" of the base and top, each opening's head and sill band holding one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.veneer_ties import TIE_SPACING_V_IN, WytheReach

_IN = 0.0254
_STUD_KINDS = ("stud", "king", "jack")
_BAND_KINDS = (*_STUD_KINDS, "cripple")
_MERGE_IN = 2.0
#: R703.8.4.1.1: an opening over this in either dimension takes perimeter ties, within 12".
OPENING_TIE_MIN_IN = 16.0
OPENING_TIE_REACH_IN = 12.0
OPENING_TIE_SPACING_IN = 36.0
#: A brick course with its bed joint (modular brick: 3 courses to 8").
COURSE_IN = 8.0 / 3.0
#: The lintel angle's height: the head band starts at its top. Authored as L3x3x1/4.
LINTEL_LEG_IN = 3.0
#: A member must stand this far into a band to take a tie in it.
_MIN_OVERLAP_IN = 0.5


@dataclass(frozen=True)
class ConcreteStrip:
    wall: str
    length_in: float
    #: wythe end it stands at ("start"/"end" of the wythe's axis) and the first stud tie's reach
    end: str
    to_first_tie_in: float


@dataclass(frozen=True)
class BandTies:
    """The ties over an opening's head (or under its sill): stations standing in the band."""

    stations: int
    #: widest spacing between consecutive stations across the band (in), and the distance of
    #: the nearest station to each opening edge (in)
    max_gap_in: float
    near_in: tuple[float | None, float | None]
    #: the elevation band (in above the wythe's base) every one of those stations stands in
    z_in: tuple[float, float] | None
    #: the row chosen in it (in above the base), or None where no bed joint fits
    row_in: float | None

    @property
    def met(self) -> bool:
        return (self.stations > 0 and self.row_in is not None
                and self.max_gap_in <= OPENING_TIE_SPACING_IN + 1e-6
                and all(g is not None and g <= OPENING_TIE_REACH_IN + 1e-6
                        for g in self.near_in))


@dataclass(frozen=True)
class OpeningTies:
    tag: str
    width_in: float
    height_in: float
    #: nearest station outboard of each jamb: gap from the jamb edge (in), None if none
    near_in: tuple[float | None, float | None]
    head: BandTies | None = None
    sill: BandTies | None = None

    @property
    def applies(self) -> bool:
        return max(self.width_in, self.height_in) > OPENING_TIE_MIN_IN + 1e-6

    @property
    def met(self) -> bool:
        return (all(g is not None and g <= OPENING_TIE_REACH_IN + 1e-6 for g in self.near_in)
                and all(b.met for b in (self.head, self.sill) if b is not None))


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
    #: the bed joints the ties stand on (in above the base), lowest first
    rows_in: tuple[float, ...]
    height_in: float

    @property
    def rows_met(self) -> bool:
        marks = [0.0, *self.rows_in, self.height_in]
        return (bool(self.rows_in)
                and all(b - a <= TIE_SPACING_V_IN + 1e-6 for a, b in zip(marks, marks[1:],
                                                                         strict=False)))

    @property
    def met(self) -> bool:
        return (self.widest_in <= self.allowed_in + 1e-6 and self.rows_met
                and all(o.met for o in self.openings if o.applies))


def _is_framed(wall: Any) -> bool:
    return any(m.category in _STUD_KINDS for m in wall.members)


def _joint_in(z_in: float, up: bool) -> float:
    """The bed joint at or above (``up``) / at or below ``z_in`` above the base."""
    k = math.ceil(z_in / COURSE_IN - 1e-9) if up else math.floor(z_in / COURSE_IN + 1e-9)
    return round(k * COURSE_IN, 4)


def _band(members, lo_u, hi_u, band_lo, band_hi):
    """Stations (in from the wythe's start) standing in the band within 12" of the span, the
    elevation range every one stands in, the widest gap and the nearest edge distances."""
    picked = []
    for u, z0, z1 in members:
        if (lo_u - OPENING_TIE_REACH_IN <= u <= hi_u + OPENING_TIE_REACH_IN
                and min(z1, band_hi) - max(z0, band_lo) > _MIN_OVERLAP_IN):
            picked.append((u, max(z0, band_lo), min(z1, band_hi)))
    merged: list[float] = []
    for u in sorted(p[0] for p in picked):
        if not merged or u - merged[-1] > _MERGE_IN:
            merged.append(u)
    zr = None
    if picked:
        lo, hi = max(p[1] for p in picked), min(p[2] for p in picked)
        zr = (lo, hi) if hi - lo > 1e-6 else None
    near_w = min((lo_u - u for u in merged if u <= lo_u + 1e-6), default=None)
    near_e = min((u - hi_u for u in merged if u >= hi_u - 1e-6), default=None)
    gap = max((b - a for a, b in zip(merged, merged[1:], strict=False)), default=math.inf)
    return len(merged), zr, gap, (near_w, near_e)


def _fill_rows(mandatory: set[float], height_in: float) -> tuple[float, ...]:
    """Bed-joint rows: the mandatory ones, plus enough that none is over 24" from the next,
    the base or the top."""
    marks = [0.0, *sorted(mandatory), height_in]
    out: list[float] = []
    for a, b in zip(marks, marks[1:], strict=False):
        extra = math.ceil((b - a) / TIE_SPACING_V_IN - 1e-9) - 1
        for i in range(1, extra + 1):
            out.append(_joint_in(a + (b - a) * i / (extra + 1), up=False))
        if b < height_in:
            out.append(b)
    return tuple(round(r, 3) for r in out)


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
    banded: list[tuple[float, float, float]] = []
    strips: list[tuple[str, float, float]] = []
    for tag in reach.backings:
        wall = model.wall(tag)
        if _is_framed(wall):
            for m in wall.members:
                if m.category not in _BAND_KINDS:
                    continue
                s = along(m.p0)
                if not u0 - 1e-6 <= s <= u1 + 1e-6:
                    continue
                banded.append((s - u0, (m.z0_m - wythe.z0_m) / _IN,
                               (m.z1_m - wythe.z0_m) / _IN))
                if (m.category in _STUD_KINDS and m.z0_m <= wythe.z0_m + 0.15
                        and m.z1_m >= wythe.z1_m - 0.5 * height):
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
        openings.append((op.tag, mid - half, mid + half, op.width_m / _IN, op.height_m / _IN,
                         op.sill_m / _IN))

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
            hit = [(lo, hi) for _t, lo, hi, _w, _h, _s in openings if a < lo and hi < b]
            if hit:
                lo, hi = hit[0]
                extent.append((s - hi) if side < 0 else (lo - s))
            else:
                extent.append(span / 2.0)
        width = sum(extent)
        if width > widest:
            widest, widest_at = width, s
    allowed = area_sf * 144.0 / TIE_SPACING_V_IN
    height_in = height / _IN
    rows: set[float] = set()
    perimeter = []
    for tag, lo, hi, w, h, sill in openings:
        west = min((lo - s for s in merged if s <= lo + 1e-6), default=None)
        east = min((s - hi for s in merged if s >= hi - 1e-6), default=None)
        west = None if west is None else max(west, 0.0)
        east = None if east is None else max(east, 0.0)
        head = sill_band = None
        if max(w, h) > OPENING_TIE_MIN_IN:
            lo_u, hi_u, top = lo - u0, hi - u0, sill + h
            n, zr, gap, near = _band(banded, lo_u, hi_u, top + LINTEL_LEG_IN,
                                     min(top + OPENING_TIE_REACH_IN, height_in))
            row = None
            if zr:
                j = _joint_in(zr[0], up=True)
                row = j if j <= zr[1] + 1e-6 else None
            head = BandTies(n, gap, near, zr, row)
            rows.update([row] if row is not None else [])
            if sill > 1e-6:
                n, zr, gap, near = _band(banded, lo_u, hi_u,
                                         max(0.0, sill - OPENING_TIE_REACH_IN), sill)
                row = None
                if zr:
                    j = _joint_in(zr[1], up=False)
                    row = j if j >= zr[0] - 1e-6 else None
                sill_band = BandTies(n, gap, near, zr, row)
                rows.update([row] if row is not None else [])
        perimeter.append(OpeningTies(tag, w, h, (west, east), head, sill_band))
    strip_out = []
    for tag, lo, hi in strips:
        at_start = lo <= u0 + 1e-6
        first = (min(merged) - u0) if at_start else (u1 - max(merged))
        strip_out.append(ConcreteStrip(tag, hi - lo, "start" if at_start else "end", first))
    return TieLayout(wythe.tag, (u1 - u0), tuple(round(s - u0, 3) for s in merged),
                     tuple(reach.backings), widest, widest_at - u0, allowed, tuple(strip_out),
                     tuple(perimeter), _fill_rows(rows, height_in), height_in)

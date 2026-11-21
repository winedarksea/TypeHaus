"""What stands behind a sheathing layer, as rectangles on its face (decision #146).

Every framing member whose face touches the sheathing's back — studs, kings, jacks,
cripples, plates, headers, sills, blocking, and a floor's rim and deck edge where the band
laps them — becomes a rectangle in the face's (station, z) plane, read off ``wall.members``
rather than stud-grid arithmetic, so staggered walls, doubled studs and corner backing
come free. A joint is backed where these rectangles cover ``min_edge_bearing`` on both
sides of it along its whole length.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon

from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section, plan_cross_section_m
from typehaus.resolve.geometry_walls import cuts_layer

_TOUCH_TOL_M = 0.125 * M_PER_IN  # a member this close to the sheathing's back bears it
_PARALLEL = 0.99
_RAKE_STEP_M = 6.0 * M_PER_IN  # a raked member is stepped into rectangles this long
_EPS = 1e-6
# A joint's end may run this far past the last member: at a through corner the panel laps
# the other wall's sheathing edge, and the end nail sits 3/8" in, on the member.
_END_ALLOWANCE_M = 0.75 * M_PER_IN


@dataclass(frozen=True)
class Rect:
    s0: float
    s1: float
    z0: float
    z1: float
    key: str


@dataclass(frozen=True)
class Frame:
    """The wall's face frame: origin, unit axis ``d``, left normal ``n``, the sheathing's
    back offset ``inner`` and which way the framing lies from it (``side``)."""

    origin: tuple[float, float]
    d: tuple[float, float]
    n: tuple[float, float]
    inner: float
    side: float

    def station(self, p) -> float:
        return (p[0] - self.origin[0]) * self.d[0] + (p[1] - self.origin[1]) * self.d[1]

    def offset(self, p) -> float:
        return (p[0] - self.origin[0]) * self.n[0] + (p[1] - self.origin[1]) * self.n[1]

    def touches(self, centre: float, across: float) -> bool:
        near = centre - self.side * across / 2.0
        return abs(near - self.inner) <= _TOUCH_TOL_M


def face_frame(layer, structure, origin, d) -> Frame | None:
    """The run frame at ``origin`` along ``d``, its back face read off ``layer``."""
    if len(layer.polygon) < 3 or len(structure.polygon) < 3:
        return None
    frame = Frame(origin, d, (-d[1], d[0]), 0.0, 1.0)
    offsets = [frame.offset(p) for p in layer.polygon]
    mid = sum(offsets) / len(offsets)
    framing = sum(frame.offset(p) for p in structure.polygon) / len(structure.polygon)
    side = 1.0 if framing > mid else -1.0
    inner = max(offsets) if side > 0 else min(offsets)
    return Frame(origin, d, frame.n, inner, side)


def _member_rects(frame: Frame, member, key: str) -> list[Rect]:
    section = cross_section(member.profile)
    dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
    run = math.hypot(dx, dy)
    if run < _EPS:  # vertical: its face along the wall is the narrow side unless turned
        o = member.orient or frame.d
        along_wall = abs(o[0] * frame.d[0] + o[1] * frame.d[1]) > 0.7
        along, across = ((section.width_m, section.depth_m) if along_wall
                         else (section.depth_m, section.width_m))
        if not frame.touches(frame.offset(member.p0), across):
            return []
        s = frame.station(member.p0)
        return [Rect(s - along / 2.0, s + along / 2.0, member.z0_m, member.z1_m, key)]
    if abs(dx / run * frame.d[0] + dy / run * frame.d[1]) < _PARALLEL:
        return _end_rect(frame, member, section, key, (dx / run, dy / run))
    across = member.plan_width_m or plan_cross_section_m(section, member.z1_m - member.z0_m)
    centre = (frame.offset(member.p0) + frame.offset(member.p1)) / 2.0
    if not frame.touches(centre, across):
        return []
    s_a, s_b = frame.station(member.p0), frame.station(member.p1)
    if member.z0_end_m is None or abs(member.z0_end_m - member.z0_m) < _EPS:
        return [Rect(min(s_a, s_b), max(s_a, s_b), member.z0_m, member.z1_m, key)]
    z1_end = member.z1_end_m if member.z1_end_m is not None else member.z0_end_m + (
        member.z1_m - member.z0_m)
    steps = max(1, math.ceil(abs(s_b - s_a) / _RAKE_STEP_M))
    rects = []
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps
        lo = min(member.z0_m + (member.z0_end_m - member.z0_m) * t for t in (t0, t1))
        hi = max(member.z1_m + (z1_end - member.z1_m) * t for t in (t0, t1))
        a, b = s_a + (s_b - s_a) * t0, s_a + (s_b - s_a) * t1
        rects.append(Rect(min(a, b), max(a, b), lo, hi, key))
    return rects


def _end_rect(frame: Frame, member, section, key: str, u) -> list[Rect]:
    """A member square to the face whose END bears on the sheathing (a corner wall's plate
    under a butting panel's last inches): its plan width, centred on its end."""
    if abs(u[0] * frame.d[0] + u[1] * frame.d[1]) > 1.0 - _PARALLEL:
        return []
    across = member.plan_width_m or plan_cross_section_m(section, member.z1_m - member.z0_m)
    for end in (member.p0, member.p1):
        if abs(frame.offset(end) - frame.inner) <= _TOUCH_TOL_M:
            s = frame.station(end)
            return [Rect(s - across / 2.0, s + across / 2.0, member.z0_m, member.z1_m, key)]
    return []


def neighbours(model, wall) -> list:
    """The walls meeting ``wall`` at a junction: a corner's framing backs a butting panel."""
    tags = {inc.wall_tag for j in model.junctions
            if any(inc.wall_tag == wall.tag for inc in j.incidents) for inc in j.incidents}
    tags.discard(wall.tag)
    return [w for w in model.walls if w.tag in tags]


def backing_rects(model, wall, frame: Frame, z0: float, z1: float, lo: float,
                  hi: float) -> list[Rect]:
    """Every member rectangle on ``wall``'s sheathing face: its own, its corner neighbours'
    and its floors'."""
    rects = [r for w in (wall, *neighbours(model, wall)) for m in w.members
             for r in _member_rects(frame, m, m.child_key if w is wall
                                    else f"{w.tag}:{m.child_key}")]
    for floor in model.floors:
        for member in floor.members:
            if member.z1_m < z0 - _EPS or member.z0_m > z1 + _EPS:
                continue
            rects.extend(_member_rects(frame, member, f"{floor.tag}:{member.child_key}"))
        rects.extend(_deck_rects(frame, floor, z0, z1, lo, hi))
    for solid in model.solids:  # a sill plate on the foundation is a solid, not a member
        if solid.category != "sill_plate" or solid.z1_m < z0 or solid.z0_m > z1:
            continue
        offsets = [frame.offset(p) for p in solid.outline]
        near = min(offsets) if frame.side > 0 else max(offsets)
        if abs(near - frame.inner) <= _TOUCH_TOL_M:
            stations = [frame.station(p) for p in solid.outline]
            rects.append(Rect(min(stations), max(stations), solid.z0_m, solid.z1_m, solid.tag))
    return rects


def _deck_rects(frame: Frame, floor, z0: float, z1: float, lo: float, hi: float) -> list[Rect]:
    """The subfloor's edge where the deck (less its voids) reaches the sheathing's back."""
    if len(floor.deck_outline) < 3 or floor.deck_z1_m < z0 or floor.deck_z0_m > z1:
        return []
    probe = frame.inner + frame.side * _TOUCH_TOL_M

    def at(s: float) -> tuple[float, float]:
        return (frame.origin[0] + frame.d[0] * s + frame.n[0] * probe,
                frame.origin[1] + frame.d[1] * s + frame.n[1] * probe)

    deck = Polygon(floor.deck_outline, floor.deck_voids).buffer(0)
    hit = deck.intersection(LineString([at(lo - 1.0), at(hi + 1.0)]))
    lines = getattr(hit, "geoms", [hit])
    rects = []
    for line in lines:
        if line.is_empty or line.length < _EPS or line.geom_type != "LineString":
            continue
        stations = [frame.station(p) for p in line.coords]
        rects.append(Rect(min(stations), max(stations), floor.deck_z0_m, floor.deck_z1_m,
                          f"{floor.tag}:deck"))
    return rects


def opening_rects(model, face) -> list[tuple[str, float, float, float, float]]:
    """``(tag, s0, s1, z0, z1)`` in run stations of every opening cutting ``face``'s layer."""
    wall, out = face.wall, []
    for opening in model.openings:
        if opening.host_wall != wall.tag or not cuts_layer(wall, face.layer.name, opening):
            continue
        z0 = wall.base_ref_z_m + opening.sill_m
        mid, half = face.run_station(opening.center_along_m), opening.width_m / 2.0
        out.append((opening.tag, mid - half, mid + half, z0, z0 + opening.height_m))
    return out


def _merged_cover(intervals, lo: float, hi: float) -> bool:
    reach = lo
    for a, b in sorted(intervals):
        if a > reach + _EPS:
            return False
        reach = max(reach, b)
        if reach >= hi - _EPS:
            return True
    return reach >= hi - _EPS


def unbacked_length(rects, vertical: bool, at: float, lo: float, hi: float, bearing: float,
                    holes=()) -> float:
    return sum(b - a for a, b in unbacked_spans(rects, vertical, at, lo, hi, bearing, holes))


def unbacked_spans(rects, vertical: bool, at: float, lo: float, hi: float, bearing: float,
                   holes=()) -> list[tuple[float, float]]:
    """Length of the joint at ``at`` (a station if ``vertical``, else a z) from ``lo`` to
    ``hi`` along which no framing covers ``bearing`` on both sides. ``holes`` are openings
    as ``(across_lo, across_hi, along_lo, along_hi)``: no panel, so no joint, inside one."""
    def span(r):  # (across the joint, along it)
        return ((r.s0, r.s1), (r.z0, r.z1)) if vertical else ((r.z0, r.z1), (r.s0, r.s1))

    near = [span(r) for r in rects]
    near = [(c, a) for c, a in near if c[0] < at + bearing and c[1] > at - bearing
            and a[1] > lo and a[0] < hi]
    cuts = sorted({lo, hi, *(v for _c, a in near for v in a if lo < v < hi),
                   *(v for h in holes for v in h[2:] if lo < v < hi)})
    missing: list[tuple[float, float]] = []
    for a, b in zip(cuts, cuts[1:], strict=False):
        mid = (a + b) / 2.0
        if any(h[0] < at < h[1] and h[2] < mid < h[3] for h in holes):
            continue
        cover = [c for c, al in near if al[0] <= mid <= al[1]]
        if _merged_cover(cover, at - bearing, at + bearing):
            continue
        if missing and abs(missing[-1][1] - a) < _EPS:
            missing[-1] = (missing[-1][0], b)
        else:
            missing.append((a, b))
    return [(a, b) for a, b in missing
            if b - a > _END_ALLOWANCE_M or lo + _EPS < a and b < hi - _EPS]


def nearest(rects, vertical: bool, at: float, lo: float, hi: float):
    """``(key, offset)`` of the member centre line nearest the joint, or ``(None, None)``."""
    best = None
    for r in rects:
        c0, c1, a0, a1 = (r.s0, r.s1, r.z0, r.z1) if vertical else (r.z0, r.z1, r.s0, r.s1)
        if a1 <= lo or a0 >= hi:
            continue
        offset = at - (c0 + c1) / 2.0
        if best is None or abs(offset) < abs(best[1]):
            best = (r.key, offset)
    return best or (None, None)

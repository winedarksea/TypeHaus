"""The boards of a stair's gypsum underside, in each flight's own (run, cross) frame.

A flight's board is a band one board deep (perpendicular) under the rake of its stringers'
cut ``elevation_profile``, swept outer face to outer face, or on to the wall face where a
wall backs that side; the horizontal foot is dropped, so the board dies at the floor.
A landing takes a flat board under its joists. Plumb returns close the steps: a flight end
at a landing, a flight head at the stairhead header, and the riser between two half
landings. An unwalled flight side takes a face board over its outer stringer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from shapely.geometry import LineString, MultiPolygon, Polygon, box

from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.overlay import difference, intersection, union_all

# A wall this far past a flight's outer stringer face backs that side.
WALL_REACH_M = 0.15
# A wall (or walls) must back this much of the run for the side to count as walled.
WALLED_FRACTION = 0.5
# A railing panel this close to the outer face covers it.
PANEL_ON_FACE_M = 0.06
# A landing within this of a flight end meets it.
LANDING_MEETS_M = 0.06
_EPS = 1e-6

Point3 = tuple[float, float, float]
Edge3 = tuple[Point3, Point3]


@dataclass(frozen=True)
class Frame:
    """A flight's plan frame: ``s`` along the run (from the stringers' ``p0``), ``c`` across."""

    origin: tuple[float, float]
    run: tuple[float, float]
    cross: tuple[float, float]

    def at(self, s: float, c: float) -> tuple[float, float]:
        return (self.origin[0] + self.run[0] * s + self.cross[0] * c,
                self.origin[1] + self.run[1] * s + self.cross[1] * c)

    def s_of(self, xy) -> float:
        return ((xy[0] - self.origin[0]) * self.run[0] + (xy[1] - self.origin[1]) * self.run[1])

    def c_of(self, xy) -> float:
        return ((xy[0] - self.origin[0]) * self.cross[0]
                + (xy[1] - self.origin[1]) * self.cross[1])

    def rect(self, s0: float, s1: float, c0: float, c1: float) -> Polygon:
        return Polygon([self.at(s0, c0), self.at(s1, c0), self.at(s1, c1), self.at(s0, c1)])


@dataclass
class Board:
    """One board before it becomes a member and a record (``stair_undersides.py``)."""

    key: str
    role: str
    p0: tuple[float, float]
    p1: tuple[float, float]
    ring: tuple[tuple[float, float], ...]  # (run from p0, z), swept across plan_width_m
    plan_width_m: float
    depth_m: float  # the section's other side: board thickness, or a plumb board's height
    area_m2: float
    outline: tuple[tuple[float, float], ...]
    run_axis: tuple[tuple[float, float], tuple[float, float]]
    z_start_m: float
    z_end_m: float
    free_edges: tuple[Edge3, ...] = ()
    raked_length_m: float | None = None


@dataclass(frozen=True)
class Flight:
    name: str
    frame: Frame
    profile: tuple[tuple[float, float], ...]  # outer stringer's cut profile
    c_lo: float  # outer stringer faces
    c_hi: float
    rake: tuple[tuple[float, float], tuple[float, float]]  # (s, z) low -> high
    head_top: float | None  # top of the plumb cut above the rake's high end
    horizontal_foot: bool


@dataclass(frozen=True)
class Landing:
    name: str
    polygon: Polygon
    underside_m: float


def flights(members) -> list[Flight]:
    """Stringer flights, grouped by key as ``checks/structural/stair_stringers._flights``."""
    groups: dict[str, list] = {}
    for member in members:
        if member.category == "stringer" and member.elevation_profile and member.p0 != member.p1:
            groups.setdefault(member.child_key.rsplit("-", 1)[0], []).append(member)
    out = []
    for key, stringers in sorted(groups.items()):
        first = stringers[0]
        dx, dy = first.p1[0] - first.p0[0], first.p1[1] - first.p0[1]
        run = math.hypot(dx, dy)
        u = (dx / run, dy / run)
        n = (-u[1], u[0])
        cs = [m.p0[0] * n[0] + m.p0[1] * n[1] for m in stringers]
        origin = (first.p0[0] - n[0] * cs[0], first.p0[1] - n[1] * cs[0])
        width = first.plan_width_m or cross_section(first.profile).width_m
        rake = _rake(first.elevation_profile)
        if rake is None:
            continue
        name = key.removeprefix("stringer").strip("-") or "flight"
        out.append(Flight(name, Frame(origin, u, n), tuple(first.elevation_profile),
                          min(cs) - width / 2.0, max(cs) + width / 2.0, rake,
                          _plumb_above(first.elevation_profile, rake[1]),
                          _horizontal_at(first.elevation_profile, rake[0])))
    return out


def _rake(ring) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """The longest sloped edge of the cut profile: the stringer's bottom, low end first."""
    best, length = None, 0.0
    for a, b in zip(ring, (*ring[1:], ring[0]), strict=True):
        ds, dz = b[0] - a[0], b[1] - a[1]
        if abs(ds) > 1e-3 and abs(dz) > 1e-3 and math.hypot(ds, dz) > length:
            best, length = (a, b) if a[1] < b[1] else (b, a), math.hypot(ds, dz)
    return best


def _neighbours(ring, vertex):
    index = next(i for i, p in enumerate(ring) if p == vertex)
    return ring[index - 1], ring[(index + 1) % len(ring)]


def _plumb_above(ring, vertex) -> float | None:
    tops = [p[1] for p in _neighbours(ring, vertex)
            if abs(p[0] - vertex[0]) < _EPS and p[1] > vertex[1] + _EPS]
    return max(tops) if tops else None


def _horizontal_at(ring, vertex) -> bool:
    return any(abs(p[1] - vertex[1]) < _EPS and abs(p[0] - vertex[0]) > _EPS
               for p in _neighbours(ring, vertex))


def landings(members) -> list[Landing]:
    """Each ``landing-{name}`` deck at the lowest of its own joists and rims (posts aside)."""
    out = []
    for deck in members:
        if deck.category != "landing" or not deck.child_key.startswith("landing-"):
            continue
        name = deck.child_key.removeprefix("landing-")
        framing = [m.z0_m for m in members if m.category == "landing_framing"
                   and m.p0 != m.p1 and (m.child_key.startswith(f"landing-joist-{name}-")
                                         or m.child_key.startswith(f"landing-rim-{name}-"))]
        z = min(framing, default=deck.z0_m)
        out.append(Landing(name, Polygon(member_footprint(deck)[0]), z))
    return out


def merged_landings(found: list[Landing]) -> list[Landing]:
    """Landings at one underside that make one rectangle are one board (a level U)."""
    by_z: dict[float, list[Landing]] = {}
    for landing in found:
        by_z.setdefault(round(landing.underside_m, 4), []).append(landing)
    out = []
    for group in by_z.values():
        shape = union_all([landing.polygon.buffer(1e-4, join_style=2) for landing in group])
        rect = aligned_rect(shape, group[0].polygon) if len(group) > 1 else None
        if rect is not None and isinstance(shape, Polygon) and abs(rect.area - shape.area) < 1e-3:
            out.append(Landing("+".join(sorted(g.name for g in group)), rect,
                               group[0].underside_m))
        else:
            out.extend(group)
    return out


def aligned_rect(shape, guide: Polygon) -> Polygon:
    """``shape``'s bounding rectangle along ``guide``'s longest edge (corners in order)."""
    ring = tuple(guide.exterior.coords)
    a, b = max(zip(ring, ring[1:], strict=False), key=lambda e: math.dist(*e))
    length = math.dist(a, b)
    frame = Frame(a, ((b[0] - a[0]) / length, (b[1] - a[1]) / length),
                  (-(b[1] - a[1]) / length, (b[0] - a[0]) / length))
    coords = [c for part in _polygons(shape) for c in part.exterior.coords]
    ss, cs = [frame.s_of(c) for c in coords], [frame.c_of(c) for c in coords]
    return frame.rect(min(ss), max(ss), min(cs), max(cs))


def wall_face(walls: list[tuple[Any, Polygon]], frame: Frame, c_face: float, outward: int,
              s0: float, s1: float, z0: float, z1: float) -> float | None:
    """Cross coordinate of the wall face backing this side, or None (a free side)."""
    strip = frame.rect(s0, s1, c_face, c_face + outward * WALL_REACH_M)
    faces, covered = [], []
    for wall, footprint in walls:
        if wall.z1_m <= z0 + _EPS or wall.z0_m >= z1 - _EPS:
            continue
        meet = intersection(footprint, strip)
        if meet.is_empty or meet.area < 1e-5:
            continue
        coords = [c for part in _polygons(meet) for c in part.exterior.coords]
        cs = [frame.c_of(p) for p in coords]
        faces.append(min(cs) if outward > 0 else max(cs))
        ss = [frame.s_of(p) for p in coords]
        covered.append((min(ss), max(ss)))
    if _covered_length(covered) < WALLED_FRACTION * (s1 - s0):
        return None
    return min(faces) if outward > 0 else max(faces)


def panel_spans(railings, frame: Frame, c_face: float) -> list[tuple[float, float]]:
    """Run intervals of this face an authored panel railing already covers."""
    spans = []
    for railing in railings:
        points = [p.xy_m for p in railing.path]
        for a, b in zip(points, points[1:], strict=False):
            if (abs(frame.c_of(a) - c_face) < PANEL_ON_FACE_M
                    and abs(frame.c_of(b) - c_face) < PANEL_ON_FACE_M):
                spans.append(tuple(sorted((frame.s_of(a), frame.s_of(b)))))
    return spans


def ceiling_clips(ceilings, footprint: Polygon, frame: Frame | None = None,
                  ) -> list[tuple[float, float, float]]:
    """``(s0, s1, z)`` for each ceiling over the board's footprint (s spans all without a frame)."""
    out = []
    for ceiling in ceilings:
        meet = intersection(Polygon(ceiling.outline), footprint)
        if meet.is_empty or meet.area < 1e-4:
            continue
        if frame is None:
            out.append((-1e3, 1e3, ceiling.z0_m))
            continue
        ss = [frame.s_of(c) for part in _polygons(meet) for c in part.exterior.coords]
        out.append((min(ss), max(ss), ceiling.z0_m))
    return out


def clip(shape, clips, *, spans=()) -> list[Polygon]:
    """``shape`` (in (s, z)) less what rises above a ceiling and what a panel covers."""
    for s0, s1, z in clips:
        shape = difference(shape, box(s0, z, s1, 1e3))
    for s0, s1 in spans:
        shape = difference(shape, box(s0, -1e3, s1, 1e3))
    return [p for p in _polygons(shape) if p.area > 1e-6]


def band(flight: Flight, thickness: float) -> tuple[Polygon, float, float]:
    """The raked board in (s, z), its vertical depth, and its slope."""
    (sa, za), (sb, zb) = flight.rake
    slope = (zb - za) / (sb - sa)
    depth = thickness * math.sqrt(1.0 + slope * slope)
    shape = Polygon([(sa, za - depth), (sb, zb - depth), (sb, zb), (sa, za)])
    if flight.horizontal_foot:  # it dies where the rake meets the floor
        shape = intersection(shape, box(sa - 1.0, za, sb + 1.0, zb + 1.0))
    return shape, depth, slope


def bottom_edges(flight: Flight, shape: Polygon, depth: float, c: float,
                 spans) -> tuple[Edge3, ...]:
    """The board's arris along one side, less what a panel covers."""
    (sa, za), (sb, zb) = flight.rake
    line = LineString([(sa, za - depth), (sb, zb - depth)])
    meet = intersection(line, shape.buffer(1e-5))
    out = []
    for piece in getattr(meet, "geoms", [meet]):
        if piece.is_empty or piece.geom_type != "LineString":
            continue
        (s0, z0), (s1, z1) = piece.coords[0], piece.coords[-1]
        for lo, hi in _gaps(sorted((min(s0, s1), max(s0, s1))), spans):
            zl = z0 + (z1 - z0) * (lo - s0) / (s1 - s0)
            zh = z0 + (z1 - z0) * (hi - s0) / (s1 - s0)
            out.append(((*flight.frame.at(lo, c), zl), (*flight.frame.at(hi, c), zh)))
    return tuple(out)


def _gaps(span, covered) -> list[tuple[float, float]]:
    out, cursor = [], span[0]
    for lo, hi in sorted(covered):
        if lo > cursor:
            out.append((cursor, min(lo, span[1])))
        cursor = max(cursor, hi)
    if cursor < span[1]:
        out.append((cursor, span[1]))
    return [(lo, hi) for lo, hi in out if hi - lo > 1e-4]


def _covered_length(spans) -> float:
    total, cursor = 0.0, -math.inf
    for lo, hi in sorted(spans):
        lo = max(lo, cursor)
        if hi > lo:
            total += hi - lo
            cursor = hi
    return total


def _polygons(shape) -> list[Polygon]:
    if isinstance(shape, Polygon):
        return [] if shape.is_empty else [shape]
    if isinstance(shape, MultiPolygon):
        return list(shape.geoms)
    return [g for g in getattr(shape, "geoms", ()) if isinstance(g, Polygon)]

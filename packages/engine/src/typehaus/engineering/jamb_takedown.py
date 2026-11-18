"""What a stacked jamb pack brings down onto a band-header seat (``band_header``).

Per seat, one tributary length along the wall line — half the opening's RO plus the seat —
the same on every storey the stack climbs. On each storey over the seat: the wall's dead
load (``WALL_DEAD_PSF`` over its framed height at the seat's outer face), the floor strip
its top carries (live + dead over half the way to the next joist line), and at a raked top
the roof strip of half a rafter spacing. Where the stack crosses a floor band, the solid
sections under the pack are found: a TJI loaded from above needs squash blocks (TJ-4000
detail CS). Stated and read numbers a reviewer redoes by hand; oracle
``notes/sunken_door_band_header.md`` §5.
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Point, Polygon

from typehaus.loads import FLOOR_DEAD_LOAD_PSF, FLOOR_LIVE_LOAD_PSF, ROOF_TOTAL_LOAD_PSF
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_walls import body_top_at, is_raked
from typehaus.resolve.model import on_joist_line
from typehaus.resolve.stacked_ladder import walls_over

_IN = 0.0254
_FT = 0.3048
#: The truss wall's dead load, carried high (note §5 adds it up to 10.0 psf).
WALL_DEAD_PSF = 15.0
#: Half of RF-HOUSE's 24" rafter spacing: what a gable carries of the roof.
GABLE_ROOF_STRIP_FT = 1.0
_SOLID = ("sister_joist", "rim", "blocking")
#: A floor whose joists top out within this of a wall's top is the floor that wall carries.
_LEVEL_M = 2 * _IN


@dataclass(frozen=True)
class Term:
    label: str
    lb: float


@dataclass(frozen=True)
class Crossing:
    """A floor band the stack crosses: what stands above it, and the solid under the pack."""

    floor: str
    above_lb: float
    solid_width_m: float
    members: tuple[str, ...]


def seat_takedown(plan, model, wall, point, along, seat, tributary_m):
    """``(terms, crossings)`` for one seat: ``point`` is its outer face on ``wall``'s line,
    ``seat`` its (lo, hi) stations along ``along``."""
    chain = [wall]
    while True:
        ups = [u for u, run in walls_over(plan, model.walls, chain[-1])
               if run[0] - 1e-6 <= _station(chain[-1], point) <= run[1] + 1e-6]
        if not ups:
            break
        chain.append(ups[0])
    terms, levels = [], []
    trib_ft = tributary_m / _FT
    for index, storey_wall in enumerate(chain):
        height = body_top_at(storey_wall, *point) - storey_wall.frame_base_z_m
        terms.append(Term(f"{storey_wall.tag} dead {WALL_DEAD_PSF:g} psf x "
                          f"{height / _IN:.3f}\"", WALL_DEAD_PSF * height / _FT * trib_ft))
        floor = _floor_on(model, storey_wall, point)
        if floor is not None:
            strip = _edge_strip(floor, storey_wall)
            terms.append(Term(f"{floor.tag} edge strip {strip / _IN:.2f}\"",
                              (FLOOR_LIVE_LOAD_PSF + FLOOR_DEAD_LOAD_PSF) * strip / _FT
                              * trib_ft))
            if index + 1 < len(chain):
                levels.append((len(terms), floor, chain[index + 1]))
        elif index + 1 == len(chain) and is_raked(storey_wall):
            terms.append(Term(f"gable roof strip {GABLE_ROOF_STRIP_FT:g} ft",
                              ROOF_TOTAL_LOAD_PSF * GABLE_ROOF_STRIP_FT * trib_ft))
    crossings = []
    for count, floor, upper in levels:
        # A band is crossed by a COLUMN only where the storey above stands a jamb pack on
        # the seat; a plain wall over it is a distributed load on the band's edge.
        if not _pack_over(upper, along, seat):
            continue
        width, members = _solid_under(floor, upper, along, seat)
        crossings.append(Crossing(floor.tag, sum(t.lb for t in terms[count:]), width, members))
    return terms, crossings


def _pack_over(wall, along, seat):
    """At least two jacks or kings of ``wall`` standing within the seat's stations."""
    return sum(1 for m in wall.members if m.category in ("jack", "king")
               and seat[0] - 1e-6 <= along(m.p0) <= seat[1] + 1e-6) >= 2


def _station(wall, point):
    (x0, y0), (x1, y1) = wall.axis
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1.0
    return ((point[0] - x0) * (x1 - x0) + (point[1] - y0) * (y1 - y0)) / length


def _floor_on(model, wall, point):
    probe = Point(point).buffer(_IN)
    for floor in model.floors:
        tops = [m.z1_m for m in floor.members if m.category == "joist"]
        if (tops and abs(max(tops) - wall.z1_m) <= _LEVEL_M
                and Polygon(floor.deck_outline).intersects(probe)):
            return floor
    return None


def _offset(wall, p):
    (x0, y0), (x1, y1) = wall.axis
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1.0
    return ((p[1] - y0) * (x1 - x0) - (p[0] - x0) * (y1 - y0)) / length


def _parallel(wall, member):
    return abs(_offset(wall, member.p0) - _offset(wall, member.p1)) < 1e-6


def _edge_strip(floor, wall):
    """Half the way from the joist line on ``wall``'s line to the next one, plus the deck
    outboard of it (an edge rim stands inboard of the wall's datum line)."""
    lines = sorted({round(_offset(wall, m.p0), 6) for m in floor.members
                    if on_joist_line(m) and _parallel(wall, m)}, key=abs)
    if len(lines) < 2:
        return 0.0
    host = lines[0]
    near = min((line - host for line in lines[1:] if abs(line - host) > 1e-6), key=abs)
    inward = 1.0 if near > 0 else -1.0
    outboard = max([0.0] + [(host - _offset(wall, p)) * inward for p in floor.deck_outline])
    return abs(near) / 2.0 + outboard


def _solid_under(floor, upper, along, seat):
    """Total width of solid sections over the wall band covering the seat's stations."""
    band = [_offset(upper, p) for layer in upper.layers for p in layer.polygon]
    lo, hi = (min(band), max(band)) if band else (0.0, 0.0)
    width, members = 0.0, []
    for member in floor.members:
        if (member.category not in _SOLID or "TJI" in member.profile
                or not _parallel(upper, member)
                or not lo - 1e-6 <= _offset(upper, member.p0) <= hi + 1e-6):
            continue
        a0, a1 = sorted((along(member.p0), along(member.p1)))
        if a0 <= seat[0] + 1e-6 and a1 >= seat[1] - 1e-6:
            width += cross_section(member.profile).width_m
            members.append(member.child_key)
    return width, tuple(members)

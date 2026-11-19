"""What bears on an edge rim from above: the concentrated loads a rim hole keeps out from under.

TJ-8000 (March 2025) p.4: "Do not locate holes under concentrated loads such as trimmers or
columns". Derived, never authored: the jamb packs (kings and jacks) of each wall standing on
the rim, a band header's stacked seats among them, and every post standing on it. The guide
states no distance, so each zone is the load's own bearing footprint along the rim.
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Polygon, box

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.solver import _structure_polygon
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedModel

_PACK_CATEGORIES = ("king", "jack")
_POST_CATEGORIES = ("column", "post")
#: A wall's plate seat or a post's base within this of the deck stands on the rim.
_SEAT_TOL_M = 0.025
_MIN_AREA_M2 = 1e-6
_JOIN_M = 1e-3


@dataclass(frozen=True)
class RimLoad:
    """A concentrated load's footprint on a rim: stations along the floor's joist axis."""

    lo_m: float
    hi_m: float
    source: str


def _rim_strip(floor: ResolvedFloor, rim: FramedMember) -> Polygon:
    along = 0 if floor.direction == "x" else 1
    centre, half = rim.p0[1 - along], cross_section(rim.profile).width_m / 2.0
    lo, hi = sorted((rim.p0[along], rim.p1[along]))
    if along == 0:
        return box(lo, centre - half, hi, centre + half)
    return box(centre - half, lo, centre + half, hi)


def _stud_footprint(wall, member: FramedMember) -> Polygon:
    (x0, y0), (x1, y1) = wall.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1.0
    ux, uy = (x1 - x0) / run, (y1 - y0) / run
    section = cross_section(member.profile)
    a, b = section.width_m / 2.0, section.depth_m / 2.0
    cx, cy = member.p0[0], member.p0[1]
    return Polygon([(cx + sa * a * ux - sb * b * uy, cy + sa * a * uy + sb * b * ux)
                    for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


def rim_point_loads(model: ResolvedModel, floor: ResolvedFloor,
                    rim: FramedMember) -> list[RimLoad]:
    """Each concentrated load on ``rim``, merged where a pack's members touch."""
    along = 0 if floor.direction == "x" else 1
    strip = _rim_strip(floor, rim)
    pieces: list[tuple[float, float, str]] = []

    def seated(z_m: float) -> bool:
        return floor.deck_z0_m - _SEAT_TOL_M <= z_m <= floor.deck_z1_m + _SEAT_TOL_M

    def over(footprint: Polygon, source: str) -> None:
        shared = footprint.intersection(strip)
        if shared.area > _MIN_AREA_M2:
            bounds = shared.bounds
            pieces.append((bounds[along], bounds[along + 2], source))

    for wall in model.walls:
        band = _structure_polygon(wall)
        if (wall.storey != floor.storey or len(band) < 3
                or not seated(wall.frame_base_z_m)
                or Polygon(band).intersection(strip).area <= _MIN_AREA_M2):
            continue
        for member in wall.members:
            if member.category in _PACK_CATEGORIES:
                over(_stud_footprint(wall, member), f"{wall.tag}'s jamb pack")
    for solid in model.solids:
        if (solid.category in _POST_CATEGORIES and len(solid.outline) >= 3
                and seated(solid.z0_m)):
            over(Polygon(solid.outline), f"post {solid.tag}")

    merged: list[RimLoad] = []
    for lo, hi, source in sorted(pieces):
        if merged and lo <= merged[-1].hi_m + _JOIN_M and merged[-1].source == source:
            merged[-1] = RimLoad(merged[-1].lo_m, max(merged[-1].hi_m, hi), source)
        else:
            merged.append(RimLoad(lo, hi, source))
    return merged

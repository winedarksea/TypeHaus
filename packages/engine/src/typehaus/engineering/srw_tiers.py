"""Tier geometry for a segmental wall: which taller retaining wall stands within 2H of it.

Split out of ``segmental_wall`` (file size). ``lower_tiers`` is what both the SRW record and
``tier_surcharge`` read, so the two cannot disagree about which court wall a leg loads.

**Facing.** The 2H rule is a TERRACE rule — an upper wall set back from a lower one that faces
the same way (AB Commercial Installation Manual p.60 "Terraces"; CMHA SRW-TEC-003). Each
wall's face points where its retained soil pushes it, ``-outward_sign * normal``
(``resolve/orientation``); two parallel walls whose faces point apart retain one fill from
opposite sides — back to back — and the rule is not theirs. A structure with no closed loop
has no recoverable winding and ``outward_sign`` is its authored direction, so an SRW's is
trusted only where the grade station its embedment is read to lies on that face's side;
otherwise facing is unknown and the row stands.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.registry import EngineeringContext

#: Two walls are designed independently only if the clear offset is >= 2 x the lower height.
TIER_FACTOR = 2.0
#: Axes within 10 degrees are parallel tiers; a perpendicular abutment is a corner.
_PARALLEL_SIN = math.sin(math.radians(10.0))
_M_PER_FT = 0.3048


@dataclass(frozen=True)
class Tier:
    tag: str
    lower_height_ft: float
    clear_ft: float
    parallel: bool
    #: True: faces point apart. None: facing could not be established.
    back_to_back: bool | None = None
    facing_basis: str = ""


def _footprint(resolved):  # type: ignore[no-untyped-def]
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    rings = [Polygon(layer.polygon) for layer in resolved.layers
             if not layer.is_cavity and len(layer.polygon) >= 3]
    return unary_union([r for r in rings if r.is_valid and r.area > 0]) if rings else None


def _direction(axis) -> tuple[float, float]:  # type: ignore[no-untyped-def]
    (ax, ay), (bx, by) = axis
    length = math.hypot(bx - ax, by - ay) or 1.0
    return (bx - ax) / length, (by - ay) / length


def _overlaps_along(axis, other) -> bool:  # type: ignore[no-untyped-def]
    """Whether ``other``'s axis projects onto a positive length of ``axis``."""
    (ax, ay), _ = axis
    ux, uy = _direction(axis)
    span = math.hypot(axis[1][0] - ax, axis[1][1] - ay)
    ts = sorted((px - ax) * ux + (py - ay) * uy for px, py in other)
    return min(ts[1], span) - max(ts[0], 0.0) > 1e-6


def _face(ctx: EngineeringContext, element, resolved
          ) -> tuple[tuple[float, float] | None, str]:  # type: ignore[no-untyped-def]
    """Unit vector the exposed face points along, and how it was established."""
    from shapely.geometry import Point

    from typehaus.resolve.orientation import resolve_storey_windings, wall_outward_sign
    from typehaus.resolve.site_earth import nearest_grade_station

    windings = resolve_storey_windings(ctx.plan, resolved.storey)
    sign = wall_outward_sign(ctx.plan, element, resolved.storey,
                             windings.sign_for_wall(element))
    (ax, ay), (bx, by) = resolved.axis
    ux, uy = _direction(resolved.axis)
    face = (sign * uy, -sign * ux)      # -sign x the left-hand normal (-uy, ux)
    if windings.outer_loop_area_by_component_key.get(windings.component_key_for_wall(element)):
        return face, "outward_sign (closed loop)"
    station = nearest_grade_station(ctx.model, Point((ax + bx) / 2.0, (ay + by) / 2.0))
    if station is None:
        return None, "no closed loop and no grade station"
    label, _ = station
    sx, sy = _station_xy(ctx, label)
    if sx is None or (sx - (ax + bx) / 2.0) * face[0] + (sy - (ay + by) / 2.0) * face[1] <= 0.0:
        return None, f"no closed loop, and {label} is not on the authored face's side"
    return face, f"authored direction, corroborated by {label}"


def _station_xy(ctx: EngineeringContext, label: str) -> tuple[float | None, float | None]:
    """The station ``nearest_grade_station`` named, by the index its label carries."""
    import re

    found = re.match(r"grade station (\d+) ", label)
    spots = ctx.model.plan.project.site.spot_elevations
    if not found or int(found.group(1)) >= len(spots):
        return None, None
    return spots[int(found.group(1))].position.xy_m


def lower_tiers(ctx: EngineeringContext, wall) -> list[Tier]:  # type: ignore[no-untyped-def]
    """Every taller RETAINING wall (authored ``unbalanced_fill`` above this wall's) whose clear
    offset is inside ``TIER_FACTOR`` x its height, parallel or not."""
    from typehaus.model.structure import FoundationWall

    resolved = {w.tag: w for w in ctx.model.walls}
    here = resolved.get(wall.tag)
    mine = _footprint(here) if here is not None else None
    if mine is None or wall.unbalanced_fill is None:
        return []
    ux, uy = _direction(here.axis)
    out = []
    for other in ctx.plan.all_elements():
        if not isinstance(other, FoundationWall) or other.tag == wall.tag:
            continue
        fill = other.unbalanced_fill
        if fill is None or fill.meters <= wall.unbalanced_fill.meters:
            continue
        # A basement wall braced by its floors does not rotate as a tier.
        if getattr(other, "lateral_support", None) == "top_and_bottom":
            continue
        theirs = resolved.get(other.tag)
        shape = _footprint(theirs) if theirs is not None else None
        if shape is None:
            continue
        lower = fill.meters / _M_PER_FT
        clear = mine.distance(shape) / _M_PER_FT
        if clear >= TIER_FACTOR * lower:
            continue
        vx, vy = _direction(theirs.axis)
        parallel = (abs(ux * vy - uy * vx) < _PARALLEL_SIN
                    and _overlaps_along(here.axis, theirs.axis))
        back, basis = None, ""
        if parallel:
            mine_face, mine_basis = _face(ctx, wall, here)
            their_face, their_basis = _face(ctx, other, theirs)
            if mine_face is None or their_face is None:
                basis = f"{wall.tag}: {mine_basis}; {other.tag}: {their_basis}"
            else:
                back = mine_face[0] * their_face[0] + mine_face[1] * their_face[1] < 0.0
                basis = f"{wall.tag}: {mine_basis}; {other.tag}: {their_basis}"
        out.append(Tier(other.tag, lower, clear, parallel, back, basis))
    return sorted(out, key=lambda t: (t.clear_ft, t.tag))

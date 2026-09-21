"""Tier geometry for a segmental wall: which taller retaining wall stands within 2H of it.

Split out of ``segmental_wall`` (file size). ``lower_tiers`` is what both the SRW record and
``tier_surcharge`` read, so the two cannot disagree about which court wall a leg loads.
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
        out.append(Tier(other.tag, lower, clear, parallel))
    return sorted(out, key=lambda t: (t.clear_ft, t.tag))

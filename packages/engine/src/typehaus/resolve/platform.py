"""Platform framing: exterior/bearing walls span floor-to-floor (#43).

Revit and SketchUp both expect a wall to run from its base level to the level above, with
the floor system butting into it. TypeHaus used to stop every wall at its own ceiling
height and patch the leftover joist band with a separate ``ResolvedEnvelopeBand`` proxy
object — which left a stud-depth void inboard of the sheathing and handed importers a
non-wall object at every storey line.

Here the lower wall simply grows to meet the wall stacked on it. Its *framing* does not:
``plate_top_z_m`` keeps the double top plate at the original ceiling height, so the band
above the plate is rim board and joists, which is what platform framing actually is.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel

# A storey line is a joist band. Anything deeper is a real void (a stairwell, a
# double-height space) and must not be silently absorbed into the wall below.
_MAX_BAND_M = inch(24).meters


def extend_walls_to_platform(model: ResolvedModel) -> None:
    """Grow each stacked lower wall up to the underside of the wall above it.

    The stack is the authored ``Wall.stacks_on`` graph — the same signal the old envelope
    band used — so this never guesses at which walls belong to one wall line.
    """
    lifted: set[str] = set()
    for upper in model.walls:
        authored = model.plan.by_tag(upper.tag)
        lower_tag = getattr(authored, "stacks_on", None)
        if not lower_tag or lower_tag in lifted:
            continue
        lower = model.wall(lower_tag)
        if lower is None or lower.is_foundation:
            continue
        band = upper.z0_m - lower.z1_m
        if band <= 1e-6 or band > _MAX_BAND_M:
            continue
        # A raked top (gable, wall-to-roof) has no flat platform to reach for.
        if lower.top_z0_m is not None or lower.top_z1_m is not None:
            continue
        _lift(model, lower, upper.z0_m)
        lifted.add(lower.tag)

    # ``stacks_on`` is authored by hand and is routinely incomplete — Catlin's attic names
    # 7 of the second storey's 15 walls. Everything it missed gets the geometric read:
    # a wall whose axis is covered by a wall above is on the same wall line.
    for lower in list(model.walls):
        if lower.tag in lifted or lower.is_foundation:
            continue
        if lower.top_z0_m is not None or lower.top_z1_m is not None:
            continue
        z = _platform_above(model, lower)
        if z is None:
            continue
        band = z - lower.z1_m
        if band <= 1e-6 or band > _MAX_BAND_M:
            continue
        _lift(model, lower, z)
        lifted.add(lower.tag)


def _lift(model: ResolvedModel, lower, z1: float) -> None:
    index = next(i for i, w in enumerate(model.walls) if w is lower)
    model.walls[index] = replace(lower, z1_m=z1, plate_top_z_m=lower.z1_m)


def _platform_above(model: ResolvedModel, lower) -> float | None:
    """Lowest ``z0_m`` among walls that sit on ``lower``'s axis, from above."""
    tol = max(lower.thickness_m, 1e-3)
    best: float | None = None
    for upper in model.walls:
        if upper is lower or upper.is_foundation or upper.z0_m < lower.z1_m - 1e-6:
            continue
        if not _collinear_overlap(lower.axis, upper.axis, tol):
            continue
        if best is None or upper.z0_m < best:
            best = upper.z0_m
    return best


def _collinear_overlap(a, b, tol: float) -> bool:
    """Do segments ``a`` and ``b`` share a direction, a line (within ``tol``), and length?"""
    (ax0, ay0), (ax1, ay1) = a
    dx, dy = ax1 - ax0, ay1 - ay0
    span = math.hypot(dx, dy)
    if span < 1e-9:
        return False
    ux, uy = dx / span, dy / span
    ts = []
    for (px, py) in b:
        ex, ey = px - ax0, py - ay0
        if abs(-uy * ex + ux * ey) > tol:  # perpendicular distance off a's line
            return False
        ts.append(ux * ex + uy * ey)
    lo, hi = min(ts), max(ts)
    return min(hi, span) - max(lo, 0.0) > tol

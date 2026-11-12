"""Where a wall-junction detail cuts along its wall: clear of openings, onto a floor member.

A stack detail (rim band, stack shelf) is about the floor between two walls, so its cut must
pass a joist or rim of that floor; a cut down a joist bay draws no floor (REPORT §1.17).
"""

from __future__ import annotations

import math

from typehaus.resolve.framing.footprint import member_footprint

# Clearance kept between a wall-junction cut and any opening's framed extent.
_OPENING_CLEAR_M = 0.15
_BAND_TOL_M = 0.05  # matches floor_band_at's straddle tolerance
_MAX_CANDIDATES = 24


def _axis_frame(wall):
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    if length <= 1e-9:
        return 0.0, lambda px, py: 0.0
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    return length, lambda px, py: (px - x0) * ux + (py - y0) * uy


def _clear_limits(model, cond, wall):
    """``(length, lo_ok, hi_ok, blocked)`` along the wall axis for a cut clear of openings."""
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    (x0, y0), (x1, y1) = wall.axis
    length, along = _axis_frame(wall)
    if length <= 1e-9:
        return 0.0, 0.0, 0.0, []
    walls = [w for w in condition_walls(model, cond) if w.tag != wall.tag]
    tags = {w.tag for w in walls} | {wall.tag}
    span_lo, span_hi = 0.0, length
    for other in walls:
        a, b = (along(*point) for point in other.axis)
        span_lo, span_hi = max(span_lo, min(a, b)), min(span_hi, max(a, b))
    if span_hi - span_lo <= 2 * _OPENING_CLEAR_M:
        span_lo, span_hi = 0.0, length
    blocked: list[tuple[float, float]] = []
    for opening in model.openings:
        host = model.wall(opening.host_wall) if opening.host_wall in tags else None
        if host is None:
            continue
        (hx0, hy0), (hx1, hy1) = host.axis
        h_len = math.hypot(hx1 - hx0, hy1 - hy0)
        if h_len <= 1e-9:
            continue
        hux, huy = (hx1 - hx0) / h_len, (hy1 - hy0) / h_len
        lo = opening.center_along_m - opening.width_m / 2
        hi = opening.center_along_m + opening.width_m / 2
        if opening.pocket_sign > 0:
            hi += opening.pocket_run_m
        elif opening.pocket_sign < 0:
            lo -= opening.pocket_run_m
        ends = [along(hx0 + hux * a, hy0 + huy * a) for a in (lo, hi)]
        blocked.append((min(ends) - _OPENING_CLEAR_M, max(ends) + _OPENING_CLEAR_M))
    return length, span_lo + _OPENING_CLEAR_M, span_hi - _OPENING_CLEAR_M, blocked


def clear_fraction(model, cond, wall) -> float:
    """Axis fraction for a wall-junction cut: inside every named wall, clear of their openings.

    A wall-junction detail (rim, foundation, eave) is about the wall, not a window, and a
    stack is only a stack where both walls exist: a 9' upper wall over a 36' lower one has
    no rim at the lower wall's midpoint. The midpoint stands when it cuts cleanly; otherwise
    the cut slides to the nearest station inside the walls' common span that misses every
    opening on any of them.
    """
    length, lo_ok, hi_ok, blocked = _clear_limits(model, cond, wall)
    if length <= 1e-9:
        return 0.5
    mid = length / 2
    if lo_ok <= mid <= hi_ok and not any(lo < mid < hi for lo, hi in blocked):
        return 0.5  # the midpoint already cuts the junction cleanly
    target = min(max(mid, lo_ok), hi_ok)
    candidates = [a for a in (target, *(edge for pair in blocked for edge in pair))
                  if lo_ok <= a <= hi_ok and not any(lo < a < hi for lo, hi in blocked)]
    return min(candidates, key=lambda a: abs(a - mid), default=target) / length


def stack_pair(model, cond):
    """``(lower, upper)`` walls of a stack condition, or ``(None, None)``."""
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    walls = sorted(condition_walls(model, cond), key=lambda w: w.z0_m)
    if len(walls) < 2 or walls[-1].z0_m <= walls[0].z0_m:
        return None, None
    return walls[0], walls[-1]


def stack_has_floor(model, derived, upper) -> bool:
    """Whether the cut shows the floor between the stacked walls: a floor member is cut and its
    band sits in the crop (what the drawing reads; a band out of frame draws nothing)."""
    from typehaus.emit.draw.detail_components.geometry import floor_band_at

    c0, c1 = derived.view.crop
    band = floor_band_at(model, upper.z0_m, derived.direction, derived.station,
                         (c0.xy_m, c1.xy_m))
    if band is None:
        return False
    z_lo, z_hi = sorted((c0.xy_m[1], c1.xy_m[1]))
    return band[1] >= z_lo and band[0] <= z_hi


def floor_fractions(model, cond, wall, upper, base_t: float) -> list[float]:
    """Axis fractions that land on a joist or rim of the floor under ``upper``, clear of
    openings, nearest the default cut first."""
    from typehaus.emit.draw.detail_components.geometry import _BAND_STRADDLE_TOLERANCE_M

    length, lo_ok, hi_ok, blocked = _clear_limits(model, cond, wall)
    if length <= 1e-9:
        return []
    _length, along = _axis_frame(wall)
    z, mid = upper.z0_m, base_t * length
    found: dict[float, float] = {}
    for floor in model.floors:
        for member in floor.members:
            if member.category not in ("joist", "rim"):
                continue
            low, high = sorted((member.z0_m, member.z1_m))
            if not low - _BAND_STRADDLE_TOLERANCE_M <= z <= high + _BAND_STRADDLE_TOLERANCE_M:
                continue
            ring = member_footprint(member)[0]
            spans = [along(px, py) for px, py in ring]
            a0, a1 = max(min(spans), lo_ok), min(max(spans), hi_ok)
            if a0 > a1:
                continue
            at = (a0 + a1) / 2 if a1 - a0 < 0.1 else min(max(mid, a0 + 0.02), a1 - 0.02)
            if not any(lo < at < hi for lo, hi in blocked):
                found[round(at, 3)] = at
    ordered = sorted(found.values(), key=lambda at: abs(at - mid))
    return [at / length for at in ordered[:_MAX_CANDIDATES]]

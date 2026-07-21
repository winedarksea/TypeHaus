"""Platform framing leaves no unclad joist band (#43 follow-up).

``stacks_on`` is authored by hand, so it reached only half of catlin's second-storey
walls and the rest stopped a joist depth below the attic — a 12" ring of bare rim board
around the building. The regression that matters is the absence of the gap, not which
tags happen to need the geometric fallback.
"""

from __future__ import annotations

import math

from typehaus.quantities import inch
from typehaus.resolve.orientation import storey_outward_sign
from typehaus.resolve.platform import _MAX_BAND_M


def _collinear_overlap(a, b, tol: float) -> bool:
    (ax0, ay0), (ax1, ay1) = a
    dx, dy = ax1 - ax0, ay1 - ay0
    span = math.hypot(dx, dy)
    ux, uy = dx / span, dy / span
    ts = []
    for (px, py) in b:
        ex, ey = px - ax0, py - ay0
        if abs(-uy * ex + ux * ey) > tol:
            return False
        ts.append(ux * ex + uy * ey)
    return min(max(ts), span) - max(min(ts), 0.0) > tol


def test_no_wall_leaves_a_joist_band_below_the_storey_above(catlin_model):
    walls = list(catlin_model.walls)
    gaps = []
    for lower in walls:
        if lower.is_foundation or lower.top_z0_m is not None:
            continue
        tol = max(lower.thickness_m, 1e-3)
        above = [
            u.z0_m for u in walls
            if u is not lower and not u.is_foundation and u.z0_m >= lower.z1_m - 1e-6
            and _collinear_overlap(lower.axis, u.axis, tol)
        ]
        if not above:
            continue
        band = min(above) - lower.z1_m
        # Anything deeper than the guard is a real void, deliberately not absorbed.
        if 1e-6 < band <= _MAX_BAND_M:
            gaps.append((lower.tag, band))
    assert not gaps, gaps


def test_lifted_walls_keep_their_plate_at_the_old_ceiling(catlin_model):
    lifted = [w for w in catlin_model.walls if w.plate_top_z_m is not None]
    assert lifted, "expected catlin walls to be extended to the platform above"
    for w in lifted:
        assert w.plate_top_z_m < w.z1_m
        assert w.z1_m - w.plate_top_z_m <= inch(24).meters


def test_catlin_exterior_loops_are_authored_counter_clockwise(catlin_model):
    """The mirror fix is load-bearing: catlin's storeys need the flip."""
    plan = catlin_model.plan
    assert storey_outward_sign(plan, "main") == -1.0
    assert storey_outward_sign(plan, "second") == -1.0

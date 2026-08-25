"""Platform framing leaves no unclad joist band (#43 follow-up).

``stacks_on`` is authored by hand, so it reached only half of catlin's second-storey
walls and the rest stopped a joist depth below the attic — a 12" ring of bare rim board
around the building. The regression that matters is the absence of the gap, not which
tags happen to need the geometric fallback.

The ring this was written to catch had one storey line it could not see: the test opened
with ``if lower.is_foundation: continue``, which excluded the basement-to-main line by
construction — the exact line that was open, ~108 LF of it, from the day the pour stopped
at the bearing seat 13 7/16" below the storey datum. ``extend_walls_to_foundation`` closes
it and the exclusion is gone.

The band is covered if *anything* on the wall line reaches the wall above, not only the
wall below. Catlin's south wall is why: the pour stops at the seat there too, but
``W-B-BRICK`` — a freestanding glazed wythe standing in front of it — runs all the way to
0'-0", so the band is clad and the framed wall above it must not be dragged down behind a
veneer.
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


def test_no_wall_line_leaves_a_bare_band_under_a_clad_wall(catlin_model):
    """Asked of the wall *line*, not of one wall, which is what lets it cover both ends.

    Written the other way round — for each lower wall, is anything above it? — it could only
    see the wall directly beneath, and neither end of catlin's south line has one: the pour
    stops at the bearing seat and it is ``W-B-BRICK``, a freestanding wythe standing in front
    of it, that runs up to meet ``W-M-S1``. Asking instead "does anything on this line reach
    the base of this wall" reads the veneer, the pour and the storey below with one rule.

    Restricted to clad walls, because bare rim board is an *envelope* condition: under an
    interior bearing wall the band is a joist bay over the basement, with no skin on either
    side of it that could be continuous.
    """
    walls = list(catlin_model.walls)
    gaps = []
    for upper in walls:
        if upper.is_foundation:
            continue
        if not any(ly.function == "cladding" for ly in upper.layers):
            continue
        tol = max(upper.thickness_m, 1e-3)
        below = [w.z1_m for w in walls
                 if w is not upper and w.z1_m <= upper.z0_m + 1e-6
                 and _collinear_overlap(upper.axis, w.axis, tol)]
        if not below:
            continue
        band = upper.z0_m - max(below)
        # Anything deeper than the guard is a real void, deliberately not absorbed.
        if 1e-6 < band <= _MAX_BAND_M:
            gaps.append((upper.tag, band))
    assert not gaps, gaps


def test_the_basement_to_main_line_is_clad_over_the_mudsill_and_rim(catlin_model):
    """The bug the exclusion above was hiding, pinned by name.

    The pour tops out at the bearing seat — mudsill + gasket + an 11 7/8" rim below the
    main-floor datum — and every ``W-M-*`` used to start at the datum. ``envelope_layer_
    takeoff`` bills per wall, so the band was a quantity shortfall (~121 SF of cladding, CI,
    WRB and sheathing on 108 LF), not a render artifact.
    """
    dropped = [w for w in catlin_model.walls if w.plate_base_z_m is not None]
    assert dropped, "no wall was extended down to its foundation"
    for wall in dropped:
        # The framing stays on the storey datum; only the skin moves.
        assert wall.plate_base_z_m > wall.z0_m
        assert wall.z0_m - wall.plate_base_z_m >= -_MAX_BAND_M
        assert wall.base_ref_z_m == wall.plate_base_z_m
        # An interior partition has no skin to lap and must not be extended.
        assert any(ly.function == "cladding" for ly in wall.layers), wall.tag

    band = {round((w.plate_base_z_m - w.z0_m) / inch(1).meters, 3) for w in dropped}
    assert band == {13.437}, band


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

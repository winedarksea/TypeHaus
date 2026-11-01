"""The low-end birdsmouth on a rafter-framed eave, and the deck plane it fixes (decision #109).

The plane is anchored at the HEEL: the plumb cut on the bearing plate's outer face. The seat
runs inward from it, flat on the plate top, to where the rafter's underside meets the plate,
so the notch at the heel is ``seat x slope`` and the deck there stands ``plumb depth - notch``
above the plate. ``plumb depth`` is the TRUE one, ``d x sqrt(1 + slope^2)``: a member's
perpendicular depth read vertically is 1.40" short on an 11 7/8" joist at 6:12.

The seat run is the one input. TJ-4000 (Jul 2025) p.31 R5 and APA D710A 10h: a birdsmouth at
the LOW end only, the flange bearing fully on the plate, the cut never past its inside face,
beveled web stiffeners both sides. ``checks/structural/_rafter_seat.ijoist_seat_problems``
grades it.
"""

from __future__ import annotations

import math

from typehaus.quantities import inch

#: The seat, heel to the underside's crossing of the plate top. 2 1/2" sits inside a TJI
#: 230's legal band at 6:12 — >= 1 3/4" bearing (TJ-4000 p.32) and a notch no deeper than
#: the 1 1/4" flange's 1.40" plumb depth (seat <= 2.80").
RAFTER_SEAT_RUN_M = inch(2.5).meters


def plumb_depth_m(depth_m: float, slope: float) -> float:
    """A sloped member's depth measured straight up."""
    return depth_m * math.hypot(1.0, slope)


def heel_deck_rise_m(depth_m: float, slope: float,
                     seat_run_m: float = RAFTER_SEAT_RUN_M) -> float:
    """Deck plane above the plate top, at the heel."""
    return plumb_depth_m(depth_m, slope) - seat_run_m * slope


def eave_deck_z_m(plate_top_z_m: float, heel_inset_m: float, depth_m: float, slope: float,
                  seat_run_m: float = RAFTER_SEAT_RUN_M) -> float:
    """Deck plane at the footprint edge, ``heel_inset_m`` outboard of the heel.

    The one formula a house's params read (``houses/catlin/params/roof_panel.py``), so its
    trim and clamps cannot drift from the resolved plane.
    """
    return plate_top_z_m + heel_deck_rise_m(depth_m, slope, seat_run_m) - heel_inset_m * slope


def rafter_eave_z_m(footprint, ridge_direction: str, form: str, bearings,
                    plate_top_z_m: float, heel_rise_m: float, slope: float) -> float:
    """``ResolvedRoof.eave_z_m`` for a rafter roof: the deck at the footprint edge.

    Each eave's heel is its bearing's outer face (``RoofBearing.support_span``). Where two
    eaves disagree, the nearer heel governs: the plane rises, so no notch is cut deeper than
    the seat input and the other eave's seat comes out shorter, which the check grades.
    """
    axis = 1 if ridge_direction == "x" else 0
    coords = [point[axis] for point in footprint]
    low, high = min(coords), max(coords)
    middle = (low + high) / 2.0
    insets = []
    for bearing in bearings:
        face_lo, face_hi = bearing.support_span(axis)
        if bearing.axis[0][axis] < middle:
            insets.append(face_lo - low)
        elif form != "shed":
            insets.append(high - face_hi)
    inset = min(insets) if insets else 0.0
    return plate_top_z_m + heel_rise_m - inset * slope

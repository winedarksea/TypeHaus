"""ICC-ES ESR-1078 (reissued January 2026): the TimberLOK rows the girt screw is read from.

Pure numbers, no model types: the part a reviewer checks line by line against the report.
Each row below is quoted in the report's own words in ``notes/catlin_truss_engineering.md``
§3. The report is the capacity; this module only says what the report's rows ARE, so
``girt_fastening`` can refuse an authored value the row does not support.

**A screw has two lengths.** Overall length is on the box; THREAD length decides whether the
screw works. A lag-type screw draws a stack together only if plain SHANK spans it: thread in
the near member jacks it away from the far one. ``plain shank = L - T`` must span the clamped
stack.
"""

from __future__ import annotations

import math

#: Table 1A, OlyLog/TimberLOK, designation -> (overall length, thread length incl. tip), in.
TIMBERLOK_1A = {"TLOK212": (2.5, 1.25), "TLOK04": (4.0, 2.0), "TLOK06": (6.0, 2.0),
                "TLOK08": (8.0, 2.0), "TLOK10": (10.0, 2.0)}
#: Table 1A, 0.189" shank; allowable tensile strength of TLOK212-TLOK08, lbf. Not increased.
SHANK_DIAMETER_IN = 0.189
TENSILE_LB = 1300.0

#: Table 2, OlyLog/TimberLOK reference withdrawal W90 (lbf/in) by specific gravity, at the
#: row's minimum embedded thread of 1.25".
MIN_EMBEDDED_THREAD_IN = 1.25
WITHDRAWAL_LB_PER_IN = {0.57: 270.0, 0.55: 260.0, 0.50: 220.0, 0.46: 200.0,
                        0.43: 180.0, 0.42: 170.0}
#: Table 3, OlyLog/TimberLOK reference head pull-through WH (lbf) by specific gravity, at a
#: minimum side member thickness of 1-1/2".
MIN_SIDE_MEMBER_IN = 1.5
PULL_THROUGH_LB = {0.57: 220.0, 0.55: 200.0, 0.50: 160.0, 0.46: 130.0,
                   0.43: 110.0, 0.42: 110.0}

#: Table 4, OlyLog/TimberLOK, minimum overall length 2-1/2", 1-1/2" side member, 1" main member
#: penetration (note 4: full thread embedment not required): Z (lbf) at the lower of the two
#: members' SG 0.50 / 0.46 / 0.42. Footnote 2 lets a thicker side member be used where the
#: row's main penetration is still achieved. (Zll, Z_perp); the lower governs here.
LATERAL_LB = {0.50: (240.0, 220.0), 0.46: (220.0, 200.0), 0.42: (200.0, 180.0)}

#: AWC NDS 2018 (read 2026-11-23): Table 2.3.2 wind/earthquake C_D 1.6 and dead 0.9; 11.3.2 caps
#: connections at 1.6 and exempts metal strength; Table 11.3.1 applies C_D to lateral, withdrawal
#: and pull-through; Table 11.3.3 wet service (in-service MC > 19%) C_M 0.7 for lateral
#: dowel-type, lag/wood-screw withdrawal and round-head pull-through. ESR-1078 §4.1.2 sends the
#: Tables 2-4 values to NDS 11.3. The 1,300 lbf tension is metal strength: no factor.
C_D_WIND = 1.6
C_D_DEAD = 0.9
WET_SERVICE_FACTOR = 0.70

#: Reaction factors from statics, not tables: an interior support of two equal spans takes
#: 5wL/4 (the 2x4 girt over blocks). The panel runs over five or more girts, and its worst
#: interior reaction over three or more equal spans is the 4-span value, 8/7 wL (3 spans 1.10,
#: 5 spans 1.132, many 1.134).
GIRT_CONTINUITY = 1.25
PANEL_CONTINUITY = 8.0 / 7.0

#: Gravity prying (note §3.5a). On a vertical wall the crossing's weight acts PARALLEL to the
#: sheathing, hung off its face, so each block tips about its bottom edge and the screw, at the
#: block's mid-height, takes the moment. Block face is a 2x4's 3-1/2" (``truss_girts``).
BLOCK_FACE_IN = 3.5
#: Panel dead load, psf: 24 ga standing seam (note §2), the heavier of the house's skins.
PANEL_DEAD_PSF = 1.2
LB_PER_IN3_PER_KG_M3 = 0.062428 / 1728.0


def prying(block_in: float, course_in: float, girt_in: float, block_depth_in: float,
           panel_in: float, density_kg_m3: float) -> tuple[float, float, float]:
    """(crossing weight lb, moment about the block's bottom edge in-lb, screw tension lb).

    Weights: the panel's tributary, the girt length of one block module, one block (face
    3-1/2" square, ``block_depth_in`` deep), the two woods at ``density_kg_m3``. Each acts at
    its own centroid's distance off the sheathing face; the screw is ``BLOCK_FACE_IN / 2``
    above the pivot.
    """
    wood = density_kg_m3 * LB_PER_IN3_PER_KG_M3
    parts = (
        (PANEL_DEAD_PSF * tributary_area_ft2(block_in, course_in),
         block_depth_in + girt_in + panel_in / 2.0),
        (wood * girt_in * BLOCK_FACE_IN * block_in, block_depth_in + girt_in / 2.0),
        (wood * BLOCK_FACE_IN * BLOCK_FACE_IN * block_depth_in, block_depth_in / 2.0),
    )
    weight = sum(w for w, _ in parts)
    moment = sum(w * e for w, e in parts)
    return weight, moment, moment / (BLOCK_FACE_IN / 2.0)


def combined_allowable_lb(withdrawal_lb: float, lateral_lb: float, alpha_rad: float) -> float:
    """NDS 2018 eq. 12.4-1: Z'a = W'p Z' / (W'p cos^2 a + Z' sin^2 a), a the angle between the
    wood surface and the load. ``withdrawal_lb`` is W'p (adjusted W x thread penetration)."""
    cos, sin = math.cos(alpha_rad), math.sin(alpha_rad)
    return withdrawal_lb * lateral_lb / (withdrawal_lb * cos ** 2 + lateral_lb * sin ** 2)


def row_at(table: dict[float, float], specific_gravity: float) -> float | None:
    """The row at or just below ``specific_gravity``; ``None`` below the lowest tabulated."""
    eligible = [sg for sg in table if sg <= specific_gravity + 1e-9]
    return table[max(eligible)] if eligible else None


def plain_shank_in(length_in: float, thread_in: float) -> float:
    """The unthreaded run below the head: what has to span the clamped stack."""
    return length_in - thread_in


def thread_in_side_member(length_in: float, thread_in: float, clamped_stack_in: float) -> float:
    """Thread standing INSIDE the clamped members. Above zero is a jack; zero is the target."""
    return max(thread_in - (length_in - clamped_stack_in), 0.0)


def thread_in_main_member(length_in: float, thread_in: float, through_in: float) -> float:
    """Embedded thread in the stud. ``through_in`` is the whole stack plus the sheathing,
    which is nailed to the stud and so counts on the stud's side of the joint. Table 2 is
    per inch of embedded thread to the point, so no tip is deducted twice."""
    return max(min(thread_in, length_in - through_in), 0.0)


def tributary_area_ft2(block_spacing_in: float, course_spacing_in: float) -> float:
    """One crossing's share of the wall: block module x course module."""
    return (block_spacing_in / 12.0) * (course_spacing_in / 12.0)


def crossing_demand_lb(pressure_psf: float, block_spacing_in: float,
                       course_spacing_in: float) -> float:
    """ASD 0.6W reaction on one screw: pressure x tributary x girt and panel continuity.

    The uniform-load tributary is the SIMPLE-span reaction; an interior screw of a girt
    continuous over the blocks, under a panel continuous over the girts, takes more.
    """
    return (pressure_psf * tributary_area_ft2(block_spacing_in, course_spacing_in)
            * GIRT_CONTINUITY * PANEL_CONTINUITY)

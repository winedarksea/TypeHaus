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

#: Table 3 footnote and §4.1.2: the reference values are dry-service; wet service takes the
#: NDS C_M. 0.70 is the house's wet bound for a screw into treated pine (the door-sill course
#: reads the same factor), printed beside the dry result and never applied to it.
WET_SERVICE_FACTOR = 0.70

#: Reaction factors from statics, not tables: an interior support of two equal spans takes
#: 5wL/4 (the 2x4 girt over blocks) and of three or more takes 11wL/10 (the panel over girts).
GIRT_CONTINUITY = 1.25
PANEL_CONTINUITY = 1.10


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
    """ASD reaction on one screw: pressure x tributary x girt and panel continuity.

    The uniform-load tributary is the SIMPLE-span reaction; an interior screw of a girt
    continuous over the blocks, under a panel continuous over the girts, takes more.
    """
    return (pressure_psf * tributary_area_ft2(block_spacing_in, course_spacing_in)
            * GIRT_CONTINUITY * PANEL_CONTINUITY)

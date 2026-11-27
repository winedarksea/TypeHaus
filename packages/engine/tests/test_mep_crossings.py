"""One owner for "the window a service gets through a floor's members".

Three readings existed and no two agreed. ``resolve/mep_crossings.py`` is the one place
they live now; ``routing/corridors.crossing_window`` and ``duct_bay_occupancy`` read it.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_crossings import (
    SOLID_SAWN_EDGE_CLEARANCE_M,
    is_member_line,
    leg_crossings,
    member_window,
)


def _floor(model, tag):
    return next(f for f in model.floors if f.tag == tag)


def test_open_web_truss_gets_its_web(catlin_model_ro) -> None:
    """FS-S-WEST is 11 7/8" floor trusses: 8 7/8" chord-to-chord at 109.625..118.5.

    The note's §3 derives both numbers by hand; this is the engine agreeing with it.
    """
    window = member_window(_floor(catlin_model_ro, "FS-S-WEST"))
    assert window is not None
    assert window.kind == "open_web"
    assert window.height_m / M_PER_IN == pytest.approx(8.875)
    assert window.z0_m / M_PER_IN == pytest.approx(109.625)
    assert window.z1_m / M_PER_IN == pytest.approx(118.5)
    assert "chord-to-chord" in window.basis


def test_an_i_joist_field_is_not_a_truss_field(catlin_model_ro) -> None:
    """FS-S-EAST is the same 11 7/8" depth in TJI 230s — a different rule, a wider window:
    inside both 1 1/4" flanges (the low end of TJ-4000's published band), 9 3/8".

    And the PASS it produces is **qualified**: the flange is clear, and the hole's diameter
    and its allowable zone along the span still come off the fabricator's chart. The old
    hardcoded-chord fallback answered 8 7/8" here too, which is right for the truss floor
    next door and wrong for this one.
    """
    window = member_window(_floor(catlin_model_ro, "FS-S-EAST"))
    assert window is not None
    assert window.kind == "i_joist"
    assert window.height_m / M_PER_IN == pytest.approx(11.875 - 2 * 1.25)
    assert "chart" in window.basis

    truss = member_window(_floor(catlin_model_ro, "FS-S-WEST"))
    assert truss is not None
    assert window.height_m != pytest.approx(truss.height_m)


def test_solid_sawn_takes_r502_8_1(catlin_model_ro) -> None:
    """A 2x12 deck (the porch since 2026-09): depth less 2" at each edge, and the citation
    is a code section."""
    window = member_window(_floor(catlin_model_ro, "FS-SG-PORCH"))
    assert window is not None
    assert window.kind == "solid_sawn"
    assert window.height_m / M_PER_IN == pytest.approx(11.25 - 2 * 2.0)
    assert "R502.8.1" in window.basis
    assert pytest.approx(2.0) == SOLID_SAWN_EDGE_CLEARANCE_M / M_PER_IN


def test_the_window_is_read_off_a_joist_not_whichever_member_came_first(
        catlin_model_ro) -> None:
    """``members[0]`` is a rim board on most floors, and a rim board is never an open web."""
    floor = _floor(catlin_model_ro, "FS-S-WEST")
    placed = [m for m in floor.members if m.z0_m is not None]
    rim = next(m for m in placed if m.category == "rim")
    assert member_window(floor, rim) != member_window(floor)
    assert member_window(floor).kind == "open_web"


def test_an_edge_rim_is_bored_centred_and_the_strongback_butts_it(catlin_model_ro) -> None:
    """FS-S-WEST's south edge is an LSL rim (TJ-8000 p.4: a centred round hole up to 2/3 of
    its depth), and FS-M-NE's strongbacks stop at its north rim's inner face."""
    floor = _floor(catlin_model_ro, "FS-S-WEST")
    rim = next(m for m in floor.members if m.child_key.startswith("edge-rim-"))
    window = member_window(floor, rim)
    assert window.kind == "rim_board" and "TJ-8000" in window.basis
    assert window.height_m / M_PER_IN == pytest.approx(11.875 * 2 / 3)
    north = _floor(catlin_model_ro, "FS-M-NE")
    ends = {round(max(m.p0[1], m.p1[1]) / M_PER_IN, 3) for m in north.members
            if m.category == "strongback"}
    assert max(ends) == pytest.approx(430.25)


def test_an_edge_rim_hole_keeps_twice_its_diameter_off_the_rim_end(catlin_model_ro) -> None:
    """TJ-8000 p.4's end distance: 2D for a round hole, 3L for a rectangle."""
    from typehaus.checks.mep.routing_members import _rim_end_finding

    floor = _floor(catlin_model_ro, "FS-S-WEST")
    rim = next(m for m in floor.members if m.child_key.startswith("edge-rim-"))
    end = min(rim.p0[0], rim.p1[0])
    hole = 1.0 * M_PER_IN
    assert _rim_end_finding("conduit", "T", floor, rim, end + 2.6 * M_PER_IN, hole, True) is None
    short = _rim_end_finding("conduit", "T", floor, rim, end + 2.4 * M_PER_IN, hole, True)
    assert short is not None and short.result.value == "fail"
    assert _rim_end_finding("duct", "T", floor, rim, end + 2.6 * M_PER_IN, hole, False)


def test_no_edge_rim_hole_under_a_jamb_pack(catlin_model_ro) -> None:
    """TJ-8000 p.4: no rim hole under a concentrated load. CD-M-DATA-PORCH crosses
    FS-S-WEST's south rim at x ~ 181.9", under WIN-S-PLANT4's RO and clear of its east
    jamb pack (W-S-S1's king and jack, 191..194"); the same hole there would FAIL."""
    from typehaus.checks.mep.routing_members import _rim_load_finding
    from typehaus.resolve.rim_loads import rim_point_loads

    floor = _floor(catlin_model_ro, "FS-S-WEST")
    rim = next(m for m in floor.members if m.child_key.startswith("edge-rim-"))
    loads = rim_point_loads(catlin_model_ro, floor, rim)
    east = next(load for load in loads if load.lo_m / M_PER_IN > 185.0)
    assert (east.lo_m / M_PER_IN, east.hi_m / M_PER_IN) == pytest.approx((191.0, 194.0))
    assert east.source == "W-S-S1's jamb pack"
    hole = 0.922 * M_PER_IN
    assert _rim_load_finding("conduit", "T", floor, rim.child_key, 181.9 * M_PER_IN, hole,
                             loads) is None
    under = _rim_load_finding("conduit", "T", floor, rim.child_key, 190.8 * M_PER_IN, hole,
                              loads)
    assert under is not None and under.result.value == "fail"


def test_no_edge_rim_hole_over_the_opening_it_spans_as_a_header(catlin_model_ro) -> None:
    """TJ-8000 p.4: FS-M-EAST's south rim spans D-B-SUNKEN's 63 5/16" RO as a header."""
    from typehaus.checks.mep.routing_members import _RIM_HEADER_RULE, _rim_load_finding
    from typehaus.resolve.rim_loads import rim_header_spans

    floor = _floor(catlin_model_ro, "FS-M-EAST")
    rim = next(m for m in floor.members if m.child_key.startswith("edge-rim-"))
    (span,) = rim_header_spans(catlin_model_ro, floor, rim)
    assert (span.lo_m / M_PER_IN, span.hi_m / M_PER_IN) == pytest.approx((224.344, 287.656),
                                                                          abs=1e-3)
    hole = 0.922 * M_PER_IN
    assert _rim_load_finding("conduit", "T", floor, rim.child_key, 250 * M_PER_IN, hole,
                             [span], _RIM_HEADER_RULE).result.value == "fail"
    assert _rim_load_finding("conduit", "T", floor, rim.child_key, 221 * M_PER_IN, hole,
                             [span], _RIM_HEADER_RULE) is None


def test_corridors_delegates_rather_than_re_deriving(catlin_model_ro) -> None:
    """The routing side and the checks side must not be able to drift apart."""
    from typehaus.routing.corridors import crossing_window

    for floor in catlin_model_ro.floors:
        window = member_window(floor)
        expected = None if window is None else (window.z0_m, window.z1_m)
        assert crossing_window(catlin_model_ro, floor) == expected, floor.tag


def test_a_leg_along_the_bay_crosses_nothing(catlin_model_ro) -> None:
    floor = _floor(catlin_model_ro, "FS-S-WEST")
    # FS-S-WEST spans in x, so its member lines are at constant y: travel in x crosses none.
    assert leg_crossings(floor, (1.0, 5.0), (4.0, 5.0), 2.85, 2.85) == []


def test_a_crossing_is_dropped_when_the_run_is_below_the_floor(catlin_model_ro) -> None:
    """A run passing under the deck is ``mep.run_in_finished_volume``'s question, not this
    one — and without this gate two basement raceways read as bored through the joists they
    hang a foot below."""
    floor = _floor(catlin_model_ro, "FS-S-WEST")
    inside = leg_crossings(floor, (1.0, 5.0), (1.0, 9.0), 2.85, 2.85)
    assert inside, "a leg crossing in y should meet members"
    below = leg_crossings(floor, (1.0, 5.0), (1.0, 9.0), 0.5, 0.5)
    assert below == []


def test_an_open_web_trimmer_is_a_truss_line(catlin_model_ro) -> None:
    """FO-S-ERV-CHASE's edges on FS-S-WEST are truss lines, so a leg across one is graded
    in the web window, not as a bore through an engineered member."""
    floor = _floor(catlin_model_ro, "FS-S-WEST")
    trimmers = [m for m in floor.members if m.child_key.startswith("trimmer-FO-S-ERV-CHASE")]
    assert trimmers and all(is_member_line(m) for m in trimmers)
    lvl = next(m for f in catlin_model_ro.floors for m in f.members
               if m.category == "trimmer" and "LVL" in m.profile)
    assert not is_member_line(lvl)


def test_adjacent_rim_holes_keep_twice_the_larger_diameter_apart(catlin_model_ro) -> None:
    """TJ-8000 p.4: edges of adjacent round holes >= 2x the larger one's diameter, unless
    the pair is a closely grouped set whose envelope is itself a legal hole."""
    from typehaus.checks.mep.rim_hole_spacing import RimHole, rim_spacing_findings

    floor = _floor(catlin_model_ro, "FS-S-WEST")
    rim = next(m for m in floor.members if m.child_key.startswith("edge-rim-"))
    window = member_window(floor, rim)
    ends = tuple(sorted((rim.p0[0], rim.p1[0])))
    mid = sum(ends) / 2.0
    d = 3.0 * M_PER_IN

    def run(gap_in, dia=d):
        a = RimHole("conduit", "A", mid, dia, True, window.z0_m, window.z0_m + dia)
        b = RimHole("duct", "B", mid + dia + gap_in * M_PER_IN, dia, True,
                    window.z0_m, window.z0_m + dia)
        return rim_spacing_findings("c", floor, "edge-rim", [a, b], window, set(), ends)

    assert run(6.01) == []
    (bad,) = run(5.9)  # the pair spans 11.9", more than the 7.9" a single hole may
    assert bad.result.value == "fail" and "A" in bad.message and "B" in bad.message
    assert run(1.0, dia=1.0 * M_PER_IN) == []  # envelope 3": a permitted group

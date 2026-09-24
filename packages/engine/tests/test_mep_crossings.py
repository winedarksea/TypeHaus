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
    """FS-S-EAST is the same 11 7/8" depth in I-joists — a different rule, a wider window.

    And the PASS it produces is **qualified**: the flange is clear, and the hole's diameter
    and its allowable zone along the span still come off the fabricator's chart. The old
    hardcoded-chord fallback answered 8 7/8" here too, which is right for the truss floor
    next door and wrong for this one.
    """
    window = member_window(_floor(catlin_model_ro, "FS-S-EAST"))
    assert window is not None
    assert window.kind == "i_joist"
    assert window.height_m / M_PER_IN == pytest.approx(11.875 - 2 * 1.375)
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

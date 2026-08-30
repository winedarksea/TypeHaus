"""``checks/structural/_stud_grid.py`` — one answer about where the studs are.

Two checks now ask: ``structural.window_framing_module`` and ``structural.door_framing_module``.
A second derivation of any of this would eventually disagree with ``resolve/framing/solver.py``
and start reporting stations nobody frames, so these tests pin the helper *against the solver*
rather than against a table of expected numbers.
"""

from __future__ import annotations

import pytest

from typehaus.checks.structural._stud_grid import (
    MIN_EDGE_M,
    feasible_stations,
    nearest_station,
    structure_framing,
    wall_module,
)
from typehaus.model.enums import PartitionLayout

_IN_M = 0.0254


def _framing(model, wall):
    return structure_framing(model.plan.library.resolve_assembly(wall.assembly))


def test_a_staggered_wall_is_framed_on_half_its_authored_spacing(catlin_model):
    """**The bug this move fixes.** ``solver.py`` lays a STAGGERED partition out on
    ``spacing / 2``: the two rows interleave on a shared plate, so an opening's jamb pack
    clears an 8" rhythm on a 16" o.c. wall. ``window_module.py`` read ``framing.spacing``
    straight and got 16, and every module verdict on such a wall was against a grid with
    twice the pitch of the built one."""
    staggered = {}
    for wall in catlin_model.walls:
        framing = _framing(catlin_model, wall)
        if framing is not None and framing.layout is PartitionLayout.STAGGERED:
            staggered[wall.assembly] = (framing.spacing.inches if framing.spacing else 16.0,
                                        wall_module(framing, 16.0))
    assert staggered, "catlin has no staggered wall left to pin this against"
    for authored, framed in staggered.values():
        assert framed == pytest.approx(authored / 2.0)


def test_it_is_dormant_on_windows_and_live_on_doors(catlin_model):
    """Why it is fixed *before* the door check exists. No catlin window sits on a staggered
    wall, so the window check never saw the disagreement; four doors do."""
    on_staggered = {"window": [], "door": []}
    for opening in catlin_model.openings:
        wall = catlin_model.wall(opening.host_wall)
        if wall is None:
            continue
        framing = _framing(catlin_model, wall)
        if framing is not None and framing.layout is PartitionLayout.STAGGERED:
            on_staggered["door" if opening.is_door else "window"].append(opening.tag)
    assert on_staggered["window"] == []
    assert sorted(on_staggered["door"]) == ["D-B-BATH", "D-B-PLAY", "D-M-BATH1",
                                            "D-S-SUITEBATH"]


def test_a_plain_wall_keeps_its_authored_module(catlin_model):
    for wall in catlin_model.walls:
        framing = _framing(catlin_model, wall)
        if framing is None or framing.layout is PartitionLayout.STAGGERED:
            continue
        expected = framing.spacing.inches if framing.spacing is not None else 16.0
        assert wall_module(framing, 16.0) == pytest.approx(expected)


# --- feasible_stations ---------------------------------------------------------------------

def test_every_station_it_names_costs_the_minimum_studs():
    """The counting rule is the solver's, enumerated rather than solved in closed form — so
    a station this returns is one ``opening_stud_module`` also calls ideal."""
    from typehaus.resolve.framing.stud_module import opening_stud_module

    spacing, stud, phase = 16 * _IN_M, 1.5 * _IN_M, 0.0
    stations = feasible_stations(32 * _IN_M, 16 * 12 * _IN_M, spacing, stud, phase)
    assert stations
    for station in stations:
        module = opening_stud_module(station, 32 * _IN_M, spacing, stud, phase)
        assert module.interrupted == module.minimum_interrupted
        assert module.offset_from_ideal_m == pytest.approx(0.0, abs=1e-6)


def test_the_edge_distance_is_the_binding_constraint_a_survey_misses():
    """A 24" opening in a 28" staggered wall has **two** perfectly good module stations, 12"
    and 16", and both put a jamb hard against a node. ``integrity.opening_fits`` is an
    ERROR-severity check, so naming either would trade a soft advisory for a hard failure —
    exactly the trade a by-hand survey of "off the module" openings makes without noticing.

    So the answer is the empty list, and the empty list means something different: not "move
    it here" but "no move on this wall will do"."""
    module, stud = 8 * _IN_M, 1.5 * _IN_M  # a 16" o.c. STAGGERED partition's real rhythm
    width, wall = 24 * _IN_M, 28 * _IN_M
    assert feasible_stations(width, wall, module, stud, 0.0) == []
    # ...and it is the edge rule that empties it, not the module: both stations are on the
    # grid and both fit the wall in bare geometry.
    for station in (12 * _IN_M, 16 * _IN_M):
        assert abs(station % module) < 1e-9 or abs(station % module - module / 2) < 1e-9
        assert station - width / 2 >= 0.0 and station + width / 2 <= wall
        assert min(station - width / 2, wall - station - width / 2) < MIN_EDGE_M
    # A wall with room for the same opening still gets its stations.
    assert feasible_stations(width, 10 * 12 * _IN_M, module, stud, 0.0)


def test_an_empty_list_is_the_honest_answer_not_a_pass():
    """Empty means "no move of this opening on this wall will do" — the check's UNKNOWN
    branch, and a different instruction (move the node, change the layout origin, narrow the
    leaf) from the one a named station gives."""
    assert feasible_stations(1.0, 0.5, 16 * _IN_M, 1.5 * _IN_M, 0.0) == []
    assert nearest_station([], 0.4) is None


def test_the_phase_shifts_the_whole_grid():
    """``layout_origin="line"`` moves the grid off the wall's start node, and the stations
    have to move with it or the check reports positions the solver does not frame."""
    module = 16 * _IN_M
    unphased = feasible_stations(24 * _IN_M, 16 * 12 * _IN_M, module, 1.5 * _IN_M, 0.0)
    phased = feasible_stations(24 * _IN_M, 16 * 12 * _IN_M, module, 1.5 * _IN_M, 3 * _IN_M)
    assert unphased and phased
    # Congruence mod the module, not a one-for-one pairing: the edge rule trims whichever end
    # station the shift pushes past a node, so the two lists need not be the same length.
    # Every phased station, with the phase taken back off, lands on a stud line or a bay
    # centre of the unphased grid — which is the whole claim.
    for stations, phase in ((unphased, 0.0), (phased, 3 * _IN_M)):
        for station in stations:
            residue = (station - phase) % module
            assert (min(residue, module - residue) < 1e-6
                    or abs(residue - module / 2) < 1e-6), station


def test_nearest_station_is_the_one_to_move_to():
    stations = [1.0, 2.0, 3.5]
    assert nearest_station(stations, 2.3) == 2.0
    assert nearest_station(stations, 3.0) == 3.5

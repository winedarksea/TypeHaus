"""The three trade adapters, and the one that had never been executed.

``trades/duct.crossing_admissible`` imported ``_open_web_opening`` from
``routing.corridors``, where no such name has ever existed. Every call raised
``ImportError`` and nothing called it, so a module with a hand-worked oracle note behind it
(``mep_duct_routing_basis.md`` §1, §3) was dead code that looked alive. The first assertion
below is the one that would have caught it: it calls the function.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.routing.corridors import Corridor
from typehaus.routing.trades import conduit as conduit_trade
from typehaus.routing.trades import duct as duct_trade
from typehaus.routing.trades import pipe as pipe_trade

pytestmark = pytest.mark.slow


def _open_web_floor(model):
    """The first floor whose joists are an open web — `FS-S-WEST` on catlin, the floor the
    duct note's §3 works by hand. `model.floors[0]` is a solid-sawn deck and answers False
    for the right reason, which makes it useless as a positive case."""
    from typehaus.resolve.mep_crossings import member_window

    for floor in model.floors:
        window = member_window(floor)
        if window is not None and window.kind == "open_web":
            return floor
    raise AssertionError("no open-web floor in this model")


# --- duct ------------------------------------------------------------------------------

def test_crossing_admissible_runs_at_all(catlin_model_ro) -> None:
    """The regression that matters: this used to raise on every call.

    A small round duct fits an 8 7/8" open web and a large one does not, which is §1's
    reading — the round OPENING, not the chord-to-chord gap a pipe may use.
    """
    floor = _open_web_floor(catlin_model_ro)
    assert duct_trade.crossing_admissible(
        catlin_model_ro, floor, diameter_m=4 * M_PER_IN) is True
    assert duct_trade.crossing_admissible(
        catlin_model_ro, floor, diameter_m=12 * M_PER_IN) is False


def test_a_floor_whose_section_publishes_no_open_web_answers_false(catlin_model_ro) -> None:
    """Refusing to propose a crossing it cannot justify is the conservative direction.

    The caller then sees a route ROUND rather than a route THROUGH, which is right: a
    solid-sawn joist takes a bored hole under R502.8 and an I-joist takes one off a chart
    this engine does not hold, and neither is the web space this predicate is about.
    """
    floor = _open_web_floor(catlin_model_ro)
    bare = type(floor)(**{**floor.__dict__, "members": ()})
    assert duct_trade.crossing_admissible(catlin_model_ro, bare, diameter_m=0.1) is False


def test_the_radius_is_half_the_LARGER_plan_dimension() -> None:
    """A rectangular duct turning a corner sweeps its own diagonal and this package has no
    fitting model to say otherwise, so the inflation is the conservative one."""
    assert duct_trade.radius_m(width_m=0.30, depth_m=0.10) == pytest.approx(0.15)
    assert duct_trade.radius_m(diameter_m=0.20) == pytest.approx(0.10)


def test_a_bay_with_section_left_is_silent_and_a_full_one_discloses() -> None:
    corridor = Corridor(tag="FS-X:bay@1", kind="bay", axis="x", station=1.0,
                        z0_m=0.0, z1_m=0.3, clear_width_m=0.3, lo_m=0.0, hi_m=5.0)
    assert duct_trade.bay_occupancy_note(corridor, 0.05) is None
    note = duct_trade.bay_occupancy_note(corridor, 0.2)
    assert note is not None and "one centreline per channel" in note


# --- conduit ---------------------------------------------------------------------------

def test_a_flat_route_is_one_leg_and_discloses_nothing() -> None:
    legs = conduit_trade.legalize([(0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 2.0, 1.0)])
    assert len(legs) == 1
    assert legs[0].rise_to_m is None
    assert conduit_trade.disclosure(legs) is None


def test_two_changes_of_elevation_become_three_runs_and_say_so() -> None:
    """A ``ConduitRun`` rises only at its LAST vertex, so emitting the 3-D polyline anyway
    produces geometry nobody authored and no check catches — every individual run
    resolves fine."""
    legs = conduit_trade.legalize([(0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 0.0, 2.0),
                                   (2.0, 0.0, 2.0), (2.0, 0.0, 3.0), (3.0, 0.0, 3.0)])
    assert len(legs) == 3
    assert [leg.rise_to_m for leg in legs] == [2.0, 3.0, None]
    disclosed = conduit_trade.disclosure(legs)
    assert disclosed is not None and "3 runs" in disclosed


# --- pipe ------------------------------------------------------------------------------

def test_a_pipe_crosses_only_where_its_whole_OUTSIDE_fits_the_window() -> None:
    """§3 works it at 8 7/8" against an 11 7/8" truss: a 3" pipe fits, a 10" does not."""
    window = (0.0, 8.875 * M_PER_IN)
    assert pipe_trade.crossing_admissible(None, 3 * M_PER_IN, window) is True
    assert pipe_trade.crossing_admissible(None, 10 * M_PER_IN, window) is False
    assert pipe_trade.crossing_admissible(None, 3 * M_PER_IN, None) is False


def test_only_drain_falls() -> None:
    assert pipe_trade.falls("drain") is True
    assert pipe_trade.falls("water_cold") is False
    assert pipe_trade.falls("vent") is False

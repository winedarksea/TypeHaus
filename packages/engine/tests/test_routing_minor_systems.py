"""Condensate, radon and sump routes (houses/catlin/notes/mep_condensate_routing_basis.md).

Hand-worked oracle values from the note: PR-B-COND's y=108 leg falls 1.170" over 54" from
z -20.276" at x=216", so an indirect line landing at x=210" lands at -20.406" (§3).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.cli.route_cleanouts import place_cleanouts
from typehaus.cli.route_roots import _landing, sleeve_hold, sump_endpoints
from typehaus.quantities import M_PER_IN, inch
from typehaus.routing.campaign import order_targets
from typehaus.routing.gravity import (
    CONDENSATE_LADDER,
    CONDENSATE_SLOPE_FLOOR_IN_PER_FT,
    CONDENSATE_SLOPE_IN_PER_FT,
    graded_route,
    minimum_slope,
    shallow_penalty,
)


def _in(*values: float) -> list[float]:
    return [inch(v).meters for v in values]


def test_a_condensate_run_lands_where_it_was_authored_not_at_the_chains_end() -> None:
    parent = SimpleNamespace(path=[(inch(216).meters, inch(108).meters),
                                   (inch(162).meters, inch(108).meters)])
    run = SimpleNamespace(path=[(inch(210).meters, inch(12).meters),
                                (inch(210).meters, inch(108).meters)])
    x, y, z = _landing(run, parent, _in(-20.276, -21.446))
    assert (x, y) == pytest.approx((inch(210).meters, inch(108).meters))
    assert z == pytest.approx(inch(-20.406).meters, abs=inch(0.001).meters)


def test_condensate_is_a_quarter_inch_target_over_an_eighth_inch_code_floor() -> None:
    """Note §5: 8.000 ft owes 2.000" at 1/4, 1.500" at 3/16, 1.000" at 1/8 (IMC 307.2.1)."""
    assert minimum_slope(inch(0.75).meters) == CONDENSATE_SLOPE_IN_PER_FT == 0.25
    assert minimum_slope(inch(0.75).meters, sanitary=False) == 0.25
    assert CONDENSATE_SLOPE_FLOOR_IN_PER_FT == 0.125
    assert [8.0 * g for g in CONDENSATE_LADDER] == pytest.approx([2.0, 1.5, 1.0])
    # Two bends (48") per 1/16"/ft below the target; none at it.
    assert [shallow_penalty(g) for g in CONDENSATE_LADDER] == pytest.approx([0.0, 48.0, 96.0])


def _lane_world(*, s_extra: float = 0.0, required_in: float = 114.0):
    """§8's two lanes (cheap L under a truss web, dear S), S optionally dearer still."""
    from test_gravity_search import _truss, _world

    from typehaus.routing.gravity_search import GravityProblem, sloped_route

    graph, space = _world()
    for key in ((1, 2), (2, 1)):
        graph.weights[key] += s_extra
    problem = GravityProblem(ceiling_m=116.5 * M_PER_IN, grade_in_per_ft=0.25, diameter_m=0.0,
                             required_m={3: required_in * M_PER_IN})
    return graded_route(lambda p: sloped_route(graph, space, 0, {3}, p, constraints=_truss),
                        problem, CONDENSATE_LADDER)


def test_the_router_stays_at_a_quarter_when_a_shallower_grade_saves_little() -> None:
    # 3/16 frees the cheap lane (84 vs 96) but 12 in saved < the 48 in penalty.
    found = _lane_world()
    assert found.grade_in_per_ft == 0.25 and found.nodes == [0, 1, 2, 3]


def test_the_router_goes_shallower_only_when_it_clearly_pays() -> None:
    found = _lane_world(s_extra=100.0)  # S now 196: 84 + 48 at 3/16 wins, 1/8 would be 180
    assert found.grade_in_per_ft == 0.1875 and found.nodes == [0, 4, 5, 6, 7, 3]
    assert "saved" in found.grade_note


def test_the_router_takes_the_floor_when_the_target_refuses() -> None:
    # Tie at 115.5": S (6 ft) owes 1.50 / 1.125 / 0.75 in of fall from 116.5; only 1/8 fits.
    found = _lane_world(required_in=115.5)
    assert found.grade_in_per_ft == 0.125 and "target is refused" in found.grade_note


def test_no_cleanouts_on_a_run_that_is_not_sanitary() -> None:
    proposal = SimpleNamespace(echo={"sanitary": False})
    assert place_cleanouts(None, None, proposal) == ((), 0.0, [])


@pytest.mark.parametrize(("occupancy", "access", "price"), [
    ("garage", "floor", 36.0),         # unfinished floor: base only, beats a 36 + 48 panel
    ("bedroom", "wall", 36.0 + 48.0),  # finished floor: 36 + 72 loses to the wall station
])
def test_a_buried_cleanout_takes_the_cheaper_of_floor_and_wall(occupancy, access, price) -> None:
    from typehaus.cli.route_cleanouts import _cheapest, _price
    from typehaus.routing.cost import RouteCost

    room = SimpleNamespace(kind="room", occupancy=occupancy)
    space = SimpleNamespace(cost=RouteCost(), soft_at=lambda xy, z: [room])
    buried = (0.0, 0.0, -0.3)
    floor = (buried, None, (1.0, 0.0), None)
    wall = (buried, SimpleNamespace(kind="wall"), (1.0, 0.0), (0.0, 0.05, 0.3))
    assert _cheapest(space, [floor, wall], 0.0) is (floor if access == "floor" else wall)
    assert _price(space, access, buried, 0.0) == price


def test_radon_and_sump_have_trades_and_only_gas_goes_unassigned() -> None:
    runs = [SimpleNamespace(tag=f"PR-{system}", system=system, storey="basement",
                            diameter_m=0.05, z_m=[0.0])
            for system in ("radon", "sump_discharge", "refrigerant", "gas")]
    model = SimpleNamespace(pipe_runs=runs, ducts=[], conduits=[])
    trades = {t.tag: t.trade for t in order_targets(model)}
    assert trades == {"PR-radon": "vent", "PR-sump_discharge": "supply",
                      "PR-refrigerant": "supply", "PR-gas": ""}


def test_a_lineset_bends_at_gree_10_cm_and_pays_no_exterior_wall_freeze_charge() -> None:
    """Soft ACR bends on Gree's flat 10 cm radius (over 4 x the 3/4" OD), and cannot freeze."""
    from typehaus.routing.cost import RouteCost
    from typehaus.routing.trades.pipe import bend_radius_m

    assert bend_radius_m(inch(0.75).meters, "refrigerant", "copper_acr") == pytest.approx(0.1)
    assert RouteCost().for_run("pipe", "refrigerant").exterior_wall_per_ft == 0.0
    assert RouteCost().for_run("pipe", "water_cold").exterior_wall_per_ft > 0.0


def test_sump_discharge_roots_on_the_leaders_riser(catlin_model_ro) -> None:
    run = next(r for r in catlin_model_ro.pipe_runs if r.tag == "PR-B-SUMP-DISCH")
    problems: list[str] = []
    root, riser = sump_endpoints(catlin_model_ro, run, problems)
    assert riser == "TR-RF-LEADER-W-EXT-RISER" and not problems
    assert root[2] == pytest.approx(run.z_m[-1])  # the authored wye is on the column


def test_a_sump_line_nothing_names_refuses_with_the_fix(catlin_model_ro) -> None:
    stray = SimpleNamespace(tag="PR-NOBODY", z_m=[0.0])
    problems: list[str] = []
    assert sump_endpoints(catlin_model_ro, stray, problems) is None
    assert "discharge_line_ref" in problems[0] and "PR-NOBODY" in problems[0]


def test_the_sump_line_is_held_through_the_cast_sleeve_it_is_authored_through(
        catlin_model_ro) -> None:
    run = next(r for r in catlin_model_ro.pipe_runs if r.tag == "PR-B-SUMP-DISCH")
    vertex, tag, _ = sleeve_hold(catlin_model_ro, run)
    assert (vertex, tag) == (2, "SP-B-N4-SUMP")  # the tail starts past the wall


def test_an_endpoint_miss_becomes_a_structured_refusal(catlin_model_ro, monkeypatch) -> None:
    from typehaus.cli import route_propose
    from typehaus.routing.cost import RouteCost

    stray = SimpleNamespace(tag="PR-NOBODY", z_m=[0.0])
    monkeypatch.setattr(route_propose, "_endpoints", lambda model, target, mode, problems:
                        sump_endpoints(model, stray, problems))
    proposals, problems, _notices, refusals = route_propose._propose(
        catlin_model_ro, ["PR-NOBODY"], mode="run", slope=None, margin_ft=8, band=None,
        avoid=frozenset(), via=[], explain=False, cost=RouteCost())
    (refused,) = refusals
    assert not proposals and problems == [refused.render()]
    payload = refused.payload()
    assert payload["element"] == "PR-NOBODY" and "discharge_line_ref" in payload["fix"]
    assert "no sump pump names it" in payload["cause"] and payload["blockers"] == []


def test_a_supply_miss_names_the_run_standing_there_as_its_element(catlin_model_ro) -> None:
    from typehaus.cli.route_miss import MissLog
    from typehaus.cli.route_roots import _supply_trunk

    run = next(r for r in catlin_model_ro.pipe_runs if r.tag == "PR-M-CW-PLANT-STUB")
    log = MissLog()
    assert _supply_trunk(catlin_model_ro, run, log) is None
    miss = log.first
    assert miss is not None and miss.element and miss.element != run.tag
    assert miss.cause.endswith("above it") and miss.fix.startswith("The riser")
    assert log == [miss.render()]


def _condensate(*, grade: float, sanitary: bool = False):
    run = SimpleNamespace(tag="PR-T-COND", system="drain", sanitary=sanitary,
                          diameter_m=inch(0.75).meters, length_m=1.0,
                          path=[(0.0, 0.0), (8 * 0.3048, 0.0)],
                          z_m=[0.0, -8 * grade * M_PER_IN])
    return SimpleNamespace(model=SimpleNamespace(pipe_runs=[run]))


def test_condensate_below_an_eighth_fails_and_below_a_quarter_advises() -> None:
    """IMC 2018 307.2.1 is the FAIL line; 1/4" is the house target, so a PASS with a prefix."""
    from typehaus.checks.mep.plumbing_dwv import drain_slope
    from typehaus.findings import Result

    (fail,) = drain_slope(_condensate(grade=0.10))
    assert fail.result is Result.FAIL and "307.2.1" in fail.message
    (shallow,) = drain_slope(_condensate(grade=0.1875))
    assert shallow.result is Result.PASS and shallow.message.startswith("ADVISORY")
    (floor,) = drain_slope(_condensate(grade=0.125))
    assert floor.result is Result.PASS
    (target,) = drain_slope(_condensate(grade=0.25))
    assert target.result is Result.PASS and not target.message.startswith("ADVISORY")
    # A sanitary drain at 3/16 is still UPC 708.0's FAIL.
    (sanitary,) = drain_slope(_condensate(grade=0.1875, sanitary=True))
    assert sanitary.result is Result.FAIL and "708.0" in sanitary.message

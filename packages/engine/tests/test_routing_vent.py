"""Vents rise, ties land on the stack, and edges are blocked by what they touch.

§5 of ``houses/catlin/notes/vent_grade_basis.md`` is the oracle for the rising search; the
rest pins B1-B4 of the ERV/vent clearance plan (2026-09-23) on worlds small enough to check
by eye.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import Graph, Node
from typehaus.routing.obstacles import HardPrism
from typehaus.routing.search import shortest_route
from typehaus.routing.space import RoutingSpace


def _space(hard=()) -> RoutingSpace:
    return RoutingSpace(radius_m=0.0, clearance_m=0.0,
                        cost=RouteCost(bend_in=24.0, corridor_discount_per_ft=0.0),
                        hard=list(hard), soft=[], corridors=[],
                        bbox=(-5.0, -5.0, 5.0, 5.0), storeys=("main",))


# --- §5: a vent never falls ---------------------------------------------------------------

def _section() -> tuple[Graph, RoutingSpace]:
    """§5's world: x, z in {0, 24, 48}", the centre (24, 24) a duct, the top row a room."""
    step = 24.0 * M_PER_IN
    coords = [(x, z) for z in (0, 1, 2) for x in (0, 1, 2) if (x, z) != (1, 1)]
    nodes = [Node(index=k, x=x * step, y=0.0, z=z * step) for k, (x, z) in enumerate(coords)]
    graph = Graph(nodes=nodes)
    for a in nodes:
        for b in nodes:
            if b.index <= a.index:
                continue
            dx, dz = abs(b.x - a.x), abs(b.z - a.z)
            if abs(dx + dz - step) > 1e-9:
                continue
            axis = "x" if dx else "z"
            weight = 12.0 if axis == "z" else (60.0 if a.z == 2 * step else 24.0)
            for i, j in ((a.index, b.index), (b.index, a.index)):
                graph.edges.setdefault(i, {}).setdefault(axis, []).append(j)
                graph.weights[(i, j)] = weight
                graph.terms[(i, j)] = {"travel_in": weight}
    return graph, _space()


def test_unconstrained_the_vent_dips_under_the_duct() -> None:
    graph, space = _section()
    route = shortest_route(graph, space, start=3, goals={4, 7})
    assert route is not None
    assert route.nodes == [3, 0, 1, 2, 4]
    assert route.cost == pytest.approx(120.0)


def test_rising_it_goes_over_and_meets_the_stack_higher() -> None:
    graph, space = _section()
    route = shortest_route(graph, space, start=3, goals={4, 7}, rising=True)
    assert route is not None
    assert route.nodes == [3, 5, 6, 7]
    assert route.cost == pytest.approx(156.0)
    assert route.bends == 1


def test_rising_with_the_stack_offered_only_at_the_root_level_refuses() -> None:
    graph, space = _section()
    assert shortest_route(graph, space, start=3, goals={4}, rising=True) is None


# --- B4: edges are blocked by geometry, not by their midpoint ------------------------------

def test_an_oblique_prism_blocks_an_edge_whose_midpoint_is_clear() -> None:
    from shapely.geometry import LineString

    # A diagonal run's envelope clipping the east end of a level step from (0,0) to (2,0).
    oblique = LineString([(1.2, -0.6), (2.2, 0.4)]).buffer(0.05)  # crosses y=0 at x=1.8
    space = _space([HardPrism(tag="PR-DIAG", kind="run", footprint=oblique,
                              z0_m=-1.0, z1_m=1.0)])
    assert space.blocked((1.0, 0.0), 0.0) is None, "the midpoint is clear"
    assert space.edge_blocked((0.0, 0.0), (2.0, 0.0), 0.0, 0.0) == "PR-DIAG"


def test_a_riser_is_blocked_by_a_thin_prism_nowhere_near_its_midpoint() -> None:
    from shapely.geometry import box

    duct = HardPrism(tag="DU-LOW", kind="run", footprint=box(-0.5, -0.5, 0.5, 0.5),
                     z0_m=0.2, z1_m=0.4)
    space = _space([duct])
    assert space.blocked((0.0, 0.0), 1.5) is None, "the riser's midpoint is 1.5 m up"
    assert space.edge_blocked((0.0, 0.0), (0.0, 0.0), 0.0, 3.0) == "DU-LOW"
    # A riser that stands ON the prism's top is not inside it.
    assert space.edge_blocked((0.0, 0.0), (0.0, 0.0), 0.4, 3.0) is None


def test_a_terminal_step_is_pardoned_only_what_the_terminal_stands_in() -> None:
    from shapely.geometry import box

    radon = HardPrism(tag="VR-radon", kind="run", footprint=box(-0.1, -0.1, 0.1, 0.1),
                      z0_m=-1.0, z1_m=1.0)
    duct = HardPrism(tag="DU-X", kind="run", footprint=box(0.4, -0.1, 0.6, 0.1),
                     z0_m=-1.0, z1_m=1.0)
    space = _space([radon, duct])
    assert space.blocked_all((0.0, 0.0), 0.0) == {"VR-radon"}
    ignore = frozenset({"VR-radon"})
    assert space.edge_blocked((0.0, 0.0), (0.3, 0.0), 0.0, 0.0, ignore=ignore) is None
    assert space.edge_blocked((0.0, 0.0), (1.0, 0.0), 0.0, 0.0, ignore=ignore) == "DU-X"


# --- B1 / B3: what a proposal may land on and touch ----------------------------------------

@pytest.mark.slow
def test_a_catlin_vent_ties_into_the_VENT_riser_and_never_the_radon(catlin_model_ro) -> None:
    from typehaus.cli.route_roots import _vent_siblings
    from typehaus.resolve.mep_envelopes import vent_risers

    run = next(r for r in catlin_model_ro.pipe_runs if r.tag == "PR-B-SAUNA-VENT")
    root, touch, paths = _vent_siblings(catlin_model_ro, run, [])
    assert "VR-M-RADON-VENT-vent" in touch
    assert "VR-M-RADON-VENT-radon" not in touch
    station = next(p[0] for t, p, _z, _d in vent_risers(catlin_model_ro)
                   if t == "VR-M-RADON-VENT-vent")
    assert root[:2] == pytest.approx(station, abs=1e-6)
    assert any(len(point) == 3 for path in paths for point in path), "goal lines carry z"


def test_a_branch_vent_teed_into_its_parent_mid_leg_finds_the_parent(catlin_model_ro) -> None:
    """PR-M-WC-VENT ends ON PR-S-BATH1-VENT's first leg, nowhere near either end of it.
    ``mep.vent_reachability`` accepts that tie; the router has to be able to find it too."""
    from typehaus.cli.route_roots import _vent_siblings

    run = next(r for r in catlin_model_ro.pipe_runs if r.tag == "PR-M-WC-VENT")
    problems: list[str] = []
    found = _vent_siblings(catlin_model_ro, run, problems)
    assert found is not None, problems
    assert "PR-S-BATH1-VENT" in found[1]


@pytest.mark.slow
def test_a_duct_touches_only_ducts_its_system_can_join(catlin_model_ro, monkeypatch) -> None:
    """Distance alone made a duct "joined" to whatever it ended beside. Forced here so every
    pair reads as joined: what survives into ``touch`` is the system filter's work."""
    import typehaus.resolve.mep_soffit as soffit
    from typehaus.cli.route_support import _duct_endpoints
    from typehaus.resolve.mep_envelopes import run_systems, systems_join

    monkeypatch.setattr(soffit, "ducts_are_joined", lambda _m, _a, _b: True)
    duct = next(d for d in catlin_model_ro.ducts if d.tag == "DU-ERV-RISER-SUP")
    ends = _duct_endpoints(catlin_model_ro, duct, [])
    systems = run_systems(catlin_model_ro)
    others = ends.touch - {duct.tag}
    assert others, "the supply side has ducts it can join"
    assert all(systems_join(systems[duct.tag], systems[tag]) for tag in others)
    assert not any(systems[tag][1] in ("exhaust", "return") for tag in others)

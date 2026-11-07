"""An emptied goal set is a refusal, never a ``min()`` of nothing (drain basis §10).

When every tie on a stack is within a wye pitch of an inlet already on it,
``route_roots._spaced_goals`` returns the empty set. The searches take a heuristic that is a
minimum over goals, so they used to raise ``ValueError``; now they return None and the CLI
prints a structured refusal naming the fixture.
"""

from __future__ import annotations

import pathlib

from typer.testing import CliRunner

from typehaus.cli.app import app
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import Graph, Node
from typehaus.routing.gravity_search import GravityProblem, GravityRefusal, sloped_route
from typehaus.routing.search import shortest_route
from typehaus.routing.space import RoutingSpace

_CATLIN = pathlib.Path(__file__).resolve().parents[3] / "houses" / "catlin"


def _two_nodes() -> tuple[Graph, RoutingSpace]:
    nodes = [Node(index=0, x=0.0, y=0.0, z=0.0), Node(index=1, x=0.6, y=0.0, z=0.0)]
    space = RoutingSpace(radius_m=0.0, clearance_m=0.0, cost=RouteCost(), hard=[], soft=[],
                         corridors=[], bbox=(0.0, 0.0, 1.0, 1.0), storeys=("main",))
    return Graph(nodes=nodes), space


def test_the_searches_refuse_an_empty_goal_set() -> None:
    graph, space = _two_nodes()
    assert shortest_route(graph, space, 0, set()) is None
    problem = GravityProblem(ceiling_m=1.0, grade_in_per_ft=0.25, diameter_m=0.0,
                             required_m={})
    assert sloped_route(graph, space, 0, set(), problem, refusal=GravityRefusal()) is None


def test_a_fully_spaced_out_stack_exits_1_with_a_refusal_naming_the_fixture(
        monkeypatch) -> None:
    import typehaus.cli.route_roots as roots

    monkeypatch.setattr(roots, "_spaced_goals", lambda model, graph, goals, ends, report: set())
    result = CliRunner().invoke(app, ["route", str(_CATLIN), "--fixture",
                                      "FX-A-STUBATH-WC"])
    assert result.exit_code == 1
    assert not isinstance(result.exception, ValueError)
    out = " ".join(result.output.split())
    assert "FX-A-STUBATH-WC: all " in out and "spaced out" in out

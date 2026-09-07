"""Route *proposals* for MEP runs — a leaf package that never grades anything.

``model/mep.py`` says auto-routing is a declared non-goal, and that statement is amended
here rather than deleted: **auto-routing stays out of ``resolve``, and this package
proposes.** The distinction is the whole design.

A search result is not a fact about the building. A ``Finding`` whose verdict moves when a
cost weight moves is not a finding — it is an opinion with a citation stapled to it. So
nothing in ``resolve/`` or ``checks/`` may import ``typehaus.routing``, and this package
imports neither of them back: it reads ``model`` / ``resolve`` / ``quantities`` and stops.
``tests/test_routing_leaf.py`` walks the imports and fails on a violation.

What *is* a fact — "this drain hangs 8 inches into the gym", "this fixture is 48 inches
from every pipe in the house" — belongs in ``checks/``, and is what the router is then
aimed at. ``mep.run_in_finished_volume`` is the constraint; :mod:`typehaus.routing.cost`
is the same constraint with a price on it.

The formulation is the standard obstacle-avoiding rectilinear one from the pipe-routing
literature: an escape graph of candidate lines, weighted A* over ``(node, incoming axis)``
states, and a repeated shortest-path heuristic for the directed Steiner tree — which is
exactly the DWV branch→main topology. ``houses/catlin/notes/mep_drain_routing_basis.md``
is the hand-worked oracle, and its §4 *is* the graph spec.
"""

from typehaus.routing.cost import RouteCost
from typehaus.routing.space import RoutingSpace, build_space

__all__ = ["RouteCost", "RoutingSpace", "build_space"]

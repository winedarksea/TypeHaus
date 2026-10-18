"""MEP route proposals, separate from resolution and checks.

Only the CLI coordinates routing and grading. This leaf reads model/resolve/quantities;
upstream packages never import it (tests/test_package_leaves.py).

The escape graph, weighted A*, and directed Steiner heuristic are specified by
houses/catlin/notes/mep_drain_routing_basis.md §§4–5. Workflow: docs/routing.md."""

from typehaus.routing.cost import RouteCost
from typehaus.routing.space import RoutingSpace, build_space

__all__ = ["RouteCost", "RoutingSpace", "build_space"]

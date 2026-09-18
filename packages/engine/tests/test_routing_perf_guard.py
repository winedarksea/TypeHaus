"""The lattice size criterion Phase 7 of the routing roadmap is graded against.

**The criterion, stated before the optimisation and not after it.** A whole-storey campaign
over catlin's pipes and ducts has to be possible at all, which means every single target on
it has to build a lattice that fits inside ``MAX_LATTICE_NODES``. Before the per-level
lattice landed, ``DU-M-ERV-R-KITCH`` — one duct, from the ERV to the kitchen — nominated
``287 x 302 x 9 = 780,066`` nodes and the router refused outright; at ``--margin 2``, a
margin too tight to route in, it still wanted 204,792.

The cause was that the candidate lines were derived once for the whole z band and then laid
down on **every plane in it**, so a footing nine feet under the attic nominated turn points
at its corners *in the attic*. :func:`~typehaus.routing.graph.candidate_lines_at` derives
them per level instead, which is not a heuristic but a correction: an obstacle that a plane
does not cut through has no corner on that plane to turn at.

**This test grades node COUNT, not wall-clock**, and that is the point of it. A count is
exact, reproducible on any machine, unaffected by the six-way parallel suite around it, and
it is the quantity the cap is written in — so unlike a timing budget it can gate honestly.
Wall clock is reported by ``haus route --timing`` for whoever is optimising; it is not
asserted here, for every reason ``test_resolve_perf_guard``'s docstring gives.
"""

from __future__ import annotations

import pytest
from _helpers import CATLIN

from typehaus.routing.graph import candidate_levels, candidate_lines_at
from typehaus.routing.space import MAX_LATTICE_NODES, RoutingSpace


def _lattice_size(space: RoutingSpace, terminals, levels=None) -> int:
    zs = candidate_levels(space, terminals, levels)
    return sum(len(xs) * len(ys)
               for xs, ys in (candidate_lines_at(space, terminals, z) for z in zs))


def test_a_level_only_nominates_the_obstacles_it_actually_cuts_through() -> None:
    """The correction itself, on a space built by hand so the claim is not about catlin.

    Two prisms at two elevations, and two planes. Each plane sees one prism's four edges
    and not the other's — under the old whole-band derivation both planes saw all eight.
    """
    from shapely.geometry import box

    from typehaus.routing.cost import RouteCost
    from typehaus.routing.obstacles import HardPrism

    low = HardPrism(tag="LOW", footprint=box(1.0, 1.0, 2.0, 2.0), z0_m=0.0, z1_m=0.5,
                    kind="fixed")
    high = HardPrism(tag="HIGH", footprint=box(5.0, 5.0, 6.0, 6.0), z0_m=3.0, z1_m=3.5,
                     kind="fixed")
    space = RoutingSpace(
        radius_m=0.05, clearance_m=0.0, cost=RouteCost(), hard=[low, high], soft=[],
        corridors=[], bbox=(0.0, 0.0, 10.0, 10.0), storeys=("basement",))
    terminals = [(0.5, 0.5, 0.25), (9.5, 9.5, 3.25)]

    at_low = candidate_lines_at(space, terminals, 0.25)
    at_high = candidate_lines_at(space, terminals, 3.25)
    assert 2.0 in at_low[0] and 2.0 not in at_high[0], "the low prism reaches the high plane"
    assert 6.0 in at_high[0] and 6.0 not in at_low[0], "the high prism reaches the low plane"


@pytest.mark.slow
def test_every_catlin_duct_builds_a_lattice_that_fits() -> None:
    """The campaign criterion: no target on catlin may refuse for lattice size.

    A duct is the hard case — a pipe drain searches one level, a duct searches every level
    the house has — so passing on every duct is what says a whole-storey campaign can run.
    """
    from typehaus.cli.route_support import _endpoints, _load
    from typehaus.routing.space import RoutingSpaceTooLarge, build_space

    _directory, model = _load(CATLIN)
    oversized: list[tuple[str, int | str]] = []
    for duct in model.ducts:
        problems: list[str] = []
        ends = _endpoints(model, duct.tag, "run", problems)
        if ends is None:
            continue  # a target the endpoint derivation refuses is not a lattice question
        terminals = [ends.origin, ends.root]
        space = build_space(model, radius_m=ends.radius_m, terminals=terminals,
                            touch=ends.touch)
        try:
            size = _lattice_size(space, terminals)
        except RoutingSpaceTooLarge as exc:
            oversized.append((duct.tag, str(exc)))
            continue
        if size > MAX_LATTICE_NODES:
            oversized.append((duct.tag, size))
    assert not oversized, (
        "these targets would refuse for lattice size rather than for anything about the "
        f"building: {oversized[:5]}")

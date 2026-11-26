"""A drain tree starts each branch at its fixture's drain port and places UPC 707.4's
cleanouts across the whole tree (docs/routing.md)."""

from __future__ import annotations

from typehaus.cli.cmd_route_tree import _propose_tree
from typehaus.model.enums import Service
from typehaus.resolve.mep_sleeves import expected_port_point


def test_basement_tree_starts_at_the_port_and_places_its_cleanouts(catlin_model_ro):
    made, _problems, _notices, _refusals = _propose_tree(
        catlin_model_ro, "PR-B-USINK-DRAIN", slope=None, margin_ft=8.0, level=None,
        avoid=frozenset(), via=[], explain=False)
    (proposal, storey), = made
    datum = next(s.elevation.meters for s in catlin_model_ro.plan.storeys if s.tag == storey)
    port = expected_port_point(catlin_model_ro, "FX-B-UTIL-SINK", Service.DRAIN)
    assert abs(proposal.points[0][2] - (datum + port[2])) < 1e-3  # 1/16" grid
    # No basement tree turns >135 deg since the slab branches run straight west (2026-11-10,
    # 2026-11-25 bath replan), so only the upper terminal's cleanout is left to place.
    assert {c.reason for c in proposal.cleanouts} == {"upper terminal"}

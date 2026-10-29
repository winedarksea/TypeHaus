"""A conduit re-route keeps the authored pull boxes it still passes and adds what NEC needs."""

from __future__ import annotations

import math

from typehaus.resolve.conduit_pulls import MAX_BEND_DEG_BETWEEN_PULLS
from typehaus.resolve.sweep import path_turns
from typehaus.routing.proposal import RouteProposal
from typehaus.routing.trades.conduit import assign_pull_points

# A staircase: seven 90 degree turns, so one box-free section would carry 630 degrees.
PATH = [(0.0, 0.0, 2.0), (3.0, 0.0, 2.0), (3.0, 3.0, 2.0), (6.0, 3.0, 2.0),
        (6.0, 6.0, 2.0), (9.0, 6.0, 2.0), (9.0, 9.0, 2.0), (12.0, 9.0, 2.0),
        (12.0, 12.0, 2.0)]


def _section_bends(points, pulls):
    turns = {t.index: t.angle_deg for t in path_turns(points)}
    totals, acc = [], 0.0
    for i in range(1, len(points) - 1):
        if i in pulls:
            totals.append(acc)
            acc = 0.0
        else:
            acc += turns.get(i, 0.0)
    return [*totals, acc]


def test_keeps_drops_and_adds_to_stay_under_360():
    kept_on_vertex = (3.05, 3.0, 2.0)  # beside vertex 2
    mid_segment = (12.0, 10.5, 2.0)  # on the last run, 1.5 m from any vertex
    gone = (20.0, 20.0, 2.0)
    found = assign_pull_points(PATH, (kept_on_vertex, mid_segment, gone))

    assert found.kept == 2 and len(found.dropped) == 1 and found.dropped[0] == gone
    assert len(found.points) == len(PATH) + 1  # a vertex went in for the mid-segment box
    assert 2 in found.indices
    assert any(math.dist(found.points[i], mid_segment) < 0.01 for i in found.indices)
    assert found.added >= 1
    assert all(0 < i < len(found.points) - 1 for i in found.indices)
    assert max(_section_bends(found.points, set(found.indices))) <= MAX_BEND_DEG_BETWEEN_PULLS
    assert "kept 2 authored" in found.disclosure()


def test_proposal_prints_pull_points_with_one_tuple_comma():
    proposal = RouteProposal(tag="CD-X-PROPOSED", kind="conduit", points=PATH[:3],
                             diameter_m=0.019, system="power_120", pull_points=(1,))
    assert "pull_points=(1,))" in proposal.source()
    assert not proposal.fittings()[0].spec  # a field bend, filed as raceway

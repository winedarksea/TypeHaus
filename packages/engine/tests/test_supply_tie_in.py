"""``supply_tie_ins`` — which run feeds this branch, and the three ways none does.

The mirror of ``test_drain_tie_in``. A drain discharges at its LAST vertex into whatever
passes beneath; a supply branch is authored tie-first, so its FIRST vertex is the tee — and
a tee sits on a SEGMENT, which no endpoint-to-endpoint tolerance can find. That is why
``_vent_siblings`` matched no supply run in this house, ever.

**The rejections are the point**, the same way they are for a drain: a run with no parent
gets a record and a reason, never a silent ``continue``.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_queries import pipe_elevations_at, pipe_invert_at
from typehaus.resolve.mep_tie_ins import supply_tie_in_records, supply_tie_ins


def _records(model):
    return {rec.child: rec for rec in supply_tie_in_records(model.pipe_runs)}


def test_the_basement_branches_derive_their_trunk(catlin_model_ro) -> None:
    ties = supply_tie_ins(catlin_model_ro.pipe_runs)
    assert ties["PR-B-CW-BATH1"] == "PR-B-CW-TRUNK"
    assert ties["PR-B-HW-BATH1"] == "PR-B-HW-TRUNK"
    assert ties["PR-B-HW-BATH2"] == "PR-B-HW-TRUNK"
    assert ties["PR-B-CW-SUITE"] == "PR-B-CW-TRUNK"


def test_every_supply_run_gets_a_record_and_most_get_a_parent(catlin_model_ro) -> None:
    records = supply_tie_in_records(catlin_model_ro.pipe_runs)
    assert len(records) == 29
    assert sum(rec.accepted for rec in records) == 23
    # Every basement branch, which is what a campaign needs to re-lane supply at all.
    basement = [rec for rec in records if rec.child.startswith("PR-B-")
                and rec.child not in ("PR-B-CW-TRUNK", "PR-B-HW-TRUNK")]
    assert all(rec.accepted for rec in basement), \
        [rec.child for rec in basement if not rec.accepted]


def test_a_cross_system_source_is_named_as_one(catlin_model_ro) -> None:
    """PR-B-HW-TRUNK leaves EQ-B-WH. PR-B-CW-WH ends at the same point and the same height,
    and a cold run is not a hot run's parent — so the honest answer is "not a run", not a
    silently wrong tie and not the nearest hot pipe 52" up."""
    rec = _records(catlin_model_ro)["PR-B-HW-TRUNK"]
    assert rec.parent is None and not rec.accepted
    assert rec.reason == "cross_system"
    assert rec.nearest == "PR-B-CW-WH"


def test_a_run_with_no_candidate_at_all_says_so(catlin_model_ro) -> None:
    """The service lateral and the trunk it feeds both leave the service entry, and the
    street main is not a run in this model."""
    records = _records(catlin_model_ro)
    for tag in ("PR-G-HYDRANT-CW", "PR-B-CW-TRUNK", "PR-M-CW-PORCH-HYD"):
        assert records[tag].reason == "no_candidate", tag
        assert records[tag].parent is None


def test_a_candidate_at_the_wrong_elevation_is_refused_with_the_number(
        catlin_model_ro) -> None:
    rec = _records(catlin_model_ro)["PR-M-CW-HYD-DIST"]
    assert rec.reason == "elevation"
    assert rec.nearest == "PR-B-CW-HYD"
    assert abs(rec.z_gap_m / M_PER_IN + 119.8) < 0.5


def test_the_derivation_is_acyclic(catlin_model_ro) -> None:
    """The guard is that two runs beginning at one point, neither carrying the other's
    load, are siblings. Without it PR-B-CW-TRUNK and PR-G-HYDRANT-CW name each other."""
    ties = supply_tie_ins(catlin_model_ro.pipe_runs)
    for child in ties:
        seen, cursor = set(), child
        while cursor in ties:
            assert cursor not in seen, f"cycle through {child}"
            seen.add(cursor)
            cursor = ties[cursor]


def test_a_manifold_at_the_trunks_first_vertex_is_not_a_sibling(catlin_model_ro) -> None:
    """Four hot branches tee off PR-B-HW-TRUNK's FIRST vertex at the water heater — a
    drain never has that. A bare same-origin sibling test leaves the whole hot tree
    parentless, which is why the guard also asks who carries whose load."""
    ties = supply_tie_ins(catlin_model_ro.pipe_runs)
    at_the_heater = ("PR-B-HW-BATH1", "PR-B-HW-WASH", "PR-B-HW-SBATH", "PR-B-HW-BATH")
    assert all(ties.get(tag) == "PR-B-HW-TRUNK" for tag in at_the_heater), \
        {tag: ties.get(tag) for tag in at_the_heater}


def test_the_nearest_ancestor_wins_not_the_largest(catlin_model_ro) -> None:
    """PR-B-CW-HYD-RISER's two fixtures are carried by PR-B-CW-HYD and by PR-B-CW-TRUNK.
    The riser tees off the branch standing at its foot, not the trunk twenty feet away —
    so of several proper supersets the derivation takes the SMALLEST."""
    assert supply_tie_ins(catlin_model_ro.pipe_runs)["PR-B-CW-HYD-RISER"] == "PR-B-CW-HYD"


def test_pipe_invert_at_is_unchanged_by_the_split(catlin_model_ro) -> None:
    """``pipe_invert_at`` is the min of ``pipe_elevations_at`` with risers DROPPED, and it
    has to stay byte-identical: a drain's receiver is a sloping leg, never the foot of
    somebody's riser. Counting those made two ``mep.drain_tie_in`` FAILs and five
    ``mep.pipe_sizing`` ones appear out of nowhere."""
    runs = catlin_model_ro.pipe_runs
    for run in runs:
        if run.z_m is None or len(run.path) < 2:
            continue
        for point in (run.path[0], run.path[-1]):
            plain = pipe_elevations_at(run, point, risers=False)
            assert pipe_invert_at(run, point) == (min(plain) if plain else None)


def test_a_riser_is_visible_to_a_supply_caller_and_not_to_a_drain_one(
        catlin_model_ro) -> None:
    """A zero-length plan segment is how every vertical leg here is authored. PR-B-CW-WH
    ends at (5'-6", 24'-0") at the water heater's outlet AND passes it at the ceiling; a
    supply tee sees both, a drain's invert reading sees only the sloping leg."""
    run = next(r for r in catlin_model_ro.pipe_runs if r.tag == "PR-B-CW-WH")
    point = run.path[-1]
    assert len(pipe_elevations_at(run, point)) > len(
        pipe_elevations_at(run, point, risers=False))


def test_a_zero_length_segment_does_not_match_every_point(catlin_model_ro) -> None:
    """``on_pipe_segment`` is TRUE for any point against a zero-length segment — its cross
    product, its dot product and its length_sq are all zero, so the range test passes
    trivially. Routing a riser through it made every run carrying one a candidate for
    every point in the house, and the derivation quietly answered 28 of 29."""
    run = next(r for r in catlin_model_ro.pipe_runs if r.tag == "PR-B-CW-TRUNK")
    far = (run.path[0][0] + 5.0, run.path[0][1] + 5.0)
    assert pipe_elevations_at(run, far) == []

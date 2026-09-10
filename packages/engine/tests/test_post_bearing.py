"""``engineering/post_bearing.py`` against the hand-worked note.

The oracle is ``houses/catlin/notes/centre_pillar_bearing.md``, worked by hand in a separate
pass before the calculation was encoded — the discipline every calc in ``engineering/`` is
held to (see ``typehaus/engineering/__init__``). A calculation that only agrees with itself
is not verified.

Three of these assertions are doing unusual work, and each pins one of the three ways this
joint was got wrong before the calc existed:

* :func:`test_the_reaction_is_taken_by_statics_not_split_evenly` — a 20" cantilever levers
  load OFF the far support. An even split is 9% light at the rear pillar.
* :func:`test_wet_service_is_applied_and_no_duration_factor_is` — 425 psi is the DRY value
  and the house's own comments graded this joint against it, while the glulam bearing on the
  top of the same post has been graded wet since the day it was computed.
* :func:`test_the_bearing_length_is_the_geometry_not_the_beam_width` — a joist that CROSSES
  a beam bears on all of it and one that ENDS on its axis bears on half, so the beam's own
  width is the right answer at one and twice the right answer at the other.

That last one runs on a **synthetic** deck, and deliberately. It used to read catlin's porch,
which carried one of each case: the joists crossed the back beam and stopped on the front
one. On 2026-09-03 ``FS-SG-PORCH``'s ``JoistSpec`` gained a 2-3/4" ``cantilever_start`` so
the joists cross BOTH beams — the right framing, and it takes ``PT-SG-BF2`` from d/c 0.76 to
0.35 — which left the END branch of ``_beam_bearing_in`` and ``_post_on_field_in`` with no
subject in this house. Deleting the assertions would have deleted the coverage with the
subject, so the old porch geometry lives on below as a fixture instead.
"""

from __future__ import annotations

import pytest

# §2, §3 and §5 of the note.
_ORACLE = {
    "PT-SG-BR2": {
        "reaction_lb": 2647.0,
        "ply_width_in": 4.50,
        # 5-1/2" of post, wholly inside the joist field.
        "post_bearing_in": 5.50,
        # The joists CROSS the 4-1/2" back beam.
        "beam_bearing_in": 4.50,
        "beam_tag": "BM-SG-BKW",
        "top_psi": 106.9, "top_capacity_psi": 304.2, "top_dc": 0.352,
        "beam_psi": 130.7, "beam_capacity_psi": 308.5, "beam_dc": 0.424,
    },
    "PT-SG-BF2": {
        "reaction_lb": 2187.0,
        "ply_width_in": 4.50,
        # 5-1/2" of post, wholly inside the joist field — the joists CROSS the front beam
        # and run 2-3/4" past its far face, so there is joist under all of the post.
        "post_bearing_in": 5.50,
        # And they therefore take all 4-1/2" of the front beam, not the 2-1/4" they took
        # while they stopped on its axis.
        "beam_bearing_in": 4.50,
        "beam_tag": "BM-SG-FRW",
        "top_psi": 88.3, "top_capacity_psi": 304.2, "top_dc": 0.290,
        "beam_psi": 108.0, "beam_capacity_psi": 308.5, "beam_dc": 0.350,
    },
}
_PILLARS = tuple(_ORACLE)

#: §2: `deck_beam/BM-SG-BLC`'s own line load, restated here because this module's whole claim
#: is that the post's demand and the beam's are the same number seen from two ends.
_BLC_LOAD_PLF = 500.0
_BLC_LENGTH_FT = 9.667


@pytest.fixture(scope="module")
def records(catlin_plan):
    from typehaus.engineering.post_bearing import compute
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    return {record.key: record for record in compute(ctx)}


def _quantity(record, name):
    return next(q.value for q in record.inputs if q.name == name)


def _state(record, fragment):
    return next(s for s in record.limit_states if fragment in s.name)


def test_only_the_two_centre_pillars_are_in_scope(records) -> None:
    """The population, and the seam it shares with ``pier_basis``.

    ``pier_basis.cast_piers`` grades a post on a footing, a pad or a foundation wall and says
    at its own scope that "a post on a floor or on a WOOD post is somebody else's rule". This
    module is that somebody else, and the two must not both claim one post: a second record on
    the same element would put two authorities on one joint and two ratios on one drawing.
    """
    assert sorted(records) == sorted(_PILLARS)


@pytest.mark.parametrize("tag", _PILLARS)
def test_the_record_reproduces_the_note(records, tag) -> None:
    """Every term of §3 and §5, against the hand working."""
    record = records[tag]
    oracle = _ORACLE[tag]
    from typehaus.engineering.item import Status

    assert record.status is Status.OK, record.missing
    assert _quantity(record, "reaction") == pytest.approx(oracle["reaction_lb"], abs=1.0)
    assert _quantity(record, "joist_stock_width") == pytest.approx(oracle["ply_width_in"])
    assert _quantity(record, "beam_bearing_length") == pytest.approx(
        oracle["beam_bearing_in"])

    top = _state(record, "on the joist top")
    assert top.demand == pytest.approx(oracle["top_psi"], rel=0.002)
    assert top.capacity == pytest.approx(oracle["top_capacity_psi"], rel=0.002)
    assert top.ratio == pytest.approx(oracle["top_dc"], abs=0.002)

    beam = _state(record, "where the joists land on")
    assert oracle["beam_tag"] in beam.name
    assert beam.demand == pytest.approx(oracle["beam_psi"], rel=0.002)
    assert beam.capacity == pytest.approx(oracle["beam_capacity_psi"], rel=0.002)
    assert beam.ratio == pytest.approx(oracle["beam_dc"], abs=0.002)


def test_the_reaction_is_taken_by_statics_not_split_evenly(records) -> None:
    """§2 — the one term an even split would get wrong, and by how much.

    ``BM-SG-BLC`` overhangs 20" north of PT-SG-BR2 and 12" south of PT-SG-BF2. A cantilever
    does not merely add its own load to the support beside it; it levers load OFF the far one.
    The two reactions still sum to the beam's whole load, which is the check that the statics
    are statics and not a fudge.
    """
    total = _BLC_LOAD_PLF * _BLC_LENGTH_FT
    reactions = {tag: _quantity(records[tag], "reaction") for tag in _PILLARS}
    assert sum(reactions.values()) == pytest.approx(total, abs=2.0)
    even = total / 2.0
    assert reactions["PT-SG-BR2"] > even * 1.08, "the north overhang must load BR2 up"
    assert reactions["PT-SG-BF2"] < even * 0.92, "and unload BF2 by the same amount"


@pytest.mark.parametrize("tag", _PILLARS)
def test_wet_service_is_applied_and_no_duration_factor_is(records, tag) -> None:
    """§4 — the two adjustments a hand check of this joint gets wrong.

    ``C_M`` 0.67 (NDS Table 4.3.1) takes SPF's Fc-perp from 425 psi to 285. The house's own
    comments graded this joint at 425 while ``glulam_beam.py`` applied wet service to the
    glulam bearing on the top of the same post — one joint, two answers.

    And NO ``C_D``: §3.10.2 takes no load duration factor on Fc-perp, because it is a
    deformation limit rather than a strength one. The only thing above 285 psi in any capacity
    here is ``C_b``, and it is capped at (6 + 0.375)/6 = 1.0625 by §3.10.4's own 6" limit.
    """
    from typehaus.engineering.post_bearing import (
        SAWN_FC_PERP_PSI,
        WET_FC_PERP,
        _bearing_area_factor,
    )

    base = SAWN_FC_PERP_PSI * WET_FC_PERP
    assert base == pytest.approx(284.75, abs=0.01)
    record = records[tag]
    assert _quantity(record, "Fc_perp_adjusted") == pytest.approx(base, abs=0.01)
    ceiling = base * _bearing_area_factor(3.0, at_member_end=False)
    for state in record.limit_states:
        assert base <= state.capacity <= ceiling + 1e-9, state.name
        assert "NO C_D" in state.citation or "C_b" in state.citation


def _end_bearing_deck():
    """catlin's porch as it was framed before 2026-09-03, as a fixture.

    Joists running in y from 17" north of the back beam at y = 0 — the porch's real
    ``cantilever_end`` — south to the FRONT beam's axis at y = -9.5 ft, where they stop.
    A 6x6 stands on each beam. Both beams 4-1/2" wide. That is one of each case on one
    deck — the back beam CROSSED, the front beam LANDED ON — which is what
    ``_beam_bearing_in`` and ``_post_on_field_in`` need a subject for and what the real
    porch no longer provides.
    """
    from types import SimpleNamespace

    from typehaus.model.elements import Node
    from typehaus.model.structure import Beam
    from typehaus.quantities import Point2D, ft, inch, m

    front_y, back_y = ft(-9.5).meters, 0.0

    def at(x_m, y_m):
        return Point2D(m(x_m), m(y_m))

    nodes = [
        Node(uid="TSTND01AAA", tag="N-BK-W", position=at(0.0, back_y)),
        Node(uid="TSTND02AAA", tag="N-BK-E", position=at(6.0, back_y)),
        Node(uid="TSTND03AAA", tag="N-FR-W", position=at(0.0, front_y)),
        Node(uid="TSTND04AAA", tag="N-FR-E", position=at(6.0, front_y)),
    ]
    beams = [
        Beam(uid="TSTBM01AAA", tag="BM-BACK", start_node="N-BK-W", end_node="N-BK-E",
             size="4.5x11.875"),
        Beam(uid="TSTBM02AAA", tag="BM-FRONT", start_node="N-FR-W", end_node="N-FR-E",
             size="4.5x11.875"),
    ]
    by_tag = {e.tag: e for e in (*nodes, *beams)}
    # One joist line is enough: the field extent is all either function reads. It runs 17"
    # PAST the back beam to the deck's north edge — catlin's real ``cantilever_end`` — and
    # stops dead on the front beam's axis, which is the pair of cases being pinned.
    joist = SimpleNamespace(category="joist", p0=(3.0, front_y),
                            p1=(3.0, back_y + inch(17).meters))
    floor = SimpleNamespace(tag="FS-TEST", members=[joist])
    deck = SimpleNamespace(
        tag="FS-TEST",
        joists=SimpleNamespace(direction="y", bearing_refs=("BM-BACK", "BM-FRONT")))
    ctx = SimpleNamespace(
        plan=SimpleNamespace(by_tag=by_tag.get, all_elements=lambda: list(by_tag.values())),
        model=SimpleNamespace(floors=[floor]))
    at_front = SimpleNamespace(size="6x6", position=SimpleNamespace(xy_m=(3.0, front_y)))
    at_back = SimpleNamespace(size="6x6", position=SimpleNamespace(xy_m=(3.0, back_y)))
    return ctx, deck, at_front, at_back


def test_the_bearing_length_is_the_geometry_not_the_beam_width() -> None:
    """§3b — one deck carrying one of each case.

    Joists that run past the BACK beam cross all 4-1/2" of it. Joists that STOP on the
    FRONT beam's axis take 2-1/4" of the same 4-1/2". Reading ``Beam.size``'s width at both
    would credit the landed joint with twice the bearing it has, which is where the 2.36 d/c
    in the note's "before" table came from — and it is still where a hand check goes wrong,
    which is why this assertion outlived the geometry that prompted it.
    """
    from typehaus.engineering.post_bearing import _beam_bearing_in

    ctx, deck, at_front, at_back = _end_bearing_deck()
    crossed_in, crossed_tag, crossed_at_end = _beam_bearing_in(ctx, deck, at_back)
    landed_in, landed_tag, landed_at_end = _beam_bearing_in(ctx, deck, at_front)
    assert (crossed_tag, landed_tag) == ("BM-BACK", "BM-FRONT")
    assert crossed_in == pytest.approx(4.5)
    assert landed_in == pytest.approx(crossed_in / 2.0)
    # And the END bearing earns no C_b, because there is no wood past it to earn one.
    assert landed_at_end and not crossed_at_end
    # catlin itself now has neither: both porch beams are crossed since the joists gained
    # their 2-3/4" ``cantilever_start``. That is what makes this fixture necessary.
    assert all(entry["beam_bearing_in"] == 4.5 for entry in _ORACLE.values())


def test_a_post_at_the_deck_edge_is_credited_only_with_what_is_under_it() -> None:
    """§3a — a post standing on the line where the joists stop is half over air.

    2-3/4" of its 5-1/2" footprint has no joist beneath it. Crediting the whole section
    would halve the reported stress at exactly the post this rule was written to catch an
    error at, and it would also hand the bearing a ``C_b`` it has not earned.

    catlin no longer poses the question — ``PT-SG-BF2`` sits on the same axis it always did,
    but the joists now run 2-3/4" PAST it, so the post is wholly over wood. The oracle below
    asserts that, and the fixture keeps the branch tested.
    """
    from typehaus.engineering.post_bearing import _post_on_field_in

    ctx, deck, at_front, at_back = _end_bearing_deck()
    edge_in, edge_at_end = _post_on_field_in(ctx, deck, at_front)
    interior_in, interior_at_end = _post_on_field_in(ctx, deck, at_back)
    assert edge_in == pytest.approx(2.75)
    assert edge_at_end
    # The post on the CROSSED beam has 17" of joist running on past it, so it keeps its
    # whole 5-1/2" and is not at a field end. Same post, same section, twice the bearing.
    assert interior_in == pytest.approx(5.50) and not interior_at_end
    # And in the house, both pillars are now credited with the whole 5-1/2".
    assert all(entry["post_bearing_in"] == 5.50 for entry in _ORACLE.values())


@pytest.mark.parametrize("tag", _PILLARS)
def test_the_check_delegates_and_the_item_reaches_the_permit_set(catlin_plan, tag) -> None:
    """The record has to arrive somewhere a reader will see it.

    ``structural.deck_post_bearing`` turns it into a Finding, and the mn-2020 profile carries
    a permit item for it — an engineered result on no checklist is work a plan reviewer cannot
    see, which is what ``test_permit_coverage.py`` exists to stop.
    """
    from pathlib import Path

    from typehaus.checks import run
    from typehaus.engineering import item_id
    from typehaus.findings import Authority, Result

    report = run(catlin_plan, Path(catlin_plan.source_root), profile="mn-2020")
    found = [f for f in report.findings
             if f.check_id == "structural.deck_post_bearing" and tag in f.element_tags]
    assert len(found) == 1, found
    assert found[0].authority is Authority.ENGINEERED
    assert found[0].result is Result.PASS, found[0].message
    assert item_id("post_bearing", tag) in report.engineering

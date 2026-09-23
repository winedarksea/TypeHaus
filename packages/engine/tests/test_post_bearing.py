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

Since 2026-09-22 the whole joint is a fixture: the court went to 17'-0" and the pillars,
the centre glulam and the porch beams it stood on are gone from catlin.
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


def _deck_borne_pillars():
    """The joint the note was worked for, rebuilt from the note's own §1-§3 inputs.

    ** STANDALONE SINCE 2026-09-22. ** This used to put the two pillars back on catlin's
    live porch framing, reading ``PT-SG-COL``/``FCOL``'s positions and the porch beams off the
    house. The 17'-0" court retired all of it — both columns, both pillars, ``BM-SG-BLC`` and
    the porch beam pairs — so there is no house left to revert, and the arrangement is built
    here from ``notes/centre_pillar_bearing.md`` alone:

    * ``BM-SG-BLC``, 3-1/2" x 11-7/8", node to node y = -0'-10" .. -10'-6" at x = 18'-0",
      bearing on ``PT-SG-BR2`` (y = -2'-6") and ``PT-SG-BF2`` (y = -9'-6"), both 5-1/2"
      square (§1, §2);
    * ``FS-SG-DECK``, a deck on that beam with a 10'-0" joist span and 9" cantilevers — the
      500 plf strip §2 takes (two resolved bays of 10'-0" either side of x = 18');
    * ``FS-SG-PORCH``, 2x8 running N-S, the field from y = -116.75" (the 2-3/4"
      ``cantilever_start``) to 17" north of the back beam, with a 3-ply pack on x = 18'
      (§3a); back beam ``BM-SG-BKW`` at y = -2'-3" and front beam ``BM-SG-FRW`` at
      y = -9'-6", both 4-1/2" wide (§3b).

    Model classes are ``model_construct``-ed so ``post_bearing``'s isinstance gates see real
    types; the resolved floors are namespaces carrying only what the module reads.
    """
    from types import SimpleNamespace

    from typehaus.model.elements import Node
    from typehaus.model.floors import FloorSystem, JoistSpec
    from typehaus.model.structure import Beam, Post
    from typehaus.quantities import ft, inch, pt

    x = 18.0

    def node(tag, x_ft, y_ft):
        return Node(uid=f"TST{tag[-6:].replace('-', '')}AAA"[:10], tag=tag,
                    position=pt(ft(x_ft), ft(y_ft)))

    nodes = [node("N-SGB-NC", x, -10.0 / 12.0), node("N-SGB-SC", x, -10.5),
             node("N-BKW-W", 9.0, -2.25), node("N-BKW-E", x, -2.25),
             node("N-FRW-W", 9.0, -9.5), node("N-FRW-E", x, -9.5)]
    pillars = [Post.model_construct(tag=tag, size="5.5x5.5", position=pt(ft(x), ft(y)),
                                    supported_by="FS-SG-PORCH", within_wall=False)
               for tag, y in (("PT-SG-BR2", -2.5), ("PT-SG-BF2", -9.5))]
    beams = [
        Beam.model_construct(tag="BM-SG-BLC", start_node="N-SGB-NC", end_node="N-SGB-SC",
                             size="3.5x11.875", bearing_refs=("PT-SG-BR2", "PT-SG-BF2")),
        Beam.model_construct(tag="BM-SG-BKW", start_node="N-BKW-W", end_node="N-BKW-E",
                             size="4.5x7.25", bearing_refs=()),
        Beam.model_construct(tag="BM-SG-FRW", start_node="N-FRW-W", end_node="N-FRW-E",
                             size="4.5x7.25", bearing_refs=()),
    ]
    balcony = FloorSystem.model_construct(
        tag="FS-SG-DECK", service="deck",
        joists=JoistSpec(member="2x10", direction="x", bearing_refs=("BM-SG-BLC",),
                         cantilever=inch(9.0)))
    porch = FloorSystem.model_construct(
        tag="FS-SG-PORCH", service="deck",
        joists=JoistSpec(member="2x8", direction="y",
                         bearing_refs=("BM-SG-BKW", "BM-SG-FRW"),
                         cantilever_start=inch(2.75), cantilever_end=inch(17.0)))
    by_tag = {e.tag: e for e in (*nodes, *pillars, *beams, balcony, porch)}

    m = 0.3048
    south, north = -116.75 / 12.0 * m, (-2.25 + 17.0 / 12.0) * m

    def member(category, p0, p1, profile="2x8"):
        return SimpleNamespace(category=category, p0=p0, p1=p1, profile=profile,
                               length_m=abs(p1[0] - p0[0]) + abs(p1[1] - p0[1]))

    # The pack: the authored joist on x = 18' and a sister each side, 1-1/2" apart, so the
    # 5-1/2" pillar sits on 4-1/2" of stock (§3a).
    pack = [member("joist" if dx == 0.0 else "sister_joist", ((x * 12 + dx) / 12 * m, south),
                   ((x * 12 + dx) / 12 * m, north)) for dx in (-1.5, 0.0, 1.5)]
    bays = [member("joist", (x0 * m, -5.0 * m), (x1 * m, -5.0 * m), "2x10")
            for x0, x1 in ((7.25, x), (x, 28.75))]
    model = SimpleNamespace(floors=[SimpleNamespace(tag="FS-SG-PORCH", members=pack),
                                    SimpleNamespace(tag="FS-SG-DECK", members=bays)])
    plan = SimpleNamespace(by_tag=by_tag.get, all_elements=lambda: list(by_tag.values()))
    return SimpleNamespace(plan=plan, model=model, soil_class="GM")


@pytest.fixture(scope="module")
def records():
    from typehaus.engineering.post_bearing import compute

    return {record.key: record for record in compute(_deck_borne_pillars())}


def test_the_house_itself_no_longer_poses_this_question(catlin_plan) -> None:
    """The retirement, pinned — and pinned HERE rather than only in the register's goldens.

    On 2026-09-14 both centre pillars came off ``FS-SG-PORCH`` and onto ``PT-SG-FCOL`` /
    ``PT-SG-COL``, on ABU66SS bases, with the four porch beams hung off their faces on
    HU212-3 hangers rather than seated beside them on the pour. ``_posts_on_framing``
    enumerates a ``Post`` whose ``supported_by`` names a ``FloorSystem`` and nothing else, so
    the population is empty and the two records have left the register.

    On 2026-09-22 the pillars retired outright with the centre support line. Everything
    below this test runs on :func:`_deck_borne_pillars`, which rebuilds the arrangement from
    the note so it can still be reproduced. This test is what says the house
    does not stand that way any more — without it, a reader could take the whole file for a
    description of the current building.
    """
    from typehaus.engineering.post_bearing import _posts_on_framing, compute
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    assert _posts_on_framing(ctx) == []
    assert compute(ctx) == []


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


def test_the_check_reports_an_earned_na_and_registers_nothing(catlin_plan) -> None:
    """What ``structural.deck_post_bearing`` says now, and that it is a verdict not a silence.

    The check used to turn each record into an ENGINEERED PASS naming
    ``post_bearing/PT-SG-B*2``, and the mn-2020 profile carries a permit item for it — an
    engineered result on no checklist is work a plan reviewer cannot see, which is what
    ``test_permit_coverage.py`` exists to stop.

    With no post in the house standing on framing there is no record to delegate, and the
    honest answer is NOT_APPLICABLE **earned from positive evidence of absence** rather than
    an empty finding list: "no post in this plan stands on a floor system (37 post(s) resolve,
    all of them on a pad, a footing, a wall, or inside one)". A rule that returned ``[]``
    would be indistinguishable from a rule that never ran (→ decision: N/A must be earned).

    The permit item and the registered kind both STAY. A house that stands a post on a deck
    tomorrow — this one or another — gets the record, the item and the checklist line back
    with no code change, which is why ``notes/centre_pillar_bearing.md`` is kept un-archived
    and why the fixture above can still reproduce it.
    """
    from pathlib import Path

    from typehaus.checks import run
    from typehaus.findings import Result

    report = run(catlin_plan, Path(catlin_plan.source_root), profile="mn-2020")
    found = [f for f in report.findings if f.check_id == "structural.deck_post_bearing"]
    assert len(found) == 1, found
    assert found[0].result is Result.NOT_APPLICABLE, found[0].message
    assert "no post in this plan stands on a floor system" in found[0].message
    assert not [key for key in report.engineering if key.startswith("post_bearing/")]

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
* :func:`test_the_bearing_length_is_the_geometry_not_the_beam_width` — the porch's joists
  CROSS one beam and END on the other, so the beam's own width is the right answer at one
  and twice the right answer at the other.
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
        # Half the post is over the deck edge: the porch outline ends on the front beam axis.
        "post_bearing_in": 2.75,
        # The joists END on the 4-1/2" front beam with 2-1/4" of bearing.
        "beam_bearing_in": 2.25,
        "beam_tag": "BM-SG-FRW",
        "top_psi": 176.7, "top_capacity_psi": 284.8, "top_dc": 0.621,
        "beam_psi": 216.0, "beam_capacity_psi": 284.8, "beam_dc": 0.758,
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


def test_the_bearing_length_is_the_geometry_not_the_beam_width(records) -> None:
    """§3b — the porch carries one of each case, on the same deck.

    The joists run past the BACK beam to the deck's north edge, so they cross all 4-1/2" of
    it. They STOP on the FRONT beam's axis, so they take 2-1/4" of the same 4-1/2". Reading
    ``Beam.size``'s width at both would credit the front joint with twice the bearing it has,
    which is where the 2.36 d/c in the note's "before" table came from.
    """
    crossed = _quantity(records["PT-SG-BR2"], "beam_bearing_length")
    landed = _quantity(records["PT-SG-BF2"], "beam_bearing_length")
    assert crossed == pytest.approx(4.5)
    assert landed == pytest.approx(crossed / 2.0)
    # And the END bearing earns no C_b, because there is no wood past it to earn one.
    assert "END bearing" in _state(records["PT-SG-BF2"], "where the joists land on").citation
    assert "END bearing" not in _state(records["PT-SG-BR2"],
                                       "where the joists land on").citation


def test_a_post_at_the_deck_edge_is_credited_only_with_what_is_under_it(records) -> None:
    """§3a — ``PT-SG-BF2`` is half over the porch's south edge.

    The porch outline ends on the front beam axis and the pillar stands on it, so 2-3/4" of
    its 5-1/2" footprint has no joist beneath it. Crediting the whole section would halve the
    reported stress at the one post this rule was written to find an error at.
    """
    assert _quantity(records["PT-SG-BR2"], "joist_plies") == 3
    top = _state(records["PT-SG-BF2"], "on the joist top")
    interior = _state(records["PT-SG-BR2"], "on the joist top")
    # Same 4-1/2" of stock and 83% of the load, and still 1.65x the stress.
    assert top.demand > interior.demand * 1.6
    assert "2.75" in top.citation


@pytest.mark.parametrize("tag", _PILLARS)
def test_the_check_delegates_and_the_item_reaches_the_permit_set(catlin_plan, tag) -> None:
    """The record has to arrive somewhere a reader will see it.

    ``structural.deck_post_bearing`` turns it into a Finding, and the mn-2024 profile carries
    a permit item for it — an engineered result on no checklist is work a plan reviewer cannot
    see, which is what ``test_permit_coverage.py`` exists to stop.
    """
    from pathlib import Path

    from typehaus.checks import run
    from typehaus.engineering import item_id
    from typehaus.findings import Authority, Result

    report = run(catlin_plan, Path(catlin_plan.source_root), profile="mn-2024")
    found = [f for f in report.findings
             if f.check_id == "structural.deck_post_bearing" and tag in f.element_tags]
    assert len(found) == 1, found
    assert found[0].authority is Authority.ENGINEERED
    assert found[0].result is Result.PASS, found[0].message
    assert item_id("post_bearing", tag) in report.engineering

"""``structural.deck_footing_size`` reads what a post actually bears on.

The check must follow more than one ``Post -> Post`` link and know about more than ``Pad``,
or eight of catlin's ten sunken-garden posts come out as *"post X does not bear on a
resolvable Pad"* — a sentence about the check's own reach, dressed up as a fact about the
model, and carrying an ENGINEERED handoff that asks a consultant to design footings for
posts that have none.

The model says exactly what every one of them bears on. Six of the eight are therefore not
IRC R507.3.1's condition at all, and the verdict is ``NOT_APPLICABLE`` **earned from positive
evidence** — the rule my `Result` docstring insists on: N/A means "the governed condition
does not exist in this building", never "the check ran out of road". Two are the condition
and stay engineered, because a 30"/36" belled pier has no row in R507.3's flat-pad table.
"""

from __future__ import annotations

import pytest

from typehaus.findings import Authority, Result

# post -> (verdict, the element the message must name as evidence)
_EXPECTED = {
    # Four balcony pillars land on the porch side walls, which have their own strip footings
    # graded by their own rules. Nothing here to size.
    "PT-SG-BR1": (Result.NOT_APPLICABLE, "W-SG-W1"),
    "PT-SG-BF1": (Result.NOT_APPLICABLE, "W-SG-W1"),
    "PT-SG-BR3": (Result.NOT_APPLICABLE, "W-SG-E1"),
    "PT-SG-BF3": (Result.NOT_APPLICABLE, "W-SG-E1"),
    # A post on a deck is not a post on the ground. BOTH centre pillars since 2026-09-03:
    # PT-SG-BF2 stood on PT-SG-FCOL's TOP until then, and came north onto the porch framing
    # when that column shrank to 12" — the exact mirror of BR2, 3" inside its beam line.
    # Either way, minting `spread_footing/PT-SG-BF2` would name a footing that does not
    # exist; what carries the load is graded on the column under the beam it lands in, and
    # `engineering/pier_basis._piers_below` is what hands it there.
    "PT-SG-BR2": (Result.NOT_APPLICABLE, "FS-SG-PORCH"),
    "PT-SG-BF2": (Result.NOT_APPLICABLE, "FS-SG-PORCH"),
    # These two DO bear on soil through their own belled piers. R507.3 has no row for a
    # 30"/36" bell, so they are real engineered items and must stay so.
    "PT-SG-COL": (Result.UNKNOWN, "FT-SG-COL"),
    "PT-SG-FCOL": (Result.UNKNOWN, "FT-SG-FCOL"),
}


@pytest.fixture(scope="module")
def findings(catlin_plan):
    from _helpers import check_context

    from typehaus.checks.structural.deck import deck_footing_size

    return deck_footing_size(check_context(plan=catlin_plan))


@pytest.mark.parametrize("post", sorted(_EXPECTED))
def test_each_post_is_graded_by_what_it_actually_bears_on(post, findings) -> None:
    want_result, want_evidence = _EXPECTED[post]
    # ``element_tags`` is ``(deck, post, evidence)``, so the SUBJECT is index 1. A post can
    # legitimately appear in a second finding as another post's evidence — a wall or a deck
    # is named by every pillar standing on it — and matching on mere membership would
    # collide there.
    mine = [f for f in findings if len(f.element_tags) > 1 and f.element_tags[1] == post]
    assert len(mine) == 1, [f.message for f in mine]
    finding = mine[0]
    assert finding.result is want_result, finding.message
    # The evidence has to be IN the message, not merely implied by it: an N/A that does not
    # say what it looked at is indistinguishable from an N/A that looked at nothing.
    assert want_evidence in finding.message, finding.message
    assert want_evidence in finding.element_tags, finding.element_tags
    assert "does not bear on a resolvable Pad" not in finding.message


def test_only_the_two_belled_piers_remain_engineered(findings) -> None:
    """The whole point of the change: eight handoffs become two.

    An ENGINEERED finding names an item a professional seal has to cover. Six of the eight
    named items nobody could ever design, because the footing they named does not exist.
    """
    engineered = {f.element_tags[1] for f in findings
                  if f.authority is Authority.ENGINEERED and len(f.element_tags) > 1
                  and f.element_tags[1].startswith("PT-")}
    assert engineered == {"PT-SG-COL", "PT-SG-FCOL"}
    items = {f.engineering_item for f in findings if f.engineering_item}
    assert items == {"spread_footing/PT-SG-COL", "spread_footing/PT-SG-FCOL"}


def test_no_post_is_reported_as_unsupported_when_the_model_says_otherwise(findings) -> None:
    """Nothing may fall through to the old sentence, and nothing may go silently missing.

    Scoped to ``PT-SG-*``: the breezeway's posts DO bear on real ``Pad``s (``PD-BW-1..4``)
    and go down the ordinary R507.3.1 area path, which this change did not touch and which
    is the branch that has to keep working.
    """
    assert not [f for f in findings if "does not bear on a resolvable Pad" in f.message]
    graded = {f.element_tags[1] for f in findings
              if len(f.element_tags) > 1 and f.element_tags[1].startswith("PT-SG-")}
    assert graded == set(_EXPECTED)
    # The untouched branch still runs: every breezeway pad is still graded on its area.
    pads = {f.element_tags[1] for f in findings
            if len(f.element_tags) > 1 and f.element_tags[1].startswith("PD-BW-")}
    assert pads == {"PD-BW-1", "PD-BW-2", "PD-BW-3", "PD-BW-4"}


def test_a_post_that_declares_no_bearing_is_unknown_not_na(catlin_plan) -> None:
    """The one branch that must NOT become N/A: a post that says nothing about its bearing.

    "No `supported_by` authored" is a modelling gap, and a gap is UNKNOWN. Reporting it N/A
    would be the exact inversion this check was fixed to remove — turning the absence of
    information into a verdict about the building.
    """
    from typehaus.checks.structural.deck import _not_a_pad

    post = next(e for e in catlin_plan.all_elements()
                if getattr(e, "tag", None) == "PT-SG-COL")
    deck = next(e for e in catlin_plan.all_elements()
                if getattr(e, "tag", None) == "FS-SG-PORCH")

    class _Ctx:
        plan = catlin_plan

    finding = _not_a_pad(_Ctx(), deck, post, None, ())
    assert finding.result is Result.UNKNOWN
    assert "declares no supported_by" in finding.message

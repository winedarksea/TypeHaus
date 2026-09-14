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
    # A post on another post is not a post on the ground. **BOTH centre pillars bear on the
    # cast columns again since 2026-09-14** — PT-SG-BF2 on PT-SG-FCOL, PT-SG-BR2 on
    # PT-SG-COL — which is where BF2 stood until 2026-09-03 and where neither stood in
    # between. The verdict did NOT move with them, and that is the interesting part: it was
    # N/A when they stood on `FS-SG-PORCH` and it is N/A now, because the rule is "this post
    # has no footing of its own to size" and a deck and a column answer it the same way.
    # What changed is the EVIDENCE, and the evidence is the whole content of an N/A: minting
    # `spread_footing/PT-SG-BF2` would name a footing that does not exist either way, and
    # `engineering/pier_basis._piers_below` is what hands the load to the item that does.
    "PT-SG-BR2": (Result.NOT_APPLICABLE, "PT-SG-COL"),
    "PT-SG-BF2": (Result.NOT_APPLICABLE, "PT-SG-FCOL"),
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


def test_only_the_belled_piers_remain_engineered(findings) -> None:
    """The whole point of the change: eight handoffs become the piers that really are one.

    An ENGINEERED finding names an item a professional seal has to cover. Six of the original
    eight named items nobody could ever design, because the footing they named does not exist.

    **Seven since 2026-09-10**, and the five new ones were the same condition, not a
    regression: the north entry piers each bore on their own ``Footing`` with an authored
    ``bottom_elevation``, which is a belled pier, and IRC Table R507.3.1 publishes flat-pad
    rows only.

    ** FIVE SINCE 2026-09-14, AND THE TWO THAT LEFT ARE THE POINT OF THE CHANGE. ** The north
    entry's three HOUSE-side piers became ``Pad``s that day and are graded prescriptively
    right here. What made that possible was teaching this rule the ROOF: ``_roof_borne_posts``
    converts a post's roof-footprint share into R507.3.1's own deck currency, so the canopy's
    snow arrives at the table as equivalent area instead of being dropped — which is what
    ``Footing`` was chosen over ``Pad`` to avoid in the first place.

    **``PT-BW-RE`` moved the other way and that is not a contradiction.** It was absent from
    this set because it carries a roof header and NO deck, so a rule that walked only a deck's
    own posts never reached it — not graded lightly: not graded. It is reached now, and it is
    a ``Pad``, so it is graded and not engineered.

    The three GARAGE-side piers stay: they are cast on the garage strip footing's own plane
    and lap ~7 1/2" into it, and the pier line is 4 1/2" from that footing's face, so no
    rectangle clears it — one pour, which only ``Footing.under`` can say. See
    ``params/north_entry_frame.py``.
    """
    engineered = {f.element_tags[1] for f in findings
                  if f.authority is Authority.ENGINEERED and len(f.element_tags) > 1
                  and str(f.element_tags[1]).startswith("PT-")}
    assert engineered == {"PT-SG-COL", "PT-SG-FCOL",
                          "PT-BW-GW", "PT-BW-GE", "PT-BW-RNE"}
    items = {f.engineering_item for f in findings if f.engineering_item}
    assert items == {f"spread_footing/{tag}" for tag in engineered}


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
    # The untouched branch still runs, and since 2026-09-14 it has subjects again: the north
    # entry's three HOUSE-side piers became ``Pad``s that day (``PD-BW-W`` / ``-E`` / ``-RE``),
    # so the area branch this rule exists for is exercised by the reference house rather than
    # only by a unit fixture. It was vacuous in between — the four passage pads it used to
    # grade went with the foundation bridge.
    pads = {f.element_tags[1] for f in findings
            if len(f.element_tags) > 1 and str(f.element_tags[1]).startswith("PD-BW-")}
    assert pads == {"PD-BW-W", "PD-BW-E", "PD-BW-RE"}


def test_a_post_that_declares_no_bearing_is_unknown_not_na(catlin_plan) -> None:
    """The one branch that must NOT become N/A: a post that says nothing about its bearing.

    "No `supported_by` authored" is a modelling gap, and a gap is UNKNOWN. Reporting it N/A
    would be the exact inversion this check was fixed to remove — turning the absence of
    information into a verdict about the building.
    """
    from typehaus.checks.structural.deck import _not_a_pad

    post = next(e for e in catlin_plan.all_elements()
                if getattr(e, "tag", None) == "PT-SG-COL")

    class _Ctx:
        plan = catlin_plan

    # A TAG, not the element: ``_not_a_pad`` takes what the finding should NAME as the thing
    # being carried, and since 2026-09-14 that is a deck tag or a ROOF tag — the check grades
    # posts that carry only a roof header too, and a roof is not a ``_Deck``.
    finding = _not_a_pad(_Ctx(), "FS-SG-PORCH", post, None, ())
    assert finding.result is Result.UNKNOWN
    assert "declares no supported_by" in finding.message

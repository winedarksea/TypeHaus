"""The suspended deck's span, read off a published table rather than waiting for a seal.

``structural.slab_published_span`` is the prescriptive read that replaced "graded by
nothing" for ``SL-M-DECK``. Three things have to hold, and each is one test below: the
authored BuildDeck row grades PASS at catlin's 18'-0"; a row whose ``member`` no longer
describes the model goes UNKNOWN naming the drift rather than printing a stale PASS; and a
house with no suspended slab earns NOT_APPLICABLE from positive evidence instead of
returning ``[]``.
"""

from __future__ import annotations

from _helpers import check_context

from typehaus.checks.structural.slab_span import slab_published_span
from typehaus.findings import Result
from typehaus.quantities import ft


def _findings(plan, model):
    return slab_published_span(check_context(plan, model))


def _replaced(catlin_plan, tag, **updates):
    element = catlin_plan.by_tag(tag)
    storey = next(s.tag for s in catlin_plan.storeys
                  if any(e.tag == tag for e in catlin_plan.storey_elements(s.tag)))
    kept = [e if e.tag != tag else element.model_copy(update=updates)
            for e in catlin_plan.storey_elements(storey)]
    return catlin_plan.with_elements(storey, kept)


def test_the_authored_buildeck_row_grades_the_deck_pass(catlin_plan, catlin_model_ro):
    findings = _findings(catlin_plan, catlin_model_ro)
    assert len(findings) == 1, [f.message for f in findings]
    finding = findings[0]
    assert finding.result is Result.PASS, finding.message
    assert finding.element_tags == ("SL-M-DECK",)
    # The short side of an 18' x 23' band, not its long side and not its diagonal.
    assert "18.00'" in finding.message
    assert "20.00'" in finding.message
    # The conditions the row assumes are printed: a prescriptive PASS nobody can read the
    # conditions of is a claim, not a read.
    assert "L/480" in finding.message
    assert "BuildDeck" in finding.message


def test_a_row_read_for_another_section_refuses_to_grade(catlin_plan, catlin_model_ro):
    """Retype the form and the quotation stops describing the building.

    ``member`` is derived from ``DECK_EPS_INT`` — the form's thickness and material name and
    the cap's thickness — so this is the drift guard doing its job, not a spelling check.
    """
    deck = catlin_plan.by_tag("SL-M-DECK")
    stale = deck.published_span.model_copy(
        update={"member": '8" BuildDeck EPS deck form under a 4" cast cap'})
    plan = _replaced(catlin_plan, "SL-M-DECK", published_span=stale)

    findings = _findings(plan, catlin_model_ro)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.result is Result.UNKNOWN, finding.message
    assert "no longer describes this member" in finding.message
    # Named both ways round, so a reader can see which half moved.
    assert '8" BuildDeck' in finding.message
    assert '10" BuildDeck' in finding.message


def test_a_deck_past_its_published_row_fails(catlin_plan, catlin_model_ro):
    """A published maximum is a maximum. No rounding, and no quiet PASS past it."""
    deck = catlin_plan.by_tag("SL-M-DECK")
    short = deck.published_span.model_copy(update={"span": ft(16)})
    plan = _replaced(catlin_plan, "SL-M-DECK", published_span=short)

    finding = _findings(plan, catlin_model_ro)[0]
    assert finding.result is Result.FAIL, finding.message
    assert "past the 16.00'" in finding.message


def test_no_authored_row_is_unknown_with_the_authoring_hint(catlin_plan, catlin_model_ro):
    plan = _replaced(catlin_plan, "SL-M-DECK", published_span=None)
    finding = _findings(plan, catlin_model_ro)[0]
    assert finding.result is Result.UNKNOWN
    assert "no published table row is authored" in finding.message


def test_a_house_with_no_suspended_slab_earns_not_applicable(catlin_plan, catlin_model_ro):
    """N/A is positive evidence of absence, never an empty list.

    Strip the ceiling from under the one suspended slab in the house and there is nothing
    left that spans: every other pour here bears on the ground.
    """
    plan = _replaced(catlin_plan, "SL-M-DECK", ceiling_below=())
    findings = _findings(plan, catlin_model_ro)
    assert len(findings) == 1
    assert findings[0].result is Result.NOT_APPLICABLE
    assert "no slab in this building is suspended" in findings[0].message

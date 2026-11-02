"""A suspended deck's span, read off a published table rather than waiting for a seal.

``structural.slab_published_span`` grades the BuildDeck row authored on
``_mixed_deck_plan``'s deck (catlin's ``SL-M-DECK`` retired 2026-11-01, decision #112). Each
test is one thing that has to hold: the row PASSes at 18'-0"; a row whose ``member`` no longer
describes the model goes UNKNOWN naming the drift; a span past the row FAILs; no row is
UNKNOWN; and a house with no suspended slab earns NOT_APPLICABLE, never ``[]``.
"""

from __future__ import annotations

from _helpers import check_context
from _mixed_deck_plan import DECK, deck, mixed_deck_model, mixed_deck_plan, published_row

from typehaus.checks.structural.slab_span import slab_published_span
from typehaus.findings import Result
from typehaus.quantities import ft


def _findings(**slab_update):
    # The check reads the plan only; the shared model just fills the context.
    plan = mixed_deck_plan(slab=deck(**slab_update))
    return slab_published_span(check_context(plan, mixed_deck_model()))


def test_the_authored_buildeck_row_grades_the_deck_pass():
    findings = _findings()
    assert len(findings) == 1, [f.message for f in findings]
    finding = findings[0]
    assert finding.result is Result.PASS, finding.message
    assert finding.element_tags == (DECK,)
    # The short side of an 18' x 18' outline, against the row's 20'.
    assert "18.00'" in finding.message
    assert "20.00'" in finding.message
    # The row's conditions are printed: a PASS nobody can read the conditions of is a claim.
    assert "L/480" in finding.message
    assert "BuildDeck" in finding.message


def test_a_row_read_for_another_section_refuses_to_grade():
    """``member`` is derived from the deck's assembly (form depth and name, cap depth), so a
    row quoted for another section stops describing the building."""
    stale = published_row(member='8" BuildDeck EPS deck form under a 4" cast cap')
    (finding,) = _findings(published_span=stale)
    assert finding.result is Result.UNKNOWN, finding.message
    assert "no longer describes this member" in finding.message
    # Named both ways round, so a reader can see which half moved.
    assert '8" BuildDeck' in finding.message
    assert '10" BuildDeck' in finding.message


def test_a_deck_past_its_published_row_fails():
    """A published maximum is a maximum. No rounding, and no quiet PASS past it."""
    (finding,) = _findings(published_span=published_row(span=ft(16)))
    assert finding.result is Result.FAIL, finding.message
    assert "past the 16.00'" in finding.message


def test_no_authored_row_is_unknown_with_the_authoring_hint():
    (finding,) = _findings(published_span=None)
    assert finding.result is Result.UNKNOWN
    assert "no published table row is authored" in finding.message


def test_a_house_with_no_suspended_slab_earns_not_applicable():
    """Strip the ceiling from under the one suspended slab and nothing left spans."""
    findings = _findings(ceiling_below=())
    assert len(findings) == 1
    assert findings[0].result is Result.NOT_APPLICABLE
    assert "no slab in this building is suspended" in findings[0].message

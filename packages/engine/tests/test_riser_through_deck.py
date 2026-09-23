"""``mep.riser_through_deck`` — a vertical through a floor needs a hole somebody drew.

``plans/TODO.md``'s "``FS-M-MECH`` still carries the vents, the radon riser and nine
conduits through its joist field **undrawn**", made into a verdict. A horizontal run has
``mep.run_member_crossing`` to answer to; a riser had nothing.
"""

from __future__ import annotations

import pytest
from _helpers import CATLIN

from typehaus.checks.mep.riser_through_deck import MIN_SPAN_FRACTION, riser_through_deck
from typehaus.findings import Result, Severity

pytestmark = pytest.mark.slow


def _by_result(ctx, result):
    return [f for f in riser_through_deck(ctx) if f.result is result]


def test_a_riser_in_a_CHASE_is_silent_ON_THAT_DECK(catlin_ctx) -> None:
    """``FO-M-ERV-OA`` and ``FO-M-ERV-EA`` are ``FloorOpeningPurpose.CHASE`` on FS-M-MECH,
    added on 2026-09-15 for exactly the two ERV risers. A chase is recognised by WHAT IT IS
    rather than by what it names, and ``DU-ERV-OA`` is silent because of it.

    **Per deck, and that is the finding.** ``DU-ERV-EA`` carries on up through FS-S-WEST,
    which has no opening at all — the other half of the TODO's sentence about the chase
    cluster being undrawn, and an 8" duct landing on a truss chord."""
    reported = {(tag, deck) for f in riser_through_deck(catlin_ctx)
                for tag in f.element_tags for deck in f.element_tags if deck.startswith("FS-")}
    assert not any(tag == "DU-ERV-OA" for tag, _deck in reported)
    assert ("DU-ERV-EA", "FS-S-WEST") in reported
    assert ("DU-ERV-EA", "FS-M-MECH") not in reported


def test_a_riser_the_deck_was_opened_FOR_is_silent() -> None:
    """``FloorOpening.penetration_for`` — the hole that exists only because THIS run goes
    through it, and the strongest statement the model has. Catlin's chase openings are
    CHASE and so are exempt geometrically; this pins the named form, which is what a
    campaign will author when it frames a hole for one duct."""
    from types import SimpleNamespace

    from shapely.geometry import Point, Polygon

    from typehaus.checks.mep.riser_through_deck import _is_authorised

    ring = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    deck = SimpleNamespace(deck_voids=(), chases=(),
                           penetrations=(("FO-X", ring, ("DU-MINE",)),))
    assert _is_authorised(deck, "DU-MINE", Point(0.5, 0.5), Polygon) is True
    # The hole was framed for one run. A different run standing in it is still a defect.
    assert _is_authorised(deck, "DU-YOURS", Point(0.5, 0.5), Polygon) is False
    # And it only covers its own footprint.
    assert _is_authorised(deck, "DU-MINE", Point(5.0, 5.0), Polygon) is False


def test_a_riser_ON_A_JOIST_fails_naming_the_member_and_the_station(catlin_plan) -> None:
    """The unambiguous half. That member is cut and nothing headed it.

    Catlin has no example left since 2026-09-23, when FS-S-WEST's 34'-8" truss moved to
    34'-5 3/4" (``JoistSpec.line_overrides``). Undo that one move and DU-ERV-EA lands on it."""
    from typehaus.checks.run import build_context
    from typehaus.model.floors import FloorSystem

    storey, items = next((s, items) for s, items in catlin_plan.elements.items()
                         if any(getattr(e, "tag", None) == "FS-S-WEST" for e in items))

    def unmoved(e):
        if not (isinstance(e, FloorSystem) and e.tag == "FS-S-WEST"):
            return e
        moves = tuple(m for m in e.joists.line_overrides if abs(m[0].inches - 416) > 1e-6)
        return e.model_copy(update={"joists": e.joists.model_copy(
            update={"line_overrides": moves})})

    ctx, _ = build_context(catlin_plan.with_elements(storey, map(unmoved, items)), CATLIN)
    finding = next(f for f in _by_result(ctx, Result.FAIL) if "DU-ERV-EA" in f.element_tags)
    assert "FS-S-WEST" in finding.element_tags
    assert "on joist joist-" in finding.message
    assert "at (2'-0.0\", 35'-0.0\")" in finding.message
    assert "nothing headed it" in finding.message


def test_a_riser_under_the_drill_allowance_is_UNKNOWN_and_quotes_its_basis(catlin_ctx) -> None:
    """Whether a 7/8" line may share an I-joist bay at that station comes off the
    fabricator's chart, which this engine does not hold. A confident verdict either way
    would be inventing one — so the finding hands back ``member_window.basis``."""
    finding = next(f for f in _by_result(catlin_ctx, Result.UNKNOWN)
                   if "PR-B-CW-BATH1" in f.element_tags)
    assert "the fabricator's chart, which this engine does not hold" in finding.message
    assert "0.88\" across" in finding.message


def test_every_finding_is_WARN_and_none_shuts_the_permit_gate(catlin_ctx) -> None:
    """This reads something NOT DRAWN YET, not something drawn wrong, and a missing floor
    opening should not carry a pipe-through-a-beam's weight. ``permit.py`` keys off ERROR
    severity alone; ``CheckReport.counts()`` still counts the FAIL."""
    assert all(f.severity is Severity.WARN for f in riser_through_deck(catlin_ctx))


def test_a_stub_into_the_sheet_is_not_a_riser_through_the_deck() -> None:
    """A run whose top stops an inch into the subfloor is a stub, and a stub is a different
    question. Half the band is the line."""
    assert MIN_SPAN_FRACTION == 0.5


def test_catlin_is_pinned_so_a_campaign_can_see_itself(catlin_ctx) -> None:
    """47: 29 risers landing on a member, 18 clear of every member but over the 2" this
    house says a trade may drill. Pinned as two counts rather than a list so a campaign that
    fixes ten is visible without re-blessing a page of tags.

    It was 29/18 when the check landed. D1 took level 2 trunk-and-branch on the same day and
    DU-M-ERV-R-LAUNDRY's turn south to the standpipe boot made it 29/19 — a 4" hole in a
    clear bay, which is the DOCUMENTATION half of this check and not the structural one.

    Back to 29/18 with D2 (2026-09-19): DU-A-ERV-R-STUBATH's riser used to stand up through
    FS-ATTIC's deck in the open and now stands inside W-A-STU-W, between the 21'-4" and
    22'-0" studs, where the wall's own plate is the hole's frame. The on-member count is
    untouched, which is the point of pinning the two separately — D2 moved ducts, and not
    one of them was landing on a joist.

    6/29 on 2026-09-23: streams G and J stepped risers off their joists and flanges (the chase
    risers, drains, and PR-B-CW-SBATH / PR-B-HW-WASH). Every one that moved into a clear bay
    changed column rather than vanishing, which is the DOCUMENTATION half again — a hole over
    2" still wants drawing.

    0/34 later that day: two FS-S-WEST trusses moved off five risers (each now undrawn in a
    clear bay), and the radon riser's FS-M-MECH hole became FO-M-ERV-EA, a CHASE."""
    fails = _by_result(catlin_ctx, Result.FAIL)
    on_member = [f for f in fails if "lands on the member" in f.message]
    undrawn = [f for f in fails if "FRAMED, NOT DRILLED" in f.message]
    assert len(on_member) == 0
    assert len(undrawn) == 34
    assert len(fails) == len(on_member) + len(undrawn)

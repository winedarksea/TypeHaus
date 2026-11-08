"""Catlin's MEP clearance ratchet (updated 2026-10-08).

``mep.run_interference``'s 11-pair campaign closed on 2026-10-08, and the first test below
holds every pair at zero except the two in ``_ON_HOLD``. The tests call the checks directly,
so a ``preferences.toml`` suppression cannot hide an ERV duct, vent or radon-riser clash.
"""

from __future__ import annotations

import re

import pytest

from typehaus.checks.mep.riser_through_deck import riser_through_deck
from typehaus.checks.mep.run_interference import run_interference
from typehaus.findings import Result

pytestmark = pytest.mark.slow

_WATCHED = re.compile(r"^DU-.*ERV|-VENT$|^VR-")

#: Held with plans/TODO.md "Holes through floor framing, ERV level 2" (owner, 2026-11-07):
#: both pipes wait on the trunk re-route. Delete with that item.
_ON_HOLD = {frozenset({"DU-M-ERV-R-BED2", "PR-M-KITCH-VENT"}),
            frozenset({"DU-M-ERV-R-LAUNDRY", "PR-A-HW-STUBATH"})}

#: No other watched run interpenetrations are accepted on catlin.
_KNOWN: set[frozenset[str]] = set()


def _failing_pairs(ctx) -> set[frozenset[str]]:
    return {frozenset(f.element_tags) for f in run_interference(ctx) if f.result is Result.FAIL}


def test_no_run_interpenetrates_another_anywhere(catlin_ctx) -> None:
    """Every pair, every trade. A new clash is a re-route, never a preferences entry."""
    pairs = _failing_pairs(catlin_ctx) - _ON_HOLD
    assert not pairs, sorted(sorted(pair) for pair in pairs)


def test_held_pairs_still_clash(catlin_ctx) -> None:
    """A hold that stops clashing is closed: delete it here and in preferences.toml."""
    cleared = _ON_HOLD - _failing_pairs(catlin_ctx)
    assert not cleared, sorted(sorted(pair) for pair in cleared)


def _watched(finding) -> bool:
    return any(_WATCHED.search(tag) for tag in finding.element_tags)


def test_no_new_erv_duct_vent_or_radon_riser_interpenetrations(catlin_ctx) -> None:
    pairs = {frozenset(f.element_tags) for f in run_interference(catlin_ctx)
             if f.result is Result.FAIL and _watched(f)} - _ON_HOLD
    assert pairs <= _KNOWN, sorted(sorted(pair) for pair in pairs - _KNOWN)


#: Risers that clear every member and pass through an open-web truss web, which the house
#: routes through by design (FS-S-WEST, storeys/second.py). The engine answers UNKNOWN
#: because whether a 1 1/2" vent may share a web is a fabricator's chart it does not hold.
#: Anything else standing in a web, or on a member, still fails this test.
#: PR-M-BATH2-TUB-VENT (e5128ca7d) is the same case as its sibling SH-VENT: 1.90" in a web bay.
#: PR-S-SUITEBATH-TUB-VENT's sloped leg is graded since the check read sloped crossings.
_WEB_PASSING_VENTS = {"PR-M-BATH1-LAV-VENT", "PR-M-BATH2-SH-VENT", "PR-M-BATH2-TUB-VENT",
                      "PR-M-LSINK-VENT", "PR-S-SUITEBATH-TUB-VENT"}


def test_every_erv_duct_and_vent_riser_stands_in_a_drawn_hole(catlin_ctx) -> None:
    found = [f.message for f in riser_through_deck(catlin_ctx)
             if f.result in (Result.FAIL, Result.UNKNOWN) and _watched(f)
             and not _web_passing(f)]
    assert not found, found


#: Trap-arm vents rising out of the joist band into the wet wall over it: clear of every
#: member, through the subfloor and the wall's own bottom plate, like the drain they tee off.
#: The three main-storey tees (mep_vent_tees.py) rise the same way through the TJI decks.
_WALL_FOOT_VENTS = {"PR-A-STUBATH-WC-VENT", "PR-M-BATH2-WC-VENT", "PR-M-BATH2-SH-VENT",
                    "PR-M-LSINK-VENT"}


def _web_passing(finding) -> bool:
    if (finding.result is Result.UNKNOWN and "clear of every member" in finding.message
            and any(tag in _WALL_FOOT_VENTS for tag in finding.element_tags)):
        return True
    return (finding.result is Result.UNKNOWN and "FS-S-WEST" in finding.message
            and "web" in finding.message
            and any(tag in _WEB_PASSING_VENTS for tag in finding.element_tags))

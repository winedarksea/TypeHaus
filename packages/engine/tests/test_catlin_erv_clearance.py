"""Catlin's MEP clearance ratchet (updated 2026-10-08).

``mep.run_interference`` is no longer suppressed in catlin's ``preferences.toml``: its
11-pair campaign closed on 2026-10-08, and the first test below holds EVERY pair at zero.
``mep.riser_through_deck`` is still blanket-suppressed for its open supply/drain campaign,
so the ERV/vent tests call the checks directly and suppression cannot hide an ERV duct, vent
or radon-riser clash.
"""

from __future__ import annotations

import re

import pytest

from typehaus.checks.mep.riser_through_deck import riser_through_deck
from typehaus.checks.mep.run_interference import run_interference
from typehaus.findings import Result

pytestmark = pytest.mark.slow

_WATCHED = re.compile(r"^DU-.*ERV|-VENT$|^VR-")

#: No watched run interpenetrations are accepted on catlin.
_KNOWN: set[frozenset[str]] = set()


def test_no_run_interpenetrates_another_anywhere(catlin_ctx) -> None:
    """Every pair, every trade. A new clash is a re-route, never a preferences entry."""
    pairs = {frozenset(f.element_tags) for f in run_interference(catlin_ctx)
             if f.result is Result.FAIL}
    assert not pairs, sorted(sorted(pair) for pair in pairs)


def _watched(finding) -> bool:
    return any(_WATCHED.search(tag) for tag in finding.element_tags)


def test_no_new_erv_duct_vent_or_radon_riser_interpenetrations(catlin_ctx) -> None:
    pairs = {frozenset(f.element_tags) for f in run_interference(catlin_ctx)
             if f.result is Result.FAIL and _watched(f)}
    assert pairs <= _KNOWN, sorted(sorted(pair) for pair in pairs - _KNOWN)


def test_every_erv_duct_and_vent_riser_stands_in_a_drawn_hole(catlin_ctx) -> None:
    found = [f.message for f in riser_through_deck(catlin_ctx)
             if f.result in (Result.FAIL, Result.UNKNOWN) and _watched(f)]
    assert not found, found

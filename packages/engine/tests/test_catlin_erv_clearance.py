"""The ERV/vent clearance campaign's ratchet on catlin (2026-09-24).

``mep.run_interference`` and ``mep.riser_through_deck`` are blanket-suppressed in catlin's
``preferences.toml`` for the plumbing and raceway pairs still open. These call the checks
directly, so suppression cannot hide an ERV duct, a vent or the radon riser coming back.
"""

from __future__ import annotations

import re

import pytest

from typehaus.checks.mep.riser_through_deck import riser_through_deck
from typehaus.checks.mep.run_interference import run_interference
from typehaus.findings import Result

pytestmark = pytest.mark.slow

_WATCHED = re.compile(r"^DU-.*ERV|-VENT$|^VR-")

#: Pairs still open, each with its reason. Empty since REG-A-STUBATH-EXH came down to 3'-0"
#: (2026-09-26). Shrink this set, never grow it.
_KNOWN: set[frozenset[str]] = set()


def _watched(finding) -> bool:
    return any(_WATCHED.search(tag) for tag in finding.element_tags)


def test_no_erv_duct_vent_or_radon_riser_interpenetrates_anything(catlin_ctx) -> None:
    pairs = {frozenset(f.element_tags) for f in run_interference(catlin_ctx)
             if f.result is Result.FAIL and _watched(f)}
    assert pairs <= _KNOWN, sorted(sorted(pair) for pair in pairs - _KNOWN)


def test_every_erv_duct_and_vent_riser_stands_in_a_drawn_hole(catlin_ctx) -> None:
    found = [f.message for f in riser_through_deck(catlin_ctx)
             if f.result in (Result.FAIL, Result.UNKNOWN) and _watched(f)]
    assert not found, found

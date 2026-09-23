"""IRC Table R507.6 by species, the ``:kdat`` key, and the deck snow gate.

The table is species-split: Southern pine 2x12 at 12" o.c. spans 18'-0", the redwood row
17'-5". The engine read only the redwood row, and ``"2x12:kdat"`` matched no key at all.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.structural.deck import deck_joist_span
from typehaus.checks.structural.deck_tables import deck_beam_span_limit, deck_joist_span_limit
from typehaus.findings import Result
from typehaus.model.floors import FloorSystem, JoistSpec
from typehaus.quantities import Point2D, ft, inch

_M_PER_FT = 0.3048


@pytest.mark.parametrize(("species", "expected"), [
    ("southern_pine", 18.00), ("df_hf_spf", 18.00), ("redwood_cedar", 17.42), (None, 17.42),
])
def test_2x12_at_12_by_species(species, expected):
    assert deck_joist_span_limit("2x12", 12.0, species) == (expected, 12.0)


def test_species_rows_differ_where_the_table_does():
    assert deck_joist_span_limit("2x10", 16.0, "southern_pine") == (14.00, 16.0)
    assert deck_joist_span_limit("2x10", 16.0, "df_hf_spf") == (13.58, 16.0)
    assert deck_joist_span_limit("2x8", 24.0, "southern_pine") == (9.67, 24.0)


def test_none_reads_the_most_restrictive_row():
    for member in ("2x6", "2x8", "2x10", "2x12"):
        for spacing in (12.0, 16.0, 24.0):
            floor = deck_joist_span_limit(member, spacing)
            assert all(floor[0] <= deck_joist_span_limit(member, spacing, s)[0]
                       for s in ("southern_pine", "df_hf_spf", "redwood_cedar"))


def test_a_treatment_suffix_is_not_part_of_the_key():
    assert deck_joist_span_limit("2x12:kdat", 12.0, "southern_pine") == (18.00, 12.0)
    assert deck_beam_span_limit("3-2x12:kdat", 10.0) == deck_beam_span_limit("3-2x12", 10.0)


def _deck(species=None) -> FloorSystem:
    ring = (Point2D(x=ft(0), y=ft(0)), Point2D(x=ft(19), y=ft(0)),
            Point2D(x=ft(19), y=ft(9)), Point2D(x=ft(0), y=ft(9)))
    return FloorSystem(
        uid="TSTFS03AAA", tag="FS-T-DECK",
        joists=JoistSpec(member="2x12:kdat", spacing=inch(12), direction="x",
                         bearing_refs=("BM-A", "BM-B"), species=species),
        outline=ring, service="deck",
    )


def _ctx(deck, span_ft, snow=None):
    joist = SimpleNamespace(category="joist", p0=(0.0, 0.0), p1=(span_ft * _M_PER_FT, 0.0),
                            length_m=span_ft * _M_PER_FT)
    return SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: [deck], by_tag=lambda tag: None),
        model=SimpleNamespace(walls=[], floors=[SimpleNamespace(tag=deck.tag,
                                                                members=[joist])],
                              solids=[]),
        preferences=SimpleNamespace(structural=SimpleNamespace(deck_snow_psf=snow)),
    )


def _one(findings):
    assert len(findings) == 1, findings
    return findings[0]


def test_18_feet_on_the_southern_pine_row_is_at_the_limit_not_past_it():
    # 18'-0" to floating-point noise, as a resolved member measures it
    finding = _one(deck_joist_span(_ctx(_deck("southern_pine"), 18.0 + 1e-9)))
    assert finding.result is Result.PASS
    assert "Southern pine" in finding.message and "18.00'" in finding.message


def test_the_same_span_fails_on_the_restrictive_row():
    finding = _one(deck_joist_span(_ctx(_deck(), 18.0)))
    assert finding.result is Result.FAIL
    assert "17.42'" in finding.message


def test_unauthored_snow_is_named_not_examined():
    finding = _one(deck_joist_span(_ctx(_deck("southern_pine"), 16.75)))
    assert finding.result is Result.PASS
    assert "snow not examined" in finding.message


def test_snow_at_or_under_40_is_governed_by_the_live_load():
    finding = _one(deck_joist_span(_ctx(_deck("southern_pine"), 16.75, snow=35.0)))
    assert finding.result is Result.PASS
    assert "40 psf live governs over 35 psf snow" in finding.message


def test_snow_over_40_takes_the_deck_off_the_table():
    finding = _one(deck_joist_span(_ctx(_deck("southern_pine"), 16.75, snow=50.0)))
    assert finding.result is Result.UNKNOWN
    assert "design snow 50 psf" in finding.message

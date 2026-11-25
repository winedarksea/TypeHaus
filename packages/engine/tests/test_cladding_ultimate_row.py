"""``structural.cladding_wind`` on a non-metal panel with an ULTIMATE-basis row (LP SmartSide,
ESR-1301 Table 3A), oracled by ``houses/catlin/notes/court_face_lp_panel.md`` "Wind read"."""

from __future__ import annotations

from typehaus import inch
from typehaus.checks.structural.published_cladding import graded_against_published_cladding
from typehaus.findings import Result
from typehaus.model.published_cladding import PublishedCladdingLoad

_LP_TAGS = ("W-B-S2-FR", "W-B-S3-FR")


def _row(**over) -> PublishedCladdingLoad:
    base = dict(source="ESR-1301", table="Table 3A", member="LP SmartSide 38 Series",
                basis="ultimate", allowable_outward_psf=71.0, allowable_inward_psf=71.0,
                fastener_spacing=inch(16), condition="fn 1-3", panel_fastener="0.113 in nail")
    return PublishedCladdingLoad(**{**base, **over})


def _grade(row, demand, spacing=16.0):
    return graded_against_published_cladding(
        "x", "wall", (), demand, "outward", row,
        material_name='LP SmartSide 38 Series 3/8" panel', fastener_spacing_in=spacing,
        coverage_in=None, panel_fastener="0.113 in nail, 2-1/2 in", support_is_wood=True,
        support_thickness_in=3.0, governing_demand_psf=19.93, wind_speed_mph=115.0,
        exposure="B")


def test_ultimate_row_compares_ultimate_demand_and_says_so():
    ok = _grade(_row(), 33.2)
    assert ok.result is Result.PASS and "33.2 psf ultimate" in ok.message
    assert _grade(_row(), 80.0).result is Result.FAIL


def test_wider_support_spacing_is_unknown_with_a_labelled_estimate():
    finding = _grade(_row(fastener_governed=True), 33.2, spacing=24.0)
    assert finding.result is Result.UNKNOWN
    assert 'indexed at 16" fastener spacing' in finding.message
    assert "Estimate, not a code read" in finding.message and "47.3 psf ultimate" in finding.message


def test_off_label_keeps_a_clean_row_unknown():
    finding = _grade(_row(off_label="over strapping"), 33.2)
    assert finding.result is Result.UNKNOWN and "over strapping" in finding.message


def test_catlin_lp_court_face_is_read_unknown_and_metal_is_untouched(catlin_ctx):
    from typehaus.checks.structural.cladding import cladding_fastener, cladding_wind
    wind = cladding_wind(catlin_ctx)
    lp = [f for f in wind if f.element_tags == _LP_TAGS]
    assert [f.result for f in lp] == [Result.UNKNOWN, Result.UNKNOWN]
    outward = next(f for f in lp if " outward" in f.message)
    for fragment in ("33.2 psf ultimate", 'indexed at 16" fastener spacing and the girts here '
                     'are 24" apart', "47.3 psf ultimate", "d/c 0.70", "Owner accepted"):
        assert fragment in outward.message, fragment
    assert all(f.result is Result.PASS for f in wind if f.element_tags != _LP_TAGS)
    fastener = {f.element_tags: f.result for f in cladding_fastener(catlin_ctx)}
    assert fastener[_LP_TAGS] is Result.NOT_APPLICABLE
    assert all(r is not Result.NOT_APPLICABLE for t, r in fastener.items() if t != _LP_TAGS)

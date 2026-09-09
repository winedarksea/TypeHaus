"""The zoning arithmetic C-101 and the cover sheet both print (→ emit/draw/site_metrics)."""

from __future__ import annotations

import pytest

from typehaus.emit.draw.site_metrics import (
    ZONING_LIMITS,
    building_coverage_ft2,
    coverage_table,
    impervious_ft2,
    lot_area_ft2,
    lot_line_dimensions,
    paving_ft2,
)
from typehaus.model.site import ImperviousSurface
from typehaus.quantities import ft, pt


def _rect(x0: float, y0: float, x1: float, y1: float):
    return (pt(ft(x0), ft(y0)), pt(ft(x1), ft(y0)), pt(ft(x1), ft(y1)), pt(ft(x0), ft(y1)))


def _site(catlin_plan, **kw):
    return catlin_plan.project.site.model_copy(update=kw)


def test_lot_area_is_derived_from_the_ring_not_stored(catlin_plan) -> None:
    """The whole point of deriving it: a 100 x 165 ring is 16,500 sf and nothing else."""
    site = _site(catlin_plan, parcel=_rect(0, 0, 100, 165))
    assert lot_area_ft2(site) == pytest.approx(16_500.0, rel=1e-9)


def test_a_ring_with_no_vertices_has_no_area_rather_than_zero(catlin_plan) -> None:
    assert lot_area_ft2(_site(catlin_plan, parcel=())) is None


def test_building_coverage_is_the_footprint_the_site_plan_draws(catlin_model_ro) -> None:
    """Same polygon as ``siteplan._primary_footprint`` — the sheet cannot show one area and
    the table another."""
    from typehaus.emit.draw.siteplan import _primary_footprint

    footprint = _primary_footprint(catlin_model_ro)
    assert footprint is not None
    assert building_coverage_ft2(catlin_model_ro) == pytest.approx(
        footprint.area * 10.763910416709722)


def test_impervious_groups_on_kind_not_on_label(catlin_plan) -> None:
    """``label`` is prose. A driveway is told from a patio by ``kind``, which is why the
    field exists at all."""
    surfaces = (
        ImperviousSurface(label="the drive", outline=_rect(0, 0, 12, 40),
                          near_elevation=ft(0), far_elevation=ft(-1), kind="driveway"),
        ImperviousSurface(label="also a drive, honest", outline=_rect(0, 50, 10, 60),
                          near_elevation=ft(0), far_elevation=ft(-1), kind="patio"),
    )
    site = _site(catlin_plan, parcel=_rect(0, 0, 100, 165), impervious_surfaces=surfaces)
    assert impervious_ft2(site) == pytest.approx({"driveway": 480.0, "patio": 100.0})
    # Only driveway/parking paving counts against Ord. 23-43's 15% / 1,000 sf cap.
    assert paving_ft2(site) == pytest.approx(480.0)


def test_the_coverage_table_prints_a_district_limit_only_when_the_district_is_known(
        catlin_plan, catlin_model_ro) -> None:
    # ``zoning_district=None`` explicitly: `_site` copies catlin's own Site, which states
    # RL, and `coverage_table` falls back to the site when the kwarg is unset — so a bare
    # copy tests the RL path twice and the unstated path not at all.
    site = _site(catlin_plan, parcel=_rect(0, 0, 100, 165), zoning_district=None)
    unstated = dict((row[0], row[2]) for row in coverage_table(catlin_model_ro, site))
    assert unstated["BUILDING COVERAGE"] == ""
    assert unstated["ZONING DISTRICT"] == ""

    rl = dict((row[0], row[2]) for row in
              coverage_table(catlin_model_ro, site, zoning_district="RL"))
    assert rl["BUILDING COVERAGE"] == "40% MAX"
    assert rl["BUILDING HEIGHT"] == "35' MAX"


def test_an_unsurveyed_parcel_says_so_instead_of_reporting_a_percentage(
        catlin_plan, catlin_model_ro) -> None:
    rows = coverage_table(catlin_model_ro, _site(catlin_plan, parcel=()))
    assert ("LOT AREA", "NOT SURVEYED", "") in rows
    assert not any(row[0] == "BUILDING COVERAGE" for row in rows)


def test_st_paul_districts_are_the_post_ordinance_ones() -> None:
    """Ord. 23-43 repealed R1-R4 / RT1 / RT2. A table still keyed on those would silently
    grade every house against a district that no longer exists."""
    assert set(ZONING_LIMITS) == {"RL", "H1", "H2"}
    assert [ZONING_LIMITS[d].max_lot_coverage_pct for d in ("RL", "H1", "H2")] == [40, 45, 50]


def test_lot_line_dimensions_index_the_same_edges_setbacks_do(catlin_plan) -> None:
    """``SetbackSpec.edge`` and a printed dimension must name one line, or the reviewer is
    reading a setback against the wrong side of the lot."""
    site = _site(catlin_plan, parcel=_rect(0, 0, 100, 165))
    dims = lot_line_dimensions(site)
    assert [i for i, _, _ in dims] == [0, 1, 2, 3]
    assert [round(length) for _, length, _ in dims] == [100, 165, 100, 165]
    assert [bearing for _, _, bearing in dims] == [
        "N 90°00' E", "N 0°00' E", "N 90°00' W", "S 0°00' W"]


# --- code.site_parcel_is_surveyed ---------------------------------------------------------
#
# Every number above is measured off the parcel ring, which is exactly why the ring's
# provenance is a graded question and lives beside the arithmetic that trusts it.

def _parcel_verdicts(catlin_model, **site_updates):
    from test_site_checks import _model_with_site

    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Tier

    model = _model_with_site(catlin_model, **site_updates)
    report = run_from_model(model, [], tier=Tier.CODE)
    return [f for f in report.findings if f.check_id == "code.site_parcel_is_surveyed"]


def test_an_unstated_parcel_basis_is_unknown_never_a_silent_survey(catlin_model) -> None:
    findings = _parcel_verdicts(catlin_model, parcel_basis=None)
    assert findings and all(f.result.value == "unknown" for f in findings)
    assert all(f.code_ref == "local zoning" for f in findings)


def test_a_placeholder_parcel_fails_and_says_the_word(catlin_model) -> None:
    findings = _parcel_verdicts(catlin_model, parcel_basis="placeholder")
    assert findings and all(f.result.value == "fail" for f in findings)
    assert "PLACEHOLDER" in findings[0].message


def test_a_survey_with_no_surveyor_named_is_not_a_survey(catlin_model) -> None:
    findings = _parcel_verdicts(catlin_model, parcel_basis="survey", survey_by=None)
    assert findings and all(f.result.value == "unknown" for f in findings)


def test_a_certified_survey_passes_and_credits_the_surveyor(catlin_model) -> None:
    findings = _parcel_verdicts(catlin_model, parcel_basis="survey",
                                survey_by="A. Surveyor, LS 12345", survey_date="2026-09-01")
    assert findings and all(f.result.value == "pass" for f in findings)
    assert "A. Surveyor, LS 12345" in findings[0].message
    assert "2026-09-01" in findings[0].message

"""The box gutter's capacity, against ``houses/catlin/notes/box_gutter_sizing.md``.

The note is the oracle: every number here is one it prints. The first layer checks the PGI
formulas on their own; the second reads the house's gutter, roof and leader from the model.
"""

from __future__ import annotations

import pytest
from _helpers import catlin_params

from typehaus.library.trim.metal_sales import (
    BOX_GUTTER_BOTTOM_IN,
    BOX_GUTTER_FRONT_IN,
    PBR_BOX_GUTTER_5X4,
)
from typehaus.resolve.gutter_sizing import leader_served_area_sf, pgi_required_width_in
from typehaus.resolve.roof_catchment import roof_catchments

_SF_PER_M2 = 1 / 0.3048**2
RUN_FT = 37.125  # note §2: one leader's gutter run, the full eave
PLAN_SF = 690.68  # note §2: one half of RF-HOUSE, horizontal projection
SLOPED_SF = 772.2  # note §2: plan x sqrt(1 + (6/12)^2)
DESIGN_IN_HR = 7.536  # note §1: St Paul 10-yr 5-min, 0.628 in x 12
RATIO_5X4 = BOX_GUTTER_FRONT_IN / BOX_GUTTER_BOTTOM_IN  # note §3: M = 4/5
LEADER_4IN_SQ_IN = 12.57
LEADER_3IN_SQ_IN = 7.07


def test_pgi_worked_example_reads_between_5_and_6_in() -> None:
    """PGI-16's own example: L 40, M 0.75, IA 7200 reads 5.31 in."""
    assert pgi_required_width_in(6.0, 1200.0, 40.0, 0.75) == pytest.approx(5.31, abs=0.01)


@pytest.mark.parametrize(
    ("intensity", "area", "expected"),
    [
        (DESIGN_IN_HR, PLAN_SF, 4.52),  # 10-yr 5-min, plan: the design basis
        (DESIGN_IN_HR, SLOPED_SF, 4.71),  # 10-yr 5-min, 6:12 sloped
        (3.55, PLAN_SF, 3.46),  # 100-yr 1-hr, plan (cross-check)
        (9.18, SLOPED_SF, 5.05),  # 25-yr 5-min, sloped: FAILS 5.00 in
        (11.88, PLAN_SF, 5.32),  # 100-yr 5-min, plan: FAILS
    ],
)
def test_5x4_demand_matches_the_note(intensity, area, expected) -> None:
    got = pgi_required_width_in(intensity, area, RUN_FT, RATIO_5X4)
    assert got == pytest.approx(expected, abs=0.01)


def test_design_basis_passes_and_the_25_year_sloped_case_fails() -> None:
    assert pgi_required_width_in(DESIGN_IN_HR, PLAN_SF, RUN_FT, RATIO_5X4) < 5.0
    assert pgi_required_width_in(DESIGN_IN_HR, SLOPED_SF, RUN_FT, RATIO_5X4) < 5.0
    assert pgi_required_width_in(9.18, SLOPED_SF, RUN_FT, RATIO_5X4) > 5.0


def test_current_6x5_box_passes_the_design_basis() -> None:
    assert pgi_required_width_in(DESIGN_IN_HR, SLOPED_SF, RUN_FT, 5.0 / 6.0) == pytest.approx(
        4.60, abs=0.01
    )


@pytest.mark.parametrize(
    ("area_sq_in", "served_sf"),
    [
        (LEADER_4IN_SQ_IN, 2001.0),  # kept: 4 in round
        (LEADER_3IN_SQ_IN, 1126.0),  # not used: clears the design basis only
    ],
)
def test_leader_capacity_matches_the_note(area_sq_in, served_sf) -> None:
    assert leader_served_area_sf(area_sq_in, DESIGN_IN_HR) == pytest.approx(served_sf, abs=1.0)


def test_3_in_leader_fails_the_100_year_sloped_cross_check() -> None:
    required = SLOPED_SF * 11.88 / 1200.0
    assert required == pytest.approx(7.64, abs=0.01)
    assert LEADER_3IN_SQ_IN < required < LEADER_4IN_SQ_IN


def test_design_intensity_is_the_noaa_10_year_5_minute_depth() -> None:
    roof_trim = catlin_params("roof_trim")
    assert pytest.approx(DESIGN_IN_HR, abs=1e-9) == roof_trim._DESIGN_INTENSITY_IN_HR


def test_house_box_gutters_are_the_5x4_catalog_section(catlin_model_ro) -> None:
    """Both eaves are the PBR 5x4 on a 37.1' run, and the section is the note's."""
    gutters = {
        el.tag: el
        for el in catlin_model_ro.plan.all_elements()
        if getattr(el, "tag", "") in {"TR-RF-GUTTER-E", "TR-RF-GUTTER-W"}
    }
    assert set(gutters) == {"TR-RF-GUTTER-E", "TR-RF-GUTTER-W"}
    for gutter in gutters.values():
        assert gutter.product == "PBR_BOX_GUTTER_5X4"
        assert gutter.thickness.inches == pytest.approx(BOX_GUTTER_BOTTOM_IN)
        points = [p.xy_m for p in gutter.path]
        run_m = sum(
            ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
            for a, b in zip(points[:-1], points[1:], strict=True)
        )
        assert run_m / 0.3048 == pytest.approx(RUN_FT, abs=0.01)
    assert PBR_BOX_GUTTER_5X4.section_in[-1] == (BOX_GUTTER_BOTTOM_IN, BOX_GUTTER_FRONT_IN)


def test_house_roof_drains_the_note_area_and_the_5x4_clears_it(catlin_model_ro) -> None:
    catchment = roof_catchments(catlin_model_ro)
    for side in ("W", "E"):
        sf = catchment.by_leader[f"TR-RF-LEADER-{side}"] * _SF_PER_M2
        assert sf == pytest.approx(PLAN_SF, abs=0.2)
        assert pgi_required_width_in(DESIGN_IN_HR, sf, RUN_FT, RATIO_5X4) < BOX_GUTTER_BOTTOM_IN


def test_house_leaders_are_4_in_and_clear_the_design_area(catlin_model_ro) -> None:
    leaders = {
        el.tag: el
        for el in catlin_model_ro.plan.all_elements()
        if getattr(el, "tag", "") in {"TR-RF-LEADER-W", "TR-RF-LEADER-E"}
    }
    assert len(leaders) == 2
    assert leader_served_area_sf(LEADER_4IN_SQ_IN, DESIGN_IN_HR) > PLAN_SF
    for leader in leaders.values():
        assert leader.diameter.inches == pytest.approx(4.0)
        # PGI-15: a downspout no wider than the gutter's bottom.
        assert leader.diameter.inches <= BOX_GUTTER_BOTTOM_IN


def test_catalog_gutter_bills_by_part_and_not_under_drainage(catlin_model_ro) -> None:
    from typehaus.takeoff.cladding_trim import cladding_trim_takeoff
    from typehaus.takeoff.drainage import drainage_takeoff

    trim = {row["part"]: row for row in cladding_trim_takeoff(catlin_model_ro)}
    # Two runs of 37.1' at 20'-3" each: two sticks per eave. One end cap of each hand per eave.
    assert trim["58079XX"]["count"] == 4
    assert trim["58081XX"]["count"] == 2 and trim["58082XX"]["count"] == 2
    # 37.125' at 3'-0" o.c. is 13 spaces, so 14 straps and 14 rivets per eave.
    assert trim["58092XX"]["count"] == 28 and trim["trim-pop-rivet"]["count"] >= 28
    drainage_tags = {tag for row in drainage_takeoff(catlin_model_ro) for tag in row["tags"]}
    assert not any(tag.startswith("TR-RF-GUTTER-") for tag in drainage_tags)

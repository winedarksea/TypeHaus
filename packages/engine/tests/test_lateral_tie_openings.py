"""Lateral tie bodies must clear the permanent opening, even if a sole plate remains."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from typehaus.hardware.config import FT_TO_M, UpliftTieRules
from typehaus.hardware.connector_dimensions import LATERAL_TIE_PLATE_DIMENSIONS
from typehaus.joints.sills import tie_plate_stations
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedOpening
from typehaus.takeoff.uplift import lateral_tie_plate_rows


def _model_with_opening(*, center=4.0, sill=0.0, height=2.0, host="W", kind="door",
                        base=0.0, wall_bottom=None, depth=None):
    wall = SimpleNamespace(
        tag="W", storey="main", axis=((0.0, 0.0), (8.0, 0.0)),
        base_ref_z_m=base, z0_m=base if wall_bottom is None else wall_bottom,
        is_foundation=False, members=[SimpleNamespace(category="stud")])
    opening = ResolvedOpening(
        uid="O", tag="OPENING", host_wall=host, type_ref=None, width_m=1.0,
        height_m=height, sill_m=sill, center_along_m=center, kind=kind,
        is_door=kind == "door", depth_m=depth)
    return SimpleNamespace(
        walls=[wall], openings=[opening],
        stack_edges=[SimpleNamespace(lower_wall="LOWER", upper_wall="W")])


# An 8 m run needs four stations to respect a 12 ft maximum pitch.
RULES = UpliftTieRules(tie_plate_pitch_ft=12.0)


@pytest.mark.parametrize("kind", ["door", "window", "rough_opening"])
def test_floor_level_void_gets_ties_on_both_solid_segments(kind):
    model = _model_with_opening(kind=kind)
    stations = tie_plate_stations(model, RULES)
    half_width = LATERAL_TIE_PLATE_DIMENSIONS.width_in * M_PER_IN / 2
    assert [station.point_m[0] for station in stations] == pytest.approx(
        [0.0, 3.5 - half_width, 4.5 + half_width, 8.0])
    [row] = lateral_tie_plate_rows(model, RULES)
    assert row["count"] == 4
    assert row["by_storey"] == {"main": 4}


def test_the_plate_edge_cannot_project_into_a_doorway():
    # The candidate centre is outside the void, but its 3-inch body crosses the jamb.
    model = _model_with_opening(center=4.5 + M_PER_IN)
    stations = tie_plate_stations(model, RULES)
    assert len(stations) == 5
    half_width = LATERAL_TIE_PLATE_DIMENSIONS.width_in * M_PER_IN / 2
    assert all(abs(station.point_m[0] - model.openings[0].center_along_m)
               >= .5 + half_width - 1e-9 for station in stations)


@pytest.mark.parametrize("changes", [
    {"sill": 0.5},
    {"sill": -2.0, "height": 1.0},
    {"host": "OTHER"},
    {"depth": 0.02, "kind": "rough_opening"},
    {"base": 3.0, "wall_bottom": 2.0},
])
def test_openings_that_do_not_cross_the_body_leave_the_station(changes):
    assert len(tie_plate_stations(_model_with_opening(**changes), RULES)) == 4


def test_opening_elevation_uses_the_wall_floor_datum():
    assert len(tie_plate_stations(_model_with_opening(base=3.0), RULES)) == 4


def test_no_order_is_emitted_when_all_stations_are_in_voids():
    model = _model_with_opening()
    model.openings = [replace(model.openings[0], width_m=10.0)]
    assert tie_plate_stations(model, RULES) == []
    assert lateral_tie_plate_rows(model, RULES) == []


@pytest.mark.parametrize("centers", [[], [4.0], [2.0, 6.0], [3.8, 4.2]])
def test_solid_segments_respect_pitch_with_multiple_or_overlapping_openings(centers):
    model = _model_with_opening()
    model.openings = [_model_with_opening(center=center).openings[0] for center in centers]
    positions = sorted(station.point_m[0] for station in tie_plate_stations(model, RULES))
    half_width = LATERAL_TIE_PLATE_DIMENSIONS.width_in * M_PER_IN / 2
    for position in positions:
        assert all(abs(position - center) >= .5 + half_width - 1e-9 for center in centers)
    for left, right in zip(positions, positions[1:], strict=False):
        # A void can exceed the pitch; the continuous solid plate cannot.
        if not any(left < center < right for center in centers):
            assert right - left <= RULES.tie_plate_pitch_ft * FT_TO_M + 1e-9

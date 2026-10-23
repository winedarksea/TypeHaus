"""Lateral tie bodies must clear the permanent opening, even if a sole plate remains."""

from types import SimpleNamespace

import pytest

from typehaus.hardware.config import UpliftTieRules
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


# Three nominal stations, at 0, 4, and 8 metres.
RULES = UpliftTieRules(tie_plate_pitch_ft=12.0)


@pytest.mark.parametrize("kind", ["door", "window", "rough_opening"])
def test_floor_level_void_excludes_the_middle_tie(kind):
    model = _model_with_opening(kind=kind)
    stations = tie_plate_stations(model, RULES)
    assert [station.point_m for station in stations] == [(0.0, 0.0), (8.0, 0.0)]
    [row] = lateral_tie_plate_rows(model, RULES)
    assert row["count"] == 2
    assert row["by_storey"] == {"main": 2}


def test_the_plate_edge_cannot_project_into_a_doorway():
    # The candidate centre is outside the void, but its 3-inch body crosses the jamb.
    model = _model_with_opening(center=4.5 + M_PER_IN)
    assert len(tie_plate_stations(model, RULES)) == 2


@pytest.mark.parametrize("changes", [
    {"sill": 0.5},
    {"sill": -2.0, "height": 1.0},
    {"host": "OTHER"},
    {"depth": 0.02, "kind": "rough_opening"},
    {"base": 3.0, "wall_bottom": 2.0},
])
def test_openings_that_do_not_cross_the_body_leave_the_station(changes):
    assert len(tie_plate_stations(_model_with_opening(**changes), RULES)) == 3


def test_opening_elevation_uses_the_wall_floor_datum():
    assert len(tie_plate_stations(_model_with_opening(base=3.0), RULES)) == 2


def test_no_order_is_emitted_when_all_stations_are_in_voids():
    model = _model_with_opening()
    model.openings = [
        ResolvedOpening(uid=str(index), tag=str(index), host_wall="W", type_ref=None,
                        width_m=1.0, height_m=2.0, sill_m=0.0, center_along_m=center,
                        kind="door", is_door=True)
        for index, center in enumerate((0.0, 4.0, 8.0))
    ]
    assert tie_plate_stations(model, RULES) == []
    assert lateral_tie_plate_rows(model, RULES) == []

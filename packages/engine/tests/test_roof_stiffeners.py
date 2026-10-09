"""Bearing stiffener solids follow the rafter planes on either roof slope."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.roof_stiffeners import bearing_stiffeners
from typehaus.resolve.geometry_ir import GSweep
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.model import FramedMember


def _rafter(axis: tuple[float, float], slope: float) -> FramedMember:
    depth = inch(11.875).meters
    return FramedMember(
        "ROOF", "rafter-005", "rafter", "11.875 TJI 230", (2.0, 3.0),
        (2.0 + axis[0] * 4.0, 3.0 + axis[1] * 4.0), 6.0 - depth, 6.0,
        math.hypot(4.0, slope * 4.0),
        z0_end_m=6.0 - depth + slope * 4.0, z1_end_m=6.0 + slope * 4.0,
    )


@pytest.mark.parametrize("axis", [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0),
                                  (0.6, 0.8)])
@pytest.mark.parametrize("slope", [4 / 12, 6 / 12, -4 / 12, 0.0])
def test_stiffener_vertices_follow_the_rafter_planes(axis, slope):
    rafter = _rafter(axis, slope)
    stiffeners = bearing_stiffeners((rafter,), hung_at_ridge=True)
    assert {m.child_key for m in stiffeners} == {
        "rafter-005-eave-stiffener", "rafter-005-ridge-stiffener"}
    for stiffener in stiffeners:
        solid = member_solid(stiffener)
        assert isinstance(solid, GSweep)
        assert math.dist(stiffener.p0, stiffener.p1) == pytest.approx(inch(4).meters)
        assert stiffener.length_m == pytest.approx(inch(11.875).meters)
        assert stiffener.material == "struct-1-plywood"
        assert stiffener.plan_width_m == pytest.approx(inch(2 * 0.71875).meters)
        assert solid.extrude[2] == 0.0
        vertices = (*solid.profile, *(tuple(p + d for p, d in zip(point, solid.extrude,
                                                                  strict=True))
                                      for point in solid.profile))
        stations = []
        on_bottom, on_top = 0, 0
        for x, y, z in vertices:
            station = (x - rafter.p0[0]) * axis[0] + (y - rafter.p0[1]) * axis[1]
            across = -(x - rafter.p0[0]) * axis[1] + (y - rafter.p0[1]) * axis[0]
            bottom = rafter.z0_m + station * slope
            top = rafter.z1_m + station * slope
            on_bottom += z == pytest.approx(bottom)
            on_top += z == pytest.approx(top)
            assert abs(across) == pytest.approx(inch(0.71875).meters)
            stations.append(station)
        assert on_bottom == on_top == 4
        assert min(stations) >= -1e-9
        assert max(stations) <= 4.0 + 1e-9
        if stiffener.connection.startswith("eave:"):
            assert min(stations) == pytest.approx(0.0)
        else:
            assert max(stations) == pytest.approx(4.0)
        _, z_low, z_high = member_footprint(stiffener)
        assert z_low == pytest.approx(min(z for _, _, z in vertices))
        assert z_high == pytest.approx(max(z for _, _, z in vertices))


def test_only_hung_i_joists_get_ridge_stiffeners():
    rafter = _rafter((1.0, 0.0), 0.5)
    assert len(bearing_stiffeners((rafter,), hung_at_ridge=False)) == 1
    assert bearing_stiffeners((replace(rafter, profile="2x12"),), hung_at_ridge=True) == ()
    generic = replace(rafter, profile="11.875 I-joist")
    assert len(bearing_stiffeners((generic,), hung_at_ridge=True)) == 2


def test_level_member_without_end_elevations_stays_level():
    rafter = replace(_rafter((0.0, 1.0), 0.0), z0_end_m=None, z1_end_m=None)
    for stiffener in bearing_stiffeners((rafter,), hung_at_ridge=True):
        assert stiffener.z0_m == stiffener.z0_end_m == rafter.z0_m
        assert stiffener.z1_m == stiffener.z1_end_m == rafter.z1_m


def test_degenerate_rafter_has_no_drawable_stiffener():
    rafter = _rafter((1.0, 0.0), 0.5)
    assert bearing_stiffeners((replace(rafter, p1=rafter.p0),), hung_at_ridge=True) == ()

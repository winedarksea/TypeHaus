"""Stringer seats follow final tread substrates without filling their notches."""

import math
from dataclasses import replace

import pytest
from shapely.geometry import LineString, Polygon, box

from typehaus.model.spatial import Stair
from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.geometry_slice import sweep_mesh
from typehaus.resolve.stairs.bearing import _clip_stair_to_subfloor
from typehaus.resolve.stairs.finish import lower_stair_substrates
from typehaus.resolve.stairs.straight import _straight_stair_members
from typehaus.resolve.stairs.stringer_cuts import cut_stringer_profiles
from typehaus.resolve.stairs.u_split import _u_split_landing_members

# Overlay uses a one-micron grid, much tighter than the requested 0.01-inch tolerance.
_GEOMETRY_TOLERANCE_M = 2e-6


def _projected_overlap(stringer, board):
    footprint = Polygon(member_footprint(stringer)[0])
    overlap = footprint.intersection(Polygon(member_footprint(board)[0]))
    if overlap.area < 1e-12:
        return None
    run = math.dist(stringer.p0, stringer.p1)
    ux = (stringer.p1[0] - stringer.p0[0]) / run
    uy = (stringer.p1[1] - stringer.p0[1]) / run
    stations = [(x - stringer.p0[0]) * ux + (y - stringer.p0[1]) * uy
                for x, y in overlap.exterior.coords]
    return min(stations), max(stations)


def _assert_clearance(members):
    for stringer in (m for m in members if m.category == "stringer"):
        profile = Polygon(stringer.elevation_profile)
        assert profile.is_valid and profile.area > 0
        assert stringer.plan_width_m == pytest.approx(cross_section(stringer.profile).width_m)
        for board in (m for m in members if m.category in {"tread", "riser", "landing"}):
            overlap = _projected_overlap(stringer, board)
            if overlap is None or overlap[1] - overlap[0] < 2 * _GEOMETRY_TOLERANCE_M:
                continue
            start, end = overlap
            interior = box(start + _GEOMETRY_TOLERANCE_M,
                           board.z0_m + _GEOMETRY_TOLERANCE_M,
                           end - _GEOMETRY_TOLERANCE_M,
                           board.z1_m - _GEOMETRY_TOLERANCE_M)
            assert profile.intersection(interior).area < 1e-12, (
                stringer.child_key, board.child_key)
            if board.category == "tread":
                # Every tread has an actual horizontal bearing seat, not just clearance.
                station = (start + end) / 2
                section = profile.intersection(LineString(((station, profile.bounds[1] - 1),
                                                          (station, profile.bounds[3] + 1))))
                assert section.bounds[3] == pytest.approx(board.z0_m, abs=_GEOMETRY_TOLERANCE_M)


@pytest.mark.parametrize("axis", ["x", "y"])
@pytest.mark.parametrize("reversed_run", [False, True])
@pytest.mark.parametrize("layout", ["straight", "u_split_landing", "u_level_landing"])
@pytest.mark.parametrize("finish_m", [0, inch(0.5).meters])
@pytest.mark.parametrize("closed_risers", [False, True])
def test_seats_clear_treads_and_risers(axis, reversed_run, layout, finish_m, closed_risers):
    stair = Stair(uid="SR00000001", tag="S-1", floor_opening="FO-1", from_storey="main",
                  to_storey="second", width=inch(36), run_direction=axis,
                  run_reversed=reversed_run, layout=layout,
                  riser_thickness=inch(0.75) if closed_risers else None,
                  stringer_spacing=inch(18))
    args = (stair, 0, 0, 0, 9, inch(7).meters, inch(10).meters,
            inch(11).meters, inch(1).meters)
    if layout == "straight":
        members = _straight_stair_members(*args)
    else:
        members = _u_split_landing_members(*args, landing_depth_m=inch(36).meters,
                                           finish_m=finish_m)
    lowered = lower_stair_substrates(members, finish_m)
    clipped = _clip_stair_to_subfloor(lowered, 0)
    cut = cut_stringer_profiles(clipped, lowered, 0)
    _assert_clearance(cut)
    for before, after in zip(clipped, cut, strict=True):
        assert replace(after, elevation_profile=before.elevation_profile,
                       plan_width_m=before.plan_width_m) == before
        if after.category == "stringer":
            assert min(z for _, z in after.elevation_profile) >= -_GEOMETRY_TOLERANCE_M
            assert member_solid(after).extrude
            original = next(m for m in lowered if m.child_key == after.child_key)
            run = math.dist(after.p0, after.p1)
            profile = Polygon(after.elevation_profile)
            middle = profile.intersection(LineString(((run / 2, profile.bounds[1] - 1),
                                                       (run / 2, profile.bounds[3] + 1))))
            # The floor clips the original soffit; it must not tilt the whole rake.
            expected_soffit = max(0, (original.z0_m + original.z0_end_m) / 2)
            assert middle.bounds[1] == pytest.approx(expected_soffit,
                                                     abs=_GEOMETRY_TOLERANCE_M)


def test_catlin_stringers_follow_the_final_stair_boards(catlin_model_ro):
    for stair in catlin_model_ro.stairs:
        _assert_clearance(stair.members)
        for member in stair.members:
            if member.category == "stringer":
                assert len(member.elevation_profile) > 4
                assert sweep_mesh(member_solid(member)).triangles


def test_box_and_cast_carriages_have_no_stringer_cuts():
    for carriage in ("box", "cast"):
        stair = Stair(uid="SR00000001", tag="S-1", from_storey="main", to_storey="second",
                      width=inch(36), carriage=carriage)
        members = _straight_stair_members(stair, 0, 0, 0, 4, inch(7).meters,
                                          inch(10).meters, inch(11).meters, inch(1).meters)
        assert cut_stringer_profiles(members, members, 0) == members


def test_catlin_ifc_and_viewer_json_preserve_stringer_silhouettes(catlin_model_ro):
    pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import lowlevel as ll
    from typehaus.emit.ifc.roof import member_representation
    from typehaus.server.model_json_shared import _member_json

    file = ll.new_file("stringer cuts")
    ll.create_entity(file, "IfcProject", name="stringer cuts")
    body = ll.add_context(file)
    for stair in catlin_model_ro.stairs:
        for stringer in (m for m in stair.members if m.category == "stringer"):
            payload = _member_json(stringer)
            assert payload["elevation_profile"] == [list(p) for p in stringer.elevation_profile]
            assert payload["plan_width_m"] == stringer.plan_width_m
            representation = member_representation(file, body, stringer)
            item, = representation.Items
            assert item.is_a("IfcExtrudedAreaSolid")
            assert item.Depth == pytest.approx(stringer.plan_width_m)
            origin = item.Position.Location.Coordinates
            axis = item.Position.Axis.DirectionRatios
            x_axis = item.Position.RefDirection.DirectionRatios
            y_axis = (axis[1] * x_axis[2] - axis[2] * x_axis[1],
                      axis[2] * x_axis[0] - axis[0] * x_axis[2],
                      axis[0] * x_axis[1] - axis[1] * x_axis[0])
            run = math.dist(stringer.p0, stringer.p1)
            ux = (stringer.p1[0] - stringer.p0[0]) / run
            uy = (stringer.p1[1] - stringer.p0[1]) / run
            side = []
            for point in item.SweptArea.OuterCurve.Points:
                px, py = point.Coordinates
                x, y, z = (o + px * a + py * b
                           for o, a, b in zip(origin, x_axis, y_axis, strict=True))
                side.append(((x - stringer.p0[0]) * ux + (y - stringer.p0[1]) * uy, z))
            assert Polygon(side).symmetric_difference(
                Polygon(stringer.elevation_profile)).area < 1e-10

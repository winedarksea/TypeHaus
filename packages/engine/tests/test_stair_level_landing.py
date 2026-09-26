"""The main-to-second U turn is one level walking surface in the stacked well."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest
from shapely.geometry import Polygon

from typehaus.checks.code.mn_residential.stairs import stair_geometry
from typehaus.checks.structural.stairs import stair_riser_uniformity
from typehaus.emit.draw.stair_symbol import member_footprint
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.stairs.walkline import intermediate_step_elevations, stair_walk_stations


def _stair(model, tag):
    return next(stair for stair in model.stairs if stair.tag == tag)


def test_main_stair_has_two_equal_flights_and_one_level_turn(catlin_model_ro):
    stair = _stair(catlin_model_ro, "ST-M2S")
    assert stair.layout == "u_level_landing"
    assert stair.riser_count == 16
    assert stair.riser_height_m == pytest.approx(inch(7.5).meters)
    assert stair.going_depth_m == pytest.approx(inch(10).meters)
    members = {member.child_key: member for member in stair.members}
    for flight in ("lower", "upper"):
        assert len([key for key in members if key.startswith(f"tread-{flight}-")]) == 7
    lower, upper = members["landing-lower"], members["landing-upper"]
    assert lower.length_m == pytest.approx(inch(42.25).meters)
    assert upper.length_m == pytest.approx(lower.length_m)
    assert lower.z1_m == pytest.approx(inch(60.9862).meters)
    assert upper.z1_m == pytest.approx(lower.z1_m)
    assert lower.p0[1] == pytest.approx(upper.p0[1])
    assert lower.p1[1] == pytest.approx(upper.p1[1])
    well_wall = next(wall for wall in catlin_model_ro.walls if wall.tag == "W-M-WELL")
    assert max(point[1] for point in well_wall.axis) == pytest.approx(
        lower.p0[1] - inch(0.75).meters)
    assert Polygon(member_footprint(lower)).distance(Polygon(member_footprint(upper))) < 1e-9
    levels = intermediate_step_elevations(stair)
    assert len(levels) == 15
    assert levels == pytest.approx([stair.base_elevation_m + step * stair.riser_height_m
                                    for step in range(1, 16)])
    route = stair_walk_stations(stair)
    landing_stations = [station for station in route
                        if abs(station[2] - lower.z1_m) < 1e-9]
    # Four deck edges plus the lower flight's synthetic arrival at the landing edge.
    assert len(landing_stations) == 5
    assert [finding.result for finding in stair_geometry(
        SimpleNamespace(model=SimpleNamespace(stairs=[stair]), plan=catlin_model_ro.plan))] \
        == [Result.PASS]
    assert [finding.result for finding in stair_riser_uniformity(
        SimpleNamespace(model=SimpleNamespace(stairs=[stair])))] == [Result.PASS]


def test_level_landing_rejects_an_uneven_or_missing_half(catlin_model_ro):
    stair = _stair(catlin_model_ro, "ST-M2S")
    for members in (
        tuple(replace(member, z1_m=member.z1_m + inch(1).meters)
              if member.child_key == "landing-upper" else member for member in stair.members),
        tuple(member for member in stair.members if member.child_key != "landing-upper"),
    ):
        malformed = replace(stair, members=members)
        assert [finding.result for finding in stair_geometry(
            SimpleNamespace(model=SimpleNamespace(stairs=[malformed]),
                            plan=catlin_model_ro.plan))] == [Result.FAIL]


def test_basement_stair_clears_level_landing_framing(catlin_model_ro):
    basement = _stair(catlin_model_ro, "ST-B2M")
    upper = _stair(catlin_model_ro, "ST-M2S")
    overhead = [member for member in upper.members
                if member.child_key in {"landing-lower", "landing-upper"}
                or member.child_key.startswith(("landing-joist-", "landing-rim-"))]
    gaps = [above.z0_m - below.z1_m
            for below in basement.members if below.category in {"tread", "landing"}
            for above in overhead
            if Polygon(member_footprint(below)).intersects(
                Polygon(member_footprint(above))) and above.z0_m > below.z1_m]
    assert gaps, "the stacked stairs must overlap in plan for this clearance check to count"
    assert min(gaps) >= inch(80).meters

    # Landing supports must stay out of the basement stair's walking surfaces.
    posts = [member for member in upper.members
             if member.child_key.startswith("landing-post-")]
    for post in posts:
        post_footprint = Polygon(member_footprint(post))
        for walking_surface in (member for member in basement.members
                                if member.category in {"tread", "landing"}):
            if post.z0_m < walking_surface.z1_m and post.z1_m > walking_surface.z0_m:
                assert not post_footprint.intersects(
                    Polygon(member_footprint(walking_surface))), (
                        f"{post.child_key} obstructs {walking_surface.child_key}")


def test_basement_stair_keeps_its_split_turn(catlin_model_ro):
    stair = _stair(catlin_model_ro, "ST-B2M")
    decks = [member for member in stair.members if member.category == "landing"]
    assert stair.layout == "u_split_landing" and stair.riser_count == 15
    assert [sum(member.child_key.startswith(f"tread-{flight}-") for member in stair.members)
            for flight in ("lower", "upper")] == [6, 6]
    assert len(decks) == 2
    assert decks[1].z1_m - decks[0].z1_m == pytest.approx(stair.riser_height_m)

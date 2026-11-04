"""Surface bases bear on real surfaces and shared heads have one mounting assembly."""

import math
from dataclasses import replace
from types import SimpleNamespace

import pytest
from _railing_fixtures import railing, resolve_railings
from shapely.geometry import Point, Polygon

from typehaus.library.railings import RAILING_EXT_ALUMINUM_SURFACE as PRODUCT
from typehaus.model.surface_mount import SurfacePostMount
from typehaus.quantities import ft, inch, pt
from typehaus.takeoff.railings import railing_takeoff


@pytest.mark.parametrize("angle", [0, math.pi/2])
def test_short_unpicketed_bay_is_measured_between_its_drawn_posts(angle):
    from typehaus.checks.code.mn_residential.short_guard_openings import short_bay_opening_m

    guard = railing(type_ref=PRODUCT.tag, mount="surface", infill="balusters",
                    baluster_spacing=inch(4), path=(pt(inch(0), inch(0)),
                    pt(inch(7*math.cos(angle)), inch(7*math.sin(angle)))))
    model = resolve_railings([guard], types=[PRODUCT])
    assert not any(s.category == "railing_infill" for s in model.solids)
    ctx = SimpleNamespace(plan=model.plan, model=model)
    assert short_bay_opening_m(ctx, guard, inch(4).meters) == pytest.approx(inch(4).meters)
    model.solids = [s for s in model.solids if not s.tag.endswith("POST2")]
    assert short_bay_opening_m(ctx, guard, inch(4).meters) is None


def test_surface_bearings_must_match_stations_without_partial_geometry():
    guard = railing(type_ref=PRODUCT.tag, mount="surface", surface_post_mounts=(
        SurfacePostMount(elevation=ft(0), substrate="concrete"),))
    model = resolve_railings([guard], types=[PRODUCT])
    assert not model.solids
    assert [f.check_id for f in model.railing_findings] == ["geometry.railing_surface_layout"]


@pytest.mark.parametrize("angle", [0, math.pi/3, math.pi])
def test_surface_bases_rotate_and_use_authored_level_bearings(angle):
    bearing = SurfacePostMount(elevation=inch(-1), substrate="concrete")
    guard = railing(type_ref=PRODUCT.tag, mount="surface", post_spacing=ft(5),
                    path=(pt(ft(0), ft(0)), pt(ft(4*math.cos(angle)), ft(4*math.sin(angle)))),
                    surface_post_mounts=(bearing, bearing))
    model = resolve_railings([guard], types=[PRODUCT])
    assert not model.railing_findings
    bases = [s for s in model.solids if "-BASE" in s.tag]
    assert len(bases) == 2
    assert all(s.z0_m == pytest.approx(inch(-1).meters) and s.body_mesh for s in bases)
    assert all(s.z0_m == pytest.approx(inch(-1).meters)
               for s in model.solids if "-POST" in s.tag)


def test_porch_stair_bases_land_on_pad_treads_and_wall(catlin_model_ro):
    model = catlin_model_ro
    solids = {s.tag: s for s in model.solids}
    stair = next(s for s in model.stairs if s.tag == "ST-SG-PORCH")
    pad = solids["SL-SG-STAIRPAD"]
    wall = next(w for w in model.walls if w.tag == "W-SG-E1")
    from typehaus.resolve.wall_faces import wall_body

    wall_plan = wall_body(wall, wall.z0_m, wall.z1_m)
    for side in ("S", "N"):
        tag = f"RL-SG-PSTAIR-{side}"
        foot, middle = (solids[f"{tag}-BASE{i}"] for i in (1, 2))
        head = solids[f"RL-SG-PTHRESH-{side}-BASE2"]
        assert Polygon(pad.outline).covers(Polygon(foot.outline))
        assert foot.z0_m == pytest.approx(pad.z1_m)
        assert wall_plan.covers(Polygon(head.outline))
        assert head.z0_m == pytest.approx(wall.z1_m)
        guard = model.plan.by_tag(tag)
        from typehaus.resolve.railings.parts import resolve_parts
        bottom = solids[f"{tag}-RAIL2"].sweep
        x = sum(px for px, _ in head.outline)/len(head.outline) + inch(1.5).meters
        a, b = bottom.path[0], bottom.path[-1]
        z = a[2] + (b[2]-a[2])*(x-a[0])/(b[0]-a[0])
        clearance = z - resolve_parts(model, guard).rail_section_m/2
        clearance -= model.plan.by_tag(f"RL-SG-PTHRESH-{side}").base_elevation.meters
        assert 0 < clearance < inch(4).meters
        assert f"{tag}-BASE3" not in solids
        assert f"{tag}-POST3" not in solids
        tread = next(m for m in stair.members if m.child_key == "tread-002")
        assert middle.z0_m == pytest.approx(tread.z1_m + stair.finish_thickness_m)
        # A full base fits within the 11 inch tread, clear of both riser lines.
        xs = [x for x, _ in middle.outline]
        assert min(xs) > tread.p0[0]-inch(5.5).meters
        assert max(xs) < tread.p0[0]+inch(5.5).meters
        backing = solids[f"{tag}-BACKING2"]
        assert backing.z1_m == pytest.approx(middle.z0_m-inch(0.94).meters)
        anchor = solids[f"{tag}-ANCHORS2"]
        assert backing.z0_m < anchor.z0_m < backing.z1_m-inch(4).meters
        # The two shaft rows fall inside the backing, not into the stair cavity.
        centre_x = sum(x for x, _ in middle.outline)/len(middle.outline)
        centre_y = sum(y for _, y in middle.outline)/len(middle.outline)
        half_spacing = PRODUCT.surface_mount.display_hole_spacing.meters/2
        assert all(Polygon(backing.outline).contains(Point(centre_x+dx, centre_y+dy))
                   for dx in (-half_spacing, half_spacing)
                   for dy in (-half_spacing, half_spacing))
    handrail = model.plan.by_tag("RL-SG-PSTAIR-HR")
    tread_xs = [p[0] for m in stair.members if m.riser_line for p in m.riser_line]
    assert handrail.path[0].xy_m[0] > max(tread_xs)
    assert handrail.path[-1].xy_m[0] < min(tread_xs)
    without_mounts = replace(model, solids=[s for s in model.solids
        if not any(part in s.tag for part in ("-BASE", "-ANCHORS", "-BACKING"))])
    assert railing_takeoff(model) == railing_takeoff(without_mounts)

"""The added east window must leave buildable piers and accessible counter outlets."""

import pytest
from shapely.geometry import Polygon

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_millwork import window_stool_prism

INCH = 0.0254
EAST_WINDOW_CENTRES_IN = {
    "WIN-M-LIV-E1": 64,
    "WIN-M-LIV-E2": 144,
    "WIN-M-LIV-E3": 192,
    "WIN-M-EAST-MID": 240,
}
NORTH_COUNTER_RECEPTACLES = (
    "ED-M-LIVING-RC14", "ED-M-LIVING-RC3", "ED-M-LIVING-RC15", "ED-M-LIVING-RC16",
)


def test_matching_windows_leave_independent_jamb_packs_and_clear_the_pantry(catlin_model_ro):
    model = catlin_model_ro
    openings = {opening.tag: opening for opening in model.openings}
    wall = model.wall("W-M-E1")
    for tag, centre in EAST_WINDOW_CENTRES_IN.items():
        opening = openings[tag]
        assert opening.host_wall == wall.tag
        assert opening.type_ref == "WT-2748"
        assert opening.center_along_m == pytest.approx(centre * INCH)
        assert opening.width_m == pytest.approx(27 * INCH)
        assert opening.height_m == pytest.approx(48 * INCH)
        assert opening.sill_m == pytest.approx(34 * INCH)

    jamb_members = sorted(
        (member for member in wall.members if member.category in {"king", "jack"}
         and 127.5 * INCH < member.p0[1] < 260 * INCH),
        key=lambda member: member.p0[1],
    )
    assert len(jamb_members) == 12
    for south, north in zip(jamb_members, jamb_members[1:], strict=False):
        required_separation = (cross_section(south.profile).width_m
                               + cross_section(north.profile).width_m) / 2
        assert north.p0[1] - south.p0[1] >= required_separation - 1e-9

    objects = {obj.tag: obj for obj in model.canvas_objects}
    pantry_south = Polygon(objects["FURN-M-KIT-PANTRY-S2"].footprint).bounds[1]
    assert pantry_south == pytest.approx(271.375 * INCH)
    north_pack_end = jamb_members[-1].p0[1] + cross_section(jamb_members[-1].profile).width_m / 2
    assert pantry_south - north_pack_end == pytest.approx(14.875 * INCH)
    brick_north = max(point[1] for point in model.wall("W-M-FIRE-JAMB-N").axis)
    south_pack_start = jamb_members[0].p0[1] - cross_section(jamb_members[0].profile).width_m / 2
    assert south_pack_start - brick_north == pytest.approx(0.75 * INCH)
    assert objects["FURN-M-LIV-ROD-E2"].position[1] == pytest.approx(
        openings["WIN-M-LIV-E2"].center_along_m)


def test_each_live_edge_stool_meets_the_continuous_counter(catlin_model_ro):
    model = catlin_model_ro
    openings = {opening.tag: opening for opening in model.openings}
    stools = {stool.window_ref: stool for stool in model.window_stools}
    counter = next(top for top in model.countertops if top.tag == "CT-M-LIV-E-N")
    objects = {obj.tag: obj for obj in model.canvas_objects}
    counter_top = max(objects[tag].body_z1_m for tag in counter.hosts)
    for tag in EAST_WINDOW_CENTRES_IN:
        stool = stools[tag]
        assert not stool.derived
        assert stool.material_ref == counter.material_ref == "live-edge-white-oak"
        assert stool.thickness_m == pytest.approx(2 * INCH)
        assert stool.overhang_m == stool.horn_m == 0
        prism = window_stool_prism(model.wall(stool.wall_tag), openings[tag], stool)
        assert prism is not None
        # The frame rail and slab deliberately differ by less than 1/64".
        assert prism.z1_m == pytest.approx(counter_top, abs=INCH / 64)


def test_counter_devices_clear_windows_framing_and_each_other(catlin_model_ro):
    model = catlin_model_ro
    objects = {obj.tag: obj for obj in model.canvas_objects}
    windows = [opening for opening in model.openings if opening.tag in EAST_WINDOW_CENTRES_IN]
    devices = [objects[tag] for tag in (*NORTH_COUNTER_RECEPTACLES, "ED-M-DINING-FH-STAT")]
    east_wall = model.wall("W-M-E1")
    for device in devices:
        _, device_south, _, device_north = Polygon(device.footprint).bounds
        for window in windows:
            opening_south = window.center_along_m - window.width_m / 2
            opening_north = window.center_along_m + window.width_m / 2
            assert device_north <= opening_south or device_south >= opening_north, device.tag
        if device.attachment_wall != east_wall.tag:
            host = model.wall(device.attachment_wall)
            assert host.tag == "W-M-FIRE-JAMB-N"
            assert min(point[1] for point in host.axis) <= device_south
            assert device_north <= max(point[1] for point in host.axis)
            assert host.z0_m <= device.body_z0_m < device.body_z1_m <= host.z1_m
            continue
        for member in east_wall.members:
            if member.category not in {"stud", "king", "jack"}:
                continue
            if member.z1_m <= device.body_z0_m or member.z0_m >= device.body_z1_m:
                continue
            half_thickness = cross_section(member.profile).width_m / 2
            assert (
                device_north <= member.p0[1] - half_thickness
                or device_south >= member.p0[1] + half_thickness
            ), (device.tag, member.child_key)
    thermostat, receptacle = objects["ED-M-DINING-FH-STAT"], objects["ED-M-LIVING-RC3"]
    assert thermostat.body_z0_m > receptacle.body_z1_m
    pantry_south = Polygon(objects["FURN-M-KIT-PANTRY-S2"].footprint).bounds[1]
    assert Polygon(objects["ED-M-LIVING-RC16"].footprint).bounds[3] < pantry_south


def test_receptacles_cover_the_whole_north_counter(catlin_model_ro):
    objects = {obj.tag: obj for obj in catlin_model_ro.canvas_objects}
    counter = next(top for top in catlin_model_ro.countertops if top.tag == "CT-M-LIV-E-N")
    west, south, east, north = Polygon(counter.outline).bounds
    receptacles = [objects[tag] for tag in NORTH_COUNTER_RECEPTACLES]
    assert all(west < obj.position[0] < east for obj in receptacles)
    stations = sorted(obj.position[1] for obj in receptacles)
    midpoints = [(a + b) / 2 for a, b in zip(stations, stations[1:], strict=False)]
    coverage_samples = [south, north, *midpoints]
    for sample in coverage_samples:
        if south <= sample <= north:
            assert min(abs(sample - station) for station in stations) <= 24 * INCH + 1e-9

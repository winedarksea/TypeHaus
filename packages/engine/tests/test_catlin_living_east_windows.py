"""The living east row (2026-10-16): E1/E2 flank the brick, one picture window on the table.

Every window must leave buildable jamb packs and accessible outlets. Since 2026-10-20 only the
dining window's stool meets the counter; E1/E2 sit over open wall with the standard stool.
"""

import pytest
from shapely.geometry import Polygon

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_millwork import window_stool_prism

INCH = 0.0254
# E2's two packs and the dining window's two, one jack and one king each.
JAMB_MEMBERS_NORTH_OF_BRICK = 8
PACK_TO_PANTRY_IN = 20.875
# tag: (centre, width, type, blind, blind type)
EAST_WINDOWS = {
    "WIN-M-LIV-E1": (48, 27, "WT-2748-TT", "FURN-M-LIV-BLIND-E1", "FT-CELLULAR-BLIND-2748"),
    "WIN-M-LIV-E2": (128, 27, "WT-2748-TT", "FURN-M-LIV-BLIND-E2", "FT-CELLULAR-BLIND-2748"),
    "WIN-M-DINING-E": (216, 63, "WT-6348-FIX", "FURN-M-LIV-BLIND-DINING",
                       "FT-CELLULAR-BLIND-6348"),
}
NORTH_COUNTER_RECEPTACLES = ("ED-M-LIVING-RC15", "ED-M-LIVING-RC16")
# South of the slat partition: wall space at the room's 16".
WALL_RECEPTACLES = ("ED-M-LIVING-RC13", "ED-M-LIVING-RC3")


def test_matching_windows_leave_independent_jamb_packs_and_clear_the_pantry(catlin_model_ro):
    model = catlin_model_ro
    openings = {opening.tag: opening for opening in model.openings}
    wall = model.wall("W-M-E1")
    for tag, (centre, width, type_ref, _, _) in EAST_WINDOWS.items():
        opening = openings[tag]
        assert opening.host_wall == wall.tag
        assert opening.type_ref == type_ref
        assert opening.center_along_m == pytest.approx(centre * INCH)
        assert opening.width_m == pytest.approx(width * INCH)
        assert opening.height_m == pytest.approx(48 * INCH)
        assert opening.sill_m == pytest.approx(34 * INCH)

    jamb_members = sorted(
        (member for member in wall.members if member.category in {"king", "jack"}
         and 110.75 * INCH < member.p0[1] < 260 * INCH),
        key=lambda member: member.p0[1],
    )
    assert len(jamb_members) == JAMB_MEMBERS_NORTH_OF_BRICK
    for south, north in zip(jamb_members, jamb_members[1:], strict=False):
        required_separation = (cross_section(south.profile).width_m
                               + cross_section(north.profile).width_m) / 2
        assert north.p0[1] - south.p0[1] >= required_separation - 1e-9

    objects = {obj.tag: obj for obj in model.canvas_objects}
    pantry_south = Polygon(objects["FURN-M-KIT-PANTRY-S2"].footprint).bounds[1]
    assert pantry_south == pytest.approx(271.375 * INCH)
    north_pack_end = jamb_members[-1].p0[1] + cross_section(jamb_members[-1].profile).width_m / 2
    assert pantry_south - north_pack_end == pytest.approx(PACK_TO_PANTRY_IN * INCH)
    brick_north = max(point[1] for point in model.wall("W-M-FIRE-JAMB-N").axis)
    south_pack_start = jamb_members[0].p0[1] - cross_section(jamb_members[0].profile).width_m / 2
    assert south_pack_start - brick_north == pytest.approx(0.75 * INCH)
    for window_tag, (_, _, _, blind_tag, blind_type) in EAST_WINDOWS.items():
        blind = objects[blind_tag]
        opening = openings[window_tag]
        assert blind.type_ref == blind_type
        assert blind.position[1] == pytest.approx(opening.center_along_m)
        assert blind.body_z0_m == pytest.approx(34 * INCH)
        assert blind.body_z1_m == pytest.approx(82 * INCH)


def test_the_dining_stool_meets_the_counter(catlin_model_ro):
    model = catlin_model_ro
    openings = {opening.tag: opening for opening in model.openings}
    stools = {stool.window_ref: stool for stool in model.window_stools}
    counter = next(top for top in model.countertops if top.tag == "CT-M-LIV-E-N")
    objects = {obj.tag: obj for obj in model.canvas_objects}
    counter_top = max(objects[tag].body_z1_m for tag in counter.hosts)
    stool = stools["WIN-M-DINING-E"]
    assert not stool.derived
    # 1 1/4" ash meeting the 1 1/4" ash slab's back edge in one plane.
    assert stool.material_ref == "ash-stool-6q"
    assert counter.material_ref == "ash-counter-6q"
    assert stool.thickness_m == pytest.approx(1.25 * INCH)
    assert counter.thickness_m == pytest.approx(1.25 * INCH)
    assert stool.overhang_m == stool.horn_m == 0
    prism = window_stool_prism(model.wall(stool.wall_tag), openings["WIN-M-DINING-E"], stool)
    assert prism is not None
    # The frame rail and slab deliberately differ by less than 1/64".
    assert prism.z1_m == pytest.approx(counter_top, abs=INCH / 64)


def test_the_brick_flanking_stools_take_the_house_standard(catlin_model_ro):
    stools = {stool.window_ref: stool for stool in catlin_model_ro.window_stools}
    for tag in ("WIN-M-LIV-E1", "WIN-M-LIV-E2"):
        stool = stools[tag]
        assert not stool.derived
        assert stool.material_ref == "ash-stool-6q"
        assert stool.thickness_m == pytest.approx(1.25 * INCH)
        assert stool.overhang_m == pytest.approx(0.75 * INCH)
        assert stool.horn_m == pytest.approx(1 * INCH)


def test_counter_devices_clear_windows_framing_and_each_other(catlin_model_ro):
    model = catlin_model_ro
    objects = {obj.tag: obj for obj in model.canvas_objects}
    windows = [opening for opening in model.openings if opening.tag in EAST_WINDOWS]
    devices = [objects[tag] for tag in (*NORTH_COUNTER_RECEPTACLES, *WALL_RECEPTACLES,
                                        "ED-M-DINING-FH-STAT")]
    east_wall = model.wall("W-M-E1")
    for device in devices:
        _, device_south, _, device_north = Polygon(device.footprint).bounds
        for window in windows:
            opening_south = window.center_along_m - window.width_m / 2
            opening_north = window.center_along_m + window.width_m / 2
            assert device_north <= opening_south or device_south >= opening_north, device.tag
        assert device.attachment_wall == east_wall.tag, device.tag
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
    # Wall space at 16", 26" under the counter devices' 42".
    counter_z = objects["ED-M-LIVING-RC15"].body_z0_m
    for tag in WALL_RECEPTACLES:
        assert counter_z - objects[tag].body_z0_m == pytest.approx(26 * INCH)
    assert "ED-M-LIVING-RC14" not in objects and "ED-M-LIVING-RC17" not in objects
    pantry_south = Polygon(objects["FURN-M-KIT-PANTRY-S2"].footprint).bounds[1]
    assert Polygon(objects["ED-M-LIVING-RC16"].footprint).bounds[3] < pantry_south


def test_receptacles_cover_the_north_counter_outside_the_dining_glass(catlin_model_ro):
    """WIN-M-DINING-E's glass took RC15's old station (2026-10-16). The slab under the glass
    is the one stretch past 24" of a receptacle, and it is an open decision, not an oversight."""
    objects = {obj.tag: obj for obj in catlin_model_ro.canvas_objects}
    openings = {opening.tag: opening for opening in catlin_model_ro.openings}
    counter = next(top for top in catlin_model_ro.countertops if top.tag == "CT-M-LIV-E-N")
    west, south, east, north = Polygon(counter.outline).bounds
    receptacles = [objects[tag] for tag in NORTH_COUNTER_RECEPTACLES]
    assert all(west < obj.position[0] < east for obj in receptacles)
    stations = sorted(obj.position[1] for obj in receptacles)
    dining = openings["WIN-M-DINING-E"]
    glass = (dining.center_along_m - dining.width_m / 2, dining.center_along_m + dining.width_m / 2)
    samples = [south + i * INCH for i in range(int((north - south) / INCH) + 1)]
    uncovered = [y for y in samples
                 if min(abs(y - station) for station in stations) > 24 * INCH + 1e-9]
    assert uncovered, "the dining-glass gap closed: drop this exemption"
    assert all(glass[0] <= y <= glass[1] for y in uncovered)

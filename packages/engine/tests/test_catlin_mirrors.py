"""Selected glass/light assemblies fit their hosts, controls, backing and ceiling."""

from __future__ import annotations

import math

import pytest
from shapely.geometry import Polygon

from typehaus.model import DeviceKind
from typehaus.model.placeable_symbols import model_parts

IN = 0.0254
MIRRORS = {
    "FURN-B-BATH-MIRROR": ("FT-MIRROR-KOHLER-26052-BNL", "FX-B-BATH-LAV", 40),
    "FURN-M-BATH1-MIRROR": ("FT-MIRROR-KOHLER-30638-CPL", "FX-M-BATH1-LAV", 42),
    "FURN-S-BATH1-MIRROR": ("FT-MIRROR-KOHLER-26050-BNL", "FX-S-BATH1-LAV", 44),
    "FURN-S-VANITY-MIRROR1": ("FT-MIRROR-KOHLER-30638-BNL", "FX-S-VANITY-LAV1", 42),
    "FURN-S-VANITY-MIRROR2": ("FT-MIRROR-KOHLER-30638-BNL", "FX-S-VANITY-LAV2", 42),
    "FURN-A-STUBATH-MIRROR": ("FT-MIRROR-KOHLER-31367-BNL", "FX-A-STUBATH-LAV", 48),
    "FURN-M-CLOSET-MIRROR": ("FT-MIRROR-UMBRA-HUBBA-PILL", None, 12),
    "FURN-S-SUITEBATH-MIRROR": ("FT-SUITEBATH-MIRROR-ESTERO", None, 46),
}


def _horizontal_coordinate(item, axis):
    return sum(value * direction for value, direction in zip(item.position, axis, strict=True))


def test_all_nine_mirrors_have_products_and_only_bath2_consumes_power(catlin_plan):
    types = {t.tag: t for t in catlin_plan.library.furniture_types}
    products = {p.tag: p for p in catlin_plan.library.products}
    elements = {e.tag: e for s in catlin_plan.storeys for e in catlin_plan.storey_elements(s.tag)}
    for tag, (type_ref, _, bottom) in MIRRORS.items():
        mirror = elements[tag]
        assert mirror.type_ref == type_ref
        assert mirror.mount.elevation.meters == pytest.approx(bottom * IN)
        assert products[types[type_ref].product_ref].model
        assert not types[type_ref].ports
    powered_glass = [e.tag for e in elements.values()
                     if getattr(e, "kind", None) == DeviceKind.LIGHT
                     and "MIRROR" in e.tag
                     and "HALO" in e.tag]
    assert powered_glass == ["ED-M-BATH2-MIRROR-HALO"]
    electrical_types = {t.tag: t for t in catlin_plan.library.electrical_device_types}
    assert not {"ED-T-LT-MIRROR-RING", "ED-T-LT-MIRROR-CLOSET"} & electrical_types.keys()
    assert "ED-M-CLOSET-MIRROR" not in elements
    assert elements["FURN-M-CLOSET-MIRROR"].uid == "4JFYZ9V9P7"
    assert elements["ED-S-BATH1-MIRROR"].uid == "QTS000KAAA"
    assert products[types["FT-SUITEBATH-MIRROR-ESTERO"].product_ref].model


def test_mirror_and_light_centrelines_follow_the_basins_with_two_inches_between(catlin_model_ro):
    objects = {o.tag: o for o in catlin_model_ro.canvas_objects}
    for tag, (_, basin_tag, _) in MIRRORS.items():
        if basin_tag is None:
            continue
        mirror = objects[tag]
        basin = objects[basin_tag]
        light = objects[tag.replace("FURN-", "ED-", 1)]
        angle = math.radians(mirror.rotation_degrees)
        axis = math.cos(angle), math.sin(angle)
        centre = _horizontal_coordinate(mirror, axis)
        assert _horizontal_coordinate(basin, axis) == pytest.approx(centre)
        assert _horizontal_coordinate(light, axis) == pytest.approx(centre)
        assert light.body_z0_m - mirror.body_z1_m == pytest.approx(2 * IN)
    halo, task = objects["ED-M-BATH2-MIRROR-HALO"], objects["ED-M-BATH2-MIRROR"]
    assert task.position[1] == pytest.approx(halo.position[1])
    assert task.body_z0_m - halo.body_z1_m == pytest.approx(2 * IN)


def test_bath2_uses_full_line_voltage_and_its_integral_controls(catlin_plan):
    elements = {e.tag: e for e in catlin_plan.storey_elements("main")}
    types = {t.tag: t for t in catlin_plan.library.electrical_device_types}
    circuits = {c.tag: c for c in catlin_plan.library.circuits}
    halo = elements["ED-M-BATH2-MIRROR-HALO"]
    plug = elements["ED-M-BATH2-MIRROR-PLUG"]
    halo_type = types[halo.type_ref]
    assert halo.controlled_by == plug.controlled_by == ()
    assert halo.circuit == plug.circuit
    assert circuits[plug.circuit].gfci
    assert halo_type.integral_switch and halo_type.dimmable
    assert halo_type.watts == halo_type.load_va == 116
    assert halo_type.cri is None
    assert halo_type.product_ref == "PROD-FLEURCO-MHAP4236"
    assert elements["ED-M-BATH2-MIRROR"].controlled_by == ("ED-M-BATH2-SW-DAY",)
    assert elements["ED-M-BATH2-CAN-SH-EVE"].controlled_by == ("ED-M-BATH2-SW-EVE",)
    for tag in ("ED-T-LT-KARLIE-2-BN", "ED-T-LT-KARLIE-2-CM",
                "ED-T-LT-KARLIE-3-BN", "ED-T-LT-MIRROR-DAY"):
        light = types[tag]
        assert light.lumens is None  # Bulb output is not delivered luminaire output.
        assert "E26" in light.lamp and "replaceable" in light.lamp
    assert types["ED-T-LT-MIRROR-DAY"].cri == 95
    assert "R9 82" in types["ED-T-LT-MIRROR-DAY"].source


def test_mirror_glass_does_not_cover_switches_or_receptacle_plates(catlin_model_ro):
    model = catlin_model_ro
    objects = {o.tag: o for o in model.canvas_objects}
    room_mirrors = [objects[tag] for tag in MIRRORS]
    room_mirrors.append(objects["ED-M-BATH2-MIRROR-HALO"])
    for glass in room_mirrors:
        angle = math.radians(glass.rotation_degrees)
        axis = math.cos(angle), math.sin(angle)
        span = [sum(p[i] * axis[i] for i in (0, 1)) for p in glass.footprint]
        for device in model.canvas_objects:
            if device.room != glass.room or device.attachment_wall != glass.attachment_wall:
                continue
            if device.kind not in {"switch", "receptacle", "gfci"} or device.tag.endswith("MIRROR-PLUG"):
                continue
            device_span = [sum(p[i] * axis[i] for i in (0, 1)) for p in device.footprint]
            overlap_width = min(max(span), max(device_span)) - max(min(span), min(device_span))
            overlap_height = min(glass.body_z1_m, device.body_z1_m) - max(glass.body_z0_m, device.body_z0_m)
            assert overlap_width <= 0 or overlap_height <= 0, (glass.tag, device.tag)
    assert objects["ED-S-VANITY-SW"].position[0] / IN == pytest.approx(37.375)
    assert objects["ED-S-VANITY-RC1"].position[0] / IN == pytest.approx(65.5)
    assert Polygon(objects["ED-M-BATH2-MIRROR-PLUG"].footprint).intersects(
        Polygon(objects["ED-M-BATH2-MIRROR-HALO"].footprint))


def test_actual_mounting_rails_and_boxes_have_backing(catlin_plan):
    elements = [e for s in catlin_plan.storeys for e in catlin_plan.storey_elements(s.tag)]
    backing = {e.tag: e for e in elements if e.element_kind == "WallBacking"}
    # K-30638's rail is 9 3/16 in. below the peak, rather than near the arch's top.
    for tag in ("BK-M-HS1-MIRROR-HANG", "BK-S-BD-N-MIRROR-HANG"):
        band = backing[tag]
        assert band.elevation.meters < (74 - 9.1875) * IN
        assert band.elevation.meters + band.height.meters > (74 - 9.1875 + 2) * IN
    for tag in ("BK-B-CW2-MIRROR-LIGHT", "BK-M-HS1-MIRROR-LIGHT",
                "BK-S-BD-N-MIRROR-LIGHT", "BK-S-BA-E1B-MIRROR-LIGHT",
                "BK-S-SN3-MIRROR-LIGHT"):
        assert tag in backing


def test_attic_and_basement_lights_clear_the_low_overhead_surfaces(catlin_model_ro):
    model = catlin_model_ro
    objects = {o.tag: o for o in model.canvas_objects}
    attic = objects["ED-A-STUBATH-MIRROR"]
    # Current 6:12 finished roof: 1.5 in. at x=0, 7 ft at x=13 ft 9 in.
    roof_low = min(1.5 + x / IN / 2 for x, _ in attic.footprint)
    assert roof_low - (attic.mount.elevation.meters / IN + 7.5) >= 0.9
    basement = objects["ED-B-BATH-MIRROR"]
    room = next(r for r in model.rooms if r.tag == "RM-B-BATH")
    assert basement.mount.elevation.meters + (7.5 + 1) * IN < room.clear_height_m


@pytest.mark.parametrize("shape", ["arch", "soft-rectangle", "capsule"])
def test_plain_mirror_mesh_has_exposed_glass_and_no_electronics(shape):
    parts = model_parts(f"plain-{shape}-mirror-nickel", 0.5, 0.035, 0.8)
    assert len(parts) == 2
    assert [p["color"] for p in parts] == ["brushed-nickel" if shape != "capsule" else "metal", "mirror"]
    assert parts[1]["center"][1] < parts[0]["center"][1]
    assert all(p["shape"] == "mesh" for p in parts)
    assert parts[1]["size"][0] < parts[0]["size"][0]


def test_mirror_support_bands_are_actually_emitted_under_the_roof(catlin_model_ro):
    from typehaus.resolve.framing.backing_panels import backing_bands

    model = catlin_model_ro
    for wall in model.walls:
        bands = sorted(backing_bands(model.plan).get(wall.tag, ()),
                       key=lambda band: (band.elevation_m, band.tag))
        for index, band in enumerate(bands):
            if "MIRROR" not in band.tag:
                continue
            assert any(m.child_key.startswith(f"backing-{index}-") for m in wall.members), band.tag
    light = next(o for o in model.canvas_objects if o.tag == "ED-A-STUBATH-MIRROR")
    kind = next(t for t in model.plan.library.electrical_device_types if t.tag == light.type_ref)
    angle = math.radians(light.rotation_degrees)
    box_x = light.position[0] + math.cos(angle) * kind.ports[0].position[0].meters
    assert box_x / IN == pytest.approx(165.25)
    # A 4-in. side-fixed box bears directly on the 168-in. stud's west face.
    assert box_x / IN + 2 == pytest.approx(168 - 0.75)
    assert abs(box_x - light.position[0]) + 2 * IN < 7.25 * IN / 2


def test_panel_counts_the_halo_load_once_on_its_plug_branch(catlin_model_ro):
    from typehaus.takeoff.electrical import panel_schedule

    row = next(row for row in panel_schedule(catlin_model_ro)
               if row["circuit"] == "CKT-BATH-ATTIC")
    assert row["connected_va"] == 116
    assert {"ED-M-BATH2-MIRROR-HALO", "ED-M-BATH2-MIRROR-PLUG"} <= set(row["devices"])

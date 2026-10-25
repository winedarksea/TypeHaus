"""Wall-hosted placeables: the model contract, the resolver, the checks and write-back."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest
from _helpers import STARTER, copy_house
from shapely.geometry import Polygon

from typehaus.checks.integrity.wall_mounts import wall_mount_on_face
from typehaus.model import (
    DeviceKind,
    ElectricalDevice,
    Location,
    Mount,
    MountKind,
    WallAttachment,
    inch,
    pt,
)
from typehaus.resolve import resolve
from typehaus.resolve.placeables import placed_xy
from typehaus.source import load_plan, macros
from typehaus.source.coordinator import ProjectCoordinator

_HOSTED = Location(attachment=WallAttachment(wall_ref="W-1", face="left",
                                             distance_from_start=inch(12)))


def test_a_placeable_has_exactly_one_of_position_or_attachment() -> None:
    wall = Mount(kind=MountKind.WALL, elevation=inch(48))
    ElectricalDevice(tag="ED-1", kind=DeviceKind.SWITCH, mount=wall, location=_HOSTED)
    ElectricalDevice(tag="ED-2", kind=DeviceKind.SWITCH, mount=wall, position=pt(0, 0))
    with pytest.raises(ValueError, match="not both"):
        ElectricalDevice(tag="ED-3", kind=DeviceKind.SWITCH, mount=wall,
                         position=pt(0, 0), location=_HOSTED)
    with pytest.raises(ValueError, match="needs a `position`"):
        ElectricalDevice(tag="ED-4", kind=DeviceKind.SWITCH, mount=wall)


def _face_distance(model, device_tag: str, wall_tag: str) -> tuple[float, float]:
    """(|normal offset| of the wall's finish face, of the body's wallward edge)."""
    wall = model.wall(wall_tag)
    obj = next(o for o in model.canvas_objects if o.tag == device_tag)
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / length, (x1 - x0) / length
    side = 1 if (obj.position[0] - x0) * nx + (obj.position[1] - y0) * ny > 0 else -1
    face = max(side * ((p[0] - x0) * nx + (p[1] - y0) * ny)
               for layer in wall.layers for p in layer.polygon)
    edge = min(side * ((p[0] - x0) * nx + (p[1] - y0) * ny) for p in obj.footprint)
    return face, edge


def test_a_wall_retype_carries_its_hosted_device(catlin_plan) -> None:
    """The regression Phase 8 exists for: a thinner wall must not leave a switch floating."""
    tag, wall_tag = "ED-B-WORKSHOP-SW", "W-B-HALL-W"
    before, _ = resolve(catlin_plan)
    storey = next(s for s in catlin_plan.elements
                  if any(e.tag == wall_tag for e in catlin_plan.storey_elements(s)))
    elements = tuple(e.model_copy(update={"assembly": "INT_2X4_PARTITION"})
                     if e.tag == wall_tag else e
                     for e in catlin_plan.storey_elements(storey))
    after, _ = resolve(catlin_plan.model_copy(
        update={"elements": {**catlin_plan.elements, storey: elements}}))
    face_0, edge_0 = _face_distance(before, tag, wall_tag)
    face_1, edge_1 = _face_distance(after, tag, wall_tag)
    assert face_1 < face_0 - 0.02, "the retype should move the finish face"
    assert edge_0 == pytest.approx(face_0, abs=1e-6)
    assert edge_1 == pytest.approx(face_1, abs=1e-6), "the device must follow its face"
    ctx = SimpleNamespace(model=after, plan=after.plan)
    assert not [f for f in wall_mount_on_face(ctx) if tag in f.element_tags]


def test_on_face_fails_a_buried_body(catlin_plan) -> None:
    model, _ = resolve(catlin_plan)
    index = next(i for i, o in enumerate(model.canvas_objects) if o.tag == "ED-B-WORKSHOP-SW")
    obj = model.canvas_objects[index]
    body = Polygon(obj.footprint)
    # Push the body 2" toward its wall's axis.
    wall = model.wall(obj.attachment_wall)
    cx, cy = Polygon(wall.layers[0].polygon).centroid.coords[0]
    dx, dy = cx - obj.position[0], cy - obj.position[1]
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / length, (x1 - x0) / length
    step = inch(2).meters * (1 if dx * nx + dy * ny > 0 else -1)
    moved = [(x + nx * step, y + ny * step) for x, y in body.exterior.coords[:-1]]
    from dataclasses import replace
    model.canvas_objects[index] = replace(obj, footprint=moved)
    findings = wall_mount_on_face(SimpleNamespace(model=model, plan=model.plan))
    assert any("ED-B-WORKSHOP-SW is buried" in f.message for f in findings)


def test_placed_xy_reads_the_resolved_centre(catlin_plan) -> None:
    model, _ = resolve(catlin_plan)
    element = catlin_plan.by_tag("ED-B-WORKSHOP-SW")
    assert element.position is None
    obj = next(o for o in model.canvas_objects if o.tag == element.tag)
    assert placed_xy(model, element) == obj.position


def test_attach_slide_detach_round_trip_through_write_back(tmp_path) -> None:
    """The server's write-back path, not a browser: every step reloads as valid source."""
    house = copy_house(STARTER, tmp_path / "starter")
    coordinator = ProjectCoordinator(house)
    plan = load_plan(house).plan
    tag = "ED-Main-SW1"
    storey = next(s for s in plan.elements if plan.by_tag(tag) in plan.storey_elements(s))

    slid = macros.slide_placeable(plan, storey, tag=tag, distance=inch(60).meters)
    coordinator.apply_patch(slid.ops, coordinator.revision())
    plan = load_plan(house).plan
    item = plan.by_tag(tag)
    assert item.position is None
    assert item.location.attachment.distance_from_start.meters == pytest.approx(
        inch(60).meters, abs=1e-4)

    with pytest.raises(macros.MacroError, match="needs a position"):
        macros.detach_placeable(plan, storey, tag=tag)
    detached = macros.detach_placeable(plan, storey, tag=tag, position=(1.0, 1.0))
    coordinator.apply_patch(detached.ops, coordinator.revision())
    plan = load_plan(house).plan
    item = plan.by_tag(tag)
    assert item.location is None and item.position.xy_m == pytest.approx((1.0, 1.0))

    attached = macros.attach_placeable(plan, storey, tag=tag, wall="W-101", face="left",
                                       distance=1.5)
    coordinator.apply_patch(attached.ops, coordinator.revision())
    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    item = result.plan.by_tag(tag)
    assert item.position is None and item.location.attachment.wall_ref == "W-101"


def test_playroom_tv_uses_a_thin_wall_panel_seated_on_the_host(catlin_model_ro):
    tv = next(item for item in catlin_model_ro.canvas_objects if item.tag == "FURN-B-PLAY-TV")
    assert tv.type_ref == "FURN-TV-98-WALL"
    face, edge = _face_distance(catlin_model_ro, tv.tag, "W-B-N1")
    assert edge == pytest.approx(face, abs=1e-9)


def test_wall_lights_face_away_from_their_host_in_both_symbol_frames(catlin_model_ro):
    from typehaus.model.placeable_symbols import model_parts, place_local, plan_symbol_strokes

    types = {product.tag: product for product in
             catlin_model_ro.plan.library.electrical_device_types}
    checked = set()
    for item in catlin_model_ro.canvas_objects:
        product = types.get(item.type_ref)
        symbol = getattr(product, "plan_symbol", None)
        if not item.attachment_wall or not symbol or not (
            symbol.startswith("sconce") or "mirror-light" in symbol
        ):
            continue
        wall = catlin_model_ro.wall(item.attachment_wall)
        (x0, y0), (x1, y1) = wall.axis
        length = math.hypot(x1 - x0, y1 - y0)
        side = 1 if item.attachment_face == "left" else -1
        outward = (-side * (y1 - y0) / length, side * (x1 - x0) / length)
        back = place_local([(0, 1)], (0, 0), item.rotation_degrees)[0]
        assert sum(a * b for a, b in zip(back, outward, strict=True)) == pytest.approx(-1), (
            f"{item.tag}: symbol back faces away from its wall")
        if item.tag == "ED-M-ENTRY-LT":
            width, depth = (dimension.meters for dimension in product.footprint)
            strokes = plan_symbol_strokes(symbol, width, depth)
            parts = model_parts(symbol, width, depth, product.height.meters)
            # The plan backplate and 3D housing must both sit wallward of their light face.
            plan_plate_y = sum(y for _, y in strokes[0]["points"]) / len(strokes[0]["points"])
            plan_throw_y = min(y for _, y in strokes[-1]["points"])
            for rear_y, front_y in [(plan_plate_y, plan_throw_y),
                                    (parts[0]["center"][1], parts[-1]["center"][1])]:
                rear, front = place_local([(0, rear_y), (0, front_y)], item.position,
                                          item.rotation_degrees)
                assert sum((f - r) * n for r, f, n in zip(rear, front, outward, strict=True)) > 0
        checked.add(item.tag)
    assert {"ED-M-ENTRY-LT", "ED-A-STUDIO-BAR-TASK"} <= checked

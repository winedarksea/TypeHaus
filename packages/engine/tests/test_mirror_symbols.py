"""Integrated mirrors preserve their face shape, front-lit band, and wall-facing depth."""

from __future__ import annotations

import dataclasses
import math

import pytest

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.scene import _SceneBuilder
from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import (
    PART_COLORS,
    lamp_role,
    model_parts,
    plan_symbol_strokes,
)
from typehaus.model.placeable_symbols._mirrors import MIRROR_LIGHT_BAND_WIDTH_M

INCH_M = 0.0254


@pytest.mark.parametrize("symbol,width,height", [
    ("round-mirror-light", 30 * INCH_M, 30 * INCH_M),
    ("mirror-light", 24 * INCH_M, 60 * INCH_M),
])
def test_mirror_glass_and_led_band_are_exposed_in_front_of_the_housing(
    symbol: str, width: float, height: float,
) -> None:
    depth = 1.75 * INCH_M
    housing, outer_glass, light, inner_glass = model_parts(symbol, width, depth, height)
    assert [part["color"] for part in (housing, outer_glass, light, inner_glass)] == [
        "luminaire-housing", "mirror", "lamp", "mirror",
    ]
    # Glass buried inside the full-depth housing used to disappear behind its opaque face.
    for rear, front in zip((housing, outer_glass, light), (outer_glass, light, inner_glass),
                           strict=True):
        assert front["center"][1] + front["size"][1] / 2 == pytest.approx(
            rear["center"][1] - rear["size"][1] / 2)
    assert inner_glass["center"][1] - inner_glass["size"][1] / 2 == pytest.approx(-depth / 2)
    assert (light["size"][0] - inner_glass["size"][0]) / 2 == pytest.approx(
        MIRROR_LIGHT_BAND_WIDTH_M)
    assert (light["size"][2] - inner_glass["size"][2]) / 2 == pytest.approx(
        MIRROR_LIGHT_BAND_WIDTH_M)
    assert inner_glass["size"][0] * inner_glass["size"][2] > width * height * 0.9
    assert all(part["center"][2] == pytest.approx(height / 2)
               for part in (housing, outer_glass, light, inner_glass))
    if symbol == "round-mirror-light":
        assert all(part["shape"] == "cylinder-depth" for part in model_parts(
            symbol, width, depth, height))
        assert all(part["size"][0] == part["size"][2] for part in model_parts(
            symbol, width, depth, height))
    else:
        assert housing["size"][2] == pytest.approx(height)
        assert housing["size"][0] == pytest.approx(width)


def test_over_mirror_bar_lens_faces_into_the_room() -> None:
    width, depth, height = 24 * INCH_M, 2 * INCH_M, 3 * INCH_M
    housing, lens = model_parts("mirror-light-bar", width, depth, height)
    assert lens["center"][2] == pytest.approx(height / 2)
    assert lens["size"][2] < height
    assert lens["center"][1] - lens["size"][1] / 2 == pytest.approx(-depth / 2)
    assert lens["center"][1] + lens["size"][1] / 2 == pytest.approx(
        housing["center"][1] - housing["size"][1] / 2)
    assert plan_symbol_strokes("mirror-light-bar", width, depth) == plan_symbol_strokes(
        "linear-light", width, depth)


def test_catlin_round_and_rectangular_mirrors_use_their_own_shapes(catlin_plan) -> None:
    types = {kind.tag: kind for kind in catlin_plan.library.electrical_device_types}
    assert types["ED-T-LT-MIRROR-RING"].plan_symbol == "round-mirror-light"
    assert types["ED-T-LT-MIRROR-CLOSET"].plan_symbol == "mirror-light"
    assert types["ED-T-LT-MIRROR"].plan_symbol == "mirror-light-bar"
    mirror = types["ED-T-LT-MIRROR-RING"]
    record = _symbol_geometry(mirror, mirror.footprint)
    assert all(part["shape"] == "cylinder-depth" for part in record["model_parts"])
    glass = [part for part in record["model_parts"] if "metalness" in part]
    assert len(glass) == 2
    assert all(part["metalness"] == 1 and part["roughness"] < 0.1 for part in glass)


def test_export_keeps_the_polished_mirror_material() -> None:
    scene = _SceneBuilder()
    index = scene._material(PART_COLORS["mirror"])
    gltf, _ = scene.build()
    surface = gltf["materials"][index]["pbrMetallicRoughness"]
    assert surface["metallicFactor"] == 1
    assert surface["roughnessFactor"] < 0.1


@pytest.mark.parametrize("turn", [0.0, 90.0])
def test_exported_bath_mirror_is_circular_on_either_wall_orientation(
    catlin_model_ro, turn: float,
) -> None:
    model = catlin_model_ro
    item = next(item for item in model.canvas_objects if item.tag == "ED-S-BATH1-MIRROR")
    item = dataclasses.replace(item, rotation_degrees=item.rotation_degrees + turn)
    mirror = next(kind for kind in model.plan.library.electrical_device_types
                  if kind.tag == item.type_ref)
    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, item, mirror, {})
    angle = math.radians(item.rotation_degrees)
    # Undo the placement and glTF's axis mapping; every curved vertex lies on the same
    # vertical circle, including when the second mirror is on the perpendicular wall.
    for part in model_parts(mirror.plan_symbol, mirror.footprint[0].meters,
                            mirror.footprint[1].meters, mirror.height.meters):
        role = lamp_role(mirror.cct_k) if part["color"] == "lamp" else part["color"]
        points, _ = mesh._buckets[PART_COLORS[role]]
        radius = part["size"][0] / 2
        local_depth_faces = [part["center"][1] - part["size"][1] / 2,
                             part["center"][1] + part["size"][1] / 2]
        radii = []
        for x, z, minus_y in points:
            dx, dy = x - item.position[0], -minus_y - item.position[1]
            local_x = dx * math.cos(angle) + dy * math.sin(angle)
            local_y = -dx * math.sin(angle) + dy * math.cos(angle)
            if any(abs(local_y - face) < 1e-9 for face in local_depth_faces):
                radial_distance = math.hypot(local_x, z - item.z_m - part["center"][2])
                if radial_distance > 1e-9:
                    radii.append(radial_distance)
        assert radii
        assert max(radii) == pytest.approx(radius)
        assert all(distance == pytest.approx(radius) for distance in radii)


def test_arch_shelf_mirror_is_arched_glass_over_a_full_depth_shelf() -> None:
    width, depth, height = 20.125 * INCH_M, 5.5 * INCH_M, 28 * INCH_M
    shelf, frame, arch, glass, glass_arch = model_parts("arch-shelf-mirror", width, depth, height)
    assert shelf["center"][2] - shelf["size"][2] / 2 == pytest.approx(0)
    assert shelf["size"][:2] == pytest.approx((width, depth))
    # The half-round tops out at the full height; the straight frame stops at its spring line.
    assert arch["shape"] == "cylinder-depth"
    assert arch["center"][2] + arch["size"][2] / 2 == pytest.approx(height)
    assert frame["center"][2] + frame["size"][2] / 2 == pytest.approx(height - width / 2)
    assert [glass["color"], glass_arch["color"]] == ["mirror", "mirror"]
    # Glass stands proud of the frame, toward the room (-y), and inside its border.
    assert glass["center"][1] < frame["center"][1]
    assert glass_arch["size"][0] < arch["size"][0]
    assert frame["center"][1] + frame["size"][1] / 2 == pytest.approx(depth / 2)
    assert len(plan_symbol_strokes("arch-shelf-mirror", width, depth)) == 2

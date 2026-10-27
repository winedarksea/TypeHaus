"""Doorway probes for Catlin's coordinated finished-floor schedule."""

from __future__ import annotations

from math import hypot

import pytest

from typehaus.resolve.walking_surface import surfaces_at

INCH_M = 0.0254
FLUSH_TOLERANCE_IN = 1 / 16  # Catlin design target, notes/floor_heights.md


@pytest.mark.parametrize(("opening", "first", "second", "difference_in"), [
    ("D-S-BED1", "RM-S-BED1", "RM-S-HALL", 0),
    ("D-S-BED2", "RM-S-BED2", "RM-S-HALL", 0),
    ("D-S-BED3", "RM-S-BED3", "RM-S-HALL", 0),
    ("D-S-SUITE", "RM-S-SUITE", "RM-S-HALL", 0),
    ("D-S-SUITEBATH", "RM-S-SUITE", "RM-S-SUITEBATH", 0),
    ("O-S-VANITY", "RM-S-HALL", "RM-S-VANITY", 0),
    ("D-S-BATH1", "RM-S-HALL", "RM-S-BATH1", 0),
    ("D-S-NCLOSET", "RM-S-HALL", "RM-S-NCLOSET", 0),
    ("D-S-STUDY2", "RM-S-HALL", "RM-S-STUDY2", 0),
    ("D-S-PLANT", "RM-S-STUDY2", "RM-S-PLANT", 0.38),
    ("D-M-MUD", "RM-M-LIVING", "RM-M-MUDROOM", 0),
    ("D-M-MECH", "RM-M-MUDROOM", "RM-M-MECH", 0),
    ("D-M-MUDC", "RM-M-MUD-CLOSET", "RM-M-MUDROOM", 0),
    ("D-M-BED2", "RM-M-LIVING", "RM-M-BED", 0.5531496062992126),
    ("D-M-BED", "RM-M-BED", "RM-M-CLOSET", 0),
    ("D-M-BATH2", "RM-M-BED", "RM-M-BATH2", 0),
])
def test_finished_planes_beside_each_door(
    catlin_model_ro, opening, first, second, difference_in,
):
    door = next(item for item in catlin_model_ro.openings if item.tag == opening)
    wall = next(item for item in catlin_model_ro.walls if item.tag == door.host_wall)
    start, end = wall.axis[0], wall.axis[-1]
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = hypot(dx, dy)
    middle = (start[0] + dx * door.center_along_m / length,
              start[1] + dy * door.center_along_m / length)
    found = {}
    # Cross the wall far enough to clear its finish face. Narrow closet doors can
    # require a deeper probe; retain the closest valid surface in each named room.
    for distance in (0.20, 0.35, 0.50, 0.80, 1.0):
        for sign in (-1, 1):
            point = (middle[0] - sign * dy / length * distance,
                     middle[1] + sign * dx / length * distance)
            for surface in surfaces_at(catlin_model_ro, point):
                if surface.room_tag in (first, second) and surface.surface_m is not None:
                    found.setdefault(surface.room_tag, surface.surface_m / INCH_M)
        if len(found) == 2:
            break
    assert set(found) == {first, second}, (opening, found)
    difference = abs(found[first] - found[second])
    assert difference == pytest.approx(difference_in, abs=0.002), (opening, found)
    if difference_in == 0:
        assert difference <= FLUSH_TOLERANCE_IN


def test_stair_heads_match_their_finished_floors(catlin_model_ro):
    stairs = {stair.tag: stair for stair in catlin_model_ro.stairs}
    assert stairs["ST-M2S"].base_elevation_m / INCH_M == pytest.approx(0.9468503937007874)
    assert stairs["ST-M2S"].arrival_elevation_m / INCH_M == pytest.approx(121.5)
    assert stairs["ST-M2S"].riser_height_m / INCH_M == pytest.approx(
        (121.5 - 0.9468503937007874) / 16)
    assert stairs["ST-S2A"].base_elevation_m / INCH_M == pytest.approx(121.5)


def test_quincy_oak_selection_is_house_local_and_includes_its_pad(catlin_plan):
    from typehaus.library.materials import ALL_MATERIALS

    materials = catlin_plan.library.materials
    assert len({material.tag for material in materials}) == len(materials)
    lvp = next(material for material in materials if material.tag == "lvp")
    assert lvp.finish_thickness_in == pytest.approx(5 / 25.4)
    assert lvp.floor_companion_refs == ()
    assert lvp.finish == "lvp-plank"
    assert lvp.color == "#bfb6ad"
    product = next(product for product in catlin_plan.library.products
                   if product.tag == lvp.product_ref)
    assert product.brand == "COREtec"
    assert product.model == "VV017-01018"
    assert "attached cork" in product.source
    generic = next(material for material in ALL_MATERIALS if material.tag == "lvp")
    assert generic.finish_thickness_in == 0.2362
    assert generic.floor_companion_refs == ("lvp-underlayment",)


@pytest.mark.parametrize(("wood_xy_ft", "concrete_xy_ft"), [
    ((28, 12.5), (28, 13.5)),  # south leg: y=13 ft movement break
    ((17.5, 25), (18.5, 25)),  # west leg: x=18 ft shared bearing
])
def test_both_legs_of_concrete_boundary_remain_flush(
    catlin_model_ro, wood_xy_ft, concrete_xy_ft,
):
    def main_surface(point, finish):
        return next(surface for surface in surfaces_at(
            catlin_model_ro, tuple(coordinate * 12 * INCH_M for coordinate in point))
            if surface.finish_ref == finish and surface.room_tag == "RM-M-LIVING")

    wood = main_surface(wood_xy_ft, "lvp")
    concrete = main_surface(concrete_xy_ft, "coated-concrete")
    assert wood.surface_m / INCH_M == pytest.approx(0.75 + 5 / 25.4)
    assert concrete.surface_m / INCH_M == pytest.approx(0.9375)
    difference_in = (wood.surface_m - concrete.surface_m) / INCH_M
    assert difference_in == pytest.approx(0.0093503937007874)
    assert difference_in < FLUSH_TOLERANCE_IN


def test_exported_quincy_oak_meshes_match_resolved_depth_and_color(catlin_model_ro):
    from typehaus.emit.gltf import emit_gltf_dict
    from typehaus.emit.gltf.palette import _room_floor_color

    gltf, _blob = emit_gltf_dict(catlin_model_ro)
    color = _room_floor_color(catlin_model_ro, "lvp")
    lvp_materials = {index for index, material in enumerate(gltf["materials"])
                     if material["pbrMetallicRoughness"]["baseColorFactor"]
                     == pytest.approx(color)}
    assert lvp_materials
    for room_tag in ("RM-M-LIVING", "RM-M-MUDROOM", "RM-M-MECH", "RM-M-MUD-CLOSET"):
        room = next(room for room in catlin_model_ro.rooms if room.tag == room_tag)
        positions = [gltf["accessors"][primitive["attributes"]["POSITION"]]
                     for node in gltf["nodes"]
                     if node.get("extras", {}).get("uid") == room.uid and "mesh" in node
                     for primitive in gltf["meshes"][node["mesh"]]["primitives"]
                     if primitive["material"] in lvp_materials]
        assert positions, room_tag
        for accessor in positions:
            # glTF Y is vertical; the room centroid may sit on concrete, but LVP is on wood.
            assert accessor["min"][1] / INCH_M == pytest.approx(0.75, abs=1e-6)
            assert accessor["max"][1] / INCH_M == pytest.approx(0.75 + 5 / 25.4, abs=1e-6)

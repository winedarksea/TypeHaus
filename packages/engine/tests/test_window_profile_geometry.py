"""Published profile dimensions reach the geometry consumed by the 3D viewer."""

from dataclasses import replace

import pytest
from pydantic import ValidationError

from typehaus.model.types import WindowType
from typehaus.quantities import inch, mm
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_millwork import window_stool_prism
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model_window_seat import window_frame_dimensions
from typehaus.server.model_json_opening_parts import opening_parts_json


def _projected_width(ring, tangent):
    coordinates = [x * tangent[0] + y * tangent[1] for x, y in ring]
    return max(coordinates) - min(coordinates)


def test_andersen_sections_keep_distinct_jamb_head_and_sill_sightlines(catlin_model_ro):
    model = catlin_model_ro
    stools = {stool.window_ref: stool for stool in model.window_stools}
    count = 0
    for opening in model.openings:
        if opening.kind != "window" or opening.type_ref not in {
            "WT-2748", "WT-2748-T", "WT-2754", "WT-3048",
        }:
            continue
        count += 1
        wall = model.wall(opening.host_wall)
        width, height, sill = window_frame_dimensions(opening)
        bottom = wall.base_ref_z_m + sill
        parts = {part.key: part for part in opening_parts(wall, opening, None)}
        jamb, _, head, rail = parts["frame"].solids
        _, tangent, _, _ = wall_frame(wall)
        assert _projected_width(jamb.ring, tangent) == pytest.approx(
            inch(9 / 16).meters)
        assert head.z1_m - head.z0_m == pytest.approx(inch(3 / 4).meters)
        assert rail.z1_m - rail.z0_m == pytest.approx(inch(13 / 16).meters)
        sash_jamb, _, sash_head, sash_sill = parts["sash"].solids
        assert sash_jamb.z0_m == pytest.approx(bottom + inch(13 / 16).meters)
        assert sash_jamb.z1_m == pytest.approx(bottom + height - inch(3 / 4).meters)
        assert sash_head.z1_m - sash_head.z0_m == pytest.approx(inch(1.625).meters)
        assert sash_sill.z1_m == pytest.approx(sash_jamb.z0_m + inch(1.625).meters)
        glass = parts["glass"].solids[0]
        assert _projected_width(glass.ring, tangent) == pytest.approx(
            width - inch(4.375).meters)
        assert glass.z0_m == pytest.approx(bottom + inch(2.4375).meters)
        assert glass.z1_m == pytest.approx(bottom + height - inch(2.375).meters)
        # The interior ledge is not the exterior sill's exposed allowance.
        stool = stools[opening.tag]
        assert window_stool_prism(wall, opening, stool).z1_m == pytest.approx(
            bottom + inch(1.125).meters)
        viewer = {part["key"]: part for part in opening_parts_json(model, opening)}
        assert viewer["glass"]["solids"][0]["z0_m"] == pytest.approx(glass.z0_m, abs=1e-6)
        assert viewer["frame"]["solids"][2]["z0_m"] == pytest.approx(head.z0_m, abs=1e-6)
    assert count == 9


def test_alucover_faces_and_stool_use_the_bare_frame_sash_bottom(catlin_model_ro):
    model = catlin_model_ro
    types = {kind.tag: kind for kind in model.plan.library.window_types}
    stools = {stool.window_ref: stool for stool in model.window_stools}
    count = 0
    for opening in model.openings:
        if opening.kind != "window" or opening.type_ref not in types:
            continue
        kind = types[opening.type_ref]
        if kind.product_ref != "PROD-DRUTEX-ALUCOVER-TT":
            continue
        count += 1
        assert kind.frame_face_width.meters == pytest.approx(.074)
        assert kind.sash_face_width.meters == pytest.approx(.050)
        wall = model.wall(opening.host_wall)
        _, _, sill = window_frame_dimensions(opening)
        stool = stools[opening.tag]
        prism = window_stool_prism(wall, opening, stool)
        assert prism.z1_m == pytest.approx(wall.base_ref_z_m + sill + .038)
        # A supplier's direct sash-bottom measurement can lower the stool but never lift
        # it off its rail when another product has a sash above that rail.
        raised_limit = replace(stool, inward_sash_bottom_m=.2)
        rail = opening_parts(wall, opening, None)[0].solids[-1]
        assert window_stool_prism(wall, opening, raised_limit).z1_m == pytest.approx(rail.z1_m)
    assert count == 11


@pytest.mark.parametrize("field, value", [
    ("frame_head_face_width", 0),
    ("frame_sill_face_width", -1),
    ("frame_sill_face_width", float("nan")),
    ("inward_sash_bottom_height", -1),
    ("inward_sash_bottom_height", float("inf")),
])
def test_profile_dimensions_reject_invalid_measurements(field, value):
    with pytest.raises(ValidationError):
        WindowType(tag="WT", width=inch(27), height=inch(48), **{field: mm(value)})

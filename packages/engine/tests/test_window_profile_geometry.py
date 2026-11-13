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


def test_max_light_units_draw_35_mm_faces_all_round(catlin_model_ro):
    # The three 14x24s and, since 2026-11-13, the nine escape units (Andersen retired).
    model = catlin_model_ro
    types = {kind.tag: kind for kind in model.plan.library.window_types}
    count = 0
    for opening in model.openings:
        kind = types.get(opening.type_ref)
        if opening.kind != "window" or kind is None:
            continue
        if kind.product_ref != "PROD-ALIPLAST-MAXLIGHT-TT":
            continue
        count += 1
        wall = model.wall(opening.host_wall)
        parts = {part.key: part for part in opening_parts(wall, opening, None)}
        jamb, _, head, rail = parts["frame"].solids
        _, tangent, _, _ = wall_frame(wall)
        assert _projected_width(jamb.ring, tangent) == pytest.approx(mm(35).meters)
        assert head.z1_m - head.z0_m == pytest.approx(mm(35).meters)
        assert rail.z1_m - rail.z0_m == pytest.approx(mm(35).meters)
        viewer = {part["key"]: part for part in opening_parts_json(model, opening)}
        assert viewer["frame"]["solids"][2]["z0_m"] == pytest.approx(head.z0_m, abs=1e-6)
    assert count == 12


def test_alucover_faces_and_stool_use_the_adaptor_sash_bottom(catlin_model_ro):
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
        assert kind.frame_sill_face_width.meters == pytest.approx(.074 + .030)  # 54123
        wall = model.wall(opening.host_wall)
        _, _, sill = window_frame_dimensions(opening)
        stool = stools[opening.tag]
        prism = window_stool_prism(wall, opening, stool)
        # 38 mm above the bare PVC frame + the 30 mm adaptor, clear of the pan's back dam
        assert prism.z1_m == pytest.approx(wall.base_ref_z_m + sill + .068)
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

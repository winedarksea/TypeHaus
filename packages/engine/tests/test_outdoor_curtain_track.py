"""Outdoor curtain hardware stays open underneath and flush with its mounting soffit."""

import json
import math

import pytest
from pydantic import ValidationError

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.model.canvas import _symbol_geometry
from typehaus.model.curtain_track import CurtainTrackSpec
from typehaus.model.placeable_symbols._curtain_track import curtain_track_type_geometry
from typehaus.quantities import inch


def test_porch_tracks_have_real_channels_and_preserve_the_soffit(catlin_model_ro):
    model = catlin_model_ro
    tracks = [obj for obj in model.canvas_objects if obj.tag.startswith("FURN-M-PORCH-TRACK-")]
    assert len(tracks) == 3
    for item in tracks:
        product = next(t for t in model.plan.library.furniture_types if t.tag == item.type_ref)
        assert product.curtain_track.outdoor_hardware
        assert not product.curtain_track.show_curtains
        assert item.z_m == pytest.approx(105 * 0.0254)
        assert item.body_z1_m == pytest.approx(105.75 * 0.0254)
        strokes, parts = curtain_track_type_geometry(product)
        assert not strokes
        assert "fabric" not in {part["color"] for part in parts}
        record = json.loads(json.dumps(_symbol_geometry(product, product.footprint)))
        assert len(record["model_parts"]) == len(parts)
        assert record["plan_strokes"] == []
        width = product.footprint[0].meters
        height = product.height.meters
        for part in parts:
            center, size = part["center"], part["size"]
            assert abs(center[0]) + size[0] / 2 <= width / 2 + 1e-9
            assert abs(center[1]) + size[1] / 2 <= 0.75 * 0.0254 / 2 + 1e-9
            assert center[2] - size[2] / 2 >= -1e-9
            assert center[2] + size[2] / 2 <= height + 1e-9
        # At mid-run the slot and carrier cavity must be actual empty space, not dark paint.
        for z in (0.0005, height / 2):
            assert not any(all(abs(point - center) < size / 2 - 1e-9
                               for point, center, size in zip((0, 0, z), part["center"],
                                                              part["size"], strict=True))
                           for part in parts)
        keys = [part for part in parts if part["color"] == "metal" and part["shape"] == "box"]
        assert len(keys) == math.ceil(width / (84 * 0.0254)) - 1
        assert [key["center"][0] + width / 2 for key in keys] == pytest.approx(
            [84 * 0.0254 * section for section in range(1, len(keys) + 1)])


def test_porch_channel_exports_with_its_rotation_and_mount_height(catlin_model_ro):
    import ifcopenshell

    from typehaus.emit.ifc.placeable_parts import parts_representation

    model = catlin_model_ro
    for item in model.canvas_objects:
        if not item.tag.startswith("FURN-M-PORCH-TRACK-"):
            continue
        product = next(t for t in model.plan.library.furniture_types if t.tag == item.type_ref)
        builder = _MeshBuilder()
        assert _add_canvas_parts(builder, item, product, {})
        vertices = [point for positions, _ in builder._buckets.values() for point in positions]
        assert min(point[1] for point in vertices) == pytest.approx(item.z_m)
        assert max(point[1] for point in vertices) == pytest.approx(item.body_z1_m)
        run_axis = 0 if item.rotation_degrees == 0 else 2
        cross_axis = 2 if run_axis == 0 else 0
        assert max(p[run_axis] for p in vertices) - min(p[run_axis] for p in vertices) == (
            pytest.approx(product.footprint[0].meters))
        assert max(p[cross_axis] for p in vertices) - min(p[cross_axis] for p in vertices) == (
            pytest.approx(0.75 * 0.0254))
        assert (max(p[0] for p in vertices) + min(p[0] for p in vertices)) / 2 == (
            pytest.approx(item.position[0]))
        assert (max(p[2] for p in vertices) + min(p[2] for p in vertices)) / 2 == (
            pytest.approx(-item.position[1]))
        file = ifcopenshell.file(schema="IFC4")
        context = file.create_entity("IfcGeometricRepresentationContext",
                                     CoordinateSpaceDimension=3)
        parts = curtain_track_type_geometry(product)[1]
        representation = parts_representation(file, context, parts, item.position,
                                             item.rotation_degrees, item.z_m)
        assert len(representation.Items) == len(parts)
        ifc_points = {tuple(round(v, 9) for v in point)
                      for solid in representation.Items for point in solid.Coordinates.CoordList}
        gltf_points = {(round(x, 9), round(-minus_y, 9), round(z, 9))
                       for x, z, minus_y in vertices}
        assert ifc_points == gltf_points


@pytest.mark.parametrize("changes", [
    {"rail_wall_thickness": inch(0.4)}, {"carrier_slot_width": inch(0.8)},
    {"stock_length": inch(0)}, {"mounting_screws_per_stock": 1},
    {"mounting_end_inset": inch(45)},
])
def test_outdoor_profile_rejects_impossible_hardware(changes):
    with pytest.raises(ValidationError):
        CurtainTrackSpec(outdoor_hardware=True, rail_width=inch(0.75), **changes)

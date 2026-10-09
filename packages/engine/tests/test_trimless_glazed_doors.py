"""A kerfed jamb can retain borrowed light without sealing the study's ERV relief path."""

from __future__ import annotations

from dataclasses import replace

import pytest
from shapely.geometry import Polygon

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.openings import _add_opening_filling
from typehaus.emit.gltf.palette import _color
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_door_products import (
    _CONCEALED_UNDERCUT_M,
    _PUSH_SET_REBATE_M,
    finish_faces,
)
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.room_lookup import room_owning


@pytest.fixture
def study_door(catlin_model_ro):
    opening = next(op for op in catlin_model_ro.openings if op.tag == "D-M-STUDY")
    wall = catlin_model_ro.wall(opening.host_wall)
    door_type = next(dt for dt in catlin_model_ro.plan.library.door_types
                     if dt.tag == opening.type_ref)
    return opening, wall, door_type


def _parts(opening, wall, door_type):
    return {part.key: part for part in opening_parts(
        wall, opening, door_type.operation, is_glazed=door_type.glazed,
        is_trimless=door_type.trimless, leaf_set=door_type.leaf_set)}


def test_study_matches_the_neighbor_jamb_and_keeps_its_glazed_outswing(
        catlin_model_ro, study_door):
    opening, wall, door_type = study_door
    bedroom = next(op for op in catlin_model_ro.openings if op.tag == "D-M-BED2")
    bedroom_type = next(dt for dt in catlin_model_ro.plan.library.door_types
                        if dt.tag == bedroom.type_ref)
    assert door_type.trimless and bedroom_type.trimless
    assert door_type.leaf_set == "pull" and bedroom_type.leaf_set == "push"
    assert door_type.glazed and door_type.tempered
    assert opening.uid == "CMD208AAAA" and opening.host_wall == "W-M-C3"
    assert opening.width_m == pytest.approx(30 * 0.0254)
    assert opening.height_m == pytest.approx(80 * 0.0254)
    assert opening.flip_hinge and opening.flip_swing
    ring = opening.swing_clearance
    swing_center = tuple(sum(point[axis] for point in ring) / len(ring) for axis in (0, 1))
    assert room_owning(catlin_model_ro, wall.storey, swing_center).tag == "RM-M-LIVING"
    plant = next(op for op in catlin_model_ro.openings if op.tag == "D-S-PLANT")
    assert plant.type_ref == "DT-INT-SWING30-GLAZED"


def test_study_glass_is_open_between_wood_stiles_and_above_the_undercut(study_door):
    opening, wall, door_type = study_door
    parts = _parts(opening, wall, door_type)
    assert set(parts) == {"jamb_liner", "leaf", "stop", "shadow_gap", "glazing", "hardware"}
    assert len(parts["jamb_liner"].solids) == 3, "no jamb sill across the relief path"
    assert len(parts["leaf"].solids) == 4, "wood stiles and rails, not an opaque slab"
    (pane,) = parts["glazing"].solids
    assert parts["glazing"].material_key == "glass"
    pane_mid_z = (pane.z0_m + pane.z1_m) / 2.0
    for wood in parts["leaf"].solids:
        if wood.z0_m < pane_mid_z < wood.z1_m:
            assert Polygon(wood.ring).intersection(Polygon(pane.ring)).area < 1e-10
    leaf_bottom = wall.base_ref_z_m + opening.sill_m + _CONCEALED_UNDERCUT_M
    assert min(solid.z0_m for solid in parts["leaf"].solids) == pytest.approx(leaf_bottom)
    assert all(solid.z0_m >= leaf_bottom - 1e-9 for key in ("leaf", "glazing", "stop", "shadow_gap")
               for solid in parts[key].solids)


@pytest.mark.parametrize("leaf_set", ["pull", "push"])
@pytest.mark.parametrize("flip_swing", [False, True])
def test_glazed_trimless_leaf_respects_the_selected_wall_face(
        study_door, leaf_set, flip_swing):
    opening, wall, door_type = study_door
    opening = replace(opening, flip_swing=flip_swing)
    door_type = door_type.model_copy(update={"leaf_set": leaf_set})
    parts = _parts(opening, wall, door_type)
    (x0, y0), _tangent, (nx, ny), _length = wall_frame(wall)

    def normal_span(solid):
        offsets = [(x - x0) * nx + (y - y0) * ny for x, y in solid.ring]
        return min(offsets), max(offsets)

    lo, hi = finish_faces(wall)
    leaf_lo, leaf_hi = normal_span(parts["leaf"].solids[0])
    if leaf_set == "pull":
        assert (leaf_lo if flip_swing else leaf_hi) == pytest.approx(lo if flip_swing else hi)
    else:
        expected = hi - _PUSH_SET_REBATE_M if flip_swing else lo + _PUSH_SET_REBATE_M
        assert (leaf_hi if flip_swing else leaf_lo) == pytest.approx(expected)
    (pane,) = parts["glazing"].solids
    pane_lo, pane_hi = normal_span(pane)
    assert leaf_lo < pane_lo < pane_hi < leaf_hi
    assert pane_lo + pane_hi == pytest.approx(leaf_lo + leaf_hi)


def test_trimless_study_exports_glass_and_opaque_joinery(study_door):
    opening, wall, door_type = study_door
    builder = _MeshBuilder()
    _add_opening_filling(builder, wall, opening, door_type.operation,
                        is_glazed=door_type.glazed, is_trimless=door_type.trimless,
                        leaf_set=door_type.leaf_set)
    assert _color("glass") in builder._buckets, "the exported pane must be translucent"
    assert _color("door_leaf") in builder._buckets
    glass_positions, _indices = builder._buckets[_color("glass")]
    (pane,) = _parts(opening, wall, door_type)["glazing"].solids
    assert min(point[1] for point in glass_positions) == pytest.approx(pane.z0_m)
    assert max(point[1] for point in glass_positions) == pytest.approx(pane.z1_m)

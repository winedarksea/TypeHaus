"""Catalog outlines, independent reveal hosts and installed-height regressions."""

from dataclasses import replace

import pytest
from shapely.geometry import Point, Polygon

from typehaus import ExteriorDoorCatalogInstallation, inch
from typehaus.engineering.exterior_door_support import cantilever_support_report
from typehaus.resolve.doorway import doorway_json
from typehaus.resolve.doorway_heights import installed_threshold_elevation
from typehaus.resolve.exterior_door_boundary import (
    ExteriorDoorBoundaryError,
    exterior_door_boundary,
)
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_walls import layer_solids


def _catalog(**changes):
    fields = dict(
        source_url="https://example.test/dimensioned-section",
        source_drawing="test section",
        sill_outline_m=((0, 0), (0.1, 0), (0.1, 0.03), (0, 0.04)),
        support_kind="timber_outriggers",
        support_ref="floor", frame_material_ref="wood",
        head_material_ref="aluminum", transition_material_ref="rubber",
    )
    return ExteriorDoorCatalogInstallation(**(fields | changes))


def test_capacities_need_evidence_and_schematic_cannot_overlay_catalog():
    with pytest.raises(ValueError, match="evidence"):
        _catalog(support_connection_capacity_lb=500)
    with pytest.raises(ValueError, match="positive"):
        _catalog(pan_height=inch(0))
    with pytest.raises(ValueError, match="outline"):
        _catalog(sill_outline_m=())


def test_member_pass_does_not_verify_missing_connection():
    result = cantilever_support_report(_catalog(), 0.2, 0.25)
    assert result["member_status"] == "PASS"
    assert result["connection_status"] == "UNKNOWN"
    assert result["connection_dcr"] is None
    overloaded = _catalog(concentrated_load_lb=30_000)
    assert cantilever_support_report(overloaded, 0.2, 0.25)["member_status"] == "FAIL"


def test_known_inadequate_connection_fails():
    result = cantilever_support_report(
        _catalog(support_connection_capacity_lb=10, support_connection_source="test capacity"),
        0.2,
        0.25,
    )
    assert result["connection_status"] == "FAIL"
    assert result["connection_dcr"] > 1


@pytest.mark.parametrize("tag", ("D-B-PATIO", "D-S-DECK-E"))
def test_catalog_installation_keeps_evidence_separate(catlin_model_ro, tag):
    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == tag)
    wall = model.wall(opening.host_wall)
    assembly = opening.doorway
    placement = assembly.exterior_placement
    assert placement.sill_design_status == "CATALOG_DESIGN"
    assert placement.factory_depth_documented
    assert assembly.supplier_status == "PENDING"
    assert assembly.fit_status == "UNKNOWN"
    assert not assembly.conflicts
    assert placement.specification.exterior_wrap_material_ref is None
    assert all(
        b.material_ref == "composite-door-frame"
        for b in placement.boards
        if b.name.startswith("exterior")
    )
    names = {s.name for s in placement.sections}
    assert "catalog-sill-outline" in names
    assert "approach-walking-plate" not in names
    assert all(Polygon(s.polygon_m).is_valid for s in placement.sections)
    report = placement.installation_report
    assert report["support"]["connection_status"] == "UNKNOWN"
    assert report["support"]["member_status"] == "PASS"
    assert report["receiver_pan_clearance_in"] >= 0.0625
    if tag == "D-S-DECK-E":
        assert report["minimum_movement_gap_in"] > 0
    assert report["minimum_flashing_overlap_in"] > 0
    height, basis = installed_threshold_elevation(opening, wall)
    assert height > assembly.rough_opening_z_m
    assert height == placement.threshold_upper_z_m
    assert "tolerance" in basis
    assert report["crest_above_interior_in"] + 0.25 <= 7.75
    assert report["crest_above_exterior_in"] + 0.25 <= 7.75
    serialized = doorway_json(assembly)
    assert serialized["exterior_placement"]["installation_report"] == report


def test_nominal_unit_and_rough_opening_are_independent(catlin_plan):
    product = next(t for t in catlin_plan.library.door_types if t.tag == "DT-EXT-FRENCH60-CATALOG")
    dimensions = product.catalog_dimensions
    assert dimensions.nominal_width.meters < dimensions.unit_width.meters < product.width.meters
    assert dimensions.nominal_height.meters < dimensions.unit_height.meters < product.height.meters
    main = catlin_plan.by_tag("D-M-BALC")
    assert main.type_ref == "DT-EXT-FRENCH60"


def test_patio_reveal_reference_and_concrete_seat_are_real(catlin_model_ro):
    model = catlin_model_ro
    door = next(o for o in model.openings if o.tag == "D-B-PATIO")
    wall = model.wall(door.host_wall)
    face, sign = exterior_door_boundary(model, wall, door)
    assert sign == door.doorway.exterior_placement.outward_sign
    assert abs(face) > wall.thickness_m / 2
    assert all(f is not None for f in door.doorway.adjacent_floors)
    notch = next(o for o in model.openings if o.tag == "AO-B-PATIO-SEAT")
    curb = model.wall(notch.host_wall)
    assert notch.width_m == door.width_m
    assert curb.base_ref_z_m + notch.sill_m == pytest.approx(door.doorway.rough_opening_z_m)
    layer = next(layer for layer in curb.depth_layers() if layer.function == "structure")
    pieces = layer_solids(curb, layer.polygon, [notch], layer_name=layer.name)
    center = opening_center(curb, notch)
    notch_z = curb.base_ref_z_m + notch.sill_m
    assert not any(
        s.z1_m > notch_z + 1e-6 and Polygon(s.ring).contains(Point(center)) for s in pieces
    )


def test_invalid_explicit_reveal_does_not_fall_back_to_host(catlin_model_ro):
    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == "D-B-PATIO")
    wall = model.wall(opening.host_wall)
    spec = opening.doorway.exterior_placement.specification.model_copy(
        update={"exterior_opening_ref": "DOES-NOT-EXIST"}
    )
    with pytest.raises(ExteriorDoorBoundaryError, match="does not resolve"):
        exterior_door_boundary(model, wall, opening, spec)


def test_mirrored_reveal_uses_host_coordinates(catlin_model_ro):
    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == "D-B-PATIO")
    wall = model.wall(opening.host_wall)
    face, sign = exterior_door_boundary(model, wall, opening)
    _, _, _, run = wall_frame(wall)
    mirrored_wall = replace(wall, axis=wall.axis[::-1])
    mirrored_door = replace(opening, center_along_m=run - opening.center_along_m)
    other_face, other_sign = exterior_door_boundary(
        model, mirrored_wall, mirrored_door, opening.doorway.exterior_placement.specification
    )
    assert other_sign == -sign
    # The reversed origin lies on the same wall axis, so normal offsets simply reverse.
    assert other_face == pytest.approx(-face)


def test_selected_undocumented_sill_cannot_get_rough_sill_height(catlin_model_ro):
    opening = next(o for o in catlin_model_ro.openings if o.tag == "D-B-PATIO")
    without_geometry = replace(opening, doorway=replace(opening.doorway, exterior_placement=None))
    height, _ = installed_threshold_elevation(
        without_geometry, catlin_model_ro.wall(opening.host_wall)
    )
    assert height is None


def test_full_width_cross_bearer_cannot_block_apron(catlin_model_ro):
    from typehaus.resolve.exterior_door_catalog_fit import catalog_drainage_conflicts

    opening = next(o for o in catlin_model_ro.openings if o.tag == "D-S-DECK-E")
    placement = opening.doorway.exterior_placement
    assert catalog_drainage_conflicts(placement) == ()
    apron = next(s for s in placement.sections if s.name == "impermeable-pan-apron")
    blocker = replace(apron, name="approach-cross-bearer-obstruction", material_ref="kdat")
    changed = replace(placement, sections=(*placement.sections, blocker))
    assert "blocks" in catalog_drainage_conflicts(changed)[0]


def test_receiver_and_movement_conflicts_are_measured(catlin_model_ro):
    from typehaus.resolve.exterior_door_catalog import add_catalog_installation

    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == "D-S-DECK-E")
    wall = model.wall(opening.host_wall)
    original = opening.doorway.exterior_placement
    catalog = original.specification.catalog_installation.model_copy(
        update={"receiver_depth": inch(2), "movement_horizontal": inch(1)}
    )
    specification = original.specification.model_copy(update={"catalog_installation": catalog})
    assembly = replace(
        opening.doorway, exterior_placement=replace(original, specification=specification)
    )
    clad, _ = exterior_door_boundary(model, wall, opening, specification)
    changed = add_catalog_installation(model, wall, opening, assembly, clad)
    assert any("receiver drilling" in message for message in changed.conflicts)
    assert any("movement closes" in message for message in changed.conflicts)

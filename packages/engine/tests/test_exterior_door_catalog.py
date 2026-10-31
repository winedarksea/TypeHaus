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
    with pytest.raises(ValueError, match="reference, source"):
        _catalog(sill_extender_depth=inch(1.1875))


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
    if tag == "D-B-PATIO":
        assert placement.installation_report["seat_interference_status"] == "PASS"
        assert placement.specification.catalog_installation.sill_extender_ref == "XMN5"
    else:
        assert assembly.fit_status == "UNKNOWN"
        assert not assembly.conflicts
    assert placement.specification.exterior_wrap_material_ref is None
    assert all(
        b.material_ref == placement.specification.exterior_material_ref
        for b in placement.boards
        if b.name.startswith("exterior")
    )
    names = {s.name for s in placement.sections}
    assert "catalog-sill-outline" in names
    if tag == "D-B-PATIO":
        assert "catalog-sill-extender-XMN5" in names
        extender = next(s for s in placement.sections
                        if s.name == "catalog-sill-extender-XMN5")
        assert extender.purchase == "separate"
        assert extender.source_url.endswith("/XMN5.pdf")
        from typehaus.takeoff.doors import door_installation_rows

        takeoff = [row for row in door_installation_rows(model)
                   if row["item"] == "XMN5"]
        assert len(takeoff) == 1
        assert takeoff[0]["tags"] == ["D-B-PATIO"]
        assert takeoff[0]["source"].endswith("/XMN5.pdf")
        from typehaus.takeoff.openings import opening_takeoff

        schedule_rows = opening_takeoff(model)
        clearance_rows = [row for row in schedule_rows if any(
            tag == "AO-B-PATIO-CURB-APPROACH" for tag in row["tags"]
        )]
        assert len(clearance_rows) == 1
        assert all(not row["framing_required"] for row in clearance_rows)
    assert "approach-walking-plate" not in names
    assert all(Polygon(s.polygon_m).is_valid for s in placement.sections)
    report = placement.installation_report
    assert report["support"]["connection_status"] == "UNKNOWN"
    assert report["support"]["member_status"] == "PASS"
    assert report["approach_slope"] == pytest.approx(1 / 48)
    assert report["drainage_clearance_in"] > 0
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
    dimensions, ro = product.catalog_dimensions, product.rough_opening
    assert product.width.meters < dimensions.unit_width.meters < ro.width.meters
    assert product.height.meters < dimensions.unit_height.meters < ro.height.meters
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
    approach_recess = next(
        o for o in model.openings if o.tag == "AO-B-PATIO-CURB-APPROACH"
    )
    host = model.wall(approach_recess.host_wall)
    assert approach_recess.depth_from == "exterior"
    assert not approach_recess.framing_required
    assert not any(m.opening_tag == approach_recess.tag for m in host.members)
    assert approach_recess.depth_m == pytest.approx(
        host.layer_depth_m("concrete", "exterior")
    )
    assert approach_recess.width_m == door.width_m
    assert approach_recess.center_along_m == pytest.approx(door.center_along_m)


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


@pytest.mark.parametrize("remove_extender,remove_recess", [(True, False), (False, True), (True, True)])
def test_patio_clearance_requires_deliberate_extender_and_recess(
    catlin_model_ro, remove_extender, remove_recess
):
    from typehaus.resolve.exterior_door_catalog_fit import catalog_seat_conflicts
    from typehaus.resolve.exterior_door_catalog_layout import catalog_installation_layout
    from typehaus.resolve.exterior_door_catalog_parts import catalog_sill_sections

    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == "D-B-PATIO")
    wall = model.wall(opening.host_wall)
    placement = opening.doorway.exterior_placement
    spec = placement.specification.catalog_installation
    if remove_extender:
        spec = spec.model_copy(update=dict(sill_extender_ref=None, sill_extender_source_url=None,
                                          sill_extender_depth=inch(0), sill_extender_height=inch(0)))
    installation = placement.specification.model_copy(update={"catalog_installation": spec})
    placement = replace(placement, specification=installation)
    if remove_recess:
        model = replace(model, openings=[o for o in model.openings
                                        if o.tag != "AO-B-PATIO-CURB-APPROACH"])
    assembly = replace(opening.doorway, exterior_placement=placement)
    clad, _ = exterior_door_boundary(model, wall, opening, installation)
    layout = catalog_installation_layout(model, wall, opening, assembly, clad)
    placement = replace(placement, sections=catalog_sill_sections(
        spec, installation, placement, opening, layout))
    assert catalog_seat_conflicts(model, wall, opening, placement)


def test_flashing_selection_and_dimensions_are_independent_of_support(catlin_model_ro):
    from typehaus.resolve.exterior_door_catalog_flashing import catalog_flashing_sections

    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == "D-S-DECK-E")
    original = opening.doorway.exterior_placement
    clad, _ = exterior_door_boundary(model, model.wall(opening.host_wall), opening)

    def sections(**changes):
        catalog = original.specification.catalog_installation.model_copy(update=changes)
        placement = replace(original, specification=original.specification.model_copy(
            update={"catalog_installation": catalog}))
        return catalog_flashing_sections(placement, opening, opening.doorway, clad)

    assert any(s.name == "flashing-end-house-adapter--1"
               for s in sections(support_kind="concrete_cantilever"))
    assert len(sections(independent_landing_flashing=False)) == 4
    modified = sections(head_cap_depth=inch(2), transition_strip_width=inch(8),
                        head_source_url="https://example.test/head", transition_sheet_thickness=inch(.04))
    cap = next(s for s in modified if s.name == "stock-headflash-cap-envelope")
    assert Polygon(cap.polygon_m).bounds[2] - Polygon(cap.polygon_m).bounds[0] == pytest.approx(.0508)
    assert cap.source_url == "https://example.test/head"
    corner = next(s for s in modified if s.name == "flashing-end-silicone-corner-envelope--1")
    assert corner.span_m == pytest.approx(.2032)
    assert abs(corner.polygon_m[-1][1] - corner.polygon_m[0][1]) == pytest.approx(.001016)
    # The module returns its own sections; the resolved session fixture stays untouched.
    assert original.sections == opening.doorway.exterior_placement.sections


def test_schematic_and_catalog_must_be_selected_exclusively():
    from typehaus import ExteriorDoorInstallation, ExteriorDoorSillDesign

    schematic = ExteriorDoorSillDesign(
        source_url="https://example.test/envelope", source_drawing="test",
        threshold_depth=inch(4.5625), threshold_height=inch(1.5), cap_depth=inch(2))
    with pytest.raises(ValueError, match="catalog installation replaces"):
        ExteriorDoorInstallation(interior_material_ref="wood", sill_design=schematic,
                                 catalog_installation=_catalog())


def test_catalog_trim_layout_is_derived_across_doors(catlin_model_ro):
    from typehaus.takeoff.door_trim_layout import TrimSheetStock, door_trim_sheet_layouts

    stock = TrimSheetStock("selected sheet", "finish", .75, 48, 96, .125)
    layouts = door_trim_sheet_layouts(catlin_model_ro, {"captivate-sheet": stock})
    assert len(layouts) == 2
    assert {p["door"] for s in layouts for p in s["pieces"]} == {"D-B-PATIO", "D-S-DECK-E"}
    assert sum(len(s["pieces"]) for s in layouts) == 9
    assert all(s["used_width_in"] <= 48 and s["maximum_length_in"] <= 96 for s in layouts)


def test_patio_brick_trim_and_crown_clearance(catlin_model_ro):
    from typehaus.resolve.geometry_door_products import finish_faces

    model = catlin_model_ro
    door = next(o for o in model.openings if o.tag == "D-B-PATIO")
    reveal = next(o for o in model.openings if o.tag == "AO-B-BRICK-DOOR")
    wall = model.wall(door.host_wall)
    placement = door.doorway.exterior_placement
    assert not any("exterior-casing" in b.name for b in placement.boards)
    face = finish_faces(wall)[1 if placement.outward_sign > 0 else 0]
    returns = [b for b in placement.boards if b.name.startswith("exterior-return")]
    assert len(returns) == 3
    for board in returns:
        assert board.normal_m + placement.outward_sign * board.depth_m / 2 == pytest.approx(face)
    crown = model.wall(reveal.host_wall).base_ref_z_m + reveal.sill_m + reveal.height_m
    head = wall.base_ref_z_m + door.sill_m + door.height_m
    assert crown < head
    assert placement.installation_report["centreline_reveal_clear_height_in"] >= 78
    assert all(b.z_m - b.height_m / 2 == pytest.approx(door.doorway.jamb_bottom_z_m)
               for b in returns if "jamb" in b.name)

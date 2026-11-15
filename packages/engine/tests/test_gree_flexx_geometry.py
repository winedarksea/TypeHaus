"""Published opening dimensions, schematic port honesty and placed service access."""

import dataclasses

import pytest
from _helpers import check_context
from shapely.geometry import Polygon

from typehaus.checks.mep.air_handler_coordination import air_handler_coordination
from typehaus.library.hvac_equipment import GREE_FLEXX_ULTRA_24_AH, GREE_FLEXX_ULTRA_24_OD
from typehaus.model.canvas import model_symbol_for
from typehaus.model.placeable_symbols import model_parts
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_ports import placed_ports

PRODUCT = GREE_FLEXX_ULTRA_24_AH
SYMBOL = "gree-flexx-ultra-24-horizontal"


def test_horizontal_shell_has_the_published_supply_aperture_and_open_return():
    parts = model_parts(SYMBOL, *(value.meters for value in (*PRODUCT.footprint, PRODUCT.height)))
    assert model_symbol_for(PRODUCT) == SYMBOL
    assert len(parts) < 30
    frames = [part for part in parts if part.get("role") == "flexx:supply-frame"]
    assert len(frames) == 3
    lower, upper, front = frames
    aperture_bottom = lower["center"][2] + lower["size"][2] / 2
    aperture_top = upper["center"][2] - upper["size"][2] / 2
    aperture_front = front["center"][1] + front["size"][1] / 2
    aperture_back = PRODUCT.footprint[1].meters / 2
    assert (aperture_top - aperture_bottom) / M_PER_IN == pytest.approx(16.75)
    assert (aperture_back - aperture_front) / M_PER_IN == pytest.approx(11.625)
    # No solid cap across either airflow face; panels run along the cabinet instead.
    assert not [part for part in parts if part["size"][0] < M_PER_IN
                and part["center"][0] > 20 * M_PER_IN]


def test_all_interfaces_have_services_and_preserve_unpublished_station_uncertainty():
    ports = {port.tag: port for port in PRODUCT.ports}
    assert set(ports) == {"power", "control", "supply", "return", "liquid", "vapor",
                          "condensate_primary", "condensate_secondary"}
    assert ports["supply"].section_m() == pytest.approx((11.625 * M_PER_IN, 16.75 * M_PER_IN))
    assert ports["return"].section_m() is None
    assert ports["liquid"].connection_size.inches == pytest.approx(0.375)
    assert ports["vapor"].connection_size.inches == pytest.approx(0.75)
    assert ports["condensate_primary"].connection_size.inches == pytest.approx(0.75)
    assert all(not port.is_exact() and port.notes for port in ports.values())


def test_visible_connection_markers_agree_with_declared_front_face_ports():
    parts = model_parts(SYMBOL, *(value.meters for value in (*PRODUCT.footprint, PRODUCT.height)))
    by_role = {part.get("role"): part for part in parts}
    for port in PRODUCT.ports:
        part = by_role.get("flexx:" + port.tag)
        if part is None:
            continue
        x, y, z = (value.meters for value in port.position)
        assert part["center"][0] == pytest.approx(x)
        assert part["center"][1] - part["size"][1] / 2 == pytest.approx(y)
        assert part["center"][2] == pytest.approx(z)


def test_catlin_faces_front_service_space_south_and_supply_west(catlin_model_ro):
    """On RM-A-EAST-UNFIN's deck (2026-11-11): the front panel faces the open attic south,
    supply discharges west into EQ-A-HP1-SUP-BOX, return enters east from EQ-S-ERV-MIX."""
    obj = next(obj for obj in catlin_model_ro.canvas_objects if obj.tag == "EQ-S-HP1-AH")
    ports = {port.port_tag: port for port in placed_ports(catlin_model_ro)
             if port.equipment_tag == obj.tag}
    assert ports["power"].direction == pytest.approx((0, -1, 0))
    assert ports["supply"].direction == pytest.approx((-1, 0, 0))
    assert ports["return"].direction == pytest.approx((1, 0, 0))
    zone, = obj.required_clearances
    case_south = min(y for _, y in obj.footprint)
    assert max(y for _, y in zone) == pytest.approx(case_south)
    assert (case_south - min(y for _, y in zone)) / M_PER_IN == pytest.approx(24)
    assert ports["supply"].x_m < obj.position[0]


def test_catlin_open_deck_install_stays_unknown_not_pass(catlin_plan, catlin_model_ro):
    """No enclosure to test against: the check asks for coordination rather than passing."""
    findings = air_handler_coordination(check_context(catlin_plan, catlin_model_ro))
    assert [finding.result.value for finding in findings] == ["unknown", "unknown"]
    assert "no soffit enclosure" in findings[0].message
    assert "return clear aperture" in findings[1].message


def _boxed(catlin_plan, catlin_model_ro, grow_to_zone: bool):
    """The AH declared inside a synthetic soffit: its case, or its case plus the zone."""
    obj = next(obj for obj in catlin_model_ro.canvas_objects if obj.tag == "EQ-S-HP1-AH")
    outline = Polygon(obj.footprint)
    if grow_to_zone:
        outline = outline.union(Polygon(obj.required_clearances[0])).convex_hull
    model = dataclasses.replace(catlin_model_ro, soffits=[
        dataclasses.replace(s, outline=list(outline.exterior.coords)[:-1])
        if s.tag == "SF-S-DUCT" else s for s in catlin_model_ro.soffits])
    elements = {storey: tuple(el.model_copy(update={"soffit_ref": "SF-S-DUCT"})
                              if el.tag == obj.tag else el for el in items)
                for storey, items in catlin_plan.elements.items()}
    plan = catlin_plan.model_copy(update={"elements": elements})
    return air_handler_coordination(check_context(plan, model))


def test_an_enclosure_without_the_front_zone_fails(catlin_plan, catlin_model_ro):
    findings = _boxed(catlin_plan, catlin_model_ro, grow_to_zone=False)
    assert [finding.result.value for finding in findings] == ["fail", "unknown"]
    assert "underside hatch" in findings[0].message


def test_an_enclosure_that_covers_the_zone_still_needs_obstruction_coordination(
    catlin_plan, catlin_model_ro,
):
    findings = _boxed(catlin_plan, catlin_model_ro, grow_to_zone=True)
    assert {finding.result.value for finding in findings} == {"unknown"}


def test_other_air_handlers_do_not_inherit_gree_installation_assumptions(catlin_plan,
                                                                      catlin_model_ro):
    library = catlin_plan.library.model_copy(update={"equipment_types": tuple(
        product.model_copy(update={"model_representation": None})
        if product.tag == PRODUCT.tag else product
        for product in catlin_plan.library.equipment_types)})
    plan = catlin_plan.model_copy(update={"library": library})
    findings = air_handler_coordination(check_context(plan, catlin_model_ro))
    assert [finding.result.value for finding in findings] == ["not_applicable"]


@pytest.mark.parametrize("equipment_tag, product, rotation", [
    ("EQ-S-HP1-AH", PRODUCT, 0), ("EQ-S-HP1-AH", PRODUCT, 90),
    ("EQ-M-HP1-OD", GREE_FLEXX_ULTRA_24_OD, 0),
    ("EQ-M-HP1-OD", GREE_FLEXX_ULTRA_24_OD, 180),
    ("EQ-A-HP1-SUP-BOX", None, 0), ("EQ-S-ERV-MIX", None, 90),
])
def test_viewer_glb_and_ifc_share_the_open_shell_and_connection_markers(
    catlin_model_ro, tmp_path, equipment_tag, product, rotation,
):
    import ifcopenshell

    from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.ifc.emitter import emit_ifc
    from typehaus.model import Building, Library, PlanModel, Project, Site, Storey, deg, ft, m
    from typehaus.resolve import resolve

    original = next(obj for obj in catlin_model_ro.canvas_objects if obj.tag == equipment_tag)
    if product is None:
        product = next(p for p in catlin_model_ro.plan.library.equipment_types
                       if p.tag == original.type_ref)
    item = dataclasses.replace(original, rotation_degrees=rotation)
    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, item, product, {})
    glb_points = {(round(x, 9), round(-minus_y, 9), round(z, 9))
                  for points, _ in mesh._buckets.values() for x, z, minus_y in points}
    equipment = catlin_model_ro.plan.by_tag(original.tag).model_copy(update={
        "rotation": deg(rotation), "circuit": None, "room": None, "outdoor_ref": None,
        "soffit_ref": None, "zone_rooms": (),
    })
    # A tiny model emits at the resolved body's datum without rebuilding the whole house.
    plan = PlanModel(
        project=Project(name="FLEXX", project_uuid=catlin_model_ro.plan.project.project_uuid,
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="second", elevation=m(original.z_m),
                       default_ceiling_height=ft(9)),),
        library=Library(equipment_types=(product,)), elements={"second": (equipment,)},
    )
    model, _ = resolve(plan)
    placed = next(obj for obj in model.canvas_objects if obj.tag == original.tag)
    # Match the synthetic ceiling-mounted body's base to the original viewport body.
    placed = dataclasses.replace(placed, z_m=original.z_m)
    model = dataclasses.replace(model, canvas_objects=[placed])
    exported = ifcopenshell.open(str(emit_ifc(model, tmp_path / "flexx.ifc")))
    handler, = [obj for obj in exported.by_type("IfcElement") if obj.Name == original.tag]
    representation, = handler.Representation.Representations
    assert representation.RepresentationType == "Tessellation"
    assert len(representation.Items) == len(model_parts(
        model_symbol_for(product),
        *(value.meters for value in (*product.footprint, product.height)), ports=product.ports))
    ifc_points = {tuple(round(value, 9) for value in point)
                  for part in representation.Items for point in part.Coordinates.CoordList}
    assert ifc_points == glb_points

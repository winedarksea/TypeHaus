"""Coffee-table floor power: placement, protection and failure-mode regressions."""

from dataclasses import replace

import pytest
from shapely.affinity import translate
from shapely.geometry import Polygon

from typehaus.checks import run_from_model
from typehaus.emit.draw.electricalplan import build_electrical_plan
from typehaus.emit.draw.scene import Text
from typehaus.model import ElectricalDevice, Mount, MountKind, PlanModel, Storey, ft, inch, pt
from typehaus.resolve import resolve
from typehaus.takeoff.electrical import panel_schedule
from typehaus.takeoff.placeables import placeables_takeoff

OUTLET = "ED-M-LIVING-FLOOR-RC1"
LISTING_CHECK = "code.E3905_7_floor_boxes"
FRAMING_CHECK = "electrical.floor_box_framing"


def _findings(model, check_id):
    return run_from_model(model, [], only=check_id).findings


def test_coffee_table_floor_box_placement_and_circuit(catlin_model_ro):
    model = catlin_model_ro
    objects = {item.tag: item for item in model.canvas_objects}
    outlet = objects[OUTLET]
    table = objects["FURN-M-PUZZLE-COFFEE-TABLE"]
    assert Polygon(table.footprint).contains(Polygon(outlet.footprint))
    assert outlet.position == pytest.approx(table.position)
    assert outlet.body_z1_m == pytest.approx(table.body_z0_m)
    assert outlet.body_z1_m - outlet.body_z0_m == pytest.approx(inch(6.55).meters)
    assert outlet.body_z0_m < 0  # The box extends into the joist cavity.

    row = next(row for row in panel_schedule(model) if row["circuit"] == "CKT-RC-MAIN")
    assert OUTLET in row["devices"]
    assert (row["breaker_amps"], row["volts"], row["afci"]) == (20, 120, True)
    assert row["connected_va"] == 1500  # Existing general-receptacle allowance.
    takeoff = next(row for row in placeables_takeoff(model) if row["type"] == outlet.type_ref)
    assert takeoff["count"] == 1
    assert takeoff["tags"] == [OUTLET]
    assert any(f.result.value == "pass" and OUTLET in f.element_tags
               for f in _findings(model, LISTING_CHECK))
    for cid in (FRAMING_CHECK, "electrical.circuit_refs",
                "code.E3902_16_afci", "code.E3902_gfci_locations"):
        assert not [f for f in _findings(model, cid) if f.result.value in {"fail", "unknown"}]
    labels = [node.content for node in build_electrical_plan(model, "main").nodes
              if isinstance(node, Text)]
    assert "FLOOR BOX / CKT-RC-MAIN" in labels


def test_floor_box_cannot_use_an_ordinary_wall_receptacle_type(catlin_model_ro):
    model = catlin_model_ro
    elements = model.plan.storey_elements("main")
    plan = model.plan.with_elements("main", tuple(
        item.model_copy(update={"type_ref": "ED-T-RECEPTACLE"}) if item.tag == OUTLET else item
        for item in elements))
    findings = _findings(replace(model, plan=plan), LISTING_CHECK)
    assert any(f.result.value == "unknown" and OUTLET in f.element_tags for f in findings)


def test_floor_box_gltf_body_is_below_the_floor(catlin_model_ro):
    from typehaus.emit.gltf.canvas_objects import _add_canvas_box
    from typehaus.emit.gltf.mesh import _MeshBuilder

    outlet = next(item for item in catlin_model_ro.canvas_objects if item.tag == OUTLET)
    mesh = _MeshBuilder()
    _add_canvas_box(mesh, outlet, inch(6.55).meters)
    elevations = [vertex[1] for vertices, _indices in mesh._buckets.values() for vertex in vertices]
    assert min(elevations) == pytest.approx(outlet.body_z0_m)
    assert max(elevations) == pytest.approx(outlet.body_z1_m)


def test_floor_box_cannot_intersect_a_joist(catlin_model_ro):
    model = catlin_model_ro
    outlet = next(item for item in model.canvas_objects if item.tag == OUTLET)
    offset = -inch(8).meters  # From bay center onto the joist at y=96".
    moved = replace(outlet, position=(outlet.position[0], outlet.position[1] + offset),
                    footprint=tuple(translate(Polygon(outlet.footprint), yoff=offset)
                                    .exterior.coords)[:-1])
    copy = replace(model, canvas_objects=[moved if item.tag == OUTLET else item
                                         for item in model.canvas_objects])
    findings = _findings(copy, FRAMING_CHECK)
    assert any(f.result.value == "fail" and "joist-0-006" in f.message for f in findings)


def test_floor_box_loses_afci_when_its_breaker_loses_protection(catlin_model_ro):
    model = catlin_model_ro
    circuits = tuple(c.model_copy(update={"afci": False}) if c.tag == "CKT-RC-MAIN" else c
                     for c in model.plan.library.circuits)
    library = model.plan.library.model_copy(update={"circuits": circuits})
    plan = model.plan.model_copy(update={"library": library})
    findings = _findings(replace(model, plan=plan), "code.E3902_16_afci")
    assert any(f.result.value == "fail" and "CKT-RC-MAIN" in f.element_tags for f in findings)


def test_recessed_floor_box_ifc_body_is_below_the_floor(project, catlin_plan, tmp_path):
    import ifcopenshell
    import ifcopenshell.geom

    from typehaus.emit.ifc.emitter import emit_ifc

    outlet = next(item for item in catlin_plan.storey_elements("main") if item.tag == OUTLET)
    device = ElectricalDevice(
        uid="TESTFRC001", tag="ED-FLOOR", kind=outlet.kind, type_ref=outlet.type_ref,
        position=pt(ft(0), ft(0)),
        mount=Mount(kind=MountKind.FLOOR, elevation=ft(0), recessed_into_host_surface=True))
    plan = PlanModel(project=project, library=catlin_plan.library,
                     storeys=(Storey(tag="main", elevation=ft(0),
                                     default_ceiling_height=ft(9)),),
                     elements={"main": (device,)})
    model, _ = resolve(plan)
    file = ifcopenshell.open(str(emit_ifc(model, tmp_path / "floor.ifc")))
    exported = next(item for item in file.by_type("IfcOutlet") if item.Name == "ED-FLOOR")
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, exported)
    elevations = shape.geometry.verts[2::3]
    assert min(elevations) == pytest.approx(-inch(6.55).meters)
    assert max(elevations) == pytest.approx(0)

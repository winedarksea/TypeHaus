from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from typehaus.model import (
    Appliance,
    ApplianceType,
    Building,
    ClearancePolicy,
    ClearanceZone,
    Door,
    DoorType,
    Furniture,
    FurnitureType,
    Footprint2D,
    Library,
    Location,
    PlanModel,
    PlacementStrategy,
    Project,
    Service,
    ServicePort,
    Site,
    Storey,
    Mount,
    MountKind,
    ModelRepresentation,
    Node,
    Wall,
    WallAttachment,
    deg,
    ft,
    m,
    pt,
    from_node,
)
from typehaus.model.canvas import canvas_object_types, canvas_objects, resolved_canvas_objects
from typehaus.resolve import resolve
from typehaus.source.loader import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.macros import (_rooms_with_moved_boundaries, assign_placeable_room, attach_placeable,
                                    detach_placeable, duplicate_canvas_object, move_nodes, move_placeable, place_placeable,
                                    rehost_opening, rotate_placeable)


def test_canvas_catalog_and_objects_use_one_normalized_contract() -> None:
    furniture_type = FurnitureType(
        tag="F-SOFA", name="Sofa", footprint=(ft(7), ft(3)), height=ft(3),
        model_representation=ModelRepresentation(primitive="cylinder"),
    )
    appliance_type = ApplianceType(
        tag="A-RANGE", name="Electric range", footprint=(ft(2, 6), ft(2, 6)), height=ft(3),
        needs=frozenset({Service.POWER_240}),
        ports=(ServicePort(tag="power", service=Service.POWER_240,
                           position=(ft(0), ft(0), ft(0))),),
    )
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=ft(0), default_ceiling_height=ft(8)),),
        library=Library(furniture_types=(furniture_type,), appliance_types=(appliance_type,)),
        elements={"main": (
            Furniture(uid="furniture-1", tag="F-1", type_ref="F-SOFA", position=pt(ft(1), ft(1))),
            Appliance(uid="appliance-1", tag="A-1", type_ref="A-RANGE", position=pt(ft(2), ft(1))),
        )},
    )

    catalog = {item["tag"]: item for item in canvas_object_types(plan)}
    assert catalog["F-SOFA"]["placement"] == PlacementStrategy.FREE_PLACED.value
    assert catalog["F-SOFA"]["model_primitive"] == "cylinder"
    assert catalog["A-RANGE"]["ports"] == [{"tag": "power", "service": "power_240"}]
    assert catalog["A-RANGE"]["mount"] == {"kind": "floor", "elevation_m": None, "drop_m": None}
    objects = {item["tag"]: item for item in canvas_objects(plan)}
    assert objects["F-1"]["domain"] == "furniture"
    assert objects["A-1"]["domain"] == "appliance"

    resolved, findings = resolve(plan)
    assert not [finding for finding in findings if finding.severity.value == "error"]
    range_object = next(item for item in resolved.canvas_objects if item.tag == "A-1")
    assert range_object.domain == "appliance"
    assert len(range_object.footprint) == 4
    assert range_object.position == (ft(2).meters, ft(1).meters)


def test_profiled_clearances_rotate_and_report_physical_encroachments() -> None:
    clearance = ClearanceZone(
        footprint=Footprint2D(points=(pt(m(-1), m(-1)), pt(m(1), m(-1)),
                                      pt(m(1), m(1)), pt(m(-1), m(1)))),
        purpose="fixture access", policy=ClearancePolicy.REQUIRED, code_profile="MN/IRC",
    )
    protected = FurnitureType(tag="F-PROTECTED", name="Protected", footprint=(m(.4), m(.4)),
                              height=m(1), clearances=(clearance,))
    obstacle = FurnitureType(tag="F-OBSTACLE", name="Obstacle", footprint=(m(.4), m(.4)), height=m(1))
    project = Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                      building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0)))
    plan = PlanModel(
        project=project,
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(furniture_types=(protected, obstacle)),
        elements={"main": (
            Furniture(uid="protected", tag="PROTECTED", type_ref="F-PROTECTED", position=pt(m(0), m(0)),
                      rotation=deg(45)),
            Furniture(uid="obstacle", tag="OBSTACLE", type_ref="F-OBSTACLE", position=pt(m(.8), m(0))),
        )},
    )
    inactive_model, inactive_findings = resolve(plan)
    assert not next(item for item in inactive_model.canvas_objects if item.tag == "PROTECTED").required_clearances
    assert not [item for item in inactive_findings if "clearance_conflict" in item.check_id]

    active = plan.model_copy(update={"project": project.model_copy(update={"active_code_profile": "MN/IRC"})})
    active_model, findings = resolve(active)
    resolved_zone = next(item for item in active_model.canvas_objects if item.tag == "PROTECTED").required_clearances[0]
    assert resolved_zone[0][0] == pytest.approx(0)
    assert resolved_zone[0][1] == pytest.approx(-2**.5)
    conflicts = [item for item in findings if item.check_id == "integrity.placeable_required_clearance_conflict"]
    assert len(conflicts) == 1
    assert conflicts[0].element_tags == ("PROTECTED", "OBSTACLE")

    advisory = protected.model_copy(update={"clearances": (clearance.model_copy(update={
        "policy": ClearancePolicy.RECOMMENDED, "code_profile": None,
    }),)})
    advisory_plan = plan.model_copy(update={"library": Library(furniture_types=(advisory, obstacle))})
    _, advisory_findings = resolve(advisory_plan)
    assert [item.severity.value for item in advisory_findings
            if item.check_id == "integrity.placeable_recommended_clearance_conflict"] == ["warn"]


def test_door_swing_and_framing_bumper_share_the_resolved_overlay_contract() -> None:
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    initial, _ = resolve(plan)
    original = next(item for item in initial.openings if item.is_door and item.swing_clearance)
    opening_storey = next(wall.storey for wall in initial.walls if wall.tag == original.host_wall)
    center = tuple(sum(point[index] for point in original.swing_clearance) / len(original.swing_clearance)
                   for index in (0, 1))
    furniture_type = FurnitureType(tag="F-SWING", name="Swing obstacle", footprint=(m(.3), m(.3)), height=m(1))
    obstacle = Furniture(uid="swing-obstacle", tag="F-SWING-1", type_ref="F-SWING",
                         position=pt(m(center[0]), m(center[1])))
    plan = plan.model_copy(update={
        "library": plan.library.model_copy(update={"furniture_types": (*plan.library.furniture_types, furniture_type)}),
        "elements": {**plan.elements, opening_storey: (*plan.storey_elements(opening_storey), obstacle)},
    })
    model, findings = resolve(plan)
    opening = next(item for item in model.openings if item.tag == original.tag)
    assert len(opening.swing_clearance) == 10 and len(opening.framing_bumper) == 4
    assert any(item.check_id == "integrity.door_swing_conflict" and item.severity.value == "warn"
               for item in findings)
    record = next(item for item in resolved_canvas_objects(model) if item["tag"] == original.tag)
    assert record["recommended_clearances"] and record["framing_bumper"]


def test_placeable_macros_preserve_typed_location_intent() -> None:
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=ft(0), default_ceiling_height=ft(8)),),
        elements={"main": (Furniture(uid="furniture-1", tag="F-1", type_ref="F-SOFA",
                                      position=pt(ft(1), ft(1))),)},
    )
    rotated = rotate_placeable(plan, "main", tag="F-1", degrees=31).ops[0]
    assert rotated.fields["rotation"].expr == "deg(30)"
    freely_rotated = rotate_placeable(plan, "main", tag="F-1", degrees=31, free_rotation=True).ops[0]
    assert freely_rotated.fields["rotation"].expr == "deg(31)"
    detached = detach_placeable(plan, "main", tag="F-1", position=(2.0, 3.0)).ops[0]
    assert detached.fields["location"] == "__haus_delete_field__"
    assert detached.fields["position"].expr == "pt(m(2), m(3))"
    with pytest.raises(Exception, match="no wall"):
        attach_placeable(plan, "main", tag="F-1", wall="W-1", face="left", distance=1)
    with pytest.raises(Exception, match="no room"):
        assign_placeable_room(plan, "main", tag="F-1", room="RM-1")


def test_placeable_macro_builds_a_catalog_typed_add_operation() -> None:
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=ft(0), default_ceiling_height=ft(8)),),
        library=Library(furniture_types=(FurnitureType(tag="F-SOFA", name="Sofa",
                                                       footprint=(ft(7), ft(3)), height=ft(3)),)),
    )
    op = place_placeable(plan, "main", type_ref="F-SOFA", position=(2.0, 3.0)).ops[0]
    assert (op.op, op.type, op.hint_list) == ("add", "Furniture", "MAIN_PLACEABLES")
    assert op.fields["type_ref"].expr == '"F-SOFA"'


def test_duplicate_placeable_uses_a_fresh_tag_and_offset_position() -> None:
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(furniture_types=(FurnitureType(tag="F-SOFA", name="Sofa", footprint=(m(1), m(1)), height=m(1)),)),
        elements={"main": (Furniture(uid="original", tag="F-1", type_ref="F-SOFA", position=pt(m(1), m(2))),)},
    )
    (op,) = duplicate_canvas_object(plan, "main", tag="F-1").ops
    assert (op.op, op.type, op.tag, op.hint_list) == ("add", "Furniture", "F-1-COPY", "MAIN_PLACEABLES")
    assert op.fields["position"].expr == "pt(m(1.3048), m(2.3048))"


def test_catlin_furniture_palette_operation_writes_and_reloads(tmp_path: Path) -> None:
    source_house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    house = tmp_path / "catlin"
    shutil.copytree(source_house, house)
    assets = house / "assets"
    assets.mkdir()
    (assets / "placeables.json").write_text(
        '{"revision": 1, "types": [{"domain": "furniture", "tag": "F-PALETTE", '
        '"name": "Palette chair", "footprint_m": [0.6, 0.6], "height_m": 0.9}, '
        '{"domain": "appliance", "tag": "A-PALETTE", "name": "Palette appliance", '
        '"footprint_m": [0.6, 0.6], "height_m": 0.9}]}'
    )
    loaded = load_plan(house).plan
    assert loaded is not None
    type_ref = "F-PALETTE"
    result = place_placeable(loaded, "main", type_ref=type_ref, position=(2.0, 2.0))
    appliance = place_placeable(loaded, "main", type_ref="A-PALETTE", position=(3.0, 2.0))
    coordinator = ProjectCoordinator(house)
    placeables_source = house / "plan" / "placeables.py"
    before = placeables_source.read_text()
    coordinator.apply_patch([*result.ops, *appliance.ops], coordinator.revision())
    source = placeables_source.read_text()
    assert "Furniture(" in source and "Appliance(" in source
    coordinator.undo()
    assert placeables_source.read_text() == before
    coordinator.redo()
    reloaded = load_plan(house).plan
    assert reloaded is not None
    assert any(item.type_ref == type_ref for item in reloaded.storey_elements("main")
               if item.element_kind == "Furniture")
    assert any(item.type_ref == "A-PALETTE" for item in reloaded.storey_elements("main")
               if item.element_kind == "Appliance")


def test_catlin_mep_starter_instances_use_the_shared_typed_catalog() -> None:
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    catalog = {item["tag"]: item for item in canvas_object_types(plan)}
    assert catalog["REG-T-SUPPLY"]["ports"] == [{"tag": "supply", "service": "supply_air"}]
    assert catalog["ED-T-RECEPTACLE"]["ports"] == [{"tag": "power", "service": "power_120"}]
    typed = ("Register", "Equipment", "ElectricalDevice")
    assert all(item.type_ref for storey in plan.storeys for item in plan.storey_elements(storey.tag)
               if item.element_kind in typed)


def test_opening_rehost_updates_host_and_topology_position_atomically() -> None:
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=ft(0), default_ceiling_height=ft(8)),),
        library=Library(door_types=(DoorType(tag="D-36", width=ft(3), height=ft(6, 8)),)),
        elements={"main": (
            Node(tag="N-1", position=pt(m(0), m(0))), Node(tag="N-2", position=pt(m(5), m(0))),
            Node(tag="N-3", position=pt(m(0), m(2))), Node(tag="N-4", position=pt(m(5), m(2))),
            Wall(tag="W-1", start_node="N-1", end_node="N-2", assembly="A"),
            Wall(tag="W-2", start_node="N-3", end_node="N-4", assembly="A"),
            Door(tag="D-1", host="W-1", type_ref="D-36", position=from_node("N-1", m(1))),
        )},
    )
    op = rehost_opening(plan, "main", tag="D-1", host="W-2", along=1.0).ops[0]
    assert op.fields["host"] == "W-2"
    assert 'from_node("N-3"' in op.fields["position"].expr
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    loaded = load_plan(house).plan
    assert loaded is not None
    model, _ = resolve(loaded)
    opening = next(item for item in resolved_canvas_objects(model) if item["kind"] == "door")
    assert opening["domain"] == "opening"
    assert opening["host"]
    assert opening["storey"]
    assert len(opening["footprint"]) == 4


def test_mount_resolution_uses_floor_wall_and_ceiling_reference_frames() -> None:
    furniture_type = FurnitureType(tag="F", name="F", footprint=(ft(1), ft(1)), height=ft(1))
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(10), default_ceiling_height=m(3)),),
        library=Library(furniture_types=(furniture_type,)),
        elements={"main": (
            Furniture(tag="FLOOR", type_ref="F", position=pt(m(0), m(0))),
            Furniture(tag="WALL", type_ref="F", position=pt(m(1), m(0)), mount=Mount(kind=MountKind.WALL, elevation=m(1.2))),
            Furniture(tag="CEILING", type_ref="F", position=pt(m(2), m(0)), mount=Mount(kind=MountKind.CEILING, drop=m(0.3))),
        )},
    )
    model, findings = resolve(plan)
    assert not [finding for finding in findings if finding.severity.value == "error"]
    heights = {item.tag: item.z_m for item in model.canvas_objects}
    assert heights == {"FLOOR": 10.0, "WALL": 11.2, "CEILING": 12.7}


def test_placeable_drag_updates_the_explicit_containing_room_assignment() -> None:
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    op = move_placeable(plan, "main", tag="FX-M-BATH1-WC", position=(0.6096, 7.3152)).ops[0]
    assert op.fields["room"] == "RM-M-BATH1"


def test_resolved_attachment_preserves_the_authored_wall_face() -> None:
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    furniture_type = FurnitureType(tag="F-ATTACHED", name="Attached shelf", footprint=(m(.6), m(.2)), height=m(.3))
    attached = Furniture(uid="ATTACHED001", tag="F-ATTACHED-1", type_ref="F-ATTACHED",
                         position=pt(m(0), m(0)), location=Location(attachment=WallAttachment(
                             wall_ref="W-M-BAE", face="right", distance_from_start=m(1),
                         )))
    model, findings = resolve(plan.model_copy(update={
        "library": plan.library.model_copy(update={"furniture_types": (*plan.library.furniture_types, furniture_type)}),
        "elements": {**plan.elements, "main": (*plan.storey_elements("main"), attached)},
    }))
    assert not [item for item in findings if item.severity.value == "error"]
    record = next(item for item in resolved_canvas_objects(model) if item["tag"] == "F-ATTACHED-1")
    assert record["attachment"] == {"wall": "W-M-BAE", "face": "right"}


def test_only_rooms_with_complete_moved_boundary_translate_with_contents() -> None:
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    movable = {item.tag for item in plan.storey_elements("main") if item.element_kind == "Node" and
               not getattr(item, "anchored", False)}
    all_rooms = _rooms_with_moved_boundaries(plan, "main", movable)
    moved = next(movable - {candidate} for candidate in movable
                 if _rooms_with_moved_boundaries(plan, "main", movable - {candidate}) < all_rooms)
    translated = _rooms_with_moved_boundaries(plan, "main", moved)
    result = move_nodes(plan, "main", sorted(moved), dx=0.1, dy=0)
    moved_room_tags = {item.tag for item in result.ops if item.type == "Room"}
    assert translated and translated < all_rooms
    assert moved_room_tags == translated

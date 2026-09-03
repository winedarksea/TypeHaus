from __future__ import annotations

from pathlib import Path

import pytest
from library.placeables.fixtures import TOILET, TOILET_WALL_HUNG

from typehaus.resolve.room_floor import room_floor_elevation

from typehaus.model import (
    Appliance,
    ApplianceType,
    Building,
    ClearancePolicy,
    ClearanceZone,
    Door,
    DoorType,
    Footprint2D,
    Furniture,
    FurnitureType,
    Library,
    Location,
    ModelRepresentation,
    Mount,
    MountKind,
    Node,
    PlacementStrategy,
    PlanModel,
    Project,
    Register,
    RegisterType,
    Service,
    ServicePort,
    Site,
    Storey,
    Wall,
    WallAttachment,
    deg,
    from_node,
    ft,
    inch,
    m,
    pt,
)
from typehaus.model.canvas import canvas_object_types, canvas_objects, resolved_canvas_objects
from typehaus.model.enums import DuctSystem
from typehaus.resolve import resolve
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.loader import load_plan
from typehaus.source.ops import RawExpr
from typehaus.source.macros import (
    _rooms_with_moved_boundaries,
    assign_placeable_room,
    attach_placeable,
    detach_placeable,
    duplicate_canvas_object,
    move_nodes,
    move_placeable,
    place_placeable,
    rehost_opening,
    rotate_placeable,
    set_placeable_mount,
)
from _helpers import CATLIN, copy_house


@pytest.mark.parametrize(("fixture_type", "expected_depth_inches"), (
    (TOILET, 28),
    (TOILET_WALL_HUNG, 19.3),
))
def test_water_closet_fixture_size_is_separate_from_required_code_clearance(
        fixture_type, expected_depth_inches: float) -> None:
    """A real bowl stays small; its code envelope is a distinct 30" by depth+24" polygon.

    24": Minn. R. 1309.0010 subp. 3.D deletes the IRC chapter P2705.1 lives in and 1309.0307
    sends fixtures to ch. 4714, which adopts UPC 402.5 unamended. See
    ``library/placeables/fixtures.py`` for the citation trail.
    """
    assert tuple(dimension.inches for dimension in fixture_type.footprint) == pytest.approx(
        (20 if fixture_type is TOILET else 15, expected_depth_inches))
    zone = fixture_type.clearances[0]
    assert zone.policy is ClearancePolicy.REQUIRED
    assert zone.code_profile == "MN/IRC"
    actual_inches = tuple(
        coordinate.inches for point in zone.footprint.points for coordinate in (point.x, point.y)
    )
    assert actual_inches == pytest.approx((
            -15, -(expected_depth_inches / 2 + 24),
            15, -(expected_depth_inches / 2 + 24),
            15, expected_depth_inches / 2,
            -15, expected_depth_inches / 2,
        ))


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
    assert catalog["A-RANGE"]["mount"] == {"kind": "floor", "elevation_m": None, "drop_m": None,
                                           "recessed_into_host_surface": False}
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
    copy_house(source_house, house)
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
    assert catalog["REG-T-ERV-SUP"]["ports"] == [{"tag": "supply", "service": "supply_air"}]
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
            # An explicit elevation wins over the storey's ceiling height: a fixture hung
            # at a stated height stays there whatever the ceiling above it does.
            Furniture(tag="CEILING_AT_HEIGHT", type_ref="F", position=pt(m(3), m(0)),
                      mount=Mount(kind=MountKind.CEILING, elevation=m(2.4))),
        )},
    )
    model, findings = resolve(plan)
    assert not [finding for finding in findings if finding.severity.value == "error"]
    heights = {item.tag: item.z_m for item in model.canvas_objects}
    assert heights == {"FLOOR": 10.0, "WALL": 11.2, "CEILING": 12.7,
                       "CEILING_AT_HEIGHT": 12.4}


def test_catlin_ceiling_lights_resolve_to_their_authored_mount_height() -> None:
    """Lights used to resolve to the floor: ``mount_height`` was a second, unread field.

    The generic ``ED-T-LIGHT`` this once read is retired — every fixture is a real
    ``LuminaireType`` now — so the three mounting rules a luminaire can be authored under
    are pinned instead: a recessed can sits on the ceiling plane, a hanging fixture sits
    its stated drop below it, and a stated elevation wins outright (the attic's cathedral).
    """
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    model, _ = resolve(plan)
    storey_elevation = {storey.tag: storey.elevation.meters for storey in plan.storeys}
    ceiling = {storey.tag: storey.default_ceiling_height.meters for storey in plan.storeys}
    by_tag = {item.tag: item for item in model.canvas_objects}

    def above_floor(tag: str) -> float:
        item = by_tag[tag]
        return item.z_m - storey_elevation[item.storey]

    # No fixture resolves to the floor, which is the regression this test exists for.
    luminaires = {product.tag for product in plan.library.electrical_device_types
                  if getattr(product, "form", None) is not None}
    placed = [item for item in model.canvas_objects if item.type_ref in luminaires]
    assert len(placed) > 50
    # ** ONE FIXTURE IS LEGITIMATELY BELOW ITS STOREY DATUM, AND IT IS NOT A FALL. **
    # ED-M-STAIR-LT is a step light on W-SG-E1's east face, lighting the head of
    # ST-SG-PORCH. That wall's TOP is 0'-0" — the `main` datum itself — so every point on the
    # face it hangs on is below the floor this arithmetic measures from, and its authored
    # elevation is a negative number on purpose. Asserted against what it was authored as,
    # rather than excused, so the heuristic below stays sharp for the other fifty-odd.
    below_datum = {"ED-M-STAIR-LT": -ft(0, 8).meters}
    for tag, want in below_datum.items():
        assert above_floor(tag) == pytest.approx(want, abs=1e-6), tag
    assert all(above_floor(item.tag) > 0.05 for item in placed
               if item.tag not in below_datum)
    # The 0.5 m line is the "did it fall to the floor" heuristic, and exactly one fixture is
    # legitimately below it: ED-M-PANTRY-LT, RM-M-PANTRY's 6'-0" vertical WALL slot, whose
    # authored base is 1'-6" so the lit line runs 1'-6"..7'-6" past every shelf edge.
    # ``resolved_mount_elevation`` returns the BASE of a body and LuminaireType.height
    # measures up from it, so a low z_m here is the fixture working, not falling. Naming it
    # keeps the heuristic sharp for the other fifty-odd.
    low = {item.tag for item in placed
           if above_floor(item.tag) <= 0.5 and item.tag not in below_datum}
    assert low == {"ED-M-PANTRY-LT"}, sorted(low)
    # ...and it is 1'-6" off the floor it STANDS on, which is the point of the paragraph
    # below: RM-M-PANTRY sits on SL-M-DECK like RM-M-LIVING, so its floor is 15/16" above
    # the storey datum and the raw z_m reads 0.481 m where 1'-6" is 0.457 m.
    pantry = next(room for room in model.rooms if room.tag == "RM-M-PANTRY")
    pantry_floor = room_floor_elevation(model, pantry) - storey_elevation["main"]
    assert above_floor("ED-M-PANTRY-LT") == pytest.approx(pantry_floor + ft(1, 6).meters)

    # A placeable is measured off the floor it STANDS on, not off the storey datum
    # (``resolve/room_floor.py``) — and on this storey those are not the same plane. The
    # datum is top-of-joists; RM-M-LIVING sits on SL-M-DECK, whose polished cap is pinned
    # to the wood bays' plywood top (``params/main_deck.py::MAIN_FINISHED_FLOOR``).
    # So everything in the living room stands
    # 3/4" above everything in RM-M-BED next door.
    #
    # ** That step is the other rooms being wrong, not this one. ** ``room_floor_elevation``
    # prefers a slab top under the room and otherwise falls back to the wall base, never
    # adding a FloorSystem's subfloor — so a room over joists resolves its floor 3/4" low.
    # RM-M-LIVING is simply the only main-storey room with a slab under it. Recorded in
    # plans/TODO.md; deriving it here rather than writing 0.75 twice keeps this test honest
    # either way.
    living = next(room for room in model.rooms if room.tag == "RM-M-LIVING")
    living_floor = room_floor_elevation(model, living) - storey_elevation["main"]

    # A recessed can hangs off the ceiling plane; its housing goes up into the bay.
    # RM-M-BED is over joists, so its floor IS the datum and there is no offset to add.
    assert above_floor("ED-M-BED-CAN2") == pytest.approx(ceiling["main"])
    # A hanging fixture sits its whole assembly below the ceiling — measured from the
    # living room's own floor, and so from its own ceiling plane.
    assert above_floor("ED-M-DINING-PEND") == pytest.approx(
        living_floor + ceiling["main"] - ft(3, 6).meters)
    # A stated elevation wins: the attic ceiling is a 6:12 rake, not the storey default.
    # 7'-1 1/2" is `1 1/2" + x/2` at this can's x=22'-0" — the plane it is recessed into.
    assert above_floor("ED-A-EAST-CAN3") == pytest.approx(ft(7, 1.5).meters)

    switch = next(item for item in model.canvas_objects if item.tag == "ED-M-LIVING-SW")
    assert switch.z_m == pytest.approx(living_floor + inch(48).meters)


def test_placeable_drag_updates_the_explicit_containing_room_assignment() -> None:
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    op = move_placeable(plan, "main", tag="FX-M-BATH1-WC", position=(0.6096, 7.3152)).ops[0]
    assert op.fields["room"] == "RM-M-BATH1"


def test_dragging_a_floor_drained_wc_carries_its_sleeve_and_drain_run() -> None:
    """The flange is not a symbol: a cast-in sleeve and a routed drop sit under it.

    FX-B-BATH-WC drains under its own bowl (no ``drain_position`` override, no hot-water
    connection), so a drag has to re-point SP-B-BATH-WC and the head of PR-B-BATH-DRAIN with
    it. Its riser is authored as the same plan point twice (two inverts), so BOTH leading
    vertices have to move or the drop becomes a slope. Leaving them behind is exactly the
    76c1871 defect: a 6.46" nudge that built cleanly and only showed up in
    `mep.sleeve_alignment`.

    Read on the basement's WC, since the main floor's own WC lost its cast sleeve when the
    deck overhaul framed it.
    """
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    fixture = next(item for item in plan.storey_elements("basement")
                   if item.tag == "FX-B-BATH-WC")
    old_x, old_y = fixture.position.xy_m
    result = move_placeable(plan, "basement", tag="FX-B-BATH-WC",
                            position=(old_x + 0.1, old_y - 0.05))

    assert [(op.type, op.tag) for op in result.ops] == [
        ("Fixture", "FX-B-BATH-WC"),
        ("SleevePenetration", "SP-B-BATH-WC"),
        ("PipeRun", "PR-B-BATH-DRAIN"),
    ]
    sleeve = next(item for item in plan.all_elements() if item.tag == "SP-B-BATH-WC")
    sleeve_x, sleeve_y = sleeve.position.xy_m
    assert _expr_point(result.ops[1].fields["position"]) == pytest.approx(
        (sleeve_x + 0.1, sleeve_y - 0.05), abs=1e-3)

    run = next(item for item in plan.all_elements() if item.tag == "PR-B-BATH-DRAIN")
    assert run.path[0] == run.path[1], "the riser's duplicated vertex pair is the point of this test"
    moved_path = _expr_path(result.ops[2].fields["path"])
    assert len(moved_path) == len(run.path)
    for index, vertex in enumerate(run.path[:2]):
        assert moved_path[index] == pytest.approx(
            (vertex.xy_m[0] + 0.1, vertex.xy_m[1] - 0.05), abs=1e-3), f"vertex {index} did not follow"
    # The downstream legs are the tie-in into the collector and must not drift with the bowl.
    for index, vertex in enumerate(run.path[2:], start=2):
        assert moved_path[index] == pytest.approx(vertex.xy_m, abs=1e-9)

    joined = " | ".join(result.warnings)
    assert "SP-B-BATH-WC" in joined and "PR-B-BATH-DRAIN" in joined
    # …and the runs that merely *serve* the WC (its supply, its vent, the house collector)
    # are reported as left behind rather than silently dragged twenty feet across the plan.
    assert "PR-B-BATH-VENT" in joined and "left as routed" in joined


def test_an_authored_drain_position_pins_the_drain_while_the_fixture_moves() -> None:
    """``drain_position`` is the author saying where the waste leaves, independently of the
    bowl — FX-B-BATH-LAV authors one on W-B-BA-N's centreline and its waste leaves there,
    not under the basin. Moving the basin says nothing about that outlet, so the macro emits
    its one op and keeps its hands off SP-B-BATH-LAV."""
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    result = move_placeable(plan, "basement", tag="FX-B-BATH-LAV", position=(5.1, 6.2))
    assert [(op.type, op.tag) for op in result.ops] == [("Fixture", "FX-B-BATH-LAV")]
    assert result.warnings == ()


def test_coupled_drain_move_writes_source_that_reloads(tmp_path: Path) -> None:
    """Followers are only real if they land in source, which is why ``SleevePenetration``
    and ``PipeRun`` are ``loader._UI_EDITABLE_KINDS``: a follower op aimed at a module
    without the ``# haus: editable`` header is dropped at commit and the drag half-applies,
    leaving the flange and the pipe further apart than before the move."""
    house = tmp_path / "catlin"
    copy_house(CATLIN, house)
    plan = load_plan(house).plan
    assert plan is not None
    fixture = next(item for item in plan.storey_elements("basement")
                   if item.tag == "FX-B-BATH-WC")
    old_x, old_y = fixture.position.xy_m
    ops = move_placeable(plan, "basement", tag="FX-B-BATH-WC",
                         position=(old_x + 0.1, old_y - 0.05)).ops
    coordinator = ProjectCoordinator(house)
    coordinator.apply_patch(ops, coordinator.revision())

    reloaded = load_plan(house)
    assert reloaded.plan is not None, [finding.message for finding in reloaded.findings]
    moved = {item.tag: item for item in reloaded.plan.all_elements()}
    assert moved["SP-B-BATH-WC"].position.xy_m == pytest.approx(
        (old_x + 0.1, old_y - 0.05), abs=1e-3)
    run = moved["PR-B-BATH-DRAIN"]
    assert run.path[0].xy_m == pytest.approx((old_x + 0.1, old_y - 0.05), abs=1e-3)
    assert run.path[0] == run.path[1]
    # The rewrite replaces vertices in place, so the per-vertex invert list still lines up.
    assert len(run.elevations) == len(run.path)


def _expr_point(value: object) -> tuple[float, float]:
    """Evaluate one emitted ``pt(...)`` back to meters."""
    return _expr_path(RawExpr(f"({value.expr},)"))[0]


def _expr_path(value: object) -> list[tuple[float, float]]:
    points = eval(value.expr, {"pt": pt, "m": m, "ft": ft, "inch": inch})  # noqa: S307 - macro output
    return [point.xy_m for point in points]


def test_mount_height_edit_preserves_the_rest_of_the_authored_mount() -> None:
    """Raising a sconce must not quietly turn it into a floor-standing, non-recessed object.

    ``kind``, ``drop`` and ``recessed_into_host_surface`` are authored intent that a height
    edit is not allowed to drop — the recessed flag in particular decides whether the object
    obstructs a neighbour's clear floor space.
    """
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None

    sconce = set_placeable_mount(plan, "basement", tag="ED-B-WORKSHOP-SW", elevation="6'").ops[0]
    assert (sconce.op, sconce.type) == ("update", "ElectricalDevice")
    assert sconce.fields["mount"].expr == "Mount(kind=MountKind.WALL, elevation=ft(6))"

    can = set_placeable_mount(plan, "basement", tag="ED-B-GYM-CAN1", elevation=2.4).ops[0]
    assert can.fields["mount"].expr == (
        "Mount(kind=MountKind.CEILING, elevation=m(2.4), recessed_into_host_surface=True)")

    pendant = set_placeable_mount(plan, "basement", tag="ED-B-WORKSHOP-PANEL1", elevation="8'").ops[0]
    assert 'drop=' in pendant.fields["mount"].expr

    # An object authored with no mount at all is floor-mounted; raising it states that.
    with pytest.raises(Exception, match="no placeable"):
        set_placeable_mount(plan, "basement", tag="ED-NOPE", elevation="3'")
    with pytest.raises(Exception, match="at or above the floor"):
        set_placeable_mount(plan, "basement", tag="ED-B-WORKSHOP-SW", elevation=-1)


def test_mount_height_edit_writes_source_that_reloads(tmp_path: Path) -> None:
    house = tmp_path / "catlin"
    copy_house(CATLIN, house)
    plan = load_plan(house).plan
    assert plan is not None
    ops = set_placeable_mount(plan, "basement", tag="ED-B-WORKSHOP-SW", elevation="6'").ops
    coordinator = ProjectCoordinator(house)
    coordinator.apply_patch(ops, coordinator.revision())
    reloaded = load_plan(house)
    assert reloaded.plan is not None, [finding.message for finding in reloaded.findings]
    raised = next(item for item in reloaded.plan.storey_elements("basement")
                  if item.tag == "ED-B-WORKSHOP-SW")
    assert raised.mount.elevation.meters == pytest.approx(ft(6).meters)
    assert raised.mount.kind is MountKind.WALL
    # And the resolved model republishes the authored mount beside the resolved height, which
    # is what lets the inspector show a height in the units it was written in.
    model, _ = resolve(reloaded.plan)
    record = next(item for item in resolved_canvas_objects(model) if item["tag"] == "ED-B-WORKSHOP-SW")
    assert record["mount"]["kind"] == "wall"
    assert record["mount"]["elevation_m"] == pytest.approx(ft(6).meters)


def test_fixture_dragged_clear_of_every_room_writes_source_that_still_loads(tmp_path: Path) -> None:
    """A drop outside any resolvable room clears the claim (`_containing_room` returns None),
    and the placeable macros are kind-agnostic — so every placeable's ``room`` must be
    nullable. While ``Fixture.room`` was a required str this legal drag wrote source the
    loader then rejected, taking `haus build` and the live server down until hand-repaired."""
    house = tmp_path / "catlin"
    copy_house(CATLIN, house)
    plan = load_plan(house).plan
    assert plan is not None
    ops = move_placeable(plan, "main", tag="FX-M-BATH1-WC", position=(50.0, 50.0)).ops
    assert ops[0].fields["room"] is None
    coordinator = ProjectCoordinator(house)
    coordinator.apply_patch(ops, coordinator.revision())
    reloaded = load_plan(house)
    assert reloaded.plan is not None, [finding.message for finding in reloaded.findings]
    moved = next(item for item in reloaded.plan.storey_elements("main")
                 if item.tag == "FX-M-BATH1-WC")
    assert moved.room is None


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


def test_generated_symbol_geometry_rides_the_canvas_type_contract() -> None:
    """The wire contract is the seam: Canvas2D, the sheet writers, Panel3D and the glTF
    emitter all render what the engine sends, so both keys have to be present and typed the
    same whether or not the type actually names a symbol."""
    with_symbol = FurnitureType(tag="F-SOFA", name="Sofa", footprint=(ft(7), ft(3)),
                                height=ft(2, 10), plan_symbol="sofa")
    without = FurnitureType(tag="F-BLANK", name="Blank", footprint=(ft(1), ft(1)), height=ft(1))
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=ft(0), default_ceiling_height=ft(8)),),
        library=Library(furniture_types=(with_symbol, without)),
    )
    catalog = {item["tag"]: item for item in canvas_object_types(plan)}
    assert catalog["F-BLANK"]["plan_strokes"] == [] and catalog["F-BLANK"]["model_parts"] == []

    strokes, parts = catalog["F-SOFA"]["plan_strokes"], catalog["F-SOFA"]["model_parts"]
    assert len(strokes) > 1 and len(parts) > 1
    # Colours resolve to hex in the serializer so the UI needs no palette table of its own.
    assert all(part["color"].startswith("#") for part in parts)
    assert all(stroke["fill"] is None or stroke["fill"].startswith("#") for stroke in strokes)
    # Plain JSON lists, not tuples — this crosses an HTTP boundary.
    assert all(isinstance(point, list) and len(point) == 2
               for stroke in strokes for point in stroke["points"])
    assert all(len(part["center"]) == 3 and len(part["size"]) == 3 for part in parts)
    # Geometry is local: the type knows nothing about where an instance was placed.
    assert max(abs(point[0]) for stroke in strokes for point in stroke["points"]) \
        <= ft(7).meters / 2 + 1e-9


def test_catlin_furnished_rooms_resolve_against_the_shared_starter_catalog() -> None:
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    model, findings = resolve(plan)
    assert not [item for item in findings if item.severity.value == "error"
                and "placeable" in item.check_id]
    sofa = next(item for item in model.canvas_objects if item.type_ref == "FURN-SOFA-84")
    assert sofa.room == "RM-M-LIVING" and len(sofa.footprint) == 4
    symbols = {item["tag"]: item["plan_strokes"] for item in canvas_object_types(plan)}
    # The shared fixtures opted in too, so the very first render shows a real glyph.
    assert symbols["FX-LAV-24"] and symbols["EQ-T-BROAN-B210E75RT"] and symbols["ED-T-PANEL"]


def test_a_door_leaf_passes_over_a_flush_body_in_its_sweep() -> None:
    """The sweep is a plan polygon, but a leaf is a solid: below the head it is stopped by
    the same bodies a clear floor space is, and by no others. A recessed floor register lying
    flush in the sweep — the catlin D-A-STUDY / REG-A-HP-EAST case — stops nothing, so the
    check now shares ``clear_floor_space_obstruction`` instead of testing plan overlap alone.
    """
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    plan = load_plan(house).plan
    assert plan is not None
    initial, _ = resolve(plan)
    original = next(item for item in initial.openings if item.is_door and item.swing_clearance)
    opening_storey = next(wall.storey for wall in initial.walls if wall.tag == original.host_wall)
    center = tuple(sum(point[index] for point in original.swing_clearance)
                   / len(original.swing_clearance) for index in (0, 1))
    register_type = RegisterType(tag="REG-T-FLUSH", name="Flush floor register",
                                 footprint=(m(.3), m(.15)), height=m(.025))
    flush = Register(uid="swing-register", tag="REG-SWING", kind=DuctSystem.SUPPLY,
                     type_ref="REG-T-FLUSH", position=pt(m(center[0]), m(center[1])),
                     mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True))
    plan = plan.model_copy(update={
        "library": plan.library.model_copy(update={
            "register_types": (*plan.library.register_types, register_type)}),
        "elements": {**plan.elements,
                     opening_storey: (*plan.storey_elements(opening_storey), flush)},
    })
    _, findings = resolve(plan)

    assert not [item for item in findings
                if item.check_id == "integrity.door_swing_conflict"
                and "REG-SWING" in item.element_tags]

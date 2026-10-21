"""A cassette can terminate on perpendicular framing without hiding missing supports."""

from uuid import UUID

import pytest
from shapely.geometry import Polygon, box

from typehaus import (
    Assembly,
    Building,
    Door,
    DoorType,
    FramingSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    OpeningFrameEndSupports,
    PlanModel,
    Project,
    Site,
    Storey,
    StructuralRole,
    Wall,
    degF,
    from_node,
    ft,
    inch,
    pt,
)
from typehaus.model.remap import ReferenceRemap, remap_ops_for
from typehaus.resolve import resolve
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.frame_end_supports import framed_extent
from typehaus.resolve.framing.pockets import pocket_segments


def _frame_plan(*, supports=True, bad=None, width=78):
    assembly = Assembly(
        tag="INT",
        layers=(
            Layer(
                name="stud",
                material_ref="wood",
                thickness=inch(3.5),
                function=LayerFunction.STRUCTURE,
                framing=FramingSpec(member="2x4"),
            ),
        ),
    )
    narrow = Assembly(
        tag="NARROW",
        layers=(
            Layer(
                name="stud",
                material_ref="wood",
                thickness=inch(2.5),
                function=LayerFunction.STRUCTURE,
                framing=FramingSpec(member="2x3"),
            ),
        ),
    )
    project = Project(
        name="Pocket support",
        project_uuid=UUID("00000000-0000-4000-8000-0000000000d4"),
        site=Site(
            lat=44.9,
            lon=-93.2,
            elevation=ft(830),
            design_temp_heating=degF(-15),
            design_temp_cooling=degF(90),
        ),
        building=Building(name="Pocket support"),
    )
    plan = PlanModel(
        project=project,
        library=Library(
            materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),),
            assemblies=(assembly, narrow),
            door_types=(
                DoorType(
                    tag="DT",
                    width=inch(36),
                    height=inch(80),
                    operation="swing" if bad == "operation" else "pocket",
                    pocket_frame=None if bad == "operation" else "eclisse",
                ),
            ),
        ),
        storeys=(Storey(uid="ST", tag="main", elevation=ft(0), default_ceiling_height=ft(9)),),
    )
    nodes = tuple(
        Node(uid=f"N{i}", tag=f"N{i}", position=pt(inch(x), inch(y)))
        for i, (x, y) in enumerate(((0, 0), (width, 0), (width, 36), (0, 36)))
    )
    walls = tuple(
        Wall(
            uid=f"W{i}",
            tag=f"W{i}",
            start_node=f"N{start}",
            end_node=f"N{end}",
            assembly="NARROW" if bad == "depth" and i == 3 else "INT",
            top=inch(70) if bad == "height" and i == 3 else ft(9),
            structural_role=(
                StructuralRole.BEARING if bad == "bearing" and i == 0 else StructuralRole.NONBEARING
            ),
        )
        for i, (start, end) in enumerate(((0, 1), (1, 2), (2, 3), (3, 0)))
    )
    reference = "ABSENT" if bad == "missing" else "W2" if bad == "disconnected" else "W3"
    door = Door(
        uid="D",
        tag="D",
        host="W0",
        type_ref="DT",
        flip_hinge=True,
        position=from_node("N0", inch(41.25 if bad == "station" else 40.25)),
        frame_end_supports=(
            OpeningFrameEndSupports(start_wall_ref=reference, end_wall_ref="W1")
            if supports
            else None
        ),
    )
    return plan.with_elements("main", (*nodes, *walls, door))


def test_supported_frame_uses_its_full_cavity_and_no_separate_jamb_packs():
    model, findings = resolve(_frame_plan())
    assert not [f for f in findings if f.check_id == "integrity.frame_end_support"]
    opening = model.openings[0]
    assert (opening.frame_start_support_wall, opening.frame_end_support_wall) == ("W3", "W1")
    assert pocket_segments(model.plan, model, opening)[1] == pytest.approx(0)
    host = model.wall("W0")
    assert not [m for m in host.members if m.category in {"jack", "king"}]
    assert next(m.length_m for m in host.members if m.category == "header") == pytest.approx(
        inch(74.5).meters
    )


@pytest.mark.parametrize(
    "bad, message",
    [
        ("missing", "does not exist"),
        ("disconnected", "disconnected"),
        ("depth", "insufficient framing depth"),
        ("height", "vertically"),
        ("station", "structure face"),
        ("bearing", "nonbearing"),
        ("operation", "pocket doors"),
    ],
)
def test_invalid_supports_fail_closed_and_keep_both_jamb_packs(bad, message):
    model, findings = resolve(_frame_plan(bad=bad))
    failures = [f for f in findings if f.check_id == "integrity.frame_end_support"]
    assert len(failures) == 1 and message in failures[0].message
    opening = model.openings[0]
    assert opening.frame_start_support_wall is opening.frame_end_support_wall is None
    assert len([m for m in model.wall("W0").members if m.category in {"jack", "king"}]) == 4


def test_unspecified_supports_keep_conventional_framing_and_end_margin():
    model, findings = resolve(_frame_plan(supports=False))
    assert not [f for f in findings if f.check_id == "integrity.frame_end_support"]
    assert pocket_segments(model.plan, model, model.openings[0])[1] > 0
    assert len([m for m in model.wall("W0").members if m.category in {"jack", "king"}]) == 4


def test_support_references_follow_renames_but_deletions_remain_detectable():
    door = _frame_plan().by_tag("D")
    operations = remap_ops_for(door, ReferenceRemap(renamed={"W3": "WEST"}))
    assert "WEST" in str(operations)
    assert not remap_ops_for(door, ReferenceRemap(deleted=frozenset({"W3"})))


def test_catlin_pantry_geometry_and_corner_members(catlin_plan, catlin_model_ro):
    door = catlin_plan.by_tag("D-M-PANTRY")
    opening = next(op for op in catlin_model_ro.openings if op.tag == door.tag)
    assert door.uid == "MSJJGJTJ42" and door.flip_hinge
    assert door.type_ref == "DT-POCKET-INT-36" and opening.pocket_sign == -1
    assert tuple(value / inch(1).meters + 216 for value in framed_extent(opening)) == pytest.approx(
        (218.75, 293.25)
    )
    assert (opening.center_along_m - opening.width_m / 2) / inch(1).meters + 216 == pytest.approx(
        257.25
    )
    assert pocket_segments(catlin_plan, catlin_model_ro, opening)[1] == pytest.approx(0)
    cavity = box(
        218.75 * inch(1).meters,
        395.25 * inch(1).meters,
        257.25 * inch(1).meters,
        398.75 * inch(1).meters,
    )
    for wall in catlin_model_ro.walls:
        if wall.tag not in {"W-M-PAN-S", "W-M-C5", "W-M-C5B", "W-M-PAN-E"}:
            continue
        for member in wall.members:
            ring, bottom, top = member_footprint(member)
            if (
                bottom >= inch(80).meters
                or member.category == "plate"
                or member.child_key.startswith("pocketsplit-")
            ):
                continue
            assert Polygon(ring).intersection(cavity).area < 1e-9, member.child_key
    supports = [
        m
        for m in catlin_model_ro.wall("W-M-C5B").members
        if m.child_key == "frame-support-D-M-PANTRY-start"
    ]
    assert len(supports) == 1 and supports[0].material == "lsl"
    assert not [
        m
        for m in catlin_model_ro.wall("W-M-PAN-E").members
        if m.child_key.startswith("frame-support-")
    ]


def test_catlin_pantry_lighting_and_shelves_stay_outside_the_cassette(catlin_plan):
    light = catlin_plan.by_tag("ED-M-PANTRY-LT")
    assert light.location.attachment.wall_ref == "W-M-C5B"
    assert light.location.attachment.face == "right"
    assert light.location.attachment.distance_from_start.inches == 6.375
    assert light.mount.elevation.inches == 18
    assert light.controlled_by == ("ED-M-PANTRY-SW",)
    for tag, station in (("ED-M-PANTRY-SW", 8), ("ED-M-KITCH-SW-UC", 12)):
        switch = catlin_plan.by_tag(tag)
        assert switch.location.attachment.wall_ref == "W-M-PAN-E"
        assert switch.location.attachment.distance_from_start.inches == pytest.approx(station)
        assert switch.mount.elevation.inches == 46
    shelves = catlin_plan.by_tag("FURN-M-PANTRY-SHELVES")
    assert shelves.position.x.inches == pytest.approx(256)
    assert shelves.position.y.inches == pytest.approx(416.375)
    bank = catlin_plan.by_tag("SB-M-PANTRY")
    assert [bay.width.inches for bay in bank.bays] == pytest.approx([36.25, 36.25])


def test_a_single_support_retains_the_opposite_conventional_jamb_pack():
    plan = _frame_plan(width=100)
    door = plan.by_tag("D").model_copy(
        update={"frame_end_supports": OpeningFrameEndSupports(start_wall_ref="W3")}
    )
    plan = plan.with_elements(
        "main",
        (door if element.tag == door.tag else element for element in plan.storey_elements("main")),
    )
    model, findings = resolve(plan)
    assert not [f for f in findings if f.check_id == "integrity.frame_end_support"]
    opening = model.openings[0]
    assert opening.frame_start_support_wall == "W3" and opening.frame_end_support_wall is None
    assert pocket_segments(plan, model, opening)[1] == pytest.approx(0)
    packs = [m for m in model.wall("W0").members if m.category in {"king", "jack"}]
    assert {m.child_key for m in packs} == {"king-0-r0", "jack-0-r0"}

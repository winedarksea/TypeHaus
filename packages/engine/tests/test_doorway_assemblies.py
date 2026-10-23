"""Small physical floor/door fixtures; no house resolves or assumed manufacturer sections."""
from dataclasses import FrozenInstanceError, replace
import json
from types import SimpleNamespace as NS

import pytest
from shapely.geometry import Polygon

from typehaus.model import DoorType, DoorwayProductSpec, DoorwaySectionPart, DoorwayTreatment
from typehaus.quantities import m
from typehaus.resolve.doorway import doorway_json, resolve_doorway, resolve_doorways
from typehaus.resolve.doorway_fit import coordinate_doorway_pans
from typehaus.resolve.doorway_floors import extend_doorway_finishes
from typehaus.resolve.doorway_framing import clear_doorway_sole_plates
from typehaus.resolve.geometry_doorway import doorway_parts
from typehaus.resolve.geometry_ir import GSweep
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model import (
    FramedMember, ResolvedFinishZone, ResolvedLayer, ResolvedModel, ResolvedOpening, ResolvedRoom,
    ResolvedWall,
)
from typehaus.resolve.walking_surface import room_finish_at
from typehaus.takeoff.doors import doorway_purchase_rows


def rectangle(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


@pytest.fixture
def doorway_model():
    layer = ResolvedLayer("stud", "wood", "structure", .14, rectangle(0, -.07, 4, .07))
    plate = FramedMember("wall", "plate-bottom", "plate", "2x6", (0, 0), (4, 0), 0, .0381, 4)
    wall = ResolvedWall(uid="wall", tag="W", storey="main", assembly="A",
                        axis=((0, 0), (4, 0)), layers=(layer,), z0_m=0, z1_m=3,
                        members=(plate,))
    opening = ResolvedOpening("door", "D", "W", "DT", .9, 2.1, 0, 2, "door", True)
    product = DoorType(tag="DT", width=m(.9), height=m(2.1))
    rooms = [ResolvedRoom("r-", "R-", "main", "habitable", True,
                          rectangle(0, -2, 4, -.07), 7.72, "plank",
                          axis_face=rectangle(0, -2, 4, 0),
                          field_finish=((rectangle(0, -2, 4, -.07), ()),), field_area_m2=7.72),
             ResolvedRoom("r+", "R+", "main", "habitable", True,
                          rectangle(0, .07, 4, 2), 7.72, "plank",
                          axis_face=rectangle(0, 0, 4, 2),
                          field_finish=((rectangle(0, .07, 4, 2), ()),), field_area_m2=7.72)]
    materials = [NS(tag="plank", finish_thickness_in=.25, coating=False),
                 NS(tag="tile", finish_thickness_in=.5, coating=False),
                 NS(tag="metal", finish_thickness_in=None, coating=False)]
    plan = NS(library=NS(door_types=(product,), materials=materials),
              by_tag=lambda tag: None, project=NS(site=NS(impervious_surfaces=())))
    slab = NS(tag="slab", category="slab", storey="main", outline=rectangle(0, -2, 4, 2),
              z1_m=0, voids=())
    return ResolvedModel(plan=plan, walls=[wall], openings=[opening], rooms=rooms, solids=[slab])


def reducer(**overrides):
    data = dict(product_ref="TEST-REDUCER", variant="synthetic reducer; not a purchased product",
                role="transition", higher_floor_side=1, floor_contact_heights_m=(0, .00635),
                floor_finish_edges_m=(-.02, .02),
                source_url="https://example.test/section.pdf",
                source_drawing="test drawing 1", installation="tile high side +normal",
                verified=True, datum="lower_floor", maximum_floor_difference_m=.02,
                compatible_finish_pairs=(("plank", "tile"),), purchase="separate",
                parts=(DoorwaySectionPart(name="ramp", material_ref="metal", polygon_m=(
                    (-.02, 0), (.02, 0), (.02, .00635), (-.02, .001))),))
    return DoorwayProductSpec(**(data | overrides))


def resolve_one(model, treatment=None, **type_changes):
    product = DoorType.model_validate(model.plan.library.door_types[0].model_dump() | type_changes)
    model.plan.library.door_types = (product,)
    assembly = resolve_doorway(model, model.walls[0], model.openings[0], product, treatment)
    model.openings = [replace(model.openings[0], doorway=assembly)]
    return assembly


def different_finishes(model):
    model.rooms[1] = replace(model.rooms[1], floor_finish="tile")


def test_continuous_floor_extends_reveals_without_double_counting(doorway_model):
    model = doorway_model
    assembly = resolve_one(model)
    assert assembly.status == "VERIFIED"
    assert assembly.floor_treatment == "continuous" and not assembly.components
    extend_doorway_finishes(model)
    assert sum(r.field_area_m2 for r in model.rooms) == pytest.approx(15.44 + .9 * .14)
    areas = [r.field_area_m2 for r in model.rooms]
    extend_doorway_finishes(model)
    assert [r.field_area_m2 for r in model.rooms] == pytest.approx(areas)
    with pytest.raises(FrozenInstanceError):
        assembly.floor_treatment = "transition"


def test_differing_finishes_remain_unknown_without_compatible_trim(doorway_model):
    different_finishes(doorway_model)
    assembly = resolve_one(doorway_model)
    assert assembly.status == "UNKNOWN" and not assembly.components
    assert "transition is unspecified" in " ".join(assembly.unknown)


def test_explicit_continuous_override_reports_conflict_without_moving_floors(doorway_model):
    different_finishes(doorway_model)
    assembly = resolve_one(doorway_model, DoorwayTreatment(floor_treatment="continuous"))
    assert assembly.status == "FAIL"
    assert assembly.rough_opening_z_m == 0
    assert [f.surface_m for f in assembly.adjacent_floors] == pytest.approx([.00635, .0127])


def test_finish_zone_at_door_outweighs_room_centroid_finish(doorway_model):
    model = doorway_model
    zone = rectangle(1, .07, 3, .4)
    model.rooms[1] = replace(model.rooms[1], finish_zones=(
        ResolvedFinishZone(zone, "tile", .66, parts=((zone, ()),)),))
    assert room_finish_at(model, "main", (2, .085))[1] == "tile"
    assembly = resolve_one(model, DoorwayTreatment(transition=reducer()))
    assert assembly.adjacent_floors[1].finish_ref == "tile"
    assert assembly.components[0].base_z_m == pytest.approx(.00635)
    extend_doorway_finishes(model)
    assert model.rooms[1].finish_zones[0].area_m2 > .66


def test_reducer_footprint_and_expansion_gaps_exclude_floor_area(doorway_model):
    model = doorway_model
    different_finishes(model)
    spec = reducer(expansion_gap_m=(.003, .005))
    assembly = resolve_one(model, DoorwayTreatment(transition=spec))
    assert assembly.status == "VERIFIED"
    assert assembly.components[0].normal_extent_m == (-.02, .02)
    extend_doorway_finishes(model)
    assert sum(r.field_area_m2 for r in model.rooms) == pytest.approx(15.44 + .9 * (.14 - .048))
    assert len(doorway_purchase_rows(model)) == 1
    assert doorway_purchase_rows(model)[0]["count"] == 1
    for purchase in ("factory_included", "kit_included"):
        resolve_one(model, DoorwayTreatment(transition=reducer(purchase=purchase)))
        assert doorway_purchase_rows(model) == []


def test_unverified_or_incompatible_section_is_omitted(doorway_model):
    different_finishes(doorway_model)
    for spec in (reducer(verified=False), reducer(compatible_finish_pairs=())):
        assembly = resolve_one(doorway_model, DoorwayTreatment(transition=spec))
        assert assembly.status == "UNKNOWN" and not assembly.components
        assert not doorway_parts(doorway_model.walls[0], doorway_model.openings[0])


def test_unsupported_reducer_height_is_a_conflict(doorway_model):
    different_finishes(doorway_model)
    assembly = resolve_one(doorway_model, DoorwayTreatment(transition=reducer(
        maximum_floor_difference_m=.002)))
    assert assembly.status == "FAIL"
    assert "outside supported range" in " ".join(assembly.conflicts)


@pytest.mark.parametrize("operation", ["swing", "double_swing", "slide", "pocket", "bifold", "overhead"])
def test_operation_never_invents_a_floor_spanning_product(doorway_model, operation):
    model = doorway_model
    assembly = resolve_one(model, operation=operation, exterior=True)
    parts = opening_parts(model.walls[0], model.openings[0], model.plan.library.door_types[0].operation)
    frame = next(p for p in parts if p.key == "frame")
    assert len(frame.solids) == 3
    assert all(p.key != "sliding_track" for p in parts)
    assert assembly.status == "UNKNOWN" and not assembly.components


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("handed", [False, True])
def test_sourced_sloped_section_is_exact_under_wall_and_handing_reversal(doorway_model, reverse, handed):
    model = doorway_model
    different_finishes(model)
    if reverse:
        model.walls[0] = replace(model.walls[0], axis=((4, 0), (0, 0)))
    model.openings[0] = replace(model.openings[0], flip_hinge=handed, flip_swing=handed)
    resolve_one(model, DoorwayTreatment(transition=reducer(
        higher_floor_side=-1 if reverse else 1)))
    sweep = doorway_parts(model.walls[0], model.openings[0])[0].solids[0]
    assert isinstance(sweep, GSweep)
    assert sorted(z for _, _, z in sweep.profile) == pytest.approx([.00635, .00635, .00735, .0127])
    assert abs(sweep.extrude[0]) == pytest.approx(.9)
    assert len({z for _, _, z in sweep.profile}) == 3


def test_overrides_and_source_spec_serialization(doorway_model):
    model = doorway_model
    different_finishes(model)
    model.plan.library.door_types = (model.plan.library.door_types[0].model_copy(update={
        "doorway": DoorwayTreatment(floor_treatment="continuous")}),)
    authored = NS(doorway=DoorwayTreatment(transition=reducer()))
    model.plan.by_tag = lambda tag: authored if tag == "D" else None
    resolve_doorways(model)
    assembly = model.openings[0].doorway
    assert assembly.status == "VERIFIED"
    serialized = json.loads(json.dumps(doorway_json(assembly)))
    specification = serialized["components"][0]["specification"]
    assert specification["source_drawing"] == "test drawing 1"
    assert specification["positive_normal_sign"] == 1
    assert serialized["status"] == "VERIFIED"


@pytest.mark.parametrize("reverse", [False, True])
def test_clear_passage_keeps_supports_below_floor_and_raised_access_sills(doorway_model, reverse):
    model = doorway_model
    if reverse:
        model.walls[0] = replace(model.walls[0], axis=tuple(reversed(model.walls[0].axis)))
    below = replace(model.walls[0].members[0], child_key="mudsill", z0_m=-.05, z1_m=0)
    raised = replace(below, child_key="sill-0", z0_m=.56, z1_m=.6)
    model.walls[0] = replace(model.walls[0], members=(*model.walls[0].members, below, raised))
    resolve_one(model)
    clear_doorway_sole_plates(model)
    plates = [p for p in model.walls[0].members if "plate-bottom" in p.child_key]
    assert len(plates) == 2
    assert plates[0].p1[0] == pytest.approx(1.55)
    assert plates[1].p0[0] == pytest.approx(2.45)
    assert below in model.walls[0].members and raised in model.walls[0].members
    assert sum(p.length_m for p in plates) == pytest.approx(3.1)


def test_missing_floor_is_unknown_and_does_not_delete_potential_support(doorway_model):
    model = doorway_model
    model.solids = []
    assembly = resolve_one(model)
    assert assembly.status == "UNKNOWN"
    assert assembly.leaf_bottom_z_m is None
    clear_doorway_sole_plates(model)
    assert len(model.walls[0].members) == 1


def test_raised_opening_does_not_extend_or_raise_floor_finish(doorway_model):
    model = doorway_model
    model.openings[0] = replace(model.openings[0], sill_m=.6)
    resolve_one(model)
    extend_doorway_finishes(model)
    clear_doorway_sole_plates(model)
    assert all(r.field_area_m2 == 7.72 for r in model.rooms)
    assert len(model.walls[0].members) == 1


def test_pan_back_dam_and_support_intersections_report_conflicts(doorway_model, monkeypatch):
    from typehaus.resolve.opening_flashing import OpeningFlashingFrame
    import typehaus.resolve.opening_flashing as flashing
    model = doorway_model
    frame = OpeningFlashingFrame((0, 0), (1, 0), (0, 1), -.07, .07, .07, .09, False)
    monkeypatch.setattr(flashing, "opening_flashing_frame", lambda *_: frame)
    spec = reducer(role="sill", datum="rough_opening", normal_offset_m=-.06)
    resolve_one(model, DoorwayTreatment(threshold=spec), exterior=True)
    coordinate_doorway_pans(model)
    assembly = model.openings[0].doorway
    assert "back dam" in " ".join(assembly.conflicts)
    assert assembly.status == "FAIL"


def test_verified_section_requires_simple_finite_profile():
    with pytest.raises(ValueError, match="cross-section"):
        reducer(parts=())
    with pytest.raises(ValueError, match="simple polygon"):
        DoorwaySectionPart(name="bad", material_ref="metal", polygon_m=((0, 0), (1, 1), (2, 2)))


def test_viewer_fixture_and_gltf_preserve_every_sourced_section_vertex(doorway_model):
    from pathlib import Path
    from typehaus.emit.gltf.mesh import _MeshBuilder

    fixtures = json.loads((Path(__file__).resolve().parents[3]
                           / "ui/src/three/builders/doorwayFixtures.json").read_text())
    for fixture in fixtures:
        model = doorway_model
        model.walls[0] = replace(model.walls[0], axis=tuple(tuple(p) for p in fixture["wall"]["axis"]))
        reverse = model.walls[0].axis[0][0] > model.walls[0].axis[1][0]
        serialized = fixture["opening"]["doorway"]
        for index, floor in enumerate(serialized["adjacent_floors"]):
            room_index = 1 - index if reverse else index
            model.rooms[room_index] = replace(model.rooms[room_index], floor_finish=floor["finish_ref"])
        spec = DoorwayProductSpec.model_validate(serialized["components"][0]["specification"])
        assembly = resolve_one(model, DoorwayTreatment(transition=spec))
        assert assembly.status == serialized["status"] == "VERIFIED"
        sweep = doorway_parts(model.walls[0], model.openings[0])[0].solids[0]
        assert sweep.profile == tuple(tuple(p) for p in fixture["profile"])
        assert sweep.extrude == tuple(fixture["extrude"])
        mb = _MeshBuilder()
        mb.add_sweep(sweep, (1, 1, 1, 1))
        positions, _ = mb._buckets[(1, 1, 1, 1)]
        expected = {(x + dx, z + dz, -y - dy) for x, y, z in sweep.profile
                    for dx, dy, dz in ((0, 0, 0), sweep.extrude)}
        actual = {tuple(position) for position in positions}
        assert actual == expected
        serialized = fixture["opening"]["doorway"]
        assert serialized["components"][0]["specification"]["verified"]


@pytest.mark.parametrize("normal_sign", [-1, 1])
def test_ifc_swept_section_keeps_slopes_and_source_identity(doorway_model, normal_sign):
    import ifcopenshell
    import ifcopenshell.api
    import ifcopenshell.geom
    from typehaus.emit.ifc.door_fillings import cased_door_representation

    model = doorway_model
    different_finishes(model)
    resolve_one(model, DoorwayTreatment(transition=reducer(positive_normal_sign=normal_sign)))
    parts = doorway_parts(model.walls[0], model.openings[0])
    model.geometry = NS(by_uid=lambda uid: NS(parts=parts))
    # The representation serializer only needs style catalog lookups, not a whole house.
    model.plan.library.materials = ()
    f = ifcopenshell.file(schema="IFC4")
    ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcProject", name="Doorway test")
    context = ifcopenshell.api.run("context.add_context", f, context_type="Model")
    body = ifcopenshell.api.run("context.add_context", f, context_type="Model",
                              context_identifier="Body", target_view="MODEL_VIEW", parent=context)
    representation = cased_door_representation(f, body, model, model.openings[0])
    assert len(representation.Items) == 1
    solid = representation.Items[0]
    assert solid.is_a("IfcExtrudedAreaSolid")
    assert solid.Depth == pytest.approx(.9)
    coordinates = [tuple(p.Coordinates) for p in solid.SweptArea.OuterCurve.Points]
    assert len({p[1] for p in coordinates}) == 3
    assert solid.StyledByItem[0].Name == "doorway:transition:ramp"

    tessellation = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), representation)
    vertices = [tuple(tessellation.verts[i:i+3]) for i in range(0, len(tessellation.verts), 3)]
    sweep = parts[0].solids[0]
    expected = [tuple(p[i] + d[i] for i in range(3)) for p in sweep.profile
                for d in ((0, 0, 0), sweep.extrude)]
    for axis in range(3):
        assert min(p[axis] for p in vertices) == pytest.approx(min(p[axis] for p in expected))
        assert max(p[axis] for p in vertices) == pytest.approx(max(p[axis] for p in expected))


def test_reversed_reducer_and_missing_orientation_are_not_verified(doorway_model):
    different_finishes(doorway_model)
    assembly = resolve_one(doorway_model, DoorwayTreatment(transition=reducer(positive_normal_sign=-1)))
    assert assembly.status == "FAIL"
    assert "faces the lower floor" in " ".join(assembly.conflicts)
    assembly = resolve_one(doorway_model, DoorwayTreatment(transition=reducer(higher_floor_side=None)))
    assert assembly.status == "UNKNOWN" and not assembly.components


def test_documented_leaf_and_jamb_datums_are_preserved_and_clearance_conflicts_reported(doorway_model):
    different_finishes(doorway_model)
    spec = reducer(leaf_bottom_m=.001, jamb_bottom_m=.004)
    assembly = resolve_one(doorway_model, DoorwayTreatment(transition=spec))
    assert assembly.status == "FAIL"
    assert assembly.leaf_bottom_z_m == pytest.approx(.00735)
    assert assembly.jamb_bottom_z_m == pytest.approx(.01035)
    assert "leaf bottom conflicts" in " ".join(assembly.conflicts)


def test_narrow_zone_at_jamb_is_detected_instead_of_extended_across_whole_door(doorway_model):
    model = doorway_model
    zone = rectangle(2.40, .07, 2.44, .4)
    model.rooms[1] = replace(model.rooms[1], finish_zones=(
        ResolvedFinishZone(zone, "tile", .0132, parts=((zone, ()),)),))
    assembly = resolve_one(model)
    assert assembly.status == "UNKNOWN"
    assert "varies across doorway" in " ".join(assembly.unknown)
    assert assembly.adjacent_floors[1] is None


def test_runtime_check_rejects_obstructing_plate_and_accepts_cleared_passage(doorway_model):
    from typehaus.checks.integrity.doorway import doorway_assembly
    from typehaus.findings import Result
    model = doorway_model
    resolve_one(model)
    ctx = NS(plan=model.plan, model=model)
    assert any(f.result == Result.FAIL for f in doorway_assembly(ctx))
    clear_doorway_sole_plates(model)
    assert all(f.result == Result.PASS for f in doorway_assembly(ctx))


def test_split_bottom_plates_do_not_change_top_plate_fastener_thickness(doorway_model):
    from typehaus.resolve.partition_fasteners import top_plate_through_in
    model = doorway_model
    top = replace(model.walls[0].members[0], child_key="plate-top-0", z0_m=2.96, z1_m=2.9981)
    model.walls[0] = replace(model.walls[0], members=(*model.walls[0].members, top))
    resolve_one(model)
    clear_doorway_sole_plates(model)
    assert top_plate_through_in(model.walls[0]) == pytest.approx(1.5)


def test_multipart_transition_is_one_purchase_and_kit_guide_is_not_a_threshold(doorway_model):
    model = doorway_model
    different_finishes(model)
    spec = reducer()
    spec = spec.model_copy(update={"parts": (*spec.parts, DoorwaySectionPart(
        name="insert", material_ref="metal", polygon_m=((0, .006), (.001, .006), (0, .007))))})
    resolve_one(model, DoorwayTreatment(transition=spec))
    assert len(doorway_parts(model.walls[0], model.openings[0])) == 2
    assert doorway_purchase_rows(model)[0]["count"] == 1
    model.rooms[1] = replace(model.rooms[1], floor_finish="plank")
    guide = reducer(role="guide", span_m=.04, purchase="kit_included")
    resolve_one(model, DoorwayTreatment(threshold=guide), operation="pocket")
    sweep = doorway_parts(model.walls[0], model.openings[0])[0].solids[0]
    assert abs(sweep.extrude[0]) == pytest.approx(.04)
    assert doorway_purchase_rows(model) == []


def test_unverified_source_identity_survives_schedule_and_unknown_findings(doorway_model):
    from typehaus.checks.integrity.doorway import doorway_assembly
    from typehaus.emit.draw.schedules.openings import _doorway_text
    from typehaus.findings import Result
    model = doorway_model
    spec = reducer(role="sill", verified=False)
    resolve_one(model, DoorwayTreatment(threshold=spec), exterior=True)
    clear_doorway_sole_plates(model)
    findings = doorway_assembly(NS(plan=model.plan, model=model))
    assert findings and all(f.result == Result.UNKNOWN for f in findings)
    assert "UNKNOWN" in _doorway_text(model.openings[0])
    assert "TEST-REDUCER" in _doorway_text(model.openings[0])


def test_missing_supported_height_range_does_not_assume_equal_floor_approval(doorway_model):
    different_finishes(doorway_model)
    assembly = resolve_one(doorway_model, DoorwayTreatment(transition=reducer(
        maximum_floor_difference_m=None)))
    assert assembly.status == "UNKNOWN" and not assembly.components
    assert "supported floor-height range" in " ".join(assembly.unknown)


def test_reducer_must_meet_actual_floor_planes_even_within_its_supported_range(doorway_model):
    model = doorway_model
    different_finishes(model)
    tile = next(m for m in model.plan.library.materials if m.tag == "tile")
    tile.finish_thickness_in = .75
    assembly = resolve_one(model, DoorwayTreatment(transition=reducer()))
    assert assembly.status == "FAIL"
    assert "contacts do not meet walking planes" in " ".join(assembly.conflicts)
    assembly = resolve_one(model, DoorwayTreatment(transition=reducer(floor_contact_heights_m=None)))
    assert assembly.status == "UNKNOWN" and not assembly.components


def test_profile_cap_overlap_uses_documented_finish_stops(doorway_model):
    model = doorway_model
    different_finishes(model)
    spec = reducer(floor_finish_edges_m=(-.005, .005), expansion_gap_m=(.003, .005))
    assembly = resolve_one(model, DoorwayTreatment(transition=spec))
    assert assembly.components[0].normal_extent_m == (-.02, .02)
    assert assembly.components[0].finish_extent_m == (-.005, .005)
    extend_doorway_finishes(model)
    assert sum(r.field_area_m2 for r in model.rooms) == pytest.approx(15.44 + .9 * (.14 - .018))
    assembly = resolve_one(model, DoorwayTreatment(transition=reducer(floor_finish_edges_m=None)))
    assert assembly.status == "UNKNOWN" and not assembly.components


@pytest.mark.parametrize("contacts, lift, status", [(True, 0, "VERIFIED"),
                                                   (False, 0, "UNKNOWN"), (True, .01, "FAIL")])
def test_sill_bearing_and_pan_fit_use_documented_contacts(doorway_model, monkeypatch,
                                                        contacts, lift, status):
    from typehaus.resolve.opening_flashing import OpeningFlashingFrame, _pan_outlet
    from typehaus.resolve.flashing_config import FLASHING as cfg
    import typehaus.resolve.opening_flashing as flashing
    model = doorway_model
    frame = OpeningFlashingFrame((0, 0), (1, 0), (0, 1), -.07, .07, .07, .09, False)
    monkeypatch.setattr(flashing, "opening_flashing_frame", lambda *_: frame)
    outlet = _pan_outlet(model.openings[0], frame, cfg)
    def bottom(x):
        return (outlet - x) * cfg.drainage_slope + cfg.sill_membrane_m
    polygon = ((-.04, bottom(-.04)), (.04, bottom(.04)),
               (.04, bottom(.04)+.01), (-.04, bottom(-.04)+.01))
    spec = reducer(role="sill", datum="rough_opening", span_m=.89,
                   elevation_offset_m=lift, leaf_bottom_m=.02, jamb_bottom_m=.015,
                   bearing_points_m=((-.04, bottom(-.04)), (.04, bottom(.04))) if contacts else (),
                   parts=(DoorwaySectionPart(name="sill", material_ref="metal", polygon_m=polygon),))
    resolve_one(model, DoorwayTreatment(threshold=spec), exterior=True)
    coordinate_doorway_pans(model)
    assembly = model.openings[0].doorway
    assert assembly.status == status, (assembly.unknown, assembly.conflicts)
    if lift:
        assert "bearing lacks modeled support" in " ".join(assembly.conflicts)

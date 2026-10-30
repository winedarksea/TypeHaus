"""Installation masks cut coverings without changing rooms or structural floors."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from shapely.geometry import Point, Polygon, box

from typehaus.model import FixtureType, Material, inch
from typehaus.resolve.fixture_floor_finish import (
    fixture_support_elevation,
    resolve_fixture_floor_finishes,
)
from typehaus.resolve.model import ResolvedFinishZone, ResolvedFloor, ResolvedModel, ResolvedRoom
from typehaus.resolve.overlay import union_all
from typehaus.resolve.room_finish import finish_parts
from typehaus.resolve.room_floor import room_finished_floor_elevation
from typehaus.resolve.walking_surface import room_finish_at


def _geometry(parts):
    return union_all([Polygon(outline, holes=list(holes)) for outline, holes in parts])


def _model(*footprints, coating=False, excludes=True, enclosure=None):
    material = Material(tag="finish", name="Finish", coating=coating,
                        finish_thickness_in=0 if coating else 0.75)
    fixtures = [SimpleNamespace(element_kind="Fixture", tag=f"FX-{index}", type_ref="BASE",
                                tub_enclosure=enclosure)
                for index in range(len(footprints))]
    plan = SimpleNamespace(
        project=SimpleNamespace(site=SimpleNamespace()),
        storeys=[SimpleNamespace(tag="main")],
        library=SimpleNamespace(materials=[material], fixture_types=[SimpleNamespace(
            tag="BASE", excludes_floor_finish=excludes)]),
        storey_elements=lambda _storey: fixtures,
    )
    room = ResolvedRoom(uid="ROOM", tag="RM", storey="main", occupancy="bathroom",
                        conditioned=True, clear_face=list(box(0, 0, 10, 10).exterior.coords)[:-1],
                        area_m2=100, floor_finish="finish",
                        field_finish=finish_parts(box(0, 0, 10, 10)), field_area_m2=100)
    canvas = [SimpleNamespace(tag=f.tag, storey="main",
                              footprint=list(p.exterior.coords)[:-1])
              for f, p in zip(fixtures, footprints, strict=True)]
    model = ResolvedModel(plan=plan, rooms=[room], canvas_objects=canvas)
    return model


def test_fixture_types_default_to_retaining_floor_finish():
    kind = FixtureType(tag="SINK", name="Sink", footprint=(inch(20), inch(20)), height=inch(30))
    assert kind.excludes_floor_finish is False
    model = _model(box(1, 1, 3, 3), excludes=False)
    original = model.rooms[:]
    assert not resolve_fixture_floor_finishes(model)
    assert model.rooms == original


def test_rotated_overlap_clipping_preserves_holes_reveals_and_is_idempotent():
    from shapely.affinity import rotate

    first = rotate(box(2, 2, 4, 6), 90)
    overlap = box(3, 2, 7, 5)
    outside = box(9, 8, 12, 12)
    model = _model(first, overlap, outside)
    # A pre-existing well and coordinated doorway reveal must survive the later mask.
    existing = box(0, 0, 10, 10).difference(box(7, 6, 8, 7)).union(box(-1, 4, 0, 5))
    model.rooms[0] = replace(model.rooms[0], field_finish=finish_parts(existing),
                             field_area_m2=existing.area)
    original = model.rooms[0]
    assert not resolve_fixture_floor_finishes(model)
    actual = model.rooms[0]
    expected = existing.difference(union_all([first, overlap, outside]))
    assert _geometry(actual.field_finish).symmetric_difference(expected).area < 1e-9
    assert actual.field_area_m2 == pytest.approx(expected.area)
    assert actual.clear_face == original.clear_face and actual.area_m2 == original.area_m2
    once = actual
    assert not resolve_fixture_floor_finishes(model)
    assert model.rooms[0] == once


def test_pentagonal_pan_leaves_floor_at_its_cut_corner():
    pan = Polygon([(1, 1), (3, 1), (4, 2), (4, 4), (1, 4)])
    model = _model(pan)
    assert not resolve_fixture_floor_finishes(model)
    field = _geometry(model.rooms[0].field_finish)
    assert field.covers(Point(3.9, 1.1))
    assert not field.covers(Point(2, 2))
    assert model.rooms[0].field_area_m2 == pytest.approx(100 - pan.area)


@pytest.mark.parametrize("coating", [False, True])
def test_finish_zones_and_field_respect_covering_versus_coating(coating):
    model = _model(box(2, 2, 6, 6), coating=coating)
    zone_geometry = box(0, 0, 4, 10)
    zone = ResolvedFinishZone(outline=list(zone_geometry.exterior.coords)[:-1],
                              material_ref="finish", area_m2=40,
                              parts=finish_parts(zone_geometry))
    model.rooms[0] = replace(model.rooms[0], finish_zones=(zone,),
                             field_finish=finish_parts(box(4, 0, 10, 10)), field_area_m2=60)
    assert not resolve_fixture_floor_finishes(model)
    room = model.rooms[0]
    assert room.field_area_m2 == pytest.approx(60 if coating else 52)
    assert room.finish_zones[0].area_m2 == pytest.approx(40 if coating else 32)
    assert room_finish_at(model, "main", (3, 3)) == (
        "RM", "finish" if coating else None, 0.0)
    assert room_finish_at(model, "main", (5, 3)) == (
        "RM", "finish" if coating else None, 0.0)
    assert room_finish_at(model, "main", (8, 8))[1] == "finish"


def test_point_queries_keep_room_ownership_and_room_aff_uses_remaining_finish():
    model = _model(box(4, 4, 6, 6))
    model.floors = [ResolvedFloor(uid="DECK", tag="DECK", storey="main", direction="x",
                                  members=(), deck_outline=model.rooms[0].clear_face,
                                  deck_z0_m=0, deck_z1_m=inch(0.75).meters)]
    assert not resolve_fixture_floor_finishes(model)
    assert room_finish_at(model, "main", (5, 5)) == ("RM", None, 0.0)
    assert room_finished_floor_elevation(model, model.rooms[0]) == pytest.approx(inch(1.5).meters)
    assert fixture_support_elevation(model, (5, 5), 0) == pytest.approx(inch(0.75).meters)
    with pytest.raises(ValueError, match="supporting"):
        fixture_support_elevation(model, (20, 20), 0)


@pytest.mark.parametrize(("excludes", "mount_in", "base_in"), [
    (False, None, 1.5), (True, None, 0.75), (True, 4, 5.5),
])
def test_placement_uses_subfloor_but_preserves_explicit_aff_mount(
        project, excludes, mount_in, base_in):
    from typehaus.model import Fixture, Library, Mount, PlanModel, Storey, ft, m, pt
    from typehaus.resolve.placeables import resolve_placeables

    model = _model(box(4, 4, 6, 6))
    kind = FixtureType(tag="BASE", name="Base", footprint=(m(1), m(1)), height=inch(30),
                       excludes_floor_finish=excludes)
    fixture = Fixture(tag="FX", type_ref="BASE", room="RM", position=pt(m(5), m(5)),
                       mount=Mount(elevation=None if mount_in is None else inch(mount_in)))
    model.plan = PlanModel(
        project=project, library=Library(materials=tuple(model.plan.library.materials),
                                         fixture_types=(kind,)),
        storeys=(Storey(tag="main", elevation=ft(0), default_ceiling_height=ft(8)),),
    ).with_elements("main", [fixture])
    model.canvas_objects = []
    model.floors = [ResolvedFloor(uid="DECK", tag="DECK", storey="main", direction="x",
                                  members=(), deck_outline=model.rooms[0].clear_face,
                                  deck_z1_m=inch(0.75).meters)]
    assert not resolve_placeables(model.plan, model)
    assert model.canvas_objects[0].z_m == pytest.approx(inch(base_in).meters)


def test_enclosure_excludes_full_deck_including_tub_cutout():
    spec = SimpleNamespace(deck_ref="DECK", knee_wall_refs=("WEST", "SOUTH"))
    model = _model(box(3, 3, 5, 7), enclosure=spec)
    model.solids = [SimpleNamespace(tag="DECK", storey="main",
                                    outline=list(box(2, 2, 6, 8).exterior.coords)[:-1],
                                    voids=[list(box(3, 3, 5, 7).exterior.coords)[:-1]])]
    walls = {tag: SimpleNamespace(storey="main", depth_layers=lambda: [])
             for tag in spec.knee_wall_refs}
    model.wall = walls.get
    assert not resolve_fixture_floor_finishes(model)
    field = _geometry(model.rooms[0].field_finish)
    assert field.intersection(box(2, 2, 6, 8)).area == 0
    assert model.rooms[0].field_area_m2 == pytest.approx(76)


@pytest.mark.parametrize("missing", ["placement", "deck", "wall"])
def test_missing_exclusion_references_report_integrity_failure(missing):
    spec = SimpleNamespace(deck_ref="MISSING", knee_wall_refs=("WEST", "SOUTH"))
    model = _model(box(3, 3, 5, 7), enclosure=spec)
    if missing == "placement":
        model.canvas_objects = []
    elif missing == "wall":
        model.solids = [SimpleNamespace(tag="MISSING", storey="main",
                                        outline=list(box(2, 2, 6, 8).exterior.coords)[:-1])]
    findings = resolve_fixture_floor_finishes(model)
    assert len(findings) == 1
    assert findings[0].check_id == "integrity.fixture_floor_finish"
    assert findings[0].result.value == "fail"
    assert model.rooms[0].field_area_m2 == 100

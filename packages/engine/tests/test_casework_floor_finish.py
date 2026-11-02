"""Toe-kick casework stands on the subfloor: a floating covering runs under its kick only."""

from types import SimpleNamespace

import pytest
from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon, box

from typehaus.library.placeables.sektion import BASE_24, CORNER_BASE_38
from typehaus.model import ApplianceType, Material, Mount, inch
from typehaus.model.placeable_symbols._sektion import _inset_l
from typehaus.resolve.fixture_floor_finish import resolve_fixture_floor_finishes
from typehaus.resolve.model import ResolvedFinishZone, ResolvedModel, ResolvedRoom
from typehaus.resolve.overlay import union_all
from typehaus.resolve.room_finish import finish_parts
from typehaus.resolve.walking_surface import room_finish_at


def _geometry(parts):
    return union_all([Polygon(outline, holes=list(holes)) for outline, holes in parts])


def _placed(tag, kind, local, position, rotation):
    world = translate(rotate(local, rotation, origin=(0, 0)), *position)
    item = SimpleNamespace(element_kind=kind, tag=tag, type_ref=None, mount=Mount())
    placed = SimpleNamespace(tag=tag, storey="main", position=position,
                             rotation_degrees=rotation,
                             footprint=list(world.exterior.coords)[:-1])
    return item, placed, world


def test_floating_floor_is_cut_behind_the_kick_and_nowhere_else():
    kick = inch(3).meters
    fridge = ApplianceType(tag="FRIDGE", name="Fridge", footprint=(inch(33), inch(27)),
                           height=inch(72))
    side = BASE_24.footprint[0].meters
    corner_side = CORNER_BASE_38.footprint[0].meters
    corner_local = Polygon([p.xy_m for p in CORNER_BASE_38.footprint_shape.points])
    specs = [  # (tag, kind, type, local footprint, position, rotation)
        ("BASE-E", "Furniture", BASE_24, box(-side / 2, -side / 2, side / 2, side / 2),
         (2.0, 2.0), 90.0),
        ("BASE-ZONE", "Furniture", BASE_24, box(-side / 2, -side / 2, side / 2, side / 2),
         (5.0, 8.0), 0.0),
        ("CORNER", "Furniture", CORNER_BASE_38, corner_local, (8.0, 3.0), 180.0),
        ("FRIDGE", "Appliance", fridge, box(-0.42, -0.34, 0.42, 0.34), (2.0, 5.0), 0.0),
    ]
    items, canvas, worlds = [], [], {}
    for tag, kind, kind_type, local, position, rotation in specs:
        item, placed, world = _placed(tag, kind, local, position, rotation)
        item.type_ref = kind_type.tag
        items.append(item)
        canvas.append(placed)
        worlds[tag] = world
    tile_zone = box(0, 8, 10, 10)
    plan = SimpleNamespace(
        storeys=[SimpleNamespace(tag="main")],
        library=SimpleNamespace(
            materials=[Material(tag="lvp", name="LVP", floating=True, finish_thickness_in=0.28),
                       Material(tag="tile", name="Tile", finish_thickness_in=0.5)],
            fixture_types=(), furniture_types=(BASE_24, CORNER_BASE_38),
            appliance_types=(fridge,)),
        storey_elements=lambda _storey: items)
    room = ResolvedRoom(
        uid="ROOM", tag="RM", storey="main", occupancy="kitchen", conditioned=True,
        clear_face=list(box(0, 0, 10, 10).exterior.coords)[:-1], area_m2=100,
        floor_finish="lvp", field_finish=finish_parts(box(0, 0, 10, 8)), field_area_m2=80,
        finish_zones=(ResolvedFinishZone(outline=list(tile_zone.exterior.coords)[:-1],
                                         material_ref="tile", area_m2=20,
                                         parts=finish_parts(tile_zone)),))
    model = ResolvedModel(plan=plan, rooms=[room], canvas_objects=canvas)

    assert not resolve_fixture_floor_finishes(model)
    room = model.rooms[0]
    # Rotated 90 degrees the front faces +x: the kick strip there keeps its plank.
    base = worlds["BASE-E"]
    bearing = box(base.bounds[0], base.bounds[1], base.bounds[2] - kick, base.bounds[3])
    # The L's two notch faces step back by the kick, as the glyph draws its kick.
    corner = translate(rotate(Polygon(_inset_l(corner_side, corner_side, side, kick)), 180,
                              origin=(0, 0)), 8.0, 3.0)
    straddle = worlds["BASE-ZONE"]
    on_lvp = box(straddle.bounds[0], straddle.bounds[1] + kick, straddle.bounds[2], 8)
    expected = union_all([bearing, corner, on_lvp])
    assert _geometry(room.floor_finish_exclusions).symmetric_difference(expected).area < 1e-9
    assert room.field_area_m2 == pytest.approx(80 - expected.area)
    # The tile zone is not floating: it still runs under the cabinet that straddles it.
    assert room.finish_zones[0].area_m2 == pytest.approx(20)
    assert room_finish_at(model, "main", (base.bounds[2] - kick / 2, 2.0))[1] == "lvp"
    assert room_finish_at(model, "main", (2.0, 2.0)) == ("RM", None, 0.0)
    assert room_finish_at(model, "main", (2.0, 5.0))[1] == "lvp"  # the fridge stands on it
    assert _geometry(room.field_finish).covers(Point(2.0, 5.0))
    once = room
    assert not resolve_fixture_floor_finishes(model)
    assert model.rooms[0] == once

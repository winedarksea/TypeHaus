"""``ResolvedRoom.field_finish``: the floor a room's finish covers (resolve/room_finish.py).

The clear face less the zones and the deck voids at the room's level. Before it, the viewer
holed every room with every well on the storey and the takeoff with none, so RM-S-HALL
billed ~70 sf of LVP over its stair and the viewer capped the well.
"""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon
from shapely.ops import unary_union

_M2_TO_FT2 = 10.7639


def _room(model, tag):
    return next(room for room in model.rooms if room.tag == tag)


def _field(room):
    return [Polygon(outline, holes=[list(hole) for hole in holes])
            for outline, holes in room.field_finish]


def _reveal_area(room):
    face = Polygon(room.clear_face)
    return sum(part.difference(face).area for part in _field(room))


def _room_with_doorway_reveals(model, room):
    from typehaus.resolve.geometry import opening_center, wall_frame
    from typehaus.resolve.geometry_door_products import finish_faces

    allowed = [Polygon(room.clear_face)]
    for opening in model.openings:
        assembly = opening.doorway
        if assembly is None or not any(f and f.room_tag == room.tag for f in assembly.adjacent_floors):
            continue
        wall = model.wall(opening.host_wall)
        faces = finish_faces(wall)
        center = opening_center(wall, opening)
        _, tangent, normal, _ = wall_frame(wall)
        half = opening.width_m / 2
        allowed.append(Polygon([(center[0] + tangent[0] * along + normal[0] * offset,
                                 center[1] + tangent[1] * along + normal[1] * offset)
                                for along, offset in ((-half, faces[0]), (half, faces[0]),
                                                       (half, faces[1]), (-half, faces[1]))]))
    return unary_union(allowed)


def test_the_hall_field_is_net_of_its_stair_well(catlin_model_ro):
    hall = _room(catlin_model_ro, "RM-S-HALL")
    # FO-S-STAIR's well on FS-S-WEST, 2.267 x 2.870 m, flush with three of the hall's edges.
    assert hall.field_area_m2 - _reveal_area(hall) == pytest.approx(
        hall.area_m2 - 6.51, abs=0.05)
    well = next(Polygon(ring) for floor in catlin_model_ro.floors
                if floor.tag == "FS-S-WEST" for ring in floor.deck_voids
                if Polygon(ring).intersection(Polygon(hall.clear_face)).area > 1.0)
    assert sum(part.intersection(well).area for part in _field(hall)) < 1e-4
    # The flush well is a notch, not a hole: nothing a triangulator can fail to cut.
    assert all(not holes for _outline, holes in hall.field_finish)


def test_a_room_with_no_void_and_no_zone_keeps_its_face_and_adds_doorway_reveals(catlin_model_ro):
    for tag in ("RM-M-BATH1", "RM-S-VANITY", "RM-M-MUDROOM"):
        room = _room(catlin_model_ro, tag)
        assert not room.finish_zones
        assert room.field_area_m2 - _reveal_area(room) == pytest.approx(
            room.area_m2, abs=1e-4), tag
        assert len(room.field_finish) == 1


def test_every_field_part_stays_inside_its_room_or_a_doorway_reveal(catlin_model_ro):
    """Finish outside the room must be confined to an actual adjacent doorway reveal."""
    for room in catlin_model_ro.rooms:
        face = _room_with_doorway_reveals(catlin_model_ro, room).buffer(1e-6)
        for part in _field(room):
            assert part.difference(face).area < 1e-6, room.tag


def test_the_takeoff_bills_the_field_not_the_gross_room(catlin_model_ro):
    from typehaus.takeoff.finishes import floor_finish_rows

    rows = {row["finish"]: row for row in floor_finish_rows(catlin_model_ro)}
    gross = sum(room.area_m2 - sum(zone.area_m2 for zone in room.finish_zones)
                for room in catlin_model_ro.rooms if room.floor_finish == "lvp") * _M2_TO_FT2
    # RM-S-HALL and RM-M-LIVING each wrap ~70 sf of well; the underlayment follows the plank.
    reveals = sum(_reveal_area(room) for room in catlin_model_ro.rooms
                  if room.floor_finish == "lvp") * _M2_TO_FT2
    reveals += sum(Polygon(outline, holes=list(holes)).difference(Polygon(room.clear_face)).area
                   for room in catlin_model_ro.rooms if room.floor_finish == "lvp"
                   for zone in room.finish_zones for outline, holes in zone.parts) * _M2_TO_FT2
    assert gross + reveals - float(rows["lvp"]["net_area_sqft"]) == pytest.approx(75.8, abs=1.0)
    assert "lvp-underlayment" not in rows


def test_the_model_json_carries_the_field(catlin_model_ro):
    from typehaus.server.model_json_spaces import spaces_json

    rooms = {room["tag"]: room for room in spaces_json(catlin_model_ro, None)["rooms"]}
    hall = rooms["RM-S-HALL"]
    assert hall["field_area_m2"] == pytest.approx(_room(catlin_model_ro, "RM-S-HALL")
                                                  .field_area_m2)
    assert hall["field_finish"] and set(hall["field_finish"][0]) == {"outline", "holes"}

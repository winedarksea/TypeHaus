"""``ResolvedRoom.field_finish``: the floor a room's finish covers (resolve/room_finish.py).

The clear face less the zones and the deck voids at the room's level. Before it, the viewer
holed every room with every well on the storey and the takeoff with none, so RM-S-HALL
billed ~70 sf of LVP over its stair and the viewer capped the well.
"""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

_M2_TO_FT2 = 10.7639


def _room(model, tag):
    return next(room for room in model.rooms if room.tag == tag)


def _field(room):
    return [Polygon(outline, holes=[list(hole) for hole in holes])
            for outline, holes in room.field_finish]


def test_the_hall_field_is_net_of_its_stair_well(catlin_model_ro):
    hall = _room(catlin_model_ro, "RM-S-HALL")
    # FO-S-STAIR's well on FS-S-WEST, 2.267 x 2.870 m, flush with three of the hall's edges.
    assert hall.field_area_m2 == pytest.approx(hall.area_m2 - 6.51, abs=0.05)
    well = next(Polygon(ring) for floor in catlin_model_ro.floors
                if floor.tag == "FS-S-WEST" for ring in floor.deck_voids
                if Polygon(ring).intersection(Polygon(hall.clear_face)).area > 1.0)
    assert sum(part.intersection(well).area for part in _field(hall)) < 1e-4
    # The flush well is a notch, not a hole: nothing a triangulator can fail to cut.
    assert all(not holes for _outline, holes in hall.field_finish)


def test_a_room_with_no_void_and_no_zone_keeps_its_whole_area(catlin_model_ro):
    for tag in ("RM-M-BATH1", "RM-S-VANITY", "RM-M-MUDROOM"):
        room = _room(catlin_model_ro, tag)
        assert not room.finish_zones
        assert room.field_area_m2 == pytest.approx(room.area_m2, rel=1e-9), tag
        assert len(room.field_finish) == 1


def test_every_field_part_stays_inside_its_room(catlin_model_ro):
    """The neighbour bleed: a finish plane must never reach past its own clear face."""
    for room in catlin_model_ro.rooms:
        face = Polygon(room.clear_face).buffer(1e-6)
        for part in _field(room):
            assert part.difference(face).area < 1e-6, room.tag


def test_the_takeoff_bills_the_field_not_the_gross_room(catlin_model_ro):
    from typehaus.takeoff.finishes import floor_finish_rows

    rows = {row["finish"]: row for row in floor_finish_rows(catlin_model_ro)}
    gross = sum(room.area_m2 - sum(zone.area_m2 for zone in room.finish_zones)
                for room in catlin_model_ro.rooms if room.floor_finish == "lvp") * _M2_TO_FT2
    # RM-S-HALL and RM-M-LIVING each wrap ~70 sf of well; the underlayment follows the plank.
    assert gross - float(rows["lvp"]["net_area_sqft"]) == pytest.approx(139.2, abs=1.0)
    assert rows["lvp-underlayment"]["net_area_sqft"] == rows["lvp"]["net_area_sqft"]


def test_the_model_json_carries_the_field(catlin_model_ro):
    from typehaus.server.model_json_spaces import spaces_json

    rooms = {room["tag"]: room for room in spaces_json(catlin_model_ro, None)["rooms"]}
    hall = rooms["RM-S-HALL"]
    assert hall["field_area_m2"] == pytest.approx(_room(catlin_model_ro, "RM-S-HALL")
                                                  .field_area_m2)
    assert hall["field_finish"] and set(hall["field_finish"][0]) == {"outline", "holes"}

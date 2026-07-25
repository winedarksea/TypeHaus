# haus: editable
from typehaus import Appliance, ElectricalDevice, Equipment, Fixture, Furniture, Register
from typehaus.model import deg, ft, m, pt

# Project-local canvas placement targets.  One list per storey keeps source ownership
# explicit while allowing every placeable domain to use the same writeback contract.
#
# The main-floor set is a furnished living/dining zone against the shared starter catalog:
# rotation 0 puts an object's back at +y (project north), so the sofa faces the media
# console across the room and the chairs face the table from both sides.
# FX-1 is the furnace-room utility sink. It stands against the north face of the 12"
# concrete cross wall W-B-CW (centerline y=18', so the face is y=18'-6"), and — like every
# fixture on a slab-on-grade — its waste drops straight down rather than into a wall stack,
# so `drain_position` puts the trap 6" out from the wall on the basin centerline and
# SP-B-UTILITY (plan/mep.py) is the pre-pour stub-up through SL-B-FLOOR that serves it.
BASEMENT_PLACEABLES = [
    Fixture(uid="5BBZTZNBWN", tag="FX-1", type_ref="FX-LAV", room="RM-B-FURNACE",
            position=pt(ft(14), ft(19, 4.5)), wall_ref="W-B-CW",
            drain_position=pt(ft(14), ft(19))),
]
MAIN_PLACEABLES = [
    Furniture(uid="XV5MXV43QJ", tag="FURN-M-SOFA", type_ref="FURN-SOFA-84", room="RM-M-LIVING",
              position=pt(m(7.87848), m(2.69813))),
    Furniture(uid="EKN22YPA9J", tag="FURN-M-MEDIA", type_ref="FURN-MEDIA-60", room="RM-M-LIVING",
              position=pt(ft(26, 11), ft(1, 10)), rotation=deg(180)),
    Furniture(uid="QWCMN48QST", tag="FURN-M-DINING", type_ref="FURN-DINING-6", room="RM-M-LIVING",
              position=pt(ft(26, 11), ft(21, 4))),
    Furniture(uid="60XVKZHFAS", tag="FURN-M-CHAIR-SW", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(25, 4), ft(18, 9)), rotation=deg(180)),
    Furniture(uid="XCW1QKV701", tag="FURN-M-CHAIR-SE", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(28, 6), ft(18, 9)), rotation=deg(180)),
    Furniture(uid="VHHDZ62B5F", tag="FURN-M-CHAIR-NW", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(25, 4), ft(23, 11))),
    Furniture(uid="17F6ZBR67K", tag="FURN-M-CHAIR-NE", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(28, 6), ft(23, 11))),
]
GARAGE_PLACEABLES = []
# Head against the east wall: rotation -90 turns the bed's back (+y) toward +x.
SECOND_PLACEABLES = [
    Furniture(uid="819QDDYMZ5", tag="FURN-S-BED1", type_ref="FURN-QUEEN-BED", room="RM-S-BED1",
              position=pt(ft(32, 5), ft(16)), rotation=deg(-90)),
]
ATTIC_PLACEABLES = []

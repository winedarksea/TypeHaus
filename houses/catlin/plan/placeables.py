# haus: editable
from typehaus import (Appliance, ElectricalDevice, Equipment, Fixture, Furniture, Mount,
                      MountKind, Register)
from typehaus.model import deg, ft, inch, m, pt

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
            position=pt(ft(7), ft(19, 4.5)), wall_ref="W-B-CW",
            drain_position=pt(ft(7), ft(19))),
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
    # --- kitchen: the NE corner of the open living face (no Room of its own) -------------
    #
    # Two datums set every number below, and both are finish faces read off the resolved
    # wall layers rather than off the module lines: the north and east interior gwb are at
    # 35'-5 3/8" (36' sheathing - 1/2" sheathing - 5 1/2" stud - 5/8" gwb), and the centre
    # bearing wall's east gwb is at 18'-3 3/8". Cabinet backs sit on those faces, so the runs
    # are dimensioned the way a millwork shop would measure them, not to wall centrelines.
    #
    # Rotation says which way a unit opens: 0 = back north, deg(90) = back west/opens east,
    # deg(-90) = back east/opens west, deg(180) = back south.

    # West run — cold storage and pantry against the centre bearing wall, opening east into
    # the kitchen. Packed from the north wall down: 12" + 18" tall pull-outs, freezer,
    # refrigerator, then the closet pantry in the nook by the stair tee. The two cold boxes
    # sit *below* the talls deliberately — their 3' door zones reach x=24'-1 3/8", and any
    # further north that band would run into the north counter run at y=33'-5 3/8".
    # Cabinets are 24" deep (centre x = 19'-3 3/8"); the cold boxes are 34" (centre 19'-8 3/8").
    Furniture(uid="WKMKJHJ7D7", tag="FURN-M-KIT-TALL-N", type_ref="CASE-TALL-PANTRY-12", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(34, 11.375)), rotation=deg(90)),
    Furniture(uid="RABKK6V43P", tag="FURN-M-KIT-TALL-S", type_ref="CASE-TALL-PANTRY-18", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(33, 8.375)), rotation=deg(90)),
    Appliance(uid="A1Y5Q0RDXV", tag="APPL-M-FRIDGE", type_ref="APPL-REFRIGERATOR", room="RM-M-LIVING",
              position=pt(ft(19, 8.375), ft(31, 5.375)), rotation=deg(90)),
    Appliance(uid="ZH6G4SNPWT", tag="APPL-M-FREEZER", type_ref="APPL-FREEZER-UPRIGHT", room="RM-M-LIVING",
              position=pt(ft(19, 8.375), ft(28, 5.375)), rotation=deg(90)),
    Furniture(uid="XTD1N9A693", tag="FURN-M-KIT-PANTRYC", type_ref="CASE-PANTRY-CLOSET-24", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(25, 11.375)), rotation=deg(90)),
    # Over the two cold boxes: the 24" between their 72" tops and the 96" top of the tall run
    # is the cheapest storage in the kitchen, and leaving it open would break the one line the
    # west run reads by. 24" deep like the talls, so all four fronts land on one plane at
    # x=20'-3 3/8" and the appliances stand 10" proud of them — which is what lets the fridge
    # and freezer doors swing clear of the cabinet above.
    Furniture(uid="8T3D1P2QRV", tag="FURN-M-KIT-OVER-FRIDGE", type_ref="CASE-OVER-36", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(31, 5.375)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
    Furniture(uid="Y4KJ6WB0ZC", tag="FURN-M-KIT-OVER-FREEZER", type_ref="CASE-OVER-36", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(28, 5.375)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(6))),

    # North run — the cooking wall. Bases are 24" deep, so their centre is y=34'-5 3/8"; the
    # range is 30" deep and so centres 3" further out at 34'-2 3/8", which is the number the
    # island aisle is measured from. The run starts where the west run's talls end
    # (x=20'-3 3/8") and stops at the east run (x=33'-4", leaving a 1 3/8" corner filler).
    # KIT-N2 is the cabinet under WIN-M-KITCH-N, the smoke window.
    Furniture(uid="KA0ETVK8F8", tag="FURN-M-KIT-N1", type_ref="CASE-B36", room="RM-M-LIVING",
              position=pt(ft(21, 9.375), ft(34, 5.375))),
    Furniture(uid="BZ9SVQVTVP", tag="FURN-M-KIT-N2", type_ref="CASE-B24", room="RM-M-LIVING",
              position=pt(ft(24, 3.375), ft(34, 5.375))),
    Appliance(uid="417H1EH5C3", tag="APPL-M-RANGE", type_ref="APPL-ELECTRIC-RANGE", room="RM-M-LIVING",
              position=pt(ft(26, 7), ft(34, 2.375))),
    Furniture(uid="7YPYR8K5FS", tag="FURN-M-KIT-N3", type_ref="CASE-B36", room="RM-M-LIVING",
              position=pt(ft(29, 4), ft(34, 5.375))),
    Furniture(uid="NF48E9MESN", tag="FURN-M-KIT-N4", type_ref="CASE-B30", room="RM-M-LIVING",
              position=pt(ft(32, 1), ft(34, 5.375))),

    # North wall cabinets, 13" deep at a 54" mount (18" of backsplash over the counter, top
    # at 96" to match the talls). They are laid out around the one window rough — the smoke
    # window at x 24'-1"..25'-3" — and around the hood.
    Furniture(uid="2BF9VM3SFA", tag="FURN-M-KIT-WN1", type_ref="CASE-W24", room="RM-M-LIVING",
              position=pt(ft(21, 3.375), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    Furniture(uid="4HM5A8P53B", tag="FURN-M-KIT-WN2", type_ref="CASE-W18", room="RM-M-LIVING",
              position=pt(ft(23, 0.375), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    # Recirculating canopy hood, 30" over the cooktop: mount 5'-6" on a 3' range.
    Appliance(uid="Q0W3FYXJGX", tag="APPL-M-HOOD", type_ref="APPL-HOOD-RECIRC", room="RM-M-LIVING",
              position=pt(ft(26, 7), ft(34, 7.375)),
              mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
    # East of the hood the wall is now unbroken, so the two 18" uppers that used to flank
    # WIN-M-KITCH-N are one 5'-6" run instead: 27'-10" (the hood's east edge) to 33'-4" (where
    # the base run below it stops). Shop-built as two ganged boxes behind a continuous face —
    # see CASE-W66 — it is the whole east half of the cooking wall in one gesture.
    Furniture(uid="DVWYR4A5J3", tag="FURN-M-KIT-WN3", type_ref="CASE-W66", room="RM-M-LIVING",
              position=pt(ft(30, 7), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),

    # East run — the sink wall, opening west. The 36" sink base centres on WIN-M-KITCH
    # (y=32'-8", sill 42" = counter height), the dishwasher sits immediately south of it on
    # the hand a right-handed cook loads with, and a 15" base closes the blind corner under
    # the north counter's return.
    Furniture(uid="49B0RDP4NW", tag="FURN-M-KIT-E1", type_ref="CASE-B30", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(27, 11)), rotation=deg(-90)),
    Appliance(uid="XPA5ZCQM5Q", tag="APPL-M-DW", type_ref="APPL-DISHWASHER", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(30, 2)), rotation=deg(-90)),
    Furniture(uid="F8A30SK31X", tag="FURN-M-KIT-SINKBASE", type_ref="CASE-SINK-BASE-36", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(32, 8)), rotation=deg(-90)),
    Furniture(uid="3QTQ2NFWYD", tag="FURN-M-KIT-E2", type_ref="CASE-B15", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(34, 9.5)), rotation=deg(-90)),
    Furniture(uid="AQTQJBTXRR", tag="FURN-M-KIT-WE1", type_ref="CASE-W30", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(27, 11)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    Furniture(uid="VKP909PNS6", tag="FURN-M-KIT-WE2", type_ref="CASE-W24", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(30, 2)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),

    # Island — 5' x 3', the mid-landing of a work triangle the architect's fridge-west /
    # sink-east program stretches to ~30' of perimeter. Its north face is 36" off the range
    # front (the NKBA minimum for a one-cook aisle; 42" to the cabinet fronts either side of
    # it) and its south face clears the dining table's chair-use zone, which ends at y=25'-10".
    # 36" deep = 24" of carcass plus the 12" overhang the stools tuck under.
    Furniture(uid="PD9W4Q86MD", tag="FURN-M-KIT-ISLAND", type_ref="CASE-ISLAND-60", room="RM-M-LIVING",
              position=pt(ft(27, 6), ft(28, 5.375))),
    Furniture(uid="MZNJ9TAN56", tag="FURN-M-KIT-STOOL1", type_ref="FURN-BAR-STOOL", room="RM-M-LIVING",
              position=pt(ft(26), ft(26, 7)), rotation=deg(180)),
    Furniture(uid="TMR4RNV2E3", tag="FURN-M-KIT-STOOL2", type_ref="FURN-BAR-STOOL", room="RM-M-LIVING",
              position=pt(ft(27, 6), ft(26, 7)), rotation=deg(180)),
    Furniture(uid="1RME2HHSQT", tag="FURN-M-KIT-STOOL3", type_ref="FURN-BAR-STOOL", room="RM-M-LIVING",
              position=pt(ft(29), ft(26, 7)), rotation=deg(180)),
]
GARAGE_PLACEABLES = []
# Head against the east wall: rotation -90 turns the bed's back (+y) toward +x.
SECOND_PLACEABLES = [
    Furniture(uid="819QDDYMZ5", tag="FURN-S-BED1", type_ref="FURN-QUEEN-BED", room="RM-S-BED1",
              position=pt(ft(32, 5), ft(16)), rotation=deg(-90)),
]
ATTIC_PLACEABLES = []

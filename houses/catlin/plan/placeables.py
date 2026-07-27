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
#
# The sauna benches are dimensioned to *liner faces*, not to the node lines the walls are
# authored on, because that is the surface the joiner scribes to. Read off the resolved
# wall layers: west liner x=9'-1 13/16", east liner (the liner-on-concrete centre wall)
# x=17'-2 1/2", south concrete face y=1'-0", north liner y=13'-6 1/8" — an 8'-0 11/16" x
# 12'-6 1/8" clear box. notes/sauna_shower_basement_detail.md reserves the north 4' for the
# shower, so everything below stops at y=9'-6" and the benches never cross into it.
BASEMENT_PLACEABLES = [
    Fixture(uid="5BBZTZNBWN", tag="FX-1", type_ref="FX-LAV", room="RM-B-FURNACE",
            position=pt(ft(7), ft(19, 4.5)), wall_ref="W-B-CW",
            drain_position=pt(ft(7), ft(19))),
    # The long two-tier run takes the east wall: it is the only unbroken face in the room —
    # the west wall has D-B-SAUNA, the south wall WIN-B-SAUNA — so the bench lands as one
    # 8'-6" carcass with no scribes around an opening. rotation -90 puts its back (+y local)
    # against that face, giving x 13'-8 1/2"..17'-2 1/2" and y 1'-0"..9'-6".
    Furniture(uid="CBF601AAAA", tag="FURN-B-SAUNA-BENCH-E", type_ref="FURN-SAUNA-BENCH-2T-102",
              room="RM-B-SAUNA", position=pt(ft(15, 5.5), ft(5, 3)), rotation=deg(-90)),
    # The foot bench returns along the south wall, butted into the two-tier run's west face
    # at 13'-8 1/2" with an 11/16" scribe left at the west liner. rotation 180 puts its back
    # to the south. Its top is 18", well clear of WIN-B-SAUNA's 3'-0" sill above it.
    Furniture(uid="CBF602AAAA", tag="FURN-B-SAUNA-BENCH-S", type_ref="FURN-SAUNA-BENCH-54",
              room="RM-B-SAUNA", position=pt(ft(11, 5.5), ft(1, 10)), rotation=deg(180)),
]
MAIN_PLACEABLES = [
    Furniture(uid="XV5MXV43QJ", tag="FURN-M-SOFA", type_ref="FURN-SOFA-84", room="RM-M-LIVING",
              position=pt(m(7.87848), m(2.69813))),
    Furniture(uid="EKN22YPA9J", tag="FURN-M-MEDIA", type_ref="FURN-MEDIA-60", room="RM-M-LIVING",
              position=pt(ft(26, 11), ft(1, 10)), rotation=deg(180)),
    # Dining, at 17'-4" — 4' south of where it sat, which is what the north end of the room
    # asked for once the island moved down and the 48" pantry took the east wall to 22'-8".
    # The chair-use zone now runs y=12'-7"..22'-1": clear of the sofa's back at 10'-5", clear
    # of the pantry by 7", and leaving a 4'-4" circulation band between the table and the
    # island's seating edge instead of the 7" the old position left.
    #
    # An 8' x 3'-6" table is an eight-*place* table, but only the six side chairs are drawn.
    # The ends are where the room's long axis runs — an end chair pulled out is exactly what
    # would block the walk from the hall pass-through to the east windows — so they stay
    # unset places, brought in from elsewhere when the table is actually filled.
    Furniture(uid="QWCMN48QST", tag="FURN-M-DINING", type_ref="FURN-DINING-8", room="RM-M-LIVING",
              position=pt(ft(26, 11), ft(17, 4))),
    Furniture(uid="60XVKZHFAS", tag="FURN-M-CHAIR-S1", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(24, 5), ft(14, 6)), rotation=deg(180)),
    Furniture(uid="XCW1QKV701", tag="FURN-M-CHAIR-S2", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(26, 11), ft(14, 6)), rotation=deg(180)),
    Furniture(uid="REJA4QPWC3", tag="FURN-M-CHAIR-S3", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(29, 5), ft(14, 6)), rotation=deg(180)),
    Furniture(uid="VHHDZ62B5F", tag="FURN-M-CHAIR-N1", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(24, 5), ft(20, 2))),
    Furniture(uid="R3XJVT80XY", tag="FURN-M-CHAIR-N2", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(26, 11), ft(20, 2))),
    Furniture(uid="17F6ZBR67K", tag="FURN-M-CHAIR-N3", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(29, 5), ft(20, 2))),
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
    # The larder, south of where the counter run stops (KIT-E1's south end, y=26'-8") and
    # running 4' down the wall to 22'-8". Twice the width of the west run's closet pantry and
    # the only bulk storage on this side of the kitchen, which is the trade for the two
    # dining windows moving 6' south to clear it — see WIN-M-DIN-E1/E2 in storeys/main.py.
    # Two 24" doors rather than one 48" (→ CASE-PANTRY-CLOSET-48), and 8' tall to close the
    # east wall out at the same line as the west run's talls.
    Furniture(uid="Z0H6MVXC71", tag="FURN-M-KIT-PANTRY-E", type_ref="CASE-PANTRY-CLOSET-48", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(24, 8)), rotation=deg(-90)),
    Furniture(uid="AQTQJBTXRR", tag="FURN-M-KIT-WE1", type_ref="CASE-W30", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(27, 11)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    Furniture(uid="VKP909PNS6", tag="FURN-M-KIT-WE2", type_ref="CASE-W24", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(30, 2)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),

    # Island — 5' x 3', the mid-landing of a work triangle the architect's fridge-west /
    # sink-east program stretches to ~30' of perimeter. Dropped 6" south of where it started
    # so the work aisle is 42" rather than 36": the range front is at y=32'-11 3/8" and the
    # island's north face is now 29'-5 3/8". 36" is the bare code-side minimum a body fits
    # through; 42" is the NKBA one-cook recommendation, and it is the number that lets the
    # oven door (a 30" range's drops ~24") open with someone still standing behind it.
    # 36" deep = 24" of carcass plus the 12" overhang the stools tuck under.
    Furniture(uid="PD9W4Q86MD", tag="FURN-M-KIT-ISLAND", type_ref="CASE-ISLAND-60", room="RM-M-LIVING",
              position=pt(ft(27, 6), ft(27, 11.375))),
    Furniture(uid="MZNJ9TAN56", tag="FURN-M-KIT-STOOL1", type_ref="FURN-BAR-STOOL", room="RM-M-LIVING",
              position=pt(ft(26), ft(26, 1)), rotation=deg(180)),
    Furniture(uid="TMR4RNV2E3", tag="FURN-M-KIT-STOOL2", type_ref="FURN-BAR-STOOL", room="RM-M-LIVING",
              position=pt(ft(27, 6), ft(26, 1)), rotation=deg(180)),
    Furniture(uid="1RME2HHSQT", tag="FURN-M-KIT-STOOL3", type_ref="FURN-BAR-STOOL", room="RM-M-LIVING",
              position=pt(ft(29), ft(26, 1)), rotation=deg(180)),

    # The main-floor bedroom's queen, head north (rotation 0) against the interior wall, so
    # the two window walls — west (WIN-M-BED-W1/W2) and south (WIN-M-BED-S1/S2) — stay free.
    # x=5' is what keeps the west side zone off ED-M-BED-RC7 on the west wall and the east
    # one off ED-M-BED-RC1; y=9'-3" holds the foot zone clear of that same pair. This is the
    # one bedroom where the queen keeps all three zones whole with room left over.
    Furniture(uid="CMB701AAAA", tag="FURN-M-BED", type_ref="FURN-BED-KING", room="RM-M-BED",
              position=pt(m(2.5945), m(2.89975))),
]
GARAGE_PLACEABLES = []
# The three east bedrooms are the same 13'-11 3/4" x 8'-10 3/4" clear box, so they get the
# same bed layout: a queen with its head north (rotation 0 puts the back at +y) and its 2'
# side-access zones running the *long* way, where there is room for them.
#
# Head against the east wall — under the window, where FURN-S-BED1 started — cannot work
# here. That orientation lays the 5'-4" width across the 8'-10 3/4" dimension, which needs
# 9'-4" once both 2' side zones are counted; the 5 1/4" shortfall pushed each zone through a
# long wall and onto the NEC 210.52 fill receptacles at 16" (integrity.placeable_recommended_
# clearance_conflict, four of them off the one bed). Turning the beds resolves it: the side
# zones now land in the 14' direction with feet to spare, and only the 2'-6" foot zone is
# short, which it borrows from the room beyond the wall rather than from a receptacle.
#
# The x centreline and the y positions are picked, not rounded: x=30' is the one band whose
# side zones clear the RC1 (north wall, x~25'-10") and RC2 (east wall) outlets, and the beds
# sit 9'-7" apart rather than on the rooms' 9'-0" pitch so each foot zone stops short of the
# headboard of the bed in the room below it. Heads therefore float 5"-6" off the north wall.
SECOND_PLACEABLES = [
    Furniture(uid="819QDDYMZ5", tag="FURN-S-BED1", type_ref="FURN-QUEEN-BED", room="RM-S-BED1",
              position=pt(m(9.71131), m(4.07897)), rotation=deg(270)),
    Furniture(uid="CSB701AAAA", tag="FURN-S-BED2", type_ref="FURN-QUEEN-BED", room="RM-S-BED2",
              position=pt(m(9.68788), m(6.90099)), rotation=deg(-90)),
    Furniture(uid="CSB702AAAA", tag="FURN-S-BED3", type_ref="FURN-QUEEN-BED", room="RM-S-BED3",
              position=pt(m(9.70988), m(9.5886)), rotation=deg(-90)),
    # Each regular bedroom gets the same compact study pair in the west-side strip. The
    # desk's back is against the west wall (rotation 90), leaving its pull-out zone toward
    # the room; the dining chair keeps the lighter dining-room plan and 3D appearance.
    Furniture(uid="DSK701AAAA", tag="FURN-S-DESK1", type_ref="FURN-DESK-48", room="RM-S-BED1",
              position=pt(m(7.24324), m(3.53828)), rotation=deg(90)),
    Furniture(uid="CHR701AAAA", tag="FURN-S-DESK-CHAIR1", type_ref="FURN-DESK-CHAIR", room="RM-S-BED1",
              position=pt(ft(25, 6), ft(11, 6)), rotation=deg(90)),
    Furniture(uid="DSK702AAAA", tag="FURN-S-DESK2", type_ref="FURN-DESK-48", room="RM-S-BED2",
              position=pt(ft(23, 9), ft(20, 6)), rotation=deg(90)),
    Furniture(uid="CHR702AAAA", tag="FURN-S-DESK-CHAIR2", type_ref="FURN-DESK-CHAIR", room="RM-S-BED2",
              position=pt(ft(25, 6), ft(20, 6)), rotation=deg(90)),
    Furniture(uid="DSK703AAAA", tag="FURN-S-DESK3", type_ref="FURN-DESK-48", room="RM-S-BED3",
              position=pt(ft(23, 9), ft(32, 6)), rotation=deg(90)),
    Furniture(uid="CHR703AAAA", tag="FURN-S-DESK-CHAIR3", type_ref="FURN-DESK-CHAIR", room="RM-S-BED3",
              position=pt(ft(25, 6), ft(32, 6)), rotation=deg(90)),
    # The master takes the king, head against the closet/bath wall that closes the suite's
    # west strip at x=9'-6 7/8" (rotation -90 turns its back to +x), so the bed faces west
    # into WIN-S-SUITE1/2 and the 2'-6" foot zone runs out to the window wall instead of into
    # a partition. It is the one bedroom wide enough to hold a 6'-8" bed with both 2' side
    # zones intact, and it does: nothing here is short.
    Furniture(uid="CSB703AAAA", tag="FURN-S-SUITE-BED", type_ref="FURN-QUEEN-BED",
              room="RM-S-SUITE", position=pt(m(1.51666), m(5.64775)), rotation=deg(0)),
]
ATTIC_PLACEABLES = []

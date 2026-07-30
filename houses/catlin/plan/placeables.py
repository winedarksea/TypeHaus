# haus: editable
from typehaus import (Appliance, ElectricalDevice, Equipment, Fixture, Furniture, Mount,
                      MountKind, Register)
from typehaus.model import DeviceKind, deg, ft, inch, m, pt

# Project-local canvas placement targets.  One list per storey keeps source ownership
# explicit while allowing every placeable domain to use the same writeback contract.
#
# The main-floor set is a furnished living/dining zone against the shared starter catalog:
# rotation 0 puts an object's back at +y (project north), so the sofa faces the media
# console across the room and the chairs face the table from both sides.

# FX-1, the furnace-room utility sink, stood here until 2026-07-30. It is gone, not deleted:
# the owner's decision that day put a bathroom at the foot of the stair and moved the
# basement's one lavatory into it as FX-B-BATH-LAV (plan/fixtures.py), which carries this
# fixture's uid forward. What went with it: SP-B-UTILITY became the new WC's stub-up,
# SP-B-CW-UTIL-DR became SP-B-CW-BATH-DR, and PR-B-UTIL-DRAIN / -VENT / PR-B-CW-UTIL /
# PR-B-HW-UTIL were all re-pointed at the new room (plan/mep.py).
#
# The one thing that did *not* simply follow it is the heat-pump condensate: PR-B-COND used to
# air-gap over this sink's basin. It now terminates over FX-B-SAUNA-FD, the sauna wet floor's
# drain — a trapped indirect-waste receptor that sees water in normal use, which is what a
# condensate air gap wants and what a finished bathroom lavatory is not.
#
# The sauna benches are dimensioned to *liner faces*, not to the node lines the walls are
# authored on, because that is the surface the joiner scribes to. Read off the resolved
# wall layers: west liner x=9'-1 13/16", east liner (the liner-on-concrete centre wall)
# x=17'-2 1/2", south concrete face y=1'-0", north liner y=13'-6 1/8" — an 8'-0 11/16" x
# 12'-6 1/8" clear box. notes/sauna_shower_basement_detail.md reserves the north 4' for the
# shower, so everything below stops at y=9'-6" and the benches never cross into it.
BASEMENT_PLACEABLES = [
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
    # East living-room storage: nine 23 5/8" BESTA units fill the 17'-10" clear span from
    # the fireplace's north edge at y=4'-10" toward the 48" pantry closet's south edge at
    # y=22'-8". Their backs sit directly on the east wall's interior face at x=35'-5 3/8";
    # the 1 3/8" residual at the pantry end is the only non-module tolerance in the run.
    # Rotation -90 puts each unit's back against the east wall and opens it toward the room.
    Furniture(uid="CMB801AAAA", tag="FURN-M-LIVING-BESTA-01", type_ref="FURN-BESTA-2358",
              room="RM-M-LIVING", position=pt(ft(34, 9.125), ft(5, 9.8125)), rotation=deg(-90)),
    Furniture(uid="CMB802AAAA", tag="FURN-M-LIVING-BESTA-02", type_ref="FURN-BESTA-2358",
              room="RM-M-LIVING", position=pt(ft(34, 9.125), ft(7, 9.4375)), rotation=deg(-90)),
    Furniture(uid="CMB803AAAA", tag="FURN-M-LIVING-BESTA-03", type_ref="FURN-BESTA-2358",
              room="RM-M-LIVING", position=pt(ft(34, 9.125), ft(9, 9.0625)), rotation=deg(-90)),
    Furniture(uid="CMB804AAAA", tag="FURN-M-LIVING-BESTA-04", type_ref="FURN-BESTA-2358",
              room="RM-M-LIVING", position=pt(ft(34, 9.125), ft(11, 8.6875)), rotation=deg(-90)),
    Furniture(uid="CMB805AAAA", tag="FURN-M-LIVING-BESTA-05", type_ref="FURN-BESTA-2358",
              room="RM-M-LIVING", position=pt(ft(34, 9.125), ft(13, 8.3125)), rotation=deg(-90)),
    Furniture(uid="CMB806AAAA", tag="FURN-M-LIVING-BESTA-06", type_ref="FURN-BESTA-2358",
              room="RM-M-LIVING", position=pt(ft(34, 9.125), ft(15, 7.9375)), rotation=deg(-90)),
    Furniture(uid="CMB807AAAA", tag="FURN-M-LIVING-BESTA-07", type_ref="FURN-BESTA-2358",
              room="RM-M-LIVING", position=pt(ft(34, 9.125), ft(17, 7.5625)), rotation=deg(-90)),
    Furniture(uid="CMB808AAAA", tag="FURN-M-LIVING-BESTA-08", type_ref="FURN-BESTA-2358",
              room="RM-M-LIVING", position=pt(ft(34, 9.125), ft(19, 7.1875)), rotation=deg(-90)),
    Furniture(uid="CMB809AAAA", tag="FURN-M-LIVING-BESTA-09", type_ref="FURN-BESTA-2358",
              room="RM-M-LIVING", position=pt(ft(34, 9.125), ft(21, 6.8125)), rotation=deg(-90)),
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
              position=pt(m(8.24278), m(5.2201))),
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
    # Swapped 2026-07-30 (owner's call): the cooking wall and the sink wall traded places, so
    # the sink now sits under north light instead of east and the range moved to the east
    # wall. Two datums still set every number below, both finish faces read off the resolved
    # wall layers rather than off the module lines: the north and east interior gwb are at
    # 35'-5 3/8" (36' sheathing - 1/2" sheathing - 5 1/2" stud - 5/8" gwb), and the centre
    # bearing wall's east gwb is at 18'-3 3/8". Cabinet backs sit on those faces, so the runs
    # are dimensioned the way a millwork shop would measure them, not to wall centrelines.
    #
    # Rotation says which way a unit opens: 0 = back north, deg(90) = back west/opens east,
    # deg(-90) = back east/opens west, deg(180) = back south.
    #
    # The two runs share one inside corner (35'-5 3/8", 35'-5 3/8") and only one of them can
    # physically turn it — a run's own 24"-deep footprint can't overlap the perpendicular
    # run's. Before the swap the sink run (east) claimed the corner and the cooking run
    # (north) yielded at x=33'-4", 1 3/8" shy of the sink run's depth-zone. Now that's
    # mirrored: the cooking run (east) claims the corner and the sink run (north) yields at
    # the same x=33'-4", 1 3/8" shy of the cooking run's depth-zone — same joint, same
    # numbers, just which run gets to turn it has swapped with them.

    # West run — cold storage and pantry against the centre bearing wall, opening east into
    # the kitchen. Untouched by the swap. Packed from the north wall down: 12" + 18" tall
    # pull-outs, freezer, refrigerator, then the closet pantry in the nook by the stair tee.
    # The two cold boxes sit *below* the talls deliberately — their 3' door zones reach
    # x=24'-1 3/8", and any further north that band would run into the north counter run at
    # y=33'-5 3/8". Cabinets are 24" deep (centre x = 19'-3 3/8"); the cold boxes are 34"
    # (centre 19'-8 3/8").
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

    # North run — the sink wall. Sink and dishwasher flipped 2026-07-30 (owner's call) to pull
    # the sink toward the middle of the run: pantry and the base cabinet stay put, but the
    # sink now sits where the dishwasher used to (closer to the run's centre) and the
    # dishwasher takes the sink's old spot, immediately east of it — the opposite hand from
    # before, since the swap put the sink on the pantry side. Bases are 24" deep, centre
    # y=34'-5 3/8".
    Furniture(uid="Z0H6MVXC71", tag="FURN-M-KIT-PANTRY-E", type_ref="CASE-PANTRY-CLOSET-48", room="RM-M-LIVING",
              position=pt(ft(22, 7), ft(34, 5.375))),
    Furniture(uid="49B0RDP4NW", tag="FURN-M-KIT-E1", type_ref="CASE-B30", room="RM-M-LIVING",
              position=pt(ft(25, 10), ft(34, 5.375))),
    # The 36" sink base centres close to WIN-M-KITCH (moved with it — see OPENINGS in
    # storeys/main.py), 7" off true centre so the RO still lands on a stud line.
    Furniture(uid="F8A30SK31X", tag="FURN-M-KIT-SINKBASE", type_ref="CASE-SINK-BASE-36", room="RM-M-LIVING",
              position=pt(ft(28, 7), ft(34, 5.375))),
    Appliance(uid="XPA5ZCQM5Q", tag="APPL-M-DW", type_ref="APPL-DISHWASHER", room="RM-M-LIVING",
              position=pt(ft(31, 1), ft(34, 5.375))),
    Furniture(uid="3QTQ2NFWYD", tag="FURN-M-KIT-E2", type_ref="CASE-B15", room="RM-M-LIVING",
              position=pt(ft(32, 8.5), ft(34, 5.375))),

    # North wall uppers — WE1 stays over the base; WE2 followed the dishwasher to its new
    # spot. Nothing over the sink (the window's there), the pantry (already full height) or
    # the corner filler.
    Furniture(uid="AQTQJBTXRR", tag="FURN-M-KIT-WE1", type_ref="CASE-W30", room="RM-M-LIVING",
              position=pt(ft(25, 10), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    Furniture(uid="VKP909PNS6", tag="FURN-M-KIT-WE2", type_ref="CASE-W24", room="RM-M-LIVING",
              position=pt(ft(31, 1), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),

    # East run — the cooking wall. Range and hood flipped 2026-07-30 (owner's call) further
    # north, swapping with N3: the corner filler N4 is unchanged, but the range now sits
    # where N3 used to and N3 takes the range's old spot, closer to N2/N1 to the south. Bases
    # are 24" deep (centre x = 34'-5 3/8"); the range is 30" deep and centres 3" further out
    # at 34'-2 3/8", same as it always did, and still the number the island aisle is measured
    # from.
    #
    # This run still claims the corner (N4 runs flush to 35'-5 3/8" — see header): the range
    # moving doesn't change which run gets to turn it, since N4 didn't move.
    Furniture(uid="KA0ETVK8F8", tag="FURN-M-KIT-N4", type_ref="CASE-B30", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(34, 2.375)), rotation=deg(-90)),
    Appliance(uid="417H1EH5C3", tag="APPL-M-RANGE", type_ref="APPL-ELECTRIC-RANGE", room="RM-M-LIVING",
              position=pt(ft(34, 2.375), ft(31, 8.375)), rotation=deg(-90)),
    Furniture(uid="7YPYR8K5FS", tag="FURN-M-KIT-N3", type_ref="CASE-B36", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(28, 11.375)), rotation=deg(-90)),
    Furniture(uid="BZ9SVQVTVP", tag="FURN-M-KIT-N2", type_ref="CASE-B24", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(26, 5.375)), rotation=deg(-90)),
    Furniture(uid="NF48E9MESN", tag="FURN-M-KIT-N1", type_ref="CASE-B36", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(23, 11.375)), rotation=deg(-90)),

    # East wall uppers, 13" deep at a 54" mount. With the range between N4 and N3 now, N3+N4
    # no longer share a face for one CASE-W66; N4 gets its own 30" box, and N3+N2 (36"+24" =
    # 60", the same combination the old WN1/WN2 pair covered) split into two plain 30" boxes.
    # N1 (south end) still gets no upper, same as before.
    Furniture(uid="2BF9VM3SFA", tag="FURN-M-KIT-WN1", type_ref="CASE-W30", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(34, 2.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    Furniture(uid="4HM5A8P53B", tag="FURN-M-KIT-WN2", type_ref="CASE-W30", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(26, 8.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    # Recirculating canopy hood, 30" over the cooktop: mount 5'-6" on a 3' range. Moved north
    # with the range.
    Appliance(uid="Q0W3FYXJGX", tag="APPL-M-HOOD", type_ref="APPL-HOOD-RECIRC", room="RM-M-LIVING",
              position=pt(ft(34, 7.375), ft(31, 8.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
    Furniture(uid="DVWYR4A5J3", tag="FURN-M-KIT-WN3", type_ref="CASE-W30", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(29, 2.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),

    # Island — 5' x 3', footprint unchanged by the swap. Its 42" work aisle used to be
    # measured off the range's old front (y=32'-11 3/8", north face at 29'-5 3/8"); left in
    # place pending `haus check` against the new range (east wall) and sink (north wall)
    # locations, since neither is the wall this clearance used to read from.
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

    # --- mudroom (RM-M-MUDROOM), converted from storage 2026-07-28 --------------------
    # South closet backs onto the south wall, running from its door to the west wall. Its
    # north-wall counterpart, FURN-M-MUD-CLOSET-N, was reframed as RM-M-MECH (2026-07-28,
    # storeys/main.py) — the radon+plumbing shaft needed real walls, not furniture, and
    # that corner was the NW-most one available.
    Furniture(uid="CMF802AAAA", tag="FURN-M-MUD-CLOSET-S", type_ref="FURN-M-MUD-CLOSET-S",
              room="RM-M-MUDROOM", position=pt(ft(3, 8.0625), ft(28, 2.1875)),
              rotation=deg(180)),
    # Back to the west wall (rotation 90 = back west, opens east), centred on WIN-M-MUD at
    # y=31'-4" so the aisle between the two closets above lands on the window too.
    Furniture(uid="CMF803AAAA", tag="FURN-M-MUD-BENCH", type_ref="FURN-M-MUD-BENCH",
              room="RM-M-MUDROOM", position=pt(ft(1, 3.125), ft(31, 4)),
              rotation=deg(90)),
]
GARAGE_PLACEABLES = [
    # The 60"-wide work surface runs along the west wall directly below the infrared
    # heater lamp. Rotation 90° turns the 30" depth into the wall-to-room dimension.
    Furniture(uid="CGF601AAAA", tag="FURN-G-WORKBENCH", type_ref="FURN-G-WORKBENCH",
              room="RM-GARAGE", position=pt(m(0.596858), m(14.4756)), rotation=deg(90)),
]
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
              position=pt(m(9.95741), m(9.68733)), rotation=deg(0)),
    # Each regular bedroom gets the same compact study pair in the west-side strip. The
    # desk's back is against the west wall (rotation 90), leaving its pull-out zone toward
    # the room; the dining chair keeps the lighter dining-room plan and 3D appearance.
    Furniture(uid="DSK701AAAA", tag="FURN-S-DESK1", type_ref="FURN-DESK-48", room="RM-S-BED1",
              position=pt(m(7.05463), m(3.4224)), rotation=deg(90)),
    Furniture(uid="CHR701AAAA", tag="FURN-S-DESK-CHAIR1", type_ref="FURN-DESK-CHAIR", room="RM-S-BED1",
              position=pt(m(7.61089), m(3.43304)), rotation=deg(-90)),
    Furniture(uid="DSK702AAAA", tag="FURN-S-DESK2", type_ref="FURN-DESK-48", room="RM-S-BED2",
              position=pt(m(7.3692), m(5.88414)), rotation=deg(0)),
    Furniture(uid="CHR702AAAA", tag="FURN-S-DESK-CHAIR2", type_ref="FURN-DESK-CHAIR", room="RM-S-BED2",
              position=pt(m(7.38828), m(6.31867)), rotation=deg(0)),
    Furniture(uid="DSK703AAAA", tag="FURN-S-DESK3", type_ref="FURN-DESK-48", room="RM-S-BED3",
              position=pt(m(8.43311), m(10.4735)), rotation=deg(0)),
    Furniture(uid="CHR703AAAA", tag="FURN-S-DESK-CHAIR3", type_ref="FURN-DESK-CHAIR", room="RM-S-BED3",
              position=pt(m(8.41785), m(10.0705)), rotation=deg(180)),
    # Compact two-person table in Study 2: west of and north of WIN-S-STUDY1, against the
    # south wall. Its west edge stays 8" clear of D-S-DECK-E's east jamb; the two chairs sit
    # on the north side, so neither the table nor its usable seating is in the door opening.
    Furniture(uid="TAB701AAAA", tag="FURN-S-STUDY-TABLE", type_ref="FURN-DINING-2-36",
              room="RM-S-STUDY2", position=pt(m(8.10913), m(0.646066))),
    Furniture(uid="CHR704AAAA", tag="FURN-S-STUDY-CHAIR1", type_ref="FURN-DINING-CHAIR",
              room="RM-S-STUDY2", position=pt(m(8.90614), m(0.530999)), rotation=deg(-90)),
    Furniture(uid="CHR705AAAA", tag="FURN-S-STUDY-CHAIR2", type_ref="FURN-DINING-CHAIR",
              room="RM-S-STUDY2", position=pt(m(7.32372), m(0.536064)), rotation=deg(90)),
    # A compact rocking chair occupies the southeast corner, below WIN-S-STUDY3 and with its
    # back to the south wall. The armchair symbol is the intentional close-enough 2D/3D
    # approximation: it keeps the plan readable while the catalog type preserves the use.
    Furniture(uid="RCK701AAAA", tag="FURN-S-STUDY-ROCKING-CHAIR",
              type_ref="FURN-ROCKING-CHAIR-30", room="RM-S-STUDY2",
              position=pt(m(10.1672), m(0.722925)), rotation=deg(225)),
    # The master takes the king, head against the closet/bath wall that closes the suite's
    # west strip at x=9'-6 7/8" (rotation -90 turns its back to +x), so the bed faces west
    # into WIN-S-SUITE1/2 and the 2'-6" foot zone runs out to the window wall instead of into
    # a partition. It is the one bedroom wide enough to hold a 6'-8" bed with both 2' side
    # zones intact, and it does: nothing here is short.
    Furniture(uid="CSB703AAAA", tag="FURN-S-SUITE-BED", type_ref="FURN-QUEEN-BED",
              room="RM-S-SUITE", position=pt(m(1.52182), m(5.57379)), rotation=deg(0)),

    # Hanging storage for the three east bedrooms, which have no built-in closet: one 48"
    # sliding-door wardrobe each, backed onto a partition.
    #
    # These rooms are full, and the placement is what the geometry allows rather than what
    # the elevation would prefer. The east wall — the exterior side, the obvious wall for a
    # case run — cannot take one: each bed's head is against it (footprints x 28'-4 1/3" to
    # 35'-4 1/3"), leaving 4 3/4" north of the bed's side-access zone and 2" south of it.
    # The west wall is the hall wall, and D-S-BED1/2/3 with their 2'-6" swings own the only
    # runs on it long enough. That leaves the north and south partitions, and the choice
    # between them is per-room because the desk pairs sit in different halves.
    #
    # Every candidate 4'-0 x 2'-0 slot against a wall in each room was enumerated on a 1"
    # grid against the resolved footprints, the resolved recommended-clearance rings and the
    # doors' swing polygons (clear faces: x 21'-11 5/8"..35'-11 3/8"; BED1 y 9'-0 5/8"..
    # 17'-11 3/8", BED2 +9', BED3 +18'). The results:
    #
    # - BED2 north partition and BED3 south partition each have a slot that conflicts with
    #   nothing at all, so both take one.
    # - BED1 has none. Its door lands at y 13'-11" to 16'-5", so the north wall's clear run
    #   starts at x=23'-4 1/2" where the swing arc leaves the wall, and the bed's 18"
    #   recommended foot zone starts at x=26'-10 1/3": 3'-5 3/4" of wall for a 4'-0 case.
    #   The position below is the least-bad of the enumeration — clear of the swing, clipping
    #   the foot zone by 1 7/32" over 6 5/16" (0.05 sf), which reports as one
    #   integrity.placeable_recommended_clearance_conflict advisory. Moving the bed 1 7/32"
    #   south would clear it, but that breaks the 9'-7" bed-to-bed pitch the comment above
    #   is built on and pushes the bed's south side zone onto the room's south wall.
    #
    # BED1's and BED2's wardrobes stand over ED-S-BED1-RC1 / ED-S-BED2-RC1, the north-wall
    # general receptacles at 16"-18" AFF. That is not a code problem (210.52 spacing counts
    # the receptacle whether or not a case stands in front of it) but it is worth knowing
    # before the electrician sets the boxes: neither room has a 4'-0 run of wall without one.
    Furniture(uid="CSB704AAAA", tag="FURN-S-BED1-WARD", type_ref="FURN-WARDROBE-48",
              room="RM-S-BED1", position=pt(m(7.36343), m(5.11445)), rotation=deg(0)),
    Furniture(uid="CSB705AAAA", tag="FURN-S-BED2-WARD", type_ref="FURN-WARDROBE-48",
              room="RM-S-BED2", position=pt(m(7.36477), m(7.8429)), rotation=deg(0)),
    Furniture(uid="CSB706AAAA", tag="FURN-S-BED3-WARD", type_ref="FURN-WARDROBE-48",
              room="RM-S-BED3", position=pt(m(7.04819), m(10.1621)), rotation=deg(90)),

    # Linen/towel storage in the hall bath, on the wall the room has nothing else on. The
    # pantry-closet carcass is the right box for it: 72" x 24" x 96", one plan symbol,
    # three 24" doors (CASE-PANTRY-CLOSET-72). RM-S-BATH1's clear face runs
    # x 0'-0 5/8"..9'-11 3/8", y 26'-4 5/8"..35'-11 3/8", and the south wall is the only run
    # it has free — the west wall above it is taken by the WC (x 1'-3 1/4"..3'-9 1/4",
    # y 28'-10 1/2"..31'-4 1/2") and by WIN-S-BATH-W, the north wall by the shower pan, the
    # east wall by the lav and its mirror. Backed onto the south wall (rotation 180 turns the
    # carcass back to -y) and run out of the SW corner, the unit occupies
    # x 0'-0 5/8"..6'-0 5/8", y 26'-4 5/8"..28'-4 5/8": still short of D-S-BATH1's opening at
    # x=7'-3", clear of the WC's REQUIRED 30"/21" zone (which starts at y 28'-10 1/2"), and
    # of every device on the walls. The 48" it replaces stopped at x 4'-0 5/8".
    Furniture(uid="CSB707AAAA", tag="FURN-S-BATH1-CLOSET", type_ref="CASE-PANTRY-CLOSET-72",
              room="RM-S-BATH1", position=pt(m(1.09343), m(8.42656)),
              rotation=deg(180)),
    # RM-S-PLANT is furnished as what it is: a place to sit among the plants, not a store
    # room. The room's clear face is the full x 0'-0 5/8"..17'-11 3/8", y 0'-0 5/8"..8'-11 3/8"
    # bay, and the program divides along y — plants on the glass, seating behind them.
    #
    # The two plants stand directly under ED-S-PLANT-TUBE1/2 (plan/lighting.py: x=5'/13',
    # y=2', suspended 2'-3" below the ceiling), which is the whole reason those tubes are on a
    # photoperiod timer: the light has to land on the foliage, not beside it. That also puts
    # both pots in the south glazing — WIN-S-PLANT1 is centred x=5'-4" and WIN-S-PLANT2
    # x=13'-4", both with 2'-0" sills — so each plant gets daylight and the tube supplements
    # it. An 18" pot at y=2' occupies y 1'-3"..2'-9", well off the 5/8" wall face.
    #
    # The chairs sit north of the plants facing them (rotation 0 puts a chair's back at +y, so
    # it looks south down the room and out the windows). Neither reaches the plants: the
    # armchair spans x 5'-6 1/2"..8'-5 1/2", the rocker x 9'-9"..12'-3", and both run
    # y 4'-0"..7'-0" against the plants' 2'-9" north edge — 1'-3" of walk-through between the
    # two zones. The 1'-3" gap the chairs leave each other straddles REG-S-SUP1 at (9', 4'),
    # which is a recessed floor register: nothing stands on it either way.
    #
    # East is the constraint that sets the chairs' x, not the west wall: D-S-PLANT swings off
    # the centre bearing line at y=4'-5 1/2" and its 2'-6" leaf sweeps back to about
    # x=15'-5". Both chairs stop 3'-2" short of that arc.
    Furniture(uid="PLT701AAAA", tag="FURN-S-PLANT-POT1", type_ref="FURN-PLANT-18",
              room="RM-S-PLANT", position=pt(ft(5), ft(2))),
    Furniture(uid="PLT702AAAA", tag="FURN-S-PLANT-POT2", type_ref="FURN-PLANT-18",
              room="RM-S-PLANT", position=pt(ft(13), ft(2))),
    Furniture(uid="CHR706AAAA", tag="FURN-S-PLANT-CHAIR", type_ref="FURN-ARMCHAIR-35",
              room="RM-S-PLANT", position=pt(m(1.13772), m(1.8808)), rotation=deg(45)),
    Furniture(uid="RCK702AAAA", tag="FURN-S-PLANT-ROCKER", type_ref="FURN-ROCKING-CHAIR-30",
              room="RM-S-PLANT", position=pt(m(4.06734), m(1.93971)), rotation=deg(-45)),
    ElectricalDevice(uid="QTS0020AAA", tag="ED-S-PLANT-SPOT", kind=DeviceKind.LIGHT,
                     position=pt(m(1.2726), m(2.63984)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-S-PLANT",
                     controlled_by=("ED-S-PLANT-SW-TIMER",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
]
# The attic study uses the same compact work-and-meeting program as the second-storey
# study, but the stair opening occupies the north side of the room. Keep the desk in the
# west strip and put the two-person table in the southeast bay, clear of the stair head and
# the study door. The desk's back is against the west side (rotation 90); the table and
# chairs reuse the Study 2 catalog family and arrangement.
ATTIC_PLACEABLES = [
    Furniture(uid="DAK701AAAA", tag="FURN-A-STUDY-DESK", type_ref="FURN-DESK-48",
              room="RM-A-STUDY", position=pt(m(10.1656), m(0.489306)), rotation=deg(0)),
    Furniture(uid="CAK701AAAA", tag="FURN-A-STUDY-DESK-CHAIR", type_ref="FURN-DESK-CHAIR",
              room="RM-A-STUDY", position=pt(m(10.205), m(1.10716)), rotation=deg(0)),
    Furniture(uid="TAK701AAAA", tag="FURN-A-STUDY-TABLE", type_ref="FURN-DINING-2-36",
              room="RM-A-STUDY", position=pt(m(8.24139), m(0.65023))),
    Furniture(uid="CAK702AAAA", tag="FURN-A-STUDY-CHAIR1", type_ref="FURN-DINING-CHAIR",
              room="RM-A-STUDY", position=pt(m(9.03786), m(0.532453)), rotation=deg(-90)),
    Furniture(uid="CAK703AAAA", tag="FURN-A-STUDY-CHAIR2", type_ref="FURN-DINING-CHAIR",
              room="RM-A-STUDY", position=pt(m(7.45287), m(0.57089)), rotation=deg(90)),
]

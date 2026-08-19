# haus: editable
from typehaus import (Appliance, ElectricalDevice, Equipment, Fixture, Furniture, Mount,
                      MountKind, Register)
from typehaus.model import DeviceKind, deg, ft, inch, m, pt

# Project-local canvas placement targets. One list per storey keeps source ownership
# explicit. Main-floor rotation 0 puts an object's back at +y (project north).

# FX-1 (furnace-room utility sink) was removed 2026-07-30: a bathroom went at the foot of
# the stair and the basement's lavatory became FX-B-BATH-LAV (plan/fixtures.py), inheriting
# this uid. SP-B-UTILITY -> new WC's stub-up, SP-B-CW-UTIL-DR -> SP-B-CW-BATH-DR, and
# PR-B-UTIL-DRAIN/-VENT/PR-B-CW-UTIL/PR-B-HW-UTIL re-pointed at the new room (plan/mep.py).
# Exception: PR-B-COND (heat-pump condensate) no longer air-gaps over this sink — it now
# terminates over FX-B-SAUNA-FD, the sauna's trapped wet-floor drain, which sees regular
# water flow the way an air gap wants and a bathroom lavatory does not.
#
# Sauna benches are dimensioned to *liner faces* (what the joiner scribes to), not node
# lines: west liner x=9'-1 13/16", east liner x=17'-2 1/2", south liner y=1'-3 1/2", north
# liner y=13'-6 1/8" — an 8'-0 11/16" x 12'-2 5/8" clear box. The south face gained 3 1/2"
# of liner (SAUNA_LINER_ON_BASEMENT_12_GARDEN on W-B-S2) on 2026-08-18, so both benches
# moved north with it. The east bench stops at y=9'-9 1/2" to leave the north end for the
# shower (notes/sauna_shower_basement_detail.md).
BASEMENT_PLACEABLES = [
    # The long two-tier run takes the east wall: it is the only unbroken face in the room —
    # the west wall has D-B-SAUNA, the south wall WIN-B-SAUNA — so the bench lands as one
    # 8'-6" carcass with no scribes around an opening. rotation -90 puts its back (+y local)
    # against that face, giving x 13'-8 1/2"..17'-2 1/2" and
    # y 1'-3 1/2"..9'-9 1/2" — still clearing FX-B-SAUNA-SH's pan by 8 11/16" at its north end.
    Furniture(uid="CBF601AAAA", tag="FURN-B-SAUNA-BENCH-E", type_ref="FURN-SAUNA-BENCH-2T-102",
              room="RM-B-SAUNA", position=pt(ft(15, 5.5), ft(5, 6.5)), rotation=deg(-90)),
    # The foot bench returns along the south wall, butted into the two-tier run's west face
    # at 13'-8 1/2" with an 11/16" scribe left at the west liner. rotation 180 puts its back
    # to the south. Its top is 18", well clear of WIN-B-SAUNA's 3'-0" sill above it.
    Furniture(uid="CBF602AAAA", tag="FURN-B-SAUNA-BENCH-S", type_ref="FURN-SAUNA-BENCH-54",
              room="RM-B-SAUNA", position=pt(ft(11, 5.5), ft(2, 1.5)), rotation=deg(180)),
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
    # Dining at 17'-4" (moved 4' south once the island moved down and the 48" pantry took
    # the east wall to 22'-8"). Chair-use zone y=12'-7"..22'-1": clear of the sofa (10'-5")
    # and pantry (7"), with a 4'-4" circulation band to the island.
    #
    # Only the six side chairs are drawn on this 8-place table — end chairs would block the
    # hall-to-east-windows walk, so those two places stay unset, brought in when needed.
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
    # Cooking wall and sink wall swapped 2026-07-30 (owner's call): sink now under north
    # light, range on the east wall. Runs are dimensioned to resolved finish faces (a
    # millwork-shop measurement), not wall centrelines: north/east interior gwb at
    # 35'-5 3/8", centre bearing wall's east gwb at 18'-3 3/8". Rotation: 0 = back north,
    # deg(90) = back west/opens east, deg(-90) = back east/opens west, deg(180) = back south.
    #
    # The two runs share one inside corner (35'-5 3/8", 35'-5 3/8"); only one 24"-deep run
    # can physically turn it. Post-swap the cooking run (east) claims it and the sink run
    # (north) yields at x=33'-4" — same joint/numbers as before the swap, just mirrored.

    # West run — cold storage and pantry against the centre bearing wall, opening east;
    # untouched by the swap. North to south: 12"+18" tall pull-outs, freezer, refrigerator,
    # closet pantry. Cold boxes sit below the talls so their 3' door zones (to x=24'-1 3/8")
    # don't run into the north counter run at y=33'-5 3/8". Cabinets 24" deep (centre
    # x=19'-3 3/8"); cold boxes 34" deep (centre 19'-8 3/8").
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
    # Over the two cold boxes: 24" deep like the talls, so all four fronts land on x=20'-3 3/8"
    # and the appliances stand 10" proud — clearing the fridge/freezer door swing.
    Furniture(uid="8T3D1P2QRV", tag="FURN-M-KIT-OVER-FRIDGE", type_ref="CASE-OVER-36", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(31, 5.375)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
    Furniture(uid="Y4KJ6WB0ZC", tag="FURN-M-KIT-OVER-FREEZER", type_ref="CASE-OVER-36", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(28, 5.375)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(6))),

    # North run — the sink wall. Sink and dishwasher flipped 2026-07-30 (owner's call): sink
    # now sits where the dishwasher used to (closer to run centre, pantry side), dishwasher
    # takes the sink's old spot immediately east. Bases 24" deep, centre y=34'-5 3/8".
    Furniture(uid="Z0H6MVXC71", tag="FURN-M-KIT-PANTRY-E", type_ref="CASE-PANTRY-CLOSET-48", room="RM-M-LIVING",
              position=pt(ft(22, 7), ft(34, 5.375))),
    Furniture(uid="49B0RDP4NW", tag="FURN-M-KIT-E1", type_ref="CASE-B30", room="RM-M-LIVING",
              position=pt(ft(25, 10), ft(34, 5.375))),
    # The 36" sink base centres close to WIN-M-KITCH (moved with it — see OPENINGS in
    # storeys/main.py), 7" off true centre so the RO still lands on a stud line.
    Furniture(uid="F8A30SK31X", tag="FURN-M-KIT-SINKBASE", type_ref="CASE-SINK-BASE-36", room="RM-M-LIVING",
              position=pt(ft(28, 7), ft(34, 5.375))),
    # Disposer hangs off FX-M-KITCH-SINK's drain fitting, at the sink's `drain_position`
    # (28'-7", 35'-0") — the flange, where the trap and SP-M-KITCH already are — not the
    # bowl centre. 14 1/2" mount = base of body (27" bowl bottom minus 12 1/2" cylinder).
    # Mount kind WALL is this file's idiom for "hangs at a stated height," same as the
    # uppers and APPL-M-HOOD.
    #
    # `install_parts` (2026-08-07): 120V motor branch on its own CKT-DISPOSAL (no longer
    # shares CKT-DISHWASHER) plus a low-voltage loop so the counter switch is a 24V button,
    # not a 120V toggle over a wet sink. Route isn't designed, so only the seven known part
    # numbers are modelled, billed through `[install_parts]`.
    Appliance(uid="ADCW7VPPC1", tag="APPL-M-DISP", type_ref="APPL-DISPOSAL", room="RM-M-LIVING",
              position=pt(ft(28, 7), ft(35)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(14.5)),
              install_parts=("24V Class-2 control transformer, 40 VA",
                             "double-pole contactor, 30 A, 24V coil",
                             "NEMA 1 enclosure, 6x6x4, hinged",
                             "guarded illuminated toggle switch, 24V",
                             "momentary pushbutton, stainless, counter-top",
                             "2-gang low-voltage mounting ring and plate",
                             "18/6 CL2 control cable, 50 ft")),
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
    # north, swapping with N3 (corner filler N4 unchanged). Bases 24" deep (centre
    # x=34'-5 3/8"); range 30" deep, centres 3" further out at 34'-2 3/8" — the number the
    # island aisle is measured from. N4 still claims the corner (flush to 35'-5 3/8").
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
    # Both mudroom closets are now framed rooms, not furniture (RM-M-MECH 2026-07-28,
    # RM-M-MUD-CLOSET 2026-08-02, storeys/main.py). Bench: back to the west wall, centred
    # on WIN-M-MUD at y=31'-4"; south end (29'-10") clears RM-M-MUD-CLOSET's north face
    # (29'-9 7/8") by 1/8".
    Furniture(uid="CMF803AAAA", tag="FURN-M-MUD-BENCH", type_ref="FURN-M-MUD-BENCH",
              room="RM-M-MUDROOM", position=pt(ft(1, 3.125), ft(31, 4)),
              rotation=deg(90)),

    # --- laundry (RM-M-LAUNDRY), 2026-07-31 ------------------------------------------
    # Fold-down drying rack over FX-M-LAUNDRY-SINK, sharing its x centreline and 24" width.
    # 48" mount is a clearance number: the tub tops out at 43" (34" rim + gooseneck), so it
    # leaves 5" over a stowed rack and 16" when down. The rack's RECOMMENDED zone names the
    # sink as its occupant so the tub groups instead of reading as an encroachment.
    # Instance restates the type's Mount because the resolver reads the instance one (same
    # as FX-M-KITCH-SINK's 27", plan/fixtures.py).
    Furniture(uid="XJSV712BWZ", tag="FURN-M-LAUNDRY-RACK", type_ref="FURN-WALL-RACK-24", room="RM-M-LAUNDRY",
              position=pt(m(3.9378), m(5.8566)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(48))),

    # --- curtain rods (2026-08-07) -------------------------------------------
    # One head line for the whole storey: 7'-0", 4" above the tallest main-floor head (6'-8",
    # WT-3048 + exterior doors) so it reads as one line rather than stepping room to room —
    # the facade discipline the elevations enforce. WIN-M-LIV-E1/E2 (5'-6" head) just get
    # longer curtains.
    # y=10" (or x, on side walls) centres the rod 10" off the wall line: 6 1/2" finish face
    # + ~3 1/2" bracket projection. Each rod centres on its opening's RO centre.
    Furniture(uid="EYJ3ZHXFSF", tag="FURN-M-LIV-ROD-S1", type_ref="FT-CURTAIN-ROD-48", room="RM-M-LIVING",
              position=pt(ft(32, 8), ft(0, 10)), rotation=deg(180),
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
    Furniture(uid="RECH3F3R45", tag="FURN-M-LIV-ROD-S2", type_ref="FT-CURTAIN-ROD-48", room="RM-M-LIVING",
              position=pt(ft(27, 4), ft(0, 10)), rotation=deg(180),
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
    # The french pair takes the 84": a 60" RO with 12" of stackback each side, so the
    # leaves clear the glass and the doors still swing.
    Furniture(uid="WJTG6V6T09", tag="FURN-M-LIV-ROD-BALC", type_ref="FT-CURTAIN-ROD-84", room="RM-M-LIVING",
              position=pt(ft(21, 10), ft(0, 10)), rotation=deg(180),
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
    Furniture(uid="2M12W07AGB", tag="FURN-M-LIV-ROD-E1", type_ref="FT-CURTAIN-ROD-48", room="RM-M-LIVING",
              position=pt(ft(35, 2), ft(4)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
    Furniture(uid="94TRP24ZX6", tag="FURN-M-LIV-ROD-E2", type_ref="FT-CURTAIN-ROD-48", room="RM-M-LIVING",
              position=pt(ft(35, 2), ft(12)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
    # "Master bedroom" is read as RM-M-BED, the main-storey bedroom — not the second-storey
    # suite. Flag if that was the wrong room: the four rods move, nothing else does.
    Furniture(uid="BYYY8GG7E6", tag="FURN-M-BED-ROD-W1", type_ref="FT-CURTAIN-ROD-48", room="RM-M-BED",
              position=pt(ft(0, 10), ft(5, 4)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
    Furniture(uid="R4A47142RN", tag="FURN-M-BED-ROD-W2", type_ref="FT-CURTAIN-ROD-48", room="RM-M-BED",
              position=pt(ft(0, 10), ft(10, 8)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
    Furniture(uid="320A53KSR4", tag="FURN-M-BED-ROD-S1", type_ref="FT-CURTAIN-ROD-48", room="RM-M-BED",
              position=pt(ft(4), ft(0, 10)), rotation=deg(180),
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
    Furniture(uid="9222FS9Q20", tag="FURN-M-BED-ROD-S2", type_ref="FT-CURTAIN-ROD-48", room="RM-M-BED",
              position=pt(ft(9, 4), ft(0, 10)), rotation=deg(180),
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),

    # --- plumbing access panels (2026-08-07) ---------------------------------
    # FX-M-BATH1-WC is the house's one wall-hung WC: bowl bolts to a steel carrier in
    # W-M-BAE's stud bay, waste drops at SP-M-WC1 (6'-0", 22'-7"). A 14x29 panel in BATH1's
    # face of that wall (3 3/8" off centreline, base 2'-0", spanning 2'-0"..4'-5") is the
    # only access to the carrier. Centred at 23'-0" rather than on the 22'-7" flange: on the
    # flange a 14"-wide panel would push 2 5/8" through BATH1's south face (22'-2 3/4") into
    # the hall (`test_bath1_fixtures_sit_inside_the_room_and_clear_of_each_other`); pushed
    # 5" north it clears by 2 3/8" while the opening (22'-5"..23'-7") still contains the
    # flange.
    #
    # NOTE unfixed: FX-M-BATH1-WC's authored position (2'-2", 23'-2", rotation 180) stands
    # its bowl ~3'-10" west of the carrier this panel serves; sleeve/drain/wall_ref all
    # agree on W-M-BAE, only the bowl doesn't. Panel follows the carrier, not the bowl.
    Furniture(uid="RSDC92XMBB", tag="FURN-M-BATH1-AP", type_ref="FT-ACCESS-PANEL-1429", room="RM-M-BATH1",
              position=pt(ft(5, 8.625), ft(23)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(2))),
    # FX-M-BATH2-TUB drains at SP-M-BATH2-TUB (7'-4", 19'-4.8"), 8" off W-M-BA2E and
    # behind the tub rather than at either end of it — so the trap and the waste-and-
    # overflow are unreachable from BATH2 without pulling the tub. They are 8" the other
    # side of that wall, in RM-M-LAUNDRY, which is where the panel goes: laundry face of
    # W-M-BA2E at the drain's own y. Base at 6" puts the opening at 6"..1'-8", the band
    # the tee and trap occupy.
    Furniture(uid="TEBYP46W7Y", tag="FURN-M-BATH2-TUB-AP", type_ref="FT-ACCESS-PANEL-1414", room="RM-M-LAUNDRY",
              position=pt(ft(8, 3.375), ft(19, 4.8)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(0, 6))),

    # --- porch curtain rods (2026-08-07) --------------------------------------
    # Two outdoor rods across the sunken garden's front pillar bays (PT-SG-BF1..BF2,
    # BF2..BF3), front row at y=-9'-6" on 10'-0" centres: 9'-6 1/2" clear between 6x6 faces,
    # which is why the type is 114" (half an inch of clearance).
    # Filed on `main` not `second` because Mount.elevation reads off the room floor and only
    # a main-storey room gives the right height: 8'-6" lands 1 1/2" under the balcony beam
    # soffit (8'-7 1/2") it hangs from.
    # `room="RM-M-BED"` follows FX-M-PORCH-HYD: the porch isn't a Room, so this names the
    # nearest interior one and accepts the `integrity.placeable_room_mismatch` advisory —
    # expected, same as the two hydrants.
    Furniture(uid="XH1JW70E8D", tag="FURN-M-PORCH-ROD-W", type_ref="FT-CURTAIN-ROD-OUTDOOR-114", room="RM-M-BED",
              position=pt(ft(13), ft(-9.5)),
              mount=Mount(kind=MountKind.WALL, elevation=ft(8, 6))),
    Furniture(uid="90BCAAC74M", tag="FURN-M-PORCH-ROD-E", type_ref="FT-CURTAIN-ROD-OUTDOOR-114", room="RM-M-BED",
              position=pt(ft(23), ft(-9.5)),
              mount=Mount(kind=MountKind.WALL, elevation=ft(8, 6))),
]
GARAGE_PLACEABLES = [
    # The 60"-wide work surface runs along the west wall directly below the infrared
    # heater lamp. Rotation 90° turns the 30" depth into the wall-to-room dimension.
    Furniture(uid="CGF601AAAA", tag="FURN-G-WORKBENCH", type_ref="FURN-G-WORKBENCH",
              room="RM-GARAGE", position=pt(m(0.596858), m(14.4756)), rotation=deg(90)),
]
# The three east bedrooms are the same 13'-11 3/4" x 8'-10 3/4" clear box: queen, head
# north, 2' side-access zones running the long (14') way. Head-against-east-wall (under the
# window) doesn't fit — the 5'-4" width needs 9'-4" across the 8'-10 3/4" dimension once
# side zones are counted, pushing zones through the wall onto the NEC 210.52 receptacles at
# 16". Turning the beds fixes it; only the 2'-6" foot zone comes up short, into open room.
# x=30' clears the RC1/RC2 outlets; beds sit 9'-7" apart (not the 9'-0" room pitch) so each
# foot zone stops short of the headboard below it — heads float 5"-6" off the north wall.
SECOND_PLACEABLES = [
    # BED1 is 7" further east than the other two (2026-07-31): the head goes tight to the
    # east wall so its foot zone leaves the north wall a 4'-0 wardrobe slot clear of
    # D-S-BED1's sweep. See the wardrobe block below.
    Furniture(uid="819QDDYMZ5", tag="FURN-S-BED1", type_ref="FURN-QUEEN-BED", room="RM-S-BED1",
              position=pt(m(9.88911), m(4.07897)), rotation=deg(270)),
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
    # BED3's pair sits 1'-3" west of where the other two rooms put theirs (2026-07-31). The
    # bed in this room is the one that faces north rather than west, so its west side-access
    # zone runs down x=28'-6" instead of along a wall, and the desk's east end stood 1'-2"
    # inside it. Moving the desk west is free: it stops 4 1/2" clear of FURN-S-BED3-WARD and
    # the pull-out zone still lands in open floor.
    Furniture(uid="DSK703AAAA", tag="FURN-S-DESK3", type_ref="FURN-DESK-48", room="RM-S-BED3",
              position=pt(m(8.05211), m(10.4735)), rotation=deg(0)),
    Furniture(uid="CHR703AAAA", tag="FURN-S-DESK-CHAIR3", type_ref="FURN-DESK-CHAIR", room="RM-S-BED3",
              position=pt(m(8.03685), m(10.0705)), rotation=deg(180)),
    # Compact two-person table in Study 2, against the south wall. Since the 2026-07-30
    # enlargement it sits partly under WIN-S-STUDY1 (centre 28'-0", sill 2'-8" — a
    # couple inches above the table top, which is the pleasant place for a table). Its
    # west edge stays 8" clear of D-S-DECK-E's east jamb; the two chairs sit on the
    # north side, so neither the table nor its usable seating is in the door opening.
    Furniture(uid="TAB701AAAA", tag="FURN-S-STUDY-TABLE", type_ref="FURN-DINING-2-36",
              room="RM-S-STUDY2", position=pt(m(8.10913), m(0.646066))),
    Furniture(uid="CHR704AAAA", tag="FURN-S-STUDY-CHAIR1", type_ref="FURN-DINING-CHAIR",
              room="RM-S-STUDY2", position=pt(m(8.90614), m(0.530999)), rotation=deg(-90)),
    Furniture(uid="CHR705AAAA", tag="FURN-S-STUDY-CHAIR2", type_ref="FURN-DINING-CHAIR",
              room="RM-S-STUDY2", position=pt(m(7.32372), m(0.536064)), rotation=deg(90)),
    # A compact rocking chair occupies the southeast corner, with its back to the south
    # wall and WIN-S-STUDY3 just north of it up the east wall (the window moved from
    # y 4'-0" to 5'-4" in the 2026-07-30 facade pass, off the chair rather than over it). The armchair symbol is the intentional close-enough 2D/3D
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

    # Hanging storage for the three east bedrooms (no built-in closet): one 48" sliding-door
    # wardrobe each, on a north or south partition. Neither the east wall (bed heads against
    # it) nor the west/hall wall (doors own the only long runs) can take one; every candidate
    # 4'-0 x 2'-0 slot was checked against resolved footprints, clearance rings and door
    # swings. BED2 north and BED3 south each had a clean slot. BED1 did not until 2026-07-31:
    # its door swing (y 13'-11"..16'-5") left only 3'-5 3/4" of clear wall, too short for the
    # case. Fixed by moving both the bed (7" east, head now 1/2" off the east wall) and the
    # case (15" east, 2" north) — clears the swing, foot zone and side zones outright.
    #
    # BED1's and BED2's wardrobes sit over ED-S-BED1-RC1 / ED-S-BED2-RC1 (north-wall general
    # receptacles, 16"-18" AFF) — not a code problem, but worth knowing before boxes are set.
    Furniture(uid="CSB704AAAA", tag="FURN-S-BED1-WARD", type_ref="FURN-WARDROBE-48",
              room="RM-S-BED1", position=pt(m(7.74443), m(5.16525)), rotation=deg(0)),
    Furniture(uid="CSB705AAAA", tag="FURN-S-BED2-WARD", type_ref="FURN-WARDROBE-48",
              room="RM-S-BED2", position=pt(m(7.36477), m(7.8429)), rotation=deg(0)),
    Furniture(uid="CSB706AAAA", tag="FURN-S-BED3-WARD", type_ref="FURN-WARDROBE-48",
              room="RM-S-BED3", position=pt(m(7.04819), m(10.1621)), rotation=deg(90)),

    # Linen/towel storage in the hall bath: a 72"x24"x96" pantry-closet carcass
    # (CASE-PANTRY-CLOSET-72) on the south wall, the only run RM-S-BATH1 has free (west has
    # the WC + WIN-S-BATH-W, north the shower pan, east the lav/mirror). Backed to the south
    # wall out of the SW corner, occupying x 0'-0 5/8"..6'-0 5/8", y 26'-4 5/8"..28'-4 5/8":
    # short of D-S-BATH1's opening (x=7'-3") and clear of the WC's REQUIRED zone. The 48" it
    # replaced stopped at x 4'-0 5/8".
    Furniture(uid="CSB707AAAA", tag="FURN-S-BATH1-CLOSET", type_ref="CASE-PANTRY-CLOSET-72",
              room="RM-S-BATH1", position=pt(m(1.09343), m(8.42656)),
              rotation=deg(180)),
    # RM-S-PLANT: a place to sit among the plants, program divides along y — plants on the
    # south glass, seating behind. Plants sit directly under ED-S-PLANT-TUBE1/2 (x=3'-4"/8'-8",
    # 2'-3" below ceiling, on a photoperiod timer) and under WIN-S-PLANT1/2 (same x, the
    # WT-3048-HP/-HP-T pair since the 2026-08-18 glazing retype — same 30" of glass, better
    # U) so each gets daylight plus the tube.
    # Chairs face south from y 4'-0"..7'-0", 1'-3" clear of the plants' north edge. The 1'-3"
    # gap between them used to straddle REG-S-SUP1 (9', 4'), a floor register; that terminal
    # went with the ERV's second-storey supply side on 2026-07-29 and the room's supply is a
    # ceiling grille now (REG-S-HP-PLANT at 6'-8", 3'-4", plan/mep_registers.py), so the gap
    # is only a gap — nothing on the floor needs keeping clear between the chairs. Chair x is
    # set by D-S-PLANT's 2'-6" swing (off y=4'-5 1/2", reaching to ~x=15'-5") — both chairs
    # stop 3'-2" short of it.
    Furniture(uid="PLT701AAAA", tag="FURN-S-PLANT-POT1", type_ref="FURN-PLANT-18",
              room="RM-S-PLANT", position=pt(ft(3, 4), ft(2))),
    Furniture(uid="PLT702AAAA", tag="FURN-S-PLANT-POT2", type_ref="FURN-PLANT-18",
              room="RM-S-PLANT", position=pt(ft(8, 8), ft(2))),
    Furniture(uid="CHR706AAAA", tag="FURN-S-PLANT-CHAIR", type_ref="FURN-ARMCHAIR-35",
              room="RM-S-PLANT", position=pt(m(1.13772), m(1.8808)), rotation=deg(45)),
    Furniture(uid="RCK702AAAA", tag="FURN-S-PLANT-ROCKER", type_ref="FURN-ROCKING-CHAIR-30",
              room="RM-S-PLANT", position=pt(m(4.06734), m(1.93971)), rotation=deg(-45)),
    # Moved y 8'-7 5/8" -> 8'-6 3/8" and retyped to the wet-location spot (2026-08-18): the
    # north partition took the plant room's humid liner, so its face came 1 1/4" south, and
    # a fixture in a room that condenses on purpose has to be wet-location listed rather
    # than the ordinary interior sconce this shared with the study.
    ElectricalDevice(uid="QTS0020AAA", tag="ED-S-PLANT-SPOT", kind=DeviceKind.LIGHT,
                     position=pt(ft(4, 2.125), ft(8, 6.375)), type_ref="ED-T-LT-SCONCE-SPOT-WET",
                     circuit="CKT-LT-UPPER", room="RM-S-PLANT",
                     controlled_by=("ED-S-PLANT-SW-TIMER",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6))),

    # --- plumbing access panel (2026-08-07) ----------------------------------
    # FX-S-SUITEBATH-TUBSH's waste-and-overflow tee is at its north end, 1" off W-S-SN3 (the
    # RM-S-HALL partition), so the panel goes in the hall face of W-S-SN3 (2 3/8" off the
    # 4 3/4" partition's centreline) on the tub's x centre — reachable from the hall.
    # FX-S-BATH1-SH gets none deliberately: its drain end is west, into the plumbing chase
    # (not a room, no standing room), and the only reachable face puts a panel over the tub
    # itself — no better than pulling the apron. Left for the ceiling below.
    # Neither fixture carries a `drain_position`; recheck this placement if one is authored.
    Furniture(uid="NHFPDD49RB", tag="FURN-S-SUITEBATH-AP", type_ref="FT-ACCESS-PANEL-1414", room="RM-S-HALL",
              position=pt(ft(16, 4.5), ft(22, 6.375)), rotation=deg(180),
              mount=Mount(kind=MountKind.WALL, elevation=ft(0, 6))),
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
    # The table set moved 4" west on 2026-07-31. Its 3'-0" chair surround reached 2 1/4" past
    # the desk's west end, which is the one direction the desk cannot give: its own east end
    # is against ED-A-STUDY-SPOT's wall. 4" west costs the set nothing — the room runs on to
    # x=18'-0 5/8" and CHAIR2 still stands 5'-3" clear of the west knee wall.
    Furniture(uid="TAK701AAAA", tag="FURN-A-STUDY-TABLE", type_ref="FURN-DINING-2-36",
              room="RM-A-STUDY", position=pt(m(8.13979), m(0.65023))),
    Furniture(uid="CAK702AAAA", tag="FURN-A-STUDY-CHAIR1", type_ref="FURN-DINING-CHAIR",
              room="RM-A-STUDY", position=pt(m(8.93626), m(0.532453)), rotation=deg(-90)),
    Furniture(uid="CAK703AAAA", tag="FURN-A-STUDY-CHAIR2", type_ref="FURN-DINING-CHAIR",
              room="RM-A-STUDY", position=pt(m(7.35127), m(0.57089)), rotation=deg(90)),
]

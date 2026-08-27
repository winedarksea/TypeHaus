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
# lines: west liner x=9'-1 13/16", east liner x=17'-2 1/2", south liner y=0'-11 1/2", north
# liner y=13'-6 1/8" — an 8'-0 11/16" x 12'-6 5/8" clear box. The south face gained 3 1/2"
# of liner (SAUNA_LINER_ON_BASEMENT_8_GARDEN on W-B-S2) on 2026-08-18, so both benches
# moved north with it; on 2026-08-21 they went back 4" south, because thinning that wall's
# pour from 12" to 8" (it aligns on face("concrete-ext"), so only the inside face moved)
# took the liner face with it — 1'-3 1/2" to 0'-11 1/2". The east liner is W-B-CS, which
# stayed 12", so x did not move. The east bench stops at y=9'-5 1/2" to leave the north end
# for the shower (notes/sauna_shower_basement_detail.md).
BASEMENT_PLACEABLES = [
    # The long two-tier run takes the east wall: it is the only unbroken face in the room —
    # the west wall has D-B-SAUNA, the south wall WIN-B-SAUNA — so the bench lands as one
    # 8'-6" carcass with no scribes around an opening. rotation -90 puts its back (+y local)
    # against that face, giving x 13'-8 1/2"..17'-2 1/2" and
    # y 0'-11 1/2"..9'-5 1/2" — clearing FX-B-SAUNA-SH's pan by 12 11/16" at its north end.
    Furniture(uid="CBF601AAAA", tag="FURN-B-SAUNA-BENCH-E", type_ref="FURN-SAUNA-BENCH-2T-102",
              room="RM-B-SAUNA", position=pt(ft(15, 5.5), ft(5, 2.5)), rotation=deg(-90)),
    # The foot bench returns along the south wall, butted into the two-tier run's west face
    # at 13'-8 1/2" with an 11/16" scribe left at the west liner. rotation 180 puts its back
    # to the south. Its top is 18", well clear of WIN-B-SAUNA's 3'-8" sill above it.
    Furniture(uid="CBF602AAAA", tag="FURN-B-SAUNA-BENCH-S", type_ref="FURN-SAUNA-BENCH-54",
              room="RM-B-SAUNA", position=pt(ft(11, 5.5), ft(1, 9.5)), rotation=deg(180)),

    # RM-B-WORKSHOP's two benches (2026-08-22). The room is L-shaped: a west bay running the
    # full 18' of the storey, plus a north strip east of the sauna block. **Both benches take
    # the west wall, not one per leg** — the north strip is 4'-2" deep and a 30" bench there
    # would leave a 20" aisle, which is not an aisle.
    #
    # The west wall is the only unbroken face the room has: 18'-0" of bare concrete
    # (CATLIN_BASEMENT_8, interior face at x=0'-8" — the pour's inboard face, the foam is all
    # outboard). `rotation=deg(90)` turns FURN-G-WORKBENCH's 30" depth into the wall-to-room
    # dimension, exactly as the garage instance does, so the centre sits 15" off that face at
    # x=1'-11". Centres at y=6'-0" (under ED-B-WORKSHOP-PANEL1, the "over a bench" panel that
    # has been naming a bench that did not exist since it was authored) and y=11'-0", giving
    # one contiguous 10'-0" run from y=3'-6" to y=13'-6" — clear of the sauna's north face
    # beyond it.
    Furniture(uid="6FJ01Z04WX", tag="FURN-B-WORKSHOP-BENCH-N", type_ref="FURN-G-WORKBENCH",
              room="RM-B-WORKSHOP", position=pt(ft(1, 11), ft(11)), rotation=deg(90)),
    Furniture(uid="8FXXT06T4E", tag="FURN-B-WORKSHOP-BENCH-S", type_ref="FURN-G-WORKBENCH",
              room="RM-B-WORKSHOP", position=pt(ft(1, 11), ft(6)), rotation=deg(90)),

    # --- RM-B-PLAY-N, the media room (2026-08-22) ---------------------------------------
    #
    # A windowless 324 sf box whose four resolved finish faces are south (W-B-CE) y=18'-3
    # 3/8", west (W-B-CN/CN2) x=18'-6", north (W-B-N1) y=35'-4", east (W-B-E2) x=35'-0" —
    # 16'-6" x 17'-0 5/8" clear. Everything below is dimensioned off those faces, not off the
    # room's `clear_face` ring, which for a concrete wall lands on the wall AXIS.
    #
    # The screen: 98" (85.3" wide), hung on the north concrete wall, centred at x=26'-9",
    # which is the room's own centreline and where the owner asked for the ethernet drop
    # (ED-B-PLAY-N-DATA1). `mount=WALL` with the panel's bottom at 2'-6" puts its top at
    # 6'-8" under an 8'-3 1/2" ceiling. **An 8" concrete wall takes anchors, not blocking** —
    # there is no stud bay behind this and the mount is a mechanical fixing into the pour.
    Furniture(uid="X99HBG99WJ", tag="FURN-B-PLAY-TV", type_ref="FURN-TV-98", room="RM-B-PLAY-N",
              position=pt(ft(26, 9), ft(34, 7.75)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(30))),
    # The U, opening north at the screen. 11'-0" of back run leaves 2'-9" either side of a
    # 16'-6" box; y 21'-6" to 29'-6" puts the back run 11'-13' off the panel — right for a
    # 98" screen — and leaves 2'-2 3/4" of walk between the bookcases and the sectional's
    # south face. FT-SECTIONAL-U-MEDIA is house-local and says why in plan/furniture_types.py.
    #
    # ** ROTATION 180 IS WHAT MAKES IT FACE THE SCREEN, and it was missing until 2026-08-24. **
    # It was authored unrotated against a footprint_shape that opened north on its own. But
    # rotation 0 puts a seat's back at +y — the note at the top of this file, and the
    # convention every glyph in `model/placeable_symbols/_families.py` draws to — so the
    # body in the viewer sat with its back to the panel while the collision outline faced it.
    # The type's ring is re-authored to the convention and the turn is declared here, which
    # is also what makes this the ONE line to edit if the screen ever moves wall.
    Furniture(uid="1KZNJX16H6", tag="FURN-B-PLAY-SECTIONAL", type_ref="FT-SECTIONAL-U-MEDIA",
              room="RM-B-PLAY-N", position=pt(ft(26, 9), ft(25, 6)), rotation=deg(180)),
    # Bookcases either side of D-B-PLAY on the south wall, backs on its 18'-3 3/8" face.
    # The door's framing runs x 23'-10" to 29'-2" and its leaf sweeps x 24'-0"..26'-6",
    # y 18'-0"..20'-6", so both pairs stand clear of the arc: west from the 18'-6" corner to
    # 23'-10", east from 29'-8" to the 35'-0" corner.
    #
    # ** 7'-6" SINCE 2026-08-24, NOT THE LIBRARY'S 6'-0" ** (owner: take the theatre's
    # shelving nearer the ceiling). FT-BOOKCASE-32-90 is house-local and argues the height in
    # plan/furniture_types.py; the short version is that the room's measured clear is 8'-0"
    # under SL-M-DECK, so 7'-6" leaves a 6" reveal — scribe room under a poured deck that is
    # never dead flat, and enough that a 90" x 12" carcass can still be stood up off the
    # floor. Anti-tip into W-B-CE's studs at every case; it is a stud wall, unlike the pour
    # the screen hangs on.
    #
    # ** THE 8'-3 1/2" CEILING QUOTED ABOVE FOR THE SCREEN IS STALE ** — it was the basement
    # number before the 2026-08-23 seat rework. `code.R305_ceiling_height` reads 8'-0" here
    # today. It does not move the panel (top of glass at 6'-8" clears either), but do not
    # re-derive anything else from it.
    #
    # The footprint is unchanged at 2'-8" x 1'-0", so every dimension above still holds: the
    # backs stay on the 18'-3 3/8" face and both pairs stay clear of D-B-PLAY's swing arc.
    # A real Billy is 31 1/2" x 11" x 79 1/2"; this is not that piece and does not try to be.
    Furniture(uid="CS3QSXP6JR", tag="FURN-B-PLAY-BOOK-W1", type_ref="FT-BOOKCASE-32-90", room="RM-B-PLAY-N",
              position=pt(ft(19, 10), ft(18, 9.375)), rotation=deg(180)),
    Furniture(uid="F9X5X4J5N5", tag="FURN-B-PLAY-BOOK-W2", type_ref="FT-BOOKCASE-32-90", room="RM-B-PLAY-N",
              position=pt(ft(22, 6), ft(18, 9.375)), rotation=deg(180)),
    Furniture(uid="0NPX3QZ0GA", tag="FURN-B-PLAY-BOOK-E1", type_ref="FT-BOOKCASE-32-90", room="RM-B-PLAY-N",
              position=pt(ft(31), ft(18, 9.375)), rotation=deg(180)),
    Furniture(uid="2XX4D4BYHR", tag="FURN-B-PLAY-BOOK-E2", type_ref="FT-BOOKCASE-32-90", room="RM-B-PLAY-N",
              position=pt(ft(33, 8), ft(18, 9.375)), rotation=deg(180)),
]
MAIN_PLACEABLES = [
    Furniture(uid="XV5MXV43QJ", tag="FURN-M-SOFA", type_ref="FURN-SOFA-84", room="RM-M-LIVING",
              position=pt(m(7.87848), m(2.69813))),
    Furniture(uid="EKN22YPA9J", tag="FURN-M-MEDIA", type_ref="FURN-MEDIA-60", room="RM-M-LIVING",
              position=pt(ft(26, 11), ft(1, 10)), rotation=deg(180)),
    # East living-room storage: EIGHT 23 5/8" BESTA units fill the 15'-10 3/8" clear span
    # from the fireplace's north edge at y=4'-10" to FURN-M-KIT-PANTRY-S2's south face at
    # y=21'-2 3/8". Their backs sit directly on the east wall's interior face at x=35'-5 3/8".
    # Rotation -90 puts each unit's back against the east wall and opens it toward the room.
    #
    # ** IT WAS NINE UNTIL 2026-08-24, AND THE NINTH WAS OVERLAPPING. ** The run was laid
    # out against a 48" pantry closet whose south edge was y=22'-8". The kitchen rework
    # replaced that with the east tall bank, which runs 1'-5 5/8" further south to
    # y=21'-2 3/8" — so FURN-M-LIVING-BESTA-09 (y 20'-7"..22'-6 5/8") ended up 1.86 SF
    # inside FURN-M-KIT-PANTRY-S2's carcass, two solid bodies in the same air. Deleting it is
    # the owner's call and the right one: the alternative is sliding all nine south into the
    # fireplace.
    #
    # ** NOTHING IN `haus check` CAUGHT THIS, and that is worth knowing. ** The advisory
    # clearance rules grade a declared CLEARANCE ZONE against a body; two bodies simply
    # occupying the same volume is not something any current check walks. The 1'-4 5/8"
    # residual between BESTA-08's north end and the tall bank is now the run's only
    # non-module tolerance, where it used to be 1 3/8" — it is slack, not a gap to fill,
    # because a tenth unit does not fit in it either.
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
    # Dining at 17'-4" (moved 4' south once the island moved down and the 48" pantry took
    # the east wall to 22'-8" — that pantry is gone, see the BESTA run above). Table
    # x 23'-0 1/2"..31'-0 1/2", y 15'-4 1/2"..18'-10 1/2"; the 36" chair-use margin reaches
    # y=12'-4 1/2" and y=21'-10 1/2", clear of the sofa and with a wide circulation band to
    # the peninsula.
    #
    # Only the six side chairs are drawn on this 8-place table — end chairs would block the
    # hall-to-east-windows walk, so those two places stay unset, brought in when needed.
    #
    # ** THE ZONE LOST ITS CORNERS (owner, 2026-08-24), which is why the type is house-local. **
    # FURN-M-KIT-PANTRY-S2's carcass (x from 33'-5 3/8", y from 21'-2 3/8") stood 7 1/8" x
    # 8 1/8" inside the NE corner of the library type's chair-use rectangle — 0.4 sf, and
    # the only recommended-clearance finding in the kitchen. It is a corner lap and nothing
    # else: the tall bank is 2'-4 7/8" east of the table's end and 2'-3 7/8" north of its
    # side, so it is outside BOTH bands at the full 36" and clear of every chair.
    #
    # The owner's call was to shrink the zone, and this is the shrink that costs nothing
    # real: FT-DINING-8-OPEN-CORNERS keeps 36" on all four sides and drops only the four
    # corner squares, where no chair goes. Retyping rather than reducing the reach is
    # deliberate — cutting 36" to 27" would have cleared the same 0.4 sf while quietly
    # unpolicing the two long sides, where the six chairs that actually exist stand.
    Furniture(uid="QWCMN48QST", tag="FURN-M-DINING", type_ref="FT-DINING-8-OPEN-CORNERS",
              room="RM-M-LIVING", position=pt(m(8.24278), m(5.2201))),
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

    # West run — cold storage and pantry against the centre bearing wall, opening east.
    # North to south: RM-M-PANTRY's south partition, freezer, refrigerator, closet pantry.
    # Cabinets 24" deep (centre x=19'-3 3/8"); cold boxes 27" deep (centre 19'-4 7/8").
    #
    # ** THE RUN'S NORTH END IS A WALL NOW, NOT A CABINET (2026-08-24). **
    # FURN-M-KIT-TALL-N (12") and -TALL-S (18") stood at y 32'-11 3/8"..35'-5 3/8" and are
    # deleted with this commit: that 2'-6" is inside RM-M-PANTRY, whose south partition
    # W-M-PAN-S puts its face at y=32'-6 5/8". Scattered tall storage became one framed
    # room — which is the whole point of the rework, and is also why the shared catalog's
    # CASE-TALL-PANTRY-12/-18 now have no instance in this house.
    #
    # The pair shifts SOUTH to meet that face and FURN-M-KIT-COLDSTORE-FILL is deleted with
    # them: the partition takes 4 3/4" off the north end, the filler gives 6 1/4" back, so
    # PANTRYC nets 1 1/2" north — the whole budget, and a bigger move means a shallower
    # pantry. The bay is 65 3/4" now, EXACTLY two appliance widths, so the run divides with
    # no filler at either end and the two over-cabinets retype CASE-OVER-36 ->
    # FT-KIT-OVER-COLD-3278 to match (two 36" boxes no longer fit).
    #
    # Fridge/freezer door zones: fronts at x=20'-6 3/8", so a 3'-0" zone reaches 23'-6 3/8"
    # — clear of W-M-PAN-E by 7 1/4" and south of the north counter run. (The old comment's
    # "to x=24'-1 3/8"" was stale from the 34"-deep allowance era.) ** DESIGN NOTE, and no
    # check catches it: ** that zone now stands in front of D-M-PANTRY. An open fridge door
    # blocks the pantry. It is the price of putting both on one aisle, and it is the price
    # the owner is paying knowingly.
    # Retyped and re-laid-out 2026-08-24, allowance -> product: the Frigidaire Professional
    # single-door pair (plan/appliance_types.py). The bay is unchanged — still 26'-11 3/8"
    # to 32'-11 3/8", still 72" — but the appliances no longer divide it in half, because a
    # column is 32 7/8" and not 36". The 6 1/4" remainder goes to FURN-M-KIT-COLDSTORE-FILL
    # at the SOUTH end, which is what lets both these boxes shift south as a contiguous
    # pair and still keep their own receptacles behind them (ED-M-LIVING-KFZ1 at y=29'-10"
    # lands behind the freezer, KRF1 at y=31'-5 3/8" behind the refrigerator). Splitting the
    # remainder into two 3 1/8" scribes would have put KFZ1 on the joint between them.
    #
    # x moved OUT, from 19'-8 3/8" to 19'-4 7/8", and the run got roomier for it: these
    # columns are 27" deep against the allowance's 34", and both are back-aligned to the
    # centre bearing wall's face at x=18'-3 3/8" the way the whole run is. They stand 3"
    # proud of the 24" tall cabinets beside them instead of 10". Frigidaire does not publish
    # the handle projection, so the *real* proudness is 3" plus a handle nobody has measured
    # — a tape on a floor sample before the cabinet order, not a number to invent here.
    Appliance(uid="A1Y5Q0RDXV", tag="APPL-M-FRIDGE", type_ref="APPL-FRIG-PRO-ALLFRIDGE", room="RM-M-LIVING",
              position=pt(ft(19, 4.875), ft(31, 6.1875)), rotation=deg(90),
              # TWINSPAIRKIT rides on the refrigerator rather than the freezer arbitrarily —
              # it is one kit for the pair, and billing it twice would be wrong. It is what
              # makes two cabinets legal to stand against each other: the shared side walls
              # would otherwise sweat.
              install_parts=("Frigidaire TWINSPAIRKIT twin pairing kit (anti-condensation heater, power supply, cord, clips)",)),
    Appliance(uid="ZH6G4SNPWT", tag="APPL-M-FREEZER", type_ref="APPL-FRIG-PRO-ALLFREEZER", room="RM-M-LIVING",
              position=pt(ft(19, 4.875), ft(28, 9.3125)), rotation=deg(90)),
    # PANTRYC closes straight up against the freezer now that the filler is gone. It still
    # stands 9 1/8" past W-M-C5's south end at y=25'-10" — pre-existing (10 5/8" before this
    # commit), improved by the 1 1/2", and it draws no finding. Do not "fix" it.
    Furniture(uid="XTD1N9A693", tag="FURN-M-KIT-PANTRYC", type_ref="CASE-PANTRY-CLOSET-24", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(26, 4.875)), rotation=deg(90)),
    # ** THE TALL UNITS GO TO THE CEILING TOO (owner, 2026-08-24). ** This was left as an
    # open question when the stacker course went in over the uppers — stack the 96" talls to
    # match, or accept a 12" step across the kitchen. The answer is stack them. The stacker
    # is a 24"-DEEP box: a tall cabinet's carcass is base depth, so the WS (13") family
    # would float a shallow box over it and put the step back in a different place.
    #
    # ** BUT NOT THE FULL 24" WIDE (owner, 2026-08-24). ** PANTRYC oversails the south end
    # of W-M-C5 at y=25'-10" — accepted at floor level (see its note above), because a
    # cabinet end standing in a 4'-wide passage is a jamb you walk past. Carrying that same
    # oversail up as a 24"-deep box floating at 8'-0" is a different object: it is a soffit
    # over the passage, and it reads as one from the living room. So the stacker is sized to
    # stop where the WALL stops, not where the cabinet does.
    #
    # It was CASE-TS15-12 when the oversail was 9 1/8". W-M-PAN-S then moved 4" north (see
    # storeys/main.py) and the whole run went with it, so the oversail is 5 1/8" and the
    # stacker steps back up to the 18" box: south end on y=25'-10 7/8", 7/8" clear of the
    # wall's end instead of 1/8" past it. Above 8'-0" the passage is clear to the ceiling.
    #
    # The 6 1/8" of PANTRYC's top left uncovered is a finished cabinet top, not a hole: it
    # is the same detail as the top of any 96" tall that stops short of a ceiling.
    Furniture(uid="ZMBSYYRCX5", tag="FURN-M-KIT-PANTRYC-ST", type_ref="CASE-TS18-12", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(26, 7.875)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),
    # Over the two cold boxes: 24" deep like the talls, so all four fronts land on x=20'-3 3/8"
    # and the appliances stand 3" proud — clearing the fridge/freezer door swing. Retyped
    # CASE-OVER-36 -> FT-KIT-OVER-COLD-3278 (2026-08-24): the bay is 65 3/4" and two 36"
    # boxes need 72". 32 7/8" is the appliance width carried up, so each box's ends land on
    # its own column's sides.
    #
    # ** THE MOUNT WENT 72" -> 75" (2026-08-24) BECAUSE 72" DID NOT FIT. ** The Frigidaire
    # columns top out at 72 1/2" at the hinge and want 1" of air above; a cabinet bottom at
    # 72" stood BELOW the hinge. The box shortened 24" -> 21" to match, so the top is still
    # 96" and the stacker course is untouched. Both numbers are the manufacturer's own and
    # were already quoted in plan/appliance_types.py — see FT-KIT-OVER-COLD-3278's note in
    # plan/furniture_types.py for the whole arithmetic. Do not lower these back to 72".
    Furniture(uid="8T3D1P2QRV", tag="FURN-M-KIT-OVER-FRIDGE", type_ref="FT-KIT-OVER-COLD-3278", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(31, 6.1875)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(75))),
    Furniture(uid="Y4KJ6WB0ZC", tag="FURN-M-KIT-OVER-FREEZER", type_ref="FT-KIT-OVER-COLD-3278", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(28, 9.3125)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(75))),
    # The stacker course over the cold run, 96" -> 108". 24" DEEP, not the 13" of the
    # counter stackers: a stacker inherits the depth of the box it sits on, and a shallow
    # box floating over a 24" over-appliance cabinet is the step this course exists to
    # close. See CASE-TS3278-12's note in library/placeables/casework.py.
    Furniture(uid="6SVFKKA66M", tag="FURN-M-KIT-OVER-FRIDGE-ST", type_ref="CASE-TS3278-12", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(31, 6.1875)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),
    Furniture(uid="WE0EY3QAXB", tag="FURN-M-KIT-OVER-FREEZER-ST", type_ref="CASE-TS3278-12", room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(28, 9.3125)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),

    # North run — the sink wall. Re-composed 2026-08-26 to centre the sink under
    # WIN-M-KITCH: the run is exactly full (5/8" scribe + B15 + DW + SINK-36 + B30 =
    # 105 5/8", pantry wall to corner) with no slack to slide the sink, so the window's
    # three-storey column moved to the sink instead — see storeys/main.py's OPENINGS.
    # B30 and B15 swapped ends and the dishwasher moved to the sink's west side. Bases 24"
    # deep, centre y=34'-5 3/8". FURN-M-KIT-PANTRY-E (a 48" CASE-PANTRY-CLOSET-48 at x
    # 20'-7"..24'-7") stood here and is deleted 2026-08-24: it is inside RM-M-PANTRY now.
    # W-M-PAN-E's east face at 24'-6 3/8" lands 5/8" off FURN-M-KIT-E1's carcass below,
    # which is a scribe, so the north counter run reads as starting at the pantry wall
    # exactly as it used to start at the pantry cabinet.
    Furniture(uid="49B0RDP4NW", tag="FURN-M-KIT-E1", type_ref="CASE-B15", room="RM-M-LIVING",
              position=pt(ft(25, 2.5), ft(34, 5.375))),
    # The 36" sink base is dead-centred under WIN-M-KITCH now that the window's column
    # moved to it (see storeys/main.py's OPENINGS) — no more off-centre split.
    Furniture(uid="F8A30SK31X", tag="FURN-M-KIT-SINKBASE", type_ref="CASE-SINK-BASE-36", room="RM-M-LIVING",
              position=pt(ft(29, 4), ft(34, 5.375))),
    # Disposer hangs off FX-M-KITCH-SINK's drain fitting, at the sink's `drain_position`
    # (29'-4", 35'-0") — the flange, where the trap and SP-M-KITCH already are — not the
    # bowl centre. 14 1/2" mount = base of body (27" bowl bottom minus 12 1/2" cylinder).
    # Mount kind WALL is this file's idiom for "hangs at a stated height," same as the
    # uppers and APPL-M-HOOD.
    #
    # `install_parts` (2026-08-07): 120V motor branch on its own CKT-DISPOSAL (no longer
    # shares CKT-DISHWASHER) plus a low-voltage loop so the counter switch is a 24V button,
    # not a 120V toggle over a wet sink. Route isn't designed, so only the seven known part
    # numbers are modelled, billed through `[install_parts]`.
    Appliance(uid="ADCW7VPPC1", tag="APPL-M-DISP", type_ref="APPL-DISPOSAL", room="RM-M-LIVING",
              position=pt(ft(29, 4), ft(35)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(14.5)),
              install_parts=("24V Class-2 control transformer, 40 VA",
                             "double-pole contactor, 30 A, 24V coil",
                             "NEMA 1 enclosure, 6x6x4, hinged",
                             "guarded illuminated toggle switch, 24V",
                             "momentary pushbutton, stainless, counter-top",
                             "2-gang low-voltage mounting ring and plate",
                             "18/6 CL2 control cable, 50 ft")),
    # Retyped 2026-08-24, allowance -> product: LG LDTS5552S (plan/appliance_types.py).
    # 23 3/4"x24 5/8" against the allowance's 24"x24" — the nominal-vs-actual quarter inch
    # a 24" cabinet opening already carries, so the run's arithmetic is unaffected.
    Appliance(uid="XPA5ZCQM5Q", tag="APPL-M-DW", type_ref="APPL-LG-DISHWASHER", room="RM-M-LIVING",
              position=pt(ft(26, 10), ft(34, 5.375))),
    Furniture(uid="3QTQ2NFWYD", tag="FURN-M-KIT-E2", type_ref="CASE-B30", room="RM-M-LIVING",
              position=pt(ft(32, 1), ft(34, 5.375))),

    # North wall uppers — re-ordered with the base run (2026-08-26). Nothing over the sink
    # (the window's there), the pantry (already full height) or the corner filler.
    Furniture(uid="AQTQJBTXRR", tag="FURN-M-KIT-WE1", type_ref="CASE-W15", room="RM-M-LIVING",
              position=pt(ft(25, 2.5), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    Furniture(uid="VKP909PNS6", tag="FURN-M-KIT-WE2", type_ref="CASE-W24", room="RM-M-LIVING",
              position=pt(ft(26, 10), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    # ** THE STACKER COURSE (2026-08-24). ** The uppers stopped at 96" under a 108" ceiling
    # and the owner asked for them to reach it. 12" is a STOCK wall-cabinet height (the
    # "wall bridge" box), so 96 + 12 = 108 lands exactly with no custom carcass — which is
    # why the answer is a second course rather than 54"-tall boxes. One per surviving
    # upper, same width, same 13" depth, same face.
    #
    # WN1 and WE3 get none: both hang at 66" and are 42" tall, so they already land on 108".
    #
    # ** ANSWERED (owner, 2026-08-24): the 96" TALL units are stacked to match. ** The
    # question was whether FURN-M-KIT-PANTRYC and the two east pantry closets should stop
    # 12" short of uppers that do not. They do not: each carries a CASE-TS24-12, so every
    # cabinet in this kitchen now lands on 108" and there is no step anywhere in the room.
    Furniture(uid="H3N6SVBPQY", tag="FURN-M-KIT-WE1-ST", type_ref="CASE-WS15-12", room="RM-M-LIVING",
              position=pt(ft(25, 2.5), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),
    Furniture(uid="PVRA77ZM2N", tag="FURN-M-KIT-WE2-ST", type_ref="CASE-WS24-12", room="RM-M-LIVING",
              position=pt(ft(26, 10), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),
    # ** THE COURSE RUNS ACROSS THE SINK WINDOW (owner, 2026-08-24). ** WE1-ST and WE2-ST
    # were laid one-per-upper, which left the 36" between them empty — because the uppers
    # below stop either side of WIN-M-KITCH. At 96" that reason is gone: the window's head
    # is 78" (sill 42" + WT-2736's 36"), so the stacker course clears it by 18" and there is
    # nothing up there to stop for. Filling it turns three floating boxes into one band at
    # the ceiling, which is what the course was for.
    #
    # 36" exactly: x 27'-10" to 30'-10", which is FURN-M-KIT-SINKBASE's own width carried
    # up, so the band's joints land on the base joints below. One stock bridge box, no
    # filler.
    Furniture(uid="RSP5MTPXPM", tag="FURN-M-KIT-WE4-ST", type_ref="CASE-WS36-12", room="RM-M-LIVING",
              position=pt(ft(29, 4), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),
    # ** EAST FLANK, OVER FURN-M-KIT-E2 (re-ordered 2026-08-26). ** CASE-W30 (E2's own
    # width carried up) takes x 30'-10"..33'-4", so the joint lands on the base joint below
    # and stops 1" clear of WIN-M-KITCH-N's RO at 33'-5", the same jamb condition WE3
    # already has on its far side.
    #
    # Hung at 54" WITH a stacker, not at 66" flush with WE3: the owner's call, and it keeps
    # the whole run's bottom on one line at 54" and buys a full extra shelf. WE3 stays the
    # single box stepped up to 66", which now reads as the window's bridge rather than as
    # one cabinet at an odd height. Tags are chronological here, not west-to-east — WE4-ST
    # is the window stacker at 29'-4".
    Furniture(uid="2V68CXXCNR", tag="FURN-M-KIT-WE5", type_ref="CASE-W30", room="RM-M-LIVING",
              position=pt(ft(32, 1), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    Furniture(uid="T0QD4C4KHD", tag="FURN-M-KIT-WE5-ST", type_ref="CASE-WS30-12",
              room="RM-M-LIVING", position=pt(ft(32, 1), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),
    # ** A CABINET OVER THE EXISTING NORTH WINDOW. ** The owner asked for cabinets above
    # BOTH small windows and WIN-M-KITCH-N has never had one. CASE-W12 spans the 12 3/8"
    # between FURN-M-KIT-E2's east end (33'-4") and FURN-M-KIT-WN1's 13"-deep return
    # (34'-4 3/8"), hung at 66" to clear the window head, 42" tall, top at 108".
    #
    # It also retires a live clash: WN1 at its OLD 54" mount lapped WIN-M-KITCH-N's opening
    # by 2 5/8" of plan width between 54" and the 66" head. Rehanging WN1 for the new EAST
    # window (below) is what fixes the NORTH one too — the two were never related until
    # this commit made them the same move.
    Furniture(uid="CC9EXX28N7", tag="FURN-M-KIT-WE3", type_ref="CASE-W12", room="RM-M-LIVING",
              position=pt(ft(33, 10.1875), ft(34, 10.875)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(66))),

    # East run — the cooking wall. Range and hood flipped 2026-07-30 (owner's call) further
    # north, swapping with N3 (corner filler N4 unchanged). Bases 24" deep (centre
    # x=34'-5 3/8"); range 30" deep, centres 3" further out at 34'-2 3/8". N4 still claims
    # the corner (flush to 35'-5 3/8").
    #
    # ** REWRITTEN 2026-08-24 WITH THE PENINSULA. ** South of the range this run is no
    # longer counter at all. FURN-M-KIT-N1 (36") and -N2 (24") occupied y 22'-5 3/8"..
    # 27'-5 3/8" and are deleted: the peninsula's east end lands on this wall at
    # y 25'-2 3/8"..28'-5 3/8", and south of it the owner asked for the tall "pull-out"
    # bank, which is FURN-M-KIT-PANTRY-S1/S2 below. N3 shortens 36" -> 24" and slides north
    # to fill exactly what is left between the peninsula and the range, with no filler.
    Furniture(uid="KA0ETVK8F8", tag="FURN-M-KIT-N4", type_ref="CASE-B30", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(34, 2.375)), rotation=deg(-90)),
    # Retyped 2026-08-24, allowance -> product: LG LSIL6336FE induction slide-in
    # (plan/appliance_types.py). `APPL-ELECTRIC-RANGE` covered coil, radiant and induction
    # alike; this house has no gas piped to it and a recirculating hood over the cooktop
    # precisely because the cooking is induction, so the allowance was wider than the
    # decision. 29 7/8"x29 5/16" against the allowance's 30"x30" — an eighth and change,
    # which is why the position and the 3"-proud offset above are unchanged.
    Appliance(uid="417H1EH5C3", tag="APPL-M-RANGE", type_ref="APPL-LG-INDUCTION-RANGE", room="RM-M-LIVING",
              position=pt(ft(34, 2.375), ft(31, 8.375)), rotation=deg(-90)),
    Furniture(uid="7YPYR8K5FS", tag="FURN-M-KIT-N3", type_ref="CASE-B24", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(29, 5.375)), rotation=deg(-90)),

    # The tall bank, y 21'-2 3/8"..25'-2 3/8" — 48" of it where N1/N2 gave 36" of base, and
    # its north face is coplanar with the peninsula's south face. The whole run sits 3"
    # further south than the plan for this work first had it, because the peninsula's
    # overhang went from 12" to NKBA's 15"; that same 3" is what keeps N3 a full 24" box.
    # South end: WIN-M-EAST-MID's RO stops at y=19'-11", so 15 3/8" of wall is left below
    # the sill — jamb return, casing and room to spare.
    #
    # ** "PULL-OUT" IS BOUGHT WITH HARDWARE, NOT WITH THE BOX, AND AT 24" IT IS A
    # SWING-OUT. ** A 24"-wide TALL PULL-OUT pantry is not a stock item: Rev-A-Shelf's tall
    # pullout ladder tops out at the 5758-20 (20 11/16" wide), because what limits it is the
    # cantilevered moment on a 74" rack, not the slide. At 24" the stock article is a
    # SWING-OUT, and this carcass is sized to it.
    #
    # ** RE-CHECKED AGAINST THE PUBLISHED SPEC, 2026-08-24 (owner). ** Rev-A-Shelf 5374-24FL:
    # unit 22 1/16"W x 18 1/2"D x 74 1/16"H, MIN CABINET OPENING 22 1/4"W x 18 3/4"D x 75"H,
    # five solid-bottom adjustable shelves on 250 lb full-extension soft-close slides, plus
    # two DOOR MOUNT BRACKETS. The brackets are the hardware that ties the rack to the door
    # leaf so it swings out with it — they are not door-mounted racks, and an earlier note
    # here said racks and overstated the storage.
    #
    # Three numbers decide whether this box is right, and all three pass:
    #   * WIDTH is the tight one. The insert needs a 22 1/4" clear opening. A FRAMELESS 24"
    #     box gives 24 - 2 x 3/4" = 22 1/2" — 1/4" to spare. A face-framed 24" cabinet gives
    #     about 21" and this insert WOULD NOT FIT IN IT. The library's casework is frameless
    #     (see its REFERENCE), which is why "24 inch" is a sufficient answer here and would
    #     not be in another catalog.
    #   * DEPTH needs 18 3/4"; a 24" frameless box gives about 22 1/2" clear. ** DELIBERATELY
    #     NOT DEEPER: ** the insert is 18 1/2" deep, so every inch of cabinet past ~20" is
    #     dead space BEHIND a rack that cannot reach it, bought by pushing the carcass
    #     further into the aisle. 24" is the depth the product is sold against.
    #   * HEIGHT needs 75"; a 96" carcass has ~90" of interior. The rack is 74 1/16" tall, so
    #     it occupies the bottom 75" and leaves roughly 15" above it — a fixed top shelf,
    #     reached from the step the pantry shelving already is.
    #
    # So the carcass type matches FURN-M-KIT-PANTRYC exactly as asked and the insert is a
    # prices.toml [allowances] line — the model has one solid carcass per cabinet, not a
    # fitting-out, so there is no element for it to hang on.
    Furniture(uid="77DB93R0QZ", tag="FURN-M-KIT-PANTRY-S1", type_ref="CASE-PANTRY-CLOSET-24", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(24, 2.375)), rotation=deg(-90)),
    # S2 used to lap the corner of FURN-M-DINING's recommended chair zone. It no longer
    # does — the table was retyped, not moved; see the dining paragraph earlier in this file.
    Furniture(uid="K09MANH37J", tag="FURN-M-KIT-PANTRY-S2", type_ref="CASE-PANTRY-CLOSET-24", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(22, 2.375)), rotation=deg(-90)),
    # Both to the ceiling with PANTRYC — see its note on the west run.
    Furniture(uid="4WFET9VXWK", tag="FURN-M-KIT-PANTRY-S1-ST", type_ref="CASE-TS24-12", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(24, 2.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),
    Furniture(uid="785R3FDGRK", tag="FURN-M-KIT-PANTRY-S2-ST", type_ref="CASE-TS24-12", room="RM-M-LIVING",
              position=pt(ft(34, 5.375), ft(22, 2.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),

    # East wall uppers, 13" deep. Rewritten 2026-08-24 with the peninsula: FURN-M-KIT-WN2
    # (over the deleted N2, at y 25'-5 3/8"..27'-11 3/8") is gone — the peninsula's east end
    # is under it and the tall bank south of that is 96" already, so there is nothing left
    # on this wall for an upper to hang over between the peninsula and the range.
    #
    # ** WN1 REHANGS 54" -> 66". ** WIN-M-KIT-E's head is 66" and WN1 spans exactly the
    # y-range the new window sits in, so at 54" it would be a cabinet across the glass.
    # 66 + 42 = 108 = the ceiling, so this box needs no stacker — and the same move clears
    # WIN-M-KITCH-N around the corner (see FURN-M-KIT-WE3 above).
    Furniture(uid="2BF9VM3SFA", tag="FURN-M-KIT-WN1", type_ref="CASE-W30", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(34, 2.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(66))),
    # Recirculating canopy hood, 30" over the cooktop: mount 5'-6" on a 3' range. Moved north
    # with the range.
    Appliance(uid="Q0W3FYXJGX", tag="APPL-M-HOOD", type_ref="APPL-HOOD-RECIRC", room="RM-M-LIVING",
              position=pt(ft(34, 7.375), ft(31, 8.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
    # WN3 follows N3: 30" -> 24" and north to 29'-5 3/8", so upper and base share a face.
    Furniture(uid="DVWYR4A5J3", tag="FURN-M-KIT-WN3", type_ref="CASE-W24", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(29, 5.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    Furniture(uid="FTTPRYMZEH", tag="FURN-M-KIT-WN3-ST", type_ref="CASE-WS24-12", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(29, 5.375)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),
    # ** WN4 FILLS THE 15" THE GARAGE LEFT ** (owner, 2026-08-24): y 27'-2 3/8"..28'-5 3/8",
    # between FURN-M-KIT-MIXER-GARAGE's north face and WN3's south face, over the peninsula's
    # east end. 15" is a stock wall-cabinet width and is why this is a second box rather than
    # a wider WN3 — extending WN3 south would have made it 39", which is not a size anyone
    # sells. It carries the same 54" mount, the same 13" depth and the same stacker course as
    # the rest of the run, so the only step on this wall is the 11" from the garage's 24"
    # depth out to the uppers' 13" — which is what a tall cabinet beside uppers always does.
    Furniture(uid="0J52FYZBY6", tag="FURN-M-KIT-WN4", type_ref="CASE-W15", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(27, 9.875)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    Furniture(uid="N8BZY1M8FA", tag="FURN-M-KIT-WN4-ST", type_ref="CASE-WS15-12", room="RM-M-LIVING",
              position=pt(ft(34, 10.875), ft(27, 9.875)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=inch(96))),

    # ** THE ISLAND BECAME A PENINSULA, 2026-08-24. ** FURN-M-KIT-ISLAND was a 5'x3'
    # CASE-ISLAND-60 at (27'-6", 27'-11 3/8"), and the comment that stood here admitted its
    # clearance had never been re-checked after the 2026-07-30 range/sink swap. It had not,
    # and it did not pass: its aisle to the range front was 3'-5 3/8", against the 42" a
    # work aisle wants. Landing the east end on the east wall turns that failed aisle into
    # counter, opens the sink aisle from 4'-0" to 5'-0", and gives the kitchen one clean
    # entry from the west instead of two pinched ones.
    #
    # 10'-0" x 3'-3", x 25'-5 3/8"..35'-5 3/8", y 25'-2 3/8"..28'-5 3/8". 24" of carcass
    # plus a 15" seating overhang on the SOUTH — NKBA's knee space for a 36" counter. The
    # 12" the retired CASE-ISLAND-60 carried is the 42" BAR-height figure and was always
    # short here. The type is a plain rectangle, exactly as CASE-ISLAND-60 was, so which
    # side overhangs is stated here and by the stools.
    #
    # Aisles, against NKBA: north face 28'-5 3/8" -> north counter front 33'-5 3/8" = 5'-0"
    # (42" one cook, 48" two, both clear). West face 25'-5 3/8" -> fridge front 20'-6 3/8"
    # = 4'-11". Behind the seated diners is the open living room, 44" to walk past.
    #
    # ** THE EAST ~24" OF SEATING OVERHANG IS NOT A SEAT, and it is now used rather than
    # merely conceded: ** FURN-M-KIT-PANTRY-S1 stands exactly where an east-end sitter's legs
    # would go, so that end was never going to seat anyone. FURN-M-KIT-MIXER-GARAGE takes it,
    # standing ON the countertop from 36" to the 108" ceiling against the east wall. Nothing
    # overlaps (the tall bank and the overhang are coplanar at y=25'-2 3/8") and no check
    # fires, because casework carries no clearance zones here. THREE stools is the honest
    # count either way, which is what is authored below.
    Furniture(uid="PD9W4Q86MD", tag="FURN-M-KIT-PENINSULA", type_ref="CASE-PENINSULA-120", room="RM-M-LIVING",
              position=pt(ft(30, 5.375), ft(26, 9.875))),
    # 24" per seat (NKBA), tucked under the 15" overhang at y=24'-10".
    Furniture(uid="MZNJ9TAN56", tag="FURN-M-KIT-STOOL1", type_ref="FURN-BAR-STOOL", room="RM-M-LIVING",
              position=pt(ft(26, 5.375), ft(24, 10)), rotation=deg(180)),
    Furniture(uid="TMR4RNV2E3", tag="FURN-M-KIT-STOOL2", type_ref="FURN-BAR-STOOL", room="RM-M-LIVING",
              position=pt(ft(28, 5.375), ft(24, 10)), rotation=deg(180)),
    Furniture(uid="1RME2HHSQT", tag="FURN-M-KIT-STOOL3", type_ref="FURN-BAR-STOOL", room="RM-M-LIVING",
              position=pt(ft(30, 5.375), ft(24, 10)), rotation=deg(180)),

    # ** THE MIXER GARAGE — where the stand mixer lives (owner, 2026-08-24). **
    # 24" x 24", sitting ON the peninsula's countertop at a 36" mount and running to the
    # 108" ceiling, at the east end against the east wall: x 33'-5 3/8"..35'-5 3/8",
    # y 25'-2 3/8"..27'-2 3/8".
    #
    # ** IT IS BUMPED SOUTH, FLUSH AGAINST FURN-M-KIT-PANTRY-S1 ** (owner, 2026-08-24), so
    # the east wall reads as one unbroken column of storage from y=21'-2 3/8" to the ceiling
    # — the two 96"+12" pantry closets, then this, with no 15" of blank counter left between
    # them. What that costs is a millwork note the model cannot draw: the peninsula's
    # southern 15" is a seating OVERHANG everywhere else along its 10'-0", and under this
    # cabinet it must be a full-depth 39" carcass instead. Nobody sits at this end — the
    # tall bank is where an east-end sitter's legs would go — so the cantilever was never
    # earning anything here, and a counter-to-ceiling cabinet cannot stand on one.
    #
    # The 15" that opened up on its NORTH side is filled by FURN-M-KIT-WN4 below.
    #
    # ** THIS REPLACES A LIFT IN A BASE BAY, AND THE LIFT WAS A MISREADING. ** "Mixer slides
    # straight out onto the peninsula, outlet in the cabinet" was first built as a
    # Rev-A-Shelf spring lift under the counter plus three flush pop-ups in the top. The
    # mixer is meant to be AT counter level already and slide out level onto the open
    # counter west of it — no lifting 25 lb up out of a base, and no holes cut in stone.
    # The bottom bay is a heavy-duty full-extension pull-out at the counter plane; that and
    # the two receptacles inside it are on the type's `source` (plan/furniture_types.py) and
    # in prices.toml [allowances].
    #
    # It can only go at this end: a counter-to-ceiling box anywhere else on the peninsula
    # hangs from the ceiling with nothing behind it. Against the east wall it is a normal
    # tall cabinet that happens to start at 36".
    Furniture(uid="5T1VTCY3EV", tag="FURN-M-KIT-MIXER-GARAGE", type_ref="FT-KIT-MIXER-GARAGE-24",
              room="RM-M-LIVING", position=pt(ft(34, 5.375), ft(26, 2.375)),
              mount=Mount(kind=MountKind.WALL, elevation=inch(36))),

    # --- RM-M-PANTRY (storeys/main.py), 2026-08-24 -----------------------------------
    # The shelf stack, wall face to wall face across the room's whole 70 1/4" clear span,
    # 24" deep against the north wall. DESIGNED TO BE STOOD ON — the full build, the span
    # arithmetic and the blocking-before-gypsum sequencing are on the type's `source`
    # (plan/furniture_types.py) and in notes/pantry_climbable_shelving.md. The one number
    # worth repeating here: a 3/4" ply shelf CANNOT span this room under a person, so the
    # mid-span gable is structure, not joinery, and it is not optional.
    #
    # 24" and not the 16" this was first drawn at — the owner's call, 2026-08-24. In a 30"
    # room that leaves 6" of floor in front of it: y 33'-5 3/8"..35'-5 3/8" is shelf and
    # 32'-11 3/8"..33'-5 3/8" is all that is left to stand in, so RM-M-PANTRY is reached
    # from the doorway rather than walked into. Recorded here because the plan reads as a
    # room and the section does not.
    Furniture(uid="J49EW9WWTQ", tag="FURN-M-PANTRY-SHELVES", type_ref="FT-KIT-PANTRY-SHELVES-70",
              room="RM-M-PANTRY", position=pt(ft(21, 2.5), ft(34, 5.375))),

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
              position=pt(m(4.54649), m(0.258555)), rotation=deg(180),
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
    # Filed on `main` not `second` because Mount.elevation reads off the floor of the storey
    # it is filed on and only the main datum gives the right height: 8'-6" lands 1 1/2" under
    # the balcony beam soffit (8'-7 1/2") it hangs from.
    # No `room=`. The porch isn't a Room, and unlike the two hydrants (plan/fixtures.py) a
    # rod has no fixture-schedule cell to fill, so naming the room behind the wall bought
    # nothing but an `integrity.placeable_room_mismatch` advisory. The elevation datum is
    # unaffected: `Mount.elevation` falls back to the storey datum, and RM-M-BED's floor IS
    # the main datum (0"), so 8'-6" resolves to the same absolute height it always did.
    Furniture(uid="XH1JW70E8D", tag="FURN-M-PORCH-ROD-W", type_ref="FT-CURTAIN-ROD-OUTDOOR-114",
              position=pt(ft(13), ft(-9.5)),
              mount=Mount(kind=MountKind.WALL, elevation=ft(8, 6))),
    Furniture(uid="90BCAAC74M", tag="FURN-M-PORCH-ROD-E", type_ref="FT-CURTAIN-ROD-OUTDOOR-114",
              position=pt(ft(23), ft(-9.5)),
              mount=Mount(kind=MountKind.WALL, elevation=ft(8, 6))),
    # The two SIDE bays, 2026-08-22 — the porch was curtained on its front edge only and open
    # on both flanks, which is three quarters of a wind break. Four bay panels rather than one
    # continuous U; the reasoning, and the U that was tried first, is on
    # `FT-CURTAIN-ROD-OUTDOOR-98` in plan/furniture_types.py.
    #
    # x = 9'-0" and 27'-0", not the 8'-6"/27'-6" guard line and not the 8'-0"/28'-0" pillar
    # line. The pillar line is 6" OUTBOARD of the guard, so a rod on it hangs its curtain
    # over the railing and outside the porch. The guard line clears the 6x6 by a quarter inch
    # at this type's 6" bracket projection, which is not a clearance. 9'-0" is the first line
    # inboard that clears the pillar by more than a bracket (6 1/2") and still has balcony
    # joists overhead to hang from — the front pair hang from the E-W girts, these from the
    # 2x8 joist field crossing them.
    #
    # 98" over an 8'-8" (104") guard run, centred at y=-5'-0": 3" short of the house edge at
    # the north end and 2" clear of the front rods' bracket line at the south. Those two gaps
    # ARE the corners — the thing four panels have and a U does not.
    Furniture(uid="K6G71PKS4C", tag="FURN-M-PORCH-ROD-SW", type_ref="FT-CURTAIN-ROD-OUTDOOR-98",
              position=pt(ft(9), ft(-5)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(8, 6))),
    Furniture(uid="D9X6HWW4DZ", tag="FURN-M-PORCH-ROD-SE", type_ref="FT-CURTAIN-ROD-OUTDOOR-98",
              position=pt(ft(27), ft(-5)), rotation=deg(90),
              mount=Mount(kind=MountKind.WALL, elevation=ft(8, 6))),
]
GARAGE_PLACEABLES = [
    # The 60"-wide work surface runs along the west wall directly below the infrared
    # heater lamp. Rotation 90° turns the 30" depth into the wall-to-room dimension.
    Furniture(uid="CGF601AAAA", tag="FURN-G-WORKBENCH", type_ref="FURN-G-WORKBENCH",
              room="RM-GARAGE", position=pt(m(0.621183), m(18.6321)), rotation=deg(90)),
]
# The three east bedrooms are the same 13'-11 3/4" x 8'-10 3/4" clear box: queen, head
# north, 2' side-access zones running the long (14') way. Head-against-east-wall (under the
# window) doesn't fit — the 5'-4" width needs 9'-4" across the 8'-10 3/4" dimension once
# side zones are counted, pushing zones through the wall onto the NEC 210.52 receptacles at
# 16". Turning the beds fixes it; only the 2'-6" foot zone comes up short, into open room.
# x=30' clears the RC1/RC2 outlets; beds sit 9'-7" apart (not the 9'-0" room pitch) so each
# foot zone stops short of the headboard below it — heads float 5"-6" off the north wall.
SECOND_PLACEABLES = [
    # BED1 does not share the other two's station. It sits 14 1/8" further south (head still
    # against the east wall, foot still west) so its FOOT zone drops clear of the wardrobe on
    # the north wall, and its west face is then held on that wardrobe's east end at
    # x 28'-7 11/16" so the NORTH side-access zone clears it too. Both zones are 18" and the
    # room is only 8'-6 3/4" deep, so the pair cannot both be satisfied at the other beds'
    # y — which is why this one is authored apart from them. The south side zone runs into
    # the south wall by design: the bed is pushed to that wall and walked on the north side.
    Furniture(uid="819QDDYMZ5", tag="FURN-S-BED1", type_ref="FURN-QUEEN-BED", room="RM-S-BED1",
              position=pt(m(9.7996), m(3.71898)), rotation=deg(270)),
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
              room="RM-S-BED1", position=pt(m(8.12003), m(5.03458)), rotation=deg(0)),
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
    # The tub alcove's east return, built as a shelf (2026-08-21). FX-S-BATH1-SH is a
    # flanged 60x30 insert and was standing in two walls, not three: the chase face at
    # x 2'-11 3/8" west (0.36" of scribe), the north wall at y 35'-5 3/8", and its EAST end
    # open at x 7'-11 3/4", with 1'-8 7/8" of dead floor between it and the east wall at
    # x 9'-8 5/8". This carcass closes it. Its west panel IS that return — the carpenter
    # frames a 2x4 behind the panel and the flange nails to it — so the same article that
    # makes the tub a legitimate three-wall install is also the only storage in the room
    # you can reach from inside the tub.
    #
    # Rotation 0 puts the back at +y against the exterior wall and opens it south into the
    # room. y centre is FX-S-BATH1-SH's own and the depth is the tub's, so the two share a
    # front line at y 32'-10 1/2" and a back line at y 35'-4 1/2"; x runs 7'-11 3/4"..
    # 9'-7 3/4", butted to the tub, with the 7/8" of slack taken as scribe at the east wall.
    #
    # Deliberately NOT a Wall. A real return partition has to tee into W-S-N3, splitting it
    # at a new node, and a segment lays its studs from its own start node — which re-phases
    # the very stud grid WIN-S-BATH-N was nudged 8" off N-S-CH2 to sit centred in
    # (test_catlin_small_windows_have_no_header_and_keep_their_flanking_studs). Built
    # millwork as Furniture is this house's existing convention: the mudroom and both sauna
    # benches are priced the same way.
    #
    # Clearances, all measured against the resolved model: FX-S-BATH1-LAV ends at y 32'-0",
    # 10 1/2" south of the front line; ED-S-BATH1-MIRROR is the tight one at y 32'-6" —
    # 4 1/2" of daylight, and the reason the case stops 7/8" short of the east wall rather
    # than being furred out to it; ED-S-BATH1-RC-MIRROR and -SW are further down at
    # y <= 31'-2"; D-S-BATH1's leaf hangs at y 26'-4" and sweeps nowhere near, 6'-3" south;
    # WIN-S-BATH-N spans x 3'-5"..4'-7" on this same wall, well west of the case;
    # REG-S-EXH1 and both cans are ceiling-mounted and none is over it; and the FH-S-BATH1
    # radiant zone stops at y 31'-3", so the unit does not stand on the mat.
    Furniture(uid="640HBGH1XS", tag="FURN-S-BATH1-SHELF", type_ref="FT-BATH1-SHELF-2030",
              room="RM-S-BATH1", position=pt(m(2.68588), m(10.4013))),
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
    # --- mechanical-shaft access panel (2026-08-21) --------------------------
    # The NW shaft (W-S-CH-W/CH-S) is the house's basement-to-attic pipe highway, not a
    # leftover corner: VR-M-RADON-VENT's 3" combined radon/plumbing riser stands in it at
    # (1', 34'-6") from -8'-10" to 23'-10", four vent branches tie into it, and the second
    # floor's own risers are meant to run it. Until now it had no opening on this storey at
    # all — RM-M-MECH's D-M-MECH is a real swing door, but that reaches the main floor's
    # segment, not this one.
    #
    # South is the only face there is: north is W-S-N3B and west is W-S-W1B, both exterior,
    # and east is W-S-CH-W with FX-S-BATH1-SH's flange on the far side of it. Panel in
    # W-S-CH-S's bathroom face, which since the 2026-08-21 corner move is y 32'-10 1/2".
    #
    # 14x29 rather than the 14x14 the suite bath's tub takes: this is a reach-in into a
    # 2'-2 1/8" deep shaft that carries live pipe, not a look at one trap. Base 2'-0" puts
    # the opening at 2'-0"..4'-5" — the same band FURN-M-BATH1-AP uses on the WC carrier.
    # Centred x 1'-4" (opening 0'-9"..1'-11"): 2 3/8" off the west corner, and the riser's
    # own x=1'-0" sits 3" inside the west jamb rather than on it.
    #
    # NOT sized for the ceiling: PR-S-BATH1-VENT and PR-S-SUITEBATH-VENT tie in at
    # elevation 9'-3"..9'-5", which no wall panel at standing height reaches. Those stay a
    # ceiling job from the storey above. Standing room in front is 1'-7 1/4", between
    # FX-S-BATH1-WC's clearance zone and the wall face — enough to kneel square to the
    # opening, and the FH-S-BATH1 mat stops at y 31'-3" so nobody kneels on it.
    Furniture(uid="7MW8644E5H", tag="FURN-S-BATH1-CH-AP", type_ref="FT-ACCESS-PANEL-1429", room="RM-S-BATH1",
              position=pt(ft(1, 4), ft(32, 10.5)),
              mount=Mount(kind=MountKind.WALL, elevation=ft(2))),
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

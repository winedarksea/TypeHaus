# haus: editable
from typehaus import (Appliance, ElectricalDevice, Equipment, Fixture, Furniture, Location,
                      Mount, MountKind, Register, WallAttachment)
from typehaus.model import DeviceKind, deg, ft, inch, m, pt

# Project-local canvas placement targets. One list per storey keeps source ownership
# explicit. Main-floor rotation 0 puts an object's back at +y (project north).

# FX-1 (furnace-room utility sink) is retired: the basement's lavatory is FX-B-BATH-LAV
# (plan/fixtures.py), inheriting this uid. SP-B-UTILITY -> new WC's stub-up,
# SP-B-CW-UTIL-DR -> SP-B-CW-BATH-DR, and PR-B-UTIL-DRAIN/-VENT/PR-B-CW-UTIL/PR-B-HW-UTIL
# point at the new room (plan/mep.py). PR-B-COND (heat-pump condensate) air-gaps over
# FX-B-SAUNA-FD, the sauna's trapped wet-floor drain, which sees regular water flow the way
# an air gap wants and a bathroom lavatory does not.
#
# ** THE SAUNA ROTATED ONTO THE GARDEN WALL ON 2026-09-05, THEN SHRANK EAST THE SAME DAY. **
# The benches are dimensioned to *liner faces* (what the joiner scribes to), not node lines:
# west liner x=9'-1 13/16", east liner x=17'-5 3/4", north liner y=9'-8 3/16", south liner
# y=0'-9 1/2" — an 8'-3 15/16" x 8'-10 11/16" clear box, and it is **one plane on each of the
# four sides now**. The 2" jog the rotation left in the south face at x=8'-10", where the
# buried pour handed over to the framed walkout, is gone with W-B-S1B: the whole south face
# is W-B-S2's garden curb on SAUNA_LINER_ON_GARDEN_CURB.
#
# The east liner is on W-B-CS, and the shower pan takes the room's NORTH-EAST corner
# (notes/sauna_shower_basement_detail.md) — x 14'-5 3/4"..17'-5 3/4". That pan is what sizes
# the benches now, not the room: it eats the east 3'-0" of the only unbroken face, leaving
# 5'-3 15/16" of north wall, so the 8'-6" two-tier carcass comes down to the 5'-0" sibling.
# ** 2026-09-22: THE ROOM IS 1'-0" NARROWER, FROM THE WEST. ** The court narrowed to 17'-0"
# and N-B-S1 came 1'-0" east with it, taking the west wall along (the east wall is the
# x=18' bearing line and cannot follow). The benches followed the west liner: the two-tier
# run is the 4'-0" sibling (x 10'-3 1/4"..14'-3 1/4"), the west foot bench moved 1'-0"
# east, and the south foot bench is the 3'-0" sibling so it still stops 7 15/16" short of
# ED-B-SAUNA-JB. The figures in the comments below are the pre-narrowing ones.
BASEMENT_PLACEABLES = [
    # The two-tier run still takes the NORTH wall: it is the only face with no opening in it
    # — the south wall has WIN-B-SAUNA, the east wall D-B-SAUNA, the west wall is the new
    # partition — and it is the only one FX-B-SAUNA-FD can hide under. rotation 0 puts its
    # back (+y local) against that face. **5'-0" carcass since the shrink**, x 9'-3 1/4"..
    # 14'-3 1/4" and y 6'-2 3/16"..9'-8 3/16": 1 7/16" of scribe at the west liner and 2 1/2"
    # clear of FX-B-SAUNA-SH's pan at its east end. The 8'-6" carcass could not follow the
    # room in: the north wall's free run is the room's 8'-3 15/16" LESS the pan's 3'-0".
    #
    # FX-B-SAUNA-FD and the two condensate air gaps over it (PR-B-COND, PR-B-ERV-COND) sit
    # UNDER this bench, 18" off the north liner, and that is deliberate: a two-tier sauna
    # bench is an open frame, the slab falls to that point, and a boxed chase in the bench's
    # back corner is the only place in the room it can go without standing in open floor.
    # The drain is at x=13'-6", still 9 1/4" inside the shortened carcass's east end — which
    # is the constraint that kept this bench on the north wall rather than moving it to the
    # west one, where a 96" carcass would have fitted and left the air gaps standing in the
    # open.
    Furniture(uid="CBF601AAAA", tag="FURN-B-SAUNA-BENCH-E", type_ref="FURN-SAUNA-BENCH-2T-48",
              room="RM-B-SAUNA", position=pt(inch(147.25), inch(95.1875)), rotation=deg(0)),
    # The foot bench returns along the WEST liner, back to it (rotation 90 turns the 54"
    # carcass into the y direction), running y 1'-0"..5'-6" with a 2 1/2" scribe at the south
    # liner and 1 3/16" clear of the two-tier bench's south face. Its top is 18";
    # REG-B-EXH2's low stale pickup sits 4" off the floor behind it, which is the convection
    # loop the sauna's two dampered terminals drive. It moved 3'-10" east with the liner.
    Furniture(uid="CBF602AAAA", tag="FURN-B-SAUNA-BENCH-S", type_ref="FURN-SAUNA-BENCH-54",
              room="RM-B-SAUNA", position=pt(inch(131.8125), inch(39)), rotation=deg(90)),
    # ** THE SOUTH LINER'S OWN FOOT BENCH, NEW 2026-09-05. ** The third bench, and the one
    # that closes the L: it butts the west foot bench's east face at x=10'-9 13/16" and runs
    # 4'-0" east to x=14'-9 13/16", scribed to the south liner at y=0'-9 1/2". `rotation=180`
    # puts its back at -y, against that liner — the opposite of the north bench's 0.
    #
    # ** IT WAS 2'-6" FOR AN HOUR, AND MOVING THE HEATER IS WHAT MADE IT 4'-0". **
    # EQ-B-SAUNA-HTR stood in the middle of this liner and left 3'-7 15/16" of it; on the
    # east liner (plan/electrical.py) it leaves 4'-7 15/16" and the bench takes all but the
    # last 7 15/16" of that.
    #
    # ** WHAT STOPS IT IS ED-B-SAUNA-JB, NOT THE WALL. ** The heater's junction box came
    # east with the heater and sits at x 15'-5 3/4"..15'-11 3/4", its base at 18" AFF, which
    # is exactly this bench's top: a 4'-6" carcass would reach under it, and a fixed seat in
    # front of a live 9 kW junction box is not a detail to draw. So 4'-0", leaving 7 15/16"
    # of clear liner to the box and 1'-1 15/16" to the heater. Nothing in this engine grades
    # either gap — `EquipmentType` carries no `clearances` and nothing tests a placeable
    # against a wall device — so both are taken here, deliberately, and a longer bench must
    # not eat them. FURN-SAUNA-BENCH-48 was minted in `library/` for it.
    #
    # It sits UNDER WIN-B-SAUNA (x 12'-1"..13'-3", sill 3'-0 3/4"), which is the reason it is
    # an 18" foot bench and not a tier: the top clears the sill by 1'-6 3/4" and the glass
    # stays glass. The 2 1/2" of liner showing at the west end is the neighbouring bench's
    # own scribe, not a gap in this one.
    Furniture(uid="V218FXRSH2", tag="FURN-B-SAUNA-BENCH-SW", type_ref="FURN-SAUNA-BENCH-36",
              room="RM-B-SAUNA", position=pt(inch(159.8125), inch(19.5)), rotation=deg(180)),

    # RM-B-WORKSHOP's two benches. The room is still L-shaped, with the legs redrawn twice
    # on 2026-09-05: a west bay **7'-10 3/16" clear (x 0'-8"..8'-6 3/16")** running from the
    # south wall up to the sauna's north face at y=10'-3 13/16", plus a north strip 8'-0"
    # deep running the full width east to x=18'. The bay was 3'-8 3/16" between the rotation
    # and the shrink; the four feet the sauna gave back all landed here, and it gave 7" of
    # them back again when W-B-SA-N went north on 2026-09-05 (round three) — the strip lost
    # that 7", the bay gained it.
    # **Both benches take the west wall**, which is the one
    # unbroken face and is continuous across both legs.
    #
    # The west wall is the only unbroken face the room has: 18'-0" of bare concrete
    # (BASEMENT_8, interior face at x=0'-8" — the pour's inboard face, the foam is all
    # outboard). `rotation=deg(90)` turns FURN-G-WORKBENCH's 30" depth into the wall-to-room
    # dimension, exactly as the garage instance does, so the centre sits 15" off that face at
    # x=1'-11". Centres at y=6'-0" (under ED-B-WORKSHOP-PANEL1, the "over a bench" panel
    # that has been naming a bench that did not exist since it was authored) and y=11'-0",
    # giving one contiguous 10'-0" run from y=3'-6" to y=13'-6" that crosses the sauna's
    # north face at y=10'-0" without stopping at it — the west bay and the north strip are
    # one wall.
    Furniture(uid="6FJ01Z04WX", tag="FURN-B-WORKSHOP-BENCH-N", type_ref="FURN-G-WORKBENCH",
              room="RM-B-WORKSHOP", position=pt(ft(1, 11), ft(11)), rotation=deg(90)),
    Furniture(uid="8FXXT06T4E", tag="FURN-B-WORKSHOP-BENCH-S", type_ref="FURN-G-WORKBENCH",
              room="RM-B-WORKSHOP", position=pt(ft(1, 11), ft(6)), rotation=deg(90)),

    # --- RM-B-PLAY-N, the media room ---------------------------------------------------
    #
    # A windowless 324 sf box whose four resolved finish faces are south (W-B-CE) y=18'-3
    # 3/8", west (W-B-CN/CN2) x=18'-6", north (W-B-N1) y=35'-4", east (W-B-E2) x=35'-0" —
    # 16'-6" x 17'-0 5/8" clear. Everything below is dimensioned off those faces (which the
    # room's `clear_face` ring now follows).
    #
    # The screen: 98" (85.3" wide), hung on the north concrete wall, centred at x=26'-9",
    # which is the room's own centreline and where the owner asked for the ethernet drop
    # (ED-B-PLAY-N-DATA1). `mount=WALL` with the panel's bottom at 2'-6" puts its top at
    # 6'-8" under an 8'-3 1/2" ceiling. **An 8" concrete wall takes anchors, not blocking** —
    # there is no stud bay behind this and the mount is a mechanical fixing into the pour.
    Furniture(uid="X99HBG99WJ", tag="FURN-B-PLAY-TV", type_ref="FURN-TV-98", room="RM-B-PLAY-N",
              mount=Mount(kind=MountKind.WALL, elevation=inch(30)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-B-N1", face="left", distance_from_start=inch(111),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The U, opening north at the screen. 11'-0" of back run leaves 2'-9" either side of a
    # 16'-6" box; y 21'-6" to 29'-6" puts the back run 11'-13' off the panel — right for a
    # 98" screen — and leaves 2'-2 3/4" of walk between the bookcases and the sectional's
    # south face. FT-SECTIONAL-U-MEDIA is house-local and says why in plan/furniture_types.py.
    #
    # ** ROTATION 180 IS WHAT MAKES IT FACE THE SCREEN. ** Rotation 0 puts a seat's back at
    # +y — the note at the top of this file, and the convention every glyph in
    # `model/placeable_symbols/_families.py` draws to. This is the ONE line to edit if the
    # screen ever moves wall.
    Furniture(uid="1KZNJX16H6", tag="FURN-B-PLAY-SECTIONAL", type_ref="FT-SECTIONAL-U-MEDIA",
              room="RM-B-PLAY-N", position=pt(ft(26, 9), ft(25, 6)), rotation=deg(180)),
    # Bookcases either side of D-B-PLAY on the south wall, backs on its 18'-3 3/8" face.
    # The door's framing runs x 23'-10" to 29'-2" and its leaf sweeps x 24'-0"..26'-6",
    # y 18'-0"..20'-6", so both pairs stand clear of the arc: west from the 18'-6" corner to
    # 23'-10", east from 29'-8" to the 35'-0" corner.
    #
    # ** 7'-6", NOT THE LIBRARY'S 6'-0" ** (owner: take the theatre's shelving nearer the
    # ceiling). FT-BOOKCASE-32-90 is house-local and argues the height in
    # plan/furniture_types.py; the short version is that the room's measured clear is 8'-0"
    # under SL-M-DECK, so 7'-6" leaves a 6" reveal — scribe room under a poured deck that is
    # never dead flat, and enough that a 90" x 12" carcass can still be stood up off the
    # floor. Anti-tip into W-B-CE's studs at every case; it is a stud wall, unlike the pour
    # the screen hangs on.
    #
    # ** THE 8'-3 1/2" CEILING QUOTED ABOVE FOR THE SCREEN IS STALE ** —
    # `code.R305_ceiling_height` reads 8'-0" here today. It does not move the panel (top of
    # glass at 6'-8" clears either), but do not re-derive anything else from it.
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
    # ** FIRST-REFLECTION TREATMENT IS NOT AUTHORED, AND THE TWO SURFACES THAT WANT IT ARE
    # THE SIDE WALLS AND THE CEILING. ** Nothing in the engine grades room acoustics, so
    # this note is the whole record. Two of the four bounces are already answered by
    # decisions above and elsewhere, which is why only two are left:
    #
    # - FLOOR: answered. RM-B-PLAY-N is `floor_finish="carpet"` in storeys/basement.py, so
    #   the floor bounce is dead already. A rug on top of it would be belt and braces.
    # - BACK WALL: answered, by accident and well. Four 7'-6" bookcases stand across the
    #   south face behind the seating. A loaded shelf of irregular spines is a diffuser,
    #   which is the right treatment for a back wall in a room this short.
    # - SIDE WALLS: open. West x=18'-6" and east x=35'-0", both bare.
    # - CEILING: open. 5/8" gypsum straight onto the joist soffit, no plenum anywhere on
    #   this storey, so it is a hard flat plane directly over the listening axis.
    #
    # The geometry, worked off the authored pieces rather than a rule of thumb. Ears sit at
    # about (26'-9", 22'-6") — the U's back run, the row people actually watch from. The
    # screen centre is (26'-9", 34'-7 3/4"). Taking L/R speakers flanking it at x=22'-6"
    # and x=31'-0" on the north wall, the mirror-image construction puts BOTH side-wall
    # reflection points at ** y = 30'-7" **, and the room is symmetric so it is the same
    # figure left and right. A 2'x4' panel centred there covers y 29'-7" to 31'-7", which
    # is ample margin for the speaker positions being an assumption. Centre it near seated
    # ear height, about 3'-6" AFF.
    #
    # The ceiling point is the midpoint of the same path: ** y = 28'-6" **, spanning the
    # L/R pair in x, so roughly x 22' to 31'.
    #
    # ** BOTH SIDE WALLS ARE 12" CONCRETE ** — W-B-CN/CN2 west on FOUNDATION_WALL_12_INT,
    # W-B-E2 east on BASEMENT_12. Checked, because the south wall is NOT: W-B-CE is
    # INT_2X6_STAGGERED_PLUMBING, which is why the bookcases anti-tip into studs. Same
    # condition
    # as the screen above: mechanical anchors into the pour, no blocking to hit, and no
    # chance of a French cleat into a stud. Size the fixings before buying panels.
    #
    # Deliberately NOT authored as Furniture: panels this size would want real types, uids
    # and prices.toml rows, and their placement depends on speakers nobody has bought. This
    # is a finish-stage purchase with no geometry consequence for the build.
]
MAIN_PLACEABLES = [
    # --- the sitting circle, turned onto the fire (2026-09-06) ---------------------------
    #
    # `plans/pattern_language_review.md` C9 (The Fire) / C10 (Sitting circle): the electric
    # fireplace was a foot below the seated eye in the SE corner and NOTHING FACED IT. This
    # turns the seats onto it. The fire is now W-M-FIRE-* at x=34'-11 7/8", centred on y=8'-8"
    # (plan/storeys/main.py), and the convention on this floor is rotation 0 = back at +y, so
    # deg(90) = back WEST / opens EAST. The sofa is west of the fire, so it takes deg(90);
    # the two armchairs flank it and mirror exactly about y=104".
    #
    # Seat to flame: sofa 9'-9 3/8", armchairs 5'-2 1/8". The review's complaint was that the
    # unit "reads flat at the 11 ft where the sofa is" — geometry has now fixed the half of
    # that it can, and the unit itself is the other half (plan/electrical.py).
    #
    # ** RE-AUTHORED IN FEET. ** The sofa was `pt(m(7.87848), m(2.69813))`, a metric literal
    # nobody could read against a plan dimensioned in inches.
    #
    # ** THE TWO BINDING CLEARANCES ARE BOTH ABOUT 1", AND BOTH SHOULD BE RE-CHECKED AFTER
    # ANY NUDGE HERE: ** the sofa's 30" front band against the armchairs' west edge, and
    # armchair N's north edge against the dining chairs' 36" use margin at y=148 1/2".
    #
    # ** THE CLEARANCE VARIANT IS SHARED. ** FT-SOFA-84-SEAT-BAND is
    # FURN-SOFA-84 in every dimension and narrows the walk band to the width of the seat, not
    # the arms. Like FT-DINING-8-OPEN-CORNERS, it retypes the clearance shape instead of
    # reducing the reach. Without it the finding is
    # `integrity.placeable_recommended_clearance_conflict` at WARN/UNKNOWN, which does not
    # break the 0-FAIL gate but does put a line in a clean report.
    #
    # ** NO COFFEE TABLE. ** Anything standing in the sofa's front band is an encroachment by
    # definition, and this band is now the walk lane to the fire.
    Furniture(uid="XV5MXV43QJ", tag="FURN-M-SOFA", type_ref="FT-SOFA-84-SEAT-BAND",
              room="RM-M-LIVING", position=pt(ft(24, 4.5), ft(8, 8)), rotation=deg(90)),
    Furniture(uid="808W2W6TPA", tag="FURN-M-ARMCHAIR-N", type_ref="FURN-ARMCHAIR-35", room="RM-M-LIVING",
              position=pt(m(9.63082), m(3.29893)), rotation=deg(-45)),
    Furniture(uid="G5QQNW9448", tag="FURN-M-ARMCHAIR-S", type_ref="FURN-ARMCHAIR-35", room="RM-M-LIVING",
              position=pt(m(9.54846), m(1.77874)), rotation=deg(-120)),
    # Aligned with WIN-M-LIV-S1, south of the armchair and west of the east-wall cabinets.
    Furniture(uid="FIGMLIV001", tag="FURN-M-LIVING-FIDDLE-LEAF-FIG",
              type_ref="FURN-FIDDLE-LEAF-FIG-24", room="RM-M-LIVING",
              position=pt(ft(32), ft(1, 9))),
    # --- the mantel, which now has a body (2026-09-06) -----------------------------------
    #
    # SB-M-FIRE-MANTEL is a ShelfBank and a ResolvedShelfBank has NO POSITION — nothing
    # emits `model.shelf_banks`, so the mantel was a cut list with no geometry anywhere. It
    # is now hosted on this placeable, the same way FURN-B-PLAY-TV and the kitchen wall
    # cabinets are hung, and plan/millwork.py's bank hangs off it.
    #
    # x=34'-11 5/8" is the CENTRE of an 11 1/2" depth, so the slab runs x 413 7/8"..425 3/8":
    # its back lands exactly on the room's gwb face (35'-5 3/8"), covering the 1 7/8" tie
    # space behind the brick, and it projects 6" past the brick face at 34'-11 7/8".
    # `rotation=deg(90)` turns the 45 1/2" onto y, flush with the panel's ends.
    #
    # ** `elevation` IS THE BASE, AND ITS DATUM IS THE FINISHED FLOOR (corrected 2026-09-11). **
    # This block argued the opposite until today, and the shelf paid for it. The old text:
    # "`resolved_mount_elevation` adds the mount to `room_floor_elevation` — the SUBFLOOR
    # datum — so an authored 64" would resolve to 63 1/16" AFF and bury the shelf 15/16"
    # into W-M-FIRE-HEAD", and 64 15/16" was authored to buy that 15/16" back. It is no
    # longer true. `resolve/placeables._floor_elevation` returns BOTH planes and
    # `resolve_placeables` passes the FINISHED one as `floor_m`; the structural plane goes
    # in separately as `structural_floor_m` and is read only by the ceiling a ceiling mount
    # hangs from. Its docstring says it outright: "an authored mount height and a body's
    # base stand on the FINISHED floor". So the hand-added 15/16" was being applied twice
    # and the mantel floated 15/16" clear of the brick, at 0 FAIL — nothing grades a
    # placeable against the wall it is mounted on.
    # An authored 64" IS 64" AFF. The body resolves 64"..66 1/4" AFF = 64 15/16"..67 3/16"
    # absolute, sitting exactly on W-M-FIRE-HEAD's top — course 24. See
    # plan/furniture_types.py for the shelf itself.
    #
    # ** KNOWN AND ACCEPTED: `placeable_clear_floor_obstruction` READS THIS AS A PROTRUDING
    # OBJECT. ** A base at 64" is under the 80" headroom exemption and 11 1/2" is past
    # A117.1 307.2's 4" allowance, so the verdict is CORRECT — a 6" hard edge at 5'-4" is a
    # protruding object — and unenforced in a dwelling. No clearance zone in RM-M-LIVING
    # overlaps its plan rectangle and no door sweeps it; the SEKTION end panels abut its y
    # range at exactly 0", which is tangency, not overlap.
    Furniture(uid="5RWQRV1P72", tag="FURN-M-FIRE-MANTEL",
              type_ref="FT-MANTEL-WALNUT-46", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(64)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(104),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    # ** SAY THE COST OUT LOUD: TURNING THE SOFA EAST MEANS IT NO LONGER ADDRESSES THIS. **
    # The fire and this console now sit 90 degrees apart, and a 64" mantel with brick above it
    # cannot take a panel — so no screen can go over the fire either.
    # `plans/pattern_language_review.md` C9/C10 named that trade; it is a real choice and not a
    # deferral. It costs less than it sounds: ** THERE IS NO TV IN THIS ROOM AT ALL. ** The 98"
    # screen is FURN-B-PLAY-TV in the basement, so this console is holding storage that the
    # east wall's SEKTION banks already hold.
    #
    # ** RETIRING IT OUTRIGHT IS DEFENSIBLE AND IS LEFT AS AN OWNER CALL. ** Kept for now
    # because deleting a 5' console is a furniture decision, not a consequence of moving a
    # fireplace; the cost of keeping it is written above so the call can be made on the facts.
    Furniture(uid="EKN22YPA9J", tag="FURN-M-MEDIA", type_ref="FURN-MEDIA-60", room="RM-M-LIVING",
              position=pt(m(8.25967), m(0.415496)), rotation=deg(180)),
    # The east wall's storage is the SEKTION line in plan/living_east_run.py (2026-10-02),
    # which retired the eight BESTA units that stood here.
    # Dining at 17'-4". Table x 22'-10 1/2"..30'-10 1/2", y 15'-4 1/2"..18'-10 1/2"; the 36"
    # chair-use margin reaches y=12'-4 1/2" and y=21'-10 1/2", clear of the sofa and with a
    # wide circulation band to the peninsula.
    #
    # ** NUDGED 2" WEST WITH ITS SIX CHAIRS (2026-10-02). ** The east chair zone reaches
    # x 406 1/2"; the live-edge slab's nominal front is x 408 7/8" and a natural edge wanders,
    # so the edge is specified at <= 1 1/2" past the fronts and the table gave 2".
    #
    # Only the six side chairs are drawn on this 8-place table — end chairs would block the
    # hall-to-east-windows walk, so those two places stay unset, brought in when needed.
    #
    # ** THE SHARED TYPE DROPS ONLY THE UNUSED CORNERS (owner's call). **
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
              room="RM-M-LIVING", position=pt(m(8.19198), m(5.2201))),
    Furniture(uid="60XVKZHFAS", tag="FURN-M-CHAIR-S1", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(24, 3), ft(14, 6)), rotation=deg(180)),
    Furniture(uid="XCW1QKV701", tag="FURN-M-CHAIR-S2", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(26, 9), ft(14, 6)), rotation=deg(180)),
    Furniture(uid="REJA4QPWC3", tag="FURN-M-CHAIR-S3", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(29, 3), ft(14, 6)), rotation=deg(180)),
    Furniture(uid="VHHDZ62B5F", tag="FURN-M-CHAIR-N1", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(24, 3), ft(20, 2))),
    Furniture(uid="R3XJVT80XY", tag="FURN-M-CHAIR-N2", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(26, 9), ft(20, 2))),
    Furniture(uid="17F6ZBR67K", tag="FURN-M-CHAIR-N3", type_ref="FURN-DINING-CHAIR", room="RM-M-LIVING",
              position=pt(ft(29, 3), ft(20, 2))),
    # Centre the 80" king between D-M-BATH2's east RO jamb (56.635") and D-M-BED's
    # west RO jamb (170"). The 113.3175" midpoint leaves 16.6825" beside each bed edge.
    # Keep the north-south placement and head-north orientation, freeing the window walls.
    Furniture(uid="CMB701AAAA", tag="FURN-M-BED", type_ref="FURN-BED-KING", room="RM-M-BED",
              position=pt(inch(113.3175), m(2.80531))),
    # Matching 16" tables are the largest whole-inch width that fits: flush with the bed,
    # with 0.6825" to each RO. Their 16" depth backs onto the bedroom face at y=153.625".
    Furniture(uid="SM4T9MMNVP", tag="FURN-M-BED-NIGHTSTAND-W", type_ref="FURN-NIGHTSTAND-16", room="RM-M-BED",
              position=pt(inch(65.3175), inch(145.625))),
    Furniture(uid="CMN702AAAA", tag="FURN-M-BED-NIGHTSTAND-E", type_ref="FURN-NIGHTSTAND-16", room="RM-M-BED",
              position=pt(inch(161.3175), inch(145.625))),

    # Southeast corner since 2026-10-03: rotation -90 puts the back on the east wall,
    # with ~1/2" to its 212.115" finish face. D-M-BED2 moved one stud bay north, leaving
    # 12 3/4" from the desk's north end to its south (hinge) jamb, where its leaf parks. Keep y unchanged so the west-
    # facing 36" chair zone stays south of the king's foot at 68.445".
    Furniture(uid="CMD701AAAA", tag="FURN-M-BED-DESK", type_ref="FURN-DESK-HEMNES-61",
              room="RM-M-BED", position=pt(inch(198.75), inch(37.75)), rotation=deg(-90)),
    # Its chair faces east, tucked beneath the desk and inside its chair pull-out zone.
    Furniture(uid="PJSHPJN6TV", tag="FURN-M-BED-DESK-CHAIR", type_ref="FURN-DESK-CHAIR", room="RM-M-BED",
              position=pt(m(4.80049), m(0.954962)), rotation=deg(90)),

    # The south window ROs end/start at x=63/161": centre the touching 70 3/4" pair
    # on x=112", leaving 13 5/8" to either RO. Back edges follow W-M-S1's finish face;
    # rotation 180 faces the shelves north. Floor-standing, with manufacturer wall anchors.
    Furniture(uid="CMBOOK0001", tag="FURN-M-BED-BOOKCASE-W", type_ref="FURN-BOOKCASE-HEMNES-35",
              room="RM-M-BED", location=Location(attachment=WallAttachment(
                  wall_ref="W-M-S1", face="left", distance_from_start=inch(94.3125),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
    Furniture(uid="CMBOOK0002", tag="FURN-M-BED-BOOKCASE-E", type_ref="FURN-BOOKCASE-HEMNES-35",
              room="RM-M-BED", location=Location(attachment=WallAttachment(
                  wall_ref="W-M-S1", face="left", distance_from_start=inch(129.6875),
                  normal_gap=inch(0), rotation_offset=deg(180)))),

    # --- mudroom (RM-M-MUDROOM) --------------------------------------------------------
    # Both mudroom closets are framed rooms, not furniture (RM-M-MECH, RM-M-MUD-CLOSET,
    # storeys/main.py). Bench: back to the west wall, centred
    # on WIN-M-MUD at y=31'-4"; south end (29'-10") clears RM-M-MUD-CLOSET's north face
    # (29'-9 7/8") by 1/8".
    Furniture(uid="CMF803AAAA", tag="FURN-M-MUD-BENCH", type_ref="FURN-M-MUD-BENCH",
              room="RM-M-MUDROOM", position=pt(ft(1, 3.125), ft(31, 4)),
              rotation=deg(90)),

    # --- laundry (RM-M-LAUNDRY) --------------------------------------------------------
    # Fold-down drying rack over FX-M-LAUNDRY-SINK, sharing its x centreline and 24" width.
    # 48" mount is a clearance number: the tub tops out at 43" (34" rim + gooseneck), so it
    # leaves 5" over a stowed rack and 16" when down. The rack's RECOMMENDED zone names the
    # sink as its occupant so the tub groups instead of reading as an encroachment.
    # Instance restates the type's Mount because the resolver reads the instance one (same
    # as FX-M-KITCH-SINK's 27", plan/fixtures.py).
    #
    # x and y track the laundry faces of W-M-LS and W-M-CLN (storeys/main.py). Shifted 5 1/2"
    # west along W-M-CLN on 2026-10-01 to clear the W-M-LS corner; it still overlaps the tub
    # in plan as a shelf should. The laundry door stays at its authored station.
    Furniture(uid="XJSV712BWZ", tag="FURN-M-LAUNDRY-RACK", type_ref="FURN-WALL-RACK-24", room="RM-M-LAUNDRY",
              mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN", face="left", distance_from_start=inch(53.53125),
                  normal_gap=inch(0), rotation_offset=deg(90)))),

    # --- RM-M-STUDY, the call booth -----------------------------------------------------
    #
    # ** A FACING PAIR, NOT AN L. ** The first fit-out was an L — bench down the west wall,
    # desk across the south, sit in the corner and turn right — and the owner turned it 90
    # degrees the same day: the bench now runs east-west along the NORTH wall and the desk
    # sits in the SOUTH-WEST corner facing it. You do not walk into this room and turn
    # around in it; you step into the 18 7/8" pocket east of the desk, sit, and slide west.
    #
    # Both are dimensioned to the WAINSCOT faces (the joiner's box), not to node lines and
    # NOT to `Room.clear_face` (the gypsum face, 3/4" behind the wainscot) — see
    # the derivation on FT-STUDY-BENCH in
    # plan/furniture_types.py. The lined box is x 164 3/4"..211 7/8", y 220 3/4"..264 7/8".
    #
    # Rotation, the thing that goes wrong: the `sauna-bench` and `desk` glyphs both put the
    # back band at LOCAL +y (plan/furniture_types.py's FURN-B-PLAY-SECTIONAL note is the
    # cautionary tale). deg(0) leaves +y as +y, so the bench's back lands on the NORTH
    # wall; deg(180) turns +y to -y, so the desk's back lands on the SOUTH wall.
    #
    # Centres, both off the lined box:
    #   bench  x 164 3/4 + 47/2 = 188 1/4";  y 264 7/8 - 17/2 = 256 3/8"
    #   desk   x 164 3/4 + 29/2 = 179 1/4";  y 220 3/4 + 20/2 = 230 3/4"
    # Which leaves the two front faces at y 247 7/8" (bench) and y 240 3/4" (desk):
    # 7 1/8" of clear floor, and feet pass under the desk's cantilevered top.
    #
    # No `room=` mismatch and no clearance zone: neither type declares one, per the casework
    # rule. The desk clears D-M-STUDY's opening entirely now (its east end is 18 7/8" west
    # of the east wall), which is the one thing the turn fixed for free.
    Furniture(uid="AZ3GY4JQFH", tag="FURN-M-STUDY-BENCH", type_ref="FT-STUDY-BENCH",
              room="RM-M-STUDY", position=pt(inch(188.25), inch(256.375)),
              rotation=deg(0)),
    Furniture(uid="90JCARB5PG", tag="FURN-M-STUDY-DESK", type_ref="FT-STUDY-DESK",
              room="RM-M-STUDY", position=pt(inch(179.25), inch(230.75)),
              rotation=deg(180)),
    # The fold-down leaf fills the 18 1/8" entry pocket the desk deliberately
    # stops short of, so 29" + 18" = the full 47" lined box when two people are in here.
    # ** IT IS DRAWN DEPLOYED AND IT IS NORMALLY STOWED ** — the long argument is on
    # FT-STUDY-DESK-LEAF in plan/furniture_types.py. Read it before moving this: the leaf's
    # STOWED envelope (the south wall of the pocket, 8" to 28") is what evicted
    # REG-M-RET-STUDY from that wall, and nothing in this file records that dependency.
    #
    # Centre off the same lined box the other two use: x 164 3/4 + 29 + 18/2 = 202 3/4";
    # y 220 3/4 + 20/2 = 230 3/4", i.e. the desk's own y, because the two tops are coplanar
    # and butt. deg(180) matches the desk so both backs land on the SOUTH wall. Its east end
    # is at 211 3/4", 1/8" off the lined face and flush with FURN-M-STUDY-BENCH's east end.
    Furniture(uid="SBR4CFX5EH", tag="FURN-M-STUDY-DESK-LEAF", type_ref="FT-STUDY-DESK-LEAF",
              room="RM-M-STUDY", position=pt(inch(202.75), inch(230.75)),
              rotation=deg(180)),

    # --- curtain rods -------------------------------------------
    # One head line for the whole storey: 7'-0", 4" above the tallest main-floor head (6'-8",
    # WT-3048 + exterior doors) so it reads as one line rather than stepping room to room —
    # the facade discipline the elevations enforce. WIN-M-LIV-E1/E2 (5'-6" head) just get
    # longer curtains. ** EXCEPT ROD-E1/-E2, AT 7'-2" (2026-10-02): ** the east row's heads
    # rose 2" to 6'-10" when the sills went to the counter line, and the rods followed.
    # y=10" (or x, on side walls) centres the rod 10" off the wall line: 6 1/2" finish face
    # + ~3 1/2" bracket projection. Each rod centres on its opening's RO centre.
    Furniture(uid="EYJ3ZHXFSF", tag="FURN-M-LIV-ROD-S1", type_ref="FT-CURTAIN-ROD-48", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-S2", face="left", distance_from_start=inch(169.28125),
                  normal_gap=inch(1.625), rotation_offset=deg(-180)))),
    Furniture(uid="WJTG6V6T09", tag="FURN-M-LIV-ROD-BALC", type_ref="FT-CURTAIN-ROD-84", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-C1", face="right", distance_from_start=inch(10),
                  normal_gap=inch(0.625), rotation_offset=deg(90)))),
    Furniture(uid="2M12W07AGB", tag="FURN-M-LIV-ROD-E1", type_ref="FT-CURTAIN-ROD-48", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7, 2)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(64),
                  normal_gap=inch(1.375), rotation_offset=deg(-180)))),
    Furniture(uid="94TRP24ZX6", tag="FURN-M-LIV-ROD-E2", type_ref="FT-CURTAIN-ROD-48", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7, 2)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(144),
                  normal_gap=inch(1.15625), rotation_offset=deg(-180)))),
    # "Master bedroom" is read as RM-M-BED, the main-storey bedroom — not the second-storey
    # suite. Flag if that was the wrong room: the four rods move, nothing else does.
    Furniture(uid="BYYY8GG7E6", tag="FURN-M-BED-ROD-W1", type_ref="FT-CURTAIN-ROD-48", room="RM-M-BED",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W4", face="left", distance_from_start=inch(108),
                  normal_gap=inch(1.375), rotation_offset=deg(-180)))),
    Furniture(uid="R4A47142RN", tag="FURN-M-BED-ROD-W2", type_ref="FT-CURTAIN-ROD-48", room="RM-M-BED",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W4", face="left", distance_from_start=inch(28),
                  normal_gap=inch(1.375), rotation_offset=deg(-180)))),
    Furniture(uid="320A53KSR4", tag="FURN-M-BED-ROD-S1", type_ref="FT-CURTAIN-ROD-48", room="RM-M-BED",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-S1", face="left", distance_from_start=inch(48),
                  normal_gap=inch(1.375), rotation_offset=deg(-180)))),
    Furniture(uid="9222FS9Q20", tag="FURN-M-BED-ROD-S2", type_ref="FT-CURTAIN-ROD-48", room="RM-M-BED",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-S1", face="left", distance_from_start=inch(179),
                  normal_gap=inch(1.53125), rotation_offset=deg(-180)))),

    # --- plumbing access panels ---------------------------------
    # FX-M-BATH1-WC is the house's one wall-hung WC: the china bolts to an in-wall carrier
    # frame and its 3" waste drops through the deck inside that frame. This 14x29 panel is
    # the access to it — the frame, its concealed tank and the angle stop behind the
    # actuator plate are otherwise sealed inside a finished wall.
    #
    # ** ON W-M-HS1, BECAUSE THAT IS WHERE THE CARRIER IS. ** A wall-hung bowl cannot stand
    # 3'-10" from its own carrier; the bowl backs W-M-HS1, the drain follows it there
    # (plan/fixtures.py, plan/mep_drainage.py::PR-B-WC1-DRAIN), and so does this panel.
    #
    # Centred on the bowl's own x — the carrier is on that centreline — with the panel body
    # set fully behind BATH1's south finish face (y 22'-6 3/8"..22'-7 3/8", the face itself
    # at 22'-7 3/8"), so the recessed frame lands flush and the 1"-deep body never overlaps
    # the china standing in front of it. Base 2'-0", so the opening spans 2'-0"..4'-5" and
    # covers the actuator-plate opening, which sits 26 3/8" up the frame.
    Furniture(uid="RSDC92XMBB", tag="FURN-M-BATH1-AP", type_ref="FT-ACCESS-PANEL-1429", room="RM-M-BATH1",
              mount=Mount(kind=MountKind.WALL, elevation=ft(2), recessed_into_host_surface=True),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-HS1", face="left", distance_from_start=inch(26.40625),
                  normal_gap=inch(-1), rotation_offset=deg(-180)))),
    # FX-M-BATH2-TUB drains at SP-M-BATH2-TUB (7'-4", 19'-4.8"), 8" off W-M-BA2E and
    # behind the tub rather than at either end of it — so the trap and the waste-and-
    # overflow are unreachable from BATH2 without pulling the tub. They are 8" the other
    # side of that wall, in RM-M-LAUNDRY, which is where the panel goes: laundry face of
    # W-M-BA2E at the drain's own y. Base at 6" puts the opening at 6"..1'-8", the band
    # the tee and trap occupy.
    Furniture(uid="1AQVMB4JJD", tag="FURN-M-BATH2-TUBDK-AP", type_ref="FT-ACCESS-PANEL-1414",
              room="RM-M-BATH2", mount=Mount(kind=MountKind.WALL, elevation=inch(3)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-TUBDK-W", face="right", distance_from_start=inch(62.625),
                  normal_gap=inch(0), rotation_offset=deg(0)))),

    # --- RM-M-BATH2 over-toilet cabinet --------------------------
    # The room's only wall storage, on the only free wall left: W-M-HS1's bathroom face,
    # x 6 5/8" (W-M-W3's finish face, which FX-M-BATH2-SINK is also struck off) to 4'-4"
    # (W-M-TUBDK-W's west face). 45 3/8" of free run, a 45" carcass, 3/16" of scribe each
    # end. Faces are struck off W-M-HS1's own layer polygons.
    #
    # `Mount.elevation` is the BOTTOM of the body (as for FURN-M-KIT-OVER-FRIDGE), so
    # 48 + 57 = 105", leaving 1" below the actual finished ceiling. The 48" bottom keeps
    # the cabinet clear of the 30" toilet tank; lowering it would take elbow room and
    # could force the bowl south, landing its front clearance inside the vanity. See
    # plan/furniture_types.py and
    # notes/bath2_over_toilet_cabinet.md.
    Furniture(uid="N688X4AYJ4", tag="FURN-M-BATH2-CAB", type_ref="FT-BATH2-CAB-4506",
              room="RM-M-BATH2",
              mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-HS1", face="right", distance_from_start=inch(29.3125),
                  normal_gap=inch(0), rotation_offset=deg(0)))),

    # --- porch enclosure track ------------------------------------
    # FOUR TRACK RUNS became THREE on 2026-09-22: one front run and two flanks. See
    # `FT-PORCH-TRACK-176` in plan/furniture_types.py and notes/porch_enclosure.md.
    #
    # ** ELEVATION: 104.75", THE BALCONY JOIST SOFFIT. ** 107.75" until the balcony came down
    # 3" (2026-09-23); 111.75" before the 2x12s.
    # `Mount.elevation` is the body BOTTOM and the extrusion is 1" tall, so the track's top is
    # ON the soffit. Filed on `main`, whose datum (0") is what the height reads off. Editable
    # files cannot import params: this is `_balcony_beam_soffit` + the 2x12 depth by hand.
    #
    # ** FRONT LINE y = -8'-11 1/4", ON THE SPARE JOIST. ** At 12" o.c. the balcony joists sit
    # at -9'-5 1/4" and -8'-5 1/4", so FS-SG-DECK carries one extra 2x12 line at -8'-11 1/4"
    # (`JoistSpec.extra_lines`) and the front run screws up into it for its whole length. One
    # continuous run: nothing splits the curtain plane now the centre beam and pillar are
    # gone. Two 90-degree curves at (10'-0", -9'-0") and (26'-0", -9'-0") turn the corners,
    # each standing in for ~8" of both legs. RL-SG-PORCH's south leg is 6" south at -9'-6".
    #
    # No `room=`: the porch isn't a Room.
    Furniture(uid="XH1JW70E8D", tag="FURN-M-PORCH-TRACK-F", type_ref="FT-PORCH-TRACK-176",
              position=pt(ft(18), ft(-8, -11.25)),
              mount=Mount(kind=MountKind.CEILING, elevation=inch(104.75))),
    # The two FLANKS, x = 10'-0" and 26'-0": 6" inside the side walls' court faces and the
    # guard's side legs, which is where they have always stood relative to the court. Each
    # crosses every joist bay perpendicular; the bay closures are FS-SG-DECK's blocks.
    #
    # ** THE NORTH END RUNS PAST THE DECK EDGE, AND NO FASTENER TOUCHES THE HOUSE. ** The
    # porch deck edge is -0'-10"; the cladding face is -0'-7 1/4" (`_WALL_OUTBOARD_IN`), not
    # the -0'-5" this said, which had the track 1 1/4" into the panel (measured 2026-09-23).
    # The track stops at -0'-7 1/2", 1/4" off the face, the last 2 1/2" on a small aluminium
    # outrigger off the balcony's north edge joist (y -0'-10"). The panel's north edge is a
    # weighted flap lying on the cladding: high bug reduction, not hermetic. TR-SG-SLOT
    # closes the vertical slot below.
    #
    # ** THE WALK-THROUGH IS IN THE EAST FLANK at y ~ -7'-6"**, the centre of RL-SG-PORCH's
    # 3'-0" guard opening onto ST-SG-PORCH.
    Furniture(uid="K6G71PKS4C", tag="FURN-M-PORCH-TRACK-W", type_ref="FT-PORCH-TRACK-102",
              position=pt(ft(10), ft(-4, -9.75)), rotation=deg(90),
              mount=Mount(kind=MountKind.CEILING, elevation=inch(104.75))),
    Furniture(uid="D9X6HWW4DZ", tag="FURN-M-PORCH-TRACK-E", type_ref="FT-PORCH-TRACK-102",
              position=pt(ft(26), ft(-4, -9.75)), rotation=deg(90),
              mount=Mount(kind=MountKind.CEILING, elevation=inch(104.75))),
    # FURN-M-PORCH-TRACK-FE (uid 90BCAAC74M) is retired with the split: spent, do not reuse.

    # --- the porch's two lounge chairs (2026-09-06) ---------------------------------------
    #
    # `plans/TODO.md` 241: the porch is roofed, fanned, lit, wired and curtained and has
    # NOTHING on it — 17'-0" x 8'-8" of deck (19'-0" until 2026-09-22) reading as empty in
    # the 3D. Two real chairs, a named product at its real size (`FT-PORCH-LOUNGE-27` in
    # the shared `library.placeables.furniture` catalog).
    #
    # ** THE WEST BAY. ** (A centre pillar split this porch until 2026-09-22.) The east half is
    # circulation: D-M-BALC lands at x 21'-4" and the porch's only route to grade is
    # RL-SG-PORCH's 3'-0" guard opening at x 26'-6", y -6'-0"..-9'-0", so the door-to-stair
    # diagonal owns the east bay. West of it is a dead end, and that is where seating goes.
    # The pair is centred on x=13'-0": 7 1/2" of margin to the west guard (x 9'-6", W-SG-W1's
    # inner face), 15" between the two chairs, and the east chair's arm at 15'-10 1/2", 5'-5 1/2"
    # short of the door. The 15" is a gap a Lollygagger side table (18") would NOT fit, which
    # is deliberate; the arms are the table until the owner buys one and the chairs slide.
    #
    # ** y = -3'-6" IS SET BY THE HOSE BIB, NOT BY THE VIEW. ** FX-M-PORCH-HYD is on W-M-S1
    # at x=12'-8", 24" up. It moved there on 2026-09-15 to get off stud-006, and it landed
    # BETWEEN the chairs rather than behind the west one: the pair is centred on 13'-0" with
    # 15" of gap, so the gap runs 12'-4 1/2"..13'-7 1/2" and the bib is 3 1/2" into it. That
    # is a better place for a hose than behind an arm. The back edge at -2'-3 1/4" keeps
    # 22 1/4" of clear deck between chair and cladding face (-0'-5"), which is reach-in room
    # for a hose. In front there is 4'-9 1/4" to the guard.
    #
    # ** `elevation=inch(1)`, and it is not optional. ** The porch walking surface is the
    # composite plank laid ON the 0'-0" joist tops (`_porch_walking_surface`, params/
    # sunken_garden.py), so a FLOOR mount with no elevation would bury both chairs 1" in the
    # deck — the RL-SG-PORCH posts start at the same 1".
    #
    # rotation 0 = back at +y: both face south, over the guard into the sunken garden. The
    # 43" guard top is picket, so a seated eye at ~3'-6" looks through it, not at it.
    #
    # NO `room=` — the porch is not a Room, the FURN-M-PORCH-TRACK-* precedent.
    #
    # ** KNOWN, AND LEFT: THE FAN IS NOT OVER THE CHAIRS. ** ED-M-PORCH-FAN hangs at
    # x=18'-0", y=-4'-10" — centred on the whole porch, i.e. on the pillar line. Its 60"
    # sweep reaches x 15'-6", which catches the east chair's outer arm and misses the west
    # chair by 1'-9". Moving the fan west to ~x 14'-6" would put it over the seats and off
    # the porch's centre; that is an owner call, not a plan error, and it is in plans/TODO.md.
    Furniture(uid="KG1WAJESNZ", tag="FURN-M-PORCH-LOUNGE-W", type_ref="FT-PORCH-LOUNGE-27",
              position=pt(ft(11, 3), ft(-3, -6)), rotation=deg(0),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(1))),
    Furniture(uid="KG4PRNB28W", tag="FURN-M-PORCH-LOUNGE-E", type_ref="FT-PORCH-LOUNGE-27",
              position=pt(ft(14, 9), ft(-3, -6)), rotation=deg(0),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(1))),

    # --- the dedicated closets' shelf-and-rod runs ----------------------
    #
    # plans/TODO.md: "wire shelves and racks in the dedicated closets", aimed at jackets in
    # the mudroom closet. All four closets were modelled as empty boxes, which reads on the
    # plan as usable floor and bills as nothing.
    #
    # Each run hangs on the closet's longest uninterrupted wall, 8" (half the 16" depth)
    # off its finish face — measured off the wall's own layer polygons. Elevation 66" is the shelf; a full-length coat hangs clear beneath it.
    #
    # RM-M-MUD-CLOSET: 63" of clear wall between x 6 5/8" and 5'-9 5/8", north wall
    # (W-M-MUDC-N, face y 29'-5 1/8"). A 60" run centres in it with 1 1/2" either side.
    Furniture(uid="1HYRGFZMA0", tag="FURN-M-MUDC-SHELF", type_ref="FT-CLOSET-SHELFROD-60",
              room="RM-M-MUD-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(66)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-STOS", face="left", distance_from_start=inch(37.84375),
                  normal_gap=inch(0.78125), rotation_offset=deg(0)))),
    # RM-M-CLOSET's fit-out is plan/closet.py.
]
GARAGE_PLACEABLES = [
    # The 60"-wide work surface runs along the west wall directly below the infrared
    # heater lamp. Rotation 90° turns the 30" depth into the wall-to-room dimension.
    Furniture(uid="CGF601AAAA", tag="FURN-G-WORKBENCH", type_ref="FURN-G-WORKBENCH",
              room="RM-GARAGE", position=pt(m(2.449983), m(19.3941)), rotation=deg(90)),
]
# The beds are placed per room: BED1 and BED2 face north; BED3 faces east. The integration
# assertion in test_catlin_source_alignment checks their clearances and door swings.
SECOND_PLACEABLES = [
    # BED1 stays in the southern part of its bay; its west-side wardrobe and north-side desk
    # leave the bed's modeled access zones open. Nudged 1/64" east (owner, 2026-10-03)
    # to clear the added east PAX frame's 18" foot-access zone.
    Furniture(uid="819QDDYMZ5", tag="FURN-S-BED1", type_ref="FURN-BED-TWIN", room="RM-S-BED1",
              position=pt(m(9.801366875), m(3.36872)), rotation=deg(-90)),
    Furniture(uid="CSB701AAAA", tag="FURN-S-BED2", type_ref="FURN-QUEEN-BED", room="RM-S-BED2",
              position=pt(m(9.95572), m(6.98818)), rotation=deg(0)),
    # BED3 is a FULL (owner, 2026-10-02), tight to the east wall and 3/8" off the north: a
    # queen's 18" side zone ran 5 3/8" into the PAX sliders (plan/bedroom_wardrobes.py) and
    # neither could move. Its south side is 30'-8"; the zone stops 1 3/4" short of the doors.
    Furniture(uid="CSB702AAAA", tag="FURN-S-BED3", type_ref="FURN-BED-FULL", room="RM-S-BED3",
              position=pt(m(9.80100), m(10.07151)), rotation=deg(-90)),
    # BED1 and BED2 have desks on their north walls with chairs to the south. BED3's desk
    # stays on the west wall with its chair to the east. The dining chair keeps the lighter
    # dining-room plan and 3D appearance.
    Furniture(uid="DSK701AAAA", tag="FURN-S-DESK1", type_ref="FURN-DESK-48", room="RM-S-BED1",
              position=pt(m(10.4995), m(4.58763)), rotation=deg(90)),
    # Three inches north of the UI placement clears BED1's 18" side-access zone by 0.58".
    Furniture(uid="CHR701AAAA", tag="FURN-S-DESK-CHAIR1", type_ref="FURN-DESK-CHAIR", room="RM-S-BED1",
              position=pt(m(10.0492), m(4.62797)), rotation=deg(90)),
    Furniture(uid="DSK702AAAA", tag="FURN-S-DESK2", type_ref="FURN-DESK-48", room="RM-S-BED2",
              position=pt(m(8.49481), m(7.75018)), rotation=deg(0)),
    # Four inches west of the desk centre keeps the chair outside BED2's side-access zone.
    Furniture(uid="CHR702AAAA", tag="FURN-S-DESK-CHAIR2", type_ref="FURN-DESK-CHAIR",
              room="RM-S-BED2", position=pt(m(8.39794), m(7.44471)), rotation=deg(-180)),
    # BED3's desk stays on the west wall, clear of the north-wall glazing.
    Furniture(uid="DSK703AAAA", tag="FURN-S-DESK3", type_ref="FURN-DESK-48", room="RM-S-BED3",
              position=pt(m(7.04819), m(10.1621)), rotation=deg(90)),
    Furniture(uid="CHR703AAAA", tag="FURN-S-DESK-CHAIR3", type_ref="FURN-DESK-CHAIR", room="RM-S-BED3",
              position=pt(m(7.6327), m(10.1621)), rotation=deg(-90)),
    # The 31 1/2" side runs north–south, with its south edge on W-S-S2's painted
    # drywall face at y=6.635". Centre is that face plus half the table length;
    # rotation 90 leaves the drawer accessible from the east side.
    Furniture(uid="TAB701AAAA", tag="FURN-S-STUDY-TABLE", type_ref="FURN-CHESS-TABLE-315",
              room="RM-S-STUDY2", position=pt(m(9.55695), inch(22.385)), rotation=deg(90)),
    Furniture(uid="CHR704AAAA", tag="FURN-S-STUDY-CHAIR1", type_ref="FURN-DINING-CHAIR",
              room="RM-S-STUDY2", position=pt(m(10.2316), m(0.589194)), rotation=deg(-90)),
    Furniture(uid="CHR705AAAA", tag="FURN-S-STUDY-CHAIR2", type_ref="FURN-DINING-CHAIR",
              room="RM-S-STUDY2", position=pt(m(8.8924), m(0.588713)), rotation=deg(90)),
    # A compact rocking chair occupies the southeast corner, with its back to the south
    # wall and WIN-S-STUDY3 just north of it up the east wall at y 5'-4" (off the chair
    # rather than over it). The armchair symbol is the intentional close-enough 2D/3D
    # approximation: it keeps the plan readable while the catalog type preserves the use.
    Furniture(uid="CSB703AAAA", tag="FURN-S-SUITE-BED", type_ref="FURN-QUEEN-BED",
              room="RM-S-SUITE", position=pt(m(1.52182), m(5.57379)), rotation=deg(0)),
    # Flush with the queen's sides; backs stop at the 3/4" walnut paneling face.
    # The 16" depth stays within the bed's 30" head-end allowance for side access.
    Furniture(uid="CSSNST0001", tag="FURN-S-SUITE-NIGHTSTAND-W", type_ref="FURN-NIGHTSTAND-16",
              room="RM-S-SUITE", position=pt(m(0.43944), m(6.51828))),
    Furniture(uid="CSSNST0002", tag="FURN-S-SUITE-NIGHTSTAND-E", type_ref="FURN-NIGHTSTAND-16",
              room="RM-S-SUITE", position=pt(m(2.59763), m(6.51828))),
    # The south wall is 106 1/2" clear: a 42" desk plus the 63" dresser leaves
    # about 1/2" at each end and between them. Desk west, dresser east (owner,
    # 2026-10-03), backs south; the chair clears the bed's 18" foot-access band.
    Furniture(uid="CSSDSK0001", tag="FURN-S-SUITE-DESK", type_ref="FURN-DESK-42",
              room="RM-S-SUITE", position=pt(m(0.711424), m(3.10858)),
              rotation=deg(180)),
    Furniture(uid="CSSCHR0001", tag="FURN-S-SUITE-DESK-CHAIR", type_ref="FURN-DESK-CHAIR",
              room="RM-S-SUITE", position=pt(m(0.716363), m(3.36318)),
              rotation=deg(0)),
    Furniture(uid="CSSDRS0001", tag="FURN-S-SUITE-DRESSER", type_ref="FURN-DRESSER-HEMNES-63",
              room="RM-S-SUITE", position=pt(inch(81.125), inch(120.6875)),
              rotation=deg(180)),

    # The three bedrooms have no built-in closets; their PAX wardrobes (BED1/2 corner sets,
    # BED3's sliding pair) are in plan/bedroom_wardrobes.py.

    # Hall-bath linen storage: three SEKTION units in plan/bath1_storage.py. Their open
    # lower bays keep the existing toilet clear of drawers without moving its drain.
    # The tub alcove's east return, built as a shelf. FX-S-BATH1-SH is a
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
    # Clearances, all measured against the resolved model (2026-09-28): FX-S-BATH1-LAV ends
    # at y 32'-10.38", only 0.12" south of the front line and across the case's whole width,
    # which is why the type closes the case below the counter; ED-S-BATH1-MIRROR ends at
    # y 32'-3", 7 1/2" of daylight, and the case stops 7/8" short of the east wall as scribe; ED-S-BATH1-RC-MIRROR and -SW are further down at
    # y <= 31'-2"; D-S-BATH1's leaf hangs at y 26'-4" and sweeps nowhere near, 6'-3" south;
    # WIN-S-BATH-N spans x 3'-5"..4'-7" on this same wall, well west of the case;
    # REG-S-EXH1 and both cans are ceiling-mounted and none is over it; and the FH-S-BATH1
    # radiant zone stops at y 31'-3", so the unit does not stand on the mat.
    Furniture(uid="640HBGH1XS", tag="FURN-S-BATH1-SHELF", type_ref="FT-BATH1-SHELF-2030",
              room="RM-S-BATH1", position=pt(m(2.68588), m(10.4013))),
    # The suite bath's twin of it, turned to open west (2026-10-03): FX-S-SUITEBATH-TUBSH's
    # SOUTH return, in the 11 1/4" between the tub (y=204.625") and W-S-SBS (y=193.375").
    # x 15'-2 5/8"..17'-8 5/8" is the tub's own 30" width; the back sits on W-S-C2C.
    # Millwork, not a wall, for the hall bath's reason: a return partition would tee into
    # bearing W-S-C2C and re-phase its stud grid. D-S-SUITEBATH's leaf parks ~36" west of it.
    Furniture(uid="P1NESXCW7K", tag="FURN-S-SUITEBATH-RETURN", type_ref="FT-SUITEBATH-SHELF-1130",
              room="RM-S-SUITEBATH", position=pt(inch(197.615), inch(199)), rotation=deg(-90)),
    # Robe pegs on W-S-DC2's bath face, y 18'-9"..20'-9", north of the door leaf's parked
    # position (y < ~18'-5") and clear of the WC's corner. Rail bottom 64", as in the closet.
    Furniture(uid="GG09CD7KYB", tag="FURN-S-SUITEBATH-PEGS", type_ref="FT-SUITEBATH-PEGS-24",
              room="RM-S-SUITEBATH", mount=Mount(kind=MountKind.WALL, elevation=inch(64)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-DC2", face="right", distance_from_start=inch(46),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    # The Estero arch mirror (owner, 2026-10-03), shelf facing into the room, centred on
    # FX-S-SUITEBATH-LAV, with ED-S-SUITEBATH-MIRROR's bar above it. Bottom 46", so the
    # shelf clears the faucet by ~10"; the top at 74" hangs off the SN3 72"-79 1/4" backing course.
    Furniture(uid="P0MWNTP6QE", tag="FURN-S-SUITEBATH-MIRROR", type_ref="FT-SUITEBATH-MIRROR-ESTERO",
              room="RM-S-SUITEBATH", mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-SN3", face="right", distance_from_start=inch(50.5),
                  normal_gap=inch(0.25), rotation_offset=deg(0))), rotation=deg(0)),
    # RM-S-PLANT: a place to sit among the plants, program divides along y — plants on the
    # south glass, seating behind. Plants sit directly under ED-S-PLANT-TUBE1/2 (x=3'-4"/8'-8",
    # 2'-3" below ceiling, on a photoperiod timer) and under WIN-S-PLANT1/2 (same x, the
    # WT-3048-HP/-HP-T pair — same 30" of glass, better U) so each gets daylight plus the
    # tube.
    # Chairs face south from y 4'-0"..7'-0", 1'-3" clear of the plants' north edge. The room's
    # supply is a ceiling grille (REG-S-HP-PLANT at 6'-8", 3'-4", plan/mep_registers.py), so
    # nothing on the floor needs keeping clear between the chairs. Chair x is
    # clear of D-S-PLANT's 2'-6" swing (y=1'-5"..3'-11", reaching to x=15'-6").
    Furniture(uid="PLT701AAAA", tag="FURN-S-PLANT-POT1", type_ref="FURN-PLANT-18",
              room="RM-S-PLANT", position=pt(m(1.28957), m(0.606871))),
    Furniture(uid="PLT702AAAA", tag="FURN-S-PLANT-POT2", type_ref="FURN-PLANT-18",
              room="RM-S-PLANT", position=pt(m(2.6348), m(0.584116))),
    Furniture(uid="CHR706AAAA", tag="FURN-S-PLANT-CHAIR", type_ref="FURN-ARMCHAIR-35",
              room="RM-S-PLANT", position=pt(m(1.13772), m(1.8808)), rotation=deg(45)),
    Furniture(uid="RCK702AAAA", tag="FURN-S-PLANT-ROCKER", type_ref="FURN-ROCKING-CHAIR-30",
              room="RM-S-PLANT", position=pt(m(4.51571), m(1.96147)), rotation=deg(-45)),
    # Centre on the finished north wall: x=(0.201041+5.383784)/2,
    # y=2.665984 minus half the 23 5/8" depth. Rotation 0 faces south into the room.
    Furniture(uid="PLTDESK001", tag="FURN-S-PLANT-DESK", type_ref="FURN-DESK-MITTZON-47",
              room="RM-S-PLANT", position=pt(m(2.7924125), m(2.3659465)), rotation=deg(0)),
    # Wet-location spot, y=8'-6 3/8": the north partition carries the plant room's humid
    # liner, whose face sits 1 1/4" south of the bare-stud line. A fixture in a room that
    # condenses on purpose has to be wet-location listed rather than the ordinary interior
    # sconce this shares with the study.
    ElectricalDevice(uid="QTS0020AAA", tag="ED-S-PLANT-SPOT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-SPOT-WET",
                     circuit="CKT-LT-UPPER", room="RM-S-PLANT",
                     controlled_by=("ED-S-PLANT-SW-TIMER",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-PS1", face="right", distance_from_start=inch(50.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # --- plumbing access panel ----------------------------------
    # FX-S-SUITEBATH-TUBSH's waste-and-overflow tee is at its north end, 1" off W-S-SN3 (the
    # RM-S-HALL partition), so the panel goes in the hall face of W-S-SN3 (2 3/8" off the
    # 4 3/4" partition's centreline) on the tub's x centre — reachable from the hall.
    # FX-S-BATH1-SH gets none deliberately: its drain end is west, into the plumbing chase
    # (not a room, no standing room), and the only reachable face puts a panel over the tub
    # itself — no better than pulling the apron. Left for the ceiling below.
    # Neither fixture carries a `drain_position`; recheck this placement if one is authored.
    Furniture(uid="NHFPDD49RB", tag="FURN-S-SUITEBATH-AP", type_ref="FT-ACCESS-PANEL-1414", room="RM-S-HALL",
              mount=Mount(kind=MountKind.WALL, elevation=ft(0, 6), recessed_into_host_surface=True),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-SN3", face="left", distance_from_start=inch(81),
                  normal_gap=inch(-1.5), rotation_offset=deg(-180)))),
    # --- mechanical-shaft access panel --------------------------
    # The NW shaft (W-S-CH-W/CH-S) is the house's basement-to-attic pipe highway, not a
    # leftover corner: VR-M-RADON-VENT's 3" combined radon/plumbing riser stands in it at
    # (1', 34'-6") from -8'-10" to 23'-10", four vent branches tie into it, and the second
    # floor's own risers are meant to run it. Until now it had no opening on this storey at
    # all — RM-M-MECH's D-M-MECH is a real swing door, but that reaches the main floor's
    # segment, not this one.
    #
    # South is the only face there is: north is W-S-N3B and west is W-S-W1B, both exterior,
    # and east is W-S-CH-W with FX-S-BATH1-SH's flange on the far side of it. Panel in
    # W-S-CH-S's bathroom face, at y 32'-10 1/2".
    #
    # 14x29 rather than the 14x14 the suite bath's tub takes: this is a reach-in into a
    # 2'-2 1/8" deep shaft that carries live pipe, not a look at one trap. Base 2'-0" puts
    # the opening at 2'-0"..4'-5" — the same band FURN-M-BATH1-AP uses on the WC carrier.
    # Shifted 8" east: centred x 2'-0" (opening 1'-5"..2'-7"), leaving 2" to the shaft's
    # southeast corner and 4 3/4" to the tub's west end. The x=1'-0" riser is now 5" west of
    # the opening's west jamb; it remains reachable just inside the shaft.
    #
    # NOT sized for the ceiling: PR-S-BATH1-VENT and PR-S-SUITEBATH-VENT tie in at
    # elevation 9'-3"..9'-5", which no wall panel at standing height reaches. Those stay a
    # ceiling job from the storey above. Standing room in front is 1'-7 1/4", between
    # FX-S-BATH1-WC's clearance zone and the wall face — enough to kneel square to the
    # opening, and the FH-S-BATH1 mat stops at y 31'-3" so nobody kneels on it.
    Furniture(uid="7MW8644E5H", tag="FURN-S-BATH1-CH-AP", type_ref="FT-ACCESS-PANEL-1429", room="RM-S-BATH1",
              mount=Mount(kind=MountKind.WALL, elevation=ft(2), recessed_into_host_surface=True),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-CH-S", face="left", distance_from_start=inch(9),
                  normal_gap=inch(-0.5), rotation_offset=deg(-180)))),

    # ** THE AIR HANDLER'S SERVICE OPENING, AND THE OLD BOX HAD NOTHING LIKE IT. **
    # Until 2026-09-04 the only way into System 1's machine was REG-S-HP-RET's hinged
    # filter face — fine for a filter, useless for a coil, a blower wheel, a condensate
    # trap or a control board. This is a 20 x 13 hinged panel in SF-S-HP1's underside
    # directly BELOW EQ-S-HP1-AH, in RM-S-NCLOSET where a stepladder can stand.
    #
    # ** IT IS THE LID ON A FRAMED HOLE, AND THE HOLE IS AUTHORED. ** `AO-S-HP1-AP` in
    # plan/storeys/second.py is the `SoffitOpening` this covers: 30" x 29" clear at
    # x 18'-10"..21'-4" by y 31'-10"..34'-3", made by heading off SF-S-HP1's rung at
    # y=33'-0 5/8" between the rungs either side of it. This panel is drawn to the same
    # rectangle, so the two agree by construction rather than by a comment.
    #
    # It was 20 x 13 for one day — the clear bay between two rungs, which is a hand and a
    # filter. The engine had no way to say "cut the rung" then; it does now, and the
    # opening reaches the air handler's north two-thirds AND its return face at y=34'-0",
    # which is where the filter rack, the coil, the blower and the condensate trap are.
    #
    # elevation 7'-3" is the box's finished underside, hand-coupled to the 21" drop the
    # same way REG-S-HP-RET's is.
    Furniture(uid="J49Q7W1RWR", tag="FURN-S-NCLOSET-AP", type_ref="FT-ACCESS-PANEL-CLG-3029",
              room="RM-S-NCLOSET", position=pt(ft(20, 1), inch(396.5)),
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 3))),

    # The second storey's two closets, same rule as the main floor's pair above.
    # RM-S-CLOSET: 94 3/4" of clear wall on the north side (W-S-CLN, face y 12'-2 5/8");
    # an 84" run leaves 5 3/8" either end clear of W-S-DC1's jamb.
    Furniture(uid="CMWJ7Q6Y7H", tag="FURN-S-CLOSET-SHELF", type_ref="FT-CLOSET-SHELFROD-84",
              room="RM-S-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(66)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS2", face="left", distance_from_start=inch(50),
                  normal_gap=inch(0.4375), rotation_offset=deg(0)))),
    # RM-S-NCLOSET is the odd one: 40 3/4" wide, so a 16" shelf plus a hang rod would leave
    # under 2' of standing room in front of it. It takes the 12"-deep LINEN shelf instead,
    # no rod — this closet is off the north hall and stores goods, not coats.
    Furniture(uid="XBBM4XVJ8Q", tag="FURN-S-NCLOSET-SHELF", type_ref="FT-CLOSET-SHELF-36",
              room="RM-S-NCLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(66)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-N1B", face="left", distance_from_start=inch(23.25),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    # BED1 stays in the southern part of its bay; its west-side wardrobe and north-side desk
    # leave the bed's modeled access zones open.
    Furniture(uid="3R2F3FARR7", tag="FURN-S-PLANT-POT2-COPY", type_ref="FURN-PLANT-18", position=pt(m(3.87087), m(0.600137)), room="RM-S-PLANT"),
]
# The attic study uses the same compact work-and-meeting program as the second-storey
# study, but the stair opening occupies the north side of the room.
#
# ** THE WHOLE PROGRAM SITS WEST, AND THE RAKE IS THE ONLY REASON. ** At 6:12 off a rafter
# plate the roof underside east of the ridge is `1 1/2" + (36' - x)/2`, so a station near the
# east end has well under 1'-6" of roof over it. Furniture does not fit under a rake by
# being pushed against it.
#
# The furniture answers to the same line every attic station does. A 30" work surface with a
# person seated at it wants ~5'-6" of ceiling, which arrives at 10'-3" from the eave, i.e.
# x <= 25'-9" on this side. So:
#   * the DESK PAIR takes the room's WEST LEG (x 18'-4"..21'-2", the full y 0..9'-4" strip
#     west of FO-A-STAIR), turned to run its 4'-0" length in y. At x=19'-8" the ceiling is
#     8'-3 1/2" — the best in the room — and it is the one part of the study that is neither
#     under the rake nor over the well. The vestibule's freed footprint next door
#     (x 21'-2"..22'-8", W-A-VE/W-A-VN/D-A-VEST, deleted the same pass) is what makes the
#     leg wide enough to work in.
#   * the TABLE SET goes to x=26'-0" (5'-1 1/2" of ceiling) with its two chairs flanking it
#     in Y rather than in X — north and south of the table on the same x, so both sit under
#     the same height instead of one of them being 2'-6" further down the slope. That is the
#     arrangement change; the catalog family is still Study 2's. Its 3'-0" chair surround
#     starts at x 22'-6", clear of the desk pair — `integrity.placeable_recommended_
#     clearance_conflict` is what settled that number.
ATTIC_PLACEABLES = [
    Furniture(uid="P8A4CASE01", tag="FURN-A-STUDY-BUILTIN", type_ref="FT-A-STUDY-BUILTIN",
              room="RM-A-STUDY",
              location=Location(attachment=WallAttachment(
                  wall_ref="W-A-SN-REAR", face="right", distance_from_start=inch(52.0625)))),
    # y=4'-6" and not 5'-0": D-A-STUDY's leaf sweeps x 18'-8 7/8"..21'-2 7/8", y 6'-10" to
    # the wall, and a desk at 5'-0" put 2" of itself under it (`integrity.door_swing_conflict`).
    Furniture(uid="DAK701AAAA", tag="FURN-A-STUDY-DESK", type_ref="FURN-DESK-48",
              room="RM-A-STUDY", position=pt(m(5.90037), m(0.812811)), rotation=deg(90)),
    Furniture(uid="CAK701AAAA", tag="FURN-A-STUDY-DESK-CHAIR", type_ref="FURN-DESK-CHAIR",
              room="RM-A-STUDY", position=pt(m(6.14764), m(0.782959)), rotation=deg(-90)),
    Furniture(uid="TAK701AAAA", tag="FURN-A-STUDY-TABLE", type_ref="FURN-DINING-2-36",
              room="RM-A-STUDY", position=pt(m(7.83976), m(0.671138))),
    # The west-end seat, TUCKED IN rather than pulled out. A UI drag left its back 8 1/2"
    # inside the desk's 3'-0" pull-out zone (which ends at x 23'-4 1/4"); that zone exempts
    # the desk's OWN chair, not a table chair. x=24'-4" clears it by 3/4" and slides the
    # seat under the table's west end.
    Furniture(uid="CAK702AAAA", tag="FURN-A-STUDY-CHAIR1", type_ref="FURN-DINING-CHAIR",
              room="RM-A-STUDY", position=pt(ft(24, 4), ft(2, 2)), rotation=deg(90)),
    Furniture(uid="CAK703AAAA", tag="FURN-A-STUDY-CHAIR2", type_ref="FURN-DINING-CHAIR",
              room="RM-A-STUDY", position=pt(ft(26, 6), ft(4, 2)), rotation=deg(0)),
    # --- the guest studio's wet bar ---------------------------------------
    # ** IT MOVED OFF THE CENTRE WALL ONTO W-A-BATH-S, 2026-09-09. ** The bar used to be three
    # pieces on W-A-C2's west face — a base, a fridge and a sink — with D-A-STUBATH swinging
    # out into them, so a person at the bowl blocked the bathroom door. It is now a SUNNERSTA
    # kitchenette against the bath wall with the door slid east past it, which is the owner's
    # own proposal. FX-A-STUDIO-BAR-SINK is in plan/fixtures.py; power is off
    # ED-A-STUDIO-BAR-GFCI, which came across with it (plan/electrical_attic.py).
    #
    # ** THE FRIDGE GOES UNDER THE KITCHENETTE, AND IT HAD TO GET SMALLER TO DO IT. **
    # APPL-BAR-FRIDGE-24 is 24" deep and 34" tall against a 22"-deep SUNNERSTA top, so the
    # old catalog envelope cannot go in the cavity the unit is built around. It is retyped to
    # APPL-BAR-FRIDGE-CUBE-19 (plan/appliance_types.py), keeping tag and uid so the GlobalId
    # follows the element. ** THE CUBE'S DIMENSIONS ARE PROVISIONAL: ** the unit's clear
    # opening is unmeasured (plan/fixtures.py lists all three open measurements), so measure
    # it before buying — if a cube will not fit, the fridge becomes a free-standing piece
    # again and needs a home, and there is no wall left in this room that takes one well.
    #
    # c/l (10'-10 7/16", 16'-2 5/8") sits it under the unit's WEST end — x 10'-0 15/16"..
    # 11'-7 15/16" inside the unit's own footprint, on its centreline in y.
    # That is the LOW end of the rake and deliberately so: the fridge and the storage take the
    # 5'-6" end and the bowl and the person using it take the 7'-2" end.
    #
    # ** SINK AND FRIDGE, AND NOTHING THAT COOKS: ** a range or a cooktop here turns the
    # studio into a second dwelling unit and brings IRC R302.3's two-family separation down on
    # the attic floor and the centre wall. Both types carry the same warning and it is written
    # three times on purpose — the SUNNERSTA is sold in markets that offer a hob for it. Do
    # not buy one.
    #
    # `rotation=deg(-90)` turns its door to open into the room off the unit's west end; the
    # footprint is square, so only the plan symbol and that door swing read it. Leaving
    # W-A-C2's west face is what unburied REG-A-HP-WEST (plan/mep_registers.py), the floor
    # boot that answers R303.1 Exception 1 for this room and had a fridge standing on it.
    Appliance(uid="7B10E5QBCF", tag="APPL-A-STUDIO-FRIDGE", type_ref="APPL-BAR-FRIDGE-CUBE-19",
              room="RM-A-STUDIO", position=pt(inch(130.4375), inch(194.625)),
              rotation=deg(-90)),
    # ** THE WET BAR IS ONE PRODUCT NOW, AND IT IS ON THE BATH WALL. ** The owner chose an
    # IKEA SUNNERSTA mini-kitchen (44 1/8" x 22" x 54 3/4", $149, article 40313363), which
    # replaces the house-local 24"x18" base that used to stand on W-A-C2's west face with
    # D-A-STUBATH swinging into it. The whole derivation is on FT-STUDIO-KITCHENETTE-4422 in
    # plan/furniture_types.py; read it before moving this.
    #
    # ** THE TOP IS NOT REVERSIBLE, AND THAT PICKED THE WALL. ** The bowl is at the unit's
    # right-hand end as you face it. On the centre wall that puts the bowl at the SOUTH end,
    # roughly 76" of trap arm from the bath vent against Table 1002.2's 60" for 2". On
    # W-A-BATH-S it puts the bowl at the EAST end, nearest the stack — which is what the short
    # revent in plan/mep_venting.py hangs on and what takes the arm well inside 60".
    #
    # c/l (11'-9 7/16", 16'-2 5/8"): back on W-A-BATH-S's 17'-1 5/8" face, occupying
    # x 9'-11 3/8"..13'-7 1/2" and y 15'-3 5/8"..17'-1 5/8". ** IT SAT 4 1/2" FURTHER EAST
    # FOR ONE BUILD ** and moved west when `structural.door_framing_module` put D-A-STUBATH's
    # only legal centre at 14'-11 1/2" (storeys/attic_studio.py): the door's station is on a
    # 16" module and the unit's is not, so the unit is what yields. Its west end still stands
    # 3 7/8" clear of the wall's own west end at 9'-7 1/2". Rotation is omitted, i.e. `deg(0)`,
    # which backs it NORTH onto the wall — local +y is the object's BACK
    # (`resolve/placeables.py`), a convention all three bar pieces used to get backwards.
    # Its east end leaves 4" to D-A-STUBATH's arc (storeys/attic_studio.py).
    #
    # The tag and the uid are kept, so the element's GlobalId follows it across the retype the
    # way RM-A-STUDIO kept CAR401AAAA. BK-A-BATH-S (plan/backing.py) is the anchor rail IKEA
    # requires; a 54 3/4" unanchored flat-pack is not buildable.
    Furniture(uid="4GVQGBXMS3", tag="FURN-A-STUDIO-BAR-BASE", type_ref="FT-STUDIO-KITCHENETTE-4422",
              room="RM-A-STUDIO", position=pt(inch(141.4375), inch(194.625))),
]

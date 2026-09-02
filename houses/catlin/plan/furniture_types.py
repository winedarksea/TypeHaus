"""House-local furniture catalog for items specific to the Catlin plan.

Only items *made to fit this house* belong here: nothing here is a product anyone would
reuse across plans (the test for house-local). Curtain rods and access panels are
``plan_symbol=None`` on purpose — a rod at 7'-0" and a panel in a wall face are not
floor-plan objects, so drawing a glyph would put a rectangle where the room is empty. They
exist to be *scheduled and billed*, and to sit in 3D at the height someone builds them at.
"""

from __future__ import annotations

from typehaus.model import (
    ClearancePolicy,
    ClearanceZone,
    Footprint2D,
    FurnitureType,
    Mount,
    MountKind,
    ft,
    inch,
    m,
    pt,
)

_WALL_MOUNT = Mount(kind=MountKind.WALL)

_ROD_SOURCE = ("plans/TODO.md — window treatments. Width is the rod, not the opening: a "
               "rod runs past the RO on both sides so the stack sits on wall, not glass.")
# 48" covers every main-storey window in the house — the widest RO on a rod is 30"
# (WT-3048), which leaves 9" of stackback each side. 84" is D-M-BALC's french pair (60"
# RO, 12" each side). Depth is the bracket projection, height the rod and finial.
CURTAIN_ROD_48 = FurnitureType(
    tag="FT-CURTAIN-ROD-48", name='Curtain rod, 48"',
    footprint=(inch(48), inch(4)), height=inch(2),
    plan_symbol=None, mount=_WALL_MOUNT, source=_ROD_SOURCE,
)
CURTAIN_ROD_84 = FurnitureType(
    tag="FT-CURTAIN-ROD-84", name='Curtain rod, 84"',
    footprint=(inch(84), inch(4)), height=inch(2),
    plan_symbol=None, mount=_WALL_MOUNT, source=_ROD_SOURCE,
)
# The porch rods are a different product, not a longer version of the same one: outdoor
# fabric on a pillar-to-pillar span, so the rod is heavier, the finish is exterior, and the
# span is set by the structure (a front pillar bay) rather than by an opening.
CURTAIN_ROD_OUTDOOR_114 = FurnitureType(
    tag="FT-CURTAIN-ROD-OUTDOOR-114", name='Outdoor curtain rod, 114"',
    footprint=(inch(114), inch(6)), height=inch(2),
    plan_symbol=None, mount=_WALL_MOUNT, source=_ROD_SOURCE,
)
# The porch's two SIDE bays. Same product as the 114" front pair, cut to the 8'-8" side
# run less its corner gaps.
#
# A continuous outdoor U-rod (straight track + corner connectors, one curtain) was tried
# first and rejected: PT-SG-BF2 sits ON the front guard line at x=18'-0" (5 1/2" square,
# y -9'-8 3/4" to -9'-3 1/4"), leaving only a quarter inch of bracket clearance past it in
# weather, and the side pillar line (x 8'-0"/28'-0") is 6" outboard of the guard, dropping
# a pillar-hung curtain outside the 42" railing. Pulling the path inboard to answer both
# costs 6" of the porch on three sides and three new types. Four bay panels — front split
# by PT-SG-BF2, one per side — is what the structure actually offers. Recorded in
# plans/TODO.md so the decision is not re-litigated from the product alone.
CURTAIN_ROD_OUTDOOR_98 = FurnitureType(
    tag="FT-CURTAIN-ROD-OUTDOOR-98", name='Outdoor curtain rod, 98"',
    footprint=(inch(98), inch(6)), height=inch(2),
    plan_symbol=None, mount=_WALL_MOUNT, source=_ROD_SOURCE,
)

_PANEL_SOURCE = ("plans/TODO.md — plumbing access. Framed metal panel in a finished wall "
                 "face; size is the clear opening, depth the frame's projection.")
# 14x14 is the tub waste-and-overflow size, 14x29 the wall-hung WC carrier size — the
# carrier is a tall frame and the panel has to reach the whole of it.
ACCESS_PANEL_1414 = FurnitureType(
    tag="FT-ACCESS-PANEL-1414", name='Access panel, 14" x 14"',
    footprint=(inch(14), inch(1)), height=inch(14),
    plan_symbol=None, mount=_WALL_MOUNT, source=_PANEL_SOURCE,
)
ACCESS_PANEL_1429 = FurnitureType(
    tag="FT-ACCESS-PANEL-1429", name='Access panel, 14" x 29"',
    footprint=(inch(14), inch(1)), height=inch(29),
    plan_symbol=None, mount=_WALL_MOUNT, source=_PANEL_SOURCE,
)

# --- built-in millwork ----------------------------------------------------------------
#
# The shelf that closes RM-S-BATH1's tub alcove (2026-08-21). FX-S-BATH1-SH is a flanged
# 60x30 insert, which wants studs on three sides, and it only had two: the chase wall to the
# west and the exterior wall to the north, with its east end standing open in 1'-8 7/8" of
# dead floor. This carcass IS that third side — its west panel is the alcove's east return,
# with a 2x4 framed behind it to nail the flange to — so one built article turns a framing
# defect and an unreachable pocket into the only storage within reach of the tub.
#
# The two dimensions are the alcove's, not a catalog's: 30" deep is the tub's own depth, so
# the two front faces land on one line, and 84" is the tub surround's head, so the north
# wall reads as a single built element from floor to 7'-0" instead of a box beside a tub.
#
# ``plan_symbol="bookcase"`` is not an approximation here — ``shelving(shelves=5)`` builds
# two side panels, a back and five shelves, which is literally what this is.
#
# No ``clearances``: per the casework rule, a built-in's back is the wall and its ends are
# its neighbours, and the floor in front of it is the same floor you stand on to use the
# tub.
BATH1_SHELF_2030 = FurnitureType(
    tag="FT-BATH1-SHELF-2030", name='Bath 1 alcove shelf, 20" x 30"',
    footprint=(inch(20), inch(30)), height=inch(84),
    storage=True, work_surface=False, plan_symbol="bookcase",
    source="Site-built millwork, not a catalogue bookcase: a 3/4\" plywood carcass scribed "
           "to the east end of RM-S-BATH1's tub alcove, whose WEST panel carries "
           "FX-S-BATH1-SH's east flange over a framed 2x4 and is what makes that insert a "
           "legitimate three-wall install. Depth matches the tub (30\"), height matches the "
           "surround head (84\"); the 7/8\" of slack at the east wall is taken as scribe.",
)


# --- RM-M-STUDY, the call booth --------------------------------------------------------
#
# The house's smallest habitable room and its only windowless one, finished as a booth for
# video calls and homework. Both pieces are house-local by the test at the top of this file —
# each is scribed to one 4-foot box, and nobody reuses either.
#
# Bench along the NORTH wall running east-west, facing a desk in the SOUTH-WEST corner: you
# enter, step into the pocket east of the desk, sit, and slide west. Two things follow:
#
#   1. Bench and desk face each other across the room's SHORT dimension (44 1/8"), so their
#      depths compete. The bench is 17" deep (a full seat depth against a back), leaving
#      7 1/8" of clear floor to the desk front. Your feet go UNDER the desk — the top is a
#      cantilevered slab on cleats, no leg or stretcher at the front.
#   2. The bench is a floor-standing plinth, scribed to the wainscot at its back and the
#      wall at each end — NOT fastened to its wall, W-M-HS4. That is the only legal answer:
#      D-M-LAUN's leaf parks inside W-M-HS4 between x 12'-4" and 16'-5", and
#      `mep.pocket_occupancy` refuses any fastener, device or pipe in that cavity. This
#      bench covers x 13'-8 3/4"..17'-7 3/4", so a cleat screwed to the wall would FAIL.
#
# Every dimension below is derived from `out/model.json`: the room's four resolved gypsum
# faces were x 13'-8" .. 17'-8 5/8", y 18'-4" .. 22'-1 5/8" — a 48 5/8" x 45 5/8" clear box,
# ~15.4 sf — with W-M-LS/W-M-CLN2 as INT_2X4_STAGGERED_DOUBLE_GWB. **STALE:** both walls are
# now the thinner single-gwb INT_2X4_STAGGERED_GWB, opening the box ~5/8" per retyped face
# (~49 1/4" x 46 1/4"), but the STUDY_BENCH footprint, wainscot-return scribe and seat-length
# math below are still cut to the OLD box. Re-derive from a fresh `out/model.json` (never
# `Room.clear_face`, see below) before this casework is built.
# ** DO NOT MEASURE OFF `Room.clear_face`: **
# `resolve/rooms.py::_lining_inset` insets a claimed face by one uniform 0.635" whatever the
# wall actually is, so it still reports the 4'-8" x 4'-4" axis box and the published 19.3 sf
# (plans/TODO.md, the RM-S-PLANT write-up). The sauna benches in plan/placeables.py are
# dimensioned the same way, off liner faces.
#
# Then the millwork is set against the LINING, not the gypsum: WP-M-STUDY-WAINSCOT keeps all
# four walls and resolves 3/4" thick, so the box the joiner scribes to is 3/4" smaller on
# every face: x 164 3/4" .. 211 7/8" and y 220 3/4" .. 264 7/8" off the house origin — a
# 47 1/8" x 44 1/8" lined box. Lining the box first and setting the built-ins against that
# is how a shop builds this, and it is why ~20 sf of wainscot lands behind the two pieces
# on purpose rather than being cut around them.
#
# No `clearances` on either, per the casework rule BATH1_SHELF_2030 states: a built-in's
# back is the wall, its ends are its neighbours, and the floor in front of it is the floor
# you stand on to use it. A declared zone here would be the room.
# ** SEAT DECK IS 16", NOT 18" — THE 2" IS THE CUSHION. ** A 3" HR-foam cushion settles
# ~1 1/2" under an adult, so an 18" deck seats you at ~19 1/2". Compressed-seat-to-desk-top
# wants 11"-12" (a 29" desk against the 17"-18" an office chair is used at); 16" + 1 1/2" =
# 17 1/2" against FT-STUDY-DESK's 29 1/2" top is 12", exact.
#
# The desk stays at 29 1/2" rather than raising to 31" to close the same gap: 31" is above
# the 28"-30" seated-laptop band and buries ED-M-STUDY-RC1/-RC2/-DATA1, all three sited at
# 32" (2 1/2" over a 29 1/2" top). Lower the deck, never raise the desk — if the cushion is
# ever re-specced thicker than 3", this number is what moves.
STUDY_BENCH = FurnitureType(
    tag="FT-STUDY-BENCH", name='Study booth bench, 47" x 17"',
    footprint=(inch(47), inch(17)), height=inch(16),
    storage=False, work_surface=False, plan_symbol="sauna-bench",
    source="Site-built walnut millwork scribed to RM-M-STUDY's NORTH wall, running "
           "east-west. 47\" of the 47 1/8\" between the wainscot's west and east returns "
           "(1/16\" of scribe each end), 17\" deep, and a 16\" seat DECK that seats you at "
           "17 1/2\" once a 3\" cushion takes an adult — see the note above; on a bench the "
           "deck height is the cushion's business. ** ITS BACK IS NOT A "
           "PART: ** the 36\" walnut wainscot already on that wall is the back rail over "
           "an 18\" seat, which is why the bench runs the full length and the desk does "
           "not. In a booth, back support beats desk width. ** IT IS A FLOOR-STANDING "
           "PLINTH, NOT WALL-HUNG: ** W-M-HS4 behind it is the untouched 2x4 partition "
           "carrying a stack edge, and nothing here asks it to hold a cantilever.",
)

# ``plan_symbol="wall-desk"`` (``slab(apron=True, legs=False, modesty_panel=False)``), not
# "desk" (which plots four corner legs and a back panel): this top is cantilevered off
# cleats with the knee space open to the wall, and nothing stands on the floor.
# FT-STUDY-DESK-LEAF below needs the same symbol for a harder reason: a leaf with a leg or a
# modesty panel cannot fold.
STUDY_DESK = FurnitureType(
    tag="FT-STUDY-DESK", name='Study booth desk top, 29" x 20"',
    footprint=(inch(29), inch(20)), height=inch(29.5),
    storage=False, work_surface=True, plan_symbol="wall-desk",
    source="Site-built walnut millwork, fixed (not a fold-down leaf), scribed into "
           "RM-M-STUDY's SOUTH-WEST corner — the west wall's wainscot at one end, the "
           "south wall's behind it, 1/16\" of scribe at each. 20\" deep at 29 1/2\", "
           "cantilevered off cleats screwed through W-M-CLN2's staggered studs, so the "
           "knee space is open to the wall and the seated occupant's feet pass under it. "
           "** MOVED TO THE CORNER ON THE OWNER'S REVIEW: ** at its first position, "
           "centred on the south wall, its east end stood in D-M-STUDY's opening and you "
           "entered past it. In the corner it stops 18 7/8\" short of the east wall, "
           "which is the pocket you step into.",
)


# ** THE FOLD-DOWN LEAF. ONLY THE EXTRA LENGTH FOLDS, AND THAT IS THE DESIGN. **
#
# The ask was a desk long enough for two that folds to the wall and still lets one person
# get in and out easily. A fold-EVERYTHING desk would have to be folded and unfolded every
# time anyone walked in, for the 95% of days one person works here alone. Folding only the
# 18" the second person needs keeps the daily room exactly as it is — a fixed 29" desk and
# the 18 7/8" pocket — and buys the two-person case on demand.
#
# ** 47" IS THE ROOM'S CEILING, BELOW EVERY PUBLISHED TWO-PERSON MINIMUM. ** 29" fixed +
# 18" leaf = 47", the full lined box, 23 1/2" each — a squeeze for two people around ONE
# laptop, not for two people each working; trade literature wants 30" per person (a
# comfortable two-person desk is 72" x 30"), 24" is where "elbows touch" starts. Do not
# read the leaf as a second workstation.
#
# ** DEPLOYED, THIS ROOM HAS NO FLOOR, AND THAT IS FINE. ** It holds y 220 3/4"..240 3/4"
# across the pocket, the same 7 1/8" slot between desk front and bench front as the fixed
# desk — a diner booth: both people sit, THEN the leaf comes down. D-M-STUDY swings OUT of
# the booth (`swing_clearance` resolves to x 216"..246", entirely east of the room), so a
# deployed leaf cannot block the door and either occupant can lift it one-handed, seated.
# Re-check that swing before anything here is re-hung.
#
# ** MODELLED DEPLOYED — THE STOWED-STATE LIE WORTH TELLING. ** A Furniture is a footprint
# plus a height; there is no way to say "a 20" panel hanging on a wall between 8" and 28"".
# Deployed is the state a plan drawing shows and the WORST case for every collision check.
# Stowed it is a flat panel projecting ~3" from the south wall, top edge at 28", bottom at
# 8" — inside WP-M-STUDY-WAINSCOT's 36" field, which is why it folds DOWN not up (folded UP
# it would cut 12" above the wainscot cap and bury ED-M-STUDY-RC1 at 32").
#
# ** THE HARDWARE, AND WHY IT IS NOT A MURPHY-DESK KIT. ** No purchasable murphy-desk
# mechanism is rated for this — the Create-A-Bed kit (Rockler #78834) is 50 lb, a laptop and
# a notebook, not two adults leaning. Built from a pair of Hafele/Hebgo 287.43.419
# heavy-duty folding table brackets (18 7/8" projection against this 20" leaf, 1100 lb/pair,
# auto-locking, released by light upward pressure on the locking arm). NOT gas struts: Blum
# Aventos / Hafele Free Flap are rated to LIFT a flap's weight, never validated to carry
# load downward when open. Soft-close, if wanted, is a Sugatsune EBD damper added to a
# load-bearing bracket, never a flap fitting standing in for one.
#
# ** RACKING IS THE FAILURE MODE, NOT CAPACITY — THE FIX IS CONTINUITY. ** Two brackets are
# two pins in a line, a hinge that parallelograms sideways when someone leans on a corner.
# So: a continuous ledger the full 18", a full-length piano hinge to it, and the leaf's west
# edge registering into FT-STUDY-DESK's east end on bullet catches, triangulating it against
# the one thing in the room that cannot move. A 1 1/2" solid walnut leaf this short needs no
# drop leg, which would defeat the point of the pocket.
#
# ** THE LEDGER IS WHERE THIS WALL BITES BACK. ** W-M-CLN2 is INT_2X4_STAGGERED_GWB, and it
# decouples its two faces because no stud touches both — a ledger lagged through the finish
# into every stud it crosses would either miss (1 3/8" of gypsum plus 3/4" of wainscot
# before a lag reaches wood) or, through-bolted to the far-face studs, short the decoupling
# this wall was retyped for. The detail is blocking LET IN AT FRAMING, laid FLAT: study-face
# studs occupy 0"..3 1/2" of the 5 1/2" plate and living-side studs 2"..5 1/2", so a 2x4 on
# the flat sits 0"..1 1/2" and clears the far studs by 1/2". The bench carries this same
# blocking; the leaf needs it too, in before the rock goes on.
FOLD_LEAF = FurnitureType(
    tag="FT-STUDY-DESK-LEAF", name='Study booth desk leaf, 18" x 20", fold-down',
    footprint=(inch(18), inch(20)), height=inch(29.5),
    storage=False, work_surface=True, plan_symbol="wall-desk",
    source="Site-built walnut fold-down leaf filling RM-M-STUDY's entry pocket, hinged to "
           "let-in blocking on the south wall and carried by a pair of Hafele/Hebgo "
           "287.43.419 folding table brackets (18 7/8\" projection, 1100 lb/pair, "
           "auto-locking). Deployed it butts FT-STUDY-DESK's east end on bullet catches for "
           "47\" of continuous top; stowed it hangs flat inside the wainscot field, 8\" to "
           "28\", and the pocket is clear floor again. ** MODELLED DEPLOYED: ** that is the "
           "worst case for collision and the state a plan draws.",
)


# --- the media room's U sectional ---------------------------------------------------------
#
# House-local for the reason at the top of this file: it is made to fit this room. 11'-0" of
# back run across a 16'-6" box, 8'-0" of arms reaching toward a 98" screen on the north wall,
# 3'-0" seat depth. Nobody reuses that across plans.
#
# ** IT CANNOT BE THREE CATALOG PIECES. ** FURN-SOFA-84 and FURN-LOVESEAT-60 each declare a
# 2'-6" ``front_zone``, so three of them in a U would each stand in the next one's declared
# walk path (`integrity.clearance_encroachment`, three times over) for a shape whose whole
# point is that the open middle IS the walk path. FURN-SECTIONAL-L's outline is generated by
# ``sectional_points``, hard-coded to an L (a back run plus one chaise); a U is not a
# parameter of it.
#
# So: an explicit ``footprint_shape``, which `resolve/placeables.py` prefers over the
# rectangular ``footprint``, and NO clearance zones at all. The empty ``clearances`` is the
# decision, not an omission — the zone a U wants is the well it encloses, and a ``front_zone``
# projecting off its own back run would land inside its own arms.
#
# The 3D massing draws the "sectional" glyph, which is L-shaped: the same acknowledged
# approximation plan/placeables.py already accepts for the armchair. The *plan* outline —
# what every clearance and collision rule measures — is the true U below.
#
# Every seating family in `model/placeable_symbols/_families.py` — `seating` and
# `sectional` alike — puts its back band at ``+y`` and faces ``-y`` (`plan/placeables.py`
# states the convention). The ring below is authored to it: back run at +y, opening toward
# -y, with FURN-B-PLAY-SECTIONAL carrying ``rotation=deg(180)`` to point the whole thing
# north. `footprint_shape` is read only by `resolve/placeables.py:_local_footprint` for
# collision and wall attachment, never by the symbol that draws — so a ring authored against
# the wrong convention draws a body with its back to the screen with nothing to catch it.
_U_WIDTH = ft(11)
_U_DEPTH = ft(8)
_U_SEAT = ft(3)  # back run and arm depth alike

_U_HALF_W = _U_WIDTH.inches / 2.0
_U_HALF_D = _U_DEPTH.inches / 2.0
_U_ARM = _U_SEAT.inches

MEDIA_SECTIONAL_U = FurnitureType(
    tag="FT-SECTIONAL-U-MEDIA", name="U sectional, 11'-0\" x 8'-0\"",
    footprint=(_U_WIDTH, _U_DEPTH), height=ft(2, 10), plan_symbol="sectional",
    # Back run at +y, opening toward -y: the same convention `seating` and `sectional` draw
    # to, so the outline and the body turn together under one rotation. Walked as one ring
    # from the west arm's open tip: across the arm's end, up its inner face, along the front
    # of the back run, down the east arm's inner face, out its tip, and back along the
    # sectional's own back and west side.
    footprint_shape=Footprint2D(points=(
        pt(inch(-_U_HALF_W), inch(-_U_HALF_D)),
        pt(inch(-_U_HALF_W + _U_ARM), inch(-_U_HALF_D)),
        pt(inch(-_U_HALF_W + _U_ARM), inch(_U_HALF_D - _U_ARM)),
        pt(inch(_U_HALF_W - _U_ARM), inch(_U_HALF_D - _U_ARM)),
        pt(inch(_U_HALF_W - _U_ARM), inch(-_U_HALF_D)),
        pt(inch(_U_HALF_W), inch(-_U_HALF_D)),
        pt(inch(_U_HALF_W), inch(_U_HALF_D)),
        pt(inch(-_U_HALF_W), inch(_U_HALF_D)),
    )),
    source=("owner, 2026-08-22 — a U sectional for RM-B-PLAY-N. Sized to the room: 11'-0\" "
            "of back run in a 16'-6\" box leaves 2'-9\" either side, and 8'-0\" of arms "
            "puts the back run 11'-13' off a 98\" screen. Seat depth 3'-0\", overall height "
            "2'-10\" to match the catalog's seating."),
)


# --- the media room's bookcases -----------------------------------------------------------
#
# House-local because it is a HEIGHT made to fit one room, not a product cloned from a
# catalog: the owner asked for the theatre's shelving to run up near the ceiling, and the
# number that answers it comes from RM-B-PLAY-N's own section, not a product page.
#
# The room's measured clear height is 8'-0" under SL-M-DECK (`code.R305_ceiling_height`) —
# NOT the 8'-3 1/2" plan/placeables.py quoted from an older revision of the deck. 7'-6"
# leaves a 6" reveal, which is the reason for that number and not a rounding:
#   * it is scribe room. A site-built case run tight to a poured deck has nowhere to go if
#     the soffit is out of level, and a basement deck is never dead flat.
#   * it keeps the case tippable. A 90" x 12" carcass swings up on a 90 3/4" diagonal, so it
#     can be built flat on the floor and stood — at 7'-10" the diagonal is 94 3/4" in a 96"
#     room and it has to be assembled standing.
# Same 2'-8" x 1'-0" footprint as the library case it replaces, so every plan dimension in
# plan/placeables.py — the clearances off D-B-PLAY's swing, the backs on the 18'-3 3/8"
# face — is unchanged by the swap.
#
# ** ANTI-TIP IS NOT OPTIONAL AT THIS HEIGHT ** and is easy here: the south wall is W-B-CE,
# INT_2X6_STAGGERED_PLUMBING, so there are real studs to catch. That is worth saying because
# the room's OTHER wall — the north one the screen hangs on — is an 8" pour that takes
# anchors instead, and someone reading only that note could reach for the wrong fastener.
THEATER_BOOKCASE = FurnitureType(
    tag="FT-BOOKCASE-32-90", name='Bookcase, 2\'-8" x 7\'-6"',
    footprint=(ft(2, 8), ft(1)), height=ft(7, 6),
    plan_symbol="bookcase", storage=True,
    source=("owner, 2026-08-24 — the theatre's shelving taken up near the ceiling. The "
            "library's FURN-BOOKCASE-32 at 6'-0\" in the same 2'-8\" x 1'-0\" footprint, "
            "stretched to 7'-6\": a 6\" reveal under RM-B-PLAY-N's measured 8'-0\" clear, "
            "which is scribe room for an out-of-level deck and keeps the 90\" x 12\" "
            "carcass tippable on its 90 3/4\" diagonal. Anti-tip strap or cleat into "
            "W-B-CE's studs at every case."),
)

# --- kitchen millwork (the peninsula/pantry-room rework) --------------------------------
#
# FT-KIT-COLDSTORE-FILLER (6 1/4" of scribed panel filling the remainder of a 72" cold bay
# after the Frigidaire Professional pair, 32 7/8" each) is RETIRED, along with its one
# instance: the pantry ROOM's south partition now takes 4 3/4" off that run, leaving a
# 65 3/4" bay — exactly two appliance widths, no remainder to fill. Deleting the type rather
# than leaving it unused is deliberate: an unreferenced house-local type reads as a size
# someone might reach for, and this one was arithmetic, not a product.


# The over-appliance box the retired CASE-OVER-36 can no longer be. Two 36" boxes need 72";
# the bay is 65 3/4". 32 7/8" is not a cabinet size and never will be — it is an APPLIANCE
# width, carried up so each box's ends land on its own column's sides and the run divides
# with no filler at either end. Same 24" DEPTH as CASE-OVER-36 (see the library type's note:
# base depth so the four fronts line up on x=20'-3 3/8" and the appliances stand 3" proud,
# clearing their own door swing).
#
# ** 21" TALL, HUNG AT 75", NOT 24" AT 72". ** The Frigidaire columns are 71 1/2" high with
# the hinge topping out at 72 1/2", and the manufacturer requires 1" of clearance above
# (`_FRIGIDAIRE_SOURCE`, plan/appliance_types.py). A cabinet bottom at 72" stands 1/2" below
# the hinge and 1 1/2" below the minimum — the door would not open. The kitchen's 96" stacker
# course fixes the box's TOP; 21" is a stock wall-cabinet height, so the bottom lands at
# 75" — 2 1/2" over the hinge, and coincidentally the datum of the 75" flush trim kit
# Frigidaire sells for these columns (deliberately not ordered; see plan/appliance_types.py).
# The cost is 3" of storage in two cabinets, the price of the door opening.
OVER_COLD_3278 = FurnitureType(
    tag="FT-KIT-OVER-COLD-3278", name='32 7/8" over-appliance cabinet',
    footprint=(inch(32.875), ft(2)), height=inch(21), plan_symbol="wall-cabinet",
    storage=True, work_surface=False,
    source=('site-built to the appliance, 2026-08-24 — 32 7/8" is the Frigidaire '
            'Professional column width, not a cabinet module. Millwork, not a catalog box. '
            '21" tall hung at 75": the columns clear 72 1/2" at the hinge and the '
            'manufacturer requires 1" above, so 24" at 72" did not fit.'),
)


# --- the peninsula's mixer garage -----------------------------------------------------
#
# ** WHERE THE STANDING MIXER LIVES, AND IT IS NOT A LIFT. ** The owner's ask — "mixer
# slides straight out onto the peninsula, outlet in the cabinet" — means the mixer sits at
# counter level already, in a cabinet ABOVE the top, sliding straight out onto the counter
# beside it: no lifting a 25 lb machine out of a base cabinet, no holes cut in the stone.
#
# 24" x 24" x 72": it stands ON the peninsula's countertop at 36" and runs to the 108"
# ceiling, so its bottom shelf IS the counter plane and the pull-out slides level. 72" is
# not a stock cabinet height and cannot be — the dimension is "counter to ceiling" in THIS
# room. Built as two ganged boxes behind one face frame is fine and is a shop decision; it
# is modelled as the one article it reads as.
#
# It takes the peninsula's EAST 24", against the east wall, which is what makes it possible:
# a counter-to-ceiling box in the middle of a peninsula would hang from the ceiling with
# nothing behind it. That end was dead frontage before this — a seated diner's legs would
# have gone where FURN-M-KIT-PANTRY-S1 stands — so the cabinet costs no seat. Three stools
# was the honest count before it and still is.
#
# No ``clearances``, per the casework rule; the counter in front of it is the counter.
MIXER_GARAGE_24 = FurnitureType(
    tag="FT-KIT-MIXER-GARAGE-24", name='24" counter-to-ceiling mixer garage',
    footprint=(inch(24), inch(24)), height=ft(6),
    storage=True, work_surface=False, plan_symbol="tall-cabinet",
    source="Site-built millwork, 36\" to 108\" on FURN-M-KIT-PENINSULA's countertop at its "
           "east end, against the east wall. Bottom bay is a HEAVY-DUTY FULL-EXTENSION "
           "PULL-OUT SHELF at the counter plane, rated for a ~30 lb stand mixer plus bowl "
           "and travelling its full depth, so the machine comes out onto the open counter "
           "rather than being lifted. Shelf face flush with the counter so nothing has to "
           "be picked up over a lip. Two GFCI receptacles inside at 42\" "
           "(ED-M-LIVING-KGF4/KMX1) — WIRE THEM BEFORE THE BOX GOES IN. Upper bays are "
           "ordinary adjustable shelving; a roll-up or lift-up door keeps a raised door out "
           "of the room, and is a millwork selection, not a model element.",
)


# --- RM-M-PANTRY's shelf stack --------------------------------------------------------
#
# House-local by the test at the top of this file: 70 1/4" is this room's clear span, wall
# face to wall face, and nothing else.
#
# ** IT IS DESIGNED TO BE STOOD ON, AND THAT IS A STRUCTURAL CLAIM, NOT A FINISH. ** There
# is no model field for "rated to climb", and each of the three mechanisms that could carry
# it is a dead end: ``Furniture`` cannot take ``install_parts`` (only ``PipeAccessory`` and
# ``Appliance`` are ``_install_part_carriers``); an ``Assembly`` is a layered WALL stack,
# not a shelf; and ``FramingSpec.blocking_heights`` is a property of the assembly, so a
# three-sided cleat would mean cloning three assemblies — the exterior truss wall among
# them, re-running its Glaser gate, its energy table and truss_wall_opening_support against
# an unreviewed tag — to bill some 40 bf of 2x4. So the build lives on ``source`` (the
# FT-BATH1-SHELF-2030 precedent) and in notes/pantry_climbable_shelving.md.
#
# ** THE MID-SPAN GABLE IS NOT OPTIONAL, AND STRENGTH IS NO LONGER THE ARGUMENT. ** Shelves
# are 1 1/2" solid white oak (plan/millwork.py, owner stock); the full 70 1/4" span carries
# 250 lb at midspan at only ~650 psi (S = 6.75 in^3), well under a 1,500-2,000 psi flatwise
# allowable. Deflection still fails it: I = 5.06 in^4 gives ~0.223" full-span against this
# shelf's L/360 = 0.195" floor criterion. Gabled to ~34 3/4" it is ~322 psi and ~0.027", not
# close to any limit. The gable also stays because the cleat/blocking layout is built around
# it, and it makes the bottom bay a step rather than a plank.
#
# No 1x3 hardwood nose: that stiffener existed to triple a PLY shelf's effective I and take
# the spring out of gabled ply sag; solid oak needs none of it, and it also closes a
# quantity gap — the nose was ~41 LF of hardwood nothing in the model counted.
#
# ** SOLID WOOD ON CLEATS MOVES, AND THE FASTENING HAS TO LET IT. ** Boards run the 34 3/4"
# bay (grain along it), so seasonal movement is FRONT TO BACK — along the side cleats,
# across their screw line — roughly 1/4" of tangential movement across 18" of white oak over
# a Minnesota RH swing. Screw tight at the FRONT only; elongate every side- and back-cleat
# hole rearward. A solid shelf pinned hard on three sides splits, in year two, not on install.
#
# ** 18" DEEP, NOT 24". ** The room is 26" clear N-S, so 24" left 2" of floor and 18" leaves
# 8". The milling supply drove it, not the ergonomics: the owner's white oak runs to 18"
# wide (a finished 18" board needs ~18 3/4" in the rough once edge-jointed), so 18" is one
# hand-picked board per shelf where 24" was two edge-glued. Published guidance favours 18"
# anyway — 16" is the usual practical reach-in maximum, 20"+ reads too deep to see into.
# ~25% of shelf area is given up for it. Two things still make an 18" reach-in good: the
# shelves are STANDABLE (bottom bay a step, top shelf reachable), and ED-M-PANTRY-LT is a
# vertical slot lighting the depth behind whatever is on each shelf.
#
# Shelf pitch is GRADUATED, not uniform — uniform spacing wastes about two shelves' worth of
# volume, and since every shelf is rated to be stood on regardless of pitch, climbing does
# not need even rungs.
PANTRY_SHELVES_70 = FurnitureType(
    tag="FT-KIT-PANTRY-SHELVES-70", name='Pantry shelf stack, 70 1/4" x 18"',
    footprint=(inch(70.25), inch(18)), height=ft(7),
    storage=True, work_surface=False, plan_symbol="bookcase",
    source="Site-built millwork, DESIGNED TO BE CLIMBED — see "
           "notes/pantry_climbable_shelving.md. 1 1/2\" solid white oak shelves (owner "
           "stock, scheduled in plan/millwork.py as SB-M-PANTRY) on continuous 1x3 cleats "
           "on three sides, screwed DOWN onto the cleats (load path is cleat -> fastener "
           "-> stud, never shelf -> pin); NO adjustable standards and no shelf pins — a "
           "pin carries a jar, not a person. Screwed tight at the FRONT only, with every "
           "side- and back-cleat hole elongated rearward so 18\" of solid oak can move "
           "without splitting. A full-height 3/4\" ply centre gable at mid-span, notched "
           "around the cleats, floor to top shelf, halves the span to ~34 3/4\" and is not "
           "optional — the full span deflects ~0.223\" under 250 lb, past the L/360 this "
           "is graded to as a floor. Two #10 x 3\" structural screws per cleat into solid "
           "wood at EVERY bay, over flat 2x4 blocking laid in each bay BEFORE the gypsum. "
           "Design load: treat as floor, not shelf — 40 psf uniform PLUS a 250-300 lb "
           "concentrated load anywhere, which governs. Graduated spacing: ~20\" bottom bay "
           "(small appliances, bulk), 12\"-14\" middle (boxes, bottles), 8\"-10\" top (cans, "
           "jars). 18\" DEEP by owner's decision (2026-08-29, replacing 24\"), which leaves "
           "8\" of floor in front of the stack and puts each shelf on one board.",
)



# --- Dining -----------------------------------------------------------------------------

_DINING_SOURCE = (
    "library FURN-DINING-8, with the chair-use zone's four corner squares removed — see "
    "FURN-M-DINING in plan/placeables.py for the decision"
)
_DINING_CHAIR = "FURN-DINING-CHAIR"


def _open_corner_chair_zone(half_width, half_depth, reach):
    """A rectangular table's chair-use margin as two crossed bands, not one bigger rectangle.

    ``library.placeables._zones.surround_zone`` grows the footprint by ``reach`` on all four
    sides, which is right for a ROUND table — its footprint is the square around the circle
    and a chair really does sit on the diagonal. On a rectangular table the four corner
    squares hold nothing: a seat is on a side, and the corner of an 8' table is where two
    seats' elbows meet, not where a seventh chair goes.

    So this is the same ``reach`` on every side, minus those corners: one band the table's
    own width running past both long sides, one band the table's own depth running past both
    ends. Strictly smaller than ``surround_zone``, and smaller only where nothing stands.
    """
    def band(hw, hd) -> ClearanceZone:
        return ClearanceZone(
            footprint=Footprint2D(points=(pt(m(-hw), m(-hd)), pt(m(hw), m(-hd)),
                                          pt(m(hw), m(hd)), pt(m(-hw), m(hd)))),
            purpose="chair-use zone", policy=ClearancePolicy.RECOMMENDED,
            source=_DINING_SOURCE, occupant_types=(_DINING_CHAIR,),
        )
    return (band(half_width.meters, half_depth.meters + reach.meters),
            band(half_width.meters + reach.meters, half_depth.meters))


# The house's dining table. Identical to library FURN-DINING-8 in every dimension — 8' x
# 3'-6", 30" high, eight places — and differs only in the shape of its recommended zone.
# It is house-local rather than a change to the shared type because the shared one is also
# the round table's rule, and on a round table the corners are real (see the helper above).
DINING_8_OPEN_CORNERS = FurnitureType(
    tag="FT-DINING-8-OPEN-CORNERS", name="Eight-seat dining table (open-corner chair zone)",
    footprint=(ft(8), ft(3, 6)), height=ft(2, 6), plan_symbol="dining-table",
    source=_DINING_SOURCE,
    clearances=_open_corner_chair_zone(ft(4), ft(1, 9), ft(3)),
)


# --- Closet shelf-and-rod, the four dedicated closets --------------------------------------
#
# Ventilated ("wire") shelving on a rod, the standard closet fit-out, and the reason it is
# a ``FurnitureType`` rather than a ``ShelfBank``: a ShelfBank reaches exactly one consumer,
# ``takeoff/hardwood.py``, whose whole subject is BOARDS out of the family's own stock. An
# epoxy-coated steel shelf has no species, no board feet and no cut list — putting one
# through the milling schedule would ask the mill to saw a ventilated shelf. As a placeable
# it bills where it belongs, in ``[placeables]``, and it draws in the closet it fills.
#
# One type per closet because a FurnitureType carries a fixed footprint and these four runs
# are four different lengths. 16" deep is the standard ventilated shelf and the depth a
# jacket on a hanger actually needs; 12" is the linen depth and is what RM-S-NCLOSET's
# 40 3/4" of wall takes without crowding its door.
#
# ``plan_symbol="bookcase"`` for the same reason PANTRY_SHELVES_70 uses it: a shelf run is a
# depth of floor the room does not have, and a plan that draws the closet empty reads as
# room that is there. They are WALL-mounted at rod height, so nothing stands on the floor —
# the symbol is the reach, not an obstruction.
_CLOSET_SOURCE = (
    "Ventilated epoxy-coated steel shelf on 12 ga. wall standards and brackets, with the "
    "integral hang rod — ClosetMaid/Rubbermaid-class, the ordinary reach-in fit-out. "
    "Standards land on studs; a 16\" shelf on 24\" bracket spacing carries a loaded rod. "
    "Mounted at 66\" so a full-length coat (54\"-58\") hangs clear of the floor with the "
    "shelf above it, which is what the mudroom closet is for (plans/TODO.md)."
)

CLOSET_SHELF_ROD_60 = FurnitureType(
    tag="FT-CLOSET-SHELFROD-60", name='Closet shelf and rod, 60" x 16"',
    footprint=(inch(60), inch(16)), height=inch(1),
    storage=True, work_surface=False, plan_symbol="bookcase",
    mount=_WALL_MOUNT, source=_CLOSET_SOURCE,
)
CLOSET_SHELF_ROD_96 = FurnitureType(
    tag="FT-CLOSET-SHELFROD-96", name='Closet shelf and rod, 96" x 16"',
    footprint=(inch(96), inch(16)), height=inch(1),
    storage=True, work_surface=False, plan_symbol="bookcase",
    mount=_WALL_MOUNT, source=_CLOSET_SOURCE,
)
CLOSET_SHELF_ROD_84 = FurnitureType(
    tag="FT-CLOSET-SHELFROD-84", name='Closet shelf and rod, 84" x 16"',
    footprint=(inch(84), inch(16)), height=inch(1),
    storage=True, work_surface=False, plan_symbol="bookcase",
    mount=_WALL_MOUNT, source=_CLOSET_SOURCE,
)
CLOSET_SHELF_36 = FurnitureType(
    tag="FT-CLOSET-SHELF-36", name='Closet linen shelf, 36" x 12"',
    footprint=(inch(36), inch(12)), height=inch(1),
    storage=True, work_surface=False, plan_symbol="bookcase",
    mount=_WALL_MOUNT, source=_CLOSET_SOURCE,
)


# --- RM-M-BATH2, the over-toilet cabinet -------------------------------------------------
#
# The room's only storage above the vanity drawers, and the only wall left to put it on:
# the vanity runs the south half of the west wall, the shower and the tub deck take the whole
# east wall, and W-M-HS1's bathroom face x 6 5/8"..4'-4" is what remains. 45" is not a
# rounding -- it is exactly three 15" flush doors, and the east end stops on W-M-TUBDK-W's
# west face (x = 52"), a plane already in the room, with 3/8" of scribe taken across the run.
#
# ** SURFACE-MOUNTED, NOT RECESSED, AND THAT IS FORCED. ** W-M-HS1 is
# INT_2X6_STAGGERED_PLUMBING: every bath-face bay has a hall-face stud 2" back at its
# midpoint, so a continuous recess means cutting and heading the bath-face studs -- and
# FX-M-BATH2-WC's vent rises in that wall directly above the bowl. 5" net after gypsum, for
# all of that, when the ask was 6". W-M-W3 is the thermal envelope and is not a candidate.
#
# ** THE 4'-0" BOTTOM IS THE COMPLIANCE LINE, NOT A COMFORT CHOICE. ** FX-TOILET-STD is 30"
# tall. A carcass coming down to tank level would push the wall face 6" south, the bowl would
# move with it, and its front clearance would land 2.8" inside FX-M-BATH2-SINK -- which clears
# by 3 1/4" today. Above 30" nothing else in the room is redrawn, and 48" leaves 18" of clear
# air over the tank lid. The engine grades this: see notes/bath2_over_toilet_cabinet.md and
# ``resolve/placeables.py::_mounted_over_the_fixture``.
#
# No ``clearances``, per the casework rule: a built-in's back is the wall and the floor in
# front of it is the floor you already stand on. ``work_surface=False`` is correct and inert --
# ``_fixed_cabinet_intervals`` only breaks an NEC 210.52 ring for cabinets within 6" of the
# floor, and a bathroom is not a graded room.
BATH2_CAB_4506 = FurnitureType(
    tag="FT-BATH2-CAB-4506", name='Bath 2 over-toilet cabinet, 45" x 6"',
    footprint=(inch(45), inch(6)), height=inch(60),
    storage=True, work_surface=False, plan_symbol="wall-cabinet",
    source="Site-built millwork, not a catalogue unit: a 3/4\" paint-grade plywood carcass "
           "screwed to W-M-HS1's studs (a staggered wall gives a fastening point every 8\") "
           "and faced with three 15\" x 60\" flush 5/8\" MDF slabs on push-to-open touch "
           "latches, painted out in the wall colour -- no pulls, hairline reveals only, so it "
           "reads as a shallow paneled wall rather than a box over the toilet. 4 adjustable "
           "shelves, ~22 linear feet. Bottom at 4'-0\" AFF, top at 9'-0\" = the ceiling.",
)


# --- RM-A-STUDIO's wet-bar base -----------------------------------------------------------
#
# FX-A-STUDIO-BAR-SINK is ``Mount(WALL, elevation=27")``, the identical mount to
# FX-M-KITCH-SINK -- and that mount only describes a real thing because a run of casework
# stands under the kitchen sink. Under the bar sink there was nothing: the studio block's
# comments describe a counter that existed as prose only, and the sink hung on the wall.
#
# ** 18" DEEP, AND THE CATALOG HAS NO SUCH BASE. ** Every ``library.placeables.casework``
# base is ``_BASE_DEPTH`` = 24". Measured against D-A-STUBATH's real swing polygon, from
# W-A-STU-W's west face at x 17'-8 5/8":
#     24" deep -> 52.4 in^2 inside the arc
#     21" deep -> 15.4 in^2 inside the arc
#     18" deep -> clear, by 0.42"
# The bath door has nowhere else to swing (see storeys/attic_studio.py's OPENINGS) -- it is
# the same arc that pushed APPL-A-STUDIO-FRIDGE south to y 13'-6" -- so the cabinet is what
# yields, and 18" is the deepest that fits. That is not a compromise dimension: an 18"
# vanity/bar base under an 18" x 14" bowl is a stock depth, and the bowl is only 14" deep,
# so nothing is lost off the back.
#
# House-local rather than a catalog addition because the depth is set by ONE door's arc in
# ONE room. A generic 18" base would be a reasonable ``casework.py`` entry on its own
# merits, but promoting it belongs in CONTRIBUTING's review, not in this fix.
#
# 24" wide in y, north face flush with the sink's at y 17'-1" (the same 5/8" scribe to
# W-A-BATH-S the sink takes), leaving 7" of open floor to the fridge -- the run stays the
# "sink, gap, fridge" the studio block already describes, now with the sink standing on
# something. It steps 6" shallower than the 24" fridge beside it, which is what an 18" base
# next to a 24" appliance looks like anywhere.
#
# No ``clearances``, per the casework rule. ``work_surface=True``: it is the bar counter.
STUDIO_BAR_BASE_2418 = FurnitureType(
    tag="FT-STUDIO-BAR-BASE-2418", name='Studio wet-bar base, 24" x 18"',
    footprint=(inch(24), inch(18)), height=ft(3),
    storage=True, work_surface=True, plan_symbol="sink-base",
    source="Stock 18\"-deep frameless vanity/bar base with two doors, no drawer box (the "
           "bowl and its trap take the space), on a site-scribed toe kick, with a 24\" x "
           "18\" solid-surface top cut for FX-A-STUDIO-BAR-SINK's 18\" x 14\" bowl. 36\" "
           "finished height, matching the 27\" bowl mount the fixture already carries.",
)


FURNITURE_TYPES = (CURTAIN_ROD_48, CURTAIN_ROD_84, CURTAIN_ROD_OUTDOOR_114,
                   CURTAIN_ROD_OUTDOOR_98,
                   ACCESS_PANEL_1414, ACCESS_PANEL_1429, BATH1_SHELF_2030,
                   MEDIA_SECTIONAL_U, THEATER_BOOKCASE, OVER_COLD_3278, MIXER_GARAGE_24,
                   PANTRY_SHELVES_70, DINING_8_OPEN_CORNERS,
                   STUDY_BENCH, STUDY_DESK, FOLD_LEAF,
                   CLOSET_SHELF_ROD_60, CLOSET_SHELF_ROD_84, CLOSET_SHELF_ROD_96,
                   CLOSET_SHELF_36, BATH2_CAB_4506, STUDIO_BAR_BASE_2418)

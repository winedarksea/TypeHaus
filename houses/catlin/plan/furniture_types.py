"""House-local furniture catalog for items specific to the Catlin plan.

Only items *made to fit this house* belong here: nothing here is a product anyone would
reuse across plans (the test for house-local). The curtain rods, access panels and closet
shelving this house places are library rows (``library.placeables.allowances``).
"""

from __future__ import annotations

from library.placeables.allowances import (
    ACCESS_PANEL_1414,
    ACCESS_PANEL_1429,
    ACCESS_PANEL_CLG_3029,
    CLOSET_SHELF_36,
    CLOSET_SHELF_ROD_60,
    CLOSET_SHELF_ROD_84,
    CLOSET_SHELF_ROD_96,
    CURTAIN_ROD_48,
    CURTAIN_ROD_84,
)

from typehaus.model import (
    BuiltInBookcaseBay,
    BuiltInBookcaseSpec,
    Footprint2D,
    FurnitureType,
    Mount,
    MountKind,
    PlacementStrategy,
    ft,
    inch,
    pt,
)

_WALL_MOUNT = Mount(kind=MountKind.WALL)

# One fabricated run, separate from the conventional partition behind it. Dimensions are
# the joiner's clear openings and board stock; every output derives the same twelve boards,
# four shared/end dividers, and three stepped backs from this record.
STUDY_BUILT_IN_BOOKCASE = FurnitureType(
    tag="FT-A-STUDY-BUILTIN", name="Attic study stepped built-in bookcase",
    footprint=(inch(99.375), inch(10.625)), height=inch(60),
    placement=PlacementStrategy.WALL_ATTACHED,
    built_in_bookcase=BuiltInBookcaseSpec(
        bays=(
            BuiltInBookcaseBay(clear_width=inch(31.25), height=inch(60), horizontal_board_count=5),
            BuiltInBookcaseBay(clear_width=inch(31.25), height=inch(42), horizontal_board_count=4),
            BuiltInBookcaseBay(clear_width=inch(31.25), height=inch(30), horizontal_board_count=3),
        ),
        shelf_depth=inch(9.875), horizontal_board_thickness=inch(1.5),
        divider_thickness=inch(0.75), back_thickness=inch(0.75),
        west_filler_width=inch(2.625),
    ),
    wood_material_ref="oak-shelf-6q",
    source="Catlin study fixed casework: front y=105 5/8 in.; x=272..368 3/4 in.; three 31 1/4 in. clear bays with 60/42/30 in. tops and 5/4/3 horizontal boards; 2 5/8 in. west filler closes to W-A-SN-WR.",
)

# 48" covers every main-storey window in the house — the widest RO on a rod is 30"
# (WT-3048), which leaves 9" of stackback each side. 84" is D-M-BALC's french pair (60"
# RO, 12" each side). Depth is the bracket projection, height the rod and finial.
# --- the porch enclosure track -------------------------------------------------------
# NOT A CURTAIN ROD. 2026-09-03: the two 114" rods and the two 98" side rods were replaced
# by a snap-carrier aluminium curtain TRACK, the hardware a screened-porch enclosure is
# actually built on (Mosquito Curtains and equivalents: 8' anodized sticks, 90-degree
# curves, splices and end caps, screwed up through the stick's centre groove).
#
# ** THE PRODUCT CHANGED BECAUSE THE ROD COULD NOT SEAL. ** A rod at 8'-6" under a joist
# soffit at 9'-4 3/4" leaves a ~10" open band across the whole opening, and rings leak at
# the top by construction — a bug highway with a curtain hanging under it. A track screwed
# flush to the soffit closes that band, and it is the same hardware for both panel sets:
# no-see-um mesh in summer, 30-ga marine clear vinyl in spring and fall for wind chill.
# Zippers were rejected as the primary closure (UV and grit make them the wear item and a
# replacement means re-sewing a panel); they survive only at the vinyl set's corner joints.
#
# ``height=inch(1)`` is the extrusion, not a rod-and-finial: ``Mount.elevation`` is the body
# BOTTOM, so the track's top lands on the soffit it fastens to. The 2" footprint depth is
# the stick plus its carriers. ``plan_symbol=None`` as with the rods — scheduled and billed,
# not drawn.
#
# ``MountKind.CEILING``, not WALL. These name no wall, so ``_resolve_location`` returns the
# authored position untouched either way and the resolved Z is byte-identical; all WALL
# bought was ``horizontal_projection_from_wall_m`` for A117.1 s307.2, which is moot above
# 80". CEILING says the true thing: they hang from a soffit.
#
# See notes/porch_enclosure.md for the panels, the magnet seam and the north sweep.
_TRACK_SOURCE = ("notes/porch_enclosure.md — snap-carrier aluminium curtain track, screwed "
                 "up through the centre groove into the balcony joists/rim above; 5 screws "
                 "per 8' stick (the VINYL spacing, so one set of hardware carries both "
                 "panel sets).")
# The FRONT run, one piece since 2026-09-22: x 10'-0"..26'-0" on the -9'-0" spare joist,
# less ~8" at each end where a 90-degree curve substitutes for the last of the stick.
PORCH_TRACK_176 = FurnitureType(
    tag="FT-PORCH-TRACK-176", name='Porch enclosure track, 176"',
    footprint=(inch(176), inch(2)), height=inch(1),
    plan_symbol=None, mount=Mount(kind=MountKind.CEILING), source=_TRACK_SOURCE,
)
# The two FLANK runs, x = 10'-0" and 26'-0", y -9'-0" to -0'-7 1/2": 2 1/2" past the porch
# deck edge on an outrigger, stopping 1/4" off the -0'-7 1/4" cladding face. 100 1/2" long; the
# tag keeps "102" because prices.toml keys the per-each row on it.
PORCH_TRACK_102 = FurnitureType(
    tag="FT-PORCH-TRACK-102", name='Porch enclosure track, 100 1/2"',
    footprint=(inch(100.5), inch(2)), height=inch(1),
    plan_symbol=None, mount=Mount(kind=MountKind.CEILING), source=_TRACK_SOURCE,
)

# 14x14 is the tub waste-and-overflow size, 14x29 the wall-hung WC carrier size — the
# carrier is a tall frame and the panel has to reach the whole of it.
# ** A CEILING PANEL IS A DIFFERENT SHAPE OF TYPE, NOT A REUSE OF THE TWO ABOVE. ** Those
# two are WALL mounts: their `footprint` is (width, frame projection) and their `height` is
# the vertical dimension of the opening. Lay one in a ceiling and the plan rectangle comes
# out 1" deep. For a ceiling panel the whole clear opening is in PLAN and the frame's
# projection is the height, so the fields swap roles and the type has to be its own.
#
# ** 30 x 29, AND IT IS THAT BIG BECAUSE THE LADDER WAS HEADED OFF FOR IT. ** It was 20 x 13
# for one day — the clear bay between two rungs at 16" o.c., which is a hand and a filter and
# nothing else. `Soffit.openings` now exists (model/floors.py), so SF-S-HP1 authors a real
# framed hole: one rung cut, two 32" headers along the box, and 30 x 29 of clear opening
# under the air handler's north two-thirds and its return face. That is a service hatch a
# blower comes out of, and `structural.soffit_opening` grades the header it hangs on.
#
# ** IT IS SEALED AND GASKETED, AND THAT IS A CODE LINE, NOT A DETAIL. ** The obvious
# convenience — leave the soffit's bottom open in the closet and reach straight up — makes
# the CLOSET the return plenum, which is exactly what IMC 601.5(7) forbids. A hinged, gasketed
# door is the compliant version of the same convenience: air does not enter through it, so it
# is a service hatch and not an inlet.

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
# CLOSED BELOW THE COUNTER (owner, 2026-09-28). FX-S-BATH1-LAV's north end panel stands
# 0.12" in front of this case's whole open face, so nothing under the 36" counter line can be
# reached. A fixed 3/4" plywood front panel (carcass, hidden behind the vanity end; no oak)
# closes floor to 35 1/4"; the lowest open shelf's top is flush with the counter at 36", so
# things slide across. Oak boards top at 36/48/60/72/84" — 11 1/4" clear each — and none
# stands in the closed base. SB-S-BATH1 bills those five.
#
# No ``clearances``: per the casework rule, a built-in's back is the wall and its ends are
# its neighbours, and the floor in front of it is the same floor you stand on to use the
# tub.
BATH1_SHELF_2030 = FurnitureType(
    tag="FT-BATH1-SHELF-2030", name='Bath 1 alcove shelf, 20" x 30"',
    footprint=(inch(20), inch(30)), height=inch(84),
    storage=True, work_surface=False,
    built_in_bookcase=BuiltInBookcaseSpec(
        bays=(BuiltInBookcaseBay(clear_width=inch(18.5), height=inch(84),
                                 horizontal_board_count=5, closed_base_height=inch(35.25)),),
        shelf_depth=inch(29.25), horizontal_board_thickness=inch(0.75),
        divider_thickness=inch(0.75), back_thickness=inch(0.75),
    ),
    wood_material_ref="oak-shelf-4q",
    source="Site-built millwork, not a catalogue bookcase: a 3/4\" plywood carcass scribed "
           "to the east end of RM-S-BATH1's tub alcove, whose WEST panel carries "
           "FX-S-BATH1-SH's east flange over a framed 2x4 and is what makes that insert a "
           "legitimate three-wall install. Depth matches the tub (30\"), height matches the "
           "surround head (84\"); the 7/8\" of slack at the east wall is taken as scribe.",
)


# RM-S-SUITEBATH's alcove return, the hall bath's shelf turned to face west (2026-10-03).
# FX-S-SUITEBATH-TUBSH is a flanged insert with its SOUTH end open; this case's north
# divider is that third side, over a framed 2x4 for the flange, and its back panel sits on
# W-S-C2C. 11 1/4" wide is the leftover between the tub and W-S-SBS; 30" deep is the tub's
# own width; 84" is the surround head. Open to the room, no closed base: eight oak boards
# make seven openings of about 11".
SUITEBATH_SHELF_1130 = FurnitureType(
    tag="FT-SUITEBATH-SHELF-1130", name='Suite bath alcove shelf, 11 1/4" x 30"',
    footprint=(inch(11.25), inch(30)), height=inch(84),
    storage=True, work_surface=False,
    built_in_bookcase=BuiltInBookcaseSpec(
        bays=(BuiltInBookcaseBay(clear_width=inch(9.75), height=inch(84),
                                 horizontal_board_count=8),),
        shelf_depth=inch(29.25), horizontal_board_thickness=inch(0.75),
        divider_thickness=inch(0.75), back_thickness=inch(0.75),
    ),
    wood_material_ref="oak-shelf-4q",
    source="Site-built millwork: a 3/4\" plywood carcass scribed into the south end of "
           "RM-S-SUITEBATH's tub alcove, open to the west. Its north divider carries "
           "FX-S-SUITEBATH-TUBSH's south flange over a framed 2x4.",
)

# RM-S-SUITEBATH's robe pegs, on W-S-DC2 north of the door leaf (2026-10-03). The closet
# rail's build at 24", four knobs.
SUITEBATH_PEGS_24 = FurnitureType(
    tag="FT-SUITEBATH-PEGS-24", name='Solid oak wall-mounted peg rail, 24", four knobs',
    footprint=(inch(24), inch(4)), height=inch(3.5),
    plan_symbol="peg-rail", mount=Mount(kind=MountKind.WALL),
    wood_material_ref="oak-shelf-4q",
    source="Solid-oak 24 in backplate with four rounded, projecting oak knobs; the "
           "FURN-M-CLOSET-PEGS rail at a shorter length.",
)

# The suite bath's mirror (owner, 2026-10-03): a plain arched shelf mirror over the lav,
# lit by a separate bar above it.
SUITEBATH_MIRROR_ESTERO = FurnitureType(
    tag="FT-SUITEBATH-MIRROR-ESTERO", name='Kate and Laurel Estero arch shelf mirror, 20" x 28"',
    footprint=(inch(20.125), inch(5.5)), height=inch(28),
    plan_symbol="arch-shelf-mirror", mount=Mount(kind=MountKind.WALL),
    product_ref="PROD-KATELAUREL-221484",
    source="Kate and Laurel Estero, gold metal frame, 4\" x 20\" shelf; retailer dimensions.",
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
#      D-M-LAUN's leaf parks inside W-M-HS4 between x 12'-1" and 15'-2", and
#      `mep.pocket_occupancy` refuses any fastener, device or pipe in that cavity. This
#      bench covers x 13'-8 3/4"..17'-7 3/4", so a cleat screwed to the wall would FAIL.
#
# Every dimension below is derived from `out/model.json`: the room's four resolved gypsum
# faces were x 13'-8" .. 17'-8 5/8", y 18'-4" .. 22'-1 5/8" — a 48 5/8" x 45 5/8" clear box,
# ~15.4 sf — with W-M-LS/W-M-CLN2 as INT_2X4_STAGGERED_DOUBLE_GWB. **STALE:** both walls are
# now the thinner single-gwb INT_2X4_STAGGERED_GWB, opening the box ~5/8" per retyped face
# (~49 1/4" x 46 1/4"), but the STUDY_BENCH footprint, wainscot-return scribe and seat-length
# math below are still cut to the OLD box. Re-derive before this casework is built:
# `Room.clear_face` IS the finish face now (axis cell minus the wall layers) and reads
# 48 1/4" x 46 1/4", 15.5 sf. The sauna benches in plan/placeables.py are dimensioned
# the same way, off liner faces.
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
    wood_material_ref="oak-shelf-4q",
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


# FT-KIT-OVER-COLD-3278 (32 7/8" x 24" x 21", hung at 75" over the Frigidaire columns) and
# FT-KIT-MIXER-GARAGE-24 (24" x 24" x 72", standing on the peninsula at 36") are both
# RETIRED, 2026-09-11, during the kitchen's move onto the IKEA SEKTION frame ladder.
# The later catalog review found that the replacement deep wall frames are not sold in
# these dimensions either. The 2026-09-29 correction reintroduced explicit house-local
# deep upper types in plan/kitchen_deep_cabinets.py:
#
#  * over-cold boxes now use stock SEKT-TS30-20 at 73 1/2" (2026-10-05), tops 93 1/2";
#  * the mixer garage is FT-KIT-DEEP24-40 under stock FT-KIT-STOCK24-30-HUNG, topping at 106".
#
# Deleted rather than left unused, per FT-KIT-COLDSTORE-FILLER's rule above: an
# unreferenced house-local type reads as a size someone might reach for. The fit-out prose
# each carried on its `source` — the mixer garage's full-extension pull-out, its flush shelf
# face and its two in-cabinet GFCI receptacles — moved to plan/kitchen_casework.py, where the
# instances are, and to prices.toml [allowances], where the money is.


# --- RM-M-PANTRY's shelf stack --------------------------------------------------------
#
# House-local by the test at the top of this file: 73 1/4" is this room's clear span, wall
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
# are 1 1/2" solid white oak (plan/millwork.py, owner stock); the full 73 1/4" span carries
# 250 lb at midspan at only ~678 psi (S = 6.75 in^3), well under a 1,500-2,000 psi flatwise
# allowable. Deflection still fails it: I = 5.06 in^4 gives ~0.253" full-span against this
# shelf's L/360 = 0.203" floor criterion. Gabled to 36 1/4" it is ~336 psi and ~0.031", not
# close to any limit. The gable also stays because the cleat/blocking layout is built around
# it, and it makes the bottom bay a step rather than a plank.
#
# No 1x3 hardwood nose: that stiffener existed to triple a PLY shelf's effective I and take
# the spring out of gabled ply sag; solid oak needs none of it, and it also closes a
# quantity gap — the nose was ~41 LF of hardwood nothing in the model counted.
#
# ** SOLID WOOD ON CLEATS MOVES, AND THE FASTENING HAS TO LET IT. ** Boards run the 36 1/4"
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
    tag="FT-KIT-PANTRY-SHELVES-70", name='Pantry shelf stack, 73 1/4" x 18"',
    footprint=(inch(73.25), inch(18)), height=ft(7),
    storage=True, work_surface=False, plan_symbol="bookcase",
    wood_material_ref="oak-shelf-8q",
    source="Site-built millwork, DESIGNED TO BE CLIMBED — see "
           "notes/pantry_climbable_shelving.md. 1 1/2\" solid white oak shelves (owner "
           "stock, scheduled in plan/millwork.py as SB-M-PANTRY) on continuous 1x3 cleats "
           "on three sides, screwed DOWN onto the cleats (load path is cleat -> fastener "
           "-> stud, never shelf -> pin); NO adjustable standards and no shelf pins — a "
           "pin carries a jar, not a person. Screwed tight at the FRONT only, with every "
           "side- and back-cleat hole elongated rearward so 18\" of solid oak can move "
           "without splitting. A full-height 3/4\" ply centre gable at mid-span, notched "
           "around the cleats, floor to top shelf, halves the span to 36 1/4\" and is not "
           "optional — the full span deflects ~0.253\" under 250 lb, past the L/360 this "
           "is graded to as a floor. Two #10 x 3\" structural screws per cleat into solid "
           "wood at EVERY bay, over flat 2x4 blocking laid in each bay BEFORE the gypsum. "
           "Design load: treat as floor, not shelf — 40 psf uniform PLUS a 250-300 lb "
           "concentrated load anywhere, which governs. Graduated spacing: ~20\" bottom bay "
           "(small appliances, bulk), 12\"-14\" middle (boxes, bottles), 8\"-10\" top (cans, "
           "jars). 18\" DEEP by owner's decision (2026-08-29, replacing 24\"), which leaves "
           "8\" of floor in front of the stack and puts each shelf on one board.",
)



# --- Shared clearance variants ----------------------------------------------------------
# The eight-seat table's open-corner chair zone and the 84" sofa's seat-width walk band are
# in ``library.placeables.furniture``. Catlin authors only the room-specific placements.


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
    footprint=(inch(45), inch(6)), height=inch(57),
    storage=True, work_surface=False, plan_symbol="wall-cabinet",
    source="Site-built millwork, not a catalogue unit: a 3/4\" paint-grade plywood carcass "
           "screwed to W-M-HS1's studs (a staggered wall gives a fastening point every 8\") "
           "and faced with three 15\" x 57\" flush 5/8\" MDF slabs on push-to-open touch "
           "latches, painted out in the wall colour -- no pulls, hairline reveals only, so it "
           "reads as a shallow paneled wall rather than a box over the toilet. 4 adjustable "
           "shelves, ~22 linear feet. Bottom at 4'-0\" AFF, top at 8'-9\" with room to install below the finished ceiling.",
)


# --- RM-A-STUDIO's wet bar: an IKEA SUNNERSTA kitchenette ----------------------------------
#
# ** RETIRED 2026-09-09: ** the studio's wet bar used to be a house-local 24"x18" base under
# FX-A-STUDIO-BAR-SINK, on the CENTRE WALL (W-A-C2), with D-A-STUBATH swinging out into it —
# the door blocked from opening fully with someone at the sink. The owner picked a real
# product instead: an IKEA SUNNERSTA mini-kitchen, 44 1/8" x 22" x 54 3/4", $149, article
# 40313363 — one piece carrying the sink, the counter and the fridge cavity together, and
# it moves the whole bar off the centre wall onto the bath wall, W-A-BATH-S, which is what
# frees D-A-STUBATH's swing and REG-A-HP-WEST underneath the old fridge. See
# plan/placeables.py and plan/fixtures.py for the siting.
#
# ** ITS TOP IS NOT REVERSIBLE, AND THAT SETTLED WHICH WALL IT WENT ON. ** The bowl is at the
# unit's right-hand end facing it. On the centre wall that puts the bowl 76" from the bath
# vent against a 60" trap-arm limit; on W-A-BATH-S it puts the bowl at the EAST end, nearest
# the stack, which is what makes the short revent in mep_venting.py possible at all.
#
# House-local, not a catalog addition, for the same reason the base it replaces was: one
# product picked for one room. ``storage=True``/``work_surface=True`` carry over from the
# old base; ``clearances`` stays unset, per the casework convention.
STUDIO_KITCHENETTE_4422 = FurnitureType(
    tag="FT-STUDIO-KITCHENETTE-4422", name='SUNNERSTA kitchenette, 44 1/8" x 22"',
    footprint=(inch(44.125), inch(22)), height=inch(54.75),
    storage=True, work_surface=True, plan_symbol="sink-base",
    source="IKEA SUNNERSTA mini-kitchen, article 40313363, $149. 44 1/8\" x 22\" x 54 3/4\", "
           "sink at the right-hand end facing the unit (top is NOT reversible). The US "
           "listing sells the faucet separately; other markets bundle a LAGAN mixer tap and "
           "a LILLVIKEN trap. Carries the fridge cavity underneath.",
)


# --- RM-M-LIVING's fireplace mantel ----------------------------------------------------
#
# The shelf over W-M-FIRE-HEAD. It existed only as `SB-M-FIRE-MANTEL`, a ShelfBank, and a
# ResolvedShelfBank carries width/depth/thickness/count and NO POSITION — no emitter reads
# `model.shelf_banks` at all, so the mantel had a cut list and no body. Nothing in the 3D,
# nothing for a clearance check to see. Hosting the bank on a wall-mounted placeable is the
# house's existing idiom (FURN-B-PLAY-TV, the kitchen wall cabinets, the CASE-*-ST stacker
# course) and gives it a real extruded solid.
#
# `plan_symbol=None`: the frozen symbol vocabulary has no shelf or mantel, and a plain box
# is honestly what a mantel is — a slab with nothing under it.
#
# ** `work_surface` IS LEFT UNSET AND THAT IS LOAD-BEARING. ** `work_surface=False` is the
# value NEC 210.52(A)'s wall-space rule keys on; `None` keeps a shelf 5'-4" in the air out
# of that rule entirely rather than leaning on the 6" floor-contact gate to do it.
MANTEL_WALNUT_46 = FurnitureType(
    tag="FT-MANTEL-WALNUT-46", name='Fireplace mantel shelf, 45 1/2" x 11 1/2"',
    footprint=(inch(45.5), inch(11.5)), height=inch(2.25),
    storage=False, plan_symbol=None,
    source="Site-made solid walnut mantel in 12/4 stock, 45 1/2\" x 11 1/2\" x 2 1/4\", "
           "flush with the brick panel's ends and cantilevered off blocking let into "
           "W-M-FIRE-HEAD's back face. Its underside sits at 64\" AFF, on the head "
           "course — 24 modular courses of visible brick — and its top at 66 1/4\". "
           "19 5/8\" of clearance from the firebox trim top at 44 3/8\" to the shelf, "
           "against Amantii's 4\" minimum for the BI-30-XTRASLIM; the brick spandrel "
           "over the 44 5/8\" masonry head is a different number (19 3/8\") for a "
           "different thing, and both are stated on the drawing.",
)


# --- the balcony leader's splash basin (2026-09-23) --------------------------------------
#
# TR-SG-RUNNEL's spout lands in it: splash stone first, bird bath in season. A shallow dish
# (<= 2") with open, sloped sides so ice lifts rather than splits it — cast concrete basins
# crack in a Minnesota winter. It spills through a south notch onto a river-rock apron and
# lawn. Rain refills it but summer evaporation empties 2" in ~8-11 days, so it is rinsed and
# topped up every 2-3 days while it holds water (MMCD's mosquito guidance).
SPLASH_BASIN_GRANITE_24 = FurnitureType(
    tag="FT-SPLASH-BASIN-GRANITE-24", name="Granite splash basin / bird bath, 24\"",
    footprint=(inch(24), inch(24)), height=inch(14),
    storage=False, plan_symbol=None,
    source="Natural granite boulder basin, ~24\" x 24\" x 14\", dish <= 2\" deep with "
           "sloped open sides and a notch spilling south; set on 4\" of compacted stone at "
           "yard grade, with a 2' x 6' washed river-rock apron on fabric beyond the notch. "
           "Stone yard selection; no product named.",
)

FURNITURE_TYPES = (STUDY_BUILT_IN_BOOKCASE,
                   CURTAIN_ROD_48, CURTAIN_ROD_84, PORCH_TRACK_176,
                   PORCH_TRACK_102,
                   ACCESS_PANEL_1414, ACCESS_PANEL_1429, ACCESS_PANEL_CLG_3029,
                   BATH1_SHELF_2030,
                   MEDIA_SECTIONAL_U, THEATER_BOOKCASE, SUITEBATH_SHELF_1130,
                   SUITEBATH_PEGS_24, SUITEBATH_MIRROR_ESTERO,
                   PANTRY_SHELVES_70,
                   STUDY_BENCH, STUDY_DESK, FOLD_LEAF,
                   CLOSET_SHELF_ROD_60, CLOSET_SHELF_ROD_84, CLOSET_SHELF_ROD_96,
                   CLOSET_SHELF_36, BATH2_CAB_4506, STUDIO_KITCHENETTE_4422,
                   MANTEL_WALNUT_46, SPLASH_BASIN_GRANITE_24)

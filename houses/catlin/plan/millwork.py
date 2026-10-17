# haus: editable
# Catlin house millwork — the owner-milled red oak, and the species placed around it.
#
# The owner has red oak off family land in southern Minnesota (it was taken for white oak
# until 2026-10-16), effectively unlimited, in 4/4 to 8/4, with boards commonly 12"+ wide and
# some to 18". Its pores are open, so it does only dry interior work: wet-room stools and the
# bath shelves are locust, and the stools are mostly bought white oak. That supply wins
# on WIDTH and FLATNESS and loses on PROFILE: a one-piece stool, shelf or tread is worth
# milling, and a knife grind plus a molder setup cannot amortise over one house. Base and
# casing sidestep that by having no profile at all — plain S4S, butt-jointed — which is
# planer work, so TRIM-STANDARD below takes them off too.
#
# The bath vanities' sink-base shelves are in plan/millwork_vanities.py; the plant room's
# quartz stools are in plan/countertops.py (stone, the slab yard's, not the sawyer's).
#
# Nothing here authors a stool. `MillworkStandard` declares the scope and the resolver
# derives one per in-scope window, exactly as `EaveTrim` derives fascia off the roof plane:
# the 41 windows sit in four assemblies of four different thicknesses (13.885" / 14.540" /
# 14.050" / 8.135"), so a single authored depth would be wrong for three of them and would
# go wrong again the first time a foam lift or a girt depth moved.

from typehaus import ft, inch
from typehaus.model import (
    MillworkStandard,
    RoomTrim,
    ShelfBank,
    ShelfBay,
    ShelfProcurement,
    StairLandingMillwork,
    TrimStandard,
)

# The one declaration. Scope is EXT_2X6 alone — 34 of the 41 windows are in scope:
# WIN-M-KITCH is authored quartz (plan/countertops.py), the three east living-room stools
# ash (plan/living_east_run.py), and the rest derive bought white oak unless
# plan/window_stools.py names a species for the room (locust, ash, cherry, red oak).
#   * PLANT_EXT_2X6_HUMID (4) is the plant room, which runs at 70% RH by design. Oak in
#     that room is a cupped stool and a black tannin stain, so those four are authored
#     3 cm quartz remnants instead (PLANT_STOOLS, plan/countertops.py).
#   * SAUNA_LINER_ON_GARDEN_FRAMED (1) is lined in basswood for a burn-safety reason
#     (low-conductivity species, plan/assemblies.py) that a hardwood stool would defeat, so
#     its stool is authored in clear cedar (`cedar-sauna-stool`, plan/window_stools.py).
#   * GARAGE_WALL_2X6 (2) is a garage.
#
# `max_board_width` is an owner-supply fact, not an engine constant and not a price, so it
# belongs in the house the way prices.toml numbers do (plans/01-decisions.md #28). It is
# what `takeoff/hardwood.py` reads for the layup column: a finished face that cannot
# come off one board of this width lays up as an edge-glued panel instead.
MILLWORK = [
    MillworkStandard(
        uid="8YE8Y9SRFP", tag="MW-STANDARD",
        stool_material_ref="oak-stool",
        # 5/4 dressed to 1" (2026-10-16, was 1 1/4"): the stock stool thickness at ~10"
        # deep, and bought stock is no thicker than 5/4. Ask for rift or quartered boards
        # and finish all six faces, or a board this wide cups.
        stool_thickness=inch(1),
        stool_overhang=inch(0.75),
        # 1" of horn each side. No apron (the window returns are drywall); the horn stands
        # past the return so the stool reads as a board, not a shelf.
        stool_horn=inch(1),
        stool_profile="eased",
        stool_assemblies=("EXT_2X6",),
        # 29 oak treads: ST-M2S (14) and ST-S2A (15, three of them winders). ST-B2M is the
        # basement flight and is carpeted, ST-G-SERVICE is the garage's. This scope is also
        # what stamps the resolved treads red oak and the landings `oak-floor-custom` (the 3D and
        # `haus takeoff`'s [stair_treads]); no Stair repeats it.
        tread_material_ref="oak-tread",
        tread_stairs=("ST-M2S", "ST-S2A"),
        # Closed risers, 3/4" off 4/4 (notes/stair_riser_basis.md).
        riser_material_ref="oak-riser",
        landing_deck=StairLandingMillwork(
            stair_refs=("ST-M2S",),
            field_material_ref="oak-floor-custom",
            # 3/4" red oak T&G on 3/4" subfloor, like the halls either end of the flight.
            field_thickness=inch(0.75),
            subfloor_thickness=inch(0.75),
            board_face_width=inch(3.5),
            board_coverage_width=inch(3.125),
            # A landing tread off the tread stock: 3/4" behind the nose, grooved for the
            # field's tongue, its bullnose lip the flights' 1" over the riser below.
            nosing_material_ref="oak-tread",
            nosing_depth=inch(3.5),
        ),
        max_board_width=inch(18),
        # The study door's 4/4 red oak casing infill. Its type in study_bridge.py owns the size;
        # the sawyer view follows any later change to it.
        board_furniture_refs=("FURN-A-STUDY-BRIDGE-FRONT",),
    ),
    # Base and door casing, derived per room and per door face (resolve/interior_trim.py).
    # One size for both: 3/4" x 3 1/2" S4S, butt-jointed, flush where base meets leg. Casing
    # is red oak; the base is black cherry (2026-10-16). The sauna's base and inside casing
    # are black locust: no finished oak in a 190 F room.
    # The base goes in after the hard floors, so there is no shoe; carpet tucks under it.
    # A bought stock (e.g. "poplar-trim-paint") leaves `haus millwork` and is priced instead.
    # tasks.toml's trim visit names its rows by stock, so rename those there too — `haus
    # site validate` names them if you forget.
    #   * Tile rooms take a tile base and sheet-vinyl rooms a flash cove: that is the floor
    #     material's `base_detail`, not a list here.
    #   * Excluded: the utility rooms (RM-B-STAIR is the one that keeps its base) and the
    #     plant room, whose 70% RH would cup oak. The garage and the unfinished attic fall
    #     out on their own (unconditioned / no floor finish).
    TrimStandard(
        uid="KXZVF6Z652", tag="TRIM-STANDARD",
        material_ref="oak-trim",
        base_material_ref="cherry-trim",
        room_trims=(RoomTrim(rooms=("RM-B-SAUNA",), material_ref="locust-trim"),),
        thickness=inch(0.75),
        base_height=inch(3.5),
        casing_width=inch(3.5),
        reveal=inch(0.1875),
        # 3/4" jamb + 1/4" shim: the leg's inside edge sits 13/16" inside the RO.
        jamb_allowance=inch(1),
        min_leg_width=inch(1.5),
        # Boards come in 8' lengths: `haus millwork` packs base and casing cuts into them.
        stock_length=ft(8),
        excluded_rooms=("RM-B-FURNACE", "RM-B-ESS", "RM-B-WORKSHOP", "RM-B-GYM",
                        "RM-S-PLANT"),
    ),
]

# --- the attic study built-in -----------------------------------------------------------
# The furniture specification is the physical carcass and the single source for geometry.
# This ShelfBank retains the owner-stock fabrication takeoff: twelve 1 in. (5/4) red oak
# boards at the explicit 9 7/8 in. finished shelf depth — books, not people. 5/4 since
# 2026-10-16 (was 6/4): over a 31 1/4" bay at 30 lb/ft, E = 1.6 Mpsi, sag is ~0.024" against
# the 0.02"/ft bookshelf limit's 0.052"; 3/4" would be 0.056" and creep. The purchased door
# shelves are outside this bank and therefore cannot enter the hardwood quantity.
ATTIC_SHELVES = [
    ShelfBank(
        uid="ZSR38F5C8F", tag="SB-A-STUDY", host="FURN-A-STUDY-BUILTIN",
        material_ref="oak-shelf-5q", thickness=inch(1), depth=inch(9.875), profile="S4S",
        procurement=ShelfProcurement.CUSTOM_MILLED,
        bays=(
            ShelfBay(width=inch(31.25), clear_height=inch(60), shelf_count=5),
            ShelfBay(width=inch(31.25), clear_height=inch(42), shelf_count=4),
            ShelfBay(width=inch(31.25), clear_height=inch(30), shelf_count=3),
        ),
    ),
]

# --- the main pantry, FURN-M-PANTRY-SHELVES --------------------------------------------
#
# See notes/pantry_climbable_shelving.md and the FT-KIT-PANTRY-SHELVES-70 source.
#
# 1. THIS SHELF IS DESIGNED TO BE CLIMBED, so its thickness is a STRUCTURAL decision, not a
#    finish one. It is 6/4 red oak, 1 1/4" (2026-10-16; 8/4 before): a climbing 250 lb point
#    at mid-span over the gabled 36 1/4" half-span governs, graded as a FLOOR at L/360.
#    f ~484 psi, deflection ~0.054" against 0.101". At 5/4 (1") it is ~0.105" and just
#    misses, so 6/4 is the floor. THE GABLE IS NOT OPTIONAL: ungabled at 1 1/4" the full
#    span deflects ~0.44". THE CLEATS AND THE BLOCKING STAY, and the bays below are the
#    two half-spans the gable creates, not one 70" shelf.
# 2. THE CARCASS IS 18" DEEP, down from 24" — and the mill is what moved it. 24" was past
#    the 18" the supply can produce, so every shelf was a two-board edge glue-up; 18" is one
#    hand-picked wide board. `depth` is still deliberately NOT authored here — the bank
#    inherits the type's footprint, so the carcass and the shelf can never disagree.
#    18" IS PAST THE EDGE OF THE SUPPLY, and the schedule says so rather than rounding it
#    away: a finished 18" face needs an 18 3/4" rough board once an edge is straight-lined
#    and the other jointed, and `max_board_width` is 18". So `haus millwork` lays each shelf
#    up as `edge-glued panel x2`, 2 boards at 9". That is not a defeat — a solid 18" shelf
#    is normally a glued panel anyway, because one 18" board that wide cups — and it is a
#    far smaller statement than the 24" it replaced, which was a two-board panel with a
#    wider, scarcer board in it. ** THE ONE-NUMBER LEVER: ** if the family stack really does
#    hold boards past 18 3/4", raise `max_board_width` above and these panels become
#    single boards with no other edit.
#
# Six boards per bay, the case top included, on the graduated pitch the type specifies —
# ~20" bottom bay, 12"-14" middle, 8"-10" top — over the 7'-0" carcass.
MAIN_SHELVES = [
    ShelfBank(
        uid="E97F8XSSZ5", tag="SB-M-PANTRY",
        host="FURN-M-PANTRY-SHELVES",
        material_ref="oak-shelf-6q",
        thickness=inch(1.25),
        profile="S4S",
        procurement=ShelfProcurement.CUSTOM_MILLED,
        bays=(
            ShelfBay(width=inch(36.25), clear_height=ft(7), shelf_count=6),
            ShelfBay(width=inch(36.25), clear_height=ft(7), shelf_count=6),
        ),
    ),
    # --- RM-M-STUDY's call booth, FT-STUDY-BENCH and FT-STUDY-DESK -----------------------
    #
    # The bench seat and the desk top. Neither is a shelf in the cabinet sense and both are
    # here for the same reason the pantry's are: a ShelfBank is how a BOARD reaches
    # `haus millwork`, and these two are the biggest single pieces of hardwood in the house
    # after the treads. `shelf_count=1` is right and is not an omission — ShelfBay counts
    # horizontal boards INCLUDING the case top, and on a bench the seat IS the top.
    #
    # ** THE WALNUT IS BOUGHT, NOT OWNER-MILLED, WHICH INVERTS THE ACCOUNTING. ** Everything
    # else in this file comes off the family stock at ~$2/sf and therefore carries no dollar
    # anywhere in prices.toml (`haus millwork` is an UNPRICED VIEW and a "shelf" row may
    # reference no other section — a test enforces it). These two boards still carry no
    # dollar HERE; their money lives in the `[placeables]` rows for FT-STUDY-BENCH and
    # FT-STUDY-DESK, which are written to include their walnut. Getting that backwards puts
    # the most expensive material in the room at $0 — see the note on those rows.
    #
    # `depth` is deliberately NOT authored on either: both hosts are FurnitureTypes, so
    # `_carcass_depth_m` inherits the footprint depth (17" and 20") and the board can never
    # disagree with the carcass. Both are past `MW-STANDARD.max_board_width` once jointing
    # loss is taken, so both lay up as edge-glued panels — 2 boards at 8 1/2" for the seat,
    # 2 at 10" for the top. That is correct and is how a solid top this wide is actually made.
    #
    # `clear_height` is the void under each board: 18" of bench less the 1 1/2" seat, and
    # 29 1/2" of desk less the 1" top (5/4 since 2026-10-16) — i.e. the knee space.
    ShelfBank(
        uid="MJ0P713ABN", tag="SB-M-STUDY-BENCH",
        host="FURN-M-STUDY-BENCH",
        material_ref="walnut-shelf-8q",
        thickness=inch(1.5),
        profile="S4S",
        procurement=ShelfProcurement.CUSTOM_MILLED,
        bays=(ShelfBay(width=inch(47), clear_height=inch(14.5), shelf_count=1),),
    ),
    ShelfBank(
        uid="AFXM3DJGX4", tag="SB-M-STUDY-DESK",
        host="FURN-M-STUDY-DESK",
        material_ref="walnut-shelf-5q",
        thickness=inch(1),
        profile="S4S",
        procurement=ShelfProcurement.CUSTOM_MILLED,
        bays=(ShelfBay(width=inch(29), clear_height=inch(28.5), shelf_count=1),),
    ),
    # The fold-down leaf's board. Same stock, same thickness, same lay-up as the
    # desk it butts, out of the SAME FLITCH as SB-M-STUDY-DESK's two boards: the two tops meet
    # in a 20" butt joint at eye level, and a colour jump there is the one defect nobody can
    # unsee. Free to avoid at the rack, impossible to fix afterwards.
    #
    # ** READ THIS BEFORE ORDERING: `haus millwork` PRINTS THIS BOARD'S GRAIN THE WRONG WAY,
    # AND THE MODEL HAS NO FIELD TO CORRECT IT. ** `takeoff/hardwood.py` runs grain along the
    # LONGER plan dimension, which is right for every other shelf in the house and is wrong
    # for the only piece here that is deeper (20") than it is wide (18"). It therefore bills a
    # 2-board lay-up at 9" with the grain running front to back, and what has to be built is a
    # 2-board lay-up at 10" — a 20 3/4" rough face, the desk's own lay-up — with the grain
    # running EAST-WEST, continuous with the desk's.
    #
    # It is not an aesthetic preference. Walnut moves across the grain and not along it, so
    # with the grain running east-west BOTH tops swell and shrink in DEPTH, together, and the
    # butt joint between them stays the width it was cut. Turn the leaf's grain 90 degrees and
    # the whole seasonal movement of an 18" board — call it 3/16" over a heating season — lands
    # in that joint, opening and closing it all year. The end grain showing at the joint is the
    # smaller half of the objection.
    #
    # Board feet are unaffected (same area, same thickness), so nothing downstream is wrong —
    # only the cutting instruction is, and only for this one row.
    #
    # `clear_height` is the void under the deployed leaf, the same 28 1/2" as the desk. That is
    # what the ADA 306 / OSHA knee envelope is measured against and it clears the 27" minimum
    # with 1 1/2" to spare — but the number that actually decides it is the BRACKET, not the
    # board. A Hebgo 287.43.419 is 7 1/16" tall; hung under the leaf at the wall it eats down
    # to ~21" of clear at the back, which is fine over a knee and NOT fine if the arm reaches
    # forward over one. Set the brackets tight to the wall and check the arm against a seated
    # knee on the bench before the blocking goes in — it cannot be moved after.
    ShelfBank(
        uid="T0BJ1M256G", tag="SB-M-STUDY-LEAF",
        host="FURN-M-STUDY-DESK-LEAF",
        material_ref="walnut-shelf-5q",
        thickness=inch(1),
        profile="S4S",
        procurement=ShelfProcurement.CUSTOM_MILLED,
        bays=(ShelfBay(width=inch(18), clear_height=inch(28.5), shelf_count=1),),
    ),
    # --- RM-M-LIVING's fireplace mantel, on FURN-M-FIRE-MANTEL --------------------------
    #
    # A custom-milled walnut shelf, 2 1/4" thick — one brick bed height, so it reads as a
    # single course pulled out — with its underside at 5'-4" and PROUD, not let-in, so the
    # coursing behind it is continuous and never breaks. It caps the surround: 2 1/4" over
    # 64" puts the top of the whole object at 66 1/4".
    #
    # ** THE HOST WAS THE WALL UNTIL 2026-09-06 AND IS NOW A PLACEABLE. ** It was the only
    # wall-hosted ShelfBank in the house, which forced `depth` to be authored here
    # (`resolve/millwork.py::_pocket_depth_m` gives a wall host its CASE POCKET depth — the
    # airgap plus stud bay — which is right for a bookcase wall and meaningless against a
    # 3 5/8" masonry wythe with no pocket at all). FURN-M-FIRE-MANTEL now carries the depth
    # on FT-MANTEL-ELM-46's footprint, so `depth` is DELETED here and `_carcass_depth_m`
    # inherits the 11 1/2" — the SB-M-STUDY-BENCH rule, that the board can never disagree
    # with the carcass it sits in, and one duplicated number fewer.
    #
    # That 11 1/2" is still the measured number: from W-M-E1's gwb at x=35'-5 3/8" out to
    # x=34'-5 7/8", dying on the wall behind and projecting a 6" shelf past the brick face at
    # x=34'-11 7/8". (It was 10"/4 1/2" until 2026-09-06; 4 1/2" is a reveal, not a mantel —
    # nothing stands on it.)
    #
    # ** THE MANTEL MUST BE TIED BACK INTO W-M-E1, AND IT IS NOT A DETAIL THAT CAN BE SKIPPED.
    # ** Work the free body about the brick's front bearing edge at x=34'-11 7/8". The board
    # bears on 3 5/8" of wythe, spans the 1 7/8" gap behind it and dies on the gwb, so its
    # centroid sits 1/4" IN FRONT of that edge: ** at 25.9 lb it overturns under its own
    # weight ** — it does not need a load on it, it needs only to not be held down. At the old
    # 10" depth the centroid was 1/2" behind the edge and a 2.5 lb tip load did it, which is
    # not meaningfully better. So: screws through the gwb into flat blocking laid in W-M-E1's
    # stud bay behind the wythe, taking the back edge down. The lever is 5 1/2" (bearing edge
    # to gwb), so 100 lb leaned on the front lip is 109 lb of tension in that line of
    # fasteners — nothing, once it exists.
    #
    # ** THE BOARD ITSELF IS NOT THE QUESTION. ** 45 1/2" x 2 1/4" gives S = 38.4 in3, so the
    # same 100 lb at 6" is 600 in-lb and 16 psi against elm's (or the walnut it replaced) ~1,000 psi Fb — a factor of
    # 60. Every bit of the margin here is in the hold-down and none of it is in the wood, so
    # sizing the shelf thicker would answer a question nobody asked.
    #
    # ** AND NOTHING IN `haus check` GRADES THE HOLD-DOWN. ** A ShelfBank still resolves to
    # width, depth, thickness and a count and nothing else — `ResolvedShelfBank` carries no
    # position — but since 2026-09-06 the BODY is real: FURN-M-FIRE-MANTEL puts a
    # 45 1/2" x 11 1/2" x 2 1/4" solid at 64"–66 1/4" AFF, so the 3D and the clearance rules
    # can see the mantel at last. What they still cannot see is the overturning above: no
    # check grades a cantilevered placeable's tie-back. This comment and
    # notes/east_breast_bearing.md remain the ONLY record of it, so they have to be right.
    #
    # `shelf_count=1` for SB-M-STUDY-BENCH's reason: a ShelfBay counts horizontal boards
    # INCLUDING the case top, and here the mantel IS the top. `clear_height` is the void under
    # it, and the number that matters is the appliance clearance: 64" less the firebox opening
    # top is the whole of it.
    #
    # ** 19 5/8", NOT 11 5/8", SINCE 2026-09-11. ** The owner reversed that day's own decision
    # to raise the firebox and EQ-M-FIREPLACE's sill went 32" AFF -> 24" (plan/electrical.py
    # carries the reversal and why). The appliance's 20 3/8" rough opening did not change
    # height, so its top went 52 3/8" -> 44 3/8" AFF and the void under a mantel still at 64"
    # gained the same 8". The mantel did NOT move — W-M-FIRE-HEAD grew 11 3/8" -> 19 3/8" to
    # hold the panel's top at 64 15/16" absolute (plan/storeys/main.py) — so this is the only
    # number in this bank the drop touches, and the board, the stock and the grain are all
    # unchanged.
    #
    # Against the Amantii BI-30-XTRASLIM's published 4" mantel rule that is now about 5x,
    # where it was about 3x. That margin is why the projection question (the 4" is quoted with
    # NO projection qualifier anywhere in the industry) is a formality here rather than a
    # risk. It is still on the list of things to get from Amantii in writing; see
    # EQ-T-FIREPLACE-EL.
    #
    # ** "64 AFF" IS EXACT, SETTLED 2026-09-11. ** 19 5/8" is measured to a mantel underside
    # at 64" AFF. `Mount.elevation` is measured off the room's FINISHED floor
    # (`resolve/placeables.py::_floor_elevation`), and RM-M-LIVING's is +15/16", so the host
    # `elevation=inch(64)` resolves to 64 15/16" absolute — exactly W-M-FIRE-HEAD's top, the
    # shelf sitting ON the brick. It was authored `inch(64.9375)` against the old subfloor
    # reading, which applied that 15/16" twice and floated the shelf off the brick at 0 FAIL;
    # plan/placeables.py carries the correction and why.
    #
    # ** 12/4 STOCK, NOT THE STUDY'S 8/4, AND `haus millwork` IS WHAT SAID SO. ** Authored on
    # `walnut-shelf-8q` first, the schedule printed that 2 1/4" finished cannot come out of
    # 8/4, which dresses to 1 1/2" — so the stock is 12/4, which dresses to 2 1/2". Since
    # 2026-10-16 it is `elm-mantel-12q`, American elm to match the slat partition, where it
    # was `walnut-mantel-12q`; same 12/4 stock, same finish.
    #
    # ** ONE BOARD, GENUINELY. ** 45 1/2" x 10" is inside MW-STANDARD.max_board_width (18")
    # even after jointing loss, so this is a one-piece milled mantel and not an edge-glued
    # panel — the only large piece of its kind in the house. `takeoff/hardwood.py` runs the
    # grain along the LONGER plan dimension, which here is the 45 1/2" length, and that is
    # correct: a mantel's grain runs its length.
    #
    # ** THE MONEY IS NOT HERE AND MUST NOT BE, AND THE HOST MOVE IS WHAT CLOSED THAT GAP. **
    # `haus millwork` is an UNPRICED VIEW and a "shelf" row may reference no other priced
    # section (a test enforces it). SB-M-STUDY-BENCH/-DESK put the walnut's dollars in the
    # `[placeables]` row of their host FurnitureType — but a ShelfBank ON A WALL has no host
    # row anywhere, so this board was carried by `finish-fireplace-mantel-walnut` in
    # prices.toml [allowances] instead. Hosting it on FURN-M-FIRE-MANTEL gives it the normal
    # path: `FT-MANTEL-ELM-46` is a `[placeables]` row carrying the same scope, and the
    # allowance is DELETED rather than zeroed — leaving both would bill the mantel twice.
    ShelfBank(
        uid="TPJ2J8VXZJ", tag="SB-M-FIRE-MANTEL",
        host="FURN-M-FIRE-MANTEL",
        material_ref="elm-mantel-12q",
        thickness=inch(2.25),
        profile="S4S",
        procurement=ShelfProcurement.CUSTOM_MILLED,
        bays=(ShelfBay(width=inch(45.5), clear_height=inch(19.625), shelf_count=1),),
    ),
    # --- the mudroom bench's seat, FURN-M-MUD-BENCH -----------------------------------
    #
    # Bought with the bench, not milled (owner, 2026-10-07): the seat is part of the
    # purchased FURN-M-MUD-BENCH and its money is in that `[placeables]` row. The bank stays
    # so the seat's board is still on record; `shelf_count=1` because the seat IS the top.
    ShelfBank(
        uid="STDXY9J49R", tag="SB-M-MUD-BENCH",
        host="FURN-M-MUD-BENCH",
        material_ref="oak-shelf-8q",
        thickness=inch(1.5),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(36), clear_height=inch(16.5), shelf_count=1),),
    ),
    # --- W-M-STRW's notched oak bench, FURN-M-STRW-BENCH: milled from the family red oak -
    ShelfBank(
        uid="CK2PDFB4JH", tag="SB-M-STRW-BENCH",
        host="FURN-M-STRW-BENCH",
        material_ref="oak-8q",
        thickness=inch(1.5),
        profile="S4S",
        procurement=ShelfProcurement.CUSTOM_MILLED,
        bays=(ShelfBay(width=inch(95.875), clear_height=inch(16.5), shelf_count=1),),
    ),
]

# --- the theatre bookcases, IKEA BILLY x4 --------------------------------------------
#
# Bought, not milled (owner, 2026-10-07): a book shelf in a basement media room does not need
# the family oak. Each case's own shelves are in its price, so these banks are
# INCLUDED_IN_HOST and leave `haus millwork`. Six boards per case — five adjustable plus the
# fixed one — over the carcass's ~30" clear width.
BASEMENT_SHELVES = [
    ShelfBank(
        uid="ZJQHBYNFZ3", tag="SB-B-PLAY-BOOK-W1",
        host="FURN-B-PLAY-BOOK-W1",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(30), clear_height=inch(77), shelf_count=6),),
    ),
    ShelfBank(
        uid="DDZP84R2PT", tag="SB-B-PLAY-BOOK-W2",
        host="FURN-B-PLAY-BOOK-W2",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(30), clear_height=inch(77), shelf_count=6),),
    ),
    ShelfBank(
        uid="KRYBE1F0A8", tag="SB-B-PLAY-BOOK-E1",
        host="FURN-B-PLAY-BOOK-E1",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(30), clear_height=inch(77), shelf_count=6),),
    ),
    ShelfBank(
        uid="40MV8CYTFF", tag="SB-B-PLAY-BOOK-E2",
        host="FURN-B-PLAY-BOOK-E2",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(30), clear_height=inch(77), shelf_count=6),),
    ),
]

# --- the bath 1 alcove shelf, FT-BATH1-SHELF-2030 --------------------------------------
#
# 4/4 like the bookcases, and for the same reason. Its DEPTH is the one surprise: the
# carcass is scribed to the tub alcove and is 30" deep to match the tub, not 20" — the
# footprint reads (20" wide, 30" deep), so this is the one shelf in the house that is
# DEEPER THAN IT IS WIDE. The boards therefore run FRONT TO BACK: grain along the 29 1/4"
# (30" less the 3/4" back), a glue-up 18 1/2" wide rather than a 30" panel.
# `takeoff/hardwood.py` derives that orientation rather than taking it on faith — it mills
# every shelf with the grain on the longer plan dimension — so nothing here authors it. In
# locust, whose boards run to ~7", it lays up as a three-board panel, and that is a fact
# worth seeing on the schedule rather than at the mill.
#
# ** WET-ROOM SPEC, FOR THIS SHELF AND SB-S-SUITEBATH ** (owner, 2026-10-16). Both stand at
# a tub's end, and the house oak is RED oak, whose open pores take water. So: black locust
# heartwood only, no sapwood (`locust-shelf-4q`, boards to ~7", so every shelf is a
# glue-up); Type III PVA; a wet-area film finish (catalysed or waterborne poly, not oil
# alone) on all six faces, end grain included, before install; stainless fasteners only;
# no board end on the tub deck or the shower's wet line. Recoat when the film wears.
# ** THIS NEEDS THE OWNER'S EXTRA 2-3 LOCUST LOGS. ** Without them, swap both refs to
# `cherry-shelf-4q`, then to bought white oak 4/4: one line each.
SECOND_SHELVES = [
    ShelfBank(
        uid="JBAEDPFV5Q", tag="SB-S-BATH1",
        # Closed below the vanity counter (2026-09-28): five boards over the 48 3/4" open
        # section, the lowest flush with the counter. Depth is the spec's 29 1/4".
        host="FURN-S-BATH1-SHELF",
        material_ref="locust-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        procurement=ShelfProcurement.CUSTOM_MILLED,
        bays=(ShelfBay(width=inch(18.5), clear_height=inch(48.75), shelf_count=5),),
    ),
    # The suite bath's alcove shelf, open to the west (2026-10-03): SB-S-BATH1's locust and
    # 3/4" stock, eight boards in a 9 3/4" bay. `depth` is left to the host's spec, as there.
    ShelfBank(
        uid="FE3PYXZY53", tag="SB-S-SUITEBATH",
        host="FURN-S-SUITEBATH-RETURN",
        material_ref="locust-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        procurement=ShelfProcurement.CUSTOM_MILLED,
        bays=(ShelfBay(width=inch(9.75), clear_height=inch(84), shelf_count=8),),
    ),
]

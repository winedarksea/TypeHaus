# haus: editable
# Catlin house millwork — the owner-milled red oak, and the species placed around it.
#
# The owner has red oak off family land in southern Minnesota (it was taken for white oak
# until 2026-10-16), effectively unlimited, in 4/4 to 8/4, with boards commonly 12"+ wide and
# some to 18". Its pores are open, so it does only dry interior work: wet-room stools and the
# bath shelves are nosed in locust, and the stools are mostly bought white oak. That supply wins
# on WIDTH and FLATNESS and loses on PROFILE: a one-piece stool, shelf or tread is worth
# milling, and a knife grind plus a molder setup cannot amortise over one house. Base and
# casing are bought and painted (TRIM-STANDARD below), bar a few hardwood accents.
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
    DoorTrim,
    MillworkStandard,
    RoomTrim,
    ShelfBank,
    ShelfBay,
    ShelfProcurement,
    StairLandingMillwork,
    TrimStandard,
)

# The one declaration. Scope is EXT_2X6 alone — 34 of the 41 windows are in scope:
# The kitchen's three are quartz (plan/countertops.py); the east living-room three are ash
# (plan/living_east_run.py). The rest derive bought white oak unless plan/window_stools.py
# names a room override (locust, ash, cherry, or white oak in circulation).
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
    # Base and door casing, derived per room and per door face (resolve/interior_trim.py),
    # 3/4" x 3 1/2" S4S, butt-jointed, flush where base meets leg (2026-10-19). Bought and
    # painted the wall white: finger-jointed pine base, MDF casing. The baths and the plant
    # room take PVC casing (and PVC base where the floor is not tile or vinyl). The sauna keeps
    # locust base and cedar casing. Two hardwood accents: cherry on D-S-SUITE's bedroom face,
    # red oak on D-A-STUDY (it matches the study bridge infill).
    # The base goes in after the hard floors, so there is no shoe; carpet tucks under it.
    # tasks.toml's trim visit names its rows by stock: rename them with the stock.
    #   * Tile rooms take a tile base and vinyl rooms a flash cove: the floor material's
    #     `base_detail`, not a list here.
    #   * Excluded: the basement utility rooms. The garage and the unfinished attic fall out
    #     on their own (unconditioned / no floor finish).
    TrimStandard(
        uid="KXZVF6Z652", tag="TRIM-STANDARD",
        material_ref="mdf-casing",
        base_material_ref="pine-fj-base",
        room_trims=(
            RoomTrim(rooms=("RM-B-SAUNA",), material_ref="locust-trim",
                     casing_material_ref="cedar-sauna-trim"),
            RoomTrim(rooms=("RM-M-BATH1", "RM-M-BATH2", "RM-S-BATH1", "RM-S-SUITEBATH",
                            "RM-S-VANITY", "RM-B-BATH", "RM-A-STUBATH", "RM-S-PLANT"),
                     material_ref="pvc-trim"),
        ),
        door_trims=(
            DoorTrim(doors=("D-S-SUITE",), room="RM-S-SUITE", material_ref="cherry-trim"),
            DoorTrim(doors=("D-A-STUDY",), material_ref="oak-trim"),
        ),
        thickness=inch(0.75),
        base_height=inch(3.5),
        casing_width=inch(3.5),
        reveal=inch(0.1875),
        # 3/4" jamb + 1/4" shim: the leg's inside edge sits 13/16" inside the RO.
        jamb_allowance=inch(1),
        min_leg_width=inch(1.5),
        # Boards come in 8' lengths: `haus millwork` packs the hardwood cuts into them.
        stock_length=ft(8),
        excluded_rooms=("RM-B-FURNACE", "RM-B-ESS", "RM-B-WORKSHOP", "RM-B-GYM"),
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
    # Booth bench cuts come from BuiltInBenchSpec, including its purchased plywood.
    # Only the fixed desk/leaf remain ShelfBanks; their dollars stay in placeables.
    ShelfBank(uid="AFXM3DJGX4", tag="SB-M-STUDY-DESK", host="FURN-M-STUDY-DESK",
              material_ref="walnut-shelf-5q", thickness=inch(1), profile="S4S",
              procurement=ShelfProcurement.CUSTOM_MILLED,
              bays=(ShelfBay(width=inch(29), clear_height=inch(28.5), shelf_count=1),)),
    ShelfBank(uid="T0BJ1M256G", tag="SB-M-STUDY-LEAF", host="FURN-M-STUDY-DESK-LEAF",
              material_ref="walnut-shelf-5q", thickness=inch(1), profile="S4S",
              procurement=ShelfProcurement.CUSTOM_MILLED,
              bays=(ShelfBay(width=inch(19.625), clear_height=inch(28.5), shelf_count=1),)),
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
    # inherits the 11 1/2" — the SB-M-STUDY-DESK rule, that the board can never disagree
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
    # `shelf_count=1` for SB-M-STUDY-DESK's reason: a ShelfBay counts horizontal boards
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
    # section (a test enforces it). SB-M-STUDY-DESK/-LEAF put the walnut's dollars in the
    # `[placeables]` row of their host FurnitureType — but a ShelfBank ON A WALL has no host
    # row anywhere, so this board was carried by `finish-fireplace-mantel-walnut` in
    # prices.toml [allowances] instead. Hosting it on FURN-M-FIRE-MANTEL gives it the normal
    # path: `FT-MANTEL-ELM-46` is a `[placeables]` row carrying the same scope, and the
    # allowance is DELETED rather than zeroed — leaving both would bill the mantel twice.
    ShelfBank(
        uid="TPJ2J8VXZJ", tag="SB-M-FIRE-MANTEL",
        host="FURN-M-FIRE-MANTEL",
        part="mantel",
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

# --- the tub-end alcove shelves, FT-BATH1-SHELF-2030 and FT-SUITEBATH-SHELF-1130 --------
#
# Both carcasses are 30" deep to match the tub. 29" deep shelves in locust (boards to ~7")
# meant 13 glue-ups, so since 2026-10-18 (owner) the shelves are bought sheet:
# `maple-ply-prefin-34` behind a 3/4" solid locust nosing, billed at the spec's 29 1/4" (the
# shop rips the nosing's 3/4" off). The nosings and the carcass face strips are the only
# locust; they bill as the furniture types' `cut_list`.
#
# ** WET-ROOM SPEC ** (owner, 2026-10-16). Plywood: veneer core, every cut edge sealed with
# a wet-area poly before install. Locust: heartwood only, the same film on all six faces,
# end grain included. Stainless pins and fasteners; recoat when the film wears.
SECOND_SHELVES = [
    ShelfBank(
        uid="JBAEDPFV5Q", tag="SB-S-BATH1",
        # Closed below the vanity counter (2026-09-28): five boards over the 48 3/4" open
        # section, the lowest flush with the counter.
        host="FURN-S-BATH1-SHELF",
        material_ref="maple-ply-prefin-34",
        thickness=inch(0.75),
        profile="S4S",
        procurement=ShelfProcurement.PURCHASED_SEPARATELY,
        bays=(ShelfBay(width=inch(18.5), clear_height=inch(48.75), shelf_count=5),),
    ),
    # The suite bath's alcove shelf, open to the west (2026-10-03): eight boards in a
    # 9 3/4" bay, the same stock and nosing as SB-S-BATH1.
    ShelfBank(
        uid="FE3PYXZY53", tag="SB-S-SUITEBATH",
        host="FURN-S-SUITEBATH-RETURN",
        material_ref="maple-ply-prefin-34",
        thickness=inch(0.75),
        profile="S4S",
        procurement=ShelfProcurement.PURCHASED_SEPARATELY,
        bays=(ShelfBay(width=inch(9.75), clear_height=inch(84), shelf_count=8),),
    ),
]


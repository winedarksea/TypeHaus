# haus: editable
# Catlin house millwork — the owner-milled white oak.
#
# The owner has white oak off family land in southern Minnesota at roughly $2/sf rough
# milled, in 4/4 and 8/4, with boards commonly 12"+ wide and some to 18". That supply wins
# on WIDTH and FLATNESS and loses on PROFILE: a one-piece stool, shelf or tread is worth
# milling, and a knife grind plus a molder setup for baseboard or casing cannot amortise
# over one house. So this file takes off the winners and nothing else —
# `finish-interior-trim-and-baseboard` stays a prices.toml lump on purpose.
#
# Nothing here authors a stool. `MillworkStandard` declares the scope and the resolver
# derives one per in-scope window, exactly as `EaveTrim` derives fascia off the roof plane:
# the 45 windows sit in four assemblies of four different thicknesses (13.885" / 14.540" /
# 14.050" / 8.135"), so a single authored depth would be wrong for three of them and would
# go wrong again the first time a foam lift or a girt depth moved.

from typehaus import ft, inch
from typehaus.model import MillworkStandard, ShelfBank, ShelfBay

# The one declaration. Scope is CATLIN_EXT_2X6 alone — 39 of the 45 windows:
#   * PLANT_EXT_2X6_HUMID (3) is the plant room, which runs at 70% RH by design. Oak in
#     that room is a cupped stool and a black tannin stain, not millwork.
#   * SAUNA_LINER_ON_GARDEN_FRAMED (1) is lined in basswood for a burn-safety reason
#     (low-conductivity species, plan/assemblies.py) that a hardwood stool would defeat.
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
        # 8/4 dressed. A 3/4" board this wide would cup: the interior return on an outie
        # window runs 12 5/8" less the frame depth, which is most of a foot of board.
        stool_thickness=inch(1.5),
        stool_overhang=inch(0.75),
        # 1" of horn each side. The apron and the casing legs die onto it.
        stool_horn=inch(1),
        stool_profile="eased",
        stool_assemblies=("CATLIN_EXT_2X6",),
        # 28 oak treads: ST-M2S (13) and ST-S2A (15, three of them winders). ST-B2M is the
        # basement flight and is carpeted, ST-G-SERVICE is the garage's.
        tread_material_ref="oak-tread",
        tread_stairs=("ST-M2S", "ST-S2A"),
        max_board_width=inch(18),
    ),
]

# --- the attic study built-in, W-A-SN --------------------------------------------------
#
# CATLIN_INT_2X4_BOOKCASE_12: a 9 7/8" clear pocket (the `case-pocket` AIRGAP over the
# `stud-case` bay), 12'-9 3/8" of run. The BOM legitimately sees only the case-back sheet
# and the nailers — this is the shelf stock it never saw.
#
# The five bays and their tops were already worked out in the comment table at
# plan/storeys/attic.py; this promotes that table from prose to data. Each bay is topped off
# the usable height at its EAST end as the rake steps down. The tops come from
# `1 1/2" + (36' - x)/2`, less ~3" of build-up and seat, rounded down to the nearest 6":
#     1  22'-8"  -> 25'-4"      usable 5'-5 1/2"   case top 5'-0"
#     2  25'-4"  -> 28'-0"      usable 4'-1 1/2"   case top 3'-6"
#     3  28'-0"  -> 30'-8"      usable 2'-9 1/2"   case top 2'-6"
#     4  30'-8"  -> 33'-4"      usable 1'-5 1/2"   case top 1'-0"
#     5  33'-4"  -> 35'-5 3/8"  usable 4 1/8"      NO CASE — the rake closes this bay out
# IT IS A LOW BOOKCASE, NOT A WALL OF SHELVES: the study's east end is under the rake
# rather than under a 5'-0" wall, and four short bays plus a closed-out fifth is what the
# geometry leaves. Widths are CLEAR between 3/4" partitions: 2'-8" pitch less 3/4" is
# 2'-7 1/4"; bay 5's 2'-1 3/8" pitch less 3/4" is 2'-0 5/8".
#
# 8/4, and one board: a 9 7/8" pocket takes a single board with room to spare against the
# 18" supply. 1 1/2" fixed shelves in dados need no stiffener and no edge banding at a
# 2'-6" bay, which is the whole argument for owner stock here — a 3/4" shelf at this span
# would want a face frame that nobody would then see the oak through.
#
# Counts are a ~12" pitch over each bay's own height, the case top included (a case top is
# cut from the same stock at the same width). Per-bay rather than one spacing: a uniform
# pitch does not divide into a raked bay, and bay 5 is 3'-0" shorter than bay 1.
ATTIC_SHELVES = [
    ShelfBank(
        uid="ZSR38F5C8F", tag="SB-A-STUDY",
        host="W-A-SN",
        material_ref="oak-shelf-8q",
        thickness=inch(1.5),
        profile="S4S",
        # THREE BAYS, not five: bay 5 (x 33'-4"..35'-5 3/8") has only 4 1/8" of usable
        # height. Bay 4 (x 30'-8"..33'-4") is dropped on the owner's call: 1'-0" of clear
        # height is two shelves you cannot see into, at the end of a run you have to stoop
        # to reach, and it reads as a leftover rather than as storage. East of 30'-8" the
        # wall is a raked closure carrying no casework — see W-A-SN in storeys/attic.py.
        # Counts stay a ~12" pitch over each bay's own height, the case top included.
        bays=(
            ShelfBay(width=ft(2, 7.25), clear_height=ft(5), shelf_count=5),
            ShelfBay(width=ft(2, 7.25), clear_height=ft(3, 6), shelf_count=4),
            ShelfBay(width=ft(2, 7.25), clear_height=ft(2, 6), shelf_count=3),
        ),
    ),
]

# --- the main pantry, FURN-M-PANTRY-SHELVES --------------------------------------------
#
# See notes/pantry_climbable_shelving.md and the FT-KIT-PANTRY-SHELVES-70 source.
#
# 1. THIS SHELF IS DESIGNED TO BE CLIMBED, so its thickness is a STRUCTURAL decision, not a
#    finish one. It is 8/4 rather than the 4/4 the other light-duty cases get: a climbing
#    250 lb point load over the gabled ~34 3/4" half-span is what governs, and 4/4 is the
#    wrong answer to that question. What the 8/4 bought, beyond passing, is that STRENGTH
#    stopped being the argument for the gable — 1 1/2" oak carries the full 70 1/4" span at
#    ~650 psi. THE GABLE STAYS ANYWAY, on deflection: the full span is ~0.223" under
#    250 lb and this shelf is graded as a FLOOR, so L/360 is 0.195" and it misses. Gabled
#    it is ~0.027". THE CLEATS AND THE BLOCKING STAY EITHER WAY, and the bays below are the
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
#    hold boards past 18 3/4", raise `max_board_width` above and both panels in this house
#    (here and SB-S-BATH1) become single boards with no other edit.
#
# Six boards per bay, the case top included, on the graduated pitch the type specifies —
# ~20" bottom bay, 12"-14" middle, 8"-10" top — over the 7'-0" carcass.
# --- RM-M-BATH2's vanity sink base, FX-M-BATH2-SINK ------------------------------------
#
# One shelf inside the 30" sink base at the north end of the 54" vanity. The owner asked
# for drawer AND shelf space; the drawers are the 24" bank at the south end and
# are NOT modelled — the engine has no drawer vocabulary, and inventing one for six boxes is
# not the trade. The shelf is, because a shelf IS a board: it has a species, a thickness, a
# cut length and a mill day, and `takeoff/hardwood.py` bills it with the rest of the
# owner-milled white oak instead of disappearing into a cabinetry lump.
#
# ** `host` IS A FIXTURE, WHICH IS LEGAL AND IS WORTH KNOWING. ** `ShelfBank.host` reads
# "a wall tag or a placeable tag", and `resolve/millwork.py` builds its placeable map from
# `model.canvas_objects` — which carries Fixtures alongside Furniture. So a vanity can host
# its own casework without a shadow FurnitureType standing inside it.
#
# ** `depth` IS AUTHORED, AND MUST BE. ** The derivation for a placeable host runs through
# `_carcass_depth_m(placeable, furniture_types)`, and this host is a FixtureType, which is
# not in that map — an underived depth is a hard finding, not a silent zero. 18 1/2" is the
# honest clear anyway: 21" of carcass less a 3/4" back and a 1 3/4" scribe/trap set-off.
# One board wide (supply runs to 18"+ and this is 18 1/2" long-grain across a 28 1/2" span),
# 4/4 like the bookcases — it carries towels and bottles, not people.
#
# `clear_height` is the sink base's interior: 34 1/2" of carcass less a 4 1/2" toe kick and
# the 3/4" counter substrate. The shelf sits below the trap, which is why there is ONE and
# not two — `shelf_count=2` is that shelf plus the case top, the convention `ShelfBay`
# documents ("the number of HORIZONTAL BOARDS in the bay, the case top included").
# THE FIVE OTHER BATHROOMS' VANITY SHELVES: same reasoning as SB-M-BATH2-VAN above,
# applied to the cabinets that replaced this house's bare lavatories.
# Each is the ONE adjustable shelf inside a sink base -- `shelf_count=2` is that shelf plus
# the case top, per ShelfBay's own convention -- and each is why those vanities could be
# bought as plain two-door boxes instead of drawer banks. A drawer base runs about 1.5x a
# door base of the same width, and a full-depth shelf recovers most of the usable volume
# for the price of a board the owner already owns.
#
# `depth` is authored on every one, and must be: the derivation for a placeable host runs
# through `_carcass_depth_m`, which is keyed on FurnitureTypes, and every host here is a
# FixtureType. The number is the carcass less a 3/4" back and a 1 3/4" scribe/trap set-off
# -- 18 1/2" clear in a 21" cabinet, 15 1/2" in an 18" one. `width` is the carcass less
# 1 1/2" of case sides. All 4/4 white oak, S4S: these carry towels and bottles.

MAIN_SHELVES = [
    ShelfBank(
        uid="3EWQ9BGVH8", tag="SB-M-BATH1-VAN",
        # 24" x 18" carcass, the smallest vanity in the house.
        host="FX-M-BATH1-LAV",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(22.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="830F8WP640", tag="SB-M-BATH2-VAN",
        host="FX-M-BATH2-SINK",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        depth=inch(18.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="E97F8XSSZ5", tag="SB-M-PANTRY",
        host="FURN-M-PANTRY-SHELVES",
        material_ref="oak-shelf-8q",
        thickness=inch(1.5),
        profile="S4S",
        bays=(
            ShelfBay(width=inch(34.75), clear_height=ft(7), shelf_count=6),
            ShelfBay(width=inch(34.75), clear_height=ft(7), shelf_count=6),
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
    # 29 1/2" of desk less the 1 1/2" top — i.e. the knee space.
    ShelfBank(
        uid="MJ0P713ABN", tag="SB-M-STUDY-BENCH",
        host="FURN-M-STUDY-BENCH",
        material_ref="walnut-shelf-8q",
        thickness=inch(1.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(47), clear_height=inch(14.5), shelf_count=1),),
    ),
    ShelfBank(
        uid="AFXM3DJGX4", tag="SB-M-STUDY-DESK",
        host="FURN-M-STUDY-DESK",
        material_ref="walnut-shelf-8q",
        thickness=inch(1.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(29), clear_height=inch(28), shelf_count=1),),
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
    # `clear_height` is the void under the deployed leaf, the same 28" as the desk. That is
    # what the ADA 306 / OSHA knee envelope is measured against and it clears the 27" minimum
    # with 1" to spare — but the number that actually decides it is the BRACKET, not the
    # board. A Hebgo 287.43.419 is 7 1/16" tall; hung under the leaf at the wall it eats down
    # to ~21" of clear at the back, which is fine over a knee and NOT fine if the arm reaches
    # forward over one. Set the brackets tight to the wall and check the arm against a seated
    # knee on the bench before the blocking goes in — it cannot be moved after.
    ShelfBank(
        uid="T0BJ1M256G", tag="SB-M-STUDY-LEAF",
        host="FURN-M-STUDY-DESK-LEAF",
        material_ref="walnut-shelf-8q",
        thickness=inch(1.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(18), clear_height=inch(28), shelf_count=1),),
    ),
    # --- the mudroom bench's seat, FURN-M-MUD-BENCH -----------------------------------
    #
    # Same reason as the two above, and the same shape of fix. FURN-M-MUD-BENCH is a
    # `Furniture` on a library FurnitureType, and `takeoff/hardwood.py` admits exactly five
    # sources — window stools, ShelfBanks, stair treads, `wood_surfaces` rows and timber
    # solids. A Furniture is none of them, so the biggest single oak board on this floor
    # was reaching `haus millwork` as nothing at all. A ShelfBank hosted on the furniture
    # tag is how a BOARD gets into the cut list.
    #
    # `shelf_count=1` for the reason spelled out at SB-M-STUDY-BENCH: a ShelfBay counts
    # horizontal boards INCLUDING the case top, and on a bench the seat IS the top.
    #
    # `depth` deliberately omitted — the host is a FurnitureType, so `_carcass_depth_m`
    # inherits its 18" footprint depth and the board can never disagree with the carcass.
    # At 18" the seat is past `MW-STANDARD.max_board_width` once jointing loss is taken, so
    # it lays up as an edge-glued panel of 2 boards at ~9 1/2", which is how a solid seat
    # this wide is actually made.
    #
    # `clear_height` is the void under it: the type's 18" of bench less the 1 1/2" seat.
    #
    # No dollar here, and that is deliberate: `haus millwork` is an UNPRICED VIEW and a
    # "shelf" row may reference no other priced section (a test enforces it). The bench's
    # money is already in its `[placeables]` row in prices.toml, which is written to
    # include the seat — the same accounting as FT-STUDY-BENCH, not the owner-milled
    # family-stock case the pantry shelves are.
    ShelfBank(
        uid="STDXY9J49R", tag="SB-M-MUD-BENCH",
        host="FURN-M-MUD-BENCH",
        material_ref="oak-shelf-8q",
        thickness=inch(1.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(36), clear_height=inch(16.5), shelf_count=1),),
    ),
]

# --- the theatre bookcases, FT-BOOKCASE-32-90 x4 ---------------------------------------
#
# 12" deep, so a single board with 6" to spare, and 4/4: these carry books, not people.
# Clear width is the 2'-8" carcass less two 3/4" sides. Six boards each — the type's
# `shelving(shelves=5)` symbol plus the case top.
BASEMENT_SHELVES = [
    ShelfBank(
        uid="6BNKG0ZT0K", tag="SB-B-BATH-VAN",
        # 36" x 18" carcass; the depth is the door swing's, not a preference.
        host="FX-B-BATH-LAV",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(34.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="ZJQHBYNFZ3", tag="SB-B-PLAY-BOOK-W1",
        host="FURN-B-PLAY-BOOK-W1",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        bays=(ShelfBay(width=inch(30.5), clear_height=ft(7, 6), shelf_count=6),),
    ),
    ShelfBank(
        uid="DDZP84R2PT", tag="SB-B-PLAY-BOOK-W2",
        host="FURN-B-PLAY-BOOK-W2",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        bays=(ShelfBay(width=inch(30.5), clear_height=ft(7, 6), shelf_count=6),),
    ),
    ShelfBank(
        uid="KRYBE1F0A8", tag="SB-B-PLAY-BOOK-E1",
        host="FURN-B-PLAY-BOOK-E1",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        bays=(ShelfBay(width=inch(30.5), clear_height=ft(7, 6), shelf_count=6),),
    ),
    ShelfBank(
        uid="40MV8CYTFF", tag="SB-B-PLAY-BOOK-E2",
        host="FURN-B-PLAY-BOOK-E2",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        bays=(ShelfBay(width=inch(30.5), clear_height=ft(7, 6), shelf_count=6),),
    ),
]

# --- the bath 1 alcove shelf, FT-BATH1-SHELF-2030 --------------------------------------
#
# 4/4 like the bookcases, and for the same reason. Its DEPTH is the one surprise: the
# carcass is scribed to the tub alcove and is 30" deep to match the tub, not 20" — the
# footprint reads (20" wide, 30" deep), so this is the one shelf in the house that is
# DEEPER THAN IT IS WIDE. The boards therefore run FRONT TO BACK: grain along the 30", a
# glue-up 18 1/2" wide rather than a 30" panel, which is two boards with one narrow rip
# instead of a full-width layup. `takeoff/hardwood.py` derives that orientation rather than
# taking it on faith — it mills every shelf with the grain on the longer plan dimension —
# so nothing here authors it. It still lays up as a panel — 18 1/2" finished wants a 19 1/4"
# rough face and the supply is 18" — and that is a fact worth seeing on the schedule rather
# than at the mill.
SECOND_SHELVES = [
    ShelfBank(
        uid="FT01G11CY0", tag="SB-S-BATH1-VAN",
        # The 30" SINK BASE half of the 48" vanity; the north 18" is a drawer
        # bank and is not shelved. 21" carcass, so 18 1/2" clear.
        host="FX-S-BATH1-LAV",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        depth=inch(18.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="XT028WRQR2", tag="SB-S-SUITEBATH-VAN",
        host="FX-S-SUITEBATH-LAV",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        depth=inch(18.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="Q97KQAVZHT", tag="SB-S-VANITY-VAN1",
        # The alcove's two 30" bases under one 61" double top: two cabinets,
        # so two banks. 18" carcasses, so 15 1/2" clear.
        host="FX-S-VANITY-LAV1",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="BHTA4WVJDW", tag="SB-S-VANITY-VAN2",
        host="FX-S-VANITY-LAV2",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="JBAEDPFV5Q", tag="SB-S-BATH1",
        host="FURN-S-BATH1-SHELF",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        bays=(ShelfBay(width=inch(18.5), clear_height=ft(7), shelf_count=6),),
    ),
]

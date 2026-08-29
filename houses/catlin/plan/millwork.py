# haus: editable
# Catlin house millwork — the owner-milled white oak, 2026-08-28.
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
# what `takeoff/hardwood.py` reads for the glue_up column.
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
        # basement flight and is carpeted, ST-G-SERVICE is the garage's. Until this was
        # authored the split lived only in a prices.toml comment, where nothing could check
        # it and where it had already drifted one revision out of date.
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
# the usable height at its EAST end as the 4:12 rake steps down:
#     1  22'-8"  -> 25'-4"      case top 7'-6"
#     2  25'-4"  -> 28'-0"      case top 7'-0"
#     3  28'-0"  -> 30'-8"      case top 6'-0"
#     4  30'-8"  -> 33'-4"      case top 5'-6"
#     5  33'-4"  -> 35'-5 3/8"  case top 4'-6"
# Widths are CLEAR between 3/4" partitions: 2'-8" pitch less 3/4" is 2'-7 1/4"; bay 5's
# 2'-1 3/8" pitch less 3/4" is 2'-0 5/8".
#
# 8/4, and no glue-up: a 9 7/8" pocket takes a single board with room to spare against the
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
        bays=(
            ShelfBay(width=ft(2, 7.25), clear_height=ft(7, 6), shelf_count=8),
            ShelfBay(width=ft(2, 7.25), clear_height=ft(7), shelf_count=7),
            ShelfBay(width=ft(2, 7.25), clear_height=ft(6), shelf_count=6),
            ShelfBay(width=ft(2, 7.25), clear_height=ft(5, 6), shelf_count=6),
            ShelfBay(width=ft(2, 0.625), clear_height=ft(4, 6), shelf_count=5),
        ),
    ),
]

# --- the main pantry, FURN-M-PANTRY-SHELVES --------------------------------------------
#
# TWO OPEN DECISIONS LIVE HERE, and both are deliberately left visible rather than answered
# quietly. See notes/pantry_climbable_shelving.md and the FT-KIT-PANTRY-SHELVES-70 source.
#
# 1. THIS SHELF IS DESIGNED TO BE CLIMBED, so its thickness is a STRUCTURAL decision, not a
#    finish one. The type as built is 3/4" birch ply on continuous 1x3 cleats with a
#    full-height mid-span gable and a 1x3 hardwood nose — the only hardwood in it today is
#    ~41 LF of nose that nothing quantifies. Scheduling solid oak instead is what is
#    authored here, at 8/4 rather than the 4/4 the other light-duty cases get: a climbing
#    250 lb point load over the gabled ~34 3/4" half-span is what governs, and 4/4 is the
#    wrong answer to that question. THE CLEATS AND THE MID-SPAN GABLE STAY EITHER WAY —
#    they are what make the 70 1/4" run legal to stand on, and the bays below are the two
#    half-spans the gable creates, not one 70" shelf.
# 2. THE CARCASS IS 24" DEEP, which is past the 18" the supply can produce, so every shelf
#    is a two-board edge glue-up. `depth` is deliberately NOT authored here: the bank
#    inherits the type's 24" footprint and `haus millwork` raises the glue_up flag, which
#    is the flag existing for exactly this. Reducing the shelf to 17 1/2" would make each
#    one a single board (and make the back of the stack reachable), but 24" is the owner's
#    recorded decision of 2026-08-24 with a written rationale, so it is not something this
#    file gets to quietly overturn.
#
# Six boards per bay, the case top included, on the graduated pitch the type specifies —
# ~20" bottom bay, 12"-14" middle, 8"-10" top — over the 7'-0" carcass.
MAIN_SHELVES = [
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
]

# --- the theatre bookcases, FT-BOOKCASE-32-90 x4 ---------------------------------------
#
# 12" deep, so a single board with 6" to spare, and 4/4: these carry books, not people.
# Clear width is the 2'-8" carcass less two 3/4" sides. Six boards each — the type's
# `shelving(shelves=5)` symbol plus the case top.
BASEMENT_SHELVES = [
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
# footprint reads (20" wide, 30" deep). That is 12" past the 18" supply, so this one glues
# up too, which is a fact worth seeing on the schedule rather than discovering at the mill.
SECOND_SHELVES = [
    ShelfBank(
        uid="JBAEDPFV5Q", tag="SB-S-BATH1",
        host="FURN-S-BATH1-SHELF",
        material_ref="oak-shelf-4q",
        thickness=inch(0.75),
        profile="S4S",
        bays=(ShelfBay(width=inch(18.5), clear_height=ft(7), shelf_count=6),),
    ),
]

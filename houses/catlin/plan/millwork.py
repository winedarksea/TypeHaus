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
# the usable height at its EAST end as the rake steps down. ** RE-DERIVED 2026-08-29 FOR THE
# 6:12 ROOF. ** The tops came from `5'-0" + (36' - x)/3` and are now `1 1/2" + (36' - x)/2`,
# less the same ~3" of build-up and seat, rounded down to the nearest 6":
#     1  22'-8"  -> 25'-4"      usable 5'-5 1/2"   case top 5'-0"
#     2  25'-4"  -> 28'-0"      usable 4'-1 1/2"   case top 3'-6"
#     3  28'-0"  -> 30'-8"      usable 2'-9 1/2"   case top 2'-6"
#     4  30'-8"  -> 33'-4"      usable 1'-5 1/2"   case top 1'-0"
#     5  33'-4"  -> 35'-5 3/8"  usable 4 1/8"      NO CASE — the rake closes this bay out
# ** THE RUN IS A LOW BOOKCASE NOW, NOT A WALL OF SHELVES. ** That is the honest consequence
# of taking the knee wall out: the study's east end is under the rake rather than under a
# 5'-0" wall, and four short bays plus a closed-out fifth is what the geometry leaves. The
# cut list below still bills what is drawn; nobody should read the old 7'-6" tops into it.
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
        # ** RE-CUT 2026-08-29 FOR THE 6:12 RAKE — FOUR BAYS, NOT FIVE. ** The tops above
        # are `1 1/2" + (36' - x)/2` less the build-up, rounded down to 6"; bay 5 (x 33'-4"
        # to 35'-5 3/8") has 4 1/8" of usable height and is closed out rather than shelved.
        # Counts stay a ~12" pitch over each bay's own height, the case top included.
        bays=(
            ShelfBay(width=ft(2, 7.25), clear_height=ft(5), shelf_count=5),
            ShelfBay(width=ft(2, 7.25), clear_height=ft(3, 6), shelf_count=4),
            ShelfBay(width=ft(2, 7.25), clear_height=ft(2, 6), shelf_count=3),
            ShelfBay(width=ft(2, 7.25), clear_height=ft(1), shelf_count=2),
        ),
    ),
]

# --- the main pantry, FURN-M-PANTRY-SHELVES --------------------------------------------
#
# BOTH OF THIS BANK'S OPEN QUESTIONS WERE ANSWERED ON 2026-08-29. See
# notes/pantry_climbable_shelving.md and the FT-KIT-PANTRY-SHELVES-70 source.
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
#    18" is the EDGE of the supply and the schedule says so: a finished 18" face needs an
#    18 3/4" rough board once an edge is straight-lined and the other jointed, so
#    `haus millwork` still raises the flag, now reading "needs a 18.75" rough board; the
#    supply is 18.00"". That is the honest instruction — hand-pick the widest boards in the
#    stack for this bank — and not the same statement as the 24" two-board glue-up it
#    replaced.
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
# footprint reads (20" wide, 30" deep), so this is the one shelf in the house that is
# DEEPER THAN IT IS WIDE. The boards therefore run FRONT TO BACK: grain along the 30", a
# glue-up 18 1/2" wide rather than a 30" panel, which is two boards with one narrow rip
# instead of a full-width layup. `takeoff/hardwood.py` derives that orientation rather than
# taking it on faith — it mills every shelf with the grain on the longer plan dimension —
# so nothing here authors it. It still carries the flag (18 1/2" finished wants a 19 1/4"
# rough board), and that is a fact worth seeing on the schedule rather than at the mill.
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

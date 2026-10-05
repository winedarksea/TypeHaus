# haus: editable
# Catlin house countertops — the work surfaces over the casework.
#
# Split out of plan/millwork.py rather than living in it: that file is the owner-milled
# HARDWOOD (stools, shelves, treads — stock a sawyer cuts), and a countertop is a purchased
# fabricated slab set by the yard that cut it. Two subs, two trades, two files.
#
# ** WHAT WAS PROSE UNTIL THIS FILE GREW THESE ELEMENTS: ** the house's stone was a
# HAND FIGURE in a prices.toml comment, added up by a reader off the cabinet schedule, and
# the peninsula's overhang rule was a paragraph in plan/assemblies.py that nothing could
# check. Both are derived now. Each top names the placeables it covers and the resolver
# derives the slab from them, so moving a cabinet moves the square footage and the estimate
# with it (→ resolve/millwork.py).
#
# THE RUNS ARE AUTHORED RATHER THAN GROWN, and this kitchen is exactly why: the peninsula's
# bases butt FURN-M-KIT-CORNER-PEN's leg, so a walk that merged everything it touched would
# hand the fabricator one slab across the range. Which cabinets share a slab is a seam
# decision.
#
# Not here: the four one-piece solid-surface vanity tops (FX-VANITY-24/30/36-*), which are
# moulded with their bowls and bought boxed with the cabinet — they bill in [placeables] as
# part of the fixture, and modelling a top over them would bill them twice. The two
# FABRICATED vanity decks below are the exception, and are the reason the split exists.

from typehaus import ft, inch
from typehaus.model import Countertop, WindowStool

MAIN_COUNTERTOPS = [
    # The north run and the NE corner as one L slab: B12, the dishwasher, the 36" sink base,
    # B18, and FURN-M-KIT-CORNER-NE, whose east leg carries the slab to
    # y=32'-3 3/8" beside the range. 25" deep: 24" of carcass and 1" of oversail; an L host
    # oversails only its notch faces.
    Countertop(
        uid="GQ3B84T2WH", tag="CT-M-KIT-N",
        cutouts=("FX-M-KITCH-SINK",),
        hosts=("FURN-M-KIT-E1", "APPL-M-DW", "FURN-M-KIT-SINKBASE", "FURN-M-KIT-E2",
               "FURN-M-KIT-CORNER-NE"),
        material_ref="quartz-counter",
        thickness=inch(1.181),  # 3 cm
        overhang=inch(1),
    ),
    # The peninsula-corner carousel, both legs: the east leg to the range, the peninsula leg to the seam at x=32'-3 3/8". A separate slab because a slide-in range
    # interrupts the stone, and the seam is where the free-standing bases start.
    Countertop(
        uid="WRDEA4N59W", tag="CT-M-KIT-E",
        hosts=("FURN-M-KIT-CORNER-PEN",),
        material_ref="quartz-counter",
        thickness=inch(1.181),
        overhang=inch(1),
    ),
    # ** THE PENINSULA IS ONE NOTCHED SLAB. ** 1" over the drawer fronts to the north, and a
    # 15" seating cantilever behind the bases for the first 73 1/2" from the west end panel,
    # which leaves 25" clear to the tall pantry's nominal west face for its doors and
    # swing-out racks. 15" is past quartz's 14" unsupported cap, so five hidden flat bars
    # carry it (FURN-M-KIT-PEN-BRACKET1..5, notes/kitchen_stock_cabinet_details.md K6). No
    # seam on the knee line: that is the weakest place in the stone.
    Countertop(
        uid="YNNE7K95XB", tag="CT-M-KIT-PENINSULA",
        hosts=("FURN-M-KIT-PEN-END", "FURN-M-KIT-PEN-B36", "FURN-M-KIT-PEN-B24-W",
               "FURN-M-KIT-PEN-B24-E"),
        material_ref="quartz-counter",
        thickness=inch(1.181),
        overhang=inch(1),
        depth=inch(40),
        unsupported_overhang=inch(15),
        cantilever_side="back",
        cantilever_length=inch(73.5),
        support="brackets",
    ),
    # The living room's two live-edge white oak slabs (plan/living_east_run.py), 2" over a
    # 1/2" sub-top, 16 1/2" nominal: 1" over the fronts, the natural edge <= 1 1/2" at its
    # widest. The south slab covers its 2 1/8" wall filler; the north ends at the tall
    # bank across a 1/8" sealed joint. The window stools meet the back edge.
    Countertop(
        uid="N3E070DD41", tag="CT-M-LIV-E-S",
        hosts=("FURN-M-LIV-E-END-S", "FURN-M-LIV-E-B36-E1", "FURN-M-LIV-E-B36-S",
               "FURN-M-LIV-E-FILLER-S"),
        material_ref="live-edge-white-oak",
        thickness=inch(2),
        overhang=inch(1),
        length=inch(74.625),
        profile="live-edge",
    ),
    Countertop(
        uid="TPTH3QMGAY", tag="CT-M-LIV-E-N",
        hosts=("FURN-M-LIV-E-END-N", "FURN-M-LIV-E-B36-E2", "FURN-M-LIV-E-B36-E3",
               "FURN-M-LIV-E-B36-MID", "FURN-M-LIV-E-B36-PANTRY"),
        material_ref="live-edge-white-oak",
        thickness=inch(2),
        overhang=inch(1),
        length=inch(144.625),
        profile="live-edge",
    ),
    # RM-M-BATH2's deck. One of the two vanity tops in the house that is FABRICATED rather
    # than moulded with its bowl, which is what puts it in this list and the other four in
    # [placeables]. 19" over an 18" carcass — the type's `source` still says 22", which it
    # was until the cabinet was narrowed from 51 x 21 to 48 x 18 on 2026-09-09; the top
    # follows the cabinet here rather than a stale sentence.
    Countertop(
        uid="TKX0M17VZQ", tag="CT-M-BATH2-VANITY",
        hosts=("FX-M-BATH2-SINK",),
        material_ref="quartz-counter",
        thickness=inch(1.181),
        overhang=inch(1),
    ),
]

# RM-S-BATH1's deck — the other fabricated one, 22" over the 21" carcass, as its type says.
SECOND_COUNTERTOPS = [
    Countertop(
        uid="8TV9EHG5TV", tag="CT-S-BATH1-VANITY",
        hosts=("FX-S-BATH1-LAV",),
        material_ref="quartz-counter",
        thickness=inch(1.181),
        overhang=inch(1),
    ),
]

# --- quartz window stools: slab-yard remnants -------------------------------------------
#
# The four plant-room windows sit in PLANT_EXT_2X6_HUMID, which MW-STANDARD leaves out: oak
# cups and tannin-stains at 70% RH (plan/millwork.py). So each gets a 3 cm remnant of the
# vanity stone instead, cut by the same yard. WIN-M-KITCH gets the same stone stool at the
# kitchen sink. They bill as quartz in [countertops]; `haus millwork` skips them (not
# custom-milled).
#
# `depth` is derived from the wall, as the oak ones are. Same 3/4" overhang and 1" horn.
# DRAINAGE: the sill pan (TR-CATLIN-PLANT-OPENING) laps OVER the stool's back edge and the
# stone is set with a slight fall to the room, no sealant bead at the back — the impervious
# stool is the pan's discharge surface, not a dam. Kerf a drip under the eased front edge.
PLANT_STOOLS = [
    WindowStool(uid="XP74RX3EKK", tag="STOOL-WIN-S-PLANT1", window_ref="WIN-S-PLANT1",
                material_ref="quartz-counter", thickness=inch(1.181),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="TCHNPGC1RT", tag="STOOL-WIN-S-PLANT2", window_ref="WIN-S-PLANT2",
                material_ref="quartz-counter", thickness=inch(1.181),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="W86GNRQ4ZW", tag="STOOL-WIN-S-PLANT3", window_ref="WIN-S-PLANT3",
                material_ref="quartz-counter", thickness=inch(1.181),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="YRS03M2AJW", tag="STOOL-WIN-S-PLANT4", window_ref="WIN-S-PLANT4",
                material_ref="quartz-counter", thickness=inch(1.181),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
]

# The sink window's sill is directly over the kitchen counter. Match the plant-room stool's
# 3 cm stone, overhang, horn and eased edge; its depth still follows its own host wall.
KITCHEN_STOOLS = [
    WindowStool(uid="N7C4V2M8QK", tag="STOOL-WIN-M-KITCH", window_ref="WIN-M-KITCH",
                material_ref="quartz-counter", thickness=inch(1.181),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
]

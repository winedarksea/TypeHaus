# haus: editable
# Catlin house countertops — the work surfaces over the casework.
#
# Split out of plan/millwork.py rather than living in it: that file is the owner-milled
# HARDWOOD (stools, shelves, treads — stock a sawyer cuts), and a countertop is a purchased
# fabricated slab set by the yard that cut it. Two subs, two trades, two files.
#
# ** WHAT WAS PROSE UNTIL THIS FILE GREW THESE ELEMENTS: ** the house's ~63 SF of stone was a
# HAND FIGURE in a prices.toml comment, added up by a reader off the cabinet schedule, and
# the peninsula's overhang rule was a paragraph in plan/assemblies.py that nothing could
# check. Both are derived now. Each top names the placeables it covers and the resolver
# derives the slab from them, so moving a cabinet moves the square footage and the estimate
# with it (→ resolve/millwork.py).
#
# THE RUNS ARE AUTHORED RATHER THAN GROWN, and this kitchen is exactly why: the peninsula's
# north face butts FURN-M-KIT-N3's south face, so a walk that merged everything it touched
# would hand the fabricator one L-shaped slab crossing two orientations, two depths and two
# materials. Which cabinets share a slab is a seam decision.
#
# Not here: the four one-piece solid-surface vanity tops (FX-VANITY-24/30/36-*), which are
# moulded with their bowls and bought boxed with the cabinet — they bill in [placeables] as
# part of the fixture, and modelling a top over them would bill them twice. The two
# FABRICATED vanity decks below are the exception, and are the reason the split exists.

from typehaus import ft, inch
from typehaus.model import Countertop, WindowStool

MAIN_COUNTERTOPS = [
    # The north run, pantry wall to the corner: B15, the dishwasher, the 36" sink base, B30,
    # and the B30 that turns the corner. The dishwasher is in the run because the slab runs
    # over it — a countertop does not stop at an under-counter appliance — and the ~1 3/8"
    # of filler between B30 and the corner box is cut straight across, not left as a hole.
    #
    # 25" deep: 24" of carcass and the 1" a top oversails its doors. Nothing here
    # cantilevers, so the overhang rule has nothing to say about this run.
    Countertop(
        uid="GQ3B84T2WH", tag="CT-M-KIT-N",
        hosts=("FURN-M-KIT-E1", "APPL-M-DW", "FURN-M-KIT-SINKBASE", "FURN-M-KIT-E2",
               "FURN-M-KIT-N4"),
        material_ref="quartz-counter",
        thickness=inch(1.181),  # 3 cm
        overhang=inch(1),
    ),
    # The east run's one surviving base, between the range and the peninsula. A separate
    # slab because a slide-in range interrupts the stone: the two tops die into its sides.
    Countertop(
        uid="WRDEA4N59W", tag="CT-M-KIT-E",
        hosts=("FURN-M-KIT-N3",),
        material_ref="quartz-counter",
        thickness=inch(1.181),
        overhang=inch(1),
    ),
    # ** THE PENINSULA IS TWO TOPS, AND THE SPLIT IS THE OVERHANG RULE MADE BUILDABLE. **
    # CASE-PENINSULA-120 is 39" of footprint over 24" of carcass — a 15" knee. A single
    # quartz slab over all 39" hangs 15" unsupported, 38% of its depth, against a published
    # maximum of 1/3 and 14" unsupported in 3 cm: outside the fabricators' limits and
    # outside the warranty (`advisory.countertop_overhang`, plan/assemblies.py's
    # `quartz-counter` note). So the stone stops at the carcass face and the owner's own
    # white oak takes the cantilever, milled to 1 3/16" to sit flush with 3 cm stone.
    #
    # `depth` is authored on both for that reason and no other: this is the one run in the
    # house where the slab deliberately stops short of the footprint it stands on.
    Countertop(
        uid="YNNE7K95XB", tag="CT-M-KIT-PENINSULA",
        hosts=("FURN-M-KIT-PENINSULA",),
        material_ref="quartz-counter",
        thickness=inch(1.181),
        # Zero: the stone's front edge IS the carcass face, where the movement joint is.
        overhang=inch(0),
        depth=inch(24),
    ),
    # The bar top. `unsupported_overhang` is authored because the derivation cannot see this
    # one: a 15" slab on a 24" carcass reads as fully supported by depth alone, and in fact
    # every inch of it is cantilever — it starts where the stone stops. 96" of the 120",
    # because the east 24" is not overhang at all (FURN-M-KIT-MIXER-GARAGE stands full-depth
    # on it) and a counter-to-ceiling cabinet cannot stand on a cantilever.
    Countertop(
        uid="7E97VPX9M2", tag="CT-M-KIT-PENINSULA-BAR",
        hosts=("FURN-M-KIT-PENINSULA",),
        material_ref="oak-counter",
        thickness=inch(1.1875),  # 1 3/16", flush with 3 cm quartz
        overhang=inch(0),
        depth=inch(15),
        length=ft(8),
        unsupported_overhang=inch(15),
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

# --- RM-S-PLANT's window stools: quartz remnants (owner decision 2026-09-28) -------------
#
# The four plant-room windows sit in PLANT_EXT_2X6_HUMID, which MW-STANDARD leaves out: oak
# cups and tannin-stains at 70% RH (plan/millwork.py). So each gets a 3 cm remnant of the
# vanity stone instead, cut by the same yard — which is why they live here and not with the
# oak. They bill as quartz in [countertops]; `haus millwork` skips them (not custom-milled).
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

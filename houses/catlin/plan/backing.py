# haus: editable
# In-wall backing — the bands a finish trade fastens into.
#
# `# haus: editable` is REQUIRED: a band is UI-movable, and a WallBacking edited in the editor
# against a file without this marker is silently dropped on write-back.
#
# ** THIS IS THE ONLY IRREVERSIBLE ITEM IN THE HOUSE. ** Every other decision here can be
# revisited with a screwdriver. Once drywall and tile close a wall, a twelve-dollar plywood
# strip becomes a $1,500-4,000 demolition, so these bands are authored where a screw *might*
# land rather than where one lands in today's model. `plan/fixture_types_wc.py` and
# `notes/interior_selections.md` have carried that policy as prose since 2026-08; this file is
# the first version of it the framer can actually build, the takeoff can buy, and the 3D model
# can show.
#
# ** WHY THESE ARE ELEMENTS AND NOT `FramingSpec.blocking_heights`. ** That field emits a flat
# course between studs for every wall of an assembly, so backing one wet wall would mean
# cloning `INT_2X6_STAGGERED_PLUMBING` and re-running its Glaser gate, its energy table and
# truss_wall_opening_support against an unreviewed tag, to bill forty board feet.
# `plan/furniture_types.py` reached that dead end and wrote it down. A band is also the wrong
# shape for that field: a course is 1 1/2" tall for a whole wall, and what a trade needs is a
# run at a stated height across the studs, not between them.
#
# ** NOTHING HERE IS CODE, WITH ONE EXCEPTION. ** ADA does not reach a private residence, the
# IRC sets no grab-bar load, and the 250 lb figure everyone quotes is IBC 1607.7 — whose
# one- and two-family exception drops it back to the handrail case. The exception is IRC
# **Table R301.5**'s 200 lb concentrated load on a handrail or guard, adopted by Minnesota via
# Minn. Rules ch. 1309, which prescribes the load and no attachment detail at all. The
# grab-bar geometry below is borrowed from California's CRC R328.1.1 — 2x8 nominal minimum,
# 32" to 39 1/4" above the floor, flush with the framing — which is the best-written version of
# this requirement in any US code and is a house's choice to adopt, not the engine's to impose.
# `advisory.wall_backing_present` grades all of it ADVISORY for exactly that reason.
#
# Not fireblocking. IRC R302.11 is a draft stop that fills the cavity; this is a fastening
# target laid flat on the stud face. An 8' wall triggers no horizontal fireblock at all.
#
# Elevations are above the storey datum — the same datum `Mount.elevation` and an opening's
# sill use — and the dialect forbids arithmetic, so every one is a literal.

from typehaus import WallBacking, inch


# --- the wet walls ---------------------------------------------------------------------
#
# One continuous 3/4" plywood band per wet wall, 32" to 80" above the floor, in ALL of them
# including the ones with no slide bar planned. Blocking only where today's model's screws
# land pins the house to today's model forever, and the sheet is ripped from stock either
# way. The band's bottom edge is CRC R328.1.1's 32" and it runs up past every towel bar,
# valve, drop elbow, tub spout, shower arm and slide-bar anchor in one piece.
#
# 48" tall is half a sheet ripped the long way, which is why the number is 48 and not 47:
# a rip that yields two usable strips wastes nothing.

_WET_ELEVATION = inch(32)
_WET_HEIGHT = inch(48)
_WET_PROFILE = "0.75x48.0"


# --- the kitchen ------------------------------------------------------------------------
#
# 2x8 flat, not plywood: a wall cabinet hangs on a rail screwed through the back at the top
# and bottom of the carcass, and each of those is one line, not a field. The band's bottom
# sits 2" under the cabinet's own elevation so the bottom rail lands inside it with room for
# a shim; a 42"-tall box's TOP rail lands in the next band up, which is why 54" and 96" both
# get one and the run between them does not.
#
# 54" is NKBA's baseline (a 36" counter plus 18" clear), 96" is the stacker course, 66" and
# 75" are this kitchen's own two odd hangs, and 84" is the living-room curtain rods on the
# same wall.

# --- closet rods and shelves ------------------------------------------------------------
#
# 66" is the single-rod height, and a rod is the one item on this list that is loaded in
# shear by a person pulling down on a coat rather than by dead weight.

# --- plumbing access panels -------------------------------------------------------------
#
# A panel frame screws to the wall the same way anything else does, and all four of these
# sit BELOW the wet-wall band's 32" bottom edge — the tub and shower valve bodies they open
# onto are down at the deck, not up at the bar line.

# The four groups above, filed on the storey each wall stands on — `PlanModel` keys

# The four groups above, filed on the storey each wall stands on: `PlanModel` keys elements
# by storey, so a band cannot ride in a list that mixes them.

BASEMENT_BACKING = [
    WallBacking(uid="MCEY2KK7X7", tag="BK-B-BA-E", wall_ref="W-B-BA-E",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="F2VB4ZSJM3", tag="BK-B-CE", wall_ref="W-B-CE",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="MVECH5GPSX", tag="BK-B-CW", wall_ref="W-B-CW",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="RVQ4CEHMJ6", tag="BK-B-CW3", wall_ref="W-B-CW3",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="DQFXW82JCN", tag="BK-B-HALL-W", wall_ref="W-B-HALL-W",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
]

MAIN_BACKING = [
    WallBacking(uid="63Q2NFMTRY", tag="BK-M-BA2E", wall_ref="W-M-BA2E",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="NGSM5DJCT1", tag="BK-M-BA2E2", wall_ref="W-M-BA2E2",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="9123HCR34E", tag="BK-M-BAE", wall_ref="W-M-BAE",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="QN93C99PCJ", tag="BK-M-HS1", wall_ref="W-M-HS1",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, over-toilet cabinet"),
    WallBacking(uid="548DDSJFJ4", tag="BK-M-HS2", wall_ref="W-M-HS2",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="TR3XTCCY65", tag="BK-M-N1-SINK", wall_ref="W-M-N1",
                elevation=inch(25), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="wall-mounted kitchen sink"),
    WallBacking(uid="EPCM53YC2B", tag="BK-M-N1-LOW", wall_ref="W-M-N1",
                elevation=inch(52), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="upper cabinet bottom rail (54 in.)"),
    WallBacking(uid="JB32670A20", tag="BK-M-N1-MID", wall_ref="W-M-N1",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="upper cabinet bottom rail (66 in.)"),
    WallBacking(uid="PVJ3823KWR", tag="BK-M-N1-HIGH", wall_ref="W-M-N1",
                elevation=inch(94), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="stacker course rail (96 in.)"),
    WallBacking(uid="70856QPNT4", tag="BK-M-E1-LOW", wall_ref="W-M-E1",
                elevation=inch(52), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="upper cabinet bottom rail (54 in.)"),
    WallBacking(uid="GBHV48GS1S", tag="BK-M-E1-MID", wall_ref="W-M-E1",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="upper cabinet bottom rail (66 in.) and the range hood"),
    WallBacking(uid="VXX1ME3YWS", tag="BK-M-E1-ROD", wall_ref="W-M-E1",
                elevation=inch(82), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="curtain rod brackets (84 in.)"),
    WallBacking(uid="8PFKG4320V", tag="BK-M-E1-HIGH", wall_ref="W-M-E1",
                elevation=inch(94), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="stacker course rail (96 in.)"),
    WallBacking(uid="SBE1761N5C", tag="BK-M-C5-MID", wall_ref="W-M-C5",
                elevation=inch(73), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="over-fridge and over-freezer cabinets (75 in.)"),
    WallBacking(uid="WVN7RFKJP6", tag="BK-M-C5-HIGH", wall_ref="W-M-C5",
                elevation=inch(94), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="stacker course rail (96 in.)"),
    WallBacking(uid="Y8RV51SN69", tag="BK-M-CLN-ROD", wall_ref="W-M-CLN",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="closet shelf and rod (66 in.)"),
    WallBacking(uid="QJSHFZFDY3", tag="BK-M-HS1-AP", wall_ref="W-M-HS1",
                elevation=inch(22), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="bath 1 plumbing access panel frame"),
    WallBacking(uid="7H0ZY02018", tag="BK-M-BA2E-AP", wall_ref="W-M-BA2E",
                elevation=inch(4), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="bath 2 tub access panel frame"),
    # The tub deck's own skirt is a 19 1/4" wall, so this band sits inside a 16" stud run:
    # 2" clears the sole plate and the 2x8 tops out at 9 1/4", well under it.
    WallBacking(uid="2WV5J50Q0C", tag="BK-M-TUBDK-AP", wall_ref="W-M-TUBDK-W",
                elevation=inch(2), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="bath 2 tub deck access panel frame"),
]

SECOND_BACKING = [
    WallBacking(uid="DA0BDATHZ7", tag="BK-S-BA-E", wall_ref="W-S-BA-E",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="7114P8MNBY", tag="BK-S-BA-E1B", wall_ref="W-S-BA-E1B",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="NJJYT7QAMA", tag="BK-S-BD-N", wall_ref="W-S-BD-N",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="KFWVA9EPGE", tag="BK-S-BD-N1B", wall_ref="W-S-BD-N1B",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="D9754TGGC7", tag="BK-S-DC2", wall_ref="W-S-DC2",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="YQESA1JG5K", tag="BK-S-SN3", wall_ref="W-S-SN3",
                elevation=_WET_ELEVATION, height=_WET_HEIGHT, profile=_WET_PROFILE,
                purpose="wet wall: grab bar, valve, spout, shower arm"),
    WallBacking(uid="0C6ST8E3ET", tag="BK-S-N1B-ROD", wall_ref="W-S-N1B",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="closet shelf and rod (66 in.)"),
    WallBacking(uid="QY4ZK9WZ6S", tag="BK-S-CH-S-AP", wall_ref="W-S-CH-S",
                elevation=inch(22), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="bath 1 chase access panel frame"),
    WallBacking(uid="W2XZ7J1J2X", tag="BK-S-SN3-AP", wall_ref="W-S-SN3",
                elevation=inch(4), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="suite bath access panel frame"),
]

ATTIC_BACKING = [
    # W-A-STU-W is the one short wet wall, and it is short twice over. Its plate is at
    # 72 3/4", so the standard 80" band has no stud to land on and `backing_panels.py` would
    # drop it in silence. The binding limit is lower still: `CARF01AAAA:rafter-020` rakes
    # down across this knee wall and passes 60 7/8" above its floor, which nothing in the
    # framing solver knows about — `top_at` reads the wall's own plate, not the roof over
    # it, so a 64" band resolved happily and `structural.member_interference` caught it.
    # 32" to 56" clears the rafter by 4 7/8" and is the whole range a knee-wall bar sink's
    # valve and towel ring can physically use.
    WallBacking(uid="GCV1Y8MJ5J", tag="BK-A-STU-W", wall_ref="W-A-STU-W",
                elevation=inch(32), height=inch(24), profile="0.75x24.0",
                purpose="wet wall (short): bar sink valve and towel ring"),
    # IKEA requires the SUNNERSTA kitchenette (FURN-A-STUDIO-BAR-BASE, plan/placeables.py) be
    # anchored to the wall, and a 44 1/8" x 54 3/4" flat-pack on an attic deck is exactly the
    # thing that walks away from an unanchored screw. 46" puts a 2x8 flat at 46"..53 1/4", which
    # takes the unit's own top rail (~52") anywhere along its 10'-3 15/16"..14'-0" run.
    # ** THE RAKE IS WHY IT IS NOT HIGHER. ** W-A-BATH-S runs from x 9'-7 1/2" east, where the
    # 6:12 underside `1 1/2" + x/2` is only 4'-11 1/4"; a band any taller runs its west end into
    # the roof plane, which is `structural.member_interference`'s business and not a guess.
    WallBacking(uid="DHRK7N7J1Y", tag="BK-A-BATH-S", wall_ref="W-A-BATH-S",
                elevation=inch(46), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="SUNNERSTA kitchenette wall anchor rail"),
]

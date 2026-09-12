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

from typehaus import WallBacking, ft, inch


# --- the kitchen ------------------------------------------------------------------------
#
# 2x8 flat, not plywood: a wall cabinet hangs on a rail screwed through the back at the top
# and bottom of the carcass, and each of those is one line, not a field. The band's bottom
# sits 2" under the cabinet's own elevation so the bottom rail lands inside it with room for
# a shim; a 42"-tall box's TOP rail lands in the next band up, which is why 54" and 96" both
# get one and the run between them does not.
#
# ** THE WHOLE SCHEME MOVED 2026-09-11 WITH THE SEKTION RETYPE ** (plan/placeables.py,
# notes/ikea_sektion_ladder.md). A 3" toe kick and 40"/15" wall frames put the uppers at 53"
# and the stacker course at 93", where they were 54" and 96"; the over-cold boxes went from
# 75" to 78". So: 53" is the upper run (NKBA's 36" counter plus a 17" backsplash, inside its
# range), 93" is the stacker course, 68" and 78" are this kitchen's own two odd hangs, 76" is
# the mixer garage's upper box, and 84" is the living-room curtain rods on the same wall.
#
# A 2x8 laid flat is 7 1/4", so one band covers a spread of hangs: BK-M-E1-MID at 64" runs to
# 71 1/4" and answers the range hood at 66" AND FURN-M-KIT-WN1 at 68" with one rail.
#
# ** W-M-E1's FOUR CABINET BANDS STOP AT THE KITCHEN. ** The wall is 36 ft and the four ran
# all of it, because `start`/`length` left None is the wall's whole run. Kitchen cabinetry on
# it starts at y 21'-2 3/8"; everything south of that is living room, so roughly 59 LF of 2x8
# ran south to back nothing. They start at station 20'-0" now and run the remaining 16 ft to
# the wall's end. y 20'-0" is the gap between the last BESTA unit (ends 19'-5") and the first
# pantry (starts 21'-2 3/8"), and 240" lands inside the jack of WIN-M-LIV-E2's north jamb
# pack, so the run begins on framing rather than in the middle of a bay.
#
# BK-M-E1-ROD is the exception and keeps its full run: at 82" it backs the two LIVING-ROOM
# curtain rods, at y 4'-0" and 13'-3 5/8", which are exactly the part of the wall the other
# four just gave up.

# --- closet rods and shelves ------------------------------------------------------------
#
# 66" is the single-rod height, and a rod is the one item on this list that is loaded in
# shear by a person pulling down on a coat rather than by dead weight.

# --- plumbing access panels -------------------------------------------------------------
#
# A panel frame screws to the wall the same way anything else does, and all four of these
# sit BELOW the wet-wall band's 32" bottom edge — the tub and shower valve bodies they open
# onto are down at the deck, not up at the bar line.

# --- handrail brackets --------------------------------------------------------------------
#
# ST-G-SERVICE's handrail RL-G-SERVICE is wall-mounted on W-G-W since 2026-09-11
# (plan/storeys/garage.py). A bracket takes IRC Table R301.5's 200 lb in any direction, and
# a 2x6 stud bay at 24" o.c. has a stud where the framer put one, not where the bracket
# lands. `post_spacing=48"` on the 3'-9" rail path resolves one bracket at each end and none
# between, so there are two stations and they are answered two different ways:
#
#  * TOP, y=47'-2 5/8" — the rail's landing end was set ON stud-010 of W-G-W (67'-2 5/8"
#    less ten 24" modules), so that bracket screws into a stud and wants no blocking. A band
#    here could not have helped anyway: the station is 1/4" north of WIN-G-S1's bay, whose
#    rough-opening exclusion clips any backing to the far side of that stud.
#  * FOOT, y=50'-9 5/8" — the flight's bottom riser, 5" from the nearest stud, so this one
#    gets a 2x12 laid flat, cut to FILL THE BAY: station 16'-0 3/4"..17'-11 1/4" from
#    N-G-NW, which is face to face between the studs at 16'-0" and 18'-0" o.c. — 22 1/2" of
#    clear bay, one cut, both ends nailed. It was authored 15'-11"..16'-11" until 2026-09-12
#    and that 12" block lapped the north stud by 1/4" and floated 10 1/4" clear of anything
#    at its south end; a block with one free end cannot be fastened. The bracket at station
#    16'-5" sits 4 1/4" inside the north end of the bay either way.
#    11 1/4" tall (`integrity.wall_backing_ref` holds `height` to the profile).
#    Centred 2 1/2" below the rail top there — the resolver's own `_BRACKET_DROP_M` — so the
#    arm lands mid-band with ~5" of play: 12"..23 1/4" above the garage datum, against a
#    rail top at +20 3/4" where the nosing line meets the first riser.
#
# Move the rail and move these. `face` is the default "left": W-G-W runs N->S, so its
# left-hand normal points east, into the garage.

# The groups above, filed on the storey each wall stands on: `PlanModel` keys elements
# by storey, so a band cannot ride in a list that mixes them.

BASEMENT_BACKING = [
]

MAIN_BACKING = [
    WallBacking(uid="TR3XTCCY65", tag="BK-M-N1-SINK", wall_ref="W-M-N1",
                elevation=inch(25), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="wall-mounted kitchen sink"),
    WallBacking(uid="EPCM53YC2B", tag="BK-M-N1-LOW", wall_ref="W-M-N1",
                elevation=inch(51), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="upper cabinet bottom rail (53 in.)"),
    WallBacking(uid="JB32670A20", tag="BK-M-N1-MID", wall_ref="W-M-N1",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf",
                purpose="north wall corner filler and any future 66-68 in. hang"),
    WallBacking(uid="PVJ3823KWR", tag="BK-M-N1-HIGH", wall_ref="W-M-N1",
                elevation=inch(91), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="stacker course rail (93 in.)"),
    WallBacking(uid="70856QPNT4", tag="BK-M-E1-LOW", wall_ref="W-M-E1",
                start=ft(20), length=ft(16),
                elevation=inch(51), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="upper cabinet bottom rail (53 in.)"),
    WallBacking(uid="GBHV48GS1S", tag="BK-M-E1-MID", wall_ref="W-M-E1",
                start=ft(20), length=ft(16),
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="range hood (66 in.) and FURN-M-KIT-WN1 (68 in.)"),
    # FURN-M-KIT-MIXER-GARAGE-UP's bottom rail. The old one-piece 72" garage spanned 36" to
    # the ceiling and was caught by whichever bands it crossed; split at 76" it has a rail of
    # its own, between BK-M-E1-MID's top at 71 1/4" and BK-M-E1-ROD's bottom at 82".
    WallBacking(uid="Z31Y1280S2", tag="BK-M-E1-GARAGE", wall_ref="W-M-E1",
                start=ft(20), length=ft(16),
                elevation=inch(74), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="mixer garage upper box bottom rail (76 in.)"),
    WallBacking(uid="VXX1ME3YWS", tag="BK-M-E1-ROD", wall_ref="W-M-E1",
                elevation=inch(82), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="curtain rod brackets (84 in.)"),
    WallBacking(uid="8PFKG4320V", tag="BK-M-E1-HIGH", wall_ref="W-M-E1",
                start=ft(20), length=ft(16),
                elevation=inch(91), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="stacker course rail (93 in.)"),
    WallBacking(uid="SBE1761N5C", tag="BK-M-C5-MID", wall_ref="W-M-C5",
                elevation=inch(76), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="over-fridge and over-freezer cabinets (78 in.)"),
    WallBacking(uid="WVN7RFKJP6", tag="BK-M-C5-HIGH", wall_ref="W-M-C5",
                elevation=inch(91), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="tall cabinet top course rail (93 in.)"),
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

GARAGE_BACKING = [
    WallBacking(uid="1FTWGZ1WJ3", tag="BK-G-W-RAIL-FOOT", wall_ref="W-G-W",
                start=ft(16, 0.75), length=inch(22.5),
                elevation=inch(12), height=inch(11.25), profile="1.5x11.25",
                material_ref="spf", purpose="handrail brackets (RL-G-SERVICE, foot of flight)"),
]

ATTIC_BACKING = [
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

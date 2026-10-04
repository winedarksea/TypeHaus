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
# W-M-E1 has no 53 1/2" upper since FURN-M-KIT-WN3 was deleted (2026-10-03), so its
# BK-M-E1-LOW band went with it.
#
# ** THE SCHEME MOVED WITH THE 2026-09-29 FINISHED-CEILING CORRECTION. ** Counter uppers
# now start at 53 1/2", their top course at 83 1/2", and the over-cold boxes at 73 1/2".
# The mixer garage's upper box remains at 76"; living-room curtain rods remain at 84".
#
# A 2x8 laid flat is 7 1/4", so one band covers a spread of hangs. The east-wall curtain
# band also covers the top cabinet course, avoiding an overlapping blocking band.
#
# ** W-M-E1's CABINET BANDS STOP AT THE KITCHEN. ** The wall is 36 ft and the four ran
# all of it, because `start`/`length` left None is the wall's whole run. Kitchen cabinetry on
# it starts at y 21'-2 3/8"; everything south of that is living room, so roughly 59 LF of 2x8
# ran south to back nothing. They start at station 20'-0" now and run the remaining 16 ft to
# the wall's end; 240" lands on a jack pack, so the run begins on framing.
#
# BK-M-E1-ROD keeps its full run: at 82" it backs the two LIVING-ROOM curtain rods (86" since
# the east row's heads rose 2", 2026-10-02) and the kitchen stacker rail at 83 1/2".
# BK-M-E1-MIXER is full length too: it carries the SEKTION base rail the whole wall now.

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
    # Frame brackets fasten near the cabinet tops.
    WallBacking(uid="ZCGDP5VDX9", tag="BK-M-N1-KIT-TOP", wall_ref="W-M-N1",
                elevation=inch(99.5), height=inch(5.5), profile="2x6",
                material_ref="spf", purpose="stock kitchen upper top brackets; diagonal corner north leg"),
    WallBacking(uid="N4B7RPNY55", tag="BK-M-E1-KIT-TOP", wall_ref="W-M-E1",
                start=inch(241.75), length=inch(190.25),
                elevation=inch(99.5), height=inch(5.5), profile="2x6",
                material_ref="spf", purpose="stock garage frame top restraint"),
    WallBacking(uid="PT15STOCK1", tag="BK-M-E1-PANTRY-TOP", wall_ref="W-M-E1",
                start=inch(241.75), length=inch(80),
                elevation=inch(95.5), height=inch(3.5), profile="2x4",
                material_ref="spf", purpose="stock 15-inch pantry top frame suspension rail (98 1/2-inch tops)"),
    WallBacking(uid="EA1DMVPCVN", tag="BK-M-N1-CORNER", wall_ref="W-M-N1", length=inch(32.75),
                elevation=inch(72), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="diagonal corner upper north leg at 73 1/2 inches"),
    WallBacking(uid="TR3XTCCY65", tag="BK-M-N1-SINK", wall_ref="W-M-N1",
                elevation=inch(25), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="wall-mounted kitchen sink"),
    WallBacking(uid="EPCM53YC2B", tag="BK-M-N1-LOW", wall_ref="W-M-N1",
                elevation=inch(51), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="upper cabinet bottom rail (53 in.)"),
    WallBacking(uid="JB32670A20", tag="BK-M-N1-MID", wall_ref="W-M-N1",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf",
                purpose="future north wall 66-68 in. hang"),
    WallBacking(uid="PVJ3823KWR", tag="BK-M-N1-HIGH", wall_ref="W-M-N1",
                elevation=inch(81.5), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="stacker course rail (83 1/2 in.)"),
    # Full length since 2026-09-25: it also takes FURN-M-FIRE-MANTEL (64 in.).
    WallBacking(uid="GBHV48GS1S", tag="BK-M-E1-MID", wall_ref="W-M-E1",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf",
                purpose="range hood (66 in.) and mantel (64 in.)"),
    # FURN-M-KIT-MIXER-GARAGE-UP's bottom rail. The old one-piece 72" garage spanned 36" to
    # the ceiling and was caught by whichever bands it crossed; split at 76" it has a rail of
    # its own, between BK-M-E1-MID's top at 71 1/4" and BK-M-E1-ROD's bottom at 82".
    WallBacking(uid="Z31Y1280S2", tag="BK-M-E1-GARAGE", wall_ref="W-M-E1",
                start=ft(20), length=ft(16),
                elevation=inch(74), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="garage lower restraint (76 in.) and kitchen uppers (73 1/2 in.)"),
    WallBacking(uid="VXX1ME3YWS", tag="BK-M-E1-ROD", wall_ref="W-M-E1",
                elevation=inch(82), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="curtain rod brackets (86 in.) and kitchen stacker rail (83 1/2 in.)"),
    # ** HOSTING SURFACED THESE, 2026-09-25. ** Until the wall-mounted bodies were hosted on
    # their faces, `advisory.wall_backing_present` could not square them onto a wall and
    # said UNKNOWN; hosted, it names the wall and there was nothing behind them.
    WallBacking(uid="PE3FV6DGRM", tag="BK-M-S2-ROD", wall_ref="W-M-S2",
                elevation=inch(82), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="curtain rod brackets (84 in.)"),
    WallBacking(uid="DQYV0CA18A", tag="BK-M-C1-ROD", wall_ref="W-M-C1",
                elevation=inch(82), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="curtain rod brackets (84 in.)"),
    WallBacking(uid="016TC9913X", tag="BK-M-W4-ROD", wall_ref="W-M-W4",
                elevation=inch(82), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="curtain rod brackets (84 in.)"),
    WallBacking(uid="7T3GDF98A5", tag="BK-M-S1-ROD", wall_ref="W-M-S1",
                elevation=inch(82), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="curtain rod brackets (84 in.)"),
    WallBacking(uid="VBFFYKBZJW", tag="BK-M-CLN-RACK", wall_ref="W-M-CLN",
                elevation=inch(46), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="laundry drying rack (48 in.)"),
    # RM-M-CLOSET (plan/closet.py). The PAX wall rails are 2x8s at 86"; the rail sits at
    # the frames' 93" top. Notch round the suite stack (x 12'-6") and the supplies (15'-9",
    # 16'-5") rising in these two walls.
    WallBacking(uid="QZAD6KWB50", tag="BK-M-CLN-PAX", wall_ref="W-M-CLN", face="right",
                elevation=inch(86), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="PAX wall rail (93 in.)"),
    WallBacking(uid="M80101YTFN", tag="BK-M-CLN2-PAX", wall_ref="W-M-CLN2", face="right",
                elevation=inch(86), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="PAX wall rail (93 in.)"),
    # The wire corner's north-leg back clips, x 8'-5 3/8"..11'-1 3/8", run to the stud at
    # 11'-5 1/4". The west leg's clips land in BK-M-BA2E2-HIGH and -GRAB (backing_wet.py).
    WallBacking(uid="KEX2RE1ERV", tag="BK-M-CLN-WIRE-HI", wall_ref="W-M-CLN", face="right",
                start=inch(3.375), length=inch(35.875),
                elevation=inch(72), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="closet wire shelf clips (upper tier, 80 in.)"),
    WallBacking(uid="D11W25Y0H8", tag="BK-M-CLN-WIRE-LO", wall_ref="W-M-CLN", face="right",
                start=inch(3.375), length=inch(35.875),
                elevation=inch(32), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="closet wire shelf clips (lower tier, 40 in.)"),
    WallBacking(uid="TFRQMAPD74", tag="BK-M-BDN2-PEGS", wall_ref="W-M-BDN2", face="left",
                start=inch(15.25), length=inch(53.875),
                elevation=inch(62), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="closet robe peg rail (64 in.)"),
    # RM-S-SUITEBATH's robe pegs (plan/placeables.py), on W-S-DC2's bath face at y 18'-9"..20'-9".
    WallBacking(uid="7ZWH2X1FEM", tag="BK-S-DC2-PEGS", wall_ref="W-S-DC2", face="right",
                start=inch(32), length=inch(32),
                elevation=inch(62), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="suite bath robe peg rail (64 in.)"),
    WallBacking(uid="ZRCH8QVDBK", tag="BK-M-C2-MIRROR-LO", wall_ref="W-M-C2", face="left",
                start=inch(3.25), length=inch(33.5),
                elevation=inch(12), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="closet lit mirror bottom cleat (14 in.)"),
    WallBacking(uid="4S4VEJSEKV", tag="BK-M-C2-MIRROR-HI", wall_ref="W-M-C2", face="left",
                start=inch(3.25), length=inch(33.5),
                elevation=inch(68), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="closet lit mirror top cleat (74 in.)"),
    WallBacking(uid="8YJBD0RKJR", tag="BK-M-STOS-SHELF", wall_ref="W-M-STOS",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="mudroom shelf (66 in.)"),
    WallBacking(uid="GWVBD431GV", tag="BK-M-N1-DISP", wall_ref="W-M-N1",
                elevation=inch(12), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="disposal switch box and air-switch bracket (14 in.)"),
    # Dropped 34" -> 31 1/2" (2026-10-02) so one band takes both the SEKTION base suspension
    # rail at the frame top (33 1/2") down the whole wall and the mixer garage's box at 36".
    WallBacking(uid="GRFFVAA88Y", tag="BK-M-E1-MIXER", wall_ref="W-M-E1",
                elevation=inch(31.5), height=inch(7.25), profile="2x8",
                material_ref="spf",
                purpose="SEKTION base suspension rail (33 1/2 in.), mixer garage lower box (36 in.)"),
    WallBacking(uid="SBE1761N5C", tag="BK-M-C5-MID", wall_ref="W-M-C5",
                elevation=inch(71.5), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="over-fridge and over-freezer cabinets (73 1/2 in.)"),
    WallBacking(uid="WVN7RFKJP6", tag="BK-M-C5-HIGH", wall_ref="W-M-C5",
                elevation=inch(81.5), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="tall cabinet top course rail (83 1/2 in.)"),
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
    # FX-M-PORCH-HYD's seat. The hydrant states a WALL/24" mount on the element as of
    # 2026-09-15 (plan/fixtures.py); before that it inherited a default FLOOR mount and
    # resolved at 1 1/4", so there was nothing at 24" for a band to be missing behind.
    #
    # ** THE BAND SPANS TWO BAYS BECAUSE THE STATION IS NOT SETTLED. ** The hydrant is
    # authored at x=12'-0" and W-M-S1's stud-006 is at 144.000" — the barrel is bored
    # through a stud today, and nothing in the engine grades that. The open question is
    # whether it moves to the bay centre (~151 1/2") or the bore is accepted; 128 3/4"..158"
    # backs it either way, so settling that question later costs no framing. Both ends land
    # on a stud face — stud-005's east at 128 3/4" and king-1-l0's west at 158" — which is
    # what advisory.wall_backing_bearing asks for. Two blocks in the field, one run here.
    WallBacking(uid="HTKFF371E9", tag="BK-M-S1-HYD", wall_ref="W-M-S1",
                start=inch(128.75), length=inch(29.25),
                elevation=inch(21), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="wall hydrant seat (FX-M-PORCH-HYD, 24 in.)"),
]

SECOND_BACKING = [
    # SEKTION high rail: cabinet top 94 1/2" AFF, near-top rail, plus 1 1/2" of floor
    # build-up above the storey datum. The 90"..97 1/4" course spans the mounting screws.
    # Two bands because the rail crosses the staggered/bearing wall split at x=70 1/2".
    WallBacking(uid="8T3FH878AV", tag="BK-S-BD-N-SEKTION", wall_ref="W-S-BD-N", face="left",
                start=inch(7.385), length=inch(63.115), elevation=inch(90),
                height=inch(7.25), profile="2x8", material_ref="spf",
                purpose="SEKTION high-cabinet suspension rail, bathroom face"),
    WallBacking(uid="KDV747MSCM", tag="BK-S-BD-N1B-SEKTION", wall_ref="W-S-BD-N1B", face="left",
                start=inch(0), length=inch(11.25), elevation=inch(90),
                height=inch(7.25), profile="2x8", material_ref="spf",
                purpose="SEKTION rail continuation to the bathroom-door king"),
    WallBacking(uid="PKRGE2ZNBP", tag="BK-S-PS2-SHELF", wall_ref="W-S-PS2",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="closet shelf and rod (66 in.)"),
    WallBacking(uid="0C6ST8E3ET", tag="BK-S-N1B-ROD", wall_ref="W-S-N1B",
                elevation=inch(64), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="closet shelf and rod (66 in.)"),
    WallBacking(uid="QY4ZK9WZ6S", tag="BK-S-CH-S-AP", wall_ref="W-S-CH-S",
                elevation=inch(22), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="bath 1 chase access panel frame"),
    WallBacking(uid="W2XZ7J1J2X", tag="BK-S-SN3-AP", wall_ref="W-S-SN3",
                elevation=inch(4), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="suite bath access panel frame"),
    # FX-S-BALC-HYD's seat, the balcony half of the same 2026-09-15 mount fix. This one sits
    # cleanly in a bay: W-S-S1's stud-002 is at 80.000" and king-1-l0 at 94.750", so the
    # hydrant at x=7'-4" (88") has 3 15/16" to the nearest stud face either side. One bay,
    # one block, both ends bearing (80 3/4"..94").
    WallBacking(uid="E5817BZ266", tag="BK-S-S1-HYD", wall_ref="W-S-S1",
                start=inch(80.75), length=inch(13.25),
                elevation=inch(21), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="wall hydrant seat (FX-S-BALC-HYD, 24 in.)"),
    # BED1-3's PAX rails (plan/bedroom_wardrobes.py), one 2x8 at 86" as BK-M-CLN-PAX. BW1/BW2
    # run the corner frame (4" off the south wall) plus the 19 5/8" frame, stud-000 to the
    # door's king; it stays under the REG-S-HP-BED1/2 side collar at 97 1/8". BD2 runs all
    # three frames from stud-004 to the east wall.
    WallBacking(uid="351NHAQ233", tag="BK-S-BW1-PAX", wall_ref="W-S-BW1", face="right",
                start=inch(3.625), length=inch(62.25),
                elevation=inch(86), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="PAX wall rail (93 in.)"),
    WallBacking(uid="HPV9RM2SBC", tag="BK-S-BW2-PAX", wall_ref="W-S-BW2", face="right",
                start=inch(0), length=inch(65.375),
                elevation=inch(86), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="PAX wall rail (93 in.)"),
    # East shelf frames: rail backing spans stud-002..005 around the 45 3/4"..65 3/8" frame.
    # The SS2 rail fasteners reach the wood backing through BED1's resilient channel.
    WallBacking(uid="AK5C5N4Q60", tag="BK-S-SS2-PAX-EAST", wall_ref="W-S-SS2", face="left",
                start=inch(32), length=inch(48),
                elevation=inch(86), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="East PAX shelf frame wall rail (93 in.)"),
    WallBacking(uid="WWKGDCM4PA", tag="BK-S-BD1-PAX-EAST", wall_ref="W-S-BD1", face="left",
                start=inch(32), length=inch(48),
                elevation=inch(86), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="East PAX shelf frame wall rail (93 in.)"),
    WallBacking(uid="XK6128ZS78", tag="BK-S-BD2-PAX", wall_ref="W-S-BD2", face="left",
                start=inch(64), length=inch(98.375),
                elevation=inch(86), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="PAX wall rail (93 in.)"),
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
    WallBacking(uid="YQYFFHW9T6", tag="BK-A-BATH-S-SINK", wall_ref="W-A-BATH-S",
                elevation=inch(25), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="bar sink hanger (27 in.)"),
]

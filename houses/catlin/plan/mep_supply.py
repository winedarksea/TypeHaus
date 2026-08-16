# haus: editable
# Catlin MEP — water supply — the house entry, hot/cold distribution, hydrant branches.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# The in-line valves, hammer arrestors and stops on these runs are authored separately in
# plan/mep_supply_devices.py.

from typehaus import (
    PipeRun,
    PipeSystem,
    ft,
    inch,
    pt,
)
from typehaus.model import m

# --- Water supply: the house entry out to the garage hydrant ------------------------
#
# The project's first PipeSystem.WATER_COLD run — everything authored before this is DRAIN
# or VENT. It starts at the house's water entry (5', 0'), where site.py's WATER UtilityLine
# terminates, and runs north under the basement slab and then out under grade to the garage,
# surfacing through SP-G-HYDRANT (params/foundations.py) at the hydrant.
#
# Elevations are the burial depth, not a ceiling height: the run leaves the entry at the
# service's own 6' depth and stays there. That is what keeps the hydrant's shutoff — which
# sits at the *end* of this run — at the 72" bury the code wants, well below the 42" frost
# depth the footings are set to. It is deliberately NOT routed up into the garage and back
# down: a supply line that rises above frost anywhere along its length freezes there.
#
# Filed on ``main`` rather than ``basement`` even though it runs under both: PipeRun
# elevations resolve as ``storey datum + authored``, and main's datum is 0'-0" = grade. On
# the basement's -9' datum the same authored -6' would resolve to -15' absolute, and the
# authored number would stop meaning "six feet down".
#
# The interior shutoff is ED/EQ-free by design: it is the hydrant's own valve at the
# buried end plus the isolation valve immediately downstream of the slab penetration, both
# of which mep.hydrant_freeze_depth asserts against this run's geometry.
# Re-routed 2026-07-29: the buried leg now runs at x=5' the whole way north (it used to
# hug the garage's west footing 8" off its edge for 24', inside the 45° influence line),
# crossing *under* FT-GF-S-DR through SP-GF-S-HYD and rising through SP-G-HYDRANT at the
# fixture.
#
# Finished 2026-08-15. That re-route stopped one vertex short: the line still turned west
# at y=61' and ran out to x=1'-6" to meet the hydrant, which put its last 4'-6" — and the
# riser, and the weep stone — back 8" off FT-GF-W's edge at 22" below bearing, the exact
# condition the re-route existed to leave. Moving the hydrant onto the x=5' service line
# (params/foundations.py) deletes the jog rather than protecting it, so the run is now a
# straight line from the water entry to the fixture and touches no footing but FT-GF-S-DR.
#
# The three basement wall crossings (S1 / CW / N3) are cast horizontal sleeves at the -6'
# bury; between them the line runs exposed across the heated basement at the same
# elevation, which is what keeps every buried vertex at the full 72" the fixture is
# specified for
# (`mep.hydrant_freeze_depth` walks all of them; the terminal rise is the hydrant's own
# self-draining barrel and is exempt).
WATER_SUPPLY = [
    PipeRun(uid="CMP920AAAA", tag="PR-G-HYDRANT-CW", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(0)), pt(ft(5), ft(59, 6)), pt(ft(5), ft(59, 6))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(-6), ft(-6), ft(0, 4.8)),
            serves=("FX-G-HYDRANT",)),
]

# --- Domestic hot/cold distribution (2026-07-29 plumbing pass) -----------------------
#
# PEX home-run-lite: a 1" cold trunk tees off the water service where it crosses the
# house (the hydrant line above IS the service; the tee at (5', 1') rises to the
# basement ceiling), and a 1" hot trunk leaves EQ-B-WH. Both run the ceiling band just
# south of the y=18' wall (cold at y=16'-2.4", hot at y=15'-10.8" — 3.6" apart, under the
# routed drains' y=16'-6" line), cross the concrete through their own WALL_SLEEVES, and
# rise to each wet-wall group through the SUPPLY_SLEEVES cast in the deck. `serves` on a
# trunk is the union of everything downstream, so `mep.pipe_sizing` sums the real WSFU.
# Filed on ``basement`` (datum -9'): ceiling runs read as 8'-ish heights.
#
# The cold trunk went from 1" to 1 1/4" on 2026-07-30, and it is worth saying why rather than
# just how: the stair-foot bathroom and the sauna shower added 4 WSFU of cold, taking the trunk
# from 30 to 34 against the 32 a 1" branch carries in Table 610.4's 46–60 psi / <100' column.
# Nothing else about the distribution changed — the hot trunk is still 1" at 21.5 WSFU — and
# the one cast crossing the trunk makes on its way east (SP-B-CS2-CW) grew with it.
SUPPLY = [
    PipeRun(uid="CBPW30AAAA", tag="PR-B-CW-TRUNK", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(1)), pt(ft(5), ft(1)), pt(ft(5), ft(16)),
                  pt(ft(8), ft(16)), pt(ft(29, 0.6), ft(16)),
                  pt(ft(29, 0.6), ft(34, 1.2)), pt(ft(29, 0.6), ft(34, 1.2))),
            diameter=inch(1.25), material="copper", finish="lacquered",
            elevations=(ft(3), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2),
                        ft(8, 1.2), ft(12, 6)),
            serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV", "FX-M-BATH2-WC",
                    "FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-SINK",
                    "FX-M-LAUNDRY", "FX-M-KITCH-SINK",
                    "FX-B-BATH-WC", "FX-B-BATH-LAV", "FX-B-SAUNA-SH",
                    "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2",
                    "FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH",
                    # The two south-face wall hydrants (2026-08-01), 2.5 WSFU cold each.
                    # 34 -> 39 on a 1 1/4" trunk that carries 64 in Table 610.4's 46-60 psi
                    # column, so the tee costs nothing in size.
                    "FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    PipeRun(uid="CBPW31AAAA", tag="PR-B-HW-TRUNK", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(m(1.88684), m(10.0015)),
                  pt(ft(6, 6), ft(19, 2.4)), pt(ft(6, 6), ft(15, 6))),
            diameter=inch(1), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(4), ft(8), ft(8), ft(8)),
            serves=("FX-M-BATH1-LAV", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK", "FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK",
                    "FX-M-KITCH-SINK",
                    "FX-B-BATH-LAV", "FX-B-SAUNA-SH",
                    "FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                    "FX-S-VANITY-LAV2", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH",
                    # The dishwasher was taking hot water from a branch that never declared
                    # it (2026-08-01). Undeclared, its 1.5 WSFU was missing from the trunk's
                    # load *and* `mep.water_hammer_arrestor` had no supply to ask about, so
                    # the quick-closing valve on it went ungraded rather than failing.
                    "APPL-M-DW")),
    # Cold feed to the water heater itself (equipment, not a fixture — no fixture units).
    PipeRun(uid="CBPW32AAAA", tag="PR-B-CW-WH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(5, 6), ft(16, 9.6)), pt(ft(5, 6), ft(19, 2.4)),
                  pt(m(1.88684), m(10.0015)), pt(m(1.88684), m(10.0015))),
            diameter=inch(1), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(4))),
    # Main-storey groups.
    PipeRun(uid="CBPW33AAAA", tag="PR-B-CW-BATH1", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(7, 4.8), ft(16, 9.6)),
                  pt(ft(7, 4.8), ft(19, 2.4)), pt(ft(6), ft(23, 7.2)),
                  pt(ft(6), ft(23, 7.2)), pt(ft(6), ft(23, 7.2))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(9), ft(12, 6)),
            wall_refs=(None, None, None, None, "W-M-BAE"),
            serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV")),
    PipeRun(uid="CBPW34AAAA", tag="PR-B-HW-BATH1", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(6), ft(24)), pt(ft(6), ft(24)),
                  pt(ft(6), ft(24))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(9), ft(12, 6)),
            wall_refs=(None, None, "W-M-BAE"),
            serves=("FX-M-BATH1-LAV",)),
    PipeRun(uid="CBPW35AAAA", tag="PR-B-CW-BATH2", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(2, 3), ft(16)),
                  pt(ft(2, 3), ft(17, 2.4)), pt(ft(2, 3), ft(17, 2.4))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(12)),
            serves=("FX-M-BATH2-WC", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK")),
    PipeRun(uid="CBPW36AAAA", tag="PR-B-HW-BATH2", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(2, 3), ft(15, 6)),
                  pt(ft(2, 3), ft(16, 9.6)), pt(ft(2, 3), ft(16, 9.6))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(8), ft(12)),
            serves=("FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-SINK")),
    # The laundry pair rises inside W-M-BA2E, so each riser is split at the deck top
    # (ft(9) basement-relative = 0'-0" project) like the BATH1 pair above: the lower leg is
    # the sleeved concrete crossing and hosts no wall, the leg above it is in the stud
    # cavity and names it. `mep.wet_wall_occupancy` checks the declared segment's z-range
    # against the wall's own extent, so a single riser spanning both would read as escaping
    # the wall it is actually inside.
    PipeRun(uid="CBPW37AAAA", tag="PR-B-CW-WASH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(8), ft(16)), pt(ft(8), ft(20, 7.2)),
                  pt(ft(8), ft(20, 7.2)), pt(ft(8), ft(20, 7.2))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(9), ft(12)),
            wall_refs=(None, None, "W-M-BA2E"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeRun(uid="CBPW38AAAA", tag="PR-B-HW-WASH", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(8), ft(21, 2.4)),
                  pt(ft(8), ft(21, 2.4)), pt(ft(8), ft(21, 2.4))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(9), ft(12)),
            wall_refs=(None, None, "W-M-BA2E"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeRun(uid="CBPW39AAAA", tag="PR-B-HW-KITCH", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(29, 6.6), ft(15, 6)),
                  pt(ft(29, 6.6), ft(33, 7.2)), pt(ft(29, 6.6), ft(33, 7.2))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(8), ft(12, 6)),
            serves=("FX-M-KITCH-SINK", "APPL-M-DW")),
    # Second-storey groups: risers straight up through the deck to the wet walls above.
    # These two climb two storeys of wall to reach the hall bath, so each riser is split at
    # both storey lines — deck top ft(9) and the second floor ft(19) (basement-relative;
    # 0'-0" and 10'-0" project) — and names the wall it is inside on each leg. The
    # main-storey leg passes through a storage-room 2x4 partition (3.5" cavity, ample for
    # 3/4" PEX); only the second-storey leg is in a staggered wet wall.
    PipeRun(uid="CBPW40AAAA", tag="PR-B-CW-SBATH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(4), ft(16, 9.6)), pt(ft(4), ft(26, 4)),
                  pt(ft(5, 7.2), ft(26, 4)), pt(ft(5, 7.2), ft(26, 4)),
                  pt(ft(5, 7.2), ft(26, 4)), pt(ft(5, 7.2), ft(26, 4))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(9), ft(19),
                        ft(21, 6)),
            wall_refs=(None, None, None, None, "W-M-STOS", "W-S-BD-N"),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # Riser moved 2.4" -> 4" east of N-M-BA1 (2026-08-02, RM-M-MUD-CLOSET): W-M-MUDC-E now
    # tees into that node from the north, and the junction trims W-M-STOS2's stud cavity
    # back to the partition's east face at x=6'-2 3/8" — the old x=6'-2.4" left half the
    # pipe in the corner pack. 6'-4" is the first clean bay past the tee, still 6 1/2"
    # west of D-M-MUD's jamb pack here and 8" west of D-S-BATH1's on the leg above.
    # SP-M-HW-SBATH (the SL-M-DECK sleeve this riser crosses) moved with it.
    PipeRun(uid="CBPW41AAAA", tag="PR-B-HW-SBATH", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(6, 4), ft(26, 4)),
                  pt(ft(6, 4), ft(26, 4)), pt(ft(6, 4), ft(26, 4)),
                  pt(ft(6, 4), ft(26, 4))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(9), ft(19), ft(21, 6)),
            wall_refs=(None, None, "W-M-STOS2", "W-S-BD-N1B"),
            serves=("FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                    "FX-S-VANITY-LAV2")),
    PipeRun(uid="CBPW42AAAA", tag="PR-B-CW-SUITE", system=PipeSystem.WATER_COLD,
            path=(pt(ft(8), ft(16)), pt(ft(13, 7.2), ft(16, 10.8)),
                  pt(ft(13, 7.2), ft(16, 10.8))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(21, 6)),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
    PipeRun(uid="CBPW43AAAA", tag="PR-B-HW-SUITE", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(14, 2.4), ft(16, 10.8)),
                  pt(ft(14, 2.4), ft(16, 10.8))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(21, 6)),
            serves=("FX-S-SUITEBATH-LAV", "FX-S-SUITEBATH-TUBSH")),
    # The stair-foot bathroom, fed from the water-heater corner down the mechanical room's
    # ceiling — the same pair of runs that fed FX-1 until 2026-07-30 (same uids), turned east
    # through W-B-STR's two new sleeves instead of dropping to a sink at x=7'. Each crosses at
    # its own y so the sleeves stay distinguishable (cold 20'-3", hot 19'-9"), then runs east
    # to x=16' and north to the partition line, where both drop inside W-B-BA-N's cavity to the
    # fixtures. Cold carries the WC and the lavatory (3.25 WSFU), hot the lavatory alone.
    PipeRun(uid="CBPW44AAAA", tag="PR-B-CW-BATH", system=PipeSystem.WATER_COLD,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(7), ft(26)), pt(ft(7), ft(20, 3)),
                  pt(ft(16), ft(20, 3)), pt(ft(16), ft(21, 9.375)),
                  pt(ft(16), ft(21, 9.375))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2),
                        ft(2, 6)),
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    PipeRun(uid="CBPW45AAAA", tag="PR-B-HW-BATH", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(7, 3.6), ft(26)),
                  pt(ft(7, 3.6), ft(19, 9)), pt(ft(16), ft(19, 9)),
                  pt(ft(16), ft(21, 9.375)), pt(ft(16), ft(21, 9.375))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8), ft(8), ft(8), ft(8), ft(8), ft(2, 6)),
            serves=("FX-B-BATH-LAV",)),
    # The sauna shower's mixer, the first supply this room has ever had. Both legs tee off the
    # trunks where they already run — cold off PR-B-CW-TRUNK's y=16' leg, hot off the end of
    # PR-B-HW-TRUNK at (6'-6", 15'-6") — come down the aisle at x=17'-4", pass through
    # W-B-SA-N's stud bay (a framed partition needs no cast sleeve, unlike every service the
    # bathroom gets) and drop to the valve at 4'-6" inside W-B-CS's liner build-up, 4" apart on
    # either side of the pan's centreline. x=17'-4" keeps both of them 2" clear of W-B-CS2's
    # concrete face at 17'-6" on the way past. No supply runs to FX-B-SAUNA-FD: a floor drain
    # has none, which is why FX-FLOOR-DRAIN declares neither WATER_COLD nor WATER_HOT.
    PipeRun(uid="CBPW46AAAA", tag="PR-B-CW-SAUNA", system=PipeSystem.WATER_COLD,
            path=(pt(ft(17, 4), ft(16)), pt(ft(17, 4), ft(12, 2)),
                  pt(ft(17, 4), ft(12, 2))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(4, 6)),
            serves=("FX-B-SAUNA-SH",)),
    PipeRun(uid="CBPW47AAAA", tag="PR-B-HW-SAUNA", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(17, 4), ft(15, 6)),
                  pt(ft(17, 4), ft(11, 10)), pt(ft(17, 4), ft(11, 10))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8), ft(8), ft(8), ft(4, 6)),
            serves=("FX-B-SAUNA-SH",)),
]

# --- The two south-face wall hydrants (2026-08-01) -----------------------------------
#
# One branch, two hydrants, and the route is decided by a wall that is not there.
#
# A frost-free *wall* hydrant is fed from inside: its seat sits in the stud cavity and the
# pipe reaching it has to arrive inside that cavity. On this house a supply cannot arrive
# from below. The main-storey exterior wall's stud bay is at y 0.5"..6" off the sheathing
# plane, and directly under it stands W-B-S1, 12" of cast concrete spanning y 0"..12" — a
# riser through SL-M-DECK into that cavity would come up through the top of a bearing wall.
# The same is true of W-M-C1 over W-B-CS on the centre line.
#
# So both hydrants are fed from *above*, out of the second floor's joist space, which is
# framed (FS-SECOND, 11 7/8" I-joists) and reaches every exterior wall in the house. One
# riser leaves the basement, and up there it splits: one leg drops down inside W-M-S1 to the
# porch hydrant, the other rises into W-S-S1 to the balcony hydrant. Neither leg is ever
# outboard of the wall's 4" of continuous exterior insulation, which is what makes a pipe in
# this exterior cavity a warm pipe rather than a burst one.
#
# The riser stands in W-M-BDN1, a main-storey 2x4 partition (3.5" cavity — ample for 3/4"
# PEX, the same clearance PR-B-CW-SBATH's W-M-STOS leg has) whose line at y=13'-4" is over
# open basement ceiling at x=6', so its deck crossing (SP-M-CW-HYD) lands in the slab and
# not on a wall below.
HYDRANT_BRANCH_BASEMENT = [
    # Two runs for one branch, because the material changes at the deck. The ceiling leg is
    # hung in the open under cast concrete, so it is lacquered copper like everything else
    # down here; from the slab up it is inside a wall and a joist bay, where nobody sees it
    # and PEX's tolerance for a hard freeze is worth more than a finish.
    PipeRun(uid="X4M2QP7B0K", tag="PR-B-CW-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(16)), pt(ft(6), ft(13))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2)),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    PipeRun(uid="Z5NB8QMK2H", tag="PR-B-CW-HYD-RISER", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(13)), pt(ft(6), ft(13)), pt(ft(6), ft(13)),
                  pt(ft(6), ft(13))),
            diameter=inch(0.75), material="pex",
            # Basement-relative: 8'-1.2" is the ceiling trunk band, 9'-0" is the top of the
            # 9" deck (0'-0" project), 18'-0" is the top plate of W-M-BDN1 (9'-0" project —
            # main-storey partitions stop there, 9'-0" being the ceiling height), and
            # 18'-3" is 9'-3" project, inside the second floor's joist space, whose 11 7/8"
            # joists hang 9'-0 1/8" to 10'-0". The split at the plate is what
            # `mep.wet_wall_occupancy` grades: a declared in-wall segment has to stay inside
            # the wall's own z-extent, and a riser drawn straight from the deck to the joist
            # bay escapes it by 3".
            elevations=(ft(8, 1.2), ft(9), ft(18), ft(18, 3)),
            wall_refs=(None, "W-M-BDN1", None),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
]

# The joist-space distribution and the two legs off it. Filed on ``main`` (datum 0'-0")
# because these are the main storey's ceiling, and a main-relative elevation of 9'-3" reads
# as the height it is; on ``second`` the same plane would have to be authored as -0'-9".
#
# The east–west leg at y=0'-9" runs *along* a joist bay rather than across one. The leg that
# gets there from the riser crosses joists at x=6' and is drilled through their webs — 3/4"
# PEX in an 11 7/8" I-joist web, which is inside every manufacturer's hole chart and is why
# the branch is PEX here rather than the copper it becomes downstairs.
HYDRANT_BRANCH_MAIN = [
    PipeRun(uid="R9TC5VZ1WQ", tag="PR-M-CW-HYD-DIST", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(13)), pt(ft(6), ft(0, 9)), pt(ft(16, 8), ft(0, 9))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(9, 3)),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    # Porch leg: south into the wall's own plane (y=3 1/4", the 2x6 cavity's centre line),
    # then straight down inside W-M-S1 to the hydrant's seat at 2'-0".
    PipeRun(uid="B6HD0NKX3M", tag="PR-M-CW-PORCH-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12), ft(0, 9)), pt(ft(12), ft(0, 3.25)), pt(ft(12), ft(0, 3.25))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(2)),
            wall_refs=(None, "W-M-S1"),
            serves=("FX-M-PORCH-HYD",)),
    # Balcony leg: the same jog into the wall plane, then up. Split at 10'-0" because the
    # second floor is between: below that line the pipe is crossing the deck and hosted by
    # nothing, above it it is inside W-S-S1's cavity (which starts at 10'-0"), and
    # `mep.wet_wall_occupancy` grades a declared segment against the wall's own z-extent.
    PipeRun(uid="V2FJ8LRY6P", tag="PR-M-CW-BALC-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(16, 8), ft(0, 9)), pt(ft(16, 8), ft(0, 3.25)),
                  pt(ft(16, 8), ft(0, 3.25)), pt(ft(16, 8), ft(0, 3.25))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(10), ft(12)),
            wall_refs=(None, None, "W-S-S1"),
            serves=("FX-S-BALC-HYD",)),
    # The barrel. This short copper leg is the hydrant's own metal tube plus the sleeve over
    # it, modelled as a run so that the insulation has somewhere to be billed and so that
    # `mep.exterior_hydrant_protection` has something to grade. It is the one place in the
    # house where a supply pipe is *in* the envelope rather than behind it: 10" of metal
    # from the seat in the stud cavity, out through 1/2" sheathing, 2" polyiso, 2" EPS and
    # the rainscreen, to the escutcheon on the cladding face at y = -5". PEX stops at the
    # seat — continuing in copper inboard would extend the bridge into the room.
    PipeRun(uid="T8WQ3E5AZC", tag="PR-M-CW-PORCH-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12), ft(0, 3.25)), pt(ft(12), inch(-5))),
            diameter=inch(0.75), material="copper",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(ft(2), ft(2)),
            serves=("FX-M-PORCH-HYD",)),
]

# The balcony hydrant's barrel, filed on ``second`` (datum 10'-0") with the wall it pierces.
HYDRANT_BRANCH_SECOND = [
    PipeRun(uid="G7YB4XN2SD", tag="PR-S-CW-BALC-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(16, 8), ft(0, 3.25)), pt(ft(16, 8), inch(-5))),
            diameter=inch(0.75), material="copper",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(ft(2), ft(2)),
            serves=("FX-S-BALC-HYD",)),
]

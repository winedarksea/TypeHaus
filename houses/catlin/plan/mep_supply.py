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

# --- Water supply: the service lateral, hydrant to house ---------------------------
#
# The project's first WATER_COLD run: the water service lateral, from the entry at the
# garage yard hydrant (5', 59'-6") south to the house's north foundation, staying at the
# service's own 6' bury the whole way — a supply line that rises above frost anywhere along
# its length freezes there. Filed on ``main`` (datum 0'-0") so the authored elevations read
# straight off the drawing set; on ``basement`` (-9' datum) they would resolve nine feet
# lower.
#
# ** IT NO LONGER CROSSES THE HOUSE (2026-08-30). ** It ran (5', 0') -> (5', 59'-6"): the
# full 59'-6" from the SOUTH basement wall, straight through RM-B-WORKSHOP and
# RM-B-FURNACE, to the garage. That was not a routing choice — plan/site.py put the water
# UtilityLine's entry on the rear of the lot while the same file declares the street on the
# north, so the lateral had to traverse the building to reach the front. Worse, at -8'-10"
# with the basement slab topping out at -9'-1 7/16", those 36 feet of 3/4" PEX were lying
# 3 7/16" ABOVE the basement floor, in the room, not buried under it. Nothing graded it:
# `mep.hydrant_freeze_depth` asks only that every vertex hold its bury below GRADE, and
# grade over the basement is the same -2'-10" it is in the yard.
#
# With the entry at the front the lateral is 24'-0" of yard, the hydrant sits on the entry
# itself, and the house taps the lateral where it reaches the foundation. PR-B-CW-TRUNK
# tees off at (5', 35'-6") through SP-B-N3-HYD, which was already bored at exactly that
# station and depth for the old crossing's *exit*.
#
# **The bury is 6' below *grade*, and grade is -2'-10" (2026-08-21), so the run sits at
# -8'-10".** It dropped with the soil it is buried in, exactly as the garage foundation it
# passes under did: FT-GF-S-DR's bearing plane went from -4'-2" to -7'-0", and this run from
# -6'-0" to -8'-10", so the 22" of cover between them is unchanged. The terminal rise ends
# 4 4/5" above the garage slab, which is also 2'-10" lower than it was.
#
# Straightened 2026-07-29 through 2026-08-15 into a straight line from entry to hydrant at
# x=5', touching only FT-GF-S-DR — earlier routes jogged around the garage footing and
# clipped its 45° influence line. `mep.hydrant_freeze_depth` checks every buried vertex holds
# the full 72" bury; the terminal rise is the hydrant's own self-draining barrel and exempt.
WATER_SUPPLY = [
    PipeRun(uid="CMP920AAAA", tag="PR-G-HYDRANT-CW", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(35, 6)), pt(ft(5), ft(59, 6)), pt(ft(5), ft(59, 6))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(-8, -10), ft(-8, -10), ft(-2, -5.2)),
            serves=("FX-G-HYDRANT",)),
]

# --- Domestic hot/cold distribution (2026-07-29 plumbing pass) -----------------------
#
# PEX home-run-lite: 1" cold trunk tees off the water service at (5', 35'-6"), 1" hot trunk
# leaves EQ-B-WH; both run the ceiling band south of the y=18' wall, cross the concrete
# through their own WALL_SLEEVES, and rise to each wet-wall group through SUPPLY_SLEEVES.
# `serves` on a trunk is the union of everything downstream, so `mep.pipe_sizing` sums the
# real WSFU. Filed on ``basement`` (datum -9') so ceiling runs read as 8'-ish heights.
#
# Cold trunk went 1" -> 1 1/4" on 2026-07-30: the stair-foot bath and sauna shower added 4
# WSFU, taking it from 30 to 34 against the 32 a 1" branch carries (Table 610.4, 46-60 psi /
# <100'). Hot trunk stays 1" at 21.5 WSFU; SP-B-CS2-CW (the trunk's cast crossing) grew with it.
SUPPLY = [
    # ** THE TRUNK NOW MEETS ITS SERVICE (2026-08-30). ** It started at (5', 1') at
    # +2'-9 7/16" on this datum, i.e. -6'-2 9/16" absolute, and called that the tee off the
    # service — but the service passed under that point at -8'-10". A 2'-7 1/2" vertical gap
    # with nothing in it: the house's cold water was fed by a run that ended in mid-air. The
    # 2026-08-21 grade drop took the service down and the trunk did not follow.
    #
    # With the entry at the front (plan/site.py) the tee belongs at the north wall, so the
    # riser moves to (5', 35'-6") — SP-B-N3-HYD's station — and starts at +0'-2", which IS
    # -8'-10" absolute, on the lateral. It then runs south down the RM-B-FURNACE ceiling
    # band to y=16' and picks up its old route unchanged, crossing W-B-CW (framed, and a
    # plumbing wall) with a bored hole rather than a sleeve.
    PipeRun(uid="CBPW30AAAA", tag="PR-B-CW-TRUNK", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(35, 6)), pt(ft(5), ft(35, 6)), pt(ft(5), ft(16)),
                  pt(ft(8), ft(16)), pt(ft(29, 9.6), ft(16)),
                  pt(ft(29, 9.6), ft(34, 1.2)), pt(ft(29, 9.6), ft(34, 1.2))),
            diameter=inch(1.25), material="copper", finish="lacquered",
            elevations=(inch(2), ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(12, 7.4375)),
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
            path=(pt(ft(5, 6), ft(24)), pt(ft(5, 6), ft(24)),
                  pt(ft(6, 6), ft(19, 2.4)), pt(ft(6, 6), ft(15, 6))),
            diameter=inch(1), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(3, 9.4375), ft(7, 9.4375), ft(7, 9.4375), ft(7, 9.4375)),
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
                  pt(ft(5, 6), ft(24)), pt(ft(5, 6), ft(24))),
            diameter=inch(1), material="copper", finish="lacquered",
            elevations=(ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(3, 9.4375))),
    # Main-storey groups.
    #
    # ** THE BATH1 PAIR STOOD IN THE BATHROOM DOORWAY UNTIL 2026-08-30, AND IT IS THE ONE
    # DEFECT NOTHING IN THIS FILE COULD SEE. ** The cold rose at (6'-0", 23'-7.2") and the
    # hot at (6'-0", 24'-0"), both from the deck to 3'-6"; D-M-BATH1's rough opening in
    # W-M-BAE runs y 23'-6"..25'-6", so both were 42" of copper standing in a 24" door with
    # no stud within a foot of either and a 2-2x8 header overhead that cannot be bored.
    # `mep.wet_wall_occupancy` passed them the whole time — a riser inside the wall's
    # FOOTPRINT is inside the wall, and a hole in that footprint is still footprint.
    # `mep.run_through_opening` is what found it.
    #
    # ** THEY LEFT W-M-BAE ALTOGETHER, AND THE BAY CENSUS IS WHY. ** Measured off the
    # resolved wall, faces in project inches along y:
    #   end stud 271.385"/272.885"  |  SOUTH BAY 4 3/8"  |  2x4 at 277.25"/278.75"
    #   king 279"/280.5", jack 280.5"/282"  |  D-M-BATH1 RO 282"..306"  |  jack, king to 309"
    #   2x4 at 309.25"/310.75"  |  NORTH BAY 6 1/2"  |  corner stud from 317.25"
    # Two bays, one each side of the door, and the 1/4" slivers beside the jambs are not
    # bays. The pair cannot be split across the door — hot and cold for one lavatory would
    # then have to cross the head to meet, which is the defect moved up 3'-6" and left
    # undrawn — so both have to fit the SAME bay, and neither bay takes them:
    #   * SOUTH BAY. The nearer one, and not empty: PR-B-LAV1-DRAIN (plan/mep_drainage.py)
    #     drops at y=275.94" and a 1 1/2" DWV pipe is 1.9" over the pipe, leaving 2 3/32"
    #     between its south side and the end stud. A bare 3/4" copper fits that. The hot line
    #     carries a 1" fiberglass sleeve — 2 7/8" over the pipe — and does not, at any
    #     station and at any depth in the cavity: to pass the drain in x it would have to
    #     centre outside the 5 1/2" stud space entirely.
    #   * NORTH BAY. 6 1/2" and empty, and 2 7/8" + 7/8" of pipe in it pushes the second
    #     riser past y=315.625", which is W-M-STOS's finish face. A stop valve half an inch
    #     off a finished corner is not a stop anybody can turn. It is also the WRONG END of
    #     the room: both fixtures are at the south end, so every branch off it would cross
    #     the door head anyway.
    #
    # ** W-M-HS1 IS THE WALL BOTH FIXTURES ACTUALLY PLUMB INTO, AND IT HAS EIGHT BAYS. **
    # FX-M-BATH1-WC's carrier stands in it and PR-B-WC1-DRAIN already drops through it at
    # x=26.409"; FX-M-BATH1-LAV's 24" carcass backs onto its finish face at y=271.385",
    # spanning x 41.5"..65.5". It is INT_2X6_STAGGERED_PLUMBING, nonbearing, 5 1/2" of
    # continuous cavity, and it carries no opening at all — nothing to stand in. Its studs
    # resolve on an 8" stagger at x = 7.385", 16", 24", 32", 40", 48", 56", 64", 72", so
    # every bay is 6 1/2" clear and the two behind the vanity are x 48.75"..55.25" and
    # x 56.75"..63.25". The pair takes those two: 8" apart on the wall's own module, both
    # behind the lavatory, with the cold 2'-9 5/8" along the same cavity from the water
    # closet's carrier at x=26.409", and no door between any of them.
    PipeRun(uid="CBPW33AAAA", tag="PR-B-CW-BATH1", system=PipeSystem.WATER_COLD,
            # Riser at (5'-0", 22'-4") — the east bay of the pair, centred with 2.81" of
            # clear to the 2x4 each side, on W-M-HS1's axis so a 7/8" pipe sits mid-cavity.
            # The cold is the east one because of how it ARRIVES: the ceiling leg comes off
            # the trunk in the south-east and the hot comes off the water heater in the
            # west, so putting them this way round is what keeps the two feeds out of each
            # other's lane below the deck.
            #
            # The old route ran the diagonal all the way to x=6'-0" and turned up there. It
            # cannot now: PR-B-MAIN-DRAIN's 4" trunk occupies x=6'-0" from y=16'-6" to
            # y=22'-7", and at y=22'-4" its crown is at -1'-2 1/4" against this run's
            # -1'-2.8" — they would share the same 2". So the diagonal stops SHORT, at
            # (5'-0", 21'-0"), and the last 1'-4" runs north to the wall. Where it does
            # cross the 4" trunk's lane, at (6'-0", 20'-3"), the trunk has fallen to
            # -1'-8.6" and there is 3.1" of clear between the two pipes' surfaces.
            path=(pt(ft(5), ft(16)), pt(ft(7, 4.8), ft(16, 9.6)),
                  pt(ft(7, 4.8), ft(19, 2.4)), pt(ft(5), ft(21)),
                  pt(ft(5), ft(22, 4)), pt(ft(5), ft(22, 4)), pt(ft(5), ft(22, 4))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375),
                        ft(7, 10.6375), ft(9, 1.4375), ft(12, 7.4375)),
            wall_refs=(None, None, None, None, None, "W-M-HS1"),
            serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV")),
    PipeRun(uid="CBPW34AAAA", tag="PR-B-HW-BATH1", system=PipeSystem.WATER_HOT,
            # Riser at (4'-4", 22'-4") — the west bay, 1.81" of clear each side of the
            # 2 7/8" jacket. Off the trunk's end at the water heater, west along y=24'-0"
            # and then straight south to the wall: the leg passes over PR-B-WH-TPR's drop at
            # (4'-4", 24'-0"), which starts 4'-3" lower, and clears PR-M-S-BATH1-DRAIN's
            # diagonal by 4.1" where it crosses at y=24'-0" (x=4'-10.5", crown -1'-9.6"). Nothing here shares a lane with
            # PR-B-CW-BATH1, which is why the two risers land in this order.
            path=(pt(ft(5, 6), ft(24)), pt(ft(4, 4), ft(24)), pt(ft(4, 4), ft(22, 4)),
                  pt(ft(4, 4), ft(22, 4)), pt(ft(4, 4), ft(22, 4))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(7, 9.4375), ft(7, 9.4375), ft(7, 9.4375), ft(9, 1.4375), ft(12, 7.4375)),
            wall_refs=(None, None, None, "W-M-HS1"),
            serves=("FX-M-BATH1-LAV",)),
    PipeRun(uid="CBPW35AAAA", tag="PR-B-CW-BATH2", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(2, 3), ft(16)),
                  pt(ft(2, 3), ft(17, 2.4)), pt(ft(2, 3), ft(17, 2.4))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(12, 1.4375)),
            serves=("FX-M-BATH2-WC", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK")),
    PipeRun(uid="CBPW36AAAA", tag="PR-B-HW-BATH2", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(2, 3), ft(15, 6)),
                  pt(ft(2, 3), ft(16, 9.6)), pt(ft(2, 3), ft(16, 9.6))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(7, 9.4375), ft(7, 9.4375), ft(7, 9.4375), ft(12, 1.4375)),
            serves=("FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-SINK")),
    # The laundry pair riser splits at the deck top (ft(9) basement-relative = 0'-0"
    # project), like the BATH1 pair above: sleeved concrete crossing below, stud cavity
    # above, each leg naming its own host so `mep.wet_wall_occupancy` doesn't read a single
    # riser as escaping the wall it's actually inside.
    #
    # ** BOTH REACH THE SINK NOW, 2026-08-29 (owner). ** They have claimed
    # `serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")` since they were drawn, and they got as
    # far as the WASHER BOX at (8'-0", 36") and stopped — the basin is 3'-0" further east
    # and nothing modelled crossed that ground. What the two runs do beyond the box:
    #
    #   riser top 36"  ->  south inside W-M-BA2E  ->  east inside W-M-CLN  ->  drop to 20"
    #
    # 20" is the stop height inside the tub's own cabinet (FX-LAUNDRY-SINK-24 is a 34" rim
    # in a cased base, 43" over the faucet), NOT the 36" the washer box stands at — a stub
    # above the rim would come out of the wall in front of the basin. Cold lands 4" west of
    # the bowl centre, hot 4" east: hot on the LEFT of someone facing the faucet, who is
    # standing north of a sink whose back is on the south wall.
    #
    # ** FOUR THINGS KEEP THE PAIR APART AND OFF THE CORNER, AND EVERY ONE IS LOAD-BEARING: **
    #   * ** the cold drops 36" -> 32" at its own riser head ** and travels the whole way at
    #     32", 4" under the hot. Both share the y=18'-1" lane, so a shared elevation would be
    #     one pipe inside the other; stacked is how the pair is actually run in a cavity.
    #   * ** the hot jogs 2" west to x=7'-10" before turning south. ** The cold riser stands
    #     at x=8'-0" and tops out at exactly the hot's 36" — same lane, same height, and the
    #     hot leg would run straight through it on its way south from y=21'-2 2/5".
    #   * ** the cold stops 8" short of the hot ** (x=11'-6 1/2" against 12'-2 1/2", the bowl
    #     centre +/-4", hot on the LEFT of someone facing the faucet). So the hot's drop at
    #     12'-2 1/2" comes down past 32" east of where the cold's leg ends, and misses it.
    #   * ** THE CORNER SEGMENT NAMES NO WALL, DELIBERATELY. ** W-M-BA2E ends at y=18'-0" and
    #     W-M-CLN starts at x=8'-3 3/8": the two only TOUCH, so no point is inside both and a
    #     leg claiming either one leaves its structure footprint — `mep.wet_wall_occupancy` is
    #     an ERROR about exactly this and said so on the first build. `None` is the honest
    #     answer, and it is the same `None` the sleeved basement crossing already carries: the
    #     4 1/2" from x=8'-0" to x=8'-4 1/2" is the corner post, and it is bored.
    # The wall this all rides in is why W-M-CLN was retyped (storeys/main.py). Through the
    # 2x4 partition that was there, this leg bores every stud between x=8'-0" and the sink
    # and `mep.wet_wall_occupancy` grades it `long_horizontal`; through the staggered pair it
    # threads between two offset stud rows and bores nothing but that one corner post.
    PipeRun(uid="CBPW37AAAA", tag="PR-B-CW-WASH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(8), ft(16)), pt(ft(8), ft(20, 7.2)),
                  pt(ft(8), ft(20, 7.2)), pt(ft(8), ft(20, 7.2)),
                  pt(ft(8), ft(20, 7.2)), pt(ft(8), ft(18, 1)),
                  pt(ft(8, 4.5), ft(18, 1)), pt(ft(11, 6.5), ft(18, 1)),
                  pt(ft(11, 6.5), ft(18, 1))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(7, 10.6375), ft(7, 10.6375), ft(9, 1.4375), ft(12, 1.4375),
                        ft(11, 9.4375), ft(11, 9.4375), ft(11, 9.4375), ft(11, 9.4375),
                        ft(10, 9.4375)),
            wall_refs=(None, None, "W-M-BA2E", "W-M-BA2E", "W-M-BA2E", None,
                       "W-M-CLN", "W-M-CLN"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeRun(uid="CBPW38AAAA", tag="PR-B-HW-WASH", system=PipeSystem.WATER_HOT,
            path=(pt(ft(5, 6), ft(24)), pt(ft(8), ft(21, 2.4)),
                  pt(ft(8), ft(21, 2.4)), pt(ft(8), ft(21, 2.4)),
                  pt(ft(7, 10), ft(21, 2.4)), pt(ft(7, 10), ft(18, 1)),
                  pt(ft(8, 4.5), ft(18, 1)), pt(ft(12, 2.5), ft(18, 1)),
                  pt(ft(12, 2.5), ft(18, 1))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(7, 9.4375), ft(7, 9.4375), ft(9, 1.4375), ft(12, 1.4375),
                        ft(12, 1.4375), ft(12, 1.4375), ft(12, 1.4375), ft(12, 1.4375),
                        ft(10, 9.4375)),
            wall_refs=(None, None, "W-M-BA2E", "W-M-BA2E", "W-M-BA2E", None,
                       "W-M-CLN", "W-M-CLN"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeRun(uid="CBPW39AAAA", tag="PR-B-HW-KITCH", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(30, 3.6), ft(15, 6)),
                  pt(ft(30, 3.6), ft(33, 7.2)), pt(ft(30, 3.6), ft(33, 7.2))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(7, 9.4375), ft(7, 9.4375), ft(7, 9.4375), ft(12, 7.4375)),
            serves=("FX-M-KITCH-SINK", "APPL-M-DW")),
    # Second-storey groups: risers climb two storeys to the hall bath, split at both deck
    # top (ft(9) basement-rel = 0'-0" project) and second floor (ft(19) = 10'-0" project),
    # naming the host wall on each leg. Main-storey leg is in a 2x4 partition (3.5" cavity,
    # ample for 3/4" PEX); only the second-storey leg is in a staggered wet wall.
    PipeRun(uid="CBPW40AAAA", tag="PR-B-CW-SBATH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(4), ft(16, 9.6)), pt(ft(4), ft(26, 6)),
                  pt(ft(5, 7.2), ft(26, 6)), pt(ft(5, 7.2), ft(26, 6)),
                  pt(ft(5, 7.2), ft(26, 6)), pt(ft(5, 7.2), ft(26, 6))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(9, 1.4375), ft(19, 1.4375), ft(21, 7.4375)),
            wall_refs=(None, None, None, None, "W-M-STOS", "W-S-BD-N"),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # Riser moved 2.4" -> 4" east of N-M-BA1 (2026-08-02, RM-M-MUD-CLOSET): the old x=6'-2.4"
    # left half the pipe in W-M-STOS2's corner pack after W-M-MUDC-E tee'd in. 6'-4" is the
    # first clean bay past the tee (6 1/2" west of D-M-MUD's jamb pack, 8" west of D-S-BATH1's
    # above). SP-M-HW-SBATH moved with it.
    PipeRun(uid="CBPW41AAAA", tag="PR-B-HW-SBATH", system=PipeSystem.WATER_HOT,
            path=(pt(ft(5, 6), ft(24)), pt(ft(6, 4), ft(26, 6)),
                  pt(ft(6, 4), ft(26, 6)), pt(ft(6, 4), ft(26, 6)),
                  pt(ft(6, 4), ft(26, 6))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(7, 9.4375), ft(7, 9.4375), ft(9, 1.4375), ft(19, 1.4375), ft(21, 7.4375)),
            wall_refs=(None, None, "W-M-STOS2", "W-S-BD-N1B"),
            serves=("FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                    "FX-S-VANITY-LAV2")),
    PipeRun(uid="CBPW42AAAA", tag="PR-B-CW-SUITE", system=PipeSystem.WATER_COLD,
            path=(pt(ft(8), ft(16)), pt(ft(13, 7.2), ft(16, 10.8)),
                  pt(ft(13, 7.2), ft(16, 10.8))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(7, 10.6375), ft(7, 10.6375), ft(21, 7.4375)),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
    PipeRun(uid="CBPW43AAAA", tag="PR-B-HW-SUITE", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(14, 2.4), ft(16, 10.8)),
                  pt(ft(14, 2.4), ft(16, 10.8))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(7, 9.4375), ft(7, 9.4375), ft(21, 7.4375)),
            serves=("FX-S-SUITEBATH-LAV", "FX-S-SUITEBATH-TUBSH")),
    # Stair-foot bathroom, fed off the same pair of runs (same uids) that fed FX-1 until
    # 2026-07-30, now turned east through W-B-STR's two sleeves at their own y (cold 20'-3",
    # hot 19'-9") to x=16', then north into W-B-BA-N's cavity. Cold carries the WC and
    # lavatory (3.25 WSFU), hot the lavatory alone.
    PipeRun(uid="CBPW44AAAA", tag="PR-B-CW-BATH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5, 6), ft(24)), pt(ft(7), ft(26)), pt(ft(7), ft(20, 3)),
                  pt(ft(16), ft(20, 3)), pt(ft(16), ft(21, 9.375)),
                  pt(ft(16), ft(21, 9.375))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375), ft(2, 3.4375)),
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    PipeRun(uid="CBPW45AAAA", tag="PR-B-HW-BATH", system=PipeSystem.WATER_HOT,
            path=(pt(ft(5, 6), ft(24)), pt(ft(7, 3.6), ft(26)),
                  pt(ft(7, 3.6), ft(19, 9)), pt(ft(16), ft(19, 9)),
                  pt(ft(16), ft(21, 9.375)), pt(ft(16), ft(21, 9.375))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(7, 9.4375), ft(7, 9.4375), ft(7, 9.4375), ft(7, 9.4375), ft(7, 9.4375), ft(2, 3.4375)),
            serves=("FX-B-BATH-LAV",)),
    # Sauna shower mixer, the first supply this room ever had. Both legs tee off the existing
    # trunks and run down the aisle at x=17'-4" (2" clear of W-B-CS2's face at 17'-6"), through
    # W-B-SA-N's framed stud bay (no cast sleeve needed) to the valve inside W-B-CS's liner.
    # No supply to FX-B-SAUNA-FD: a floor drain has none.
    PipeRun(uid="CBPW46AAAA", tag="PR-B-CW-SAUNA", system=PipeSystem.WATER_COLD,
            path=(pt(ft(17, 4), ft(16)), pt(ft(17, 4), ft(12, 2)),
                  pt(ft(17, 4), ft(12, 2))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(7, 10.6375), ft(7, 10.6375), ft(4, 3.4375)),
            serves=("FX-B-SAUNA-SH",)),
    PipeRun(uid="CBPW47AAAA", tag="PR-B-HW-SAUNA", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(17, 4), ft(15, 6)),
                  pt(ft(17, 4), ft(11, 10)), pt(ft(17, 4), ft(11, 10))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(7, 9.4375), ft(7, 9.4375), ft(7, 9.4375), ft(4, 3.4375)),
            serves=("FX-B-SAUNA-SH",)),
]

# --- The two south-face wall hydrants (2026-08-01) -----------------------------------
#
# Both fed from above, out of the second floor's joist space (FS-S-WEST since 2026-08-21,
# 11 7/8" open-web floor trusses), rather than from below: the main-storey exterior wall's
# stud cavity sits directly over
# W-B-S1 (cast concrete — 8" since 2026-08-21, and W-M-C1/W-B-CS on the centre line, which
# is still 12"), so a riser through
# SL-M-DECK would surface through the top of a bearing wall. One riser leaves the basement
# and splits upstairs — one leg into W-M-S1 to the porch hydrant, one into W-S-S1 to the
# balcony hydrant — always inboard of the wall's 4" continuous exterior insulation so the
# pipe stays warm.
#
# The riser stands in W-M-BDN1, a 2x4 partition (3.5" cavity, ample for 3/4" PEX) whose
# deck crossing (SP-M-CW-HYD) lands in open slab at x=6', not on a wall below.
HYDRANT_BRANCH_BASEMENT = [
    # Two runs, one branch: material changes at the deck. Ceiling leg is exposed lacquered
    # copper like everything else down here; slab-up it's inside wall/joist bays, hidden, so
    # PEX's freeze tolerance matters more than finish.
    PipeRun(uid="X4M2QP7B0K", tag="PR-B-CW-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(16)), pt(ft(6), ft(13))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(7, 10.6375), ft(7, 10.6375)),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    PipeRun(uid="Z5NB8QMK2H", tag="PR-B-CW-HYD-RISER", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(13)), pt(ft(6), ft(13)), pt(ft(6), ft(13)),
                  pt(ft(6), ft(13))),
            diameter=inch(0.75), material="pex",
            # Basement-relative -> project: 8'-1.2" ceiling trunk, 9'-0" deck top (0'-0"),
            # 18'-0" W-M-BDN1's top plate (9'-0", the partition's ceiling height), 18'-3"
            # (9'-3") inside the joist space (11 7/8" joists hang 9'-0 1/8" to 10'-0"). Split
            # at the plate because `mep.wet_wall_occupancy` grades an in-wall segment against
            # the wall's own z-extent; a straight riser would escape it by 3".
            elevations=(ft(7, 10.6375), ft(9, 1.4375), ft(18, 1.4375), ft(18, 4.4375)),
            wall_refs=(None, "W-M-BDN1", None),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
]

# Joist-space distribution, filed on ``main`` (datum 0'-0") so 9'-3" reads as the ceiling
# height it is. The E-W leg runs *along* a joist bay at y=0'-9"; the riser crosses joists at
# x=6' drilled through their webs — 3/4" PEX in an 11 7/8" I-joist web is within every
# manufacturer's hole chart, which is why this branch stays PEX rather than becoming copper.
HYDRANT_BRANCH_MAIN = [
    #
    # ** THE EAST END CAME BACK TO x=12'-0" ON 2026-08-30. ** It ran to 16'-8" because that
    # is where the balcony leg used to tee off, and the balcony leg has now followed its own
    # hydrant west to x=7'-4" (see below). Everything east of the porch tee at 12'-0" fed
    # nothing at all: 4'-8" of dead leg on a cold line, which is stagnant water on a branch
    # that is used a handful of times a summer. Both tees are still ON this polyline —
    # balcony at 7'-4", porch at 12'-0" — so nothing else about the branch changes.
    PipeRun(uid="R9TC5VZ1WQ", tag="PR-M-CW-HYD-DIST", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(13)), pt(ft(6), ft(0, 9)), pt(ft(12), ft(0, 9))),
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
    #
    # ** THE RISER NEVER FOLLOWED ITS HYDRANT, AND STOOD IN THE DECK DOOR FOR SIX DAYS. **
    # FX-S-BALC-HYD moved 16'-8" -> 7'-4" on 2026-08-24, when D-S-DECK-W slid 1'-0" inward
    # and its rough opening (x 12'-2"..17'-2") swallowed the old station — plan/fixtures.py
    # says so in its own comment. The FIXTURE moved; this riser and PR-S-CW-BALC-HYD-CU did
    # not, so 24" of pipe stood inside a 5'-0" deck door and the barrel pierced W-S-S1 in the
    # middle of the same opening. Nothing graded it until `mep.run_through_opening`.
    #
    # x=7'-4" is the hydrant's own station and it is a real bay, not just a number copied
    # across: W-S-S1 resolves king-1-r0 at x=5'-5 1/4" (face 5'-6") and king-2-l0 at
    # x=7'-10 3/4" (face 7'-10") with ONE stud between them, at x=6'-8". That leaves two
    # 13 1/4" bays, and 7'-4" is 7 1/4" off the stud's east face and 6" off the king's — the
    # 16" module bay centre the fixture comment names. It is also 4'-8" clear of D-S-DECK-W's
    # west jamb pack, which starts at x=11'-11".
    PipeRun(uid="V2FJ8LRY6P", tag="PR-M-CW-BALC-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(7, 4), ft(0, 9)), pt(ft(7, 4), ft(0, 3.25)),
                  pt(ft(7, 4), ft(0, 3.25)), pt(ft(7, 4), ft(0, 3.25))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(10), ft(12)),
            wall_refs=(None, None, "W-S-S1"),
            serves=("FX-S-BALC-HYD",)),
    # The barrel: the hydrant's own metal tube + sleeve, modelled as a run so the insulation
    # can be billed and `mep.exterior_hydrant_protection` has something to grade. The one
    # place in the house where a supply pipe is *in* the envelope rather than behind it — 10"
    # of metal from the seat out through sheathing/polyiso/EPS/rainscreen to the escutcheon
    # at y=-5". PEX stops at the seat so the thermal bridge doesn't extend into the room.
    PipeRun(uid="T8WQ3E5AZC", tag="PR-M-CW-PORCH-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12), ft(0, 3.25)), pt(ft(12), inch(-5))),
            diameter=inch(0.75), material="copper",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(ft(2), ft(2)),
            serves=("FX-M-PORCH-HYD",)),
]

# --- kitchen cold stub, for a future cold-storage water connection (2026-08-24) ---------
#
# The owner chose an all-refrigerator with no ice maker and no dispenser, so nothing in the
# cold-storage bay takes water and nothing here `serves` anything. This is provision, not
# plumbing: a capped 1/2" line to the back of the bay so the day a unit with an ice maker or
# a filtered tap arrives, the job is pulling the appliance out and opening a stop, not
# opening a finished kitchen.
#
# **Why it is worth authoring now and not later.** SL-M-DECK is a 12 5/8" cast concrete band
# covering x 18'-36', y 13'-36' (plan/mep_sleeves.py) — the whole cold-storage bay stands on
# it. A line fed from *below* would need a cast-in sleeve set before the pour, and coring a
# structural band afterwards is a different kind of job. This one never goes below the floor:
# it tees off the kitchen cold where it has already surfaced, at the riser head in the sink
# base (SP-M-CW-KITCH, ft(29, 9.6) / ft(34, 1.2)) where PA-M-KITCH-STOP-CW and PA-M-RO-STUB
# already sit, and runs at 2'-6" through the backs of cabinets that are being built anyway —
# west along the north run, then south down the west run. No penetration, no sleeve, no
# concrete, and every inch of it behind a removable cabinet back.
#
# PEX rather than copper for the same reason HYDRANT_BRANCH_MAIN is: it is a cold branch
# threading a built assembly, not a trunk. 1/2" stubbed and reduced at the stop, so the tee
# suits a filtered tap as well as the 1/4" an ice maker wants.
#
# ** RE-ROUTED 2026-08-24, AND THE OLD ROUTE WAS NOT MERELY UNTIDY. ** It ran west at 2'-6"
# along y=34'-1.2" and dropped at x=18'-9", which after the pantry rework lands INSIDE
# D-M-PANTRY's rough opening (x 18'-7 1/2"..23'-9 1/2"). Threading it through the 1 3/4"
# between W-M-C5B's stud band and the door's west king stud is geometrically possible and is
# rejected: nobody builds a 1 3/4" window.
#
# ** THE CORNER IT USED TO CROSS IS A ROOM NOW, so there is no cabinet-back path left. **
# That is the honest cost of the pantry, not a routing failure: the run's whole premise was
# "behind removable cabinet backs the whole way", and between x=18'-0" and 24'-4" the
# cabinets that made that true have become RM-M-PANTRY. So the crossing is made where a
# plumber would actually make it — UP into the framing at each end, ACROSS at 8'-6",
# clear over FURN-M-PANTRY-SHELVES' 7'-0" top and under the 9'-0" plate. Six feet of it is
# exposed in the pantry, above the shelves and out of reach, and every vertical is inside a
# stud cavity parallel to the studs, boring nothing:
#   * the rise at x=24'-5" is in W-M-PAN-E's cavity (studs 24'-2 1/4"..24'-5 3/4");
#   * the drop at x=18'-0" is on W-M-C5/C5B's own axis, mid-cavity (17'-9 1/4"..18'-2 3/4"),
#     and carries on south inside it to y=31' before stepping east to the stub.
# Still no penetration of SL-M-DECK, still no cast-in sleeve, which is what the paragraph
# above is actually protecting.
KITCHEN_STUB_MAIN = [
    PipeRun(uid="N0D5ATAN07", tag="PR-M-CW-COLDSTORE-STUB", system=PipeSystem.WATER_COLD,
            path=(pt(ft(29, 9.6), ft(34, 1.2)),
                  pt(ft(24, 5), ft(34, 1.2)),
                  pt(ft(24, 5), ft(34, 1.2)),
                  pt(ft(18), ft(34, 1.2)),
                  pt(ft(18), ft(34, 1.2)),
                  pt(ft(18), ft(31)),
                  pt(ft(18, 9), ft(31))),
            diameter=inch(0.5), material="pex",
            elevations=(ft(2, 6), ft(2, 6), ft(8, 6), ft(8, 6), ft(2, 6), ft(2, 6),
                        ft(2, 6))),
]

# The balcony hydrant's barrel, filed on ``second`` (datum 10'-0") with the wall it pierces.
# ** MOVED 16'-8" -> 7'-4" ON 2026-08-30 WITH THE RISER IT SITS ON. ** The barrel is the
# escutcheon-to-seat penetration, so its x IS the riser's x and is not independently chosen;
# at 16'-8" it drove 8 1/4" of copper straight through D-S-DECK-W's rough opening, 24" above
# the threshold. PA-S-BALC-HYD-SEAL (plan/mep_supply_devices.py) moved with it.
HYDRANT_BRANCH_SECOND = [
    PipeRun(uid="G7YB4XN2SD", tag="PR-S-CW-BALC-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(7, 4), ft(0, 3.25)), pt(ft(7, 4), inch(-5))),
            diameter=inch(0.75), material="copper",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(ft(2), ft(2)),
            serves=("FX-S-BALC-HYD",)),
]


# --- the attic guest studio, 2026-08-29 -------------------------------------------------
# Both runs TEE OFF THE EXISTING SUITE RISERS at their heads and carry on up W-S-DC2 into
# W-A-STU-W — the same 5 1/2" staggered cavity the drain and the vent use, and the reason the
# bath is on the x=9'-7 1/2" line at all. 3/4" copper, matching PR-B-CW-SUITE/PR-B-HW-SUITE
# rather than stepping down: the run is short and the pair already carries a three-fixture
# bath, so there is nothing to gain by narrowing and a pressure-drop argument to lose.
#
# ** `serves` IS LOAD-BEARING ON THESE TWO. ** Unlike the drains — which `mep.pipe_sizing`
# grades on the geometric upstream subtree — supply runs grade on the AUTHORED tuple. A fixture
# missing from it is an unfed fixture as far as the checks are concerned.
#
# The hot run copies PR-B-HW-SUITE's insulation string VERBATIM so `mep.hot_water_insulation`
# passes the way every other hot run in the house passes; do not paraphrase it.
#
# ** FILED ON ``main`` (datum 0'-0"), SO THESE ELEVATIONS ARE PROJECT ELEVATIONS. ** Same
# convention, and the same reason, as SECOND_DRAINS in plan/mep_drainage.py: the run spans
# three storeys and the numbers are only readable if they read off the drawing set. Authored
# against the attic datum ft(20) until 2026-08-29, which put them 20'-0" above the roof.
#
# ** THE TEE IS IN THE TRUSS FLOOR, NOT AT THE RISER HEAD, AND THAT IS NOT A REFINEMENT. **
# PR-B-CW-SUITE/-HW-SUITE surface at (13'-7.2"/14'-2.4", 16'-10.8") at 12'-6" — 2'-6" above the
# second floor, inside RM-S-SUITEBATH. Teeing there and running west to the W-S-DC2 axis meant
# 4'-5" of exposed copper across that bathroom at chest height. So the branch tees LOWER, where
# the suite risers are already passing through FS-S-WEST, and makes the whole east-west jog in
# the truss floor — through the open webs, boring nothing. That is the same crossing
# PR-A-STUBATH-DRAIN makes, in the same floor, for the same reason.
#
# Cold rides at 9'-4" and hot at 9'-7" so the two jogs cannot foul each other where they
# converge on the wet wall; both sit inside the trusses (8'-11 3/8" to 9'-11 1/4"). From
# (9'-7 1/2", 20'-6"/21'-0") each rises straight up W-S-DC2 and W-A-STU-W to its stop at 22'-6".
#
# ** BOTH RISERS MOVED NORTH ON 2026-08-30, 19'-0"/19'-6" -> 20'-6"/21'-0", TO GET OUT FROM
# BEHIND THE TOILET. ** The water closet went back onto this wall (plan/fixtures.py) and its
# tank occupies y 18'-6"..20'-2" against it — which would have left both angle stops walled in
# behind a fixture while `PA-A-STUBATH-STOP-*.accessible` still claimed True. Nothing checks
# that: `mep.stop_accessibility` grades the FLAG, not the geometry. The 6" of y between the
# two risers is unchanged, and so is the 3" of z (cold 9'-4", hot 9'-7") that keeps their
# truss-floor jogs apart. North of the WC they are also nearer the lavatory they feed.
STUDIO_SUPPLY = [
    PipeRun(uid="WJZGK0YFHY", tag="PR-A-CW-STUBATH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(13, 7.2), ft(16, 10.8)), pt(ft(9, 7.5), ft(20, 6)),
                  pt(ft(9, 7.5), ft(20, 6))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(9, 4), ft(9, 4), ft(22, 6)),
            serves=("FX-A-STUBATH-WC", "FX-A-STUBATH-LAV", "FX-A-STUBATH-SH",
                    "FX-A-STUDIO-BAR-SINK")),
    PipeRun(uid="TCWF4YDZTW", tag="PR-A-HW-STUBATH", system=PipeSystem.WATER_HOT,
            path=(pt(ft(14, 2.4), ft(16, 10.8)), pt(ft(9, 7.5), ft(21)),
                  pt(ft(9, 7.5), ft(21))),
            diameter=inch(0.75), material="copper",
            insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(9, 7), ft(9, 7), ft(22, 6)),
            serves=("FX-A-STUBATH-LAV", "FX-A-STUBATH-SH", "FX-A-STUDIO-BAR-SINK")),
]

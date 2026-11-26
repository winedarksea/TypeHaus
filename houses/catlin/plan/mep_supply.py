# haus: editable
# Catlin MEP — water supply — the house entry, hot/cold distribution, hydrant branches.
#
# plan/mep.py re-exports the storey lists below (AGENTS.md §1.1), so the manifest is
# unchanged.
#
# The in-line valves, hammer arrestors and stops on these runs are authored separately in
# plan/mep_supply_devices.py.
#
# ** ALL SUPPLY IS PEX-A SINCE 2026-09-26 (owner). ** The lacquered-PEX runs were left over
# from the visible-PEX rule `preferences.toml` retired on 2026-08-21. PEX is built to
# PEX tube size, so every OD, clearance and bore quoted below holds; its off-angle turns
# are bends graded against the maker's minimum radius, not missing fittings.

from typehaus import (
    PipeRun,
    PipeSystem,
    RoughOpening,
    ft,
    from_node,
    inch,
    pt,
)
from typehaus.model import m

# --- Water supply: the service lateral, and the hydrant branch beside it -------------
#
# ** THE HYDRANT IS A BRANCH OF THE TRUNK (owner, 2026-10-29). ** PR-G-SERVICE-CW (1 1/4") is
# the lateral, street entry (11'-4", 48'-6") to the house, and feeds PR-B-CW-TRUNK only.
# PR-G-HYDRANT-CW (3/4") tees off the trunk riser inside, 12" above PA-B-MAIN-SHUTOFF,
# carries PA-G-HYD-BFP and goes back out beside the lateral to the garage yard hydrant
# (11', 48'-1 5/16"). The house trunk is open; only the hydrant is behind a dual check.
# Both are buried 6' below grade, 4" apart in one trench, each in its own wall and footing
# sleeve. Filed on ``main`` (datum 0'-0") so elevations read straight off the drawing set.
#
# What follows is the hydrant line's history; the lateral took its x=11'-0" lane 4" east.
#
# ** ONE STRAIGHT LEG, NO BURIED TURN (2026-09-16). ** It used to enter the house at x=5'-0"
# and jog east at y=38'-0" to a hydrant at y=62'-0", 30'-6" of trench and two elbows. The
# hydrant moved south beside ST-G-SERVICE and the entry moved east to x=11'-0", under
# ST-B2M's upper landing (SP-B-N3-HYD): now 12'-7 5/16" of trench after the 2026-10-13 move.
# The water goes west to the old
# x=5'-0" riser INSIDE the heated basement, at the ceiling, as PR-B-CW-TRUNK.
#
# The bury is 6' below *grade* (-2'-10"), so the run sits at -8'-10". It crosses the
# garage's south foundation at x=11'-0", 22" under FT-GF-S-DR's -7'-0" bearing plane, inside
# SP-GF-S-HYD (plan/mep_sleeves.py) — perpendicular, which is why the leg stays orthogonal.
# The north-entry piers all bear below this invert. `mep.hydrant_freeze_depth` holds every
# buried vertex to 72"; the terminal rise is the hydrant's own self-draining barrel.
WATER_SUPPLY = [
    # Basin tap from the existing south wet-wall cold riser, below the blocking.
    PipeRun(uid="KV1KTD2P01", tag="PR-M-CW-BATH1-LAV", system=PipeSystem.WATER_COLD,
            path=(pt(inch(60), inch(268)), pt(inch(60), inch(271.385))),
            diameter=inch(0.5), material="pex",
            elevations=(inch(24.0), inch(25.0255906),),
            serves=("FX-M-BATH1-LAV",)),
    PipeRun(uid="CMP920AAAA", tag="PR-G-HYDRANT-CW", system=PipeSystem.WATER_COLD,
            # ** THIS RUN DID NOT MOVE FOR THE 2026-09-10 NORTH ENTRY PIERS; THEY MOVED
            # AROUND IT. ** Every rerouting tried here traded one clash for another -- the
            # 45 degree influence line under the garage-side pads, or an elbow buried inside a
            # footing. What actually resolves it is depth: all five north-entry footings now
            # bear BELOW this invert, so `mep.footing_clearance` sees the pipe above their
            # bearing planes and no influence at all. Keep it that way if a pier ever moves.
            #
            # Tee on PR-B-CW-TRUNK's riser at 4'-0" over the basement slab (-5'-1 7/16"), 4"
            # west, down through PA-G-HYD-BFP at 3'-0", out through SP-B-N3-HYD and north to
            # the hydrant. The indoor legs are warm, so `mep.hydrant_freeze_depth` grades only
            # the buried ones.
            path=(pt(ft(11, 4), inch(420)), pt(ft(11), inch(420)), pt(ft(11), inch(420)),
                  pt(ft(11), ft(48, 1.3125)), pt(ft(11), ft(48, 1.3125))),
            diameter=inch(0.75), material="pex",
            elevations=(inch(-61.4375), inch(-61.4375), ft(-8, -10), ft(-8, -10),
                        ft(-2, -5.2)),
            serves=("FX-G-HYDRANT",)),
    # The service lateral: street entry to the house, the trunk's whole load. The street main,
    # curb stop and meter are SPRWS's and are not runs here (notes/water_service.md). It
    # passes 4" east of the hydrant's buried valve, through its weep stone. Drawn street to
    # house, so PR-B-CW-TRUNK tees onto its END (two runs sharing an origin are siblings).
    PipeRun(uid="XGCMPK0Z1C", tag="PR-G-SERVICE-CW", system=PipeSystem.WATER_COLD,
            path=(pt(ft(11, 4), ft(48, 6)), pt(ft(11, 4), inch(420))),
            diameter=inch(1.25), material="pex",
            elevations=(ft(-8, -10), ft(-8, -10)),
            serves=("FX-G-HYDRANT", "FX-M-BATH1-WC", "FX-M-BATH1-LAV", "FX-M-BATH2-WC",
                    "FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-FILLER",
                    "FX-M-BATH2-SINK",
                    "FX-M-LAUNDRY", "FX-M-KITCH-SINK",
                    "FX-B-BATH-WC", "FX-B-BATH-LAV", "FX-B-BATH-SH",
                    "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2",
                    "FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH", "FX-M-PORCH-HYD", "FX-S-BALCONY-HYD")),
]

# --- Domestic hot/cold distribution (2026-07-29 plumbing pass) -----------------------
#
# PEX home-run-lite: 1" cold trunk tees off the water service at (5', 35'-6"), 1" hot trunk
# leaves EQ-B-WH; both run the ceiling band south of the y=18' wall, cross the framed
# centre walls (a bored stud bay, or over the plate) and rise to each wet-wall group.
# `serves` on a trunk is the union of everything downstream, so `mep.pipe_sizing` sums the
# real WSFU. Filed on ``basement`` (datum -9') so ceiling runs read as 8'-ish heights.
#
# Cold trunk went 1" -> 1 1/4" on 2026-07-30: the stair-foot bath and sauna shower added 4
# WSFU, taking it from 30 to 34 against the 32 a 1" branch carries (Table 610.4, 46-60 psi /
# <100'). Hot trunk stays 1" at 21.5 WSFU.
#
# ** THE TWO-BAND CONVENTION, AND IT IS LOAD-BEARING FOR EVERY ELEVATION BELOW
# (2026-09-19). ** The basement ceiling runs ride TWO bands, not one, and which band a leg
# is on is a fact about the pipe rather than about the room it crosses:
#
#   COLD   ft(8, 4.6375) basement-relative  =  -0'-8.8" project
#   HOT    ft(8, 1.4375) basement-relative  =  -1'-0.0" project
#
# ** WHY TWO. ** They used to be 1.2" apart — cold at 7'-10 5/8", hot at 7'-9 7/16" — and a
# bare 3/4" PEX cold is 0.4375" from centre to surface while a hot inside a 1" fiberglass
# sleeve with an ASJ jacket is 1.4375". The pair therefore needs 1.875" between centres to
# be two pipes at all, and it had 1.2". ** EVERY cold-over-hot crossing in this house
# overlapped by 0.675" by construction ** — which is the 0.68" `mep.run_interference`
# reported verbatim, on crossing after crossing, as a defect in a lane. It was never a lane
# problem. It was one number, written once, and wrong. At 3.2" apart there is 1.325" in hand.
#
# ** WHAT THE BANDS PHYSICALLY ARE, WHICH IS NOT WHAT THEY WERE. ** FS-M-*'s joists are
# 11 7/8" I-joists whose bottom flange sits at -1'-0.1" project, so the old pair hung in the
# room BELOW the floor and the new pair does not:
#
#   * the COLD band is INSIDE the joists. `mep.run_member_crossing` reads every crossing at
#     crown +6.737", invert +1.013" in the 9.12" web window, clear of both 1.38" flanges.
#     Each of those is a DRILLED WEB HOLE, and the check says out loud what it cannot
#     settle: the hole's diameter and its allowable zone along the span come off the
#     fabricator's chart, which this engine does not hold. 1 1/4" PEX through an 11 7/8"
#     I-joist web is inside every published chart; it is still the builder's to confirm.
#   * the HOT band is BELOW the joists, its 2 7/8" jacket tucked 0.1" under the bottom
#     flange. An insulated line is not drilled through a web — the sleeve would have to be
#     interrupted at every joist — so it stays hung, and the 4" it rose is the whole of
#     what the floor cavity had to give it.
#
# ** THE CONVENTION NOW RUNS THROUGH x=18'-0" (2026-11-01, decision #112). ** East of the
# centre line and north of y=13'-0" the ceiling used to be SL-M-DECK, a cast deck whose soffit
# put the cold band 4.6" inside the slab, so PR-B-CW-TRUNK and PR-B-HW-KITCH stepped back
# down at x=17'-6" and crossed W-B-CS2 through cast sleeves. It is FS-M-NE's 11 7/8"
# open-web trusses now, chord window 99 1/16"..107 15/16" basement-relative, and the cold band
# (100 5/8") sits inside it. Both runs cross the x=18' line OVER the framed plate, through the
# 2x6 box the resolver frames in the bearing-line blocking (a bored stud would be the other
# way, and R602.6 caps a bearing stud's bore at 2.20"), then run east in truss bays: cold in
# the 15'-16' bay (y=186"), hot in the 16'-17' bay (y=197", the lane it already had west of
# the wall). They turn north at x=357.6" (cold) and 363.6" (hot), inside the web opening
# 353.5".."366.5" every truss shares, and rise in the 35'-36' bay at y=424.2". The hot lane
# is north of the cold one and its riser east of it, so the cold's north-south leg crosses the
# hot's east-west one: the hot rides 2 1/2" higher (103.2", invert 102 1/4", over the cold's
# 101 5/16" crown) from the hall bay on.
#
# ** THE WINDOW IS NARROW AT THE HOT END AND WIDE AT THE COLD END, MEASURED. ** Sweeping
# both bands against the full registry with suppression lifted:
#
#   cold +0"  hot +0"     188 interference        (as authored before today)
#   cold +6"  hot +4"      147, nothing else moved
#   cold +6"  hot +4.25"   146, and +11 mep.run_member_crossing
#
# and then 147 -> 146 once the two runs under the cast deck (SL-M-DECK, since replaced by
# FS-M-NE) were stepped back down, the honest figure: the 147 row was measured with a 1 1/4"
# PEX trunk drawn inside a cast slab.
#
# One eighth of an inch of hot is all that is left: at +4.25" the jacket clips the joists'
# bottom flange and eleven crossings stop being clear. Cold is broad — +3" through +10" all
# measure the same — with ONE exception, PR-B-CW-TRUNK's bearing-line crossing, which is
# the next note down. ** If either band ever moves again, re-derive it; do not interpolate
# these three rows. **
SUPPLY = [
    # The service enters at (11'-4", 35'-6") — SP-B-N2-SVC, under ST-B2M's upper landing —
    # at -8'-10" absolute and comes 6" inboard to the riser, where PA-B-MAIN-SHUTOFF sits.
    # ** THE RISER IS AT y=35'-0" SINCE 2026-10-31 (owner), NOT 35'-6". ** On the old line it
    # stood 2" inside W-B-N2's concrete (face y=35'-4"), as did the hydrant tee and
    # PA-G-HYD-BFP. At 35'-0" it is in the bay between the landing joists at 33'-9 5/8" and
    # 35'-1 5/8", so it cuts none (the 35'-3 1/4" edge joist on W-B-N2 stays whole) and
    # passes only the deck sheet, rising 3 1/4" off the wall to clear CD-B-GARAGE at the top.
    # At the ceiling it runs west to x=5'-0" over RM-B-ESS (bored through W-B-STR and the
    # closet partition; firestop the ESS penetrations), then south down the RM-B-FURNACE
    # ceiling band to y=16', crossing W-B-CW with a bored hole.
    #
    # ** IT DUCKS UNDER THE x=9'-10.7" BEARING LINE AND STEPS UP AT x=9'-6" (2026-09-19). **
    # This is the one exception to the cold band above, and it is not a lane that could be
    # searched around. FS-M-MECH and FS-M-STAIR both close their bays on the SAME bearing
    # line at x=9'-10.7", because a wall stands on it the whole way: the blocking there runs
    # the full -11.87"..0 joist depth, and the cold band is inside that depth by 3.07". The
    # westward leg crosses that line at y=35'-0", and `mep.run_through_blocking` is an ERROR
    # about exactly it.
    #
    # Three things were measured before the step was authored. Moving the leg in y to y=35'-3"
    # — the 7.8" gap between bearing-block-1-013 and -016 — only moves the crossing into
    # FS-M-STAIR's bearing-block-0-006, because the line is continuous. Dropping the whole
    # cold band to +2" clears it and gives back 14 of the 41 pairs. So the run does what a
    # plumber does: it stays in the OLD band, 7'-10 5/8", from the riser west past the
    # bearing line, and steps up to 8'-4 5/8" at x=9'-6" — the closest clear station, since
    # x=9'-9" is still inside the blocking. Two elbows, four inches west of the wall, and
    # the other 36 feet of the trunk is on the convention.
    #
    # ** THE STEP MAY NOT LAND ON A JOIST (2026-09-23). ** mep.run_in_joist_flange: at
    # y=35'-0" the step took joist-0-010-1's bottom flange. The west leg rides y=34'-10".
    # East of the x=17'-5" jog the trunk leaves joist-0-012's plane (y=16'-0") for the truss
    # bay at y=15'-6".
    #
    # ** IT DIPS UNDER FO-M-ERV-OA's TRIMMER PACKS (2026-09-23). ** Both 2-ply 1.75x11.875
    # LVL packs run full bay (x 6"..10'-0"), so any x=4'-9" crossing bores four plies. The
    # maker's chart does not allow it: Weyerhaeuser TJ-9015 "Allowable Holes for Trus Joist
    # Products" (Sept 2018), "Other Trus Joist Headers and Beams" — Microllam LVL, 7 1/4"-20"
    # deep: 2" max round hole, middle 1/3 span AND middle 1/3 depth, UNIFORM LOADS ONLY.
    # These trimmers carry header-FO-M-ERV-OA-1's reaction at x=3'-11" (a point load), and
    # the band sits 3.07" off the bottom face (zone starts 3.96"). So the leg drops to
    # 8'-0 1/4" at y=34'-10", runs under both packs (top 5/8" below the joists) in
    # RM-B-FURNACE's open service ceiling, and climbs back at y=33'-0", mid-bay south of the
    # packs. Four PEX 90s; nothing bored.
    # Its riser is at x=11'-4" since 2026-10-29 (the lateral's new lane), y=35'-0" since
    # 2026-10-31; PR-G-HYDRANT-CW tees off it at 4'-0", under the landing.
    PipeRun(uid="CBPW30AAAA", tag="PR-B-CW-TRUNK", system=PipeSystem.WATER_COLD,
            path=(pt(ft(11, 4), inch(420)), pt(ft(11, 4), inch(420)), pt(ft(11, 4), inch(420)),
                  pt(ft(11, 4), ft(34, 10)),
                  pt(ft(9, 6), ft(34, 10)), pt(ft(9, 6), ft(34, 10)),
                  pt(ft(4, 9), ft(34, 10)), pt(ft(4, 9), ft(34, 10)),
                  pt(ft(4, 9), inch(386.5)), pt(ft(4, 9), inch(386.5)),
                  # Joist 012's web is on y=16'-0", so the trunk rides the 170..186 bay's
                  # y=14'-8" lane (4" south of PR-B-SH2-DRAIN's x=8'-2" drop) and steps to the
                  # old y=15'-0" line at x=200" for the bearing-line box (2026-11-12).
                  pt(ft(4, 9), inch(176)), pt(inch(200), inch(176)), pt(inch(200), inch(180)),
                  pt(ft(29, 9.6), inch(180)),
                  pt(ft(29, 9.6), inch(424.2)), pt(ft(29, 9.6), inch(424.2)),
                  pt(ft(29, 9.6), inch(421.5)), pt(ft(29, 9.6), inch(421.5))),
            diameter=inch(1.25), material="pex",
            elevations=(inch(2), ft(4), ft(7, 10.6375), ft(7, 10.6375), ft(7, 10.6375),
                        ft(8, 4.6375), ft(8, 4.6375), inch(93.44), inch(93.44),
                        ft(8, 4.6375), ft(8, 4.6375), ft(8, 4.6375),
                        ft(8, 4.6375), ft(8, 4.6375),
                        ft(8, 4.6375), inch(120), inch(120), ft(10, 9.4375)),
            serves=("FX-G-HYDRANT", "FX-M-BATH1-WC", "FX-M-BATH1-LAV", "FX-M-BATH2-WC",
                    "FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-FILLER",
                    "FX-M-BATH2-SINK",
                    "FX-M-LAUNDRY", "FX-M-KITCH-SINK",
                    "FX-B-BATH-WC", "FX-B-BATH-LAV", "FX-B-BATH-SH",
                    "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2",
                    "FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH",
                    # The two south-face wall hydrants, 2.5 WSFU cold each — 39 total on a
                    # 1 1/4" trunk that carries 64 in Table 610.4's 46-60 psi column, so the
                    # tee costs nothing in size.
                    "FX-M-PORCH-HYD", "FX-S-BALCONY-HYD")),
    # ** 7.2 FT, TAP TO HEADER, IN THE WORKSHOP'S NE CORNER (2026-11-09; was 19.3). ** Off the
    # HydroBoost riser's side tap (E 42 3/8"), a 3" stub on the port axis under DU-B-WH-OUT,
    # a 90 to x=12'-9 3/4" (8" clear of the ducts), up to 95 1/2", north and east, and down
    # into EQ-B-HW-HEADER's +y-facing inlet. UPC 604.13: copper at the tap, never PEX.
    # PR-B-HW-SBATH (PEX-A) and PR-B-HW-SUITE stay 3/4" and tee off the 95 1/2" legs ahead of the
    # header. The header's eight 1/2" branches: plan/mep_supply_header.py.
    PipeRun(uid="CBPW31AAAA", tag="PR-B-HW-TRUNK", system=PipeSystem.WATER_HOT,
            path=(pt(inch(145.023), inch(188.405)), pt(inch(146.523), inch(185.807)),
                  pt(inch(153.786), inch(190)), pt(inch(153.786), inch(190)),
                  pt(inch(153.786), inch(196.16)), pt(inch(160), inch(196.16)),
                  pt(inch(160), inch(196.16)), pt(inch(160), inch(198.66))),
            diameter=inch(1), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(inch(42.375), inch(42.375), inch(42.375), inch(95.5), inch(95.5), inch(95.5),
                  inch(88), inch(88)),
            serves=("FX-M-BATH1-LAV", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-FILLER", "FX-M-BATH2-SINK", "FX-M-LAUNDRY",
                    "FX-M-LAUNDRY-SINK",
                    "FX-M-KITCH-SINK",
                    "FX-B-BATH-LAV", "FX-B-BATH-SH",
                    "FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                    "FX-S-VANITY-LAV2", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH",
                    # APPL-M-DW must be declared here: without it, its 1.5 WSFU is missing
                    # from the trunk's load and `mep.water_hammer_arrestor` has no supply to
                    # ask about, so the quick-closing valve on it goes ungraded rather than
                    # failing.
                    "APPL-M-DW")),
    # Cold feed to the water heater itself (equipment, not a fixture — no fixture units).
    PipeRun(uid="CBPW32AAAA", tag="PR-B-CW-WH", system=PipeSystem.WATER_COLD,
            # Tees off PR-B-CW-TRUNK's y=14'-8" leg over the tank, runs 6 3/8" north in the
            # cold band (2026-11-12; was 9 5/8" south off joist 012's line) and drops on the
            # inlet's axis, 3" off the riser-foot tap (K 5 1/16"),
            # 9" clear of the ducts (2026-11-09; 9.0 ft, was 30.8). The full drop is Rheem's
            # 6" heat trap many times over.
            path=(pt(inch(138.152), inch(176)), pt(inch(138.152), inch(182.383)),
                  pt(inch(138.152), inch(182.383)), pt(inch(138.048), inch(185.381))),
            diameter=inch(1), material="copper",
            # The cold band rides INSIDE FS-M-WEST's I-joist
            # web, whose window is -10 1/2" to -1 3/8"; two inches down puts a 1" PEX's
            # invert 7/8" into the bottom flange and `mep.run_member_crossing` says so. Two
            # inches up is the same 2" of separation in the half of the window that is
            # empty.
            elevations=(inch(100.638), inch(100.638), inch(5.0625), inch(5.0625))),
    # Main-storey groups.
    #
    # BATH1 cold stays in the shared south wet wall; the basin takes a separate
    # tap at 24 in. above the main datum. Keep the insulated hot on its own
    # basement ceiling route so neither line crosses the entry doorway.
    PipeRun(uid="CBPW33AAAA", tag="PR-B-CW-BATH1", system=PipeSystem.WATER_COLD,
            # Riser at (5'-0", 22'-4") — the east bay of the pair, centred with 2.81" of
            # clear to the 2x4 each side, on W-M-HS1's axis so a 7/8" pipe sits mid-cavity.
            # Since 2026-11-12 it tees on the trunk's x=4'-9" leg level with the riser and runs
            # 3" east to it, in FS-M-MECH's 261..277 bay: the old y=16'-0" tee stood in joist
            # 012's web, and the diagonal's bores (x=6'-10", 5'-2") went with it. The hot
            # (x=4'-2 1/2") still arrives from the west under the joists, so the two never share
            # a lane.
            path=(pt(ft(4, 9), ft(22, 4)), pt(ft(5), ft(22, 4)), pt(ft(5), ft(22, 4)),
                  pt(ft(5), ft(22, 4)), pt(ft(5), ft(22, 4)), pt(ft(5), ft(22, 4))),
            diameter=inch(0.75), material="pex",
            # The 12.7" (main) vertex is PR-M-BATH1-WC-CW's tee, at the carrier inlet's height.
            elevations=(ft(8, 4.6375), ft(8, 4.6375), ft(9, 1.4375), inch(122.1375),
                        inch(133.4375), ft(12, 7.4375)),
            wall_refs=(None, None, "W-M-HS1", "W-M-HS1", "W-M-HS1"),
            serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV")),
    # Basin hot rises in the shared wet wall; the insulated ceiling run stays below it.
    PipeRun(uid="CBPW34AAAA", tag="PR-B-HW-BATH1", system=PipeSystem.WATER_HOT,
            # Header out-7, west to x=7'-9 1/2", north through W-B-CW3 at 83 1/2" and west
            # under PR-B-MAIN-DRAIN to the riser at x=4'-2 1/2" (2026-11-09).
            path=(pt(inch(160), inch(209.288)), pt(inch(160), inch(209.288)), pt(inch(151), inch(209.288)),
                  pt(inch(151), inch(209.288)), pt(inch(105.5), inch(209.288)),
                  pt(inch(105.5), inch(209.288)), pt(inch(93.5), inch(209.288)),
                  pt(inch(93.5), inch(266.25)), pt(inch(50.5), inch(266.25)),
                  pt(inch(50.5), inch(266.25)), pt(inch(50.5), inch(271.375))),
            diameter=inch(0.5), material="pex",
            elevations=(inch(86.149), inch(83.5), inch(83.5), inch(95.4375), inch(95.4375), inch(83.5),
                  inch(83.5), inch(83.5), inch(83.5), inch(134.438), inch(134.438)),
            serves=("FX-M-BATH1-LAV",)),
    # ** THE COLD RISER IS IN W-M-HS1 SINCE 2026-09-09, NOT STANDING IN THE ROOM. ** It came
    # up at (2'-3", 17'-2.4") and stopped at 3'-0" — three feet of bare PEX in the middle
    # of a bathroom floor, 2'-2" from the nearest thing it feeds, which is what
    # `mep.run_in_finished_volume` reported at the room's full 107 1/2". It now does what
    # PR-B-CW-BATH1 does twenty lines up: runs west under the deck to W-M-HS1 — BATH2's own
    # north wall, INT_2X6_STAGGERED_PLUMBING, 5 1/2" of continuous cavity — and splits at the
    # deck top so the upper leg names the wall it is inside.
    #
    # The bay is x=1'-0", between the studs at 7.385" and 16": 3 1/8" of clear each side of a
    # 7/8" tube. It is the WEST end of the wall deliberately — PR-B-WC1-DRAIN's 3" carrier
    # drop occupies x=2'-2 3/8" in this same cavity (the bay the old x=2'-3" lane would have
    # risen into), and FX-M-BATH2-SINK is the fixture nearest this end of the wall.
    PipeRun(uid="CBPW35AAAA", tag="PR-B-CW-BATH2", system=PipeSystem.WATER_COLD,
            # ESR-1153 Table A: x=1'-1" puts the 1.12" hole 6.4" off the x=6" face (6" wanted).
            # Tees on the trunk's x=4'-9" leg in the 192..208 bay (y=16'-8"), not in joist 012.
            path=(pt(ft(4, 9), ft(16, 8)), pt(ft(1, 1), ft(16, 8)),
                  pt(ft(1, 1), ft(22, 4)), pt(ft(1, 1), ft(22, 4)),
                  pt(ft(1, 1), ft(22, 4))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(8, 4.6375), ft(8, 4.6375), ft(8, 4.6375),
                        ft(9, 1.4375), ft(12, 1.4375)),
            wall_refs=(None, None, None, "W-M-HS1"),
            serves=("FX-M-BATH2-WC", "FX-M-BATH2-SINK")),
    PipeRun(uid="CBPW36AAAA", tag="PR-B-HW-BATH2", system=PipeSystem.WATER_HOT,
            # Header out-5 (plan/mep_supply_header.py), up at x=7'-6" into the web at 103.2"
            # (it rode 97 7/16", in the ceiling board and bottom flange; 2026-11-12), bored
            # through joist 012 into the 186..192 bay (y=189"), west, and back through 012 at
            # x=1'-4" (ESR-1153 field row: 9.6" off the x=6" face; x=9" is 2.6") to the riser.
            # The sister block at x=6'-2 9/16" closes the 192..208 bay, so it cannot stay there.
            path=(pt(inch(160), inch(206.288)), pt(inch(160), inch(206.288)), pt(inch(151), inch(206.288)),
                  pt(inch(151), inch(206.288)), pt(inch(105.5), inch(206.288)),
                  pt(inch(105.5), inch(206.288)), pt(inch(90), inch(206.288)),
                  pt(inch(90), inch(206.288)), pt(inch(90), inch(189)), pt(inch(16), inch(189)),
                  pt(inch(16), inch(201.6)), pt(inch(9), inch(201.6)), pt(inch(9), inch(201.6))),
                        diameter=inch(0.5), material="pex",
            elevations=(inch(86.149), inch(83.5), inch(83.5), inch(95.4375), inch(95.4375), inch(83.5),
                  inch(83.5), inch(103.2), inch(103.2), inch(103.2), inch(103.2), inch(103.2),
                  inch(145.438)),
                        serves=("FX-M-BATH2-SINK",)),
    # The laundry pair riser splits at the deck top (ft(9) basement-relative = 0'-0"
    # project), like the BATH1 pair above: sleeved concrete crossing below, stud cavity
    # above, each leg naming its own host so `mep.wet_wall_occupancy` doesn't read a single
    # riser as escaping the wall it's actually inside.
    #
    # Both runs claim `serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")`: they end at the basin
    # (west of the tower since 2026-11-07), and the tower's own branches
    # (PR-M-WASH-CW/-HW, below) tee off their terminal corners:
    #
    #   riser top 40"/42"  ->  south inside W-M-BA2E  ->  east inside W-M-CLN  ->  drop to 20"
    #
    # 20" is the stop height inside the tub's own cabinet (FX-LAUNDRY-SINK-24 is a 34" rim
    # in a cased base, 43" over the faucet), NOT the 35"-37 1/2" the washer box stands at — a
    # stub above the rim would come out of the wall in front of the basin. Cold lands 4" west of
    # the bowl centre, hot 4" east: hot on the LEFT of someone facing the faucet, who is
    # standing north of a sink whose back is on the south wall.
    #
    # FOUR THINGS KEEP THE PAIR APART AND OFF THE CORNER, AND EVERY ONE IS LOAD-BEARING:
    #   * the cold tops out at 40" at its own riser head and travels the whole way at 40",
    #     2" under the hot's 42". Both share the y=18'-1" lane, so a shared elevation would
    #     be one pipe inside the other; stacked is how the pair is actually run in a cavity.
    #     (32" until 2026-11-07.)
    #   * the hot rides 42", over the cold riser's 40" head, on W-M-BA2E's axis (see
    #     PR-B-HW-WASH).
    #   * the cold stops 4 1/2" short of the hot (x=9'-1 1/2" against 9'-6", the tub's
    #     port stations, hot on the LEFT of someone facing the faucet). So the hot's drop at
    #     9'-6" comes down past 40" east of where the cold's leg ends, and misses it.
    #   * THE CORNER SEGMENT NAMES NO WALL, DELIBERATELY. W-M-BA2E ends at y=18'-0" and
    #     W-M-CLN starts at x=8'-5 3/8": the two only TOUCH, so no point is inside both and a
    #     leg claiming either one leaves its structure footprint — `mep.wet_wall_occupancy` is
    #     an ERROR about exactly this. `None` is the honest answer, and it is the same `None`
    #     the sleeved basement crossing already carries: the 4 1/2" from x=8'-2" to
    #     x=8'-6 1/2" is the corner post, and it is bored. (Both numbers are +2" on where they
    #     sat before 2026-09-09; for a few hours in between, a jogged W-M-BA2E2 put a SECOND
    #     post in this bore's path, and taking the jog out took that back out with it.)
    # The wall this all rides in is why W-M-CLN was retyped (storeys/main.py). Through the
    # 2x4 partition that was there, this leg bores every stud between x=8'-0" and the sink
    # and `mep.wet_wall_occupancy` grades it `long_horizontal`; through the staggered pair it
    # threads between two offset stud rows and bores nothing but that one corner post.
    PipeRun(uid="CBPW37AAAA", tag="PR-B-CW-WASH", system=PipeSystem.WATER_COLD,
            # ** 2" EAST OF THE WALL'S AXIS, NOT ON IT (P3, 2026-09-19). ** It kept clear of the
            # washer standpipe and its riser (retired 2026-11-07, the washer drains to the tub)
            # and still clears the hot riser on the axis: the wall is 6 3/4" (2x6), so a
            # 3/4" PEX 2" off the axis is 3/10" clear of the stud face.
            # The riser tops out at the run's own 40" and turns south inside the wall.
            path=(pt(ft(8, 4), inch(176)), pt(ft(8, 4), m(6.22941)), pt(ft(8, 4), m(6.22941)), pt(ft(8, 4), m(6.22941)), pt(ft(8, 4), ft(18, 1)), pt(ft(8, 6.5), ft(18, 1)), pt(inch(109.5), ft(18, 1)), pt(inch(109.5), ft(18, 1)),),
            diameter=inch(0.75), material="pex",
            elevations=(ft(8, 4.6375), ft(8, 4.6375), ft(9, 1.4375),
                        ft(12, 5.4375), ft(12, 5.4375), ft(12, 5.4375), ft(12, 5.4375),
                        ft(10, 9.4375)),
            wall_refs=(None, None, "W-M-BA2E", "W-M-BA2E", None,
                       "W-M-CLN", "W-M-CLN"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeRun(uid="CBPW38AAAA", tag="PR-B-HW-WASH", system=PipeSystem.WATER_HOT,
            # ** ON W-M-BA2E's AXIS (2026-09-23). ** At x=8'-0" the jacket stood 0.69" proud of
            # the stud plane. It rides 42" (12'-7 7/16" basement-rel), 2" over the cold, and the
            # riser is at y=20'-9 1/4", the bay south of joist-0-016 — at 21'-2.4" the jacket
            # took its flanges.
            # ** UP INSIDE W-M-CLN AT x=9'-3 3/4" SINCE 2026-11-09, ** straight over the header's
            # lane (out-4), 1 1/2" east of the cold riser; W-M-BA2E's riser is retired. Sink
            # terminal at x=9'-6", well clear of PR-M-S-SUITE-DRAIN's stack at x=12'-6".
            path=(pt(inch(160), inch(204.788)), pt(inch(160), inch(204.788)), pt(inch(151), inch(204.788)),
                  pt(inch(151), inch(204.788)), pt(inch(111.75), inch(204.788)),
                  pt(inch(111.75), inch(204.788)), pt(inch(111.75), inch(217)),
                  pt(inch(111.75), inch(217)), pt(inch(111.75), inch(217)),
                  pt(inch(114), inch(217)), pt(inch(114), inch(217))),
            diameter=inch(0.5), material="pex",
            # Down off header out-4, over the tank at 95 7/16", up into the joist bay at 103".
            elevations=(inch(86.149), inch(83.5), inch(83.5), inch(95.4375), inch(95.4375), inch(103),
                  inch(103), inch(109.438), inch(151.438), inch(151.438), inch(129.438)),
            wall_refs=(None, None, None, None, None, None, None, "W-M-CLN", "W-M-CLN", "W-M-CLN"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    # ** THE WASHER BOX IS BEHIND THE TOWER, ON W-M-CLN (owner, 2026-11-07). ** It stood on
    # W-M-BA2E at y=20'-7", 4' of hose from the machine's rear inlets and against BATH2's tub
    # wall; its valves are 5" behind the rear inlets, 8" apart about x=141.5" (hot 137.5", cold
    # 145.5"; the WashTower's inlet stations are scaled, not dimensioned), on a branch that tees off the tub pair's terminal corner and
    # runs east in the same staggered cavity, in the y=215" lane: 1" clear of PR-M-LSINK-VENT's
    # riser at (124", 217.5"), 1 3/4" short of PR-M-S-SUITE-DRAIN's 3" barrel at x=12'-6", and 5.7" under the receptacle boxes ED-M-LAUNDRY-RC1/DR1
    # (43" AFF, recessed 2.5"-4"). Cold rides 35", hot 37 1/2" and ends first, so the cold
    # passes under it; the last 3" turn out to the box face. LG sells the hoses separately
    # (5' pair, appliance_types.py), so each reaches with 4' to spare.
    PipeRun(uid="B879Z3S3VC", tag="PR-M-WASH-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(109.5), inch(217)), pt(inch(109.5), inch(215)),
                  pt(inch(109.5), inch(215)), pt(inch(145.5), inch(215)),
                  pt(inch(145.5), inch(218)),),
            diameter=inch(0.75), material="pex",
            elevations=(inch(149.4375), inch(149.4375), inch(144.4375), inch(144.4375),
                        inch(144.4375),),
            wall_refs=("W-M-CLN", "W-M-CLN", "W-M-CLN", "W-M-CLN"),
            serves=("FX-M-LAUNDRY",)),
    PipeRun(uid="W4T0H24P8K", tag="PR-M-WASH-HW", system=PipeSystem.WATER_HOT,
            path=(pt(inch(114), inch(217)), pt(inch(114), inch(215)),
                  pt(inch(114), inch(215)), pt(inch(137.5), inch(215)),
                  pt(inch(137.5), inch(218)),),
            diameter=inch(0.5), material="pex",
            elevations=(inch(151.4375), inch(151.4375), inch(146.9375), inch(146.9375),
                        inch(146.9375),),
            wall_refs=("W-M-CLN", "W-M-CLN", "W-M-CLN", "W-M-CLN"),
            serves=("FX-M-LAUNDRY",)),
    # ** IT STEPS NORTH AND UP TO CROSS RM-B-STAIR (2026-09-09; the heights re-derived
    # 2026-09-19). ** The original argument was a finished-volume one and it is worth
    # keeping as the record of why this jog EXISTS: the y=15'-6" hot lane rode at
    # 7'-9 7/16", 3.9" under a 7'-11 3/16" finished ceiling, `mep.run_in_finished_volume`
    # allows 3", and the hall is neither the workshop nor the gym's east half. The lane
    # could not simply be raised in place, because PR-B-HW-SAUNA occupies it out to
    # x=17'-3" and PR-B-CW-SAUNA drops across it at x=17'-4". So the crossing took its own
    # lane: north to y=16'-5", 5" clear of PR-B-CW-TRUNK's y=16'-0" and north of
    # PR-B-CW-SAUNA's head at y=16'-0", across the hall, and back down in RM-B-GYM.
    #
    # ** THE TWO-BAND CONVENTION SETTLED THE HEIGHT PART OF THAT ARGUMENT OUTRIGHT. ** The
    # hot band is now 8'-1 7/16" and the cold 8'-4 5/8" — both ABOVE the 7'-11 3/16"
    # finished ceiling, tucked in the floor cavity rather than hanging under it — so
    # `mep.run_in_finished_volume` has nothing to measure on either of them anywhere in the
    # hall. The jog keeps its PLAN shape, which is still doing work (the sauna pair really
    # does own the y=15'-6" lane out to x=17'-4"), and its two raised vertices ride the COLD
    # band the way they always did.
    # ** THE x=17'-6" AND x=18'-9" STEPS ARE GONE (2026-11-01). ** They put the leg through
    # W-B-CS2's cast sleeve and then under SL-M-DECK; with the framed wall and FS-M-NE it stays
    # on the cold band across the plate and through the truss bay at y=16'-5" (see the
    # convention above), and the y=15'-6" return that dodged PR-B-CW-TRUNK's lane is moot.
    # ** BOTH KITCHEN RISERS SURFACE AT THE SINK BASE'S BACK (2026-10-23). ** At y=35'-1 1/2",
    # 3.9" off its back panel and east of the disposer and drain, stopping 20" AFF under the
    # bowl. ** SINCE 2026-11-01 THEY RISE 2 3/4" FARTHER NORTH, AT y=35'-4 3/16" (424.2"), **
    # the 35'-36' truss bay: y=35'-1 1/2" is the chord of the 420" truss line (418 1/4".. 421 3/4"; lines are 16" o.c.).
    # Each jogs back south above the floor, the hot at 118 1/2" (just over the dishwasher stub
    # at 114 15/16") and the cold at 120", to the stop positions it always had.
    PipeRun(uid="CBPW39AAAA", tag="PR-B-HW-KITCH", system=PipeSystem.WATER_HOT,
            # Both steps are plumb (2026-09-26): a 3" jog over 2" of plan was a 58-degree
            # bend a 3/4" PEX cannot make in that little tube.
            path=(pt(inch(160), inch(201.788)), pt(inch(160), inch(201.788)), pt(inch(153), inch(201.788)),
                  pt(inch(153), inch(201.788)), pt(inch(162), inch(201.788)),
                  pt(inch(162), inch(197)), pt(inch(210), inch(197)),
                  pt(inch(370.6), inch(197)), pt(inch(370.6), inch(424.2)),
                  pt(inch(363.6), inch(424.2)), pt(inch(363.6), inch(424.2)),
                  pt(inch(363.6), inch(421.5)), pt(inch(363.6), inch(421.5))),
            diameter=inch(0.5), material="pex",
            # Down off header out-2, up into the y=16'-5" joist bay at 103 3/16" beside the
            # header, over W-B-HALL-W's plate and the authored route east and north (it
            # crosses the trusses in D12; one run per pocket). PR-M-DW-HW tees on its riser.
            elevations=(inch(86.149), inch(83.5), inch(83.5), inch(103.2), inch(103.2), inch(103.2),
                  inch(103.2), inch(103.2), inch(103.2), inch(103.2), inch(118.5), inch(118.5),
                  inch(129.438)),
            serves=("FX-M-KITCH-SINK", "APPL-M-DW")),
    # Second-storey groups: risers climb two storeys to the hall bath, split at both deck
    # top (ft(9) basement-rel = 0'-0" project) and second floor (ft(19) = 10'-0" project),
    # naming the host wall on each leg. Main-storey leg is in a 2x4 partition (3.5" cavity,
    # ample for 3/4" PEX); only the second-storey leg is in a staggered wet wall.
    PipeRun(uid="CBPW40AAAA", tag="PR-B-CW-SBATH", system=PipeSystem.WATER_COLD,
            # y=26'-5 1/4", not the wall axis: FS-S-WEST's truss joist-0-020 starts at
            # 26'-6 1/4", and on the axis the riser took 3/16" of it.
            # x=5'-3" since 2026-09-24: at 5'-7.2" the riser stood in DU-M-ERV-R-LIVING's lane
            # through FS-S-WEST. The basement leg passes the BATH1 stack on y=26'-2" and turns
            # north onto the riser east of it (west of it, the vanity arm lands on the stack).
            # Tees on the trunk's x=4'-9" leg at y=17'-0", 4" north of PR-B-CW-BATH2's tee
            # (2026-11-12; the y=16'-0" tee stood in joist 012's web).
            path=(pt(ft(4, 9), ft(17)), pt(ft(4), ft(17)), pt(ft(4), ft(26, 2)),
                  pt(ft(5, 3), ft(26, 2)), pt(ft(5, 3), ft(26, 6.75)),
                  pt(ft(5, 3), ft(26, 6.75)),
                  pt(ft(5, 3), ft(26, 6.75)), pt(ft(5, 3), ft(26, 6.75)), pt(ft(5, 3), ft(26, 6.75)),
                  pt(inch(63), inch(318.75)),),
            diameter=inch(0.75), material="pex",
            # Two inches OVER the band for the length of the branch: its y=26'-6" leg has to
            # cross the cold trunk's own north-south lane, and two 3/4" pipes on one
            # elevation is a lap rather than a crossing.
            elevations=(ft(8, 4.6375), ft(8, 6.6375), ft(8, 6.6375), ft(8, 6.6375), ft(8, 6.6375), ft(9, 1.4375), inch(222.9375), ft(19, 1.4375), ft(21, 7.4375), inch(323.4375),),
            wall_refs=(None, None, None, None, None, "W-M-STOS", "W-M-STOS", "W-S-BD-N", "W-S-BD-N",),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # Tees off PR-B-HW-TRUNK's riser leg by the header (2026-11-09) and runs west at 95 1/2"
    # over the tank's ducts and PR-B-SAUNA-VENT, drops to 82 1/2" at x=8'-6" to pass
    # W-B-CW3 and the header's lanes, north to y=22'-10.8", then (2026-11-21, the ERV by the
    # sink) back up to 95 1/2", north over the ERV's plenums
    # and up into FS-M-MECH's y=26'-7 1/2" bay, west in it over the risers to its old riser.
    # The main-storey leg rises at x=5'-6 1/2" in W-M-STOS's last bay, west of D-M-MUD's
    # derived RO (owner, 2026-10-29), and jogs east over the plates in FS-S-WEST's
    # y 311 3/4"..322 1/4" bay to x=6'-4", where the second-storey branches tee off. The
    # bay is 2 3/4" wide, so this run takes the 1/2" (R-3.1) sleeve the house uses elsewhere.
    # PEX-A since 2026-11-19 (design review §10): same 7/8" OD, 0.681" bore (SDR 9) against
    # copper's 0.785", so the branch holds ~0.75 gal, not 1.00 (notes/water_service.md). The
    # tee stays on the copper trunk.
    PipeRun(uid="CBPW41AAAA", tag="PR-B-HW-SBATH", system=PipeSystem.WATER_HOT,
            path=(pt(inch(153.786), inch(191.36)), pt(inch(102), inch(191.36)), pt(inch(102), inch(212.5)),
                  pt(inch(102), inch(212.5)), pt(inch(102), inch(274.8)),
                  pt(inch(102), inch(274.8)), pt(inch(102), inch(319.5)),
                  pt(inch(102), inch(319.5)), pt(inch(66.5), inch(319.5)),
                  pt(inch(66.5), inch(319.5)), pt(inch(66.5), inch(319.5)),
                  pt(inch(76), inch(319.5)), pt(inch(76), inch(319.5)),
                  pt(inch(76), inch(319.5)), pt(inch(76), inch(319.5))),
            diameter=inch(0.75), material="pex", insulation='1/2" fiberglass sleeve, ASJ jacket (R-3.1)',
            elevations=(inch(95.5), inch(95.5), inch(95.5), inch(82.5), inch(82.5), inch(95.5), inch(95.5),
                  inch(103), inch(103), inch(109.438), inch(219.438),
                  inch(219.438), inch(229.438), inch(259.438), inch(321.438)),
            wall_refs=(None, None, None, None, None, None, None, None, None, "W-M-STOS", None,
                  None, "W-S-BD-N1B", "W-S-BD-N1B"),
            serves=("FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                    "FX-S-VANITY-LAV2")),
    # ** BOTH RISERS FINISH IN W-S-SN3 SINCE 2026-09-09. ** They used to surface at
    # (13'-7.2"/14'-2.4", 16'-10.8") at 12'-6" and stop there — two stubs standing 2'-6" out
    # of RM-S-SUITEBATH's floor, 4'-3" from the lavatory they feed and in a wall-free part of
    # the room. `mep.run_in_finished_volume` called both at that room's full 107 1/2".
    #
    # They now make the same move PR-A-CW-STUBATH makes off the same risers: stop in
    # FS-S-WEST, jog north through the open truss webs to y=22'-4" — W-S-SN3, the staggered
    # wet wall FX-S-SUITEBATH-WC and -LAV are both plumbed into — and rise inside it to the
    # 12'-6" stops. Elevations here are BASEMENT-relative (datum -9'-1 7/16"), so the jogs
    # read 18'-7 3/16" and 18'-11 7/16" = 9'-5 1/2" and 9'-10" project.
    #
    # THE TWO JOG HEIGHTS ARE BOTH PINNED, AND NOT BY EACH OTHER. The truss floor is busy:
    # six ERV branches ride its middle at 9'-1 5/8" (6" round, so 8'-10 5/8"..9'-4 5/8") and
    # the suite bath's three drains cross above them at 9'-7"..9'-9 1/2". The cold threads
    # the 2 1/2" gap between the two — 7/8" clear of the ducts, 10/16" clear of
    # PR-M-S-SUITE-TUB-DRAIN at y=19'-0". The hot cannot: PR-A-HW-STUBATH tees off it at
    # 9'-7", so it has to be ABOVE the drains and rides at 9'-10", 7/8" under the top chord.
    # x stays on each riser's own lane, which keeps the cold 2 3/10" clear of
    # PR-M-S-SUITE-LAV-DRAIN's drop at x=13'-9 1/2". Each rise then SPLITS AT THE SECOND
    # FLOOR (ft(19,1.4375) basement-rel = 10'-0" project), the way PR-B-CW-SBATH does:
    # W-S-SN3 starts at the deck it stands on, and a leg naming it from inside the truss
    # floor is a leg `mep.wet_wall_occupancy` reads as escaping the wall.
    # ** BOTH RISE INSIDE W-M-CLN2 SINCE 2026-09-23, NOT IN THE MASTER CLOSET. ** They stood
    # at y=16'-10.8", 9.8" off the closet's north wall and through FURN-M-CLOSET-SHELF;
    # RM-M-CLOSET is `closed_to_services`. W-M-CLN2 is staggered 2x4 on 2x6 plates,
    # non-bearing, studs every 8" on alternate faces: the cold stands mid-bay at x=15'-9",
    # the hot at 16'-5", 3 1/4" off every stud and east of DU-M-ERV-R-LAUNDRY's drop at
    # x=14'-5". Each bores the top plate into FS-S-WEST, runs north in the same web opening
    # (15'-4 1/2"..16'-7 1/2") to y=22'-4", and west under W-S-SN3 to its old riser. The
    # wall leg is split at the wall's base and top so it names only the wall it is in.
    PipeRun(uid="CBPW42AAAA", tag="PR-B-CW-SUITE", system=PipeSystem.WATER_COLD,
            # 2026-11-06: crosses the trusses at x=15'-3" (TrimJoist pocket D13, clear of ED-M-STUDY-LT's
            # housing), jogging west in the 208..224 bay; one run per pocket. 2026-11-08: the
            # y=256" truss's D13 is the tub drain's, so it jogs east to D14 (x=16'-0 3/8")
            # there; CD-M-DATA-KITCH gave that pocket up.
            # 2026-11-12: square off the trunk's y=14'-8" lane at x=15'-3", north through joists
            # x00/012/013 (33" clear of PR-M-S-SUITE-DRAIN's hole at x=150", 7" west of the hall
            # cans' x=190" line) and 6" east in the 208..224 bay to the riser; the old diagonal
            # started in joist 012's web and crossed the x=14'-6" sister block.
            path=(pt(inch(183), inch(176)), pt(inch(183), ft(18)), pt(ft(15, 9), ft(18)), pt(ft(15, 9), ft(18)),
                  pt(ft(15, 9), ft(18)), pt(ft(15, 9), ft(18)), pt(inch(183), ft(18)),
                  pt(inch(183), inch(250)), pt(inch(192.375), inch(250)),
                  pt(inch(192.375), inch(262)), pt(inch(183), inch(262)),
                  pt(inch(183), ft(22, 4)),
                  pt(ft(13, 7.2), ft(22, 4)), pt(ft(13, 7.2), ft(22, 4)),
                  pt(ft(13, 7.2), ft(22, 4)), pt(ft(13, 7.2), ft(22, 4)),
                  pt(ft(13, 7.2), ft(22, 4))),
            diameter=inch(0.75), material="pex",
            # +5/16" on 2026-09-16 (7.1875 -> 7.5): the 4" ERV ducts' crowns are at 9'-5 5/8",
            # and KITCH/BED2 now cross this jog at y=21'-10"/22'-2". 5/16" left under the tub drain.
            elevations=(ft(8, 4.6375), ft(8, 4.6375), ft(8, 4.6375), ft(9, 1.4375), ft(18, 1.3125),
                        ft(18, 7.5), ft(18, 7.5), ft(18, 7.5), ft(18, 7.5), ft(18, 7.5),
                        ft(18, 7.5), ft(18, 7.5), ft(18, 7.5), ft(19, 1.4375),
                        inch(238.9375), inch(253.4375), ft(21, 7.4375)),
            wall_refs=(None, None, None, "W-M-CLN2", None, None, None, None, None, None, None,
                       None, None, "W-S-SN3", "W-S-SN3", "W-S-SN3"),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
    PipeRun(uid="CBPW43AAAA", tag="PR-B-HW-SUITE", system=PipeSystem.WATER_HOT,
            # Tees off PR-B-HW-TRUNK's 95 1/2" leg by the header (2026-11-09), rises at once
            # to 105.4", runs north in the joist bay to y=17'-0" and square east, into the
            # riser's bay from the SOUTH: FS-M-WEST blocks that bay at x=14'-6" under the
            # laundry duct's drop. It crosses the trusses in TrimJoist pocket D15.
            # 2026-11-13: the basement lane rode 97 7/16", its jacket (r 0.94") 0.81" into joist
            # 013's bottom flange at x=197" and in the ceiling board. 105.4" is inside the web
            # (window 98.81..108.19; jacket 104.46..106.34, 0.95" over PR-B-HW-KITCH's 103.2"
            # lane, 1.85" under the top flange): one bare 3/4" bore at x=197", 1.125" hole,
            # 15.7" off the support (field row 6"), sleeve cut each side of the web.
            # ** IN THE TRUSS FLOOR IT RUNS UNDER THE TUB WASTE (2026-10-08). ** The north leg
            # shares x=16'-5" with PR-M-S-SUITE-TUB-DRAIN's leg (0.6" apart) and there is no
            # lane beside it: the web opening ends at 16'-7 1/2" and DU-M-ERV-R-BED2 (deleted
            # 2026-11-20) and the cold held the west. So it rides under the waste at 9'-6 11/16"
            # on a 1/2" sleeve (R-3.1, as PR-A-HW-STUBATH), over the STUDY radial's crown, dips
            # to 9'-6" under CD-M-DATA-KITCH at y=21'-1.3" and through truss 016's opening,
            # steps to 9'-7" for DU-M-ERV-R-KITCH. North of truss 017 it jogs 5" west to
            # x=16'-0" (2026-11-05), clear of the tub's trap and under its arm, and climbs to
            # 9'-10" only under W-S-SN3 before turning west over the cold.
            path=(pt(inch(158), inch(196.16)), pt(inch(158), inch(196.16)), pt(inch(158), inch(204)),
                  pt(inch(163), inch(204)), pt(inch(197), inch(204)), pt(inch(197), inch(216)),
                  pt(inch(197), inch(216)), pt(inch(197), inch(216)), pt(inch(197), inch(216)),
                  pt(inch(201.75), inch(216)), pt(inch(201.75), inch(249)),
                  pt(inch(201.75), inch(251.625)), pt(inch(201.75), inch(258.75)),
                  pt(inch(201.75), inch(265.5)), pt(inch(201.75), inch(268)),
                  pt(inch(171.6), inch(268)), pt(inch(171.6), inch(268)),
                  pt(inch(171.6), inch(268))),
            diameter=inch(0.75), material="pex", insulation='1/2" fiberglass sleeve, ASJ jacket (R-3.1)',
            elevations=(inch(95.5), inch(105.4), inch(105.4), inch(105.4), inch(105.4),
                  inch(105.4), inch(109.438), inch(217.312), inch(224.125), inch(224.125),
                  inch(224.125), inch(223.438), inch(224.438), inch(224.438), inch(226.938),
                  inch(227.438), inch(229.438), inch(259.438)),
            wall_refs=(None, None, None, None, None, None, "W-M-CLN2", None, None, None, None, None, None,
                  None, None, None, "W-S-SN3"),
            serves=("FX-S-SUITEBATH-LAV", "FX-S-SUITEBATH-TUBSH", "FX-A-STUBATH-LAV",
                    "FX-A-STUBATH-SH", "FX-A-STUDIO-BAR-SINK")),
    # The utility sink's cold (and the old stair-foot bath's, until 2026-11-25). 3/4", kept from
    # when it also fed the WC. It tees off PR-B-CW-TRUNK's x=4'-9" leg at y=20'-3" and runs
    # east 2" over the band (over PR-B-CW-BATH1's diagonal) to its drop in W-B-STR2.
    PipeRun(uid="CBPW44AAAA", tag="PR-B-CW-BATH", system=PipeSystem.WATER_COLD,
            path=(pt(inch(57), inch(243)), pt(inch(57), inch(243)), pt(inch(120), inch(243)),
                  pt(inch(120), inch(238)), pt(inch(120), inch(238))),
            diameter=inch(0.75), material="copper",
            elevations=(inch(100.638), inch(102.638), inch(102.638), inch(102.638), inch(27.4375)),
            # The stair-foot bath it was named for is gone (2026-11-25): the utility sink only.
            serves=("FX-B-UTIL-SINK",)),
    PipeRun(uid="CBPW45AAAA", tag="PR-B-HW-BATH", system=PipeSystem.WATER_HOT,
            # Header out-6, west to x=9'-8 1/2", north through W-B-CW3 at 83 1/2" and over to
            # the bath riser. The drop is at 18'-8 1/2" (2026-10-31): at 19'-4 1/2" it stood in
            # W-B-STR2's stud-001; north of the stud DU-B-ERV-R-PLAY fills the bay, and south
            # of it PR-B-BATH-VENT and PR-B-LSINK-DRAIN's crossing leave no 5/8" gap until here.
            path=(pt(inch(160), inch(207.788)), pt(inch(160), inch(207.788)), pt(inch(151), inch(207.788)),
                  pt(inch(151), inch(207.788)), pt(inch(116.5), inch(207.788)),
                  pt(inch(116.5), inch(207.788)), pt(inch(116.5), inch(224.5)),
                  pt(inch(116.5), inch(224.5)), pt(inch(120), inch(224.5)),
                  pt(inch(120), inch(224.5))),
                        diameter=inch(0.5), material="pex",
            elevations=(inch(86.149), inch(83.5), inch(83.5), inch(95.4375), inch(95.4375), inch(83.5),
                  inch(83.5), inch(95.4375), inch(95.4375), inch(27.4375)),
                        serves=("FX-B-UTIL-SINK",)),
    # RM-B-BATH's supplies (2026-11-25; the sauna shower's until then). Both still tee where
    # they did and drop south through the floor cavity, then run west in the bath's hung-
    # ceiling cavity as headers over W-B-SA-N's room face — cold on y=8'-7" at 7'-8 1/2", hot
    # on y=8'-8 1/2" at 7'-9 1/2" — to the shower valve. The lav's terminals and the WC's stop
    # tee off them (mep_lavatories.py, mep_supply_branches.py). Each drops in the valve's bay
    # 1 1/4" behind the face and turns into the valve's side inlet. Cold is 3/4" (4.75 WSFU).
    PipeRun(uid="CBPW46AAAA", tag="PR-B-CW-SAUNA", system=PipeSystem.WATER_COLD,
            # ESR-1153 Table A: x=206.5" puts the 0.88" hole 6.3" off the x=213.25 face; it tees
            # on the trunk's y=15'-0" leg.
            path=(pt(inch(206.5), inch(180)), pt(inch(206.5), inch(103)),
                  pt(inch(206.5), inch(103)), pt(inch(137.5), inch(103)),
                  pt(inch(137.5), inch(98.25)), pt(inch(137.5), inch(98.25)),
                  pt(inch(140.25), inch(98.25))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(8, 4.6375), ft(8, 4.6375), inch(92.5), inch(92.5), inch(92.5),
                        inch(51.4375), inch(51.4375)),
            serves=("FX-B-BATH-SH", "FX-B-BATH-LAV", "FX-B-BATH-WC")),
    PipeRun(uid="CBPW47AAAA", tag="PR-B-HW-SAUNA", system=PipeSystem.WATER_HOT,
            # Header out-1, up to 103 3/16" and south in the joist web to its y=15'-8" lane
            # east, crossing the hall at x=16'-3", and down x=16'-3" over PR-B-CW-TRUNK's
            # y=14'-8" lane into the bath's cavity.
            path=(pt(inch(160), inch(200.288)), pt(inch(160), inch(200.288)),
                  pt(inch(154.5), inch(200.288)), pt(inch(154.5), inch(200.288)),
                  pt(inch(154.5), inch(188)), pt(inch(195), inch(188)),
                  pt(inch(195), inch(104.5)), pt(inch(195), inch(104.5)),
                  pt(inch(147), inch(104.5)), pt(inch(147), inch(98.25)),
                  pt(inch(147), inch(98.25)), pt(inch(144.25), inch(98.25))),
            diameter=inch(0.5), material="pex",
            elevations=(inch(86.149), inch(83.5), inch(83.5), inch(103.2), inch(103.2), inch(103.2),
                        inch(103.2), inch(93.5), inch(93.5), inch(93.5), inch(51.4375),
                        inch(51.4375)),
            serves=("FX-B-BATH-SH", "FX-B-BATH-LAV")),
]

# --- The two south-face wall hydrants ------------------------------------------------
#
# Both fed from above, out of the second floor's joist space (FS-S-WEST, 11 7/8" open-web
# floor trusses), rather than from below: the main-storey exterior wall's stud cavity sits
# directly over W-B-S1 (cast concrete, 8", and W-M-C1/W-B-CS on the centre line, 12"), so a
# riser through the main floor there would surface through the top of a bearing wall. One
# riser leaves the basement and splits upstairs — one leg into W-M-S1 to the porch hydrant, one into
# W-S-S1 to the balcony hydrant — always inboard of the wall's 4" continuous exterior
# insulation so the pipe stays warm.
#
# The riser stands in W-M-BDN1, a 2x4 partition (3.5" cavity, ample for 3/4" PEX) whose
# floor crossing lands in an open joist bay at x=6', not on a wall below.
HYDRANT_BRANCH_BASEMENT = [
    # Two runs, one branch, split at the deck: the ceiling leg and the slab-up leg inside the
    # wall/joist bays.
    PipeRun(uid="X4M2QP7B0K", tag="PR-B-CW-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), inch(176)), pt(ft(6), ft(13))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(8, 4.6375), ft(8, 4.6375)),
            serves=("FX-M-PORCH-HYD", "FX-S-BALCONY-HYD")),
    PipeRun(uid="Z5NB8QMK2H", tag="PR-B-CW-HYD-RISER", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(13)), pt(ft(6), ft(13)), pt(ft(6), ft(13)),
                  pt(ft(6), ft(13))),
            diameter=inch(0.75), material="pex",
            # Basement-relative -> project: 8'-4 5/8" cold band (-0'-8.8", six inches up on
            # 2026-09-19), 9'-0" deck top (0'-0"),
            # 18'-0" W-M-BDN1's top plate (9'-0", the partition's ceiling height), 18'-3"
            # (9'-3") inside the joist space (11 7/8" joists hang 9'-0 1/8" to 10'-0"). Split
            # at the plate because `mep.wet_wall_occupancy` grades an in-wall segment against
            # the wall's own z-extent; a straight riser would escape it by 3".
            elevations=(ft(8, 4.6375), ft(9, 1.4375), ft(18, 1.4375), ft(18, 4.4375)),
            wall_refs=(None, "W-M-BDN1", None),
            serves=("FX-M-PORCH-HYD", "FX-S-BALCONY-HYD")),
]

# Joist-space distribution, filed on ``main`` (datum 0'-0") so 9'-3" reads as the ceiling
# height it is. The E-W leg runs *along* a joist bay at y=0'-9"; the riser crosses joists at
# x=6' drilled through their webs — 3/4" PEX in an 11 7/8" I-joist web is within every
# manufacturer's hole chart.
HYDRANT_BRANCH_MAIN = [
    # The east end stops at x=12'-8", where both hydrant legs leave it (2026-11-03): the porch
    # leg drops in W-M-S1 and the balcony leg rises off it in W-S-S1, one station.
    PipeRun(uid="R9TC5VZ1WQ", tag="PR-M-CW-HYD-DIST", system=PipeSystem.WATER_COLD,
            # ** THE SOUTH LEG IS ON THE UPPER TIER AT x=6'-3" SINCE 2026-09-24. ** On x=6'-0"
            # at +9'-3" it crossed DU-M-ERV-R-LIVING, -BED and -PLANT on their lower-tier bay
            # legs; 3" east it clears DU-M-ERV-R-BED's upper-tier lane and rides over all three.
            # 2026-11-08: x=8'-0 1/2" in pocket D7, 6" over the chord (over the ERV takeoffs):
            # D6 is DU-M-ERV-R-BED's.
            path=(pt(ft(6), ft(13)), pt(inch(96.5), ft(13)), pt(inch(96.5), ft(13)),
                  pt(inch(96.5), ft(0, 9)), pt(inch(96.5), ft(0, 9)), pt(ft(12, 8), ft(0, 9))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), inch(114.125), inch(114.125), ft(9, 3), ft(9, 3)),
            serves=("FX-M-PORCH-HYD", "FX-S-BALCONY-HYD")),
    # Porch leg: south into the wall's own plane (y=3 1/4", the 2x6 cavity's centre line),
    # then straight down inside W-M-S1 to the hydrant's seat at 2'-0".
    PipeRun(uid="B6HD0NKX3M", tag="PR-M-CW-PORCH-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12, 8), ft(0, 9)), pt(ft(12, 8), ft(0, 3.25)),
                  pt(ft(12, 8), ft(0, 3.25))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), inch(22)),
            wall_refs=(None, "W-M-S1"),
            serves=("FX-M-PORCH-HYD",)),
    # Balcony leg: tees off the porch leg in the wall plane and rises straight over it. Split
    # at 10'-0" because the second floor is between: below that line the pipe is crossing the
    # deck and hosted by nothing, above it it is inside W-S-S1's cavity (which starts at
    # 10'-0"), and `mep.wet_wall_occupancy` grades a declared segment against the wall's own
    # z-extent.
    #
    # x=12'-8" (2026-11-03, on the balcony and over FX-M-PORCH-HYD): W-S-S1 resolves stud-003
    # at 144" and king-2-l0 (WIN-S-PLANT4) at 158 3/4", a clear bay of 144 3/4"..158", so
    # the riser is 7 1/4" off the stud and 6" off the king, the 16" bay centre.
    PipeRun(uid="V2FJ8LRY6P", tag="PR-M-CW-BALCONY-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12, 8), ft(0, 3.25)), pt(ft(12, 8), ft(0, 3.25)),
                  pt(ft(12, 8), ft(0, 3.25))),
            diameter=inch(0.75), material="pex",
            # 12'-0.829": the seat is 24" over RM-S-PLANT's finished floor, 0.829" over the
            # deck, and so are AO-S-BALCONY-HYD and SP-S-BALCONY-HYD — one centreline.
            elevations=(ft(9, 3), ft(10), inch(144.829)),
            wall_refs=(None, "W-S-S1"),
            serves=("FX-S-BALCONY-HYD",)),
    # The barrel: the hydrant's own metal tube + sleeve, modelled as a run so the insulation
    # can be billed and `mep.exterior_hydrant_protection` has something to grade. The one
    # place in the house where a supply pipe is *in* the envelope rather than behind it — 10"
    # of metal from the seat out through sheathing/polyiso/EPS/rainscreen to the escutcheon
    # at y=-5". PEX stops at the seat so the thermal bridge doesn't extend into the room.
    PipeRun(uid="T8WQ3E5AZC", tag="PR-M-CW-PORCH-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12, 8), ft(0, 3.25)), pt(ft(12, 8), inch(-5))),
            diameter=inch(0.75), material="pex",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(inch(22), inch(22)),
            serves=("FX-M-PORCH-HYD",)),
]

# --- kitchen cold stub, for a future cold-storage water connection ---------------------
#
# The owner chose an all-refrigerator with no ice maker and no dispenser, so nothing in the
# cold-storage bay takes water and nothing here `serves` anything. This is provision, not
# plumbing: a capped 1/2" line to the back of the bay so the day a unit with an ice maker or
# a filtered tap arrives, the job is pulling the appliance out and opening a stop, not
# opening a finished kitchen.
#
# **Why it is worth authoring now and not later.** The whole cold-storage bay stands on
# FS-M-NE's trusses (x 18'-36', y 13'-36'). A line fed from *below* would be a hole through
# the floor, and coring a finished truss floor afterwards is a different kind of job. This one never goes below the floor:
# it tees off the kitchen cold where it has already surfaced, at the riser head in the sink
# base (ft(29, 9.6) / inch(421.5)) where PA-M-KITCH-STOP-CW and PA-M-RO-STUB
# already sit, and runs at 20" (the stop height) through the backs of cabinets that are
# being built anyway — west along the north run, then south down the west run. No penetration, no sleeve, no
# concrete, and every inch of it behind a removable cabinet back.
#
# A cold branch threading a built assembly, not a trunk. 1/2" stubbed and reduced at the stop, so the tee
# suits a filtered tap as well as the 1/4" an ice maker wants.
#
# The pantry's south wall now contains the west-parking Eclisse cassette. This route
# stays in the perpendicular walls and crosses the pantry at 8'-4", above the pocket.
# No pipe or fastener may enter the cassette (notes/pocket_frame_eclisse.md).
#
# THE CORNER IT WOULD CROSS IS A ROOM NOW, so there is no cabinet-back path left there. That
# is the honest cost of the pantry, not a routing failure: the run's whole premise was
# "behind removable cabinet backs the whole way", and between x=18'-0" and 24'-4" the
# cabinets that made that true have become RM-M-PANTRY. So the crossing is made where a
# plumber would actually make it — UP into the framing at each end, ACROSS at 8'-4",
# clear over FURN-M-PANTRY-SHELVES' 7'-0" top and under the 9'-0" plate. Six feet of it is
# exposed in the pantry, above the shelves and out of reach, and every vertical is inside a
# stud cavity parallel to the studs, boring nothing:
#   * the rise at x=24'-5" is at the pantry's east end, just west of W-M-PAN-E;
#   * the drop at x=18'-0" is on W-M-C5/C5B's own axis, mid-cavity (17'-9 1/4"..18'-2 3/4"),
#     and carries on south inside it to y=31' before stepping east to the stub.
# No penetration of the floor.
KITCHEN_STUB_MAIN = [
    PipeRun(uid="N0D5ATAN07", tag="PR-M-CW-COLDSTORE-STUB", system=PipeSystem.WATER_COLD,
            path=(pt(ft(29, 9.6), inch(421.5)),
                  pt(ft(24, 5), inch(421.5)),
                  pt(ft(24, 5), inch(421.5)),
                  pt(ft(18), inch(421.5)),
                  pt(ft(18), inch(421.5)),
                  pt(ft(18), ft(31)),
                  pt(ft(18, 9), ft(31))),
            diameter=inch(0.5), material="pex",
            elevations=(inch(20), inch(20), ft(8, 4), ft(8, 4), ft(2, 6), ft(2, 6),
                        ft(2, 6))),
]

# The balcony hydrant's barrel, filed on ``second`` (datum 10'-0") with the wall it pierces.
# The barrel is the escutcheon-to-seat penetration, so its x IS the riser's x and is not
# independently chosen. PA-S-BALCONY-HYD-SEAL (plan/mep_supply_devices.py) shares the station.
HYDRANT_BRANCH_SECOND = [
    PipeRun(uid="G7YB4XN2SD", tag="PR-S-CW-BALCONY-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12, 8), ft(0, 3.25)), pt(ft(12, 8), inch(-5))),
            diameter=inch(0.75), material="pex",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(inch(24.829), inch(24.829)),
            serves=("FX-S-BALCONY-HYD",)),
]

# ======================== THE TWO HYDRANT BARREL PENETRATIONS =========================
#
# Each wall hydrant drives a 10" barrel through a 2x6 wall with 4" of continuous exterior
# insulation, and until 2026-09-15 the hole it needs was in no file. `PA-*-HYD-SEAL` bills
# the escutcheon and the foam; what it could not do is cut the wall, because a
# `PipeAccessory` resolves no void. The same argument `mep_erv_outdoor.py` makes for AO-M-ERV-OA
# applies here and the same element answers it.
#
# ** BOTH LAND IN A CLEAR BAY, AND ONE OF THEM ONLY JUST STARTED TO. ** An RO on a stud
# centreline grows a king/jack/header pack and shoves the 16" module sideways; that is what
# a trial of these two produced before FX-M-PORCH-HYD moved off stud-006 (plan/fixtures.py
# carries the stations and the arithmetic). Measured bays, from the resolved walls:
#   W-M-S1  stud-006 144"..145 1/2", king-1-l0 158 3/4"  -> clear 145 1/2"..158 3/4"
#   W-S-S1  stud-002  80"..81 1/2",  king-1-l0  94 3/4"  -> clear  81 1/2"..94 3/4"
# A 2 1/2" hole centred on each hydrant leaves 5" and 4 3/4" of clear framing to the nearer
# stud face — it is a drilled hole in a bay, not a framed opening, and no pack is generated.
#
# ** 2 1/2" IS THE HOLE SAW, NOT THE ARITHMETIC. ** The barrel is 3/4" PEX inside a 1/2"
# elastomeric sleeve, so 1 7/8" over the sleeve, and `PA-*-HYD-SEAL` foams a 1/4" annulus:
# 2 3/8" is the computed minimum and 2 1/2" is the size that exists. The extra 1/16" of
# annulus per side is foam, which is what the seal's install_parts already buy.
# AO-M-PORCH-HYD is 2 7/8" since decision #142: the derived 2 1/2" Sch 40 PVC sleeve's OD
# (PENETRATION-STANDARD, one size over the 1 7/8" lagged barrel). SP-S-BALCONY-HYD is authored.
#
# ** TWO DATUMS, AND THEY ARE NOT THE SAME ONE (E11, 2026-09-20). ** `RoughOpening.
# sill_height` is measured off the WALL BASE — W-M-S1's `base_ref_z` is 0", W-S-S1's is
# +10'-0" — while the barrel it has to admit is a `Fixture` whose `Mount.elevation` is
# measured off the ROOM'S FINISHED FLOOR. Both hydrants sit at 2'-0" on their room's
# finished floor, and both rooms build up over the structure: RM-M-BED by 1 1/4" and
# RM-S-PLANT by 0.8287". So a sill of 1'-10 3/4" on both (barrel centre 2'-0" minus half a
# 2 1/2" hole) put each hole BELOW its own barrel by exactly its room's build-up, and the
# PEX came through the gypsum rather than the hole. The sills carry the build-up now:
# 2'-0" here and 1'-11.579" on the balcony, each = build-up + 24" - 1 1/4".
#
# ** BOTH ARE BLIND FROM THE YARD, AND THAT CLOSED A DELIBERATE OVER-CUT (2026-09-20). **
# A `RoughOpening` was a hole through the whole assembly -- it had no depth field -- so each
# of these took 2 1/2" out of the gypsum and its paint as well. A wall hydrant is operated
# from OUTSIDE: the barrel stops at its seat inside the cavity (PA-*-HYD-SEAT) and nothing
# pierces the room side. That over-cut was 6.25 sq in of board per hydrant, deliberate rather
# than missed, and the note here said closing it wanted a schema change worth 12.5 sq in
# across the house. The fireplace pocket bought that change, and these two ride it in.
#
# `depth=inch(12)` with `depth_from="exterior"` is a BAND, not a fit, and the band is what
# makes the number safe. The bore has to reach past the sheathing into the stud cavity (the
# stud's outer face is 7 3/4" in from the cladding on BOTH walls) and has to stop short of the
# room-side finish (13 1/4" in on both, again). Anything in 7 3/4"..13 1/4" cuts exactly the
# same set of layers, so 12" sits mid-band with better than an inch of slack each way and is
# what the barrel actually does -- it lands on its seat INSIDE the cavity, not against the
# back of the board. On W-S-S1 the same 12" also leaves the vapour membrane whole, which
# matters more than the board does.
#
# ** BOTH LIMITS ARE THE SAME ON THE TWO WALLS BY ARITHMETIC, NOT BY LUCK: ** EXT_2X6 is
# 13.885" with 0.635" of paint + board; PLANT_EXT_2X6_HUMID is 14.54" with 1.29" of PVC panel
# + liner furring + humid membrane; 13.885 - 0.635 = 14.54 - 1.29 = 13.25, and both carry the
# same 5 1/2" stud behind the same 1/2" sheathing. Nothing links the literal to the stack --
# `resolve/pipeline._blind_depth` only refuses a depth that reaches THROUGH the wall -- so
# a stack change of more than an inch wants this re-derived.
#
# The ERV's two sleeves take no depth: a duct really does go all the way through.
#
# What these still cost correctly is the sheathing -- the bore reaches it, and
# `takeoff/framing.py` deducts a blind opening only from the layers it reaches. They cost no
# LUMBER at all -- a bore is drilled through whatever it meets rather than framed around,
# which is `resolve/framing/openings.framed_around` and the reason BK-M-S1-HYD survives it.
PENETRATIONS_HYDRANT_MAIN = [
    RoughOpening(uid="H72PNVX9AV", tag="AO-M-PORCH-HYD", host="W-M-S1",
                 position=from_node("N-M-SW", inch(150.5625)),
                 width=inch(2.875), height=inch(2.875), sill_height=inch(20.5625),
                 depth=inch(12), depth_from="exterior",
                 penetration_for=("PR-M-CW-PORCH-HYD-CU", "PR-M-CW-PORCH-HYD")),
]
PENETRATIONS_HYDRANT_SECOND = [
    RoughOpening(uid="AZMYHB7P8J", tag="AO-S-BALCONY-HYD", host="W-S-S1",
                 position=from_node("N-S-SW", inch(150.75)),
                 width=inch(2.5), height=inch(2.5), sill_height=inch(23.579),
                 depth=inch(12), depth_from="exterior",
                 penetration_for=("PR-S-CW-BALCONY-HYD-CU", "PR-M-CW-BALCONY-HYD")),
]


# --- the attic guest studio -------------------------------------------------------------
# Both runs TEE OFF THE EXISTING SUITE RISERS at their heads and carry on up W-S-DC2 into
# W-A-STU-W — the same 5 1/2" 2x6 cavity the drain and the vent use, and the reason the
# bath is on the x=9'-7 1/2" line at all. 3/4" PEX, matching PR-B-CW-SUITE/PR-B-HW-SUITE
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
# FILED ON ``main`` (datum 0'-0"), SO THESE ELEVATIONS ARE PROJECT ELEVATIONS. Same
# convention, and the same reason, as SECOND_DRAINS in plan/mep_drainage.py: the run spans
# three storeys and the numbers are only readable if they read off the drawing set.
#
# ** THE TEE IS IN THE TRUSS FLOOR, NOT AT THE RISER HEAD, AND THAT IS NOT A REFINEMENT. **
# PR-B-CW-SUITE/-HW-SUITE surface at (13'-7.2"/14'-2.4", 16'-10.8") at 12'-6" — 2'-6" above the
# second floor, inside RM-S-SUITEBATH. Teeing there and running west to the W-S-DC2 axis meant
# 4'-5" of exposed PEX across that bathroom at chest height. So the branch tees LOWER, where
# the suite risers are already passing through FS-S-WEST, and makes the whole east-west jog in
# the truss floor — through the open webs, boring nothing. That is the same crossing
# PR-A-STUBATH-DRAIN makes, in the same floor, for the same reason.
#
# Cold rides at 9'-4" and hot at 9'-7" so the two jogs cannot foul each other where they
# converge on the wet wall; both sit inside the trusses (8'-11 3/8" to 9'-11 1/4"). From
# (9'-7 1/2", 20'-6"/21'-0") each rises straight up W-S-DC2 and W-A-STU-W to its stop at 22'-6".
#
# BOTH RISERS ARE NORTH OF THE TOILET, DELIBERATELY: the water closet is on this wall
# (plan/fixtures.py) and its tank occupies y 18'-6"..20'-2" against it — a riser behind the
# tank would wall in the angle stop while `PA-A-STUBATH-STOP-*.accessible` still claimed
# True. Nothing checks that geometry: `mep.fixture_control_valve` reads the FLAG (UPC 606.6).
# 6" of y separates the two risers, and 3" of z (cold 9'-4", hot 9'-7") keeps their
# truss-floor jogs apart. North of the WC they are also nearer the lavatory they feed.
STUDIO_SUPPLY = [
    PipeRun(uid="WJZGK0YFHY", tag="PR-A-CW-STUBATH", system=PipeSystem.WATER_COLD,
            # ** THE RISER IS 2" WEST OF THE WALL'S AXIS AND THE FEED IS 5 3/5" HIGHER
            # (P3, 2026-09-19). ** It used to stand ON x=9'-7 1/2", which is
            # PR-A-STUBATH-LAV-DRAIN's own lane down the same wet wall — two pipes on one
            # line for two feet. W-A-STU-W is 2x6, so 2" off the axis keeps a 7/8" PEX
            # 3/10" inside the stud face and puts 1 5/8" between it and the drain, which is
            # what the two want. The feed leg went +9'-4" -> +9'-9 3/5" for a different
            # reason: at the old height it ran through PR-M-S-SUITE-WC-DRAIN's fall inside
            # FS-S-WEST's web window AND through two of D1's radials at the low tier. The
            # window is 109 5/8"..118 1/2" and the clear band over the drain is
            # 117.19"..118.06"; this sits in it.
            # Squared off (2026-10-26): the diagonal crossed the 256" truss on a web. West in
            # its own 256..272 bay, south on x=10'-0" (the 113 1/2"..126 1/2" opening, west of
            # PR-M-S-SUITE-WC-DRAIN's east leg), then west in the 240..256 bay to the riser.
            # 2026-11-06: the south leg is at x=10'-2" (TrimJoist pocket D8), not 10'-0" at its edge.
            # North 1 1/2" between x=10'-11" and 12'-2" round PR-M-S-SUITE-WC-DRAIN's north
            # corner (2026-11-08), back on 22'-4" clear of P-S-SN3-SQUASH.
            # 2026-11-22: the jog over PR-M-S-SUITE-WC-DRAIN's north corner goes OVER it, at
            # 117 5/8" (the band above its crown), not 1 1/2" north: y=269.5 is where the 1 1/4"
            # LSL strip under W-S-SN3 now lies (`FS-S-WEST` reinforcement, x 122"..216").
            path=(pt(ft(13, 7.2), ft(22, 4)), pt(inch(146), ft(22, 4)), pt(inch(146), ft(22, 4)),
                  pt(inch(131), ft(22, 4)), pt(inch(131), ft(22, 4)),
                  pt(ft(10, 2), ft(22, 4)), pt(ft(10, 2), ft(20, 6)),
                  pt(ft(9, 5.5), ft(20, 6)), pt(ft(9, 5.5), ft(20, 6)),
                  pt(ft(9, 5.5), ft(20, 6))),
            diameter=inch(0.75), material="pex",
            # The 248.87" vertex is PR-A-STUBATH-WC-CW's tee, at the WC stop's height.
            elevations=(ft(9, 6.0625), ft(9, 6.0625), inch(117.625), inch(117.625), ft(9, 6.0625),
                        ft(9, 6.0625), ft(9, 6.0625), ft(9, 6.0625), inch(248.87), ft(22, 6)),
            serves=("FX-A-STUBATH-WC", "FX-A-STUBATH-LAV", "FX-A-STUBATH-SH",
                    "FX-A-STUDIO-BAR-SINK")),
    PipeRun(uid="TCWF4YDZTW", tag="PR-A-HW-STUBATH", system=PipeSystem.WATER_HOT,
            # ** 1/2" SLEEVE, AND THE FEED GOES ROUND THE SUITE LAV DRAIN (2026-10-08). ** On a
            # 1" sleeve (2.88" OD) this riser could neither share the wall axis with
            # PR-A-STUBATH-LAV-DRAIN nor stand 2" off it inside a 2x6. Now the lav drain jogs
            # east in the joist band, and the riser stands at 20'-10", 3 3/8" off its drop. The
            # sleeve is 1/2" fiberglass, R-3.1 (Owens Corning 722579, k 0.16 by ASTM C547),
            # which still meets IECC R403.5.3's R-3, and it is what lets the feed cross over
            # PR-M-S-SUITE-WC-DRAIN under the 10'-0" deck.
            # The feed leg: 2 3/4" west along W-S-SN3's line, south on x=14'-0 3/4" between
            # PR-M-S-SUITE-LAV-DRAIN (3 1/4") and DU-M-ERV-R-LAUNDRY (4 1/4") through the
            # 13'-4 1/2"..14'-7 1/2" web opening (bare crown 118.46" against 118.5"), then west
            # on y=20'-3", inside the 20'-0"..21'-4" truss bay, to the riser.
            # 2026-11-06: it crosses the 256" truss in TrimJoist pocket D12, which a 0.88" line
            # fits only at 115.4" or lower: a plumb drop onto the crossing (clear of the cold's
            # y=22'-4" run) and a plumb rise to the old 118.25" in the 240..256 bay.
            path=(pt(ft(14, 3.6), ft(22, 4)), pt(ft(14, 0.75), ft(22, 4)),
                  pt(ft(14, 0.75), inch(260)), pt(ft(14, 0.75), inch(260)),
                  pt(ft(14, 0.75), inch(252.7)),
                  pt(ft(14, 0.75), inch(252.7)), pt(ft(14, 0.75), ft(20, 3)),
                  pt(ft(9, 7.5), ft(20, 3)),
                  pt(ft(9, 7.5), ft(20, 10)), pt(ft(9, 7.5), ft(20, 10))),
            diameter=inch(0.75), material="pex",
            insulation='1/2" fiberglass sleeve, ASJ jacket (R-3.1)',
            elevations=(ft(9, 9.8), ft(9, 9.8), ft(9, 9.8), ft(9, 7.4), ft(9, 7.4),
                        ft(9, 10.25), ft(9, 10.25), ft(9, 10.75), ft(9, 10.75), ft(22, 6)),
            serves=("FX-A-STUBATH-LAV", "FX-A-STUBATH-SH", "FX-A-STUDIO-BAR-SINK")),
]

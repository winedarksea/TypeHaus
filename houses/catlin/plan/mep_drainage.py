# haus: editable
# Catlin MEP — drainage — waste and condensate runs, the TPR discharge, the radon sump.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# Authored routing only — the user places the runs; the resolver validates them against the
# framing (joist bays, bearing lines, slab hosts) and the sheets draw them. The concrete
# penetrations these runs pass through are in plan/mep_sleeves.py; their vents are in
# plan/mep_venting.py.

from typehaus import (
    PipeRun,
    PipeSystem,
    Sump,
    SumpPump,
    ft,
    inch,
    pt,
)
from typehaus.model import m

# Basement-ceiling collector: picks up both WC sleeves, heads to the south-wall sewer
# exit. Starts at SP-M-WC1's new carrier-outlet point on the x=4' wall line (the wall-hung
# WC drops its waste inside W-M-BAE, → SLEEVES). Axis-aligned so the authored length is
# exact (4'-7" + 1' + 18' = 23'-7"); inverts give a comfortable 8"/23'-7" ≈ 0.34"/ft
# slope, well above the 1/8"/ft minimum a 4" line needs (it was sized 3" until the
# 2026-07-31 building-drain upsize), and SP-M-WC2 still ties in at the (3', 18') corner
# fitting.
# Routed 3D drains (2026-07-29 plumbing pass). Every run now carries an invert at every
# vertex (`elevations`), vertical drops are repeated plan points, and the collector rides
# y=16'-6" — a foot clear of the y=18' concrete cross walls it used to be drawn *inside*
# of — crossing them perpendicular through the WALL_SLEEVES above. The first leg falls hard
# (≈2"/ft) so the 46' kitchen branch can hold its own 1/4"/ft and still tie in from above.
#
# The sewer goes out UNDER the slab (2026-07-30, owner's call: the municipal connection is
# buried below the slab, as Minnesota does to keep it under frost). That changes where the
# building drain leaves and it is worth writing down why the geometry has only one answer:
#
#   * the foundation walls stop at -9'-0", which is the *top* of the slab, so there is no
#     wall left to pass through below it — the old exit at -2'-3" through W-B-S1 was 2'-3"
#     under grade, above MN's 42" frost line, which is the thing the owner's note rules out;
#   * the footings sit -9'-8" to -9'-0", so the drain leaves *beneath* FT-B-S1 inside a
#     protection sleeve — IRC P2604, the same relieving-arch treatment PR-G-HYDRANT-CW
#     already gets under the garage footing.
#
# So the collector stays hung at the basement ceiling where it belongs (that is where the
# upper-floor stacks arrive), and at its downstream end it drops through the slab at
# (3', 15'-6") — SP-B-SLAB-MAIN — and runs under the slab to the exit. That drop is also
# what makes every slab fixture in the basement possible: see PR-B-BATH-DRAIN and
# PR-B-SAUNA-DRAIN below. (Until 2026-07-30 there was exactly one such fixture, FX-1.)
DRAINS = [
    PipeRun(uid="CMP905AAAA", tag="PR-B-MAIN-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(6), ft(22, 7)), pt(ft(6), ft(22, 7)), pt(ft(6), ft(16, 6)),
                  pt(ft(3), ft(16, 6)), pt(ft(3), ft(15, 6)), pt(ft(3), ft(15, 6)),
                  pt(ft(3), ft(-1))),
            diameter=inch(4), material="pvc",
            # …ceiling collector… | 1' more at the ceiling | drop through the slab |
            # under-slab to the exit. The drop is at y=15'-6", not at the collector's own
            # y=16'-6" turn: 5'-6" down under the slab the pipe sits 10 5/8" below FT-B-CW's
            # bearing plane, so it needs at least that much lateral clearance from the
            # footing's 45° influence line and 16'-6" gave only 8". y=15'-6" gives 20".
            # -1.1 and -1.55 are basement-relative: -10'-1 1/5" and -10'-6 3/5" project, so
            # the 16'-6" under-slab leg falls 5.4" (0.33"/ft — a 4" line only needs
            # 0.125"/ft) and its 4" crown clears the slab underside by 5.7". Sized 4"
            # (2026-07-31): the rolled-up basement load is 42 DFU, past the 35 a 3"
            # horizontal branch carries (Table 703.2); inverts stayed put, only the crown
            # rose.
            elevations=(ft(9), ft(8), ft(7), ft(6, 11.2), ft(6, 10.9), ft(-1.1),
                        ft(-1.55)),
            serves=("FX-M-BATH1-WC", "FX-M-BATH2-WC", "FX-M-KITCH-SINK",
                    "FX-M-BATH1-LAV", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK", "FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK",
                    "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2",
                    "FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
    # Re-routed 2026-07-30 with the sink's move to the north wall, then re-routed again the
    # same day with the sink/dishwasher flip: straight down the deck sleeve's own column (no
    # jog — a jog at y=35' would run right along W-B-N1's inner concrete face) to the same
    # W-B-CE/W-B-CS2 crossings (SP-B-CE-KITCH-DR, SP-B-CS2-KITCH) and west to the main stack
    # tie-in — that route is fixed by the basement framing, not by where in the kitchen the
    # sink sits. Elevations re-solved to land on both sleeves' cast centerlines exactly, at
    # >= 0.25"/ft on every segment.
    PipeRun(uid="S0Y00EZNNG", tag="PR-B-KITCH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(28, 7), ft(35)), pt(ft(28, 7), ft(35)),
                  pt(ft(28, 7), ft(16, 6)), pt(ft(6), ft(16, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 2.9), ft(7, 8.44), ft(6, 11.57)),
            serves=("FX-M-KITCH-SINK",)),
    # BATH2's WC, at its re-pointed flange on the wet wall (→ SP-M-WC2).
    PipeRun(uid="CBPD01AAAA", tag="PR-B-WC2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(m(0.686504), m(6.14439)), pt(m(0.686504), m(6.14439)),
                  pt(m(0.686504), ft(16, 6)), pt(ft(3), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9), ft(8), ft(7, 2), ft(7)),
            serves=("FX-M-BATH2-WC",)),
    PipeRun(uid="CBPD02AAAA", tag="PR-B-LAV1-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(6), m(7.00891)), pt(ft(6), m(7.00891)), pt(ft(6), ft(22, 7))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(8, 0.2)),
            serves=("FX-M-BATH1-LAV",)),
    PipeRun(uid="CBPD03AAAA", tag="PR-B-TUB2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(7, 4), ft(19, 4.8)), pt(ft(7, 4), ft(19, 4.8)),
                  pt(ft(6), ft(19, 4.8))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 7.2)),
            serves=("FX-M-BATH2-TUB",)),
    PipeRun(uid="CBPD04AAAA", tag="PR-B-SH2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(1, 9), ft(17, 3)), pt(ft(1, 9), ft(17, 3)),
                  pt(ft(3), ft(16, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 1.2)),
            serves=("FX-M-BATH2-SH",)),
    PipeRun(uid="CBPD05AAAA", tag="PR-B-SINK2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(1), ft(16, 6)), pt(ft(1), ft(16, 6)), pt(ft(3), ft(16, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 0.6)),
            serves=("FX-M-BATH2-SINK",)),
    PipeRun(uid="CBPD06AAAA", tag="PR-B-WASH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(8), ft(20)), pt(ft(8), ft(20)), pt(ft(6), ft(20))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 8.4)),
            serves=("FX-M-LAUNDRY",)),
    # The laundry tub (2026-07-31). Down its own cast sleeve under the basin, then 5'-9" west
    # along the basement ceiling to PR-B-MAIN-DRAIN's x=6' collector — the same two-move shape
    # as PR-B-SINK2-DRAIN and PR-B-WASH-DRAIN above, because the 9" concrete deck leaves no
    # other way off this floor.
    #
    # It is the tub's trap arm as well as its branch, and that is what sizes it: the vent is
    # PR-M-WC-VENT's leg standing in W-M-BA2E at x=8', which this run passes 3'-9" from, and
    # Table 1002.2 allows 60" on 2" against 42" on 1 1/2". Falls 7.6" over the 5'-9" horizontal
    # (1.32"/ft, well over the 1/4"/ft floor) and arrives at 7'-5", about 6" above the
    # collector's interpolated invert at this y — a branch tees into the top of a horizontal
    # drain, not into its side.
    PipeRun(uid="ZK49S63X8X", tag="PR-B-LSINK-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(11, 9), ft(18, 9)), pt(ft(11, 9), ft(18, 9)),
                  pt(ft(6), ft(18, 9))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 5)),
            serves=("FX-M-LAUNDRY-SINK",)),
    # --- the two basement slab-fixture branches (2026-07-30) ---------------------------
    #
    # Every fixture on these two runs stands *on* the basement floor, so none of them can
    # reach the ceiling collector 6'-6" overhead: each drops through its cast stub and runs
    # under the slab to PR-B-MAIN-DRAIN's under-slab leg at x=3'. That leg exists because the
    # sewer goes out under the slab (the 2026-07-30 decision above); before it there was no
    # gravity drain anywhere on this floor, which is why the basement had one fixture.
    #
    # Inverts are basement-relative, so -0.7 reads as 8 2/5" below the finish floor. Both runs
    # fall a uniform 0.3"/ft — above the 1/4"/ft `mep.drain_slope` minimum for <= 3" with
    # enough margin that no segment lands on the threshold — and both stay deep enough that
    # their crowns keep the 1" of bedding `mep.under_slab_burial` wants below the slab's
    # -9'-3 1/2" underside, while arriving at the main between its invert and its crown so the
    # tie is a wye into the upper half of the pipe rather than a bottom entry.
    #
    # A note on what these runs are NOT on: neither fixture group appears in
    # PR-B-MAIN-DRAIN's `serves`. That follows the convention FX-1 set — a slab branch
    # carries its own fixtures and the main lists the stacks it collects — and since
    # 2026-07-31 the convention is load-safe: `mep.pipe_sizing` rolls every drain's load
    # up through the routed geometry (resolve/mep.py::accumulated_serves), so these 8 DFU
    # land on the main whether or not they are re-listed. That rollup is what showed the
    # building drain carrying 42 DFU against the 35 a 3" line takes, and why it is 4" now.
    #
    # The bathroom branch. Its route is the one FX-1's used, extended east into the new room:
    # 3" out of the WC's closet bend at (11'-8", 20'), west under FT-B-STR's bearing plane in
    # a protection sleeve (SP-B-STR-BATH-DR), across the mechanical room, under FT-B-CW in the
    # second sleeve (SP-B-CW-BATH-DR — FX-1's old crossing, upsized in place), then west to the
    # main at (3', 15'-6"). Going west rather than straight south is deliberate: south would
    # cross under W-B-CW2, which has no footing in params/foundations.py to hang a protection
    # sleeve on, and a crossing that depends on a missing footing is not a crossing that has
    # been detailed.
    PipeRun(uid="CBPD07AAAA", tag="PR-B-BATH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(11, 8), ft(20)), pt(ft(11, 8), ft(20)), pt(ft(7), ft(20)),
                  pt(ft(7), ft(15, 6)), pt(ft(3), ft(15, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(0), ft(-0.758), ft(-0.875), ft(-0.988), ft(-1.088)),
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    # The lavatory's own 1 1/2" arm, west along the room to the WC's branch — the same
    # relationship PR-B-LAV1-DRAIN has to the main-floor collector. It arrives at -7 5/8",
    # inside the 3" branch's upper half at that point (invert -8 5/8", crown -5 5/8").
    PipeRun(uid="CBPD09AAAA", tag="PR-B-BATH-LAV-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(17), ft(20)), pt(ft(17), ft(20)), pt(ft(11, 8), ft(20))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(1, 6), ft(-0.52), ft(-0.653)),
            serves=("FX-B-BATH-LAV",)),
    # The sauna group: the curbed pan's 2" drop at (15'-8 1/2", 12'-0 3/16"), south to the
    # wet floor's own line, west through the floor drain at (13'-6", 12'-9"), then straight
    # west under the workshop to the main. One 2" branch carries both — 4 DFU against the 6 a
    # 2" horizontal branch takes — and passes under no footing on the way: W-B-SA-W is a
    # framed partition on the slab, and the run stops 1'-8" short of FT-B-W2 while sitting only
    # 5" below its bearing plane, so it stays outside the 45° influence line.
    PipeRun(uid="CBPD08AAAA", tag="PR-B-SAUNA-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(15, 8.5), ft(12, 0.1875)), pt(ft(15, 8.5), ft(12, 0.1875)),
                  pt(ft(15, 8.5), ft(12, 9)), pt(ft(13, 6), ft(12, 9)),
                  pt(ft(3), ft(12, 9))),
            diameter=inch(2), material="pvc",
            elevations=(ft(0, 2), ft(-0.715), ft(-0.733), ft(-0.788), ft(-1.051)),
            serves=("FX-B-SAUNA-SH", "FX-B-SAUNA-FD")),
    # The floor drain's own way through the slab, and the whole of it: a floor drain has no
    # trap arm above the floor to draw — the body *is* the penetration — so this run is one
    # vertical drop from the strainer at finish floor onto the branch above. It is authored
    # separately rather than as a vertex on the branch because a mid-run vertex crosses no
    # slab, and `mep.sleeve_coverage` correctly reads a cast stub that no run passes through
    # as either a stale sleeve or a mis-routed run.
    PipeRun(uid="CBPD10AAAA", tag="PR-B-SAUNA-FD-DROP", system=PipeSystem.DRAIN,
            path=(pt(ft(13, 6), ft(12, 9)), pt(ft(13, 6), ft(12, 9))),
            diameter=inch(2), material="pvc",
            elevations=(ft(0), ft(-0.788)),
            serves=("FX-B-SAUNA-FD",)),
]

# Second-storey waste stacks, filed on ``main`` (datum 0' = the deck they drop through)
# so the elevations read as heights on the storey the pipe is actually visible from:
# +9'-9" is the second floor's underside, the negative inverts are the basement ceiling.
SECOND_DRAINS = [
    PipeRun(uid="CMPD07AAAA", tag="PR-M-S-BATH1-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(5), ft(26, 4)), pt(ft(5), ft(26, 4)),
                  pt(ft(4, 6.4), ft(17, 4.8)), pt(ft(3), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 9), ft(-1.5), ft(-1.9), ft(-2)),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    PipeRun(uid="CMPD08AAAA", tag="PR-M-S-SUITE-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(13), ft(16, 10.8)), pt(ft(13), ft(16, 10.8)),
                  pt(ft(6, 2.4), ft(16, 8.4)), pt(ft(6), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 9), ft(-1.5), ft(-1.917), ft(-1.983)),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
]

# Heat-pump condensate (plans/TODO.md §condensate): a collected 3/4" air-gap line at the
# basement ceiling, falling continuously to terminate over a receptor — never tied into the
# sanitary system. PR-M-COND-HEADS drops the two main-storey
# wall heads (master bed + living room, both by the centre line on the south wall)
# through SP-M-COND and hands off to the basement collector, which also picks up the gym
# head. EQ-S-HP1-AH's line down the second-floor chase is still undrawn — the chase route
# to this collector is a follow-up, recorded rather than guessed.
CONDENSATE_MAIN = [
    PipeRun(uid="CMPC02AAAA", tag="PR-M-COND-HEADS", system=PipeSystem.DRAIN,
            path=(pt(ft(17, 6), ft(1)), pt(ft(17, 6), ft(1)), pt(ft(27), ft(9))),
            diameter=inch(0.75), material="pvc",
            elevations=(ft(2, 6), ft(-1), ft(-1.342))),
]

# --- RM-M-LAUNDRY: the two air gaps (2026-07-31) --------------------------------------
#
# Both of this room's indirect wastes are air-gapped, and neither of them is a fitting the
# model has a name for, so they are drawn as the pipe they are and explained here.
#
# The washer's is the ordinary one: a 2" standpipe rising in W-M-BA2E's stud bay behind the
# machine, its top at 36" — inside the 18"..42"-above-the-trap band, and above the machine's
# own tub so it cannot back-siphon. The discharge hose is *dropped into* that standpipe, not
# sealed to it, and that open annulus is the air gap. A backup therefore spills out of the
# box at 36" rather than into the machine. Below the deck the trap and the branch are already
# drawn as PR-B-WASH-DRAIN; this run is the leg above the deck that was missing.
#
# The dryer's is the new one, and it is the reason this room needs no duct. A ventless
# heat-pump dryer condenses its moisture instead of blowing it outdoors; the pump lifts that
# condensate out of the machine and it has to land somewhere that is not the sanitary system.
# It lands over the laundry tub — 3'-0", which is 2" clear of the tub's 34" flood rim, twice
# the 1" a 3/4" line needs. A tub is what an air gap wants (trapped, sees water in normal
# use), the same reading that put PR-B-COND over FX-B-SAUNA-FD rather than over a lavatory
# when FX-1 was retired.
#
# The condensate line stays on this floor: PR-B-COND is a basement collector terminating over
# the sauna floor drain and there is no reason to drop 9' and cross the house when the
# receptor is 2' away. `mep.drain_slope` grades it as the DRAIN it is filed as and holds every
# segment to IRC P3005.3's 1/4"/ft, which a 22" run at 12" of fall per leg clears many times
# over. Neither run declares `serves`: a standpipe's fixture units are counted on the branch
# below it, and condensate is not a drainage fixture at all.
LAUNDRY_MAIN = [
    PipeRun(uid="P8A9ADNE6N", tag="PR-M-WASH-STANDPIPE", system=PipeSystem.DRAIN,
            path=(pt(ft(8), ft(20)), pt(ft(8), ft(20))),
            diameter=inch(2), material="pvc",
            elevations=(ft(3), ft(0)),
            wall_refs=("W-M-BA2E",)),
    # Both ends ride their fixtures: +8" in y on 2026-08-03 with the stack and the tub, when
    # W-M-CLN moved to y=18'-0". The run's shape, length and fall are unchanged — it leaves
    # the dryer's east face and turns south over the tub exactly as before.
    PipeRun(uid="5NYN0SKYSV", tag="PR-M-DRYER-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(10, 8), ft(19, 8.635)), pt(ft(11, 9), ft(19, 8.635)),
                  pt(ft(11, 9), ft(18, 11.135))),
            diameter=inch(0.75), material="pvc",
            elevations=(ft(5), ft(4), ft(3))),
]

# Re-terminated 2026-07-30, when FX-1 was retired: the collector used to run north across
# W-B-CW and air-gap over that sink's basin, and it now stops short of that wall and
# terminates over FX-B-SAUNA-FD instead — the sauna wet floor's drain (owner's call). A
# condensate air gap wants a trapped receptor that sees water in normal use, which a shower
# floor's drain is and a finished bathroom's lavatory is not.
#
# The route west across the sauna ceiling is the one this run already took (SP-B-CS-COND, the
# cast crossing of the centre wall at (18', 9'), is unchanged in plan and re-levelled to the
# new interpolated centreline); it runs above the sauna's hung drop ceiling. What is new is
# the last leg: north to y=12'-9" and then straight down in a boxed chase against W-B-SA-N,
# which is why the floor drain sits 12" off that wall rather than mid-floor — a 3/4" drop in
# the open middle of a tiled wet room is not a detail anyone would build. The air gap is 9"
# above the finish floor.
#
# 0.3"/ft of fall across all three horizontal legs — more than a condensate line needs, but
# `mep.drain_slope` grades this run as what it is filed as, a DRAIN, and holds every segment to
# IRC P3005.3's 1/4"/ft. It drains toward the receptor over its whole length either way.
CONDENSATE = [
    PipeRun(uid="CBPC01AAAA", tag="PR-B-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(27), ft(9)), pt(ft(18), ft(9)), pt(ft(13, 6), ft(9)),
                  pt(ft(13, 6), ft(12, 9)), pt(ft(13, 6), ft(12, 9))),
            diameter=inch(0.75), material="pvc",
            elevations=(ft(7, 7.9), ft(7, 5.2), ft(7, 3.85), ft(7, 2.725),
                        ft(0, 9))),
]

# --- TPR relief discharge (P2804.6.1) ------------------------------------------------
#
# The one pipe on a water heater whose job is to stop the tank exploding, and the one the
# model had no instance of until 2026-08-15: `code.P2804_water_heater_relief` reported
# UNKNOWN because EQ-B-WH named no `relief_discharge_ref`, and an unmodeled safety
# discharge is exactly the kind of gap a permit set is read for.
#
# 3/4" full-size copper, which is the valve's own outlet size: P2804.6.1 forbids reducing
# it, and forbids a valve, a trap or a rise anywhere along the run. Vertical drop from the
# valve at 3'-6" to 8" above the slab, then 1'-0" of horizontal at 2"/ft to an air gap 6"
# over the floor — the low end of P2804.6.1's 6"-24" band, and well past IRC P3005.3's
# 1/4"/ft, which `mep.drain_slope` holds every DRAIN segment to. It discharges onto the
# slab in the mechanical room by design: the room's floor falls to SM-B-RADON and there is
# no fixture below to damage, which is the same reason P2801.6 asks for no pan under it.
TPR_DISCHARGE = [
    PipeRun(uid="CBPT01AAAA", tag="PR-B-WH-TPR", system=PipeSystem.DRAIN,
            path=(pt(ft(5, 0.3), ft(32, 9.7)), pt(ft(5, 0.3), ft(32, 9.7)),
                  pt(ft(5, 0.3), ft(31, 9.7))),
            diameter=inch(0.75), material="copper",
            elevations=(ft(3, 6), ft(0, 8), ft(0, 6))),
]

# --- Radon sump + shared radon/plumbing vent riser ---------------------------------
# A sealed radon sump in the NW basement furnace room, riding RM-M-MECH's framed shaft
# closet up through the NW notch moved into RM-S-BATH1 (2026-07-28 — was at (3',33'),
# floating in open mudroom floor space with no enclosure; storeys/main.py, storeys/
# second.py). Its passive radon vent and the plumbing vent share one mechanical chase up
# to 23'-10" — under the 4:12 rake, which is at 25'-5.7" over the chase's x=1' — turn 90°
# out through the north gable siding, then 90° back up, clamped to the standing seam with
# S-5!-style clamps. The termination is derived (12" above the true roof surface at the
# riser — the deck plane plus CATLIN_ROOF's above-structure skin, resolve/
# vent_termination.py), not authored: an authored absolute cannot follow a rake, which is
# how it drifted to 33', 2' above its own ridge. Elevations are project-frame.
RADON_SUMP = [
    Sump(uid="CMSP01AAAA", tag="SM-B-RADON", position=pt(ft(1), ft(34, 6)),
         diameter=inch(18), depth=inch(24), host_ref="SL-B-FLOOR",
         sealed_cover=True, radon_vent=True, vent_ref="VR-M-RADON-VENT",
         # CKT-SUMP has existed on the panel schedule all along; the pit it feeds only
         # implied a pump. Saying it here is what puts an IfcPump/SUMPPUMP in the export,
         # joins it to the stormwater system, and gives the discharge somewhere to be
         # checked — the foundation schedule used to infer "DRAINING TO SUMP" from the mere
         # existence of this pit while every drain tile on the project said "daylight".
         pump=SumpPump(model="1/3 hp cast-iron submersible", horsepower=0.33,
                       discharge="daylight", circuit_ref="CKT-SUMP")),
]

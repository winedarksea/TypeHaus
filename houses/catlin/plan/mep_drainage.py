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

# Basement-ceiling collector: picks up both WC sleeves and heads to the south-wall sewer
# exit, riding y=16'-6" (a foot clear of the y=18' cross walls it used to be drawn inside
# of) through the WALL_SLEEVES above. Every vertex carries its own invert (`elevations`);
# the first leg falls hard (~2"/ft) so the 46' kitchen branch can hold 1/4"/ft off it.
#
# The sewer exits UNDER the slab (2026-07-30, owner's call: the municipal connection sits
# below the slab, under MN's 42" frost line). The foundation walls stop at -9'-0" (the
# slab's top), so there's no wall left below grade to exit through, and the footings sit
# -9'-8" to -9'-0", so the drain leaves *beneath* FT-B-S1 in a protection sleeve (IRC
# P2604, same treatment as PR-G-HYDRANT-CW under the garage footing). The collector stays
# hung at the ceiling (where the upper-floor stacks arrive) and drops through the slab at
# (3', 15'-6") — SP-B-SLAB-MAIN — to run under-slab to the exit. That drop is also what
# makes every basement slab fixture possible (PR-B-BATH-DRAIN, PR-B-SAUNA-DRAIN below);
# before 2026-07-30 there was exactly one such fixture, FX-1.
DRAINS = [
    #
    # ** THE LEADING VERTICAL WENT AWAY 2026-08-29. ** This run used to open with the pair
    # (6'-0", 22'-7") -> (6'-0", 22'-7"), 109 7/16" falling to 93 7/16": a 16" drop through
    # the deck that WAS FX-M-BATH1-WC's stack, back when that wall-hung bowl's
    # `drain_position` pointed at this corner instead of at its own carrier. It doesn't any
    # more (plan/fixtures.py), and nothing else drops here — PR-B-LAV1-DRAIN makes its own
    # drop at (6'-0", 22'-11 15/16") and arrives horizontally — so the segment was a 16"
    # riser under an unbroken floor. The collector now simply STARTS at the tie, and both
    # BATH1 branches (PR-B-WC1-DRAIN 3", PR-B-LAV1-DRAIN 1 1/2") come into it there: one
    # combination wye at the head of the 4" line, which is what was always going to be built.
    PipeRun(uid="CMP905AAAA", tag="PR-B-MAIN-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(6), ft(22, 7)), pt(ft(6), ft(16, 6)),
                  pt(ft(3), ft(16, 6)), pt(ft(3), ft(15, 6)), pt(ft(3), ft(15, 6)),
                  pt(ft(3), ft(-1))),
            diameter=inch(4), material="pvc",
            # The slab drop is at y=15'-6", not the collector's y=16'-6" turn: at that depth
            # the pipe needs 20" of lateral clearance from FT-B-CW's 45° influence line and
            # 16'-6" gave only 8". -1.1/-1.55 are basement-relative (-10'-1 1/5"/-10'-6 3/5"
            # project): the under-slab leg falls 5.4" (0.33"/ft, above the 0.125"/ft floor)
            # with its crown 5.7" clear of the slab underside. Sized 4" (2026-07-31): the
            # rolled-up basement load is past the 35 a 3" branch carries (Table 703.2). It
            # read 42 DFU when the upsize was made and is 48 today — the bath and laundry
            # fixtures added since. Unchanged by PR-B-WC1-DRAIN: `accumulated_serves` unions
            # the upstream subtree, and that branch's one fixture was already in this list.
            elevations=(ft(7, 9.4375), ft(6, 9.4375), ft(6, 8.6375), ft(6, 8.3375), inch(-13.2), inch(-18.6)),
            serves=("FX-M-BATH1-WC", "FX-M-BATH2-WC", "FX-M-KITCH-SINK",
                    "FX-M-BATH1-LAV", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK", "FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK",
                    "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2",
                    "FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
    # Re-routed twice 2026-07-30 (sink to north wall, then sink/dishwasher flip), then +9"
    # east 2026-08-26 with the sink: runs straight down the deck sleeve's own column,
    # through the same W-B-CE/W-B-CS2 crossings, west to the main tie-in — the route is
    # fixed by basement framing, not sink position.
    # Elevations re-solved onto both sleeves' cast centerlines at >= 0.25"/ft.
    #
    # These are BASEMENT-relative, so ft(9, 4.75) is project +3/4" — the main floor's
    # finished surface, which is the plywood top of the wood bays and, since 2026-08-21, the
    # cap top of SL-M-DECK with it (params/main_deck.py::MAIN_FINISHED_FLOOR). It read
    # ft(9, 4) while the resolver put the cap top on the datum itself; at that value the trap
    # arm now starts 3/4" INSIDE the concrete, and the drop stops being a through-crossing of
    # the band, so SP-M-KITCH goes unclaimed. This file is editable-dialect and cannot import
    # the constant, but nothing here can drift quietly: `mep.sleeve_coverage` fails the build
    # the moment this run stops passing through its sleeve.
    PipeRun(uid="S0Y00EZNNG", tag="PR-B-KITCH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(29, 4), ft(35)), pt(ft(29, 4), ft(35)),
                  pt(ft(29, 4), ft(16, 6)), pt(ft(6), ft(16, 6))),
            diameter=inch(2), material="pvc",
            # Starts on the cap's own top (+15/16" project = 9'-2 3/8" basement-relative,
            # 2026-08-23) and drops clear of the deck's SOFFIT, which is the bearing seat at
            # -13 7/16" and 1 9/16" lower than it was — a drop that stops inside the pour is
            # what `mep.sleeve_coverage` reads as a sleeve serving nothing.
            #
            # **The two horizontal legs were re-solved 2026-08-27.** The tie-in invert had
            # read 6'-11 9/16" since the run was authored, when it started 9" further west
            # and 3 1/4" higher; the 2026-08-23 re-level of the drop left it behind and the
            # last leg fell 0.243"/ft — under P3005.3's 1/4" and a real `mep.drain_slope`
            # FAIL, not a rounding one. 10'-3 3/8" of head over 41'-10" of run buys 0.245"/ft
            # if it is spent evenly, which is why BOTH numbers move: 7'-5 3/16" at the turn
            # and 6'-11 1/4" at the collector put the legs on 0.257"/ft and 0.254"/ft rather
            # than 0.253"/ft and 0.243"/ft. The end still lands 1 13/16" above
            # PR-B-MAIN-DRAIN's 6'-9 7/16" invert — a side entry into the 4" barrel's upper
            # half, which is what a 2" branch wants. Neither number is pinned to a sleeve
            # (SP-B-CS2-KITCH is matched in plan, not elevation), so this is free head to
            # spend; the drop above it is not, and did not move.
            elevations=(ft(9, 2.375), ft(7, 9.9375), ft(7, 5.1875), ft(6, 11.25)),
            serves=("FX-M-KITCH-SINK",)),
    # BATH2's WC, at its re-pointed flange on the wet wall (→ SP-M-WC2).
    # Re-pointed 2026-08-29: FX-M-BATH2-WC moved off the middle of the floor onto W-M-HS1
    # (x 2'-3" -> 2'-6", y 20'-1 3/4" -> 20'-10 5/8"), and the flange goes where the bowl
    # goes — the run's first two points ARE the fixture's drain convention, under the bowl.
    # The turn at y=16'-6" and the tie at x=3'-0" are unchanged; only the leg above the
    # turn got 9" longer.
    PipeRun(uid="CBPD01AAAA", tag="PR-B-WC2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(2, 6), ft(20, 10.615)), pt(ft(2, 6), ft(20, 10.615)),
                  pt(ft(2, 6), ft(16, 6)), pt(ft(3), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 1.4375), ft(7, 9.4375), ft(6, 11.4375), ft(6, 9.4375)),
            serves=("FX-M-BATH2-WC",)),
    # ** BATH1's WALL-HUNG WC, WHICH HAD NO DRAIN RUN OF ITS OWN UNTIL 2026-08-29. ** Its
    # waste was the first vertex of PR-B-MAIN-DRAIN: the only water closet in the house
    # discharging straight into the 4" building drain, with no branch and no size of its own.
    # Everything about that was wrong for the fixture:
    #
    #   * a wall-hung carrier connects at 3" (Geberit Duofix / TOTO DuoFit both call out
    #     Ø90 mm; Minn. R. 4714.0702 Table 702.1 gives a 1.6 gpf WC a 3" minimum trap at
    #     3.0 DFU), so 3" is the branch — see library/placeables/fixtures.py, which now
    #     carries the port that says so;
    #   * the waste left at (6'-0", 22'-7"), on W-M-BAE's axis, 46" from the china it is
    #     bolted to;
    #   * and it started 3 5/16" BELOW the finished floor, which is a closet-flange invert.
    #     A wall-hung bowl's trap is integral and above the deck: there is no flange, the
    #     stub turns down inside the carrier frame, and the pipe crosses the floor plane —
    #     ft(9, 4.75), the main floor's finished surface — on its way into the joist bay.
    #
    # Route is the house's standard two-move branch (cf. PR-B-WC2-DRAIN): drop in W-M-HS1's
    # own bay under the bowl, 6" south to clear the wall's plate line, then 3'-9 5/8" east to
    # the collector. The tie is at y=21'-10", 9" below PR-B-LAV1-DRAIN's at the head and 22"
    # above PR-B-WASH-DRAIN's at y=20'-0" — far enough from both to be separate fittings.
    # Falls 0.375"/ft on the short leg and 0.263"/ft on the long one, arriving 1/2" over the
    # main's interpolated 91.96" invert: a side entry into the 4" barrel's upper half.
    PipeRun(uid="5RGKWZZSY0", tag="PR-B-WC1-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(m(0.670778), ft(22, 4)), pt(m(0.670778), ft(22, 4)),
                  pt(m(0.670778), ft(21, 10)), pt(ft(6), ft(21, 10))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 4.75), ft(7, 9.625), ft(7, 9.4375), ft(7, 8.4375)),
            serves=("FX-M-BATH1-WC",)),
    PipeRun(uid="CBPD02AAAA", tag="PR-B-LAV1-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(6), m(7.00891)), pt(ft(6), m(7.00891)), pt(ft(6), ft(22, 7))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(9, 1.4375), ft(7, 10.0375), ft(7, 9.6375)),
            serves=("FX-M-BATH1-LAV",)),
    # 1 1/2", not the 2" this ran at until 2026-08-29. The change is the FIXTURE, not a
    # re-sizing: FX-M-BATH2-TUB became the Kohler K-5713-W1 (plan/fixtures.py), whose spec
    # drawing labels a 1 1/2" bath drain and whose required waste-and-overflow — K-7272
    # Clearflo, PROD-KOHLER-7272 — is a 1 1/2" PVC tee. The 2" was inherited from the
    # FX-TUB-60 planning allowance and described a trap this bath does not have.
    # Still one bathtub at 2 DFU, and 1 1/2" is the trap size the code tables give a
    # bathtub, so nothing about the sizing moves; only the pipe that gets ordered.
    PipeRun(uid="CBPD03AAAA", tag="PR-B-TUB2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(7, 4), ft(19, 4.8)), pt(ft(7, 4), ft(19, 4.8)),
                  pt(ft(6), ft(19, 4.8))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(9, 1.4375), ft(7, 10.0375), ft(7, 4.6375)),
            serves=("FX-M-BATH2-TUB",)),
    PipeRun(uid="CBPD04AAAA", tag="PR-B-SH2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(1, 9), ft(17, 3)), pt(ft(1, 9), ft(17, 3)),
                  pt(ft(3), ft(16, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9, 1.4375), ft(7, 10.0375), ft(6, 10.6375)),
            serves=("FX-M-BATH2-SH",)),
    PipeRun(uid="CBPD05AAAA", tag="PR-B-SINK2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(1), ft(16, 6)), pt(ft(1), ft(16, 6)), pt(ft(3), ft(16, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9, 1.4375), ft(7, 10.0375), ft(6, 10.0375)),
            serves=("FX-M-BATH2-SINK",)),
    PipeRun(uid="CBPD06AAAA", tag="PR-B-WASH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(8), ft(20)), pt(ft(8), ft(20)), pt(ft(6), ft(20))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9, 1.4375), ft(7, 10.0375), ft(7, 5.8375)),
            serves=("FX-M-LAUNDRY",)),
    # The laundry tub (2026-07-31): down its own cast sleeve, then 5'-9" west along the
    # ceiling to PR-B-MAIN-DRAIN's x=6' collector — same two-move shape as PR-B-SINK2-DRAIN/
    # PR-B-WASH-DRAIN, forced by the 9" concrete deck. This is the tub's trap arm too, sized
    # 2" (not 1 1/2") since the vent (PR-M-WC-VENT's leg at x=8') sits 3'-9" away and Table
    # 1002.2 allows 60" on 2" vs. 42" on 1 1/2". Falls 1.32"/ft, arriving ~6" above the
    # collector's invert — a top tee-in, not a side one.
    PipeRun(uid="ZK49S63X8X", tag="PR-B-LSINK-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(11, 9), ft(18, 9)), pt(ft(11, 9), ft(18, 9)),
                  pt(ft(6), ft(18, 9))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9, 1.4375), ft(7, 10.0375), ft(7, 2.4375)),
            serves=("FX-M-LAUNDRY-SINK",)),
    # --- the two basement slab-fixture branches (2026-07-30) ---------------------------
    #
    # Every fixture on these two runs stands *on* the basement floor, too low to reach the
    # ceiling collector, so each drops through its cast stub and runs under the slab to
    # PR-B-MAIN-DRAIN's under-slab leg at x=3' — possible only since the sewer moved
    # under-slab (above); before that the basement had exactly one fixture, FX-1.
    #
    # Inverts are basement-relative. Both runs fall a uniform 0.3"/ft (above `mep.drain_slope`'s
    # 1/4"/ft minimum), stay deep enough for `mep.under_slab_burial`'s 1" bedding below the
    # slab's -9'-3 1/2" underside, and tie into the main between its invert and crown (a wye
    # into the pipe's upper half, not a bottom entry).
    #
    # Neither fixture group is re-listed in PR-B-MAIN-DRAIN's `serves` — the convention is a
    # slab branch carries its own fixtures while the main lists the stacks it collects, and
    # since 2026-07-31 `mep.pipe_sizing` rolls every drain's load up through the routed
    # geometry regardless (resolve/mep.py::accumulated_serves), which is how the main's load
    # was found to be 42 DFU against a 3" line's 35, hence the 4" upsize.
    #
    # The bathroom branch reuses FX-1's old route, extended east: 3" out of the WC's closet
    # bend at (11'-8", 20'), west under FT-B-STR (SP-B-STR-BATH-DR) and FT-B-CW
    # (SP-B-CW-BATH-DR, FX-1's old crossing) to the main at (3', 15'-6"). It goes west rather
    # than straight south because south would cross under W-B-CW2, which has no footing to
    # hang a protection sleeve on.
    PipeRun(uid="CBPD07AAAA", tag="PR-B-BATH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(11, 8), ft(20)), pt(ft(11, 8), ft(20)), pt(ft(7), ft(20)),
                  pt(ft(7), ft(15, 6)), pt(ft(3), ft(15, 6))),
            diameter=inch(3), material="pvc",
            # The 0.3"/ft above is the authored fact now; the two intermediate inverts fall
            # out of it. (They moved 0.004" and 0.010" doing so — the old hand-computed
            # numbers were rounded to the thousandth of a foot, which is where that came
            # from. The stub at path[1] is the vertical drop's foot and must stay authored.)
            elevations=(ft(0), ft(-0.758), None, None, ft(-1.088)),
            slope_in_per_ft=0.3,
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    # The lavatory's own 1 1/2" arm to the WC's branch, arriving at -7 5/8" — inside the
    # 3" branch's upper half there (invert -8 5/8", crown -5 5/8").
    PipeRun(uid="CBPD09AAAA", tag="PR-B-BATH-LAV-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(17), ft(20)), pt(ft(17), ft(20)), pt(ft(11, 8), ft(20))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(1, 6), ft(-0.52), ft(-0.653)),
            serves=("FX-B-BATH-LAV",)),
    # The sauna group: curbed pan's drop, south to the floor drain at (13'-6", 12'-9"), west
    # under the workshop to the main. One 2" branch carries both (4 DFU vs. the 6 a 2" branch
    # takes) and crosses no footing — W-B-SA-W is a framed partition, and the run stops 1'-8"
    # short of FT-B-W2, outside its 45° influence line.
    PipeRun(uid="CBPD08AAAA", tag="PR-B-SAUNA-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(15, 8.5), ft(12, 0.1875)), pt(ft(15, 8.5), ft(12, 0.1875)),
                  pt(ft(15, 8.5), ft(12, 9)), pt(ft(13, 6), ft(12, 9)),
                  pt(ft(3), ft(12, 9))),
            diameter=inch(2), material="pvc",
            # As PR-B-BATH-DRAIN: the grade is authored and the intermediate inverts follow
            # (-0.004" and -0.007" off the old rounded numbers).
            elevations=(ft(0, 2), ft(-0.715), None, None, ft(-1.051)),
            slope_in_per_ft=0.3,
            serves=("FX-B-SAUNA-SH", "FX-B-SAUNA-FD")),
    # The floor drain's own drop through the slab: a floor drain has no trap arm above the
    # floor — the body *is* the penetration — so this is one vertical drop, authored
    # separately (not as a vertex on the branch) so `mep.sleeve_coverage` sees a run actually
    # passing through the cast stub rather than a stale or mis-routed sleeve.
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
            path=(pt(ft(5), ft(26, 6)), pt(ft(5), ft(26, 6)),
                  pt(ft(4, 6.4), ft(17, 4.8)), pt(ft(3), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 9), ft(-1.8333), ft(-2.2333), ft(-2.3333)),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    PipeRun(uid="CMPD08AAAA", tag="PR-M-S-SUITE-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(13), ft(16, 10.8)), pt(ft(13), ft(16, 10.8)),
                  pt(ft(6, 2.4), ft(16, 8.4)), pt(ft(6), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 9), ft(-1.8333), ft(-2.2503), ft(-2.3163)),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
]

# Heat-pump condensate (plans/TODO.md §condensate): a collected 3/4" air-gap line, falling
# continuously to a receptor, never tied into the sanitary system. PR-M-COND-HEADS drops
# the two main-storey wall heads (master bed + living room, south centre line) through
# SP-M-COND to the basement collector, which also picks up the gym head. EQ-S-HP1-AH's line
# down the second-floor chase is still undrawn — a follow-up, recorded rather than guessed.
CONDENSATE_MAIN = [
    PipeRun(uid="CMPC02AAAA", tag="PR-M-COND-HEADS", system=PipeSystem.DRAIN,
            path=(pt(ft(17, 6), ft(1)), pt(ft(17, 6), ft(1)), pt(ft(27), ft(9))),
            diameter=inch(0.75), material="pvc",
            elevations=(ft(2, 6), ft(-1.3333), ft(-1.6753))),
]

# --- RM-M-LAUNDRY: the two air gaps (2026-07-31) --------------------------------------
#
# Both of this room's indirect wastes are air-gapped, with no named fitting in the model,
# so they're drawn as the pipe they are.
#
# The washer's is ordinary: a 2" standpipe in W-M-BA2E's stud bay, top at 36" (inside the
# 18"-42" band, above the machine's tub so it can't back-siphon). The discharge hose drops
# into it rather than sealing to it — that open annulus is the air gap. Below the deck the
# trap/branch are already PR-B-WASH-DRAIN; this is the missing leg above it.
#
# The dryer's is new and is why this room needs no duct: a ventless heat-pump dryer
# condenses its moisture and the pump lifts it out, landing over the laundry tub (3'-0",
# 2" clear of the 34" flood rim) — a tub being what an air gap wants (trapped, sees water in
# normal use), same reading that put PR-B-COND over FX-B-SAUNA-FD when FX-1 was retired.
#
# The condensate line stays on this floor rather than dropping 9' to PR-B-COND, whose
# receptor is 2' away. Neither run declares `serves`: a standpipe's fixture units count on
# the branch below it, and condensate isn't a drainage fixture at all.
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

# Re-terminated 2026-07-30 when FX-1 was retired: used to air-gap over that sink's basin
# north across W-B-CW; now stops short and terminates over FX-B-SAUNA-FD instead (owner's
# call) — a condensate air gap wants a trapped receptor that sees water in normal use, which
# a shower floor drain is and a finished lavatory is not.
#
# Route is unchanged west across the sauna's hung drop ceiling (SP-B-CS-COND crossing
# re-levelled to the new centreline); what's new is the last leg north to y=12'-9" then
# straight down in a boxed chase against W-B-SA-N — the floor drain sits 12" off that wall
# rather than mid-floor because an exposed drop in a tiled wet room isn't buildable. Air gap
# is 9" above finish floor, falling 0.3"/ft (above IRC P3005.3's 1/4"/ft `mep.drain_slope`
# minimum) across all three legs.
# --- the ERV's condensate (2026-08-25) -------------------------------------------------
#
# A cold-climate ERV core makes water — on the order of a gallon or two a day at this flow
# against -15 F outdoor air — and EQ-B-ERV had no drain at all. `pan_drain_ref` on the unit
# names this run.
#
# **It shares FX-B-SAUNA-FD rather than tying into PR-B-COND, and the arithmetic is why.**
# PR-B-COND's horizontal leg is at 85" and change where it passes x=13'-6", because it is
# carrying the main storey's heads down from 7'-5 3/8". The basement's clear height is
# 8'-0 15/16" and the Broan's case is 21.6" tall, so the highest its spigot can possibly sit
# is about 75" — ten inches BELOW the tie-in. There is no gravity connection to be made, and
# the alternative the plan floated (the mechanical-room sink) still has no drain of its own,
# which is the same plans/TODO.md open item it predicted this would land on.
#
# So it runs its own line to the same receptor, dropping in the same boxed chase against
# W-B-SA-N 6" north of PR-B-COND's drop: two air gaps over one trapped floor drain that sees
# water in normal use, which is the whole reason that receptor was chosen in the first place.
# 0.3"/ft across both horizontal legs, the same grade as its neighbour and above IRC
# P3005.3's 1/4"/ft minimum.
ERV_CONDENSATE = [
    PipeRun(uid="3XVTM6HD5T", tag="PR-B-ERV-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(3, 11), ft(30, 9)), pt(ft(3, 11), ft(13, 3)),
                  pt(ft(13, 6), ft(13, 3)), pt(ft(13, 6), ft(13, 3))),
            diameter=inch(0.75), material="pvc",
            elevations=(inch(72), inch(66.75), inch(63.88), inch(9))),
]

CONDENSATE = [
    PipeRun(uid="CBPC01AAAA", tag="PR-B-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(27), ft(9)), pt(ft(18), ft(9)), pt(ft(13, 6), ft(9)),
                  pt(ft(13, 6), ft(12, 9)), pt(ft(13, 6), ft(12, 9))),
            diameter=inch(0.75), material="pvc",
            # The 0.3"/ft the comment above states, authored as the grade it is: the two
            # intermediate inverts solve to exactly the numbers that were hand-written here.
            # path[3] is the top of the boxed chase's drop and stays authored — a vertical
            # leg has no plan run to fall over.
            elevations=(ft(7, 5.3375), None, None, ft(7, 0.1625), ft(0, 9)),
            slope_in_per_ft=0.3),
]

# --- Balcony heat-pump defrost condensate (2026-08-28) -------------------------------
#
# EQ-M-HP1-OD and EQ-M-HP2-OD stand on FS-SG-DECK, which is the roof of an occupied porch.
# In heating mode a cold-climate heat pump is a condensate factory: every defrost cycle dumps
# the melted frost load out of the base pan, all winter. Until now nothing carried it.
#
# ** LETTING IT RUN ONTO THE DECK IS NOT THE CHEAP OPTION, IT IS THE EXPENSIVE ONE. ** The
# plank is watertight and falls 2" to a drip edge, so the water does leave — but it leaves by
# sheeting 8'-8" across bare aluminium at ambient, in February, on a surface D-S-DECK-W and
# D-S-DECK-E open onto. It refreezes on the way. What it does not freeze on the deck it
# freezes in the box gutter and the 3" leader, and a plugged leader overflows TR-SG-DRIP onto
# the porch below. So each unit gets a piped line to the trough instead.
#
# Filed on ``second`` (datum 10'-0" = the deck joist tops, so +2" is 1/2" above the plank).
# Straight south, on the deck's own fall, discharging over TR-SG-GUTTER's rim at -2" — an air
# gap above the trough, never into it. 0.75"/ft over the run, well past P3005.3's 1/4"/ft.
#
# ``freeze_protection`` is the whole point of the pipe and not an accessory to it: an
# untraced condensate line in this climate is a line full of ice by December, which puts the
# meltwater straight back on the deck and loses everything the pipe was for. The cable runs
# the pipe AND is specified onto the leader in notes/heat_pump_deck_mounting.md, which is the
# part this model cannot hold — TR-SG-LEADER-SE is a Downspout, not a PipeRun.
HP_CONDENSATE = [
    PipeRun(uid="SGPC01AAAA", tag="PR-S-HP1-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(9, 2), ft(-4, -2)), pt(ft(9, 2), ft(-9, -6))),
            diameter=inch(0.75), material="pvc",
            elevations=(inch(2), inch(-2)),
            freeze_protection="5 W/ft self-regulating, 120 V"),
    PipeRun(uid="SGPC02AAAA", tag="PR-S-HP2-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(17, 6), ft(-4, -1)), pt(ft(17, 6), ft(-9, -6))),
            diameter=inch(0.75), material="pvc",
            elevations=(inch(2), inch(-2)),
            freeze_protection="5 W/ft self-regulating, 120 V"),
]

# --- TPR relief discharge (P2804.6.1) ------------------------------------------------
#
# The pipe that stops the tank exploding; the model had no instance until 2026-08-15, when
# `code.P2804_water_heater_relief` reported UNKNOWN for EQ-B-WH's missing
# `relief_discharge_ref`.
#
# 3/4" full-size copper (the valve's own outlet — P2804.6.1 forbids reducing it, or any
# valve/trap/rise along the run). Drops from the valve at 3'-6" to 8" above the slab, then
# 1'-0" horizontal at 2"/ft to an air gap 6" over the floor — the low end of P2804.6.1's
# 6"-24" band. Discharges onto the mechanical-room slab by design, with no fixture below to
# damage — the same reason P2801.6 needs no pan under the tank.
#
# The run followed EQ-B-WH south on 2026-08-23 (see plan/mep_hvac.py): it hangs 2" off the
# tank's west face and drops a foot toward the door, exactly as it did in the old corner.
# **What did change is the distance to the sump.** The discharge used to land 4'-10" from
# SM-B-RADON and now lands 11'-11" from it, so "the floor falls to SM-B-RADON" is no longer
# an argument that carries itself. The air gap is what P2804.6.1 actually requires and it is
# unchanged; the slope is a slab-pour question, and the honest statement is that the pour
# has to be told to fall this way rather than assumed to. Flagged in plans/TODO.md.
TPR_DISCHARGE = [
    PipeRun(uid="CBPT01AAAA", tag="PR-B-WH-TPR", system=PipeSystem.DRAIN,
            path=(pt(ft(4, 4), ft(24)), pt(ft(4, 4), ft(24)),
                  pt(ft(4, 4), ft(23))),
            diameter=inch(0.75), material="copper",
            elevations=(ft(3, 6), ft(0, 8), ft(0, 6))),
]

# --- Radon sump + shared radon/plumbing vent riser ---------------------------------
# A sealed radon sump in the NW basement furnace room, riding RM-M-MECH's framed shaft
# closet (moved into RM-S-BATH1's notch 2026-07-28; was floating unenclosed at (3',33')).
# Its passive radon vent shares the plumbing vent's chase up to 23'-10", then turns out
# through the north gable siding and back up. ** SINCE 2026-08-29 IT JOGS EAST INSIDE THE
# ATTIC FIRST ** — at x=1'-0" the 6:12 roof underside is 20'-8 1/4" and the riser cannot
# stand up there at all, so `VentRun.chase_offset` steps it 12'-4" through the FS-ATTIC
# joist webs to x=13'-4" before it rises (mep_venting.py). The chase itself does not move
# through any storey below, and there is still no roof penetration. Termination
# is derived (12" above the true roof surface, resolve/vent_termination.py), not authored —
# an authored absolute can't follow a rake, which is how it once drifted 2' above the ridge.
RADON_SUMP = [
    Sump(uid="CMSP01AAAA", tag="SM-B-RADON", position=pt(ft(1), ft(34, 6)),
         diameter=inch(18), depth=inch(24), host_ref="SL-B-FLOOR",
         sealed_cover=True, radon_vent=True, vent_ref="VR-M-RADON-VENT",
         # CKT-SUMP was already on the panel schedule but the pit only implied a pump;
         # declaring it here puts an IfcPump/SUMPPUMP in the export and gives the
         # discharge something to check against.
         pump=SumpPump(model="1/3 hp cast-iron submersible", horsepower=0.33,
                       discharge="daylight", circuit_ref="CKT-SUMP")),
]


# --- the guest studio, 2026-08-29 -------------------------------------------------------
# ** THIS RUN IS WHY THE BATHROOM IS WHERE IT IS, NOT THE OTHER WAY ROUND. ** The attic bath was
# sited on the x=9'-7 1/2" line precisely so its stack could drop inside W-S-DC2 — the suite
# bath's own INT_2X6_STAGGERED_PLUMBING wet wall, 5 1/2" of continuous cavity with NO STUD TO
# BORE — and land on PR-M-S-SUITE-DRAIN's existing head at (13'-0", 16'-10.8"). Nothing new is
# cut through a finished storey and no new riser is bought.
#
# The route, and every leg of it is chosen: WC flange -> down into the FS-ATTIC bay -> west
# along y=20'-8" (248" = 8 + 15 x 16, a BAY CENTRE, so it runs between joists rather than
# through them) -> down 10'-0" inside W-S-DC2 -> east in the FS-S-WEST truss field to the stack
# head. The truss leg passes freely: open-web chord-to-chord is 8 7/8".
#
# ** DO NOT HAND-EDIT PR-M-S-SUITE-DRAIN.serves OR PR-B-MAIN-DRAIN.serves TO MATCH. **
# `mep.pipe_sizing` grades a drain on the geometric upstream subtree, not on authored `serves`,
# so connecting the endpoint IS the connection. What it does change is the load those two
# carry: PR-B-MAIN-DRAIN goes ~42 -> ~51 DFU on its 4" barrel, and the table is the arbiter of
# whether that still fits, not this comment. `elevations` is authored explicitly so
# `mep.drain_slope` has something to grade; 1/4"/ft is trivially available on both legs.
# ** FILED ON ``main`` (datum 0'-0"), like SECOND_DRAINS above and for the same reason: **
# these are project elevations, so +19'-4" is the attic floor's underside and +9'-9" is the
# second floor's, where PR-M-S-SUITE-DRAIN's head is waiting. Filed on ``attic`` until
# 2026-08-29, which resolved the whole stack 20'-0" high, hanging over the roof.
STUDIO_DRAINS = [
    # ** THE DOG-LEG IS GONE (2026-08-30) AND THAT IS THE POINT OF THE NEW WC STATION. **
    # 2026-08-29 pushed the flange out to (13'-6", 21'-4") — off any bay centre — so this run
    # had to jog south 8" before it could turn west, and the stack head at (9'-7 1/2", 20'-8")
    # stayed where it was. Putting the water closet back on the wet wall (plan/fixtures.py)
    # let its c/l land on y=19'-4", 232" = 8 + 14 x 16, a bay centre in its own right: the
    # flange now drops straight between joists and the run is flange -> west -> down, three
    # points. The drop moves one bay south with it, from (9'-7 1/2", 20'-8") to
    # (9'-7 1/2", 19'-4"), which is still deep inside W-S-DC2 (y 15'-11"..22'-4"), and it now
    # clears the two supply risers at y 20'-6"/21'-0" instead of standing between them.
    # The lavatory's 1 1/2" arm comes south off the north wall into the same west leg.
    PipeRun(uid="HTZ1RGAGXP", tag="PR-A-STUBATH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(11, 0.875), ft(19, 4)), pt(ft(9, 7.5), ft(19, 4)),
                  pt(ft(13), ft(16, 10.8))),
            diameter=inch(3), material="pvc",
            elevations=(ft(19, 4), ft(19, 3.5), ft(9, 9)),
            serves=("FX-A-STUBATH-WC", "FX-A-STUBATH-LAV", "FX-A-STUBATH-SH")),
    # ** THE BAR IS NO LONGER BACK-TO-BACK WITH THE BATH (2026-08-29). ** It moved to
    # W-A-C2's west face at (17'-0", 16'-8") because the 6:12 rake left nothing usable at the
    # wet wall, so its 2" branch now crosses the joist field west on the y=16'-8" bay centre
    # (200" = 8 + 12 x 16) and turns north to the same stack head. Seven feet of extra 2" PVC
    # in a bay it shares with nothing — the price of a counter you can stand at.
    # ** THE HEAD MOVED UNDER THE BOWL ON 2026-08-30 AND GAINED A 4" TAILPIECE LEG. ** The
    # sink's `drain_position` had drifted 4 3/8" east of the bowl and 9" north of it
    # (plan/fixtures.py), so this run started under nothing at all. Straightening the sink
    # onto W-A-C2's face and clear of W-A-BATH-S's 17'-1 5/8" south face lands its c/l on
    # y 16'-4", which is 4" off the 16'-8" bay centre — so the arm drops at the bowl, turns
    # 4" north onto the bay, and only then runs west as before. The 16'-8" leg and its
    # 1/4"/ft are untouched; the new 1/4" over the 4" leg is 0.75"/ft.
    # Its north leg now ends at (9'-7 1/2", 19'-4") with the stack, not at the old 20'-8".
    PipeRun(uid="ZY2V3KWMVK", tag="PR-A-BAR-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(17, 1.625), ft(16, 4)), pt(ft(17, 1.625), ft(16, 8)),
                  pt(ft(9, 7.5), ft(16, 8)), pt(ft(9, 7.5), ft(19, 4))),
            diameter=inch(2), material="pvc",
            # 2" over the 7'-11" west leg and 1" over the 4'-0" north one — 1/4"/ft on both,
            # which `mep.drain_slope` grades segment by segment. The whole profile sits inside
            # FS-ATTIC's 11 7/8" joist band (19'-0 1/8"..20'-0"), through the webs.
            elevations=(ft(19, 7.75), ft(19, 7.5), ft(19, 5.5), ft(19, 4.5)),
            serves=("FX-A-STUDIO-BAR-SINK",)),
]

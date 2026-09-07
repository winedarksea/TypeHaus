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
# exit, riding y=16'-6" (a foot clear of the y=18' cross walls) through the WALL_SLEEVES
# above. Every vertex carries its own invert (`elevations`);
# the first leg falls hard (~2"/ft) so the 46' kitchen branch can hold 1/4"/ft off it.
#
# The sewer exits UNDER the slab (owner's call: the municipal connection sits below the
# slab, under MN's 42" frost line). The foundation walls stop at -9'-0" (the slab's top), so
# there's no wall left below grade to exit through, and the footings sit -9'-8" to -9'-0",
# so the drain leaves *beneath* FT-B-S1 in a protection sleeve (IRC P2604, same treatment as
# PR-G-HYDRANT-CW under the garage footing). The collector stays hung at the ceiling (where
# the upper-floor stacks arrive) and drops through the slab at (3', 15'-6") —
# SP-B-SLAB-MAIN — to run under-slab to the exit. That drop is also what makes every
# basement slab fixture possible (PR-B-BATH-DRAIN, PR-B-SAUNA-DRAIN below).
DRAINS = [
    #
    # The collector STARTS at the tie (6'-0", 22'-7"); nothing drops through the deck here.
    # Both BATH1 branches (PR-B-WC1-DRAIN 3", PR-B-LAV1-DRAIN 1 1/2") come into it there: one
    # combination wye at the head of the 4" line.
    PipeRun(uid="CMP905AAAA", tag="PR-B-MAIN-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(6), ft(22, 7)), pt(ft(6), ft(16, 6)),
                  pt(ft(3), ft(16, 6)), pt(ft(3), ft(15, 6)), pt(ft(3), ft(15, 6)),
                  pt(ft(3), ft(-1))),
            diameter=inch(4), material="pvc",
            # The slab drop is at y=15'-6", not the collector's y=16'-6" turn: at that depth
            # the pipe needs 20" of lateral clearance from FT-B-CW's 45° influence line and
            # 16'-6" gave only 8". -1.1/-1.55 are basement-relative (-10'-1 1/5"/-10'-6 3/5"
            # project): the under-slab leg falls 5.4" (0.33"/ft, above the 0.125"/ft floor)
            # with its crown 5.7" clear of the slab underside. Sized 4": the
            # rolled-up basement load is past the 35 a 3" branch carries (Table 703.2), at
            # 48 DFU. Unchanged by PR-B-WC1-DRAIN: `accumulated_serves` unions
            # the upstream subtree, and that branch's one fixture was already in this list.
            elevations=(ft(7, 9.4375), ft(6, 9.4375), ft(6, 8.6375), ft(6, 8.3375), inch(-13.2), inch(-18.6)),
            serves=("FX-M-BATH1-WC", "FX-M-BATH2-WC", "FX-M-KITCH-SINK",
                    "FX-M-BATH1-LAV", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK", "FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK",
                    "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2",
                    "FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
    # ** REROUTED 2026-09-07: NORTH INTO THE DECK, THEN THE WHOLE WIDTH OF THE HOUSE. **
    # It used to go south down x=29'-4" and west along y=16'-6", and `mep.run_in_finished_
    # volume` measured what that cost: **14.5 ft hanging 6.7" into RM-B-PLAY-N and 9.1 ft
    # hanging 9.9" into RM-B-GYM.** Not a routing mistake so much as an unavoidable one —
    # RM-B-PLAY-N's finished ceiling resolves at -14 1/16" while SL-M-DECK's soffit is at
    # -13 7/16", a furred plane 5/8" UNDER the slab, so anything hung beneath that deck is
    # in the theater by construction. Rerouting inside the basement cannot fix that.
    #
    # ** THE FIX IS TO STAY IN THE DECK, NOT UNDER IT. ** SL-M-DECK is a LiteDeck EPS
    # stay-in-place form: 4 3/8" of cast cover over a 10" foam beam whose ribs run in x, the
    # same direction this leg travels. So the drain drops through the cap only, turns west at
    # -7 1/2" inside the foam — a routed channel between ribs, which is what an EPS deck is
    # sold for — and stays there for the whole 11'-4" over the theater, coming out at
    # -10 3/4" with its bottom still 2 11/16" above the foam's soffit. Zero exposure in
    # RM-B-PLAY-N. `resolve/mep_queries.concrete_bands` is what lets the model say this:
    # before it, `concrete_crossings` read the deck as one 14 3/8" prism and called a pipe
    # lying in the foam an unsleeved crossing of the pour.
    #
    # ** WEST OF x=18' IT IS EXPOSED, AND THAT IS THE OWNER'S CALL. ** Past the deck edge it
    # runs in FS-M-STAIR's joist bay at y=35'-0", drops out of it about halfway across, and
    # crosses RM-B-STAIR 1 3/8" below that room's -12 1/2" ceiling — under the 3" grazing
    # tolerance, so `run_in_finished_volume` does not report it, and a stair is somewhere a
    # pipe may show. It then bores W-B-STR and W-B-ESS-W (both framed: a hole on the day, no
    # cast sleeve) and crosses RM-B-ESS. ** THAT IS A BATTERY CLOSET BEHIND A TYPE X
    # MEMBRANE ** — the owner accepted the crossing on 2026-09-07, and both penetrations
    # need a listed firestop to keep the membrane's rating. Nothing in this engine grades
    # that; this comment is the record.
    #
    # ** y=35'-0", NOT 35'-6". ** The north foundation walls W-B-N1..N4 are 12 3/16" on the
    # y=36' axis, so their inner face is y=35'-5 7/8" and a 2" pipe at 35'-6" is INSIDE the
    # pour — three unsleeved crossings, and the wall-cover exemption in
    # `run_in_finished_volume` would have hidden the stair leg while it was there. Six inches
    # south is the whole difference.
    #
    # Elevations re-solved onto SP-M-KITCH's cast centerline at >= 0.25"/ft.
    #
    # These are BASEMENT-relative, so ft(9, 4.75) is project +3/4" — the main floor's
    # finished surface, which is the plywood top of the wood bays and the cap top of
    # SL-M-DECK with it (params/main_deck.py::MAIN_FINISHED_FLOOR). At ft(9, 4) — the datum
    # itself — the trap arm starts 3/4" INSIDE the concrete and the drop stops being a
    # through-crossing of the band, so SP-M-KITCH goes unclaimed. This file is
    # editable-dialect and cannot import the constant, but nothing here can drift quietly:
    # `mep.sleeve_coverage` fails the build the moment this run stops passing through its
    # sleeve.
    PipeRun(uid="S0Y00EZNNG", tag="PR-B-KITCH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(29, 4), ft(35)), pt(ft(29, 4), ft(35)),
                  pt(ft(18), ft(35)), pt(ft(10), ft(35)),
                  pt(ft(6), ft(35)), pt(ft(4, 6), ft(35)),
                  pt(ft(4, 6), ft(16, 6))),
            diameter=inch(2), material="pvc",
            # Starts on the cap's own top (+15/16" project = 9'-2 3/8" basement-relative) and
            # drops clear of the deck's SOFFIT, the bearing seat at -13 7/16" — a drop that
            # stops inside the pour is what `mep.sleeve_coverage` reads as a sleeve serving
            # nothing.
            #
            # ** THE PROFILE IS NOT UNIFORM, AND THAT IS THE POINT. ** 8'-5 3/16" of head
            # over 43'-4" would allow 0.235"/ft spread evenly — under the minimum — so the
            # head is spent where it is worth something instead. The theater leg takes the
            # least it legally can (3 1/16" over 11'-4", 0.270"/ft) to keep the pipe inside
            # the foam for its whole length; the stair leg 0.273"/ft; and the last leg, once
            # the run is over RM-B-FURNACE and RM-B-WORKSHOP where nothing cares how low it
            # hangs, takes 13 5/8" over 19'-0" at 0.717"/ft.
            #
            # The end lands at 6'-9 1/8", 1/16" over PR-B-MAIN-DRAIN's interpolated invert at
            # x=4'-6" — a side entry into the 4" barrel's upper half, which is what a 2"
            # branch wants, and inside `drain_tie_ins`' 1" tolerance so the load still rolls
            # up. It ties on the main's y=16'-6" leg rather than at its (6'-0") head, which
            # is 1'-6" of 2" PVC saved and one fitting fewer.
            elevations=(ft(9, 2.375), ft(8, 5.9375), ft(8, 2.6875), ft(8, 0.5),
                        ft(7, 11.25), ft(7, 10.75), ft(6, 9.125)),
            serves=("FX-M-KITCH-SINK",)),
    # BATH2's WC, at its flange on the wet wall (→ SP-M-WC2), x 2'-6" y 20'-10 5/8" — the
    # run's first two points ARE the fixture's drain convention, under the bowl.
    PipeRun(uid="CBPD01AAAA", tag="PR-B-WC2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(2, 6), ft(20, 10.615)), pt(ft(2, 6), ft(20, 10.615)),
                  pt(ft(2, 6), ft(16, 6)), pt(ft(3), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 1.4375), ft(7, 9.4375), ft(6, 11.4375), ft(6, 9.4375)),
            serves=("FX-M-BATH2-WC",)),
    # ** BATH1's WALL-HUNG WC, ON ITS OWN BRANCH, NOT PR-B-MAIN-DRAIN'S FIRST VERTEX. **
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
    # 1 1/2": FX-M-BATH2-TUB is the Kohler K-5713-W1 (plan/fixtures.py), whose spec
    # drawing labels a 1 1/2" bath drain and whose required waste-and-overflow — K-7272
    # Clearflo, PROD-KOHLER-7272 — is a 1 1/2" PVC tee.
    # One bathtub at 2 DFU, and 1 1/2" is the trap size the code tables give a
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
    # The laundry tub: down its own cast sleeve, then 5'-9" west along the
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
    # --- the two basement slab-fixture branches ---------------------------------------
    #
    # Every fixture on these two runs stands *on* the basement floor, too low to reach the
    # ceiling collector, so each drops through its cast stub and runs under the slab to
    # PR-B-MAIN-DRAIN's under-slab leg at x=3'.
    #
    # Inverts are basement-relative. Both runs fall a uniform 0.3"/ft (above `mep.drain_slope`'s
    # 1/4"/ft minimum), stay deep enough for `mep.under_slab_burial`'s 1" bedding below the
    # slab's -9'-3 1/2" underside, and tie into the main between its invert and crown (a wye
    # into the pipe's upper half, not a bottom entry).
    #
    # Neither fixture group is re-listed in PR-B-MAIN-DRAIN's `serves` — the convention is a
    # slab branch carries its own fixtures while the main lists the stacks it collects;
    # `mep.pipe_sizing` rolls every drain's load up through the routed geometry regardless
    # (resolve/mep.py::accumulated_serves).
    #
    # The bathroom branch: 3" out of the WC's closet bend at (12', 24'-1 5/8"), straight
    # south under the bathroom and W-B-CW2 to y=15'-6", then west under the workshop to the
    # main's slab drop at (3', 15'-6"). It crosses no footing at all: W-B-CW2 is a framed
    # partition on the slab and FT-B-CW / FT-B-STR2 were retired with the pours they sat
    # under, so there is nothing on this route to sleeve through.
    #
    # ** THE GRADE IS 1/4"/ft, NOT 0.3, AND THE ROTATED ROOM IS WHY. ** The WC moved to the
    # bath's north end, which is 4'-1 5/8" further from the main than the old west-end
    # station — 17.64 ft of plan run against 13.17. At 0.3"/ft that eats 5.3" of the 5.7"
    # the main's crown has under the slab and the branch arrives BELOW the 4" line's invert.
    # 1/4"/ft is IRC P3005.3's published minimum for 3" and above (and twice the 1/8"/ft
    # `mep.drain_slope` floor), and it lands the branch at -13" against the main's -13.2"
    # invert — the same hair of margin the old route had.
    PipeRun(uid="CBPD07AAAA", tag="PR-B-BATH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(12), inch(289.625)), pt(ft(12), inch(289.625)),
                  pt(ft(12), ft(15, 6)), pt(ft(3), ft(15, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(0), inch(-8.6), None, inch(-13.01)),
            slope_in_per_ft=0.25,
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    # The lavatory's own 1 1/2" arm. The vanity sits on the same x=12' line as the WC, so
    # its trap drops straight onto the 3" branch below it — one vertical leg with no
    # horizontal arm under the slab at all, authored as its own run (not a vertex on the
    # branch) so `mep.sleeve_coverage` sees a run passing through SP-B-BATH-LAV.
    # It arrives at -8", inside the 3" branch's upper half there (invert -9 15/16",
    # crown -6 7/16").
    PipeRun(uid="CBPD09AAAA", tag="PR-B-BATH-LAV-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(12), inch(224.375)), pt(ft(12), inch(224.375))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(1, 6), inch(-8)),
            serves=("FX-B-BATH-LAV",)),
    # The sauna group: the curbed pan's drop at the NE corner, west along the pan's own
    # centre line to the floor drain at (13'-6", 8'-2 3/16"), then south to y=4'-0" and west
    # under the sauna and the workshop to the main. One 2" branch carries both (4 DFU vs.
    # the 6 a 2" branch takes) and crosses no footing — W-B-SA-W is a framed partition, and
    # the run stops at x=3'-0", 2'-2" clear of FT-B-W2's edge and outside its 45° influence
    # line. It ties into the main's under-slab leg at -13 3/4" — it was -13 9/16" until
    # W-B-SA-N went north on 2026-09-05 and lengthened the drain leg 7"; the tie-in follows
    # the grade, not the other way round — between that pipe's -16 15/16" invert and its
    # -12 15/16" crown.
    PipeRun(uid="CBPD08AAAA", tag="PR-B-SAUNA-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(inch(191.75), inch(98.1875)), pt(inch(191.75), inch(98.1875)),
                  pt(ft(13, 6), inch(98.1875)), pt(ft(13, 6), ft(4)),
                  pt(ft(3), ft(4))),
            diameter=inch(2), material="pvc",
            # As PR-B-BATH-DRAIN: the grade is authored and the intermediate inverts follow.
            elevations=(ft(0, 2), inch(-8.58), None, None, inch(-13.728)),
            slope_in_per_ft=0.3,
            serves=("FX-B-SAUNA-SH", "FX-B-SAUNA-FD")),
    # The floor drain's own drop through the slab: a floor drain has no trap arm above the
    # floor — the body *is* the penetration — so this is one vertical drop, authored
    # separately (not as a vertex on the branch) so `mep.sleeve_coverage` sees a run actually
    # passing through the cast stub rather than a stale or mis-routed sleeve.
    PipeRun(uid="CBPD10AAAA", tag="PR-B-SAUNA-FD-DROP", system=PipeSystem.DRAIN,
            path=(pt(ft(13, 6), inch(98.1875)), pt(ft(13, 6), inch(98.1875))),
            diameter=inch(2), material="pvc",
            elevations=(ft(0), inch(-9.324)),
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
            # ** THE HEAD IS ABOVE THE SECOND FLOOR NOW, NOT UNDER IT. ** It was 9'-9" —
            # inside the truss depth — for as long as this stack had no branch piping at
            # all. PR-M-S-VANITY-DRAIN is a wall arm in W-S-BD-N's cavity at 10'-2 9/16",
            # and a stack tops out at its highest inlet, so the barrel rises 6" further to
            # 10'-3" and every other branch ties onto the vertical below it.
            elevations=(ft(10, 3), ft(-1.8333), ft(-2.2333), ft(-2.3333)),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # ** THE HEAD IS 1 1/2" LOWER THAN ITS BATH1 TWIN, AND DELIBERATELY. ** The attic bath's
    # branch has to fall 1/4"/ft over the 4.161 ft from its drop inside W-S-DC2 to this head,
    # and its 3" crown has to stay under FS-S-WEST's 10'-0" deck underside. At 9'-9" those two
    # cannot both hold. At 9'-7 1/2" the branch drops to 9'-8 3/4", falls 0.30"/ft, and crowns
    # 1 3/4" clear. Nothing else reads this number and the drop below it is vertical, so the
    # cost of the move is 1 1/2" of stack.
    PipeRun(uid="CMPD08AAAA", tag="PR-M-S-SUITE-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(13), ft(16, 10.8)), pt(ft(13), ft(16, 10.8)),
                  pt(ft(6, 2.4), ft(16, 8.4)), pt(ft(6), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 7.5), ft(-1.8333), ft(-2.2503), ft(-2.3163)),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
]

# --- the second storey's bathroom branches ---------------------------------------------------
#
# ** UNTIL 2026-09-07 THIS STOREY HAD TWO STACKS AND NO BRANCH PIPING AT ALL. ** Six fixtures
# named PR-M-S-BATH1-DRAIN or PR-M-S-SUITE-DRAIN in `serves` and the nearest pipe to any of
# them was 37"-79" away; the suite bath's water closet read as undrained in the 3D view
# because it was. `mep.fixture_drain_reach` is the check that says so out loud.
#
# ** EVERY LEG IS IN FS-S-WEST, AND THAT IS WHY THE WEST HALF IS TRUSSES. ** `params/
# second_deck.py` chose 11 7/8" open-web floor trusses west of x=18' precisely so services
# cross *through* the webs. So a leg running in y (across the trusses) passes freely, and a
# leg running in x has to lie in a bay: chords are 3 1/2" wide on the 16" grid, so the clear
# zone between two lines is 12 1/2" and a 3" pipe on a bay centre has 4 3/4" either side.
# ** The one thing the webs do NOT forgive is depth: ** chord-to-chord is 8 7/8", so a
# crossing leg's OUTSIDE has to stay inside 109 5/8"..118 1/2" absolute. That single number
# sets every starting invert below. A leg riding a bay may use the full 108 1/8"..120".
#
# ** BOTH STACK HEADS MOVED, AND FOR OPPOSITE REASONS. ** PR-M-S-BATH1-DRAIN's head went UP
# to 10'-3", into W-S-BD-N's cavity, because the vanity alcove's arm is a wall arm above the
# floor and a stack has to top out at its highest inlet. PR-M-S-SUITE-DRAIN's stayed at
# 9'-7 1/2" (it took its 1 1/2" drop on 2026-09-07 with PR-A-STUBATH-DRAIN's dog-leg fix) and
# the attic branch now lands 2 1/2" above the collector rather than on top of it, so the
# two are separate inlets on one vertical instead of a double fitting at a point.
#
# ** FILED ON ``main``, like SECOND_DRAINS and STUDIO_DRAINS, ** so every elevation here is
# project-absolute: 10'-0 3/4" is the second storey's finished floor, 10'-0" its deck, and
# 9'-0 1/8" the underside of the trusses.
SECOND_BRANCH_DRAINS = [
    # ** THE HALL BATH'S 3" COLLECTOR. THE CLOSET BEND IS OFFSET AND THAT IS NOT A ROUNDING. **
    # FX-S-BATH1-WC's flange is at y=365.29" and the truss line at 368" occupies
    # 366.25"..369.75", so a 3" pipe dropping on the flange centre would notch a chord by
    # 0.54". A closet bend is a fitting with 5 1/4" of translation in it: the pipe leaves the
    # flange at the floor plane and is on the y=360" bay centre 5 1/4" later, 3'-0" below.
    # That first leg falls 8.5"/ft, which is a bend and not a slant — `mep.drain_offset_
    # geometry` grades it on the conjunction and 3 3/4" of fall is nowhere near its 18".
    # Then east on the bay to x=5'-0" and south across the trusses to the stack.
    PipeRun(uid="K28BQ29KCW", tag="PR-M-S-BATH1-WC-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(m(0.560313), m(9.2783)), pt(m(0.560313), ft(30)),
                  pt(ft(5), ft(30)), pt(ft(5), ft(26, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(10, 0.75), ft(9, 9), ft(9, 6.625), ft(9, 4)),
            serves=("FX-S-BATH1-WC",)),
    # The tub-shower's 1 1/2" waste: straight down in its own bay at the west end, then south
    # across the trusses to the collector at (3'-3 1/4", 30'-0"). It arrives 1/16" over the
    # collector's own invert there — a side entry, which is what `drain_tie_ins` wants and
    # what a wye is. 1 1/2" because the tub's waste-and-overflow is 1 1/2" and that is the
    # trap size the table gives a bathtub (cf. PR-B-TUB2-DRAIN).
    PipeRun(uid="0W45BR6619", tag="PR-M-S-BATH1-TUB-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(inch(39.25), inch(409.5)), pt(inch(39.25), inch(409.5)),
                  pt(inch(39.25), ft(30))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(10, 0.75), ft(9, 9.75), ft(9, 7.9375)),
            serves=("FX-S-BATH1-SH",)),
    # The 48" vanity's 1 1/2" arm. The drop is at y=31'-0" rather than on the bowl's own
    # 369.88" for the same reason as the water closet's: 369.88" is 0.13" off the 368" truss
    # line's south face. y=372" is the 369.75"..382.25" bay, 2 1/8" from the bowl and exactly
    # where PR-S-BATH1-VENT already takes off. West on that bay to x=5'-0", then 1'-0" south
    # onto the collector's corner.
    PipeRun(uid="E9TA1G01B8", tag="PR-M-S-BATH1-LAV-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(10), ft(31)), pt(ft(10), ft(31)),
                  pt(ft(5), ft(31)), pt(ft(5), ft(30))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(10, 0.75), ft(9, 9.75), ft(9, 7.1875), ft(9, 6.6875)),
            # No `wall_ref`: only the first vertex is in W-S-BA-E1B, and the drop leaves
            # the wall's own z band the moment it passes the deck at 10'-0". `wall_ref`
            # claims EVERY segment is in that wall, which this run cannot honestly say.
            serves=("FX-S-BATH1-LAV",)),
    # ** THE DOUBLE VANITY'S ARM NEVER LEAVES THE WALL. ** W-S-BD-N is
    # INT_2X6_STAGGERED_PLUMBING — 5 1/2" of continuous cavity with no stud to bore — and
    # both bowls sit on it, so their 1 1/2" arm runs east inside it at 2 3/4" above the
    # finished floor and lands on the stack head at 10'-2 9/16". That is what took the head
    # up to 10'-3": a stack tops out at its highest inlet, and this is it. Both lavatories
    # are named because both drain here; LAV2 at x=52 3/8" already sat 7 5/8" from the head
    # and passed `fixture_drain_reach` for a reason that was true by accident.
    PipeRun(uid="WJ1ZY1QTET", tag="PR-M-S-VANITY-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(inch(22.375), ft(26, 6)), pt(inch(52.375), ft(26, 6)),
                  pt(ft(5), ft(26, 6))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(10, 3.5), ft(10, 2.75), ft(10, 2.5625)),
            serves=("FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2"), wall_ref="W-S-BD-N"),
    # ** THE SUITE BATH'S 3" COLLECTOR. ** The water closet is floor-drained and its flange
    # at (134.81", 250.625") lands cleanly in the 241.75"..254.25" bay, so this one drops
    # vertically — no offset bend needed. South across the trusses to the y=16'-10.8" bay the
    # stack head sits in, then 1'-9 3/16" east onto it. It starts at 9'-8 1/2" so its 3"
    # crown clears the truss webs' 118 1/2" ceiling by 1/2", and lands at 9'-4" on the stack's
    # vertical, 3 1/2" below where the attic branch enters it.
    PipeRun(uid="885X4850FE", tag="PR-M-S-SUITE-WC-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(inch(134.81), inch(250.625)), pt(inch(134.81), inch(250.625)),
                  pt(inch(134.81), ft(16, 10.8)), pt(ft(13), ft(16, 10.8))),
            diameter=inch(3), material="pvc",
            elevations=(ft(10, 0.75), ft(9, 8.5), ft(9, 5.375), ft(9, 4)),
            serves=("FX-S-SUITEBATH-WC",)),
    # The 30" vanity's 1 1/2" arm: down inside W-S-SN3 (the staggered wet wall this bath was
    # laid out around), south across one truss, then west on the y=246" bay to the collector.
    # The tie is at y=246" and not at the 240" truss line, which is where the arithmetic
    # first put it — a wye centred on a chord is not a fitting anybody can install.
    PipeRun(uid="HNBWJNTS71", tag="PR-M-S-SUITE-LAV-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(inch(165.5), ft(22, 4)), pt(inch(165.5), ft(22, 4)),
                  pt(inch(165.5), inch(246)), pt(inch(134.81), inch(246))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(10, 0.75), ft(9, 9.5625), ft(9, 9), ft(9, 8.25)),
            serves=("FX-S-SUITEBATH-LAV",)),
    # The tub-shower's 1 1/2" waste, from the north-end waste-and-overflow at
    # (197.615", 261.125"): down its own bay, south under the tub across three trusses, then
    # west on the y=19'-0" bay to the collector 1'-6" south of the vanity arm's tie. Two
    # separate wyes on the 3", 18" apart, rather than one fitting taking both.
    PipeRun(uid="WVNA8G8ZHX", tag="PR-M-S-SUITE-TUB-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(inch(197.615), inch(261.125)), pt(inch(197.615), inch(261.125)),
                  pt(inch(197.615), ft(19)), pt(inch(134.81), ft(19))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(10, 0.75), ft(9, 9.4375), ft(9, 8.625), ft(9, 7.0625)),
            serves=("FX-S-SUITEBATH-TUBSH",)),
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

# --- RM-M-LAUNDRY: the two air gaps -----------------------------------------------------
#
# Both of this room's indirect wastes are air-gapped, with no named fitting in the model,
# so they're drawn as the pipe they are.
#
# The washer's is ordinary: a 2" standpipe in W-M-BA2E's stud bay, top at 36" (inside the
# 18"-42" band, above the machine's tub so it can't back-siphon). The discharge hose drops
# into it rather than sealing to it — that open annulus is the air gap. Below the deck the
# trap/branch are already PR-B-WASH-DRAIN; this is the missing leg above it.
#
# The dryer's is why this room needs no duct: a ventless heat-pump dryer
# condenses its moisture and the pump lifts it out, landing over the laundry tub (3'-0",
# 2" clear of the 34" flood rim) — a tub being what an air gap wants (trapped, sees water in
# normal use), the same reading that put PR-B-COND over FX-B-SAUNA-FD.
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
    # Both ends ride their fixtures — it leaves the dryer's east face and turns south over
    # the tub.
    PipeRun(uid="5NYN0SKYSV", tag="PR-M-DRYER-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(10, 8), ft(19, 8.635)), pt(ft(11, 9), ft(19, 8.635)),
                  pt(ft(11, 9), ft(18, 11.135))),
            diameter=inch(0.75), material="pvc",
            elevations=(ft(5), ft(4), ft(3))),
]

# Terminates over FX-B-SAUNA-FD, owner's call — a condensate air gap wants a trapped
# receptor that sees water in normal use, which a shower floor drain is and a finished
# lavatory is not.
#
# Route: west across the sauna's hung drop ceiling (SP-B-CS-COND crossing), then north to
# the drain and straight down in a boxed chase 1'-9" off W-B-SA-N. Air gap is 9" above
# finish floor, falling 0.3"/ft (above IRC P3005.3's 1/4"/ft `mep.drain_slope` minimum)
# across all three legs. The drop point sits over FX-B-SAUNA-SH's centre line — an indirect
# waste has to discharge over its receptor.
# --- the ERV's condensate ---------------------------------------------------------------
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
# So it runs its own line to the same receptor, dropping in the same boxed chase 6" north of
# PR-B-COND's drop: two air gaps over one trapped floor drain that sees
# water in normal use, which is the whole reason that receptor was chosen in the first place.
# 0.3"/ft across both horizontal legs, the same grade as its neighbour and above IRC
# P3005.3's 1/4"/ft minimum.
#
# ** THE NORTH-SOUTH LEG MUST STAY CLEAR OF D-B-FURN'S ROUGH OPENING. ** At x=3'-11" it
# would pass through W-B-CW at y=18'-0", the furnace room door (RO x 3'-4"..6'-0", head
# 6'-8"), 68" above the sill — a 3/4" PVC line across the top of a doorway with nothing to
# hang it from and a header it cannot be bored into.
#
# ** THE FIX IS HORIZONTAL, BECAUSE THIS LINE FALLS. ** The usual answer to a run in an
# opening is to carry it over the head; the head is at 80" basement-relative and the run
# STARTS at 72", at the Broan's condensate spigot. There is no gravity route over it, and
# there is no re-levelling either — the whole point of the run is 0.3"/ft of continuous fall
# to FX-B-SAUNA-FD, above IRC P3005.3's 1/4"/ft. So the leg moves west out of the opening
# and everything else stays.
#
# ** x=2'-11" IS A MEASURED BAY, AND x=2'-9" — THE OBVIOUS GUESS — IS NOT. ** W-B-CW
# resolves studs at x=0'-8 3/4", 1'-4", 2'-8" and 6'-9", with the door's king at 3'-0 3/4".
# That leaves a 3 1/4" bay between the 2x8 stud's east face (2'-8 3/4") and the king's west
# face (3'-0"), and a 14 1/2" bay west of it. 2'-9" lands 1/4" off the stud face, which a
# 1.05"-OD 3/4" PVC pipe cannot clear — it would be bored half into the stud. 2'-11" leaves
# 1 3/4" to the stud and **0.475" to the king**, so the hole is a hole in sheathing and
# gypsum and nothing else — but it is the tightest dimension in this run, and it is what
# fixed D-B-FURN at 3'-3" rather than the 3'-4" it was authored at before the 2026-09-05 UI
# drag (this note was struck against that 3'-4", where the king's west face was 3'-1" and
# the bay 4 1/4"). Any move of that door east re-opens the clash this line was routed around.
# The bigger western bay was declined: it costs another 1'-11" of jog each way and puts the
# line into the lane PR-B-WC2-DRAIN (x=2'-6") and the BATH2 supply pair (x=2'-3") share.
#
# The one thing in the new lane is PR-B-MAIN-DRAIN, whose 4" trunk runs x=3'-0" between
# y=16'-6" and y=15'-6". Their plan lanes overlap by about half an inch there and their
# elevations do not: the trunk is at -2'-4.8" project and this line passes under it at
# -3'-6.7", 13 7/8" of clear. Nothing else lies between y=13'-3" and y=30'-9" at x=2'-11"
# — the only basement wall the leg crosses is W-B-CW itself.
#
# The jog off the spigot is 1'-0" long and takes its own 0.3" of fall, so the two legs below
# it are 66.45" and 63.275". Monotonic from 72" to 9", 0.3"/ft on every horizontal segment.
#
# ** THE DROP FOLLOWS THE DRAIN, AND ITS OFFSET IS IN x, NOT y. ** FX-B-SAUNA-FD sits at
# y=8'-2 3/16" (FX-B-SAUNA-SH's centre line) since W-B-SA-N went north on 2026-09-05, so
# this line stops the east leg 6" short at x=13'-0" and runs 5'-0 13/16" south from y=13'-3"
# to the drain's own horizontal. The 6" separation from PR-B-COND's drop is west of it
# rather than north, and both air gaps are over the grate.
#
# The 6" is taken in x deliberately: a drop at (13'-6", 8'-2 3/16") would land its last
# vertex ON PR-B-SAUNA-DRAIN's new north jog in plan and above its invert, which is exactly
# what `resolve/mep_queries.drain_tie_ins` reads as a connection. An air gap that resolves
# as a tie-in is no longer an air gap (test_plumbing_pass::test_drain_loads_roll_up...).
# The long leg at x=2'-11" stays in the lane vetted above and crosses nothing new; 0.3"/ft
# throughout puts the two intermediate inverts at 63.42" and 63.05". The last horizontal
# leg is 5'-0 13/16" and its authored end came up 43.73" -> 43.905" with the drain's move,
# so the 0.3"/ft this paragraph claims is still true of every leg.
ERV_CONDENSATE = [
    PipeRun(uid="3XVTM6HD5T", tag="PR-B-ERV-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(3, 11), ft(30, 9)), pt(ft(2, 11), ft(30, 9)),
                  pt(ft(2, 11), ft(13, 3)),
                  pt(ft(13), ft(13, 3)), pt(ft(13), inch(98.1875)),
                  pt(ft(13), inch(98.1875))),
            diameter=inch(0.75), material="pvc",
            # Starts at 4'-6": EQ-B-ERV's four ports are on top, with 3 5/16" of ceiling
            # above them (see plan/electrical.py). The pan is the run's high point; the fall
            # is 0.3"/ft the whole way, and the tie-in at FX-B-SAUNA-FD is 9".
            elevations=(inch(54), inch(53.7), inch(48.45), inch(45.425),
                        inch(43.905), inch(9))),
]

CONDENSATE = [
    PipeRun(uid="CBPC01AAAA", tag="PR-B-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(27), ft(9)), pt(ft(18), ft(9)), pt(ft(13, 6), ft(9)),
                  pt(ft(13, 6), inch(98.1875)), pt(ft(13, 6), inch(98.1875))),
            diameter=inch(0.75), material="pvc",
            # The 0.3"/ft the comment above states, authored as the grade it is: the two
            # intermediate inverts solve to exactly the numbers that were hand-written here.
            # path[3] is the top of the boxed chase's drop and stays authored — a vertical
            # leg has no plan run to fall over.
            elevations=(ft(7, 5.3375), None, None, inch(85.042), ft(0, 9)),
            slope_in_per_ft=0.3),
]

# --- TPR relief discharge (P2804.6.1) ------------------------------------------------
#
# The pipe that stops the tank exploding — `code.P2804_water_heater_relief` grades
# EQ-B-WH's `relief_discharge_ref`.
#
# 3/4" full-size copper (the valve's own outlet — P2804.6.1 forbids reducing it, or any
# valve/trap/rise along the run). Drops from the valve at 3'-6" to 8" above the slab, then
# 1'-0" horizontal at 2"/ft to an air gap 6" over the floor — the low end of P2804.6.1's
# 6"-24" band. Discharges onto the mechanical-room slab by design, with no fixture below to
# damage — the same reason P2801.6 needs no pan under the tank. Hangs 2" off the tank's west
# face and drops a foot toward the door, 11'-11" from SM-B-RADON — too far for "the floor
# falls to SM-B-RADON" to be an argument on its own. The air gap is what P2804.6.1 actually
# requires; the slope is a slab-pour question the pour has to be told to fall this way
# rather than assumed to. Flagged in plans/TODO.md.
TPR_DISCHARGE = [
    PipeRun(uid="CBPT01AAAA", tag="PR-B-WH-TPR", system=PipeSystem.DRAIN,
            path=(pt(ft(4, 4), ft(24)), pt(ft(4, 4), ft(24)),
                  pt(ft(4, 4), ft(23))),
            diameter=inch(0.75), material="copper",
            elevations=(ft(3, 6), ft(0, 8), ft(0, 6))),
]

# --- Radon sump + shared radon/plumbing vent riser ---------------------------------
# A sealed radon sump in the NW basement furnace room, riding RM-M-MECH's framed shaft
# closet. Its passive radon vent shares the plumbing vent's chase up to 23'-10", then turns
# out through the north gable siding and back up. ** IT JOGS EAST INSIDE THE ATTIC FIRST **
# — at x=1'-0" the 6:12 roof underside is 20'-8 1/4" and the riser cannot stand up there at
# all, so `VentRun.chase_offset` steps it 12'-4" through the FS-ATTIC joist webs to
# x=13'-4" before it rises (mep_venting.py). Termination is derived (12" above the true
# roof surface, resolve/vent_termination.py), not authored — an authored absolute can't
# follow a rake.
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


# --- the guest studio ---------------------------------------------------------------------
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
# second floor's, where PR-M-S-SUITE-DRAIN's head is waiting.
STUDIO_DRAINS = [
    # ** THE RUN IS FLANGE -> WEST -> DOWN -> EAST, NO DOG-LEG. ** The water closet is
    # on the wet wall (plan/fixtures.py), c/l on y=19'-4", 232" = 8 + 14 x 16, a bay centre:
    # the flange drops straight between joists. The drop, at (9'-7 1/2", 19'-4"), is deep
    # inside W-S-DC2 (y 15'-11"..22'-4") and clears the two supply risers at y 20'-6"/21'-0".
    # The lavatory's 1 1/2" arm comes south off the north wall into the same west leg.
    #
    # ** THE DROP IS ITS OWN LEG — A REPEATED PLAN VERTEX WITH TWO ELEVATIONS. ** It used to
    # be one diagonal from the attic bay straight to the stack head, falling 114.5" over
    # 4.16 ft of plan. That is 27.5"/ft and there is no fitting for it; `mep.drain_slope` was
    # blind to it (it grades the FLATTEST segment) and `mep.drain_offset_geometry` now is not.
    # The drop bottoms at 9'-8" so the east leg still holds 1.5" over its 4.161 ft —
    # 0.36"/ft, clear of P3005.3's 1/4" — and its 3" crown sits at 9'-9 1/2", inside the
    # 8 7/8" chord-to-chord window a leg crossing FS-S-WEST's trusses has to stay in. That
    # window is what took PR-M-S-SUITE-DRAIN's head down 1 1/2" (below); the two profiles
    # move together or neither moves. It lands at 9'-6 1/2" on the stack's vertical, 2 1/2"
    # above where PR-M-S-SUITE-WC-DRAIN enters it — two inlets on one barrel, not a double
    # fitting at one point.
    PipeRun(uid="HTZ1RGAGXP", tag="PR-A-STUBATH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(11, 0.875), ft(19, 4)), pt(ft(9, 7.5), ft(19, 4)),
                  pt(ft(9, 7.5), ft(19, 4)), pt(ft(13), ft(16, 10.8))),
            diameter=inch(3), material="pvc",
            elevations=(ft(19, 4), ft(19, 3.5), ft(9, 8), ft(9, 6.5)),
            serves=("FX-A-STUBATH-WC", "FX-A-STUBATH-LAV", "FX-A-STUBATH-SH")),
    # ** THE BAR IS NOT BACK-TO-BACK WITH THE BATH. ** It is on W-A-C2's west face at
    # (17'-0", 16'-8") because the 6:12 rake leaves nothing usable at the wet wall, so its
    # 2" branch crosses the joist field west on the y=16'-8" bay centre (200" = 8 + 12 x 16)
    # and turns north to the stack head. Seven feet of extra 2" PVC in a bay it shares with
    # nothing — the price of a counter you can stand at.
    # ** THE HEAD IS UNDER THE BOWL, WITH A 4" TAILPIECE LEG. ** The sink sits on W-A-C2's
    # face, clear of W-A-BATH-S's 17'-1 5/8" south face, c/l at y 16'-4", 4" off the 16'-8"
    # bay centre — so the arm drops at the bowl, turns 4" north onto the bay, and only then
    # runs west. The 16'-8" leg is 1/4"/ft; the 4" leg is 0.75"/ft.
    PipeRun(uid="ZY2V3KWMVK", tag="PR-A-BAR-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(17, 1.625), ft(16, 4)), pt(ft(17, 1.625), ft(16, 8)),
                  pt(ft(9, 7.5), ft(16, 8)), pt(ft(9, 7.5), ft(19, 4))),
            diameter=inch(2), material="pvc",
            # 2" over the 7'-11" west leg and 1" over the 4'-0" north one — 1/4"/ft on both,
            # which `mep.drain_slope` grades segment by segment. The whole profile sits inside
            # FS-ATTIC's 11 7/8" joist band (19'-0 1/8"..20'-0"), through the webs.
            elevations=(ft(19, 7.75), ft(19, 7.5), ft(19, 5.5), ft(19, 4.5)),
            serves=("FX-A-STUDIO-BAR-SINK",)),

    # ** THE LAVATORY AND THE SHOWER, COLLECTED IN THE WET WALL. ** Both were 15"-27" from any
    # pipe naming them until 2026-09-07. This 2" leg runs south inside W-A-STU-W's 5 1/2"
    # staggered cavity — under the bottom plate, through two FS-ATTIC I-joist webs at y=256"
    # and y=240" — from the lavatory's drop to the west leg's own drop point at (9'-7 1/2",
    # 19'-4"), where it lands exactly on that vertex at 19'-3 1/2".
    PipeRun(uid="FY6M0PTE7C", tag="PR-A-STUBATH-LAV-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(9, 7.5), inch(258.625)), pt(ft(9, 7.5), inch(258.625)),
                  pt(ft(9, 7.5), ft(19, 4))),
            diameter=inch(2), material="pvc",
            elevations=(ft(20, 0.75), ft(19, 4.25), ft(19, 3.5)),
            # No `wall_ref`, for the same reason as PR-M-S-BATH1-LAV-DRAIN: the leg runs
            # under W-A-STU-W's plan footprint but below its base, in the joist band, so a
            # claim that every segment is inside that wall's cavity would be false.
            serves=("FX-A-STUBATH-LAV",)),
    # The 36" pan's 2" waste. FS-ATTIC is I-joists, not the second floor's trusses, so this
    # leg buys its freedom by running WEST — parallel to the joists, in the 241 1/4"..254 3/4"
    # bay the pan's grate already sits in — and crosses nothing at all for 6'-7". It ties into
    # the leg above at (9'-7 1/2", 20'-7 5/8"), 1/16" over that pipe's invert there.
    PipeRun(uid="BVZG9VAP7M", tag="PR-A-STUBATH-SH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(16, 2.625), ft(20, 7.625)), pt(ft(16, 2.625), ft(20, 7.625)),
                  pt(ft(9, 7.5), ft(20, 7.625))),
            diameter=inch(2), material="pvc",
            elevations=(ft(20, 0.75), ft(19, 5.75), ft(19, 4)),
            serves=("FX-A-STUBATH-SH",)),
]

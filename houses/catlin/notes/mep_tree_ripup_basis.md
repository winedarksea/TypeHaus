# Tree rip-up and `--lift` — hand-worked basis for `routing/tree_ripup.py`

**House:** catlin. **Oracle for:** E1's rip-up inside a drain Steiner tree (`routing/tree.py`,
`cli/route_tree_branches.py`) and `--lift TAG` (`cli/route_tree_lift.py`). Written 2026-11-07 from the
spec, `mep_drain_routing_basis.md` §5/§13 and the authored plan geometry, **before** E1 coded. No router
output is an input; the one place a router number is quoted (§4.1) is marked.
**What this is not:** a claim that catlin's two refusals close. §4 says which part the hand model can
decide and which it cannot.

Units: inches, project frame, main-floor datum z = 0 (top of joists). Elevations are pipe centrelines.
OD is the real outside (`pipe_sections`): 1 1/2" PVC 1.900, 3/4" Cu 0.875, 1" Cu 1.125, 1/2" PEX 0.625.
Clearance between surfaces 0.5" (`obstacles.CLEARANCE_M`). Grade 1/4"/ft = 0.020833 in/in.

---

## 1. The policy

A terminal T refuses (RSPH, deepest first, §5). Its refusal names the laid branches its labels ran into.

* **P1 Trigger.** Rip-up runs only for a refused terminal whose refusal names at least one laid branch of
  *this* tree. A refusal naming only authored runs or hard geometry is final (that is `--lift`'s job, §3).
* **P2 Candidates and order.** The named branches, **most recently laid first** (ties: later in lay order,
  then tag descending). Argued like §5: RSPH lays by ascending slack, so the most recent branch has the
  most slack, is cheapest to re-lay, and is the one least "forced"; lifting the earliest would unseat the
  branch the order says is nearly unique. It also moves T ahead of the fewest branches.
* **P3 Cascade.** Lifting L lifts every branch whose tie lies on L, transitively (`Branches.lines[i].down`
  chain). The lifted set is re-laid in its **original lay order**.
* **P4 Trial, keep or rollback.** Remove the lifted set, search T, lay it, re-lay the set. **Keep only if
  T and every lifted branch lay.** Otherwise restore the pre-trial tree exactly (routes, inverts, owners).
  A kept trial changes `unserved` by -1 and never +1.
* **P5 Bound.** At most `MAX_LIFTS = 2` trials per refused terminal, counting rolled-back ones. The first
  success wins. Re-lays never rip up.
* **P6 Never reversed.** Record `(T, L)`; L may not lift T later. Each trial inverts one pair that was in
  deepest-first order, so inversions grow by exactly 1 per kept trial and are bounded by n(n-1)/2:
  **it terminates** even without P5, and P5 caps the number of failing searches (the costly ones: a refusal
  can walk the whole label budget, ~70 s on catlin).
* **P7 Determinism.** Same inputs, same tree; every tie breaks on tag.

* **P8 Size-only refusals upsize before they lift** (added after E1 built it; I proposed the idea in 4.3,
  E1 settled the details). A tie refused only because the carrying branch is too small (`admits`: Table 703.2,
  e.g. 2 + 2 = 4 DFU on a 1 1/2" that carries 3) is tried first by upsizing the carrier one size and re-laying it.
  - **P8a (re-search, not re-lay).** The upsized branch is searched afresh within 2 ft of its old lane: a bigger
    OD moves every clearance. Hand arithmetic for BATH2-SH: a TJI blocking row stands at x = 74.56 (panels
    y 193.2..206.8, 209.2..222.8, 225.2..238.8, 243.5..254.8, z full depth, flange width 2.312, so faces at
    73.40 and 75.72), a rail the run "never rides" (§13). A centre must stay `1.156 + 0.5 + r` from it: 1 1/2"
    (r 0.95) x >= **77.17**, 2" (r 1.1875) x >= **77.40**; the east limit is CW-BATH1 at 82, `0.4375 + 0.5 + r`:
    **80.11** / **79.875**. The shower stands at x = 76.62, so it is 0.55" / 0.78" inside the clearance and must
    jog east into a 2.94" / 2.48" window. The "2.5" window of 9.6" corridor" I gave in 4.3 forgot this row.
  - **P8b (cascade, later branches too).** Every branch laid **after** the upsized one is lifted and re-laid in
    order, as in P3. The radius grows 0.2375" (OD 1.900 -> 2.375), so any later neighbour laid with less than
    that slack is displaced (E1: LAUNDRY blocked the 2" shower by 0.139", i.e. it cleared the 1 1/2" by 0.099").
    I would have lifted only the named blockers; re-laying all later ones is simpler, deterministic and correct,
    at the cost of searches. **Accepted.**
  - **Order and cap.** P8 trials run **before** P1 lifts and count inside the two-trial cap of P5: a size
    refusal has a known cause and one re-lay, a P1 lift only a guess. Termination: sizes only grow along
    1 1/4, 1 1/2, 2, 3, 4", at most four steps per branch, and a rolled-back P8 trial restores P4's exact state.

Reported per tree: `lifts_tried`, `lifts_kept`, and for each kept lift `(T, [lifted...])` in order.

---

## 2. A synthetic world by hand

Plan lattice, 24" pitch, plain edge price 24, bend 6, no gravity (budget None, so order is by tag):

```
 y=24   n3 ---- n4 ---- n5          edge n3-n0 is hard (removed)
                 |       |
 y= 0   n0 ---- n1 ---- n2          root n0 = {goal}
        x=0     x=24    x=48
```

Rules: a laid branch's interior nodes and edges are obstacles; a terminal may *end* on a node of the tree
only if `admits` (a branch never ties onto a smaller line: 3" onto 1 1/2" refused, §5). Fixture start nodes
are occupied by their own branch.

### 2a. Two branches (E1's basic unit test)

T1 = 1 1/2" at n4. T2 = 3" at n2. Order by tag: T1, T2.

* **T1:** lanes n4-n1-n0 = 24 + 24 + one bend 6 = **54**; n4-n3-n0 is removed; n4-n5-n2-n1-n0 is 96 + 3 bends.
  Lays n4-n1-n0, 54", 4.5 ft.
* **T2:** n2-n1-n0 rides T1's n1-n0 (blocked); a tie at n1 is not admitted (3" onto 1 1/2"); n2-n5-n4 ends on
  T1's start node (occupied). **Refuses.** Blocker named: T1.
* **Rip-up:** lift T1 (no dependents). T2 lays n2-n1-n0: 24 + 24 = **48**, no bend. Re-lay T1: n4-n1, a tie on
  T2 at n1 (1 1/2" onto 3", admitted), **24**, no bend.

| | unserved | developed | cost | lay order | lifts |
|---|---|---|---|---|---|
| no rip-up | {T2} | 54" = 4.5 ft | 54 | T1 | 0 |
| with rip-up | {} | 48 + 24 = **72" = 6.0 ft** | **72** | T2, T1 | tried 1, kept 1: `(T2, [T1])` |

Tree nodes after: {n0, n1, n2, n4} = 4.

### 2b. A cascade and a rolled-back trial

Tags A1 (1 1/2", n4), A2 (1 1/2", n5), B (3", n2). Order A1, A2, B.

* A1: n4-n1-n0 = 54. A2: n5-n4 (a tie on A1 at its start node, 24, no bend; one lav each, 2 DFU on a
  1 1/2" that carries 3) beats n5-n2-n1 (54). B refuses exactly as T2 did; blockers named: A1 (at n1) and A2
  (at n5).
* P2: most recent first: **A2**. Trial 1: lift A2 alone. B still meets A1 at n1 and A1's start at n4:
  refuses. **Rolled back**, tree unchanged.
* Trial 2: **A1**, cascading to A2 (A2's tie lies on A1). B lays n2-n1-n0, 48. Re-lay in order: A1 n4-n1
  (24), A2 n5-n4 (24, a tie on the new A1).

Totals: **48 + 24 + 24 = 96" = 8.0 ft**, cost 96; lay order B, A1, A2; `lifts_tried` 2, `lifts_kept` 1; trial
order `[A2, A1]`; tree nodes {n0, n1, n2, n4, n5} = 5. P5's bound (2) is reached, so a third candidate would
not be tried. A variant a test can force: make A1's re-lay refuse (patch it); then trial 2 is rolled back too,
the tree equals the pre-rip-up tree, B stays unserved, `lifts_kept = 0`, `lifts_tried = 2`.

---

## 3. `--lift TAG`

* **L1.** A lifted run is **not an obstacle** while the tree is searched (it joins `touch`, as the drains the
  tree replaces already do). `--lift` takes authored runs of any system; catlin's two are supply.
* **L2.** After the tree, each lifted run is re-proposed as a run (`--run` semantics: its authored first and
  last terminals, port stubs honoured) against occupancy = every tree proposal + all authored geometry
  except lifted runs not yet re-laid **and the authored drains the tree's own proposals replace** (those serving
  a fixture the tree proposed; a refused fixture's authored drain stays an obstacle, it is still the pipe serving
  it). Amended after E1: without the exclusion a proposal sits next to its own old pipe, a phantom clash, and
  the tree search already treats them the same way (`touch` = the target plus `replaced`). Order: larger OD first, then tag (the campaign order, §12).
* **L3.** One-way: a lifted run never rips up a drain proposal; the tree is final before any re-lay.
* **L4.** Each lifted run ends **LAID** (new path, length, how far it moved from the authored one) or
  **REFUSED** with the blocking proposal tags. The tree stands either way; a refused lift is reported as
  "needs a hand re-lay of TAG", never silently dropped. Cost: `|lift set|` searches. Terminates.
* **L5 (1-D test a re-lay must pass).** A supply of OD `D_s` crossing above a drain of OD `D_d` at centreline
  height `z_d` needs `z_s >= z_d + (D_d + D_s)/2 + 0.5`, and stays inside the crossing member's window
  (`member_window`, centreline `[low + D_s/2, high - D_s/2]`).

**Supply tees (L6-L9, added 2026-11-07).** `--run` lays a supply from its fixture riser to any point on
its feeder and knows nothing of what tees on it, so L4 refused all three catlin lifts ("loses N"). The rules
that keep the tees:

* **L6 Taps are derived.** A supply run taps the lifted run only when `supply_tie_in_records` names the
  lifted run as its parent (its first vertex, the tee). Sharing a vertex is not a tap. CW-WH's first vertex
  (57, 192, -8.8) is also the first vertex of CW-BATH1, CW-BATH2 and CW-SBATH, which all derive
  CW-TRUNK: three false losses. Its one true child is CW-BATH (tee at (84, 330, -6.8) on its y = 330 leg).
  Drains and vents keep the geometric test (either end within 1" of the line).
  *2026-11-11:* EQ-B-WH's move (2026-11-10) cut CW-WH to 9.0 ft; it has no kept child now and
  CW-BATH tees on the trunk at (57, 243). The lift re-lays CW-WH in 8.91 ft (dropping on the heater
  inlet's own axis to -104.38") and CW-BATH in 12.05 ft. The L6 numbers above are the 11-07 house.
* **L7 Hold the tail an unlifted branch tees on.** For the branches that are not lifted, find the segment
  `i` (parameter `t`) of the lifted run's authored line nearest each tee; the hold starts at vertex
  `k = i + 1` if `t = 1`, else `i`, minimised over the branches and capped at `n - 2`. The last
  `n - 1 - k` legs are held as authored and the search starts at vertex `k` (`--hold-upstream` on a supply
  holds its fixture end; the held legs are appended after the reversal). `k = 0` would leave nothing to
  search: hold 0, and the branches are lost (L4). The cap holds the last leg for a tee on the fixture end
  itself, so the run arrives as authored. The first build held nothing there, and CW-BATH came UP to
  (120, 238, -82) inside USINK-TERMINAL-CW's riser going down from the same point (`mep.run_interference`).
  By hand: HW-KITCH (16 vertices) carries PR-M-DW-HW's tee at (363.6, 424.2, 5.5), on the riser from vertex
  12 (z -6.24) to vertex 13 (z 9.06), so `k = 12` and **3 legs are held**: the riser, the 2.7" jog and the
  riser to 20.0. CW-BATH (8 vertices) has two branches (LAV-, USINK-TERMINAL-CW) teeing at its last vertex
  (120, 238, -82): `k = 6`, **1 leg held**, the riser down from (120, 238, -6.8).
* **L8 A lifted branch tees onto its feeder's new line.** A re-laid feeder's proposal replaces its authored
  line as the branch's goal set (`reroot_supply`), so the branch is re-laid after its feeder. L2's
  larger-OD-first order gives that on catlin (CW-WH 1" before CW-BATH 3/4"). A branch re-laid first would
  tie onto the old line, and L4 refuses that ("its tie onto ...").
* **L9 Accessories that come off the line are listed.** An accessory on a lifted run whose point is more than
  1" off the new line is named in the after-paste re-seat line, the same sentence `--tree --topology trunk`
  writes. One on a held leg stays: PA-M-KITCH-STOP-HW (363.6, 421.5, 9.06) is HW-KITCH vertex 14, and
  PA-B-BATH-STOP-CW stood on CW-BATH's fixture end (removed 2026-11-10, W5). PA-B-BFP-BATH (84, 312, -8.8) and PA-B-WH-STOP-CW
  (93.5, 335.5, -61.44) are on searched legs, so they are listed unless the new line happens to pass them.

---

## 4. Catlin, by hand

### 4.1 Facts the arithmetic stands on

* **The tree's root is one point.** `_propose_tree` ties only into main vertices in the band
  `[-24", +6"]` about the floor. `PR-B-MAIN-DRAIN`'s vertices: (72", 271") -16.0 (in), then -25.5, -26.3
  and deeper (out). Root = **(72", 271"), z = -16.0"**. Every branch ends there or on another branch.
* **Windows** (`member_window`): FS-M-WEST/MECH/STAIR TJI 230 (1.25" flanges): crossing window -10.625..-1.25,
  so a 1 1/2" run's centreline in **[-9.675, -2.20]**. FS-M-NE trusses: -10.375..-1.5, centreline **[-9.425, -2.45]**.
  A run inside a bay (parallel to joists) has floor -11.875, so centreline >= -10.925. Deck: crown under 0,
  so a 1 1/2" start is <= **-0.95**.
* **FS-M-MECH joists** (read from the model): y = 261.38, 277.38, 293.38, 309.38, 325.37, ... The tie (72, 271)
  stands in the bay y 262.5..276.2.
* **The cold fence round the tie** (authored, all inside the web window): `PR-B-CW-WH` x = 68.5, y 203.5..330
  at -6.8, then east along **y = 330, x 68.5..93.5** at -6.8, dropping at (93.5, 335.5) to -104.4;
  `PR-B-CW-BATH` x = 84, y 243..330 at **-8.8** (3/4" Cu), tee'd off CW-WH's y=330 leg, and its y = 243 leg at -6.8;
  `PR-B-CW-BATH1` (57,192)->(82,201.6)->(82,230.4)->(62,252) at -8.8. `PR-B-HW-WASH` crosses at
  (96.3, 269) at **-12.0**. So the tie sits in a pocket, x between 68.5 + 2.01 = **70.5** (CW-WH) and
  84 - 1.89 = **82.1** (CW-BATH), open to the north across CW-WH's y = 330 leg and to the east in the
  y 262.5..276.2 bay.
* **Read late (2026-11-07 re-check), not in the first pass:** `PR-B-CW-TRUNK` (1 1/4" Cu, OD 1.375, z = -8.8):
  x = 357.6 N-S y 180..424.2 (5.6" east of the sink, not crossed by a west lane), **y = 418 E-W x 57..114**
  (crossed by any north-lane descent at x < 114), x = 57 N-S y 192..386.5. The 18' bearing line has **TJI
  blocking panels full depth at x = 214.1, y 262.5..276.2** (the whole STAIR bay) and truss blocking at
  x = 217, y 253.8..266.2 (flanges are hard prisms, the web between is open: pass at z in [-9.675, -2.2]).
  FS-M-NE trusses are at y = 252, 268, 284, 300, 316/332 (doubled), ... **268 stands inside the STAIR bay
  (262.5..276.2), so a lane at y = 269 is on a truss line; use y = 272.5** (section 4.2). The three EMT
  conduits are 3/4" (OD 0.922, exclusion half 1.911).
* Exclusion half-height for a 1 1/2" drain (OD 1.9) over a pipe of OD `D`: `0.95 + 0.5 + D/2`.
  CW-WH (1.125): **2.0125**, so z-exclusion (-8.8125, -4.7875). CW-BATH (0.875): 1.8875, (-10.69, -6.91).
  HW-WASH or HW-KITCH at -12 (PEX 0.625): 1.7625, (-13.76, **-10.24**).
* `TODO.md` says: KITCH-SINK refuses at 1 1/2" with PR-B-CW-WH tightest across the fall band; BATH2-SH is
  blocked by PR-B-HW-KITCH along y = 15'-6" at 97 7/16" basement-relative (= **-12.0**) (the router's words).

### 4.2 FX-M-KITCH-SINK (1 1/2": 2 DFU, Table 703.2)

Drain point (352", 416.99"). Any monotone lane to the root is `|352 - 72| + |416.99 - 271| = 280 + 145.99
=` **425.99" = 35.50 ft**, so the fall is **8.875"** at 1/4"/ft; head available 0 - (-16) = 16"; slack 7.125".
The global budget is not what binds. The windows do.

*The north lane* (down the stair/mech strip, into the pocket across CW-WH's y = 330 leg, then south to the
tie). Its last joist web is y = 277.38 at x ~ 76: `s = (352-76) + (416.99-277.38)` = **415.61"**, fall there
8.658". The centreline must clear the window floor: `z_s - 8.658 >= -9.675`, so `z_s >= -1.017`; the deck gives
`z_s <= -0.95`. **The fall band is [-1.017, -0.950], 0.067" wide.**

CW-WH crossing at plan x_c in the pocket [70.5, 82.1], `s_c = (352 - x_c) + 86.99`:

| x_c | s_c | fall | z_s needed to pass UNDER CW-WH (z <= -8.8125) | vs band bottom -1.017 |
|---|---|---|---|---|
| 70.51 | 368.48" | 7.677" | <= -1.136 | **short 0.119"** |
| 82.11 | 356.88" | 7.435" | <= -1.378 | short 0.361" |

Passing over needs `z_s` > 0. **With CW-WH in place the band is closed by 0.12" at best.** Lifted: the band
is 0.067" wide, i.e. open in continuous 1-D by about one 1/16" (0.0625"). The search rounds each graded
leg's fall up to 1/16" (§13, up to 0.0875" on three legs; this lane has more), so the expected outcome is
**lifting CW-WH alone still refuses** (0.067" against an allowance that is >= 0 and up to ~0.3"). Not
decidable by hand to better than "knife-edge".

*The south bay lane* (down to y = 272.5 at x = 230, then west in the STAIR bay 262.5..276.2 and the
truss bay 268..284, no joist crossing; `s = 122 + 144.5 + (230 - x)`):

* CW-BATH at x = 84, `s` = 416.0", fall 8.666": below it needs `z <= -10.69`, so `z_s <= -2.024`; the bay
  floor needs `z_s >= -10.925 + 8.875 = -2.05`.
* HW-WASH at x = 96.34, `s` = 403.7", fall 8.410": above its exclusion needs `z >= -10.24`, so `z_s >= -1.828`.

`-1.828` against `-2.024`: **closed by 0.197".** Lift CW-BATH: band `[-1.828, -0.95]` = **0.878"**, open.
Lift HW-WASH only: `[-2.05, -2.024]` = 0.026", no. **CW-WH is not on this lane at all.**

**Expected outcome:** lifting **PR-B-CW-WH alone does not open KITCH-SINK**; lifting **PR-B-CW-BATH** should
(south lane, 0.878") but E1 reports it does not: see the re-check below, still open. HW-KITCH is not near the sink's drain (x = 363.6/370.6, east of it): irrelevant.
**Re-check (E1 lifted HW-KITCH, CW-WH and CW-BATH and still refuses), and what E1 found.** My 1-D pass found no
closing obstacle, and the conduits are not it. **E1 found what I missed: the start.** The sink's drain point
(352, 416.99) sits in the 12" bay of trusses y = 408 and 420. The y = 420 chord is 3.5" wide (face at 418.25); the
pipe's edge is `416.99 + 0.95 = 417.94`, a gap of **0.31" against the 0.5" rule, 0.19" inside it**. I had written
"holds a 1.9" pipe with the sink's own 0.3"" and passed it; the rule is 0.5". The chord clearance binds wherever
the pipe is in the chord's z band (crown above -1.5 - 0.5), so the start can only leave the point near the
ceiling: E1 reads the start band as **[-0.047, 0]**, and the snap's round-up uses it. Hand check of the
consequence: a centre in the bay is at most `418.25 - 0.5 - 0.95 =` **416.80**, so a drain point 0.19" south,
(352, 416.8), clears it (E1: **0.7" band** from there). With the start held at z = -0.02 my south-lane margins
(x_d = 222, 130" of s to the descent) are DATA-MEDIA 1.6" above, PLAY-SPARE 1.8" above, **KITCHEN (y = 280, z -3.5,
exclusion bottom -5.411) crossed at `-0.02 - 267/48 = -5.58`, 0.17" below** (the thin one, and it is a
below-pass), HW-WASH 1.9" over its -10.24, end -8.9 over the bay floor: positive, but the KITCHEN margin is
under the snap's worst 0.125" plus a 1/16" station error. **The north-lane figures stand** (its band came
from the window floor and the deck, not the start). E1's other findings, accepted: **x = 230 hits a web at
truss y = 408; x = 222 and x = 238 pass** (stations 16" apart, so my "24" pitch" was wrong for these webs), and
**the 1.5" final jog is under the 2.19" minimum between fittings** (1 1/2" hub OD, `fitting_room`): the last leg
must be >= 2.19", so run at y = 273.2 (inside the 271.2..274.77 overlap) and drop at y = 271.

Corrected lane to force (constant 1/4"/ft, start z held at -0.02, drain point moved to y = 416.8):

| vertex | x | y | z (in) | s (in) |
|---|---|---|---|---|
| V0 sink drain | 352 | 416.8 | -0.02 | 0 |
| V1 | 222 | 416.8 | -2.73 | 130 |
| V2 | 222 | 273.2 | -5.72 | 273.6 |
| V3 | 72 | 273.2 | -8.84 | 423.6 |
| V4 tie (plumb drop to -16.0 follows) | 72 | 271 | -8.89 | 425.8 |

Still unmodelled by me: the bore through the TJI blocking web at x = 214.1 (s = 281.5, z = -5.88, inside the
web window), `fitting_room` at the tie (a 7.1" plumb drop beside the 4" head), and the doubled trusses y = 316/332.

*Conduits:* now read (3/4" EMT) and clear on the lane above.

*Re-lay of a lifted CW-WH* (L5), north lane, `z_s = -1.0165` at x_c = 70.51: drain `z_d = -1.0165 - 7.677 =
-8.693`; the supply's y = 330 leg needs `z >= -8.693 + 0.95 + 0.5 + 0.5625 =` **-6.681** (authored -6.8, raise
0.119"); at `z_s = -0.95` it is -6.615 (raise 0.186"). Both inside CW-WH's window (-10.06, -1.81). Re-laid on
its own lane, 1/8" to 3/16" higher: **LAID**. Re-lay of a lifted CW-BATH across the south lane at x = 84, mid-
band `z_s = -1.5`: `z_d = -10.166`, supply `z >= -8.278` and `<= -1.69`: 6.6" of room, **LAID** (e.g. at -6.8).

### 4.3 FX-M-BATH2-SH (1 1/2": 2 DFU)

Drain point (76.62", 179.0"). Lane north in the corridor x 70.5..80.1 (CW-WH x = 68.5, CW-BATH1 x = 82):
`|4.62| + 92.0 =` **96.62" = 8.05 ft**, fall **2.013"**, slack 13.99". CW-BATH1's diagonal crosses at about
(76, 199) and (76, 237): free band above it `[-6.91, -2.20]` = 4.7", so `z_s` anywhere in about `[-5.7, -1.0]`
passes. The joists it crosses (192 ... 259.06, 261.38) need only `z >= -9.675` (`z_s >= -7.9`).
**PR-B-HW-KITCH at -12.0 has exclusion top -10.24, 0.565" under the window floor (-9.675): it overlaps no
lane that crosses a joist web, and only the bottom 0.69" of a bay (floor -10.925).**

**Expected outcome:** lifting HW-KITCH **does not open** BATH2-SH, and it is not needed: from the supplies
alone the corridor is open with 4.7" to spare. BATH2-SH's refusal has a cause this hand model does not
contain (candidates: the bearing-line gap and blocking at y = 259.06..261.38, where two joists 2.32" apart
must both be bored; `members` bore rules). E1 should read its own `--counterfactual`, not this note, for
BATH2-SH. HW-KITCH needs no re-lay (it hangs under the joists and was never in the band).

**BATH2-SH lays, BATH2-TUB then refuses ("one lane, two fixtures").** Between y = 193 and 255 the TJI blocking
row at x = 74.56 (P8a) leaves a 1 1/2" run centres in x 77.17..80.11, **2.94" wide**; two 1 1/2" lines need 2.4"
between centres, so plan alone leaves 0.54". The cause is the single tie point plus the size rule: both
branches must end plumb at (72, 271), and the tub cannot tie onto the shower branch because 2 + 2 = 4 DFU needs
2" (Table 703.2: 1 1/2" carries 3), so `admits` refuses, as in section 2's T2 onto T1. The remedy is P8 (section 1):
upsize the shower branch to 2" (window 77.40..79.875 = 2.48", above the CW-BATH1 diagonal z >= -6.675), re-search
it within 2 ft, re-lay later branches, then the tub ties on at about (77, 215).

### 4.4 Numbers a test may assert

Root (72, 271, -16.0). KITCH-SINK: 425.99" / 35.50 ft / fall 8.875"; north-lane band 0.067"; CW-WH short
0.119"; south-lane CW-BATH+HW-WASH short 0.197", lifted 0.878". CW-WH re-lay z >= -6.681. BATH2-SH: 96.62"
/ fall 2.013" / free band 4.7". §2a: 72" / cost 72 / lifts `[(T2,[T1])]`. §2b: 96" / cost 96 / trials `[A2, A1]`.
Row `tree:main+lift` (CW-WH + HW-KITCH) does **not** propose KITCH-SINK (confirmed by E1); with CW-BATH too the hand model still says the south lane (section 4.2 table) is open, E1's router says not: unresolved, and the forced lane's objection is the missing fact.

---

## 5. What this note does not do

* No duct, conduit or framing-bore check beyond the web window (ducts in the main floor cavity near the
  pocket: none read; the NE conduit lattice only to 1-D).
* No grid-snap arithmetic on a real lane (needs the lane); §4.2 says only how much room the snap has.
* No claim about BATH2-SH's cause, and no router run: its numbers are not inputs here.
* No cost model for a lift beyond "re-laid or refused"; a lifted run's price is not weighed against the drain.

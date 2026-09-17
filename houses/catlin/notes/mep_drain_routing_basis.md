# The suite-bath drain group — routing basis, and the oracle for `typehaus/routing/`

**House:** catlin, Minnesota (MN 2020 Residential Code, adopting the 2018 IRC).
**Group:** `RM-S-SUITEBATH`'s three fixtures and the stack that takes them —
`PR-M-S-SUITE-DRAIN` and the three branches authored onto it 2026-09-07.
**Oracle for:** `typehaus/routing/gravity.py` (§2), `routing/corridors.py` (§3),
`routing/graph.py` + `routing/search.py` (§4), `routing/tree.py` (§5); and, from the other
end, `mep.fixture_drain_reach` (§1). Reproduced numerically by
`tests/test_routing_oracle.py`.
**What this is not:** a fitting take-off, a venting design, or a claim of optimality. §6.

Every number below is recomputed here from the authored model, with the arithmetic shown, so
a reviewer can check the chain without opening the engine. Plan coordinates are inches in the
project frame; elevations are inches, project-absolute, and are **pipe centrelines** — see
`model/mep.py` on `PipeRun.elevations`, which settled that convention on 2026-09-07.

---

## 1. The four terminals, and the gaps that said nobody had drawn them

This storey had two stacks and no branch piping at all until 2026-09-07. Three of the four
points below are fixtures; the fourth is the root they have to reach.

| point | plan (in) | how it is derived |
|---|---|---|
| `FX-S-SUITEBATH-WC` | (134.81, 250.625) | its own position. A water closet is the one common fixture with no hot connection, which is the model's only reliable signal that a fixture is floor-drained — `resolve/mep_sleeves._expected_drain_point` |
| `FX-S-SUITEBATH-LAV` | (165.5, 268.0) | the cabinet stands at (165.5, 254.13) and needs hot water, so the derivation projects it onto `wall_ref` `W-S-SN3`'s axis at y=268 — the wet wall the waste actually turns down in |
| `FX-S-SUITEBATH-TUBSH` | (197.615, 261.125) | **authored** `drain_position`. Left to the convention it landed on `W-S-C2C`'s axis at x=216, inside a bearing wall's studs. The tub runs y 204.625..264.625 on the x=197.615 centreline; its waste-and-overflow is 3 1/2" in from the north end face |
| root: `PR-M-S-SUITE-DRAIN` head | (156.0, 202.8) | the stack's top vertex, at elevation 115.5 |

**The gaps, hand-worked.** Straight-line plan distance from each fixture's drain point to the
nearest pipe of any run naming it — which, before the branches existed, was the stack head:

    WC   √((156 − 134.81)² + (202.8 − 250.625)²) = √(21.19² + 47.825²)
         = √(449.02 + 2287.23) = √2736.25 = 52.31"
    LAV  √((156 − 165.5)²  + (202.8 − 268.0)²)   = √(9.5²  + 65.2²)
         = √(90.25 + 4251.04) = √4341.29 = 65.89"
    TUB  √((156 − 197.615)² + (202.8 − 261.125)²) = √(41.615² + 58.325²)
         = √(1731.81 + 3401.81) = √5133.62 = 71.65"

`mep.fixture_drain_reach` reported 52.3", 65.9" and 71.6". **That check's 12" threshold is
this measurement and its siblings**: across the whole house the distribution was bimodal with
an empty band — fixtures a branch actually reached measured 0"–8", the nine without measured
15.6" and up. Twelve inches sits in the hole with about 50% of margin either side.

**Note the TUB number moved when the model got more honest, not less.** Before
`drain_position` was authored it measured 67.9" — smaller, and to a point inside a wall. A
routing engine aimed at the old number would have solved the wrong problem.

---

## 2. The head budget, term by term

This is the arithmetic `GravityProfile.invert_at` has to reproduce: an invert is a derived
monotone potential, `invert = start − slope × developed plan length`, and nothing else.

**The 3" collector, `PR-M-S-SUITE-WC-DRAIN`.** Flange at the finished floor, drop, south
across the trusses, east onto the stack.

| leg | from → to | plan length | fall | slope |
|---|---|---|---|---|
| flange drop | (134.81, 250.625) 120.75 → 116.5 | 0 | 4.25" | vertical |
| south | → (134.81, 202.8) 113.375 | 250.625 − 202.8 = 47.825" = 3.9854 ft | 3.125" | 0.784"/ft |
| east | → (156, 202.8) 112.0 | 156 − 134.81 = 21.19" = 1.7658 ft | 1.375" | 0.779"/ft |

Developed plan length 69.015" = 5.7513 ft; total fall 4.5"; **mean 0.782"/ft**, and the
flattest segment is 0.779"/ft against ch. 4714 (UPC) 708.0's 0.25"/ft minimum. `mep.drain_slope` grades
the flattest and reports it.

**Why the drop bottom is 116.5 and not higher.** The south leg crosses the trusses, so the
pipe's crown has to stay inside the chord-to-chord window of §3, whose top is 118.5. A 3"
pipe centred at 116.5 crowns at 118.0 — 1/2" of margin. At 117.0 the crown is exactly on the
chord, and the routing engine must treat that as infeasible rather than tight: the search's
terminal test is the head budget, and the budget is bounded above by geometry, not by
preference.

**The minimum-slope feasibility statement.** Over 5.7513 ft at 0.25"/ft the collector needs
1.4378" of fall. The available head is (117.0 ceiling on the start) − (115.5 stack head) =
1.5". **Slack: 0.0622".** That is the sense in which this terminal's route is nearly unique,
and it is the whole argument of §5.

**What that 0.0622" is NOT is this run's build margin**, and the distinction matters because
the number has been read the other way. It is measured to the stack **head** at 115.5,
because that is the arrival a *search* must assume before it knows where on the barrel the
tie will land. The authored run ties at **112.0**, 3.5" lower, so what the pipe as drawn
actually holds is **3.062" of surplus fall** — 0.779"/ft flattest against 0.25"/ft, a 3.1×
margin. `mep.drain_slope_margin` is the check that reports the build number; `slack_in` is
an ordering key and reports the search number. Had the stack head stayed at 115.5 with the
collector tying there, rather than at 112 on the barrel below it, there would have been 1/16"
in hand — which is exactly what makes 0.0622" the right *ordering* number and the wrong
*margin* number.

**The two 1 1/2" arms**, each tying onto the collector's south leg rather than onto the stack
(two wyes 18" apart on a 3" beats three pipes at one point):

| arm | route | plan length | start → end | flattest |
|---|---|---|---|---|
| LAV | (165.5, 268) ↓ → (165.5, 246) → (134.81, 246) | 22" + 30.69" = 4.3908 ft | 117.5625 → 116.25 | 0.293"/ft |
| TUB | (197.615, 261.125) ↓ → (197.615, 228) → (134.81, 228) | 33.125" + 62.805" = 7.9942 ft | 117.4375 → 115.0625 | 0.294"/ft |

Each end elevation is checked against the collector's own **centreline** at that station
(`pipe_invert_at` interpolates the authored elevations, and an authored elevation is a
centreline — see `model/mep.py`). An arm entering in the collector's upper half is an
ordinary side entry; `mep.drain_tie_in` grades it. That station is
the interpolation above: at y=246 the collector reads 116.5 − 4.5 × (4.625/69.015) = 116.198,
and the arm arrives at 116.25 — **0.052" above it**, a side entry into the upper half of the
3". At y=228 the collector reads 116.5 − 4.5 × (22.625/69.015) = 115.025 against the arm's
115.0625, **0.0375" above**. Both are inside `_TIE_IN_INVERT_TOL_M` (1"), which is what keeps
`drain_tie_ins` linking them and `accumulated_serves` rolling the load up: 13 DFU on the
stack, 48 still on `PR-B-MAIN-DRAIN`'s 4".

---

## 3. The bay, hand-derived from the authored `JoistSpec`

`params/second_deck.py` states the west half as
`JoistSpec(member="11.875 floor truss", spacing=inch(16), direction="x")`.

    direction "x"     ⇒ trusses run in x, so their LINES are at constant y
    spacing 16"       ⇒ lines at y = 16n; bay centres at y = 8 + 16n
    2x4 flat chords   ⇒ 3.5" wide, centred on the line
    clear bay         = 16 − 3.5 = 12.5"     ← what clear_bay_width_m() returns
    clear zone        = (16n + 1.75) .. (16(n+1) − 1.75)

A 3" pipe on a bay centre therefore has (12.5 − 3)/2 = **4.75" either side**, and the widest
round section that fits a bay at all is 12.5". This is what `routing/corridors.py` turns into
a negative-cost channel: a leg running in **x** rides a bay and is cheap; a leg running in
**y** crosses the trusses.

**The vertical window is the constraint the plan view hides.** The members resolve
z 108.125..120 and the deck 120..120.75, so the structure is 11 7/8" deep. Chord-to-chord on
this truss is 8 7/8", which places the open web between

    108.125 + 1.5 = 109.625   and   120 − 1.5 = 118.5      (118.5 − 109.625 = 8.875 ✓)

So a **crossing** leg's outside must lie inside 109.625..118.5.

** AND "A 3 INCH PIPE" IS 3.500" ACROSS, NOT 3.000". ** The authored `diameter` is the
nominal the code tables are keyed on; 3" PVC DWV measures **3.500"** OD (ASTM D2665), and
`resolve/pipe_sections.py` is where the engine now converts one to the other. Worked at the
real size the admissible centreline band is **[111.375, 116.75]**, a quarter inch tighter at
each end than the [111.125, 117.0] this section used to state.

A leg **riding a bay** may use the full 108.125..120, because nothing is in the way along
it. Two different admissibility rules for the same pipe, decided by its direction relative
to `JoistSpec.direction`, and the reason a router that only knows "is it in a bay" produces
routes that cannot be built.

**Worked once for the collector, at 3.500".** Its south leg runs in y from 116.5 to 113.375:
crown 118.25 ≤ 118.5 ✓, invert 111.625 ≥ 109.625 ✓. Its east leg runs in x at y=202.8, in
the bay between the y=192 and y=208 lines (clear 193.75..206.25): the pipe spans
201.05..204.55, with 7.30" and 1.70" of clearance. Both admissible, by different rules.

Those are **whole-leg envelope** numbers — the crown taken at the leg's high end against the
chord ceiling — and the envelope is the conservative read, not the build margin. The high
end (y=250.625) sits in the 241.75..254.25 clear bay, where there is no truss at all.
`mep.run_member_crossing` grades the three truss lines the leg **actually crosses** and
reports **+0.944"** of crown at the tightest, `joist-0-015-0`. BLD-05's "half an inch of
clearance" was this envelope at the nominal size; both halves of that number have moved.

---

## 4. One escape graph, by hand

Deliberately tiny, so a reviewer can redo it in five minutes and check the engine against it.
This is the spec for `routing/graph.py` and `routing/search.py`; the numbers here are what
`test_routing_oracle.py` asserts.

**The world.** A 3×3 lattice on a 24" grid. Nodes at (24i, 24j), i,j ∈ {0,1,2}.

**The obstacle.** A chase whose inflated footprint (`radius + clearance`, already applied)
covers the centre node E. **E is REMOVED, not merely disconnected** — `build_graph` never
creates a node inside a hard prism — so ids are assigned to the eight survivors in
`(z, y, x)` order and E's number is never used:

          y=48   G(5)   H(6)   I(7)
          y=24   D(3)    ·     F(4)
          y= 0   A(0)   B(1)   C(2)
                 x=0    x=24   x=48

**Start** A, **goal** I. Supply pipe, so no gravity predicate — §5 adds that.

**Cost.** `g = travelled length + BEND × turns`, with **BEND = 24"** (one change of axis
costs as much as two feet of pipe). **Heuristic** `h = |Δx| + |Δy|`, Manhattan plan only, no
penalty terms — which is what keeps it admissible: a real path's bends can only add to it.

**State is `(node, incoming axis)`,** not the node alone. The bend penalty is a function of
the *turn*, so a node reached travelling east and the same node reached travelling north are
different states with different futures. A search without the axis in the state produces
staircases.

**Tie-break, stated because A* is otherwise non-deterministic and this oracle is byte-exact:**
`(f, node id, axis)` ascending, with axis order `+x < +y`.

**Expansion, in order.**

| # | popped state | g | h | f | pushed |
|---|---|---|---|---|---|
| 1 | (A, —) | 0 | 96 | 96 | (B,+x) g=24 f=96; (D,+y) g=24 f=96 |
| 2 | (B,+x) | 24 | 72 | 96 | (C,+x) g=48 f=96 — E is not there |
| 3 | (C,+x) | 48 | 48 | 96 | (F,+y) g=48+24+**24**=96 f=120 |
| 4 | (D,+y) | 24 | 72 | 96 | (G,+y) g=48 f=96 — E is not there |
| 5 | (G,+y) | 48 | 48 | 96 | (H,+x) g=48+24+**24**=96 f=120 |
| 6 | (F,+y) | 96 | 24 | 120 | (I,+y) g=120 f=120 |
| 7 | (H,+x) | 96 | 24 | 120 | (I,+x) g=120 f=120; (G,+x) g=120 f=168 |
| 8 | (I,+x) | 120 | 0 | 120 | **goal** |

Steps 5 and 6 are where the id tie-break is visible: both (F,+y) and (H,+x) sit at f=120,
and F's id of 4 pops before H's 6. Step 8 is where the AXIS tie-break is: two states for
the same node I at the same f, and `+x` before `+y`.

Eight pops. The winner is **A → D → G → H → I**, length 96", one bend, **cost 120**, and it
wins the tie against A → B → C → F → I on the axis rule at step 8 alone — both are 96" with
one bend. Two things a reviewer should confirm from the table:

* **going round the obstacle costs 2 bends, not 4.** Any path that hugged the inflated
  footprint's corners would take four turns and cost 96 + 96 = 192. The lattice has no nodes
  there to hug, which is the point of building candidate lines from *offset obstacle edges*
  rather than from a uniform grid.
* **the heuristic never over-estimates.** At every pop above, `h` ≤ the true remaining cost:
  at (C,+x), h=48 against a real remainder of 72 (48" of travel and one bend).

---

## 5. Deepest first, not cheapest first

`routing/tree.py` builds the DWV branch→main topology as a directed Steiner tree by repeated
shortest path (RSPH): route one terminal to the root, then route each remaining terminal to
the *tree*, with nodes already on it costing zero. That is the standard heuristic and it is
the right one. **The one domain change is the order.**

RSPH conventionally takes the cheapest terminal first. Gravity makes that wrong, and this
group is the counter-example.

**Slack, per terminal** — the head each has left over after its own minimum fall, where the
start ceiling comes from §3's chord window and the required arrival is the stack head at
115.5. **These are ordering keys, not build margins**, for the reason §2 gives: the arrival
is the stack head because a search does not yet know where on the barrel the tie will land.
The routes these produce tie in lower and hold far more fall than the table shows:

Routes are **rectilinear** — `|Δx| + |Δy|`, which is what the router produces and what §4's
lattice can express — not the straight lines of §1:

| terminal | dia. | start ceiling | rectilinear route | fall @ 0.25"/ft | slack |
|---|---|---|---|---|---|
| WC | 3" | 117.00 | 21.19 + 47.825 = 69.015" = 5.7513 ft | 1.4378" | **0.062"** |
| TUB | 1 1/2" | 117.75 | 41.615 + 58.325 = 99.94" = 8.3283 ft | 2.0821" | 0.168" |
| LAV | 1 1/2" | 117.75 | 9.5 + 65.2 = 74.7" = 6.2250 ft | 1.5563" | 0.694" |

The water closet has **about a tenth** of the lavatory's slack, and for two reasons that
compound: a 3" pipe's crown is 3/4" higher than a 1 1/2" pipe's for the same centreline, so
its start ceiling is 3/4" lower; and the tub, which is the physically longest run, is on the
smaller pipe and therefore has the higher ceiling to spend.

**Length is not a proxy for slack, and these three are the counter-example.** The tub has
the LONGEST route and the SECOND-tightest budget; the lavatory has a shorter route and four
times the head to spend. Order by length and you get WC, LAV, TUB; order by slack and you
get WC, TUB, LAV. The two agree about the water closet here **by luck** — its route happens
to be both the shortest and the tightest, by six inches of pipe — and disagree about
everything after it.

**Why the disagreement is not cosmetic.** RSPH routes each terminal to the *tree*, and
nodes already on the tree are free. So the second terminal routed takes the direct lane and
the third bends around whatever the first two built:

* **slack order** puts the tub second. It spends its 0.168" getting to the 3" at y=228,
  and the lavatory — with 0.694" in hand — bends around it and joins 18" further up.
  Both fit. This is what is authored.
* **length order** puts the lavatory second. It takes the lane at the elevation *its* own
  budget allows, and the tub arrives third with 0.168" and a tree that is now in its way.
  Its shortfall lands in `unserved`, and the honest report is "no feasible route for the
  fixture with the least head", which is the terminal a length-ordered search was always
  going to fail on.

**And the water closet's luck runs out one edit from here.** Move the lavatory six inches
closer to the stack, or the closet six inches further, and length order routes a 1 1/2" arm
first, straight down the lane the 3" needs. RSPH then joins the closet branch to the nearest
tree node, which is that arm: a **3" closet branch discharging into a 1 1/2" line.** Table
703.2 does not permit it, `mep.pipe_sizing` fails it, and the search reported a feasible
tree. Ordering by slack cannot produce that outcome, because the pipe with the least head is
always the pipe that gets the lane.

**So the ordering key is `required invert`, ascending** — the terminal whose route is most
nearly forced goes first, and the ones with slack bend around it. A terminal with no feasible
route lands in `unserved` with its shortfall in inches; it is never dropped.

---

## 7. Two lanes, and why there is no third

`routing/alternatives.py` offers more than one route by **penalty re-search**: route A is the
plain search, then the lanes A rode are multiplied by a factor and the search is run again on
the dearer copy, with every result re-priced on the *original* weights. §4's lattice is the
smallest world where the whole mechanism is checkable by hand, so it is reused here.

**The world is §4's**, unchanged: eight nodes, E removed, every edge 24", BEND = 24",
start A, goal I.

**How many simple paths are there, really?** Enumerate them. From A the only moves are to B
(+x) and to D (+y).

* Take **B**. B's surviving neighbours are A and C — E is gone — so the path is forced to C.
  C's are B and F, so it is forced to F. F's are C and I. Path: **A–B–C–F–I**.
* Take **D**. By the same argument through G and H: **A–D–G–H–I**.

A path may not revisit a node, so there are **exactly two**, and they share **no edge at
all**. Both are 96" of travel with one bend, so both cost **120**.

**Round 0.** The unpenalised search returns A–D–G–H–I — §4's answer, and the tie against
A–B–C–F–I is broken at the last pop by the axis rule, not by this module. **Route A must be
byte-identical to §4 and is.**

**Round 1.** A's legs are the vertical x = 0 from y = 0 to 48, and the horizontal y = 48 from
x = 0 to 48. The band round a leg is `max(2 × (radius + clearance), 12")`, and in this world
radius and clearance are both zero, so it is **12"**. The grid step is 24", so the band round
x = 0 reaches x = ±12 and catches the two edges *on* x = 0 and nothing on x = 24. Six edges
are tripled: A–D, D–G (x = 0, axis y) and G–H, H–I (y = 48, axis x). The penalised cost of
A–D–G–H–I is therefore 4 × 72 + 24 = **312**, and A–B–C–F–I is untouched at **120**, so the
second search returns it.

**Re-priced on the original graph it is 120**, which is the number a reader compares — not
the 120 it happened to have on the penalised copy, and never the 312 the incumbent was
quoted at there.

**Accepted?** Shared fraction is measured by length against every route already accepted.
The two are edge-disjoint, so it is **0.0**, comfortably under the 0.5 line. Accepted.

**Round 2.** Both lanes are now dear. Every edge in the world lies on one of them, so the
search returns whichever is cheapest — A–D–G–H–I again, at 312 penalised — and its shared
fraction against an accepted route is **1.0**. Rejected. Nothing changes on any later round,
and the loop stops at its `3 × k` bound.

**So `k = 3` yields exactly 2.** That is the assertion, and it is the one that matters: this
module returns *fewer* than asked rather than padding the list with the same route wearing a
jog. A lane that is the only lane is a fact about the building.

**What a reviewer should confirm from the above.**

* **The factor must be ≥ 1.** At 0.5 the tripled lane would be *halved* instead and round 1
  would return A–D–G–H–I at 60, which is the same route offered as an alternative to itself.
* **Nodes are never removed.** I is on both lanes and is penalised on round 2; it is still
  reachable, so a forced tie-in can always be reached. Deleting taken edges would have made
  round 2 report "no route" — a refusal manufactured by the alternatives machinery rather
  than by the building.
* **The band is a lane, not a line.** Penalising only literally-collinear edges would let a
  2" branch find "another route" one candidate line — sometimes a sixteenth of an inch —
  away from the one just offered.

---

## 8. A drain searched where it falls, by hand

`routing/gravity_search.py` puts the developed length **into the search state**, so the
invert is known at every relaxation rather than applied to a finished plan route. This
section is the smallest world where that changes the answer, and the answer it changes is
the important kind: the search returns a **dearer** route because the cheaper one runs out
of head at a truss.

**The world.** A 24" grid, two rows of four, every node at z = 0. Ids in `(z, y, x)` order,
as §4 states:

          y=24   E(4)   F(5)   G(6)   H(7)
          y= 0   A(0)   B(1)   C(2)   D(3)
                 x=0    x=24   x=48   x=72

**Start** A, **goal** D. Two simple paths, and they are the whole of the world:

* **S, the short one:** A→B→C→D. Three 24" edges, **72" of travel, 0 bends, 6.00 ft
  developed.**
* **L, the long one:** A→E→F→G→H→D. Five edges, **120" of travel, 2 bends, 10.00 ft
  developed.**

**The upper row is a corridor and the lower one crosses a bedroom.** E–F, F–G and G–H ride
a joist bay at `corridor_discount_per_ft` = 8, so each 2 ft edge prices at 24 − 2×8 = **8**.
B–C crosses a finished room and pays 24" of penalty on top of its travel, so it prices at
**48**. `BEND` is **6"** here rather than §4's 24", which is the only other change from §4
and is what makes the comparison turn on head instead of on fittings.

**Costs, on the plain search's ruler.**

| path | travel | bends | cost |
|---|---|---|---|
| S | 24 + 48 + 24 = **96** | 0 | **96** |
| L | 24 + 8 + 8 + 8 + 24 = **72** | 2 × 6 = 12 | **84** |

**So `search.shortest_route` returns L.** It is cheaper by twelve inches of equivalent
travel, and everything about that answer is correct as far as the plain search can see.

(The discount is 8 and not 12 for a reason worth stating: `heuristic_floor()` returns
1 − 8/12 = **1/3**, so the A* heuristic at A is 72 × 1/3 = 24, comfortably under L's true
84. Price the bay at zero without telling `RouteCost` and the heuristic stops being a lower
bound — A* then never pops E at all and returns S for the wrong reason, which looks exactly
like this section passing.)

**Now the gravity.** The flange sets the ceiling at **116.50"**; the grade is the code
minimum **0.25"/ft**; the tie at D accepts anything at or above **114.00"**. And `FS-ORACLE`
crosses the bay at the middle of edge F–G, where the truss's web gives the centreline
**115.50" … 116.50"**.

* **S at the goal.** 6.00 ft × 0.25 = 1.50" of fall. Invert at D = 116.50 − 1.50 =
  **115.00"**, which clears the 114.00" tie by a full inch. Nothing on S crosses `FS-ORACLE`.
* **L at the goal.** 10.00 ft × 0.25 = 2.50". Invert at D = **114.00"** — exactly the tie,
  and feasible. A head-budget test taken at the END would pass this route.
* **L at the truss.** The crossing is the midpoint of F–G. Developed there is
  (24 + 24)/12 = 4.00 ft to F, plus half of F–G's 2.00 ft, = **5.00 ft**. Invert =
  116.50 − 1.25 = **115.25"**, and the window's floor is 115.50". **L is 0.250" below the
  web and is not a route.**

That quarter inch is the whole of §8. It is invisible to a search that solves the plan and
then lowers the pipe, because by then the lane is chosen and the only report available is
"the head budget does not close" — about a budget that closes perfectly well at the goal.

**What the label-setting search returns: S, at 96.** Twelve inches dearer, and the only one
of the two that can be built.

**Why the Pareto frontier is needed, and why dominance is safe.** At one `(node, axis)` a
label carries a cost *and* a developed length, and neither implies the other: the corridor
buys length with money, which is exactly what L does. So a state keeps every label that is
not beaten on both. A label is dropped only when another is **no dearer and no longer** (and
starts no lower), and that is sound because every constraint tested is monotone in the
invert once the ceiling is fixed — a longer route arrives lower, and lower is worse at a
window and worse at a tie.

**The one case that is NOT monotone, and is refused rather than exploited.** An existing
run's prism could in principle be passed *under* by a longer route that has fallen further.
Those are treated as blocking anywhere in the drain's possible band, `[required, ceiling]`,
and the refusal says so. Lengthening a drain to slip beneath a duct is a decision with a
head cost somebody has to want; the search will not make it quietly.

**Rises never.** A vertical edge downward lowers the ceiling for the remainder — a drop is
free fall and takes no grade — and a vertical edge upward is not relaxed at all.

---

## 6. What this note does not do

* **No fittings.** Everything here grades polylines. A route that passes still has to be
  built out of elbows, wyes and closet bends that exist, and the offset in §2's flange drop
  is *called* a closet bend here because that is what it is, not because the engine knows.
* **No venting.** The trap arms are `mep.trap_arm_length`'s, and the vents were already drawn
  — `PR-S-SUITEBATH-VENT`'s own route is what told the branches where the intended lane was.
* **No claim of optimality.** A* over a candidate-line lattice is optimal *on that lattice*,
  and the lattice is built from obstacle edges, corridor centrelines and terminal coordinates.
  A cheaper route through a line nobody nominated will not be found, and the engine should
  not pretend otherwise.
* **No structural grading of a penetration.** §3's chord window is where a pipe *fits*. What a
  bored joist or a cut chord does to the floor is `structural.*`'s question, and an open-web
  truss is chosen precisely so the question does not arise.
* **The soft spot in the wall exemption is inherited.** `mep.run_in_finished_volume` treats
  any wall footprint as cover, and a 12" cast wall satisfies that while hosting nothing. A
  proposal must not "solve" a room crossing by hugging concrete.

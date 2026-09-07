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
flattest segment is 0.779"/ft against P3005.3's 0.25"/ft minimum. `mep.drain_slope` grades
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
and it is the whole argument of §5. Had the stack head stayed at 115.5 with the collector
tying there, rather than at 112 on the barrel below it, there would have been 1/16" in hand.

**The two 1 1/2" arms**, each tying onto the collector's south leg rather than onto the stack
(two wyes 18" apart on a 3" beats three pipes at one point):

| arm | route | plan length | start → end | flattest |
|---|---|---|---|---|
| LAV | (165.5, 268) ↓ → (165.5, 246) → (134.81, 246) | 22" + 30.69" = 4.3908 ft | 117.5625 → 116.25 | 0.293"/ft |
| TUB | (197.615, 261.125) ↓ → (197.615, 228) → (134.81, 228) | 33.125" + 62.805" = 7.9942 ft | 117.4375 → 115.0625 | 0.294"/ft |

Each end elevation is checked against the collector's own invert at that station, which is
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

So a **crossing** leg's outside must lie inside 109.625..118.5 — for a 3" pipe, a centreline
in [111.125, 117.0]. A leg **riding a bay** may use the full 108.125..120, because nothing is
in the way along it. Two different admissibility rules for the same pipe, decided by its
direction relative to `JoistSpec.direction`, and the reason a router that only knows "is it
in a bay" produces routes that cannot be built.

**Worked once for the collector.** Its south leg runs in y from 116.5 to 113.375: crown
118.0 ≤ 118.5 ✓, invert 111.875 ≥ 109.625 ✓. Its east leg runs in x at y=202.8, in the bay
between the y=192 and y=208 lines (clear 193.75..206.25): a 3" pipe spans 201.3..204.3, with
7.55" and 1.95" of clearance. Both admissible, by different rules.

---

## 4. One escape graph, by hand

Deliberately tiny, so a reviewer can redo it in five minutes and check the engine against it.
This is the spec for `routing/graph.py` and `routing/search.py`; the numbers here are what
`test_routing_oracle.py` asserts.

**The world.** A 3×3 lattice on a 24" grid. Nodes `N(i,j)` at (24i, 24j), i,j ∈ {0,1,2},
identified by `id = 3j + i`:

          y=48   G(6)   H(7)   I(8)
          y=24   D(3)   E(4)   F(5)
          y= 0   A(0)   B(1)   C(2)
                 x=0    x=24   x=48

**The obstacle.** A chase whose inflated footprint (`radius + clearance`, already applied)
covers node E. Every edge into E is removed; nothing else is.

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
| 2 | (B,+x) | 24 | 72 | 96 | (C,+x) g=48 f=96 — E is blocked |
| 3 | (C,+x) | 48 | 48 | 96 | (F,+y) g=48+24+**24**=96 f=120 |
| 4 | (D,+y) | 24 | 72 | 96 | (G,+y) g=48 f=96 — E is blocked |
| 5 | (G,+y) | 48 | 48 | 96 | (H,+x) g=48+24+**24**=96 f=120 |
| 6 | (F,+y) | 96 | 24 | 120 | (I,+y) g=120 f=120 |
| 7 | (H,+x) | 96 | 24 | 120 | (I,+x) g=120 f=120 |
| 8 | (I,+x) | 120 | 0 | 120 | **goal** |

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
115.5:

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

**Length alone does not give this ordering.** By route length the order is TUB (8.33 ft),
LAV (6.23), WC (5.75) — the water closet, whose route is nearly forced, sorts *last*. By
slack it sorts first. That is the entire content of "deepest first".

**Cheapest first fails, and fails in a way that looks like it worked.** Order LAV, TUB, WC:

1. LAV routes directly to the stack head, taking the x=134.81 lane south — the only lane that
   reaches the head without crossing the tub.
2. TUB routes to the tree, and the tree is now that 1 1/2" lane, which is free to join. It
   joins.
3. WC routes to the tree. Its nearest tree node is the 1 1/2" lane a few inches away, so RSPH
   discharges a **3" closet branch into a 1 1/2" arm.** Table 703.2 does not permit it,
   `mep.pipe_sizing` fails it, and the search reported a feasible tree.

**Deepest first works.** Order WC, TUB, LAV — by required invert, deepest first:

1. WC routes directly, spending 4.5" of its 5.5" available head on 5.7513 ft (0.782"/ft), and
   lands on the stack barrel at 112 rather than on its head at 115.5. That is what buys the
   margin the 0.062" figure above says it does not have: **the root is a vertical, and a
   vertical is a range of legal arrivals, not a point.** A router that models the root as a
   node loses this.
2. TUB routes to the tree and joins the 3" at y=228, arriving 0.0375" above its invert there.
3. LAV routes to the tree and joins the 3" at y=246, arriving 0.052" above its invert there.

Every join is a larger pipe receiving a smaller one, every arrival is above the receiving
invert, and `drain_tie_ins` derives the whole tree from the geometry alone.

**So the ordering key is `required invert`, ascending** — the terminal whose route is most
nearly forced goes first, and the ones with slack bend around it. A terminal with no feasible
route lands in `unserved` with its shortfall in inches; it is never dropped.

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

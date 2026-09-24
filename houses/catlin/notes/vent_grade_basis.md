# Vent grade — the oracle for `mep.vent_grade` and `mep.vent_grade_margin`

**House:** catlin, Minnesota. **Code:** MN Plumbing Code, Minn. R. ch. 4714, which adopts
the UPC. **Not IRC P3104.1** — Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33 and
P3104 is in chapter 31, so the section that governs a vent's grade here is **UPC 905.1**
(*Vent Grade and Connections*): vent pipes shall be free of drops and sags, and each vent
shall be graded and connected so as to drip back to the drainage pipe by gravity. This is
the same correction `notes/` and `checks/mep/plumbing_dwv.py` already carry for the drainage
half (UPC 708.0, not IRC P3005.3).

**Oracle for:** `checks/mep/vent_geometry.py`, both checks. Reproduced numerically by
`packages/engine/tests/test_vent_grade.py`.

The rule has two halves and this engine grades them as two checks, exactly as
`mep.drain_slope` / `mep.drain_slope_margin` split the drainage grade:

1. **`mep.vent_grade`, Tier.CODE** — *free of drops and sags*. Over a run's segments in
   path order (drainage connection → terminal) the elevation may never decrease. A vertex
   below both its neighbours is a low point; condensate collects there, the vent seals, and
   the trap seals it protects are siphoned by the next fixture that discharges. Vertical
   segments (zero plan length) are exempt: a riser holds no grade.
2. **`mep.vent_grade_margin`, Tier.ADVISORY** — the house's own **1/8"/ft**, from
   `plan/mep_venting.py`'s header ("fall ~1/8"/ft back toward the fixtures so condensate
   returns rather than pooling"). 905.1 states a *direction* and no figure, so a shortfall
   is reported as PASS with an `ADVISORY — ` prefix, the way `mep.equipment_turndown` reports
   an over-sized unit. It is not a code defect and nothing in the permit set gates on it.

Elevations below are inches, storey-relative as authored; a *difference* along one run is
the same number on any datum, which is why the check reads the profile without touching
`storeys`. Plan coordinates are inches in the project frame.

---

## 1. `PR-M-KITCH-VENT` — per-vertex elevations (the `z_m` branch)

Authored in `plan/mep_venting.py`: 1 1/2", serving `FX-M-KITCH-SINK`, six vertices with six
authored elevations. Since 2026-09-24 it ties into `PR-M-BATH2-VENT` rather than the chase.

| i | plan point (in) | elevation (in) |
|---|---|---|
| 0 | (392, 429) | `ft(9,3)` = 111 |
| 1 | (392, 232) | `ft(9,4)` = 112 |
| 2 | (187.3125, 232) | 112.5 |
| 3 | (187.3125, 212.75) | 114.45 |
| 4 | (98.5, 212.75) | 115.9 |
| 5 | (98.5, 212.75) | 116 |

Plan lengths (every leg is orthogonal, so each is one subtraction), and the rise across it:

    seg 0  429    − 232    = 197"      = 16.4167 ft    rise 112    − 111    = +1.000"
    seg 1  392    − 187.3125 = 204.6875" = 17.0573 ft  rise 112.5  − 112    = +0.500"
    seg 2  232    − 212.75 =  19.25"   =  1.6042 ft    rise 114.45 − 112.5  = +1.950"
    seg 3  187.3125 − 98.5 =  88.8125" =  7.4010 ft    rise 115.9  − 114.45 = +1.450"
    seg 4  riser at (98.5, 212.75)                     rise 116    − 115.9  = +0.100"

**`mep.vent_grade`: PASS.** Five segments, five positive rises, no drop and therefore no
sag. Four of five are horizontal, so the finding counts four.

Grades, rise ÷ plan:

    seg 0  1.000 / 16.4167 = 0.0609 "/ft
    seg 1  0.500 / 17.0573 = 0.0293 "/ft   <- flattest
    seg 2  1.950 /  1.6042 = 1.2156 "/ft
    seg 3  1.450 /  7.4010 = 0.1959 "/ft

**`mep.vent_grade_margin`: PASS with `ADVISORY — `.** The flattest leg is segment 1 at
**0.029"/ft**, under a quarter of the 1/8"/ft this house grades a vent to. It is held low on
purpose: it passes under `PR-B-CW-SUITE`, which is itself pinned under the suite tub's arm.
It does rise, so 905.1 is satisfied and no FAIL is issued.

## 2. `PR-M-BATH2-VENT` — two authored inverts (the interpolation, and the fallback)

2", `start_elevation=inch(115.9)`, `end_elevation=inch(116)`, three vertices and no
per-vertex tuple. The resolver interpolates over developed plan length, so every segment
comes out at the same grade and the check's two branches must agree on that number.

    A (79, 204)   → B (98.5, 204)   19.5"
    B (98.5, 204) → C (98.5, 266.5) 62.5"
    developed plan length           19.5 + 62.5 = 82" = 6.8333 ft

    grade = (116 − 115.9) / 6.8333 = 0.01463 "/ft, on every segment

**`mep.vent_grade`: PASS** (two segments, each +0.015"/ft × its own length, both positive).
**`mep.vent_grade_margin`: PASS with `ADVISORY — `** at 0.015"/ft, under 1/8"/ft.

Strip the resolved per-vertex tuple and the check's second branch reads the same run as one
segment of 6.8333 ft rising 0.100" — **0.015"/ft, the identical number**. That is the point
of the two branches being written from one profile: a legacy run with two inverts and a
routed run with six must not be graded against different arithmetic. (This section read
`PR-S-BATH1-VENT` until 2026-09-24, when that run took per-vertex elevations.)

## 3. The whole house, 2026-09-24

Nine vent runs, and the flattest horizontal leg of each:

| run | elevations | segments | flattest | verdict |
|---|---|---|---|---|
| `PR-B-BATH-VENT` | per-vertex | 2 (1 riser) | 1.699"/ft | PASS / PASS |
| `PR-B-SAUNA-VENT` | per-vertex | 9 (1 riser) | 0.093"/ft | PASS / advisory |
| `PR-M-WC-VENT` | per-vertex | 4 (1 riser) | 0.014"/ft | PASS / advisory |
| `PR-M-BATH2-VENT` | two inverts | 2 | 0.015"/ft | PASS / advisory |
| `PR-M-KITCH-VENT` | per-vertex | 5 (1 riser) | 0.029"/ft | PASS / advisory |
| `PR-S-BATH1-VENT` | per-vertex | 3 | 0.046"/ft | PASS / advisory |
| `PR-S-SUITEBATH-VENT` | per-vertex | 2 | 0.032"/ft | PASS / advisory |
| `PR-A-STUBATH-VENT` | per-vertex | 2 | 0.152"/ft | PASS / PASS |
| `PR-A-BAR-VENT` | per-vertex | 4 (1 riser) | 0.300"/ft | PASS / PASS |

**9 of 9 PASS the CODE check** — nothing in this house drops or sags on its way to a
terminal. Six of the nine hold less than 1/8"/ft and carry the advisory prefix; the two
attic runs and the basement bath vent are the only ones built at a grade a plumber would
recognise as a grade. The long runs are held flat by what they pass under — the ERV bank in
FS-S-WEST, the supply lines, the attic joists' flanges — and 905.1 does not ask for more.

## 4. What this does not claim

Not a venting *design*: whether a vent is required, where it may connect, its size and its
termination are `mep.vent_reachability`, `mep.vent_termination_height`, `mep.pipe_sizing`
and `checks/mep/vent_path.py`. This note is about one thing — the shape of the profile
between the drainage connection and the terminal.

## 5. The router: a vent never falls on its way to the stack

The oracle for `routing/search.shortest_route(rising=True)`, which `haus route` uses for
every vent and radon target (`routing/trades/pipe.rises`), and for the vent root being the
stack's own VENT riser (`cli/route_roots._stack_leg`). Reproduced by
`tests/test_routing_vent.py`.

MN 905.1 wants a vent graded to drain back to its drain. For a search that is one rule: no
step from the origin (the fixture end) to the root (the stack) may lose elevation. A vent
that dips under a duct and climbs back is a trap, however cheap its lane.

**The world.** A vertical section, x and z each at 0, 24 and 48 inches, all at y = 0. The
centre node (24, 24) is a duct and is absent. Costs are the §4 drain-note units, inches of
equivalent travel:

- a 24" horizontal step costs 24; on the top row (z = 48) it costs 60, which is 24 of
  travel plus 36 for crossing a finished room;
- a 24" vertical step costs 12, which is 24 x the 0.5 riser weight;
- each bend costs 24.

Node ids go in (z, x) order: 0 (0,0), 1 (24,0), 2 (48,0), 3 (0,24), 4 (48,24), 5 (0,48),
6 (24,48), 7 (48,48). The origin is node 3. The stack stands at x = 48, so nodes 4 and 7
are both on it.

**Unconstrained.** The cheapest route dips under the duct:

| route | steps | bends | cost |
|---|---|---|---|
| 3 → 0 → 1 → 2 → 4 (under) | 12 + 24 + 24 + 12 = 72 | 2 × 24 = 48 | **120** |
| 3 → 5 → 6 → 7 (over, onto the stack) | 12 + 60 + 60 = 132 | 1 × 24 = 24 | 156 |
| 3 → 5 → 6 → 7 → 4 (over, down to the root) | 132 + 12 = 144 | 2 × 24 = 48 | 192 |

A router without the rule proposes the first route: a 24" dip, which is a trap.

**Rising.** Step 3 → 0 loses 24", so the whole dip is refused. The only way off node 3 is up
to node 5, and 7 → 4 falls too, so the answer is **3 → 5 → 6 → 7, cost 156, one bend**. The
vent reaches the stack 24" higher than the node it was drawn to, which is where a vent
rising over a duct bank really meets the stack.

**Refusal.** Offer the stack only at node 4, the root's own level, and no rising route
exists. The search returns nothing, and the refusal is the finding: the lane has to go
somewhere else, or the stack has to be offered higher.

**Why the root is the stack, not the chase point.** A `VentRun` bundles its risers ±2.4"
either side of `chase_position` (`vent_termination.riser_polylines`). On catlin the chase
point is between the radon and vent risers, inside both envelopes, so a vent routed to it
was routed into the radon pipe. The root is now the VENT riser's own leg, clipped to the
vent's own elevation band plus 24" of headroom (`_STACK_HEADROOM_M`). The radon riser stays
a hard prism, and a terminal's one-step leniency covers only the prisms the terminal itself
stands in (`routing/graph.build_graph`).

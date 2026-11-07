# One ERV branch in a bay — the duct routing basis

**House:** catlin. **Run:** `DU-M-ERV-R-KITCH`, a 4" round ERV extract riding `FS-S-WEST`.
**Oracle for:** `typehaus/routing/trades/duct.py` and the corridor half of
`routing/corridors.py`. Reproduced by `tests/test_routing_oracle.py`.
**Companion:** `mep_drain_routing_basis.md`, which does the same job for gravity drainage.
Read §4 there for the escape graph and the A* expansion — this note does not repeat it.

**Why a second note at all.** A drain oracle covers gravity, and gravity is the thing a duct
does not have. What a duct has instead is a **section that must fit a bay** and a crossing
rule that is not the drain's, so an oracle covering only drains would overclaim on exactly
the constraint that decides a duct's route.

---

## 1. The terminal and the bay it has to reach

`DU-M-ERV-R-KITCH` is authored `DuctRouting.JOIST_BAY` with `floor_ref="FS-S-WEST"`, which is
the model saying out loud that this run is a corridor rider rather than a free route. Its
register is in the main floor's ceiling and its trunk is at the ERV; everything between is
one bay.

`resolve/mep_ducts` resolves it to a round section, so the radius the router inflates
obstacles by is `diameter / 2 = 1.5"`. For a **rectangular** duct the corresponding number is
half the larger plan dimension, because a rectangular duct turning a corner sweeps its own
diagonal and the router has no fitting model to say otherwise. That is the whole of
`trades/duct.py`'s radius rule and it is deliberately conservative.

---

## 3. The bay, and what "fits" means for a section rather than a pipe

Same derivation as the drain note's §3, and the same authored `JoistSpec` — repeated here in
the terms a duct is graded in.

    spacing 16" o.c., 2x4 flat chords 3.5" wide      ⇒  clear bay 12.5"
    bay centres                                       y = 8 + 16n
    truss depth 11 7/8", chord-to-chord 8 7/8"        ⇒  crossing window 109.625 .. 118.5

A 4" duct on a bay centre leaves (12.5 − 4)/2 = **4.25" either side.** Two 4" ducts in one
bay leave 12.5 − 8 = 4.5" between them if they are both centred on their own lanes, which is
buildable — and is exactly what `mep.duct_joist_bay_occupancy` reports UNKNOWN about on this
floor today, because the model gives each run **one centreline per bay** and so cannot place
two lanes side by side. **The router inherits that limit and must not paper over it:** a
proposal that puts a second duct in an occupied bay has to say so, not price it as free.

**The crossing rule is where duct and pipe part company.** A pipe crossing the trusses is
admissible when its outside fits the 8 7/8" window. A duct crossing is admissible only within
`open_web_opening_m` — the round hole the truss's own web geometry permits, which
`mep.duct_bay_occupancy` already grades and which is smaller than the chord-to-chord gap. A
router that reused the pipe rule here would propose crossings a fabricator would refuse.

---

## 3a. The panel layout: where along a truss there is an opening at all

§3 says how TALL the slot is. Until 2026-09-19 nothing said where along the member there was
a slot, so `profiles.open_web_opening_m`'s 8 7/8" window read as a **continuous chase** — and
thirteen 4" ducts crossing every truss inside a 41" band passed `mep.run_member_crossing`
without a word. A real truss has webs at panel points. A duct lands in an opening or it lands
on a web, and nothing bores, notches or moves a web.

**Superseded 2026-11-06 (decision #117):** FS-S-WEST is TrimJoist J12 and its published openings (`notes/open_web_truss_geometry.md`) replace this layout; the arithmetic below is history. **The datum was the owner's from 2026-10-26** — the fabricator builds to it. `params/second_deck.py`
authors the layout and says in its own `#:` how each number was arrived at (2x4 webs take the
opening to **13"**; the hand-work below was done at the earlier 15");
`mep.open_web_panel` reports UNKNOWN naming the floor for any deck that states none. What is
worked here is the ARITHMETIC that layout feeds, not the layout.

### Worked by hand on one truss — FS-S-WEST, `joist-0-019-0`

Authored: pitch **24"**, clear opening **15"**, offset **12"** from the member start.

    panel point n           at  12 + 24n
    web band either side    (24 − 15)/2 = 4.5"  ⇒  web occupies  12 + 24n ± 4.5"
    opening n               12 + 24n + 4.5  ..  12 + 24n + 19.5
      n = 0                 16.5" .. 31.5"        (1'-4.5" .. 2'-7.5")
      n = 1                 40.5" .. 55.5"        (3'-4.5" .. 4'-7.5")
      n = 2                 64.5" .. 79.5"        (5'-4.5" .. 6'-7.5")

**A run is clear when its whole outside is inside one opening**, so a run of outside
diameter *d* centred at station *s* needs `low + d/2 ≤ s ≤ high − d/2`, which leaves
`15 − d` of legal centreline in opening 1:

    4" galvanized duct   42.5" .. 53.5"   11.0" of legal centreline
    3" DWV (3.5" o.d.)   42.25" .. 53.75" 11.5"
    8" galvanized duct   44.5" .. 51.5"    7.0"

**Width along the MEMBER is not diameter.** A cylinder cut obliquely is an ellipse: a 4" duct
crossing the truss square occupies 4.00" of its length, the same duct at 45° occupies
4 / sin 45° = **5.66"**, and at 30° it occupies 8.00". The engine multiplies the outside
dimension by `|leg| / |component across the member lines|`, which is `1 / sin`.

### The over-subscription arithmetic, on the level-2 neck as drawn today

Nine radials leave the two `RM-M-MECH` plenums and cross the truss field in one x-lane. Each
is 4" galvanized, each crosses square, and all nine sit on `_BAY_Z` — one elevation.

    9 runs x 4.00" (square crossing)   =  36.00"
    opening 1's clear width            =  15.00"
    over by                            =  21.00"

**A TIER, not a sum.** Runs that share an elevation compete for one opening's width; runs
that STACK do not compete at all. Two 4" ducts at 111 5/8" and 116 1/2" — the two tiers the
8 7/8" window admits — use 4.00" of the opening each, not 8.00" between them. Summing them
would call a 15" opening full of two ducts that never meet, which is the same error
`resolve/mep_packing` was written to stop making about a bay's clear width.

So the honest reading of the neck is: 15" takes **three** 4" radials at one elevation
(3 x 4 = 12 ≤ 15; a fourth needs 16"), and the 8 7/8" window admits **two** tiers — so **six
radials through one opening, and nine are drawn.** Nothing rearranges that; three of them
take another opening, another tier, or another lane. That is D1's problem and this note only
prices it.

---

## 4. What the escape graph inherits, and the one thing it does not

The lattice, the `(node, incoming axis)` state, the bend penalty and the admissible Manhattan
heuristic are all §4 of the drain note, unchanged — a duct bends for the same reason a pipe
does and the search does not care which trade is asking.

One term is different and it is a **negative** one. `corridors.py` seeds candidate lines from
`joist_line_stations()` + `clear_bay_width_m()`, so every bay centreline is already a
candidate line, and a segment lying on one is priced **below** free travel. That is what makes
a duct proposal come out *in a bay* rather than merely *not through a joist* — the difference
between a route that passes `mep.duct_joist_bay` and one that was aimed at it.

`soffit_occupancy` supplies the same thing for a bulkhead: it reports each soffit's
*remaining* clear section, so a route into a box that is already full is priced out rather
than proposed. Neither discount may make a segment's cost negative in total — the heuristic
is admissible only if no edge is cheaper than its Manhattan length, so the discount is capped
at the travel term and never applied to the bend penalty.

---

## 5. Which z planes a 3-D lattice needs (2026-11-04)

A corridor's window `z_window(r) = (z0 + r, z1 - r)` is every centreline height at which a run
of radius `r` rides it, and `corridor_at` tests the window, not the midpoint. So a corridor
needs *a* plane inside its window, not a plane of its own. `graph._merged_levels` keeps the
terminals' z and an occupied bay's two tiers first, then adds an empty corridor's midpoint
only when no kept plane already lies inside that corridor's window.

Worked on `DU-B-ERV-R-SAUNA-SUP` (4" duct, r = 0.051 m), every window read off the space:

| Corridors | Window (m) | Midpoint | Kept plane inside the window |
| --- | --- | --- | --- |
| FS-M-* bays, FO-M-ERV-OA | -0.251 .. -0.051 | -0.151 | none yet: keep -0.151 |
| FS-SG-PORCH | -0.235 .. -0.051 | -0.143 | -0.151, merge |
| FS-BW-FLOOR | -0.157 .. -0.075 | -0.116 | -0.151, merge |
| SF-B-BATH | -0.530 .. -0.352 | -0.441 | terminal -0.494, merge |
| FS-S-WEST (occupied) | 2.797 .. 2.997 | tiers 2.797, 2.997 | anchors |
| FS-SG-BALCONY | 2.737 .. 2.982 | 2.860 | 2.797, merge |
| FS-S-EAST, FO-S-* chases | 2.797 .. 2.997 | 2.897 | 2.797, merge |
| SF-S-HP1 / SF-S-DUCT | 5.261 .. 5.744 / 5.486 .. 5.744 | 5.502 / 5.615 | 5.615 merges into 5.502 |

13 planes become 7 and the lattice 545,331 → 281,426 nodes (cap 500,000). A merged plane
sits at a window's edge, which is the run hard against a chord: legal by the window's own
definition, and the same reading §3a gives the two FS-S-WEST tiers.

---

## 6. What this note does not do

* **No fittings, no pressure drop.** Everything here is centrelines and sections. Whether the
  proposed route's total equivalent length fits the fan is `mep_erv`'s question, and the ERV
  static budget is its own recorded fight (0.4", not 0.2" — see `plans/TODO.md`).
* **No balancing.** A route that reaches a register says nothing about the register getting
  its design cfm.
* **No claim about two ducts in one bay.** The model cannot place two lanes; §3 says so and
  the router says so.

---

## 7. Laying length: what a turn costs in straight duct (wave 0, 2026-11-07)

Worked by hand from the `DuctStandard` rows in `plan/ducts.py` and the geometry authored in
`plan/mep_erv_l2.py`, before E3 codes `routing/duct_fittings.py`. Inches throughout. Read once
more in `plan/ducts.py`, `resolve/duct_standard.elbow_for_turn` and `checks/mep/fitting_pattern.py`
(whose `_takeoff_in` / `_floor_in` this section re-derives rather than copies).

**The rule.** A turn of angle theta takes `R tan(theta/2)` of straight from each leg, with R the
elbow's centre-to-face at 90 degrees (`DuctElbowRow.center_to_face`; at 90 degrees tan 45 = 1, so
R = C2F). A straight between two turns has to be at least the sum of their take-offs; a straight
between a turn and a run end (collar, port, tee, terminal) owes only the turn's own. Short of the
sum is UNKNOWN; short of the **floor** (the same sum at R = D/2, the tightest throat made) is FAIL
(`mep.fitting_pattern`, 1/16" tolerance). `elbow_for_turn` picks the row: a stamped elbow within
10 degrees of 45/90 first, else the adjustable 90 set down (angles to 100 degrees), else none.

**What is read and what is not.** The stamped Linx E90/E45 rows carry **no `center_to_face`**
(`plan/ducts.py`: "The stamped laying length is unpublished: 1.5 D stands in"). The only
published laying length is the C.L. Ward adjustable's dimension A, read as C2F: **4.75 / 6 / 7"**
at 4 / 6 / 8" (`plan/ducts.py` `DuctElbowRow` rows, source `notes/air_distribution_products.md`
"DuctStandard"). So the table has three columns and E3's test must carry C2F as a parameter:

* **stamped, 1.5 D stand-in** (R = 6 / 9 / 12): what `mep.fitting_pattern` uses today
  (`library/fittings.py` gored radius). Unpublished; conservative.
* **stamped, 1.0 D** (R = 4 / 6 / 8): the r/D the Linx loss C 0.22 was taken at (Fitting 3-1).
  Also unpublished. The two stand-ins disagree by 50% and the note cannot settle it.
* **adjustable, A read as C2F** (4.75 / 6 / 7): published.

### 7.1 Take-off per turn (inches)

| D | stamped 90, R=1.5D | stamped 45, R=1.5D | stamped 90 / 45, R=1.0D | adjustable 90 / 60 / 45 / 30 | floor 90 / 45 |
|---|---|---|---|---|---|
| 4" | 6.000 | 2.485 | 4.000 / 1.657 | 4.750 / 2.742 / 1.968 / 1.273 | 2.000 / 0.828 |
| 6" | 9.000 | 3.728 | 6.000 / 2.485 | 6.000 / 3.464 / 2.485 / 1.608 | 3.000 / 1.243 |
| 8" | 12.000 | 4.971 | 8.000 / 3.314 | 7.000 / 4.041 / 2.899 / 1.876 | 4.000 / 1.657 |

(tan 22.5 = 0.41421, tan 30 = 0.57735, tan 15 = 0.26795; 4" stamped 45 at 1.5 D is 6 x 0.41421 =
2.485.) Catlin uses round 4" (every radial), 6" (trunks, risers, HP-FEED, the HP bedroom feeds) and
8" (OA, EA, the level-2 extract trunk).

### 7.2 Minimum straight between two consecutive turns (sum of take-offs)

| D | basis | 90 + 90 | 90 + 45 | 45 + 45 | floor 90+90 / 90+45 / 45+45 |
|---|---|---|---|---|---|
| 4" | stamped 1.5 D | 12.000 | 8.485 | 4.971 | 4.000 / 2.828 / 1.657 |
| 4" | stamped 1.0 D | 8.000 | 5.657 | 3.314 | |
| 4" | adjustable | 9.500 | 6.718 | 3.935 | |
| 6" | stamped 1.5 D | 18.000 | 12.728 | 7.456 | 6.000 / 4.243 / 2.485 |
| 6" | stamped 1.0 D = adjustable | 12.000 | 8.485 | 4.971 | |
| 8" | stamped 1.5 D | 24.000 | 16.971 | 9.941 | 8.000 / 5.657 / 3.314 |
| 8" | stamped 1.0 D | 16.000 | 11.314 | 6.627 | |
| 8" | adjustable | 14.000 | 9.899 | 5.799 | |

E3's A* state (straight since the last turn) refuses a turn whose predecessor's take-off plus its
own exceeds the straight carried; test the numbers above with C2F injected, not the house default.

**Implemented (E3, 2026-11-07):** `routing/duct_fittings.py` (take-off, elbow choice, kit lead) and
`routing/duct_search.py` (the fitted A*: a label carries `slack` = straight since the last turn
less that turn's take-off, capped at one take-off; a lattice turn is always 90 degrees, so one T
per run). Every lattice turn on a 4" run therefore needs 12.0" behind it at the 1.5 D stand-in, and
the last straight into a run end 6.0". `tests/test_routing_duct_fittings.py` asserts §7.1-§7.2
with R injected, §7.3's 1.096, and §7.5's 12.579.

### 7.3 Worked route A: `DU-M-ERV-R-BED2`, 4", clean (0 gaps)

Authored (`mep_erv_l2.py`, resolved z, inches): P0 (45.75, 168, 111.625) -> P1 (192, 168, 111.625)
-> P2 (192, 178, 116.5) -> P3 (192, 210, 116.5) -> P4 (192, 220, 111.625) -> P5 (337, 220, 111.625).
The two tiers are FS-S-WEST's 111 5/8" and 116 1/2" (§3a).

| vertex | in-leg | out-leg | turn | stock | take-off (1.5 D / adj) |
|---|---|---|---|---|---|
| 1 | (146.25, 0, 0) | (0, 10, 4.875) | 90.00 | stamped 90 | 6.000 / n.a. |
| 2 | (0, 10, 4.875) | (0, 32, 0) | atan(4.875/10) = 25.99 | adjustable, set down | 4.75 tan 12.995 = 1.096 |
| 3 | (0, 32, 0) | (0, 10, -4.875) | 25.99 | adjustable | 1.096 |
| 4 | (0, 10, -4.875) | (117, 0, 0) | 90.00 | stamped 90 | 6.000 |

(25.99 is outside the 45 +- 10 snap and inside the 90 set-down's range, so the jog's two 26-degree
turns are Ward adjustable 90s; 6.000 is the stand-in at the stamped 90.) Straights:

    P0-P1   146.250 vs 6.000                      ok (a run end owes nothing)
    P1-P2    11.125 vs 6.000 + 1.096 = 7.096      ok   (sqrt(10^2 + 4.875^2) = 11.1245)
    P2-P3    32.000 vs 1.096 + 1.096 = 2.192      ok
    P3-P4    11.125 vs 1.096 + 6.000 = 7.096      ok
    P4-P5   117.000 vs 6.000                      ok

**Expected `fitting_pattern_gaps` = 0** at every basis in §7.1 (the tightest, 1.5 D, leaves 4.03").
This is the baseline too: no `mep.fitting_pattern` finding names this run
(`scratchpad/baseline/check_nosuppress.txt`).

### 7.4 Worked route B: `DU-M-ERV-R-LIVING`, 4", one short straight

Authored: P0 (57, 404, 101.25) -> P1 (57, 404, 111.625) -> P2 (67.5, 404, 111.625) -> P3
(67.5, 356.219, 111.625) -> P4 (67.5, 347.781, 116.5) -> P5 (67.5, 162, 116.5) -> P6 (67.5, 152,
111.625) -> P7 (324, 152, 111.625). Turns: v1 90 (up to east), v2 90 (east to south), v3 and v4
atan(4.875/8.438) = 30.02 (adjustable, 1.273), v5 25.99 (adjustable, 1.096), v6 90.

    P1-P2    10.500 vs v1 + v2 = 6.000 + 6.000 = 12.000   SHORT 1.500   (1.5 D)
                       4.75 + 4.75 = 9.500  ok, 1.000 spare              (adjustable)
                       4.000 + 4.000 = 8.000 ok, 2.500 spare             (1.0 D)
    P2-P3    47.781 vs 6.000 + 1.273 = 7.273     ok
    P3-P4     9.745 vs 1.273 + 1.273 = 2.546     ok   (sqrt(8.438^2 + 4.875^2))
    P4-P5   185.781 vs 1.273 + 1.096 = 2.369     ok
    P5-P6    11.125 vs 1.096 + 6.000 = 7.096     ok
    floor P1-P2 = 2.000 + 2.000 = 4.000 <= 10.5, so UNKNOWN, never FAIL.

**Expected gaps = 1 at the 1.5 D stand-in (as authored today: baseline reads "10.5" between vertex
1 and 2 against 12.0""), 0 at 1.0 D and at the adjustable's A.** `DU-M-ERV-R-BED` is the same
shape (10.5" vs 12.0", baseline). The fix a router would find is the jog lane at x >= 69.0 (12.0"
off the collar riser), not a different fitting. Reading Linx's published centre-to-face closes
the question for every run in the house; until then the 1.5 D result is the conservative one.

### 7.5 A pattern gap that is not a laying-length gap: `DU-B-ERV-R-GYM`

Baseline: vertex 4 (18.2) and vertex 7 (95.3) "no catalogued pattern", and **no** straight
reported. Hand reading disagrees on both counts, because two snaps are in play: `library/fittings`
matches a stock duct elbow within **5** degrees of 30/45/90, while `elbow_for_turn` (what is
bought) snaps within **10** of the stamped 90/45 and takes the adjustable below that. 95.27 is a
bought stamped 90 and 18.2 an adjustable set down, yet the catalog calls both "no pattern", and
`_takeoff_in` then returns 0 for the 95.3 (stamped row has no C2F, spec is None), hiding a real
short straight: P7 (204, 160, -25.438) -> P8 (204, 160, -19.313) is 6.125 vertical against the 95.27
turn's 6 tan 47.64 = 6.579 plus P8's 90 turn 6.000 = **12.579**. Floor 2.193 + 2.000 = 4.193 <= 6.125,
so UNKNOWN. **Request to E3: one snap (the DuctStandard's 10), so the catalog and the bill cannot
disagree.** Expected for GYM then: 0 pattern gaps, 1 short straight (6.1" vs 12.6") at 1.5 D.

Rectangular runs are out of scope: `DU-S-HP-RET` (2 turns), `DU-S-HP-SOUTH` (2), `DU-S-HP-SOUTH-RISE`
(1) stay "fabricated, no throat radius" (5 turns, 3 runs, unchanged). No rectangular throat radius is
read in this repo, so a fabricated elbow is last-resort and priced only; nothing here sets its R.

## 8. Flex and the PortKit lead (wave 0, 2026-11-07)

**Read.** Broan B210E75RT manual pp. 10-11, as quoted in `notes/air_distribution_products.md`
"Port kits": "If using 8-in. ducts, install 6-in. to 8-in. transitions on the ports ... If rigid
ducting is used, install a 12-in. section of flexible duct between the transition and the rigid
ducting." Kit rows in `plan/ducts.py`: outdoor and exhaust = GV0772 6-to-8 increaser +
`flex_length` 12"; supply and return = 12" flex only (the ducts are 6", the ports are 6").
**Not on file:** the increaser's length (Imperial prints SKUs and gauges, no dimensions;
`PortKit.transition_length` is None), and **any flex minimum bend radius**.
`PROD-DUCT-FLEX-R8` (JP Lamborn MHP-45R8) carries a UL class and an R value only, and
`DUCT-T-FLEX-6.bend_equivalent_length` (84") is a pressure-loss length, not a radius. Flex support
is 5 ft (`DuctSupportRow`, SMACNA S3.35). So E3 models the flex as a **straight lead that never
bends**; if a radius is later read, it is a new `PortKit` field, not a default.

**The lead.** Distance from the port face to the first rigid turn's vertex
= transition length (unread, count 0 and print the gap) + 12.000 flex + take-off of the first turn.

Worked at the **supply port** (EXACT, 6", `EQ-B-ERV` at (80.44, 358), port local (8.21875, 6.625),
direction +z; resolved port (88.656, 364.625, -33.838)):

    kit lead (flex only)          12.000
    first turn, stamped 6" 90     + 9.000  (1.5 D)    = 21.000 to the vertex
                                  + 6.000  (adjustable A, or 1.0 D) = 18.000
    existing `route_ports` stub   6.0 + 2.0 allowance = 8.000  (shorter than the flex alone)

`route_ports.stub_length_m` (OD + 2") is therefore not a PortKit lead; E3 replaces it for ports
whose type has a kit and keeps it elsewhere. **The authored `DU-B-ERV-SUP-TRUNK` is 10.401" long**
(z -33.838 to -23.437, no turns): 1.599" short of the 12" flex before any fitting, so the lead
check will report it. That is H1's geometry (the ERV re-layout), not a router fault.

At an 8" leg (outdoor/exhaust, ports approximate until H1): lead = L(GV0772, unread) + 12.000 +
first turn at 8" (12.000 stamped 1.5 D; 8.000 at 1.0 D; 7.000 adjustable) = L + 24.000 / 20.000 /
19.000. **Test assertions:** flex 12.000, supply lead 21.000 and 18.000, the transition length
reported as unread (not 0 silently), and `DU-B-ERV-SUP-TRUNK` short by 1.599".

**Implemented (E3):** `cli/route_ports.py` lays the kit lead (`duct_fittings.kit_lead`) in place
of the OD + 2" stub at a kitted port, the search leaves its tip along the lead with no slack, and a
run whose far end stands on the lead is refused with the shortfall (DU-B-ERV-SUP-TRUNK: the model
reads 10.400" from port to far end, so 1.600"; this section's 10.401 rounds the endpoints first).

**Open.** Broan's manual also says insulated ducts "must have the same diameter as the ports to
ensure proper drainage", which contradicts its 8" advice (`air_distribution_products.md`): the
lead model is the same either way, only the transition drops out.

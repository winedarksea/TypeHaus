# One cold trunk and its tree, by hand — `PR-B-CW-TRUNK`

**House:** catlin. **Run:** `PR-B-CW-TRUNK`, 1 1/4" PEX-a cold, the basement-ceiling trunk fed by
`PR-G-SERVICE-CW`. **Oracle for:** `routing/supply_tree.py` and `cli/cmd_route_supply_tree.py`
(E4), rows `tree:CW-TRUNK` and `trunk:CW`. **Written:** 2026-11-07, wave 0, before the code.
**Companions:** `mep_drain_routing_basis.md` §11 (PEX bend, the supply cost terms) and §12 (rack);
§5 there for the Steiner order this note mirrors for supply.

**Source of every number.** The authored `PipeRun`s in `plan/mep_supply*.py` as resolved
(project-frame inches; basement datum is -109.4375"), summed leg by leg with
`developed = sum of 3-D segment lengths` (the same formula as `RouteProposal.developed_ft`).
No router output is used. Branch tees are found geometrically: a branch's first vertex lies on
the trunk's polyline (gap 0.00" on all 13).

---

## 1. The source and the trunk

`PR-G-SERVICE-CW` (1 1/4", 13.50 ft, buried at -106", street entry (11'-4", 48'-6") to the house)
ends at (136, 420, -106.0); the trunk begins at (136, 420, -107.4375) and **tees onto that end**
(`mep_supply.py`: "two runs sharing an origin are siblings"). The service is the tree's root
and is **not** part of the trunk's length. Authored `serves`: 23 fixtures (every cold fixture,
the two south hydrants, and `FX-G-HYDRANT`).

### 1.1 The trunk, leg by leg (19 points, 18 legs; z project-frame)

| leg | from (x, y, z) | to | developed (in) | what it is |
|---|---|---|---|---|
| 0-1 | (136, 420, -107.44) | (136, 420, -61.44) | 46.000 | riser, lateral to 4'-0" over slab |
| 1-2 | | (136, 420, -14.80) | 46.638 | riser to the old 7'-10 5/8" band |
| 2-3 | | (136, 418, -14.80) | 2.000 | jog south, y 35'-0" to 34'-10" |
| 3-4 | | (114, 418, -14.80) | 22.000 | west |
| 4-5 | | (114, 418, -8.80) | 6.000 | step up at x=9'-6" to the cold band |
| 5-6 | | (57, 418, -8.80) | 57.000 | west |
| 6-7 | | (57, 418, -16.00) | 7.198 | dip under FO-M-ERV-OA's packs |
| 7-8 | | (57, 386.5, -16.00) | 31.500 | south under the packs |
| 8-9 | | (57, 386.5, -8.80) | 7.198 | climb back |
| 9-10 | | (57, 192, -8.80) | 194.500 | south to y=16'-0" |
| 10-11 | | (96, 192, -8.80) | 39.000 | east |
| 11-12 | | (200, 192, -8.80) | 104.000 | east |
| 12-13 | | (200, 180, -8.80) | 12.000 | south onto the truss-bay line |
| 13-14 | | (357.6, 180, -8.80) | 157.600 | east through the FS-M-NE bay |
| 14-15 | | (357.6, 424.2, -8.80) | 244.200 | north through the web opening |
| 15-16 | | (357.6, 424.2, +10.56) | 19.363 | riser, 100 5/8" to 120" basement-relative |
| 16-17 | | (357.6, 421.5, +10.56) | 2.700 | jog |
| 17-18 | | (357.6, 421.5, +20.00) | 9.437 | riser to the sink stop |

    total = 1,008.334 in = **84.028 ft** (every leg is axis-aligned: 866.500 in of plan travel +
    141.834 in of vertical).

(Duplicate-vertex pairs in the source, e.g. points 0..2 at one (x, y), are the vertical legs above.)

## 2. Every branch, and where it tees

`s` is developed distance along the trunk from its first vertex. Eleven tees land on the cold band
at z = -8.80; the hydrant tees on the riser (z = -61.44) and `COLDSTORE-STUB` at the trunk's end (z = +20.0).

| branch (dia., material) | tee point | s (ft) | branch developed (ft) | fixtures |
|---|---|---|---|---|
| `PR-G-HYDRANT-CW` (3/4" pex) | (136, 420, -61.44) riser | 3.83 | 23.56 | 1 (buried, outdoors) |
| `PR-B-CW-WH` (1" copper) | (57, 192) | 35.00 | 23.15 | 0 (the heater; feeds `PR-B-CW-BATH`) |
| `PR-B-CW-BATH1` (3/4") | (57, 192) | 35.00 | 12.68 | 2 |
| `PR-B-CW-BATH2` (3/4") | (57, 192) | 35.00 | 13.73 | 2 |
| `PR-B-CW-SBATH` (3/4") | (57, 192) | 35.00 | 30.52 | 5 |
| `PR-B-FILLER-CW` (1/2") | (71.25, 192) | 36.19 | 3.08 | 2 |
| `PR-B-CW-HYD` (3/4") | (72, 192) | 36.25 | 3.00 | 2 |
| `PR-B-BATH2-SH-CW` (1/2") | (84, 192) | 37.25 | 7.64 | 1 |
| `PR-B-CW-WASH` (3/4") | (100, 192) | 38.59 | 14.65 | 2 |
| `PR-B-CW-SUITE` (3/4") | (110, 192) | 39.42 | 26.60 | 3 |
| `PR-B-BATH-WC-CW` (1/2") | (139.5, 192) | 41.88 | 17.54 | 1 |
| `PR-B-CW-SAUNA` (1/2") | (206.5, 180) | 48.46 | 13.72 | 1 |
| `PR-M-CW-COLDSTORE-STUB` (1/2") | (357.6, 421.5, +20) the END | 84.03 | 29.18 | 0 (an unserved stub) |

Four branches share one tee at (57, 192, -8.8), the corner where the trunk turns east: WH, BATH1,
BATH2 and SBATH. Their third-and-deeper descendants (BATH on WH; the STUBATH chain on SUITE; the
hydrant risers on HYD) are in §3.

Worked leg by leg, one branch (`PR-B-CW-WASH`, 3/4" PEX): (100, 192, -8.8) -> (100, 245.25, -8.8) =
53.252 in; up to z=0 = 8.800; up to z=+32 = 32.000; west to (100, 217) = 28.252; east to (102.5, 217)
= 2.500; east to (141.5, 217) = 39.000; down to z=+20 = 12.000; total **175.804 in = 14.650 ft**.

## 3. The tree, deeper, and the four totals

The cold network downstream of the trunk has 40 runs (the service lateral is upstream). Where each starts on another cold run
(geometrically, not at that run's own start) gives the parent graph; the groups below sum a
branch and everything it feeds:

| top branch | subtree total (ft) | runs | farthest end from source (ft) |
|---|---|---|---|
| `PR-B-CW-SBATH` | 80.23 | 6 | 95.44 (`PR-S-BATH1-WC-CW`) |
| `PR-B-CW-SUITE` | 75.23 | 9 | 92.60 (`PR-A-STUBATH-SH-CW`) |
| `PR-B-CW-HYD` | 45.16 | 8 | 77.65 (`PR-M-CW-PORCH-HYD-CU`) |
| `PR-B-CW-WH` | 45.10 | 4 | 69.24 (`PR-B-LAV-TERMINAL-CW`) |
| `PR-B-CW-SAUNA` | 13.72 | 1 | 62.19 |
| `PR-B-BATH-WC-CW` | 17.54 | 1 | 59.42 |
| `PR-B-CW-BATH2` | 24.56 | 3 | 57.13 (`PR-M-BATH2-LAV-CW`) |
| `PR-B-CW-WASH` | 14.65 | 1 | 53.24 |
| `PR-B-CW-BATH1` | 15.54 | 3 | 47.80 |
| `PR-B-BATH2-SH-CW` | 7.64 | 1 | 44.89 |
| `PR-B-FILLER-CW` | 3.08 | 1 | 39.27 |
| `PR-G-HYDRANT-CW` | 23.56 | 1 | 27.39 |
| `PR-M-CW-COLDSTORE-STUB` | 29.18 | 1 | 113.20 (unserved) |

**Authored totals, the numbers the 1.1x acceptance divides:**

| scope | authored (ft) | 1.10x limit (ft) | row |
|---|---|---|---|
| S1 trunk alone | **84.028** | 92.431 | `trunk:CW` (E4: "splits trunk and branch proposals") |
| S2 trunk + 13 direct branches | 303.075 | 333.383 | informational |
| S3 trunk + all 40 downstream cold runs | 479.204 | 527.124 | upper bound |
| S3' S3 less the two unserved stubs (`COLDSTORE-STUB` 29.175, `PLANT-STUB` 0.250) | **449.779** | 494.757 | `tree:CW-TRUNK` (what the 23 fixtures need) |
| S3'' S3' less the buried hydrant branch (23.556) | 426.217 | 468.845 | if E4 keeps outdoor runs out of the tree |

E4 must say which scope each row compares against; **recommended S1 and S3'**. A router's tree
shares segments (one pipe feeds several fixtures), so S3' is also the right yardstick for a
Steiner total. A proposal under S1 that merely rebuilds the same 84.03 ft is the pass; one near 92.4
ft is the boundary.

## 4. The order: farthest first

Key = developed distance from the source to the **farthest fixture end in the subtree** (so the
branch that reaches farthest is routed first and the shorter ones tee onto what exists, the same
reason §5 of the drain note routes deepest first). From §3 the order of the 12 served top
branches, authored:

    1 SBATH 95.44   2 SUITE 92.60   3 HYD 77.65   4 WH 69.24   5 SAUNA 62.19   6 BATH-WC 59.42
    7 BATH2 57.13   8 WASH 53.24   9 BATH1 47.80   10 BATH2-SH 44.89   11 FILLER 39.27
    12 HYDRANT 27.39

At fixture level the five farthest are `PR-S-BATH1-WC-CW` 95.44, `PR-A-STUBATH-SH-CW` 92.60,
`PR-A-BAR-LAV-CW` 90.09, `PR-A-STUBATH-LAV-CW` 89.01, `PR-S-BATH1-SH-CW` 85.00 ft. The
farthest-by-Euclidean order may differ; the test should pin that the **first** branch routed
contains `FX-S-BATH1-WC` and that no later branch is farther than an earlier one by developed
distance.

## 5. The z gate: where a trunk may ride, and why

Three bands appear in the authored trunk (project z, inches; basement-relative in brackets):

| band | z | where | why |
|---|---|---|---|
| cold band | **-8.80** [100 5/8"] | legs 4-5, 9-17: the whole ceiling run | inside the floor members' depth |
| old band | -14.80 [94 5/8"] | legs 1-4 | below the joists; only where no joist/blocking is crossed |
| dip | -16.00 [93.44"] | legs 6-9 | under FO-M-ERV-OA's LVL packs (a 2" bore max, `mep_supply.py`) |

**Cold band, as a window.** 1 1/4" PEX is 1.375" OD (`pipe_sections.TUBE_OD_IN`), radius 0.6875".
The I-joist web window (TJI 230, `mep_supply.py`, CW-WH comment) is -10.500 .. -1.375; the
FS-M-NE truss chord window (99 1/16" .. 107 15/16" basement-relative) is -10.375 .. -1.500.
The centreline gate is therefore, per window,

    I-joist: -10.500 + 0.6875 = -9.8125  <=  z  <=  -1.375 - 0.6875 = -2.0625
    truss:   -10.375 + 0.6875 = -9.6875  <=  z  <=  -1.500 - 0.6875 = -2.1875
    both:    [-9.6875, -2.1875]; authored -8.80 is 0.8875 above the floor of the gate.

At -8.80 the crown is -8.1125 and the invert -9.4875: **crown 6.7375" and invert 1.0125" clear
of the I-joist window** (the 6.737 / 1.013 the plan comment quotes), invert 0.8875" in the truss
window. **Where the trunk crosses a joist line it must be inside this window; where it rides a
bay it may use the full depth.** The drilled hole is OD + 1/4" = 1.625" (the 2" row of ESR-1153
Table A, `notes/framing_bore_limits.md` §11), 12" from an end support face: at x=200 a hole
sits 213.25 - 200 - 0.8125 = 12.44 in from the x=213.25 face, which is why leg 11-12 turns
south at x=200 (`mep_supply.py` comment). A truss-web lane: leg 14-15 at x=357.6 is inside the
353.5 .. 366.5 opening every truss shares: 357.6 - 0.6875 - 353.5 = 3.41 clear on the west side and 366.5 - 357.6 -
0.6875 = 8.21 on the east.

**Below the drains.** In this house the cold is **above** the DWV mains it crosses, not below
(`mep_supply.py`: the cold band rides "-0'-8.8", 5.45" over" `PR-B-MAIN-DRAIN`'s crown at
y=22'-4", crown -14.25). A gravity pipe wants the high end of the depth; the trunk must therefore
stay at or above its band wherever a drain is crossed, and the router should take the drain's crown
as a floor, not the joist window. Clearances beyond the one quoted are not restated here.

**Hot and cold separation.** Hot rides `-12.0` [97 7/16"], jacket tucked 0.1" under the flange;
the pair needs 1.875" between centres to be two pipes (`mep_supply.py` "two-band convention"):
here 3.2". The trunk's gate is not the hot's: the hot band is not a legal cold band.

**PEX turns, §11.** R = 6 x OD = 8.25" for the trunk; the 90-degree corners are PEX elbows
(a catalogued pattern), and an off-stock turn is a bend needing R tan(theta/2) of tube each side,
shared legs counting half (`resolve/mep_fittings._bend`). The trunk has no bend; the baseline's one
PEX bend gap is `PR-S-VANITY-LAV2-CW`'s 108.5 degrees on a 2.9" leg, elsewhere.

## 6. Expected outcome and what E4's tests should assert

**0 refusals, 0 evaluation fails.** The 23 fixtures are all served by the authored lanes at the
cold band, so a farthest-first tree with those lanes available has nothing to refuse. Two
authored features come from obstacles the router must see or it will propose across them: the
dip at legs 6-9 exists only because of FO-M-ERV-OA's LVL packs (a 2" bore maximum), and the
step at x=114 only because of the bearing-line blocking (`mep.run_through_blocking`).

Assert, with the §1-§3 values (tolerance 0.05 ft):

* trunk developed 84.028 ft, 18 legs, plan 866.5 in;
* 13 tees at the §2 `s` values (3.83, 35.00 x4, 36.19, 36.25, 37.25, 38.59, 39.42, 41.88,
  48.46, 84.03);
* order 1 SBATH, 2 SUITE, 3 HYD, 4 WH, 5 SAUNA ... 12 HYDRANT (§4);
* `trunk:CW` <= 92.43 ft; `tree:CW-TRUNK` <= 494.76 ft (S3'), or the scope E4 names;
* every horizontal cold-band leg's centreline z in [-9.6875, -2.1875] where it crosses a joist/truss line.

## 7. Not done / open

* The router's tree is built from fixture **ports**, not the authored runs; if the fixture-end
  geometry differs (a stub offset) the authored sums are a yardstick, not an identity.
* `PR-B-CW-WH` is 1" copper (the heater's own cold feed) and `PR-B-HW-*` are hot: a cold tree
  does not route them.
* No water-hammer, pressure-loss or sizing is graded here (`mep.pipe_sizing` owns Table 610.4).
  The trunk stays 1 1/4" at 39 WSFU (`mep_supply.py` comment).
* Question for E4: does `--topology trunk` count the service lateral (13.50 ft) in the trunk's
  length? This note says no.

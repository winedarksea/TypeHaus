# ERV static budget — hand-worked basis

**House:** catlin
**Structure:** `EQ-B-ERV` (Broan B210E75RT) and the whole balanced distribution system it
drives — 5 fabricated plenums, 22 radials, 4 trunks/risers, 2 outdoor legs, 25 terminals.
**Written:** 2026-09-12, by hand, before the calculation it oracles was encoded.
**Oracle for:** `checks/mep/erv_static.py`, reported by `mep.erv_static_budget`; reproduced
by `tests/test_erv_static_oracle.py`.
**Companions:** `notes/room_heat_loss_baths.md` — the radiant arithmetic from the same
BLD-08 pass; `notes/system1_return_path.md` — the *other* air system's return path, which
shares none of this machine's duct.
**What is asked of the reviewer:** redo §6's two column sums and §10.4/§10.6's additions, and
check that 200.0 delivered (§10.22) against R403.5's 188.0 (4,900 sf CFA, five bedrooms, §10.23) holds. Both of §7's 8" upsizes are now bought, so there
is no cheap lever left in this note — what remains is `DU-ERV-RISER-EXH`, which is 58 % of the
governing column on its own. The friction arithmetic in §2–§5 is ordinary Darcy–Weisbach and
is offered for checking, not for deciding.

> ⚠ **2026-10-31: THE HOODS ARE COUNTED NOW, AND THE MACHINE DELIVERS 203.9 cfm** (§10.6):
> extract governs at 0.4413 in. w.g. **R403.5 asks 203.0 cfm** on 4,900 sf of CFA measured to
> the structural face (owner, 2026-10-31; `notes/conditioned_floor_area.md`), and
> `code.N1103_6_whole_house_ventilation` grades the delivered 203.9 against it: +0.9 cfm.
> Every 2026-09/-10 figure below is the pre-hood reading, and every "205" below is the old
> centreline-area target.

> ⚠ **`ventilation_cfm = 210` IS A DESIGN INTENT, NOT A PROMISE THE CURVE CAN KEEP.** 210 is
> the model-name number and it is the curve's value at 0.2 in. w.g. No duct system this size
> lands under 0.2 in. w.g., so the delivered figure will always read short of 210. What
> governs is MN 1322 R403.5's **203.0 cfm** (§10.6), which `code.N1103_6_whole_house_ventilation`
> grades against the delivered figure. `mep.erv_static_budget` reports the shortfall against 210 as UNKNOWN and never as
> a FAIL, for exactly that reason — see §8.

> ⚠ **2026-11-12: A PATH PAYS THE BOX IT PASSES THROUGH, AND A TAPPED TRUNK ONLY TO ITS
> TAP (§10.21).** Both §9 items are closed in the engine. Extract via SUITEBATH governs at
> **0.4327 in., 204.4 cfm** against 203.0.

> ⚠ **2026-11-11: A PATH PAYS ONLY THE TRUNKS ON ITS OWN ROUTE (§10.20).** The second
> conservatism below is retired: `DU-S-ERV-HP-FEED` is a graded path of its own and no
> basement radial carries a riser. Extract governs at **0.4216 in., 204.9 cfm** against
> 203.0. The block below is the 2026-09 record.

> ⚠ **THE GRADED NUMBER IS DELIBERATELY CONSERVATIVE IN TWO PLACES**, both named in §9: the
> risers are worked at their authored 210 cfm over their whole length though the real flow
> below the level-2 tap is 200 and above it 54, and the trunk chain is summed whole though
> `DU-S-ERV-HP-FEED` parallels the path rather than lying on it. The graded reading is
> **0.3251 in. w.g. and 207.5 cfm**; the unsimplified one is lower still, and **it has not
> been re-worked for this revision** — see §9, where the reason is that the split it needs is
> not a typed fact and the old figure was derived against a riser that has since grown. Both
> readings clear 205; neither reaches 210.
>
> ⚠ **BOTH OUTDOOR LEGS MOVED TO THE NORTH FACE ON 2026-09-15, AND THAT IS WHAT PAID FOR
> THE SECOND 8".** Off the west facade each leg had to sweep the NW chase to reach its hood,
> which is why `DU-ERV-OA` could not be upsized — an 8" envelope overran the shaft. Out the
> north wall each run leaves at its own station: `DU-ERV-OA` is 13'-9" and four elbows where
> it was 14'-0" and six, and its term fell **0.1318 -> 0.0315**. The governing side went back
> to extract and the delivered figure to 207.0 cfm. Twelve measured duct-on-duct and
> duct-on-pipe interpenetrations went with it — see `plan/mep_erv_l1.py`.
>
> ⚠ **THE EXTRACT SIDE WAS REBALANCED ON 2026-09-15 AND THE GOVERNING PATH MOVED.** It was
> authored at 265 cfm against a 210 cfm machine — 65 basement + 146 main + 54 attic, summed
> per plenum and never per SIDE, which is why nothing had caught it. Six terminals came down
> (owner: plant room to a slow turnover, the workshop bench hood is not a fume hood, the
> attic to 5) and the side now reads 210 exactly: 46 basement + 114 main + 50 attic. The
> graded figure fell 0.459 -> 0.417 and the worst path stopped being `DU-M-ERV-R-PLANT`.

---

## 1. The system as built

After the 2026-09-12 redesign (`plans/buildability.md` BLD-08) there is no proprietary part
anywhere in the distribution. The topology — one home run per terminal off a dampered
plenum — did not change; what it is built from did.

| piece | what it is | count |
|---|---|---|
| the machine | Broan B210E75RT, 6" top ports, `fan_curve` authored | 1 |
| plenums | fabricated galvanized box, 8" inlet collar, N x 4" dampered start collars | 5 (28 ports, 23 live) |
| radials | 4" galvanized snap-lock, one per terminal | 22 |
| trunks and risers | 6" galvanized | 5 (the level-2 extract feed joined them 2026-09-20) |
| outdoor legs | `DU-ERV-OA` and `DU-ERV-EA`, both **8"**, both inside an R-8 vapour-sealed wrap, both out the NORTH face | 2 |
| terminals | 4"-collar commodity diffusers and grilles | 26 |

Developed lengths and elbow counts below are read off the resolved model
(`takeoff/runs.py::run_schedule`), not scaled off a drawing.

## 2. The friction model

Darcy–Weisbach with a Colebrook friction factor, in the units the sources publish in.

| term | working | value |
|---|---|---|
| standard air, 70 °F | ρ = 0.075 lb/ft³ | — |
| kinematic viscosity | ν, 70 °F dry air | 1.63 x 10⁻⁴ ft²/s |
| area | A = πD²/4 | ft² |
| velocity | V = Q / A | fpm |
| velocity pressure | P_v = (V / 4005)² | in. w.g. |
| Reynolds number | Re = (V/60) · D / ν | — |
| friction factor | 1/√f = −2 log₁₀( ε/3.7D + 2.51/(Re√f) ) | — |
| pressure drop | Δp = f · (L_eff / D) · P_v | in. w.g. |
| effective length | L_eff = developed + (elbows x bend equivalent length) | ft |
| unit bridge | 1 in. w.g. = 249.089 Pa | — |

The physics is the engine's. The two coefficients it needs are readings off **ASHRAE
Fundamentals Ch. 21** and belong to the house, authored on `DuctProductType`:

| product | ε (ASHRAE Table 1) | bend equivalent length | working |
|---|---|---|---|
| 4" galvanized snap-lock | 0.0003 ft (galvanized, longitudinal seam — "medium smooth") | 2'-6" | C = 0.22 (smooth r/D = 1.5), L_e = C·D/f = 0.22 x 0.3333 / 0.0324 = 2.26 ft, rounded up for a stamped adjustable elbow |
| 6" galvanized | 0.0003 ft | 4'-6" | 0.22 x 0.5 / 0.0225 = 4.89 ft, rounded down to the nearest half foot |
| 8" galvanized | 0.0003 ft | 6'-6" | 0.22 x 0.6667 / 0.0234 = 6.27 ft, rounded up to the nearest half foot |
| 4" semi-rigid aluminium | 0.0009144 m = 0.003 ft (flexible metallic, fully extended) | 3'-6" | bore 3.8", not 4.0" |
| 6" insulated flex | 0.003 ft | 7'-0" | the rejected alternative — §6 |

**The 8" row's friction factor is HIGHER than the 6" row's, and the upsize still pays.** At
210 cfm an 8" pipe runs 602 fpm against 1,070 fpm at 6", so Re falls ~54,700 -> ~41,000 and
Colebrook returns 0.0234 rather than 0.0225. The bend equivalent length rises with both f and
D, 4'-6" -> 6'-6", so an elbow on this pipe costs half as much again in developed feet. What
falls is the velocity pressure, as V²: 0.07131 -> 0.02256, a factor of 3.16, against an L/D
that falls by 0.75. **The upsize is bought with velocity pressure and pays part of it back in
friction factor and elbow length** — which is why `DU-ERV-EA`'s four elbows make its term
0.0437 rather than the 0.0361 a 6" bend length would have given (§6). Both outdoor legs are
8" and both are dominated by their elbows: 26 of `DU-ERV-OA`'s 39.74 effective feet are bends.

**Roughness is read fully extended, and that is the honest reading only if the duct is
installed fully extended.** A compressed flex run is several times worse and is a defect,
not a product; nothing in this note or the check models one.

## 3. The radials, term by term

Every radial is 4" galvanized. `Δp_duct` is §2's formula; `Δp_terminal` is §5's.

| run | Q (cfm) | developed (ft) | elbows | L_eff (ft) | V (fpm) | P_v (in.) | Re | f | Δp_duct (in.) |
|---|---|---|---|---|---|---|---|---|---|
| `DU-B-ERV-R-SAUNA-EXH` | 20 | 45.50 | 7 | 63.00 | 229 | 0.00327 | 7,811 | 0.0342 | **0.0212** |
| `DU-B-ERV-R-PLAY` | 30 | 25.48 | 8 | 45.48 | 344 | 0.00737 | 11,717 | 0.0311 | **0.0313** |
| `DU-M-ERV-R-LIVING` | 20 | 44.93 | 5 | 57.43 | 229 | 0.00327 | 7,812 | 0.0342 | 0.0193 |
| `DU-M-ERV-R-PLANT` | 5 | 23.32 | 1 | 25.82 | 57 | 0.00020 | 1,953 | — | ~0.0005 |

`DU-B-ERV-R-PLAY` was 15.50 ft on 2 elbows (0.0141) until 2026-09-22, when it came off
`ST-B2M` (R311.7.2 headroom) and went round through `SF-B-BATH`: 0.5 + 10.90 + 0.60 ft of
drop, lane and rise, 1.50 + 2.75 + 1.04 + 4.50 + 6.44 + 2.25 ft of level legs, and 8 turns:
30.48 ft, 0.0347. On 2026-09-23 `REG-B-SUP2` moved from y=25' to y=20' and the hall leg went
6.44 -> 1.44 ft: 25.48 ft on the same 8 turns, 0.0311 x (45.48 / 0.3333) x 0.00737 = 0.0313.

`DU-A-ERV-R-BED3`, the longest radial in the house at 54'-1" and about a thousandth of an
inch at 5 cfm, sat in this table until 2026-11-11: BED3 returns to System 1 now
(`notes/system1_return_path.md`) and its 5 cfm went to the kitchen. Static goes as Q², so
length was never the criterion.

**THREE ROWS WERE STALE AND ALL THREE WERE RE-READ OFF THE MODEL (2026-09-20)**, BED3 among
them. `DU-M-ERV-R-LIVING` read 46.01 on 2 and is 44.93 on 5, and
`DU-M-ERV-R-PLANT` read 53.00 on 3 and is **23.32 on 1** — the level-2 trunk-and-branch
redesign stopped it being a home run from the plenum and made it a takeoff off the trunk at
the trunk's own south end. So PLANT is no longer the second-longest radial in the house;
`DU-M-ERV-R-LIVING` is, at 44.93 ft. **None of it moves the budget**: every one of these runs
is on the 5-to-20 cfm shelf where the Q² term is a thousandth of an inch, and none of the
three appears in either §6 column.

**PLANT was in the first row of this table until 2026-09-15, and the rebalance is what moved
it to the last.** At 25 cfm its 60'-6" effective length cost 0.0301 in. and its RH-dampered
terminal another 0.0424 — together 16% of the whole extract path, and the reason the prose in
`plan/mep_erv_l2.py` called it "the radial whose drop the installer must check". At 5 cfm the Q²
term takes both to about a thousandth. **A 5x cut in flow is a 25x cut in friction**, which is
why re-balancing bought more than any of the three duct changes the owner considered.

The two runs that matter now are `DU-B-ERV-R-SAUNA-EXH` (20 cfm through a motorised damper —
the damper is most of it, not the duct) and `DU-B-ERV-R-PLAY` (30 cfm, still the highest flow
on any radial).

**A 5 cfm radial (`DU-M-ERV-R-PLANT`, the old BED3) is LAMINAR (Re ≈ 1,950), and Colebrook is
a turbulent correlation.** Where Re < 2,300 the flow is laminar and Hagen–Poiseuille is exact,
so f = 64/Re = 64/1,953 = 0.0328; on BED3's 69.05 ft the drop was
0.0328 × (69.05/0.3333) × 0.00020 = **0.0014 in.** Between 2,300 and 4,000 there is no
correlation at all and the conservative read is the turbulent value at the top of the band,
which is what the check uses. Nothing in this band can govern — a 5 cfm branch's velocity
pressure is two orders below a 210 cfm trunk's — but the regime has to be named rather than
reported as a gap in the model.

## 4. The plenum, derived

There is no manufacturer, so there is no published curve. What is authored is worked here
from ASHRAE fitting coefficients, at the house's **largest** port flow (25 cfm), which makes
it conservative at every other port.

| term | working | value |
|---|---|---|
| inlet velocity, 8" collar at 210 cfm | A = 0.3491 ft²; V = 210/0.3491 | 602 fpm |
| inlet velocity pressure | (602/4005)² | 0.02256 in. = 5.62 Pa |
| abrupt expansion into the box | C = 0.80 (area ratio > 4) x 5.62 | 4.50 Pa |
| port velocity, 4" collar at 25 cfm | A = 0.08727 ft²; V = 25/0.08727 | 286 fpm |
| port velocity pressure | (286/4005)² | 0.00512 in. = 1.27 Pa |
| contraction into the collar + butterfly damper, full open | C = 0.50 + 0.30 = 0.80 x 1.27 | 1.02 Pa |
| **inlet-to-port total at 210 cfm** | 4.50 + 1.02 | **5.5 Pa** |

The authored curve is that figure scaled as Q² on the **trunk** flow, because the expansion
term is the larger and the only one the trunk flow moves:

`((60, 0.5), (120, 1.8), (210, 5.5))` Pa — 5.5 x (120/210)² = 1.80 ✓, 5.5 x (60/210)² = 0.45 ✓.

`EQ-T-ERV-MANIFOLD-10` carries the same curve: the ten-port box is **longer, not fatter**,
and neither the 8" inlet nor one 4" collar changes with its length.

## 5. The terminals, derived

Same situation and same treatment: commodity bath-fan grilles, no published drop at 20 cfm.
K on the **collar** velocity pressure (0.81 Pa at 20 cfm through 4"):

| type | K | basis | at 20 cfm |
|---|---|---|---|
| `REG-T-ERV-SUP` / `-EXH` / `-EXH-WALL` | 5 | plain dampered round diffuser | 4.0 Pa |
| `REG-T-ERV-SAUNA-SUP` / `-SAUNA-EXH` / `-PLANT-EXH` | 8 | face carries a closable or motorised damper of its own | 6.5 Pa |
| `REG-T-ERV-VALVE-EXH` (`REG-B-RET1`) | 6 | stock 100 mm extract valve at 46" AFF since 2026-11-15 (was the fabricated `REG-T-ERV-BENCH-HOOD`, K 6); damper in-line (§10.24) | Trox LVS 100 curve, ~0.7 Pa at 6 cfm |

Each row is authored as three points scaling Q², so the check interpolates rather than
re-derives. **A submitted product with a real test curve replaces the three points and
nothing else in this note.**

**The check interpolates LINEARLY between the authored points, and a chord across a Q² curve
sits above it.** That is deliberate and it is why §6's terminal reads 10.6 Pa where the Q²
value at 25 cfm is 10.16, and the plenum 2.9 Pa where Q² gives 2.66: linear between (20, 6.5)
and (30, 14.6) is (6.5 + 14.6)/2 = 10.55, and between (120, 1.8) and (210, 5.5) at 146 cfm is
1.8 + 3.7 × 26/90 = 2.87. Three points is what a component sheet publishes, three points is
what is authored, and reading a chord between them is the conservative direction. It costs
this system 0.002 in. w.g. in total. **Adding points to a curve tightens the graded figure;
it never loosens it.**

## 6. The two air paths, and which governs

The machine's curve is an **external static per side**, so the governing figure is the worse
of the two paths and never their sum. Each path is: worst radial + its terminal + the plenum
that radial lands in (at the sum of that plenum's radial flows; since §10.6, at its trunk's
flow when that trunk runs to the machine) + every trunk on that side. **Since 2026-11-11
(§10.20) it is the trunks on that radial's own route from the machine, plus the outdoor leg;
the tables below are the 2026-09 record of the old rule.**

**EXTRACT — `DU-B-ERV-R-SAUNA-EXH` → `EQ-B-ERV-MAN-EXH` → basement trunk → machine → `DU-ERV-EA`**

| term | working | Δp (in. w.g.) |
|---|---|---|
| `DU-B-ERV-R-SAUNA-EXH` | §3 | 0.0173 |
| terminal `REG-T-ERV-SAUNA-EXH` | 20 cfm is the curve's own point, 6.50 Pa / 249.089 | 0.0261 |
| plenum `EQ-B-ERV-MAN-EXH` at 46 cfm | below the curve's first point (60, 0.5), so clamped to it | 0.0020 |
| `DU-ERV-RISER-EXH` | 210 cfm, 36.15 ft + **5** x 4.5, f 0.0225, P_v 0.07131 | 0.1886 |
| `DU-B-ERV-RET-TRUNK` | 210 cfm, 5.83 ft + **2** x 4.5 | 0.0477 |
| `DU-M-ERV-EXH-FEED` | 114 cfm, **2.97** ft + **2** x 4.5, f 0.0251, P_v 0.02102 | **0.0126** |
| `DU-ERV-EA` | 210 cfm in **8"**, 29.15 ft + 4 x **6.5**, f 0.0234, P_v 0.02256 | 0.0433 |
| | | **0.3377** |

**`DU-M-ERV-EXH-FEED` is new on 2026-09-20 and it is the level-2 plenum's drawn outlet into
the riser** — 6" galvanized out of `EQ-M-ERV-MAN-EXH`'s west end, down to +93 1/2", south and
west into `DU-ERV-RISER-EXH`. It is in this column for §6's stated reason (every trunk on
that side) and it costs 0.0128. **The column rises 0.3251 -> 0.3379 and the delivered figure
falls 207.5 -> 207.2 cfm** — the price of drawing a leg that was always going to be built and
was never in the arithmetic. It is also what makes §9's first bullet quantifiable; see there.

**The riser is in this column although the sauna's own air never enters it**, and that is
§6's stated method rather than an oversight: the path is "worst radial + its terminal + its
plenum + EVERY trunk on that side". `DU-B-ERV-R-SAUNA-EXH` lands in the BASEMENT plenum, so
its air goes straight out the return trunk; the riser above carries the two upper storeys'
share into the same box. Summing it is the conservative reading and it is §9's second listed
conservatism — now worth **0.189 of the 0.325, 58 % of the column**, and by a wide margin the
largest single term in this note. With both 8" upsizes bought it is also the only large term
left anywhere: the next revision of this system is a riser question or it is nothing.

*D2 took 10" off the riser on 2026-09-19 and D3 took a turn out of it the same day, and
the SECOND one is worth four times the first.* D2 moved `DU-ERV-RISER-EXH`'s trunk leg from
`EQ-A-ERV-MAN-EXH`'s own centre at x=5'-0" to x=4'-2", west of all four attic collars
(`plan/mep_erv_risers.py`), which shortened the run 434.44" -> 424.44". D3 then replaced its
9-degree basement rake — one leg climbing -27" to port level over 46" — with a level run and
two 90s into the plenum's underside. **An elbow on a 6" duct is worth 4.5 ft of equivalent
length and the whole rake was worth 0.8 ft of real one**, so trading the sixth turn for a
foot of straight pipe is a net 3.7 ft off the effective length: 62.37 ft -> 58.65 ft, and the
drop is linear in effective length at fixed flow and diameter. **0.2006 -> 0.1886.**

*The return trunk gave up a turn for the same reason and it is the second-biggest move here.*
`DU-B-ERV-RET-TRUNK` used to leave the plenum's east end, drop, cross under the x=6'-6" lane
two radials shared, and come back west — three elbows to get round ducts D3 has since moved
out of its way. It now drops out of the plenum's underside and runs straight west on two.
19.12 ft effective -> 14.83 ft, and **0.0615 -> 0.0477**.

*The sauna's own radial paid part of it back, and that is the trade D3 made on purpose.*
`DU-B-ERV-R-SAUNA-EXH` goes west and down the x=3'-9" corridor now instead of straight south
down the middle of the drain field: 35.17 ft on two elbows becomes 39.08 on five, and
**0.0135 -> 0.0173**. The five reported interpenetrations it walks away from cost
0.0038 in. w.g., and D3 paid that on purpose.

**2026-10-01: the sauna extract was moved west of D-B-FURN's header and into the sauna wall's
stud cavity.** It now crosses W-B-CW at x=1'-0 1/2" in the west clear bay, shares that lane
with supply at a separate tier, and enters W-B-SA-W between its studs. W-B-SA-W changes to
SAUNA_2X6 so the 4" drop fits the 5 1/2" cavity without changing the sauna face. The new route
is 45.50 ft on 7 elbows; its duct term is **0.0212 in. w.g.**, up from 0.0173. Extract rises
about 0.0039 to 0.3303 in. w.g.; SUPPLY still governs at 0.3713 and 207 cfm delivered.

**The column falls 0.3470 -> 0.3251 and the delivered figure rises 207.1 -> 207.5 cfm.**

**Two things moved this column on 2026-09-15 and they moved it in opposite directions.**

*The riser got longer, 0.147 -> 0.203, and that is the cost of telling the truth.*
`DU-ERV-RISER-EXH` used to stop at (1'-2", 33'-7 1/2") @ +244" — in mid-air, 46" short of
`EQ-A-ERV-MAN-EXH`. `mep.duct_connectivity` passed it anyway, because its head stood within
`DUCT_JOINT_TOLERANCE_M` (3") of `DU-A-ERV-R-BATH1`'s north-south leg at (1'-0", 33'-7 1/2"):
**a 210 cfm riser was reading as teed into a 20 cfm bath radial, and the check passed BECAUSE
of the interference.** Re-stationing the riser 4 5/8" east dissolved the accident and the
check said "lands on nothing" the same minute. The feed is now drawn — north to y=34'-6",
then east along the line the four attic radials already share, into the manifold — and it
costs 3.94 ft and three elbows. That is the honest number this column never carried.

*The discharge got bigger, 0.167 -> 0.044, and that is the owner's lever.* `DU-ERV-EA` went
6" -> 8". Area goes as d² and friction as V², so the same 210 cfm through 1.78x the area
costs (1/1.78)² of the velocity pressure; against a slightly higher f at the lower Reynolds
number the term falls to a quarter. **It is worth more than everything else in this note put
together**, and the shaft was sized for it months ago — the riser's own prose argued y=34'-8"
because "at y=35'-6" an 8" envelope would stand 4 5/8" inside the stud cavity".

**SUPPLY — `DU-ERV-OA` → machine → basement trunk → `EQ-B-ERV-MAN-SUP` → `DU-B-ERV-R-PLAY`**

| term | working | Δp (in. w.g.) |
|---|---|---|
| `DU-B-ERV-R-PLAY` | §3 | 0.0313 |
| terminal `REG-T-ERV-SUP` | linear at 30 cfm = the curve's own point, 9.00 Pa / 249.089 | 0.0361 |
| plenum `EQ-B-ERV-MAN-SUP` at 60 cfm | the curve's own point, 0.50 Pa / 249.089 | 0.0020 |
| `DU-ERV-OA` | 210 cfm in **8"**, 13.74 ft + 4 x **6.5**, f 0.0234, P_v 0.02256 | 0.0315 |
| `DU-B-ERV-SUP-TRUNK` | 210 cfm, 3.03 ft + **2** x 4.5 | 0.0387 |
| `DU-ERV-RISER-SUP` | 210 cfm, **29.90** ft + **5** x 4.5 | **0.1685** |
| `DU-S-ERV-HP-FEED` | 100 cfm, **44.79** ft + 7 x 4.5 | **0.0635** |
| | | **0.3713** |

**2026-09-23: both chase risers moved 2 3/4" north** (off `W-M-MECH-S`, mid-bay in
FS-S-WEST's trusses), and `DU-S-ERV-HP-FEED`'s south leg 7/8" further south, off
`W-A-STU-N`. Supply +0.0011 (0.3406 -> 0.3417); on extract `DU-M-ERV-EXH-FEED` now tees into
the riser's east face, 2 1/2" shorter, -0.0002 (0.3379 -> 0.3377). Delivered is still
**207.2 cfm** (207.17).

**Later on 2026-09-23: `REG-B-SUP2` moved 5' south** and `DU-B-ERV-R-PLAY` lost 5' of hall
leg (§3), -0.0034: supply 0.3417 -> **0.3383**. Delivered 207.23 cfm.

**2026-09-24: `DU-ERV-RISER-SUP` humps over the basement crossing, +0.0330.** Its y=31'-8"
leg at -1'-5 15/16" crossed `DU-ERV-OA`, `PR-B-KITCH-DRAIN` and `PR-B-SAUNA-VENT`, each at its
own height, and no one elevation cleared all three. It now leaves the plenum north, rises 12"
into FS-M-MECH's joist bay at -7.4", runs west over everything and drops onto the riser's
foot: 28.11 ft on 3 elbows becomes 29.90 on 5, 0.1338 -> 0.1685 (the 2026-09-23 chase re-pack
had already taken 28.66 -> 28.11 and the column to 0.3365). Supply 0.3365 -> **0.3713**.

**This column barely moved and the chase re-pack is why it barely moved.** All four risers
were re-stationed onto the shaft's own clear width — `DU-ERV-RISER-SUP` 0'-5" -> 9 5/8",
`DU-ERV-RISER-EXH` 1'-2" -> 18 5/8", `DU-ERV-OA` 1'-11" -> 27 5/8" — and the two supply legs
that changed changed by the same 4 5/8" in opposite senses: `DU-ERV-OA`'s hood leg grew by
it, its basement leg shrank by it, and its developed length is identical to the foot.
`DU-ERV-RISER-SUP`'s basement leg shrank 4 5/8" (-0.0015) and `DU-S-ERV-HP-FEED`'s attic jog
shrank from 7" to 2 3/8" (-0.0003) because the riser head came out to meet it.

**SUPPLY GOVERNS, at 0.3713 in. w.g. since 2026-09-24, against extract's 0.3269** (the
extract table above predates the 2026-09-23 chase re-pack; the model's own legs now read
`DU-ERV-RISER-EXH` 34.77 ft / 5 elbows 0.1842, `DU-M-ERV-EXH-FEED` 2.21 ft 0.0118,
`DU-ERV-EA` 28.10 ft / 3 elbows 0.0374). Supply led by 0.0006 before the riser hump; it leads
by 0.0444 now, so the next supply-side saving is worth its full size again. Off the
authored fan curve, between (0.3, 208) and (0.4, 206):

> 208 − (0.0713 / 0.1) x 2 = **206.6 cfm delivered** (206.57; it was 207.2 before the hump)

against 205 cfm required by MN 1322 R403.5 and 210 cfm of design intent. **The system clears
the code rate by 0.8 % and falls 1.6 % short of the intent.**

> ⚠ **THE GOVERNING SIDE HAS NOW SWAPPED TWICE IN ONE DAY, AND THE SECOND SWAP IS THE ONE
> THAT MATTERS.** The order was: extract governed at 0.4169; `DU-ERV-EA` 6" -> 8" took
> extract to 0.3548 and handed the lead to supply at 0.4064, of which only the first 0.0086
> in. ever reached the delivered figure; then both hoods moved to the north face, which took
> `DU-ERV-OA` from 0.1318 to 0.0315 and handed the lead **back to extract** at 0.3495. The
> delivered figure went 205.0 -> 205.7 -> 207.0 cfm.
>
> The lesson the first swap taught is worth keeping even though its arithmetic is spent: a
> lever on the non-governing side buys only the gap between the two columns, and that gap was
> 0.0086 in. It was **0.0051 in.** after D3 and is **0.0179 in.** now that the level-2
> extract feed is drawn — still small. **So there is no cheap extract lever left: anything
> taken off extract below eighteen thousandths buys nothing at all, and the next real move
> has to take BOTH columns down or it is decoration.**
>
> **The one term that dominates everything is `DU-ERV-RISER-EXH` at 0.1886**, 56 % of the
> governing column and more than twice the next term. Both 8" upsizes are bought; there is no
> other large, cheap move left in this note. Anything that materially improves this system
> from here is a change to that riser — shorter, straighter, or bigger — **or it is simply
> the recognition that 0.1886 is not what that riser costs.** §9 can now say what it does
> cost, because its level-2 tap is drawn: **0.0747 in.**, 50 cfm above the tap and 164 below,
> and the 0.1139 in. between the two figures is the single largest piece of conservatism in
> this note — larger than every remaining physical lever put together.
>
> **The code margin is 1.1 %**, which is 2.2 cfm. It was 0.2 cfm before the rebalance and
> 0.7 cfm before the hoods moved. That is a real improvement and it is still a commissioning
> measurement rather than a calculation: §8's instruction to measure with a low-flow hood
> stands, and since 2026-09-22 it is the SUPPLY side (`DU-B-ERV-R-PLAY`) to hood.

**The rejected build, for the record.** Insulated flex is what a Twin Cities contractor
reaches for on a 6" ERV leg. The same two outdoor runs, worked at flex's roughness and bend
length:

| | `DU-ERV-OA` | `DU-ERV-EA` | pair |
|---|---|---|---|
| **8" galvanized in an R-8 wrap — as built** | **0.0315** | **0.0437** | **0.0752** |
| 6" galvanized in an R-8 wrap (the old west-facade pair) | 0.1318 | 0.1666 | 0.2985 |
| 6" insulated flex | 0.2683 | 0.3082 | 0.5766 |

Flex costs **0.50 in. w.g. more than what is built** on two runs — more than the machine's
whole budget — and even against the 6" galvanized pair it costs 0.28. It would take delivered
flow to about 195 cfm, under MN's 205. **Rigid pipe here is not a refinement, it is what makes
the system legal.** `DUCT-T-FLEX-6` stays in the catalog, named by no run, so this comparison
reads off typed data.

### Dry-fire clearance revision, 2026-10-13

The extract riser keeps its low north–south leg below the sauna-supply radial. At
(26.9", 350") it rises 1 9/16" before crossing the lane at 83.5" AFF, leaving 80.5"
under its bare 6" section. This adds two elbows, and no developed length: the new
1 9/16" rise is taken off the final rise into the extract plenum. The bench and sauna
extract crossings rise to 82.5" centres (80.5" underside); their initial drops shorten
by exactly the amount their terminal drops grow, so their lengths and elbow counts
stay unchanged.

Independent arithmetic using §2: at 210 cfm in 6" galvanized, f≈0.0225,
P_v≈0.07131, and D=0.5 ft, the two extra riser elbows cost
0.0225 × (2 × 4.5 / 0.5) × 0.07131 = **0.0289 in. w.g.**
The return trunk takes the same 59.5" of horizontal travel and 10.4" of drop, but
turns west at y357" after staying east at x74". Its elbow count rises from two to
three: another **0.0144 in. w.g.**, with no added developed length.
Using the October sauna revision's extract total of approximately 0.3303 gives
**0.3303 + 0.0289 + 0.0144 = 0.3736 in. w.g.** Extract now governs over the
unchanged 0.3713 supply column. The fan curve gives
208 − (0.3736−0.3) × 20 = **206.53 cfm**, above the 205 cfm gate.
The engine rounds this to 0.374 in. w.g. and 207 cfm. This budget covers the
retained machine arrangement, not the unqualified full-length relocation.

### ERV east of the dry-fire lane, 2026-10-17

`EQ-B-ERV` moved east to (80 5/8", 358") so the lane could be required (72" clear). Four
runs changed; developed length and elbows taken off the new geometry, priced with §2:

| run | before | after | Δp before -> after |
|---|---|---|---|
| `DU-B-ERV-RET-TRUNK` (6") | 5.83 ft + 3 x 4.5 | 1.74 ft + 2 x 4.5 | 0.0620 -> 0.0345 |
| `DU-ERV-EA` (8", f 0.0234) | 28.10 ft + 3 x 6.5 | 30.83 ft + 7 x 6.5 | 0.0377 -> 0.0604 |
| `DU-ERV-OA` (8") | 13.74 ft + 4 x 6.5 | 18.07 ft + 6 x 6.5 | 0.0315 -> 0.0452 |
| `DU-B-ERV-SUP-TRUNK` (6") | 3.03 ft + 2 x 4.5 | 0.87 ft, no elbow | 0.0386 -> 0.0028 |

Extract: 0.3736 - 0.0276 + 0.0227 = **0.3688 in. w.g.** Supply: 0.3713 - 0.0358 + 0.0137 =
0.3492, so extract still governs. Delivered: 208 - (0.3688 - 0.3) x 20 = **206.62 cfm**. The
engine reports 0.369 in. w.g. and 207 cfm.

## 7. Broan's own instruction, and what obeying it would cost

The B210E75RT installation manual carries one distribution instruction: **above 200 cfm with
long runs or many elbows, take the trunk up to 8 in.** This system is 210 cfm with 43 ft of
outdoor leg and eight elbows on it, so the instruction is squarely aimed at it.

Worked at 8" galvanized (ε unchanged, bend equivalent 6'-6" — §2):

| run | at 6" | at 8" | saved | status |
|---|---|---|---|---|
| `DU-ERV-EA` | 0.1666 | 0.0437 | 0.1229 | **BOUGHT 2026-09-15** |
| `DU-ERV-OA` | 0.1318 | 0.0315 | 0.1003 | **BOUGHT 2026-09-15** |

**THIS SECTION IS SPENT. BOTH UPSIZES ARE BOUGHT AND THE HOUSE NOW OBEYS BROAN'S INSTRUCTION
IN FULL.** It did not obey it at all a day ago, and the second half of it was blocked on
geometry rather than money right up until the blocking geometry was removed.

**WHAT UNBLOCKED `DU-ERV-OA` WAS NOT A BIGGER CHASE — IT WAS LEAVING THE CHASE.** The
sentence that used to close this section, *"the NW chase has the room — four 6" insulated
risers at about 25 % fill"*, was false, and the revision that replaced it was only half
right. Measured off the resolved model, the shaft's clear is 24" x 26 1/8" and it already
carried four ERV risers, `VR-M-STACK`, six plumbing vents on the y=34'-6" line and nine
conduits. At its old station an 8" `DU-ERV-OA` overran the shaft's east face by an inch, and
no ordering of four risers packed out of it — that much was correct, and it was read as
"the upsize is blocked until the chase question is settled".

The chase question was the wrong question. `DU-ERV-OA` runs main -> basement only; it is the
one leg in this system that never needed a continuous basement-to-attic shaft, and it was in
the shaft solely because its hood was on the WEST facade with the shaft in between. Moving
the hood to the north wall of `RM-M-MECH` put the riser at (3'-4", 33'-11"), in the open
closet, where 8" is not tight. The upsize followed for free, and took 0.1003 in. with it —
**more than the whole remaining margin of the system, and more than this section ever priced
it at** (it was scored at 0.0902, against a 6-elbow route; the north route has four).

The saving is larger than the sum of the two upsizes' table rows suggests, because the moves
also shortened both runs and removed three elbows between them. What the pair actually cost
the static budget, end to end: **0.2985 -> 0.0752 in. w.g.**, and the delivered figure went
205.0 -> 207.0 cfm.

**What is left is not in this section.** The governing column is extract and 58 % of it is
`DU-ERV-RISER-EXH`. The remaining levers, in order of size: shorten or straighten that riser
(0.1886), riser segmentation, and `DU-ERV-RISER-SUP` at 0.1348 on the side that now sits
five thousandths behind. **The extract elbow audit this list used to name is spent** — D3
took the sixth turn off the extract riser and the third off the return trunk — and the gap
it could work in is 0.0051 in., so the two columns must now come down together. None of them
is a purchase; all of them are geometry. (Since 2026-09-22 supply leads by 0.0027 in.: the
play radial's detour round the basement stair, §3, is the newest term on that side.)

## 8. Commissioning — and the real risk is the measurement

22 radials averaging 9 cfm each is not hard to balance; it is hard to **measure**. Every
term in §3–§5 is a design figure, and the only thing that closes this system out is a
measured one.

- **A capture hood is the wrong instrument below about 150 cfm.** Ordinary flow hoods read
  25–30 % low in that band, and a 9 cfm terminal is a quarter of the way down their scale.
  A **TSI Alnor LoFlo-class** balometer (or equivalent low-flow hood) is required equipment
  here, not a preference. A reading taken with a standard hood is not evidence.
- **Measure the total across the core, not by summing terminals.** Sum 23 low-flow readings
  and the instrument error compounds; one measurement at the machine's supply and extract
  collars is one error.
- **Then balance at the plenum, never at the grille.** Every port has a butterfly damper at
  the start collar; that is the adjustment. Closing a grille face throttles the branch and
  makes it whistle.
- **Report per terminal**: tag, design cfm, measured cfm, damper position. 23 rows, one
  page, filed with the O&M.
- **The number to hit is 188 cfm net supply** (MN 1322 R403.5 on 4,900 sf and five bedrooms, §10.23), not 210.
- **Set the mixing-box feed with the air handler running.** `DU-S-ERV-HP-FEED`'s 6" locking
  damper (§10.29) sets 115 cfm into `EQ-S-ERV-MIX` with `EQ-S-HP1-AH` at its interlocked fan
  speed (the box is negative, so the reading moves with the AH), then lock the quadrant.

## 9. What is NOT graded here

- **2026-11-12: the extract riser is GRADED in segments (§10.21).** A path that leaves
  `DU-ERV-RISER-EXH` at the `DU-M-ERV-EXH-FEED` tap pays it only below the tap; an attic path
  pays the stretch above at 164 − 119 = 45 cfm (`checks/mep/erv_segments.py`). The 2026-09
  record follows.
- **THE EXTRACT RISER'S SEGMENTED FIGURE IS RESTORED (2026-09-20), AND THE SUPPLY RISER'S
  IS STILL WITHDRAWN.** This bullet has been an IOU since the level-2 manifolds were drawn
  with no feed. Half of it is now payable.

  The check grades `design_cfm`, which is ONE number per run, so `DU-ERV-RISER-EXH` is
  worked at 210 cfm over its whole 36.15 ft in §6 and in `mep.erv_static_budget` alike.
  **It does not carry 210 cfm over its whole length and it never did.** With
  `DU-M-ERV-EXH-FEED` drawn — 6" out of `EQ-M-ERV-MAN-EXH` into the riser at **+93 1/2"** —
  the tap is a typed fact and the split is arithmetic rather than a guess:

  | segment | Q (cfm) | developed | elbows | L_eff | V (fpm) | P_v | Re | f | Δp |
  |---|---|---|---|---|---|---|---|---|---|
  | above the tap | 50 | 16.03 ft | 2 | 25.03 ft | 255 | 0.00404 | 13,019 | 0.0299 | **0.0060** |
  | below the tap | 164 | 20.12 ft | 3 | 33.62 ft | 835 | 0.04349 | 42,702 | 0.0235 | **0.0687** |
  | | | 36.15 ft | 5 | | | | | | **0.0747** |

  **0.0747 in. against the 0.1886 in. §6 carries — a conservatism of 0.1139 in.** Above the
  tap the riser carries only what `EQ-A-ERV-MAN-EXH` gathers (`DU-A-ERV-R-STUBATH` 20 +
  `-BATH1` 20 + `-ATTIC` 5 + `-BED3` 5 = **50 cfm**, not the 54 this bullet used to claim),
  and below it that 50 plus the level-2 trunk's 114 = **164 cfm**, not 200. The split is
  16.03 ft and two elbows above, 20.12 ft and three below, measured along the authored
  polyline from the tap station.

  Run that through §6's extract column in place of the 0.1886 and it falls
  **0.3379 -> 0.2240 in.**, at which point extract is further behind: supply's 0.3406 governs
  (it was 0.3200, and 207.6 cfm, before `DU-B-ERV-R-PLAY` left the stair), and the delivered
  figure off the fan curve is **207.2 cfm** either way. That is a
  reading and not a revision — §6 stays as it is, because §6 grades what the model types and
  the model types one flow per run. What this bullet now says is how much the honest number
  differs, and the answer is **about a tenth of an inch, all of it on the side that appeared
  to govern.**

- **2026-11-11: the supply riser is charged WHOLE to every path that crosses it, at 160
  cfm** (`DU-M-ERV-R-BED` 35 incl. LIVING + `-STUDY` 10 + `DU-S-ERV-HP-FEED` 115). Those
  paths are the level-2 supplies and HP-FEED's own (§10.20); no basement radial crosses it
  any more. The geometric reason below still stands, so the level-2 supply plenum is charged
  the riser as the tap it would take (`erv_routes`: an unfed plenum takes its nearest trunk).
  This is the one named conservatism left on the supply side.
- **The supply riser still cannot be segmented, and the reason is geometric.**
  `DU-ERV-RISER-SUP` carries 150 cfm below its level-2 tap and 100 above (`DU-S-ERV-HP-FEED`
  takes the 100; `EQ-M-ERV-MAN-SUP`'s three radials take 15 + 20 + 15 = 50) — but **there is
  no level-2 tap to measure from, because no 6" duct can reach that box.** Measured off the
  resolved envelopes in RM-M-MECH, whose true inside faces are x 6 5/8"..69 5/8" by
  y 402 3/8"..425 3/8":

  * the supply riser stands WEST of the exhaust riser on the same y, so the south band is
    closed to it by 6" of galvanized standing floor-to-deck;
  * north of that, the two gates are **3 7/8"** (west wall face to the radon stack) and
    **3 5/8"** (exhaust riser crown to the radon stack's south face);
  * past the first gate the north band dead-ends on `DU-ERV-EA`, 8" wide and full height,
    with 1 3/8" to the wall beside it.

  Every obstacle is full height, so no change of elevation opens anything, and
  `haus route houses/catlin --run DU-M-ERV-SUP-FEED` refuses in its own words. A 6" round
  through the 3 5/8" gate is a 2 1/2" interpenetration with the radon stack — a real
  `mep.run_interference` FAIL — and a 3" x 8" flat section threads it with 5/16" a side but
  takes `mep.erv_static_budget` from a reported figure to "no DuctProductType", because the
  check sizes round pipe only. **So this half stays an unquantified conservatism and is
  named as one.** The move that would close it is ~2 1/2" of northward travel on
  `VR-M-STACK`, which opens the gate to 6 1/8" and still clears W-M-N3B; that is a
  drainage-set decision and it is the owner's.

- ~~**The trunk chain is summed whole.**~~ **Resolved 2026-11-11 (§10.20).** Each path walks
  the joint graph from the machine (`checks/mep/erv_routes.py`): PLAY no longer pays the
  riser (25.9 Pa) or `DU-S-ERV-HP-FEED` (15.5 Pa), and the basement extract radials no longer
  pay `DU-ERV-RISER-EXH`/`DU-M-ERV-EXH-FEED`.
- ~~**A path does not pay the basement plenum it passes THROUGH.**~~ **Charged since
  2026-11-12 (§10.21)**, at the box's §10.6 curve. The 2026-11-11 record: Riser air enters
  `EQ-B-ERV-MAN-SUP` through the same trunk collar the basement radials' air does, and leaves
  `EQ-B-ERV-MAN-EXH` through it; both boxes are worked at 210 cfm for their own radials
  (§10.6) but every level-2 and attic path skips them. Charged, the 15.2 Pa would put extract
  SUITEBATH at ~0.483 in. and ~201.8 cfm, under R403.5's 203.0. Not charged here, and not
  hand-worked: whether the riser collar's pass-through loss is the box curve (an inlet
  expansion keyed on the trunk collar) or a smaller straight-through term is an owner/engineer
  question, recorded 2026-11-11.
- **Leakage.** Sealed rigid pipe leaks; nothing here models it. A duct-leakage test is the
  only answer and it is a commissioning item, not a calculation.
- **Filter loading and airflow indication.** This budget uses the clean-filter curve and does
  not model the fan reserve used as filters load. Broan says VIRTUO maintains the selected
  airflow despite filter clogging in a typical installation; the built-in LCD shows real-time
  airflow and diagnostics, and the manual's low-airflow warnings direct service to inspect
  filters, registers, hood screens, and ductwork. The sources describe no dedicated
  filter-loading alarm, so keep the quarterly cleaning schedule and use the airflow display
  as a performance check. See `notes/erv_service_access.md` for access and service details.
- **Frost on the intake hood screen.** `EQ-M-ERV-HOOD-OA` carries a deliberately coarse 1/4"
  bird screen for this reason, and a screen partly blocked at −15 °F is a real static the
  design cannot bound.
- **The machine's own internal resistance**, its recirculation defrost cycle, and anything
  about heat recovery. This note is pressure only.
- **The 6" ERV collars themselves.** Four collar transitions at the machine are inside its
  certified rating and are not double-counted here.

## 10. Outdoor legs: thermal and hood losses (2026-10-31)

Added with the air-distribution product pass (`notes/air_distribution_products.md`). It is
§10 and not §9 because a dozen files cite §9 by number. Three things moved the governing
figure, and each is a read off a published sheet or a defect fixed, not a guess.

### 10.1 The hoods are in the budget now

`mep.erv_static_budget` summed only the radial terminals; the two outdoor hoods each pass
the whole side's 210 cfm and were never counted. They are 8" since this pass (typed 6" behind
8" legs since 2026-09-15 — `mep.duct_connectivity` now FAILs that mismatch). RenewAire's
FA8 chart is read at its end points and scaled as Q², which is how a screened hood behaves:

| term | published reading | working | at 210 cfm |
|---|---|---|---|
| FA8 intake ("supply" mode) | 0.34 in. w.g. at 400 cfm | 0.34 × (210/400)² × 249.089 | **23.3 Pa** (0.0936 in.) |
| FA8 discharge ("exhaust" mode) | 0.215 in. w.g. at 400 cfm | 0.215 × 0.2756 × 249.089 | 14.8 Pa |
| BD8 inline damper, discharge only | 0.5 in. w.g. at ~830 cfm | 0.5 × (210/830)² × 249.089 | 8.0 Pa |
| discharge total | | 14.8 + 8.0 | **22.7 Pa** (0.0912 in.) |

The BD8 end point is a chart read to ±30 % at low flow; that is ±2.4 Pa, 0.01 in., 0.5 cfm.

### 10.2 The terminals carry published curves

The 100 mm disc valves carry Trox LVS 100's +5 mm (fully open) table, PD-02/2022: 8 / 19 /
33 / 52 Pa at 10 / 15 / 20 / 25 L/s. Below 10 L/s (21.2 cfm), where most of this house's
terminals run, the points are that row's own K = 8 / 21.2² = 0.0178 Pa/cfm². At 20 cfm a
valve loses **7.3 Pa against the 4.0 Pa** §5 derived for a plain diffuser — the honest cost
of a disc valve.

`REG-B-SUP2` is the one 30 cfm terminal. On a 100 mm valve it lost **17.1 Pa** (linear
between 21.2 and 31.8 cfm) and governed the machine at 0.475 in. w.g., 202 cfm. It takes the
**125 mm** valve on a 4x5 increaser instead (LVS 125: 9 / 15 / 24 / 35 Pa at 15 / 20 / 25 /
30 L/s): 30 cfm is 14.2 L/s, between (10 cfm 0.9, 31.8 cfm 9.0) → **8.2 Pa**.

### 10.3 The level-2 extract plenum was read at 228 cfm

`EQ-M-ERV-MAN-EXH` feeds one 8" trunk, and the ten branches tee off the trunk. The plenum's
flow was the sum over everything that "lands" in it — the trunk's 114 cfm AND the ten
branches' 114 again — so it read 228 cfm, past its own curve's last point (5.5 Pa at 210).
It is read at what leaves it, 114 cfm: (60, 0.5)–(120, 1.8) → **1.67 Pa**. This is the
"plenum at each port's own flow" lever, and it is a defect fix, not a reading: it moved the
level-2 extract paths by 3.8 Pa. (The basement plenums were left at their radials' 46/60 cfm here; §10.6 corrects that.)

### 10.4 The two columns

| column | 2026-10-17 | + hood | + valves / plenum | now |
|---|---|---|---|---|
| extract, via `DU-B-ERV-R-SAUNA-EXH` | 0.3688 | + 0.0912 | sauna terminal unchanged | **0.4600** |
| supply, via `DU-B-ERV-R-PLAY` | 0.3492 | + 0.0936 | terminal 9.0 (derived K) → 8.2 Pa on 125 mm | **0.4392** |

Extract governs. Delivered off the curve between (0.4, 206) and (0.5, 201):
206 − 5 × 0.600 = **203.0 cfm**. The engine reports 0.460 in. w.g. and 203 cfm.

**203.0 was 2.0 cfm under the then-target 205; §10.6 corrects it to 203.9, against a
requirement now 203.0.** The owner's shortfall policy (2026-10-30) stands and is now the
code check's: a delivered flow 2 cfm or less under the R403.5 rate is UNKNOWN (never
suppressed), left to commissioning (§8: LoFlo-class hood, balanced at the plenum collar
dampers, valves fully open); more is a FAIL. **What would add margin, if commissioning
reads low:**

- a 10" hood on an 8x10 increaser in the foam/girt zone, both sides. RenewAire lists FA10 but
  publishes no curve; at equal hood K the loss scales as (8/10)⁴ = 0.41, so ~13 Pa a side,
  extract 0.408 → ~205.6 cfm. **Unverified until RenewAire gives FA10 test data** (the chart
  footer cites "RD20200402 Collected Test Data"), and the 10" back plate needs a fit check at
  the HP3 cabinet and the disconnect's work space;
- the BD8 off the discharge (−8 Pa) — rejected here on 2026-10-31, and **reversed 2026-11-05**
  (C4 E3, owner): Broan's manual §2.4 forbids a damper on the discharge hood (it freezes) and
  the machine's motorized port dampers are what keep backflow out; see §10.10;
- (§10.6 takes the risers to their real flows; what is left of §9's segmented conservatism
  is the 50 cfm above the level-2 tap.)

### 10.6 Two errors that cancelled (review, 2026-10-31)

Both were in the inputs, not the method, and they run in opposite directions.

**The risers were authored at 210 cfm, which neither carries anywhere.** The extract riser
takes the attic's 50 and, below the tap, level 2's 114: **164** at most; the basement's 46
lands in the basement plenum and never enters it. The supply riser takes 210 less the
basement plenum's 60: **150** at most. `design_cfm` is now each run's highest flow. Worked with
§2 (6" bore, ε 0.0003 ft, ν 1.63e-4 ft²/s, a bend 4.5 ft):

| riser | L_eff | Q | V (fpm) | P_v | Re | f | Δp at 210 → now |
|---|---|---|---|---|---|---|---|
| `DU-ERV-RISER-EXH` | 34.77 + 7 x 4.5 = 66.27 ft | 164 | 835 | 0.04349 | 42,702 | 0.0235 | 0.2131 → **0.1354** |
| `DU-ERV-RISER-SUP` | 29.90 + 5 x 4.5 = 52.40 ft | 150 | 764 | 0.03638 | 39,056 | 0.0238 | 0.1685 → **0.0909** |

**The basement plenums were read at their own radials' flow, on an 8" box's curve.** §4 keys
a plenum's curve on its TRUNK collar's flow, because the expansion at the trunk is the larger
term. Each basement box's 6" trunk runs straight to the machine and passes all 210 cfm, riser
air included, so the check now reads such a box at that trunk's flow, not at 46/60. And the
curve those two boxes carried was §4's 8" figure. On a 6" collar at 210 cfm, P_v = 0.07131 in.
= 17.76 Pa; 0.80 x 17.76 = 14.21 Pa, plus §4's 1.02 Pa port term = **15.2 Pa**, so the curve is
`((60, 1.24), (120, 4.96), (210, 15.2))`. Both boxes carry it, the extract one under §4's
supply-direction coefficients (conservative, as §4 already is for the level-2 extract box).
0.5 → 15.2 Pa is +0.0590 in. on every basement path.

| column | §10.4 | risers | basement plenum | now |
|---|---|---|---|---|
| extract, via `DU-B-ERV-R-SAUNA-EXH` | 0.4600 | − 0.0777 | + 0.0590 | **0.4413** |
| supply, via `DU-B-ERV-R-PLAY` | 0.4392 | − 0.0776 | + 0.0590 | **0.4206** |

Extract governs. 206 − 5 x 0.413 = **203.9 cfm**; the engine reports 0.441 in. w.g. and 204.
Against the 203.0 cfm R403.5 now asks (below) that is **0.9 cfm over**, and
`code.N1103_6_whole_house_ventilation` grades exactly this figure. The 10" hood pair would
give ~0.387 in. and ~206 cfm.

**The graded column is still conservative.** The sauna's own
air never enters the extract riser or `DU-M-ERV-EXH-FEED` (0.147 of the 0.441, §6's whole-chain
rule), and the riser's upper 16 ft carry 50 cfm, not 164. The worst series path (an attic or
level-2 extract through the riser and both boxes) works out near 0.426 in., about 204.7 cfm.

**What the code asks is settled (owner, 2026-10-31): 203.0 cfm.** R403.5's "conditioned
floor area" is measured to the outer face of the structure (studs + sheathing, or the
foundation concrete), excluding the ccSPF, girts and cladding, with each stair well deducted
once on the storey above: basement 1,296 + main 1,228 + second 1,226 + attic 1,150 =
**4,900 sf**, and 0.02 x 4,900 + 15 x 7 = **203.0 cfm** (`notes/conditioned_floor_area.md`,
`resolve/conditioned_area.py`). Delivered 203.9 clears it by 0.9 cfm, which is inside the
chart-reading error of §10.1, so commissioning (§8) remains the real check. The superseded
readings: finish-face rooms 4,479 sf / 195 cfm, centrelines ~5,000 / 205, exterior
dimensions 5,455 / 214.

### 10.7 The panel spaces re-route (2026-10-31)

NEC 110.26(A)/(E) clearances at the W-B-W1 panels moved four runs (`plan/mep_erv_l1.py`,
`plan/mep_erv_risers.py`). `DU-ERV-OA` keeps 18.07 ft on six elbows (term unchanged).
`DU-ERV-RISER-SUP` drops out of its bay 1.66" further east and jogs north then west onto the
riser foot: 29.90 ft on **seven** elbows, L_eff = 29.90 + 7 x 4.5 = 61.40 ft; at 150 cfm
(§10.6's V, P_v, f) Δp = 0.0238 x (61.40 / 0.5) x 0.03638 = **0.1063** (engine 0.1065), so
supply 0.4206 + 0.0154 = **0.4360**. `DU-B-ERV-R-SAUNA-EXH` shortens 45.50 → 44.33 ft
(0.0212 → 0.0208) while `EQ-B-ERV-MAN-EXH`'s 1" move south adds 1" each to
`DU-ERV-RISER-EXH` and `DU-B-ERV-RET-TRUNK` (+0.0006): extract **0.4413**, unchanged to the
fourth place. Extract still governs, by 0.005 in.; 203.9 cfm.

### 10.8 The sealed sauna door (2026-11-03)

`D-B-SAUNA` became a sealed insulated sauna door, so the room has to balance. The 20 cfm
extract (`REG-B-EXH2`) is R303.3's continuous rate on a BATHROOM-occupancy room, graded by
`code.R303_3_local_exhaust`, so it stays and the supply rises instead: `REG-B-SUP3` 12 → 20
cfm, `REG-B-SUP1` (gym) 18 → 10, on the same `EQ-B-ERV-MAN-SUP` plenum, so the plenum, riser
and trunk flows do not move.

| branch | cfm | duct | terminal | branch total |
|---|---|---|---|---|
| `DU-B-ERV-R-SAUNA-SUP`, was | 12 | 0.0103" | 2.6 Pa | 0.0207" |
| `DU-B-ERV-R-SAUNA-SUP`, now | 20 | 0.0250" (x (20/12)^1.8 ≈ 2.5) | 6.5 Pa (§5, 8 cfm row scaled) | 0.0511" |
| `DU-B-ERV-R-GYM`, now | 10 | 0.0050" | 1.8 Pa | 0.0122" |
| `DU-B-ERV-R-PLAY` (governs supply) | 30 | 0.0333" | 8.2 Pa | 0.0662" |

The play radial still governs the supply column at **0.4383** and extract still governs the
machine at **0.441**; delivered stays 203.9 cfm against 203.0. The gym keeps fresh air at
10 cfm plus System 1's conditioned supply.

### 10.9 Short-leg clearing, routing only (2026-11-05)

Geometry changes forced by `mep.fitting_pattern`'s FAIL floor (a straight under two take-offs at
R = D/2). **The static arithmetic of this note is NOT redone here**; §10 is re-worked once, after
the DuctStandard's elbow C, the Broan port kit and E3 land.

| Run | Before | After |
|---|---|---|
| `DU-B-ERV-RET-TRUNK` | start 2.5" off the first elbow | 3.25" |
| `DU-ERV-EA` | rise off the port 2.9"; 2.9" drop at x 52"; x-jog 6.5" | rise 4 1/8" (wrap top 1/4" under MAN-SUP); steps to -31.4" then -33 3/4" on 30 degree bends; no x-jog |
| `DU-ERV-OA` | 3.9" step at y 31'-1" | 30 degree pair, y 31'-8" to 373.2" |
| `DU-ERV-RISER-SUP` | 1.7" x-jog onto the foot | 30 degree pair from y 399 1/8" |
| `DU-ERV-RISER-EXH` | 1 9/16" lift at y 350"; 2.5" rise into the box | level at -28.4" (NEC working spaces), 30 degree climb to -22" at x 34"-45", enters the plenum's WEST face (x 59.8") |
| `DU-B-ERV-R-SAUNA-SUP` / `-EXH` | 1" and 2" jogs | collar drop 2.1", 86 1/2" lane from x 32", register end without the y jog |
| `DU-S-ERV-HP-FEED` | 3.4" west jog at the deck | deck leg at x=15.4" |

**Open (E2):** EA is still on Broan port 1's side and RET on port 3's; OA still ends 4.8" off port
4. A swap cannot be drawn with the machine as it hangs: OA and EA (12" wrapped) cannot cross
inside the 21.9" between the case top and the joists, and RET/SUP lie under MAN-SUP (10.4"). It
needs the machine rotated 270 and the two plenums' roles swapped, or the EA riser re-sited east.
**Drain-back (M1-114):** drawn since §10.28 (1/8"/ft to the foot, a capped tee); the off-pattern
objection below does not hold at that slope.

### 10.10 The DuctStandard rework (2026-11-05, decision #114)

Three inputs changed together, and §10.1-§10.7's figures are superseded by these:

1. **Elbows carry a published C.** Each duct turn now pays C x K x velocity pressure instead of
   the duct row's `bend_equivalent_length`. A 90 or 45 is a die-stamped elbow, C 0.22 (ASHRAE
   Fitting 3-1, r/D 1.0); any other angle is an adjustable 90 set down, C 0.37 (Fitting 3-2,
   4-piece, r/D 1.0); K is Locklin's angle factor (0.45 at 30, 0.60 at 45, 1.00 at 90). The old
   equivalent lengths came out near C 0.22, so the stamped elbow keeps this budget where it was.
   With every turn a retail adjustable instead, delivered air was 197.8 / 200.1 / 202.2 cfm at C
   0.50 / 0.37 / 0.27 (r/D 0.75 / 1.0 / 1.5): short of 203.0 at every reading. That is why the
   stamped elbow was chosen (`notes/air_distribution_products.md`, "DuctStandard").
2. **The BD8 is off** (E3): the discharge hood is 22.7 → **14.8 Pa** at 210 cfm.
3. **The Broan port kit** rides with the trunk it lands on. Only the supply port is EXACT, so
   only its 12" of 6" flex is counted, **1.2 Pa** (Darcy over the `DUCT-T-FLEX-6` row). The
   6-to-8 transitions (C 0.22 on the 6" velocity pressure) and the other three flexes follow the
   E2 rotate-and-swap (`plans/TODO.md`); on the extract side they would cost roughly 0.01-0.02".

Result, as `mep.erv_static_budget` reads it (§10.9's re-routed legs included):

| side | static | worst radial | terms |
|---|---|---|---|
| supply | **0.430"** | `DU-B-ERV-R-PLAY` | radial 0.031", valve 8.2 Pa, MAN-SUP 15.2 Pa, SUP-TRUNK 0.003", flex 1.2 Pa, RISER-SUP 0.104", OA 0.041", OA hood 23.3 Pa, HP-FEED 0.058" |
| extract | 0.400" | `DU-B-ERV-R-SAUNA-EXH` | radial 0.019", valve 6.5 Pa, MAN-EXH 15.2 Pa, RET-TRUNK 0.037", RISER-EXH 0.121", EA 0.064", EA hood 14.8 Pa, EXH-FEED 0.012" |

The governing side is supply again. Off the fan curve between 0.4" (206) and 0.5" (201) at
0.430": 206 - (0.030 / 0.1) x 5 = **204.5 cfm**, which is what the check reads. Against R403.5's
**203.0**: **+1.5 cfm** (was +0.9). Commissioning (§8) still closes it.

### 10.11 Direct condensate, and how far the ERV can drop (2026-11-07)

Owner: the pan drains to the utility sink, so the line may run exposed through the mechanical
room. `PR-B-ERV-COND` now leaves the pan (80.6", 352") east under the case to x=91.5", south to
y=311", east to the W-B-STR3B face, south to the sink and 5.5" west over the basin. Plan legs:

    10.9 + 41 + 24 + 73 + 5.5 = 154.4 in = 12.87 ft      (was 275.15 in = 22.93 ft)

Fall to the unchanged outlet (44.25" AFF, 10" air gap over the 34" rim) from a pan at P:

    available = P - 44.25;   required = 12.87 ft x s        s = 1/4: 3.22 in   3/16: 2.41   1/8: 1.61

At the old pan (52.5", case bottom 54"): 8.25 in available, so the ERV may drop
8.25 - 3.22 = **5.0 in** at 1/4"/ft, **5.8 in** at 3/16", **6.6 in** at 1/8" (IMC 2018 307.2.1's
floor; the engine still grades 1/4" until the slope rule lands). Before: 8.25 - 22.93 x 0.25 = 2.5
in, which is the "~3.8 in" of the TODO less the branch's own slack. The legs hold 0.33-0.52"/ft
(`mep.drain_slope` passes at 0.25).

**Spent now: 1.7 in.** The case hangs at 52.3" (pan 50.8"; 6.55 in head), which makes the 6" supply
trunk 12.1 in long (port 73.9" to the plenum at 86"): Broan's 12 in flex lead fits, where 10.4 in
left it 1.6 in short. `PR-B-WH-COND` steps 2.5" west and falls onto the ERV line at (91.5", 352",
50.5"), under the case edge (pipe top 51.5" < 52.3"). Other limits on the drop, none binding by
5 in: the T&P valve port at 46" (case bottom 49" at 5 in), headroom under the case, and the
lane (x 40..68", unaffected). The number the rotation pass takes: **5.0 in at 1/4"/ft (6.6 at
1/8")** of drop from the 54" case, so up to 3.3 in more than now.

Static: SUP-TRUNK is 1.7 in longer, which adds 0.00046 in. (Darcy, 6", 210 cfm: 0.0032 in./ft x 0.142 ft) and moves the
delivered flow 204.50 -> 204.48 cfm (50 cfm/in. off the curve), so the check reads 204; R403.5's
203.0 is still cleared.

**MAN-SUP feed, tried and not closed (no change in the house).** Up through FO-M-ERV-OA's east
end (opening to x=58.5", feed up x=52", y=408" from a tee on RISER-SUP's x=65" leg under the
joists). The vertical has room (3" east of OA's wrap, 1.4" west of PR-B-CW-TRUNK), but the way
there crosses DU-ERV-EA's x=58.5" north leg (wrap AFF 72-85.7") under CD-B-GARAGE's conduit at x=60"
(AFF 91.8"): 5.1 in for a 6 in duct, and EA cannot rise (OA's wrap bottom leaves its y=418.5" leg
0.7 in) or fall (the lane). It closes once the rotation re-routes EA (no x=58.5" leg); the opening
change, FO header at 58.5" and PR-B-CW-TRUNK / PR-B-KITCH-DRAIN crossing it (both
`run_through_floor_member` UNKNOWN) come with it. EA drain-back is the same dependency: its low
point is the riser foot because OA's riser crosses its y=418.5" leg 0.7 in above.

### 10.12 The 270 degree layout does not close (2026-11-07, W3-ERV phase 2)

Kit gate: closed by W3-FLEX (`notes/flex_lead_bend_basis.md`): at 270 the OA/EA lead's wrap top
stands 7.7 in under the joist underside (case at 52.3"; ports 73.9"). What does not close is
the routing, and it does not depend on the kit. Ports at 270 (case centre (80.44", 354")):
supply (87.06", 345.78") SE, return (85.31", 359.16") NE, **outdoor (77.19", 357.41") NW,
exhaust (77.19", 347.66") SW**. The rotated door faces the lane (x 40..68"), which is clear.

The risers stand in the opposite order. OA rises at (40", 409"), 12" wrapped (x 34..46",
y 403..415"); EA's foot is (24.6", 418.5"); DU-ERV-RISER-EXH (26.9", 406.8") is full height
(x 23.9..29.9"). So OA starts NORTH of EA and ends SOUTH-EAST of it, and one must cross the
other:

* West of OA's riser there is 4" (x 30..34") between OA's wrap and the EXH riser: nothing passes.
* East of it EA must travel north on x >= 52" (the only way to reach y=418.5" and cross OA's
  corner at y 412.5..415", as today, EA 12.7" under OA's turn). OA's port is east of that line
  and its riser west, so OA crosses EA's north leg at y 357..409". Everything south of y=412"
  and x 40..68" is the dry-fire lane (nothing under 72" AFF).
* The crossing window is 72" to the ceiling at 96.94" = 24.94" for two 12" wraps (24"): 0.94"
  of total slack, 0.47" per side, which no wrap or hanger can hold.
* The one alternative is EA west of the lane through the 36" panel working spaces, across every
  west-going radial (BENCH x=24", SAUNA-SUP/-EXH x=19").
* It closes only if OA's and EA's risers swap sides (EA east of OA), which moves EA's upper end
  on level 2 and its hood: **held** (commit 9a5804f14). Rotation 90 puts the door on the tank
  (2") and 180 on W-B-ESS-S (1").

Static if it did close: each bent 8" lead is +0.0593 in. over a stock elbow (C 2.85 against
0.22, VP 0.0226 in. at 210 cfm, `flex_bend_loss_c` now authored on the kits). OA is on the supply
column (0.430 -> 0.489 in., 201.5 cfm off the curve, short of R403.5's 203.0) and EA on the
extract (0.400 -> 0.459). Both sides leave the 0.4" rating, so the 10" hood or an 8" supply
trunk would have to pay for it.

### 10.13 Three alternatives to the OA/EA swap, measured (2026-11-07, study G)

Question: does the 270 degree layout route **without** moving the EA riser and hood (the swap of
§10.12), if OA wears a thinner wrap, the dry-fire lane relaxes, or the EXH riser moves? Method:
`cross.py`-style scan of the real resolved model (every run, wall layer, the rotated case, the lane
floor), plus three sandbox branches of the house (not merged; `haus check` per branch). Static
numbers are pre-S (adjustable turns graded as today); each is a delta on this study's own baseline.

**Baseline, same worktree.** Current 0 degree model: supply 0.4301 in., extract 0.3996, 204.5 cfm.
Adding the two bent 8" leads (+0.0593 each, §10.12): **supply 0.4894, extract 0.4589, 201.5 cfm**
against 203.0 (1.5 cfm short; a miss of 2 or less is UNKNOWN). MAN-SUP gates: EXH crown to EA wrap
**2.70"** (2.92" to the EA riser's round wrap); SUP to EXH 5.50"; south of EXH 1.18" to
CD-B-DATA-CHASE (1.30" TUB-DRAIN, 1.55" W-M-MECH-S finish); north of EA 1.00" to W-M-N3B finish.
Feed over EA's x = 58.5" leg (route R1, §10.11): CD-B-GARAGE's bottom AFF 91.0 less EA's top 84.0
(north of y = 381") = **7.0"** (5.3" over EA's first leg, wrap top 85.7).

**The 24.94" window of §10.12 assumed an empty ceiling. It is not empty.** Over the crossing the
rectangle both wraps share meets these, bottom AFF: CD-B-GARAGE x 58.7-60.3 (91.0, N-S, y 333-424),
CD-B-DATA-MEDIA y 359.5-360.5 and CD-B-KITCHEN y 347.5-348.5 (92.7, E-W; they leave an **11.0"**
band, too narrow for a 12" wrap), PR-B-SAUNA-VENT x 50.3-52.7 (93.9). The OA row also cannot sit at
the port's y = 357.4": DU-B-ERV-R-SAUNA-SUP (y 360.5-364.5, AFF 86.5-92.6) stands in its wrap, so
the row is y <= 354.5". The largest free gap at any station for two 12" wraps, lane at 72": **20.73"**
(x_e = 52, AFF 72.0-92.7), 3.3" short of 24". Delete those three conduits from the model and the
scan returns exactly 24.94" at x_e 59-62 with the EA north leg unblocked: the §10.12 figure is the
no-conduit case.

| | baseline | a: OA 1" wrap | b: lane notch | c: EXH riser |
|---|---|---|---|---|
| Routes without the swap | no | **no alone**; yes on paper with CD-B-GARAGE moved (a+) | **yes at the crossing** (sandbox); port-end items open | no |
| Crossing gap vs stack | 20.73 vs 24 | 23.54 vs 22 (x_e 41-44), 23.04 (x_e 67-74); a+: 24.94 vs 22, x_e 59-74 | 91.0 - 66 = 25.08 vs 24 at x_e 57-62 | not in the crossing |
| Slack per side | -1.64 | 0.77 / 0.52; a+: **1.47** | **0.54** | n/a |
| Static supply / extract (with leads) | 0.4894 / 0.4589 | 0.4894 / 0.4589 (wrap is not in the friction) | 0.4924 / 0.4539 (OA +0.003, EA -0.005: 7 and 8 elbows against 6 and 9) | 0.4894 / 0.4604 (EXH-FEED +0.0015) |
| Delivered cfm vs 203.0 | 201.5 | 201.5 | 201.4 | 201.5 |
| MAN-SUP R1 gap (EA top to conduit) | 7.0" | 7.0"; a+ conduit gone, 12.9" to the joists | 7.0" (notch ends y 380); 9.3" if EA stays low the full lane | 7.0" |
| MAN-SUP chase gates | 2.70 / 5.50 / 1.18 / 1.00 | unchanged; EA also 1": 3.70-3.92 / 5.50 / 1.18 / 2.00 | unchanged | 6.00 only at 3.3" south (9 FAILs); the clean limit 1.18" gives 3.88 |
| EA drain-back (M1-114) | no | no | no from a notch (sag under OA's corner, lane floor hump); yes if the 66-70" height runs the whole N-leg | no |
| OA chase lid | engine has no ledger element | same | same | same |

**a. Thinner OA wrap.** Armacell **AP Armaflex sheet, 1"** (K-Flex Insul-Sheet equal; the product
already in `air_distribution_products.md` §9), R-4.2 on the datasheet figure used in §10.5; **OD 10"**
on the 8" duct, 2" less than today's two layers. R-3.3 is the code floor. Condensation: surface
70 - 85 x 0.68 / (4.2 + 0.68) = 58.2 F against a 50.5 F dew point at 70 F / 50% RH (holds to ~66%
RH; R-8.4 gives 63.6 F). Heat cost: UA 0.285 -> 0.471 Btu/h.F.ft; OA leg 438 -> 724 Btu/h, so
**+285 Btu/h at design**, 65% recovery falling ~1.5 points (EA also 1": +316 more, ~3.1 points in all;
tens of dollars a year). It fits the 11" conduit band (0.5" a side). Sandbox (`g-a`, EA x_e = 69,
OA ramping to AFF 90.9): three FAILs at the crossing, as the scan predicted: CD-B-GARAGE vs OA's
ramp 2.99", CD-B-DATA-MEDIA vs OA 2.87", EA vs OA 3.56" (OA must climb from under the conduit's 91.0
to above EA's top in the 2.7" between the conduit and EA's wrap). The only stations that fit 22"
are x_e 41-44, on OA's own x = 40" leg (and over KITCH-DRAIN), and x_e 67-74, which meet
W-B-ESS-W/-S at y >= 368.6" and the case top (73.9"). **Moving CD-B-GARAGE's run off x 53-68 over
y 341-361** (one 1-1/4" EMT, or into a joist bay) makes 24.94" free: 22" in it leaves **1.47" a
side** at x_e 59-62, N-leg unblocked, and removes R1's binding member (7.0" -> 12.9"). Moving the
two E-W conduits instead buys nothing (23.54", no station).

**b. Relaxed lane.** The clear height needed over the crossing is the real ceiling less 24" less 2s:
under CD-B-GARAGE (91.0): **67.0" for zero slack, 66.0" for 0.5" a side, 65.0" for 1.0"**, against
72" today; with that conduit moved (92.7): 68.7 / 67.7 / 66.7; with all three moved (96.94):
72.94 / 71.9 / 70.9 (0.06" of relief makes the note's 0.47" a side exactly 0.5"). Sandbox (`g-b`):
case at y = 354, 270 degrees, lane split into a 72" lane and a **66" notch, x 40.5-68", y 341.5-380"**
(38" long: EA's wrap reaches 341.7" and its rise to 78" takes to 373"); OA row y = 354.5 at AFF
78.5-90.5, EA north leg x = 59.5" at AFF 66.1-78.1 through the crossing, then up to 72-84. Result:
no FAIL at the crossing, in the lane or against SAUNA-SUP, CD-B-GARAGE or the ESS walls. Four FAILs
remain, all at the ports and common to every 270 layout: the supply trunk (not re-landed),
R-GYM through OA's drop (2.7"), RET-TRUNK through EA's lead (0.6"), and OA/EA 2.25" apart in plan
at 9.75" port spacing against 12" wraps (the leads must splay). Owner trade: 5'-6" over a 12" x
38" strip, 6" under the 6' minimum of 2026-10-17; the whole N-leg (y 347-412) at 66-70" is what
drain-back needs.

**c. Moved EXH riser.** It is not in the crossing, so it cannot change whether 270 routes; its
only job is the MAN-SUP gate. The y stack (EXH 6 + gap 2.70 + EA 12 + 1.55 + 1.00 to the walls) is
23.25" against 6 + 6 + 12 = 24" for a 6" duct between them: short by 0.75" even with both pushed
to their walls. Moving it 3.3" south (`g-c-exh`) gives 6.00" and **nine FAILs**: through-floor
member trimmer-FO-M-ERV-OA (1.0" in), I-joist flange, `run_through_stud` on W-M-MECH-S (EXH 1.25",
EXH-FEED 0.84"), and `run_interference` with CD-M-DATA-PORCH, PR-B-SAUNA-VENT, PR-M-S-BATH1-TUB-DRAIN,
PR-S-BATH1-SH-VENT and PR-S-BATH1-WC-CW. The 4" window west of OA's wrap (x 29.9-34) would need EXH
8" west; SUP's riser is 5.5" away, so at most 9.6" against 12".

**Ranking for the owner (no riser swap, no hood move in any of them).**

1. **a+: 1" OA wrap and CD-B-GARAGE off the crossing.** The lane stays at 72". Slack 1.47" a side,
   clears R1, +285 Btu/h. Open: no end-to-end route was drawn; the port-end items are shared with b.
2. **b: 66" notch.** The only variant drawn clean at the crossing, and no conduit moves, but it
   spends the owner's headroom and still leaves drain-back open.
3. **c: EXH riser.** Reject.

Pair: a with a 68" notch (0.5" a side under the conduit) halves each cost. Not tried: moving the
EA riser is held, and `haus route --run DU-ERV-OA` with its root moved to the 270 port reports "1 of
3,650 nodes reachable from the origin, blocked by AO-M-ERV-OA" though the opening names the run in
`penetration_for` (an exact OA port instead says the 14" lead meets CD-B-DATA-MEDIA and R-GYM);
the router could not be used, so a and a+ are screened, not routed.

### 10.14 The flat level-2 extract trunk (2026-11-08)

The 8" round `DU-M-ERV-EXH-TRUNK` fit no TrimJoist J12 opening (owner chose a flat trunk,
2026-11-07). It is now an 8x4 galvanized trunk in the D pockets' 9x4 R2 at x=27", fed by a 6x4
`DU-M-ERV-EXH-NECK` off the plenum's top, both carrying the whole 114 cfm. `mep.erv_static_budget`
grades a rectangular run at its Huebscher equivalent diameter with the rectangular row's ε
(`DUCT-T-GALV-RECT-10`, the round rows' 0.0003 ft), and adds the trunk and neck to every
branch they carry.

**Equivalent diameter**, De = 1.30 (ab)^0.625 / (a+b)^0.25 (ASHRAE Fundamentals 2017 Ch. 21 Eq. 25):

| | a x b | (ab)^0.625 | (a+b)^0.25 | De |
|---|---|---|---|---|
| trunk | 8 x 4 | 32^0.625 = 8.724 | 12^0.25 = 1.8612 | 6.0935" |
| neck | 6 x 4 | 24^0.625 = 7.284 | 10^0.25 = 1.7783 | 5.3281" |

**Turns.** No rectangular elbow C is in the DuctStandard, so each turn is the row's equivalent
length: a smooth-radius 90 at r/W 1.0, H/W 0.5, Co 0.25 (ASHRAE, "Fitting Loss Coefficients",
online supplement to *Principles of HVAC* 9th ed., 2021, Fitting 3-5, p. 12, after Idelchik
Diagram 6-1). L = Co x De / f = 0.25 x 6.09 / 0.026 = 59". Each run takes two turns (the trunk's
30-degree drop is charged as a full 90, conservative).

**Friction** at 114 cfm, ν 1.62e-4 ft²/s, Colebrook iterated by hand:

| | developed (in) | + 2 x 59" | L (ft) | A (ft²) | V (fpm) | Re | f | VP (in. w.g.) | Δp = f (L/D) VP |
|---|---|---|---|---|---|---|---|---|---|
| trunk | 300.3 | 418.3 | 34.86 | 0.20252 | 562.9 | 29,408 | 0.0251 | 0.019755 | **0.034"** |
| neck | 74.3 | 192.3 | 16.02 | 0.15484 | 736.3 | 33,632 | 0.0247 | 0.033796 | **0.030"** |

The engine reports 0.034" and 0.030". The extract side's worst path becomes
`DU-M-ERV-R-SUITEBATH` at **0.417"** (was 0.400" via `DU-B-ERV-R-SAUNA-EXH`, with no level-2
trunk on any path). It stays under the supply side's 0.430" via `DU-B-ERV-R-PLAY`, so the
machine still delivers **204.5 cfm**, against 203.0 cfm required (`code.N1103_6_whole_house_ventilation`).

### 10.15 Ceiling collars and the basement sidewall supplies (2026-11-10)

A ceiling valve now takes its run's end on a derived stock 90 (`resolve/terminal_drops.py`), and
both basement supplies moved to sidewall valves on the x=18' line. Only the governing radial
changes the answer.

**`DU-B-ERV-R-PLAY`**, 30 cfm, 4" galvanized. It used to turn east at (16'-9", 20'-6") onto a
45 climb to 101 1/4" (10 1/2" plan, 14.85" developed) and run 16 1/2" over W-B-CN2's plate to
the ceiling valve. Now it runs 15" level into the stud bay and ends on `REG-B-SUP2` (125 mm,
same `_VALVE_125_PA` curve, 8.2 Pa). The corner at (16'-9", 20'-6") was a compound 90 (north to
east-and-up, dot product 0) and stays a 90; the 45 at the top of the climb goes.

    developed: 14.85 + 16.50 - 15.00 = 16.35 in shorter = 1.3625 ft     25.976 -> 24.614 ft
    elbows:    Sum C K 1.8387 - 0.22 x 0.60 = 1.7067                     (one 45 fewer)
    VP:        V = 30 / (pi/4 x (4/12)^2) = 343.8 fpm;  VP = (343.8/4005)^2 = 0.007369 in.
    old:       friction 0.03139 - 1.8387 x 0.007369 = 0.01784 in. over 25.976 ft = 0.000687 in./ft
    new:       24.614 x 0.000687 + 1.7067 x 0.007369 = 0.01691 + 0.01258 = 0.0295 in.

The supply column falls by 0.0314 - 0.0295 = 0.0019 in.: **0.4301 -> 0.4282 in.** Off the curve
between 0.4" (206) and 0.5" (201): 206 - (0.0282 / 0.1) x 5 = **204.6 cfm**, against R403.5's
203.0: **+1.6 cfm**. The check reads 0.428 and 205 (rounded).

`DU-B-ERV-R-GYM` loses its 12" exposed gym leg (0.0040 -> 0.0039 in.), off the governing path.
On the extract side `DU-M-ERV-R-BATH1`, `-BATH2`, `-KITCH`, `-MUD` and the new `-RET3` branch
gain a climb and a drop (at most 0.002 in. each: BATH1 0.0004 -> 0.0022, at 20 cfm); the worst
extract path is still `DU-M-ERV-R-SUITEBATH` at **0.417 in.**, unchanged.

### 10.16 STUDY's drop on the adjustable 90 (2026-11-10)

`DU-M-ERV-R-STUDY` dropped 2.94" onto `REG-M-SUP4` against the stamped 90's 6.0" (1.5 D
stand-in). `PR-A-HW-STUBATH` crosses over the last leg at x=168.7" (centre 118.25"), so the leg
climbs only to 115.2" (crown 117.2"): a 4.76" drop, which the C.L. Ward adjustable's 4.75"
fits. The run names that vertex and the turn into the low-tier bay (`adjustable_elbows=(6, 9)`);
the port-end ramp eases from 32.2 to 25.1 degrees (x 63/70 -> 65.125/74.5"). Every straight
now clears its take-offs (vertex 1-2 7.13 vs 7.06", 5-6 7.99 vs 7.24", 7-8 6.82 vs 4.97",
9-10 4.76 vs 4.75"). A sidewall valve was refused: the booth's walls stop under the floor's
3/4" deflection gap or are 2x4, so it would add two 90s and a bored plate.

15 cfm, 4" galvanized:

    VP:        V = 15 / (pi/4 x (4/12)^2) = 171.9 fpm;  VP = (171.9/4005)^2 = 0.001842 in.
    old:       friction 0.008011 - 1.6249 x 0.001842 = 0.005018 in. over 24.672 ft = 0.0002034 in./ft
    developed: tail  climb 4.243 -> 6.824, level 14.500 -> 12.675, drop 2.938 -> 4.763  (+2.581 in)
               head  5.000 + 8.268 + 36.875 -> 7.125 + 10.356 + 32.375                (-0.287 in)
               24.672 + 2.294/12 = 24.863 ft
    elbows:    vertices 2, 3 (adjustable, 32.15 -> 25.14 deg): K 0.4715 -> 0.3771,
               2 x 0.37 x -0.0944 = -0.0699; vertices 6, 9 stamped 0.22 -> adjustable 0.37: +0.30
               Sum C K 1.6249 - 0.0699 + 0.30 = 1.8551
    new:       24.863 x 0.0002034 + 1.8551 x 0.001842 = 0.005057 + 0.003417 = 0.008474 in.

The STUDY path rises 0.0005 in., **0.3332 -> 0.3337 in.** (radial + 4.6 Pa valve + the level-2
plenum's 0.5 Pa + the supply trunks), 0.0945 in. under `DU-B-ERV-R-PLAY`'s governing
**0.4282 in.** Delivery is unchanged: **204.6 cfm** against 203.0, **+1.6 cfm**.

### 10.17 HP-FEED back on x=12" (2026-11-10)

The 1-1/2" roof rise grew `W-A-STU-N` a real stud at x=16", in the deck leg's way at x=15.4", so
the leg returns to x=12" with a 3.4" jog in the bay. One more 90 on 100 cfm: governing supply
**0.4282 -> 0.432 in.**, off the curve 206 - (0.032 / 0.1) x 5 = **204.4 cfm**, against R403.5's
203.0: **+1.4 cfm**.

### 10.18 The 270 degree build, attempted: neither a+ nor the swap closes (2026-11-11)

Owner brief: rotate EQ-B-ERV to 270, choose a+ (OA in 1" AP Armaflex, CD-B-GARAGE off the
crossing) or the OA/EA riser swap, make all four Broan ports exact. **Not landed.** The draft
(layout X below) is on branch `wip/erv-270-layout-x-not-landed` for reference; the house is
unchanged and the ERV OA/EA/RET hold stands.

**1. The static fails before any routing.** Making the outdoor port exact derives Broan's kit on
OA: the 6-to-8 transition and the bent flex, both on the governing supply column.

    6" at 210 cfm:  V = 210 / (pi/4 x 0.5^2) = 1069.5 fpm   VP = (1069.5/4005)^2 = 0.07131 in.
    8" at 210 cfm:  V = 210 / 0.3491 = 601.6 fpm           VP = (601.6/4005)^2  = 0.02256 in.
    transition      C 0.22 x 0.07131                        = +0.0157 in.  (3.9 Pa)
    bent flex       C 2.85 x 0.02256 + friction (engine 16.6 Pa)  = +0.0666 in.
    port-end stamped 90 the bend replaces: -0.22 x 0.02256  = -0.0050 in.
    supply column:  0.432 + 0.0773 = 0.509 in.  ->  201 - 0.009/0.1 x 5 = 200.5 cfm

That is 2.5 cfm under R403.5's 203.0, outside the 2 cfm commissioning band: a FAIL with OA
re-routed at no extra length at all. §10.12's 201.5 cfm left out the transition and the
flex's friction. The draft measured **0.519 in., 200.6 cfm** (engine: PLAY 0.026, valve 8.2 Pa,
MAN-SUP 15.2 Pa, SUP-TRUNK 0.003 + flex 1.2 Pa, RISER-SUP 0.108, OA 0.045 + hood 23.3 +
transition 3.9 + flex 16.6 Pa, HP-FEED 0.062). Extract was 0.40-0.41 in., not governing.

Any 270 layout therefore needs a supply-side saving as well. The one that is worked: an **8"
supply trunk into an 8" plenum inlet** (Broan's own 8" advice). §4 at an 8" collar gives 0.80 x
5.62 + 1.02 = 5.5 Pa against 15.2 (-9.7 Pa); the supply port then takes the 6-to-8 transition
(+3.9 Pa) and an 8" flex (1.2 -> about 0.3 Pa). Net -6.7 Pa = **-0.027 in.**: 0.482 in.,
**about 201.9 cfm**. The 10" hood (§10.4) is the other lever and is unverified.

**2. Geometry: the layer at 92.7-94" is what binds, not CD-B-GARAGE.** Measured off the resolved
model (AFF, basement datum -109.4375" project):

| item | where | z |
|---|---|---|
| CZ-B-DRYFIRE | x 40.5-68", y <= 411.6" | top 72.0" |
| CD-B-KITCHEN / CD-B-DATA-MEDIA (3/4" EMT) | E-W at y 348" / 360", x 10-115" | bottom 92.73" |
| PR-B-SAUNA-VENT | N-S x = 51.5" (y 344-400"); E-W y = 344" (x 51.5-108") | bottom 93.95" / 93.3" |
| CD-B-PLAY-SPARE | E-W y = 349.4", x 9.5-40"; N-S x = 40" | bottom 95.5" |
| FS-M-MECH joists | E-W, 16" o.c. (341.4", 357.4", 373.4"...) | underside 97.56" |
| ports at 270 | case at 49.0" (the condensate's 1/4"/ft limit, §10.11) | 70.6" |
| EA's bent lead | port + 2" start + R tan 45 = 8" | corner 80.6" |

Topology: at 270 the outdoor port is north of the exhaust port, and EA's riser foot (24.6",
418.5") is north-west of OA's (40", 409"). West of OA's riser there is 5.1" to DU-ERV-RISER-EXH
(§10.12), so EA reaches its foot from the east along y = 418.5" and its north leg stands at
x 51-62.6" (between OA's 10" wrap and W-B-ESS-W). OA's row from its port to x = 40" must cross
that leg, so the two stack once. Over the lane EA's centre is >= 78.0" (wrap 72-84"), so OA's
bottom is >= 84.0" and its top >= **94.0"**. OA's row has to pass the vent's x = 51.5" leg, which
spans every y from 344" to 400", where its top must be <= **93.95"**; and every route out of the
machine passes a 3/4" conduit at 92.73". OA cannot be over EA and under the vent at once: 0.05"
short with zero slack everywhere else, and the study's 1.47" a side (§10.13) is 3.0" short.
§10.13 put EA's leg at x_e 59-62", clear of the vent, but OA's row still has to pass the vent
on its way to x = 40"; that study screened the crossing station and did not route OA beyond it. EA also cannot reach 78.0" off its
80.6" corner before the crossing: a 15 degree pair takes 12 + 0.9 + 9.6" of north travel.

Under OA instead (EA high): EA's west row runs between the vent's y = 344" leg and CD-B-KITCHEN,
so it is <= 86.7" there, and then OA's top <= 80.7", bottom 70.7", in the lane. No.

**Layout X (drawn, the WIP branch).** It crosses at the machine, off the lane: OA's flex lead
rises 21.4" and turns south at 92" over EA's lead (0.4" over its wrap, 0.56" under the joists),
then west at y = 335.5" and north on x = 40". `haus check`: **12 FAIL**. The three that kill it are
OA's south leg through CD-B-DATA-MEDIA (3.77" in plan), CD-B-KITCHEN (5.29") and the vent's
y = 344" leg (3.40"). Every E-W line over the machine sits at 92.7-96.3". The rest are fixable
(SAUNA-SUP vs SUP-TRUNK 0.89"; BATH vs PR-B-HW-SBATH 0.94"; EA vs PR-B-KITCH-DRAIN 0.19";
CD-B-DATA-STUDY vs RISER-SUP 0.52"), plus the static and four R303.1 cascades from it. Parts
of it worth keeping: plenums over the east ports with straight 12" trunks (a bent 6" lead
costs 1.18 x 0.0713 = 0.084 in.), risers out of the box tops through the FS-M-MECH bays
(RISER-SUP 4 x 90 + 2 x 30, one 90 fewer than today), and SAUNA-SUP and PLAY with no short
straights. `haus route --run DU-ERV-OA` on the draft: no route ("not within this search"; the
port lead is laid straight at port + 24" = 94.6"); `--counterfactual` lifting EA or RET opens nothing.

**Swap (not drawn).** EA east of OA puts EA's riser at x >= 51". On the second storey that is
RM-S-BATH1 (the chase notch is x 6.6-30.6"), over its tub; on main the level-2 plenums fill the
closet's east half at +97-105". A main-storey EA hood on W-M-N3B is 3-4 ft from the intake;
`mep.erv_outdoor_terminals` wants 10 ft (3-D, no 3 ft exception). It needs a new chase through BATH1.

**What would close it, for the owner.**
1. Re-lane PR-B-SAUNA-VENT's furnace-room loop (y = 344", x = 51.5", y = 400") and
   CD-B-KITCHEN / CD-B-DATA-MEDIA out of the crossing (into FS-M-MECH bays, or west of x 35").
   That frees 72-97.56" for 22" of OA + EA, about 1" a side. Add the 8" supply trunk (1.) for
   the static. Five elements beyond the ERV set.
2. The 66" notch (§10.13 b): rejected by the owner.
3. Keep the 0 degree machine and its cross-wired EA/RET.

Thermal and wrap figures for a+ (OA 1", +285 Btu/h) stand as §10.13 worked them.

### 10.19 HP-FEED ends on the attic deck (2026-11-11)

System 1's air handler and `EQ-S-ERV-MIX` moved onto RM-A-EAST-UNFIN's deck, so the feed no
longer drops through the second-storey ceiling: it runs east in the FS-ATTIC bay to x = 310",
rises through `FO-A-ERV-HPFEED-E` and turns north on the deck into the box's south face.
**44.694 ft on 7 elbows -> 45.954 ft on 6.** Rate backed out of the old term:

    VP, 6" at 100 cfm:  V = 100 / 0.19635 = 509.3 fpm   VP = (509.3/4005)^2 = 0.016171 in.
    old term 0.062088 = rate x 44.694 + 1.54 x 0.016171  ->  rate = 0.000832 in./ft
    new term = 0.000832 x 45.954 + 1.32 x 0.016171 = 0.03824 + 0.02135 = 0.05958 in.

Engine: 0.059580. Governing supply **0.43223 -> 0.42972 in.**; off the curve
206 - (0.02972 / 0.1) x 5 = **204.5 cfm** against R403.5's 203.0: **+1.5 cfm**.

### 10.20 Shorter shared runs and per-path trunks (2026-11-11)

**Engine.** `mep.erv_static_budget` charges each path only the trunks on its own route from
the machine (`checks/mep/erv_routes.py`): a walk over trunk-to-equipment ends and trunk joints,
passing through distributing plenums only. The outdoor leg and its hood ride every path of
their side. A trunk ending in other equipment is a path of its own, so `DU-S-ERV-HP-FEED` into
`EQ-S-ERV-MIX` is graded. A round run whose FIRST vertex lies on a landing radial away from
its plenum end is a branch whatever its size (the old rule hopped only a smaller one, so
`DU-M-ERV-R-RET3` was never graded); a branch's path is its parent leg at the parent's authored
flow + its own leg + its own terminal (at the register's own flow) + the plenum.

**Moves (owner, 2026-11-11).**

| run | was | now | how |
|---|---|---|---|
| `DU-B-ERV-R-SAUNA-SUP` | 49.5 ft, 9 elbows | 5.3 ft, 3 | tee off GYM's y=13'-4" leg at x=11.2', hatch over the upper bench (owner accepts leaving Harvia's "inlet near heater") |
| `DU-B-ERV-R-BENCH` | 25.1 ft, 4 | 1.2 ft, 1 | side take-off off SAUNA-EXH's x=1'-7" leg at y=8'-6"; damper in-line since §10.24 |
| `DU-M-ERV-R-LIVING` | 46.6 ft, 7 | 20.8 ft, 5 | tee off BED's 83 3/4" lane at y=12'-8"; the 42 1/4" lane is free |
| `DU-M-ERV-R-BED1` | 25.8 ft, 0 | 11.9 ft, 0 | tee off BED2's crossing at (16.15', 16'-8"); grille at (28'-1", 16'-8") |
| `DU-M-ERV-R-PLANT` | 24.9 ft round, 1 | 10.3 ft 3 1/4x8 rect, 1 | trunk end, up W-S-PS1 to a high sidewall at x=3'-6 1/2", 8'-3" to centre |
| `DU-M-ERV-EXH-TRUNK` | 25.03 ft | 23.36 ft | dead end trimmed to PS1's axis |

About **124 ft** less duct, three plenum collars not cut (`collar-sauna` on the supply box,
`collar-bench`, `collar-living`). **Flows:** PLAY 30 -> 20, STUDY 15 -> 10, HP-FEED 100 -> 115
(supply 95 + 115 = 210); shared legs carry their branch (GYM 30, SAUNA-EXH 26, BED 35, BED2 10).

**The trimmed trunk, hand-worked** (§10.14's method; 8x4, De 6.0935", 119 cfm, 2 turns x 59"):

    L_eff = 23.36 + 9.83 = 33.19 ft;  V = 119 / 0.20252 = 587.6 fpm;  VP = 0.021526 in.
    Re = 9.793 x 0.50779 / 1.62e-4 = 30,698;  Colebrook f = 0.0249 (eps/D 5.908e-4)
    dp = 0.0249 x (33.19 / 0.50779) x 0.021526 = 0.03503 in.   (25.03 ft read 0.03679)

**The governing path, extract via `DU-M-ERV-R-SUITEBATH`.** Every other term is unchanged
from the Phase-0 reading of the same geometry (0.42334 in., the old SUITEBATH sum less RET3's
0.0001 in., which was a trunk in the chain and is now a branch):

    0.42334 - (0.03679 - 0.03503) = 0.42158 in.
    terms (Pa): radial 1.5 + trunk 8.7 + neck 8.1 + terminal 11.5 + plenum 1.8 at 119
                + EA 15.9 + hood 14.8 + RET-TRUNK 9.3 + RISER-EXH 30.2 + EXH-FEED 3.1 = 105.0
    delivered: 206 - 5 x 0.2158 = 204.9 cfm   (R403.5: 203.0, +1.9)

Engine: 0.421580, 204.92 cfm.

**The supply column.** Worst is now `DU-M-ERV-R-LIVING` at 0.3396 in. (LIVING 2.4 + BED at 35
cfm 9.4 + valve 7.3 + plenum 0.5 + OA 10.3 + hood 23.3 + trunk and flex 2.0 + riser at 160
cfm 29.3 Pa). HP-FEED's own path reads 0.3379 (riser 29.3 + feed at 115 cfm 19.3). PLAY fell
**0.4297 -> 0.2323** (no riser, no feed, 20 cfm). Supply is 0.082 in. behind extract.

**STUDY at 10 cfm** (§10.16's run, flow only): Re 3,930 is under the turbulent floor, so f is
read at 4,000: f = 0.04081, VP = 0.0008187 in.;
24.863 x 0.04081 / 0.3333 x 0.0008187 + 1.8551 x 0.0008187 = 0.002492 + 0.001519 = **0.004011
in.** Engine: 0.004011.

**Next lever** (not in scope): extract SUITEBATH. Its terminal (11.5 Pa) and the level-2 neck
(8.1) and trunk (8.7) are the radial-side terms. §9's pass-through bullet is closed by §10.21.

### 10.21 The pass-through box and the tapped riser (2026-11-12)

**Pass-through.** Riser air reaches a basement box through one collar and leaves through
another on a different face, so it takes the same abrupt expansion the radials' air does
(§10.6: 14.2 of the box's 15.2 Pa at 210 cfm). A straight-through term is not available.
`erv_routes` now names every plenum a walk passes THROUGH and the path pays its curve at its
trunk-collar flow. That is the low side on extract: there the riser's own 6" collar dumps
164 cfm into the box (~10.8 Pa), then contracts into the 6" trunk at 210 (~8.9 Pa), ~20 Pa.
Charged alone, SUITEBATH read **0.4826 in., 201.9 cfm**.

**Tapped riser.** `DU-ERV-RISER-EXH` is 33.59 ft with six turns; `DU-M-ERV-EXH-FEED` lands on
it 15.07 ft from its top, so SUITEBATH's air travels the lower **18.52 ft** with the two 90s
(stamped, C 0.22) and the two 29.6° bends (adjustable, 0.37 x K 0.444) at 164 cfm:

    V = 164 / 0.19635 = 835.2 fpm;  VP = 0.043493 in.;  Re 42,702;  f = 0.02348
    friction = 0.02348 x (18.52 / 0.5) x 0.043493 = 0.03783 in.
    turns    = (2 x 0.22 + 2 x 0.37 x 0.44415) x 0.043493 = 0.7687 x 0.043493 = 0.03343 in.
    below the tap = 0.07127 in.   (whole run at 164 cfm: 0.12118)

**The governing path, extract via `DU-M-ERV-R-SUITEBATH`:**

    0.42158 + 15.2 / 249.089 - (0.12118 - 0.07127) = 0.42158 + 0.06102 - 0.04991 = 0.43269 in.
    delivered: 206 - 50 x 0.03269 = 204.4 cfm   (R403.5: 203.0, +1.4)

Engine: 0.432693. Supply via LIVING takes the supply box the same way: 0.3396 + 0.0610 =
**0.4006 in.**, 0.032 behind extract. An attic extract pays the riser 0.0757 (18.52 ft at 164
+ 15.07 ft at 45) where it paid 0.1212.

**Still not graded:** tee and take-off junction losses anywhere in the system (no
coefficient is authored), and extract's riser-collar term above the box curve (~5 Pa,
~1 cfm). Together they are the margin's real risk; the commissioning reading (§8) settles it.

### 10.22 All four ports exact: the machine at 90 degrees, 13" south (2026-11-11)

Owner brief: keep the Broan B210E75RT and its gravity drain, land all four ports exact, accept a
low cfm for now. **Landed.** The ERV OA/EA/RET hold is retired.

**Why every earlier layout crossed.** The risers fix the order. `DU-ERV-OA` turns north at
x = 40" (W-M-N3B's stud module), and `DU-ERV-EA` reaches its chase foot (24.6", 418.5") from
the east, because `DU-ERV-RISER-EXH` holds x = 26.9" and only 5.1" is left west of OA. So EA's
north leg stands east of OA's, and for the two rows travelling west EA must be the NORTH row.
Broan's ports (local frame, port 2 SUP at +x+y, RET at -x+y, OA at -x-y, EA at +x-y) give, per
rotation, for the two outdoor ports:

| rotation | outdoor ports | order vs the risers | blocked by |
|---|---|---|---|
| 0 (until today) | SW / SE, same y | EA east of OA | EA must cross OA or the SUP stem north of it |
| 90 | east half, EA north of OA | **right** | SUP/RET stems under the rows (below) |
| 180 | north half, EA west of OA | wrong | door north into W-B-ESS-S |
| 270 | west half, OA north of EA | wrong | the §10.18 crossing |

At 90 the supply and return ports sit on the west half, under those two rows. With straight
leads neither can turn below the rows (6" lead: 12" flex + 6" elbow = port + 18"; 8": port + 19"),
and the supply plenum sits right above the supply stem, so EA's westbound row runs into it.
That is why the 2026-11-11 morning plan (90 with straight leads everywhere) could not close.
**Bent leads under the rows are the answer**: each 6" kit flex bends at port + 8" (2" straight,
R = 1D), runs level under the rows and turns up into its plenum. The 13" that leg needs (the
flex's 6.6" out plus the 6" adjustable elbow) is what moved the machine.

**Other options considered.** West of the lane: NEC 110.26(A) working spaces (x 12-50", to 78").
The RS (side-port) unit: horizontal leads add a 90 at every port and the same handedness holds.
Hanging RT above the lane (bottom >= 72"): the case top meets the 92.7" layer. The south furnace
room (y 245-314"): open, but OA and EA would each grow by about 10 ft. Moving MAN-SUP east of
the case: its three radials and the riser move with it, and EA still meets the supply stem.

**As built.**

| element | was | now |
|---|---|---|
| `EQ-B-ERV` | (80.44, 358"), rotation 0, case 52.3" | (80.44, 344.75"), **rotation 90**, case 40.4", ports 62.0" |
| ports | SUP exact; RET/OA/EA approximate | all four exact: SUP (73.81, 352.97), RET (75.56, 339.59), OA (83.69, 341.34), EA (83.69, 351.09) |
| `DU-B-ERV-SUP-TRUNK` | straight 12.1" | bent flex to 70", 13" north, adjustable 90 up into `EQ-B-ERV-MAN-SUP` (unchanged) |
| `DU-B-ERV-RET-TRUNK` | jog under the case | bent flex to 70", 13" south, adjustable 90 up into `EQ-B-ERV-MAN-EXH` |
| `EQ-B-ERV-MAN-EXH` | y = 341" | **y = 326.5"**; `collar-sauna` x -15" -> -8" (between `PR-M-S-BATH1-DRAIN` and `PR-B-HW-SBATH`) |
| `DU-ERV-OA` | onto (74, 351) at service level | row at y = 341" (11/32" off its port, taken by the flex), 84.5", straight kit lead |
| `DU-ERV-EA` | onto (74, 363) at service level | straight kit lead to 81", row at y = 351.3", 30 deg pair to 78" before the lane |
| OA / EA wrap | 2" (12" OD) | **1" AP Armaflex (10" OD)**; the rows clear by 0.09" |
| `PR-B-ERV-COND` | 12.9 ft via x = 115.5" | 9.7 ft straight down x = 91.5", ends 2.3" over the 34" rim |
| radials | | GYM holds 90" over EA's elbow; BATH, SAUNA-EXH and RISER-EXH follow the box |

Two engine changes came with it. `resolve/flex_bend.run_bend` takes the adjustable elbow's take-off
where the run names that vertex in `adjustable_elbows`: an 8" stamped 90 publishes no
centre-to-face, so at 1.5D a 19" lead read as bent. And `mep.run_interference` does not report
two kit leads touching inside their own lead lengths off one machine: Broan's 8" ports stand
9 3/4" apart, so two lagged leads overlap at the collars by construction. EA's elbow against
OA's flex is outside that and was still reported; it moved 0.2".

**The static, hand-worked against §10.21** (210 cfm on both trunks; 6": V 1069.5 fpm,
VP 0.071314, Re 54,679, f 0.02255; 8": V 601.6, VP 0.022564, Re 41,009, f 0.02322; galvanized
eps 9.14e-5 m, nu 1.63e-4 ft2/s):

    RET flex, bent    1.18 x 0.071314 = 0.084150 + 12" of flex friction (1.196 Pa) 0.004802 = 0.088952
    RET rigid         0.02255 x (3.0312 / 0.5) x 0.071314 + 0.37 x 0.071314
                      = 0.009747 + 0.026386 = 0.036133   (was 0.037448: 1.8875 ft, C 0.44)  -0.001315
    EA transition     0.22 x 0.071314                                                    = 0.015689
    EA flex, straight 12" of 8" flex at 210 cfm (0.268 Pa)                               = 0.001076
    EA rigid          0.02322 x (33.8169 / 0.6667) x 0.022564 + 2.1550 x 0.022564
                      = 0.026576 + 0.048625 = 0.075201   (was 0.064030: 30.7737 ft, C 1.7659) +0.011171
                      (C: three adjustable 90s 1.11, two stamped 90s at the chase 0.44, the
                      30 deg pair 0.329, the 24.5 deg pair at y = 418.5" 0.276)
    RISER-EXH         below the tap 18.52 -> 19.73 ft at 164 cfm, 0.0020424 in./ft x 1.2083 = +0.002468

    extract via SUITEBATH: 0.43269 + 0.11803 = 0.55072 in.
    delivered: 201 - (0.05072 / 0.1) x 2 = 200.0 cfm   (R403.5: 203.0, -3.0)

Engine: 0.550724, 200.0 cfm. Supply via LIVING takes the same two kit terms on OA and SUP's bent
flex: 0.4006 + 0.1395 = about 0.540, still behind extract. **3 cfm short is outside the 2 cfm
commissioning band, so `code.N1103_6_whole_house_ventilation` FAILs** and, with it, R303.1
Exception 1 in RM-A-STUDIO, RM-B-PLAY-N, RM-S-BED3 and RM-S-PLANT. The owner carries that red
(no suppression) until the attic bedroom drops, which takes about 15 cfm off the 203.0.
Almost all of the cost is the return's bend (0.089 in.); levers if it is wanted back: tee
`DU-ERV-RISER-EXH` into the return trunk instead of through the box (about 20 Pa, but junction
loss is not graded), or a stamped 90 on the return's rise (2.7 Pa, needs MAN-EXH 2 1/2" further
south and off the `PR-M-S-BATH1-DRAIN` stack).

**Thermal, 1" wrap** (§10.5's method): R-4.2 + 0.8 films = R-5.0 over pi x 9" = 2.356 ft2/ft,
UA 0.471 Btu/h.F.ft. OA 0.471 x 20.60 x 85 = 825; EA 0.471 x 33.82 x 55 = 876; **1,701 Btu/h**
(2" at these lengths: 1,029). Effective recovery 65% -> 0.65 x (12,530 - 1,701) / 12,530 = 56%.
Surface condensation stays safe to about 66% RH indoors (§10.13 a).

**Field items.** The case hangs on a strut trapeze and GV0772's length is read (both §10.28).
The ERV door zone shares about 10" x 14" with D-B-CLOSET's swing. Broan's top-port drainage
question (`air_distribution_products.md`) stands.

### 10.23 The attic bedroom drops: RM-A-STUDIO is a craft room (2026-11-11)

Owner: the attic suite is a craft room now and maybe a bedroom later. `Occupancy.HOBBY` is
habitable but not sleeping, so R403.5 counts five bedrooms:

    TVR = 0.02 x 4,898 + 15 x (5 + 1) = 97.97 + 90 = 188.0 cfm
    delivered (unchanged, §10.22)                       200.0 cfm   (+12.0)

No duct or flow changes; `EQ_S_ERV_MIX` stays at 115 and the margin is banked. The FAIL clears,
and R303.1 Exception 1 carries its four rooms again. Retyping the room BEDROOM puts back the 15
cfm and the −3.0.

### 10.24 The bench damper is an in-line part (2026-11-12)

The bench hood's 4" balancing damper left the hood's K (6.3 -> 6, curve back to
`((10, 1.2), (25, 7.6), (40, 19.4))`) and is now `DU-B-ERV-R-BENCH`'s
`inline_dampers=(12.25",)`: centred 6" + 6 1/4" along the run, 2" over the hood's collar at 76",
below the 90's 4" laying length. The DuctStandard's `damper` row charges it, fully open, at
C x the run's velocity pressure.

**C = 0.34.** No 4" damper maker publishes a loss. The smallest round damper with a published
AMCA 500-D test is Greenheck VCDR-53 at 12", Fig. 5.3 (fully ducted, Aug 2023 sheet):

| fpm | in. wg | VP = (V/4005)^2 | C |
|---|---|---|---|
| 1500 | 0.05 | 0.14028 | 0.356 |
| 2000 | 0.08 | 0.24938 | 0.321 |
| 2500 | 0.13 | 0.38966 | 0.334 |
| 3000 | 0.19 | 0.56110 | 0.339 |

0.34 is the 3000 fpm row (the table's two-digit rounding matters least there). §4's ASHRAE
butterfly term is 0.30, so this is the higher of the two. A 4" blade and shaft block more of
the bore than a 12" one, so a measured 4" C would likely be higher still. At 6 cfm that cannot
reach the delivered figure.

**`DU-B-ERV-R-BENCH`, hand-worked** (6 cfm, 4" bore, 1.1875 ft, one stamped 90):

    A = 0.087266 ft2;  V = 6 / 0.087266 = 68.755 fpm;  VP = (68.755 / 4005)^2 = 0.00029472 in.
    Re = 1.1459 x 0.33333 / 1.63e-4 = 2,343: transition band, f read at 4,000 = 0.04081
    friction = 0.04081 x (1.1875 / 0.33333) x 0.00029472 = 0.00004285 in.
    elbow    = 0.22 x 0.00029472                         = 0.00006484 in.
    damper   = 0.34 x 0.00029472                         = 0.00010020 in.
    leg      = 0.00010769 -> 0.00020789 in.

**Its path** pays the hood at the register's 6 cfm, under the curve's first point, so it reads
that point: 1.3 -> 1.2 Pa (-0.000401 in.). Net on the bench path: +0.000100 - 0.000401 =
**-0.000301 in.** The bench path is far from governing either way. The shared terms are
SAUNA-EXH 0.029835 at 26 cfm, `EQ-B-ERV-MAN-EXH`, and the extract chain.

**Governing:** unchanged. Extract via `DU-M-ERV-R-SUITEBATH`, 0.550724 in., **200.0 cfm**
against R403.5's 188.0 (§10.23, +12.0). Engine: 0.550724, 199.99 cfm; bench leg 0.000208.

**Re-worked 2026-11-15: the hood became a stock valve at 46" AFF.** `REG-B-RET1` is
`REG-T-ERV-VALVE-EXH` at (11", 7'-9"); the run is 8" west at 82 1/4" plus the derived drop to
the collar at 48 15/16" (33 5/16"), 3.4427 ft and one stamped 90. The damper sits 20" down the
drop (`inline_dampers=(28",)`), at 62 1/4".

    friction = 0.04081 x (3.4427 / 0.33333) x 0.00029472 = 0.00012422 in.
    elbow    = 0.22 x 0.00029472                         = 0.00006484 in.
    damper   = 0.34 x 0.00029472                         = 0.00010020 in.
    leg      = 0.00028926 in.   Engine: 0.00028926.

The terminal reads the Trox LVS 100 curve at 6 cfm (~0.7 Pa, under the hood's 1.2). The bench
path is still far from governing; the delivered 198.9 cfm does not move.

### 10.25 EQ-M-ERV-MAN-SUP's feed: no lane in the closet; drawn from the basement (2026-11-12)

`mep.manifold_feed` FAILs the box: BED and STUDY leave its collars and nothing arrives. §10.13's
gates, re-read off the resolved envelopes (EA's wrap now 10" OD, axis (24.625", 418.5")):

| gate (main closet, full height) | §10.13 (2" wrap) | now |
|---|---|---|
| EXH riser crown 409.8" to EA wrap | 2.70 (2.92 round) | **3.70 (3.92 round)** |
| CD-B-SPARE-CHASE top 410.5" to EA wrap | under 1 | **3.0, binds** |
| SUP riser 18.4" to EXH riser 23.9" | 5.50, three conduits in it | 5.50 |
| EXH riser 403.8" to W-M-MECH-S finish 402.25" | 1.55 | 1.55 |
| EA wrap 423.5" to W-M-N3B finish 425.375" | 1.00 | **1.88** |

An east-going feed off the riser must clear all three verticals on one line: y >= 409.4 + 1.1 + 3
= 413.5 for SPARE and y <= 418.5 - 5 - 3 = 410.5 for EA, so it is **3.0" short**. Across the
column the closet is 23 1/8" deep; EXH 6 + feed 6 + EA 10 + four 1/2" clearances is 24.0, so
re-packing SUP/EXH/EA around the conduits cannot open it either. `haus route` from the riser at
+80": 80 of 12,881 nodes reachable, blocked by CD-B-ATTIC-RISER and CD-B-SPARE-CHASE, and lifting
either alone opens nothing.

The basement does not either. Under FO-M-ERV-OA every point east of the column is DU-ERV-OA's
leg (x 35-45", AFF 83.4-93.4) or EA (y 413.5-423.5"). East of the header the FS-M-MECH bay
(405.4-421.4") has no drawn hole, and the lane up to it is CD-B-GARAGE (x 58.7-60.3") to
PR-B-KITCH-DRAIN (x 65.3"): **5.0"**. §10.11's R1 window over EA's x=58.5" leg is 8.0" now (EA top
AFF 83.0 to CD-B-GARAGE's 91.0; was 7.0), but KITCH-DRAIN's leg (y 401.8-404.2", AFF 84.8-87.6)
stands in it, leaving 3.4" over and 1.8" under.

**What the budget charges meanwhile.** `erv_routes` gives an unfed plenum the nearest trunk,
whole: MAN-SUP's three paths pay `DU-ERV-RISER-SUP` end to end at 160 cfm, **0.117"**. Supply
via LIVING is 0.5401", 0.0106" under the governing extract (0.5507"). A drawn 6" feed at 45 cfm
would cost A = 0.19635 ft2, V = 229.2 fpm, VP = (229.2 / 4005)^2 = 0.003275 in.; 0.020"/100 ft
and 0.22 x VP = 0.00072" per stamped elbow, so about 0.0002" per foot plus 0.0007" per turn, and
the riser would be charged only to its tap. The supply paths can only fall, and the extract
governs, so **delivered stays 200.0 cfm against 188.0**. No term moved; the oracle is unchanged.

**What would open it** (not in this lane's files): (a) CD-B-GARAGE off x 58.7-60.3" north of
y 394", which leaves a 7.6" lane between PR-B-CW-TRUNK and KITCH-DRAIN over KITCH-DRAIN's leg, plus a
drawn 6" FloorOpening in that bay under the box (east of FO-M-ERV-OA's header). Not routed:
the tee off the riser's basement corner still has to step 3 1/2" west. (b) The three chase
conduits out of x 18.8-22.8", so EXH can stand north of SUP and the feed leaves SUP's east
face at y 406.8". (c) EA's riser and hood moved: held (§10.12).

**Addendum, same day: (a) drawn.** CD-B-GARAGE's north leg moved from x=59.5" to 54.5", west of
PR-B-CW-TRUNK. `DU-ERV-RISER-SUP` moved from x=65" to 62" and up 1" (-18 7/16"; bay leg -6.4"), and
`EQ-B-ERV-MAN-SUP` grew 36 -> 38" west so its collar stays on the face. `DU-M-ERV-SUP-FEED` tees off
the riser's basement corner (62", 394.8") and runs straight north at -18 7/16", 4.2" off
KITCH-DRAIN's drop and 0.4" over its leg. One stamped 90 takes it up through `FO-M-ERV-SUP-FEED`
(7" x 6 1/2", in the 405-421" bay, cutting no member) into the box's underside at y=412".
`EQ-M-ERV-MAN-SUP` is 11 1/2" deep now (was 8), so that collar clears the joist flange (406.5") and
STUDY's riser (5.32" between centres against 5.0); the radials' collars keep their stations.

    feed: 45 cfm, 6", 17.2" + 116.9375" = 134.1375", one stamped 90 (C 0.22)
      A = 0.19635 ft2, V = 229.18 fpm, VP = 0.0032746 in., Re = 11,717, f = 0.03061
      friction = 0.03061 x (11.178 / 0.5) x 0.0032746 = 0.002241;  elbow 0.000720
      leg = 0.002961 in.
    riser to the tap: 24.8" at 160 cfm, no turn before it (the corner is the tee)
      V = 814.87, VP = 0.0413976, Re = 41,660, f = 0.02358 -> 0.004035 in.
    riser past the tap: 330.77" at 115 cfm, the seven turns (five stamped 90s at 0.22, the two
      30 degree bends adjustable, 0.37 x 0.45): C = 1.433
      V = 585.69, VP = 0.0213861, Re = 29,943, f = 0.02504 -> 0.029518 + 1.433 x VP 0.030646
      = 0.060164 in.
    riser whole (the old charge): 357.57" -> 355.57" now; 0.117497 -> 0.117172 in.

| path | before | after | delta |
|---|---|---|---|
| supply via LIVING | 0.540112 | 0.540112 - 0.117494 + 0.004035 + 0.002961 = **0.429614** | -0.1105 |
| supply via BED | 0.519253 | 0.408754 | -0.1105 |
| supply via STUDY | 0.474268 | 0.363770 | -0.1105 |
| supply via HP-FEED into EQ-S-ERV-MIX | 0.538463 | 0.538463 - 0.117494 + 0.064199 = **0.485167** | -0.0533 |
| extract via SUITEBATH (governs) | 0.550724 | 0.550724 | 0 |

The engine reads the same figures (0.429614, 0.485167; feed leg 0.0029610). The supply side now
trails the extract by 0.0656". **Delivered is unchanged: 200.0 cfm against 188.0.** The tee's own
junction loss is ungraded, as everywhere else in this budget.

### 10.26 Short straights lengthened: the neck, the feed and the supply riser's foot (2026-11-12)

`mep.fitting_pattern` asks a straight to hold the take-offs of the two elbows at its ends. Five
runs were moved to pass it (stamped 90 = 1.0 D = 6" on a 6", 4" on a 4"; a 45 is R tan 22.5):

| run | move | straight now |
|---|---|---|
| `DU-M-ERV-EXH-NECK` | ends 51.5" (was 54"); the trunk's ramp starts there, 2.5" west | 6.0" against 6.0 |
| `DU-M-ERV-EXH-FEED` | tees 29" (was 29.4") | 6.0" against 6.0 |
| `DU-ERV-RISER-SUP` | the foot's jog (30 pair) is one skewed leg 17.9" -> 15.4", the foot at -18 7/16" | 12.0" between the drop's two 90s |
| `DU-ERV-RISER-EXH` | the attic jog is a 45 pair; the basement ramp starts 0.6" east | 8.5" and 7.7" |
| `DU-B-ERV-R-PLAY`, `-R-BED`, `-R-BATH2` | PLAY 7/8" lower on its flat; BED's ramp 1.4" east; BATH2's pair 2.7" west | 4"-leg take-offs hold |

**Terms that moved, hand-worked** (119 cfm; De by Huebscher, A = pi De^2/4 as in §10.14,
Colebrook at nu 1.63e-4 ft2/s, eps 0.0003 ft; a turn's 59" equivalent length is constant):

    trunk 8x4: De 6.0935", A 0.20252 ft2, V 587.6 fpm, Re 30,509, f 0.02493, VP 0.021526
      8.805e-5 in./in. x -2.5"                    = -0.000220
    neck 6x4:  De 5.3281", A 0.15484 ft2, V 768.5 fpm, Re 34,892, f 0.02453, VP 0.036824
      1.6952e-4 in./in. x +2.5"                   = +0.000424
    feed 6":   V 606.1 fpm, Re 30,985, f 0.02488, VP 0.022900
      9.494e-5 in./in. x +0.4"                    = +0.000038
    governing extract (SUITEBATH): 0.550724 + 0.000242 = 0.550966 in.

Delivered off the curve between (0.5, 201) and (0.6, 199): 201 - 2 x (0.550966 - 0.5) / 0.1 =
**199.981 cfm** (was 199.986); it reads 200.0 against R403.5's 188.0 either way. The engine reads
0.550965 and 199.98. `DU-ERV-RISER-EXH`'s 45 pair is above the level-2 tap and not on the
governing stretch (19.7 ft), so its extra turn costs the extract side nothing.

**The supply riser** loses two turns (the 30 pair): 355.545" at 160 cfm, V 814.87 fpm, VP
0.0413976, f 0.02358: friction 0.02358 x (355.545 / 6) x 0.0413976 = 0.057845 + five stamped 90s
1.10 x VP = 0.045537 = **0.103382 in.** (was 0.117172). Past the tap (330.745" at 115 cfm, VP
0.0213861, f 0.02504): 0.029519 + 1.10 x VP 0.023525 = 0.053044 (was 0.060164), so supply via
HP-FEED reads 0.485167 - 0.007120 = 0.478047. The supply side stays under the extract.

### 10.27 The plant extract retired; the trunk capped short (2026-11-12)

RM-S-PLANT is sealed (`notes/plant_room_moisture_budget.md`): `DU-M-ERV-R-PLANT`, its grille and
deck opening are gone, and its 5 cfm went to `REG-M-RET-MUD` (5 -> 10, on the neck), so the
neck and trunk still carry 119 and the machine stays 210/210. With the plant stack no longer
chained to its end, the trunk is capped 6" past BED2's take-off: y=9'-0" -> 13'-6", 54" shorter.

    trunk 8x4 at 119 cfm (§10.26's slope): 8.805e-5 in./in. x -54" = -0.004755 in.
      0.0348519 -> 0.0300972 in.
    governing extract (SUITEBATH): 0.550966 - 0.004755 = 0.546211 in.
    delivered: 201 - 2 x (0.546211 - 0.5) / 0.1 = 200.076 cfm   (R403.5: 188.0, +12.1)

Engine: 0.546, 200.1 cfm. MUD's radial at 10 cfm is a 4" stub on the neck, far off the
governing path.

### 10.28 The rotation's residue closed: GV0772, HP-FEED's skew, EA's fall and drain (2026-11-12)

**GV0772's length.** Imperial publishes none (PP1142 gives SKU and gauge). Stand-in: M&M Mfg.'s
400 round reducer submittal (read 2026-11-12), 1.75 + 2.50-3.50 + 1.75 = 6.0-7.0"; the 7.0"
maximum is drawn with no collar engagement, as `PROD-DUCT-REDUCER-8-4` does
(`PortKit.transition_length`). The straight lead then needs 7 + 12 + 7 (adjustable 90) = 26";
OA has 22.5" (port 62.0" to row 84.5"), EA 19.0", so `run_bend` lays both leads as a flex bend at
R = 1D = 8" in place of the stock 90. Rows and paths hold; nothing new meets the 92.73" conduits.
Getting the straight lead back would lift OA's row 3.5" and EA's about 6.2" (case down 0.8"),
re-seating EA's first 30 pair: not worth 1.2 cfm. (Search results also name the 6x8 increaser
GV1360; the SKU is a construction hold.)

    EA (8", 210 cfm, VP 0.022564): stock adjustable 90 gone  -0.37 x VP = -0.008349
                                   flex bend                  +2.85 x VP = +0.064307
                                   flex 16.57" against 12"               = +0.000410
                                                                           +0.056368 in.

**EA falls to its foot (M1-114).** `slope_in_per_ft=0.125` on `DU-ERV-EA`; the foot drops
-33.7375 -> -34.8332". §10.9's objection does not hold: a 1/8"/ft fall moves a turn ~0.6 deg, inside
`elbow_for_turn`'s 10 deg snap, so every stamped row stays (the 30 pair reads 29.41, the 24.5 pair
23.9, both already adjustable). The 10.8" leg off the kit lead stays level (falling it makes the
lead's turn 90.6 deg, past what a straight lead takes), and vertex 3 holds -31.4" (lower meets
`DU-B-ERV-SUP-TRUNK`). Basis §10.22 (f 0.02322):

    length 33.81688 -> 33.90876 ft: 0.02322 x (0.091881 / 0.66667) x VP     = +0.0000722
    turns  30 -> 29.41: 0.37 x 0.45 x (29.41/30 - 1)                      = -0.003275 C
           24.5 pair -> 23.9: 2 x 0.37 x (0.3585 - 0.3675)                = -0.00666  C
           dC -0.00997 x VP                                                = -0.0002249
                                                                             -0.000153 in.

A drain tee (`PROD-DUCT-DRAIN-TAP-8`, 3/4" outlet) stands one stamped take-off east of the foot,
on the level leg, outlet down, **capped**: no gravity line reaches a receptor. The foot's wrap
bottom is 69.6" AFF and the corner is boxed by the dry-fire lane (x 40.5-68", nothing under 72"),
the panels' NEC 110.26 spaces (x 12-50", to 78") and the inverter / RM-B-ESS on the north wall.
`mep.duct_drainage` passes it as emptied by hand (the owner's call; `construction_holds.md`).

**HP-FEED's jog is a skew (the last ERV `fitting_pattern` UNKNOWN).** The 3.4" level jog between
two 90s at -8 1/2" (3.4" against 6.0") is one leg off the riser head at -9 3/4", 30.06 deg off vertical
onto x=12" at -3 7/8": 6.79" on adjustable elbows (R 6", take-off 6 tan 15.03 = 1.61"), leaving
7.875" of stand for the deck 90's 6.0 + 1.61. The riser head drops 231.875 -> 230.25" absolute.
The junction elbow at the riser head belongs to neither run and is charged nowhere, as its 90 was.

    riser (160 cfm, VP 0.0413976, f 0.02358): 0.02358 x (353.920 / 6) x VP + 1.10 x VP
                                            = 0.057580 + 0.045537 = 0.103117 in. (was 0.103382)
      past the tap (115 cfm, VP 0.0213861, f 0.02504): 0.029374 + 0.023525 = 0.052899 (0.053044)
    HP-FEED (115 cfm): 551.448 -> 550.213", C 1.32 -> 1.10 + 0.37 x 0.4506 = 1.26672
      0.02504 x (550.213 / 6) x VP + 1.26672 x VP = 0.076193 in. (was 0.077447)
    supply via HP-FEED: 0.478047 - 0.000145 - 0.001254 = 0.476648 in. (extract still governs)

**Governing extract (SUITEBATH):** 0.546211 - 0.000153 + 0.056368 = **0.602426 in.**; delivered
off (0.6, 199)-(0.7, 195): 199 - 4 x 0.002426 / 0.1 = **198.903 cfm** against R403.5's 188.0
(+10.9). Engine: 0.602426, 198.9.

**The case hangs on a strut trapeze** (`Equipment.hangers`): four B-Line ATR 3/8" rods (730 lb)
at the short sides' overhangs, two Unistrut P1000 channels under the case, each rod on a strut
bridge cut between two TJI 230 webs and BEARING on the tops of their bottom flanges, inside the
bay (under them it stood in the ceiling board), screwed down with 1/4" x 1-1/2" lags (graded
as if in withdrawal, 245 lb by TB-808's example). The north strut sits 1/2" inboard so its rods
clear joist 006's flange. 47 lb / 4 = 11.8 lb a rod; the worst joist carries 21.2 lb in 5 ft,
all on one side of its web, against TB-808's 500 lb (250 a side). Drop 57.2".
`structural.equipment_hangers` passes all three.

### 10.29 HP-FEED's balancing damper; the deck leg 3/4" up (2026-11-17)

No backdraft damper (owner): `EQ-S-ERV-MIX` is always below room pressure, so a gravity damper
would open in the feed's own direction. A 6" locking volume damper (`PROD-AIR-DAMPER-6-MANUAL`,
the DuctStandard's 6" `damper` row, C 0.34 on §10.24's VCDR basis) sits at
`inline_dampers=(517",)`, y = 297" on the north deck leg between its two saddles. That leg now
rides +4 3/4" (was +4") for the box's 1" fresh-collar land, so the stand-up is 3/4" longer
(550.213 -> 550.963") and each saddle bears on a 3/4" sleeper.

    HP-FEED (115 cfm, 6" bore, VP 0.0213861, f 0.02504; §10.28):
      friction  +0.02504 x (0.75 / 6) x VP = +0.0000669 in.
      damper     0.34 x VP                 = +0.0072713 in.
      leg 0.076193 -> 0.083531 in.          Engine: 0.083528 (f rounding).
    supply via HP-FEED: 0.476648 + 0.000067 + 0.007271 = 0.483986 in.

**Governing:** unchanged. Extract via `DU-M-ERV-R-SUITEBATH`, 0.602426 in., **198.9 cfm**.

### 10.5 The thermal penalty of the legs (hand-worked)

Both legs run through conditioned space in 2" of closed-cell elastomeric (two 1" layers of
AP Armaflex sheet, R-4.2 per 1" layer on the datasheet → R-8.4; with ~0.8 of surface films,
R-9.2 overall). Per foot of 8" duct the mean wrap circumference is π × 10" =
2.62 ft², so UA = 2.62 / 9.2 = **0.285 Btu/h·°F per ft**.

| leg | length | air inside at −15 °F design | ΔT to 70 °F | Q |
|---|---|---|---|---|
| `DU-ERV-OA` | 18.07 ft (6 elbows) | −15 °F outdoor air | 85 °F | 0.285 × 18.07 × 85 = **438 Btu/h** |
| `DU-ERV-EA` | 30.83 ft (7 elbows) | 70 − 0.65 × 85 = 14.8 °F (SRE 65 %) | 55 °F | 0.285 × 30.83 × 55 = **483 Btu/h** |
| | | | | **~920 Btu/h** |

The ERV's sensible recovery at design is 1.08 × 210 × 85 × 0.65 = 12,530 Btu/h; the legs
take ~920 of it, so the effective recovery falls **65 % → ~60 %**. The A0 research pass read
~770 Btu/h (a lower exhaust-leg ΔT); either way it is a few hundred watts at design and a
few tens of dollars a year. Code asks R-3.3 and a vapour retarder (Minn. R. 1322 Table
R403.2.1); R-8.4 is there for condensation, not for this arithmetic. More R on the riser is
rejected: the EA riser has ~1" of chase clearance, and R-12 would buy ~$10/yr.

**The wall line.** The wrap runs through the gypsum into the stud bay and stops 1-2" short of
the sheathing; the bare 8" duct is foamed through the sheathing (low-expansion PU, bonded to
the metal) and wrapped by the 4" ccSPF outboard. The exposed metal inboard of the foam is the
sheathing's thickness plus the gap, a few inches of duct in a ~25 °F bay, with no air path to
it. `SP-M-ERV-OA-SEAL` / `SP-S-ERV-EA-SEAL` carry the detail and bill it.

## Sources

- ASHRAE *Handbook — Fundamentals*, Ch. 21 (Duct Design): Table 1 absolute roughness for
  galvanized steel and flexible metallic duct; fitting loss coefficients for abrupt
  expansion, sudden contraction, butterfly damper and round elbow.
- Colebrook, C. F. (1939), *Turbulent flow in pipes* — the implicit friction-factor
  relation; Darcy–Weisbach for the pressure drop itself.
- Broan **B210E75RT** specification sheet — the fan curve authored on
  `EQ-T-BROAN-B210E75RT`: 214 cfm @ 0.1, 210 @ 0.2, 208 @ 0.3, 206 @ 0.4, 201 @ 0.5,
  199 @ 0.6, 195 @ 0.7, 191 @ 0.8, 184 @ 1.0, 176 @ 1.2 in. w.g.; 1.3 in. w.g. is the
  ceiling above which the core deforms. Recirculation defrost, HVI-tested at −13 °F,
  SRE 65 % there.
- Broan **B210E75RT installation manual** — the 8"-trunk-above-200-cfm instruction (§7).
- Broan **B210E75RT specification sheet** — VIRTUO airflow regulation, real-time airflow
  display, the 3" electrical-box-side clearance, and the 13" maintenance clearance.
- Broan **AI Series installation manual** — quarterly filter and intake-hood inspection,
  unit-door access, and low-airflow troubleshooting (W22/W32).
- HVI **Certified Products Directory**, HVI ID 2004940 — 206 cfm net supply at 0.4 in. w.g.
- Minnesota Rules **1322** (MN amendments to IRC Ch. 11), R403.5 — the 188.0 cfm whole-house
  rate this building requires on 4,900 sf of CFA and five bedrooms (§10.23), graded against the delivered flow
  by `code.N1103_6_whole_house_ventilation`.
- RenewAire **Hoods and Dampers** sheet (renewaire.com, 2025-09) — FA8 supply/exhaust and BD8
  pressure-drop charts (§10.1).
- TROX **LVS** product data sheet PD-02/2022 — LVS 100 and LVS 125 quick-sizing tables (§10.2).
- Armacell **AP Armaflex** sheet data — k 0.25 at 75 °F mean (§10.5).
- TSI **Alnor LoFlo** balometer product literature — the low-flow instrument class §8 calls
  for, and the documented −25 to −30 % bias of ordinary capture hoods below 150 cfm.

# ERV static budget — hand-worked basis

**House:** catlin
**Structure:** `EQ-B-ERV` (Broan B210E75RT) and the whole balanced distribution system it
drives — 5 fabricated plenums, 23 radials, 4 trunks/risers, 2 outdoor legs, 26 terminals.
**Written:** 2026-09-12, by hand, before the calculation it oracles was encoded.
**Oracle for:** `checks/mep/erv_static.py`, reported by `mep.erv_static_budget`; reproduced
by `tests/test_erv_static_oracle.py`.
**Companions:** `notes/room_heat_loss_baths.md` — the radiant arithmetic from the same
BLD-08 pass; `notes/system1_return_path.md` — the *other* air system's return path, which
shares none of this machine's duct.
**What is asked of the reviewer:** redo §6's two column sums, and say whether 2.0 cfm of
margin over MN's 205 is enough to build on. Both of §7's 8" upsizes are now bought, so there
is no cheap lever left in this note — what remains is `DU-ERV-RISER-EXH`, which is 58 % of the
governing column on its own. The friction arithmetic in §2–§5 is ordinary Darcy–Weisbach and
is offered for checking, not for deciding.

> ⚠ **`ventilation_cfm = 210` IS A DESIGN INTENT, NOT A PROMISE THE CURVE CAN KEEP.** 210 is
> the model-name number and it is the curve's value at 0.2 in. w.g. No duct system this size
> lands under 0.2 in. w.g., so the delivered figure will always read short of 210. What
> governs is MN 1322 R403.5's **205 cfm**, which `code.N1103_6_whole_house_ventilation`
> grades. `mep.erv_static_budget` reports the shortfall against 210 as UNKNOWN and never as
> a FAIL, for exactly that reason — see §8.

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
| radials | 4" galvanized snap-lock, one per terminal | 23 |
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
| `DU-B-ERV-R-SAUNA-EXH` | 20 | 39.08 | 5 | 51.58 | 229 | 0.00327 | 7,811 | 0.0342 | **0.0173** |
| `DU-B-ERV-R-PLAY` | 30 | 15.50 | 2 | 20.50 | 344 | 0.00737 | 11,717 | 0.0311 | **0.0141** |
| `DU-M-ERV-R-LIVING` | 20 | 44.93 | 5 | 57.43 | 229 | 0.00327 | 7,812 | 0.0342 | 0.0193 |
| `DU-M-ERV-R-PLANT` | 5 | 23.32 | 1 | 25.82 | 57 | 0.00020 | 1,953 | — | ~0.0005 |
| `DU-A-ERV-R-BED3` | 5 | 54.05 | 6 | 69.05 | 57 | 0.00020 | 1,953 | — | ~0.001 |

The last two rows are the point worth writing down: **`DU-A-ERV-R-BED3` is the LONGEST
radial in the house at 54'-1", and it is nowhere near the worst.** Static goes as Q², and at
5 cfm it costs about a thousandth of an inch. Length was never the criterion.

**THREE OF THESE FIVE ROWS WERE STALE AND ALL THREE ARE RE-READ OFF THE MODEL HERE
(2026-09-20).** `DU-A-ERV-R-BED3` read 56.15 ft on 5 elbows and develops 54.05 on 6 — the
`_ATTIC_BAY_Z` re-derivation to -8 1/2" lifted two bay-leg verticals 1 3/8" each, which
shortens the run and adds a turn. `DU-M-ERV-R-LIVING` read 46.01 on 2 and is 44.93 on 5, and
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

**`DU-A-ERV-R-BED3` at 5 cfm is LAMINAR (Re ≈ 1,950), and Colebrook is a turbulent
correlation.** Six of the 23 radials run below Re 4,000. Where Re < 2,300 the flow is laminar
and Hagen–Poiseuille is exact, so f = 64/Re = 64/1,953 = 0.0328 and the drop is
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
| `REG-T-ERV-BENCH-HOOD` | 6 | fabricated hood — a plenum with a collar | 7.6 Pa at its own 25 cfm |

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
that radial lands in (at the sum of that plenum's radial flows) + every trunk on that side.

**EXTRACT — `DU-B-ERV-R-SAUNA-EXH` → `EQ-B-ERV-MAN-EXH` → basement trunk → machine → `DU-ERV-EA`**

| term | working | Δp (in. w.g.) |
|---|---|---|
| `DU-B-ERV-R-SAUNA-EXH` | §3 | 0.0173 |
| terminal `REG-T-ERV-SAUNA-EXH` | 20 cfm is the curve's own point, 6.50 Pa / 249.089 | 0.0261 |
| plenum `EQ-B-ERV-MAN-EXH` at 46 cfm | below the curve's first point (60, 0.5), so clamped to it | 0.0020 |
| `DU-ERV-RISER-EXH` | 210 cfm, 36.15 ft + **5** x 4.5, f 0.0225, P_v 0.07131 | 0.1886 |
| `DU-B-ERV-RET-TRUNK` | 210 cfm, 5.83 ft + **2** x 4.5 | 0.0477 |
| `DU-M-ERV-EXH-FEED` | 114 cfm, 3.18 ft + **2** x 4.5, f 0.0251, P_v 0.02102 | 0.0128 |
| `DU-ERV-EA` | 210 cfm in **8"**, 29.15 ft + 4 x **6.5**, f 0.0234, P_v 0.02256 | 0.0433 |
| | | **0.3379** |

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
| `DU-B-ERV-R-PLAY` | §3 | 0.0141 |
| terminal `REG-T-ERV-SUP` | linear at 30 cfm = the curve's own point, 9.00 Pa / 249.089 | 0.0361 |
| plenum `EQ-B-ERV-MAN-SUP` at 60 cfm | the curve's own point, 0.50 Pa / 249.089 | 0.0020 |
| `DU-ERV-OA` | 210 cfm in **8"**, 13.74 ft + 4 x **6.5**, f 0.0234, P_v 0.02256 | 0.0315 |
| `DU-B-ERV-SUP-TRUNK` | 210 cfm, 3.03 ft + **2** x 4.5 | 0.0387 |
| `DU-ERV-RISER-SUP` | 210 cfm, 28.43 ft + 3 x 4.5 | 0.1348 |
| `DU-S-ERV-HP-FEED` | 100 cfm, 44.20 ft + 7 x 4.5 | 0.0630 |
| | | **0.3200** |

**This column barely moved and the chase re-pack is why it barely moved.** All four risers
were re-stationed onto the shaft's own clear width — `DU-ERV-RISER-SUP` 0'-5" -> 9 5/8",
`DU-ERV-RISER-EXH` 1'-2" -> 18 5/8", `DU-ERV-OA` 1'-11" -> 27 5/8" — and the two supply legs
that changed changed by the same 4 5/8" in opposite senses: `DU-ERV-OA`'s hood leg grew by
it, its basement leg shrank by it, and its developed length is identical to the foot.
`DU-ERV-RISER-SUP`'s basement leg shrank 4 5/8" (-0.0015) and `DU-S-ERV-HP-FEED`'s attic jog
shrank from 7" to 2 3/8" (-0.0003) because the riser head came out to meet it.

**EXTRACT GOVERNS, at 0.3379 in. w.g. against supply's 0.3200 — by eighteen
thousandths.** Off the authored fan curve, between (0.3, 208) and (0.4, 206):

> 208 − (0.0379 / 0.1) x 2 = **207.2 cfm delivered**

against 205 cfm required by MN 1322 R403.5 and 210 cfm of design intent. **The system clears
the code rate by 1.1 % and falls 1.3 % short of the intent.**

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
> stands, and it is now the EXTRACT side to hood.

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
carried four ERV risers, `VR-M-RADON-VENT`, six plumbing vents on the y=34'-6" line and nine
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
is a purchase; all of them are geometry.

## 8. Commissioning — and the real risk is the measurement

23 radials averaging 9 cfm each is not hard to balance; it is hard to **measure**. Every
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
- **The number to hit is 205 cfm net supply**, MN 1322 R403.5, not 210.

## 9. What is NOT graded here

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
  **0.3379 -> 0.2240 in.**, at which point EXTRACT NO LONGER GOVERNS: supply's 0.3200 does,
  and the delivered figure off the fan curve is **207.6 cfm** rather than 207.2. That is a
  reading and not a revision — §6 stays as it is, because §6 grades what the model types and
  the model types one flow per run. What this bullet now says is how much the honest number
  differs, and the answer is **about a tenth of an inch, all of it on the side that appeared
  to govern.**

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
  `VR-M-RADON-VENT`, which opens the gate to 6 1/8" and still clears W-M-N3B; that is a
  drainage-set decision and it is the owner's.

- **The trunk chain is summed whole.** `DU-S-ERV-HP-FEED` is a parallel branch off the
  supply riser, not a segment of the path to `DU-B-ERV-R-PLAY`; summing it over-counts the
  supply path by 0.0630 in. The supply path does not govern either way — though after D3 it
  is only 0.0051 in. behind, so this over-count is now larger than the gap it sits inside.
- **Leakage.** Sealed rigid pipe leaks; nothing here models it. A duct-leakage test is the
  only answer and it is a commissioning item, not a calculation.
- **Filter loading.** The curve is a clean-filter curve. MERV 8 at end of life adds
  meaningfully to the extract-side static; MERV 13, which this machine offers, adds more.
  The filter is inside the machine, so it is inside the curve's own zero — which means a
  loaded filter eats the margin this note reports and nothing warns of it but the schedule.
- **Frost on the intake hood screen.** `EQ-M-ERV-HOOD-OA` carries a deliberately coarse 1/4"
  bird screen for this reason, and a screen partly blocked at −15 °F is a real static the
  design cannot bound.
- **The machine's own internal resistance**, its recirculation defrost cycle, and anything
  about heat recovery. This note is pressure only.
- **The 6" ERV collars themselves.** Four collar transitions at the machine are inside its
  certified rating and are not double-counted here.

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
- HVI **Certified Products Directory**, HVI ID 2004940 — 206 cfm net supply at 0.4 in. w.g.
- Minnesota Rules **1322** (MN amendments to IRC Ch. 11), R403.5 — the 205 cfm whole-house
  rate this building requires, graded by `code.N1103_6_whole_house_ventilation`.
- TSI **Alnor LoFlo** balometer product literature — the low-flow instrument class §8 calls
  for, and the documented −25 to −30 % bias of ordinary capture hoods below 150 cfm.

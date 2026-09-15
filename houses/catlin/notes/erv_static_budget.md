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
**What is asked of the reviewer:** redo §6's two column sums and say whether 6" trunks are
accepted or the 8" upsize in §7 should be bought. The friction arithmetic in §2–§5 is
ordinary Darcy–Weisbach and is offered for checking, not for deciding.

> ⚠ **`ventilation_cfm = 210` IS A DESIGN INTENT, NOT A PROMISE THE CURVE CAN KEEP.** 210 is
> the model-name number and it is the curve's value at 0.2 in. w.g. No duct system this size
> lands under 0.2 in. w.g., so the delivered figure will always read short of 210. What
> governs is MN 1322 R403.5's **205 cfm**, which `code.N1103_6_whole_house_ventilation`
> grades. `mep.erv_static_budget` reports the shortfall against 210 as UNKNOWN and never as
> a FAIL, for exactly that reason — see §8.

> ⚠ **THE GRADED NUMBER IS DELIBERATELY CONSERVATIVE IN TWO PLACES**, both named in §9: the
> risers are worked at their authored 210 cfm over their whole length though the real flow
> below the level-2 tap is 200 and above it 54, and the trunk chain is summed whole though
> `DU-S-ERV-HP-FEED` parallels the path rather than lying on it. Worked without either
> simplification the system reads **0.380 in. w.g. and 206.4 cfm**, against the graded
> 0.406 and 205.7. Both readings clear 205; neither reaches 210.
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
| trunks and risers | 6" galvanized | 4 |
| outdoor legs | 6" galvanized inside an R-8 vapour-sealed wrap | 2 |
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
| 4" semi-rigid aluminium | 0.0009144 m = 0.003 ft (flexible metallic, fully extended) | 3'-6" | bore 3.8", not 4.0" |
| 6" insulated flex | 0.003 ft | 7'-0" | the rejected alternative — §6 |

**Roughness is read fully extended, and that is the honest reading only if the duct is
installed fully extended.** A compressed flex run is several times worse and is a defect,
not a product; nothing in this note or the check models one.

## 3. The radials, term by term

Every radial is 4" galvanized. `Δp_duct` is §2's formula; `Δp_terminal` is §5's.

| run | Q (cfm) | developed (ft) | elbows | L_eff (ft) | V (fpm) | P_v (in.) | Re | f | Δp_duct (in.) |
|---|---|---|---|---|---|---|---|---|---|
| `DU-B-ERV-R-SAUNA-EXH` | 20 | 35.17 | 2 | 40.17 | 229 | 0.00327 | 7,811 | 0.0342 | **0.0135** |
| `DU-B-ERV-R-PLAY` | 30 | 17.00 | 1 | 19.50 | 344 | 0.00737 | 11,717 | 0.0311 | **0.0134** |
| `DU-M-ERV-R-LIVING` | 20 | 46.01 | 2 | 51.01 | 229 | 0.00327 | 7,811 | 0.0342 | 0.0171 |
| `DU-M-ERV-R-PLANT` | 5 | 53.00 | 3 | 60.50 | 57 | 0.00020 | 1,953 | — | ~0.001 |
| `DU-A-ERV-R-BED3` | 5 | 56.15 | 5 | 68.65 | 57 | 0.00020 | 1,953 | — | ~0.001 |

The last two rows are the point worth writing down: **`DU-A-ERV-R-BED3` is the LONGEST
radial in the house at 56'-2", and `DU-M-ERV-R-PLANT` is the second-longest at 53'-0", and
neither is remotely the worst.** Static goes as Q², and at 5 cfm each costs about a
thousandth of an inch. Length was never the criterion.

**PLANT was in the first row of this table until 2026-09-15, and the rebalance is what moved
it to the last.** At 25 cfm its 60'-6" effective length cost 0.0301 in. and its RH-dampered
terminal another 0.0424 — together 16% of the whole extract path, and the reason the prose in
`plan/mep_erv.py` called it "the radial whose drop the installer must check". At 5 cfm the Q²
term takes both to about a thousandth. **A 5x cut in flow is a 25x cut in friction**, which is
why re-balancing bought more than any of the three duct changes the owner considered.

The two runs that matter now are `DU-B-ERV-R-SAUNA-EXH` (20 cfm through a motorised damper —
the damper is most of it, not the duct) and `DU-B-ERV-R-PLAY` (30 cfm, still the highest flow
on any radial).

**`DU-A-ERV-R-BED3` at 5 cfm is LAMINAR (Re ≈ 1,950), and Colebrook is a turbulent
correlation.** Six of the 23 radials run below Re 4,000. Where Re < 2,300 the flow is laminar
and Hagen–Poiseuille is exact, so f = 64/Re = 64/1,953 = 0.0328 and the drop is
0.0328 × (68.65/0.3333) × 0.00020 = **0.0014 in.** Between 2,300 and 4,000 there is no
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
| `DU-B-ERV-R-SAUNA-EXH` | §3 | 0.0135 |
| terminal `REG-T-ERV-SAUNA-EXH` | 20 cfm is the curve's own point, 6.50 Pa / 249.089 | 0.0261 |
| plenum `EQ-B-ERV-MAN-EXH` at 46 cfm | below the curve's first point (60, 0.5), so clamped to it | 0.0020 |
| `DU-ERV-RISER-EXH` | 210 cfm, 36.20 ft + 6 x 4.5, f 0.0225, P_v 0.07131 | 0.2028 |
| `DU-B-ERV-RET-TRUNK` | 210 cfm, 5.62 ft + 3 x 4.5 | 0.0614 |
| `DU-ERV-EA` | 210 cfm in **8"**, 29.32 ft + 5 x 4.5, f 0.0232, P_v 0.02256 | 0.0407 |
| | | **0.3465** |

**The riser is in this column although the sauna's own air never enters it**, and that is
§6's stated method rather than an oversight: the path is "worst radial + its terminal + its
plenum + EVERY trunk on that side". `DU-B-ERV-R-SAUNA-EXH` lands in the BASEMENT plenum, so
its air goes straight out the return trunk; the riser above carries the two upper storeys'
share into the same box. Summing it is the conservative reading and it is §9's second listed
conservatism — now worth **0.203 of the 0.347, 59% of the column**, and by a wide margin the
largest single term in this note.

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

*The discharge got bigger, 0.167 -> 0.041, and that is the owner's lever.* `DU-ERV-EA` went
6" -> 8". Area goes as d² and friction as V², so the same 210 cfm through 1.78x the area
costs (1/1.78)² of the velocity pressure; against a slightly higher f at the lower Reynolds
number the term falls to a quarter. **It is worth more than everything else in this note put
together**, and the shaft was sized for it months ago — the riser's own prose argued y=34'-8"
because "at y=35'-6" an 8" envelope would stand 4 5/8" inside the stud cavity".

**SUPPLY — `DU-ERV-OA` → machine → basement trunk → `EQ-B-ERV-MAN-SUP` → `DU-B-ERV-R-PLAY`**

| term | working | Δp (in. w.g.) |
|---|---|---|
| `DU-B-ERV-R-PLAY` | §3 | 0.0134 |
| terminal `REG-T-ERV-SUP` | linear at 30 cfm = the curve's own point, 9.00 Pa / 249.089 | 0.0361 |
| plenum `EQ-B-ERV-MAN-SUP` at 60 cfm | the curve's own point, 0.50 Pa / 249.089 | 0.0020 |
| `DU-ERV-OA` | 210 cfm, 13.99 ft + 6 x 4.5 | 0.1318 |
| `DU-B-ERV-SUP-TRUNK` | 210 cfm, 2.78 ft + 1 x 4.5 | 0.0234 |
| `DU-ERV-RISER-SUP` | 210 cfm, 29.10 ft + 3 x 4.5 | 0.1367 |
| `DU-S-ERV-HP-FEED` | 100 cfm, 44.20 ft + 7 x 4.5 | 0.0630 |
| | | **0.4064** |

**This column barely moved and the chase re-pack is why it barely moved.** All four risers
were re-stationed onto the shaft's own clear width — `DU-ERV-RISER-SUP` 0'-5" -> 9 5/8",
`DU-ERV-RISER-EXH` 1'-2" -> 18 5/8", `DU-ERV-OA` 1'-11" -> 27 5/8" — and the two supply legs
that changed changed by the same 4 5/8" in opposite senses: `DU-ERV-OA`'s hood leg grew by
it, its basement leg shrank by it, and its developed length is identical to the foot.
`DU-ERV-RISER-SUP`'s basement leg shrank 4 5/8" (-0.0015) and `DU-S-ERV-HP-FEED`'s attic jog
shrank from 7" to 2 3/8" (-0.0003) because the riser head came out to meet it.

**THE SUPPLY SIDE GOVERNS NOW, at 0.4064 in. w.g. against extract's 0.3465.** Off the
authored fan curve, between (0.4, 206) and (0.5, 201):

> 206 − (0.0064 / 0.1) x 5 = **205.7 cfm delivered**

against 205 cfm required by MN 1322 R403.5 and 210 cfm of design intent. **The system clears
the code rate by 0.3 % and falls 2.0 % short of the intent.**

> ⚠ **THE SIDES SWAPPED, AND THE PREVIOUS REVISION OF THIS SECTION PREDICTED IT.** The
> 2026-09-15 rebalance left extract governing by 0.0086 in. and this note said in as many
> words that "the next improvement to the extract side buys almost nothing, because the
> supply side takes over within a hundredth of an inch". `DU-ERV-EA` 6" -> 8" was then bought
> and extract fell 0.0704 — of which only the first 0.0086 bought anything. **The remaining
> 0.062 in. of extract margin is not a saving; it is headroom nobody is spending.**
>
> So the two extract levers still on the table — the elbow audit (11 six-inch elbows on the
> extract trunks) and riser segmentation — are now worth **nothing at all** to the delivered
> figure, and should not be bought for this reason. They may still be worth buying to get the
> riser's 0.203 down as insurance, since that one term is 59% of its column and is the thing
> that grew when the feed was drawn honestly. Every lever that moves the DELIVERED number
> from here is on the SUPPLY side: `DU-ERV-RISER-SUP` (0.1367), `DU-ERV-OA` (0.1318) and
> `DU-S-ERV-HP-FEED` (0.0630) are 82% of the governing column.

> ⚠ **THE TWO SIDES HAVE ALL BUT CONVERGED, AND THAT CHANGES WHICH LEVER MATTERS.** Extract
> governed by 0.051 in. before the rebalance and governs by **0.0086** now (0.4169 against
> supply's 0.4083). The next improvement to the extract side buys almost nothing, because the
> supply side takes over as the governing path within a hundredth of an inch — and every
> lever the owner was offered (`DU-ERV-EA` 6" -> 8", the extract elbow audit, riser
> segmentation) is an EXTRACT lever. Worth 0.0086 between them, and then the arithmetic
> changes. Re-read this section before buying any of them; the supply column's own big terms
> are `DU-ERV-OA` (0.1318) and `DU-ERV-RISER-SUP` (0.1382).
>
> **And the code margin is now 0.1 %**, which is 0.2 cfm. It was 1.9 %. The rebalance moved
> the delivered figure UP, so this is not a loss — but a margin that thin is a commissioning
> measurement, not a calculation, and §8's instruction to measure it with a low-flow hood
> stops being advice.

**The rejected build, for the record.** Insulated flex is what a Twin Cities contractor
reaches for on a 6" ERV leg. The same two outdoor runs, worked at flex's roughness and bend
length:

| | `DU-ERV-OA` | `DU-ERV-EA` | pair |
|---|---|---|---|
| 6" galvanized in an R-8 wrap | 0.1318 | 0.1666 | **0.2985** |
| 6" insulated flex | 0.2683 | 0.3082 | **0.5766** |

Flex costs **0.28 in. w.g. more on two runs** — more than half the machine's whole budget,
and it would take delivered flow to about 195 cfm, under MN's 205. **Rigid pipe here is not
a refinement, it is what makes the system legal.** `DUCT-T-FLEX-6` stays in the catalog,
named by no run, so this comparison reads off typed data.

## 7. Broan's own instruction, and what obeying it would cost

The B210E75RT installation manual carries one distribution instruction: **above 200 cfm with
long runs or many elbows, take the trunk up to 8 in.** This system is 210 cfm with 30 ft of
outdoor leg and eleven elbows on it, so the instruction is squarely aimed at it.

Worked at 8" galvanized (ε unchanged, bend equivalent 6'-6" = 0.22 x 0.6667 / 0.0232):

| run | at 6" | at 8" | saved |
|---|---|---|---|
| `DU-ERV-EA` | 0.1666 | 0.0486 | 0.1180 |
| `DU-ERV-OA` | 0.1318 | 0.0416 | 0.0902 |

Upsizing the two outdoor legs alone takes the extract path to about **0.339 in. w.g.** and
delivered flow to about **207 cfm**, plus roughly 0.02 in. for a 6→8 transition at each ERV
collar and each hood — call it **0.36 in. and 206.5 cfm**. It buys about 3 cfm.

**It is priced here and not built.** What it costs: ~43 LF of 8" pipe in place of 6" (about
$60–130 of material), two 8" wall hoods and two enlarged flashed penetrations in place of
the 6" pair already modelled (`AO-M-ERV-OA`, `AO-S-ERV-EA` are 7" rough openings; a 9"
opening still lands inside a stud bay and still takes no header, but it cuts a second girt
course), and four 6→8 transitions. Roughly **$400–900 all in**, for 3 cfm the house does not
need. The NW chase has the room — four 6" insulated risers at about 25 % fill — so if the
commissioning measurement in §8 comes in under 205, this is the lever, and it is the first
one to pull.

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

- **The risers are worked at 210 cfm over their whole length.** `DU-ERV-RISER-EXH` really
  carries 200 cfm below the level-2 tap and 54 above it; `DU-ERV-RISER-SUP` likewise. The
  authored `design_cfm` is what is graded, because the tap elevation is not a typed fact and
  inferring one would be the check inventing a number. Worked segmented, the extract riser
  costs 0.0700 in. instead of 0.1472 and the path total falls to **0.382 in. / 206.4 cfm**.
- **The trunk chain is summed whole.** `DU-S-ERV-HP-FEED` is a parallel branch off the
  supply riser, not a segment of the path to `DU-B-ERV-R-PLAY`; summing it over-counts the
  supply path by 0.0633 in. The supply path does not govern either way.
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

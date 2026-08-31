# Cost options — priced upgrades and downgrades

Started 2026-08-08. Menu of swaps if the number needs to come down, each priced against a
line in `houses/catlin/prices.toml`. **Nothing here is decided** — the plan as authored is
the plan, this is the menu.

**Rules:** every row cites the prices.toml line and the delta at both ends of the range —
an unpriced idea lives in TODO.md's "potential cost cutting" list until it has a number. A
swap that changes what the house *does*, not just what it costs, gets a **cost of the cut**
note. Rows are material+labour unless noted.

**Start here:** [Premium features](#premium-features--what-each-one-costs-2026-08-24) — what
each optional thing costs — and the
[cost-reduction sweep](#cost-reduction-sweep--2026-08-24) — everything worth $3,000 or more
off the bottom line. Both were added 2026-08-24, both measured against the 2026-08-23
baseline below, and both quote **bid totals**, not section deltas.

## Baseline — it moved four times; read this before comparing rows

| date | change | before → after |
|---|---|---|
| 08-18 | suspended deck got its own price key (was billed at slab-on-grade rate) | $274,206–562,712 → $307,330–627,774 |
| 08-20 | labour added to file (21/24 sections were $0 labour) | constr. total $306,982–627,214 → **$574,980–1,135,114**; labour $0 → $211,280–421,533; $/gsf $51–104 → $96–189 |
| 08-20 | allowance register authored in + 3 of 4 bid-ladder stages turned on | net $576,557–1,139,150 → **total $978,947–2,061,452**; $/gsf $96–189 → **$163–343** |
| 08-23 | mixed-deck bearing seat, 8'-0" pour, joist alignment (net of every TAKEN row below) | **total $951,336–1,992,450**; $/gsf **$138–289**; $/conditioned sf **$162–341** |

Four owner decisions on 08-20 took **$64,782** off the high end: wire closet shelving not
laminate (−$35,000), summer pour (−$21,000), code-min ice barrier confirmed as base scope,
suburban Hennepin's 8.525% tax not the city's 9.025% (−$3,182).

`[markup]` (GC overhead/profit, ~$130,000–375,000) is **off by choice**, present at zero.

A delta below is measured against the *section* it names, not the total — the bid ladder
multiplies it ~1.20x (waste, 10% contingency, material tax) on the way to the bottom line,
~1.40x if markup is switched on. A $10,000 saving in `envelope_layers` is ~$12,000 off the
printed total today.

**Two conventions live in this file, and every row says which it uses.** The rows above and
below this line are *section* deltas. The two 2026-08-24 sections that follow — the premium
menu and the cost-reduction sweep — quote **bid-total** deltas instead, measured by rebuilding
the estimate with the change made. The measured ladder multiplier is **~1.17x**, not the 1.20x
estimated above.

## Premium features — what each one costs (2026-08-24)

Asked for directly: the things this house has that an ordinary 5,100 sf Minnesota house
would not, each with a number against it.

**Every figure in this section is a BOTTOM-LINE delta** — what the printed `haus takeoff`
total moves by — not a section delta. It already carries waste, the 10% contingency and
material tax; `[markup]` is still off. That is deliberately a different convention from the
rest of this file, and the rows say which one they use.

**Method.** Delete the feature's elements from the *resolved* model, re-run
`bill_of_materials` + `estimate_costs`, diff the bid total. Where a feature cannot simply be
deleted — something else has to stand where it stood — the replacement is costed off named
`prices.toml` rows and subtracted. Those rows show their arithmetic below the table.

| feature | cost | of the $951k–$1.99M total | |
|---|---|---|---|
| **Habitable cathedral-roofed attic** — 1,281 sf of floor *and* the hot roof over it | **$89,000–160,000** | 9.4% / 8.0% | vs a trussed cold attic |
| **Sunken garden / porch / balcony** — the freestanding concrete structure | **$47,900–86,900** | 5.0% / 4.4% | balcony alone is $10,300–19,100 of it |
| ⏳ **PV array + battery backup** — 5.28 kW, 14.3 kWh, EG4 12kPV | **$38,000–73,000** | 4.0% / 3.7% | defer, but pre-wire |
| **Sauna** — 127 sf, heater, benches, T&G liner, shower, its own ERV pair | **$12,700–29,500** | 1.3% / 1.5% | |
| **Insulated + heated detached garage** — the insulation and the heat only | **$12,500–24,000** | 1.3% / 1.2% | the whole garage is $62,300–119,100 |
| ⏳ **Raised garden apron** — 245 SF of SRW wrapping the sunken garden | **$8,700–17,400** | 0.9% / 0.9% | defer |
| **Concrete deck over the theatre** — 414 SF of LiteDeck + cast cap | **$6,300–10,700** | 0.7% / 0.5% | premium over I-joists |
| | **$215,100–$401,500** | **22.6% / 20.2%** | |

⏳ **easy to defer to a small later renovation** — both are outside the weather envelope and
neither is trapped behind finished work. The raised garden is a landscape contract that can
be let any spring. The PV + battery is deferrable *only if the roof, the conduit and the
service are built for it now*: `ED-A-PV-JB`, the attic riser conduit, the backup subpanel
enclosure and the 12 S-5! PVKIT seam clamps are ~$1,500–3,500 of the $38,000–73,000 and
they are the part that is expensive to retrofit. Leave those in, defer the modules, racking,
inverter and battery — **$34,500–69,500** deferred for ~$1,500–3,500 of insurance.

Deferring both ⏳ rows takes **$43,200–86,900** out of the first build.

### Habitable cathedral attic — **$73,000–141,000** (re-measured 2026-08-29)

> **RE-MEASURED AFTER THE ATTIC REWORK.** The $89,000–160,000 below was struck 2026-08-24
> against the 5'-0" knee-wall / 4:12 attic and a hand-tabulated put-back. It has been
> re-run end to end against the built 6:12 rafter-plate attic, this time with the trussed
> cold attic **modelled** rather than tabulated — a `CATLIN_TRUSS_ROOF` assembly (4:12,
> energy-heel truss, 19 1/4" of blown fibreglass to R-60, one 3/4" plywood deck, the same
> mechanically-seamed panel) carrying the same gable-end walls, with the PV array and the
> eave water chain held constant on both sides so only the roof system and the habitable
> storey move.
>
> | | low | high |
> |---|---|---|
> | built, cathedral attic | $809,859 | $1,690,900 |
> | trussed cold attic | $737,123 | $1,550,079 |
> | **premium** | **$72,736** | **$140,822** |
>
> Split, with the `11.875 I-joist` row divided by measured length (1,115 LF of rafter vs
> 987 LF of `FS-ATTIC` joist and trimmer) rather than guessed:
>
> | | low | high |
> |---|---|---|
> | roof SYSTEM swap (rafter + polyiso cathedral → truss + blown-in) | −$27,900 | −$49,000 |
> |   · insulation: 6" polyiso + R-19 rafter batt → R-60 blown | −$8,476 | −$13,813 |
> |   · deck: ZIP + OSB nailbase → one 3/4" plywood deck | −$7,449 | −$13,007 |
> |   · membranes, underlayment, vent mat | −$3,576 | −$7,247 |
> |   · rafters out (I-joist share) | −$5,144 | −$8,651 |
> |   · **trusses IN, ridge beam + hangers + ridge cap OUT** | **+$290** | **−$243** |
> |   · roofing panel, same skin over ~90 SF less roof | −$930 | −$1,639 |
> | habitable storey fit-out (deck, finishes, openings, stair, MEP, interior walls) | −$45,300 | −$94,300 |
>
> **The truss framing is a wash, and it is not the crane that makes it one.** 2,368 LF of
> truss lumber costs almost exactly what the I-joist rafters, the `2-1.75x16 LVL` ridge beam,
> its `LSSR` hangers and the ridge cap cost together. And the model is *generous* to the
> truss here: `[framing]` still has no roof-truss row, so 36'-0" shop-fabricated trusses are
> billed at the `2x4` stick rate ($1.20–2.00/LF installed = $2,842–4,736) against a market
> $5.00–9.00/SF of footprint ($6,480–11,664). Carry that correction and the framing swap goes
> to roughly break-even and the premium to **$69,100–133,900**. **A truss row belongs in
> `prices.toml`** — this is the second time it has had to be hand-sourced.
>
> The saving is in the *insulation and the deck*, not the framing: a vented attic does not
> need 6" of continuous polyiso, a nailbase deck over it, a deck vapour barrier or a vent
> mat. That is $19,500–34,100 of the $27,900–49,000.
>
> **Per square foot it is still the cheapest floor area in the building.** $72,736–140,822
> buys back 1,170.9 conditioned SF (5,001.3 → 3,830.4), i.e. **$62–120/SF** — against
> **$134–279 per gross SF** and **$162–338 per conditioned SF** for the house as a whole.
> 609.5 SF of what goes is already `storage`-typed; ~561 SF is finished habitable room.
>
> **And it is an air-barrier decision, not only a money one.** The cathedral roof keeps every
> control layer outboard of structure and unpenetrated. A blown attic moves the air barrier
> to the ceiling plane, where every can light, partition top plate and attic hatch crosses it.
> Cheaper per R, harder to keep tight.
>
> Method: `houses/_ablate_attic`, a full house copy with `.with_elements("attic", ...)`
> replaced by a `plan/storeys/attic_truss.py` that reuses `attic.NODES` and the six gable
> walls by tag and adds one `CATLIN_TRUSS_ROOF` roof. Deleted after measuring; re-create it
> the same way.

#### The 2026-08-24 measurement, superseded — $89,000–160,000

The single largest optional thing in the house, and this is the number
`plans/TODO.md`'s "remove the attic level and switch to truss/blown-in" line has been
waiting for since it was written.

| | low | high |
|---|---|---|
| delete the attic storey **and** `RF-HOUSE`/`RB-HOUSE`/`FS-ATTIC`/`ST-S2A` | −$131,528 | −$240,185 |
| put back a trussed cold attic (below) | +$42,600 | +$80,400 |
| **premium** | **$88,900** | **$159,800** |

Gross area 6,027 → 4,664 sf; conditioned 5,113 → 3,832 sf. Bill-of-materials movers:
`envelope_layers` −$60,956/−$108,496, `framing` −$22,075/−$37,542, `openings`
−$8,415/−$17,345, `sheet_goods` −$8,670/−$14,856, `floor_finishes` −$5,532/−$12,541.

The put-back, priced off this file's own rows (trusses are the one number not sourced here —
`[framing]` has no truss row for a 36'-0" roof truss, so $5.00–9.00/SF of footprint is a
market rate, not a house number):

| | low | high |
|---|---|---|
| 36'-0" gable trusses @24" o.c., energy heel, set, 1,296 SF footprint | $6,480 | $11,664 |
| 7/16" OSB deck, 1,436.6 SF (`envelope_layers` "osb" basis) | $1,724 | $3,161 |
| synthetic underlayment, 1,436.6 SF (`roof-underlayment-synthetic`) | $1,221 | $2,730 |
| standing seam retained, 1,436.6 SF (`standing-seam`) | $15,084 | $26,577 |
| edge trim + eave water chain, unchanged (`edge_trim`) | $2,070 | $4,805 |
| blown fibreglass to R-60 over 1,296 SF (`blown-fiberglass` ×1.6 for depth) | $1,866 | $4,562 |
| flat ceiling: gwb + paint, 1,296 SF (`gwb` + `latex-paint`) | $4,019 | $7,322 |
| two gable triangles still clad, 216 SF of `CATLIN_EXT_2X6` | $3,024 | $5,616 |
| attic access, ridge/edge venting | $900 | $2,300 |
| net | $36,388 | $68,737 |
| × the bid ladder (~1.17) | **$42,600** | **$80,400** |

**Read this before treating it as a saving.** $89,000 over 1,281 sf is **$69–125 / sf**,
against **$138–289 / gross sf** for the house as a whole. *The attic is the cheapest square
footage in the building* — it buys no foundation, no site work and no extra stair run, and
1,079 sf of it (`RM-A-WEST-UNFIN` 598, `RM-A-EAST-UNFIN` 481) is already typed `storage`, i.e. the
cheapest finish level in the house. If square footage is wanted anywhere, it is wanted here
before anywhere else.

**Cost of the cut** is bigger than the money. The 5' knee walls, the N–S structural ridge
(`RB-HOUSE` on `W-A-C1/C2`, which stacks unbroken to the footings), `FO-A-STAIR`, the whole
south gable composition (four openings mirrored about x=18') and `params/solar.py`'s 12-module
fit on the ridge planes are all consequences of this decision. It is a re-design of the
building's whole upper third, not a line item. It also drops `preferences.toml`'s R-60 roof to
whatever the blown depth reaches, and swaps every control layer from outboard-of-structure to
a ceiling plane — a different building-science argument entirely (see `CATLIN_ROOF`'s note).

### Sunken garden / porch / balcony — $47,900–86,900

Ablating every `*-SG-*` element: bid $951,336–1,992,450 → $903,397–1,905,540.
`wall_structure` −$14,590/−$26,262 (29.2 cy of `SUNKEN_GARDEN_WALL`), `concrete`
−$12,147/−$23,214, `sheet_goods` −$8,496/−$15,900 (the aluminium balcony plank, see the
sweep below), `footing_bedding` −$3,592/−$5,389, `framing` −$1,198/−$1,974,
`timber` −$764/−$1,311.

Sub-slices, each measured on its own: **balcony** (`FS-SG-DECK`, `RL-SG-BALCONY`, three
`BM-SG-BL*` beams, six `PT-SG-B*` pillars) **$10,323–19,071**; **Ishtar-gate brick veneer**
(`W-B-BRICK` + `FT-B-BRICK` + the two arched reveals) **$3,322–7,107**.

Not included and not modelled: the E–W lateral bracing the arch removal left open
(`plans/TODO.md`), and the seven `FT-SG-*` footings that `structural.frost_depth` routes to
UNKNOWN. Both go to the same engineer, and neither is free.
*(2026-08-30: the frost question closed on 2026-08-29 via ASCE 32 soil replacement, and the
FOUNDATION half of the E-W question closed with `W-SG-ARCH`'s return as a grade beam — see
"Sunken-garden arch → column, beams, metal railing" under **Taken**. The deck-and-balcony
half above the garden floor is still open and still goes to the same engineer.)*

### PV array + battery backup — $38,000–73,000

`[allowances] electrical-pv-array-modules-and-racking` $24,000–46,000 (→ $26,400–52,900 after
contingency) plus the modelled hardware: ablating `SP-A-PV-*`, `EQ-B-ESS-INV`, `EQ-B-ESS-BATT`,
`ED-B-BACKUP-*`, `ED-A-PV-JB`, `RM-B-ESS` and `W-B-ESS-*` moves the bid total
−$11,152/−$19,608, almost all of it `placeables` (−$8,610/−$14,935 — the 12 kPV hybrid inverter
and the 14.3 kWh PowerPro).

**The allowance is the weakest number in it.** $24,000–46,000 for 5.28 kW DC is
**$4.55–8.71 per watt**. Published 2026 US residential installed cost sits at $2.60–3.60/W,
and a small (<6 kW) system in the Twin Cities at $3.50–4.50/W — i.e. **$18,500–23,800** for
this array. One quote is worth $6,000–22,000 here and is the highest-value phone call on the
list after the roofer's. See **Open questions**.

### Sauna — $12,700–29,500

Ablating `RM-B-SAUNA`, `W-B-SA-W/N`, `EQ-B-SAUNA-HTR`, the two benches, `D-B-SAUNA`,
`WIN-B-SAUNA`, the drain/vent run and the dampered ERV pair: **−$10,748/−$25,591**
(`placeables` −$2,913/−$8,915, `envelope_layers` −$2,617/−$4,807, `floor_finishes`
−$1,460/−$3,358, `openings` −$1,065/−$2,250).

Plus what the ablation cannot reach: the liner that rides on concrete rather than on a
sauna-only wall — 177.1 SF of `sauna-shiplap` ($1,860–3,542) + `polyiso-foil` ($460–832) on
`W-B-S2` and `W-B-CS`, less the $549–1,001 of gwb + paint those walls would carry instead.
**+$2,000–3,950** after the ladder.

The two liner assemblies (`SAUNA_LINER_ON_CONCRETE`, `SAUNA_LINER_ON_BASEMENT_8_GARDEN`) are
the reason the sauna is not simply two partitions: its vapour control has to be continuous on
all four sides, so two basement walls carry a second, house-local stack.

### Insulated + heated detached garage — $12,500–24,000

The garage entire is **$62,250–119,051** (571 sf, `RM-GARAGE` + `RF-GARAGE` + `W-G-*` +
`W-GF-*` + `SL-G-*` + `D-G-*`). What "insulated" costs inside that, against the same box
built cold, unlined and unheated:

| | low | high | source row |
|---|---|---|---|
| ICF stem, 8.8 cy + 952.5 SF of form | $12,859 | $22,385 | `wall_structure GARAGE_ICF_6`, `envelope_layers icf-eps` |
| *less* a conventional formed 8" frost wall, 9.8 cy | −$4,851 | −$7,938 | `CATLIN_BASEMENT_8`'s re-derived $495–810/cy |
| 1.5" Zip-R, 663.3 SF, *less* plain 7/16" OSB | +$1,526 | +$2,919 | `envelope_layers zip-r` vs `osb` |
| blown fibreglass, 576 SF at 14.5" | +$518 | +$1,267 | `envelope_layers blown-fiberglass` |
| gwb band on the ICF stem above grade (R316.4) | +$217 | +$372 | `envelope_layers gwb` |
| unit heater + its 240 V circuit and conduit | +$400 | +$1,200 | `EQ-T-GARAGE-HEATER`, `[conduit]` |
| net | $10,669 | $20,205 | |
| × the bid ladder | **$12,500** | **$23,600** | |

**Two-thirds of it is the ICF stem, not the insulation** — see the sweep below, where
swapping it for a conventional frost wall stands on its own as a $9,400–16,900 line. The
garage walls themselves carry no cavity insulation by decision (2026-08-20); only the Zip-R
and the ceiling are thermal layers, so this is already the cheap version of a warm garage.
Interior wall gypsum is not in the table: it is inside `envelope_layers`' 11,392.8 SF bulk
`gwb` row and cannot be separated out, and a detached garage 4' from a dwelling may want it
for exposure reasons regardless.

### Raised garden apron — $8,700–17,400

Ten elements (`W-RG-*` and their levelling pads): `wall_structure` −$7,350/−$14,700 for
245 SF of `RETAINING_BLOCK_12`, `footing_bedding` −$136/−$287. No engine work, no envelope,
no MEP — which is exactly why it defers cleanly.

### Concrete deck over the theatre — $6,300–10,700

Deleting `SL-M-DECK` alone: **−$11,450/−$20,843** (`envelope_layers` −$5,092/−$8,032, the
10" LiteDeck forms; `concrete` −$4,562/−$9,683, the 18.37 cy). Putting 414 SF of 11-7/8"
I-joist floor back at this file's own researched $10.58–20.94/SF is **+$5,125/+$10,143**
after the ladder. The finish is close to a wash — 411 SF of cream polish
($1,751–3,708, and a $2,000–3,500 mobilisation lump either way) against LVP at $1,449–3,623.

**Cost of the cut**, as recorded on 2026-08-21 and still true: the acoustic isolation over
`RM-B-PLAY-N` is the whole point of the line, `FH-M-DINING` is an `in_slab` embed that would
re-author to mat-under-LVP, and the thermal mass sits under the south glazing the facade is
composed around. The flat bearing seat of 2026-08-23 does not change any of that.

## Cost-reduction sweep — 2026-08-24

Asked for: things that take real money out without giving up a high-performance house.
**Threshold for appearing here is $3,000 off the bottom line.** Same convention as the
premium table above — every number is a **bid-total** delta, not a section delta.

Four of these were priced by actually building the change: a copy of the house with the
edit made, `haus check` run to confirm it stays at 0 FAIL, and `haus takeoff` run to read
the total. Those rows say **built**. The rest are arithmetic on named `prices.toml` rows.

| # | change | saves | how priced |
|---|---|---|---|
| 1 | **Attic level → trussed cold attic + blown R-60** | **$89,000–160,000** | see above |
| 2 | ⏳ Driveway apron + walks — defer to a later contract | $18,000–44,000 | allowance |
| 3 | **House-wall cladding: standing-seam snap-lock → exposed-fastener PBR panel on the same girts** | **$14,043–30,279** | **TAKEN 2026-08-26**, 0 FAIL |
| 4 | Excavation: reuse spoil on site instead of hauling off | $10,000–25,000 | allowance note |
| 5 | Roofs (house + garage, 2,186 SF): standing seam → architectural asphalt | $9,700–18,200 <br>+$1,500–3,000 of snow retention | built |
| 6 | ~~Garage ICF stem → conventional formed frost wall~~ | ~~$9,400–16,900~~ **WITHDRAWN 2026-08-29 — real figure ~$1,000–1,800** | arithmetic on a double-billed rate |
| 7 | ⏳ Raised garden apron — defer | $8,700–17,400 | ablation |
| 8 | Windows: mid-range clad/fibreglass → vinyl or entry fibreglass, same U-0.25 | $6,500–11,000 | the `[openings]` note's own number |
| 9 | Concrete deck over the theatre → I-joists | $6,300–10,700 | see above |
| 10 | Delete the 8 discretionary attic windows | $6,200–12,100 | built, 0 FAIL |
| 11 | Exterior CI: 4" → 2.5" of ccSPF (R-38.7 → R-32.7) | $5,600–8,000 | built, 0 FAIL |
| 12 | Plant room → an ordinary second-floor room | $5,300–10,400 | arithmetic |
| 13 | Trim, stool and apron package simplified | $5,000–13,000 | allowance scope |
| 14 | Oak floor + red-oak stair treads → LVP / carpet | $4,300–6,800 | `[floor_finishes]` |
| 15 | Exterior guards: Trex Signature → builder-grade aluminium | $3,700–5,700 | `[railings]` |
| 16 | Balcony aluminium plank → walkable PVC membrane deck | $3,400–10,000 | `[sheet_goods]`, low confidence |
| 17 | Ishtar-gate glazed brick veneer → plain brick, or delete | $3,300–7,100 | ablation |
| 18 | HVAC System 3 folded into the multi-zone | $3,000–5,400 | ablation + line-set allowance |

**These do not add up, and must not be summed as they stand.** Row 1 swallows row 10 whole
and shrinks rows 3, 5 and 11 (a smaller house has less wall, less roof and less continuous
insulation). Row 6 is two-thirds of the "insulated garage" premium above; rows 7 and 9 are
the same money as the ⏳ raised-garden and concrete-deck rows in the premium table; row 16 is
inside the sunken-garden number. **Decide row 1 first** — everything else is priced against
the house as drawn and has to be re-read if the attic goes.

With the attic **kept**, and counting each of the remaining seventeen once:

| | low | high | |
|---|---|---|---|
| permanently cheaper (rows 3–6, 8–9, 11–18) | **$91,100** | **$177,200** | 9.6% / 8.9% of the bid total |
| deferred, not saved (rows 2 and 7) | $26,700 | $61,400 | comes back as a later contract |
| out of the first build | **$117,800** | **$238,600** | 12.4% / 12.0% |

None of the seventeen touches the wall assembly, the air barrier, the ERV, the ACH50 target
or the window U-value. The only one that spends measurable building performance is row 11 —
and it is the smallest of the four built rows, which is the argument for weighing it last.

### 3 — the wall cladding is the biggest lever that is not a feature

> **TAKEN on 2026-08-26.** The house walls are `pbr-panel-26`, a 26 ga exposed-fastener PBR
> panel at $4.50–7.25/SF installed. The realised saving is **−$14,043 / −$30,279** on
> `subtotal_net` and **−$16,778 / −$36,318** on the full marked-up total — the low end lands
> on this row's pre-flight estimate and the high end runs past it, because the pre-flight
> was written against 3,512 SF and the resolved area is 3,672 SF. The garage was **excluded**;
> see the note at the end of this section. Figures and caveats below are the original
> estimate, kept as written so the estimate can be judged against the outcome.

3,512.2 SF of `standing-seam-snaplock` at $8.75–16.00/SF installed = **$30,732–56,195** —
the largest single row in the *resolved* bill of materials (allowance lump sums aside),
ahead of the 11,392.8 SF of gypsum ($17,659–30,191) and the roof's own metal
($15,084–26,577).

It is a *rainscreen skin*: it carries no structure, no air control, no water control and no
thermal control — the Swinburne truss wall's 4" of ccSPF is all four of those at once. So it
is the one big exterior line where a downgrade costs nothing but looks.

Re-priced at $5.00–9.00/SF installed (steel or engineered-wood lap, or a fibre-cement panel —
the band published for metal siding and for LP SmartSide alike): total
$951,336–1,992,450 → **$935,575–1,963,226**, **−$15,600 / −$29,000**.

- **The girts decide what can go on, and since 2026-08-26 they decide in favour of more.**
  The wall's stand-off is now two tiers of KDAT/SPF 2x4 laid **flat and horizontal** at 24"
  o.c. (the catlin truss), not the vertical outriggers this row was written against. A
  vertical ribbed or corrugated panel wants exactly this — horizontal girts — so the "would
  need a second layer, which eats a third of the saving" caveat is **gone**: the substrate is
  already there. Horizontal lap is the one that now wants thought, since its nailer would
  want to be vertical; a lap panel spanning 24" between girts is ordinary, but check the
  product's span rating before assuming it.
- **A half version exists.** Keeping standing seam on the south and west elevations
  (~1,212 SF) and lapping north and east (~2,300 SF) is roughly **−$10,000 / −$17,600**.
- **Cost of the cut:** this is a metal-clad house whose roof, walls, corner trim and edge
  trim are one continuous material, and `brief.md`'s style line says so. Lap siding on the
  walls makes the roof a different material from the walls for the first time, and the
  elevations want revisiting. Exposed-fastener products also put 20–30 year gasketed screws
  on the wall where there are none today.

**What was actually taken, and how it differs from the row above.** The swap went to a
36"-coverage PBR panel, not to lap siding, so the "metal-clad house" objection under *cost
of the cut* mostly does not land: the walls are still white PVDF steel and still declare
`skin_family="standing-seam"`, which is what keeps the flush zero-overhang roof edge
(`resolve/roof_edge_geometry.continuous_skin_cladding`) instead of reverting it to a
fascia-and-drip-edge detail nobody drew. The gasketed-screw caveat does land, in full: 3,098
of them, and the gaskets set the service life.

**The garage was excluded, deliberately.** `GARAGE_WALL_2X6` has no furring at all — cladding
sits straight on Zip-R — so PBR there needs a whole new girt layer plus through-insulation
structural screws, and that cost cancels the saving over 631 SF. It keeps
`standing-seam-nailstrip-26`, and with it its 28 `S-5-N` wind clamps. Both roofs are untouched.

**Three smaller lines moved with it**, and two of them are not economies:

| line | before | after | delta |
|---|---|---|---|
| house-wall cladding, 3,670.7 → 3,672.2 SF | $32,119–58,731 | $16,525–26,623 | **−$15,594 / −$32,108** |
| 48 `S-5-S` wall wind clamps | $300–492 | — | −$300 / −$492 |
| 11 CanDuit rings + 13 S-5! seam clamps (11 carried, 2 on enclosures) | $227–437 | $32–58 | −$195 / −$379 |
| 3,098 T09150HWAM panel screws | — | $1,794–2,246 | **+$1,794 / +$2,246** |
| **net on `subtotal_net`** | | | **−$14,043 / −$30,279** |

The `S-5-S` clamps and the CanDuit rings went because they *cannot work* on a seamless panel,
not to save money: the S clamp closes on a snap-lock leg, and `S5_CANDUIT_PIPE_CLAMP` declares
`requires_role=ROLE_STANDING_SEAM_CLAMP`, so every ring ordered brings a bracket that would
have nothing to grip. The screws are the counterpart — the first cladding fixings in this
house billed as a counted part rather than inside a $/SF rate.

### 5 — the roof row in this file was wrong, and here is the honest split

The **Standing-seam metal roof → architectural asphalt shingle** row in *Downgrades* below
compares $54,777–99,331 of metal over 6,322 SF against $31,600–56,900 of asphalt, then says
in its own detail that only 2,180 SF of that is roof and the other 4,143 SF "is not
shinglable". Both halves are true and the subtraction between them is not — the row's headline
"**~$20,000–42,400, the biggest lever on the list**" is really two different swaps added
together, and the asphalt column is priced over area that can never take asphalt.

Split honestly, both built:

| swap | area | current | saves |
|---|---|---|---|
| **roofs only** → architectural asphalt, both roofs | 2,186 SF (`RF-HOUSE` 1,436.6 + `RF-GARAGE` 749.6) | $20,331–36,322 | **$9,700–18,200** |
| **house walls only** → PBR panel (row 3 above, TAKEN) | 3,672.2 SF | $32,119–58,731 | **$14,043–30,279** *(realised)* |
| *garage walls, left alone* | 663.3 SF (`standing-seam-nailstrip-26`) | $3,980–7,296 | *under threshold on its own* |

Plus, on the roof swap only, the S-5! seam clamp family and the formed ridge cap go away:
~$1,500–3,000 more, per this file's existing note. So the roof-only lever is
**$11,200–21,200** and the wall-only lever is **$15,600–29,000**; together **$26,800–50,200**,
which is where the old row's $20,000–42,400 was reaching. They are independent decisions and
should be taken as two.

Everything the old row says about the *cost of the cut* stands, and the PV argument is the
strongest part of it: `S-5-PVKIT` clamps to a standing seam with zero penetrations, and
asphalt needs 48 flashed penetrating feet instead.

### 6 — the garage ICF stem — **WITHDRAWN 2026-08-29. KEEP THE ICF.**

> **This row was arithmetic on a double bill, and the double bill is now gone.** The $27–47
> per SF of wall it convicted the ICF of was never a real price — it was `GARAGE_ICF_6`
> (an **installed** ICF wall rate, blocks included, by its own comment) plus
> `[envelope_layers]."icf-eps"` billing the same blocks a second time at $6.50–11.50 per
> face-SF over 952.5 SF, which is **both faces** of one 476 SF stem. `icf-eps` is zeroed as
> of 2026-08-29 (see *Refactors*), and `GARAGE_ICF_6`'s labour half came down 30% the same
> day for wall height. The stem now prices at **$12.31–19.63/SF**, inside every published
> band. Against a conventional formed 8" wall the honest saving is about **$1,000–1,800**,
> in exchange for R-22 → R-10 on the garage's only below-grade thermal layer. **Under the
> threshold, and not worth taking.** The paragraph below is kept for the record; its
> concrete comparison still holds, its ICF number does not.

~~`GARAGE_ICF_6` is 8.8 cy of core at $758–1,299/cy plus 952.5 SF of EPS form at
$6.50–11.50/SF — **$12,859–22,385**, or **$27–47 per SF of wall**, for a 476 SF frost wall
under an unheated-by-default detached garage.~~ A conventional formed 8" wall at this file's
own re-derived $495–810/cy (see the 12"→8" entry) is $4,851–7,938 for the same 9.8 cy,
forms in the rate.

~~**−$8,000 / −$14,400 net, −$9,400 / −$16,900 after the ladder.**~~

- **Cost of the cut:** R-21.9 → R-1.8 on the stem, and the stem is the garage's only
  below-grade thermal layer. If the garage stays heated, ~64 LF × 5' of uninsulated frost
  wall is a real loss; 2" of exterior XPS on a conventional wall buys most of it back for
  $1,900–3,800 and still lands well under the ICF.
- **This file's two existing garage rows go the *other* way** (full-height ICF at
  +$3,540–7,940 net, CMU at +$11,200–15,600, both under *Upgrades* below). This is the third
  direction and the only one that is cheaper than what is drawn.
- The `_find_framed_on_concrete` sill logic already fires for a formed concrete stem
  (`material_ref == "concrete"`), so unlike the two upgrade rows there is no engine gap here.

### 10 — the eight discretionary attic windows

> **STALE SINCE 2026-08-29 — THIS OPTION IS NO LONGER FREE, AND THE SENTENCE BELOW IS WHY.**
> `RM-A-WEST-UNFIN` became `RM-A-STUDIO`, a guest bedroom, when the west attic was finished.
> Three of these eight windows now do real work and cannot be deleted:
> `WIN-A-S-JUL-W` is the studio's **R310 emergency escape opening** — its 27" x 64" raw
> opening is the only thing satisfying that rule on the storey; and `WIN-A-S2` and `WIN-A-W-S`
> are 7.0 of the 21.3 sf of glazing the room already falls short with. The room passes R303.1
> only under **Exception 1**, on 6,000 lm of artificial light delivering 8.08 fc against a
> 6 fc floor — so removing glazing does not merely fail the natural-light test, it removes
> area from a room that is already relying on the exception. Re-price this option against
> five windows, not eight, and never against `WIN-A-S-JUL-W`.

**Built: 699 pass, 0 fail, 45 not evaluable** — deleting all eight breaks no rule in the
registry. `RM-A-WEST-UNFIN` and `RM-A-EAST-UNFIN` are `storage` occupancy, so R303.1's natural-light
rule never applied to them, and none of the eight is an emergency escape opening.

| unit | ×  | what it is |
|---|---|---|
| `WIN-A-W-N`, `WIN-A-W-S`, `WIN-A-E-N` (`WT-1424`), `WIN-A-E-S` (`WT-1424-T`) | 4 | the 5' knee band, both eave walls |
| `WIN-A-S2`, `WIN-A-S3` (`WT-1448`) | 2 | south gable flankers |
| `WIN-A-S-JUL-W`, `WIN-A-S-JUL-E` (`WT-2464`) | 2 | the juliet pair |

$951,336–1,992,450 → **$945,008–1,980,177**, **−$6,300 / −$12,300**, plus a share of
`[allowances] envelope-opening-flashing-and-sill-pans` and `finish-window-stools-and-aprons`
that is a lump and does not move on its own: 8 of 45 openings is ~$900–2,100 more.

**Why these eight and not any other eight.** `[openings]`' own 2026-08-20 pass found that
windows are priced by **united-inch band, not by area** — a 14x24 costs the same as a 27x36.
Eleven `WT-1424` and two `WT-1448` are the house's thirteen sub-stock-size
units, and the same note flags both families as possibly **below a stock line's minimum
size** (Simonton's awning minimum is 23.5" wide; Andersen 400's narrowest casement is
20-11/16"). So these are the units that cost the most per square inch of daylight *and* carry
the most availability risk. The juliet pair was a third such family until 2026-08-24, when
it widened 18" -> 24" (`WT-1864` -> `WT-2464`) and cleared the casement minimum; it is still
in the cut below for composition reasons, but it is no longer an availability risk, and the
band change (82 -> 88 united inches) makes it ~$120-220 dearer than the figures above. The four in the knee band buy daylight for carpeted storage.

**Cost of the cut is entirely compositional, and it is not small.** `houses/catlin/CLAUDE.md`
spends three paragraphs on this: the knee band "reads as its own row across 5'-6" of blank
wall", the south gable's four openings are exactly mirrored about x=18' and moving
`N-A-V1` to 22'-8" was done to make that mirror possible. Delete them and the south gable
has two openings, and the east/west elevations lose their top row. Render before deciding.

### 11 — 4" of exterior ccSPF → 2.5"

**Built. R-38.7 → R-32.7, 700 pass / 0 fail / 45 unknown — unchanged from the baseline,
including `building_science.condensation`'s monthly Glaser gate.** Design heating load
30,869 → 32,333 BTU/h (+4.7%); cooling 17,923 → 18,268 BTU/h.

One line each in `CATLIN_EXT_2X6` and `PLANT_EXT_2X6_HUMID`: the outrigger's `CavityFill`
thickness 2.5" → 1.0", leaving the 1.5" continuous band behind it untouched. Total
$951,336–1,992,450 → **$945,604–1,984,213**, **−$5,600 / −$8,000**.

- **The ratio is what keeps the sheathing dry, and it survives.** R-16.25 of exterior ccSPF
  against R-21 of cavity is a 0.44 CI-to-total ratio, over the ~0.36 zone 6 wants and over
  IRC Table R702.7.1's R-11.25 minimum for a 2x6 wall. That is *why* the gate still passes,
  and it is the number to re-check before going thinner still.
- `preferences.toml` asks for `wall_r = 40`; this is a deliberate move to R-33, still well
  clear of the MN prescriptive R-20+5ci and still inside the Pretty Good House band for
  zone 6. It is the row on this list that most directly spends building performance for
  money, and it is the smallest saving of the four built rows — **weigh it last, not first.**
- **RESTATE THIS ROW BEFORE COSTING IT (2026-08-26).** It was written against the Swinburne
  outrigger band, where the foam and the vent shared one 3-1/2" layer and the saving was a
  single `CavityFill` thickness. The catlin truss authors the 4" as three separate bands
  (1-1/2" band A, the inner girt's own 1-1/2" fill, and 1" of band C in front of it), so the
  same move is now "drop `foam-vent` to zero and the inner girt's fill to 1-1/2"" — mostly
  the same foam, spelled in a different place. The R numbers above are stale for the same
  reason: the baseline is R-40.7 on the card and ≈R-37.5 honest, not R-38.7.
- **RE-PRICE IT AGAIN AFTER 2026-08-29.** Band C (`foam-vent`, the 1" this row proposes to
  delete) was **not being billed at all** when the −$5,600/−$8,000 above was measured — it
  matched no price key. It is priced now, so this row's saving is *larger* than the figure
  above, not smaller. See *Refactors*.
- **The lumber does not come back with it.** Both girt tiers stay 2x4 flat; what grows is the
  vent gap. Taking the KDAT line down means a narrower OUTER girt, not a narrower foam band,
  and `[framing]` has no 2x3 row — price that separately.

### 12 — the plant room

`RM-S-PLANT`, 159 sf, held at ~75 °F / 70% RH: `PLANT_EXT_2X6_HUMID` /
`PLANT_INT_*_HUMID` carry a fully-adhered vapour barrier and a PVC plank liner, the floor is
heat-welded sheet vinyl with a 6" integral flash cove, and three windows are a **different
manufacturer** (U-0.14 Alpen/Zola class) because `building_science.glazing_dew_point` FAILs
them at U-0.25.

| | low | high |
|---|---|---|
| `pvc-panel`, 445.2 SF | $2,894 | $5,565 |
| `humid-room-membrane`, 445.2 SF | $779 | $1,402 |
| `vinyl-sheet` 179 SF *less* LVP | $1,163 | $2,014 |
| the three `-HP` window units *less* their U-0.25 twins | $845 | $1,845 |
| RH-controlled dampered ERV branch *less* a plain extract | $247 | $575 |
| *less* the gwb + paint an ordinary room would carry on 445.2 SF | −$1,380 | −$2,515 |
| net | $4,548 | $8,886 |
| × the bid ladder | **$5,300** | **$10,400** |

**Cost of the cut is the room, not the finish.** The liner exists to stop 70% RH air reaching
a stud bay; take it out and the room cannot be run at that setpoint, so this is "delete the
plant room", not "cheapen it". The three HP windows are the part that is *not* optional at
75 °F/70% — `glazing_dew_point` is a FAIL check and it FAILs them at U-0.25.

### 13, 14, 15, 16, 17, 18 — the short ones

- **13, trim/stool/apron.** `[allowances]` carries `finish-interior-trim-and-baseboard`
  $12,000–20,000, `paint-trim-and-doors` $8,000–18,000 and `finish-window-stools-and-aprons`
  $3,300–7,400 — $23,300–45,400, none of it modelled. Drywall-return jambs at the 41 windows
  (the house already details its four cased openings exactly that way) plus a flat paint-grade
  base takes **$5,000–13,000** out of that block. **Do not read this as "go trimless"** — the
  `DT-INT-SWING30-TRIMLESS` row in *Downgrades* below shows a hidden-jamb *door* is a 4–5x
  premium, not a
  saving. Returns at windows are cheap; reveals at doors are not.
- **14, oak.** `[floor_finishes]` "oak" is 351 SF at $11.50–20.50/SF installed
  ($4,037–7,196), and its own note says 351 SF is **under most Twin Cities sand-and-finish
  minimums** — a $1,200–1,800 mobilisation plus a trip per coat, for two rooms. LVP over the
  same 351 SF is $1,229–3,071: **−$2,800/−$4,100**. The red-oak stair treads add
  $1,500–2,700 more (the existing *Downgrades* row below; note `stair_finish` is not in the
  priced sections today, so that half does not show in the total).
- **15, guards.** `RAILING-EXT-ALUMINUM-FASCIA` is 74.6 LF (balcony 38.3 + porch 36.3) of
  Trex Signature at $90–135/LF = $6,714–10,071. Builder-grade aluminium at $40–70/LF is
  $2,984–5,222: **−$3,700/−$5,700**. Both guards or neither — the two levels stop matching
  otherwise. (This supersedes the $1,343–2,611 in the *Downgrades* row below, which predates
  the porch guard replacing the masonry parapet.)
- **16, the balcony plank.** `[sheet_goods] "aluminum-deck"` is 6 sheet-equivalents = 182.0 SF
  at $30–52/SF installed = **$6,948–12,252**, and the row itself says **CONFIDENCE: LOW** and
  that no published price exists for any waterproof interlocking aluminium deck. A walkable
  PVC membrane (Duradek/Tufdek class) over a plywood substrate is $12–22/SF installed =
  $2,184–4,004, and the existing downgrade row quotes composite-over-membrane at
  $2,000–3,600. **−$3,400/−$10,000** after the ladder — a wide range because the top end is
  a quote-only product. **Call Versadeck, (651) 356-1870, before deciding**; the existing row
  already says the call may make the swap moot. Dry-below is not optional: this deck is the
  porch's roof.
- **17, the brick veneer.** Ablating `W-B-BRICK`, `FT-B-BRICK` and the two arched reveals:
  **−$3,322/−$7,107**, essentially all `wall_structure` (129.2 SF of glazed lapis, gold and
  brown at $15–27/SF). This supersedes the "$1,233–2,603" *Downgrades* row below. Cost of the
  cut is the entire Ishtar-Gate composition, the voussoir rings and the one place the sunken
  garden has colour — it is a *look* line, and cheap for what it does.
- **18, HVAC System 3.** Installed capacity is ~63,000 BTU/h (`GREE-MULTI-U30` 30k +
  `GREE-SLIM24` 24k + `SAPPHIRE-9` 9k) against a **30,869 BTU/h** design heating load and
  1.49 tons of cooling — roughly 2x, before any cold-climate derate. Folding System 3's
  `EQ-M-HP3-STAIR`/`-OD` pair into System 2's multi-zone: **−$2,574/−$4,593** on
  `placeables`, plus one of the five pairings in `[allowances] hvac-refrigerant-line-sets`
  (~$750–1,400). **The existing downgrade row is right that this is not free money** — the
  Sapphire's true VFD soft-start is what lets it run off the battery. Folding it in gives up
  a battery-backed heat zone unless the inverter is resized.

### Priced and *not* recommended

- **Basement interior 12" walls (`W-B-CN`/`CN2`/`CS2`/`STR`) → 2x6 stud.** Ablation
  −$4,177/−$6,979, but replacing 255.5 SF with framing, gypsum both faces and paint costs
  $2,100–3,700 back — **net $2,100–3,300**, under the threshold, and it retires two-storey
  bearing lines and their footings. The W-B-STR entry below already worked this through in
  detail and reached the same answer.
- **`struct-1-plywood` → OSB on the exterior walls.** Only $0.20–0.55/SF apart in this
  file's own rates: $700–1,930 over 3,512 SF. Not worth the shear-value argument.
- **Consolidating the two second-floor deck doors** (`D-S-DECK-E`/`-W`, both onto the same
  balcony) to one, and one `DT-EXT-FRENCH60` to a `DT-EXT-SWING36`: $1,900–4,200. Under
  threshold at the low end, and it is the south facade.
- **The wall-hung toilet** (`FX-TOILET-WH` $1,010–2,720 against `FX-TOILET-STD`'s $290–960):
  $720–1,760. Under threshold — and **not available at any price**. Re-checked 2026-08-29:
  RM-M-BATH1 is 61.98" x 44.24" between finish faces (the room's resolved `clear_face` reads
  46.73" deep and is centreline-based, so it is not the number to price against). A 28"-deep
  `FX-TOILET-STD` needs 52" of depth on the wall the bowl is on — the governing front
  clearance in Minnesota is UPC 402.5's **24"**, not IRC P2705.1's 21" — and turned onto the
  west wall its 15"-each-side band plus that envelope leaves no strip anywhere for
  `FX-M-BATH1-LAV`. The 19.3" wall-hung bowl is what makes the room work; this row is a
  saving that cannot be taken, not one that is merely small. See `plan/fixtures.py` for the
  arithmetic in every orientation.

  The same pass found the room 1.06" short of that 24" **as built**, and closed it by moving
  W-M-STOS (and the whole y=26'-4" line, both storeys) 2" north to y=26'-6". That is a
  layout change, not a cost line: it spends 2" of `RM-M-MUD-CLOSET`'s depth (34 3/4" ->
  32 3/4", still inside the 32"-36" reach-in band) and buys nothing billable. No fixture
  substitution could have done it — the shortest wall-hung bowl obtainable in the US is
  18.90" against the 18.24" the old room needed.
- **Lighting.** 306 luminaires, runs and controls total **$285–695** of `placeables` movement
  — the fixture *count* is not where lighting money is. It is in
  `[allowances] electrical-branch-circuit-conductors` ($10,000–25,000), which no fixture
  decision touches.

## Downgrades (money back)

| swap | current → new | saves | notes |
|---|---|---|---|
| ~~Standing-seam metal roof → architectural asphalt shingle~~ | ~~$54,777–99,331 → $31,600–56,900~~ | ~~**~$20,000–42,400**~~ | **SUPERSEDED 2026-08-23** — this row adds two independent swaps and prices asphalt over 4,143 SF of wall that cannot take it. Split into roof-only ($11,200–21,200) and wall-only ($15,600–29,000) in the sweep above |
| Elm tudor posts → paint/stain-grade species | $2,006–6,001 → $700–1,500 | ~$1,300–4,500 | 6-1/8" S4S elm isn't a purchasable article — needs a glued-up blank from 8/4 stock. **Get a real quote first** (Wood From The Hood, Siwek Millwork) — low end is only $2,006 |
| Aluminium balcony deck → composite over membrane | $6,948–12,252 → $2,000–4,004 | **$3,400–10,000** (bid total) | RE-PRICED 2026-08-23: the plank grew when it stopped being a Slab (2026-08-22), so the current line is $6,948–12,252, not $5,838–10,290. Still quote-only and still the least certain line in the file. Call Versadeck (651) 356-1870 first — may make the swap moot |
| Fabricated box gutter → seamless K-style | $1,179–2,506 → $600–1,100 | ~$600–1,400 | plus $150–400/ea conductor heads a box gutter needs (not in estimate) |
| Trimless interior door → standard cased prehung | $1,220–2,800 → $305–755 | ~$915–2,045 + schedule risk | hidden-jamb reveal is a 3-trade sequencing item; frame must be set before drywall, so this can't be reversed later |
| Post bases: ABU66SS stainless → ABU66Z/RZ ZMAX | $1,500–2,300 → ~$550 | ~$950–1,750 | wrong $1,000 to save — one detail nobody re-does without jacking the structure |
| Exterior guards: Trex Signature → builder-grade aluminium | $6,714–10,071 → $2,984–5,222 | **$3,700–5,700** (bid total) | RE-PRICED 2026-08-23: 74.6 LF at $90–135/LF, not $2,835–5,222 — the 08-20 material re-source (Signature is the premium line) and the fascia-mount labour premium both landed after this row was written. Covers both balcony (38.3 LF) and porch (36.3 LF) — downgrade together or the two levels stop matching |
| Basement brick veneer → delete | $2,573–5,467 | **$3,300–7,100** (bid total) | RE-PRICED 2026-08-23 — the row predates the Ishtar-Gate re-authoring (2026-08-20), which took one flat field to five priced bands over 129.2 SF |
| Stair treads: red oak → carpet, all 3 flights | $2,668–5,544 → $1,200–2,800 | ~$1,400–2,700 | cheapest finish change per dollar; basement flight is already carpet |
| System 3: Gree Sapphire → Vireo/Livo single-zone | $2,600–3,450 → $1,600–2,200 | ~$1,000–1,250 | **not free money** — Sapphire's true VFD soft-start is what lets it run off the battery; a hard-starting compressor can't. Losing it means giving up backup heat on that zone or resizing the inverter |

### Standing-seam metal roof → architectural asphalt shingle
Largest single lever with labour in the file. Only the house roof (1,430 SF) is
mechanically seamed; walls are snap-lock, garage is nail-strip — those are already
$2–6/SF cheaper installed. Asphalt is cheaper again ($5–9/SF installed vs $12–22/SF metal).

| | metal, as priced | asphalt |
|---|---|---|
| house roof, mech seam, 1,430 SF | $10.50–18.50/SF | |
| house walls, snap lock, 3,511 SF | $8.75–16.00/SF | not shinglable |
| garage roof, nail strip, 750 SF | $7.00–13.00/SF | |
| garage walls, 26ga nail strip, 631 SF | $6.00–11.00/SF | not shinglable |
| **6,322 SF** | **$54,777–99,331** | **$31,600–56,900** |

Only the 2,180 SF of *roof* could ever shingle — the other 4,143 SF of wall needs a
different cladding entirely. Three things move with it, not in the table:
- Snow-retention/wind hardware (S-5! clamp family) goes away, ~$1,500–3,000 — it's
  seam-specific. Asphalt needs cheaper pad-style guards instead if any.
- `edge_trim:ridge_cap` goes from formed metal ($4–8/LF) to shingle ridge ($1.50–3.50/LF).
- PV mounting changes: `S-5-PVKIT` clamps to the seam with zero penetrations; asphalt
  needs flashed penetrating feet — 48 more roof holes. Strongest argument for keeping metal.

**Cost of the cut:** 50+ year service life (vs 25–30) on a roof that's also the solar
substrate — reroof and array service life stop being independent decisions. Architecturally
this is a metal-clad house with matching wall/roof material and formed-metal edges; shingling
the roof alone breaks that, and the elevations would want revisiting.

## Basement ceiling — TAKEN 2026-08-21

**The house doesn't choose concrete vs. wood — it has both, at equal depth, boundary
movable later.** Supersedes the all-joists vs. all-concrete debate below.

- 819 SF → `FS-M-WEST`/`FS-M-EAST`, 11-7/8" I-joists @16"oc, same 18' span as FS-SECOND.
- 414 SF over the dining radiant zone stayed concrete, but as `SL-M-DECK`: an 8" BuildDeck/
  LiteDeck EPS stay-in-place form + 4-5/8" cast cap (12-5/8" total, matching the joist depth
  beside it) — **$10–20/SF** (`unit="SF"`, bills the true 7.35cy pour not the 16.13cy gross
  prism) plus forms at $9–14.50/SF. **$7,900–14,300** for the 414 SF, vs. $10,600–20,300 at
  the old shored-pour rate. **Both halves of that line were revised 2026-08-23 — see the
  bearing-seat entry below; the decision does not change, only the number.**
- Saving came from skipping **formwork**, and from a shoring package a residential crew owns
  rather than the $25,000–40,000 commercial mobilisation floor a plywood-and-scaffold shored
  deck requires. This line read "skipping shoring/formwork" until 2026-08-23 and the shoring
  half of it was simply wrong: the LiteDeck WRS manual requires continuous temporary shoring
  at 6' o.c. for any span over 5', held to 75% strength / 21 days, and this deck spans 18'-0".
  Four interior 12" concrete cross walls became stud partitions, taking 4 footings and 4
  drain-tile runs with them.
- **Cost:** house rose 4" (12-5/8" deck vs 9" slab, basement kept its headroom) — grew the
  foundation protection panel ~50 SF and added 4" to the zoning-height question in TODO.md.
  R-25 of EPS between two conditioned storeys buys nothing thermally; it's there as formwork.
- **Next cut available:** 10" form + 3" cap, same depth class, ~21% less concrete, R-31 —
  one line in `houses/catlin/params/main_deck.py`. **Spent, in the other direction, on
  2026-08-23:** the section is 10" + 4-3/8" now, deeper rather than leaner, because the depth
  is set by the bearing seat and not by matching the wood bay's depth. See below.

## Mixed deck: one flat bearing seat — TAKEN 2026-08-23

**Two structures that meet share the plane they BEAR on, not the plane people walk on**
(decision #61). The 2026-08-21 deck was tuned to the wood bay's *depth*, which matched both
finished floors and left its soffit 1-9/16" above the plane the wood bay's mudsill sits on —
so the joists and their rim resolved inside the top foot of walls that ran to the storey
datum, with nothing between wood and concrete.

- The deck goes 12-5/8" → **14-3/8"** (10" LiteDeck beam = 8" base + 2" top hat, under a
  4-3/8" cast cover) so its soffit lands on the same seat as the mudsill: **-13-7/16"**, flat
  all the way round, no stepping in the forms.
- **The basement floor rises 2-9/16"; the house does not move.** This is #60 read backwards —
  grade is pinned to soil, the soil did not change, and the basement simply gets shallower.
  Slab and storey to -9'-1-7/16", footings and the sunken garden's floor with them (the
  walkout stays flush by construction).
- **The pour comes out at exactly 8'-0"**, which is IRC Table R404.1.2(8)'s 8'-unsupported
  row rather than the 10' row a 9'-4" wall rounds up to: `#6 @ 48" o.c.` → **`#5 @ 41" o.c.`**
  on the nine 8" segments. A lighter bar at a tighter spacing, and ~14% less concrete in every
  basement wall — total wall yardage across the house goes from >100 cy to ~93 cy.
- **Costs, honestly:** the cover re-derives off the manual's consumption table at
  **0.01869 cy/SF** (the authored 0.01774 was ~4% light even at the old section), so 7.35 →
  **7.74 cy**; the form re-quotes for the 10" beam (25% more EPS, one more piece per bay); and
  a **shoring line goes in at $2.00–5.00/SF** — ~12–15 rentable adjustable posts at 6' o.c.
  under 414 SF, set and struck by the placing crew. Net on the deck rows: $8.85–18.20/SF →
  **$11.02–23.39/SF** concrete-plus-shoring, and $9.00–14.50/SF → $10.75–16.75/SF on forms.
  Against the $25–40k mobilisation floor this decision was made to avoid, it does not flip.
- **What it bought besides truth:** the basement's clear height is 8'-0-15/16" under the
  joists (7'-10-7/8" under the band), both over R305.1's 7'-0"; the mudsill is one board
  serving the studs and the joists, billed once over the union of the two runs — 370.0 LF,
  where the old framed-only rule left ~10 LF of bearing wall with no plate at all.
- **What it cost:** the basement ceiling's step at the wood/concrete line goes 1/2" →
  **2-1/16"** (1/2" is the form's steel rib, the rest is the deck being deeper than the wood
  bay). The finished floors go 3/16" apart, which the 6 mm plank absorbs — it finishes
  1/64"–1/20" proud of the polish, and the reducer that used to be specified becomes a
  T-moulding.
- **Guarded, which is the actual point.** `structural.mixed_deck_bearing_seat` (FAIL) holds
  the seat, the plate thickness and the finished planes; `integrity.floor_bearing_grid` holds
  every joist cut over its own wall's structure. The 2026-08-21 arithmetic was already right
  and had nothing watching it, which is how it went wrong three days later.

## Basement perimeter pour, 12" → 8" — TAKEN 2026-08-21

**The follow-on the ceiling decision left on the table.** 12" was chosen to seat a cast
deck; once only `SL-M-DECK` was still cast, the eight perimeter segments it does *not* land
on were carrying 4" of concrete that bought nothing.

- The rule is physical and narrow: 12" is earned only where a cast concrete deck lands on
  the wall top **beside** the sill plate and needs its own bearing seat inboard of it. A
  wood floor needs no extra width — the I-joists and rim bear on the same 2x6 mudsill the
  framed wall above stands on. `SL-M-DECK` (x 18'–36', y 13'–36', one-way E–W) bears on the
  east wall and the centre line, and nowhere else.
- So `W-B-E1/E2` stay 12" (`CATLIN_BASEMENT_12`) and the other eight — 108 LF of west,
  north and south perimeter — went to 8": `CATLIN_BASEMENT_8`, `CATLIN_BASEMENT_8_GARDEN`,
  `SAUNA_LINER_ON_BASEMENT_8_GARDEN`. The five interior walls that still meet a pour
  (`W-B-CS/CS2/CN/CN2/STR`) also stay 12".
- **Not free:** IRC Table R404.1.2(8) at 45 psf/ft GM soil, 10' unsupported, 7' unbalanced
  fill reads NR at 12" and 10" but **#6 @ 48" o.c. vertical at 8"** — ~27 bars, authored on
  each wall and gated by `structural.foundation_unbalanced_fill`. (The 2026-08-23 bearing-seat
  entry above takes the wall to 8'-0" and the cell to `#5 @ 41" o.c.`; the 12"-vs-8" decision
  itself is unaffected.)
- **8" and not 10"** (which also reads NR): 8" is the standard residential form module and
  the market rate is quoted for it. Thickness above 8" adds concrete without adding forming,
  so 10" would pay an odd-thickness forming premium and hand back half the yardage to save
  the bar.
- **The saving, measured:** −12.0 cy (48.5 → 36.5 cy across the perimeter rows),
  **−$3,239 to −$5,759** on `[wall_structure]`. Re-derived rates, not the 12" row: the 12"
  $420–700/cy is $110–180/LF of forming, crew and pour at that height, and forming does not
  get cheaper because the wall got thinner. 8" × 9'-4" is 0.2305 cy/LF, so the same
  $114–187/LF is **~$495–810/cy** — and at the 8'-0" wall of 2026-08-23, $98–160/LF over
  0.1975 cy/LF is the same **$495–810/cy**, which is the point of quoting per cubic yard.
  Pricing the 8" wall at the 12" rate would have claimed
  −$8,700, which is the whole trap here.
- **What else moved:** the walls align on `face("concrete-ext")`, so only the inside face
  came in. Furnace room 8'-6" → 8'-10" clear, workshop 7'-6" → 7'-10", playroom unchanged at
  16'-6" (bounded by the two walls that stayed 12"). ~36 SF more usable basement floor. Two
  spurious conduit sleeves stopped crossing anything and were deleted; seven face-mounted
  devices on the west/north/south concrete moved 4" with the face. Gross floor area and the
  brick veneer stand-off are both unmoved, by construction — the exterior face did not move,
  and the 4.55" outboard tail is not part of the pour.
- **Rode along:** the 8"/12" cast foundation family was promoted to `library/`
  (`FOUNDATION_WALL_{8,12}_{INT,XPS4}` + the `_CORE` layer tuples), so the catlin walls now
  compose off a shared, reviewed core plus a house-local skin.

<details><summary>Historical comparison this decision was made against (concrete vs. all-joists, researched 08-18/08-20)</summary>

| | concrete deck | I-joist floor |
|---|---|---|
| structure, installed | $31,862–60,298 (~$26–49/SF) | $13,045–25,819 ($10.58–20.94/SF) |
| main-floor finish, 996 SF | sealer $996–2,989 | LVP $3,487–9,963 |
| **total** | **$32,858–63,287** | **$16,532–35,782** |

Concrete's old $175–280/cy rate was the slab-on-grade rate; a suspended 9'-air-pour deck
needs formwork, ~10' shoring (ACI 347 minimum-rental month), 2.0–2.7 tons rebar, boom pump,
trowel finish, commercial-sub mobilisation, engineer's stamp — corrected to $30.56–58.33/SF.
TJI spec note: a 110 fails outright at this 18' span; 210 is the code minimum; spec the 230
(~$650 more) for margin under finished rooms. Fire protection and bridging are both **$0** —
already covered by the 5/8" ceiling and not triggered at this span.

**Cost of the cut** (still real if this were ever revisited): a 9" slab gives acoustic
isolation a wood floor doesn't reach; 34cy of thermal mass under the south glazing the
facade is composed around; `FH-M-DINING`/`FH-M-BATH2` radiant would need re-authoring from
`in_slab` embed to mat-under-LVP; `assemblies.py`'s `_SAUNA_CEILING_EXTENT` explicitly
anticipates a joist ceiling raising the sauna liner to full wall height.
</details>

## W-B-STR, the 12" stair wall — PRICED 2026-08-22, TAKEN 2026-08-24 (the third option)

> **Both options priced below were declined, and the wall was framed anyway on 2026-08-24
> — by a route neither of them describes.** The blocker in both is `FO-M-STAIR`'s west edge
> at x=10'-6", and both answers below treat that edge as fixed: one leaves it and eats an
> engineered header, the other proposes moving it to 10'-4" and calls the stair
> re-dimension a cost. The route taken moves it to **10'-3 3/8"** — the plywood face of a
> 2x6 stud line aligned plumb under `W-M-STRW`'s studs with
> `face("stud-ext", offset=inch(-2.625))`, which is where `FO-S-STAIR`'s west edge already
> was one storey up. So the well's west face becomes one continuous plane top to bottom
> rather than a new dimension, the 2 5/8" is absorbed into the two flights (3'-3 3/4" ->
> 3'-5 1/16", both further over the 36" minimum than before), `RM-B-FURNACE` gains 3 1/8",
> and `_opening_edge_has_declared_bearing` is satisfied on the layer footprint with no
> header. `FT-B-STR`/`FT-B-STR3` stay — a framed bearing wall wants the same footing — so
> the "retires the one interior footing the 2026-08-21 pass kept" objection below does not
> apply either. Two segments, `W-B-STR` + `W-B-STR3`, ~9.8 cy out. The prices below stand;
> read the objections as the constraints the route had to satisfy, not as reasons it did
> not happen.


The last 12" pour anybody asked about: `W-B-STR`, the basement stair shaft's west wall,
14'-2 5/8" x 9'-4" = 132.7 SF, **4.92 cy** of `FOUNDATION_WALL_12_INT` on the x=10'-0" axis.
Two ways to make it cheaper were asked for — thin it, or frame it — and both are priced
below. Neither is recommended, and the reason in both cases is the same floor opening.

| swap | current → new | saves | notes |
|---|---|---|---|
| `W-B-STR` 12" → 8" pour | 4.92 cy → 3.28 cy | **$330–560** | NOT $771–1,279. See below — the forms do not go away. Pulls a 9'-0" engineered floor header |
| `W-B-STR` → `CATLIN_INT_2X6_BRG` stud wall | $2,312–3,838 concrete → $1,093–1,923 framing | **$389–2,745** | retires a two-storey bearing line and the one interior footing the 2026-08-21 pass deliberately kept |

**Why the 8" saving is a third of what a $/cy multiply says.** `[wall_structure]`
`FOUNDATION_WALL_12_INT` is $470–780/cy, and 1.64 cy x that is $771–1,279. That number is
wrong in kind: it is a **merged placed rate for a formed wall**, and a formed wall is bought
by the foot of form. Thinning it changes neither form area (2 x 132.7 SF), nor the strip,
nor the rebar, nor the labour — only the mud. 1.64 cy of ready-mix at this file's own
$200–320/cy delivered-plus-placement basis is **$330–560**, and that is the honest figure.
The same trap is why `[concrete]`'s 2026-08-20 pass raised every small-pour rate: *a formed
pour is bought by the FOOT OF FORM, not the yard of mud.*

**Why 8" pulls an engineered header, exactly.**
`resolve/floors.py::_opening_edge_has_declared_bearing` tests a floor opening's edge against
the bearing wall's plan **footprint**, not its axis. `FO-M-STAIR`'s west edge is at
x=**10'-6"**. At 12" the wall's footprint is 9'-6"–10'-6" and the edge sits on its boundary,
carried. At 8" the footprint is 9'-8"–10'-4" and the edge is **2" outside it**: the resolver
emits a header over the whole 8'-11 5/8" edge, and `structural.floor_opening_header` FAILs it
as past R602.7's 8'-0" prescriptive table — the emitted `engineered-LVL` is a placeholder for
a designed beam.
- **The fix exists and is not free:** move `FO-M-STAIR`'s west edge to 10'-4". That widens
  the well to 7'-2" (it is at the 7'-0" code minimum now, so wider is legal), and `ST-B2M`'s
  flight width is measured off that face, so the stair re-dimensions. No materials, several
  drawings.
- A 6.75" `CATLIN_INT_2X6_BRG` wall has faces at 9'-8 5/8"/10'-3 3/8" — the same problem, 1/8"
  worse. *(This is the line the 2026-08-24 change turned around: it is only a problem while
  the opening edge is treated as fixed. Move the edge to the stud line's own face — which is
  where the storey above already drew it — and the footprint reaches it exactly.)*

**What framing it really costs.** 4.92 cy at $470–780/cy is $2,312–3,838 out of
`[wall_structure]`; the replacement is ~155 LF of 2x6 at `[framing]`'s $1.75–2.75/LF, 265 SF
of gypsum both faces at `[envelope_layers]`' $1.55–2.65/SF, and 265 SF of paint at
$1.55–3.00/SF = **$1,093–1,923**. So $389–2,745 back, and the low end is nearly nothing.
**The cost of the cut is structural, not financial:**
- It is a **two-storey bearing line**. `W-M-STRW` and `W-M-STRW2` name it in `stacks_on`
  (`plan/storeys/main.py:362,372`) and carry to the footings.
- `FT-B-STR` is the one interior footing the 2026-08-21 framing pass deliberately did *not*
  retire (`params/foundations.py:76-80`), and it is there because this wall bears.
- The stair well is at the 7'-0" code minimum and `ST-B2M`'s flight width is measured off
  this wall's east face, so any thickness change is a stair change.
- No *check* requires concrete here: `unbalanced_fill=ft(0)` makes
  `structural.foundation_unbalanced_fill` skip it entirely (it retains nothing — it is an
  interior wall). The constraints are dimensional and structural, and they are the ones the
  "do not touch" note at `plan/storeys/basement.py:284-297` already lists.

**What moves with it, either way.** Two cast conduit sleeves — `SP-B-STR-CD-GAR` and
`SP-B-STR-CD-KITCH` — become bored stud-bay crossings if it is framed, which is *cheaper*;
`SP-B-CN-CD-KITCH` through `W-B-CN` is unaffected, and `SP-B-STR-BATH-VENT` already crosses
`W-B-STR2`'s steel studs. Three blessed section goldens are keyed to this junction —
`detail_wall_foundation-`, `detail_stack_width_change-` and
`detail_storey_stack-rim-CATLIN_INT_2X6_BRG-FOUNDATION_WALL_12_INT`. The assembly survives on
`W-B-CN/CN2/CS2` so those scenes stay, but a stud-on-stud junction appears that wants
blessing.

**Recommendation as written 2026-08-22: neither.** $330–560 for a stair-well re-dimension
plus an engineered header is a bad trade at any confidence; $389–2,745 for retiring a
two-storey bearing line and its footing is a worse one.

**Superseded 2026-08-24 by the note at the head of this entry.** The framing option was
taken across both segments, and the two objections that carried the recommendation both
turned out to be answerable rather than true: the bearing line is not retired (a framed
bearing wall on the same footing is still a bearing line, and `FT-B-STR`/`FT-B-STR3` did
not move), and the stair re-dimension is not a cost — the well's west face lands on the
plane `FO-S-STAIR` already used, and the flights got wider.

## The framing sweep — BUILT 2026-08-28

Four unpriced framing ideas sat at the foot of this file (and in `plans/TODO.md`'s "potential
cost cutting" bucket) with no numbers against them. All four have numbers now. Three were
built, one was declined, and one item was re-scoped from a saving into a spec finding for the
engineer. Baseline for every delta below is the 2026-08-28 pre-sweep run:
**$943,562 – $1,952,673** bid total (`subtotal_net` $820,324 – $1,706,816).

Combined result: **−$1,342 / −$3,302** on the bid total, `haus check` at **0 FAIL**
throughout, the full suite green, two engine defects fixed, one check stopped reading a
house-wide preference where it should read the wall, and one new engine capability
(`Wall.base_elevation`) that item C could not be built without.

### A. The real backfill on the south walls — BUILT, worth $0, and that was the point

None of `W-B-S1/S2/S3` authored `unbalanced_fill`, so
`checks/structural/foundation.py::_unbalanced_fill_ft` fell back to its documented proxy —
grade (−2'-10") minus the wall bottom (−9'-1 7/16") = **6.29 ft on all three** — and rounded
up to IRC Table R404.1.2(8)'s 7' row, which is what bought them `#5 @ 41" o.c.` The proxy's
own docstring warns about exactly this case: *"it over-reports a walkout wall whose exterior
grade falls away."*

The sunken garden is excavated from x=8'-10" to x=28'-0" (`params/sunken_garden._x_ax_e`) with
its floor flush with the basement slab, so:

| wall | x range | retains |
|---|---|---|
| `W-B-S1` | 0'-0" → 8'-10" | 6'-4" — buried |
| `W-B-S2` | 8'-10" → 18'-0" | **0** — inside the court |
| `W-B-S3` | 18'-0" → 28'-0" | **0** — inside the court |
| `W-B-S4` | 28'-0" → 36'-0" | 6'-4" — buried |

`W-B-S4` is new: the old `W-B-S3` was one wall carrying two conditions, split at the
excavation edge on a new node `N-B-S3`. It joined `params/foundations._HOUSE_WALL_TAGS` (index
22) and `_FROST_FORMED`, so `FT-B-S4` keeps its `FOOTING_FPSF_20` insulated form and
`structural.frost_depth` still PASSes on it at 8" of cover below `SL-SG-FLOOR`. The two
zero-fill segments dropped out of `structural.foundation_unbalanced_fill` entirely (the check
skips at `fill <= 0`) and dropped their vertical steel with the load — on the merits, not
because the check went quiet. **No dollars: `[wall_structure]`'s note says vertical steel has
no line of its own, it is inside the $/cy rate.** The one measurable move is ~$20–46 of extra
drain tile, because the split adds one more footing-bedding record over the same run.

Worth building anyway: it makes the model true, and C could not be authored without the split.

### B. `W-B-CS`, the sauna's east wall, 12" concrete → 2x6 bearing studs — BUILT, **−$886 / −$1,467**

The last of the four 12" segments `basement.py`'s WALLS header defends, and the one it already
admitted *"carries wood on both faces and COULD go to 8"."* It could go to nothing: what it
carries is `FS-M-WEST` and `FS-M-EAST` (two 18' I-joist spans) and the
`W-M-C1 → W-S-C1/C2 → W-A-C1 → RB-HOUSE` stack to the footing, which is a 2x6 bearing wall's
job on every storey above. Same trade `W-B-STR`/`W-B-STR3` made on 2026-08-24.

- **Out:** 4.1 cy of `SAUNA_LINER_ON_CONCRETE`, `$1,722 – $2,870`. The `[wall_structure]` row
  is retired with the assembly; no replacement row is needed, because
  `takeoff/wall_structure.py` skips framed structure layers and the wall bills through
  `[framing] "2x6"` plus its faces.
- **Back:** +146 LF of 2x6 (`$256 – $402`), plus gypsum, mineral wool, and a longer liner —
  `[envelope_layers]` moves `$662 – $1,150`. Hardware picks up 4 LTP4, 1 MASA and 1 STHD.
- New assembly `SAUNA_LINER_INT_2X6_BRG`. **The "INT" token is load-bearing** —
  `mn_energy._is_interior_assembly` is literally `"INT" in tag.split("_")`, and the retired
  concrete assembly never carried one because a 12" interior pour was never reaching the R-21
  table.
- **The trap, caught in the same commit:** `alignment=face("concrete-ext", offset=inch(-6))`
  is a hand-written HALF of the 12" thickness. On 5 1/2" studs it is
  `face("stud-ext", offset=inch(-2.75))`. Leaving the −6 would have slid the x=18' bearing
  line 3 1/4" west without touching a node. `integrity.floor_bearing_grid` stays PASS on all
  seven floor systems and `structural.mixed_deck_bearing_seat` did not move.
- `SP-B-CS-COND`/`-COND2` retired: a framed wall takes a bored hole on the day, not a sleeve
  set before a pour — the same reading that retired eighteen sleeves on 2026-08-21.
- `prices.toml`'s `pt-sill-plate` note shrank: `W-B-CS`'s 0.83 LF was one of the stretches
  named as under-billed, and a framed wall now stands on that run.

**The cost of the cut, for the record:** 12" of concrete between a sauna and `RM-B-PLAY-N` is
real acoustic and thermal mass, and the sauna's vapour control moves from liner-on-pour to a
framed stack.

**One thing it bought, on the record rather than hidden:** `integrity.junction_fallback` now
reports `N-B-C1` UNKNOWN. `W-B-CS` is spf and `W-B-CS2`, collinear with it on the x=18' line,
is still 12" concrete under the cast band — so the junction's *through* pair is two different
bearing materials and the solver has no interface rule for it. It is a real detail (a stud
wall landing in line against the end of a pour wants a bearing plate and dowels drawn), not a
modelling artefact. The house answered the same finding at `N-B-CW-E` by running one wall type
down the whole line; that answer is not available here, because `W-B-CS2` carries `SL-M-DECK`.

### C. The framed walkout at the sunken garden — BUILT, **−$456 / −$1,835**, a third of the prediction

`W-B-S2` and `W-B-S3` — 19'-2" of the south wall standing inside the court — are a 2x6 framed
wall (`W-B-S2-FR`, `W-B-S3-FR`) on a 7 1/4" concrete curb since 2026-08-28.

**The prediction was −$1,400 / −$2,700 and the model says a third of that at the low end.**
The prediction counted 3.69 cy of pour out against "~180 LF of 2x6" back. What it did not
count is everything else a framed wall needs and a concrete wall does not: sheathing, gypsum,
mineral wool, an air barrier, and the curb that stays. Measured, against the post-B run:

| | low | high |
|---|---|---|
| `[wall_structure]` concrete out (~2.9 cy net of the door and window openings) | −$1,436 | −$2,349 |
| the two 7 1/4" curbs back in | +$210 | +$420 |
| `[framing]` — +196 LF of 2x6, +24 LF of 1x4, one 2-2x10 header | +$394 | +$621 |
| `[envelope_layers]` — sheathing, gypsum, mineral wool, liner, less XPS and parge | +$475 | +$844 |
| hardware (4 LTP4, 1 MASA, 1 STHD) | +$11 | +$22 |
| allowances (damp-proofing area, vapour retarder) | −$70 | −$1,240 |
| **`subtotal_net`** | **−$415** | **−$1,682** |
| **bid total** | **−$456** | **−$1,835** |

**The strongest argument is still invisible to the estimate, and it is now measured.**
`takeoff/wall_structure.py` bills wall volume *net of openings* and adds nothing back for the
buck or the extra forming — the 5'-0" french door and the sauna window are a **0.84 cy
credit** in the numbers above, when forming two holes in a wall is exactly the cost this swap
removes. So the true saving is the table plus whatever two formed openings cost, and the model
cannot say what that is.

Built the way the owner's constraint asks:

- **The curb is kept and it is 7 1/4"** — the actual width of a 2x8 — so heavy rain standing
  in the court reaches concrete and not a bottom plate. `W-B-S2`/`W-B-S3` keep their tags,
  uids and footings and *become* the curbs, which is what keeps `FT-B-S2`/`FT-B-S3`,
  `_FROST_FORMED`, `structural.frost_depth`, `CN-M-HD-BALC-W/E`'s STHD embedments and
  `W-B-BRICK`'s dimensions all naming a piece of concrete on a footing that did not move.
- **The curb is 6" and not 8", and the reason is a plane, not a load.** 6" of concrete is
  exactly stud-plus-sheathing, so the curb's outboard face lands where the sheathing's does
  and its inboard face where the studs' does. An 8" curb would have left a 2" shelf on the wet
  side of a sauna wall. Verified in the resolved model: every south segment — `W-B-S1`, both
  curbs, both framed walls, `W-B-S4` — still presents its parge face at **y = −4.55"**, and
  `W-B-BRICK`'s 1" air gap still starts there. The veneer did not move. *(The tie hardware
  does change in reality — corrugated ties into framing rather than anchors into concrete.
  Veneer over wood framing is ordinary; it is said here because the model cannot say it.)*
- **`Wall.base_elevation` is new** (see the engine notes under E): a framed wall standing on
  something inside its own storey. `W-B-S2-FR`/`W-B-S3-FR` base on −102 3/16" and the studs
  resolve at **7'-0 1/4"** rather than the 8'-0" they would be off the slab — confirmed in the
  built members, bottom plate at −102.19" and top plates closing at −13.44".
- **The framed run is its own wall-graph component.** Two wall edges between one pair of nodes
  is a junction with no answer, and the solver said so — eight `integrity.junction_polygon`
  ERRORs, one per layer. It has its own nodes at the same three stations with `open_end` at
  both ends, the same device `W-B-BRICK` uses, which is also why both framed walls author
  `interior_room` rather than trust the winding.
- **`D-B-PATIO`'s `sill_height` went `inch(7)` → `inch(0)`, and the threshold did not move.**
  A sill is measured from its host wall's base, and that base is the curb top now. The door
  sits *on* the curb instead of 7" up a pour with a quarter inch of concrete still above it.
- **`WIN-B-SAUNA` moved 9" east, 2'-6" → 3'-3" off the corner** — the framed wall asking, not
  the design changing. A hole in a pour lands where you form it; a 14" RO in a stud wall wants
  a **bay centre**, where the bay's own two studs carry the rough sill and head nailer and it
  needs no header, no jacks and no kings (`preferences.toml`'s `max_window_ro_unbroken_in`).
  `structural.window_framing_module` said so at 7" off the moment the wall stopped being
  concrete. `AO-B-BRICK-WIN` followed it; both sills still land at −65 7/16".
- The sauna's curb carries the liner down over its face rather than stopping at the curb top:
  `building_science.humid_room_liner` FAILed the bare 7 1/4" strip immediately, and it was
  right to — a hole in the hot side's vapour control is a hole.

### E. The engine work the 24" module needs — DONE; the attic gables are NOT built

Per owner decision the gables stay at **16" o.c.** for now, so this item moves no money yet.
What is done is the part that had to come first: **before 2026-08-28 no wall in this house
could have been a spacing other than 16", and neither defect would have announced itself.**

1. **`resolve/framing/openings.py::_cripple_stations` hardcoded `DEFAULT_SPACING`.** Sill and
   head cripples were framed on a 16" grid in every wall in the house regardless of what the
   wall was actually built on. A bug, not a limitation; it reads the host wall's own spacing
   now. `frame_opening` grew a `cripple_spacing` argument to keep it honest on a STAGGERED
   wall, where the jamb-pack module is half the nominal one but the opening is framed full
   plate depth — so its cripples are full-depth members on the nominal module, which is
   exactly what they were before and must stay.
2. **`structural.window_framing_module` read `preferences.toml` house-wide.** The solver has
   always laid a wall out on its own `FramingSpec.spacing`; the check read the preference.
   They agreed only because every spacing in this house is 16 — a latent split brain that
   would have graded a 24" wall against a grid nobody built. The check reads the wall's
   spacing now with the preference as fallback, and `_ro_caps` re-derives the whole RO ladder
   at that module: the ladder's three rungs are arithmetic on the module and a stud (one
   clear bay; two bays less the broken stud; that again less a jack each side), so at 24"
   the unbroken bay is 22 1/2" and the nonbearing cap 46 1/2". The authored numbers are the
   geometric ones rounded down for a window schedule, and that rounding is carried across
   rather than re-invented — at the declared module the function returns the authored values
   unchanged, which is what keeps a 16" house's results identical. The rule moved to its own
   module, `checks/structural/window_module.py`, which put `checks.py` back under the
   500-line bound. `test_catlin_window_openings_follow_the_sixteen_inch_framing_module` is
   `..._follow_their_walls_framing_module` now — renamed, not loosened; the assertion is
   still an empty exception list.
3. **`Wall.base_elevation` is new, and item C could not be built without it.** A framed wall
   standing on something *inside* its own storey — a stud wall on a concrete curb — had no
   way to say so: `FoundationWall` has carried absolute `bottom_elevation`/`top_elevation`
   since day one, and a plain `Wall` started at the storey datum, full stop. Everything
   downstream follows for free, because `ResolvedWall.z0_m` is what the framing solver
   measures plates and studs from and what every opening sill is datumed on — which is why
   `W-B-S3-FR`'s studs resolve at 7'-0 1/4" and `D-B-PATIO`'s threshold landed on the curb
   top with `sill_height=inch(0)`. `_wall_z_range` reads it too, so the curb and the wall on
   it split into two bearing tiers at a shared node rather than fighting over one junction.

**What the gables would buy when they are taken: −$490 / −$860**, and the money is not the
reason. IRC Table R602.3(5) permits a *nonbearing* 2x6 at 24" o.c. to a 20' height with no
load argument at all, so the six gable walls need no plan reviewer's judgement — while the
knee walls and every bearing wall below stay at 16". The interesting part is the RO ladder:
at 24" the unbroken bay goes 14 1/2" → 22 1/2", which turns the two `WT-1448` south flankers
— 14" wide *only because that is what fits a 16" bay* — into ~22" stock casements with no
header, no jacks and no kings, clearing Andersen 400's 20-11/16" narrowest casement.
`WT-1448`'s own note says the 4:12 rake forbids the usual remedy because any width over 14"
takes a header that hits the rake; at 24" o.c. that constraint dissolves. 48" is the saving
grace on the re-grid — `CATLIN_EXT_2X6` sets `layout_origin="line"`, so the 24" and 16" grids
strike from one origin and coincide every 48", 36'-0" is 9 × 48", and the juliet pair's stud
lines at 16'-0" and 20'-0" are stations on both. Two nodes to check when it is taken:
`N-A-V1` at 22'-8" (a 16" station but not a 24" one) and `N-A-S1` at 8'-8" (on neither).

### D. Declined without building — the two that were already taken

- **Built-up beams and columns.** There is no PSL and no glulam in this house: every multi-ply
  beam is *already* built-up sawn (seven 3-2x12 KDAT, four 2-2x8), and
  `params/sunken_garden.py` records the 2026-08-23 LVL → 3-2x12 swap that did it, worth about
  $850–2,100 *and* an improved check (3-2x12 is in IRC Table R507.5(1) where an LVL returns
  UNKNOWN). Replacing the ten 6x6 posts with 3-2x6 built-ups saves $150–300 of material and
  gives it straight back: NDS 15.3.3 wants two rows of 30d nails at 8" o.c. (0.207", not
  gun-drivable), the `ABU66SS` bases do not fit a 4 1/2" x 5 1/2" section, and six of the ten
  are white-painted architectural pillars where laminations would show.
- **LSL for LVL is worth ~$0.** The rim boards are *already* LSL — `resolve/floors.py`
  hardcodes the 1.25" TimberStrand dimension and `prices.toml` priced them off I-joist-and-LSL
  builder-guide surveys. The whole house contains **12 LF** of LVL beam (0.19 cy, $252–468 of
  material), and `BM-S-HALL`/`BM-M-HALL` are genuinely governed — shear governs `BM-M-HALL` —
  where LSL's lower Fv is worse. `resolve/framing/profiles.py` also has no LSL grammar:
  `"3-1.75x11.875 LSL"` falls through every regex to the silent 1.5x5.5 stud fallback.
- **Floor joists at 24" o.c. — the only $3,000+ item on the list, and declined.** A third of
  4,580 LF of I-joist is $6,700–11,300, but every deck spans 18'-0", so it needs a heavier
  series or 14" depth — and depth moves `BEARING_SEAT` and the whole 2026-08-23 flat-seat
  chain, guarded by `structural.mixed_deck_bearing_seat` at FAIL tier. Add a 24"-rated
  subfloor over ~2,000 SF and `structural.ijoist_span` going UNKNOWN at any spacing but 16"
  (`checks/structural/checks.py`), and the saving is gone along with the guard.

### `RB-HOUSE` — a spec finding for the engineer, not a saving

Recorded here rather than built. `RB-HOUSE` is three plies of LVL bearing **continuously** on
`W-A-C1/C1B/C2` for its full 36' (`plan/storeys/attic.py`), so it answers no span, and no
check grades it — `_resolve_ridge_beam` emits `structural.ridge_support` only when a ridge
`Beam` is *absent*. Re-specifying it honestly runs **deeper, not lighter**: an 11 7/8" I-joist
rafter at 4:12 has a 12.52" plumb cut, so the current ridge is fractionally too shallow.
`2-1.75x14` LVL is ~$460–800 back. **For the engineer to settle, not this file.**

> **SETTLED 2026-08-28, then re-settled 2026-08-29 — the section above is history twice
> over.** `RB-HOUSE` went `3-1.75x11.875` → `2-1.75x14` → **`2-1.75x16`**: three plies
> answered no load, then the roof pitch moved 4:12 → 6:12 and the plumb cut that sets the
> depth moved with it (14.15" now, not 13.10"), so 14" — which cleared the old target by
> 0.90" — missed the new one by 0.15". The full derivation is in `CLAUDE.md`'s "Structural
> ridge" bullet; `notes/ridge_beam_detail.md` carries the hanger/strap/fastener detail but is
> flagged superseded at the top for the pitch change. **Deeper is cheaper than wider**, in
> fasteners as well as in LVL — the third ply would have wanted 5" screws from both faces.
> At the current 16" section a 12' ply is 106 lb (was 92 lb at 14"); the one-piece 36'
> alternative would be 317 lb (was 277 lb) — still no crane at any depth this beam has held.

## The crane-free / heavy-lift audit — 2026-08-29

Asked for: whether this house needs a crane, and whether anything excessively heavy or bulky
has an easy swap that takes real money out. Priced from the resolved model, the BOM and
market research; **nothing in this section is built** except the four price-file corrections
recorded under *Refactors* below, which are estimate fixes and not design changes.

**The crane question is settled, and it was never really open.** **CHECKED AGAINST EVERY
multi-ply LVL/PSL header and beam in the house, 2026-08-30, not only the ridge:** no framed
member exceeds **258 lb** assembled (the garage overhead-door header — table below). The
two heaviest OBJECTS in the project — the 1,656 lb sunken-garden column `PT-SG-FCOL` and the
932 lb pier — are cast in disposable fibre tubes and never lifted at all. The two elements
that *would* have forced a pick were engineered out on purpose long before this audit, with
the reasoning written down: `RB-HOUSE` buys its 36' as three 12-footers
(`notes/ridge_beam_detail.md` §4), and the column is a tube, not a precast.

One item in the house *does* exceed 258 lb and is heavier than any single framing piece: the
**LG WashTower** (`FX-M-LAUNDRY`, main floor) is a factory-integrated single unit — LG does
not sell the washer and dryer separately — at **353 lb**
(`plan/appliance_types.py`). Not a crane question (two people and an appliance dolly through
a main-floor door), and not something a design pass can change, but the earlier draft of
this audit's "no piece exceeds ~340 lb" line was wrong: the ceiling on *framing* is 258 lb;
the ceiling on anything delivered to site is the WashTower's 353.

**So crane-free is a tiebreaker, not a constraint, and it should stop driving decisions.** A
30–40 ton metro boom truck is **$1,500–2,500** for a half or full day, operator and in-metro
mobilisation included. `[allowances] site-scaffolding-and-lift-rental` already carries
**$3,000–8,000** — the crane is inside the money the file has already set aside. On a bid of
this size a crane day is 0.1–0.2% of the build. Where staying crane-free is free — splicing a
beam that bears everywhere, casting a column in a tube — take it, as this design already
does. Where preserving it would cost more than a couple of thousand dollars, it is false
economy.

> **READ THE RANGES BELOW AGAINST THE RIGHT BASELINE.** They were struck while the bid stood
> at $948k–1.97M; it is $810k–1.69M now. **Do not read that whole drop as the attic rework** —
> that attribution was wrong and is corrected here. Measured before-and-after CSVs put the
> 2026-08-29 attic rework at **−$19,400/−$36,200** (−$17,200/−$32,300 all-in, net of three
> pricing corrections made in the same pass); the rest of the $948k → $810k is the cost
> sweep, the framing sweep and the price fixes recorded elsewhere in this file. Anything
> below that scales with the attic — roof area, wall area, continuous insulation — is still
> quoted **high** and has to be re-read before it is spent. The four price corrections under
> *Refactors* are exact; these are not.

### The candidates this file did not already carry

Same convention as the sweep above: every number is a **bid-total** delta, and **none of
these is built**. The threshold is relaxed to $1,500 here because two of the rows are
thermally positive and one is free.

| change | saves | what it costs you |
|---|---|---|
| **Shorten the sunken court, 28' → 16' north–south** | **$9,700–16,600** | Garden area, and nothing else |
| **Roof: standing seam → exposed-fastener PBR** | $7,400–14,500 | The PV mounting — **see the warning below** |
| **Single-tier girt on 5.5" blocks** (deletes the inner SPF tier) | $6,400–10,300 | A new failure mode and an engineer's fee |
| **Exterior-wall cavity mineral wool → fiberglass** | $4,900–7,200 | ~0.8 whole-wall R; verify the row split first |
| **Girt courses 24" → 32" o.c.** | $4,100–6,900 | Two re-checks — and it is worth **+R-0.8** |
| **Engineer the garden footing base and stone bed** | $3,200–8,000 | Nothing, if it stamps |
| **Refrigerator columns → one 36" side-by-side** | $3,000–4,500 | All-fridge/all-freezer capacity and a 21" of layout |
| **Garage stem → frost-protected shallow foundation** | $2,000–3,900 | The option of ever leaving the garage unheated |
| **Drop the interior vapour-retarder allowance on the truss walls** | $1,500–9,600 | Arguably nothing |
| French doors → sliders where the swing isn't needed | ~15–25% of $7,000–15,800 | Double-leaf swing. **Unpriced — needs a quote** |

**These do not add up either.** The 32" girt row and the single-tier girt row are mutually
exclusive. Court-shortening and footing engineering overlap. The girt rows and the
mineral-wool row all shrink if the attic goes (sweep row 1). Taking only the independent
ones — court, 32" girts, vapour retarder, refrigerators — is roughly **$18,000–37,000**.

**Shortening the court is the highest-value item on the list, and it is not "delete the
garden."** The sunken garden is a third of the entire cast-concrete package: 29.2 cy of 10'
retaining wall, 63% of all footing concrete in the project, and 100% of the 71.8 cy stone
line. Taking 12' out of it leaves the porch, the balcony and the walkout untouched, still
gives a 19x16 = 304 sf court, and cuts roughly 60 cy of excavation on top of the concrete.
**Do not extend the logic to deleting it:** `D-B-PATIO` and `WIN-B-SAUNA` are the only
exterior openings in the entire basement, and without the court the theatre, gym, sauna and
shop are all windowless with no direct exit.

**The girt respacing is the best value-to-risk row here and the only one that pays twice.**
32" is exactly 2x the 16" stud module, so every block stays where it is and only the course
count drops 25% — about 941 LF of SPF, 928 LF of KDAT and 1,049 structural screws. Re-running
`notes/catlin_truss_engineering.md`'s own arithmetic at the larger tributary puts screw
withdrawal at 36% (was 27%) and girt bending under 14%; nothing crosses half. It is also
thermally **positive**, worth roughly +R-0.8 whole-wall, in a wall that currently misses its
target. Two things to re-check before spending it: the 26 ga PBR panel's published purlin-span
table at −26.7 psf, and every window head and sill against the new course phase (see
`notes/` on girt courses vs. window elevations — no window has to move at 24", and that has
to be re-established at 32").

**The roof swap is the largest single lever and the worst trade in the file.** The flush
zero-overhang edge survives it — `pbr-panel-26` already declares the same `skin_family` — but
`S-5-PVKIT` clamps to a *seam* with **zero penetrations**, and on PBR 48 attachments have to
pierce the water plane and the vent mat that is the assembly's only drying path, under a
$15.8–27.5k array. Add ~3,700 gaskets on the primary roof plane of a Minnesota house at 4:12
with no overhang, at 20–30 year gasket life against a seam that would not need re-roofing in
25. **Under a PV array, leave the roof alone.** (This is a different row from sweep #5, which
is roof → asphalt, and from sweep #3, which is the *wall* cladding and is already taken.)

**The single-tier girt is bigger than the 32" respacing and much more dangerous.** It deletes
the inner SPF tier and carries the outer girt on deeper blocks straight off the studs, and on
the engineering note's own method it would actually *meet* the R-40 target. But the
sequencing argument inverts — all 4" now has to be sprayed around blocks standing 5.5" proud
and shaved 1.5" below their faces, where the note already calls a 1/2" shave "inside ccSPF
surface tolerance" — and it creates a failure mode the wall does not have today: the current
block bears in compression, a 5.5" block **cantilevers**, so block bending and screw prying
become the design case and §4 of the note no longer describes the wall. Not without an
engineer.

**Two rows need a number confirmed before they are spent.** The mineral-wool row depends on
splitting 6,313 SF between the exterior walls (the candidate) and the acoustic and humid
walls (`INT_2X4_PARTITION` / `INT_2X6_STAGGERED` at STC 36/52, the sauna, the plant room) that
must **not** be touched; the BOM reports mineral wool as two rows that were not attributable
without re-running the model. The vapour-retarder row is an allowance driven off sheathing
area at $0.35–2.20/SF whose own comment admits "nobody has decided which" — on the truss
walls the decision is already made by 4" of exterior ccSPF, far past IRC R702.7.1's
exterior-CI exemption for a 2x6 wall in zone 6, and adding a retarder would sandwich the
mineral wool between two Class II layers with no drying direction. Keep the allowance for the
garage's Zip-R only, and have whoever stamps the envelope confirm it.

### Do not do these

Each looks like a saving and isn't. Two were already settled the other way in the project's
own notes; they are recorded here so they do not get reopened a third time.

| idea | why not |
|---|---|
| **Swap the ccSPF for rigid board** | Reclaimed polyiso looks like −$6,900/−$8,600. Then a WRB comes back (+$2,200/+$4,900), opening flashing gets harder, the ACH50 1.0 target loses the layer that made it nearly automatic (+$1,500/+$4,000), the wall drops R-2, and you either cut ~4,200 holes in rigid foam or go back to through-foam furring — which puts the wall **back under IRC R703.15 and its 4" foam limit**, the exact provision the current wood-to-wood detail was engineered to escape. Virgin polyiso is a wash |
| **Outer girt KDAT → plain SPF** | $2,968–4,452, and already settled the other way in the engineering note's Risks. That girt is a 3-1/2" horizontal ledge inside the vent gap that will wet-cycle for the life of the wall |
| **Buy a proprietary clip-and-rail standoff** | $14,700–29,300 over 3,665 SF for clip and rail *alone*, against $16,028–26,118 for the entire current standoff **including window bucks**. Costs more, and reintroduces a through-foam fastener |
| **"Simplify" `RB-HOUSE` to one 36' stick** | The one place a well-meant simplification would actually put a crane on the job: **317 lb per ply** landing 11–12 ft above the attic deck at +32', against 106 lb as three 12-footers (16" section, re-struck 2026-08-30 for the pitch/depth change). Identical lineal feet, zero offcut — 36' divides three ways exactly |
| **Precast the 16" garden column** | 1,656 lb. The disposable fibre tube is a wheelbarrow of concrete; precast is a crane pick and a delivery problem. Even an 18" or 20" tube revert stays crane-free. Precast is the only version of this element that does not |

### What the build actually needs — three things nothing in this file names

No crane. But the plan and the price file are silent on all three of these, and the third one
costs nothing to fix now and a lot to discover late.

- **A telehandler, for the roof — not for the frame.** The roof plane is the largest
  material-handling problem in the project: ZIP, two staggered 3" polyiso courses, 5/8" OSB
  nailbase, standing seam and the PV modules, onto a 4:12 plane with a 26' eave and a 32'
  ridge and **zero overhang to stage on**. No single piece is over 67 lb, but the polyiso is
  a sail. Budget a telehandler or ladder conveyor — $700–1,000/day or $3,500–5,000/month —
  plus the same machine for the 26'-long PBR wall panels.
- **A boom pump, several days.** Forced by the sunken garden: 29.2 cy of 10' wall and its
  footings at the bottom of a 9' court, 5" from the house on the north side. A ready-mix
  chute cannot reach it. The main-floor deck's cap 9' in the air adds a day. Shortening the
  court trims this; only deleting it would remove the pump.
- **A sequencing note.** There is **no exterior stair** to the balcony and none into the
  sunken garden — every stair in the model is interior. So the two outdoor heat pumps
  (`EQ-M-HP1-OD` 92.6 lb, `EQ-M-HP2-OD` 145.5 lb) have to go up the interior stair and out
  through a 5' French pair **before the balcony guard rail goes up**. The alternative is a
  machine reaching 13 ft over an open 9' excavation with fresh footings in it.

### Every multi-ply framing member in the house, checked — 2026-08-30

Asked directly: are any of the framed pieces themselves overweight? No. Every multi-ply
LVL/PSL header and beam in the house, not only the ridge, per-piece as it would actually be
lifted:

| member | section | span / length | weight | spliceable? |
|---|---|---|---|---|
| Garage overhead-door header | 2-ply 14" LVL | 16' opening, `garage.py:366` | **258 lb** assembled, **129 lb/ply** | No — it spans, cannot lap over bearing |
| `RB-HOUSE` ridge, as ordered | 2-1.75x16 LVL | three 12' sticks per ply | **106 lb/piece** | Yes — bears continuously the full 36' |
| `BM-S-HALL` (2nd fl. hall opening) | 3-1.75x11.875 LVL | 8'-6" clear span | ~176 lb bundled, ~59 lb/ply | No — single span |
| `BM-M-HALL` (main fl. hall opening) | 3-1.75x11.875 LVL | 4'-2" clear span | ~90 lb bundled, ~30 lb/ply | No — single span |
| Sunken-garden / balcony beams | 3-2x12 sawn KDAT | ~8' span | ~70 lb bundled, ~23 lb/ply | No — sawn lumber, trivial regardless |

**The garage header is the heaviest non-spliceable member on site, and it stays the answer —
but per ply, every piece here is a one- or two-person carry.** `BM-S-HALL` and `BM-M-HALL`
are *shorter* single-span headers than the garage door's, so despite being 3-ply against the
garage's 2-ply, no single ply of either exceeds 60 lb. Not a crane job at a 7' lift for the
garage header, and not one anywhere else in this table. If the garage header ever becomes
awkward to set as a 2-ply unit, two 8' doors halve it; it does not need to be handled as one
258 lb assembly if a crew prefers to nail the plies up individually and stitch them in place,
same as the ridge and both hall beams already are.

### An engine finding — the order sheet asks for lumber that does not exist

**No dollars attached**: the lineal feet and the rates are identical either way. But it is
the wrong order sheet and the wrong lift, and it is the same mistake `RB-HOUSE` was already
fixed for.

`FramedMember.continuously_supported` is set in **exactly one place** in the engine —
`resolve/framing/roof.py:468`, for roof beams. Wall plates (`resolve/framing/solver.py:450`),
rim boards (`resolve/floors.py:244`) and girts never receive it, so they miss
`takeoff/framing.py`'s splice path entirely and fall through `_order_length_ft`'s over-length
branch (`framing.py:52-55`), which returns `ceil(len/2)*2` — **inventing** even-foot sticks
past the 20' stock ladder. The current order sheet asks for **105 pieces over 20 ft**,
including six 36' LSL rim boards (LSL tops out at 24' at most yards), three 36' 2x6 plates
and eight 36' 2x4 girts (SPF 2x6 maxes at 20'; 24' is special order). Metal trim runs are
legitimately long; the dimensional lumber is not.

The real-world answer for all of them is a lapped joint over bearing, which the model builds
correctly but the takeoff does not express. Extending `continuously_supported` to plates, rim
and girts would fix it — a real engine change with golden-test churn, so it is recorded here
rather than done inside a costing pass.

### Housekeeping — found along the way

Four of these were fixed on 2026-08-29 and are recorded under *Refactors* below. The rest are
open.

| finding | detail | impact |
|---|---|---|
| ~~`brief.md` is stale~~ | ~~"4" exterior polyiso+EPS", "2x4 upper walls", "standing seam" walls~~ | **FIXED 2026-08-29** — the model builds ccSPF, 2x6 throughout, PBR walls. Not evidence of a cheaper abandoned spec, just an out-of-date document |
| ~~Missing window price rows~~ | ~~`WT-2748` / `WT-2748-T`, six units, unpriced since the 2026-08-27 retype~~ | **FIXED 2026-08-29**, +$5,604/+$11,030 |
| ~~Stale row-comment quantities~~ | ~~`footing` 38.63 cy, `FOUNDATION_WALL_12_INT` 22.18 cy, `xps` 2,520 SF~~ | **FIXED 2026-08-29** — BOM is 33.25 cy, 5.25 cy, 4,182 SF (+66%) |
| Cold-weather protection is $0 | An explicit calendar bet. The file itself names the suspended deck as the worst case — "tenting the underside of a slab 9 feet in the air" | $8,000–21,000 |
| Second sprayer mobilisation | 2,448 LF of girt course and 45 openings' worth of jamb posts go on **between** the two foam passes; no sprayer waits through that. No row carries the second set-up | $500–1,500 |
| `FT-BOOKCASE-32-90` unpriced | Four units, `placeables` and `furnishings` both. An owner price, not one to invent | small |
| Garden slab priced as interior | The slab rate is justified as "the cheapest slab there is — no perimeter forming, no edge finish, no exposure", then applied to 5.75 cy of **exposed exterior** slab at the bottom of a 9' court | under ~$460–930 |
| Garden footings priced as strips | The `footing` rate derives from a 16"x8" strip, then covers the garden's 84"-wide reinforced retaining bases — 20.9 of 33.25 cy | under ~$1,500–2,100 |
| Garage slab may be thin | 3-1/2" carrying vehicle loads through MN freeze–thaw; 4"–5" is normal | +$343–1,810 |
| Excavation is one lump | $24,000–55,000 with no quantity anywhere in the model, so no design change can ever demonstrate a saving against it. The sunken garden alone implies ~200–250 cy of extra cut | the weakest number in the file |
| The published "≤340 lb" claim was wrong | The WashTower (353 lb, `FX-M-LAUNDRY`) is heavier than that. Corrected 2026-08-30 to: no framing piece exceeds 258 lb; no delivered item exceeds 353 lb — see the crane-verdict paragraph and the framing table above | none — not a cost item, an audit correction |

### Provenance

Verified directly in the repo: the four price corrections and their measured takeoff deltas,
the over-20-ft order-sheet count, the single site where `continuously_supported` is set, the
unpriced window rows, and a 749 pass / 0 fail baseline. Crane and machine rates are sourced
market research — the crane figure is a published Chicago rate card used as a Midwest proxy,
since no Twin Cities firm posts rates. The concrete, envelope and equipment ranges come from
specialist analysis that was reviewed but not re-derived end to end; treat them as
well-argued estimates, not quotes, particularly the girt respacing arithmetic and the
mineral-wool row split.

Also worth knowing when any steel-vs-wood comparison in this file is re-read: 2026 tariffs
put steel at 50% (25% on derivatives, locked in) while Canadian softwood duties are
provisionally being cut to ~24.8%. The basis has shifted toward wood since these rates were
struck.


## The garage sweep — PRICED 2026-08-30

Two ideas from TODO.md, both measured as **bid-total** deltas (the 2026-08-24 convention)
against a same-day baseline of **$939,199–$1,951,568**. Method: sandbox copy of catlin
inside the repo, one `Layer`/`FramingSpec` edited, `haus takeoff` re-run. Both are small —
this whole section is 0.07%–0.18% of the job.

| change | bid-total delta | verdict |
|---|---:|---|
| `GARAGE_ROOF` truss layer to `spacing=inch(24)` | **−$681 / −$1,136** | **TAKE** |
| `GARAGE_WALL_2X6` cladding → `pbr-panel-26`, direct on the Zip-R | **−$736 / −$2,391** | conditional — one phone call |
| …same, but adding a 2x4 girt layer to carry it | +$1,298 / +$1,493 (see caveat) | **no** |
| both taken together | **−$1,417 / −$3,527** | |

**24" o.c. trusses — take it; nothing else changes.** The saving is 488 LF off the `"2x4"`
row (`prices.toml:267`, $1.20–2.00/LF) — 6 fewer trusses — plus 12 fewer `H2.5A` ties.
`haus check --only all` moves **no verdict**; truss capacity is already the unsealed
engineered item `rafter/RF-GARAGE`, so the engine never had an opinion on spacing either
way. What the literature settles that the engine cannot: Alpine's span table (struck at
24" o.c.) gives 2x4/2x4 chords **41 ft** at 4/12 and 55 psf total / 40 psf snow, against a
24 ft span; **IRC Table R802.11** — whose conditions name 115 mph, Exposure B, span ≤32 ft
and *trusses at not more than 24" o.c.* — asks **178 lb** per tie at 24 ft / pitch <5:12,
against the H2.5A's 260 lb at reduced nailing; and R702.3.5's 5/8" ceiling board at 24" o.c.
is already in `default_lining`. Industry pricing corroborates the number: $90–175/truss
material + $5–10 to set × 6 = $570–1,110. 24" o.c. is the residential default; 16" is the
anomaly in this plan.

**PBR — not a savings question, a substrate question.** 663 SF swaps off
`"standing-seam-nailstrip-26"` ($6.00–11.00/SF installed, `prices.toml:1991`) onto
`"pbr-panel-26"` ($4.50–7.25, `prices.toml:1978`), less 640 more `T09150HWAM` gasketed
screws that `takeoff.fasteners` bills because the material carries `exposed_fastener=True`.
The `pbr-panel-26` comment in `plan/assemblies.py` says PBR here "would need a whole new
girt layer, and that cost cancels the saving" — **both halves are wrong.** Metal Sales'
manual puts PBR over "open structural framing **or** solid substrate" with a plain #10-14
woodscrew, no framing penetration; Huber says ZIP-R's outer 7/16" panel "can be used as a
nailbase for finished exterior cladding that does not require direct attachment to
structural framing." The longer-screw problem is `CATLIN_EXT_2X6`'s 4" of exterior foam and
does not transfer. The one real gap is thickness — Metal Sales wants **5/8"** substrate,
Zip-R gives **7/16"** — and **the incumbent has the same gap**: nail-strip is also a
solid-substrate panel and the same guidance calls for 5/8"–3/4", so the garage as drawn
already fastens into 7/16" OSB. So: get the supplier to accept 7/16" Zip-R in writing (and
get the same answer for the nail-strip already specified while on the phone). Yes → take it.
No → leave the cladding alone; girts make it a wash and buy an exposed-fastener look nobody
asked for.

**Caveat on the girt row — a stale price, not a real cost.** $774–$1,742 of that +$1,298/
+$1,493 is one line: `"bug_screen:GARAGE_WALL_2X6"` (`prices.toml:1096`), a $/SF proxy struck
against a 3/8" cavity (3.0 SF = 96 LF) and retired at 0 SF on 2026-08-20. A 1.5" girt reports
12.1 SF and the proxy quadruples — the exact failure `bug_screen:CATLIN_EXT_2X6`'s own comment
warns about. At the researched $2.00–4.50/LF × 96 LF, PBR-plus-girt is roughly a **wash**
(≈ +$25 to +$550). **Re-strike that rate before anyone reads the girt option off this table.**

**Cost of the cut:** none on the trusses. On PBR, exposed fasteners across 663 SF against a
garage roof that stays nail-strip — the garage would read mixed, as the house already does.

**One engine gap found:** nothing checks R702.3.5, so at 24" o.c. the 5/8" garage ceiling
board becomes load-bearing on a spacing the engine does not enforce. A later "drop to 1/2"
to save money" would go through clean. (And `CavityFill(framing_factor=0.09)` is documented
as 1.5/16; at 24" o.c. it is 1.5/24 ≈ 0.0625.)


## Taken

### Metal skin: one rate to four, garage rainscreen dropped — 2026-08-20
**$969,191–2,043,414 → $963,261–2,022,366. Saved $5,930–21,049** ($5,287–17,635 of it the
metal itself, the rest the bid ladder).

`standing-seam` was one key billing all 6,322 SF at the mechanically-seamed rate; split into
four by actual method (mech seam house roof, snap-lock house walls, nail-strip garage roof,
26ga nail-strip garage walls) — see the table in the roof-shingle entry above for the
per-key numbers. Nail-strip face-fastens straight to Zip-R's taped face, so the garage's
0.375" furring layer is gone and its wall panel dropped 24ga→26ga (−$0.80–1.10/SF material).
Bought back: 76 modelled S-5! wind clamps at wall/roof corners, $468–772 (garage only — the
house roof's folded seam is already the strongest uplift connection in the catalogue).

**Cost of the cut**, garage only: 26ga oil-cans more visibly than 24ga (specify a striated
pan), nail-strip is face-fastened so shorter-lived than clipped, and the garage's drying now
depends entirely on Zip-R's taped face being detailed right.

### Sunken-garden arch → column, beams, metal railing — 2026-08-18
**$282,561–580,402 → $277,166–569,145. Saved $5,395–11,257** (a third larger than the
`wall_structure` line alone, because the arch's footing and parapet face area came with it).

| line | before → after |
|---|---|
| `wall_structure` | $47,822–94,192 → $43,630–85,180 (−$4,191 to −9,012) |
| `envelope_layers` | $56,568–116,051 → $55,497–113,843 (−$1,070 to −2,208) |
| `footing_bedding` | $4,435–8,387 → $3,670–6,944 (−$764 to −1,443) |
| `concrete` | $19,974–32,346 → $19,233–31,181 (−$741 to −1,166) |
| `railings` | $3,125–6,551 → $4,505–9,092 (+$1,379 to +2,541) |

Bought back: `RL-SG-PORCH` (36.3 LF fascia-mount guard, matches the balcony), a footed
column, two beams, and ~17 LF of extra 6x6 (5 of 6 balcony pillars now start lower). Curved
formwork was the expensive part, as predicted — the concrete itself was always cheap.

**PARTIALLY REVERSED 2026-08-30, for $2,456–4,191 of the $5,395–11,257.** Retiring the arch
also retired the sunken garden's only E-W element, and with it the closed loop that let
`W-SG-W2` and `W-SG-E2` cancel each other's soil thrust. Graded as three isolated
cantilevers the retaining walls reached FS 0.73 against IRC R404.4's 1.5 and catlin went off
0 FAIL. What comes back is **not the arch**: `W-SG-ARCH` is a buried 12" x 17 1/2" grade beam
below the garden floor, invisible, and the two semicircular arches, the 42" masonry parapet
and the three pillars grouted into it all stay retired. The court reaches **FS 1.58**.

| line | reversal |
|---|---|
| `wall_structure` (`SUNKEN_GARDEN_WALL` 29.1 → 30.20 cy) | +$540 to +972 |
| `concrete` (footings 31.56 → 33.66 cy, the toe widening) | +$588 to +945 |
| `footing_bedding` (washed stone 70.2 → 82.7 cy) | +$627 to +940 |
| the rest (fabric, tile, incidentals) | +$701 to +1,334 |
| **bid total** | **$939,199–1,951,568 → $941,655–1,955,759** |

**Checked, because it is exactly the shape of an artefact:** an unpriced type is silently
dropped from the BOM and the total FALLS, so a "saving" here would have been the missing row
rather than the design. The total ROSE, every new key is priced, and the three quantity
comments this file's `prices.toml` neighbours carried (97.07 cy of stone, 803/804 LF of tile,
28.91 CY of garden wall) were re-measured in the same pass — two of them had been stale
before this work started.

**The cheap part is that the concrete went where the ground already is.** The eccentricity
fix needed 12" more footing, and putting it on the heel side would have walked the outboard
edge under the raised garden's apron, whose 3'-0" clear is the owner's own figure from the
brief. Put on the toe side instead it is +2.10 CY under the garden floor, no new excavation
outboard, and the apron does not move at all. `Footing.offset` is the field that made that
expressible; before it, the only shape the model could state was symmetric.

## Upgrades (money out)

| swap | current → new | costs | notes |
|---|---|---|---|
| Breezeway glazing: 16mm polycarb → aluminium storefront + IGU | $1,424–3,168 → $8,100–16,455 | ~$6,700–13,300 | breezeway isn't glazed in glass *today* — it's polycarb in a channel, no frame, no thermal break. Glazier minimum + shop drawings alone are $1,500–3,500; a 79 SF job can't buy direct from a fabricator |
| Breezeway roof: polycarb panel → stock fixed skylight | $480–960 → $1,430–3,185 | ~$950–2,225 | a Velux FCM 4646 + curb kit, real dealer pricing. A *custom* sloped unit is $200–480/SF, 2–4x this — don't confuse the two |
| Roof ice barrier: eave-only → full-deck high-temp | $5,000–11,000 → $17,400–38,300 | ~$12,400–27,300 | neither is in the estimate today (roof prices as bare panel). Code wants eave-only; standing seam runs hot enough to want full-deck as standard practice |
| Main-floor concrete: sealer → genuine polish | $1,270–3,696 → $4,600–8,100 | ~$3,300–4,400 | `sealed-concrete` is a densifier + sealer, not a polish — a separate specialty contract. Also the sensitivity behind the basement-deck downgrade: polishing before deleting the deck saves a further $3,000–5,000 |
| Interior vapour retarder: poly → smart membrane | $2,200–4,000 → $5,700–10,700 | ~$3,500–6,700 | not in the estimate today. MN Zone 6 needs Class I/II; a variable-permeance membrane (Intello, MemBrain) also lets the assembly dry inward — cheapest building-science insurance on the list |
| Oak flooring in the LVP rooms, 1,272 SF | $2,544–5,724 → $5,088–10,176 | ~$2,500–4,500 | living, study, 2F hall, two upstairs baths — oak in a bathroom is a maintenance call |

### Garage: full-height ICF walls (stem extended to plate)
New `wall_structure:GARAGE_ICF_FULL` replaces `GARAGE_WALL_2X6` on all 4 walls — **net
envelope+structure delta ≈ $5,600–10,900 more**, before unquantified framing-removal
savings. Not a full BOM line yet.

Garage is freestanding, 24'×24', already a hybrid: a 22" ICF stem carries an 8'-0" 2x6 wood
wall today. Extending the stem is a bigger version of an assembly that already exists.

| | added | removed |
|---|---|---|
| `wall_structure` ICF-6, ~11cy | $5,280–11,000 | |
| `envelope_layers` icf-eps, 1,200 SF | $2,640–4,560 | |
| `envelope_layers` stucco, 600 SF | $1,200–2,700 | |
| zip-r sheathing, 600 SF | | $1,320–2,520 |
| mineral-wool cavity, 600 SF | | $660–1,200 |
| nail-strip cladding, 600 SF | | $3,600–6,600 |
| **subtotal** | **$9,120–18,260** | **$5,580–10,320** |
| **net** | **$3,540–7,940** (before framing removal) | |

2x6 stud + rainscreen furring removal has no dedicated $/SF rate to net out (~$2,000–4,500
generic allowance, not house-sourced, would trim the net toward breakeven).

**What's genuinely new, not automated:** the roof-truss-to-ICF sill detail (materials
~$150–350, but the model's `_find_framed_on_concrete` sill logic doesn't fire for a roof
bearing directly on a wall within one storey — needs new engine work); garage-door jamb
bucks (no engine logic for openings against a `MasonrySpec` wall); a wood cripple wall above
the overhead door (standard practice, ICF pours in fixed courses); and the footing/stem
haven't been re-checked for the added dead load.

**Cost of the cut:** better fire/wind/impact resistance and thermal mass — worth weighing
against this being an unheated detached garage, the weakest case for ICF's usual energy
payback.

### Garage: CMU block wall + exterior Zip-R (third option)
New `wall_structure:GARAGE_CMU_8` (8'-0" tier only, ICF stem stays) — **net delta ≈
$11,200–15,600 more**. Counterintuitively pricier than full ICF, and with a bigger engine
gap. Keeps the existing Zip-R + nail-strip skin rather than switching to stucco.

| | added | removed |
|---|---|---|
| `wall_structure` CMU-8, ~14.8cy | $10,800–14,360 | |
| new furring layer (CMU has none built in) | $1,614–1,926 | |
| mineral-wool cavity | | $660–1,200 |
| **net** | **$11,214–15,626** | |

Two things work against it: (1) CMU installed cost ($18–24/SF) runs *higher* than ICF
($8–18/SF) — counterintuitive but corroborated by two source families; (2) the sill/anchor
finder gates on `material_ref == "concrete"` and CMU would be tagged `"cmu"` — it wouldn't
fire at all, a strictly bigger gap than ICF's. Anchor spacing is tighter too (4' o.c. under
R403.1.6.3, not ICF's 6'). Not priced: Tapcon-to-block labour premium, and a CMU bond-beam
top course (standard practice, no sourced $/LF).

Where CMU wins: ~30% less dead load than full ICF (partial-grout ~50-55psf vs ICF's ~74psf),
and a better-documented lintel detail at the garage door (CMHA TR91B) than ICF's thinner
jamb-buck research. Right answer only if wall weight matters to the footing more than the
dollars, or stucco is a hard no — otherwise full ICF is the stronger of the two masonry options.

## Not yet priced

- ~~Remove the attic level, truss + blown-in insulation.~~ **PRICED 2026-08-23 at
  $89,000–160,000** — see the cost-reduction sweep at the top of this file. It did not need a
  declared variant in the end: `variants.toml` can only swap assemblies and retune layer
  thicknesses, and this deletes elements. It was measured by ablating the resolved model
  (attic storey + `RF-HOUSE`/`RB-HOUSE`/`FS-ATTIC`/`ST-S2A`) and costing the trussed cold
  attic that replaces it off named `prices.toml` rows.

## Scope the model can't resolve — the allowance register

Compiled 2026-08-20, **authored into `prices.toml`'s `[allowances]` table the same day** —
these were real costs the estimate couldn't see because Type:Haus prices resolved
quantities, and the model doesn't resolve earthwork, permits, or a GC. Overlaps between
trades (gutters, ice-and-water, radon, window flashing) counted once. Installed 2026 Twin
Cities dollars, 6,012 gross SF, walk-out basement, detached garage; excludes GC
overhead/profit (itemised separately below).

### Site and structure

| item | low | high | note |
|---|---|---|---|
| Excavation, backfill, haul-off, grading | $24,000 | $55,000 | biggest swing: on-site spoil reuse can drop haul-off from $30k to $2-5k |
| Rebar, furnished + installed | $10,000 | $18,000 | ~5 tons — **not** authored; assumed inside the $/cy wall/footing rates |
| Garage slab, driveway apron, walks | $18,000 | $44,000 | driveway/walk often a separate later contract |
| Drain tile labour, rock, sump, outlet | $9,000 | $19,000 | pipe itself is in `drain_tile` |
| Concrete pumping | $4,600 | $7,800 | most-forgotten line — ready-mix and flatwork subs both exclude it |
| Damp/waterproofing | $1,200 | $16,000 | code min $1,200-3,200; +dimple board to $7k; full membrane to $16k |
| Window bucks, block-outs | $1,500 | $4,500 | |
| Radon rough-in, egress wells | $3,400 | $10,200 | MN requires radon-resistant new construction |
| Cold-weather concrete (Nov–Apr pour) | $8,000 | $21,000 | worst case is the suspended deck (tenting the underside, 9' up) |
| Survey, staking, erosion control | $2,000 | $6,000 | watershed-district requirement |

### Envelope

| item | low | high | note |
|---|---|---|---|
| Roof underlayment, full field | $4,500 | $9,000 | roof prices as bare panel |
| Ice & water barrier | $5,000 | $38,300 | $5-11k code eave/valley min, $17.4-38.3k full-deck high-temp |
| Drip edge, valley, boots, flashings, snow retention | $6,000 | $14,000 | partly overlaps `edge_trim` |
| Rainscreen furring over exterior polyiso | $4,400 | $8,800 | |
| Window/door flashing, sill pans, air sealing | $5,100 | $11,800 | 45 openings |
| Air sealing labour + 2 blower-door tests | $3,100 | $7,200 | MN caps 3.0 ACH50 |
| Interior vapour retarder | $2,200 | $10,700 | poly low, smart membrane high |
| Attic blown insulation | $2,700 | $4,700 | batts price wall-only today |
| Exterior sealants/caulking | $1,800 | $4,500 | |
| Sub-slab vapour barrier, sill sealer | $1,255 | $2,760 | |
| Scaffolding, lift rental | $3,000 | $8,000 | |
| Exterior hoods + flashing | $800 | $2,000 | dryer, range, HRV, hose bibs |

### MEP

| item | low | high | note |
|---|---|---|---|
| PV array — modules, racking, shutdown, labour | $24,000 | $46,000 | only inverter/battery/junction box priced today |
| Branch-circuit conductors | $10,000 | $25,000 | largest MEP omission — ~4,500-6,500 LF NM-B + feeders (conduit alone is priced) |
| Municipal water/sewer connection, SAC | $6,000 | $18,000 | verify 2026 Met Council rate; unsewered is $12-25k + septic $18-45k |
| Electrical service entrance | $3,500 | $9,000 | incl. temp construction power |
| Refrigerant line sets, 5 pairings ~145 LF | $3,735 | $7,090 | absent today |
| Water softener/filtration | $2,500 | $6,000 | optional on municipal, essential on a well |
| Structured low-voltage drops | $2,000 | $6,000 | enclosure priced, 20-35 drops not |
| Range hood + MN makeup air | $1,500 | $4,500 | not optional, all-electric |
| AFCI/GFCI breakers | $1,400 | $2,900 | load-centre price is can+main only |
| HVAC controls, thermostats | $1,200 | $3,000 | |
| Duct insulation, mastic, leakage test | $1,000 | $2,500 | required for MN energy code |
| Bath exhaust fans | $750 | $2,400 | duct is priced, fans aren't |
| Condensate drains, traps, pumps | $600 | $1,600 | |
| Radon fan, smoke/CO, surge, misc | $2,450 | $8,000 | |
| MEP permits | $1,500 | $4,000 | separate from building permit |

### Interior finishes

| item | low | high | note |
|---|---|---|---|
| Interior trim/baseboard, ~1,400-1,800 LF | $12,000 | $20,000 | no key today |
| Paint on trim and doors | $8,000 | $18,000 | `latex-paint` covers wall/ceiling area only |
| Closet shelving | $3,000 | $40,000 | wire $3-5k vs. semi-custom laminate $12-40k — pick a lane |
| Floor prep, self-levelling | $4,500 | $11,700 | |
| Tile backer/waterproofing | $4,000 | $8,000 | not in the tile labour rate |
| Door hardware, ~36 doors | $3,000 | $11,000 | |
| Window stools/aprons, 41 windows | $3,300 | $7,400 | |
| Floor transitions, thresholds | $1,000 | $3,000 | |
| Garage door opener | $500 | $1,400 | |
| Protection, final clean, dumpsters | $3,500 | $8,500 | |

### The three that dwarf all of the above

| item | low | high |
|---|---|---|
| General conditions (supervision, temp power/heat, toilet, fencing, trash) | $35,000 | $80,000 |
| GC overhead and profit, 13–22% published band | $100,000 | $375,000 |
| Design, permits, plan review, SAC/WAC, testing, insurance | $20,000 | $60,000 |

### Authored into the estimate, 2026-08-20

Every line above is now a row in `[allowances]` (`cli/prices.ALLOWANCES`), priced at count 1
(a lump sum prints as `ls`). Three deliberate differences from the raw sum:

| line | register | authored | why |
|---|---|---|---|
| Rebar | $10,000–18,000 | absent | already inside the concrete $/cy rates per `[basis_notes]` |
| GC overhead/profit | $100,000–375,000 | absent | that's `[markup]`, deliberately zero — a side door would also tax and contingency the fee |
| Ice & water | $5,000–38,300 | $5,000–11,000 | full-deck stays an upgrade, not base scope |
| Cold-weather concrete | $8,000–21,000 | $0–21,000 | schedule question — summer pour is genuinely $0 |

General conditions **is** authored (it's direct job cost, not overhead — conflating the two
is the most common six-figure estimate error). Subtotals: site $81,700–201,500, envelope
$39,855–121,760, MEP $62,135–145,990, finishes $42,800–129,000. Authored total after
adjustments and the four owner decisions: **$263,490–636,950**.

Four owner decisions, 2026-08-20:

| row | was | now | why |
|---|---|---|---|
| closet shelving | $3,000–40,000 | **$3,000–5,000** | wire on standards — biggest single narrowing on the file |
| cold-weather concrete | $0–21,000 | **$0–0** | summer pour, May–Oct; kept as the reminder of what a slip costs |
| ice barrier | code min | **code min, confirmed** | strategy not saving — the insulated assembly + low-friction seam + full-field underlayment prevents dams forming; don't value-engineer the underlayment while this stays minimal |
| tax rate | 9.025% | **8.525%** | suburban Hennepin not the city (−$3,182). Labour rates stay Minneapolis-wage regardless — only tax is jurisdictional |

Full bid ladder now:

| stage | low | high |
|---|---|---|
| resolved quantities | $576,557 | $1,139,150 |
| `[allowances]` | $263,490 | $692,950 |
| subtotal_net | $840,047 | $1,832,100 |
| waste | $25,470 | $47,904 |
| subtotal_ordered | $865,517 | $1,880,004 |
| contingency, 10% | $86,552 | $188,000 |
| markup — off by choice | $0 | $0 |
| sales tax, material only | $28,454 | $58,229 |
| **total** | **$980,523** | **$2,126,233** |
| **$/gross sf** | **$163** | **$354** |
| *memo: GC O&P at 15-20% if taken* | *+$130,000* | *+$375,000* |

Reconciles against published 2026 Twin Cities custom-home cost ($250-400+/sf) for a complex
house (walk-out basement, suspended deck, 5 refrigerant systems, sauna, plant room, PV+battery)
— low end is an owner-builder skipping the GC fee, matching the published band's GC assumption.

Sales tax reaches less than half the estimate ($290,550–709,886 stays merged — concrete,
wall_structure, seamless gutter, most allowances — printed by `haus takeoff` rather than
assumed away; MN taxes materials only, not construction labour, per DOR Fact Sheet 128).

## Refactors — where the price model itself was the problem

Not cost swaps — places the *estimate* was wrong or fragile, found in the 2026-08-20 pass.

**FOUR CORRECTIONS APPLIED 2026-08-29**, during the crane-free audit above. Each was
verified against the file's own stated basis and measured as a takeoff delta. **Net effect
on the bid: +$2,276 / +$3,494 — the estimate went UP.** The two silent under-bills were
bigger than the two over-bills, which is the point of doing this before anyone quotes it.
(The first two deltas were measured on the pre-attic-rework tree; the last two on
`355c207`.)

- **An inch of spray foam was free — `+$3,665 / +$5,497`, the bid was UNDER.** The truss wall
  is 4" of ccSPF in **two passes**, authored as **three bands** in `plan/assemblies.py`
  (1.5" band A, the girt's 1.5" `CavityFill`, and 1.0" `foam-vent`) so `analysis._layer_rsi`
  can parallel-path the wood through band B and still credit foam over 100% of band C. That
  split is R-value bookkeeping, not a third lift. `prices.toml` carried only `:1.5` and a
  retired `:2.5`, so band C emitted `closed-cell-spray-foam:1.0`, matched no key, and dropped
  into the take-off's own "not priced" list — **the bid was carrying 3" of a 4" wall**.
  Adding `:1.0` at the same $1.00–1.50/board-foot basis costs the same as the retired `:2.5`
  spelling of pass 2 did ($1.50–2.25 + $1.00–1.50 = $2.50–3.75/SF), because the ladder is
  linear in board-feet and carries no set-up. **The set-up is the part still missing** — the
  girts go on between the passes, so budget a second sprayer mobilisation, ~$500–1,500.
- **The garage ICF blocks were billed twice — `−$6,191 / −$10,954`.** The file convicted
  itself: `GARAGE_ICF_6`'s own comment calls it the **installed** ICF wall rate and spells
  out that the blocks are "$5.00–7.00/SF of face … on top of the ready-mix and steel." Then
  `[envelope_layers]."icf-eps"` billed them again at $6.50–11.50 per face-SF over 952.5 SF —
  both faces of the same stem. The house was paying $27–47/SF for a 6" ICF frost wall against
  a $13–25/SF market. `icf-eps` is zeroed, following the `SG_FROST_WING_XPS1/2` precedent
  already in the file. This is what withdrew sweep row 6 above.
- **The ICF stem was paying for bracing it does not need — `−$802 / −$2,079`.** $14–24/SF is
  the band a **full-height** ICF wall earns, and its labour half is priced around a
  turnbuckle alignment system every ~6 LF with an integral walk-through scaffold platform,
  staged lifts and a two-level crew. `W-G-STEM*` is **5'-4" — four 16" courses** — set from
  grade, braced with corner and end kickers only, poured in one low lift and consolidated by
  hand off the top of the wall. There is no platform to build, strip and move. Material does
  not move (blocks are blocks); labour comes off ~30%, $296–696 → $205–460/cy, giving
  **$665–1,060/cy = $12.31–19.63/SF** — inside $8–18/SF for the ICF wall system and
  $10–25/SF for an ICF foundation, where the old low sat *above* the middle of both.
  `GARAGE_ICF_6_BRICKLEDGE` is re-struck off it, $620–1,060 → $561–907/cy.
- **Six windows were free — `+$5,604 / +$11,030`, the bid was UNDER.** `WT-2748` was minted
  2026-08-27 when BED1/BED2 came down from 54" and STUDY3 went up from 36", and no price row
  followed it; `WT-2748` (4 ea) and `WT-2748-T` (2 ea) sat in the take-off's "not priced"
  list. Derived, not invented: 27x48 is **75 UI**, past the 0–71 flat band, so it keeps the
  over-band premium, and the nearest unit on the table is its own width — `WT-2754` (27x54)
  with 6" of height off, ~7% less glass and frame and still a one-man set. The result
  brackets correctly against `WT-3048` (30x48, 78 UI): three inches narrower, four percent
  under. The delta is larger than the rows themselves because
  `envelope-opening-flashing-and-sill-pans` is **driven off** `openings` — a measurement, not
  a second bill.
- **Not applied, recorded instead:** the mineral-wool row split, the exposed garden slab
  priced at an interior rate, the garden's 84"-wide retaining bases priced off a 16"x8" strip
  rate, and `FT-BOOKCASE-32-90`. See the housekeeping table in the crane-free audit above.

- **`PORCH_DECK_COMPOSITE` "disagreed with itself" — not a bug, closed.** The 0.05cy solid
  and the 164.7 SF sheet_goods row are two different decks (sunken-garden porch vs. breezeway
  deck), not one counted twice. Breezeway solid is now priced ($216-515) — no unpriced rows
  remain that aren't confirmed mirrors.
- **Six rows priced per cubic yard for things nobody sells by the yard — built.** A price row
  can now name `unit=` and read a different BOM field (`cli/price_file.ALTERNATE_UNITS`).
  `thermal_break` was wrong by 10x in the direction that hides scope (three bearing pads
  billing $9-15 total); the rest were honest totals with unauditable rates. `drain_tile`
  converts exactly ($18-42/SF, confirmed independently against `footing_bedding`'s 761.3 LF).
- **761 LF of drain tile — a quantity question, not a pricing one.** Model rings each of 26
  footing beddings separately rather than one building perimeter + laterals — correct for
  isolated pads, double-counts a continuous wall footing. At $6-14/LF, 761 LF vs. a ~250 LF
  perimeter is **$3,000-7,200**. Worth checking against the drainage plan.
- **`[drainage]` blending two 3x-different products — built.** `QUALIFIED_KEY_FIELD` now
  splits `gutter`/`downspout` by `product` into 4 keys (aluminum vs. metal-dark-exterior);
  bare fallback keys deleted so an unpriced product surfaces instead of silently blending.
  Money moved only 3% — it was always weighted right for today's mix.
- **Three roof-edge quantities — reconciled, closed.** No phantom trim: fascia (251.5 LF) is
  three runs, one deliberately doubled (garage backer + face ply); edge cladding (243.9 LF)
  is wall-top closure, not fascia; gutter (121.5 LF) covers eaves only, not rakes, and matches
  drip edge exactly. 4 downspouts, confirmed via BOM `count`, is right for a 2-storey walk-out.
- **`construction_returns:pt-sill-plate` — closed.** The 306.6 LF is the wall's own PT bottom
  plate (`_append_plates` appends one to every framed wall unconditionally), not a second
  mudsill. No change to the number needed.
- **Waste, contingency, tax — 3 of 4 stages turned on, 2026-08-20.**
  - `[waste]` 3-10%, material only, never on declared labour (a real bug when first turned on
    put 41% of waste on labour — fixed, pinned by `test_waste_never_rides_on_declared_labour`;
    stage dropped from $25,470-47,904 to $14,938-28,107). Not declared on sections whose
    order quantity already carries waste (framing, sheet_goods, floor_finishes, wood_surfaces)
    or on unit-quantity items (openings, placeables, allowances).
  - `[contingency]` 10% (not the 15-20% a schematic estimate needs, because this house is
    modelled deeper than most). Applies to allowances too, deliberately not special-cased.
  - `[tax]` 8.525%, material only, and only material not already taxed once — a real
    double-count existed where a rate was back-derived from a published *installed* price
    (openings, floor_finishes, 6 allowance rows, worth $7,887-17,685). Fixed with
    `[tax_included]`, a boolean per section/key (not a rate — "does this number already
    include tax" has an answer; "what rate is buried in this average" doesn't). Tax stage
    fell from $26,551-54,450 to $18,664-36,765.
  - `[markup]` stays zero by choice, present so turning it on is one edit
    (`test_catlin_does_not_pay_the_gc_twice` pins it against `[allowances]` so neither a
    double-count nor a hole can happen silently).
- **The roof is priced as bare panel, and the boundary is guessed across 4 tables** —
  envelope_layers (panel+clips), allowances (underlayment, ice-and-water, flashings),
  edge_trim (drip edge, closure), hardware (seam clamps). **The highest-value phone call on
  the list**: a single roofing quote settles what's inside the roofer's number, touching the
  house's largest line ($60-117k) plus $15,500-34,000 of allowances. If the roofer's price
  includes underlayment, the modelled `roof-underlayment-synthetic` row has to come out the
  same day — and it must stay a *permeable* synthetic, not peel-and-stick, or the
  condensation gate fails.
- **Basement steel framing** — interior basement walls as steel stud, not yet costed.

## Open questions

| # | question | what it moves |
|---|---|---|
| 1 | Is the GC fee in or out? `[markup]` stays zero for now | — |
| 2 | Is rebar inside the concrete $/cy rates, or its own line? Assumed inside; reversing means editing both places at once | $10,000–18,000 if wrong |
| 3 | Is 761 LF the right drain-tile length, or should it be one perimeter ring? | $3,000–7,200 |
| 4 | One roofing quote — see Refactors above | resolves ~$15,500–34,000 of boundary |
| 5 | **Is the attic staying?** Priced 2026-08-24 at $89,000–160,000 — the largest single decision left in the model, and the only one that changes the building's whole upper third | $89,000–160,000 |
| 6 | **The PV allowance prices 5.28 kW at $4.55–8.71 per watt.** Published 2026 US residential installed cost is $2.60–3.60/W, and a sub-6 kW Twin Cities system $3.50–4.50/W — i.e. $18,500–23,800 for this array. One quote settles it | $6,000–22,000, and the second-highest-value phone call on the list after the roofer's |
| 7 | Cladding: is this a metal-clad house on all four elevations, or on the two that are seen? | $10,000–29,000 |
| 8 | The balcony plank: one call to Versadeck, (651) 356-1870, turns the least certain row in the file into a real one | $3,400–10,000 |

~~Our original 16" OC spacing for studs and joists was built around the idea that we had to directly support 16" OC standing seam siding. Now that we are using exposed fastener siding, can we trim down the stud spacing (especially perhaps for the attic level?). This would also bump up the window width for betweeen studs.~~ — SETTLED 2026-08-28, see "The framing sweep" above. **The 16"-for-standing-seam premise is dead and was always wrong:** cladding is `pbr-panel-26` on *horizontal* girts at 24" o.c. and `takeoff/hardware_config.py` fixes the screw grid at 12" rib x 24" support pitch, into the girt — no fastener has ever landed on a stud. **IRC Table R602.3(5) is the real bound**, and it stops the main storey dead (2x6 bearing at 24" is permitted for roof-ceiling only, or one floor + roof-ceiling; the main storey carries the second floor, the attic floor and a habitable attic). The attic knee walls would qualify and stay at 16" by owner decision; the six nonbearing gables are permitted at 24" to a 20' height with no load argument and are the only live candidate — **not yet built.** The two engine defects that had to be fixed before any wall in this house could be a spacing other than 16" are fixed (item E in the sweep above). Floor joists at 24" were priced and declined.
~~Maybe swap out the concrete wall across the sunken garden side of the basement for wood framing (avoids formwork for the doors and windows) but might violate the cross-bracing needed for concrete basement walls per tables.~~ — BUILT 2026-08-28, item C above. The bracing worry does not arise: those two segments retain **nothing** (the garden floor is flush with the basement slab), which item A established by authoring `unbalanced_fill=ft(0)` on them. Net effect on the estimate −$456/−$1,835, a third of the prediction — and the formwork the idea is really about is exactly what the takeoff cannot see.
~~Are there any locations where it is worth specifying built up columns/beams (ie stacks of 2x6s)? As long as they don't need heavy duty bolts, this can be a cheaper option. Also perhaps LSL instead of LVL in some places.~~ — DECLINED 2026-08-28, item D above. Both moves are already taken: every multi-ply beam in the house is built-up sawn already, and the rim boards are already LSL. The whole house holds 12 LF of LVL.
Resilient membrane under subfloor for better STC?

Attic swap:
Open space over stairs
One bathroom (note cheap spec). Note around 42" height for vent stack
Increase joist spacing

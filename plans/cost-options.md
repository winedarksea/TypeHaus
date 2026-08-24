# Cost options — priced upgrades and downgrades

Started 2026-08-08. Menu of swaps if the number needs to come down, each priced against a
line in `houses/catlin/prices.toml`. **Nothing here is decided** — the plan as authored is
the plan, this is the menu.

**Rules:** every row cites the prices.toml line and the delta at both ends of the range —
an unpriced idea lives in TODO.md's "potential cost cutting" list until it has a number. A
swap that changes what the house *does*, not just what it costs, gets a **cost of the cut**
note. Rows are material+labour unless noted.

**Start here:** [Premium features](#premium-features--what-each-one-costs-2026-08-23) — what
each optional thing costs — and the
[cost-reduction sweep](#cost-reduction-sweep--2026-08-23) — everything worth $3,000 or more
off the bottom line. Both were added 2026-08-23 and both quote bid totals, not section deltas.

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
below this line are *section* deltas. The two 2026-08-23 sections that follow — the premium
menu and the cost-reduction sweep — quote **bid-total** deltas instead, measured by rebuilding
the estimate with the change made. The measured ladder multiplier is **~1.17x**, not the 1.20x
estimated above.

## Premium features — what each one costs (2026-08-23)

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

### Habitable cathedral attic — $89,000–160,000

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
1,079 sf of it (`RM-A-WEST` 598, `RM-A-EAST` 481) is already typed `storage`, i.e. the
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
sauna-only wall — 177.1 SF of `sauna-tg` ($1,860–3,542) + `polyiso-foil` ($460–832) on
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

### Raised garden apron — $8,700–17,400

Ten elements (`W-RG-*` and their levelling pads): `wall_structure` −$7,350/−$14,700 for
245 SF of `RETAINING_BLOCK_12`, `footing_bedding` −$136/−$287. No engine work, no envelope,
no MEP — which is exactly why it defers cleanly.

## Cost-reduction sweep — 2026-08-23

Asked for: things that take real money out without giving up a high-performance house.
**Threshold for appearing here is $3,000 off the bottom line.** Same convention as the
premium table above — every number is a **bid-total** delta, not a section delta.

Four of these were priced by actually building the change: a copy of the house with the
edit made, `haus check` run to confirm it stays at 0 FAIL, and `haus takeoff` run to read
the total. Those rows say **built**. The rest are arithmetic on named `prices.toml` rows.

| # | change | saves | how priced |
|---|---|---|---|
| 1 | **Attic level → trussed cold attic + blown R-60** | **$89,000–160,000** | see above |
| 2 | **House-wall cladding: standing-seam snap-lock → lap siding on the same outriggers** | **$15,600–29,000** | built |
| 3 | Excavation: reuse spoil on site instead of hauling off | $10,000–25,000 | allowance note |
| 4 | Roofs (house + garage, 2,186 SF): standing seam → architectural asphalt | $9,700–18,200 <br>+$1,500–3,000 of snow retention | built |
| 5 | Garage ICF stem → conventional formed frost wall | $9,400–16,900 | arithmetic |
| 6 | ⏳ Raised garden apron — defer | $8,700–17,400 | ablation |
| 7 | ⏳ Driveway apron + walks — defer to a later contract | $18,000–44,000 | allowance |
| 8 | Windows: mid-range clad/fibreglass → vinyl or entry fibreglass, same U-0.25 | $6,500–11,000 | the `[openings]` note's own number |
| 9 | Delete the 8 discretionary attic windows | $6,200–12,100 | built, 0 FAIL |
| 10 | Concrete deck over the theatre → I-joists | $6,300–10,700 | see above |
| 11 | Exterior CI: 4" → 2.5" of ccSPF (R-38.7 → R-32.7) | $5,600–8,000 | built, 0 FAIL |
| 12 | Plant room → an ordinary second-floor room | $5,300–10,400 | arithmetic |
| 13 | Trim, stool and apron package simplified | $5,000–13,000 | allowance scope |
| 14 | Oak floor + red-oak stair treads → LVP / carpet | $4,300–6,800 | `[floor_finishes]` |
| 15 | Balcony aluminium plank → walkable PVC membrane deck | $3,400–10,000 | `[sheet_goods]`, low confidence |
| 16 | Exterior guards: Trex Signature → builder-grade aluminium | $3,700–5,700 | `[railings]` |
| 17 | Ishtar-gate glazed brick veneer → plain brick, or delete | $3,300–7,100 | ablation |
| 18 | HVAC System 3 folded into the multi-zone | $3,000–5,400 | ablation + line-set allowance |

**They do not add up.** #1 contains #9 outright and part of #2, #4 and #11; #5 is
two-thirds of the "insulated garage" premium; #6, #7 and #10 also appear in the premium
table. Take #1 and rows 9, and most of 2/4/11, shrink with it.

### 2 — the wall cladding is the biggest lever that is not a feature

3,512.2 SF of `standing-seam-snaplock` at $8.75–16.00/SF installed = **$30,732–56,195** —
the largest single row in the *resolved* bill of materials (allowance lump sums aside),
ahead of the 11,392.8 SF of gypsum ($17,659–30,191) and the roof's own metal
($15,084–26,577). It is a *rainscreen
skin*: it carries no structure, no air control, no water control
and no thermal control — the Swinburne truss wall's 4" of ccSPF is all four of those. So this
is the one exterior line where a downgrade costs nothing but looks.

Re-priced at $5.00–9.00/SF installed (steel or engineered-wood lap, or a fibre-cement panel —
the band published for metal siding and for LP SmartSide alike): total
$951,336–1,992,450 → **$935,575–1,963,226**, **−$15,600 / −$29,000**.

- **The outriggers decide what can go on.** They are KDAT 2x4 on edge, **vertical**, at 16"
  o.c. That is a direct nailer for *horizontal* lap or panel and takes it with no extra
  framing. A vertical ribbed or corrugated panel wants horizontal girts and would need a
  second layer, which eats a third of the saving — price that version separately before
  choosing it.
- **A half version exists.** Keeping standing seam on the south and west elevations
  (~1,212 SF) and lapping north and east (~2,300 SF) is roughly **−$10,000 / −$17,600**.
- **Cost of the cut:** this is a metal-clad house whose roof, walls, corner trim and edge
  trim are one continuous material, and `brief.md`'s style line says so. Lap siding on the
  walls makes the roof a different material from the walls for the first time, and the
  elevations want revisiting. Exposed-fastener products also put 20–30 year gasketed screws
  on the wall where there are none today.

### 4 — the roof row in this file was wrong, and here is the honest split

The **Standing-seam metal roof → architectural asphalt shingle** row above compares
$54,777–99,331 of metal over 6,322 SF against $31,600–56,900 of asphalt, then says in its own
detail that only 2,180 SF of that is roof and the other 4,143 SF "is not shinglable". Both
halves are true and the subtraction between them is not — the row's headline
"**~$20,000–42,400, the biggest lever on the list**" is really two different swaps added
together, and the asphalt column is priced over area that can never take asphalt.

Split honestly, both built:

| swap | area | current | after | saves |
|---|---|---|---|---|
| **roofs only** → architectural asphalt | 2,186 SF (`RF-HOUSE` 1,436.6 + `RF-GARAGE` 749.6) | $20,331–36,322 | $10,931–19,675 | **$9,700–18,200** |
| **walls only** → lap siding (row 2 above) | 3,512 SF house + 663 SF garage | $34,712–63,491 | — | **$15,600–29,000** |

Plus, on the roof swap only, the S-5! seam clamp family and the formed ridge cap go away:
~$1,500–3,000 more, per this file's existing note. So the roof-only lever is
**$11,200–21,200** and the wall-only lever is **$15,600–29,000**; together **$26,800–50,200**,
which is where the old row's $20,000–42,400 was reaching. They are independent decisions and
should be taken as two.

Everything the old row says about the *cost of the cut* stands, and the PV argument is the
strongest part of it: `S-5-PVKIT` clamps to a standing seam with zero penetrations, and
asphalt needs 48 flashed penetrating feet instead.

### 9 — the eight discretionary attic windows

**Built: 699 pass, 0 fail, 45 not evaluable** — deleting all eight breaks no rule in the
registry. `RM-A-WEST` and `RM-A-EAST` are `storage` occupancy, so R303.1's natural-light
rule never applied to them, and none of the eight is an emergency escape opening.

| unit | ×  | what it is |
|---|---|---|
| `WIN-A-W-N`, `WIN-A-W-S`, `WIN-A-E-N` (`WT-1424`), `WIN-A-E-S` (`WT-1424-T`) | 4 | the 5' knee band, both eave walls |
| `WIN-A-S2`, `WIN-A-S3` (`WT-1448`) | 2 | south gable flankers |
| `WIN-A-S-JUL-W`, `WIN-A-S-JUL-E` (`WT-1864`) | 2 | the juliet pair |

$951,336–1,992,450 → **$945,008–1,980,177**, **−$6,300 / −$12,300**, plus a share of
`[allowances] envelope-opening-flashing-and-sill-pans` and `finish-window-stools-and-aprons`
that is a lump and does not move on its own: 8 of 45 openings is ~$900–2,100 more.

**Why these eight and not any other eight.** `[openings]`' own 2026-08-20 pass found that
windows are priced by **united-inch band, not by area** — a 14x24 costs the same as a 27x36.
Eleven `WT-1424`, two `WT-1864` and two `WT-1448` are the house's fifteen sub-stock-size
units, and the same note flags all three families as possibly **below a stock line's minimum
size** (Simonton's awning minimum is 23.5" wide; Andersen 400's narrowest casement is
20-11/16"). So these are the units that cost the most per square inch of daylight *and* carry
the most availability risk. The four in the knee band buy daylight for carpeted storage.

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
- `preferences.toml` asks for `wall_r = 40`; this is a deliberate move to R-33, still roughly
  double the MN prescriptive R-20+5ci. It is the row on this list that most directly spends
  performance for money, and it is the smallest saving of the four built rows — **weigh it
  last, not first.**
- **The lumber does not come back with it.** The outrigger stays a 2x4 on edge and the
  rainscreen gap grows 1.0" → 2.5". A 2x3 outrigger (1.5" foam + 1" gap, R-35 total) would
  take the KDAT line down too, but `[framing]` has no 2x3 row and the truss-wall geometry
  tests are written against the 3.5" member — price that separately.

### 5 — the garage ICF stem

`GARAGE_ICF_6` is 8.8 cy of core at $758–1,299/cy plus 952.5 SF of EPS form at
$6.50–11.50/SF — **$12,859–22,385**, or **$27–47 per SF of wall**, for a 476 SF frost wall
under an unheated-by-default detached garage. A conventional formed 8" wall at this file's
own re-derived $495–810/cy (see the 12"→8" entry) is $4,851–7,938 for the same 9.8 cy,
forms in the rate.

**−$8,000 / −$14,400 net, −$9,400 / −$16,900 after the ladder.**

- **Cost of the cut:** R-21.9 → R-1.8 on the stem, and the stem is the garage's only
  below-grade thermal layer. If the garage stays heated, ~64 LF × 5' of uninsulated frost
  wall is a real loss; 2" of exterior XPS on a conventional wall buys most of it back for
  $1,900–3,800 and still lands well under the ICF.
- `plans/cost-options.md`'s two existing garage rows go the *other* way (full-height ICF at
  +$3,540–7,940 net, CMU at +$11,200–15,600). This row is the third direction and the only
  one that is cheaper than what is drawn.
- The `_find_framed_on_concrete` sill logic already fires for a formed concrete stem
  (`material_ref == "concrete"`), so unlike the two upgrade rows there is no engine gap here.

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
  `DT-INT-SWING30-TRIMLESS` row above shows a hidden-jamb *door* is a 4–5x premium, not a
  saving. Returns at windows are cheap; reveals at doors are not.
- **14, oak.** `[floor_finishes]` "oak" is 351 SF at $11.50–20.50/SF installed
  ($4,037–7,196), and its own note says 351 SF is **under most Twin Cities sand-and-finish
  minimums** — a $1,200–1,800 mobilisation plus a trip per coat, for two rooms. LVP over the
  same 351 SF is $1,229–3,071: **−$2,800/−$4,100**. The red-oak stair treads add
  $1,500–2,700 more (existing row above; note `stair_finish` is not in the priced sections
  today, so that half does not show in the total).
- **15, the balcony plank.** `[sheet_goods] "aluminum-deck"` is 6 sheet-equivalents = 182.0 SF
  at $30–52/SF installed = **$6,948–12,252**, and the row itself says **CONFIDENCE: LOW** and
  that no published price exists for any waterproof interlocking aluminium deck. A walkable
  PVC membrane (Duradek/Tufdek class) over a plywood substrate is $12–22/SF installed =
  $2,184–4,004, and the existing downgrade row quotes composite-over-membrane at
  $2,000–3,600. **−$3,400/−$10,000** after the ladder — a wide range because the top end is
  a quote-only product. **Call Versadeck, (651) 356-1870, before deciding**; the existing row
  already says the call may make the swap moot. Dry-below is not optional: this deck is the
  porch's roof.
- **16, guards.** `RAILING-EXT-ALUMINUM-FASCIA` is 74.6 LF (balcony 38.3 + porch 36.3) of
  Trex Signature at $90–135/LF = $6,714–10,071. Builder-grade aluminium at $40–70/LF is
  $2,984–5,222: **−$3,700/−$5,700**. Both guards or neither — the two levels stop matching
  otherwise. (This supersedes the $1,343–2,611 in the row above, which predates the porch
  guard replacing the masonry parapet.)
- **17, the brick veneer.** Ablating `W-B-BRICK`, `FT-B-BRICK` and the two arched reveals:
  **−$3,322/−$7,107**, essentially all `wall_structure` (129.2 SF of glazed lapis, gold and
  brown at $15–27/SF). This supersedes the "$1,233–2,603" downgrade row above. Cost of the
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
  $720–1,760. Under threshold.
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

## W-B-STR, the 12" stair wall — PRICED 2026-08-22, RECOMMENDATION IS NEITHER

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
  worse.

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

**Recommendation: neither.** $330–560 for a stair-well re-dimension plus an engineered
header is a bad trade at any confidence; $389–2,745 for retiring a two-storey bearing line
and its footing is a worse one. If the stair well is ever re-drawn for another reason, the
8" pour comes almost free at that moment — revisit it then, not before.

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
| 5 | **The PV allowance prices 5.28 kW at $4.55–8.71 per watt.** Published 2026 US residential installed cost is $2.60–3.60/W, and a sub-6 kW Twin Cities system $3.50–4.50/W — i.e. $18,500–23,800 for this array. One quote settles it | $6,000–22,000, and it is the second-highest-value phone call on the list |
| 6 | **Is the attic staying?** Now priced at $89,000–160,000 — the largest single decision left in the model, and the only one that changes the building's whole upper third | $89,000–160,000 |
| 7 | Cladding: is this a metal-clad house on all four elevations, or on the two that are seen? | $10,000–29,000 |
| 1 | Is the GC fee in or out? `[markup]` stays zero for now | — |
| 2 | Is rebar inside the concrete $/cy rates, or its own line? Assumed inside; reversing means editing both places at once | $10,000–18,000 if wrong |
| 3 | Is 761 LF the right drain-tile length, or should it be one perimeter ring? | $3,000–7,200 |
| 4 | One roofing quote — see Refactors above | resolves ~$15,500–34,000 of boundary |

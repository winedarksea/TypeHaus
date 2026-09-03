# Cost options — the menu

Started 2026-08-08. **Rewritten 2026-08-31 into three tables against one baseline**
(decision #66). Nothing here is decided: the plan as authored is the plan, this is the menu.

## Method — read this before comparing any row

**The single baseline. Every figure in this file is a delta off**
**`$917,729 – $1,895,004`**, the printed `haus takeoff houses/catlin` bid total on
2026-08-31. That total already carries waste, the 10% contingency and material sales tax.
`[markup]` is **zero by owner decision**, so the GC's $100,000–375,000 fee is already out of
the number and cannot be counted again as a saving by anyone — including a self-performer.

**One convention, not two.** Every row quotes a **bid-total** delta. The older file mixed
section deltas with bid-total deltas and made the reader check which; it no longer does. When
a row was originally struck as a *section* delta it has been carried through the ladder. The
measured marginal multiplier is **~1.16x** (waste is per-row and sales tax reaches material
only, so it is not a flat 1.20x).

**The rule this file exists to enforce, cited by `plans/pattern_language_review.md:9`:**
*an unpriced idea lives in `plans/TODO.md` until it has a number.* A row here has a number, a
named `prices.toml` line or model element behind it, and — where the change is a spec change
and not an arithmetic one — a **cost of the cut**.

**`how priced` is one of four things.** `built` — a sandbox copy of the house with the edit
made, `haus check` confirmed at **0 FAIL**, `haus takeoff` re-read. `ablation` — the feature's
elements filtered out of the *resolved* model and the BOM re-run. `arithmetic` — named
`prices.toml` rows added and subtracted. `allowance` — a lump the model does not resolve.
Rows marked **re-measured** were rebuilt on 2026-08-31 against the baseline above.

**Rows NOT marked re-measured were struck against a baseline within 1.3% of $941k** (the file
carried four: $939,199, $941,655, ~$948k and $951,336). The 2026-08-30 allowance correction
then moved the base **−2.8% at the low end and −3.3% at the high**. Read an unre-measured row
**−3% or so**, and do not sharpen it further — that is inside its own precision.

**Three rows were rebuilt on 2026-08-31 and one was not.** The two ccSPF depths and the
attic windows were re-measured as sandbox copies inside the repo, each confirmed at 0 FAIL
before its number was trusted. **The attic row was not**: measuring it needs a modelled
trussed cold attic (a `CATLIN_TRUSS_ROOF` assembly, gable walls, ceiling plane, and the ERV,
lighting, electrical and PV elements re-homed off the storey), and that sandbox was deleted
after the 2026-08-29 measurement and never committed. Its $69,100–133,900 is that
measurement, and it survives the base move for a reason worth stating rather than assuming:
the premium is the **difference** of two builds, and almost every allowance corrected on
2026-08-30 is a house-wide lump that is identical on both sides of it. The area-driven ones
that are not — air sealing at $0.15–0.45/SF over the ~1,363 gross sf that would go, plus the
window flashing and stool rows — move the premium by well under $1,000, inside its own
precision. **Rebuilding that sandbox is the one outstanding measurement in this file.**

**The garage wall was rebuilt the same day the baseline above was printed, and the baseline
predates it.** `GARAGE_WALL_2X6` went 2x6 @16" o.c. / empty bays / 1.5" Zip-R / 26 ga
concealed nail-strip → **2x6 @24" o.c. / 2" ccSPF / 5/8" CDX / 7/8" corrugated
exposed-fastener panel** (`houses/catlin/CLAUDE.md`), and the trusses went to 24" o.c. with
it. It is `built` in the fullest sense — not a sandbox copy, the reference house itself —
confirmed at 0 FAIL. Diffing `haus takeoff` immediately either side of that one commit
(759850a vs. the redesign) puts it at **−$2,916–$5,359** off the bid total, ahead of the
plan's own arithmetic estimate of ≈−$1,700–$3,500: the ccSPF spends back roughly a third of
what the cladding and 24" spacing save, in exchange for a real air seal and roughly double
the wall's honest R-value (R-7–8 → R-13.2 card, up from a dishonestly-read R-14.3 that was
billing the empty bay as solid framing). **The single baseline above is therefore stale by
that amount** — it is the PRE-rebuild total, not the current one — and every unre-measured
row's "read it 3% low" guidance does not cover this; the true current baseline is
$914,813–$1,889,645. The two menu rows this rebuild superseded (Garage cladding → PBR
direct on the Zip-R; Garage roof trusses → 24" o.c.) are gone from *Cost cutting* below —
their premise, a wall that still has Zip-R and 16" o.c. trusses to change FROM, no longer
exists in the model, and both are now inside the baseline rather than options against it.

**"Delete the eight attic windows" is now FIVE, and not for the reason the old row gave.**
Four of the eight — `WIN-A-W-N`, `WIN-A-W-S`, `WIN-A-E-N`, `WIN-A-E-S`, the knee-wall pairs —
were **already deleted on 2026-08-29** with the knee walls themselves; their hosts are 1-1/2"
plates laid flat and a plate has nothing to glaze. Six windows remain on the storey. Deleting
all six FAILs `code.R310_egress` and **nothing else** (confirmed by build), so the deletable
set is the five that are not the studio's emergency escape opening.

**The baseline fell $26,000–65,000 on 2026-08-30 and none of it was a saving.** An audit of
`prices.toml`'s 49-row `[allowances]` table found 15 defects, 6 of them double-bills or scope
this house does not contain — bath exhaust fans in a house that ventilates entirely through
ERV radial extract; an interior vapour retarder the wall assembly must not have; egress
window wells for a basement with no bedroom. Fixing them made the estimate correct, not
cheaper. **Report it as "the estimate was wrong", never as a cut**, or it lands in the table
below twice.

---

## 0 — What the optional features cost

Not a menu of cuts — the answer to "what does this house have that an ordinary 5,000 sf
Minnesota house would not". Several rows in table 1 are slices of these, which is why this
table is here: **a feature and its slice are the same money.**

| feature | cost | of the bid total | note |
|---|---:|---|---|
| **Habitable cathedral-roofed attic** — 1,281 sf of floor and the hot roof over it | **$69,100–133,900** | 7.5% / 7.1% | vs a modelled trussed cold attic. $59–114/sf — the cheapest floor area in the building |
| **Sunken garden / porch / balcony** — the freestanding concrete structure | **$47,900–86,900** | 5.2% / 4.6% | balcony alone is $10,300–19,100 of it; brick veneer $3,300–7,100 |
| ⏳ **PV array + battery** — 5.28 kW, 14.3 kWh, EG4 12kPV | **$38,000–73,000** | 4.1% / 3.9% | defer, but pre-wire — see *Upgrades* |
| **Sauna** — 127 sf, heater, benches, T&G liner, shower, its own ERV pair | **$12,700–29,500** | 1.4% / 1.6% | Two basement walls carry a second house-local liner stack |
| **Insulated + heated detached garage** — the insulation and heat only | **$12,500–23,600** | 1.4% / 1.2% | the whole garage is $62,300–119,100 |
| ⏳ **Raised garden apron** — 245 SF of SRW wrapping the sunken garden | **$8,700–17,400** | 0.9% / 0.9% | defer — a landscape contract |
| **Concrete deck over the theatre** — 414 SF of LiteDeck + cast cap | **$6,300–10,700** | 0.7% / 0.6% | premium over I-joists |
| **all seven** | **$195,200–$375,000** | **21.3% / 19.8%** | |

Method: ablation — delete the feature's elements from the *resolved* model, re-run
`bill_of_materials` + `estimate_costs`, diff the bid total; where something has to stand where
the feature stood, the replacement is costed off named `prices.toml` rows and subtracted.
Percentages are against the 2026-08-31 baseline; the underlying deltas except the attic were
struck against a base within 1.3% of $941k, so read them −3% (see *Method*).

---

## 1 — Cost cutting

Every live scope or spec change, one row each. **These do not add up** — see *Interactions*.

| change | saves (bid total) | how priced | DIY? | interacts with | cost of the cut |
|---|---|---|---|---|---|
| **Attic level → trussed cold attic + blown R-60** | **$69,100–133,900** | built 2026-08-29, truss-rate corrected | no | **swallows the attic-windows row; shrinks roof, girt, ccSPF, mineral wool** | A redesign of the building's whole upper third. Cheapest sf in the house at $59–114/sf against $159–331 per conditioned sf house-wide. Moves the air barrier to a penetrated ceiling plane |
| ⏳ Driveway apron + walks — defer to a later contract | $18,000–44,000 | allowance | part | — | Nothing, if the drive can be gravel for a season |
| Excavation: reuse spoil on site instead of hauling off | $10,000–25,000 | allowance note | no | court-shortening | Nothing. Depends entirely on the daylight-side regrade |
| **Shorten the sunken court, 28' → 16' N–S** | **$9,700–16,600** | arithmetic | no | garden-footing engineering; the boom pump | 12' of garden. Still a 19x16 = 304 sf court |
| Roofs (house + garage, 2,186 SF) → architectural asphalt | $9,700–18,200<br>+$1,500–3,000 snow retention | built | no | attic | 50-yr service life → 25–30, on the PV substrate. 48 flashed penetrations instead of zero |
| ⏳ Raised garden apron — defer | $8,700–17,400 | ablation | yes | **its own premium-table row — the same money** | Nothing. A landscape contract, let any spring |
| Windows → vinyl or entry fibreglass, same U-0.25 | $6,500–11,000 | `[openings]` note | no | **imports: windows — do not sum** | Frame material and warranty |
| **Single-tier girt on 5.5" blocks** (deletes the inner SPF tier) | $6,400–10,300 | arithmetic | no | attic; both ccSPF rows | A new failure mode: the block **cantilevers**, so bending and screw prying become the design case. **Not without an engineer** |
| Concrete deck over the theatre → I-joists | $6,300–10,700 | arithmetic | no | **its own premium-table row — the same money** | Acoustic isolation over `RM-B-PLAY-N`; `FH-M-DINING`'s in-slab embed; the thermal mass under the south glazing |
| **Delete the 5 discretionary attic windows** | **$5,016–10,114** | **built, re-measured** | no | attic | The south-gable mirror about x=18' and the north pair. **`WIN-A-S-JUL-W` is not one of the five** — see *Do not reopen* |
| **Exterior CI: 4" → 2.5" of ccSPF** | **$5,422–7,996** | **built, re-measured** | no | attic; single-tier girt | R-41.4 card / ≈R-38.2 honest → ≈R-32. The one row that spends measurable building performance. **Weigh it last** |
| Plant room → an ordinary second-floor room | $5,300–10,400 | arithmetic | part | — | This is *delete the plant room*, not cheapen it: the liner is what lets the room run at 75 °F / 70% RH |
| Trim, stool and apron package simplified | $5,000–13,000 | allowance | **yes** | DIY trim + paint | Drywall-return jambs at 45 windows and a flat paint-grade base. **Not "go trimless"** — a hidden-jamb door is a 4–5x premium |
| Exterior-wall cavity mineral wool → fibreglass | $4,900–7,200 | arithmetic | **yes** | attic | ~0.8 whole-wall R. **Verify the row split first** — the acoustic, sauna and plant walls must not be touched |
| Oak floor + red-oak stair treads → LVP / carpet | $4,300–6,800 | `[floor_finishes]` | **yes** | DIY floor finishes | 351 SF of oak is under most Twin Cities sand-and-finish minimums anyway |
| ccSPF 4" → 3.0" — the one-step version of the row above | $3,296–4,682 | **built, re-measured** | no | supersedes/halves the 2.5" row | Deletes band C only; the block geometry does not move |
| Exterior guards: Trex Signature → builder-grade aluminium | $3,700–5,700 | `[railings]` | no | — | Both guards or neither, or the two levels stop matching |
| Balcony aluminium plank → walkable PVC membrane | $3,400–10,000 | `[sheet_goods]`, **low confidence** | no | inside the sunken-garden premium | Dry-below is not optional: this deck is the porch's roof. **Call Versadeck (651) 356-1870 first** |
| Ishtar-gate glazed brick veneer → plain brick, or delete | $3,300–7,100 | ablation | no | inside the sunken-garden premium | The whole Ishtar-Gate composition and the one place the garden has colour |
| Engineer the garden footing base and stone bed | $3,200–8,000 | arithmetic | no | court-shortening | Nothing, if it stamps |
| HVAC System 3 folded into the multi-zone | $3,000–5,400 | ablation + line-set allowance | no | — | The Sapphire's true VFD soft-start is what lets that zone run off the battery |
| Refrigerator columns → one 36" side-by-side | $3,000–4,500 | arithmetic | no | — | All-fridge/all-freezer capacity, and 21" of layout |
| Garage stem → frost-protected shallow foundation | $2,000–3,900 | arithmetic | no | — | The option of ever leaving the garage unheated |
| Elm tudor posts → paint/stain-grade species | $1,300–4,500 | `[timber]` | no | — | 6-1/8" S4S elm is not a purchasable article. **Get a quote first** — the low end is only $2,006 |
| Trimless interior door → standard cased prehung | $915–2,045 | `[openings]` | no | trim simplification | A 3-trade sequencing item; the frame is set before drywall, so it cannot be reversed later |
| Fabricated box gutter → seamless K-style | $600–1,400 | `[edge_trim]` | no | — | Plus $150–400/ea for the conductor heads a box gutter needs, which are not in the estimate |

⏳ **Deferrable to a later contract** — outside the weather envelope, not trapped behind
finished work. Deferring both is **$26,700–61,400** out of the first build, and it comes back.

**Narrow the house, 36'x36' → 30'x36'** (a 40' lot). **$51,000–97,000**, band
$40,000–130,000 — `arithmetic`, every takeoff section split area / perimeter / fixed and
scaled by 0.833 / 0.917. **Not built.** It is not a cost row, it is a lot-fit row: it takes
16.7% of the floor (5,001 → 4,168 conditioned sf) to buy 5% of the money, and **$/sf goes UP
13–14%**, $159–330 → $180–376. Perimeter falls half as fast as area (wall per floor sf
+10%), and `placeables`, `allowances`, `openings` and `wall_structure` barely move — the
house is one of four structures and only it shrinks. Not counted: 18' clear spans become
~14', so the 3,556 LF of 11-7/8" I-joist could drop a depth. **The garage (24' wide) and the
sunken garden (~21' outer) already fit a 30' band** — only the house has to move.

**Unpriced, therefore not a row:** French doors → sliders where the swing is not needed
(~15–25% of $7,000–15,800, needs a quote). It lives in `plans/TODO.md` until it has a number.

---

## 2 — Self-perform (DIY)

Labour only. Nothing here changes scope, the spec, or a single element in the model — which
is why it is a separate table: **it is a different kind of decision.** Explicit labour in the
estimate is **$308,666–$625,505**, with a further **$149,439–$380,492** merged (installed,
split unknown) — together 55–60% of the bid.

**Three rows are `installed` with no declared split, so their labour half cannot be
separated.** They quote the **whole installed figure** and are an **upper bound**, never an
invented 55/45 — `cost_model.split_by_basis` exists precisely so a merged number is never
divided.

| scope | prices.toml row(s) | labour low | labour high | skill | risk |
|---|---|---:|---:|---|---|
| Drywall hang + finish | `envelope_layers.gwb`, `.gwb-x`, `sheet_goods.gwb` | 20,189 | 35,082 | high finish skill, low tool cost | A level-5 ceiling under raking light is where amateurs lose. Sequencing gate for every trade after it |
| Interior + trim paint | `envelope_layers.latex-paint`, `.latex-paint-accent`, `[allowances] paint-trim-and-doors` | 16,621 | 33,140 | low | Time, not skill. It is the last trade and it is on the critical path to occupancy |
| Trim and baseboard | `[allowances] finish-interior-trim-and-baseboard` | 7,800 | 13,000 | medium–high | Interacts with the trim-simplification row in table 1; do not price both |
| Floor finishes | `[floor_finishes]` — all 10 rows | 11,409 | 23,214 | mixed | Oak sand-and-finish and heat-welded sheet vinyl are **not** DIY; LVP, carpet and rubber are |
| Cavity insulation | `mineral-wool`, `fiberglass`, `fiberglass-r19`, `blown-fiberglass` | 4,619 | 9,082 | low | **Batts only.** The 3,094.9 SF of ccSPF is a licensed sprayer and is not on this table |
| Floor prep / self-levelling | `[allowances] finish-floor-prep-and-self-levelling` | *4,401* | *11,453* | medium | **merged — upper bound** |
| Tile backer + waterproofing | `[allowances] finish-tile-backer-and-waterproofing` | *4,000* | *8,000* | high | **merged — upper bound.** A failed shower pan is the most expensive DIY mistake in a house |
| Site protection, final clean, dumpsters | `[allowances] site-protection-final-clean-and-dumpsters` | *3,500* | *8,500* | none | **merged — upper bound.** Dumpster haul is a real invoice either way |
| Closet shelving and rod | `[allowances] cabinet-closet-shelving-and-rod` | *600* | *1,500* | low | **merged — upper bound** |
| **splittable labour, all five** | | **60,638** | **113,518** | | |
| **merged rows, whole installed figure** | | *13,145* | *31,512* | | upper bound |

**Realistic ceiling if every row were self-performed: ~$74,000–$145,000.** Treat the top of
that as fiction — nobody self-performs drywall, paint, trim, floors and insulation on a
5,000 sf house without pushing the schedule past a winter, which turns on the $8,000–21,000
cold-weather line under *Not in the estimate*.

**And it is not on top of the GC fee.** `[markup]` is already zero. Self-performing buys the
sub's labour, not a general contractor's margin — that was never in this total.

---

## 3 — Upgrades (money out)

Small, and this is where a cost-cutting row goes once it is taken.

| upgrade | costs | note |
|---|---|---|
| Roof ice barrier: eave-only → full-deck high-temp | $12,400–27,300 | Neither is in the estimate today. Code wants eave-only; standing seam runs hot enough that full-deck is normal practice |
| **Foundation: damp-proofing → full adhered membrane** | **$0–14,650** | New 2026-08-30. $0.00–12.50/SF over the 1,010.2 SF below-grade face, through the ladder. The code-minimum coat is a **modelled layer and already bought**, which is why the low end is zero; this row is the **upgrade delta only**. Dimple board is the middle rung at ~$2–5/SF |
| Garage: full-height ICF walls (stem extended to plate) | $3,540–7,940 net | Before unquantified framing-removal savings. Needs new engine work for the truss-to-ICF sill |
| Garage: CMU block + exterior Zip-R | $11,200–15,600 net | Counterintuitively **dearer** than full ICF, with a bigger engine gap. Right answer only if wall weight matters more than dollars |
| Breezeway glazing: 16 mm polycarb → aluminium storefront + IGU | $6,700–13,300 | Glazier minimum and shop drawings alone are $1,500–3,500 on a 79 SF job |
| Main-floor concrete: sealer → genuine polish | $3,300–4,400 | `sealed-concrete` is a densifier, not a polish — a separate specialty contract |
| Oak flooring in the LVP rooms, 1,272 SF | $2,500–4,500 | Living, study, 2F hall, two upstairs baths. Oak in a bathroom is a maintenance call |
| Breezeway roof: polycarb panel → stock fixed skylight | $950–2,225 | A Velux FCM 4646 + curb kit. A *custom* sloped unit is 2–4x this |
| **PV array + battery, if deferred and then taken** | $34,500–69,500 | Deferrable **only if** the roof, conduit and service are built for it now — `ED-A-PV-JB`, the attic riser, the backup subpanel and 12 S-5! PVKIT clamps are ~$1,500–3,500 of insurance |

---

## 4 — Imports: direct-from-factory sourcing

Researched 2026-08-31, **not built and not modelled.** Nothing in `prices.toml` or the model
was edited for this section — an import decision changes who sells the article, not what the
article is. Every row is priced against the **material half** of the `prices.toml` section it
would replace; the labour half is local either way. One row (`finish-door-hardware`) is a
**merged** allowance with no declared split, so its "at risk" figure is the whole installed
lump and its saving is the narrower of the seven judgements here.

**Consolidators.** Two verified Foshan one-stop suppliers cover exactly these categories with
container consolidation across them, which is what makes a single-house import viable at all:
**George Group** (georgebuildings.com — founded 2006, seven Foshan plants, ~100,000 m²,
aluminium windows, wooden doors, cabinets, stairs, flooring, sanitary ware, lighting) and
**Dechaab Group** (dechaabgroup.com — windows, doors, cabinets, wardrobes, curtain wall,
railings, stairs, with sourcing-to-warranty service). A one-house order is 1–2 x 40 HQ, and
**one container that mixes seven categories is the whole economic argument** — any single
category alone does not fill one.

**Landed cost is 1.3–1.7x FOB** (ex-factory + inland haulage + ocean freight + destination
charges + duty + drayage). Ocean freight is $3,500–6,500 per 40 HQ to LA/Long Beach plus
inland to the Twin Cities; production is 25–35 days and the sailing 30–45 more.

| category | vs prices.toml section | material at risk | landed saving | lead time | gating risk |
|---|---|---:|---:|---|---|
| **Windows** | `[openings]` `WT-*` material | $24,800–47,160 | **$3,700–14,100** | 4–6 months | **See below. This is a gate, not a footnote** |
| Exterior + interior doors | `[openings]` `DT-*` material | $14,800–39,130 | $3,700–15,700 | 4–6 months | Fire-rated garage-to-dwelling separation needs a listed assembly; the overhead door is a US spec |
| Plumbing fixtures | `[placeables]` `FX-*` material | $10,290–30,960 | $3,100–13,900 | 3–5 months | **cUPC/IAPMO listing is mandatory in MN.** Unlisted fixtures fail plumbing inspection |
| Flooring | `[floor_finishes]` goods material | $8,054–19,621 | $1,600–6,900 | 3–5 months | CARB Phase 2 / TSCA Title VI formaldehyde certification; Lacey Act declaration on wood |
| Cabinets | `[placeables]` `CASE-*` material | $5,005–13,040 | $1,500–6,500 | 4–6 months | TSCA Title VI. Published builder savings are 30–50%; this is the strongest row on the table |
| Hinges and handles | `[allowances] finish-door-hardware` | $2,940–10,710 *(merged)* | $1,000–5,300 | 3–4 months | None material, but the line is **merged** — the saving is on the hardware, not the hanging, and the split is a judgement not a number. Buy 15% spare |
| Lighting | — | **nothing to save** | **$0** | — | The estimate carries no luminaire price rows at all; 306 fixtures move `placeables` by $285–695. **The money is in `[conductors]`, which no fixture decision touches** |
| **total, if all seven** | | | **$14,600–62,400** | | |

**The windows row is gated on labelling, and unlabelled product cannot be permitted.**
Minnesota requires the U-factor and SHGC to come from an **NFRC label on the product** (or
fall to the IECC default table, which this design cannot pass), and requires an air-
infiltration rate **≤0.3 cfm/sf** for windows and ≤0.5 for swinging doors, **tested to NFRC 400
or AAMA/WDMA/CSA 101/I.S.2/A440 by an accredited independent laboratory and labelled by the
manufacturer.** Ask for the NFRC CPD number before anything else; a factory that cannot
produce one is selling a window this house cannot install.

**Two more things that move the windows number and are not in it.** 2026 tariffs are roughly
**25.3% on uPVC and 77.7% on aluminium** window frames — aluminium is effectively off the
table, and the row above assumes uPVC/composite. And the three plant-room units are U-0.14
Alpen/Zola class because `building_science.glazing_dew_point` **FAILs** them at U-0.25; they
are not an import candidate at any price.

**Do not sum this row with cost-cutting "Windows → vinyl or entry fibreglass"
($6,500–11,000).** They are the same money reached two ways.

*Sources, 2026-08-31:* [georgebuildings.com](https://georgebuildings.com/) ·
[dechaabgroup.com](https://dechaabgroup.com/) ·
[landed-cost and 2026 tariff guide](https://georgefurnitureglobal.com/importing-windows-from-china-landed-cost-guide/) ·
[freight and container costs](https://owlsourcing.com/china-windows-and-doors/) ·
[builder savings on imported cabinets](https://foshansourcing.com/how-to-buy-and-import-kitchen-cabinets-from-china-2/) ·
[MN residential energy code, ch. 4 RE](https://up.codes/viewer/minnesota/mn-energy-code-2015/chapter/RE_4/re-residential-energy-efficiency).
Rates and duties are **research, not quotes** — get a customs broker to review the
classification before any order is confirmed, which is the one step every source agrees on.

---

## 5 — Interactions: the anti-summation map

**Decide the attic first.** Everything else is priced against the house as drawn.

- **The attic row swallows the attic-windows row whole** and shrinks the roof,
  the cladding, the mineral-wool and both ccSPF rows — a smaller house has less wall, less
  roof and less continuous insulation.
- **The two ccSPF rows are the same row at two depths.** 4"→3.0" ($3,296–4,682) is the first
  step; 4"→2.5" ($5,422–7,996) is that step plus a second. Take one.
- **The single-tier girt row and the ccSPF rows overlap** — both are about the same 4" of foam
  and the frame standing in it.
- **The raised-garden and theatre-deck rows are the same money as their premium-table twins.**
  Deferring the garden and deleting the deck premium are one decision each, not two.
- **The balcony-plank row is inside the sunken-garden number**, and so is the brick veneer.
- **Court-shortening and garden-footing engineering overlap** — both take money out of the
  same cast-concrete package.
- **The imports windows row and cost-cutting "windows → vinyl" are the same money.**
- **Trim/stool/apron in table 1 and the trim and paint rows in table 2 are the same scope** priced two ways:
  one buys less trim, the other buys the same trim and installs it yourself.
- **The garage rows are independent of everything** and of each other.

With the attic **kept**, and counting each independent row once, the cost-cutting table is
roughly **$70,000–140,000** permanently cheaper plus **$26,700–61,400** deferred. With the
attic **taken**, do not add the attic row to the rest — re-measure.

---

## 6 — Do not reopen

These have each been proposed, priced and killed. The reason is the row.

| idea | why not |
|---|---|
| **Wall-hung toilet in RM-M-BATH1** | It is a saving that **cannot be taken.** MN's governing front clearance is **UPC 402.5's 24"**, not IRC P2705.1's 21". At 61.98" x 44.24" between finish faces, a 28"-deep standard bowl leaves no strip anywhere for the lav in any orientation. The 19.3" wall-hung bowl is what makes the room work |
| **Delete the sunken court** (as opposed to shortening it) | `D-B-PATIO` and `WIN-B-SAUNA` are the **only exterior openings in the entire basement.** Without the court the theatre, gym, sauna and shop are windowless with no direct exit |
| **PBR the roof under the PV array** | $7,400–14,500, and the worst trade in the file. `S-5-PVKIT` clamps to a seam with **zero penetrations**; on PBR, 48 attachments pierce the water plane *and* the vent mat that is the assembly's only drying path, under a $15.8–27.5k array — plus ~3,700 gaskets at 20–30 yr life on a 4:12 roof with no overhang |
| **Interior vapour retarder — poly, or a smart membrane as an upgrade** | **Deleted from the estimate 2026-08-30.** The interior paint *is* the Class III retarder, because the cavity carries 4" of exterior ccSPF. Poly or a membrane inboard of that traps the stud bay between two low-perm layers with no drying direction. Not an upgrade — an assembly failure |
| **`WIN-A-S-JUL-W`** | The studio's only **R310 emergency escape opening.** Deleting all six attic windows FAILs `code.R310_egress` and nothing else — confirmed by build. It is why the deletable set is five, not six |
| **Garage ICF stem → conventional formed frost wall** | **Withdrawn 2026-08-29.** The $9,400–16,900 was arithmetic on a double bill (`icf-eps` billing the blocks a second time). The stem now prices inside every published band and the honest saving is ~$1,000–1,800, for R-22 → R-10 on the garage's only below-grade thermal layer |
| **House-wall cladding → PBR** | **Taken 2026-08-26.** −$14,043 / −$30,279 on `subtotal_net`. It is in the baseline; it is not still available |
| **Swap the ccSPF for rigid board** | Reclaimed polyiso looks like −$6,900/−$8,600, then a WRB comes back, the ACH50 target loses the layer that made it nearly automatic, the wall drops R-2, and through-foam furring puts it **back under IRC R703.15's 4" foam limit** — the exact provision the current wood-to-wood detail was engineered to escape |
| **Outer girt KDAT → plain SPF** | $2,968–4,452, settled the other way in the engineering note's Risks. That girt is a horizontal ledge inside the vent gap that wet-cycles for the life of the wall |
| **Buy a proprietary clip-and-rail standoff** | $14,700–29,300 for clip and rail *alone*, against $16,028–26,118 for the entire current standoff **including window bucks.** Costs more and reintroduces a through-foam fastener |
| **"Simplify" `RB-HOUSE` to one 36' stick** | The one place a well-meant simplification would put a crane on the job: 317 lb per ply landing at +32', against 106 lb as three 12-footers. Identical lineal feet, zero offcut |
| **Precast the 16" garden column** | 1,656 lb. The disposable fibre tube is a wheelbarrow of concrete; precast is a crane pick and a delivery problem |
| **Post bases: ABU66SS stainless → ZMAX** | ~$950–1,750, and the wrong $1,000 to save — one detail nobody re-does without jacking the structure |
| **Basement interior 12" walls → 2x6 stud** | Ablation −$4,177/−$6,979, but the framing, gypsum and paint cost $2,100–3,700 back. Net ~$2,100–3,300, and it retires two-storey bearing lines and their footings |
| **`struct-1-plywood` → OSB on the exterior walls** | $700–1,930 over 3,512 SF. Not worth the shear-value argument |
| **16" stud spacing "because standing seam needs it"** | The premise is dead and was always wrong: cladding is `pbr-panel-26` on horizontal girts and no fastener has ever landed on a stud. **IRC Table R602.3(5)** is the real bound and it stops the main storey dead |

---

## 7 — Not in the estimate

Upward exposures, so the tables above are not read as a complete picture.

| exposure | amount | why it is not a row |
|---|---:|---|
| **GC overhead and profit** | $100,000–375,000 | `[markup]` is zero **by owner decision.** Not an omission — a decision. Turning it on also taxes and contingencies the fee |
| **Cold-weather concrete protection** | $8,000–21,000 | Carried at **$0** on a summer-pour bet, May–Oct. If the pour lands Nov–Apr this is 10–25% of the whole concrete package. **The most expensive line in the file that a calendar can turn on** |
| **Telehandler or ladder conveyor** | $700–1,000/day, $3,500–5,000/month | The roof plane is the largest material-handling problem in the project: 4:12, 26' eave, 32' ridge, **zero overhang to stage on**, and the polyiso is a sail. Also the 26'-long PBR wall panels |
| **Boom pump, several days** | inside `concrete-pumping` $4,600–7,800 — probably short | Forced by the sunken garden: 29.2 cy of 10' wall at the bottom of a 9' court, 5" from the house. A chute cannot reach it |
| **Second sprayer mobilisation** | $500–1,500 | 2,448 LF of girt course and 45 openings' jamb posts go on **between** the two foam passes. No sprayer waits through that |
| **Rebar, ~5 tons** | $10,000–18,000 | Still inside the `[concrete]` and `[wall_structure]` $/cy rates, and **the "nothing enforces that" is fixed as of 2026-09-03**: `[rebar_inclusive]` in `prices.toml` declares which rates still contain their steel, and pricing `[reinforcement]` against one that does is a hard error naming both sides (`cli/price_file._check_rebar_not_double_billed`). `takeoff/reinforcement.py` bills the tonnage NOW, priced at nothing, so the quantity can be read against this row before any rate is cut — 1.74 tons of it so far, from the sunken-garden court alone; the rest of the house is not yet migrated to `ReinforcementSpec` |
| Excavation has no quantity | the weakest number in the file | $24,000–55,000 as a lump, so no design change can ever demonstrate a saving against it. The sunken garden alone implies 200–250 cy of extra cut |
| Garden footings priced as strips | ~$1,500–2,100 under | The `footing` rate derives from a 16"x8" strip, then covers the garden's 84"-wide reinforced bases — 20.9 of 33.25 cy |
| Garage slab may be thin | +$343–1,810 | 3-1/2" carrying vehicle loads through MN freeze–thaw; 4"–5" is normal |
| Garden slab priced as interior | ~$460–930 under | "The cheapest slab there is — no perimeter forming, no edge finish, no exposure", applied to exposed exterior slab at the bottom of a 9' court |
| `FT-BOOKCASE-32-90` unpriced | small, x4 | An owner price, not one to invent |
| Branch-circuit conductor measurement gap | named, not sized | `[conductors]` bills 4,218 conductor-feet off `mean_pull_ft`, a conservative proxy. Fix it in `takeoff/electrical.py`; **do not restore the retired lump beside the section** |

**One steel-vs-wood note, for any comparison in this file that is re-read:** 2026 tariffs put
steel at 50% (25% on derivatives) while Canadian softwood duties are provisionally cut to
~24.8%. The basis has moved toward wood since these rates were struck.

---

## Open questions

| # | question | what it moves |
|---|---|---|
| 1 | **Is the attic staying?** The largest single decision left in the model | $69,100–133,900 |
| 2 | **The PV allowance is retired but the array is not quoted.** `[solar_modules]` prices 5,280 W at $3.00–5.20/W. One quote settles the band | $6,000–22,000 |
| 3 | One roofing quote | ~$15,500–34,000 of boundary |
| 4 | Is 761 LF the right drain-tile length, or should it be one perimeter ring? | $3,000–7,200 |
| 5 | The balcony plank: one call to Versadeck, (651) 356-1870, turns the least certain row in the file into a real one | $3,400–10,000 |
| 6 | Cladding: is this a metal-clad house on all four elevations, or on the two that are seen? | $10,000–29,000 |
| 7 | Will a PBR supplier accept 7/16" Zip-R as substrate in writing? Ask for the nail-strip already specified on the same call | $736–2,391, and a spec risk that already exists |

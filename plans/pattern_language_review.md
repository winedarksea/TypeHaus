# Pattern-language design review — Catlin house

Started 2026-08-29. A review, not a design pass: the house is at 0 FAIL, the permit set
prints, and the bid total is **$931,549–$1,934,801**. What follows is a **ranked, priced list
of style and liveability gaps**, measured against Christopher Alexander's patterns **95–253**
(`docs/design_patterns.md`) — the 160 at building and construction scale. Patterns 1–94 are
town- and region-scale and are out of scope for one house on one lot.

**Nothing here is decided.** This file follows the convention `plans/cost-options.md` states:
an idea lives in a plans doc until it has a number, then moves to the priced menu. Rows
marked **TAKE NOW** carry a *measured* number; rows marked **DEFER** or **NOTE ONLY** carry a
researched estimate and say so.

## Rules this review was held to

- **~$5,000 per item**, not per pass. The list totals far more; the owner picks.
- **Long-term durability and a high-performance envelope are the top priorities.** Anything
  that degrades the envelope without paying for itself was dropped, not ranked.
- **`houses/catlin/CLAUDE.md` records the reasoning for nearly every choice in this house.**
  A finding that contradicts it had to overturn it on evidence or be dropped. Several were
  dropped. One (Pattern 234, the cladding) was tested hard and the repo **won** — see below.
- Every dollar figure is either **measured** (`haus takeoff` before/after, said so) or
  **researched** with a cited basis (said so). Nothing is asserted.

## Method

Five themed reviews ran in parallel — light and glazing; entry, circulation and outdoor
rooms; rooms, intimacy and built-ins; construction, materials and durability; site, garden
and approach — each reading the live model, `houses/catlin/CLAUDE.md`, and the plan source,
and each required to research cold-climate precedent, product durability and 2026 Twin
Cities pricing rather than assert numbers. Their findings were then deduplicated, checked
against the repo's own recorded reasoning, and — for the top candidates — **re-measured by
building the change in a throwaway copy of the house and diffing `haus takeoff`.**

## At a glance

**MEASURED** = built in a throwaway copy of the house and diffed with `haus takeoff`; every one
held 0 FAIL. **Researched** = a cited external basis, no bid.

| | item | patterns | cost | basis |
|---|---|---|---|---|
| **A1** | Snow retention on RF-HOUSE's east eave — *and a check that cannot see the hazard* | 160, 168 | $3,500–6,000 | researched |
| **A2** | Sound-isolate the three bedrooms from each other (STC 36 → 52) | 198 | **+$875–1,570** | MEASURED |
| **A3** | Tile the mudroom | 248 | **+$33–360** | MEASURED |
| **A4** | Acetylated jamb posts + copper-naphthenate end seal | 207 | $1,100–2,100 | researched |
| **A5** | An exterior stair off the porch — the first route to the ground | 168, 120 | $2,600–4,200 | researched |
| **G1** | East living row WT-2748 → WT-2764 | 192, 128 | **+$269–562** | MEASURED |
| **G2** | Main-floor south sill to 18" — *takes the great room off IRC Exception 1* | 222, 180, 202 | $540–1,900 | researched\* |
| **G3** | Orientation-tuned glass (the product exists; the plant-room note is backwards) | 128 | $0–800 | researched |
| **G4** | Dimmers in the bedrooms and studies (99 of 128 fixtures are on a plain toggle) | 252, 135 | $407–996 | MEASURED count |
| **B1** | The garden apron's base course has **negative embedment** | 173 | $700–1,500 | verified defect |
| **B2** | Oak in the second-floor hall | 233 | **+$1,943–2,695** | MEASURED |
| **B3** | A front door you can actually walk to | 110, 112, 130 | $5,550–8,250 | researched |
| **B4** | Natural wood where people are (52 SF in the whole house) | 250, 249 | $2,000–2,500 | researched |
| **B5** | A window seat that is actually a window seat | 202, 180, 222 | $1,100–2,700 | researched |
| **G5** | A window for the gym (324 sf, 0.0 sf of glazing) | 192 | $1,024–2,049 | researched |
| **G6** | An interior lite for `RM-M-STUDY` | 194 | $515–1,055 | researched |
| **G7** | Light on two sides for the primary bedroom — *rank last* | 159 | $690–1,405 | researched |

\* G2's cost is researched rather than measured **because the measurement was wrong and the
report says so**: a minted `WT-3062` came back unpriced, so the units it replaced dropped out
of the bill and the total fell by ~$3,000. That apparent saving is an artifact.

**The three biggest findings, if you read nothing else:**

1. **A1 — 36 feet of unretained 6:12 standing seam sheds 23 feet onto the house's only
   at-grade sitting space, and `structural.sliding_snow` is structurally incapable of seeing
   it.** All six snow guards are on the garage.
2. **G1 + G2 together take `RM-M-LIVING` — the 748 sf great room — off IRC Exception 1
   outright**, measured at 60.3 sf against 59.8 required, with 0 FAIL, no new opening and no
   facade column moved.
3. **A2 — the two walls between the three children's bedrooms are the weakest partition in the
   house (STC 36), while a wall nine feet away with a *bathroom* on its far side is STC 52.**
   Two tokens, measured at +$875–1,570, zero envelope impact.

---

# 1. Already satisfied — do not spend here

This house is further along the pattern language than most. Named so the report is not read
as a list of failures, and so nobody "improves" something that is already right.

- **95 Building Complex** — four separate structures (house, garage, sunken-garden/porch/
  balcony, breezeway) rather than one monolith. The strongest single move in the project.
- **111 Half-Hidden Garden / 173 Garden Wall** — the sunken court, 19'-0" x 19'-4" clear
  inside 9'-10" walls, with the Ishtar-Gate brick face. Textbook, and untouched by this
  report.
- **113 Car Connection** — sheltered end to end, garage → five risers → breezeway → mudroom.
  Three proposals below are shaped specifically to leave it alone.
- **133 Staircase as a Stage** — the 20'-4" daylit stair void with its chandelier.
- **167 Six-Foot Balcony** — porch and balcony both **8'-8"** deep. Satisfied outright.
- **163 Outdoor Room** — the porch is roofed, fanned, lit, wired and curtained on two bays.
- **197 Thick Walls / 211 Thickening the Outer Walls / 223 Deep Reveals** — 13-7/8" wall,
  ~9-3/8" return, 39 oak stools derived via `MillworkStandard`, the 12-3/4" bookcase wall.
- **204 Secret Place / 179 (private)** — `D-A-STUDY` as a flush Murphy bookcase door hidden
  in the attic study's run.
- **136/137 Couple's and Children's Realms** — four sleeping realms on four levels.
- **139 Farmhouse Kitchen** — 747.6 sf holding kitchen, an 8-place table and the sitting
  group in one room. **129, 131, 132, 127** all likewise satisfied; the main floor has no
  corridor at all.
- **235 Soft Inside Walls**, **236 Windows Which Open Wide** (40 of 43 casement or awning),
  **225 Frames as Thickened Edges**, **224 Low Doorway**, **205 Structure Follows Social
  Spaces**, **209 Roof Layout**, **200/201 shelves**, **193 Half-Open Wall**, **196 Corner
  Doors**, **189 Dressing Rooms**, **144 Bathing Room**, **145 Bulk Storage**,
  **141 A Room of One's Own**, **142 Sequence of Sitting Spaces**.
- **138 Sleeping to the East** — satisfied for **three of five bedrooms** (BED1/2/3 all take
  their light off the east wall). Worth naming because it was not designed for.
- **154 Teenager's Cottage / 155 Old Age Cottage** — `RM-A-STUDIO`, the 356 sf attic guest
  studio with its own bath and wet bar, very nearly satisfies both.
- **157 Home Workshop** — `RM-B-WORKSHOP`, 197 sf.
- **195 Staircase Volume**, **214 Root Foundations**, **215 Ground Floor Slab** (the house
  stands **2'-10"** out of grade, well past Alexander's 6–9 inches).

## Two findings the review tested and *rejected*

**Pattern 234, Lapped Outside Walls — the 2026-08-26 PBR cladding decision survives.**
The review was pointed at flat exposed-fastener panel as a likely gap against Alexander's
lapped, weathering, repairable skin. It is not one, and the swap moved the house *toward*
the pattern:
1. Alexander's real criterion is repair in small patches. A face-screwed PBR sheet comes off
   **one panel at a time with a driver**; a mechanically-seamed field does not.
2. **The screws never reach the water plane.** They land in the KDAT outer girt, outboard of
   the 1/2" vent gap, outboard of the 4" ccSPF face that *is* the water plane
   (`notes/catlin_truss_engineering.md` §5, §9). Every "exposed fasteners leak" citation
   describes a *barrier* roof where the screw pierces the water plane. This is a rainscreen;
   the 25–30 year re-screw is maintenance, not a leak path.
3. Over 50 years: re-screw at $2.50–4.50/SF incl. removal over 3,092.6 SF plus the house's
   own $3,000–8,000 lift row is **$5,000–15,000 once or twice**, against the **$15,594–32,108
   one-time saving** already booked in `plans/pbr-cladding-savings-report.md`. A wash at
   worst, a win at best. **Do not revisit the cladding.**
The one honest debit is already written down: 26 ga oil-cans more visibly than 24 ga — and
26 ga is the *recommended* gauge for PBR expected to outlast 20–25 years.

**Pattern 250, Warm Colors — the base colour is not the problem.** `#f0ede6` is LRV ~85 at
hue ~43°, a *warm* high-LRV white, which is what the literature prescribes for cool north
light under 2700K LED. Repainting was proposed and dropped. The real gap is that Alexander's
250 lists **natural wood first**, and the house has 52 SF of it on interior walls — all of it
in a 19 sf windowless office. That is item **B4** below.

---

# 2. The ranked list

Ranked by value per dollar, with durability and envelope impact weighted first.

## Tier A — TAKE NOW

Measured, cheap, zero envelope risk, and each one closes a gap the model can point at.

### A1. Snow retention on RF-HOUSE's east eave — and a check that cannot see the hazard
**Patterns 160 Building Edge, 168 Connection to the Earth. $3,500–6,000, researched.**

**The most important finding in this review.** `RF-HOUSE` is a 6:12 gable with
`ridge_direction="y"` and `overhang=ft(0)` (`plan/storeys/attic.py:514-521`), so **the eaves
are the east and west footprint edges**, and `params/roof_trim.py` hangs a 6" box gutter
tight to the wall plane on both. The eave stands roughly **23' above grade**. Ground snow is
**50 psf** (MN Rules 1303.1700).

**There is no snow retention anywhere on `RF-HOUSE`.** All six `CN-G-SNOW-*` ColorGard units
are on `RF-GARAGE` (`plan/storeys/garage.py:496-499`, `connects=("RF-GARAGE",)`), protecting
the breezeway canopy. Meanwhile `plan/site.py:168` puts the `patio` hardscape at
**x 36'–42', y 10'–22' — directly under the east eave** — and calls it the house's only
at-grade sitting space.

**And `structural.sliding_snow` is structurally blind to it.** `_lower_surfaces`
([`checks/structural/snow.py:91-113`](packages/engine/src/typehaus/checks/structural/snow.py#L91))
enumerates **only lower roofs and horizontal `GlazingPanel`s**. An `ImperviousSurface`, a
slab, a deck or a door is invisible to it. At a ~23' drop the check's own `_MAX_REACH_FT` is
15.0 — the entire patio, and nine feet of yard beyond it, sit inside that band. The house's
754 PASS / 0 FAIL is silent here **because the check has no eyes, not because the roof is
safe.**

- **Change:** a continuous S-5! ColorGard row on the **east** eave, full 36'-0"
  (`Connector(kind=SNOW_GUARD, connects=("RF-HOUSE",))`, written longhand — the editable
  dialect allows no comprehensions). **Do not localise it over the patio**: a partial row
  shears the pack diagonally, which is worse than none. Quote the west eave at the same time.
  Row count and seam spacing at Pg = 50 psf stay the manufacturer's calculation, exactly as
  `garage.py:485` already says.
- **Authorable:** yes, `Connector` with `ConnectorKind.SNOW_GUARD`, on the garage precedent.
- **Cost:** $3,500–6,000 for the east eave (36 lf of rail, ~27 clamps at one per 16" seam),
  scaled from the house's own `prices.toml:563` ColorGard row plus roof-access labour at 23'.
  **Basis is a per-unit connector price, not a lineal quote — a fabricator will move it.**
- **Durability:** this *is* the durability item. Clamps are set-screw on the seam — **no
  penetration of the standing seam** — and the row also protects the drip-edge → box-gutter →
  downspout lap chain that `test_catlin_eave_water.py` pins.
- **Not authored here, deliberately.** Two reasons: the spacing is an engineering calculation
  this review will not invent, and **teaching `_lower_surfaces` to see hardscape would very
  likely turn the house's headline from 0 FAIL to 1 FAIL and block `haus print`.** That is
  the right thing to do *after* the guards are specified, not before. Both halves are the
  owner's call.

### A2. Sound-isolate the three bedrooms from each other
**Pattern 198 Closets Between Rooms. MEASURED: +$875 – $1,570 on the bid total. 0 FAIL.**

`W-S-BD1` and `W-S-BD2` ([`second.py:268-271`](houses/catlin/plan/storeys/second.py#L268))
separate `RM-S-BED1 / BED2 / BED3` and are `INT_2X4_PARTITION` — **STC 36**
(`library/assemblies.py:239-249`, a lab transcription). Nine feet away on the same storey,
`W-S-SN1` / `W-S-SN2` are `INT_2X4_STAGGERED_DOUBLE_GWB` — **STC 52** — and the comment says
why: *"a wall whose far face carries a vanity and a bath is the one the sleeper hears
through."* **A wall with a sleeper on *both* faces has a strictly stronger claim, and it got
the weakest assembly in the house.** Nothing will ever flag this: no check in the engine
reads `Assembly.stc`, and `preferences.toml` has no acoustic key.

- **Change:** two tokens — `assembly="INT_2X4_PARTITION"` → `"INT_2X4_STAGGERED_DOUBLE_GWB"`
  on both walls. The name is already imported and already used on this storey. No new
  assembly, no new price row, no library change. **STC 36 → 52.**
- **Measured:** built in a throwaway copy of the house. `haus check` **755 pass / 0 fail / 97
  unknown — identical to baseline.** Bid total $931,549 → $932,424.
- **The cost, stated honestly, is depth.** Each wall goes **8.25" → 11.5"** in the resolved
  model (+3.25"), so BED2 loses 3.25" and BED1/BED3 lose 1.63" each. **The model will not show
  this**: `Room.clear_face` sits on the wall *axis*, not the finish face, so the reported
  areas (119.7 / 124.3 / 129.0 sf) do not move at all. BED1 is already the tight one — its
  north walk zone goes 18" → ~16.4".
- **Cheaper on depth if that matters:** a house-local `CATLIN_INT_2X4_BEDROOM` at two layers
  of 5/8" each side (**STC 45**, +1.25" total), following the `CATLIN_INT_2X6_BRG_PLUMBING`
  precedent. Do **not** use resilient channel: one screw into the stud behind kills it, and
  nobody will ever measure it after drywall.
- **Durability / envelope:** zero, both directions. Interior partitions cross no control
  layer. This is the cleanest $/value in the report precisely because it touches nothing the
  house is good at.

### A3. Tile the mudroom
**Pattern 248 Soft Tile and Brick. MEASURED: +$33 – $360 on the bid total. 0 FAIL.**

`RM-M-MUDROOM` (58.8 sf) and `RM-M-MUD-CLOSET` (18.8 sf) — the room **every person in this
house enters through**, in Minnesota, with salt and snow — are heat-welded homogeneous sheet
vinyl with a 6" integral flash cove, billed at **$10–20/SF** (`prices.toml:1548`). That is a
*laboratory floor* specification, priced above tile, on the front hall. Meanwhile the whole
fired-clay interior of a 5,001 sf house is **119 SF of tile in two bathrooms**, which
`prices.toml:1529` notes is under any tile sub's minimum ("expect a LUMP of $1,500–2,500").

- **Change:** `floor_finish="vinyl-sheet"` → `"tile"` on both rooms (unglazed quarry or
  through-body porcelain). One word each. Break the washable spine at `D-M-MUD`, a real door,
  and leave the laundry/bath/hall band as authored.
- **Measured:** 755 pass / **0 fail**, bid total $931,549 → $931,582. **Effectively free** —
  and it takes the tile scope 119 → 197 SF, sharing a mobilisation lump the house is already
  paying, so the marginal tile foot is cheaper than the rate row implies.
- **Durability:** unglazed quarry is the material Alexander names — it wears, it shows use,
  and a chip exposes the same body (the through-body logic the repo already applied to the
  garage brick). **50–100 years** against sheet vinyl's 10–20, which cannot be spot-repaired.
- **Two honest costs:** it is a rigid finish over an 18'-0" I-joist span, so it needs an
  uncoupling membrane (the detail `RM-M-BATH2` already carries); and you trade the seamless
  flash-cove tray for grout, which is exactly what the 2026-08-25 decision was buying. **That
  decision is defensible and this is an owner's preference, not a defect** — which is why it
  is a report row and not an authored change.

### A4. Acetylated jamb posts and head/sill courses
**Pattern 207 Good Materials. $1,100–2,100, researched. The durability item.**

`notes/catlin_truss_engineering.md` §9 already identifies the two most exposed, least
inspectable pieces of wood in the envelope and **parked the fix**: brush-treat field-cut ends
with copper naphthenate as they are cut (KDAT's .15 pcf retention does not follow the saw,
and a 2,432 LF field course puts a fresh untreated cut at every butt), and use an acetylated
wood for the **jamb posts and head/sill courses at openings, ~192 LF**.

Those 192 LF sit **behind the window returns, outboard of the vent gap, on a wall with no
WRB** — the foam is the water plane and the girt frame is on the wet side of it. They are the
only wood in this house that wet-cycles for its whole life and **cannot be reached again
without removing cladding and windows.** Nothing in the plan source applies either upgrade.

- **Cost:** Accoya 2x4 at ~$7–11/LF against KDAT at ~$1.30–2.20/LF = **$5–9/LF x 192 LF =
  $960–1,730**, plus $150–400 of copper naphthenate. **A national retail spread, not a Twin
  Cities quote — escalate before ordering.**
- **Durability:** a published **50-year above-ground warranty** against rot and decay, and
  dimensional stabilisation that matters for a jamb post carrying a window flange and a sill
  pan. This buys the least-accessible wood in the envelope a service life matching the
  concrete, for **~0.15% of construction cost.** It also drops the DB-coating requirement on
  every fastener landing in it. **The single best durability dollar in this report.**

### A5. An exterior stair off the porch — the house's first route to its own ground
**Patterns 168 Connection to the Earth, 120 Paths and Goals. $2,600–4,200, researched.**

`grep "Stair(" houses/catlin/` returns exactly four flights — `ST-B2M`, `ST-M2S`, `ST-S2A`,
`ST-G-SERVICE` — and **not one is outdoors.** Grade is -2'-10"; every pedestrian exterior door
lands at 0'-0" on a deck, or at -9'-1" inside a walled court. Verified against the model: the
only at-grade opening in the entire complex is `D-G-OVERHEAD`, a 16'-0" vehicle door.

So the great room's outdoor room — a 19'-0" x 8'-8" porch — is a **balcony you can only
leave by going back indoors**, and `D-M-BALC`'s 60" French pair opens into the air.

- **Change:** five 7" risers off the porch's **east** edge (the rise is only **2'-11"**:
  porch walking surface +0'-1" to yard -2'-10"), landing on a frost pad clear of `FT-SG-E1`.
  Composite treads matching the porch plank; fascia-mount aluminium rail matching
  `RL-SG-PORCH` so the guard reads as one line.
- **Authorable:** yes — `Stair` with `base_elevation`/`top_elevation` and **no
  `floor_opening`**, which is exactly the `ST-G-SERVICE` precedent (2026-08-22). Verified in
  `model/spatial.py:78-96`. Authoring it as a real `Stair` rather than as slabs is what gets
  it graded by `structural.stair_riser_uniformity` and `code.R311_7_8_handrail`.
- **Durability:** one frost pad at 42" in a waxed fibre tube so heaving soil cannot grip the
  shaft. Through-bolt the stringer top into cast concrete with stainless, with a sill gasket
  isolating the KDAT. **Gapped composite treads, not the balcony's dry-below aluminium**, so
  meltwater drains rather than glazing over.
- **Caveat:** the yard grade immediately outside `W-SG-E1` is not a modelled spot elevation,
  so the riser count may go to six.

## Tier B — DEFER (right, but a real trade or a real survey stands in front of it)

### B1. The raised-garden apron's base course has negative embedment
**Pattern 173 Garden Wall. $700–1,500 (regrade) or $7,350–14,700 (rebuild).**

**Verified against the model.** `Site.grade` is **-0.8636 m = -2'-10"**; `W-RG-BLOCK`,
`W-RG-WEST`, `W-RG-EAST` and the two balcony returns all resolve at **z0 = -2'-6"**. The base
course of a dry-stacked SRW retaining **3'-0" of fill stands 4" clear of finished grade**,
with its 6" levelling pad two-thirds exposed.

`params/raised_garden.py` **asserted the opposite** — "its base sits at -2'-6", and -2'-6" is
now finished grade" — which was true for three days. Grade went to -2'-10" on 2026-08-21 and
the apron did not follow; nothing ties `BASE` to `SITE_GRADE` and nothing checks the two
against each other. `unbalanced_fill` still states 3'-0", so **the model believes this wall
retains three feet and knows nothing holds its toe.**

A segmental retaining wall is a *flexible* system and is correctly designed here to ride 42"
of frost without a frost footing — but it depends absolutely on base-course embedment to
resist sliding and on a buried pad to resist erosion and frost lensing. With 55–60 freeze-thaw
cycles a winter, an unembedded base course walks outward.

- **Recommended fix (cheap):** raise finished grade against the outboard face by 10"–12" over
  a ~4' bench, feathering out 8'–10'. Three or four new `SpotElevation`s in the editable
  `plan/site.py`; those stations sit 20'+ from the house, outside `code.R401_3_grading`'s 10'
  band. **$700–1,500**, and **free if the real survey reshapes this yard anyway** — which is
  why it is DEFER and not TAKE NOW.
- **Done in this pass:** the false paragraph is corrected in
  [`params/raised_garden.py`](houses/catlin/params/raised_garden.py), with the defect, the two
  options and their costs written into the docstring so the next reader is not misled.
- **Everything else on that terrace waits for this.** Do not add saturated soil behind a wall
  whose toe is unembedded.

### B2. Oak in the second-floor hall
**Pattern 233 Floor Surface. MEASURED: +$1,943 – $2,695 on the bid total. 0 FAIL.**

2,491 SF of the finished floor is petrochemical sheet goods with a 10–25 year life and no
refinish path, against **357 SF of oak** — a 7:1 ratio. The specific incoherence:
`ST-M2S` delivers **13 red-oak treads onto an oak landing**, which lands in `RM-S-HALL` —
**206.8 sf of LVP** — off which `RM-S-STUDY2` (oak) opens and from which `ST-S2A`'s 15 oak
treads leave. **Oak stair → vinyl hall → oak room, twice, in fifteen feet.**

- **Change:** `RM-S-HALL.floor_finish="lvp"` → `"oak"`, one word,
  [`second.py:710`](houses/catlin/plan/storeys/second.py#L710).
- **Measured:** LVP 766 → 538 SF, oak 357 → 585 SF; 755 pass / **0 fail**; bid total
  $931,549 → $933,492. **The takeoff overstates it**, and the price file says so itself
  (`prices.toml:1508`): 351 SF is under the Twin Cities sand-and-finish minimum, so a
  $1,200–1,800 mobilisation plus a trip per coat is **already sunk**. Amortised over 585 SF
  instead of 357 that is $2.13–3.19/SF instead of $3.36–5.04 on oak the house is already
  buying — credit that back and the true delta is meaningfully under the measured $1,943.
- **Durability:** site-finished solid oak is **50–100+ years**, resanded every 10–20. LVP is
  10–20 and **never refinishable** — once the wear layer is gone the floor is landfill. Over
  50 years the hall is 2–4 LVP replacements against zero.
- **The family oak is not a discount — and that is the useful finding.** 207 SF needs ~290 bf
  of 4/4 rough: $580 at ~$2/sf, plus kiln ($87–290) and T&G milling ($218–580) = **$885–1,450,
  i.e. $4.28–7.00/SF** — the *same* as the retail material band already in `prices.toml`. Buy
  it for **width, character and provenance** (Pattern 253), not for savings: it is 12–18"
  wide-plank white oak at 2-1/4" strip prices, a material that installs at $18–25/SF here.
  Take the big logs **quartersawn** — roughly half the face movement of plainsawn.
- **Do NOT convert the great room's LVP field.** `params/main_deck.py:160-166` pins the number
  the whole mixed-deck detail rests on: the 6 mm plank surface lands at **+0.95"–0.99"** and
  the `SL-M-DECK` cap tops at **+15/16"**, flush within 1/64". 3/4" solid oak tops at **+1.5"**
  — a **9/16" step** in a walking path, reverting the 2026-08-23 T-moulding to a reducer. If
  the owner wants oak there, this is the one place milling your own logs solves a *geometry*
  problem: 3/8" solid T&G landing the surface on the cap.

### B3. A front door you can actually walk to
**Patterns 110 Main Entrance, 112 Entrance Transition, 130 Entrance Room. $5,550–8,250.**

A guest with no garage remote cannot reach a door of this house. The pedestrian route is:
open a 16'-0" overhead door → cross 570.9 sf of unconditioned garage → up five risers →
`D-G-SERVICE` → a 4'-0" glazed tube → `D-M-ENTRY`. The breezeway is closed on **both** flanks
by `GL-BW-WALL-W/-E` (`params/breezeway.py:463,469`). And `plan/site.py:160` authors a
32 sf `ImperviousSurface` called **"front walk"** in the 4'-0½" canyon between the two
buildings, **serving no door and ten feet east of the one it is named for.**

**The door is on the correct wall and must not move.** `params/roof_trim.py` states it: the
ridge runs N–S, so the **north and south walls are rakes** — they shed nothing — while east
and west are the unretained eaves of item A1. On this roof the north wall is the only
elevation where a door is not standing under an avalanche. **The gap is the approach, not the
door.**

- **Change:** an 8'-0" x 8'-0" entry court at the garage's SE corner running west as a 4'-0"
  walk down the slot (replacing the misplaced "front walk"), plus a **36" outswing full-lite
  door in the breezeway's east wall** onto a landing, five risers matching `ST-G-SERVICE`'s,
  and a 36" guard. Outswing keeps a third swing arc out of a 4'x4' vestibule and seals against
  wind pressure.
- **Authorable:** yes throughout — `ImperviousSurface`, `Door`, `Stair`, `Footing.bottom_elevation`.
- **Envelope: untouched.** The new door goes into the **breezeway**, a freestanding
  unconditioned polycarbonate structure on isolated piers. The house's pressure boundary, its
  4" of spray foam and ACH50 = 1.0 are unaffected; the only two envelope penetrations on this
  route already exist and do not move.
- **A permit risk worth taking to the AHJ before framing.** IRC R311.2 requires the egress
  door to open "into a public way or to a yard or court that opens to a public way." Neither
  `D-M-ENTRY` (onto a breezeway deck) nor `D-M-BALC` (onto a railed porch, no stair) does.
  **The engine has no rule for it** — `code.R311_door_width` and `code.R311_2_door_height`
  grade width and height only — which is why 0 FAIL is silent here. Item A5's stair is the
  cheapest thing that answers it.

### B4. Natural wood where people are
**Patterns 250 Warm Colors, 249 Ornament. $2,000–2,500 with owner oak.**

Measured interior wood on walls: **52 SF of walnut T&G**
([`main.py:1175`](houses/catlin/plan/storeys/main.py#L1175)) — in `RM-M-STUDY`, a **19.3 sf
office**. That is the entire wood-wall inventory of a 5,001 sf house, against **8,231 SF of
latex paint** and one 78.2 SF accent wall in a child's bedroom. The 747 sf great room — the
one room Pattern 250 is written for — has **0 SF of wood on its walls**, ~14 recessed
downlights and an off-white ceiling. And every ornament programme in this house is *outdoors*
(the Ishtar-Gate register bands, the Copper Penny ridge cap, the Roman-coursed brick).

- **Change:** a 3'-6" white-oak T&G wainscot on the great room's seating and dining end, off
  the owner's stock. `WallPaneling` takes `walls=(...)` to restrict scope and `spans`/`offset`
  for windows, so this is precise rather than all-or-nothing. Add one `Material(tag="oak-tg")`
  beside the existing `oak-stool` / `oak-tread` / `oak-shelf-*` rows.
- **Cost:** ~210 SF. Retail $10–24/SF = $2,100–5,040; off owner stock ~$763–1,250 material
  plus ~$6/SF install = **$2,000–2,500 all-in.**
- **Durability:** the most durable interior wall surface available — takes chair backs,
  vacuums and dogs for 50+ years where painted Level-4 gypsum wants a repaint every 7–10.
- **Envelope:** none **if `replaces_wall_finish=False`**, so the band sits over the painted
  gypsum and the Class III latex vapour retarder is untouched. **Do not set it True on an
  exterior wall without re-running the condensation gate.**

### B5. A window seat that is actually a window seat
**Patterns 202 Built-in Seats, 180 Window Place, 222 Low Sill. $1,100–2,700.**

`FURN-M-MUD-BENCH` is a **freestanding** 36"x18"x18" catalog piece centred on `WIN-M-MUD` — a
`WT-1424-FIX` at **sill 4'-0"**. **Sill 48" minus seat 18" = 30" of blank wall between where
you sit and where you can see out.** The unit is 2.33 sf of glass at head height: it lights
the bench without giving it a view. Three patterns land on this one element and all three
miss. House-wide, the lowest sill anywhere is 24" (attic gable, over unfinished storage);
**every habitable main- and second-floor sill is 30"–48".** No window in a 5,001 sf house can
be sat in.

- **Change:** retype `WIN-M-MUD` to a **14x48 fixed unit at sill 2'-0"**. Head stays at 6'-0";
  glass goes 2.33 → 4.67 sf; the sill lands **6" above the bench top**. Then replace the
  catalog bench with a house-local 4'-0" built-in on the `plan/furniture_types.py` precedent.
- **This clears the RO ladder outright, because the ladder caps WIDTH and this change is
  entirely in HEIGHT.** 14" is `max_window_ro_unbroken_in` — no stud broken, no header, no
  jacks — so the 27" bearing cap on `W-M-W1` is never approached. Only the rough sill drops
  and two cripples come out. **`WT-1448` already exists** (`main.py:155`) and is already
  priced (`prices.toml:2218`); a `WT-1448-FIX` follows the `WT-1424-FIX` / `WT-3660-FIX`
  precedent. R308.4 does not bite: 4.67 sf pane (< 9 sf), bottom edge 24" AFF (> 18").
- **Free with the retype:** `MW-STANDARD` scopes `CATLIN_EXT_2X6`, so the 1-1/2" 8/4 oak stool
  re-derives at the new sill. A ~9-3/8" oak return 6" above the seat **is** the ledge — the
  deep reveal the house already paid for finally does something a body touches.
- **Envelope:** +2.33 sf of glass. ΔUA = 0.53 Btu/h·°F ≈ **45 Btu/h** at the 85 °F design ΔT,
  against a house whose ERV alone moves 210 cfm. Noise. Keeping it **fixed** is the
  envelope-positive choice at ACH50 = 1.0.

## Tier C — NOTE ONLY

- **C1. Trees (Pattern 171).** Zero trees on ~13,300 sf of open ground, on a house with **zero
  overhang** where a tree is the only summer shading device available at any price. But the
  side yards are 32' wall-to-line, and canopy guidance is *plant at ≥ mature height* — **a
  50–70' tree physically cannot stand 40' from this foundation in a side yard.** The only
  place one fits is the north/front yard (40.5' deep). Proposed: one *Gymnocladus dioicus*
  'True North' (UMN introduction, seedless) north at ≥30'; two *Ostrya virginiana* west at
  20–25'; one *Amelanchier* × *grandiflora* 'Autumn Brilliance' by the east patio.
  **Nothing within 25' of `W-SG-W2/E2/S`** — those are 12" cantilever-T stems retaining ~7'-1"
  with an occupied court behind them. **~$4,500 for all four**, installed, from a vendor 15 mi
  away. Survey-dependent. Not authorable — no `Tree` class exists.
- **C2. A vegetable garden in ground that is already built (177).** The apron and the
  sunken-garden walls already enclose a **3'-0" wide, ~203 sf U-shaped terrace of retained
  fill** — an ideal reach-in bed with a wall on each side, and nothing says what is in it.
  **$1,400–2,900** for mix, edging and one drip zone. Three hard rules: **item B1 first**;
  drip on a timer, never spray; and **annuals only, no woody roots** — the inboard face is the
  back of a cast retaining wall and the outboard face is dry-stacked block.
- **C3. Climbing plants — the answer on the house wall is NO, at any price (246).**
  Self-clinging climbers are negatively phototropic: shoot tips grow *into* gaps in cladding,
  roof edges and gutters. This wall offers every one — exposed fasteners on a ~12" grid, a
  1/2" vent gap that is the assembly's **only drying path** outboard of a spray foam with no
  WRB above it, zero overhang with no fascia break to stop a shoot, and a box gutter.
  Removing a mature vine later means unscrewing panels. **A freestanding trellis 4'-0" clear
  of any wall** is the only responsible form — $3,500–5,500 frost-footed, with *Clematis*
  'Jackmanii' (pruning group 3: cut to 12" every spring, so it can never reach anything).
- **C4. An entry canopy hung off the GARAGE, not the house (112).** A 4'-0" x 6'-0"
  `GlazingPanel` in the breezeway's own polycarbonate, on PE-stamped brackets into `W-G-S`.
  This is the move that does not fight `params/roof_trim.py`: the garage already has a 16"
  overhang, a fascia and eave trim; the house's flush zero-overhang skin is never touched.
  **$1,800–3,200**, and it needs the Pg = 50 psf stamp, not a stock bracket. Note the garage's
  **south eave sheds into the slot for its whole 24'**, and the ColorGard row covers only
  x 1'-4"..8'-0" — extend it to x 24'-0" ($1,600–3,000) or the new walk is under unretained
  snow.
- **C5. Exterior lighting (102).** Three exterior luminaires in the whole complex, **two of
  them on the south porch nobody arrives at**. One repeated `ED-T-LT-SCONCE-EXT` at each
  arrival door, full-cutoff and ≤3000K so `advisory.dark_sky_lighting` stays PASS.
  **$600–1,200 — the softest number in this report**, an allowance rather than a quote.
- **C6. Outdoor seating (241).** 109 `Furniture` elements; outdoors there are four curtain
  rods and a workbench. **Zero chairs, benches or tables.** The right spot is already built:
  the south-facing porch, roofed, fanned, lit, wired and curtained on two bays. Two lounge
  chairs and a low table, **$800–2,500** — the highest value-per-dollar item in the review,
  and a purchase, not a trade line. Author with **no `room=`** (the porch is not a `Room`;
  naming the room behind the wall buys an advisory and nothing else). **Do not put seats on
  the east patio until A1 is bought.**
- **C7. A sitting wall and bench at the new entry (242/243).** The one low wall on the site
  tops at +0'-6", which is **3'-4" above grade** — 20" too tall to sit on, on the wrong side of
  the house, and unreachable. In the new court: an 8'-0" **cast** wall at 18" with a
  drip-kerfed cap, on a 42" footing, with an oak slab bench. **$2,300–4,000.** Cast, not SRW —
  a dry-stacked seat wall rides heave and walks. **Leave a 2" isolation joint at the garage
  stem**, the discipline `params/sunken_garden.py` already uses at the house footing.
- **C8. Ceiling height variety (190) — and an engine trap worth writing down.**
  Basement, main and second all carry `default_ceiling_height=ft(9)`; the only `Room.ceiling`
  authored anywhere is `FollowRoof` on the four attic rooms, and there are exactly **two
  `Soffit`s in the building**, both mechanical. **`Room.ceiling` as a `Length` is read by
  exactly one consumer** — `code.R305`'s ceiling-height rule. `resolve/ceilings.py::_pieces`
  derives the plane from the deck region and never consults it, so **authoring
  `Room.ceiling=ft(8)` on a main- or second-floor room changes the report and produces no
  geometry.** On those storeys the lever is `Soffit`, and only `Soffit`. One 10" band over the
  dining table (~31 LF, **$800–1,500**) does Pattern 182's enclosure and 190's contrast at
  once. **Test it loose first** — hang the pendant at the intended height for a week; unlike
  everything else here it is not reversible after the drywall.
- **C9. The Fire, answered honestly (181).** The house is not fireless: `EQ-M-FIREPLACE` is a
  **4'-0" linear electric unit** on its own 20 A circuit. Two things are wrong with it, and
  neither is the absence of combustion. It is specified as a **$300–900 big-box insert**,
  which reads flat at the 11 ft where the sofa is; and **nothing faces it** — the sofa
  addresses the media console on the *south* wall while the fire sits 10'-1" east, off-axis,
  with its top at 28" AFF. **Combustion was researched and rejected**, and the rejection
  should be recorded as a decision rather than left as a default: MN Rules 1346.0501 *does*
  permit a sealed closed-combustion appliance without additional makeup air, but this house
  has no gas service, and every flue route penetrates either a hot roof of 6" polyiso under a
  zero-overhang continuous skin or **4" of continuous foam that is the water plane with no WRB
  to lap to.** Instead: buy a unit that reads as fire at 11 feet (**+$600–2,600**), raise the
  mount from 7" to 18–24" so the flame sits at seated eye level, give it a dark `WallPaneling`
  surround (**$1,400–3,000**), and turn the seats toward it.
- **C10. Sitting circle (185).** 747.6 sf of common room, **three seats** — one 84" sofa —
  against eight sleeping places. The house already knows how to do this and did it in the
  basement, where a sectional is authored with `rotation=deg(180)` explicitly *"to make it
  face the screen."* Two armchairs, **$800–3,000**, zero construction cost. Pairs with C9.
- **C11. Glazed interior doors for borrowed light (237).** `DT-INT-SWING30-GLAZED` exists and
  is used twice. `RM-B-PLAY-N` (324 sf) and `RM-B-GYM` (324 sf) have **zero glazing** and pass
  R303.1 only under Exception 1. A retype moves nothing (see the direct change below);
  **$150–450/door**. Specify an obscure/reeded lite in the basement and a **laminated** lite in
  the media room, since the acoustic cost is real.
- **C12. Half-inch trim (240).** Interior trim is **two lump allowances with no specification**
  — $12,000–20,000 plus $8,000–18,000 — over stock described as "finger-joint or MDF against
  the carpenter", while `plan/millwork.py` specifies the winners in detail. The molder
  argument is correct for *profiled* casing and is not overturned; but a **square-edged S4S
  board** needs no knife grind — it is a rip and a plane, which is what the owner's supply and
  `MillworkStandard` already do for every shelf. Specify flat 1x6 S4S oak base and 1x4 casing
  in the oak rooms, **drawn from the existing allowance** — true incremental **$600–1,200**.
  Not modellable: `prices.toml:3398` says baseboard follows room perimeter and no BOM table
  reports it.
- **C13. Alcoves (179), child caves (203), different chairs (251), stair seats (125),
  wild garden (172), paving with cracks (247), site repair (104).** Real but low-value or
  survey-dependent; each is a line in the register, not a row here. **247 is worth one note:**
  keep Alexander's *intent* (no mortar, open joints, water goes through) and reject his
  *construction* — stone laid directly on soil heaves out of level in one Minnesota season.
  6"–8" of open-graded angular base over geotextile is **more** freeze-durable than mortared
  flagstone, and at $15–32/SF dry-laid the **marginal cost over plain concrete is ~$0.**

## Deliberately dropped

- **Repainting for warmth (250)** — the base colour is already a warm high-LRV white. See §1.
- **Changing the cladding (234)** — the PBR decision survives on its own evidence. See §1.
- **A greenhouse (175)** — an attached glass box against a wall whose water, air, vapour and
  thermal plane is a single seamless foam with no WRB, under a zero-overhang roof, at −15 °F
  design. Every attachment penetrates the one control layer, at $30k+. **Two 4'x8' cold frames
  on the terrace, $400–1,200, do the growing half with no envelope contact.**
- **Moving the front door to the street side (110)** — the north wall is a rake and the only
  weather-correct elevation for a door on this roof. The design already made this call.
- **A literal roof garden (118)** — impossible on a hot roof with 6" polyiso and zero overhang;
  the 8'-8" balcony is the pattern's substance and it is built.
- **A radiant mat under the great room's seating group (230)** — proposed at $2,000–4,300, but
  it is **mutually exclusive with nail-down oak there**, and `advisory.floor_finish_over_radiant`
  flags a mat under LVP. Pick one; do not buy both.
- **An arch in `W-SG-S` for a view out of the court (115)** — that wall is
  `lateral_support="unsupported"` at 7.09' of retained height, which R404.4 makes **engineered**
  and which `structural.foundation_unbalanced_fill` already reports UNKNOWN for exactly that
  reason. Cutting a hole re-opens the consultant's scope. Noted, not priced.

## A documentation drift worth fixing

`brief.md` lists the house style as **"arched concrete garden walls."** `params/arches.py:7`
says: *"No current caller: the sunken garden's arched front cross-wall was replaced by a
column and two beams (2026-08-18)."* Verified — the module has **zero callers**. The only
arches left in the complex are the two **brick reveals** on `W-B-BRICK`'s Ishtar-Gate face,
and those are on the *house* wall, not the garden walls. The brief is the owner's statement of
intent, so this report flags the drift rather than editing it: either the brief should say
"arched brick gate wall", or the arches should come back.

---

# 3. Direct changes made in this pass

Four edits. Every one is a **correction** — a bug, a false pass, a stale fact, or a room the
plan already named — not a design preference. Every design preference above stayed a report
row, because the owner picks.

## 3.1 `_room_windows` credited interior glazing as emergency egress — fixed

**The blocker the review plan identified, confirmed and closed.**
[`_common.py:61`](packages/engine/src/typehaus/checks/code/mn_residential/_common.py#L61)
selected a room's windows **by proximity to the room boundary and nothing else** — it never
tested whether the host wall was exterior. Both `code.R303_1_light_and_ventilation` and
**`code.R310_egress`** consumed it, so **an interior transom or borrowed-light sash of
adequate size in a bedroom would have been credited as that bedroom's emergency escape
opening.** R310.1's subject is an opening "opening directly into a public way, yard or court";
a window into the hallway reaches none of them.

- `_room_windows` takes a new `exterior_only` keyword, filtering on `_wall_is_exterior` — the
  helper that already lived in the same module and derives the answer from what has modeled
  space on each side, never from a tag prefix.
- **`code.R310_egress` passes it `True`**, and so does `_required_escape_openings`, which
  feeds `code.R310_2_3_window_well` — a window the escape rule cannot credit is not one the
  well rule should be sizing a well for.
- **`code.R303_1` deliberately leaves it `False`**, and the reason is written into the
  docstring rather than left to be rediscovered: that rule adjudicates its own Exception 1 and
  reports the shortfall in the finding text, so the conservative default there is to keep
  counting what the room can see. **The day this house authors real borrowed-light glazing,
  that choice is worth revisiting on its own evidence.**

**Behaviour on catlin is unchanged** — all six credited egress windows were already on
exterior walls — which is exactly the desired result: the hole is closed and nothing regressed.

**Two tests, and the pair was proven to catch the bug.** A two-sided synthetic pair in
`test_code_coverage_expansion.py` follows that file's one-field-moved discipline: the same
7.5 sf opening passes when the far side of its host wall is outdoors and **fails when a room
is put there**. Flipping the flag back to `False` makes the negative test fail; restoring it
makes it pass. Alongside it, `test_catlin_contract_m3.py` gains a standing invariant that
re-derives, from the resolved model, that each of the six windows `code.R310_egress` credits
sits on a wall with modeled space on one side only.

## 3.2 `D-M-STUDY` is glazed — the house's one windowless habitable room gets daylight

**MEASURED: +$261 – $503 on the bid total. 0 FAIL, and one more rule now grades.**

`RM-M-STUDY` is **19.3 sf of `office` occupancy with no window at all** — the only habitable
room in the house with none — and it cleared R303.1 solely on Exception 1's electric-light
substitute (1500 lm over 19 sf = 37 fc). Its door hosts on `W-M-C3`, the centre bearing wall,
whose far side is `RM-M-LIVING`.

Retyped `DT-INT-SWING30` → **`DT-INT-SWING30-GLAZED`**, a type that already existed and was
already hung for the same reason at `D-S-PLANT`. **A retype, not a move:** same 2'-6" x 6'-8"
leaf, same RO, same jamb pack, same bearing header, same swing, same uid. The type already
carries `tempered=True`, which R308.4.1 requires of glazing in a door as a property of the
product rather than of its location — and `code.R308_4_safety_glazing` now grades it, taking
the encoded rule count 851 → 852 and the passes 754 → 755.

**Stated honestly: this buys the ROOM daylight; it does not buy the CHECK anything.**
`_room_windows` skips doors, so R303.1 still reports 0.0 sf of glazing here and still passes
the room on Exception 1. That is the correct accounting — R303.1's 8% is measured on glazing
to the outdoors, and a borrowed-light leaf is not that. `office` is not a sleeping occupancy,
so there is no R310 exposure, and since §3.1 there could not be one anyway.

## 3.3 `params/raised_garden.py` asserted a fact that stopped being true on 2026-08-21

See **B1**. The docstring claimed the apron's base sat *at* finished grade. It sits **4"
above** it. The paragraph and its ASCII section are corrected to state the defect, why it
matters (base-course embedment is what resists sliding on a flexible SRW), why it is
**deliberately not fixed in code** (the cheap remedy is a `plan/site.py` regrade, not a change
to this module), and what each remedy costs. No geometry moved.

---

# 4. Verification

Run after every change, on the working tree:

- `.venv/bin/haus build houses/catlin` — **exit 0.**
- `.venv/bin/haus check houses/catlin` — **755 pass, 0 FAIL, 97 not evaluable of 852 rules.**
  Baseline was 754 / 0 / 97 of 851; the extra rule is `code.R308_4_safety_glazing` on the
  newly glazed study door. **The reference house is held to a clean report, and it is clean.**
- `.venv/bin/haus print houses/catlin` — **exit 0.** The permit set still prints, which matters
  because `haus print` gates on UNKNOWN as well as FAIL, and the UNKNOWN count did not move.
- `.venv/bin/python -m pytest packages/engine/tests` — **exit 0**, full suite green, redirected
  to a file and the code read directly (a pipe would report `tail`'s status).
- `.venv/bin/haus render --view plan` and `--view elevation`, **and the PNGs were looked at.**
  This is where the shading analysis in §5 came from — it is not visible in any number.
- `.venv/bin/haus takeoff houses/catlin` before and after: **$931,288–$1,934,298 →
  $931,549–$1,934,801.**
- `ruff` and `mypy` on the four changed engine/test files, diffed against `git show HEAD:` of
  each: **zero new findings.** (`scripts/verify.sh --fast` still exits 1 on the repo's
  pre-existing, unrelated ruff backlog — every other stage passes.)
- `.venv/bin/haus build --inspect houses/catlin` — **exit 0**, the editable dialect lints.

Tier A and B candidates were measured the same way, by **building each change in a throwaway
copy of the house inside the repo and diffing the takeoff**, then deleting the copy. Every one
held 0 FAIL.

---

# 5. Measured facts this review produced

Numbers that did not exist before, recorded here because several of the rows above depend on
them and because the next reader should not have to re-derive them.

## The south face is three facades, not one

The review plan called this "the zero-overhang / porch-shading asymmetry." Measured, off the
resolved model and the south elevation render:

- Balcony beam soffit (`BM-SG-BLW/BLC/BLE`) at **z = 8.46 ft** above the main floor.
- Southmost extent **y = -9.71 ft**, i.e. it projects **9.5 ft** from the house's south face.
- Balcony guard tops at 13.60–13.70 ft (a 90-baluster picket, partly transparent).
- MSP noon solar altitude at lat 44.9778: **Dec 21 = 21.6°**, equinox 45.0°, **Jun 21 = 68.5°**.

**Main-floor south windows** (`WIN-M-BED-S1/S2`, `WIN-M-LIV-S1` — 30.0 sf, sill 2'-8", head
6'-8"):
- Dec 21 noon: the shadow drops 9.5 × tan(21.6°) = 3.76 ft below the soffit → sun line at
  z 4.70 ft. Sunlit = **2.03 ft of a 4.0 ft window: 51% at the winter peak.**
- Equinox noon: sun line at −1.04 ft. **Fully shaded.** Jun 21: fully shaded.

**Second-floor south** (`WIN-S-STUDY1/2`, `WIN-S-PLANT1/2`): nothing above them but the
house's own zero-overhang eave. **Fully unshaded, all year.**
**Attic south** (`WIN-A-S-JUL-E/W`, `WIN-A-S2/S3`): unshaded.

That is textbook passive-solar overhang behaviour at the main floor, and aggressive: that
glass sees direct sun only around midwinter, and only half of it. **Any orientation-tuned
glazing or shading recommendation has to be written per storey, not per facade.**

## What the engine can and cannot say about SHGC

`checks/building_science/energy_load.py:317-322` is the **only** consumer of SHGC in the tree:
`window_solar += area × shgc × orientation_weight × 164.0`, weighted N 0.25 / E 0.70 / S 1.00 /
W 0.85 — and it feeds **cooling only**. **There is no solar heating credit anywhere in the
engine.**

Measured baseline (`model.json` `building_science.energy`): heating **30,866 Btu/h**; cooling
**17,355 Btu/h** (1.446 tons), of which **10,965 Btu/h — 63% — is window solar gain**; windows
in the thermal envelope 247.2 sf at UA 58.85. WWR **N 1.29 / E 1.78 / S 4.46 / W 2.64 %**.

So raising south SHGC makes the *measured* number worse and shows no measured benefit. Any
claim about winter gain has to be sourced externally, not "measured" — and honestly, at ~20 sf
of unshaded south glass a ΔSHGC of 0.15 is single-digit dollars a year. **If an SHGC retype is
worth doing it is worth doing for winter sun in the room, not for the meter.**

## Daylight: eight rooms on IRC Exception 1, not two

The review plan recorded two. The current tree has **eight**, including **three of the five
bedrooms**:

| room | occupancy | glazing | required |
|---|---|---|---|
| `RM-B-PLAY-N` | media | 0.0 sf | 25.9 sf |
| `RM-B-GYM` | living | 0.0 sf | 25.9 sf |
| **`RM-M-LIVING`** | **living** | **48.4 sf** | **59.8 sf** |
| `RM-M-STUDY` | office | 0.0 sf | 1.5 sf |
| `RM-S-BED1` | bedroom | 9.0 sf | 9.6 sf |
| `RM-S-BED2` | bedroom | 9.0 sf | 9.9 sf |
| `RM-S-BED3` | bedroom | 9.8 sf | 10.3 sf |
| **`RM-A-STUDIO`** | **bedroom** | **13.6 sf** | **28.5 sf** |

**Three of these are deliberate, documented trades, not regressions**, and the report treats
them as such. BED1/BED2 landed on Exception 1 in the WT-2754 → WT-2748 retype
(`second.py:520-536`): *"What the 54\" bought was compliance without the exception; that is
what is spent here, not compliance itself."* BED3 followed on 2026-08-27 to complete a
three-storey 14" east column. Whether those were the right calls at ~0.5 sf of glass apiece is
a fair pattern-language question — it is not a bug report.

`RM-M-LIVING`'s shortfall has a specific cause, and it is also a deliberate facade decision:
**`WIN-M-LIV-S2` (a WT-3048-T, 10 sf) was deleted on 2026-08-24** because *"the south face
reads as a column now, not a pair of pairs"* (`main.py:786-788`). Both south walls are
`StructuralRole.NONBEARING`, so the RO cap is 30" and **height is free** — which is what makes
this remediable at all. The glazing review's ranked answer to it is in §6.

---

# 6. Light, sun and glazing — the ranked slice

Kept as its own section because it is the largest single thread in the review and because two
of its items were **measured**, not estimated.

## G1. The east living row, retyped — MEASURED: +$269 – $562, 0 FAIL

`WIN-M-LIV-E1`, `WIN-M-LIV-E2` and `WIN-M-EAST-MID` all **WT-2748 → WT-2764** (27" x 48" →
27" x 64"). **WT-2764 already exists in the catalog and is already priced**
(`prices.toml:2224`, catalog-only since 2026-08-29 — it is the attic juliets' type). Same 27"
bearing width, so `W-M-E1`'s cap holds; the sill stays 2'-6" over the BESTA run's 29-3/4" top;
the row's 4'-0" / 12'-0" beat, its stud lines and `WIN-M-LIV-E1`'s column with `WIN-S-STUDY3`
are all untouched. The single head line moves 6'-6" → 7'-10", which a 2-2x8 header clears under
the 9'-0" plate with 3-3/4" of cripple — the same arithmetic that disproved the WT-2754 plate
conflict on 2026-08-25.

**Measured in a throwaway copy:** `RM-M-LIVING` glazing **48.4 → 57.4 sf**, 755 pass / **0
fail**, bid total $931,549 → $931,819. Still 2.4 sf short of the 59.8 sf R303.1 wants, so on
its own it does **not** take the room off Exception 1. Pair it with G2.

## G2. Drop the main-floor south sill to 18" — MEASURED: the living room comes off Exception 1

Alexander 222 asks for a sill you can sit by at 12"–14". The lowest sill in this house is 24",
in the attic over unfinished storage; **every habitable main- and second-floor sill is 30"–48".**
Mint **WT-3062** (30" x 62") on the `-T` / `-HP` retype precedent and put `WIN-M-BED-S1`,
`WIN-M-BED-S2` and `WIN-M-LIV-S1` on it at an **18" sill**. The head stays at **6'-8"** — the
door-head line the whole south face and both french doors sit on, which cannot move. The sill
line drops as a *line*, all three together, so the facade stays coherent, and the second floor
keeps 2'-8" — which for the first time gives the south face a vertical gradient (Pattern 221).

Width is capped at 30" and both south walls are `StructuralRole.NONBEARING`
(`main.py:389-395`), so **this is bought entirely in height** — the RO ladder working as
designed.

**Measured, combined with G1:**
- **`RM-M-LIVING`: 60.3 sf glazing / 30.2 sf openable on 748 sf — it PASSES R303.1 on its own
  glazing and comes off IRC Exception 1 outright.**
- `RM-M-BED` improves to 39.3 sf / 19.7 sf.
- **756 pass, 0 fail**, 853 encoded rules.
- **`code.R312_2_window_fall_protection` PASSES** — R312.2 needs a sub-24" sill *and* more than
  72" of drop outside, and the main floor is only 34" out of grade. Verified, not assumed.

**Cost is researched, not measured, and here is why.** `WT-3062` came back **unpriced** —
`haus takeoff` listed `openings:WT-3062` among its unpriced items, so the three WT-3048 units
it replaced simply dropped out of the bill and the total *fell* by ~$3,000. **That apparent
saving is an artifact.** (Worth recording on its own: **minting a `WindowType` without a
`prices.toml` row silently removes it from the takeoff.**) The honest figure: WT-3048 is 78
united inches and WT-3062 is 92, **the same 72–101 UI band**, so no band surcharge applies and
only incremental glass and frame move — **+$120–260 material each**, framing a wash (a taller
RO on a nonbearing wall means *fewer* cripples), tempering optional at a flat $150–250/unit.
**$540–$1,900 for all three.**

**Free with the retype:** `MillworkStandard` re-derives all three oak stools. At an 18" sill
over a 13-7/8" wall with a ~9-3/8" return, that stool **becomes a bench ledge** — Pattern 202
arriving at no cost. And two of the three (`WIN-M-BED-S1` at x 4'-0", `WIN-M-LIV-S1` at
x 32'-8") stand **clear of the balcony deck** (which spans x 7'-6"…28'-6"), so they are the
only unshaded, sittable, ground-floor south windows this house can have.

**Envelope:** +8.75 sf of south glazing = +168 Btu/h at the design ΔT. Against it, south
vertical glass in the upper Midwest returns on the order of 130–160 Btu/sf/day in January, so
on the two unshaded units this is **net-positive over the heating season**. No new opening, no
new flashing, no new buck, no change to the girt mount plane.

## G3. Orientation-tuned glass — the product exists, and the plant room's note is backwards

**Every one of the 43 windows is SHGC 0.35 / VT 0.50, on all four facades.** The three
plant-room `-HP` types carry a comment saying SHGC was *"deliberately unchanged at 0.35: a
triple unit that bought its U with a low SHGC would take the light the room exists for"*
(`main.py:270-277`). **That reasoning is inverted — 0.35 *is* the low-SHGC, light-taking
option.** The conclusion may still be right for that room (U-0.14 and SHGC 0.50 do not co-exist
in a shippable product), but the reason on file is wrong and must not be reused as precedent
for the other nine south units.

**The product is real and mainstream**, which the review plan asked to confirm before anything
was authored: Andersen's 400 Series casement with **Low-E4 PassiveSun w/HeatLock is
NFRC-certified at U 0.26 / SHGC 0.47 / VT 0.58** (the picture version is U 0.23 / SHGC 0.52 /
VT 0.64), and Andersen markets PassiveSun explicitly for the northernmost climate zones. For a
genuine triple at U ≤ 0.25, **Cardinal LoĒ-180 (LoĒ-180 / clear / LoĒ-180) is the standard
high-solar-gain triple**, centre-of-glass **U 0.13–0.18 at SHGC 0.56**; Alpen's Zenith
thin-triple publishes U-0.19 / SHGC 0.48 whole-window. Marvin and Kolbe both glaze with
Cardinal, so this is an order-form line, not a substitution.

- **South, second floor + attic (47.2 sf, permanently unshaded — see §5):** high-solar-gain.
- **East (58.7 sf):** raise **VT**, not SHGC. `vt` is authored on all 21 types and consumed by
  **nothing** in the engine, so it is pure specification and costs nothing to state correctly.
- **West (72.3 sf):** leave at 0.35 or go lower — west is the one orientation where
  cold-climate practice wants the low-gain coating, and `energy_load.py` weights it 0.85 for
  cooling.
- **Plant room:** keep U-0.14; **fix the comment.**

**Cost: $0–$800 for eight units.** PassiveSun is a coating checkbox at the same pane count, and
single-silver LoĒ-180 is *cheaper to make* than triple-silver SmartSun. `prices.toml:2186`
notes a whole triple-pane upgrade is only +10–15%; this is less than that. **Cheapest item in
the review per square foot of effect.** Envelope: neutral to positive — via LoĒ-180 the
U-factor *improves*.

**But do not expect the model to applaud.** Per §5, `haus check` will report cooling going
**up** and show **no winter credit at all**. Buy this for the light, not the meter.

## G4. Pools of light — 99 of 128 luminaires are on a plain toggle
**MEASURED off `electrical.lighting.controls`. Net $407–$996.**

Only 15 fixtures are on a dimmer, 4 on paired dimmers, 3 on a timer. **51 of 128 are one type**
— the 4" 900 lm can. Every fixture in `RM-S-SUITE`, all three east bedrooms, `RM-M-BED`,
`RM-A-STUDIO`, `RM-A-STUDY`, `RM-S-STUDY2`, `RM-M-STUDY` and `RM-B-GYM` is on a plain toggle.
Four identical cans on one toggle over a bed has exactly one state: all on, evenly, at ceiling
height — the condition Alexander names as disorienting. The house already knows better:
`RM-M-LIVING` has 9 dimmed fixtures plus two shadow-gap coves, `RM-B-PLAY-N` is fully dimmed.
**The sleeping and working rooms were simply left out.**

- Retype ~15 `ED-T-SWITCH` → `ED-T-SWITCH-DIM` (already in the catalog, already priced, already
  used 6x). **$555–1,380.**
- In `RM-S-SUITE` and `RM-M-BED` **only**, delete two of four cans and replace with switched
  receptacles for table and floor lamps — light placed low and apart, which is the pattern's
  actual instruction. Returns $308–732; receptacles cost $160–348.

**A trap that turns a PASS into a FAIL, recorded so nobody hits it.** `_room_lumens`
(`ventilation.py:76-104`) counts **point luminaires only** — a `LightRun` cove counts for
nothing. `RM-A-STUDIO`, `RM-B-GYM`, `RM-B-PLAY-N`, `RM-M-LIVING`, `RM-M-STUDY` and
`RM-S-BED1/2/3` all pass R303.1 **on Exception 1's lumen floor**. `RM-A-STUDIO` has 6,000 lm
against a 4,457 lm requirement — **two cans out is 3,000 lm and an outright FAIL.**
**Dim them all; delete cans only in `RM-S-SUITE` and `RM-M-BED`**, which clear R303.1 on
glazing. Envelope impact is **zero** either way: the roof's air and vapour barriers are the
taped ZIP deck and the deck membrane, both **outboard of the rafters**, so the usual objection
to cans in a cathedral ceiling does not apply here.

## G5. A window for the gym — $1,024–$2,049

`RM-B-GYM` is **324.0 sf of `LIVING` occupancy with 0.0 sf of glazing against 25.9 sf
required** — the worst absolute daylight number in the house. It is not buried: its south wall
`W-B-S3-FR` stands **inside the excavated sunken-garden court** and has been a framed 2x6 wall
since 2026-08-28. One **WT-2748** (existing, priced) east of `D-B-PATIO`, in the 3'-8" of wall
left to the court's east face, sill 24" off the wall base.

**Honest about what it does not do:** +9.0 sf against 25.9 sf does **not** take the gym off
Exception 1, and nothing that fits on 9'-6" of bearing wall would. What it does is turn a
324 sf daily-use room from *a door in a blank wall* into *a room that fronts the garden*.
**Three durability notes that are not optional:** the 24" sill keeps the unit clear of snow and
meltwater collecting in a walkout well (**do not drop this sill for Pattern 222**); a sill pan
with end dams and a back leg must be lapped **onto the spray-foam face**, bucks before foam;
and the Ishtar-Gate brick wythe stands in front of this wall, so **the opening needs its own
`RoughOpening` reveal through the veneer** — budget it rather than discovering it on site.

## G6. An interior lite for `RM-M-STUDY` — $515–$1,055

The glazed door authored in §3.2 is the first half; this is the second. A **fixed 14" x 48"
interior lite in `W-M-C3`** beside `D-M-STUDY`. The study's east wall is 4'-3" and the door RO
takes 2'-8", so the opening is width-constrained to 14" — **which is the ideal case: a 14" RO
breaks no stud and needs no header, jacks or kings**, the cheapest opening this house can
build. `WT-1448` exists and is priced; a `WT-1448-FIX` twin follows the `WT-1424-FIX` /
`WT-3660-FIX` precedent. **The real cost is acoustic** — specify a **laminated** lite (STC ≈ 35,
cheaper than the tempered adder) or a millwork shutter; do not put a plain single lite in a
room used for calls.

## G7. Light on two sides for the primary bedroom — $690–$1,405, and rank it last

`RM-S-SUITE` is 154.3 sf and both its windows are WT-2736 on `W-S-W3`, **the west wall**. The
suite touches exactly one exterior face. Adding *more* west glass makes it worse; the pattern
asks for a second **side**. The only lever at any price is a fixed interior lite in the suite's
south partition, borrowing from `RM-S-PLANT` and its 20.0 sf of unshaded south glass.

**The building science resolves cleanly** and is worth recording: the plant room runs 75 °F /
70 % RH → dew point **64.4 °F**; a lite between it and the 70 °F suite sits at ~70–72 °F on both
faces, **6–8 °F above that dew point**, so neither face condenses — unlike the room's exterior
glass, which is exactly why those three units are U-0.14. Use a sealed insulating lite, and
carry the plant room's vapour control unbroken around the buck. **The real objection is
privacy, not physics**: the plant room is reached off the hall, so this opens the couple's
realm onto a shared room. Put it to the owner as a taste question and let them kill it.

## Glazing notes only

- **Pattern 107 Wings of Light.** The one-side-light problem in the suite, all three east
  bedrooms, the studio and every main-floor west room is a **plan** consequence: a 36' x 36'
  block on an 18' bearing centreline gives every room an 18'-deep single-aspect cell. No wing
  is possible and no item here fixes it — G6 and G7 are borrowed-light palliatives and should
  be read as such.
- **Pattern 231 Dormers — the repo is right and the review attacked it properly.** `RM-A-STUDIO`
  is 355.9 sf on 13.6 sf of glazing. The claim that only a dormer or a roof penetration would
  help was tested rather than accepted: the south gable is **full** — `WIN-A-S2` has 4" of rake
  margin over its outer jamb and the juliets have 2½", so no height remains; and a 30" unit at
  the nearest legal stud line would leave a **3½" clear pier** to the juliet's jamb pack, which
  is not buildable. **Not overturned.** All the studio can have is G3's glass and G4's dimming.
- **No shading check will ever fire on this house.** `adequate_overhang_ft = 0.0` and
  `south_wwr_threshold = 0.40` against an actual 4.5 %. The absence of shading is **invisible,
  not approved.** An overhang is correctly ruled out (it breaks the continuous
  `skin_family="standing-seam"` reading and forces a fascia-and-drip-edge detail nobody has
  drawn), and a `GlazingPanel` canopy would penetrate the foam that *is* the water plane —
  **do not propose one.** The remedy here is vegetal, and it belongs to C1/C3.
- **Pattern 199 Sunny Counter — tested and dropped.** The kitchen's total glazing is 11.3 sf, of
  which 9.1 sf faces north. Retyping `WIN-M-KIT-E` to 27" forces it onto a stud line: 33'-4"
  runs it over the cooktop backsplash, 34'-8" leaves under 7" to the corner pack. **The 14"
  bay-centre unit at 34'-0" is correct as authored** and the 2026-08-24 reasoning stands. The
  kitchen wants a different corner of the plan, which is far past $5,000.
- **A check under-count worth knowing about.** `D-M-BALC` is a `DT-EXT-FRENCH60` with
  `glazed=True` — ~16.7 sf of tempered glass on `RM-M-LIVING`'s south wall — and
  `_room_windows` skips doors, so **no glazed door anywhere in this house counts toward
  R303.1.** The great room's real aperture is ~65 sf, not 48.4. `RM-B-GYM` is in the same
  position with `D-B-PATIO`. That is a check under-count, not a design defect, and it is the
  companion to the R303.1 half of the fix in §3.1 — the same rule, the same deliberate
  conservatism, now written down in both places.

---

# Appendix — triage of the 56 patterns no themed reviewer was given

The five themed slices covered 103 of the 160. The rest, bucketed inline.

**Not applicable — Alexander's own 1970s construction system, which an IRC light-frame,
PGH-class house deliberately does not build:** 206 Efficient Structure, 208 Gradual
Stiffening, 210 Floor and Ceiling Layout, 212 Columns at the Corners, 213 Final Column
Distribution, 216 Box Columns, 217 Perimeter Beams, 218 Wall Membrane, 219 Floor-Ceiling
Vaults, 220 Roof Vaults, 226 Column Place, 227 Column Connections, 228 Stair Vault, 229 Duct
Space. These call for poured-fill wall membranes, box columns and vaulted floors; this house
is 2x6 + 4" exterior spray foam on a 16" module, and reads them as history, not instruction.

**Not applicable — town, institution or workplace scale, not one house on one lot:**
100, 101, 103, 108, 122, 123, 124, 126, 146, 148, 149, 150, 151, 152 (absent from the source
list), 153, 158, 164, 165, 178, 186.

**Already satisfied:** 95 Building Complex (four structures, not a monolith — the house's
strongest move at this scale) · 96 Number of Stories · 97 Shielded Parking (a *freestanding*
garage; the brief lists an attached one under "Dislikes") · 98 Circulation Realms · 99 Main
Building · 109 Long Thin House (N/A by intent — 36x36 compact is a surface-to-volume decision,
and Alexander's own cold-climate exception applies) · **138 Sleeping to the East** (satisfied
for three of five bedrooms; worth naming because it was not designed for) · 154 Teenager's
Cottage / 155 Old Age Cottage (`RM-A-STUDIO` very nearly satisfies both) · 157 Home Workshop ·
195 Staircase Volume · 214 Root Foundations · 215 Ground Floor Slab (2'-10" out of grade, well
past Alexander's 6–9 inches).

**Gaps carried into the ranked list above:**

- **117 Sheltering Roof** — a simple 4:12 gable with **zero overhang** reads as a folded plane
  rather than a shelter. This is the overhang question from the other direction, and it is not
  free: the zero overhang is what lets the wall PBR and the roof standing seam read as one
  continuous skin. **Cross-referenced with A1 and the glazing notes; deliberately not
  double-counted.**
- **106 Positive Outdoor Space** — the sunken garden is strongly positive; the rest of the lot
  is undifferentiated. Folded into B3 and C6.
- **116 Cascade of Roofs** — one ridge, one pitch. Real against the pattern, deliberate against
  the brief ("simple gable forms"). Note only.
- **125 Stair Seats** — the 20'-4" stair void is a stage (133) with nowhere to sit in it.
  Small and cheap; folded into C13.
- **184 Cooking Layout** — the kitchen sits inside the 748 sf great room; see the Sunny Counter
  note in §6, which tested the one available lever and dropped it.
- **187 Marriage Bed** — `RM-S-SUITE` takes light on one side only. This is **G7**.
- **253 Things From Your Life** — one line, not a row, and the honest answer is that this is
  the owner's to satisfy rather than the drawing's. The white oak off family land (B2, B4) is
  the one place the *drawing* can carry it.

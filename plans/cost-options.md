# Cost options — priced upgrades and downgrades

Started 2026-08-08. Menu of swaps if the number needs to come down, each priced against a
line in `houses/catlin/prices.toml`. **Nothing here is decided** — the plan as authored is
the plan, this is the menu.

**Rules:** every row cites the prices.toml line and the delta at both ends of the range —
an unpriced idea lives in TODO.md's "potential cost cutting" list until it has a number. A
swap that changes what the house *does*, not just what it costs, gets a **cost of the cut**
note. Rows are material+labour unless noted.

## Baseline — it moved three times; read this before comparing rows

| date | change | before → after |
|---|---|---|
| 08-18 | suspended deck got its own price key (was billed at slab-on-grade rate) | $274,206–562,712 → $307,330–627,774 |
| 08-20 | labour added to file (21/24 sections were $0 labour) | constr. total $306,982–627,214 → **$574,980–1,135,114**; labour $0 → $211,280–421,533; $/gsf $51–104 → $96–189 |
| 08-20 | allowance register authored in + 3 of 4 bid-ladder stages turned on | net $576,557–1,139,150 → **total $978,947–2,061,452**; $/gsf $96–189 → **$163–343** |

Four owner decisions on 08-20 took **$64,782** off the high end: wire closet shelving not
laminate (−$35,000), summer pour (−$21,000), code-min ice barrier confirmed as base scope,
suburban Hennepin's 8.525% tax not the city's 9.025% (−$3,182).

`[markup]` (GC overhead/profit, ~$130,000–375,000) is **off by choice**, present at zero.

A delta below is measured against the *section* it names, not the total — the bid ladder
multiplies it ~1.20x (waste, 10% contingency, material tax) on the way to the bottom line,
~1.40x if markup is switched on. A $10,000 saving in `envelope_layers` is ~$12,000 off the
printed total today.

## Downgrades (money back)

| swap | current → new | saves | notes |
|---|---|---|---|
| Standing-seam metal roof → architectural asphalt shingle | $54,777–99,331 → $31,600–56,900 | **~$20,000–42,400**, the biggest lever on the list | see detail below |
| Elm tudor posts → paint/stain-grade species | $2,006–6,001 → $700–1,500 | ~$1,300–4,500 | 6-1/8" S4S elm isn't a purchasable article — needs a glued-up blank from 8/4 stock. **Get a real quote first** (Wood From The Hood, Siwek Millwork) — low end is only $2,006 |
| Aluminium balcony deck → composite over membrane | $5,838–10,290 → $2,000–3,600 | ~$3,800–6,700 | quote-only product, least certain line in the file. Call Versadeck (651) 356-1870 first — may make the swap moot |
| Fabricated box gutter → seamless K-style | $1,179–2,506 → $600–1,100 | ~$600–1,400 | plus $150–400/ea conductor heads a box gutter needs (not in estimate) |
| Trimless interior door → standard cased prehung | $1,220–2,800 → $305–755 | ~$915–2,045 + schedule risk | hidden-jamb reveal is a 3-trade sequencing item; frame must be set before drywall, so this can't be reversed later |
| Post bases: ABU66SS stainless → ABU66Z/RZ ZMAX | $1,500–2,300 → ~$550 | ~$950–1,750 | wrong $1,000 to save — one detail nobody re-does without jacking the structure |
| Exterior guards: Trex Signature → builder-grade aluminium | $2,835–5,222 → $1,492–2,611 | ~$1,343–2,611 | now covers both balcony (38.3 LF) and porch (36.3 LF, replaced the masonry parapet) — downgrade together or the two levels stop matching |
| Basement brick veneer → delete | $1,233–2,603 | full line | the one masonry note on the basement wall |
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
  the old shored-pour rate.
- Saving came from skipping shoring/formwork — the $25,000–40,000 commercial mobilisation
  floor a shored deck requires. Four interior 12" concrete cross walls became stud
  partitions, taking 4 footings and 4 drain-tile runs with them.
- **Cost:** house rose 4" (12-5/8" deck vs 9" slab, basement kept its headroom) — grew the
  foundation protection panel ~50 SF and added 4" to the zoning-height question in TODO.md.
  R-25 of EPS between two conditioned storeys buys nothing thermally; it's there as formwork.
- **Next cut available:** 10" form + 3" cap, same depth class, ~21% less concrete, R-31 —
  one line in `houses/catlin/params/main_deck.py`.

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
  each wall and gated by `structural.foundation_unbalanced_fill`.
- **8" and not 10"** (which also reads NR): 8" is the standard residential form module and
  the market rate is quoted for it. Thickness above 8" adds concrete without adding forming,
  so 10" would pay an odd-thickness forming premium and hand back half the yardage to save
  the bar.
- **The saving, measured:** −12.0 cy (48.5 → 36.5 cy across the perimeter rows),
  **−$3,239 to −$5,759** on `[wall_structure]`. Re-derived rates, not the 12" row: the 12"
  $420–700/cy is $110–180/LF of forming, crew and pour at that height, and forming does not
  get cheaper because the wall got thinner. 8" × 9'-4" is 0.2305 cy/LF, so the same
  $114–187/LF is **~$495–810/cy**. Pricing the 8" wall at the 12" rate would have claimed
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

- Remove the attic level, truss + blown-in insulation. Touches framing, envelope_layers,
  floor_finishes, stairs and the ST-S2A guard at once — needs a variant (`haus variants
  compare`), not an arithmetic estimate.

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
| 1 | Is the GC fee in or out? `[markup]` stays zero for now | — |
| 2 | Is rebar inside the concrete $/cy rates, or its own line? Assumed inside; reversing means editing both places at once | $10,000–18,000 if wrong |
| 3 | Is 761 LF the right drain-tile length, or should it be one perimeter ring? | $3,000–7,200 |
| 4 | One roofing quote — see Refactors above | resolves ~$15,500–34,000 of boundary |

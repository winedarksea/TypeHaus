# Buildability — the owner-builder audit

Started 2026-09-10. The house is about to be built with the owner as general
contractor. `plans/cost-options.md` asks what each feature costs. This file asks a
different question about the same features: **how likely is each one to be built
correctly, on the first try, by the subs actually available, without the owner
standing over them?**

Nothing here is decided. The plan as authored is the plan; this is the menu.

## Method — read this before comparing any row

**The baseline.** Every figure is measured against `haus takeoff houses/catlin` on
2026-09-10, which printed a construction total of **$807,796 – $1,667,219**
(with furnishings, $816,606 – $1,714,869). That is materially below the
$917,729 – $1,895,004 baseline `plans/cost-options.md` still carries, so do not
mix a row from that file with a row from this one without re-striking it.
The check report on the same day was **1,085 pass · 3 fail · 46 unknown ·
21 not applicable**, and the calculation package carried **42 engineered items, 25
of them open**.

**Where the numbers were measured.** Another session was editing this house
concurrently while this audit ran — `params/breezeway.py` went from 195 to 486
lines mid-measurement, and an assembly appeared in `plan/assemblies.py` after a
sandbox had been copied, which silently contaminated the first attempt at BLD-03.
**Every `built` row in this file was therefore re-struck in a detached worktree at
commit `286ef997`**, with `PYTHONPATH` pointed at that worktree's engine, so
neither the house nor the engine could move underneath a measurement. Both sides
of every comparison built with zero errors. Re-strike any row here the same way
rather than in the working tree.

**How a row is priced** is one of the four things `plans/cost-options.md` already
defines: `built` (a sandbox copy of the house inside the repo with the edit made,
the check report confirmed unchanged, `haus takeoff` re-read), `ablation`,
`arithmetic`, or `allowance`. A row that cannot be priced honestly says
`unpriced` and stays that way. **A takeoff total that falls because a type lost
its `prices.toml` row is not a saving** — that trap has bitten this repo before,
so every `built` row states the unpriced-row-group count on both sides.

**Risk is defined, not felt.**

- **HIGH** — a wrong execution gets buried by later work and is expensive to
  reach, or the element is life safety or water management.
- **MED** — visible and fixable, at the cost of a callback.
- **LOW** — costs an argument and an hour.

**What this file is not.** It proposes no durations and no dates. It does not
reopen a decision already struck with a measurement; the open-web basement
ceiling was trialled against the real model and rejected, and rows like that get
cited rather than relitigated.

---

## 1. Distinct-detail census

Counted from the built model on 2026-09-10, not estimated. Reproduce with
`haus build houses/catlin` then read `houses/catlin/out/model.json`, or
`haus takeoff houses/catlin --json`.

| Family | Instances | Distinct kinds | Used exactly once |
|---|---|---|---|
| Wall assemblies | 178 walls | **37** | **13** |
| Transition details | — | **21** | — |
| Window types | 40 units | 15 | 5 |
| Door types | 36 units | **17** | **10** |
| Framing profiles | — | **52** profiles / 60 profile-material rows | — |
| Connector part numbers | — | **31** | — |
| Roof assemblies | 2 roofs | 2 | — |
| Floor systems | 11 decks | 6 framing types | — |
| Foundation methods | — | **4** | — |
| Cladding materials | — | **7** | — |

A production framer executes three to five wall assemblies. This house has
thirty-seven, and thirteen of them appear on exactly one wall:

`BASEMENT_BRICK_VENEER`, `GARDEN_CURB_6`, `GARDEN_FRAMED_2X6`,
`INT_2X4_BOOKCASE_12`, `INT_2X6_BRG_RC`, `PLANT_INT_2X6_BRG_HUMID`,
`SAUNA_LINER_INT_2X6_BRG`, `SAUNA_LINER_ON_GARDEN_CURB`,
`SAUNA_LINER_ON_GARDEN_FRAMED`, `SG_VENEER_BEAM_14`,
`STAIRWALL_INT_2X6_BRG_TYPEX`, `STAIRWALL_INT_2X6_BRG_UNDERSTAIR`,
`STAIRWELL_PARTITION_4H`.

**Windows are already disciplined and doors are not.** Forty windows on fifteen
types is a 2.7-to-1 ratio and reflects the brief's rough-opening ladder working as
designed. Thirty-six doors on seventeen types is 2.1-to-1, with ten types on a
single leaf: `DT-EXT-OVERHEAD192`, `DT-INT-ACCESS24`, `DT-INT-BIFOLD56`,
`DT-INT-BOOKCASE30`, `DT-INT-BYPASS48`, `DT-INT-BYPASS60`, `DT-INT-CLOSET24`,
`DT-INT-DOUBLE60`, `DT-INT-SWING30-TRIMLESS`, `DT-POCKET-INT-48`. Several are
genuinely different products; several are one dimension away from an existing
type. This is the cheapest consolidation in the file and nothing currently counts
it — `plans/12-m1-emit.md` planned a door-size variety check beside the window one
and only the window half was ever built.

---

## 2. The engineering register, and the one change that empties it

`haus calcs houses/catlin` on 2026-09-10:

| Status | Items |
|---|---|
| draft (engine computed, ratio within capacity) | 17 |
| OVER | 0 |
| INCOMPLETE (computed in part, an input missing) | **20** |
| NO LOCAL CALC (deferred to a designer of record) | 5 |
| covered by a seal in `engineering.toml` | **0** |
| **Total** | **42, of which 25 open** |

**All twenty INCOMPLETE items are one question asked twenty times.** Every one is
a `wall_panel/*` on a north or south facade clad in `board-batten-24`, and every
one is missing the same input: the concealed-leg screw withdrawal allowable for a
board-and-batten panel over open girts at 24-inch spacing, which no manufacturer
publishes at any spacing. The panel's bending is fine at a demand-capacity ratio
of 0.31. The limit state that actually governs it is unpublished.

`houses/catlin/CLAUDE.md` already records that the report usually cited here,
ESR-4729, does **not** cover this wall — it is a roof-panel report over 16 gauge
steel — and that of eight manufacturers surveyed only two permit open girts, only
one of those is verified, and that one's fastener clause needs a variance that is
still open.

`engineering.toml` does not exist, so **no item in the house is sealed and
`haus print --sealed` correctly refuses.** That is the true state, not a gap in
setup.

---

## 3. Trade-visit map

**`haus tasks` cannot answer this today, and that is worth saying plainly.** The
command groups work at trade by storey, but most of this house's cost lands in
rows with no storey tag, so twelve of the thirteen trades report a single
`building` package. The visit count below is therefore derived by hand from the
design, not from the model, and the gap is itself a finding for the project
management work deferred at the foot of `plans/TODO.md`.

| Trade | Distinct mobilisations | Why more than one |
|---|---|---|
| Concrete | **at least 5** | footings and basement walls · garage ICF stem (a different sub) · slabs · the cast deck over the LiteDeck form, which needs a pump after sill plates are set · sunken-garden walls, piers and the four cast columns · then the polished-concrete finish pass, which cannot happen until the building is closed |
| Envelope | **4, with an inspection hold** | framer lays blocks and girts flat before tilt · **hold: the 8-inch screws must be inspected before the sprayer arrives, because they are blind and invisible once foamed** · foam sub · panel sub · window sub, mounting outie on the girt plane |
| Masonry | **2** | the five-element firebox with its steel lintel · the 129 sf sunken-court wythe, a minimum-mobilisation job needing scaffold |
| Metals | **5+** | garage stem coil band on its vented standoff · six drip flashing runs · wall panels · roof panels · eave water chain · two guard systems with two different mounting details · snow guards and seam clamps |
| Plumbing / electrical / mechanical | **2 each, minimum** | all three must be on site during forming to place 83 cast pipe sleeves, then return for rough-in |

The single worst coupling: **`FS-S-WEST`'s open-web floor trusses carry nearly
every second-floor service crossing** — both drain stacks, four supply risers, the
radon and plumbing chase, hydrant distribution, and data conduits — through
8 7/8-inch web openings. Plumber, electrician and HVAC all thread the same truss
field. If the truss order is late or the webs land wrong, three trades stop at
once.

---

## 4. Findings — the roll-up

Ranked by risk times reach, not by dollars. A HIGH-risk detail that saves nothing
is still the first thing to remove.

| id | Finding | Risk | Verdict | Delta |
|---|---|---|---|---|
| BLD-01a | Drop board-and-batten; one wall panel product | HIGH | **SIMPLIFY** | **−$1,704 to −$4,635** |
| BLD-12 | No soils report, and the piers make one mandatory | HIGH | **SIMPLIFY** | +$2,500 to $5,000 |
| BLD-06 | Service load calc rests on unlisted devices | HIGH | **SIMPLIFY** | +$0 or +$10k–15k |
| BLD-01b | The girt-and-block exterior wall | HIGH | OWNER CALL | unpriced |
| BLD-03 | Two floor systems on the main storey | HIGH | **SIMPLIFY** | **−$7,536 to −$13,486** |
| BLD-02 | The freestanding concrete structure | HIGH | OWNER CALL | unpriced |
| BLD-05 | Suite bathroom drain, 0.062" of slack | HIGH | **SIMPLIFY** | ~free if timed right |
| BLD-13 | Conditions the engine does not grade | HIGH | KEEP as checklist | — |
| BLD-08 | ERV radial scheme off-catalog; heat pumps fine | MED | split | unpriced |
| BLD-07 | Unvented roof: painter, insulator, undrawn eave | MED | KEEP + 2 instructions | — |
| BLD-04 | 13 one-off assemblies, 10 one-off door types | MED | **SIMPLIFY** | unpriced |
| BLD-10 | Seven cladding materials, three scopes | MED | **SIMPLIFY** | unpriced |
| BLD-09 | Four foundation methods | MED | OWNER CALL | ~$500–1,500/extra pour |
| BLD-11 | 2,000 board feet of owner-milled hardwood | MED | OWNER CALL | unpriced |
| BLD-15 | Owner-GC licensing, pricing, inspection order | MED | KEEP as checklist | −10 to −20% on subs |
| BLD-16 | Jurisdiction profile names a code that doesn't exist | LOW | **SIMPLIFY** | — |
| BLD-14 | Documentation disagrees with the source | LOW | **SIMPLIFY** | — |

**The two measured simplifications together are −$9,240 to −$18,121, and BLD-01a
alone takes the house from 25 open engineering items to 5.**

**If you do only three things:** authorise the soils report (BLD-12, it gates
BLD-02 and is code-mandatory for the piers), drop board-and-batten (BLD-01a), and
put a listed Power Control System behind the service calculation or upsize the
service (BLD-06).

## 5. The findings in full

### BLD-01a — Drop board-and-batten. One wall panel product. **HIGH · SIMPLIFY**

| | |
|---|---|
| element | twenty `layer_materials=` overrides in `plan/storeys/{main,second,attic}.py`, plus the corner-trim material in `params/roof_trim.py` |
| what a sub sees | Two different concealed- and exposed-fastener metal wall panels on one house, on different elevations |
| failure mode | Not a site failure. A permit failure: twenty engineered items that no engineer can close, because the governing limit state is unpublished |
| risk | **HIGH** — it is twenty of the twenty-five open items on the calculation package |
| trade | Siding. Does not change the visit count |
| simplification | Clad the twenty north and south walls in `pbr-panel-26`, the exposed-fastener panel already used on every other elevation. PBR is prescriptive here: ASC, Metal Panels Inc. and Homewood publish span tables giving 144 to 168 psf at 3'-0" |
| cost of the cut | Appearance only. The north and south facades lose the 20-inch batten rhythm and read as PBR like the rest of the house. Exposed fasteners become visible on those elevations |
| **delta** | **−$1,704 to −$4,635** |
| how priced | `built`. Sandbox `houses/_sbx_pbr`, overrides deleted, rebuilt |

**The measurement, both sides freshly generated at engine 0.1.1:**

| | catlin | one-panel sandbox |
|---|---|---|
| check: pass / fail / unknown / N.A. | 1085 / 3 / 46 / 21 | **1085 / 3 / 46 / 21** |
| engineered items | 42 | **22** |
| open items | 25 | **5** |
| INCOMPLETE | 20 | **0** |
| NO LOCAL CALC | 5 | 5 |
| unpriced row groups | 76 | 75 |
| construction total | $807,796 – $1,667,219 | $806,092 – $1,662,585 |

The check report is byte-identical, so nothing was traded away to get it. The one
row group that disappears is the `board-batten-24` line itself, which is the
consolidation, not a silent drop.

**This is the highest-leverage single edit in the file.** It takes the house from
twenty-five open engineering items to five, and the five that remain are all
already assigned to a designer of record: both roofs' rafters, both roofs' uplift
path, and the overhead-door header.

**The research makes the case stronger than the model does.** The design's own
note records that no manufacturer publishes the withdrawal allowable. Three
further facts came back:

- **The one evaluation report that covers a board-and-batten panel forbids this
  application outright.** Western States' ESR-4730 §5.2 and §4.2 both state the
  panels "must be backed by a solid substrate." Its Table 2 evaluates their
  board-and-batten at **8-inch width with support fasteners at 12 inches maximum**,
  allowable negative pressure 48 psf. This design is 20-inch coverage at 24-inch
  girts, outside the evaluated geometry on both axes.
- **The manufacturer's own install guide contradicts its own evaluation report.**
  The guide says the panel is used over open purlins and that "most details in this
  guide are shown with panels attached to open framing." The guide sells you open
  framing; the report the official reads forbids it.
- **The specified panel may not exist at the second source.** Metal Sales'
  board-and-batten is published at **10-inch and 12-inch coverage only**, over steel
  framing 18 ga or thicker, plywood, oriented strand board or 1x lumber. There is no
  20-inch product and no girt spacing given. McElroy's is 12-inch over solid deck;
  Bridger's is 12 or 16-inch with fasteners every 16 inches over solid substrate.
  No board-and-batten install guide or evaluation report was found from ASC at all.

**One honest caveat, and it matters.** Switching to PBR closes the *engineering
register* because PBR's published span tables reach it — 26 gauge at a 2-foot span
carries an allowable outward load of 211 psf. But those tables carry a footnote
that the allowable load "does not address web crippling, **fasteners**, support
material or load testing." So even on PBR, the panel is never the limit; **the
screw's grip in a 1 1/2-inch flat treated girt is, and nobody publishes that
either.** BLD-01a removes twenty items from the register and does not remove the
underlying physical question, which belongs to BLD-01b.

### BLD-01b — The girt-and-block exterior wall. **HIGH · OWNER CALL**

| | |
|---|---|
| element | `EXT_2X6` in `houses/catlin/plan/assemblies.py`, on 34 walls |
| what a sub sees | Four inches of spray foam on the *outside* of the sheathing with no housewrap, horizontal treated 2x4s floating in mid-air on stacks of loose offcuts, and one long screw holding each stack |
| risk | **HIGH** — buried, structural, and it is the cladding attachment for the whole house |
| trade | Framer, foam sub, siding crew, window sub. Four visits and an inspection hold |

**Scale of the operation, from the takeoff:**

| Item | Quantity | Priced |
|---|---|---|
| SDWS22800DB 8" timber screws | **1,118**, one per crossing | $1,286 – $1,957 |
| `3-2x4:kdat` block stock (3,354 offcuts, stacked in threes) | 344 LF | $1,514 – $2,305 |
| `2x4:kdat` flat girts | 2,790 LF | $5,580 – $8,928 |
| 4" exterior closed-cell spray foam | — | $22,003 – $34,093 |
| **Standoff system subtotal** | | **$8,379 – $13,190** |

The material price is not the risk. Cutting and stacking 3,354 offcuts, marking the
stud line across each girt face as it is laid, and driving 1,118 blind eight-inch
screws is per-piece work, and `plans/TODO.md` already records this exact class of
under-billing for the window bucks.

**Four findings from outside the model. The first is a specific, checkable defect.**

1. **The screw may not be able to clamp the joint, and that is a different failure
   mode from the one the engineering note grades.** Simpson publishes the
   SDWS22800DB with a **2 3/4-inch thread length**. The side member here is girt
   1.5 inches plus block 4.5 inches plus sheathing 0.5 inches, **6.5 inches total**,
   so the threaded portion runs from 5.25 to 8.0 inches under the head. That puts
   roughly **1 1/4 inches of thread in the block and sheathing** rather than all of
   it in the stud. Threads engaged in *both* members prevent clamp-up: the screw
   jacks the girt off the block instead of drawing it tight. Simpson's own table
   note adds that published values assume pull-through of a **1 1/2-inch** side
   member; nobody has tested a 6.5-inch one. Withdrawal from the stud computes to
   about 280 lb at a load duration factor of 1.0 and 449 lb at 1.6, which is in the
   range the house's note works with — but **withdrawal is not the question raised
   here**. This wants checking against `notes/catlin_truss_engineering.md` before
   anything else in this file.
2. **The prescriptive attachment table does not reach this wall, on three counts.**
   IRC Table R703.15.2 requires foam with a minimum compressive strength of 15 psi
   per ASTM C578 or C1289; closed-cell spray foam is neither, it is C1029, so the
   table is inapplicable on its face. Its maximum foam thickness is 4.00 inches,
   which is exactly where this design sits. And its note (e) requires that **in a
   horizontal orientation the tabulated spacing be achieved with two fasteners into
   studs at 16 and 24 inches on centre.** These girts are horizontal with **one**
   screw at **every other** stud, roughly a quarter of the prescriptive fastener
   count. The blocks bearing directly on sheathing rather than on foam is
   structurally better than the tabulated case, but it means no table and no
   evaluation report applies and the connection is engineered by default.
3. **Foam as the water barrier is achievable, but only product by product.** BASF's
   ESR-2642 §4.5 permits WALLTITE LWP as an alternative to the prescribed
   water-resistive barrier at one inch minimum, **provided all construction joints
   and penetrations are sealed with the same foam**. Two conditions bite: §3.2
   states the flame-spread testing was done at a **maximum thickness of 4 inches**,
   so a 4-inch design has zero tolerance for an over-thick pass; and §4.2 requires
   the substrate to be free of moisture, frost and ice, the work protected from
   weather during and after application, and each pass cured ten minutes per inch.
   Minnesota's own R703 amendment still says "or other approved water-resistive
   barrier," and the approval mechanic is Minn. R. 1300.0110, under which the
   official approves an alternate only on finding it at least equivalent. **Hand
   the reviewer the evaluation report for the specific foam the sprayer actually
   buys, not a generic argument.** No Minnesota precedent was found.
4. **Four inches is three or four passes, not two, and it is weather-dependent
   work on a critical-path day.** Industry guidance caps a lift at about 1 1/2
   inches with a cool-down between, so 4 inches is three passes minimum. Exterior
   application adds a 50°F substrate minimum on most formulations and a shutdown
   above roughly 10 to 15 mph of wind. Thickness shortfall is the single
   most-reported dispute in this trade and it is verified by the owner with a stiff
   wire, so **specify a minimum, never an average**, and have thin spots marked for
   touch-up before the crew leaves.

**One thing nobody could answer.** No source of any kind describes holding sprayed
foam to a gauge behind a projecting standoff, and no manufacturer publishes a
maximum-thickness tolerance. Lstiburek states flatly that sprayed foam does not go
on smooth, flat and of uniform thickness — which is exactly why he specifies
furring as the straight reference plane rather than trusting the foam surface.
Here the blocks' 1/2 inch of proud is the *only* thing making the girt plane
straight, and not burying it is an unverified field assumption.

**And the openings are where this class of wall actually fails.** With no sheet
barrier there is nothing to lap flashing to, so every window, door and penetration
becomes a bespoke liquid-applied detail. Lstiburek's own detail for this wall calls
for extended wooden bucks with plywood lips forming an under-window gutter, liquid
flashing over the buck, head flashing before the field spray, and filleted foam at
every opening perimeter — and says explicitly not to spray foam to the windows.
**This compounds with the zero-overhang roof** (BLD-07): no overhang plus no sheet
barrier puts the entire water-management burden on the foam and the liquid flashing
at 31 exterior windows.

**The alternative, with numbers.** Zip-R is out on design intent rather than cost —
it tops out at R-12, so R-20 continuous is not reachable with it at all. The
realistic build-up here is about 3 inches of foil-faced polyiso, roughly R-19.5, or
about 4 1/2 inches of mineral wool over a taped barrier with **vertical** furring
over studs, which lands inside Table R703.15.2 up to 4.00 inches and needs no
engineering. A published builder comparison puts 2x6 with Zip-R and a cavity batt
at about $3.62 per square foot against 2x6 with plywood, 1 1/2 inches of mineral
wool and a batt at about $5.82. Worth stating plainly: **Minnesota's own minimum
for a zone 6 or 7 wood-frame wall is R-20 cavity, or R-13 plus R-5 continuous.
Everything above R-5 continuous here is voluntary.**

### BLD-02 — The freestanding concrete structure. **HIGH · OWNER CALL**

| | |
|---|---|
| element | `params/sunken_garden.py` — retaining walls `W-SG-W2`/`E2`/`S`/`ARCH`, columns `PT-SG-BR1`/`BR3`/`BF1`/`BF3`/`COL`/`FCOL`, grade beam `W-SG-BRKBM`, piers `FT-SG-COL`/`FCOL` |
| what a sub sees | Cantilever-T retaining walls up to 10'-3" of retained height, an arched load-bearing wall, two bell-bottom augered piers, a 19-foot buried grade beam, and four 12-inch round columns fixed at their bases with hot-dip galvanized cages in fiber tube |
| risk | **HIGH** — structural, buried, and the largest remaining block of engineering once BLD-01a closes |
| trade | Commercial cast-in-place concrete, not a residential foundation crew |
| **delta** | `unpriced` — but see the four cost mechanisms below, none of which is in the model |

**Four findings from outside the model, each of which a sub will raise and the
design currently does not answer.**

1. **The walls are permitted, engineered structures and the threshold is lower
   than it looks.** Minnesota Rules 1300.0120 subp. 4.A.(4) exempts a retaining
   wall only up to four feet measured **from the bottom of the footing**, not from
   grade, and any surcharged wall of any height is permitted. Engineering for the
   wall alone runs $800 to $2,500 in Minnesota, and engineers price the added
   liability of a stamp-only review at $500 to $2,000 on top.
2. **The four columns are the least forgiving lateral system in the code.** A
   cantilevered-column system carries an ASCE 7 response modification factor of
   1.25 with ordinary detailing, limits axial demand to 15 percent of available
   axial strength, and requires the foundations to be designed for the overstrength
   load. Practising engineers also treat base fixity as something earned rather
   than drawn: fixity here is limited by rotation of the 12-inch wall the column
   stands on, plus dowel development. Expect a residential engineer either to
   decline this or to price a full lateral analysis, not a stamp.
3. **Circular ties are a shop order.** Fabricators sell prefabricated rings and
   welded cages; a catalog 5-foot by 12-inch circular cage runs about $126, or
   roughly $25 per foot of cage before galvanizing and before custom bar. Field
   bending accurate #3 circles to a 2-inch-cover diameter is not a foundation
   crew's skill. Rebarfab in New Brighton and Rio Grande both fabricate locally.
4. **Hot-dip galvanized bar is a quoted special order with no published stock,
   minimum, or lead time anywhere in the Midwest.** The premium is 25 to 50 percent
   over black, and a small cut-and-bent mixed lot prices at the top of that range.
   One specification point to fix before quoting: the design names ASTM A767
   **Class 1**, but Class 2 is the class intended to be fabricated after
   galvanizing. Class 1 bent after coating needs extensive repair.

**The mix is not the risk; the order desk is.** Every metro plant runs
low-water-cement air-entrained mixes daily, so an F3/C2 mix at w/cm 0.40 with 6
percent air is ordinary plant capability. The failure mode is a residential order
desk selling a "5000 psi" with neither the water-cement limit nor the air content
written on the ticket. Budget roughly $15 to $30 per yard over a 4000 psi mix for
the strength, $5 to $15 for air entrainment, and $8 to $15 for water reducer.

**The piers have an unverified soil precondition.** A belled excavation must stand
open long enough to set the cage and place concrete, which rules out sand, soft
clay, and any caving or water-bearing ground. Twin Cities glacial outwash sand is
exactly the condition that voids belling, and nothing in the design set
establishes cohesive soil at bearing depth. See BLD-12 — this is not a
nice-to-have, it is a precondition of the detail.

Things nothing in the engine grades here, which therefore must be walked by hand:
dowel geometry against the two footings each one names, thermal-break continuity
between house and garden footings, and the requirement that every wall-to-house
joint carry one continuous 2-inch board from the house footing underside to the
porch wall top.

### BLD-03 — Two floor systems on the main storey. **HIGH · SIMPLIFY**

Upgraded from MED after the research. `SL-M-DECK` puts 414 square feet of 10-inch
LiteDeck EPS stay-in-place form under a 4 3/8-inch cast topping inside an I-joist
floor. Four independent findings point the same way.

1. **No Minnesota dealer or installer was found.** LiteForm publishes a dealer map
   with no Minnesota entry, and no Twin Cities distributor or installer surfaced.
   The nearest source is Benchmark Foam in Watertown, South Dakota, about three and
   a half hours out. This is a special-order, freight-in product with no local
   installer bench.
2. **The manufacturer's own common use is not this.** LiteForm describes the wood
   rib system as most commonly used for porch caps and storm shelters, secondarily
   garages and suspended slabs. A 414-square-foot occupied main-floor bay is off
   the common-use path, and LiteForm states engineering is required per
   installation. No ICC-ES evaluation report was located, so the building official
   will be reading manufacturer engineering plus a PE stamp.
3. **The shoring is the job, and its design is the installer's liability.** The
   plank needs continuous shoring perpendicular to the sections at roughly five to
   six feet on centre, on solid footings, and per LiteForm **the installer owns the
   shoring design under ACI 347R**. That is a liability most residential framers
   will not knowingly accept.
4. **Polishing a suspended slab is the flagged risk in the trade press.**
   *Concrete Construction* published a piece titled "Why Polishing Suspended
   Concrete Slabs is More Likely to Disappoint Customers." The mechanism is
   documented: thin bonded toppings curl, and non-uniform aggregate exposure
   follows the high spots that curling creates. With only 4 3/8 inches of topping
   over foam, with rebar and conduit inside it, grind depth and aggregate exposure
   are not guaranteed.

**Cost runs against it too.** LiteDeck form material alone lists at $6 per square
foot for base sections, top hat extra. Published installed cost for EPS deck
systems is $10 to $18 per square foot, described in the trade press as about
double a conventional wood system; wood I-joist floors run about $7.50 to $12.50
installed. So the bay is roughly a 1.5 to 2 times cost multiple against the floor
it abuts, before the topping and before polishing at $7 to $12 per square foot.

**And the polishing carries a silica obligation.** This is an indoor grind, so
under 29 CFR 1926.1153 Table 1 it needs shroud and HEPA collection plus APF 10
respirators once the task passes four hours in a shift. Independent of Table 1 the
employer owes a written exposure control plan, a designated competent person with
stop-work authority, training, and medical exams for anyone in a respirator 30 or
more days a year. There is no small-residential-contractor carve-out. An
owner-GC hiring a two-man polishing crew is buying that paperwork.

**Measured: extending the I-joist field across the whole storey.**

| | catlin | all-wood main deck |
|---|---|---|
| check: pass / fail / unknown / N.A. | 1085 / 3 / 46 / 21 | 1075 / **7** / 46 / 21 |
| build errors | 0 | 0 |
| unpriced row groups | 76 | 76 |
| construction total | $807,796 – $1,667,219 | $800,260 – $1,653,734 |
| **delta** | | **−$7,536 to −$13,486** |

`built`, worktree at `286ef997`, sandbox `houses/_sbx_wood`: `EAST_FLOOR`'s
outline extended to the full storey in `params/main_deck.py`, `DECK` removed from
`MAIN_ELEMENTS`, and the four cast sleeves that exist only because the deck is
concrete deleted (`SP-M-KITCH`, `SP-M-CW-KITCH`, `SP-M-HW-KITCH`,
`SP-M-CD-KITCH` — in a wood deck those are bored holes, not pre-pour items).

**The cost of the cut is four new FAILs and they are all one thing.** The concrete
deck's EPS form is doubling as an MEP chase. Remove it and `PR-B-HW-KITCH`,
`CD-B-KITCHEN` and `CD-B-DATA-MEDIA` drop out of the form and hang 3.9 inches
below a finished basement ceiling in the gym and the north playroom. That is
solvable with a bulkhead or a reroute, and `plans/TODO.md` already records those
same runs competing for that same lane — but it is real work that the $7.5k to
$13.5k has to pay for.

Also given up, and not in the number: polished concrete as the finished floor, the
fire-rated separation over the media room, and the thermal mass. Against that, the
wood floor removes an entire concrete mobilisation with a pump, a shoring design
the framer would have to own, a freight-in product with no local installer, and
the silica programme.

**Recommendation: SIMPLIFY.** The three evicted runs are the only real objection
and they are cheaper to solve than the deck is to build.

### BLD-04 — Thirteen wall assemblies used once, ten door types used once. **MED · SIMPLIFY**

The lookup burden, not any single assembly, is what generates callbacks for an
owner-GC. Two consolidations look free on inspection and want measuring:

- The four stair-wall variants (`STAIRWALL_INT_2X6_BRG`, `_TYPEX`,
  `_UNDERSTAIR`, `STAIRWELL_PARTITION_4H`) are one wall built four ways along its
  length. `_TYPEX` and `_UNDERSTAIR` differ only in the Type X substitution and
  both exist for the same R302.7 reason.
- The three sauna liner assemblies (`SAUNA_LINER_INT_2X6_BRG`,
  `_ON_GARDEN_CURB`, `_ON_GARDEN_FRAMED`) differ by what they land on, not by
  what the carpenter builds.

Deliberately **not** on this list: `W-B-CW3`/`W-B-STR2`'s over-specified
steel-stud assembly, which `plans/TODO.md` already records as not worth
re-opening.

### BLD-05 — The suite bathroom drain group. **HIGH · SIMPLIFY**

`PR-M-S-SUITE-WC-DRAIN` carries **0.062 inches** of head slack over 5.75 feet,
threads an 11 7/8-inch open-web truss with half an inch of clearance at the pipe
crown, and ties in 0.052 inches above the collector invert.
`notes/mep_drain_routing_basis.md` says the route is nearly unique, which is
exactly the problem: there is no second solution if the first is built wrong.

**Three findings from outside the model sharpen this considerably.**

1. **Minnesota gives no relief on slope.** Chapter 4714 adopts the UPC, whose
   grade rule is a quarter inch per foot, and whose reduced-slope exception reaches
   only **pipe 4 inches and larger**, only where quarter-inch is impractical for
   structural reasons, and only with the building official's approval. The
   commonly-cited eighth-inch allowance at 3 inches is **IPC 704.1**, and Minnesota
   is not an IPC state. The quarter inch is a hard floor here.
2. **Field tolerance is an order of magnitude coarser than the design margin.**
   The standard trade method is rigid standoffs stepped a whole inch every four
   feet. 0.062 inches is about two thicknesses of plumber's tape. And the tolerance
   is one-directional: plumbers will happily give you more pitch, never less, so
   every thousandth of slack must be spent going steeper.
3. **A laser-set invert is not the answer, because it is not residential
   practice.** No source describes it for residential drain-waste-vent; the
   published methods are stepped standoffs, string lines and torpedo levels. Asking
   for it buys an argument, not a tolerance.

**The real answer is upstream of the plumber.** *JLC* on open-web floor trusses:
the trusses are the right host and need no drilling, and truss designers will plan
chases around toilet drops — but "it is beneficial to have plumbing layouts
designed in advance and **reviewed by the plumber before trusses are
fabricated**." A 3-inch line with half an inch of crown clearance is a shop-drawing
input, not a rough-in discovery.

So: either move the fixture group closer to a stack, or put the drain layout in
front of the truss fabricator and the plumber **before the truss order is
placed**, and get the chase designed into the webs. The second costs nothing but a
meeting held at the right time, and the truss order is already on the critical
path for three trades (see the trade-visit map).

### BLD-06 — The service load calculation rests on devices that are not listed for it. **HIGH · SIMPLIFY**

This was the finding that moved most on research, and it moved against the design.

NEC 220.82 demand is 191.4 amps against a 200 amp service, 95.7 percent, and it
only reaches that number because four load-management groups credit 18,240
volt-amps. **Unmanaged demand is 64,176 volt-amps, or 267 amps.**

1. **Minnesota adopted the 2026 NEC on 17 August 2026.** Permits filed on or after
   that date comply with 2026. Article 750 no longer exists; energy management
   moved to **Article 130**, whose Part II covers only systems providing overload
   control, that is, Power Control Systems.
2. **Listing is now explicit and mandatory.** 2026 NEC 130.2 requires an energy
   management system to be listed, and one providing overload control to be listed
   and labelled specifically as a Power Control System. The product standard is
   UL 3141.
3. **220.70 was replaced by 120.7, and it is stricter.** A Power Control System may
   be used in a service calculation, but the control setting must be determined by
   qualified persons and set to no more than 80 percent of the overcurrent device
   rating for the monitored circuit.
4. **The Emporia Vue is a monitor, not a controller.** Emporia's own help centre
   describes it as tracking electricity use in real time. Its certifications are
   UL/cUL 61010-2-030 for measurement equipment and UL 2808 for the current
   transformers. Emporia's certification page lists **no UL 916, no UL 3141, and no
   EVEMS listing at all** — only UL 2594 for the EV chargers.

**Consequence.** The EV group has a defensible path, because Emporia's charger-side
load management is real control and NEC 625.42(A) recognises an EVSE-side energy
management system. **The spa-and-sauna group, the auxiliary strip heat interlock,
and the water heater group have no listed device behind them and a Vue cannot
supply one — it has no relay.** Those three credits should be assumed to fail plan
review.

**Two ways out, and both should be priced.**

- **Buy a listed Power Control System.** SPAN earned the first-in-class UL 3141
  certification in October 2025 and Lumin is also certified. That keeps the 200 amp
  service and puts a real device behind the calculation.
- **Upgrade the service.** In Xcel's Minnesota territory a residential "400 amp"
  service is a 320 amp continuous meter socket with an approved lever bypass;
  above that means a current-transformer cabinet. Metro pricing for 100 to 200
  amps runs $7,700 to $9,500 installed, and $10,000 to $15,000 is a defensible
  budget for 200 to 400 on a house not yet built.

Two smaller items found alongside. **The sauna's omitted GFCI is correct** —
210.8(F) reaches only outdoor dwelling outlets on circuits of 150 volts to ground
or less and 50 amperes or less, and a 60 amp indoor circuit is outside it on both
counts. **But the spa on the same management group is not**: 680.44 requires
ground-fault protection on the outlet supplying a self-contained or packaged spa,
indoors or out, plus a disconnect within sight and bonding per 680.42. Do not let
the sauna reasoning bleed onto the spa circuit. Separately, 2026 NEC 230.70(A) now
requires the service disconnect for a one- or two-family dwelling to be outdoors or
within sight, and explicitly bars remote-control devices.

**The energy storage system is fine on paper and fragile in practice.** The EG4
12kPV carries UL 1741 and the PowerPro WallMount carries UL 1973, 9540A and 9540,
and 14.3 kWh is under IRC R328's 20 kWh per-unit cap. The recurring inspection
failure mode is not the brand but the **configuration**: officials reject
inverter-and-battery combinations that fall outside the specific configurations
named on the UL 9540 certificate. Pull that certificate and match battery count and
model verbatim before ordering. Also note Minnesota requires solar installers to
hold a residential building contractor or remodeler licence.

### BLD-07 — The unvented roof, the painter, and the eave nobody has drawn. **MED · KEEP with two written instructions**

**The assembly is sound and clears its code test with margin.** One correction:
the citation is **R806.5 item 5.1.3**, not 5.3 — there is no item 5.3. Table
R806.5 requires R-25 of air-impermeable insulation in climate zone 6; five inches
of closed-cell foam is R-33 to R-36. Minnesota does not amend R806.5.

**Instruction one, for the painter.** R806.5 item 2 prohibits an interior Class I
vapour retarder on this ceiling, and it is a code violation rather than a
preference. The only drying path for the batt cavity is inward — the deck is
capped by fully-adhered butyl above and foam below — so a vapour-barrier primer
creates a moisture trap with no recovery. **There is no published repair short of
removing the coating.** This is a Minnesota exposure specifically, because the
local habit is polyethylene and vapour primer everywhere, and Minnesota's own
R702.7 amendment reinforces it for frame *walls*. Put "no Class I vapour retarder
and no vapour-barrier primer at ceilings, IRC R806.5 item 2" in the painting
section of the spec and on the reflected ceiling plan, and name the permitted
primer by product. Note the same amendment's second sentence: **a Class II vapour
retarder is permitted only when specified on the construction documents**, so if
one is wanted anywhere it has to be drawn.

**Instruction two, for the insulator.** R806.5 requires the air-permeable
insulation to be installed **directly under** the foam, meaning physical contact.
The documented callback is exactly that interface: batts that fail to stay against
the cured foam leave an air space and convective currents. The remedy is a
deliberately thicker, compressed batt — an R-30C nominally 8 1/4 inches deep
compressed into the 6 7/8 inches this bay leaves. **That must be on the drawing or
the batt sub will order R-21 and leave a gap.** Related and unpublished anywhere:
whether the sprayer reliably fills the shadow behind an I-joist top flange so the
foam stays continuous against the deck. Treat that as an inspection item.

Also worth knowing: five inches of foam is four passes overhead at the
industry lift limit with cure time between, and the foam needs a thermal barrier
per R316.4 wherever the space is used for anything but servicing utilities. Gypsum
satisfies it; the batt does not.

**The zero overhang is better defended than it looks, and the eave is not drawn.**
The classic ice-dam mechanism needs a cold shelf where meltwater refreezes past the
heated envelope. With zero overhang there is no shelf, and Minnesota's R905.1.2
ice barrier requirement of 24 inches inside the wall line is far exceeded by a
fully-adhered deck membrane. What roofers actually object to is the wall and the
ground: no-overhang metal dumps snow against cladding and windows, and without
gutters it slides off the edge, which is acceptable only where no door is below.
The durability rule of thumb is that above roughly 30 inches of annual rain,
no-overhang walls want detailing that is bang on, and the Twin Cities sit at that
threshold. **That compounds directly with BLD-01b: no overhang plus no sheet
water barrier puts the entire water-management burden on the sprayed foam and the
liquid flashing at the openings.**

**And one detail nobody has drawn.** No roofer commentary, manufacturer detail or
code text was found for standing-seam eave termination with **no fascia**. A
standing seam panel normally hooks a cleat fastened to fascia or drip edge. How
this panel terminates with neither fascia nor gutter is a shop-drawing question for
whoever roll-forms it, and it is the first detail to put in front of the roofer.

Two items the engine does not grade: the roof deck oversails the last rafter and
spans the wall girts, a cantilever nothing checks; and the rafters hang off the
ridge on 38 hangers rather than bearing at the high end, so the printed span table
does not apply and `structural.rafter_span` is correctly UNKNOWN at both spacings.

### BLD-08 — Split verdict: the heat pumps are right, the ERV scheme is off-catalog. **MED**

**Three separate outdoor units is good practice, not a red flag — KEEP.** The
building-science literature actively prefers it in a cold climate. A multi-zone
outdoor unit bottoms out near 35 percent of maximum capacity, above the
shoulder-season load of a good envelope, with efficiency collapsing; the explicit
recommendation is to use two or three smaller single-zone systems instead of one
oversized multi-zone. A multi-zone is also a single point of failure for the whole
house. A Twin Cities contractor will probably push brand substitution rather than
architecture change.

**But the equipment data has a hole — OWNER CALL.** Gree publishes 24,000 Btu/h at
95°F and **16,500 Btu/h at 17°F**, with an operating range to −22°F. **No published
capacity at 5°F, −13°F or −15°F was found**, and "reliable heating down to −22°F"
is an operating range, not a capacity. The FLEXX Ultra could not be confirmed on
the cold-climate heat pump list. `houses/catlin/CLAUDE.md` states 21,000 Btu/h read
at −15°F; that number's provenance should be checked against a certified rating
before the Manual J is considered closed.

**Warranty is a real, unbudgeted cost.** Gree's warranty statement gives 10 years
parts and compressor only where the unit is purchased and installed by a certified
Gree Select Dealer and registered within 60 days; otherwise 5 and 5. Both tiers
require installation by a licensed contractor and exclude labour and faulty
installation. **Owner-supplied from an online reseller forfeits the ten-year tier
by definition**, and the trade default on owner-supplied equipment is refusal on
liability grounds.

**The ERV distribution is the item to reconsider — SIMPLIFY.**

- **Radial semi-rigid is not a Twin Cities practice.** Every local contractor page
  found sells an "air exchanger" — Lifebreath, Broan, Bryant — with no manifolds and
  no home runs. Zehnder lists no Minnesota or Upper Midwest dealer at all, routing
  buyers to factory design. The accepted local workaround is tying the unit into the
  air handler return plenum.
- **Broan does not sell a 75 mm radial system.** The AI Series has 6-inch round
  ports, and Broan's own manual advises going *up* to 8 inch above 200 cfm with long
  runs or many elbows. No Broan literature blesses a manifold arrangement, and no
  manufacturer, Zehnder included, publishes a maximum number of 75 mm runs per unit.
  Zehnder's ComfoTube is the only radial semi-rigid product sold in the USA.
- **The rating point is unverified.** Broan's page says only "up to 210 CFM" with
  no static table, and one distributor lists the unit at **210 cfm at 0.2 inches
  water gauge**, contradicting the 0.4-inch figure the design works from. The
  authoritative check is the HVI directory's net-supply-at-0.4-inch column, which is
  a downloadable spreadsheet. **Run that lookup before the duct scheme is
  committed.**
- **Capacity is not the risk; balancing is.** At Zehnder's nominal 18 cfm per
  75 mm tube, 21 terminals is 378 cfm of nominal capacity against a roughly 206 cfm
  unit. The hard part is balancing 21 low-flow radials, and the commissioning skill
  for that does not exist locally.
- **Cost.** A conventional Twin Cities heat recovery ventilator installed is
  "$2,600 and up." Radial systems quote at $9,200 to $9,500 for a 2,200 square foot
  house. One builder saved $7,000 by using two simple units instead. ComfoTube alone
  at 21 runs of about 30 feet is $800 to $1,200 before manifolds, grilles and
  labour.

**The three radiant zones need arithmetic, not a decision.** IRC R303.10, adopted
unamended in Minnesota, requires heating capable of 68°F at three feet above the
floor at the design temperature. Two zones are the sole heat in their room, and
**Schluter states DITRA-HEAT is intended as a secondary heat source**, with floor
output of about 43 Btu/h per square foot at its 9 cm minimum spacing — the 200 W/m²
figure is a *wall* spacing. Effective output over *room* area falls to roughly 25
to 30 Btu/h per square foot once the keepouts around tub, vanity and cabinets are
deducted, which is marginal for a zone 6 room with exterior walls. Not all
manufacturers agree — nVent claims primary-heat service — but either way the
resolution is a per-room heat-loss calculation at −15°F, and there isn't one.

### BLD-09 — Four foundation methods. **MED · OWNER CALL**

Cast-in-place 8-inch and 12-inch, a 6-inch-core ICF garage stem, segmental block
retaining, and the EPS-form concrete deck.

**Cast-in-place and ICF under one contractor does exist in this market** — MCM
Concrete, Master Concrete MN and Van Haren all advertise both — so those two
consolidate. The block retaining walls are a hardscape trade, and per BLD-03 the
EPS deck has no local installer at all. So the job still needs at least three
unrelated subs plus a shoring-competent framer.

**Each extra pour has a published cost even before the crew's setup day.** Short
load fees run $50 to $250 per yard under the minimum, which is typically eight to
ten yards, commonly quoted as $75 to $125 on an order under three or four yards.
Add $50 to $150 delivery per trip, $50 to $100 for a weekend, and $200 to $600 for
a pump where access is poor. A small pour can absorb $400 to $1,200 in short-load
penalty alone, and a planning figure of $500 to $1,500 per extra small pour in
truck and pump charges is defensible. Contractor labour mobilisation per extra
pour is not published anywhere; the trade guidance is simply to bundle work into
one contract.

### BLD-10 — Seven cladding materials, three scopes, and a rule with no enforcement. **MED · SIMPLIFY**

Three standing-seam profiles, board-and-batten, PBR panel, corrugated, and a flat
PVDF aluminium band. BLD-01a removes one. The remaining question is whether three
standing-seam profiles are three products or one.

**This is probably three separate scopes, not one crew.** These are different skill
classes rather than different products. Exposed-fastener PBR and corrugated screw
straight through the face, which makes them the fastest and cheapest to install.
Standing seam depends on clip spacing, substrate, underlayment and seam type, and
a crew that gets clip spacing wrong produces oil canning that no later tightening
removes. Locally, standing seam is a sheet-metal roofing trade, residential steel
siding is a separate exteriors trade, and the flat aluminium band is a brake-metal
shop item. **No Twin Cities contractor advertising all five was found.** The
practical test is to bid it as one scope and see who declines.

**The aluminium rule has manufacturer backing, so write it into the contract.**
Western States' own install guide states that panels and flashings should never be
installed in contact with dissimilar metals, which turns a house rule into a
contract clause. Two mechanisms, and they are different:

- **Aluminium against concrete is alkaline attack, not galvanic.** The Aluminum
  Design Manual M.7.3 requires aluminium to be painted where it contacts concrete
  or masonry unless the concrete stays dry after curing — and a foundation stem in
  a splash zone is exactly the wet case the exception does not cover. Current
  practice has moved off bituminous coatings to a nonporous isolator plus a hemmed,
  drained standoff so the aluminium never sits in a wet joint. The garage stem
  band's 1/4-inch vented standoff is the right instinct; it needs the isolator named
  in the spec as well.
- **Aluminium against steel panel** wants separation by thick elastomeric tape,
  non-absorptive plastic or sealant. Note that **a PVDF finish is not itself an
  isolator** where a sheared edge or a fastener hole exposes bare metal, and
  anodising alone is usually insufficient. Stainless fasteners into aluminium are
  fine, because the stainless area is small relative to the aluminium.

**The enforcement gap is real and nothing closes it.** No evaluation report,
install guide or inspection provides a field check. The only lever is a drawn
detail at every aluminium-to-steel and aluminium-to-concrete junction with a named
isolator product.

### BLD-11 — Two thousand board feet of owner-milled hardwood. **MED · OWNER CALL**

Four species, 39 derived window stools, 17 shelf banks of which several need
edge-glued panels because one board cannot make the width, four custom elm posts,
six site-built soffits. This is a schedule risk more than a quality one, and it
sits on the critical path to closing walls. Already correct and worth preserving:
baseboard and casing stay a priced lump rather than a knife grind, because a
custom profile cannot amortise over one house.

### BLD-12 — No soils report, and for the piers it is not optional. **HIGH · SIMPLIFY**

Every soil input is a presumptive IRC table value and the soil classification came
from a survey of the wrong county. `code.site_parcel_is_surveyed` is one of the
three standing FAILs.

**Three separate code hooks reach this design, and one of them is mandatory.**

- **IBC 1803.5.5 is not discretionary.** Where deep foundations will be used a
  geotechnical investigation *shall* be conducted, and it must name the bearing
  stratum, the recommended deep-foundation types and installed capacities, spacing,
  installation procedures, field verification of installed bearing capacity, and
  load-test requirements. The two augered bell-bottom piers are deep foundations.
- **IRC R401.4** leaves it to the building official where questionable soil
  characteristics are likely — and the discretion belongs to the official, not the
  designer.
- **The retaining walls** leave the four-foot exemption entirely (BLD-02), so
  their engineer needs a real friction angle, unit weight and bearing value. A
  wrong-county soil classification is the single input a reviewer is most likely to
  challenge.

**And it gates the pier detail rather than following it.** The bell assumes a
cohesive excavation that stands open. Twin Cities glacial outwash sand voids that
assumption, and only borings resolve it.

**Cost and turnaround are both small.** A residential geotechnical report in the
Twin Cities runs about $2,500 to $5,000 all in; component pricing is $700 to
$1,500 for two borings, $300 to $900 per additional boring, plus $200 to $500 for
utility locating. Minnesota's own published maximum-cost standard for hollow-stem
auger borings, Minn. R. 2890.3300, is $1,128 for the first 25 feet. Expect two to
six weeks to schedule pending Gopher State One Call clearance, one or two days of
field work, and one to two weeks to the report — call it four to eight weeks from
authorisation, with verbal recommendations sooner. Braun Intertec and American
Engineering Testing both run in-house drill crews in the metro.

**This is the cheapest risk reduction in the file and it is on the critical path
to BLD-02.** Authorise it first.

### BLD-13 — The manual-verification register. **HIGH · KEEP as a checklist**

`haus check` does not grade these, and assuming it does is the failure mode. Each
must be walked by hand before the work it covers is buried:

1. The eave roof-deck cantilever over the wall girts.
2. `Dowel` geometry against the two footings each dowel names.
3. Thermal-break continuity — a `Footing` resolves to one blob with no polygon.
4. `Flashing.back_side` on the six garage stem drip runs. One wrong wall points a
   drip *at* the wall at zero FAIL.
5. Aluminium-to-steel and aluminium-to-concrete contact anywhere on the envelope.
6. Equipment clearance envelopes — HP1's disconnect working space, and HP3's back
   clearance, which is 8 inches against a manufacturer minimum of 12 and can never
   be more in that slot.
7. Placeable against register, and placeable against framing member.
8. Any run routed through a `CHASE` rather than a modelled `Soffit`. The engine
   declares this an unchecked case.
9. Wall device depth — nothing grades a device against the wall face it sits in.

### BLD-14 — Documentation that disagrees with the source. **LOW · SIMPLIFY**

Three sections of `houses/catlin/CLAUDE.md` are marked stale pending the
north-entry rewrite, and `params/breezeway.py` still carries retired names for
elements that no longer exist. A sub reading a stale note is a callback with no
design cause behind it.

---

### BLD-15 — What the owner-GC may legally self-perform, and what it costs to hire out. **MED · KEEP as a checklist**

Not a design finding, but it bounds every other row in this file.

**The licensing position, with the statutes.**

- **Building contractor licence: exempt.** Minn. Stat. 326B.805 subd. 6 exempts an
  owner of residential real estate who builds or improves property they occupy or
  will occupy. There is no holding period, but the exemption does not apply to
  building for resale or speculation, and **speculation is presumed if the owner
  builds or improves more than one property in any 24-month period**.
- **Electrical: exempt, narrowly.** Minn. Stat. 326B.33 subd. 21(f) exempts an
  individual who **physically performs** electrical work on a dwelling they own and
  actually occupy, **provided the dwelling has a separate electrical utility service
  not shared with another dwelling**. "Physically performs" means it cannot be
  extended to a hired unlicensed helper, and it exempts licensing only — the permit
  and the state inspection still apply.
- **Plumbing: exempt at state level, but a city can switch it off.** Minn. Stat.
  326B.46 subd. 1(a) permits unlicensed work on premises owned and actually occupied
  by the worker **unless forbidden by local ordinance**. Check the specific
  jurisdiction; the state exemption alone does not settle it.
- **Mechanical: no state licence**, though contractors must carry a $25,000 bond,
  and Minneapolis and St. Paul both require a competency card.
- **Solar: Minnesota requires the installer to hold a residential building
  contractor or remodeler licence.**

**Statutory warranty.** Minn. Stat. ch. 327A attaches the one, two and ten year
warranties to a **sale**, and the obligor is the vendor. Building for your own
occupancy creates no vendee and no warranty date, and once occupied the building is
no longer "a new building, not previously occupied," so a later resale is not a
sale of a "dwelling" under the chapter. **The risk case is building and selling
without ever occupying** — that plausibly makes the owner a vendor owing the full
warranty, and it breaks the 326B.805 exemption at the same time. No Minnesota
appellate decision was found either way. Worth one conversation with counsel.

**Pricing. No supplier publishes an owner-builder differential, and that absence is
the finding.** The best available figures: on materials, dealer tiering gives 5 to
10 percent to a buyer above $25,000 a year and 10 to 15 percent above $100,000, so
a one-house owner-builder should expect **0 to 10 percent off retail against 15 to
22 percent for a production builder**. On subcontract labour the gap is larger and
is about risk and scheduling rather than volume — the figure that recurs in the
trade is **at least 20 percent more to work directly for a homeowner**, on the
grounds that owner-builders are unprepared when the sub arrives, there is no repeat
work, and schedule priority goes to general contractors. Working range: materials
0 to 10 percent worse, subcontract labour 10 to 20 percent worse.

**Inspection sequencing, and the two ordering rules owner-builders trip over.**
Minn. R. 1300.0210 subp. 6 sets the statewide list: footing, foundation before
backfill, under-floor before concrete, rough-in before concealment, frame after
roof and firestopping, energy, lath, final. The two rules that bite:
**rough-in electrical, plumbing and mechanical must all be signed off before the
framing inspection**, and **all three trade finals must be complete before the
building final.** The trade inspectors are a separate queue with their own lead
time. Scheduling is the permit holder's responsibility and the windows are tight —
Woodbury, for one, requires electrical inspections to be booked by 9:00 a.m.

No jurisdiction publishes an owner-builder failure list. The nearest real data is
the industry finding that roughly 45 percent of residential field inspections
produce a violation, with the top ten led by missing documentation on site,
misplaced anchor bolts, braced-wall errors, improper joist bearing, deck ledger
flashing, and missing fire blocking. **Five of those ten are coordination failures
between trades** — precisely the seam a superintendent normally closes and an
owner-GC owns personally.

### BLD-16 — The jurisdiction profile names a code edition that does not exist. **LOW · SIMPLIFY**

The engine runs this house against a profile named `mn-2024`. **There is no 2024
Minnesota residential energy code.** The edition in force is the 2020 Minnesota
Residential Energy Code, Minn. R. ch. 1322, effective 31 March 2020; the only 2024
energy code adopted is the *commercial* one. A 2024-cycle residential code is still
in rulemaking, expected late 2026 or early 2027.

The ventilation arithmetic the profile uses is right — Minn. R. 1322.0403 Equation
R403.5.2 gives total cfm as 0.02 times conditioned square feet plus 15 times
bedrooms plus one, with the continuous rate at least half the total and never below
40, balanced within 10 percent. Only the label is wrong. Rename the profile, or at
minimum note in `checks/code/mn_residential/profile.py` which edition each rule
actually came from, before a reviewer reads "mn-2024" on a printed sheet and asks.

**Separately and more urgently: the electrical side of that profile is now a
cycle behind.** Minnesota adopted the 2026 National Electrical Code on
17 August 2026. See BLD-06.

## Probable KEEPs, named so the audit does not spend time on them

- **The second-floor mixed deck.** Open-web trusses west and I-joists east looks
  like gratuitous variety and is not: the truss field is what lets three trades
  cross without boring anything, and both fields are the same depth so the split
  needs no movement joint or finish break.
- **Interior trim as a priced lump** rather than milled, for the reason above.
- **The window rough-opening ladder.** Three caps on the 16-inch module is a
  constraint that has already paid for itself in the 40-to-15 unit-to-type ratio.

## What is still genuinely unanswered

These were researched and came back empty. Each is a phone call or a spreadsheet
download, not more searching.

1. **Does the SDWS22800DB clamp up through a 6.5-inch side member?** Simpson's
   published values assume a 1.5-inch side member and a 2 3/4-inch thread. This is
   the one item in the file that could invalidate a structural note, and it should
   go to Simpson's engineering line and to `notes/catlin_truss_engineering.md`
   before anything else here is acted on. (BLD-01b)
2. **Will a Minnesota electrical inspector accept an energy-management credit in
   the service calculation, and under what listing?** No Minnesota bulletin,
   amendment list or guidance was published for the 2026 code. Call the Department
   of Labor and Industry electrical unit. (BLD-06)
3. **The Broan B210E75RT's certified net supply at 0.4 inches water gauge.** The
   directory publishes that column but renders it in JavaScript; the spreadsheet is
   downloadable. One distributor contradicts the design's figure. (BLD-08)
4. **The Gree FLEXX Ultra's capacity at 5°F and −13°F, and its cold-climate
   listing status.** Manufacturer submittals blocked automated access. Look it up
   manually before closing the heat-loss calculation. (BLD-08)
5. **Whether one Twin Cities crew installs all the metal systems**, and any Twin
   Cities price for *exterior-side* spray foam. Neither is published. Bid it and
   see. (BLD-01b, BLD-10)
6. **Hot-dip galvanized rebar minimum order, lot charge and lead time** — not
   published by any Midwest supplier. Must be quoted. Also fix the A767 class:
   the design names Class 1, and Class 2 is the class intended for fabrication
   after galvanizing. (BLD-02)
7. **Whether the local jurisdiction's ordinance permits owner-performed
   plumbing.** The state exemption can be switched off locally. (BLD-15)
8. **Whether ch. 327A reaches an owner-builder who sells without occupying.** No
   Minnesota case law either way. Ask counsel. (BLD-15)
9. **A standing-seam eave termination with no fascia and no gutter.** Nothing
   published anywhere. Shop-drawing question for the panel fabricator. (BLD-07)

## Follow-on work this audit suggests but did not do

- **A `checks/buildability/` package** so the census in section 1 re-runs forever
  rather than being a snapshot. It needs no new tier, no schema change, and no
  decision that contradicts an existing one: register into `Tier.ADVISORY` with a
  `buildability.*` id prefix beside `mep.*` and `electrical.*`, and
  `checks/pytest_plugin.py` gives it test coverage for free. The shape to copy is
  `checks/advisory/checks.py::_note` — a fact reported, not a verdict, because a
  check nobody can drive to zero is a check nobody reads. The half-built precedent
  is `advisory.window_size_variety`; `plans/12-m1-emit.md` planned a door-size
  sibling that was never written.
- **A trade-visit count over `takeoff/tasks.py`.** Section 3 had to be derived by
  hand because most rows carry no storey, so twelve of thirteen trades report a
  single `building` package. Fixing the storey attribution would make the
  mobilisation count a computed number, and it feeds directly into the project
  management work deferred at the foot of `plans/TODO.md`.

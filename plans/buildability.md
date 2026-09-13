# Buildability — the owner-builder audit

Started 2026-09-10. The house is about to be built with the owner as general
contractor. `plans/cost-options.md` asks what each feature costs. This file asks a
different question about the same features: **how likely is each one to be built
correctly, on the first try, by the subs actually available, without the owner
standing over them?**

Nothing here is decided. The plan as authored is the plan; this is the menu.

## Method — read this before comparing any row

**The baseline, re-struck 2026-09-10 after the bug-fix pass below.**
`haus takeoff houses/catlin` prints a construction total of
**$810,802 – $1,671,945** (with furnishings, $819,612 – $1,719,595). That is
materially below the $917,729 – $1,895,004 baseline `plans/cost-options.md` still
carries, so do not mix a row from that file with a row from this one without
re-striking it. The check report is **1,131 pass · 1 fail · 45 unknown ·
31 not applicable** of 1,208 encoded rules, and the calculation package carries
**58 engineered items, 27 of them open**.

**The first draft of this file quoted a stale baseline and it is worth saying why.**
It reported three standing FAILs where there is one, and 42 engineered items where
there are 58. The house moves daily and this file does not. **Re-read the numbers
before acting on a row**, and treat every figure here as of its stated date. The
one standing FAIL is `code.site_parcel_is_surveyed` — see BLD-12, which is the
finding about exactly that.

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
| draft (engine computed, ratio within capacity) | 31 |
| OVER | 0 |
| INCOMPLETE (computed in part, an input missing) | **20** |
| NO LOCAL CALC (deferred to a designer of record) | 7 |
| covered by a seal in `engineering.toml` | **0** |
| **Total** | **58, of which 27 open** |

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

**`haus tasks` cannot answer this today, and the reason is narrower than the first
draft of this file claimed.** It is not that twelve of thirteen trades collapse into
one package — all thirteen carry a `building` item and eleven also carry real
per-storey items. It is that **roughly three-quarters of the low estimate sits in
`building` by value**: walls are ~100% there, plumbing and mechanical 96%, earth
95%, drainage 90%, roof 75%, openings 65%.

The mechanism is a join, not missing data. `takeoff/tasks.py::_tags_by_row` keys a
work item on `(estimate section, price key)`, so two per-storey rows of the same key
merge and their tags span storeys, which sends the merged row to `building`. The
placeables takeoff already groups by storey and the tasks join throws that away.
Fixing it changes the granularity of the estimate join itself, not just the task
export, so it is named here and deliberately not attempted. The visit count below is
derived by hand from the design.

| Trade | Distinct mobilisations | Why more than one |
|---|---|---|
| Concrete | **at least 5** | footings and basement walls · garage ICF stem (a different sub) · slabs · the cast deck over the LiteDeck form, which needs a pump after sill plates are set · sunken-garden walls, piers and the six cast columns · then the deck cap's coating pass (a cream polish until 2026-09-12 — BLD-03), which cannot happen until the building is closed and the cap has passed its ASTM F2170 RH test |
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
| BLD-01a | Drop board-and-batten; one wall panel product | ~~HIGH~~ LOW | **KEEP — resolved 2026-09-11** | re-strike |
| BLD-12 | No soils report, and the piers make one mandatory | HIGH | **SIMPLIFY** | +$2,500 to $5,000 |
| BLD-06 | Service load calc rests on unlisted devices | HIGH | **RESOLVED 2026-09-12 — Class 320 service** | +$2.5k–5k, 320 A service |
| BLD-01b | The girt-and-block exterior wall | HIGH | **KEEP + ENGINEERED (2026-09-12)** | screw −$0.34/ea |
| BLD-03 | Two floor systems on the main storey | HIGH | **KEEP — resolved 2026-09-12** (product decision + finish change) | cut declined; the −$7,536 to −$13,486 stands as the measured price of the feature |
| BLD-02 | The freestanding concrete structure | HIGH | **RESOLVED 2026-09-12 (BLD-12 still gates the piers)** | unpriced |
| BLD-05 | ~~Suite bathroom drain, 0.062" of slack~~ **`PR-B-BATH-DRAIN` at the code minimum, under a slab** | HIGH | **SIMPLIFY — re-struck + graded 2026-09-12** | ~free if timed right; the branch itself cannot be bought out |
| BLD-13 | Conditions the engine does not grade | HIGH | KEEP as checklist | — |
| BLD-08 | ERV radial scheme off-catalog; heat pumps fine | MED | **RESOLVED 2026-09-12 — standard parts, provenance closed** | **+$766 to +$1,520** measured; the conventional-ERV comparison + warranty stay owner calls |
| BLD-07 | Unvented roof: painter, insulator, undrawn eave | MED | KEEP + 2 instructions | — |
| BLD-04 | 13 one-off assemblies, 10 one-off door types | MED | **SIMPLIFY** | unpriced |
| BLD-10 | Seven cladding materials, three scopes | MED | **SIMPLIFY** | unpriced |
| BLD-09 | Four foundation methods | MED | OWNER CALL | ~$500–1,500/extra pour |
| BLD-11 | 2,000 board feet of owner-milled hardwood | MED | OWNER CALL | unpriced |
| BLD-15 | Owner-GC licensing, pricing, inspection order | MED | KEEP as checklist | −10 to −20% on subs |

**The two measured simplifications together are −$9,240 to −$18,121** (as of
`286ef997`; see BLD-01a on why its engineering-register figure needs re-striking).
**BLD-03 is no longer one of them** — resolved 2026-09-12 as KEEP, so its −$7,536 to
−$13,486 is now the measured *price of a feature that is being bought*, not a saving on
offer. It stays quoted in the ablation below and in `plans/cost-options.md`'s premium table,
which is where a price belongs.

**METHOD NOTE — the baseline was re-read on 2026-09-12 and this file's is stale.**
`haus check houses/catlin` reads **1245 pass / 0 fail / 45 unknown / 30 N/A**, and the
register holds **no INCOMPLETE item at all**. Every `1085 / 3 / 46 / 21` in the tables
below, and every register count derived from it, is from `286ef997` and is quoted as
history. Re-strike in a detached worktree at HEAD, per §2's own method, before quoting a
dollar figure from here.

**What the 2026-09-10 bug-fix pass closed**, leaving every simplification decision
open: BLD-16 (the profile name, and an `nec_base` field so the 2026 NEC adoption is on
record), BLD-14 (eight stale cross-references, three comments naming deleted constants,
six wrong-county citations), BLD-07's citation (2015 item numbering under a declared
2018 base, in the engine as well as the house), BLD-02's A767 sequence, and BLD-13
item 4 — which is now graded, and caught four inverted drip runs nobody had found.
Three claims in this file did not survive verification and are corrected in place: the
baseline, the spa GFCI, and the trade-visit count.

**What 2026-09-12 closed on top of that:** BLD-01a (verdict reversed, the panel stays),
BLD-01b (the girt screw is now a graded `girt_screw` register item), BLD-04 (measured,
and the assemblies given provenance), and **BLD-02** — answered on all four findings, with
the cage restated as one purchased part and the bar spec restated as a goal plus a ladder.
BLD-02's own column count, retained height and cage count did not survive verification
either, and are corrected in place: **six** cast columns not four, **10'-4"** retained, and
**twelve** identical cage sections not eight.

**If you do only three things:** authorise the soils report (BLD-12 — it is now the LAST
thing gating BLD-02, whose other four findings are closed, and it is code-mandatory for the
piers), get the foam's own E331/E2178 data for the
WRB approval (BLD-01b finding 3), and
and upsize the service (BLD-06 — **done 2026-09-12**: a Class 320 meter-main, not a
listed Power Control System).

## 5. The findings in full

### BLD-01a — Drop board-and-batten. ~~One wall panel product.~~ **KEEP — RESOLVED 2026-09-11**

> **VERDICT REVERSED, 2026-09-12 (owner). The panel stays.** This finding was written
> against a house that had already moved: commits `0925db4f` and `b4b8afb3` on 2026-09-11
> named the product, closed the screw, and collapsed the register entry. Specifically —
>
> * **The panel is a named product**: **Metal Sales BB75-1111, 11" coverage, 24 ga PVDF**,
>   on-label over "Lumber – 1x or thicker" OPEN framing in the manufacturer's own words,
>   which `Material.open_framing_source` now carries verbatim.
> * **The twenty INCOMPLETE items are gone.** They are **one draft group item,
>   `wall_panel/W-A-N1`**, computing bending d/c **0.31** against the manufacturer's
>   published 58 psf at 24" and withdrawal d/c **0.12** from NDS 2018 §12.2. The register
>   holds no INCOMPLETE item anywhere. **The stated failure mode — "twenty engineered items
>   no engineer can close" — no longer exists.**
> * **The cladding screw is 2", Type 17 wood point**, which closes the Metal Sales
>   "1/2" past the inside face of the support" variance outright. It is no longer open.
>
> **Three paragraphs below are SUPERSEDED and are kept only as the record of what was
> searched.** The 20"-coverage claim, the ESR-4730 reading and the "Metal Sales publishes 10
> and 12 only" finding were all against a product this house does not specify: BB75-1111 is
> **11"**, and ESR-4730 is Western States' report for a different panel. What survives of
> that research is its conclusion — that no report covers a concealed panel on open wood
> girts — and that is exactly why `wall_panel` is an engineered item rather than an UNKNOWN.
>
> **The published alternative, recorded and not taken.** **AEP Span Flush Panel**, IAPMO UES
> **ER-309** Tables 6.6/6.7: 24 ga, 12" coverage, **66 psf ASD negative at 24" over "Lumber
> (DFL) 1" min" open framing**. That is a published span table for this exact condition, so a
> Flush Panel would leave the register entirely as a `PublishedSpan` — the PBR precedent. It
> is not taken because the owner wants the batten line and the item computes at 0.31. See
> `notes/board_batten_girt_span.md` §7.9.
>
> **The dollar delta is kept, re-labelled.** −$1,704 to −$4,635 at `286ef997` is now the
> **cost of the appearance**, not a saving on the table, and it needs re-striking at HEAD
> before it is quoted.


| | |
|---|---|
| element | twenty `layer_materials=` overrides in `plan/storeys/{main,second,attic}.py`, plus the corner-trim material in `params/roof_trim.py` |
| what a sub sees | Two different concealed- and exposed-fastener metal wall panels on one house, on different elevations |
| failure mode | ~~A permit failure: twenty engineered items that no engineer can close~~ **SUPERSEDED** — withdrawal is now computed per NDS §12.2 and the item is draft |
| risk | ~~**HIGH** — it is twenty of the twenty-five open items on the calculation package~~ **LOW as of 2026-09-11** — one draft group item, d/c 0.31 |
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

**This is the highest-leverage single edit in the file, and its register figure
needs re-striking before it is quoted.** The measurement above was taken at
`286ef997`, against a register of 42 items of which 25 were open. That register now
holds 58 items of which 27 are open. **The twenty INCOMPLETE items this edit removes
are unchanged** — they are still twenty, still all `wall_panel/*`, still all the same
missing input — so the edit still empties the INCOMPLETE column outright. What has
moved is the denominator, and "25 open to 5" is no longer the right sentence. The
dollar delta is as of `286ef997` and should be re-struck the same way.

**The research makes the case stronger than the model does.** The design's own
note records that no manufacturer publishes the withdrawal allowable. Three
further facts came back:

- **SUPERSEDED — this is the wrong panel's report.** ESR-4730 is Western States'; the
  house specifies Metal Sales BB75-1111. Kept as the record of what was searched.
  **The one evaluation report that covers a board-and-batten panel forbids this
  application outright.** Western States' ESR-4730 §5.2 and §4.2 both state the
  panels "must be backed by a solid substrate." Its Table 2 evaluates their
  board-and-batten at **8-inch width with support fasteners at 12 inches maximum**,
  allowable negative pressure 48 psf. This design is 20-inch coverage at 24-inch
  girts, outside the evaluated geometry on both axes.
- **The manufacturer's own install guide contradicts its own evaluation report.**
  The guide says the panel is used over open purlins and that "most details in this
  guide are shown with panels attached to open framing." The guide sells you open
  framing; the report the official reads forbids it.
- **SUPERSEDED — BB75-1111 is 11" coverage and it is the specified product.**
  **The specified panel may not exist at the second source.** Metal Sales'
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

**And that caveat is the one thing in this finding that aged perfectly.** "The screw's grip
in a 1 1/2-inch flat treated girt is the limit, and nobody publishes that either" was
right — and as of 2026-09-12 it is a named item, `girt_screw/W-A-N1`, with the head
pull-through of that very girt governing at d/c 0.487. See BLD-01b finding 1.

### BLD-01b — The girt-and-block exterior wall. **HIGH · KEEP + ENGINEERED (2026-09-12)**

> **OWNER DECISION: the wall stays, and the screw goes engineered — with the screw
> replaced.** Finding 1 below is REAL and it was unanswered, which is why this is not a
> "keep as is". Finding 4 is WRONG and is corrected. Findings 2 and 3 stand, and 3 is now
> stated as an open approval item rather than a generic argument.
>
> **What changed in the house.** The crossing screw is **FastenMaster TimberLOK 8"
> (TLOK08), ICC-ES ESR-1078**, replacing the SDWS22800DB, and it is graded as
> `girt_screw/W-A-N1` — three limit states over all 36 `standoff="block"` walls as one
> design, head pull-through governing at **d/c 0.487**. The screw's numbers are authored on
> the girt band's `FramingSpec` and the takeoff bills exactly the part the record stamped.
> `notes/catlin_truss_engineering.md` §3 is the oracle and was rewritten with it.


| | |
|---|---|
| element | `EXT_2X6` (34 walls) and `PLANT_EXT_2X6_HUMID` (2) in `houses/catlin/plan/assemblies.py` — **36 walls**, one design |
| what a sub sees | Four inches of spray foam on the *outside* of the sheathing with no housewrap, horizontal treated 2x4s floating in mid-air on stacks of loose offcuts, and one long screw holding each stack |
| risk | **HIGH** — buried, structural, and it is the cladding attachment for the whole house. Now GRADED, which is not the same as reduced |
| trade | Framer, foam sub, siding crew, window sub. Four visits and an inspection hold |

**Scale of the operation, from the takeoff:**

| Item | Quantity | Priced |
|---|---|---|
| ~~SDWS22800DB~~ **TLOK08** 8" timber screws | ~~1,118~~ **1,131**, one per crossing | ~~$1,286 – $1,957~~ **$916 – $1,244** |
| `3-2x4:kdat` block stock (3,354 offcuts, stacked in threes) | 344 LF | $1,514 – $2,305 |
| `2x4:kdat` flat girts | 2,790 LF | $5,580 – $8,928 |
| 4" exterior closed-cell spray foam | — | $22,003 – $34,093 |
| **Standoff system subtotal** | | **$8,379 – $13,190** |

The material price is not the risk. Cutting and stacking 3,354 offcuts, marking the
stud line across each girt face as it is laid, and driving 1,131 blind eight-inch
screws is per-piece work, and `plans/TODO.md` already records this exact class of
under-billing for the window bucks.

**Four findings from outside the model. The first is a specific, checkable defect.**

1. **ANSWERED, AND THE FINDING WAS RIGHT. The screw could not clamp the joint, and the
   screw has been replaced.** The mechanism is exactly as stated — thread engaged in both
   members prevents clamp-up and jacks the girt off the block — and nothing in the house
   answered it, because nothing in the house had ever written down the thread length.
   Three corrections to the arithmetic, none of which changes the verdict:
   * **The thread is 3", not 2 3/4".** The right report is **IAPMO UES ER-192 Table 7**
     (the SDWS), not ESR-2236 (the SDS, which the house's own note cited). Every SDWS22
     threads 3" whatever its overall length.
   * **The clamped stack is 6.0", not 6.5".** Girt 1-1/2" + block 4-1/2". The 1/2" plywood
     is **nailed to the stud**, so it is on the stud's side of the joint and is not a member
     being drawn together; counting it is counting the anchor as part of the load. At 6.0"
     the 8" SDWS leaves 5" of plain shank and stands **1" of thread inside the stack**.
   * **The pull-through observation was the sharpest part of the finding.** The 1-1/2" side
     member the table assumes IS the girt — a single flat 2x4 — not the 6.5" through-count.
     That is now a graded state, and at **200 lb** against a 97.4 lb demand it is the
     **governing** one of the three.
   **The fix: TimberLOK 8" (TLOK08), ESR-1078 Table 1A — 2" thread**, so 6" of plain shank
   spans the 6.0" stack exactly and 1-1/2" of thread lands in the stud, above the report's
   1.25" minimum. Coating rated for ACQ-D ≤ 0.40 pcf (§4.1.7 / Table 6). It is also $0.34
   cheaper per screw. Rejected: SDWS221000DB (10" restores engagement; the owner wants 8"),
   Rothoblaas HBS/TBS 8 mm (3-1/8" thread at every length, ESR-4645 dry service only), HECO
   TOPIX-plus (no US report). **HeadLOK 8" (HLGM8) is the recorded alternate** — same 2"
   thread, 600 lb pull-through — held back only because ESR-1078 Table 2 wants 2.0" embedded
   thread for it, which needs the 1/2" ply counted and the report is silent on sheathing.
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
   **STANDS, and it is now acted on rather than noted.** "Engineered by default" is exactly
   decision #65's condition, and as of 2026-09-12 the connection has a name
   (`girt_screw/W-A-N1`), a computed demand, three read capacities and a fingerprint a seal
   pins to. The same reasoning the DESIGN-LOG records at "Three requirements left the
   engineering register" (L178-181) applies in reverse here: no published table reaches it,
   so it stays in the register.
3. **STANDS, AND IT IS AN OPEN APPROVAL ITEM — stated as one rather than argued.** The
   product is now named: **Huntsman Heatlok HFO High Lift, ICC-ES ESR-4073**. But **ESR-4073
   does not evaluate WRB at all**, so naming the product does not close this. The only report
   found granting ccSPF a WRB listing is **Icynene ProSeal Eco (ESR-3493 §4.6, 1-1/2"
   minimum), and it expired in 2021**. Approval therefore runs through **Minn. R. 1300.0110**
   on **Huntsman's own ASTM E331 and E2178 data for the product actually bought** — which is
   this finding's own instruction, and it is not yet done. It is recorded in
   `notes/catlin_truss_engineering.md` §9, in the assembly comment and in `prices.toml`, so
   the next reader cannot take §1's "the foam is the water plane" as a closed question.
   The BASF paragraph below is kept as the shape of what an acceptable report looks like.
   **Foam as the water barrier is achievable, but only product by product.** BASF's
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
4. **CORRECTED — the 1 1/2-inch lift figure does not apply to this foam.** It is legacy
   SPFA guidance. **ESR-4073 §4.2 permits 6-1/2" per pass**, and the product's TDS gives the
   ladder by substrate temperature: **6.5" at or below 70 °F, 4" at 70–80 °F, 3.25" above
   80 °F**. So **"one 4-inch application" holds below 80 °F** — which is the design, and the
   labour case the whole one-tier wall was built on. What is real is the temperature condition:
   spray above 80 °F and it becomes two lifts and a second mobilisation. (Heatlok HFO **Pro**
   is a different product, ESL-1372, at 2"/pass; do not let a supplier substitute it.) The
   rest of this finding stands and is worth keeping — the substrate minimum, the wind
   shutdown, and **specify a minimum thickness, never an average**.
   ~~Industry guidance caps a lift at about 1 1/2
   inches with a cool-down between, so 4 inches is three passes minimum.~~ Exterior
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

### BLD-02 — The freestanding concrete structure. **HIGH · RESOLVED 2026-09-12**

| | |
|---|---|
| element | `params/sunken_garden.py` — retaining walls `W-SG-W2`/`E2`/`S`/`ARCH`, columns `PT-SG-BR1`/`BR3`/`BF1`/`BF3`/`COL`/`FCOL`, grade beam `W-SG-BRKBM`, piers `FT-SG-COL`/`FCOL` |
| what a sub sees | Cantilever-T retaining walls up to **10'-4"** of retained height (`notes/sunken_garden_court_free_body.md`), an arched load-bearing wall, two bell-bottom augered piers, a 19-foot buried grade beam, and **six** 12-inch round columns fixed at their bases with galvanized cages in fibre tube — only the **four balcony corners** are saddle-collar formed on a wall top; `PT-SG-COL` and `PT-SG-FCOL` are tubes in a hole |
| risk | **HIGH** — structural, buried, and the largest remaining block of engineering once BLD-01a closes |
| trade | Commercial cast-in-place concrete, not a residential foundation crew |
| **delta** | `unpriced` — but see the four cost mechanisms below, none of which is in the model |

**RESOLVED 2026-09-12 — two of the four were worth acting on, and the other two get an
answer rather than a change.** The engineering is not the gap this finding took it for:
every court item is a `draft` record with a published d/c, and the two things a seal really
adds are already named as deferred items. What *was* real is procurement, and it is now
stated as a part number and a ladder.

1. **Permitted, engineered walls — agreed, and already the state.** Every court item is a
   `draft` record in the register (`out/calcs/02-item-register.md`): `retaining_wall` at
   d/c **0.92** on sliding, `deck_post` **0.02–0.26**, `spread_footing` **0.60**. The
   finding's dollar figures are the cost of the stamp, and the stamp is BLD-01a's line item
   — not a second scope. Nothing to change.
2. **Cantilevered-column system at R = 1.25 — the ASCE 7 Ch. 12 framing does not reach this
   site.** Minnesota's mapped values (S_S ≈ 0.04 g, S_1 ≈ 0.02 g) put the lot in **SDC A**
   under ASCE 7 §11.4.2 (S_1 < 0.04 and S_S ≤ 0.15), and §11.7 then sends an SDC A structure
   to §1.4 alone: F_x = 0.01 W, about **50 lb per column**, against the **153 lb** wind
   shear these columns already carry. There is no R, no 15%-axial limit and no overstrength
   foundation case to apply. **Values to be confirmed at the USGS/ASCE Hazard Tool for the
   lot's own coordinates before the calc package goes out** — the site has not been
   queried, only the statewide picture. The one *valid* residue of the finding is its last
   sentence: base fixity is earned, not drawn. That is exactly the two **deferred** items
   already on the register, `column_support/W-SG-W1` and `column_support/W-SG-E1`
   (`out/calcs/03-open-items.md` §A). Cite them; nothing new is added.
3. **Circular ties are a shop order — agreed, and it becomes the win.** The design had
   already assumed a stock cage (`notes/balcony_moment_columns.md`), so the answer is to
   make it **one purchased part**. The authored cage — (4) #5, #3 ties @ 10", 2" cover on a
   6-5/8" bar circle — is **8.0" out-to-out of ties** (6.625 + 0.625 + 2 × 0.375), which is
   the trade's "8-inch cage", not the 12-inch cage this finding priced. *A 12" cage in a 12"
   column is zero cover; it was the wrong part.* Bolsinger's **stock** 8" cage (4 #4, #3 @
   12", 3–8 ft, **$49–77** black, tied or welded, Cascade IA to MN in 15–20 business days)
   is **not a drop-in**: 4 #4 = 0.80 in² against ACI 318-19 §10.6.1.1's 1.131 in² floor, and
   12" ties exceed §25.7.2.1's 16d_b = 8" for a #4. The authored #3 @ 10" is exactly 16d_b
   for a #5. So the part is a **custom 8" cage in a stock format**: **one cross-section,
   twelve off** — six court columns and the six north-entry pours, which carry the same
   cage — lengths per pour, **tied not welded**. Rebarfab Inc (720 First St SW, New
   Brighton MN, 651-633-3337, in-house detailing and fabrication) or a Bolsinger custom.
   Cost floor is the **$49–77** stock row; budget roughly **$90–140 each** at (4) #5 with
   galvanizing. *(The finding said eight cages; twelve is the measured count — all six
   north-entry pours share `ENTRY_PIER_CAGE`, not only the two roof columns.)*
4. **"HDG bar is a special order with no published stock" — exaggerated, and the goal was
   the thing worth restating.** The A767 *after-fabrication* sequence this file added is
   only **one of two routes**. **ASTM A1094** (CMC GalvaBar, Catoosa OK) is a stocked mill
   product that "ships in days" and **bends and fabricates after galvanizing without
   repair**; ACI 318-19 §20.2.1.7.2 lists A767 and A1094 alike and ψ_e = 1.0 either way.
   The A767 route has two Minnesota plants — **AZZ Galvanizing, Winsted (800 6th St S) and
   NE Minneapolis**. So the fabricator picks the route and **names it on the order**. The
   spec now states the **goal** (long-term durability of exposed concrete in F3 + C2, which
   the mix alone meets: w/cm ≤ 0.40, f'c ≥ 5,000, 6% ± 1.5 air, 2" cover) with the accepted
   ladder under it — **owner, 2026-09-12: galvanized either standard preferred → black bar
   at the stated cover and mix accepted as a documented written exception → epoxy and
   stainless stay refused.** Galvanizing is the owner's margin, not a code requirement, so
   the spec can now flex on schedule without losing what it was for.

**Not resolved, and cited rather than folded in: BLD-12.** The belling precondition below
still has no soils report behind it, and it gates the two augered piers.

The original finding, for the record:

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
   **The specification point here was stated wrongly in the first draft and is now
   fixed in the house.** A767's Class 1 and Class 2 are *coating weights*, not a
   bend-order distinction, so "use Class 2 instead" was not the answer. The real gap
   was that the design named a class and never named a **sequence**, while these cages
   are shop-bent — #3 ties to a 6-5/8" bar circle. What the rebar order needs on it is
   *galvanize after fabrication*, plus coating repair per **ASTM A780** at any field
   cut or bend, and the note that a **welded** cage leaves A767 altogether for
   ASTM A123. `houses/catlin/CLAUDE.md` and the court note now say so.

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

### BLD-03 — Two floor systems on the main storey. **HIGH · RESOLVED 2026-09-12**

**RESOLVED 2026-09-12 — KEEP, with a product decision and a finish change. Three of the
four findings do not survive contact with the manufacturers' own documents, and one of them
was already contradicted by this repo's `prices.toml`, which is the later and better-sourced
record.** The concrete stays: the thermal mass under the south glazing, `FH-M-DINING`'s
in-slab radiant embed and the acoustic separation over `RM-B-PLAY-N` are what it was bought
for, and none of them is replaceable by wood. What changed is that the deck now names a
product, carries a published span row the engine grades, and takes a finish with less
execution risk than the polish.

**Verdict: SIMPLIFY → KEEP.** The roll-up row and the summary above are updated; BLD-03 no
longer sums into the measured simplifications.

**What the deck IS now.** **BuildDeck (BuildBlock) is the basis of design.**
`plan/assemblies.py` already sourced both its span basis *and* its R-value from BuildDeck
while naming LiteDeck as the product — the change makes the model self-consistent and picks
up two documents LiteDeck's free literature does not publish.

| | LiteDeck (LiteForm) | **BuildDeck (BuildBlock)** |
|---|---|---|
| Span table for a 10" deck + 4" cap | not in the free manual (the 2013 design book 403s) | **yes** — 20 ft @ 2-#5 = 62 psf LL |
| Shoring design | **the installer's**, per ACI 347R, in writing | **PE-sealed** (McLaren Engineering Group, File 150609.00, 2016) |
| Rebar schedule | "installer responsible, per ACI 318" | **published** — #3 stirrups 4' each end @ 5" o.c., 12"x12" #4 grid |
| ICC-ES report | none found | none found |
| Nearest source | Benchmark Foam, Watertown SD (~3h) | Ostertag Cement, Shakopee MN (a BuildBlock distributor; **unverified for BuildDeck**) |
| Depths, R as installed | 8" base + 2/4/6" top hat | 8" R-23, **10" R-29**, 12" R-36 |

LiteDeck and Insul-Deck stay **named alternates** — the depth-matching argument in
`params/main_deck.py` is product-neutral and that is the point — but a substitution has to
bring its own span table, its own shoring design and its own R per section with it.

**Finding by finding.**

1. *No MN dealer* — **PARTLY STANDS.** Benchmark Foam (Watertown SD, ~3h) lists Lite-Deck;
   BuildBlock lists a Shakopee MN distributor. **Both need a phone call to confirm**, and
   neither has been made. This is the one finding that survives essentially intact.
2. *Off common use, no ICC-ES* — **the ICC-ES half STANDS**, for all four systems examined.
   Note the trap: `ESR-1269` is cited on Amvic's AmDeck page and evaluates **wall** forms,
   not decks. Nobody publishes an evaluation report for an EPS floor deck.
   What does NOT stand is the conclusion drawn from it — "the building official will be
   reading manufacturer engineering plus a PE stamp". A published allowable-load table is a
   **prescriptive read**, the same act as reading an IRC table. It is now IN the model:
   BuildDeck's 10" deck / 4" cap / 2-#5 row (20'-0" at 62 psf) is quoted onto
   `SL-M-DECK.published_span` and graded by the new `structural.slab_published_span`, which
   refuses the row if the section, the product or the demand drifts away from what it was
   read at. Before this the deck was graded by **nothing at all** — no `engineering/` kind
   for a suspended slab, no check reading a slab's span. That is the substantive change this
   finding produced.
3. *Shoring is the installer's liability* — **DOES NOT SURVIVE.** BuildDeck publishes a
   **PE-sealed** shoring design (McLaren Engineering Group, File 150609.00, 2016): wood stud
   walls at 6'-0" o.c. with 2x8/2x10 joists at 24" o.c., 97 psf dead + 25 psf construction
   live, in place no more than 6 weeks, struck after the 28-day cure. `prices.toml` said so
   on 2026-08-23 and BLD-03 did not read it. **One open question remains for the EOR, and it
   is not a defect:** McLaren used 25 psf construction live load where ACI 347 §2.2.1 asks
   for ≥50 psf live and ≥100 psf combined. 97 + 25 = 122 psf clears the combined floor and
   not the live-load floor. Ask.
4. *Polishing a suspended slab* — **ALREADY DESIGNED AROUND, and now superseded.** The cited
   mechanism is non-uniform **aggregate exposure** following curl, and
   `notes/mixed_deck_movement_joint.md` has specified a **cream** polish — surface paste
   only, ~1/16", no aggregate — since before this audit was written. Superseded regardless:
   the deck now takes a **coating**, and the cream polish is kept in the note and in
   `prices.toml` as the named, costed fallback the owner may revert to at pour time.
   The corrected finish spec, in order: ACI 302.1R **Class 3/7** two-course floor — "Class A"
   is a *formed-surface* class and says nothing about a floor; a **light** steel trowel (ACI
   302.1R's maximum density for a slab receiving an adhered covering); ACI 117's 3/8"-under-a
   -10'-straightedge and **no F-numbers**, because ASTM E1155 §7.2.1 sets a **320 ft² minimum
   test section** and 414 SF cannot carry a meaningful set; wet cure or a cure-and-seal the
   primer bonds through; diamond grind to **ICRI CSP 2-3** (every coating TDS found — Tnemec
   201, Sikafloor-1620/217, Dur-A-Flex, Sherwin-Williams — asks for CSP 2-4, and a
   hard-troweled cream reads *below* CSP 2, so a hone toward 200 grit moves away from
   profile); **ASTM F2170 in-situ RH at 40% of depth as the gate**; a moisture-mitigating
   primer rated to 100% RH; and a matte 2K aliphatic PU topcoat, **roller-applied**, since
   spray moves isocyanate handling to supplied-air.

   **The real risk the coating introduces is moisture, and it is manageable.** The cap dries
   **upward only** (EPS below) and hard troweling collapses capillaries — one study found
   burnished slabs holding >94% in-situ RH for 18 months. Because the deck pours at
   *structure* stage and coats at *finish* stage the 4-5 month conditioned dry is probably
   free, but *probably* is not a test result. Nothing in the engine grades any of this: a
   `floor_finish` is not a `Layer`, so no vapour check sees a near-vapour-tight film over a
   cap that can only dry one way. Recorded in the note.

**And BLD-03's silica paragraph is WRONG, about polishing as well as about coating.**
29 CFR 1926.1153 Table 1 puts a light hone and a full polish in the **same row** —
walk-behind floor grinders with dust collection, **no respirator required at any duration
indoors**. The finding's "APF 10 respirators once the task passes four hours" is not what
Table 1 says for this equipment indoors. Grinding to CSP 2-3 is near-identical work in that
same row, so the silica question does not distinguish the two finishes at all. What IS owed
either way, and the finding is right about, is the written exposure control plan, the
designated competent person, training, and medical exams for anyone in a respirator 30+ days
a year. Corrected rather than transferred.

**Two corrections to the measured ablation below, which otherwise stands and is kept intact.**
The four evicted MEP runs are a real finding and the honest half of this section.

- **Reconcile the two deltas.** BLD-03 measures **−$7,536 to −$13,486**; `plans/cost-options.md`
  says **$6,300–10,700** for the same cut. They are not averaged and neither is wrong:
  BLD-03's is `built` (an ablation in a sandbox at `286ef997`, which also deleted the four
  cast sleeves) and cost-options' is `arithmetic`. **Quote the `built` figure**, and say which
  it is.
- **The fire-rated separation is NOT given up by going to wood.** The original's "also given
  up ... the fire-rated separation over the media room" is wrong.
  `code.R302_13_floor_protection` is satisfied by the 5/8" gypsum, which is continuous over
  both systems either way (`ceiling_below` on the joists, the R316.4 thermal barrier on the
  deck). What is genuinely given up is the **acoustic** separation over `RM-B-PLAY-N`, the
  thermal mass, and the concrete as a finished floor — three real things, and the fourth was
  never at stake.

**What changed in the tree (2026-09-12):** `Slab.published_span` + `checks/structural/slab_span.py`
(the new prescriptive read); `params/main_deck.py` (the row, the BuildDeck docstring, the
coating); `plan/assemblies.py` (`POLISHED_MIX` → `DECK_CAP_MIX`, R-3.125 → R-2.9 for the 10"
section, the stale 4 5/8"/8" comment); `coated-concrete` in `library/materials.py`,
`takeoff/finishes.py` and `checks/integrity`; `prices.toml`;
`notes/mixed_deck_movement_joint.md`; `notes/rebar_backout.md`. **Not done, deliberately:**
authoring the now-sourced cap rebar schedule as a `ReinforcementSpec` — it moves tonnage into
the estimate and lands in the middle of `notes/rebar_backout.md` §3's back-out arithmetic.

The original finding, for the record:

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

**RESOLVED 2026-09-12 — and the count was mostly honest.** Measured, catlin carried 29 wall
assemblies over 143 walls, not 37 over 178 (that count included roofs, slabs, decks and
posts). Exactly ONE pair was a genuine duplicate — the mudroom and stair walls, one wall
authored twice over a stud species — and it is now `INT_2X6_BRG_EXPOSED_PLY` with
`Wall.layer_materials` carrying the species. The two families below are *real* stack
differences and could not be merged, so they were given provenance instead: eight
assemblies became `variant_of` + `substitute` (#35), whose cards name their base and whose
shared layers track it forever. Two dead tags went, one promoted to the library, and
`advisory.assembly_variety` now FAILs a material-only twin and prints the inventory. **28
wall assemblies over 143 walls, 11 used once.** Decision #72 is the rule for keeping it
there; stars were the wrong lever, since `Transition.star` curates only the permit set.

The original finding, for the record:

The lookup burden, not any single assembly, is what generates callbacks for an
owner-GC. Two consolidations look free on inspection and want measuring:

- The four stair-wall variants (`STAIRWALL_INT_2X6_BRG`, since merged, `_TYPEX`,
  `_UNDERSTAIR`, `STAIRWELL_PARTITION_4H`) are one wall built four ways along its
  length. `_TYPEX` and `_UNDERSTAIR` differ only in the Type X substitution and
  both exist for the same R302.7 reason.
- The three sauna liner assemblies (`SAUNA_LINER_INT_2X6_BRG`,
  `_ON_GARDEN_CURB`, `_ON_GARDEN_FRAMED`) differ by what they land on, not by
  what the carpenter builds.

Deliberately **not** on this list: `W-B-CW3`/`W-B-STR2`'s over-specified
steel-stud assembly, which `plans/TODO.md` already records as not worth
re-opening.

### BLD-05 — The suite bathroom drain group. ~~**HIGH · SIMPLIFY**~~ **RESOLVED 2026-09-12 — re-aimed at `PR-B-BATH-DRAIN`**

> **VERDICT RE-STRUCK, 2026-09-12. All three numbers in the original finding are
> engine-internal metrics, not field margins — and the run it names is the sixth *loosest*
> drain in the house.** Measured against the resolved model, not estimated:
>
> | BLD-05 said | What the number actually is | Measured |
> |---|---|---|
> | 0.062" of head slack over 5.75 ft | `HeadBudget.slack_in` — a **search ordering key** (`routing/gravity.py`), computed against a hypothetical arrival at the stack **head** (115.5") from the chord-window ceiling (117.0"). The authored run ties at **112.0"**, on the barrel 3.5" below it. | **3.062" of surplus fall.** 0.779"/ft flattest against a 0.25"/ft minimum — a 3.1× margin. |
> | 1/2" of crown clearance in an 11 7/8" truss | The **conservative whole-leg envelope** — the crown at the leg's high end against the chord ceiling. That high end (y=250.625) sits in the 241.75–254.25 **clear bay**, where there is no truss at all. | **+0.944"** at `joist-0-015-0`, graded at 3" PVC's real 3.500" OD, the tightest of the three truss lines the leg actually crosses. |
> | ties in 0.052" above the collector **invert** | 0.052" above its **centreline** — elevations are centrelines (`model/mep.py`), and §2 of the note said "invert" for one. An ordinary upper-half side entry. | Fine as drawn (+0.052"). |
>
> **So the design is not the problem. The absence of grading was**, and *that* half of the
> original finding was exactly right — for different reasons than it gave. Four conditions
> nobody graded, now graded:
>
> * **`mep.run_member_crossing`** (STRUCTURAL) — nothing graded a pipe, duct or raceway
>   crossing a floor's members. The 8 7/8" window that sets every starting invert on this
>   storey was prose and a router invariant; the note's §6 conceded it outright. Three trades
>   thread that field.
> * **`mep.drain_tie_in`** (CODE) — `drain_tie_ins` silently `continue`d past a branch
>   arriving below its collector, so `accumulated_serves` under-counted and `mep.pipe_sizing`
>   under-sized downstream pipe **with no finding at all**.
> * **`mep.drain_slope_margin`** (ADVISORY) — a run at exactly 0.250"/ft passed as cleanly as
>   one at 0.78"/ft. The field method is rigid standoffs stepped ~1" every 4 ft, so the
>   *surplus* over the minimum is the buildability fact, and the model could not state it.
> * **The MN slope citation was wrong.** The profile cited **IRC P3005.3**; Minn. R.
>   1309.0010 subp. 3.D deletes IRC chapters 25–33, and P3005 is in ch. 30. UPC 708.0 is
>   1/4"/ft at **every** size, and the reduced-slope exception reaches only 4"+ with the
>   building official's approval. The engine's `>3" → 0.125"/ft` row was an IRC row with no
>   Minnesota force. Finding #1 below was right about the code and the engine disagreed with it.
>
> **And the finding was aimed at the wrong run.** Swept over every drain segment against
> MN/UPC's 1/4"/ft at every size, flattest per run:
>
> | margin over min | slope | dia | run |
> |---|---|---|---|
> | **+0.000"/ft** | 0.250 | 3" | **`PR-B-BATH-DRAIN`** — authored `slope_in_per_ft=0.25`, **under the slab** |
> | +0.013 | 0.263 | 3" | `PR-B-WC1-DRAIN` |
> | +0.015 | 0.265 | 2" | `PR-A-STUBATH-SH-DRAIN` |
> | +0.017 | 0.267 | 4" | `PR-B-MAIN-DRAIN` — reads as comfortable only under the deleted IRC row |
> | +0.023 | 0.273 | 2" | `PR-B-KITCH-DRAIN` |
> | **+0.529** | 0.779 | 3" | **`PR-M-S-SUITE-WC-DRAIN`** — the run BLD-05 named, **6th loosest of 30** |
>
> **`PR-B-BATH-DRAIN` is the finding BLD-05 was reaching for.** It sits at *exactly* the code
> minimum with zero margin; its own authoring comment records that at 0.3"/ft "the branch
> arrives BELOW the 4" line's invert" — measured, **0.26"/ft, a 4% overpitch, puts it under
> the main.** Finding #2 below is that the plumber's tolerance runs one way, *toward more
> pitch*, which here is exactly the wrong direction — and it is buried under a slab, which is
> HIGH risk by this file's own definition.
>
> **And it cannot be fixed.** Steepening it 0.05"/ft costs 0.43" of fall over 8.64 ft and
> lands it 0.24" **below** the main — trading an advisory for a real `mep.drain_tie_in` FAIL.
> The main itself runs 0.267"/ft to a **cast** invert at `SP-B-SEWER-EXIT`. The basement head
> budget is genuinely spent, so catlin authors `min_drain_slope_margin_in_per_ft = 0.0` in
> `preferences.toml` with that argument beside it, and every PASS still prints its margin —
> which is what keeps the five thin runs visible without gating on them. The engine default
> stays 0.0625.
>
> **`PR-M-S-SUITE-WC-DRAIN` is not moved.** The decision was to let the check decide, and it
> has: at +0.944" it is not close to the tightest crossing in the house (`PR-B-HW-SUITE`, the
> 1/2" hot line to the suite, is +0.062").
>
> **What the new check found instead, and it is not a drain.** Fifteen crossings sit below
> the chord window on `FS-S-WEST`: `CD-M-DATA-KITCH` and `CD-M-DATA-PORCH`, whose authoring
> comment claimed 3/4" EMT "passes between the 8 7/8" chords without a hole in anything" —
> real EMT is 0.922" OD, not 0.750", so the invert was 0.086" *into* the bottom chord — and
> **thirteen ERV radials**, whose shared `_BAY_Z` put a 4" duct's invert on the bottom of the
> bottom chord. That elevation is correct for the legs riding a bay and 1.5" wrong for the
> south legs that cross. All fixed; see workstream C of the plan.
>
> **The JLC coordination argument survives intact and is now mechanical.** An owner hold
> `insp/truss_mep_review` stands ahead of `site/long-lead-orders` in `inspections.toml`, so
> "reviewed by the plumber before trusses are fabricated" is a blocker the board reports
> rather than a sentence in a document.
>
> **Risk stays HIGH and the verdict stays SIMPLIFY**, on `PR-B-BATH-DRAIN`: a zero-margin
> branch under a slab, in a basement with no head left to give it.

The original finding, for the record:

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

### BLD-06 — The service load calculation rests on devices that are not listed for it. **HIGH · RESOLVED 2026-09-12**

**RESOLVED 2026-09-12 — CLASS 320 SERVICE, and load management retired from the house
entirely.** The premise held: three of the four credits rested on Emporia/software with no
UL 3141 behind them and would not have survived plan review. The exit was not a $2-3k listed
power control system but the service itself — one Class 320 HDLB meter-main with **two 200 A
mains outdoors** (which also answers 2026 NEC 230.70(A)), at ~$2.5k-5k of increment on a
house not yet built. **267.4 A of unmanaged 220.82 demand against 320 A**, no software
anywhere in the calculation. `houses/catlin/DESIGN-LOG.md` §"Electrical service" carries the
derivation; `houses/catlin/CLAUDE.md` §"Electrical service" carries what must stay true.

**Two corrections to the finding below, in opposite directions.**

- **Too optimistic on the EV group.** The finding says "the EV group has a defensible path,
  because NEC 625.42(A) recognises an EVSE-side energy management system". Under the **2026**
  625.42(A) that EVSE-side system must itself be a PCS under Article 130 Part II, and
  Emporia's charger carries UL 2594 / 2231 / 991 and no UL 3141. So **all three** software
  credits were exposed, not two.
- **Too pessimistic on the strip-heat lockout.** 220.82(C)(2)/(4) credits a controller that
  prevents a compressor and its supplemental heat from operating at the same time **in the
  article itself** — no Article 130 device, no listing. `LM-HP1-AUX` was the FLEXX Ultra's
  own outdoor-thermostat lockout and was earnable all along. It is retired anyway, because
  with a 320 A service it buys nothing; the lockout is still SET, as an HVAC control setting
  recorded on `CKT-HP1-AH`.

**And "$10,000 to $15,000" is retrofit pricing.** On a new build the delta is the meter-main
over a plain 200 A socket, a second 200 A load centre, and two short 4/0 Al SER feeders —
all three now priced in `houses/catlin/prices.toml`. Note also that **there is no 225 A and
no 400 A service class**: Xcel MN residential sockets are 200 A or 320 A continuous, both
heavy-duty lever bypass, and "400 A" is trade shorthand for 320 / 0.8.

**What changed in the engine.** `LoadManagement.strategy` is now a constrained literal
(`hvac_interlock` | `noncoincident` | `pcs`) with a `listing` field, and
`takeoff/electrical.py` **refuses** a credit whose basis does not hold — that closes the
"no field for the listing" gap recorded at the foot of this file.
`code.NEC_705_12_interconnection` now reads a panel's own main rather than borrowing the
meter's `service_amps` (at 320 A it would have graded the wrong number), and a new ADVISORY
`electrical.panel_feeder_load` grades each panel's 220.82 demand against its own main, which
is the binding constraint once load is split across two feeders.

**The Article 680 items and the 230.70(A) service-disconnect-location check are NOT closed
here** — they are checking gaps and stay with BLD-13.

The original finding, for the record:

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
  budget for 200 to 400 on a house not yet built. *(Corrected above: that is retrofit
  pricing; on a new build the increment is ~$2,500 to $5,000.)*

Two smaller items found alongside, and **the first draft of this file got the spa
wrong.** The sauna's omitted GFCI is correct — 210.8(F) reaches only outdoor dwelling
outlets on circuits of 150 volts to ground or less and 50 amperes or less, and a
60 amp indoor circuit is outside it on both counts. The worry was that the same
reasoning had bled onto the spa, which 680.44 does reach. **It has not.**
`plan/circuits.py` already authors `CKT-SPA` with `gfci=True`, and `ED-B-SPA-DISC` is
placed on the porch wall. The design was right.

What is true is that **nothing grades it.** `code.E3902_gfci_locations` populates
only from 125 V receptacles, so a 240 V hardwired spa outlet is outside its subject
by construction; no check in the engine cites Article 680 at all, and none grades
the within-sight disconnect or the 680.42 bonding either. So the `gfci=True` on that
circuit is authored data no check reads. That is a checking gap, not a design defect,
and it belongs with BLD-13 rather than here. Separately, 2026 NEC 230.70(A) now
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

**The assembly is sound and clears its code test with margin.** Table R806.5
requires R-25 of air-impermeable insulation in climate zone 6; five inches of
closed-cell foam is R-33 to R-36. Minnesota does not amend R806.5.

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
ridge on 38 hangers rather than bearing at the high end, which is the condition the
printed span table assumes. Since 2026-09-11 `structural.rafter_span` reads that
published row prescriptively (17'-9 3/4" against 18'-4") and carries the hanging
condition on the finding rather than reporting UNKNOWN; ForteWEB still owns the last
word. See `houses/catlin/notes/roof_rafter_span_read.md` §3.

### BLD-08 — Split verdict: the heat pumps are right, the ERV scheme is off-catalog. **MED · RESOLVED 2026-09-12**

**RESOLVED 2026-09-12 — the design was right about the machine and wrong about where to buy
the pipe.** Three of the four items closed against published documents rather than against
judgement; the fourth became arithmetic the engine now does. **Cost and the Gree Select
warranty tier stay open as owner calls** and nothing below decides them.

**1. The rating point was never in dispute — it was one curve read at two stations.**
Broan's B210E75RT spec sheet publishes the whole thing: 214 cfm @ 0.1", 210 @ 0.2", 208 @
0.3", **206 @ 0.4"**, 201 @ 0.5, 199 @ 0.6, 195 @ 0.7, 191 @ 0.8, 184 @ 1.0, 176 @ 1.2 in.
w.g., with **1.3 in. w.g. a hard ceiling** above which the core deforms. The distributor's
"210 at 0.2"" and the design's "206 at 0.4"" are both correct and neither is the rating of
the other. **That closes open question 3** — and it closes it as typed data, not as prose:
`EQ-T-BROAN-B210E75RT.fan_curve` carries all ten points, and `mep.erv_static_budget`
computes what this duct system costs and reads the curve at it. **0.459 in. w.g. worst path,
203 cfm delivered**, the worst path being `DU-M-ERV-R-PLANT` on the extract side. Recovery is
recirculation defrost, HVI-tested at −13 °F with SRE 65 % there, which is already what the
block load uses.

**2. "Radial semi-rigid is off-catalog" was right, and the answer was not to give up the
topology.** Only Zehnder (three US sellers) and Brink through 475 sell 75 mm systems, and
neither has a Minnesota dealer. **Owner decision: no proprietary tube.** But a home run per
terminal off a dampered plenum is documented standard practice — an 8" plenum with 4"
takeoffs — and needs no special part. So the topology is untouched and every piece of it is
now a commodity: **4" galvanized snap-lock radials, 6" galvanized trunks and risers,
fabricated galvanized plenums** (8" inlet collar, N × 4" start collars with butterfly
dampers, mastic-sealed — from any sheet-metal shop, exactly as `EQ-T-ERV-MIXING-BOX` already
is), **4"-collar bath-fan grilles and diffusers**. **4" and not 3" is a CATALOGUE decision,
not a pressure one**: 3" pipe, elbows and start collars are stocked, but 3" dampers and
grilles are a thin, Amazon-grade catalogue. The retype moved the check tally by **not one
finding** — `mep.duct_joist_bay_occupancy` reads the same UNKNOWN at 4" that it read at 3",
because a 12 1/2" clear bay holds two 4" runs with 4 1/2" to spare.

**3. "21 radials not balanceable" was 23 radials, and the risk is the MEASUREMENT.** Adjustment
is a butterfly damper at each start collar — one per port, at the plenum, never at the grille
face. What is genuinely hard is reading 9 cfm: ordinary capture hoods bias **−25 to −30 %
below 150 cfm**, so a **TSI Alnor LoFlo-class** instrument is required equipment and a reading
from a standard hood is not evidence. `notes/erv_static_budget.md` §8 is the commissioning
spec — measure the total across the core rather than by summing 23 low-flow readings, then
balance at the plenum, then report per terminal.

**4. The Gree data hole is closed, and TWO MISREADS WERE FOUND ON OUR OWN SIDE.** The −15 °F
figure is **verbatim**, not interpolated: Gree Extended Ratings catalogue
`GREE_FLEXX_ULTRA_EXTENDED RATINGS_08272024`, model FXU24, 70 °F return, **"MAX OUTPUT"**
band — −22 °F 18,000 Btu/h @ COP 1.49; −15 °F **21,000 @ 1.57**; a flat 24,000 from −5 to
47 °F. The unit **is** on the cold-climate list: NEEP ccASHP **id 504980**, ENERGY STAR Cold
Climate, −22 °F maximum 18,000 Btu/h at **COP 1.36** — same capacity as Gree's own row at a
lower COP, so quote NEEP's when a figure must be conservative. **AHRI 215213329 certifies
SEER2/EER2/HSPF2 and the 47 °F and 17 °F points only**, and pointing at it for the −15 °F
number was always going to fail at a plan review; that scope is now stated in the type's
`source`. **That closes open question 4.** The two misreads: airflow is **760 cfm at 0.5" ESP
(speed 3)**, not "760 at 1.0"" — 850 cfm is the only speed that reaches 1.0" — and the heat
kit is a **field-installed accessory** (5/6/10 kW) the cabinet accepts, not factory-fitted.
Neither changes the decision, and **the interlock argument is untouched**: what the DUC24
lacked was the aux-heat *terminal*, and this cabinet has it.

**5. The radiant zones got their arithmetic, and one of them is short.** Schluter's own
relation is Q = 8.92·ΔT^1.1 W/m²; at the recommended **84 °F floor over a 72 °F room** that
is **22.8 Btu/h/ft²** — not the **18.6** this house quoted in two files (Schluter's *82 °F
example*) and not the **25–30** the finding below assumes. MN 1322's **−15 °F** is confirmed
as the governing design temperature. Against the engine's room-scoped load:
**`RM-S-BATH1` delivers 623 Btu/h against 591 and is covered; `RM-M-BATH2` delivers 399
against 673 and is 41 % short.** **And a bigger cable cannot fix it** — the DHEHK12016
already *draws* 693 Btu/h; what the room lacks is heated FLOOR AREA (29.5 ft² needed, 17.52
available after the manufacturer's own keepouts). The verdict is UNKNOWN rather than a
failure because a room-scoped block load over-states a small interior bathroom on continuous
extract in three named ways. **Also worth knowing: R303.10 does not reach either room** —
R202 excludes bathrooms from habitable space by name — so no inspector will ask, which is
precisely why it had to be asked here. The decision left open is one hour of Manual J, a
second heat source in `RM-M-BATH2`, or accepting it.

**What is NOT closed, deliberately.** **Cost** — but the *retype's own* delta is measured, so
say that first. `prices.toml` is re-banded for what is now specified, and against the
proprietary build it replaces the whole house moves **+$766 to +$1,520** on a $821k–$1.68M
construction total, about **0.1 %**: `ducts` +$720/+$1,439 (rigid pipe is dearer per foot
than semi-rigid in both material and labour — it is cut, crimped and screwed rather than
pushed through a bay), `duct_fittings` +$52/+$104 (41 elbows at 4" instead of 42 at 3"), and
`placeables` −$5/−$20 (a fabricated plenum's material falls and its labour rises).
**Going to commodity parts costs about a thousand dollars and buys a Twin Cities supply
chain.** What is NOT answered is the finding's own comparison — "$9,200–9,500 radial vs
$2,600 conventional" was against the proprietary system nobody is buying now, and re-costing
this build against a conventional single-trunk ERV is a real question nobody has done. **Warranty tier** — 5 parts / 7 compressor standard; 10/10 only through a Gree
Select Dealer with 60-day registration. **Owner-supplied is NOT void**, it simply cannot
reach Select, and both tiers require a licensed installing contractor and exclude labour.
Recorded on the type; still an owner call.

**Three checks came out of this**, all registered in `checks/mep/`:
`mep.erv_static_budget` (ADVISORY — the whole system's Darcy–Weisbach/Colebrook budget
against the published curve), `mep.erv_manifold_ports` (INTEGRITY, **blocks** — it grades
`plan/mep_erv.py`'s "full at 10 of 10" prose), and `mep.room_heat_source` (ADVISORY — item 5).
New schema: `EquipmentType.fan_curve` / `fan_curve_max_static_in_wg` / `duct_ports` /
`port_diameter` (with a load-time validator that refuses a mistranscribed curve),
`AirHandlingProductFacts.static_loss_pa_at_cfm`, `FloorHeat.delivered_btuh_per_ft2`, and a new
`DuctProductType` keyed on the **(material, nominal diameter)** pair `prices.toml`'s `[ducts]`
already qualifies on — one join, so a run cannot price as one product and resist as another.
Oracles: `notes/erv_static_budget.md`, `notes/room_heat_loss_baths.md`.

The original finding, for the record:

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
PVDF aluminium band. ~~BLD-01a removes one.~~ **BLD-01a was reversed on 2026-09-12 and the
board-and-batten stays, so the count is unchanged at seven.** The remaining question is
whether three standing-seam profiles are three products or one.

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
4. ~~`Flashing.back_side` on the six garage stem drip runs.~~ **CLOSED 2026-09-10 —
5. Aluminium-to-steel and aluminium-to-concrete contact anywhere on the envelope.
6. Equipment clearance envelopes — HP1's disconnect working space, and HP3's back
   clearance, which is 8 inches against a manufacturer minimum of 12 and can never
   be more in that slot.
7. Placeable against register, and placeable against framing member.
8. Any run routed through a `CHASE` rather than a modelled `Soffit`. The engine
   declares this an unchecked case.
9. Wall device depth — nothing grades a device against the wall face it sits in.

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

1. ~~**Does the SDWS22800DB clamp up through a 6.5-inch side member?**~~ **CLOSED
   2026-09-12 — no, and the screw was replaced.** It did not need a phone call: IAPMO UES
   ER-192 Table 7 publishes the thread length (3" at every length), the clamped stack is
   6.0" once the stud-nailed sheathing is taken off the girt's side of the joint, and the
   arithmetic closes itself. The screw is now TimberLOK TLOK08 (ESR-1078, 2" thread) and the
   joint is graded as `girt_screw/W-A-N1`. `notes/catlin_truss_engineering.md` §3 was
   rewritten. (BLD-01b finding 1)
2. ~~**Will a Minnesota electrical inspector accept an energy-management credit in
   the service calculation, and under what listing?**~~ **MOOT for this house
   (2026-09-12)**: catlin takes no energy-management credit at all. The Class 320 service
   fits 267.4 A unmanaged, so nothing in the calculation depends on an inspector's reading.
   The question still stands for anyone who wants the credit, and the answer the engine now
   requires is a UL 3141 listing (2026 NEC 130.2). (BLD-06)
3. ~~**The Broan B210E75RT's certified net supply at 0.4 inches water gauge.**~~
   **ANSWERED 2026-09-12 — 206 cfm, and the premise of the contradiction was wrong.** The
   distributor's "210 at 0.2"" and the design's "206 at 0.4"" are the same fan curve read at
   two stations; the spec sheet publishes all ten points and they are now authored as
   `EQ-T-BROAN-B210E75RT.fan_curve`, so nobody re-derives either figure from prose again.
   `mep.erv_static_budget` reads the curve at the static this duct system actually makes:
   0.459 in. w.g., 203 cfm delivered. (BLD-08)
4. ~~**The Gree FLEXX Ultra's capacity at 5°F and −13°F, and its cold-climate
   listing status.**~~ **ANSWERED 2026-09-12 — verbatim, and it IS listed.** Gree Extended
   Ratings `GREE_FLEXX_ULTRA_EXTENDED RATINGS_08272024`, FXU24, 70 °F return, "MAX OUTPUT":
   −22 °F 18,000 Btu/h @ COP 1.49, −15 °F **21,000 @ 1.57**, flat 24,000 from −5 to 47 °F.
   NEEP ccASHP **id 504980**, ENERGY STAR Cold Climate, −22 °F 18,000 @ COP 1.36. **AHRI
   215213329's scope is SEER2/EER2/HSPF2 and the 47/17 °F points only** — say so at plan
   review rather than pointing at the certificate for a −15 °F number. (BLD-08)
5. **Whether one Twin Cities crew installs all the metal systems**, and any Twin
   Cities price for *exterior-side* spray foam. Neither is published. Bid it and
   see. (BLD-01b, BLD-10)
6. ~~**Hot-dip galvanized rebar minimum order, lot charge and lead time** — not
   published by any Midwest supplier.~~ **CLOSED 2026-09-12 — the premise was wrong: there
   are two routes and one of them is stocked.** **ASTM A1094** (CMC GalvaBar, Catoosa OK)
   is a stocked mill product that ships in days and bends after coating without repair, and
   the **A767** after-fabrication route has two Minnesota plants (**AZZ Winsted** and **AZZ
   NE Minneapolis**). The fabricator picks and names the route on the order. What remains is
   an ordinary quote for a fabricated part, not a search for whether the product exists.
   (BLD-02 finding 4)
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
- **A trade-visit count over `takeoff/tasks.py`.** Section 3 still has to be derived
  by hand. The cause is now pinned: `_tags_by_row` keys a work item on
  `(estimate section, price key)`, so per-storey rows sharing a key merge and their
  merged tags span storeys, which sends about three-quarters of the low estimate to the
  `building` package. The placeables takeoff already carries a storey the join throws
  away. This was examined in the 2026-09-10 pass and deliberately not attempted,
  because changing the slot granularity changes the *estimate* join and mints new task
  GlobalIds — the fix is a project, not a patch. It feeds the project management work
  deferred at the foot of `plans/TODO.md`.

- **Article 680, and a 230.70(A) service-disconnect-location check.** Nothing in the engine
  cites Article 680, so the spa's GFCI, its within-sight disconnect and its 680.42 bonding
  are authored and ungraded, and `code.E3902_gfci_locations` cannot reach a 240 V outlet by
  construction. Nothing grades where the service disconnect is, either. **Both move wholly
  under BLD-13.** The other half of this item — `LoadManagement` having no field for the
  *listing* of the device doing the controlling — is **CLOSED** by BLD-06's 2026-09-12
  resolution: `strategy` is a constrained literal, `listing` exists, and an unearned credit
  is refused rather than applied.

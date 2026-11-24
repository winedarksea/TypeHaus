# A2: raised-garden segmental retaining walls (`tiered_retaining/W-RG-*`)

Reviewer A2 · 2026-11-22 · report only, no repo edits, no haus or pytest runs.
Scratch scripts are in `out/review/scratch/A2_srw/`: `srw_check.py` (the independent free body), `variants.py`, `ab27.py`, `snow.py`. The Allan Block manual was fetched and its text extracted to `ab/abcomm.txt`.

Sources read: `calcs/tiered_retaining.md`, `appendix/tiered_retaining*.md`, `04-assumptions.md` §tiered_retaining, `engineering/{segmental_wall,srw_gravity,srw_tiers,srw_backfill,tier_surcharge,soil}.py`, `notes/raised_garden_srw.md`, `notes/sunken_garden_court_free_body.md` §4c/§4d/§9/§13, `notes/foundation_aggregate_and_backfill.md` §7, `params/raised_garden.py`, `plan/landscape.py`, `params/landscape_gardens.py`, and `engineering_gap_review_2026-09-18.md`.

Fetched primary sources:
- AB Commercial Installation Manual (allanblock.com/PDF/ABCommManual.pdf), read from the PDF text: Table 1.3 p.10, the p.11 sample, Table 2.1, p.59 Steps 1–4, p.60 "Terraces", Tables 6.2/6.3.
- Minn. R. 1300.0120 subp. 4 A(4) (revisor.mn.gov).
- IBC 2018 §1610.1 and the IRC 2018 / MN 2020 R404.4 text (UpCodes).

---

## Headline

1. **The engine's sliding arithmetic is right.** I rebuilt it from first principles and reproduced every number on the sheet. **The basis it cites is not right.** These walls hold 40", 36" and 37" of unbalanced fill. IRC R404.4, the section every row cites for its FS 1.5, applies only to walls retaining *in excess of 48 inches* of unbalanced fill (or over 24" tall *and* resisting lateral loads in addition to soil). None of the five is in R404.4's scope. Nothing in the adopted code requires an engineered design for them. The repo already knows this: `params/raised_garden.py:296-302` authors `unbalanced_fill` at 40" precisely so the walls stay under R404.1.1/R404.4's 48". Yet `segmental_wall.segmental_walls()` registers any wall with fill > 0 as an engineered item.
2. **A published-table route exists.** AB Table 1.3 (Level, Clay 27°, 12° AB Stones) allows 3'-6" exposed, cap included. With one small change (add AB Capstones and drop the wall one cap height) every leg reads 3'-4" exposed or less, cap included. This is the owner's preferred answer. Details in G1.
3. **If the item stays engineered, the 1.538 rests on three choices a PE will challenge:**
   - φ = 27.8° back-solved from the IBC EFP at the low unit weight.
   - μ = tan φ (0.528) instead of IBC 1806.2's presumptive 0.25.
   - 12" of wall rock credited at 36° by length-weighting.

   Change any one and the wall drops below 1.5. The effective horizontal pressure graded is 22.5 psf/ft, which is 56% of the IBC Table 1610.1 value the sheet cites as its source. §1610.1 calls that value a *minimum* absent a geotechnical investigation.
4. **The cheapest robust engineered fix is 24" of wall rock instead of 12".** That is about 8–9 cy, replacing terrace fill already authored as granular. Sliding goes to 1.75 at 110 pcf and 1.91 at 130, with the 12" topsoil cap taken as native. It even reaches 1.62 at AB's own clay 27° / 120 pcf. No engine change is needed.

---

## Findings

### F1 · ERROR (wrong code basis) · every sliding/overturning row, `segmental_wall.py:67`, `:291-294`; sheet header "Basis", R1–R13
- **What.** Every graded FS row cites "IRC R404.4" for the 1.5 requirement.
- **What the code says.** R404.4 (2018 IRC, unamended in the MN 2020 code, UpCodes) covers walls "not laterally supported at the top and that retain in excess of 48 inches (1219 mm)" of unbalanced fill, or walls over 24" that resist lateral loads in addition to soil.
- **Evidence.** Authored `unbalanced_fill`: BLOCK, EAST, WEST 40"; WEST-BALCONY 36"; EAST-BALCONY 37". The terrace is a planting bed with no surcharge (owner rule, `params/raised_garden.py:63-81`). The runnel and leader on the east return add no lateral load. Even the free body's 48" (which counts the embedment) is not "in excess of" 48".
- **Effect.** The item is outside R404.4. The code mandates no FS 1.5 calculation, and therefore no engineered item.
- **Confidence.** High on the text. The applicability argument rests on the authored terrace staying unloaded.
- **Class.** DECISION, see G1. If the free body is kept as corroboration, the minimal SMALL-FIX is in `segmental_wall.py:67` and the three `LimitState` citations at `:291-294`: "IRC R404.4" → "NCMA/AB gravity practice, FS 1.5 (IRC R404.4 not triggered: unbalanced fill ≤ 48")". No ratio moves.

### F2 · REVIEWABILITY (a contradiction a PE will stop on) · `friction_coefficient 0.25` vs the governing μ = tan 27.8°; `segmental_wall.py:360`
- **Why both print.** `inputs` always prints `base.friction_coefficient`, the IBC 1806.2 class 4 row for GM, at 0.25. Where a pad φ is authored, `_end()` (`:280-284`) actually uses `μ = tan(min(36°, φ_ground)) = tan 27.818° = 0.5276`. The 0.25 is dead data on the sheet and in the fingerprint inputs, and the μ actually used is printed nowhere as a number.
- **What μ = 0.25 would give.** On the same thrust: FS 0.25 × 525.06 / 180.09 = **0.729** at 110 pcf, 0.724 at 130 pcf.
  - The oracle note's "0.575" (`raised_garden_srw.md:263`) is stale. It is the AB Classic number; for AB Stones it is 0.729.
- **Should 0.25 govern?** Under the IBC presumptive regime (§1806.1: higher values need substantiating data), 0.25 is the presumptive coefficient for class 4. Taking tan φ = 0.528, 2.1× that, with no geotechnical investigation is a method choice: NCMA/AB practice. AB's own p.11 sample uses `(W + Fv) tan φ`. But φ here is not a measured or chart value either; it is synthesized from the EFP (F3).
  - Since R404.4 does not apply (F1), IBC Ch. 18 presumptives are not mandated for this wall. They are mandated only if one chooses to design to them, and the sheet's basis line claims to.
- **Confidence.** High.
- **Class.** SMALL-FIX for the presentation, plus DECISION on the basis:
  - (a) `segmental_wall.py:360`: print `Quantity("friction_coefficient_used", mu, "", 0.001)` from the governing end, and either drop the 0.25 or rename it `ibc_1806_2_coefficient_unused`. No ratio moves; the fingerprint changes.
  - (b) Fix the note at `raised_garden_srw.md:261-264`: 0.575 → 0.729.
  - (c) Resolve the basis through G1. A chart read removes the IBC presumptive frame from this item entirely.

### F3 · ERROR-unconservative relative to the cited basis (method mixing) · `srw_gravity.phi_from_efp`, `segmental_wall._end`
- **The two pressure models.**
  - The sheet cites IBC Table 1610.1 (40 psf/ft, GM). §1610.1: these loads "shall be used as the minimum design lateral soil loads unless determined otherwise by a geotechnical investigation".
  - The engine back-solves a Rankine φ from 40 psf/ft at an assumed γ (27.8° at 110, 32.0° at 130), then re-applies Coulomb with δ = ⅔φ, a 12° batter, and a two-zone wedge crediting the rock.
- **Effective horizontal EFP actually graded:** 2·P_h/H² = **22.5 psf/ft** at 110 and 23.1 at 130, i.e. 56–58% of the cited minimum.
- **Read literally**, the code value (40 psf/ft, horizontal, over the 4.0' free body) gives P_h = 320 plf and W = 504.4:

  | μ | FS sliding |
  |---|---|
  | tan 27.8° | 0.83 |
  | 0.25 | 0.39 |
  | tan 36° | 1.15 |

  So no gravity SRW of this size passes on the code values the sheet names.
- **Soil class.** Presumed GM (Ramsey County till, read regionally). The excavation note simultaneously presumes OSHA Type A *cohesive* clay (`foundation_aggregate_and_backfill.md` §7a), and that note flags the disagreement itself (line 17).
- **Coupling.** The back-solve ties low γ to low φ by construction. Run independently at AB's own chart condition (clay 27°, earth backfill 120 pcf, AB p.67 design parameters), the graded section gives sliding **1.32** with 12" of rock (`ab27.py`).
- **Confidence.** High on the arithmetic. The severity depends on which frame governs.
- **Class.** DECISION:
  - (A) Chart route (G1), with AB's soil model. Recommended.
  - (B) Keep the free body but declare the soil frame honestly: "φ ≥ 27° per AB Table 1.3/2.1 clay row; IBC 1610.1 not used because R404.4 does not apply". Then grade at φ = 27°, γ 110–130, which needs the 24" rock fix (F7) to pass.
  - (C) A geotechnical report.

### F4 · Sliding free body, rebuilt independently · verified
`srw_check.py` §1, standalone, reproduces every graded number:

| | 110 pcf (governs) | 130 pcf |
|---|---|---|
| φ (from EFP) | 27.818° | 31.966° |
| critical plane ρ, rock share, φ_eq | 49.706°, 0.3935, 31.212° | 52.384°, 0.4480, 33.821° |
| P_a (wedge) | 181.27 plf | 187.18 |
| P_h = P cos(δ−ω) / P_v = P sin(δ−ω) | 180.09 / 20.66 | 184.71 / 30.28 |
| W = 130 × 0.97 × 4.0 | 504.40 | 504.40 |
| N = W + P_v | 525.06 | 534.68 |
| μ = tan min(36°, φ) | 0.5276 | 0.6240 |
| **FS sliding** | **1.538** | 1.806 |
| FS overturning | 2.020 | 2.018 |
| q (e in kern, B = 0.97') | 603.9 psf | 606.0 |
| course shear (wedge at 3.333') | 120.52 plf, FS 5.35 | 125.73, FS 5.13 |

Answers to the brief's question 1:
- **Height the thrust acts over:** the full 4.000' free body, i.e. 3.333' retained plus 0.667' embedded, to the underside of the base course. No passive is credited on the embedment (conservative).
- **Horizontal force:** P_h = P_a cos(δ−ω), with δ−ω = 18.545° − 12° = 6.545°.
- **Vertical force:** P_v = P_a sin(δ−ω), downward. It is counted in N for sliding and in the restoring moment.
- **Resolution direction.** I checked the sign geometrically: on a back face battered toward the fill, the face normal tilts up by ω and wall friction acts down the face, so P sits δ−ω below horizontal. This is correct, and more conservative than AB's own `cos δ` resolution (AB's gives 1.73 at the same inputs).
- **Coulomb check:** K_a against AB's p.11 sample gives 0.2199 vs 0.2197.
- **Sliding plane:** the underside of the base course, with μ from the weaker of the pad and the ground.

### F5 · GAP · sliding plane at the pad base not checked; the "weaker interface" is applied at the upper plane
- **What.** μ = tan(ground φ) is applied to N and P at the underside of the block (−4'-0"). The ground interface is actually the pad's underside (−4'-6"), where the thrust is larger and N also carries the pad and the soil over its 6" overhangs.
- **Evidence** (`srw_check.py` §6, 110 pcf):

  | Plane and assumption | FS |
  |---|---|
  | Block on pad, μ tan 36°, sheet thrust | 2.12 |
  | Pad on native, N₀ ≈ 916 plf, Coulomb δ = φ on a vertical virtual back | 1.81 |
  | Pad on native, Rankine (δ = 0) on the virtual back | 1.19 |

  The engine's combination is AB's simplified method and sits between these. It is neither a bound nor a check of the lower plane.
- **Confidence.** Medium; it depends on the virtual-back assumption.
- **Class.** SMALL-FIX (reviewability): add one sentence to the record notes, "Sliding is checked at the base-course underside with μ of the weaker of pad and ground (AB/NCMA simplified); the pad-base plane is not separately checked." Or close it by making the ground under the pad granular (F8).

### F6 · GAP (foundation) · the apron founds on the court's backfill, with no compaction spec
- **What.**
  - The court excavation lays back 3/4:1 with its lip 10.7' past the bed edge (`foundation_aggregate_and_backfill.md` §7a/§7b). The whole apron (pad at x 3.0–5.0' off the court axis, bottom −4'-6") stands on 4–5 ft of re-placed *native spoil*. Native spoil is what §7b bills as backfill.
  - No compaction requirement was found for that spoil. Only the #57 is described, and it is "seated, not Proctor-compacted".
  - AB Table 2.1 p.15 (fetched): "If the soils at the base of the wall have been disturbed - i.e. excavated and replaced - it is imperative that these soils are properly compacted before construction begins." AB p.59: "Site Soils Engineer should verify that a proper base is established."
- **Effect.** The bearing row (604 psf against a presumptive 2,000 for *native* class 4) and the ground φ both assume a material that is not what the wall stands on. A dry-stack wall tolerates some settlement, but differential settlement over a clay fill wedge that deepens toward the court is the realistic failure mode here.
- **Confidence.** High that it is unspecified; medium on consequence.
- **Class.** DECISION:
  - (a) Cheapest: specify the court backfill in a 4'-wide strip under each apron leg, from the court heel up to the pad, in ≤8" lifts compacted to a stated density with field tests. This is spec text only.
  - (b) Place that strip as granular fill (about 77 LF × 3 ft × 4.6 ft ≈ 1,060 cf ≈ 40 cy). This also makes the pad-base interface granular: μ ≥ tan 34° at both planes, which closes F5 and lifts the governing sliding row toward 2.1 (block on pad).

  Recommend (a) at minimum.

### F7 · ERROR-unconservative (thin margin on unverified inputs) · the 1.538 depends on three choices
`srw_check.py` §4, `ab27.py`, `variants.py`, 110 pcf unless noted:

| Variant | FS sliding |
|---|---|
| Graded | 1.538 |
| Wall rock at 34° (AB Table 3.1 "crushed stone 34°+") | 1.470 ✗ |
| No rock credited | 1.300 ✗ |
| φ = 27° (AB clay row) at 110 / 120 / 130 pcf | 1.44 / 1.32 / 1.23 ✗ |
| μ = 0.25 | 0.729 ✗ |
| 50 psf ground snow on the 2.1' bed strip (`snow.py`) | 1.29 ✗ |

The snow row is a sensitivity only. Practice on applying ground snow to a landscape backfill varies, AB's "Level" row makes no allowance for it, and it is UNVERIFIED as a required case. But the sheet should say it was considered.

**Fixes, with numbers.** In order of cost, if the item stays engineered:

| Fix | 110 pcf | 130 pcf | Other |
|---|---|---|---|
| **24" of wall rock** (top 12" taken as native topsoil, `variants.py`) | **1.753** (OT 2.30) | 1.911 | 1.62 at AB clay 27° / 120 pcf; 1.50 at the 27° / 130 corner; ~1.55 with 50 psf snow |
| Rock to the court face (2.97') | same as 24" | same as 24" | the topsoil band then governs |
| Specify the terrace fill below the topsoil at φ ≥ 34° (it is already authored "compacted granular terrace fill", `raised_garden.py:429`) | 1.83 (native μ) | 1.85 | 2.15–2.5 if the pad also sits on granular (§5) |
| Lower the free body to 3'-8" | 1.70 | | conflicts with the court-top datum |
| Deeper embedment | worse (H grows; no passive) | | |
| Wider or thicker pad | no change at the graded plane | | |

**Recommended:** 24" rock. It is a data edit in the engine (`WALL_ROCK.width = inch(24)`, `params/raised_garden.py:319`). Cost: about 1 ft × 3 ft × 77 LF ≈ 8.5 cy of AB wall rock substituted for terrace fill, a small net cost. Re-oracle `raised_garden_srw.md` §3b and `tests/test_segmental_wall.py`.

**Effect on the court:** none. `tier_surcharge` reads only the unit weight on its pad, and the rock replaces soil of the same weight band.

- **Confidence.** High on the numbers.
- **Class.** SMALL-FIX (data) or DECISION, alongside G1.

### F8 · GAP · AB's drain pipe and the toe discharge
- **Drain pipe.** AB p.59 Step 3: "Drain pipe is required for walls over 4 ft (1.2 m) tall or are constructed in silty or clay soils." The presumed native is a clay-end soil, and the module docstring admits the pipe is not modelled (`raised_garden.py:126-128`).
  - Outlet problem: a pipe at the base (−4') cannot daylight to the −3'-4" yard locally.
  - Candidate outlets: (a) a pipe at the base of the wall rock tied at a corner into the court's dimpleboard-and-collector path to the soakaway; (b) AB's alternate drain location (manual p.65, not read in detail); (c) document the terrace as free-draining granular onto the court's dimpleboard as the relief path.
- **Toe discharge.** `FURN-SG-SPLASH-BASIN` (`plan/landscape.py:18-26`) is placed 6" off W-RG-EAST's yard face and takes TR-SG-RUNNEL's deck runoff (~17 gpm design) right at the SRW toe. That is the condition AB p.11/Table 2.1 warn about ("When moisture is present, extra precautions may be required"). Move the basin 3'+ off the toe, or pipe its overflow away.
- **Confidence.** High that both are unaddressed.
- **Class.** DECISION (a drainage design question, small cost).

### F9 · REVIEWABILITY · the published-chart guard contradicts the engine's own tier logic · `segmental_wall.py:164-168`
- **What.** `published_refusal()` refuses a chart row if *any* taller wall in `lower_tiers()` stands within 2 × *this* wall's height. That includes perpendicular, end-on walls and back-to-back walls.
- **The contradiction.** `_one()` (`:325`) and the note (§6) both establish that the 2H rule is a same-facing terrace rule and does not apply back to back. AB p.60 (fetched) frames it the same way: "distance between gravity walls is at least two times the height of the lower wall, and the height of the upper wall is equal to or less than the height of the lower wall".
- **Effect.** The guard blocks the chart route with a rule the engine elsewhere rules inapplicable, and it measures 2H off the wrong wall.
- **Fix** (SMALL-FIX at `:165`): `near = [t for t in tiers if t.parallel and t.back_to_back is False and t.clear_ft < TIER_FACTOR * t.lower_height_ft]`. Unknown facing should still refuse.
- **No other refusal reason remains** once the cap is modelled (G1), since drainage zone and batter are already authored.
- **Confidence.** High.

### F10 · REVIEWABILITY · sheet presentation
- **Header says "Design method: not declared".** Declare "NCMA/AB gravity, two-zone Culmann wedge, allowable-stress FS".
- **Cryptic tier symbols.** The symbol table prints `tier_W-SG-*_facing` as 0 / −1 / 1, where 0 means "facing not evaluated (perpendicular)", not "unknown". It also prints court geometry on the SRW sheet with no sketch. Replace with words and add one section sketch showing yard, embedment, pad, block, 12° lean, rock zone, terrace, court wall, and the critical plane exiting 3.39' (past the 2.97' court face).
- **The SRW sheet shows no surcharge number.** The coupling to the court (80 psf net strip, 50 plf at 110 pcf; 0 at 130) is printed on the court's records only. Add a one-line pointer with the number.
- **COSMETIC.** `params/landscape_gardens.py:97` says W-RG-BLOCK's "south face -33'-10"". The apron axis is −31.333', so the face is −31'-10".

### F11 · question 5: five identical ratios · verified, not copied
Each record runs its own geometry. Retained height plus embedment is exactly 4.00' for all five:
- BLOCK, EAST, WEST: 40" + 8" (grade stations 15, 14 and 13 at −3'-4").
- WEST-BALCONY: 36" + 12" (station 0, −3'-0").
- EAST-BALCONY: 37" + 11" (station 1, −3'-1").

The free body depends only on H, the unit and the soil, so the ratios coincide. The embedment rows differ (0.75 / 0.75 / 0.75 / 0.50 / 0.545), which confirms per-wall reads. None hits the overtopping cap.

Caveat: embedment is read from the *nearest* station, 6.7–10.6 ft away. Grade at the actual toe is not modelled. The heat-pump pad sits in front of the east return's north (toe) face, and I did not verify that its excavation leaves ≥ 6" of buried block.

### F12 · question 4: loads on the wall and the coupling to the court
- **Planting soil.** Covered by the 110–130 pcf band, moist. A saturated or perched case is excluded on the drained presumption, which in turn rests on F8.
- **Tier above.** None. Nothing stands on the terrace.
- **People.** Excluded by owner rule; no walking surface is authored.
- **Snow.** Not considered (F7 sensitivity).
- **Balcony and patio loads.** The balcony columns stand on the court wall tops, not on the returns. The leader and runnel on the east return are negligible. No patio load is behind any leg.
- **Reverse direction (apron onto court).** Yes: `tier_surcharge.py` carries the apron's *net* bearing (520 psf gross − γ × 4.0') as a rigid-wall Boussinesq strip on W-SG-S/W2/E2's records. That is 80 psf and 50 plf at 110 pcf, 0 at 130.
  - I checked the strip integral against the note's closed form (0.63105 q at 5.436'); the formula in `strip_load` matches.
  - Taken gross (328 plf), the court's system sliding falls to 1.47 (court note §4d). That is the court reviewer's item, but it is driven by this wall.
  - P_v (21–30 plf) is not carried onto the court; this is named.
  - The balcony returns' bearing behind W1/E1 is graded nowhere (court note §4c, small).
- **Global stability.**
  - SRW side: AB p.11 (fetched) asks for a global check only "on sites with slopes or surcharges". These walls have a level bed, no surcharge and a level yard, so AB's own criterion closes the SRW's own global case.
  - The coupled deep-seated slip under the court plus the apron is a *court* failure mode toward the court floor. It belongs on `retaining_system/W-SG-ARCH`, not on these five records.
  - It is currently "excluded", not addressed, on both. Recommend moving the exclusion off the SRW records and keeping it, with the apron surcharge, on the court's.

### F13 · 2026-09-18 gap review, row "Five W-RG-* upper-tier walls"
- **Closed:**
  - The upper walls are computed (they were OVER, now draft).
  - The surcharge on the lower walls is graded.
  - The terrace-versus-back-to-back geometry is established.
- **Still open:**
  - Coupled global stability, which belongs on the court item (F12).
  - "Geotechnical basis": the soil is still presumed.
  - "Supplier engineering": not needed if G1 is taken.
- **On "height alone does not close the tiered condition".** True for a real terrace. Here the pair is back to back, and the two consequences the terrace rule protects against are carried on the court. Height together with R404.4's scope (F1) *does* close the SRW's own engineering requirement.

---

## G1 · Goal 1: the prescriptive route (recommended)

**What is published** (AB Commercial Installation Manual, Table 1.3, p.10, fetched): "Maximum Wall Heights – AB Gravity Walls", 12° AB Stones column.

| Condition | Clay 27° | Silty Sand 32° | Sand/Gravel 36° |
|---|---|---|---|
| Level | **3'-6"** | 5'-4" | 5'-10" |
| 100 psf surcharge | 1'-8" | 3'-10" | 4'-6" |

Footnote: "All heights based on exposed wall heights and include a cap block… do not account for seismic loading… Final designs for construction purposes must be performed by a local registered Professional Engineer." The surcharge row "assumes a solid surface such as concrete, asphalt or pavers".

Related published conditions:
- p.59: buried block ≥ 6"; ≥ 6" compacted wall rock base; drain pipe in silty or clay soils; 12" wall rock behind the units and in the cores.
- p.60: the terrace rule (same-facing only).
- p.11: global stability is needed only with slopes or surcharges.
- Table 6.3 (AB Stones geogrid chart, "for material estimates only"): clay 27°, level, 4' wall height → 3 layers × 3' grid. That is the geogrid fallback if ever needed. It fits inside the 2.97' strip, and its top layer reaches about 2.85'.

**Where the walls stand today.** Exposure is 3'-4" (perimeter), 3'-0" (west return) and 3'-1" (east return). There is **no cap**, so the "include a cap block" condition is unmet. That is also one of the engine's refusal guards.

**The change** (numbers assume a 4" AB Capstone; the cap height is UNVERIFIED and must be read off AB's cap sheet):
- Lower every leg one cap height: base −4'-0" → −4'-4", pad bottom −4'-10".
- Keep six 8" AB Stones courses and add AB Capstones with the cap top at 0'-0", so terrace and court-top datums hold.
- Exposure stays 3'-4" including the cap, against 3'-6" (≈5% in height). Embedment becomes 12", against AB's 6" minimum.
- Returns: 3'-0" and 3'-1" including the cap. The east return carries TR-SG-RUNNEL in place of a cap. Either seat the runnel on a capstone (move it up one cap height) or accept the return on its 3'-1" exposure, a 3.5'-long return butted into the court wall.
- Add the drain pipe (F8) and a compaction spec for the founding fill (F6). Keep the 12" wall rock (24" is optional extra margin; F7).

**Conditions the guards must check:** level bed, no hardscape or path on the terrace (already an owner rule), cap present, exposure ≤ 3'-6", buried ≥ 6", rock zone ≥ 12", drain present, φ ≥ 27°. The presumed GM back-solves to 27.8–32°, and the clay row is the floor.

**Real margin option.** If the retained prism is specified granular, as the authored terrace fill already is, the 36° row (5'-10") gives 75% height margin. But the founding soil is clay spoil, so I would read the clay row and treat the granular fill as extra margin, not as the basis.

**Why the item can then leave the register:**
1. R404.4 is not triggered (≤ 48" unbalanced fill, no added lateral load), so no code provision requires engineering.
2. A major manufacturer's published chart covers the wall, with every condition answered by a guard. Under the repo's own rule (root CLAUDE.md), that is a prescriptive read.
3. The SRW's global case is closed by AB p.11; the coupled case lives on the court.

AB's "final designs… by a PE" footnote is a liability disclaimer. It does not create a code requirement where R404.4 has none. That is the same reasoning the house applies to the Metal Sales footnote.

**Permit threshold.** Minn. R. 1300.0120 subp. 4 A(4) (fetched) exempts "retaining walls that are not over four feet (1,219 mm) in height measured from the bottom of the footing to the top of the wall, unless supporting a surcharge…".
- Today: base course to top is 4'-0" (exempt). Measured from the pad underside it is 4'-6" (not exempt). With the cap change it is 4'-4" or 4'-10".
- The AHJ's reading of "footing" for a dry-stack wall on a stone pad decides this, and it is moot in practice: the court beside it needs a permit anyway, so the SRW will be on the permit set.
- The exemption is not the argument for leaving the register. R404.4's scope is.

**What the engine needs:**
- (a) A scope rule in `segmental_wall.segmental_walls()`: a wall with `unbalanced_fill` ≤ 48", no surcharge and no added lateral load is not a `tiered_retaining` item. It is graded by a check that reads `srw.published` (the `checks/structural/published.py` pattern), with the free body kept as an ADVISORY corroboration.
- (b) The F9 guard fix.
- (c) A `cap` on the spec.
- (d) Keep `tier_surcharge` running off `segmental_walls()`-equivalent scope, so the court still receives the apron load. Today it imports `segmental_walls` and `reading`, so the scope change must not drop the surcharge.
- Docstring `segmental_wall.py:20-22` ("published corroborates at most") is the policy line to change.

**Cost and complexity:**
- Caps: about 77 LF of AB Capstones plus adhesive.
- 4" deeper trench.
- Drain pipe: about 77 LF plus an outlet tie-in.
- Compaction spec text.
- Engine: one scope rule, one guard edit, one spec field, one new check, and re-oracled tests.

**Recommendation:** take G1. If the owner wants the free body kept as corroboration, also take 24" of rock, so the advisory reads about 1.75 rather than 1.54.

---

## Verified correct (and how)
- Coulomb K_a form and batter sign: reproduced AB p.11 (0.2199 vs 0.2197).
- Two-zone trial wedge: my independent scan reproduces P_a 181.27 / 187.18, ρ, share and φ_eq to the printed digits.
- P_h and P_v resolution at δ−ω: derived geometrically; correct and conservative versus AB's cos δ.
- Overturning arms W(B/2 + H/2·tan ω) and P_v(B + H/3·tan ω), moment P_h·H/3: FS 2.020 / 2.018.
- Bearing in the kern, q = N/B(1 + 6e/B): 603.9 / 606.0 psf.
- Course interface shear: demand at the joint above the base course, 120.52 / 125.73 plf, against 645 plf. AB Table 1.2's 645 lb/ft confirmed in the fetched manual.
- AB Stones 8×12×18, 75 lb, 12° (Table 1.1); d 0.97 ft, 130 pcf (p.11 sample): confirmed in the fetched manual.
- Per-member geometry and why the five ratios coincide (F11).
- Tier facing: back to back for BLOCK/WEST/EAST; perpendicular for the rest.
- `tier_surcharge` strip integral against court note §4c.

## Not verified
- The AB Capstone height (assumed 4").
- AB p.65 alternate drain detail.
- Whether MnDOT Class 5 (the authored pad) meets AB's "wall rock" gradation (0.25–1.5", ≤ 10% fines). AB specifies wall rock for the base (p.59).
- The heat-pump pad excavation versus the east return's toe.
- Whether ground snow on a planted backfill is a customary SRW load case.
- The narrow-backfill literature cited in `srw_backfill.py`, and the court's own arithmetic beyond the surcharge hand-off.
- No haus or pytest runs were made.

# B — Sunken-garden balcony frame: structural review

Reviewer B · 2026-11-22 · report only, no repo edits, no `haus`/pytest runs.
Scope: `base_rotation/PT-SG-*`, `column_head_joint/PT-SG-*`, `column_support/W-SG-E1|W1`,
`deck_post/PT-SG-*`, `glulam_beam/BM-SG-BLE|BLW`, plus the deck load that feeds them.
Scratch scripts (standalone, no model load): `out/review/scratch/B_balcony/glulam_snow.py`
(beam statics, snow drift), `out/review/scratch/B_balcony/pm_round.py` (P-M of the 12" round).

Geometry used (read from `houses/catlin/params/sunken_garden.py`, lines 2145-2665): two
3-1/2" x 11-7/8" treated SP 24F-V5M1 glulams running N-S on the column lines x = 8' and x = 28'.
Bearings at y = -9.833' (front) and -2.5' (rear), back span 7.33', overhangs 0.67' S and 1.67' N.
2x12 KDAT joists at 12" o.c. span E-W 18' between the beams and run 9" past them. The plank is
watertight aluminium (AridDek-type) and is the porch's roof (`sunken_garden.py:369, 2525`). The
north rim stops 3-1/4" off the house's SOUTH GABLE cladding. Columns are 12" rounds, (4) #5 +
#3 @ 10", 2" cover, 5,000 psi. They stand on the 12" W-SG-W1/E1 wall tops (#6 @ 38" vertical,
`sunken_garden.py:699-703`), with (4) #5 dowels embedded 24" (`sunken_garden.py:683-693`).

---

## Findings, worst first

### B-01 · ERROR-unconservative · Snow, including drift against the house, never reaches the balcony load path
- **What and where.** No balcony record carries a snow load:
  - `glulam_beam` grades D+L only, 10 + 40 psf at C_D 1.0 (`engineering/glulam_beam.py:150-151`, 338-339; sheet §4).
  - `deck_post` computes `snow = roof_tributary_ft2 * roof_snow_psf` (`engineering/deck_post.py:679`), and the roof tributary is 0 here. Its "1.2D + 1.6S + 0.5W" row is therefore just 1.2D (Pu 1,795 lb, 04-assumptions `deck_post` #14 [6]).
  - The joists are a table read at R507.6's 40 psf. `preferences.toml:63-68` sets `deck_snow_psf = 35` and argues that live load governs.
- **Why it is wrong.** The balcony is a solid, watertight roof surface, and it sits 3-1/4" from a gable wall that rises roughly 10-20 ft above it. That is the same geometry the house already designs the north canopy for, at 73.7 psf (`preferences.toml:101-122`). The balcony faces the SOUTH gable of the same 36 ft roof, so the leeward drift from a north wind is identical. Inputs below are the repo's own values from that comment (ASCE 7-16 §7.7, pg 50, Ct 1.2, Ce = Is = 1.0):
  - balanced pf = 42 psf
  - drift hd = 2.45 ft, pd = 50.3 psf at the wall, w = 9.8 ft
  - the deck is 9.67 ft deep, so the triangle covers all of it: about 92 psf of snow at the north rim and an average drift of 24 psf.
  - The engineered members fall under R301.1.3 and so must follow ASCE 7. The MN 1309.0507 footnote edit cited in `preferences.toml` speaks to the prescriptive table, not to an engineered beam.
  - The 2026-09-18 review (§5) already said "establish snow/drift … before accepting that basis". That is still open.
- **Evidence (my numbers, `glulam_snow.py`):**

| case | R_front | R_rear | bearing, record's 3" basis | bearing, authored 3.5" pack + C_b 1.107 | bending |
|---|---|---|---|---|---|
| D+L as graded | 2,035 | 2,678 | 0.65 (matches sheet) | 0.51 | 0.22 |
| D + S(35 + drift), C_D 1.15 | 2,299 | 4,214 | **1.02** | 0.79 | 0.24 |
| D + S(42 + drift), C_D 1.15 | 2,584 | 4,589 | **1.11** | 0.86 | 0.27 |

  - **Joists.** At the north rim the load is about 10 + 92 = 102 psf against the table's 50 psf. 2x12 SP No.2 @ 12" over 18' gives fb ≈ 1,570 psi against Fb' ≈ 750 x 1.15 C_D x 1.15 C_r ≈ 990 psi, about 1.6. The Fb of 750 psi is my recollection and UNVERIFIED in the repo. By the same arithmetic the north ~5.5-7 ft of the deck is over capacity. The table is no longer applicable either way.
  - **Columns.** Service axial at the rear column roughly doubles (about 2,360 to 4,590 lb). Every column state rises with axial or does not depend on it: P-M, slenderness and seat bearing all stay well under 0.2. The head seat bearing goes about 0.053 to 0.11.
- **Confidence.** High that drift loads this deck physically. Medium on how an AHJ reads the prescriptive joist table under the MN amendment.
- **Class: DECISION, with SMALL-FIXes.**
  1. Author a deck design snow profile for FS-SG-BALCONY, balanced plus a triangular drift from the house face. Feed it to `glulam_beam` (add a D+S case at C_D 1.15) and to `deck_post` (the S term).
  2. In `glulam_beam.py:111` replace `BEARING_LENGTH_IN = 3.0` with the authored `HeadConnector.bearing_length_in` (3.5", `params/column_heads.py:31`) and apply NDS §3.10.4 C_b. Expected bearing is then 0.79-0.86 with snow.
  3. The joists need either an NDS calculation under the drift profile or a framing change for the north ~6 ft, for example 2x12 @ 6" or sistered. Cheapest is to close spacing in the drift band. Owner decision.

### B-02 · GAP · Planter load on the balcony is intended but modelled nowhere
- `notes/balcony_irrigation.md` (FX-S-BALCONY-HYD serves "the balcony's plants"). `sunken_garden.py:355` and `glulam_beam` assumption #3 call the 11-7/8" depth the "owner's planter margin", but no record carries a planter load.
- A saturated 18" planter is on the order of 150 psf over its footprint (soil at roughly 100-120 pcf). That number is not from the repo and is order-of-magnitude only.
- **Class: DECISION.** Author a planter allowance: a psf over a declared zone, or "planters only over the beam lines, ≤ N lb each". Then grade the joists and beams for it. Without an allowance the "margin" is not a design statement a PE can stamp.

### B-03 · ERROR-unconservative (minor) · Loads do not reconcile between successive members
- **Where.** `deck_post` gives each column half its beam's strip: 47.12 ft2, D 471 lb, L 1,885 lb. But `glulam_beam`'s statics with the 20" north overhang put more on the rear column and less on the front one.
- **Effect on `column_head_joint` seat bearing.** It uses `P_u = 1.2(D - shaft) + 1.6L` = 3,582 lb off the equal split. By statics the rear column carries **4,089 lb** (+14%). d/c 0.053 becomes 0.060, with no verdict change.
- **Effect on the P-M and dowel cases.** These are threatened by LOW axial. The front column's statics dead reaction is 407 lb, not 471. Neither record runs the legitimate pattern of an empty floor with someone leaning on the guard (ASCE 7-16 §4.3.3 partial live): 1.2D + 1.0W + L_guard, or 1.2D + 1.6L_guard, with floor live absent. Worked by hand:
  - Pu = 1.2 x (407 + 1,025 shaft) = 1,718 lb
  - Mu ≈ (1,840 + 2,644) x 1.02 ≈ 4,575 lb-ft
  - φMn at that Pu ≈ 23,877 lb-ft (my P-M script, 45° bar orientation)
  - **deck_post P-M 0.188 → 0.19**
  - **column_support dowel tension**: T = (54,900 − 1,718 x 4.706)/7.394 = 6,260 lb against 16,740, so **0.304 → 0.37**
  - All still PASS.
- **Class: SMALL-FIX.**
  - In `engineering/deck_post.py:655-695` `_combinations`, take the beam-statics reactions (per pattern) from `glulam_beam` rather than `tributary_ft2` halves.
  - Add two rows with floor live off and the guard on (1.2D + 1.6L_g; 1.2D + 1.0W + L_g).
  - `column_head_joint` R8 should read the same reaction.

### B-04 · ERROR-unconservative (minor) · base_rotation magnifies the wrong combination; column_support uses the rigid-base magnifier
- `base_rotation` applies its flexible-base δ to "deck_post's governing Mu 4,230" (guard at 1.6L, Pu 4,833). The governing deck_post pair is 1.2D + 1.0W + L instead: first-order 4,484 lb-ft at Pu 3,680 for BF, 4,517 at 3,702 for BR.
  - With the flexible Pc (168,440 / 163,331): δ = 1.030 / 1.032, giving Mu 4,619 / 4,664 against φMn 24,371 / 24,376. **d/c 0.178 → 0.190.**
- `column_support` grades the joint with the rigid δ 1.020/1.021 (R2-R9). On the flexible base, dowel tension rises about 1%.
- **Class: SMALL-FIX.**
  - In `engineering/base_rotation.py`, run the flexible δ over every `_combinations` pair and report the worst.
  - Hand the flexible δ to `column_support`.

### B-05 · GAP · Stem flexure under the column moment ("pilaster") is still handed to "the structural engineer of record"
- **Where.** `04-assumptions.md` `column_support` #3(2): "...answered above except for the pilaster question, which stays with the structural engineer of record". This is a goal-2 failure.
- **The stem.** The 12" wall carries only the braced-wall schedule, #6 @ 38" (`sunken_garden.py:699-703, 854-859`). A #6 may not even be near a column.
- **Close by calculation.** The E-W column moment is out-of-plane for the N-S wall. Treat the wall as fixed at its footing and propped at its head (porch diaphragm), with the moment applied at the head.
  - Plain-concrete lower bound, ACI 318-19 §14.5.2.1, φ 0.60, Mn = 5√f'c·S:
    - the column's own 12" strip at the head: φMn = 0.6 x 5 x 70.7 x 288 = 61.1 k-in = 5,090 lb-ft against Mu 4,612, **0.91** (and that zone is reinforced by the dowels anyway)
    - at the dowel end, 24" down, with a 45° spread (b = 60") and M(x) = M(1 − 1.5x/H) = 0.67M ≈ 3,090 lb-ft: φMn ≈ 25,500 lb-ft, **0.12**
  - The retained-soil moment near the propped head is small. Superpose it in the record; I did not compute it.
- **Recommendation (cheap insurance).** Add two #5 verticals in the wall at each column, lapped class B (28") with the dowels. That makes it a reinforced section and removes the plain-concrete argument.
- **Head prop.** Prop force = 1.5M/H = 1.5 x 4,612 / 9.12 = **760 lb factored per column**, about 1,520 lb per wall. It goes into the ledger row (THD50600H6SS @ 16" staggered) and the porch diaphragm, and the diaphragm delivers it in compression into the opposite wall's backfill. Grade the anchors in shear. They will be trivial, but the path is currently "declared, not graded" (`base_rotation` #2(2)).
- **Stale justification.** The comment that justifies `lateral_support="top_and_bottom"` for W1/E1 (`sunken_garden.py:829-837, 857`) describes "back beams and front beams die into these walls in HUCQ410-SDS hangers… beam pockets". Those beams and hangers were retired 2026-09-22 (spent-uid list at `sunken_garden.py:3187-3190`); the porch now hangs on two ledgers (`:1808-1870`). A PE reading the brace claim will find it is about parts that do not exist. That is REVIEWABILITY, and the comment needs rewriting.
- **Other column_support exclusions, each closable by calculation:**
  - **(3) Footing bearing under the column points.** About 5.6 kip service with drift, spread through 9 ft of wall onto a 7 ft footing, is tens of psf.
  - **(4) Torsion through the joint.** T_u = 47 lb-ft against T_th ≈ 2,000 lb-ft (the same numbers as `column_head_joint` R7).
- **Class: SMALL-FIX** (add the stem and prop states to `column_support`), plus a detail line for the two lap bars.

### B-06 · GAP · Wind area omits the guard, the columns and the closed porch curtains; the "no uplift" premise is false
- **Wind area.** `balcony_wind` bands are the fascia and beams only (`engineering/balcony_wind.py`). Three things are missing:
  - The 12" columns themselves. About 66 lb ASD each, distributed, adding roughly 290 lb-ft ASD at the base.
  - The baluster guard legs.
  - The porch enclosure, hung on the balcony joists (`plan/placeables.py:391-430`: front track on the spare joist, flank tracks across the joists). In spring and autumn it is 30-ga clear vinyl (`notes/porch_enclosure.md`). Closed, the front panel is about 16' x 8.75'. With half its MWFRS load to the top track: 0.6 x 18.5 x 0.85 x 1.3 x 140 / 2 ≈ **860 lb ASD N-S**, or 215 lb per column. C_f 1.3 is my assumption, UNVERIFIED.
  - Effect on combo 4: Mu ≈ (3,130 + 2,644) x 1.02 ≈ 5,890 lb-ft, P-M **0.24**, dowel tension **0.43**, HETA wind 0.16. Still PASS, but it is load the records do not carry.
- **Uplift.** `column_head_joint` assumption #1 says "ASCE 7-16 assigns an open-jointed walking surface no uplift". This deck is a sealed aluminium roof (`sunken_garden.py:369, 2525`), so free- or attached-canopy uplift applies. Rough estimate (net C_N ≈ −1.5, UNVERIFIED): about 14 psf ASD less 0.6D, roughly 380 lb per column against the HETA pair's 2,560 lb. The FL11473 §9 interaction (uplift + lateral) is then also owed. PASS by a wide margin, but the stated premise is wrong. The joist-to-beam ties and plank fastening also see this uplift, which is outside my items.
- **Class: SMALL-FIX.**
  - Add the column, guard and curtain bands to `balcony_wind`, or declare the curtains removed. A removal is an operational assumption a PE may not accept.
  - Replace assumption #1 with a canopy uplift row and the interaction.

### B-07 · GAP (2026-09-18 finding still open) · The dowel lap ABOVE the joint is graded against the column height
- `deck_post` "dowel lap, class B 27.58 / 104.4 column height" (sheet §4, R15).
- The dowel `BarSpec` authors `embedment=24` but **no `projection`** (`sunken_garden.py:687`). Compare the veneer-beam dowels, which do author one (`:715`). So the provided lap is unknown to the engine.
- `sunken_garden.py:679` calls the dowel "a #5 L … hooked into the wall top", but the check says straight with no hook credited. Pick one.
- **Class: SMALL-FIX.** Add `projection=inch(30.0)` (or the drawn value) and grade 27.58 against it: 0.92 at 30". Fix the comment.

### B-08 · REVIEWABILITY (conservative) · The 0.88 dowel-development ratio cites the wrong clause, and the real ratio is about 0.53
- The sheet and `deck_post.py:616` cite ACI 318-19 §25.4.2.4, but the number 21.21" is the **simplified Table 25.4.2.3** row: fy ψt ψe ψg/(25λ√f'c)·db = 60,000/(25 x 70.71) x 0.625 = 21.21 (`resolve/rebar/detailing.py:30`).
  - That row's conditions hold: clear spacing 3.18" ≥ 2db, wall cover 3" ≥ db.
- The §25.4.2.4 equation gives a shorter length:
  - cb = min(half the c-c spacing, 1.90"; cover to centre, 3.31") = 1.90; Ktr = 0
  - (cb + Ktr)/db = 3.04, capped at 2.5; ψs 0.8 for #5
  - ld = (3/40)(60,000/70.71)(0.8/2.5)(0.625) = **12.7"**, against 24" = **0.53**.
- **ψe 1.0 for galvanized is correct**: ACI 318-19 Table 25.4.2.5 puts zinc-coated with uncoated. This agrees with the engine (`deck_post.py:565-567`); I did not re-read the primary text. No epoxy factor is used anywhere.
- **Is 24" really available?** Yes. The stem is 109.4" tall and cast in one placement at one form height (`sunken_garden.py:860-865`), with no construction joint in the top 24".
  - **Constructability catch:** the porch ledger anchors (1/2" x 6" Titen HD, staggered 16", `sunken_garden.py:1818-1824`) drill 6" horizontally into the wall's top 11", straight through the dowel zone (dowels 3.3-4.1" off the court face). A drill will strike a #5 dowel at each column. Note on the drawing: skip or relocate anchors within ±8" of a column centreline, or scan first.
- The same state is graded twice, as `deck_post/PT-SG-*` and `column_support/W-SG-*`: one limit state, eight register rows, two seals.
- **Class: SMALL-FIX.** Either cite §25.4.2.3, or compute §25.4.2.4 and report 0.53. Grade the state in `column_support` only, and have `deck_post` cross-reference it.

### B-09 · GAP · HETA20Z head tie depends on a written manufacturer confirmation, and its table applicability is unshown
- `AN-SG-HETA-TRIM` (`sunken_garden.py:3175-3177`) says to field-trim each 16" strap at the beam top, then "**confirm the trim with Simpson before the pour**". That is a written-approval dependency, which the owner's preferences exclude.
- FL11473 Table 3 is quoted as "double HETA, concrete, **2- or 3-ply**" (`params/column_heads.py:20-33`). The beam is a single 3-1/2" glulam, between 2-ply (3") and 3-ply (4-1/2") widths. Note 3 (strap ≤ 1/8" wider than the member) is not shown to hold. UNVERIFIED — I did not read FL11473.
- **Class: DECISION.** Options:
  - (a) Show from the table's own notes that trimming above the used holes is within the listing, and the width condition. Cheapest if the document supports it.
  - (b) Pick a cast-in strap whose length needs no trim (repo says no HETA12/16 in ZMAX/SS).
  - (c) Accept it as engineer's judgement under the seal.
  - I recommend (a), then (c).

### B-10 · GAP · Glulam record: remaining NDS states are unshown (all trivially pass)
- **Assumption #2 lists LTB at an unsheathed stage, creep, uplift at a bearing, and end connections.** Each closes by calculation:
  - Uplift at a bearing: B-06.
  - End connections: cross-reference `column_head_joint`.
  - Creep: dead-only deflection is a few thousandths of an inch. Use NDS §3.5.2 K_cr (value not checked in the repo).
  - LTB: self-weight only, about 10 plf.
- **Assumption #1 says the joists brace the compression edge "every 16"".** The joists are at **12"** o.c. (`sunken_garden.py:2654`).
  - Over the rear bearing the bottom edge is in compression and unbraced (negative M = 487.5 x 1.67²/2 ≈ 680 lb-ft D+L, fb ≈ 100 psi). It is trivial, but not graded.
- **Class: SMALL-FIX.** Add the states, correct the spacing text, and add the D+S case (B-01).

### B-11 · REVIEWABILITY · Items a PE will stumble on
- **`column_head_joint` "head moment transfer (none asked of the joint) 2 required / 2.1 provided, d/c 0.952".** This is a k-factor consistency statement dressed as a near-limit ratio. It is the largest ratio on the sheet and means nothing structurally. Move it to assumptions.
- **"Design method: not declared"** on `base_rotation`, `column_head_joint` and `column_support`. `column_head_joint` mixes ASD connector rows with strength concrete rows (V_u = 1.6 x 200). Declare each.
- **`column_support` "footprint on the wall top 6 required / 6 provided, 1.000".** The 12" round is flush with both 12" wall faces, with zero placement tolerance. State the tolerance accepted, or widen the wall top locally.
- **`column_head_joint` assumption #2** still refers to "the gusset's anchor edge distance". There is no gusset since the HETA swap: a stale remnant.
- **`column_head_joint` §8** oracles the balcony joints off `north_entry_piers.md` §9. Acceptable, but say so on the sheet.
- **The 6.556/6.685 "R" and the "k 2.1 x 1/(1+3/R)" Pc.** These are an approximation: the exact flagpole-on-spring solution, λL·tan λL = R, gives k = 2.30 and Pc ≈ 198,000 lb, not the 163,331 used. The approximation is conservative (it double-counts the 2.1 real-fixity allowance on top of the spring). Say which is graded and why.

### B-12 · GAP (closable by statement) · Drift/serviceability and seismic are not graded
- **Head displacement** under the service guard load, using EI = 1.193e9 and the flexible base:
  - δ = PH³/3EI + PH²/kθ = 200 x 104.4³/(3 x 1.193e9) + 200 x 104.4²/7.51e7 = 0.064 + 0.029 = **0.09"** (H/1,100)
  - wind: 0.06"
  - The 1-1/8" movement gap to the house is in the N-S direction, where the base is in-plane and stiffer still.
- **Seismic.** The house elsewhere earns "drift N/A from SDC A". The balcony record should state the SDC A exemption, or the ASCE 7 §1.4 minimum lateral force (~1% of D, ~15 lb per column).
- **Class: SMALL-FIX.** Add both as states or N/A findings with evidence.

---

## Answers to the eight questions

**1. Load-path reconciliation.**
- Guard (200 lb), wind (127 lb ASD per column, base 1,104/1,123 lb-ft ASD) and the column self-weight agree across deck_post → column_head_joint → column_support → base_rotation.
- Gravity does not reconcile: deck_post and the head seat use equal halves while the glulam uses statics (B-03).
- **No snow, balanced or drift, reaches any member** (B-01). Sliding snow does not apply: the house's south face is a gable.
- Wind omits the columns, guard and curtains (B-06). Planters are unmodelled (B-02).
- base_rotation magnifies a non-governing pair (B-04).
- Wall-footing point bearing is excluded but trivial (B-05).

**2. Combinations, shear, drift, torsion.**
- The 2026-09-18 finding is largely closed. deck_post now runs all five ASCE 7-16 §2.3.1 combinations at their own axial (`deck_post.py:655-695`):
  - 1.4D
  - 1.2D+1.6L+0.5S
  - 1.2D+1.6S+0.5W
  - 1.2D+1.0W+L+0.5S (wind and guard summed — conservative)
  - 0.9D+1.0W
- I reproduced φMn independently: 23,877 / 24,371 / 24,667 lb-ft at Pu 1,795 / 3,680 / 4,811 lb (45° bar orientation, matches exactly).
- Column shear (0.026) and torsion vs threshold (0.031) are now graded in `column_head_joint`.
- **Still missing:**
  - 1.2D+1.6S+L (combo 3's L branch)
  - floor-live-absent guard patterns
  - S on the deck
  - wind uplift on the sealed deck
  - drift
  - a seismic statement
- **My hand values for the missing cases:** guard with floor empty 0.18-0.19 (P-M), dowel tension 0.37; with curtain wind 0.24 / 0.43; 1.2D+1.6S+L ≈ 0.11. **None governs and none fails.**

**3. Lateral system.**
- Both directions are resisted by four flagpole columns, fixed at the wall tops, with a free head. There is no tie to the house: it is a separate structure with a movement joint.
- An IRC R507.9.2 tension tie to the house restrains only N-S pull-away. E-W racking would still need the columns' fixity, so **none of base_rotation / column_head_joint / column_support could leave the register**.
- A full house attachment (R507.9.1 ledger) is not a table read through 4" ccSPF plus girts. It would also couple two foundations the design deliberately separates.
- In-plane bracing has no clear plane:
  - N-S over the walls: the east flank has the porch stair walk-through and the porch guard runs.
  - E-W: the 18' open porch front.
  - The knee-brace scheme was abandoned for unrated joints (`balcony_moment_columns.md` §0).
- **Recommendation:** keep the moment columns, which run at 0.18-0.43 in every case I could build, and finish the closures. Tell the owner the no-cantilever preference is not efficiently satisfiable here. The same preference is also crossed by the glulams' 20"/8" overhangs and the 9" joist overhangs (gravity cantilevers; R507.5.1/R507.6.1 quarter rules).

**4. Dowel development.**
- 21.21" is the simplified Table 25.4.2.3 value. §25.4.2.4 gives 12.7", so the real ratio is 0.53 (B-08).
- ψe 1.0 for zinc is right; no epoxy factor is used.
- 24" is physically available: the stem is 109" and one placement. Watch the ledger anchors.
- The open part of this joint is not development. It is the lap length above (B-07) and the stem below (B-05).

**5. Glulam.**
- Now a proper engineered record: wet-service C_M on every property, C_V, the eight live patterns, and a fingerprint. The dry-use row is retired (that 2026-09-18 finding is closed).
- **Missing:**
  - snow/drift — this decides it (B-01)
  - authored bearing length and C_b
  - creep, LTB, uplift and negative-moment C_L (B-10)
  - planters (B-02)
- **Prescriptive route: no.**
  - IRC Table R507.5 covers sawn and built-up beams only (repo `deck_tables.py`). Its most-restrictive 3-2x12 row at an 18' joist span is 6.83' against the 7.33' back span.
  - Moving the rear row south 6" to fit breaks R507.5.1 (26" overhang against 20.5").
  - The table is 40 psf with snow not concurrent, which the drift exceeds.
  - The adopted table's SP row may be longer; I could not verify it (UNVERIFIED).
  - I found no exposed-use treated-glulam span table in the repo.
  - Keep it engineered. It is a small calculation.

**6. Prescriptive deck posts.**
- R507.4 (2018, repo table) allows a 6x6 to 14'. The posts are about 8.7', so the GRAVITY post would be prescriptive.
- What makes these engineered is that they are the whole lateral system: freestanding, with no ledger.
- A posts + beam + R507.9 scheme needs a ledger into the house through the outsulated truss wall. That is not prescriptive and defeats the separation joint.
- It also leaves the beam (B-05 above) and the drift snow (B-01) off-table.
- **Not recommended.**

**7. Presumed soil, n_h.**
- The soil barely matters. With kf = 0 (footing gives no rotational restraint), the wall-top spring is 3EI/H = 6.69e7, giving R 5.95, δ 1.043 and d/c 0.179 against 0.178 at the presumed n_h. A rigid footing gives R ≈ 7.9.
- **SMALL-FIX:** grade `base_rotation` at the kf = 0 bound and drop `soil_presumed` and the n_h gap row from these four items. No geotech is needed for them. Do it on top of B-04's governing combination: ≈ 0.19.

**8. Assumptions handed to the PE, and how to close each.**

| kind / # | open item | close by |
|---|---|---|
| base_rotation #1, #5 | presumed n_h | kf = 0 bound (Q7) |
| base_rotation #2(2) | wall-head diaphragm "declared, not graded" | prop 760 lb/column into the ledger row and porch diaphragm (B-05) |
| base_rotation #2(4) | linear subgrade | moot under the kf = 0 bound |
| base_rotation #2(5) | §6.6.4.6.2 storey sum, β_ds | state: four identical columns, so ΣPu/ΣPc = single; no sustained lateral load, so β_ds = 0 |
| column_head_joint #1 | "no uplift" | wrong; canopy uplift row and FL11473 interaction (B-06) |
| column_head_joint #2 | fastener schedule, free-head proof, stale "gusset" | the schedule is in AN-SG-HETA-TRIM (6-16d HDG per strap); bound the strap pair's rotational capacity as negligible; delete "gusset"; resolve the Simpson trim confirmation (B-09) |
| column_head_joint #5 | guard couple through the deck bearings | ±200 x ~4.3 ft / 7.33 ft ≈ ±120 lb against a 407 lb front dead reaction: no uplift, one line |
| column_support #3(2) | stem flexure / pilaster left to the SEOR | calculation plus two #5 lap bars per column (B-05) |
| column_support #3(3) | footing bearing at the column points | trivial; calculation |
| column_support #3(4) | torsion | threshold calculation (47 lb-ft against ~2,000 lb-ft) |
| deck_post #10, #19 | wind area, all shear on the columns | add the column/guard/curtain bands (B-06) |
| deck_post #14 | combination set | add guard-pattern and S rows (B-03, B-01) |
| deck_post #5/#6, R15 | lap graded against column height | author the projection (B-07) |
| glulam_beam #2 | LTB, creep, uplift, connections | B-10 |
| glulam_beam #1 | "16 in" joist bracing | 12 in; add negative-moment C_L |
| all five kinds | "SCREENING" coverage label | remove once the above states exist |

---

## Status of the 2026-09-18 review findings (this area)
- **§2, fixed-base joint deferred.** Mostly CLOSED: bearing, dowel tension, shear friction, development, footprint and base rotation are graded. **OPEN:** stem flexure/pilaster, footing point bearing, joint torsion, and the lap against actual geometry.
- **§4, single-axial P-M; shear, torsion, drift missing.** P-M combinations CLOSED. Shear and torsion CLOSED. Directional connector checks CLOSED. **OPEN:** drift, seismic statement, uplift (the false premise), the floor-empty pattern.
- **§5, glulam dry-use row with no record.** CLOSED: engineered wet-service record with a fingerprint. **OPEN:** "establish snow/drift … and planter loading", now B-01/B-02.

## Verified correct (independent check)
- **φMn of the 12" round, (4) #5 at r = 3.3125".** My strain-compatibility script matches the engine exactly at all three axial loads, taking the worse (45°) orientation.
- **Glulam D+L.** Reactions 2,035/2,678 lb, bearing 255 psi (0.65), V and M consistent with the sheet. C_M values as printed (0.80 / 0.875 / 0.53 / 0.833). Tributary 9.75' = 9' + 0.75' joist overhang.
- **Column dead load.** 471 + 1,025 lb shaft = 1,496 lb. L = 40 x 47.12 = 1,885 lb.
- **Sway magnifiers.** 1.020/1.027 at k 2.1. Pc rigid 245,513 / 236,627 lb.
- **base_rotation spring algebra.**
  - Wall strip EI 2.438e9 = 0.35·Ec·Ig, with 4EI/H = 8.91e7 and 3EI/H = 6.69e7.
  - The combination with the footing spring (5.24e7) gives kθ 7.51e7: k = (4EI/H)(kf + 3EI/H)/(kf + 4EI/H).
  - R = 6.685, δ 1.041.
- **column_support.**
  - Dowel tension 5,083 lb = (M − P·4.706)/7.394 for one bar on the tension axis.
  - Bearing compression 9,369 lb from the two-bar orientation.
  - φ0.65 x 0.85f'c x 14.04 in2 = 38,790 lb.
- **HETA wind demand.** 126.9 lb = M_wind/H, consistent with deck_post.

## Not verified
- FL11473 / ESR values for the HETA20Z pair, and its member-width applicability.
- SP No.2 2x12 Fb (750 psi, used only for the B-01 joist estimate).
- The glulam Fc⊥ 740 psi, and NDS creep and C_b values beyond the formula.
- ASCE 7 canopy uplift coefficients and the curtain C_f (both estimates, flagged).
- The adopted 2018 IRC R507.5 species rows.
- The retaining-soil moment in W1/E1 superposed with the column moment.
- Balcony joist hangers, ties and plank uplift fastening.
- The wind storey shear's band areas (508 lb taken as printed).

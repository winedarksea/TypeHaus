# F — House-to-court junction: thermal breaks, the D-B-SUNKEN band header, the brick veneer

Reviewer F, 2026-11-22. Report only. No `haus` or pytest run. I checked the numbers by hand in
`out/review/scratch/F/hand.py` (plain Python, no model load), using the inputs the calc
package prints and the authored plan.

Code text verified this pass: 2018 IRC as adopted (MN 2020) R703.8.2, R703.8.3,
R703.8.3.1/Table R703.8.3.1, R703.8.3.2, R703.8.4, R703.8.4.1, Table R703.8.4(1) and (2), and
R703.8.5. Source: UpCodes, Minnesota IRC-2018 ch. 7. I did not check the MN amendment chapters
for changes to R703.8. The 2021/2024 rows (W1.7 at 4 5/8", W2.8 at 6 5/8") are as the repo
states them in `notes/sunken_garden_veneer_beam.md` §6k. **UNVERIFIED by me**: I did not fetch
the 2021 or 2024 text.

---

## Findings, most important first

### F-01 · GAP (code) · Brick openings have segmental brick arches and no lintel. IRC R703.8.3 requires a lintel
- **Where:** `houses/catlin/plan/storeys/basement.py:1231-1246`, which authors `AO-B-BRICK-WIN`
  (14" wide, `Arch(rise=2")`) and `AO-B-BRICK-DOOR` (63 5/16" wide, `Arch(rise=8")`) in
  `W-B-BRICK`. No `Beam` and no lintel element is authored for either opening. Nothing in
  `typehaus/checks` cites R703.8.3. A grep for `R703.8.3` and for "veneer lintel" finds nothing.
- **Evidence:** 2018 R703.8.3 (verified): "Veneer above openings shall be supported on lintels
  of noncombustible materials." Bearing must be at least 4". Openings must comply with
  R703.8.3.1 or R703.8.3.2. The fetched text has no masonry-arch alternative. Table R703.8.3.1,
  "no story above" column: 3x3x1/4 spans 6'-0", and the door is 5.28'. The porch joists clear
  the wythe top by about 2", so no story bears on it.
- **Confidence:** high on the code text, high that the plan has no lintel.
- **SMALL-FIX (plan):** author two `Beam` lintels the way `BM-M-FIRE-LINTEL` is authored:
  `size="L3.5x3.5x0.25"`, A36 HDG, long leg vertical, at least 4" bearing each side. The house
  already bills this one section by the foot, and it is at least the table's 3x3x1/4, so the
  section count stays at one. The segmental arch can stay as a face course over the angle.
  R703.8.5 also requires flashing at lintels and under the base course on `W-SG-BRKBM`. The
  engine models neither: `check.txt:43` says veneer opening flashing is not modelled. Put both
  on the wall section.
- **Engine follow-up:** add a `structural.veneer_lintel` check that reads Table R703.8.3.1 for
  every opening hosted in an anchored wythe. It is a pure table read, prescriptive, and creates
  no register item.

### F-02 · GAP (prescriptive route) · 2018 Table R703.8.4(1) has no row for concrete backing at all
- **Where:** the `veneer_cavity_width` finding (`check.txt:109`) lists W-B-S1 and W-B-S4
  (concrete) as backing. Note §6k gives "brick to concrete 6.000 W-B-S1 / W-B-S4 ends".
- **Evidence:** the 2018 table (verified) has exactly three rows: wood stud with corrugated
  sheet metal, wood stud with W1.7 strand wire, and CFS stud with adjustable W1.7. None of them
  is concrete or masonry backing. The concrete-backed stretches of the wythe are therefore off
  the 2018 table at any standoff, not only at 6.0". `veneer_ties.py` grades them against the
  W1.7 row as if concrete were stud backing. That is a misread of the table.
- **Confidence:** high on the table. I did not measure how many feet of wythe stand in front
  of concrete.
- **DECISION:** either (a) stop the wythe, or its tie zone, where the framed backing
  (W-B-S2-FR/S3-FR) ends, or (b) take the concrete stretches to TMS 402 anchor design. I did
  not verify whether the 2018 IRC admits TMS 402 as an alternative. Any fix under F-03 has to
  answer this too. The engine change is to make `veneer_ties` refuse a concrete backing under
  `_ROWS_2018`.

### F-03 · DECISION · Veneer anchors (6 1/2" against 4 1/2"): what is in the cavity, and every route to a prescriptive wall
**The cavity, from the authored assembly** (note §6k, `basement.py:989`):

| layer (y, inches, north = house) | thickness |
|---|---|
| stud face +0.5 → sheathing outer face 0 (1/2" CDX) | 0.50 |
| membrane | 0.06 |
| 2 x 2" XPS, foam face −4.06 | 4.00 |
| airspace (brick back at −6.000) | 1.94 |
| **brick back to stud face** | **6.50** |

**What fixes the brick:** the brick back sits on `W-SG-BRKBM`'s north face. That face is the
house strip face (−4.0) plus the 2" isolation board. Thinner foam or a thinner airspace does
**not** shorten the brick-to-stud distance; it only changes the airspace. The note says the
same ("No sheathing change moves the margin"). The only ways to shorten it are to move the
brick north or to change what it is tied to.

| Option | Change | Result | Cost / consequence | Prescriptive under MN 2020? |
|---|---|---|---|---|
| **A. Move the court 2"+ north** | Move the house strips' south face from −4 to −2 (south projection P goes 4" → 2", R403.1.1's minimum, zero margin; north projection 11" → 13", which still meets P ≤ T 15", to be confirmed per strip). Isolation board 2" → 1 3/4". Beam, wythe, TB boards and court north ends follow. | Brick back at −3.75. Brick to stud **4.25"** (0.25" margin). For a 1" airspace the foam face must sit at −2.75 or further north, so the XPS goes **4" → 2.5"**. Airspace becomes 1.19". | Continuous insulation on that stretch drops from R-20 to R-12.5 (−R-7.5) on about 129 sf. Total wall about R-21 cavity + R-12.5. Whether MN 1322 accepts that is **UNVERIFIED**; check the wall table. Blast radius: 8 house strips, court north ends, TB-SG-* boards, BRKBM, wythe nodes, both reveals, D-B-SUNKEN tread, thermal_break and retaining records. Bigger shift buys margin but runs out of P. | Yes, for the framed-backed stretch. The concrete-backed stretch still needs F-02. Lintels per F-01. |
| **A′. A with a thinner board only** | Board 2" → 1"; strips 1" north (P = 3"). | Brick to stud 4.5", **zero** margin. | The mason's tolerance spends the margin. Not recommended alone. | Only at exactly 4.5". |
| **B. Switch cladding on this stretch to the house's metal** | Replace W-B-BRICK with the truss-wall girts plus BBD75 or PBR on W-B-S2-FR/S3-FR (and a finish on the exposed concrete ends). | `veneer_anchor` retires. `W-SG-BRKBM`, its bed, its board, both masonry joints, both lintels and the veneer flashing all go. The BRKBM board is **13,419 of 27,316 lb (49%)** of the thrust into the house. My beam-on-elastic-foundation estimate puts the governing peak at about 5 psi, d/c about 0.15, down from 0.676 (end boards only). | Loses the court's brick blend and the arches. Needs base trim at the court floor and R317 clearance. Matches "fewest, simplest differences" (every other face is metal). Probably cheaper: no mason, no beam. | Yes. The cladding is already a published Metal Sales read. |
| C. TMS 402 anchor design | PE designs the ties for 6.5" (and the concrete stretches). | Engineered item stays, with a seal. | One design and a stamp. | No (engineered). |
| D. R104.11 on the 2024 W2.8 row (current basis) | none | 0.125" margin on a row the AHJ must accept. Does not answer F-02. | A written approval: the owner's least-preferred route. | No (alternate). |

**Not a route:** Table R703.8.4(2) (ties straight into structural panel through foam up to 2")
has no distance column. Table (1)'s 4 1/2" maximum still applies to it, so thinning the foam to
2" buys nothing on its own.

**Recommendation:** B if the owner accepts the appearance. It removes one deferred item and
halves the junction thrust. Otherwise A at a 2" shift, with 2.5" XPS, lintels (F-01) and a
fix for the concrete stretches (F-02). D should not be the plan of record.

### F-04 · GAP · `W-SG-BRKBM` (the beam itself) is graded nowhere. Its resultant sits outside the kern of its 12" bed
- **Where:** `engineering/veneer_beam.py:109-112` skips any wall a `FootingBedding` hosts
  (`FB-SG-BRKBM`), so `veneer_beam` is wired to the register but finds nothing. That is correct
  for a beam that does not span, but nothing replaced it. Note §6k:902 says plainly "Nothing
  grades its bearing". The register's `thermal_break_transfer/W-SG-BRKBM` grades only the
  isolation board and the house behind it, not the beam. `veneer_beam` is wired, not orphaned:
  it is a registered kind with no subject in this plan.
- **Evidence:**
  - Brick back −6.000, front −9.625, so the brick centroid is at −7.81". The beam concrete runs
    −6 to −18, centroid −12. Eccentricity of the wythe load is 4.19".
  - The resultant of the wythe (268.86 plf) and the beam's own weight (221.9 plf) lies
    e = 2.29" off the centre. That is more than B/6 = 2.00" for the 12" bed, so the resultant
    is **outside the middle third**.
  - Rigid-footing q_max = 2P/(3(B/2 − e)) ≈ **1.06 ksf**, low in absolute terms, but the south
    edge lifts off.
  - In practice the beam is held by its monolithic ends at W-SG-E1/W1, by the brick ties into
    the house studs, and by the board bearing on the house strips. That is a load path across
    the "pure isolation joint" (see F-05), and nobody states it.
  - The torsion and the end joints into the court walls (the old §6c/§6e content) are no longer
    graded. The cage is "kept as nominal".
- **Confidence:** high on the arithmetic; the bed width (12") is read from §6k.
- **Options:**
  - (1) SMALL design fix: widen the stone bed 4" south (16" bed, B/6 = 2.67" > e). Then add a
    bearing row against the presumptive soil value. I did not verify the IRC Table R401.4.1
    figure for GM; read it from the repo's soil table. This also closes the open note.
  - (2) Keep 12" and grade the beam as a footing with torsion carried to the court walls
    (§6c-style), which is engineering.
  - (3) Option B under F-03 deletes the beam.

### F-05 · GAP / REVIEWABILITY · "Nothing crosses the break" is not true, and the compliant layer's cap rests on an unbounded court displacement
- **Where:** assumptions #1 and #5 in `04-assumptions.md` (`thermal_break_transfer`) and
  `engineering/thermal_break.py` `_NOTES`.
- **What crosses:** the W2.8 ties (a wythe founded on the court, tied to house studs), and the
  BRKBM board resisting the beam's eccentric tilt (F-04). Both are small. Two things are ungraded:
  - the vertical adjustment the ties must allow for differential settlement or frost between
    the court bed and the house strips;
  - the restoring force the board takes.
- **The cap:** the 3.5 psi figure is the D1056 2A1 stress at 25% compression. It holds only
  while closure stays under 0.125". Thermal closure alone uses 0.0533" (0.426), leaving
  **0.072"**. The court's own soil thrust pushes it north: the sheet's net is 27,986 lb toward
  the house. Friction holds that (retaining_system/W-SG-ARCH sliding 0.865, FS about 1.73), but
  mobilising friction takes some displacement. Lateral frost or ratcheting would add more. No
  row bounds any of this. Past 25% the sponge stiffens, and the "graded at the cap" thrust stops
  being an upper bound.
- **Fix (calc):**
  - Add a state "court displacement toward the house ≤ remaining compliant strain". This can be
    a stated elastic-sliding estimate, or a design that thickens the EPDM to 3/4" for
    0.1875" at 25% (still published by the same sheet).
  - Rewrite assumption #1 to "no STRUCTURAL member crosses; ties and the board's tilt restraint
    are named and bounded".
  - Add a tie-adjustment row (the W2.8 pintle's published vertical range against the
    differential movement; range **UNVERIFIED**).

### F-06 · REVIEWABILITY (goal 3) · Five register ids carry one loop-level number. Make it one item
- **Where:** `engineering/thermal_break.py:209-234` `_thrust_rows`. Every board's record gets
  the loop total `house_thrust`, `path.path_rows` (slab edge, strut, house sliding, far-wall
  soil), `court_sliding`, `line.line_rows` (near-line flexure, shear, **peak sustained 0.676**)
  and `winter_rows` (court tension). These rows are the same in all five records. Only the
  board rows differ: compliant strain 0.426 vs 0.427, board strain, and the stems' house-wall
  rows R17-R22.
- **Effect:**
  - The PE reads and seals the same beam-on-elastic-foundation five times.
  - Five fingerprints all stale together on a house-slab change.
  - `W-SG-BRKBM`'s id makes a reader think the brick beam is graded (it is not; F-04).
  - The winter-tension and court-sliding rows are the court's own reinforcement and free body,
    and belong under `retaining_system/W-SG-ARCH`.
- **SMALL-FIX (engine):**
  - In `compute()`, group boards by `loop_ref` and emit one record,
    `thermal_break_transfer/<loop>` (for example `/W-SG-ARCH`), whose `elements` lists all five
    boards. Keep the board rows inside it, prefixed with the board tag (or move them to an
    ADVISORY check: they are D1056 and C578 product reads).
  - Move the winter and court-sliding rows to `retaining_system`.
  - Governing ratio unchanged at 0.676. The register goes from 51 items to 47 and the seals
    from 5 to 1.
- **Prescriptive?** No. The capacities are published:
  - OC NGX 1000: 100 psi, 1/3 sustained rule, E 3,700.
  - Hanna 4014-E: D1056 2A1.
  - FOAMULAR 150: 15 psi.

  But the demand is a derived elastic-foundation analysis no table publishes, so the item stays
  engineered. It can only shrink (Option B halves it) or be documented better.

### F-07 · ERROR-unconservative (minor) · The band header leaves out D-M-PORCH's sill-beam seat loads, which land inside its span
- **Where:** `engineering/band_header.py:91-112` `_loads_on_band` counts only wall vertical
  members on the band. The note says `loads_inside_span 0`. But
  `notes/exterior_door_sill_beam.md` §1-§3: PORCH's sill beam seats (2x8 stacks, 10" long, at
  the beam ends inside the 63 5/16" RO) are HeadLOK-screwed into the FS-M-EAST LSL rim with
  **D-B-SUNKEN's LVL plies as the backer**. Each seat reaction is about 325.73 lb, eccentric on
  the outside face.
- **Evidence (hand):**
  - End shear 138 → about 426 lb (0.018 → **0.054**).
  - Plies on W-B-S3-FR's plates 0.207 → **0.243**.
  - Bending stays negligible.
  - Torsion on the rim plus plies from the outboard seat (about 326 lb x about 7-8" arm per
    end) is ungraded. The subfloor and the plate restrain it, but nobody states that.
  - Governing 0.434 does not move.
- **Confidence:** medium-high. I read the seat positions from the sill-beam note, not the
  resolved model.
- **SMALL-FIX:** read `SillCourseFastening` seat reactions into `_loads_on_band` as
  concentrated loads at their stations, and add a one-line torsion statement or row. Both
  ratios stay under 0.25.

### F-08 · DECISION (goal 1) · `band_header/D-B-SUNKEN` can leave the register: the LVL plies do no structural work the rim cannot do on published rows
- **Why it sits outside `resolve/header_loads.py`:** that path picks R602.7(1)/(2) rows for a
  header **in the wall's own framing**. Here the rough head is 4 5/8" under the plates
  (note §1), so no in-wall header fits. The opening is spanned by the main-floor band instead
  (`Door.header_in_band`). R602.7's tables are sawn headers in walls, so no R602.7 row
  describes a floor-band header. Lowering the door to fit an R602.7 2-2x10 is not acceptable
  (catalog French unit).
- **What the record shows:**
  - The span carries only 8.6" of floor: 47.88 plf, bending 0.011.
  - The stacked jamb loads land on the **seats**, over the jamb packs, not in the span.
  - The plies exist "for the bearing it must give the stacked jambs" (note §3).
  - The 1 1/4" LSL rim already in the band is a published header for the span
    (TJ-8000 p.6, 6'-0" row, 792 plf), d/c **0.060**.
  - Rim alone under the full seat load of 1,708 lb, on TJ-8000 p.5 / ESR-1387 Table 4:
    concentrated 1,708 / 3,760 = **0.45**; vertical 3,417 plf / 5,400 = **0.63**.
  - SPF plate under the 1.25" x 6" rim: 1,847 / 7.5 in² = 246 psi against 425, **0.58**.
- **Change:**
  - Delete the 2-ply LVL.
  - Put a 10" rim-stock ply behind the rim at each seat, the BALCONY/ENTRY backer pattern.
    PORCH's HeadLOKs need 2" of thread in wood, and this ply gives it while doubling the rim
    under each pack.
  - Author the rim header as a `published_span` (TJ-8000 p.6 row) plus the p.5 vertical rows,
    the way `WIN-M-DINING-E`'s VERSA-LAM header is authored (`notes/dining_window_header.md`).
  - Grade it in `checks/structural/published.py`. The plate bearing row is a one-line NDS
    §3.10.2 read; Weyerhaeuser's own bearing tables use 425.
  - Check the TJ-8000 p.5/p.6 footnotes on the bearing condition (**UNVERIFIED** here).
- **Engine:** in `band_header.py`, when the opening is spanned by a `JoistSpec.edge_rims` rim
  and the plies are absent, emit no record. A `structural.rim_header` published check takes it
  instead. `ItemRow("band_header", …)` then reports N/A ("no opening names a floor band as its
  header" stays false, so the N/A text needs care).
- **Cost:** cheaper (no LVL), same labour. Fewer member types. Keep the jamb takedown
  (`jamb_takedown.py`) as the published read's demand. It is stated arithmetic and I
  reproduced it: 1,708.35 lb west seat; 1,171.13 lb above FS-S-EAST.

### F-09 · GAP (small) · Jamb packs from the band down to the foundation are not graded
- **Where:** band_header grades the plies on W-B-S3-FR's plates (0.207). The 4-ply 2x6 pack
  below it and its bearing on the PT sill and curb are not graded.
- **Evidence:** 1,847 lb on 4 x 1.5 x 5.5 = 33 in², about 56 psi. That is trivial, but it is
  unshown.
- **SMALL-FIX:** cite IRC Table R602.7.5 (king studs) and the R602.7 jack count for the
  6.3' opening as a prescriptive read, plus one bearing line. Either closes it without
  engineering.

### F-10 · REVIEWABILITY · Sheet wording a PE will stumble on
1. **Thermal R7.** "the far wall's 36.00' less the near face's 17.00' (the court retains
   nothing)". The code (`thermal_break_path.py:216`) uses `near` = the BACKFILLED length of the
   near face (36 − 19' court opening). The arithmetic is right; I reproduced FS 3.749. The
   words say the opposite. Reword to "less the near face's backfilled 17.00' (the 19.00' court
   opening retains nothing)".
2. **"Design method: not declared"** on all three sheets.
   - thermal_break: state "service-load beam on elastic foundation; capacities ASD
     (manufacturer sustained-load rule) / ACI 318 plain".
   - band_header: "ASD, NDS + manufacturer tables".
3. **The veneer_anchor sheet has "Basis —" and "No citation is recorded"**, even though
   `ItemRow` carries R703.8.4, R104.11 and TMS 402. The open-item row (A) names the owner
   asking the building official as the "designer of record". That is the least-preferred route
   and ignores the design-change options in F-03. Print those options.
4. **Thermal sheet R3/R16, the "board strain" row**, reads an ESTIMATED 525 psi modulus that,
   by its own note, no verdict depends on. Either drop the row or swap the board for an XPS
   grade with a published modulus (I did not verify which OC grades publish one). As it
   stands, it is an "estimated" flag on a sealed sheet for no benefit.
5. **The 50 °F specified set temperature** (ΔT 30) is a pour-day condition the model cannot
   enforce. Carry it as a `tasks.toml` checkpoint on the court pour and print it in §6. Even a
   35 °F set gives closure 0.080" < 0.125", so state that tolerance too.

---

## `04-assumptions.md`: every item in these kinds that leaves something open, and how to close it

| Kind / # | Assumption | Open to | Close by |
|---|---|---|---|
| band_header #1 | Framing seated on the packs bypasses the span | none (geometry) | Already derived. Add the sill-seat loads (F-07). |
| band_header #2 | Jamb takedown at 15 psf wall, 40/10 floors, 50 psf roof strip | none; conservative (attic at 40 live; D+L+S unreduced) | Fine. Becomes the demand of the published read (F-08). |
| thermal #1 | Pure isolation joint, nothing crosses | wrong as stated | Name the ties and the tilt restraint; bound them (F-04, F-05). |
| thermal #2 | Estimated XPS modulus 525 psi | flagged "estimated" | Drop the row or use a published-modulus product (F-10.4). |
| thermal #3 | Formed and stripped, field sequence | site | Placement annotation (exists) plus a schedule checkpoint and inspection hold. |
| thermal #4 | No flotation row | none | Closed by the stripped-slot sequence. |
| thermal #5 | Retired with the bars: differential settlement, joint opening | partly open | Tie vertical adjustment and closure budget rows (F-05). |
| thermal #6 | Retired with the strip | none | Closed (house lateral path graded). |
| thermal #7 | E sensitivity: no row moves | none | Fine. |
| thermal #8 | Stress-capped at 3.5 psi | conditional on closure < 25% | Add the court-displacement closure row, or 3/4" EPDM (F-05). |
| thermal #9 | Soil presumed (GM) | outside input | Geotechnical report only. Sliding FS 3.75 and far-wall 0.40 have margin. |
| veneer_anchor (no assumptions printed) | 6.5" > 4.5"; concrete backing has no row | design | F-02 / F-03 (A or B), plus lintels F-01. |

## Status of the 2026-09-18 gap review (lines 177-178) for this area
- **W-SG-BRKBM veneer beam:**
  - "NO_CALC / connect the calc": overtaken. The beam is now bedded and `veneer_beam` is skipped
    by design, but the bedded beam has **no** grading (F-04): **open**.
  - Torsion and end restraint: moot while bedded; open in substance (F-04).
  - Movement joints: **closed** (`structural.masonry_joint`, Class 50, 0.365).
  - Masonry anchorage: **open** (veneer_anchor, F-02/F-03).
- **TB-SG-* transfers:**
  - Demand: **closed** (stated and graded).
  - GFRP dowels: **closed** (deleted).
  - Pour support: **closed** (formed and stripped, with a field hold).
  - Differential movement: **partly open** (F-05).

## Verified correct (what I checked)
- **Board thrusts at the 3.5 psi cap:** 2,352 x 2 + 4,596 x 2 + 13,419 = **27,315 lb**. Slab
  edge 22,154 lb, average 14.65 psi (0.44 against 33.3).
- **Peak sustained 22.5 psi**, reproduced independently with a Hetényi infinite-beam estimate:
  - Near line 25" x 15" plain, E_c 4.03e6, I = 19,531 in⁴, bed k = 3,700 x 3.5 / 1.5 =
    8,633 lb/in/in; λ = 0.01287/in, λL = 5.56.
  - The BRKBM board load (62.1 lb/in over 216") gives 0.00687". The end boards net of the floor
    line give about 0.00189". Sum **0.00876"** → 21.6 psi (0.648), against the engine's
    0.00914" / 22.54 psi.
  - Within 5%; the finite-beam ends account for the remainder.
- **House global sliding FS** (0.25 x 280,144 + 1,703.9 x 19) / 27,316 = **3.749**. Friction
  0.25 and lateral 150 psf/ft are consistent with each other; I did not re-verify them against
  IBC Table 1806.2.
- **Compliant strain** 5.5e-6 x 30 x 323 = 0.0533" against 0.125": **0.426**.
- **Band header §3:** M 199.7 lb-ft against 17,849, V 138.3 against 7,897, Δ 0.00106" against
  0.1925", all reproduced.
- **Band header §5 takedown** 1,708.35 lb; rim reads 0.311 / 0.434; bearing rows
  0.122 / 0.191 / 0.207 / 0.367. All reproduced.
- **Veneer cavity** 6.000 − 4.060 = 1.94" air; 6.5" to studs. The tie spacing / wind
  derivation (18.25 psf < 30 → 2.67 sf) is as printed; I did not recompute the wind.
- `veneer_beam` is a registered calculation (`checks/engineered_rows.py:74`) whose finder
  deliberately skips bedded walls. It is not orphaned.

## Not verified
- MN amendments to R703.8.
- The 2021/2024 Table R703.8.4(1) text, and whether either edition has a concrete-backing row.
- Whether the 2018 IRC admits TMS 402 for anchored veneer.
- The IRC R401.4.1 / IBC 1806.2 values for GM.
- The TJ-8000 p.5/p.6 footnotes on bearing.
- The W2.8 pintle's vertical adjustment range.
- MN 1322 wall insulation requirement for the 2.5" XPS option.
- The length of wythe backed by concrete.
- Each strip's P/T after a 2" shift.
- No model was loaded.

# Catlin engineering review — 2026-11-22

Successor to `engineering_gap_review_2026-09-18.md`. Reviewed at commit `01a4d13f3` plus
this pass's edits. Register: **51 items in 18 kinds — 48 computed and passing (worst d/c
0.975), 3 deferred, none sealed**. `haus check`: 0 FAIL.

**Verdict.** The arithmetic is sound: seven independent reviewers each rebuilt their
family's numbers from first principles in standalone scripts and every printed figure
reproduced. The house is still not at "a PE confirms a resolved design", for three reasons:
a few loads and load paths are missing (§1), about half the register is engineered where a
published table or a small change would do (§2), and the sheets show results without the
working (§4).

Evidence: the seven reports and their scripts are in
`houses/catlin/notes/engineering_review_2026-11-22/` (the Allan Block manual text a script
reads is in gitignored `docs/local-code-notes/allan-block/`). Finding ids below (A1-03, B-01 …) are theirs. Figures marked *hand* are a
reviewer's standalone calculation, not an engine result. Code and manufacturer values a
reviewer could not open are marked UNVERIFIED in the reports and are not repeated as fact
here.

## 1. Open: loads and load paths a PE will not sign over

Ordered by consequence. Each needs an owner decision or a design edit.

| # | Item | What is open | Numbers (*hand*) | Recommended closure |
|---|---|---|---|---|
| 1 | Balcony `glulam_beam`, `deck_post` PT-SG-*, the deck joists (B-01) | **No snow reaches the balcony.** The glulam grades 10 + 40 psf only; the columns' snow term counts roof area, which is zero; the joists are the R507.6 table at its 18'-0" limit. The deck is a sealed surface 3 1/4" from the south gable — the same roof-step drift the north canopy is designed for at 73.7 psf. `preferences.toml` sets `deck_snow_psf = 35` on the argument that live governs. | 42 psf balanced + 50 psf drift at the wall over 9.8 ft. Glulam bearing 0.65 → 1.02–1.11 on the record's 3" basis, 0.79–0.86 on the authored 3.5" seat with C_b. North ~6 ft of 2x12 @ 12" about 1.6x over (Fb unconfirmed). Columns barely move. | Author a balcony snow profile (balanced + drift) as was done for the canopy; feed `glulam_beam` and `deck_post`; close joist spacing in the drift band or add a mid-span line. Owner: the load basis is yours to set. |
| 2 | Balcony planters (B-02) | The irrigation note and the beam's "planter margin" intend planters; no record carries a planter load. | — | Owner sets an allowance (psf over a zone, or a weight limit over the beam lines). |
| 3 | `retaining_system/W-SG-ARCH` (A1-01) | The sliding FS counts friction under E2/W2 north-south. That is only true if each side wall's 51 kip thrust travels in its own footing, bending in plan from the south corner to the strut. Nothing grades that path; the bars there are `#4 @ 18"` distribution steel. | Needs 0.54–0.72 in² at the court-side edge against ~0.40 in²: d/c 1.3–1.8 simple, 0.9–1.3 with end fixity. Medium confidence. | 3 #5 on each edge of FT-SG-W2/E2 lapped into FT-SG-S and W1/E1 (~400 lb), plus a `footing plan bending` row. |
| 4 | Court sliding basis (A1-03, A1-05, A1-07, A1-08, D-R4) | See §3. | | |
| 5 | Entry screen W-BW-SCREEN (C-1) | `lateral_system` sends 1,035 lb shear and a 2,230 lb hold-down into piers PT-BW-W / PT-BW-GW. Their `deck_post` records say "no wind moment" and they have no `column_base` item. | GW as a free pole: 7.2 ft needed, 4.5 ft provided (~1.6). Pull-out ~0.93–1.10. | Grade the screen-to-landing link and declare the pier tops propped by the landing; a 2'-6" pad under GW gives pull-out ~0.75. |
| 6 | Canopy chord force (C-2) | N-S chord force uses the 6.0 ft deck depth; the named chords are 4.0 ft apart. The ±517 lb end-strap couple is ungraded. | 517 → 751 lb (or 505 lb naming the garage gable truss as north chord). Strap couple 0.63–0.73. | Correct the lever arm or rename the chord; add the strap row. This number goes to the truss fabricator, so fix it before the order. |
| 7 | `deck_tie/FS-BW-FLOOR` (C-10) | Passes at 0.78 on a DRY-service reading; `roof_beam` and `wood_roof_post` take the same canopy zone as wet. The HL33 is graded heel-vertical, outside its catalog orientation. | At C_M 0.7 the N-S case is 1.09. | Pick one service condition for the zone; confirm the orientation against the catalog. |
| 8 | Brick veneer W-B-BRICK (F-01..F-05) | Openings are brick arches with no lintel (R703.8.3). The concrete-backed stretches have no row in the adopted tie table at any distance. The beam W-SG-BRKBM is graded nowhere and its resultant is 2.29" off centre on a 12" bed (kern 2.0"). The ties and the beam's tilt restraint cross a joint the sheets call pure isolation. | Brick to stud 6.5" against 4.5". | Decide the wall first (§2 row 9). If brick stays: two L3.5x3.5x1/4 HDG lintels, a 16" bed with a bearing row, and a row bounding court movement at the joint. |
| 9 | Walls W-SG-W1/E1 under the column moments (B-05, D-R3) | Pass Table R404.1.2(8), which has no surcharge column, while carrying up to 4.6 kip-ft per column at the wall top on #6 @ 38". Still handed to "the engineer of record". The porch ledger anchors drill through the dowel zone. | Plain-concrete bound 0.91 at the head. ~760 lb factored per column into the porch diaphragm, ungraded. | Add the stem row; two #5 lap bars per column; a drawing note to skip ledger anchors at the columns. |
| 10 | Balcony frame, smaller (B-03, B-04, B-06, B-07, B-09) | Reactions split equally where statics puts more on the rear column; no guard-on, floor-empty combination; `base_rotation` magnifies the wrong combination; wind area omits guard, columns and porch curtains; "no uplift" premise assumes an open-jointed deck; dowel lap above the joint is checked against column height (no projection authored); HETA20Z needs a written Simpson confirmation. | Rear seat 4,089 vs 3,582 lb. Dowel tension 0.30 → 0.37 → 0.43. 0.178 → 0.190. Lap at 30" authored: 0.92. All pass. | Engine corrections; author a 30" dowel projection; choose a head tie whose table row covers a 3 1/2" member (owner preference: no written approvals). |
| 11 | `W-S-SN3` over FS-S-WEST (D §2.3, D-R2) | ~240 plf from SN3 and the attic opening trimmer reaches truss J12 through the subfloor; that truss passes a uniform-load table. The plan says SN3 is non-bearing in `second.py` and bearing in `main.py`. | — | Resolve the contradiction; an LSL rim strip under the wall on a published vertical capacity, and the load on the truss order. |
| 12 | `code.MN_1309_0404_wall_top` W-B-N2 (D §2.6) | Opening headers ~87" apart against the 72" blocking limit: no prescriptive equivalent. | 400 plf over ~7.25 ft, M ≈ 2,630 lb-ft. | One-page horizontal-beam calc of the stairwell rim pack. |
| 13 | `band_header/D-B-SUNKEN` (F-07, F-09) | Omits D-M-PORCH's sill-beam seats (~326 lb each, eccentric); jamb packs below are ungraded. | Shear 0.018 → 0.054; governing 0.434 unchanged. | Fold into §2 row 4. |
| 14 | Wall bracing story count (D-R1) | `bracing_eval` drops the attic citing R325.6 without testing its conditions. | — | Read the adopted R325.6 text and grade its conditions. Low effort, high consequence if it turns. |

## 2. Goal 1 — what can leave the register

| # | Kind (items) | Why it is engineered today | Route off | Change |
|---|---|---|---|---|
| 1 | `tiered_retaining` (5) | Registered because fill > 0. IRC R404.4 covers walls retaining over 48", or over 24" with added lateral load; these retain 40" / 36" / 37" of soil only (A2-F1). | Allan Block gravity chart (Table 1.3, 12° AB Stones, level, clay 27°): 3'-6" exposed, cap included. | Lower each leg one cap height, add capstones, a drain pipe and a compaction spec for the founding fill; engine scope rule, the guard fix at `segmental_wall.py:165`, a chart check. Removes the 0.975 ratio. If kept engineered instead: 24" of wall rock gives 1.75. |
| 2 | `girt_screw` (1) | ASCE 7 suction against ICC-ES allowables. | Published read, the cladding's own pattern. | Author the published capacity; correct the demand first (girt continuity x1.25–1.375, height from grade): 0.49 → ~0.73 (C-7). |
| 3 | `deck_tie` (1) | Same pattern against the Simpson HL table. | Published read. | After §1 row 7. |
| 4 | `band_header` (1) | Floor-band header, outside R602.7. | The 1 1/4" LSL rim alone on TJ-8000 rows (0.45 / 0.63, bearing 0.58) (F-08). | Delete the LVL plies, add rim backers at the seats, author it like the dining-window header. |
| 5 | `thermal_break_transfer` (5 → 1) | One loop-level analysis printed under five ids (F-06). Stays engineered: no table publishes the demand. | — | Emit one item per loop: five seals become one. |
| 6 | North-entry piers: `column_base` (2), `deck_post` PT-BW (6) | Modelled fixed-base. They are 3 ft pedestals on embedded piers (C-11). | IBC 1807.3 code read; or pinned with lateral through `deck_tie` and the canopy diaphragm (D). | Reclassify; add a bond-breaker sleeve note over the frost depth. |
| 7 | `rafter` (2) | Trusses: a normal deferred submittal. | Stays deferred, but decided. | Print a truss criteria schedule (loads, drift per truss, bearings, chord force, deflection, max uplift); a specified 450 lb/heel lets the chain below be graded now (*hand* 289 lb net, 0.41). Drop the splice-slip ask: it never enters a ratio (C-8). |
| 8 | `glulam_beam` (2) | Off R507.5 on species column and wet use. | 3-ply 2x12 SP on R507.5 (D) — **only if the table's 40 psf basis stands**; it does not survive §1 row 1. | Decide row 1 first. |
| 9 | `veneer_anchor` (1) | 6.5" cavity against the adopted 4.5". | (A) court 2" north + thinner board/foam, loses ~R-7.5 on ~129 sf, large blast radius; (B) clad the stretch in the house's metal — retires the anchor, the beam, its board and the lintels, and cuts the thermal-break governing ratio to ~0.15; (C) 2021 row under R104.11 — an approval, 1/8" margin, and it does not cover the concrete-backed stretches. | Owner: B if the look is acceptable, else A. |
| — | Stay engineered | Court (4), balcony frame (14), `lateral_system`, `roof_beam` (2). | The plain alternatives (wood posts with braces or a ledger; braced wall tops or 48" terraces) are in D §1.2. | — |

Ratios that are overstated and can simply be corrected: `lateral_system` 0.91 → ~0.50 (the
authored 190 plf is a deliberate half of the table's 342 plf, C-3); `roof_beam` 0.877 →
~0.66 (C-4); dowel development 0.88 → ~0.53 on the general equation (B-08).

## 3. Sliding

**Court (`retaining_system/W-SG-ARCH`, FS 1.735).** Reproduced exactly: thrust 3,122.79 plf,
friction 97,508 lb against a 56,210 lb resultant. Per wall, with no system, FS is 0.61–0.63.
The pass therefore rests on the loop, and on three things a PE will press:

- **The load path** — §1 row 3.
- **The bed.** At μ 0.25 (no stone) the graded FS is 1.24. The engine leaves out friction
  under concrete already in the loop: FT-SG-W1/E1 and the two corner squares. Counting them
  gives **2.20 at μ 0.35 and 1.57 at μ 0.25** with no new concrete (A1-03). It depends on
  the porch bracing the W1/E1 tops. Optional: a 12" x 24" key under FT-SG-S (~1.9 cy) for
  2.09 / 1.60.
- **The soil and water.** Clay-till backfill at 100 psf/ft at rest gives 1.05; specifying
  imported granular backfill (~60–90 cy) fixes the pressure by spec (A1-07). No wet case is
  registered: water perched 6 ft above the footing underside gives 1.49 (1.88 with the
  credit above); full height 1.17 (1.46) (A1-05). The plane under the 54" of stone is still
  handed to a geotechnical engineer: screening 1.35–2.0 (A1-08).

The `retaining_court` study's 7.66 is a per-foot isolated wall in a 5 ft blocked-drain case
on stale inputs. It is not comparable to the register and should not ship as is (A1-06).
The strut demand is low (25.5 → 34–46 kip) and its capacity uses 3,000 psi against a
5,000 psi mix; net ~0.55–0.91, passes (A1-02).

**SRW tiers (`tiered_retaining`, FS 1.538).** Reproduced; the five identical ratios are
real (every leg is exactly 4.00' of free body). The margin is fragile: rock at 34° gives
1.47, φ 27° gives 1.44, no rock credit 1.30; the pressure graded is 56% of the IBC §1610.1
value (A2-F3, F7). The answer is §2 row 1, not a better free body.

## 4. Goal 3 — the documents

Remaining, in priority order (E §6B): show the working for each limit state, not only the
quotient; a per-family "not covered, and who owns it" table; a one-page reviewer's summary
with changes since the last issue; the structural sheets and a key plan in the handoff
bundle; seal-form defaults so name, licence and date are typed once; the per-member
appendix in the stamped PDF by default; a complete criteria page (live, dead, guard,
seismic statement, all materials); free-body sketches. Also: one loop shows base friction
97,508 lb on one sheet and 107,211 lb on another, unexplained (E-15); stale text in the
court, SRW and north-entry oracle notes (A1-11, A2-F2, C-8).

Outside the register: the concrete mixes state no chloride limit, cement or S class
(deliberately awaiting the mix submittal; D §2.1 gives spec values that can be authored
now); `FS-S-WEST` has no north edge rim behind the sheathing joints (D §2.2).

## 5. Changed in this pass

- Calc sheets: numbers print positionally and to the figure (FS 1.5 against 1.538, not
  "1.5 / 1.5"; no `6e+04`); ratios to three places; the governing member is bold in the
  schedule; a factor of safety is labelled; the citation column uses the R-keys.
- A design method on all 18 kinds (nine printed "not declared"); the load-combination
  footnote no longer claims a kind "combined nothing".
- Open items: identical deferrals share one row; empty sections say "None".
- Each family's "does not cover" section names its exclusion rows in `04-assumptions.md`;
  the PE README no longer claims a list the sheets do not carry.
- Seal form header documents the four find-and-replaces that fill it.
- `tiered_retaining` prints the friction coefficient the sliding row used (0.528), not the
  unused table value (0.25). The five tiered fingerprints change; no seal exists.
- Citations: the simplified development length is Table 25.4.2.3, not §25.4.2.4.
- `deck_post` summary and the thermal-break far-wall reference reworded.
- Court free-body note §13: the empty W1/E1 weight mixed 130 and 110 pcf. Half-rule staged
  FS 1.64 → **1.58**, one side empty 1.37 → 1.31; test re-pinned.

No member size, reinforcement, load or authored plan value was changed.

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

## 6. Closure (2026-11-23, branch `eng-review-close`)

Every finding id mapped to a commit or a decision. The register went from 51 items to 32; `haus check` reports 0 FAIL. "Recorded" means a stated basis, with no change. A2 ids are written A2-Fn and D section-2 ids D-S2.n. The commit `0aa2a0938` is the review pass itself.

| Id | Finding (≤12 words) | Outcome | Where |
|---|---|---|---|
| 6A-1 | Governing demand/capacity/ratio print positionally to the figure | fixed | 0aa2a0938 |
| 6A-2 | No exponents (6e+04) in sheet numbers | fixed | 0aa2a0938; 46f1ef5e8 (appendix) |
| 6A-3 | Ratios to three places (0.975 not 0.98) | fixed | 0aa2a0938 |
| 6A-3b | Governing member not marked in schedule | fixed | 0aa2a0938 |
| 6A-3c | Coverage/Seal columns repeat constants on every row | fixed | 46f1ef5e8 |
| 6A-4 | Criteria page: design method missing for some kinds | fixed | 0aa2a0938 (see a: E-09) |
| 6A-5 | Criteria wording ("not stated", section pointers) | fixed | a486e6823 |
| 6A-6 | Long citations printed twice; use R-keys | fixed | 0aa2a0938 |
| 6A-7 | Identical deferrals one row each; empty sections say None | fixed | 0aa2a0938; a486e6823 |
| 6A-8 | Handoff README claims a list the sheets lack | fixed | 5dbc52da3 |
| 6A-9 | Seal form header: four repeated strings undocumented | fixed | 5dbc52da3 |
| 6A-10 | "No inputs to fingerprint" wording on sheets | fixed | 46f1ef5e8 |
| 6A-11 | "this engine" speak across calc modules | fixed (swept with the working) | a486e6823; fcdda53dd; e4bfdbaab; bb3f5a72b |
| 6A-12 | Stamped PDF omits per-member appendix by default | fixed | 5dbc52da3 |
| 6A-13 | deck_post summary: 0.18 beside d/c 0.88 | fixed | 0aa2a0938 |
| 6A-14 | tiered_retaining prints two friction values | retired (kind gone) | cdf409d8b; 0aa2a0938 |
| 6A-15 | Format docs stale (counts, "commented out", tiered example) | fixed | 5dbc52da3; d5c8ee0b0 |
| 6A-16 | deferred.py reason strings carry dates and check ids | fixed | e3623dbe2 (rafter); 0f8275001 (veneer) |
| 6A-17 | README says nine sections; sheets have ten | fixed | 46f1ef5e8 |
| 6A-18 | NO_CALC sheet omits designer and deliverable | fixed | 46f1ef5e8 |
| A1-01 | Footing plan bending of W2/E2 is the ungraded load path | fixed (3 #5 per edge, d/c 0.51) | 44ec45224; c4f7beb5f |
| A1-02 | Strut force omits braced legs; 3,000 psi capacity | fixed (0.54) | c4f7beb5f |
| A1-03 | Friction under concrete already in the loop not counted | fixed (owner D1) | c4f7beb5f |
| A1-04 | Staged-backfill W1/E1 weight mixed 130 and 110 pcf | fixed | 0aa2a0938; e488e82fe (§15e) |
| A1-05 | No wet or blocked-drain sliding case | fixed (perched, flooded, snow graded; snow+perched not combined: owner basis) | c4f7beb5f; 60bf4c116; fcec8ca28 |
| A1-06 | retaining_court study unreconciled with the register (7.66) | fixed | 659779220 |
| A1-07 | Retained-soil class drives answer; imported backfill option | owner decision (no bulk imported backfill; at-rest 60 psf/ft specified) | 60bf4c116; b9cd54ab9 |
| A1-08 | Deep plane under the stone handed to a geotechnical engineer | owner decision (no geotech; graded on specified native φ' 25 deg, excavation check, lean-wall fallback) | 60bf4c116; L1 note §15h |
| A1-09 | Extra rows: stem shear, native bearing, corner bars, compaction | fixed (native bearing 0.559 on class 4; corner L-bars as modelled; plates within 3' of a stem) | 4e4bd2b4b; e8b5191fd |
| A1-10 | Corner shear transfer grades the wrong mechanism | fixed (corner delivery row 0.12) | c4f7beb5f |
| A1-11 | Stale oracle-note text (19'x26' court, FS 1.63) | fixed | e488e82fe |
| A2-F1 | R404.4 is the wrong basis; walls retain under 48" | retired (R404.4 scope; kind gone) | 67f418cc3; cdf409d8b |
| A2-F2 | friction 0.25 shown against governing tan 27.8 deg | retired | cdf409d8b (0aa2a0938 printed 0.528) |
| A2-F3 | Method mixing; margin fragile (34 deg 1.47) | retired (chart replaces free body) | cdf409d8b |
| A2-F4 | Sliding free body rebuilt, verified | recorded | L6, raised_garden_srw.md §10 |
| A2-F5 | Sliding plane at pad base not checked | retired | 67f418cc3; cdf409d8b |
| A2-F6 | Apron founds on court backfill, no compaction spec | fixed (95% Proctor, 8" lifts on SrwChartSection) | eb3ca4690 |
| A2-F7 | 1.538 rests on three unverified choices | retired | cdf409d8b |
| A2-F8 | Drain pipe and toe discharge unaddressed | fixed (pipe to #57 column; runnel end, splash pad; owner G9a) | eb3ca4690; 4e948830d; 0f1b549ad (billing open, see b) |
| A2-F9 | Chart guard contradicts engine tier logic | fixed | 67f418cc3 |
| A2-F10 | Sheet presentation: design method, tier symbols | fixed | 67f418cc3; eb3ca4690 |
| A2-F11 | Five identical ratios verified, not copied | recorded | L6, raised_garden_srw.md §10 |
| A2-F12 | Loads on wall and coupling to the court | recorded | L6 §10; court record row (c4f7beb5f) |
| A2-F13 | 2026-09-18 row on upper-tier walls | recorded | L6, raised_garden_srw.md §10 |
| A2-G1 | Goal 1: leave register via Allan Block Table 1.3 | fixed (5 items to 0; owner G9a) | 67f418cc3; cdf409d8b |
| B-01 | No snow reaches the balcony; 3.0" seat divisor | owner decision (MN deck basis 40+10, no snow; seat reads 3.5" with C_b) | 56cfab325 |
| B-02 | Planter load intended but modelled nowhere | fixed (171.7 plf over beam lines, cased) | 56cfab325 |
| B-03 | Column reactions split equally; no guard-on case | fixed | 4a78d78d2 |
| B-04 | base_rotation magnifies the wrong combination | fixed | 4a78d78d2 |
| B-05 | Stem flexure under column moment handed to EOR | fixed (stem, strut, footing rows; dowels 48"; soil prop in compression) | 4a78d78d2; 43cac111a; a2aedc4d4 |
| B-06 | Wind area omits guard, columns, curtains; "no uplift" | owner decision (curtains stowed in high wind, not a band); guard, shafts, uplift row fixed | 13d0dec90; 4a78d78d2; 585059463 |
| B-07 | Dowel lap graded against column height | fixed (30" projection, 0.55) | 4a78d78d2 |
| B-08 | 0.88 dowel development cites wrong clause (~0.53) | fixed (general equation, 0.27) | 4a78d78d2 |
| B-09 | HETA20Z needs written Simpson confirmation | owner decision (use printed 1-ply FL11473 row; accepted reading) | 4a78d78d2; 4c56ce406 |
| B-10 | Glulam: remaining NDS states unshown | fixed | 56cfab325 |
| B-11 | Items a PE will stumble on (spacing text, notes) | fixed | 4a78d78d2 |
| B-12 | Drift/serviceability and seismic not stated | fixed | 4a78d78d2 |
| C-1 | Screen shear path below chord bases not closed | fixed (MSTA49Z screen strap; pads 30x30x12; pull-out rows) | 9aae73914; 8a7011ece; ab23576f0 |
| C-2 | Chord force uses deck depth, not chord spacing | fixed (752 lb; 764 lb on jacketed posts; strap couple 0.77) | 5e1fe4c43; 4419ed8bd |
| C-3 | lateral_system 0.91 from arbitrary halving | fixed (SDPWS 4.2A, deck row 0.496) | 5e1fe4c43 |
| C-4 | roof_beam 0.877 overstated truss bearing | fixed (0.662) | 5e1fe4c43 |
| C-5 | Equal post share ignores N-S drift gradient | recorded (+205 lb at piers); header posts modelled | 9aae73914; 0efc0b5bb |
| C-6 | Pad bearing gravity-only | fixed (0.82) | 9aae73914 |
| C-7 | girt_screw demand omits continuity; h from floor datum | fixed (retired to ESR-1078 read, pull-through 0.842) | 21a81ba34; 3143541b9; 0052bc67b |
| C-8 | Splice-slip ask not load-bearing | fixed | 5e1fe4c43 |
| C-9 | Deferred trusses: what the house can decide now | fixed (supporting structure closed); open: supplier designs | 9bf9540d8; dfb4736d6; b64e5ab5d |
| C-10 | Landing tie: dry reading, HL33 orientation | owner decision (wet throughout; HL43 read for as-installed direction) | 8a7011ece; 39aaf6e9b |
| C-11 | Entry piers modelled fixed-base; can leave register | fixed (8 items retired; IBC 1807.3 check) | 9aae73914; c0aa6c4c5 |
| C-12 | roof_beam / wood_roof_post prescriptive routes | recorded (R507.4 not adopted for roof posts) | 9aae73914 |
| D-R1 | Bracing story count never tests R325.6 | fixed (four conditions graded; premise wrong, no area fraction in 2018) | 7cb5425d8 |
| D-R2 | J12 carries ~240 plf from SN3 outside its table | fixed (SN3 bearing + LSL strip; J12 on truss order) | 7cb5425d8; 9bf9540d8 |
| D-R3 | W1/E1 stems pass R404.1.2(8) with column moments | fixed (stem rows) | 4a78d78d2 |
| D-R4 | Stone/GM interface under court footings ungraded | owner decision (as A1-08) | 60bf4c116 |
| D-R5 | Cladding read: older p.13 58/43 psf vs 07/2026 CTR 42/75 | recorded (graded both ways on p.13; the CTR row recorded, not adopted; 42 inward would read ~0.33) | house guide, Shell |
| D-R6 | FS-M-NE peninsula loads outside OJ418S table | fixed (point-load list on the truss order) | 345438a75; 9bf9540d8 |
| D-S2.1 | Concrete mix chloride, cement, sulfate, ASR fields | fixed; ASR open until plant submittal | 6f022b5ff |
| D-S2.2 | Sheathing edge support: north and south joints | fixed | 345438a75; eebf8f8f0 |
| D-S2.3 | stacked_line_ladder: real load, SN3 contradiction | fixed | 7cb5425d8 |
| D-S2.4 | Trussed roofs: reactions, uplift, rafter span | fixed (supporting structure); open: supplier designs | 9bf9540d8 |
| D-S2.5 | veneer_anchor and cavity width | owner decision (as F-03) | 0f8275001 |
| D-S2.6 | W-B-N2 wall top exceeds 72" blocking limit | fixed (3-ply LVL pack, ties; no register item) | 345438a75; eebf8f8f0 |
| E-01 | No per-family "not covered / who owns it" | fixed (NotCovered table on every family) | 46f1ef5e8; fcdda53dd; e4bfdbaab; bb3f5a72b |
| E-02 | Arithmetic not shown, only the quotient | fixed (Step chains on all 12 graded kinds; lint) | 46f1ef5e8; fcdda53dd; e4bfdbaab; bb3f5a72b |
| E-03 | Bundle has no structural sheets or key plan | fixed | 5dbc52da3 |
| E-04 | No reviewer's summary or "what changed" | fixed | a486e6823; 1b62d8f41 |
| E-05 | Stamped PDF omits per-member data | fixed | 5dbc52da3 |
| E-06 | "Worked at governing member" hides sub-templates | fixed | 46f1ef5e8 |
| E-07 | Rounding makes demand = capacity; notation | fixed | 0aa2a0938; 46f1ef5e8 |
| E-08 | tiered_retaining prints two friction values | retired | cdf409d8b |
| E-09 | Design method "not declared"; combinations unstated | fixed (method declared; every graded state names its combination in words) | 46f1ef5e8; fcdda53dd; e4bfdbaab; bb3f5a72b |
| E-10 | Symbols without descriptions; units "—" | fixed (plain-word labels) | 46f1ef5e8; fcdda53dd; e4bfdbaab; bb3f5a72b |
| E-11 | Citations long prose, printed twice | fixed | 0aa2a0938; 46f1ef5e8 |
| E-12 | Open-items page: tone, naming, empty sections | fixed | a486e6823; e3623dbe2 |
| E-13 | Seal path: placeholders repeat in every block | fixed | 5dbc52da3; 46f1ef5e8 |
| E-14 | Design-criteria page incomplete or misleading | fixed | a486e6823; 1b62d8f41 |
| E-15 | Numbers disagree between pages | fixed (15.2 bodies reconciled; 15.5 M_u = M_ASD / 0.6 shown as a step) | c4f7beb5f; 0aa2a0938; a486e6823; 39c1a2c73 |
| E-16 | Hedging, history and engine-speak in strings | fixed (jargon sweep with the working) | fcdda53dd; e4bfdbaab; bb3f5a72b |
| E-17 | Cosmetic: PDF id splits, header table, README | fixed | a486e6823; 84a412077; 46f1ef5e8 |
| F-01 | Brick arches with no lintel (R703.8.3) | fixed (flat heads on HDG L3x3x1/4; 316 flashing on EPDM) | 0f8275001; 1f0a7e149 |
| F-02 | No 2018 tie row for concrete-backed brick | fixed (2024 W2.8 ties on studs only; slotted HB-213) | 0f8275001; 1f0a7e149 |
| F-03 | Veneer anchors 6 1/2" against 4 1/2" cavity | owner decision (brick stays; 2024 W2.8; dated dependency) | 0f8275001 |
| F-04 | W-SG-BRKBM resultant outside kern of 12" bed | fixed (bed bearing 0.53) | 0f8275001 |
| F-05 | "Nothing crosses the break" false; unbounded movement | fixed (owner D29: detail takes movement; bond break; joint 0.68) | 44ec45224; cdbf93b84; f24fad8a9 |
| F-06 | Five register ids carry one loop-level number | fixed (5 to 1) | c4f7beb5f |
| F-07 | Band header omits porch sill-beam seat loads | fixed | aae182ceb |
| F-08 | band_header can leave the register (LSL rim, TJ-8000) | fixed (retired; published read) | aae182ceb |
| F-09 | Jamb packs below band ungraded | fixed | aae182ceb |
| F-10 | Thermal/band/veneer sheet wording (5 items) | fixed (R7 reworded; method declared; veneer citations; board strain a detailing row; 50 F fit checkpoint) | 6814726c0; d6b064162; f0735f855; cf30b33c9 |


**Still open after the close:**
- **The veneer ties' code edition.** `veneer_anchor/W-B-BRICK` waits for Minnesota's 2024-based code to take effect on or before the application date; failing that, an R104.11 request.
- **The supplier truss designs**, for `RF-BW-CANOPY` and `RF-GARAGE`:
  - The supporting structure is graded on the specified reactions. The component closes when the supplier's reaction schedule is entered.
  - The canopy heel's uplift, 289 lb, is over the three-nail H2.5ASS row's 260 lb, and no published Simpson route closes it. The heel goes on the truss order.
- **The ForteWEB report for D-B-SUNKEN's rim header:** for the owner to run and keep (`engineering_review_2026-11-22/forteweb_D-B-SUNKEN.md`).
- **Soil report confirmation:** the court is closed on specified parameters (bed friction >= 0.43, native phi' >= 25 deg). `structural.soil_parameters_confirmed` stays UNKNOWN until `Site.confirmed_soil` is entered. The lean-wall fallback is printed.
- **Billing:** the SRW drain pipe and capstone adhesive are not billed (`plans/TODO.md`).
- **Ratios at or above the 0.85 owner cost-review trigger** (not limits):

  | Item | Ratio | Governing state |
  |---|---|---|
  | `thermal_break_transfer` | 0.998 | winter tension |
  | `retaining_system` | 0.981 | staged backfill |
  | veneer ties | 0.91 | — |
  | `deck_tie` | 0.876 | — |
  | `retaining_wall` x3 | 0.865 | stem flexure |
  | girt screw pull-through | 0.842 | — |

- **A question for the sealing engineer, `column_support`'s bearing row:**
  - C is solved on the block the force itself needs at 0.85 f'c. The capacity is taken on the column's P-M block.
  - The joint is adequate either way: as a flexural section it is the dowel tension row, 0.894; held to φ·0.85 f'c the block still fits.
  - The second reading would put the dowels at about 0.93, over the owner's 0.92 acceptance.

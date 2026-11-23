# E — Reviewability: can a PE stamp this quickly and without concern?

Reviewer role: licensed structural PE handed the package, plus technical editor of the generator.
Scope: goal 3 only (the DOCUMENTS and the code that writes them). Report-only: no repo file was
edited. One `haus handoff` run was made (allowed exception); everything else is read-only.

Paths are relative to `/Users/colincatlin/Documents-NoCloud/TypeHaus`. "Package" =
`houses/catlin/out/calcs/` (byte-identical to `out/review/handoff/calcs/`, checked with `diff -rq`).
"PDF" = `out/review/handoff/calcs.pdf` (115 pages, letter, produced 10:26 today; rendered and read
pages C-1, D-1, R-1, O-1, S-20, S-22, S-40, S-71, S-72, S-65).

---------------------------------------------------------------------------------------------

## 0. Bottom line

A PE can follow the structure (cover, criteria, register, per-family sheet, assumptions) and the
tables render properly now. They cannot stamp quickly, for six reasons, in order of cost:

1. **The arithmetic that produces each demand and capacity is not shown** (E-02). The PE must rebuild
   every number from the model and the oracle note. The PDF is a results listing, not a calculation.
2. **No page says, per family, which limit states are NOT graded and who owns them** (E-01). The
   handoff README says each sheet's section 9 does this. It does not: section 9 is one generic line.
3. **No sketch, key plan or load path anywhere, and the bundle carries none of the structural sheets**
   (E-03). "PT-SG-BF3" cannot be located by the PE without opening the IFC.
4. **There is no one-page reviewer's summary** (E-04), and the PDF the PE is asked to stamp omits the
   per-member data for 47 of 51 items (E-05).
5. **The text still reads like engine internals and project history** (E-15, E-16): "this engine",
   check ids, Python field names, "Until 2026-09-18 ...", "(2026-09-20)", "retired deferral".
6. **Numbers print so a PE cannot read the margin**: "Demand 1.5 / Capacity 1.5 / d/c 0.98", "fy 6e+04",
   `seat_eccentricity 8.882e-16 in` (E-07).

The seal path itself is short and works (E-13): four placeholder strings, found-and-replaced, fill 72
of 84 blanks in about 3 minutes; the PE does not need 51 separate entries. It is just undocumented, and
the three deferred acceptances sit in the same file.

Most of the S-size fixes (section 6A) are text or format-only, touch no ratio or fingerprint, and the
calc-package tests are assertion-based, not golden (`packages/engine/tests/test_calc_package.py:3`).

---------------------------------------------------------------------------------------------

## 1. Findings (lead with what is wrong)

Severity vocabulary from the brief; everything here is REVIEWABILITY unless stated.
Class: SMALL-FIX = exact edit given in 6A; DECISION = options and a recommendation.

### E-01 · GAP + false statement · No per-family "not covered / who owns it"; README claims otherwise
- **Where.** `packages/engine/src/typehaus/takeoff/handoff.py:246-252` (the PE README) says "Section 9
  of each sheet lists, in that item's own terms, the failure modes this engine does not enumerate".
  Actual section 9 is `takeoff/calc_family.py:227-229`: `**SCREENING** — §4's states only; see
  06-conventions.md.` (e.g. `calcs/deck_post.md:136`). `06-conventions.md:20-22` is generic. PDF page S-22
  shows it: one line.
- **Evidence.** 16 of 18 sheets say SCREENING, 2 say EXTERNAL, 0 say COMPLETE
  (`grep "^\*\*Coverage" calcs/*.md`). The real exclusions exist, but only as free text scattered through
  `04-assumptions.md` under six spellings: "NOT GRADED" (rows at lines 17, 63, 65, 68, 90, 93, 110, 314,
  337, 434, 437), "Not graded:" (337), "SCREENING:" (147-150, 367, 435), "REVIEWER ITEM" (326), "CONFIRM"
  (`calcs/deck_post.md:36`). Some name an owner ("the geotechnical engineer", "the SRW supplier's engineer",
  line 434), most do not. Examples a PE must hunt for: global stability of the 9.1 ft court and the
  tiered SRW (`04-assumptions.md:434,437`), the wall-top's own capacity and stem flexure under the
  column moment (`:17,110`), connection detail at the cast column head (`:90`), corner bar development
  of the cast court loop ("is not something this engine has looked at", `:367`), the C_f 1.80 ceiling
  "because the figure's own cell is not a value this repository holds" (`:141`).
- **Confidence.** High (read directly).
- **Class.** SMALL-FIX now (fix the README claim, 6A-8); DECISION for the real fix.
  Options: (a) a hand-written per-kind table in the calc module (`NotCovered(state, why, owner, closes_by)`),
  printed in section 9 and on one front-matter page; cost M, ~18 kinds x 2-4 rows, mostly re-using the
  existing NOT GRADED text; not fingerprinted (same treatment as `Scope`, `item.py:228-234`).
  (b) lint the existing free text into one keyword. Cheaper, still scattered. **Recommend (a).** It also
  forces the owner to be named, which is the thing the PE is missing.

### E-02 · REVIEWABILITY (the big one) · Arithmetic is not shown, only the final quotient
- **Cause in code.** `LimitState` (`engineering/item.py:126-180`) has `name, demand, capacity, unit,
  citation, flags, combination` and nothing else. `_worked` (`takeoff/calc_family.py:137-171`) can only
  print `f"{demand:,.4g} demand / {capacity:,.4g} capacity"` (lines 160-165). Whatever substitution exists
  lives inside the free-text `citation`.
- **Which families show a real substitution, which only the quotient** (read in full on the sheets):

  | Shows numbers of the working inside the citation text | Shows only "demand / capacity" and a clause |
  |---|---|
  | thermal_break_transfer (e.g. `(mu 0.25 x D 280,144 + net at-rest 32,375) / H 27,316`; `5.5e-06 x 30 F x the full 323.0"`) | **tiered_retaining** (FS 1.538: no K_a, thrust, weight, delta, wedge) |
  | lateral_system (`1,034.6 lb x 8.682' / 4.979' = 1,804.0 lb, plus 426.5`; `M / W' = 2,064.3 / 23.469' = 88.0 lb`) | **retaining_wall** (stem flexure 1.228e4 / 1.418e4 ft-lb/ft: the thrust, H, lever arm and M are absent; As, d, f'c are given) |
  | wood_roof_post (`632.1 / 1,950 + 397.5 / 1,760`) | **retaining_system** (needs the E2/W2 cancellation, stated only in `04-assumptions.md:361`) |
  | column_head_joint (`T_th = ... = 1,999.3 lb-ft`) | **deck_post** (P_u 4,811, c 2.75" given; the Pu/Mu build-up is only in the per-member sheet's LOAD COMBINATIONS bullet) |
  | roof_beam (`M 3,858 lb-ft`, reaction `2,492 lb`) partial | glulam_beam, band_header, base_rotation, girt_screw (97.47 lb: tributary x pressure only in the scope line), deck_tie, column_base |

  So 5 of 16 computed families carry partial working, and in all of them it is prose, never an
  equation -> substitution -> result chain with units. The code's own docstring promises it:
  `calc_family.py:140-143` "THE SUBSTITUTIONS ARE THE POINT".
- **My check.** From the printed inputs of `retaining_system` alone I get 0.35 x (5,427x16.33 + 5,627x18 +
  5,427x16.33) = 97,486 lb and 3,123x18 = 56,214 lb -> FS 1.734; the sheet says 1.735. It reproduces, but
  only if I know that the E2 and W2 thrusts cancel, which is not on the sheet. For `tiered_retaining` I
  cannot reproduce 1.538 from the sheet at all.
- **Confidence.** High.
- **Class.** DECISION. Option A (recommended): add `LimitState.working: str = ""` (one line, e.g.
  `M = 0.5 x 40 psf/ft x 9.12^2 x 9.12/3 ... = 12,277 ft-lb/ft`), not hashed, printed as an extra column or a
  second line in `_worked` and the appendix. Fill in per kind, worst first: tiered_retaining,
  retaining_wall, retaining_system, deck_post, glulam_beam, girt_screw. Size L overall, M for the first
  three. Option B (M, lower value): promote the named intermediate values the modules already compute
  (thrust plf, weight plf, mu, M_u, V_u, P_u) from private variables to `Quantity` outputs so they appear in
  the symbol table; the symbol table then supports a hand re-do. Option C: leave it to the oracle notes,
  which is the status quo and the reason the PE has to rebuild every number.

### E-03 · GAP · No sketch, key plan or load path; the bundle carries no structural sheets
- **Evidence.** `grep -in "svg|sketch|figure|diagram|key plan|image|png" takeoff/calc_*.py takeoff/handoff.py
  cli/cmd_handoff.py` finds nothing relevant. The bundle tree (`docs/handoff-bundle-format.md:9-26`) is
  README, MANIFEST, draft toml, calcs, calcs.pdf, notes, model.ifc, model.glb, analysis/. The PDF has no
  image on any page I rendered. `03-open-items.md:11` points at "the S-603 rafter/truss line" and the draft
  toml / register cite sheets S-100, S-103, S-602 (`schedule/handoff.py:101-298`), none of which is in the
  bundle. The only locator is `analysis/centreline.dxf` (labelled members) and the IFC property sets.
  The register's "Elements" column is a tag list (and 36 tags in one cell for `girt_screw`,
  `02-item-register.md:31`).
- **Class.** DECISION. (1) S: put the permit set's structural sheets (foundation / framing / bracing / S-603)
  in `drawings/` of the bundle by calling the same print code, and cite them by sheet id in the register.
  (2) M: a generated key plan per storey (SVG from the model; engineered tags labelled and coloured by
  kind) as PDF page K-1..K-3, plus a "where" column (storey, nearest grid) in the register. (3) L:
  one small free-body or load-path sketch per kind (court section with thrust/weight/friction; column
  elevation with V, M, P; diaphragm plan with delivered shear). **Recommend (1)+(2) first.** The 3-D
  viewer is not a substitute: the PE signs a paper set.

### E-04 · GAP · No one-page reviewer's summary; no "what changed"; "presumed" list is soil only
- **Evidence.** The front matter is cover, criteria (4 PDF pages), register (4), open items (3),
  assumptions (20), scope (1). The register is sorted by id, not d/c. The five tiered walls at 0.975 and
  18 of 48 computed items at d/c >= 0.85 are not flagged anywhere (computed from `out/review/engineering.json`).
  Four deck posts show d/c 0.00-0.02 (`02-item-register.md:20-22,25`) because bending is not graded for them
  (`04-assumptions.md:147` "no bending from the beams' eccentric landing"), which reads as huge margin and
  is the opposite of information. There is no revision/issue or previous-issue comparison (the manifest
  hashes exist, `MANIFEST.json`, but nothing diffs them). `03-open-items.md` section D lists only
  `*_presumed` flags (`calc_package.py:378-382`), i.e. soil and n_h. It omits inputs that are authored or
  estimated: the 73.7 psf drift snow (`01-design-criteria.md:23`), the XPS "modulus ESTIMATED 525 psi ...
  (none published)" and "grade unstated ... the lowest the standard admits" (`calcs/thermal_break_transfer.md:23,37`),
  the C_f 1.80 ceiling, G 0.42 for LSL studs (`04-assumptions.md:326`).
- **Class.** DECISION: add `00-summary.md` / PDF page "SUM-1" with (i) criteria in a box (V_ult 115, Exp B,
  RC II, p_g 50 / design 73.7, soil GM presumed EFP 40/60, f'c, f_y), (ii) the ten highest-d/c items with
  governing state, (iii) counts by status/scope, (iv) every presumed/authored/estimated input with its
  source, (v) the not-covered owner table (E-01), (vi) "changed since issue X" (needs the previous
  fingerprints; the register's fingerprint per item makes this a straightforward diff:
  `haus calcs --since <prev out/calcs>`). Size M. Also put "states graded: n of n" beside every d/c so
  0.01 is not read as a result.

### E-05 · REVIEWABILITY · The PDF the PE is asked to stamp omits the per-member data
- **Evidence.** `cli/cmd_handoff.py:49-52`: `full: bool = typer.Option(False, ...)`. PDF page X-1 says
  "Not printed in this document." For `deck_post` (10 members) the PDF works one member (PT-SG-BF1) and
  prints the other nine as a schedule row; for `tiered_retaining` four of five, `base_rotation` three of
  four. The README (`handoff.py:234-237`) says "the file to mark up and stamp, because no jurisdiction accepts
  Markdown" and in the same breath that the member tables are in the Markdown. A seal binds to the flattened
  file, so the members' inputs are outside the sealed document.
- **Size of fix.** The appendix is 33 pages (`tests/test_calc_pdf.py:506-520`: default 89 -> 121 at the time;
  now 115 -> about 148 against a 150/220 budget), so `--full` as the default passes the existing page-budget test.
- **Class.** SMALL-FIX (6A-12).

### E-06 · REVIEWABILITY · "Worked at the governing member" hides distinct sub-templates
`deck_post` is three different calculations (M1 cast 12" fixed column, M2 14" with 6 bars, M3 axial-only,
`appendix/deck_post.md:9-11`) but only the M1 worst member is worked. The PE sees no P-M check for
PT-BW-PE/PNE (d/c 0.85 dowel anchorage, bending, magnified moment) or the four axial-only posts. The same
collapse machinery that makes M1-M3 (`calc_collapse.py`) can pick one worked member per template.
Class: DECISION, size M (`calc_family.py:232-287`, `_worked` per template group). Confidence: high.

### E-07 · REVIEWABILITY · Rounding makes demand = capacity, and notation hides the margin
- **Confirmed.** `calc_family.py:118-121` formats the schedule `f"{demand:,.1f}"`, `f"{capacity:,.1f}"` and
  `f"{ratio:.2f}"`. Observed (PDF S-72, `calcs/*.md` schedules): `tiered_retaining` "1.5 | 1.5 | (blank unit) |
  0.98" for FS 1.5 required / 1.538 achieved (true d/c 0.975); `retaining_system` "1.5 | 1.7 | | 0.86" for
  1.5 / 1.735; `deck_tie` "0.8 | 1.0 | | 0.78"; `wood_roof_post` "0.5 | 1.0 | | 0.55". Four of 18 schedules. The
  unit cell is empty on every FS row because the state is built with `unit=""` (`engineering/segmental_wall.py:291-294`).
- **Related.** `calc_family.py:149` and `:161-165` use `,.4g`, which switches to exponent notation at
  5 digits: `fy 6e+04`, `phi_Mn 2.467e+04`, `house_thrust 2.732e+04`, `4.08e+04 demand / 7.973e+04 capacity lb`;
  64 exponent tokens in the PDF text. Same in `calc_appendix.py:116-117` and `item.py:122`. Float noise
  prints as data: `calcs/column_head_joint.md:53` `seat_eccentricity 8.882e-16 in` (and `seat_bending 2.651e-13 lb-ft`),
  `calcs/band_header.md:57` `e 2e+06 psi`. `calcs/thermal_break_transfer.md:23` prints `x 2.00"/E 0.00000"`,
  a division by zero on the page.
- **The register and open items** use `.2f` (`calc_package.py:282,347,357,371`), so 0.975 and 0.98x are the same.
- **Class.** SMALL-FIX (6A-1, 6A-2). No ratio, state or fingerprint changes (`fingerprint.py` hashes
  rounded inputs and the ratio to 2 dp, not the print format).

### E-08 · REVIEWABILITY · tiered_retaining prints two friction values (confirmed and located)
- **Evidence.** `calcs/tiered_retaining.md:65` `friction_coefficient | 0.25 | —` and :82 citation
  `mu = tan 27.8°`. Source: `engineering/segmental_wall.py:360` emits
  `Quantity("friction_coefficient", base.friction_coefficient, "", 0.01)` unconditionally, but `_end`
  (`segmental_wall.py:283-290`) uses mu = tan(min(pad_phi, phi)) = 0.527 whenever a pad phi is authored (it
  is: `pad_friction_angle 36`); 0.25 (the IBC fallback) is not used. So the printed input is the one number
  that did NOT enter the 0.975 sliding ratio, and the one that did (0.527) appears only in the citation.
- **Other defects on the same sheet.** `soil_presumed 1 | -` (a flag with unit "-"), `wall_friction_ratio`,
  `tier_W-SG-S_facing -1 | —` (a sign convention: -1 = back-to-back, 1 = parallel, 0 = unknown,
  `segmental_wall.py:370-371`), `pad_friction_angle 36 deg` beside "the weaker of FB-RG-BLOCK's 36° and the ground's
  27.8°", where "FB-RG-BLOCK" is an internal pad tag. Fifteen of the 25 symbols have no meaning a PE can read.
- **Class.** SMALL-FIX (6A-14), but it changes the 5 tiered fingerprints, so bump `basis_version`
  (no seal exists yet). Confidence: high.

### E-09 · REVIEWABILITY · Design method "not declared" on 9 of 18 kinds; load combinations "not stated" is false for some
- **Cause.** `takeoff/calc_criteria.py:65-81` `DESIGN_METHOD` has 10 rows, one of which (`post_bearing`,
  `spread_footing`, `veneer_beam`) is not in this house; catlin's kinds missing from it: tiered_retaining,
  thermal_break_transfer, lateral_system, wood_roof_post, band_header, column_support, base_rotation,
  column_head_joint, deck_tie, rafter/veneer_anchor (deferred print their own words). `calc_family.py:246`
  falls back to "not declared". `01-design-criteria.md:79-95` shows the result.
- **Combinations.** `calc_criteria.py:122-123` prints "not stated ... this kind's arithmetic combines no cases"
  for kinds that do combine: `wood_roof_post` (citation "D + S ... roof_beam_snow_psf",
  `calcs/wood_roof_post.md` NDS wet-service row), `roof_beam` (D + S), `glulam_beam` ("M over the live patterns
  (ASCE 7-16 §4.3.3)"), `lateral_system` (0.6W / 0.6D + 0.6W is in the hold-down citation). The Load combination
  column is populated for only 5 kinds (column_support, deck_post P-M row only, deck_tie, girt_screw, thermal
  "1.0T") plus two declared by table (retaining_wall, retaining_system); for deck_post the governing
  five-combination table (1.4D / 1.2D+1.6L+0.5S / ... with Pu, Mu, phi*Mn, d/c each) exists only in a bullet of the
  per-member sheet (`appendix/deck_post__PT-SG-BF1.md:95`). The sentence at `01-design-criteria.md:98`
  ("'not stated' is not a missing factor") reads as defending a gap.
- **Class.** SMALL-FIX for the method column (6A-4) and the wording (6A-5). DECISION/M for populating
  `LimitState.combination` per kind (the field and its docstring, `item.py:154-180`, already invite it; the
  only guard is the intent that it not be guessed, which `test_calc_pdf.py:248-257` pins only as a default).

### E-10 · REVIEWABILITY · Symbols have no description; units "—" or "-"
`Quantity` (`item.py:98-122`) has `name, value, unit, quantum` and no label. Counted over the symbol tables:
unitless symbols are 8 of 26 in column_support, 6 of 19 in glulam_beam, 6 of 25 in tiered_retaining, 4 each
in base_rotation, girt_screw, retaining_system, 3 in column_base. Examples that block a PE: `tier_W-SG-S_facing`,
`soil_presumed`, `thread_in_stud`, `PT-SG-BR3.factored_axial` (PDF p.50), `joint_couple_lb_ft`,
`slats_crossing_mid_SB-BW-BAND`, `fy 6e+04`. **Class.** DECISION, size M: add `Quantity.label: str = ""`
(not hashed: `fingerprint.py` uses name, rounded value, unit only) and a fallback dictionary of the 60 most common
names; print "Symbol | Meaning | Value | Unit". Flags (`*_presumed`, `*_facing`) should render as words
("presumed: yes", "back-to-back").

### E-11 · REVIEWABILITY · Citations are long prose, printed twice, and each family lists dozens
- **Evidence.** The family sheet prints each citation in full in section 2 as `R1..Rn`
  (`calc_family.py:269`) and again in full in the section-4 table (`calc_family.py:168`). `deck_post` has 29
  references of which 20 are the same sentence with a different number (R8, R9, R17, R21, R26 are one
  "e_min magnified by delta_ns" sentence; R11, R18, R22, R27 one P-M sentence). `tiered_retaining` has 14,
  nine of which differ only by a tag. `lateral_system` repeats a 1,500-character construction note
  ("Field-verify that the six outermost holes start >=4-1/2in ... Keep deck panels continuous ...") fourteen
  times, one row per PDF page: pages S-40 to S-50 are eleven pages each holding one row (page 75 rendered).
  That text is a detailing instruction, not a reference, and a PE cannot tell which part is the clause.
  The lateral sheet alone is 22 of the 115 pages.
- **Class.** SMALL-FIX now: print `R#` in the section-4 column instead of the full text
  (`calc_family.py:168`). DECISION for the real fix: split `LimitState.citation` into `source` (the short key:
  "ACI 318-19 §25.4.2.4") and `note` (the member-specific numbers), or run `calc_collapse.collapse` over the
  references the way it already does for assumptions. Size M. The construction-note text belongs in the notes
  column of a schedule, once, not 14 times.

### E-12 · REVIEWABILITY · Open items page
- `03-open-items.md:11-12` repeats one 190-word cell verbatim for both roofs. Source: the deferral registry is
  per kind (`engineering/deferred.py:65-101`), and `_open_items` (`calc_package.py:320-337`) emits a row per
  item. Group rows whose (designer, deliverable, unblocks) are equal: "rafter/RF-BW-CANOPY, rafter/RF-GARAGE".
- The cell is internal prose: check ids `structural.truss_reactions`, `structural.uplift_capacity`, Python
  `Roof.published_reactions`, `DiaphragmSpec.chord_splice_slip`, `chord_force_*`, `lateral_system/<roof>`, history
  "is no longer a second role here", "(2026-09-20)". The PE-facing ask is two sentences (a component design
  and a reaction schedule for the stated snow and drift case, and the chord splice slip assumed).
- Headings are "A." and "D." with B and C silently absent (`calc_package.py:338-359` only print when non-empty): a
  reader assumes pages are missing. Print "B. Incomplete — none." and "C. Over capacity — none."
- Tone: "Nothing on this page is a guess that failed" (`:3`), "exactly as blocking as they were before they had
  names" (`:7`). Reads as defensive.
- Three names for the same three items: cover "NO LOCAL CALC 3", open items "3 of 51 not finished",
  scope "Deferred 3".

### E-13 · Seal path (answer to the 10-minute question)
- **Read from** `engineering/scaffold.py` and `engineering/register.py`. The draft has one `[[signoff]]` per
  kind (18 blocks, `scaffold.py:82-93`), each with four blanks (`engineer`, `license`, `sealed_on`, `document`,
  lines 45-48 and 160-166) = 72, plus `[signoff.external."<item>"]` for 3 deferred items with four more each
  (`document`, `revision`, `sha256`, `envelope`) = 12; 84 blanks of 7 distinct strings. Fingerprints are
  filled; the loader refuses any `<<...>>` left (`register.py:265-278`).
- **Is it under ten minutes?** Yes, if the four recurring strings are replaced globally
  (`<<ENGINEER NAME, PE>>`, `<<STATE 00000>>`, `<<YYYY-MM-DD>>`, `<<path/to/sealed.pdf>>`), and the test does exactly
  that (`tests/test_handoff.py:171-176`). By hand, 72 separate entries is not. Nowhere does the draft header,
  the README or `docs/engineering-toml-format.md` say so.
- **Defects.**
  (i) The deferred blocks (rafter, veneer_anchor) are live in the same file, and their `revision`, `sha256` and
  `envelope` cannot be filled by the PE today: the truss fabricator's document does not exist. The file will be
  refused by the loader until the PE deletes those two blocks. The header says "DELETE the blocks they did not"
  (`scaffold.py:73-74`) but the README step 2 (`handoff.py:289-292`) does not.
  (ii) `docs/engineering-toml-format.md:181` still says "Deferred kinds arrive **commented out** ... a live
  block would only invite a stamp that cannot work": the opposite of `scaffold.py:126-153`. The doc and its own
  example "a tiered retaining wall" (line 140) are stale (tiered retaining is computed now).
  (iii) The seal binds to `calcs.pdf`, yet the draft's `document` blank is `<<path/to/sealed.pdf>>`; the draft
  does not name the PDF or its sha256, although the PDF is byte-deterministic and the manifest already has the hash.
  (iv) `calc_family.py:299`, `calc_sheet.py:199` print "a seal can be recorded, never pinned" for NO_CALC, which
  contradicts the external-acceptance path.
  (v) The `[signoff]` per kind forces 16 blocks for one engineer stamping one PDF.
- **Class.** SMALL-FIX for the hint text, the README step and the stale doc (6A-9, 6A-15). DECISION (M):
  (a) a `[defaults]` table (engineer, license, sealed_on, document) in `engineering.toml` that every `[[signoff]]`
  inherits, loader change in `register.py:181-221`; or (b) `haus handoff --engineer ... --license ... --sealed-on ...
  --document calcs.pdf` writes the draft with those four filled (the engine still writes only into `out/`, so decision #65
  is untouched); and (c) write the 3 deferred acceptances to a second file `engineering-external.toml.draft` so a PE
  never has to delete blocks. **Recommend (b)+(c) plus pre-filling `document = "calcs.pdf"` and its sha256.**
  After that the PE's job is: type name, licence and date once.

### E-14 · REVIEWABILITY · Design-criteria page is incomplete or misleading in four places
- `01-design-criteria.md:53` "Where one value appears twice, two calculations were run against two different
  strengths. That is reported and not reconciled." The table shows one f'c (5,000). But
  `calcs/thermal_break_transfer.md:77` uses `slab_fc 4,000 psi` (the strut capacity 2,040 psi =
  0.6 x 0.85 x 4,000). The `_MATERIAL_INPUTS` whitelist (`calc_criteria.py:263-269`) lists only `fc`, `fy`,
  `Fb_adjusted`, `E_adjusted`, `concrete_unit_weight`, so slab concrete, every lumber species and grade (SP No. 2
  timbers, SPF, 24F-V4 DF, 24F-V5M1/SP, LVL 2.0E, LSL), steel shim grades and the connector table are absent. A PE
  expects a materials schedule. Confidence on the 4,000 vs 5,000 point: high.
- No live, dead, guard or seismic criteria. The sheets use 40 psf floor live, 10 psf dead, the 200 lb guard,
  15 psf wall dead, 8 psf framed walls; none is on D-1..D-4. The seismic design category is not stated at all
  (the bracing and diaphragm kinds rely on wind only, with no "seismic not governing" line).
- `01-design-criteria.md:55` heading "5. Service conditions" is a list of standards; a PE reads it as moisture and
  temperature exposure (the wet/dry service C_M choices are in assumptions). Rename.
- `01-design-criteria.md:15` "see the design-method column above": the column is in section 6, below.
- The markdown cover says `Jurisdiction profile: mn-2020` only; the PDF cover has the code name but the line
  `LOADS see the design criteria sheet` (PDF C-1) is blank because `asce_edition` is never passed
  (`cmd_handoff.py:84-91`).
- `00-cover.md:30` "every ratio is within capacity" over-claims against the scope text (graded states only).
- **Class.** SMALL-FIX for the rename, "above", cover fields; DECISION (M) for the loads and materials tables
  (derive from the same inputs as now: widen the whitelist and read library material records).

### E-15 · Numbers that disagree between pages
1. `calcs/deck_post.md:15` "at d/c 0.18 in bending" vs `:61` and `:116` d/c 0.88. The summary states a bending-state
   ratio next to "d/c"; the item's d/c is 0.88. Source: `engineering/deck_post.py:870` builds
   `f"{... :.2f} in bending on {which}"` into the summary. Fix: "bending d/c 0.18".
2. Same loop, two friction totals: `calcs/retaining_system.md:15` "97,508 lb of base friction ... 56,210 lb of
   resultant thrust" vs `calcs/thermal_break_transfer.md:29,33` "loop W-SG-ARCH's base friction 107,211 lb" and
   "retained soil's 55,301 lb at 130 pcf" (the other sheet's soil basis is 110 pcf, `04-assumptions.md:361`).
   Probably different load bases, but no sentence says so. I did not trace it. UNVERIFIED which is intended.
3. The schedule's first row is not the governing member, and nothing marks it: `base_rotation` schedule leads with
   PT-SG-BF1 (0.1783) while §1 names PT-SG-BR1 (0.1785) and "Governed by"; same in `column_base`
   (PT-BW-PE listed first, 0.34; the sheet is worked on PT-BW-PNE, 0.50) and `roof_beam`.
4. "3 of 51 not finished" / "Deferred 3" / "NO LOCAL CALC 3" (E-12). Also `02-item-register` d/c prints 0.98, the sheet 0.975.
5. `calcs/deck_post.md:72-94` (worked symbols) and `04-assumptions.md:143` ("Until 2026-09-11 ... 1,104 -> 1,840 lb-ft")
   give two moment bases; the sheet uses 1,840 and 4,230 lb-ft (strength level) correctly, but a PE must read the
   assumption to learn that "wind_base_moment_Mu" is the ASD value divided by 0.6.
6. `01-design-criteria.md:39` "Soil unit weight band 110–130 pcf" while `calcs/tiered_retaining.md:15` reports
   "at 110 pcf" only; the 130 pcf end (which governed other walls) is not shown.

### E-16 · Hedging, history and engine-speak (the text that would make a PE distrust)
See section 4 for the quoted list (file:line). Counts over the markdown package: "this engine"/"the engine" 14
in front matter and sheets (`calc_*.py`, `handoff.py`, `scaffold.py`: lines listed in 6A-11); dated history 8
("Until 2026-09-11", "Until 2026-09-18" x2, "until 2026-09-12", "(2026-09-11)", "(2026-09-20)", "no longer" x2,
"retired deferral" x2, "now puts a force"); Python identifiers and check ids about 40 (`pier_basis`, `balcony_wind`,
`ConcreteSpec`, `lateral_support="top_and_bottom"`, `Pad.resists_base_moment`, `structural.truss_reactions`,
`Roof.published_reactions`, ...); statements that hand a decision to the reader (E-01). Many sit in strings inside
the calc modules, so they are fixed in the engineering code, not the emitter.
**Class.** DECISION, size M, then a lint: one test that fails on `\b20\d\d-\d\d-\d\d\b` (except "read <date>"
retrieval dates), `no longer`, `Until `, `retired`, `this engine`, `structural\.[a-z_]+`, double backticks and
snake_case.Class.attr tokens in any `record.notes` or `citation` (extend `test_calc_pdf.py:457` style masks).

### E-17 · COSMETIC
- PDF: item ids split mid-token ("column_head_joi / nt/PT-SG-BF1", "band_header/D-B / -SUNKEN", p.R-1; member names
  "PT-SG-BF / 1", S-20). The family-sheet header (9 key/values) is nine paragraphs, half a page (S-65, S-71): use one
  two-column table. Schedule columns Coverage and Seal repeat constants on every row (`calc_family.py:132-133`).
  Symbol tables use 1/3 of the width.
- README: "in the standard nine-section order" (`takeoff/calc_package.py:144`, `README.md:12`) but family sheets have ten
  sections; `docs/calc-package-format.md:181` "Thirty items in catlin are computed by nothing" is stale and
  contradicted two paragraphs later ("An exact count does not belong in this document").
- The handoff README step 1 (`handoff.py:216-217`) sends the PE to `calcs/00-cover.md` for "the design criteria every
  calculation shares. If a criterion is wrong, stop here." The criteria are in `01-design-criteria.md`; and the path
  `calcs/calcs/<kind>.md` (line 221) is easy to misread.
- Section 10 "Per-member fingerprints" and "Basis version" on every sheet are machine data a PE does not use; they
  belong in the register/seal form, not in each calculation.
- Independent-check rows cite `tests/test_pier_calcs.py`, a path in a repo the PE does not have (PDF S-22).
  The notes are in the bundle (`notes/`), the tests are not; name the note only.

---------------------------------------------------------------------------------------------

## 2. The brief's specific questions, answered

| # | Question | Confirmed? | Where | Fix |
|---|---|---|---|---|
| 1 | Schedule rounds FS so demand = capacity | Yes, 4 of 18 schedules | `calc_family.py:118-121` | 6A-1 |
| 2 | Arithmetic behind "1.735 achieved" not shown | Yes; real working only inside prose of 5 families | `item.py:126-180`, `calc_family.py:137-171` | E-02 |
| 3 | tiered friction 0.25 vs tan 27.8 | Yes; the 0.25 is unused | `segmental_wall.py:360` vs `:283-290` | 6A-14 |
| 4 | "Design method: not declared" | Yes, 9 kinds | `calc_criteria.py:65-81` | 6A-4 |
| 5 | Symbols undescribed, unit "—"/"-" | Yes | `item.py:98-122` | E-10 |
| 6 | Long prose citations repeated | Yes (29 refs for deck_post, 14 pages of one repeated note) | `calc_family.py:168,269` | 6A-6 + E-11 |
| 7 | Open items repeats 200-word cell | Yes | `calc_package.py:320-337`, `deferred.py:65-101` | 6A-7 |
| 8 | Coverage SCREENING; are exclusions per family with owners? | No; the PE must infer | `calc_family.py:227-229` | E-01 |
| 9 | Sketch / key plan; bundle carries plan sheets? | None; no | `cmd_handoff.py`, `docs/handoff-bundle-format.md` | E-03 |
| 10 | One-page summary (by d/c, changes, criteria box, presumed inputs) | None | `calc_package.py:92-101` | E-04 |
| 11 | Governing load combination ever printed? | Yes for 7 of 16 kinds; 9 print a dash or "not stated" | `calc_criteria.py:96-137` | E-09 |
| 12 | Path from "PE agrees" to sealed; 51 items in 10 minutes? | Yes, ~3 min with find/replace of 4 strings; undocumented | `scaffold.py:53-79` | E-13 |

---------------------------------------------------------------------------------------------

## 3. PDF inspection (the one allowed `haus handoff` run)

Run: `.venv/bin/haus handoff houses/catlin --out out/review/handoff` started 10:18, `calcs/` and `calcs.pdf` written
10:26, command finished later with "wrote out/review/handoff (120 files, 51 item(s), 16 note(s))". Package text under
`calcs/` is byte-identical to the checked-in `houses/catlin/out/calcs/`. The finished bundle also confirmed:
`engineering.toml.draft` has 18 `[[signoff]]` blocks and 84 blanks of 7 distinct strings (`ENGINEER NAME, PE` 18,
`STATE 00000` 18, `YYYY-MM-DD` 18, `path/to/sealed.pdf` 21, revision 3, sha256 3, envelope 3), the rafter and
veneer_anchor blocks are live (uncommented) with `[signoff.external]` tables, and the deferred blocks' comment repeats the
whole open-items cell (with its history and check ids). The bundle `README.md` step 2 says the register is "on one page"
(it is four PDF pages) and step 1 points at `00-cover.md` for the criteria.

- `pdfinfo`: 115 pages, letter, 482 KB, CreationDate pinned to 1999-12-31 (deterministic), no tags, no
  outline check done. Index on C-1 lists every section and links.
- Page mix (labels): C-3, D-4, R-4, O-3, A-20, SR-1, S-1 (conventions), then calculations S-2..S-?, appendix
  divider X-1. Front matter is 35 pages; `lateral_system` alone is S-33..S-54 (22 pages).
- Rendered and read at 70 dpi:
  - **C-1 cover.** Clean. "PREPARED BY TYPE:HAUS", "CHECKED BY ______", `LOADS see the design criteria sheet`, an
    empty seal box, index. No gate status, no "issue/revision", no summary.
  - **D-1 criteria.** Readable tables; see E-14 for content gaps.
  - **R-1 register.** 13 items per page; item ids wrap mid-token; d/c 0.00-0.02 rows with no flag.
  - **O-1 open items.** One tall cell of ~190 words in a narrow column, Python identifiers wrapped mid-word
    (`structu / ral.truss_reactions`, `Roof / .published_reaction / s`).
  - **S-20 deck_post worked table.** `fy 6e+04`, `phi_Mn 2.467e+04`; a 21-row symbol table using a third of the width.
  - **S-22.** Section 6 is a pointer, section 9 is one line, section 10 fingerprints; `tests/test_pier_calcs.py`.
  - **S-40 (lateral_system).** One table row per page, 1,500-character citation (E-11); the eleven pages S-40..S-50.
  - **S-65 / S-71.** Header block as nine stacked paragraphs; thermal R2/R3 show `5.5e-06` and `E 0.00000"`.
  - **S-72 (tiered).** `Demand 1.5 | Capacity 1.5 | Unit (blank) | d/c 0.98`; `soil_presumed 1 -`; `friction_coefficient 0.25`.
  - **X-1.** "Not printed in this document." (E-05).
- Widest tables: the 10-column schedule (S-72) fits but wraps tags; the appendix's 4-member tables (not in the PDF
  by default) are the widest in the package (`appendix/deck_post.md`: cells like `1,454 / 2.859e+05 = 0.005 (R2)`).

---------------------------------------------------------------------------------------------

## 4. Cold-read list: where I got lost, quoted with file:line

(Everything under `houses/catlin/out/calcs/` unless noted. "Q" = quote.)

**Undefined terms / engine words**
- `README.md:3` Q "it is this engine's own first-principles arithmetic, checked against an independently hand-worked
  note" ("this engine" is never defined for the reader; the cover calls it "the Type:Haus engine" once).
- `02-item-register.md:3` Q "identity is per element and never per group" (modelling jargon).
- `calcs/column_head_joint.md` and `04-assumptions.md:90` Q "what the retired deferral asked for".
- `06-conventions.md:9` Q "A member not in it is a member this engine does not know about".
- `03-open-items.md:11` Q "`structural.truss_reactions` ... (`Roof.published_reactions`, 2026-09-20)".
- `04-assumptions.md:141` Q "(the Fig. 29.3-1 Case A/B ceiling, taken because the figure's own cell is not a value
  this repository holds)".
- `04-assumptions.md:143` Q "Wind arrives from ``pier_basis`` at ASD — ``balcony_wind`` bakes §2.4.1's 0.6 in".
- `calcs/thermal_break_transfer.md:30,31,33` Q "(free body §11m.2)", ":9 free body §11k" (a section of a note not named in
  the line); "BarSpec.continues_into" (`:34`); "FB-RG-BLOCK" (`calcs/tiered_retaining.md:22`).
- `calcs/lateral_system.md:22` Q "the column recorded; DF/SP is 1,175 lbf for the same row"; `:44` Q "(the row reads 15 OSB)".
- `calcs/wood_roof_post.md` Q "F2 along Connector.axis y" (CBSTQ rows).
- "record", "fingerprint", "basis version", "oracle" appear in PE-facing text (`02-item-register.md`, `05-scope`, section 10).

**Self-referential history / dates**
- `calcs/rafter.md:15` Q "(2026-09-11)"; `03-open-items.md:11` Q "no longer a second role here ... 2026-09-20".
- `04-assumptions.md:143` Q "Until 2026-09-11 both were compared at working stress against phi*Mn, which mixed two
  bases inside one P-M point; no column was re-sized by the correction."
- `04-assumptions.md:144,145` Q "Until 2026-09-18 only 1.2D + 1.6L's axial was used, which credited this column with
  compression the governing case does not have."
- `04-assumptions.md:321` Q "ALTERNATE THAT FAILS, recorded because it was the specified screw until 2026-09-12".
- `04-assumptions.md:367` Q "`corner shear transfer` now puts a force on what it would have to develop".
- `calcs/lateral_system.md:44` Q "unchanged from the 5/8in CDX reading".
- Retrieval dates `read 2026-09-30` (25 times) are acceptable as accessed-on dates, but say "accessed".
These are the sentences that make a reader ask what the numbers were before and whether the correction is complete.

**Hedging / reads as not finished**
- `04-assumptions.md:367,435` Q "SCREENING on presumptive code values, not a design" (retaining court and tiered SRW).
- `04-assumptions.md:313` Q "a service-condition judgement the engineer of record confirms".
- `04-assumptions.md:326` Q "REVIEWER ITEM: the main-storey studs are LSL ... for the PE to confirm or replace".
- `calcs/deck_post.md:36` Q "CONFIRM the tie continuation and the side cover on the drawing: both psi factors are 1.6
  and 1.25 without them" and `:35` "The AUTHORED lap is in the assembly's source and on the drawing" (the PE has neither).
- `calcs/thermal_break_transfer.md:23,36` Q "modulus ESTIMATED 525 psi = 35 x 15 ... (none published)"; `:37` "grade unstated,
  graded at ASTM C578 Type X 15 psi, the lowest the standard admits".
- `calcs/lateral_system.md:35,38,46` Q "a deliberate round-down for this 19/32in deck, and G_a at the soft end of the band".
- `04-assumptions.md:326` and `:313` leave decisions to the reader; each is an E-01 row that needs an owner and a closure.

**Cross-references the PE must follow**
- Every §4 row needs §2 (R#), `04-assumptions.md` (the working), an `appendix/<kind>.md` table (other members) and a
  note in `notes/` (the check). Four documents per number.
- `calcs/tiered_retaining.md:21-34` R2..R14 are indexed by member but nothing says which R belongs to which member
  (the appendix does, the family sheet does not).
- `01-design-criteria.md:98` and `calcs/deck_post.md` rows "—" for Load combination while the combination is in the
  citation prose ("ASCE 7-16 §2.3.1's 1.6L").

**Numbers that read wrong**
- `calcs/column_head_joint.md:53` `seat_eccentricity | 8.882e-16 | in`.
- `calcs/band_header.md:57` `e | 2e+06 | psi` (E, lower-case, sci notation).
- `calcs/thermal_break_transfer.md:23` `x 2.00"/E 0.00000"`.
- `calcs/tiered_retaining.md:62` `soil_presumed | 1 | -`; `:75` `tier_W-SG-S_facing | -1 | —`.
- `calcs/retaining_system.md:28` "1.5 | 1.7" for FS 1.5 required / 1.735 achieved.
- `02-item-register.md:20-22,25` d/c 0.01, 0.00, 0.02, 0.02 beside 0.88.

---------------------------------------------------------------------------------------------

## 5. Status of the 2026-09-18 gap review items in my area

- **Finding 8 (PDF not easy to review).** Tables render, no truncation, index and links complete, appendix
  collapsed, one sheet per family: CLOSED (8a in the note). STILL OPEN from its own "Close with": annotated load-path
  plans/sections; "substitutions/units alongside equations" (only partial, E-02); linked construction details; the
  prescriptive-evidence schedule (not in the bundle; `05-scope-of-review.md:14` says it is "graded by haus check
  and is not in this package"); one-page readiness summary.
- **Finding 9 (computed vs ready for review).** CLOSED: `Scope` axis, README no longer says "nothing missing" or "not
  yours", criteria state a method per kind (but 9 kinds undeclared, E-09), design snow printed beside p_g,
  permit-gate state in the README. STILL OPEN: "make every exclusion an owned closure item" (E-01), generate the
  criteria "from the actual cases" (materials/loads incomplete, E-14).
- **Finding 10 (seal freshness / external acceptance).** CLOSED in code (`register.py` UNPINNABLE, external
  acceptance, scaffold live block). The doc `docs/engineering-toml-format.md:181` was not updated (E-13).

---------------------------------------------------------------------------------------------

## 6. Target shape

### Target document order (PDF = what the PE stamps; markdown identical)

1. **SUM-1 Reviewer's summary (1 page)**: criteria box; 10 highest-d/c items; counts by status/scope; presumed,
   authored and estimated inputs with source; not-covered owner table (top lines); "changed since issue" list.
2. C cover (code edition, loads edition, issue/revision, gates, seal box).
3. D criteria (complete loads and materials).
4. **K key plan + load path** (1-3 pages) and the structural sheets in `drawings/`.
5. R register sorted by d/c, "graded states n/n", where (storey, grid), flag column.
6. O open items (grouped, no history, with owner and closure).
7. **N not covered, by family, with owner** (E-01).
8. S calculations: header table, schedule (governing row bold; true numbers), worked member per template with a
   Working column, references as R-keys, 1-line fingerprint at the end only.
9. A assumptions (history and engine-speak removed).
10. X appendix (printed by default).
11. Seal form with PE name/licence/date entered once.

### 6A. S-size, text/format-only, clearly safe (exact edits)

All paths under `packages/engine/src/typehaus/`. None changes a ratio, state or fingerprint (except 6A-14, flagged).
Tests: none of the calc-package tests pins these strings (grep checked `test_calc_package.py`,
`test_calc_package_truthfulness.py`, `test_calc_pdf.py`, `test_handoff.py`), they are assertion-based, and
byte-determinism (`test_calc_package.py:359`, `test_calc_pdf.py:167,544`) only compares two runs.

| ID | File:line | Old | New | PE gains |
|---|---|---|---|---|
| 6A-1 | `takeoff/calc_family.py:118-121` | `demand = f"{governing.demand:,.1f}"`; `capacity = f"{governing.capacity:,.1f}"`; `unit = governing.unit`; `ratio = f"{governing.ratio:.2f}"` | `demand, capacity = _num(governing.demand), _num(governing.capacity)`; `unit = "FS (req'd / achieved)" if governing.is_safety_factor else governing.unit`; `ratio = f"{governing.ratio:.3f}"`, with a new helper `_num(x, sig=4)`: returns "0" if `abs(x) < 1e-9`, else `f"{x:,.{max(0, sig-1-floor(log10(abs(x))))}f}"` (positional, never exponent) | 1.500 / 1.538 / 0.975; 0.7838 / 1.000; no "0.8" |
| 6A-2 | `takeoff/calc_family.py:149,161-167`; `takeoff/calc_appendix.py:116-117`; `engineering/item.py:122` | `f"{q.value:,.4g}"`, `f"{state.demand:,.4g}"` etc. | `_num(...)` (import from a shared `takeoff/numfmt.py`) | No `6e+04`, `8.882e-16`; "60,000", "24,667", "0" |
| 6A-3 | `takeoff/calc_package.py:282,347,357,371`; `calc_family.py:185`; `calc_sheet.py:162` | `{...ratio:.2f}` | `{...ratio:.3f}` | 0.975 not 0.98 |
| 6A-3b | `takeoff/calc_family.py:124` | `f"\`{record.item_id.split('/', 1)[1]}\`"` | wrap in `**` when `record is worst` | the governing member is marked in the schedule |
| 6A-3c | `takeoff/calc_family.py:132-133` | always `"Coverage", "Seal"` columns | drop a column when all rows are equal and print it once in the header block | wider schedule, fewer wraps |
| 6A-4 | `takeoff/calc_criteria.py:65-81` | 10 rows | add (wording to be confirmed against each module's docstring; I derived them from the sheets): `tiered_retaining`: "ASD (IRC R404.4 safety factors on service loads; IBC Table 1806.2 allowable bearing)"; `thermal_break_transfer`: "MIXED — ASD for soil, sliding and the foam's sustained-load rule; LRFD for the plain-concrete near line and the winter-tension bars (ACI 318-19, phi 0.60 / 0.90, 1.0T)"; `lateral_system`: "ASD (SDPWS-2015 nominal unit shear / 2.0; wind at 0.6W; published connector allowables)"; `wood_roof_post`: "ASD (NDS 2018 reference values x adjustment factors; ICC-ES connector allowables)"; `band_header`: "ASD (NDS 2018; the LVL and rim-board makers' allowable design values)"; `column_support`: "LRFD (ACI 318-19 §22.8 bearing, §22.9 shear friction, §25.4 development; ASCE 7-16 §2.3.1)"; `base_rotation`: "LRFD (ACI 318-19 §6.6.4.5 at the factored deck_post demands)"; `column_head_joint`: "MIXED — LRFD for column shear, torsion and seat bearing; ASD for the head connector's published allowable"; `deck_tie`: "ASD (published connector allowables, linear interaction; 0.6W)" | no "not declared" on 18 sheets. Add a test that every kind in a package has a non-empty method (sibling of `test_calc_package_truthfulness.py:161`) |
| 6A-5 | `takeoff/calc_criteria.py:38,122-123,167-169,295-296` | `"5. Service conditions"`; `"not stated"` / `"this kind's arithmetic combines no cases"`; `"see the design-method column above for which kinds are ASD and which are LRFD"`; the "reported and not reconciled" sentence | `"5. Codes and standards, by kind"`; `"not recorded on the limit states"` / `"see the kind's sheet, section 4"`; `"see section 6 for which kinds are ASD and which are LRFD"`; emit the "two different strengths" sentence only when a material row actually repeats | consistent, true wording |
| 6A-6 | `takeoff/calc_family.py:168-169` | `state.citation` in the Citation column | `` f"R{refs.index(state.citation)+1}" `` (the full text is already in section 2) | ~1.5 pages saved on deck_post; lateral sheet shrinks by 12+ pages |
| 6A-7 | `takeoff/calc_package.py:320-337,338-359` | one row per deferred item; B/C absent when empty | group items with identical (designer, deliverable, unblocks) into one row ("rafter/RF-BW-CANOPY, rafter/RF-GARAGE"); when B or C is empty print "B. Incomplete — none." / "C. Over capacity — none." | no 190-word cell twice; no apparent missing sections |
| 6A-8 | `takeoff/handoff.py:246-252` | "Section 9 of each sheet lists, in that item's own terms, the failure modes this engine does not enumerate — they are not evaluated and they are not implied to pass." | "The failure modes not graded for each family are listed in `04-assumptions.md` (rows beginning NOT GRADED or SCREENING). They are not evaluated and not implied to pass." (until E-01 lands, then point to `N`). Also `:216-217` "`calcs/00-cover.md` — the building, the code edition, and the design criteria" -> "`calcs/00-cover.md` (status) and `calcs/01-design-criteria.md` (the criteria every calculation shares)". Test `test_calc_package_truthfulness.py:141-159` pins only `"screening"` and the two absent phrases | the README stops asserting what the sheets do not contain |
| 6A-9 | `engineering/scaffold.py:53-79` (the `_HEADER`) | step 2 "Fill in the engineer, the license, the date and the path ..." | add: "Four strings repeat in every block: `<<ENGINEER NAME, PE>>`, `<<STATE 00000>>`, `<<YYYY-MM-DD>>`, `<<path/to/sealed.pdf>>`. Replace each with one find-and-replace. The `[signoff.external]` blocks (rafter, veneer_anchor) need a supplier's document: delete those two blocks until it exists." Keep the placeholder constants unchanged (`tests/test_handoff.py:171-176` replaces them literally) | the 3-minute route is stated; the 2 external blocks no longer break the loader |
| 6A-10 | `takeoff/calc_family.py:299`; `takeoff/calc_sheet.py:199` | "— (no inputs to fingerprint; a seal can be recorded, never pinned)" | "— (not pinned to the model; an outside designer's sealed document is recorded instead, see `engineering.toml.draft`)" | true after decision #65 external acceptance |
| 6A-11 | `calc_family.py:151,342,346,351`; `calc_appendix.py:62`; `calc_criteria.py:211`; `calc_package.py:46,185,240,247,317,333`; `calc_sheet.py:29,43,56,103,253,258`; `handoff.py:143,151,227,246,250,259,263,315` | "this engine", "the engine" | "this calculation" / "the analysis" (name the software once, on the cover: "generated by Type:Haus"). Example: `calc_package.py:240` "This engine derived a demand and a capacity" -> "A demand and a capacity were computed". Mind `test_calc_package_truthfulness.py:141-159`: it pins "**Some of them are yours.**" only | reads as a calculation, not as software |
| 6A-12 | `cli/cmd_handoff.py:49-52` | `full: bool = typer.Option(False, "--full", ...)` | default `True`, flag `--full/--no-appendix` (page budget test `test_calc_pdf.py:506` passes: ~148 pages < 220) | the stamped PDF contains every member's data |
| 6A-13 | `engineering/deck_post.py:870` (also `:968`, `:1040`) | `f"{...:.2f} in bending on {which}"` after "at d/c" | "bending d/c {x:.2f} on {which}" | no 0.18 vs 0.88 on one page |
| 6A-14 | `engineering/segmental_wall.py:360` (+ bump `basis_version`) | `Quantity("friction_coefficient", base.friction_coefficient, "", 0.01)` | `Quantity("friction_coefficient", math.tan(math.radians(shown.base_phi_deg)) if shown.base_phi_deg is not None else base.friction_coefficient, "", 0.01)` computed after `shown` is chosen (line ~323); relabel `facing` and `soil_presumed` per E-10. **Changes the 5 tiered fingerprints** (no seal exists) | one friction value, the one used |
| 6A-15 | `docs/engineering-toml-format.md:140,172,181`; `docs/calc-package-format.md:181`; `docs/handoff-bundle-format.md:51` | "Deferred kinds arrive **commented out** ..."; "a tiered retaining wall" as an external item; "forty"; "Thirty items in catlin" | rewrite to the live external-acceptance block; drop counts | docs match behaviour |
| 6A-16 | `engineering/deferred.py:72,77-80` (reason/designer strings) | "(2026-09-11)", "is no longer a second role here", "(`Roof.published_reactions`, 2026-09-20)", check ids | "A roof framed in an engineered profile is not here: its maker's published span table is read directly. The truss fabricator's design is the component only; the chain below the heel is checked against its published reactions once they are entered." (no dates, no ids) | open-items cell is half the length and readable |
| 6A-17 | `takeoff/calc_package.py:144` and `README.md:12` | "in the standard nine-section order" | "in a ten-section order" | accurate |
| 6A-18 | `takeoff/calc_family.py:193-200` (`_open_inputs`) and `:283` | NO_CALC sheet: `_None._`, "No citation is recorded." | print the deferral's designer and deliverable from `DEFERRALS` on the NO_CALC sheet | `calcs/rafter.md` says who owns it |

### 6B. Larger restructures (priority order)

| Pri | Change | PE gains | Generator files | Size | Determinism / tests affected |
|---|---|---|---|---|---|
| 1 | **Working column**: `LimitState.working`, filled for tiered_retaining, retaining_wall, retaining_system, deck_post first | the PE can check, not rebuild (E-02) | `engineering/item.py`, calc modules, `calc_family._worked`, `calc_appendix._states` | L (M for the first 3 kinds) | none hashed (not in `fingerprint.py`); `test_every_citation_on_a_record_reaches_its_references` unaffected |
| 2 | **Not-covered table per family with owner** (E-01) | the PE sees what a stamp does not cover | `engineering/item.py` (`NotCovered`), calc modules (re-use the NOT GRADED text), `calc_family._exclusions`, new `N` page in `calc_pdf.SECTIONS` | M | `test_calc_pdf.py::test_every_front_matter_file_has_a_prefix`, `::test_no_boilerplate_line_is_printed_twice`; not hashed |
| 3 | **Reviewer's summary page + changes since last issue** (E-04) | one page to decide whether to read the rest | new `calc_summary.py`, `calc_package.calc_package`, `calc_pdf.SECTIONS`, `cmd_calcs`/`cmd_handoff` `--since` | M | `test_the_front_matter_is_complete`, `test_every_front_matter_page_the_doc_lists_is_actually_written`; adds a file |
| 4 | **Structural sheets + key plan in the bundle** (E-03) | tags can be located; sheet ids cited in open items exist | `cmd_handoff.py`, the print pipeline, `emit/draw/*plan*.py` for an overlay | M (sheets) + M (key plan) | manifest changes; `docs/handoff-bundle-format.md` |
| 5 | **Seal form**: `[defaults]` or `haus handoff --engineer ...`, external blocks to a second file, `document = calcs.pdf` + sha256 | PE types name/licence/date once (E-13) | `engineering/scaffold.py`, `engineering/register.py:181-221`, `cmd_handoff.py` | M | `tests/test_handoff.py:154,171`, `test_engineering_register.py` (placeholder strings must stay) |
| 6 | **Citation = source key + note**; collapse near-duplicate references (E-11) | 29 -> about 8 references on deck_post; clauses legible | calc modules (split citation), `calc_collapse.py`, `calc_family.references` | M | `test_every_citation_on_a_record_reaches_its_references` |
| 7 | **Symbol labels + flag words** (E-10) | no guessing at `soil_presumed`, `facing` | `item.py` `Quantity.label`, calc modules, `calc_family._worked` | M | not hashed |
| 8 | **Worked member per template** (E-06) | all three deck_post designs are shown | `calc_family.render_family`, `calc_collapse` | M | `test_every_family_calculation_carries_its_own_sections_in_order` |
| 9 | **Load combinations everywhere** (E-09) | governing combination named at every row | calc modules set `LimitState.combination`; `calc_criteria` | M-L | `test_the_load_combination_column_prints_a_dash_and_never_a_guess` (default only) |
| 10 | **Complete criteria page**: live/dead/guard/seismic, full materials schedule (E-14) | the PE sees every criterion in one place | `calc_criteria.py` (widen `_MATERIAL_INPUTS`, read library materials) | M | `test_calc_package.py:352-359` pins specific strings |
| 11 | **Free-body / load-path sketches per kind** | the geometry of each calc is visible | new drawing helpers | L | additive |
| 12 | **Text lint** for history/engine-speak/check ids, then sweep ~60 strings (E-16) | trust | one test + calc modules | M | new test |

Rough effort: 6A about one day; items 1-2 and 5 the main PE-facing wins; 3-4 are what a PE notices first.

---------------------------------------------------------------------------------------------

## 7. Verified correct / what I did not verify

**Verified (with the check):**
- Package vs bundle: `diff -rq houses/catlin/out/calcs out/review/handoff/calcs` differs only by `MANIFEST.json`
  (generator is deterministic; the markdown I read is what the PE would get).
- `retaining_system` FS 1.735 reproduces to 1.734 from the sheet's own inputs (inline hand calculation, E-02) apart from the
  undisclosed E2/W2 cancellation.
- Blank count in the draft toml (84) matches my count from `scaffold.py` and the test's four literal replacements.
- Seal path: `register.py:265-278` refuses any `<<...>>`; `scaffold.py` emits one block per kind and 84 blanks; the
  test fills them with four literal replacements (`tests/test_handoff.py:171-176`).
- Fingerprint excludes everything proposed (`fingerprint.py`: name, rounded value, unit, basis_version, ratio 2 dp), so
  `Quantity.label`, `LimitState.working`, `NotCovered`, formats and wording do not stale any seal; only 6A-14 does.
- Page budget: current PDF 115 pages vs the 150/220 ceiling in `test_calc_pdf.py:506-530`.
- Sorted d/c table: from `out/review/engineering.json` (5 tiered at 0.975; 0.908 lateral; 0.884 x 6; 0.877 x 2;
  18 items >= 0.85; 4 items < 0.05).

**Not verified:**
- Any engineering value (code tables, manufacturer values, friction/EFP, wind); that belongs to the engineering reviewers.
- Whether `retaining_system` 97,508 lb and `thermal_break_transfer` 107,211 lb of "W-SG-ARCH base friction" are the same quantity
  on different bases (E-15.2). UNVERIFIED.
- The proposed DESIGN_METHOD wording (6A-4) is my reading of the sheets, not of each calc module's docstring; confirm
  before pasting.
- Model content of `model.ifc` / `model.glb` and `analysis/` (only their existence and the README's description were checked).
- I did not run any tests; test names above come from reading them.

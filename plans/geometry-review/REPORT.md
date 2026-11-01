# Geometry & dimensional-accuracy review — report (2026-10-31)

Review of SHA `247a13e9`. The review ran in three phases:

- **Phase 1:** 26 Sonnet reviewers produced 244 findings. Six thin areas were sent back once (S2, O3, O4, F1, I4).
- **Phase 2:** 7 Opus adjudicators re-measured every finding, fixed the small ones and escalated the rest. Their verdicts are in `adjudicated/C1..C7.md`.
- **Phase 3:** the coordinator integrated the work and ran the gate.

The method is in `README.md`.

| | fixed | escalated | rejected | handed off |
|---|---|---|---|---|
| C1 stairs & guards | 5 | 4 | 4 | 4 |
| C2 openings | 5 | 24 (12 groups) | 6 | 15 |
| C3 structure | 13 | 23 | 4 | 28 |
| C4 envelope | 4 | 5 | 5 | 5 |
| C5 interiors | 7 | 12 (10 groups) | 6 | 14 |
| C6 MEP | 8 | 17 (11 groups) | 8 | 7 |
| C7 set & viewer | 42 + 4 partial | ~40 (11 groups) | 5 | 6 |

Handoffs mostly converged on C7; the few left open are listed at the end. No finding was a
true build-blocker at the reviewers' measured confidence. The gate result:

- **`haus check`:** the FAIL list is identical to the baseline. The only FAILs are the two `code.R311_7_1_stair_width` lines on ST-S2A. UNKNOWNs went from 202 to 200, because two `advisory.trim_device_clash` findings cleared.
- **Permit set:** both sets regenerate with the same 63 and 158 sheets, numbered as before.
  They are written ungated to `houses/catlin/out/geometry-review-2026-10-31/after/`, beside
  the baseline set.
- **`scripts/verify.sh`:** the engine suite passes (10,210 passed) and so do the starter
  checks. The catlin strict check then stops the script on the two baseline FAILs, which were
  already red at `247a13e9`. The stages it skips were run by hand: ruff is clean, the UI
  typecheck is clean and `npm test` exits 0.
- **Not done:** the plan's headless screenshot of the window-bottom case. The fix is verified
  by probe (frames 3.66"/3.25", coplanar stool/rail overlaps 39 → 1) and by the viewer mirror,
  not by eye; `plans/TODO.md` keeps a line to confirm it in the viewer.

## 1. Escalations awaiting the owner

Ranked by construction-set impact, then build risk. "→" is the adjudicator's recommendation.
Full evidence, options and blast radius are in the cited `adjudicated/` file.

### Blocks the permit print or misprints what a trade builds from

**Status 2026-10-31 (later): items 1–7 are resolved** (each `adjudicated/` entry carries a
"Resolved" line). `haus print` passes the gate at 74 sheets (was 63: S-001.1, S-602.1, the five
plant-rim details, A-512.1/.2, A-513.1/.2). New checks: `integrity.header_under_plate`,
`integrity.transition_shadowed`, `electrical.panel_handle_height`. Follow-ups are in `plans/TODO.md`.

1. **ST-S2A guard posts stand 2.9" inside the 36" flight and on the head landing**
   (C1-E1: S1-001, S3-001/002, S1-002). This causes both baseline FAILs and keeps `haus print`
   shut. `code.R311_7_6_stair_head_landing` cannot see guard posts, so it reports a false PASS.
   → Surface-mount RL-A-STAIR on the deck (Williams 42" surface kit), base flush to the well edge.
   That clears both FAILs (36.00" / 32.55"); then teach the head-landing check to read posts.
   Alternatives: end the guard at the newel, or widen the flight (size L).
2. **Schedule sheets overprint** (C7-E1): S-602, S-601, S-101.x, S-100 and S-001. This is not
   the root cause that was fixed: schedule widths are reserved in model inches but print at the
   minimum font, about 3× wider. → Continuation sheets, which add and renumber sheets.
3. **Plan dimension strings** (C7-E2: D1-001..004). Interior chains run to the near stud face
   and no sheet states the reference. Every string rounds to whole inches, so the A-104 chain
   sums to 36'-1" under a 36'-0" overall. The S-100/S-101 "overall" strings measure bearing
   axes only, and there are no locating strings on the framing plans.
   → Pick and state one convention (face of stud), print to 1/8", and add locating strings.
4. **Detail sheets carry no dimensions or enlarged parts** (C7-E4): A-501..A-511, the A-512
   head and sill, and A-507 has no tub, valve or tile. → A dimension pass on the authored
   details, plus enlarged head/sill details.
5. **The plant-room vapour-barrier rim detail never derives** (C5-E10, new). Transitions
   match first-wins and `TR-CATLIN-RIM-BAND` precedes `TR-CATLIN-PLANT-RIM`, so all 5
   `*PLANT_*` rim keys print the generic band. About 20 interior rim/stack details also inherit
   envelope continuity data. The drawing side is fixed; the data is not. → Reorder the
   transitions and add interior transitions without continuity. The set gains up to 5 sheets.
6. **Headers run into the top plates**: D-G-SERVICE by 2" (C3-E1) and D-B-PATIO by 4⅝" on a
   bearing wall (C3-E2). → Re-seat each header under the plates. This moves the RO or plate
   height, which is an owner call.
7. **Service panels sit 60–96" AFF**, so the top breaker handle is about 90" against
   NEC 240.24(A)'s 79" (C6-E8: M3-002, plus M3-006 for raceways through the working space).
   Nothing grades it. → Lower the panels and re-run about 10 conduit starts. Add a check.

### Structural fit (needs a design or engineering decision)

8. **The garage sill bears 3⅝" of its 5½" on the ICF core**, with 1⅞" over EPS (C3-E8: F5-001).
   This conflicts with the recorded "coplanar outside" decision.
9. **The RF-HOUSE birdsmouth cuts 1.47" plumb into the TJI 230 bottom flange** (C3-E5: F4-001).
   → Read Weyerhaeuser TJ-4000 / TB-805, or switch to a beveled bearing plate.
10. **HU28-2Z (a double-2x8 seat, 3⅛") hangs a single 2x8** on BM-BW-SCSILL (C3-E11: F6-001).
    → LUS28Z.
11. **Frost wings are credited from 32" away** (C3-E10: F5-002). `structural.frost_depth`
    shields on distance alone, so FT-B-S1..S4 are 8" below the court floor. Needs an engineer.
12. **Canopy trusses bear 2¾" on 5½" glulams**, the heel lift treats the chord as plumb, and the
    north-entry seat-beam hangers sit 1.1" below their posts with the shim pack modelled at no
    height (C3-E6, E7, E12–E14).
13. **The floor-to-floor stack does not close** (C3-E3: F3-001). Sole plates start inside the
    3/4" subfloor; a real stack is 120.625" per storey against the modelled 120". This is a
    recorded split, not a bug. → Start walls on the subfloor and cut studs to 102⅞", keeping
    the storey datums.

### Fit and product data that change what is built

14. **BBD75 band**: the lower panel top sits 7.5" past its last girt with nothing to screw to,
    and the lap check reads the trim leg (2½") rather than the true 1.5" (C4: E2-001).
    → Lower the band girt course. An honest lap check would add a FAIL until then.
15. **The B&B window head trim is the PBR part** (coordinator, O5-005). Metal Sales' BBD75
    guide (10/2025 p.16) publishes its own board-and-batten **Head Trim 58720XX** and Window
    Closure 55539XX, but every B&B window uses PBR's 58114XX. → Swap the B&B heads to 58720XX
    and re-check the K6 cap lap against its 2½"/1⅛" profile.
16. **3" stacks in 2x4 walls**: W-M-STOS and W-S-DC2 stud-005 (C6-E5/E6, = F2-004/005). The
    bore checks ignore pipe insulation (C6-E3, which would add 2 FAIL) and treat exterior walls
    as non-bearing (C6-E4, which would add 3 FAIL on W-A-HALL-S).
17. **Ducts**: the ERV start points aren't on the Broan B210E75RT collars (C6-E1). 39 of 156
    round legs are shorter than the elbows at their ends need (C6-E2). Both need a re-route.
18. **Trap arms** are measured as plan distance, and vents aren't connected in 3D (C6-E7).
19. **PLAY-N sconces cannot cover a RACO 232 surface box** (C6-E10; confirms the TODO). The TV
    also sits over two surface boxes (C6-E11).
20. **Window reveal**: the buck-lined interior reveal of an outie window (2.3–2.75") has no
    specified finish (C2-E1). → A derived jamb-extension board. The Drutex sill rail may be
    125 mm against the 2.953" stool rule, pending the DAKAM drawing (C2-E10).
21. **ST-G-SERVICE top riser**: it ends at the deck, not at the MMI threshold above it, giving
    about 7.8–8.3" against 7.75" (C1-E2 = C2-E9). The fix needs MMI's sill height, which is
    unpublished.
22. **Kitchen**: the fridge columns have 1/8" behind them against Frigidaire's 1" (C5-E2). The
    north-run 1.319" build-up under the stone is unspecified (C5-E1). The stone is 1/4" past
    the fronts, not 1"; changing it breaks pinned fabrication tests (C5-E3).
23. **Floors**: the carpet stack is modelled at 0.75" but its published parts add to ≥ 1.0",
    which moves the bedroom thresholds (C5-E5). No transition product exists at 58 doorways
    (C5-E6).
24. **Smaller product and data items**:
    - Interiors: the Swanstone surround is 96" but modelled at 106" (C5-E4). One J-bead serves
      two board thicknesses (C5-E7). The sauna base runs behind the benches (C5-E8).
      `clear_height_m` ignores dropped ceilings (C5-E9).
    - Doors and trim (C2-E2..E8): MDF casing is 11/16" against the modelled 3/4". Bypass ROs
      use the swing equation. Jamb depths are unspecified for 7 doors. The mudroom base stands
      proud of its casing. The Murphy RO datum is unconfirmed. Exterior door frames are
      anchored to the studs.
    - Roof (C4 E1-002/007/008/009): Metal Sales has a part-numbered vented ridge for the
      garage. 4" round leaders are not a Metal Sales part. Ridge end caps are unbilled. The
      garage and canopy seams are out of register.
    - Structure and viewer (C3 E4/E9/E15–E23, C7 E3/E5–E11): see their files.

## 2. Fixes applied

Every fix carries a cited real dimension and a probe-measured before and after; the full rows
are in each `adjudicated/C*.md`.

| cluster | fix | effect |
|---|---|---|
| C2 | **O4-001** Window frame drawn at `WindowType.frame_depth`, not to the pan dam (`geometry_openings.py`; `WindowSeat.frame_depth_m` served) | Frames 5.44" → 3.66" / 3.25". Stool/rail coplanar overlaps 39 → 1. This is the TODO's glitchy window bottoms |
| C7 | Viewer mirror of `window_seat.frame_depth_m` (`openings.ts`); floor-truss blocking drawn as boxes (U1-003) | The viewer matches the engine |
| C2 | O4-002 Returns stop at the sheathing face | Return area 171.9 → 158.0 sf |
| C2 | O1-001 Sole plate cut across the whole pocket cavity | Leaf bottoms no longer sit over a 1.5" plate; 9.6 LF of plate removed |
| C2 | O2-005 No floating casing head when both legs drop; O4-007 note | — |
| C3 | **F2-001/002** Backing advisory reads the absolute body bottom; BK-G-S-EVSE re-authored | The EVSE band moves 29.5–40.75" → 7.5–18.75" and now covers the EVSE |
| C3 | F1-003 Plates over 20 ft bought spliced | S-601 loses its 36/28/24/22 ft sticks; 2,374 LF unchanged |
| C3 | F3-003 Main deck seats on the mudsill above concrete | Rim moves 1/2" to the framed wall face; seat 6¾" → 4¼" |
| C3 | F3-006 / F6-005 I-joist ends bill IUS, trusses THA422, FS-BW-FLOOR LUS28Z | Correct hanger families |
| C3 | F2-012, F6-007/008, F5-009, F2-010, F3-011, F4-010 | Profile name, source and quantity text |
| C4 | **E1-001** Roof-edge pieces store slope length, not plan length | Rake 52126XX 16 → 20 ea; cleats 16 → 20, 40 → 44; fascia, soffit and closure LF up |
| C4 | E1-005, E2-007, E2-008 | Note and citation text |
| C5 | I3-002 Sauna exhaust hatch rotation; I3-005 PAX corner height; I1-007 Broan hood size; I1-005 DW face flush; I1-008 AXSTAD articles; I3-004 sauna headroom 83 1/16" | Each corrected to the cited product sheet |
| C6 | **M3-003** Conduit and sleeve solids at true OD (e.g. 3/4" EMT 0.75 → 0.922") | Overlap golden re-blessed |
| C6 | I2-008 Carlyle II at TOTO's 16½ × 28 5/16 × 28¾ (flange held); I2-001 powder-room receptacle moved off the mirror wall; M3-004 attic switch/AP clear the casing; M1-005 grille face; M1-007, I2-010 | — |
| C7 | **D2-001** Paper-space card text no longer printed in model space (`sheet_writer.py`) | Clears the pile-ups on A-512, A-515, A-554, A-570, A-586..589 and ~20 more |
| C7 | **D2-002** `{glob}`-scoped sheet notes (`sheet_notes.py`); eave and foundation notes scoped | A-591 no longer prints the basement wall, #5@41" and veneer; slab reads 4,000 psi on 2" XPS |
| C7 | A-301: T.O. PLATE is the real plate (main 10'-0" → 9'-0", second 20'-1" → 19'-0"); bubbles only where cut; CLG overprint | — |
| C7 | A-592 now draws; A-105 drops false overhangs; truss length 24'-0" → 26'-8"; fractions ("3 5/8"" not "3.62"); gwb types; A-514 24 ga; ICF "2 1/2" EPS" | — |
| C7 | A-601 pocket kit RO 74.5", 1/8" ROs; A-602 "Rough opening"; A-603 Base/Walls filled and ceiling board, not paint | — |
| C7 | P-10x pipe sizes as fractions (1/2" no longer "0""); slope from horizontal grade (4.79 → 0.26"/ft); round ducts "4" RD"; E-602/E-603 layout; E-601 area 4,479 → 4,900 sf (service load 271.4 → 273.5 A, PASS) | — |
| C1 | `floor_heights.md` deck datum, porch-stair x, handrail and rail citations | Text only |
| coord. | `prices.toml` IUS allowance; TP-holder test follows the corrected Carlyle depth; pocket docstring; sauna headroom and SF-S-DUCT figures in `houses/catlin/CLAUDE.md` | — |

Goldens re-blessed after reading the diffs:
- `catlin_elevations.json`: pocket plates, casing, hangers, hood, receptacle, PAX, WC, conduit OD.
- 99 of 100 catlin section scenes plus the starter slice: mostly fractions, returns, A-301 labels.
- `solids3d_overlaps.json`: conduit at true OD.

## 3. Rejected (38)

| reason | count | e.g. |
|---|---|---|
| A deliberate, recorded decision or convention | 12 | S1-004, O3-002, O4-008, E1-003, E2-009, I1-005, I3-008, D2-005, F1-004 |
| The reviewer mis-measured or misread the engine | 11 | O5-001, S3-007, E1-004, M3-005, M3-010, F1-011 (the coordinator's approximate R602.7.5 table was wrong; the engine was right) |
| Within tolerance or normal site practice | 7 | S3-005, O2-011, E2-002, E2-006, S2-004 |
| Not a defect, no authoritative data, or covered elsewhere | 8 | F1-005/006, I3-006, I4-008, M3-009, M2-008, I1-004 (the sink hold) |

## 4. Emitter mismatches (deferred)

None was recorded. The viewer-side twin (`openings.ts` duplicating `_opening_parts`) is C7-E9.

## Open handoffs

Each of these needs an authoring or design decision, so none is fixed:
- **C-101 "STAIR AREA 27 SF"** is an authored `ImperviousSurface` outline; re-trace it to the
  tier 1 and porch pad footprints (S2-005).
- **A-528 K2** is a window keynote printed on the door detail; scope it once the opening is
  confirmed (O1-008).
- **D-G-SERVICE header plies**: 2-ply in the note against 3-ply in `CLAUDE.md` (O3-010).
- **A fireblocking (R302.11) general note** (F2-009).
- **The ST-M2S skirt blank** needs 10' stock (O2-010).
- **The backing bands split around stack bays** after C6-E5 (F2-003).

# The analytical model — boundary conditions and load cases, as claims

**House:** catlin
**Structure:** the engineered items and their load path — the balcony's four moment
columns (PT-SG-BF1/BF3, PT-SG-BR1/BR3), the two pinned pillars between them (PT-SG-BF2,
PT-SG-BR2), the sunken-garden columns PT-SG-COL/FCOL, the breezeway posts PT-BW-*, and
the beams they carry.
**Written:** 2026-09-12, by hand, before `typehaus/analytical/` was oracled against it.
**Oracle for:** `analytical/supports.py`, `analytical/loads.py`, `analytical/solve.py`;
reproduced by `tests/test_analytical_oracle.py`.
**Companions:** `balcony_moment_columns.md` — the column *capacity* and the wind arithmetic
this note re-uses; `north_entry_piers.md` — the breezeway piers' tributaries.
**What is asked of the reviewer:** §1 and §2 are *claims*, not arithmetic. Agree or reject
each fixity and each load case; §3's arithmetic is only there to show the exported model
solves to the numbers the calc sheets already carry.

> ⚠ An analytical model is not a calculation, but its boundary conditions and load cases
> ARE structural claims. This note is where they are stated so that a person can disagree
> with them. A PE who models the balcony columns pinned will get a different building.

---

## 1. Boundary conditions — what is claimed and why

| Support | Claim | Basis |
|---|---|---|
| PT-SG-BF1, BF3, BR1, BR3 (12" round cast) | **FIXED** — six DOF | They are the balcony's lateral system: no knee brace, no beam landing in a wall since 2026-09-03 (`balcony_moment_columns.md` §0). `deck_post` grades their base moment on exactly this fact (`_Pier.lateral_system`); a model that pinned them would have no lateral system at all. |
| PT-BW-E/W/GE/GW/RE/RNE (breezeway cast columns) | **FIXED** | Same rule, same derivation: `_base_moments` finds a storey shear for them and no brace or wall to take it. |
| PT-SG-BF2, BR2, COL, FCOL and every wood post on a base | **PINNED** — translations, plus twist about the post's own axis and roll about the plan axis of the beam it carries | A post base connector transfers shear and uplift and no moment; in-plane bending stays free, which is what makes it a pin. The twist and roll restraints stand in for the deck plane, which braces these columns and is carried in the graph as a line load rather than as members. Stated in the model's `assumptions`; the reaction moment about the braced axis comes back ~0 under gravity, which is the check on the claim. |
| A beam end on a wall (BM-SG-BK*, FR* on W-SG-E1/W1) or on a beam seat | **PINNED** for bending, **held against roll** about the beam's axis | The beam sits on a plate; it can rotate in bending and cannot roll. Without the roll restraint a moment-released beam between two pins is a mechanism. |
| A beam bearing on a post top | end released for bending | The beam bears on the post; the post top node sits ON the beam centreline (rigid-link convention, half a depth of eccentricity not modelled). |

## 2. Load cases — what each carries, and where the number comes from

| Case | Content | Source |
|---|---|---|
| `dead` | deck dead 10 psf as a line load on each deck beam over the deck's joist span; roof beams' `design_dead` share of `uniform_load` | `engineering/pier_basis.DECK_DEAD_LOAD_PSF`; `roof_beam` record inputs |
| `live` | IRC Table R301.5 deck live 40 psf, likewise | `pier_basis` |
| `snow` | roof beams' `design_snow` share of `uniform_load` | `roof_beam` record inputs |
| `wind` | each fixed column's ASD storey shear at the deck plane, so that V × h = the record's ASD wind base moment | `_Pier.wind_base_moment_lb_ft`, `balcony_moment_columns.md` §2b |
| `guard` | IRC R301.5 200 lb at the top of the guard, as a nodal force + moment at the column top | `_Pier.guard_base_moment_lb_ft`, §2c |

**Self weight is not a load in the graph.** It carries a section and a modulus, not a
density; a solver's dead reaction is therefore the deck's dead load without the column's own
150 pcf, and `pier_basis`'s `dead_load` includes it. §3 puts it back by hand.

## 3. Hand checks the solve must reproduce

### 3a. Balcony wind — the number the whole lateral system rests on

From `balcony_moment_columns.md` §2b, unchanged:

| term | working | value |
|---|---|---|
| ASD storey shear, E-W | 0.6 × 18.6 × 0.85 × 1.80 × 35.94 | 614 lb |
| per column | 614 / 4 | 153.4 lb |
| lever, front row | column height | 9.03' |
| base moment M_w | 153.4 × 9.03 | **1,385 lb-ft** (BF1, BF3) |
| rear row (2" higher) | 153.4 × 9.19 | **1,410 lb-ft** (BR1, BR3) |

The graph applies 153.4 lb at each column top in the `wind` case. With the base fixed
and the column top free to rotate, each column is a cantilever and the solver's base
moment is V × h. **Finding (2026-09-12):** the record's lever h is the AUTHORED post
height (9.01' front, 9.18' rear); the model's column runs from its base to the beam
centreline, and the resolver shortens the built post to the beam's underside, so the
model's lever is 8.92' / 9.08' — 1.0–1.1 % shorter. The solve gives 1,380 / 1,386 lb-ft
against 1,385 / 1,410. The record errs long, i.e. conservative, by that 1 %. Tolerance in
the test: 3 %, and this paragraph is why.

### 3b. Balcony guard

200 lb × (9.01' + 3.5' guard) = **2,502 lb-ft** at a front column, 2,535 lb-ft at a rear
one (§2c). Applied as its nodal equivalent at the column top: 200 lb horizontal plus
200 × 3.5 = 700 lb-ft. Base moment = 200 × 9.01 + 700 = 2,502. Tolerance 3 %, for the
same lever reason as §3a (the solve gives 2,496 / 2,504).

### 3c. Balcony gravity — one column, by statics

`BM-SG-BLW` carries the deck's full 10.0' joist span as a line load (the `pier_basis`
rule: each beam takes the whole span, conservatively double-counting the overlap):

| term | working | value |
|---|---|---|
| live line load | 40 psf × 10.0' | 400 plf = 5,838 N/m |
| beam span between BF1 and BF2 | | 2.947 m (9.67') |
| reaction at BF1, simple span | 400 × 9.67 / 2 | **1,934 lb** vs record `live_load` 1,933 |
| dead line load | 10 psf × 10.0' | 100 plf |
| deck dead at BF1 | 100 × 9.67 / 2 | 483 lb |
| column self weight | 0.785 ft² × 9.03' × 150 pcf | 1,062 lb |
| dead total | 483 + 1,062 | **1,545 lb** vs record `dead_load` 1,545 |

**Finding (2026-09-12):** `pier_basis` splits the beam's load by simple-span statics,
1,933 lb to each column. The graph carries the beam as it is built — continuous over both
columns, 0.20 m of cantilever at the front and 0.51 m at the rear — and the frame solve
hands the rear column **2,135 lb** live and the front **1,733 lb** (± 10 % against the
record's equal split); dead likewise 1,615 / 1,495 against 1,564 / 1,545. The pair sums
agree with the records to 0.03 % (3,868 vs 3,867 live; 3,110 vs 3,109 dead), so the total
is right and the *distribution* is what the calc sheet does not see. At d/c 0.04 axial
this changes no verdict; on a heavier deck it would, and it is the reason a solve is worth
running beside the sheet. The test asserts each pair sum within 1 % and each column within
15 %.

### 3d. Roof beams

`roof_beam/BM-BW-RE` and `BM-BW-RW`: `uniform_load` 1,170.9 plf, split by the record's own
`design_dead` 10 psf / `design_snow` 73.7 psf into 0.119 dead / 0.881 snow. The test asserts
the graph's dead + snow line loads on each beam sum to `uniform_load` exactly.

## 4. What is NOT modelled, positively

- Retaining walls and the retaining system (`retaining_wall/*`, `retaining_system/W-SG-ARCH`)
  and the board-and-batten panel item are not in the graph. Their oracle is
  `sunken_garden_court_free_body.md`, a free body a surface model would not check better.
- The trussed roofs and the uplift path (`rafter/*`, which carries the uplift reactions
  too since 2026-09-14, and `column_support/*`)
  resolve to no curve member; the gaps say so by item id.
- **The canopy roof's tributary on PT-BW-E/W/GE/GW** reaches those piers through framing the
  graph carries only as BM-BW-RE/RW, so a solve there under-runs the record's `dead_load`
  by that share (7.7–47.7 ft²). And the breezeway's two seat beams run CONTINUOUS over
  four fixed columns and two pinned posts, so the storey shear applied at each column top
  redistributes through the beams instead of staying on its own column: `haus analysis
  --solve` prints ~340 lb-ft at PT-BW-E against the record's 595 (which took the shear
  split equally and each column as an independent cantilever). The breezeway frame is
  MODELLED — its fixity claims stand in §1 — but nothing on it is asserted by the test; the
  balcony bent, where the beam is one span between two columns, is the oracle.
- Self weight (above). Second-order effects: `deck_post` magnifies the moment itself
  (ACI 318-19 §6.6.4); the linear solve does not, and does not claim to.
- Moduli are assumed where no record carries an adjusted E (SPF No.2 1.4e6 psi, ACI
  57000√f'c). They move deflections, not the reactions this note checks.

## Sources

- ASCE 7-16 §29.3 — wind on other structures; `balcony_moment_columns.md` §2b for the terms
- IRC 2024 (MN 2024) Table R301.5 and note f — 40 psf deck live, 200 lb guard load
- ACI 318-19 §6.6.4 (magnification, done in `deck_post`), §19.2.2.1 (E_c)
- AWC NDS 2018 Supplement Table 4A — SPF No.2 E, the assumed framing modulus
- CSI, *IFC4 Import and Export* Technical Note (Oct 2013) — the entities SAP2000/ETABS read
- RISA-3D help, *DXF Files* — LINE → member, POINT → node, layer → section set

# Wall headers against IRC 2018 Table R602.7 — hand-worked oracle

Oracle for `structural.header_span` and the solver's header choice
(`resolve/framing/header_tables.py`, `resolve/header_loads.py`,
`resolve/framing/header_choice.py`; decision #116). Worked by hand from the plan source and the
printed table, 2026-11-06. `tests/test_header_spans.py` pins these numbers.

## Basis

- **Table:** IRC 2018 R602.7(1) (exterior bearing walls) and R602.7(2) (interior bearing walls),
  as adopted by Minnesota (UpCodes). The 2021 tables are identical cell for cell; the 2015
  edition is not (its widths are 20/28/36' and its spans longer). Sources in the
  `header_tables.py` docstring.
- **Site:** ground snow 50 psf (`project.site.ground_snow_load_psf`) → the 50 psf column.
- **Building width:** `RF-HOUSE` bears on `W-A-E1`/`-E2` (x = 432") and `W-A-W1`/`-W1B` (x = 0);
  the ridge runs y, so the width is 432" = 36'-0" → the 36' column (note c; no interpolation,
  the next column that covers).
- **Note f (R602.7(2): note e):** a header whose top carries cripple studs is not laterally
  braced, and a 2x8/2x10/2x12 span is multiplied by 0.70. Every catlin bearing header sits
  13–18" under its plates, so every one carries cripples. A 2-2x6 is not named by the note
  and keeps its printed span — which is why the house's 2-2x8 minimum can need more than the
  code minimum does.
- **Clear span:** between the trimmers, i.e. the RO (a pocket's 2W + 1").
- **A floor's bearing ref is a LINE** (2026-11-06 review): the floor framing cuts its joists at
  the named wall's line coordinate across the whole deck, so a floor loads every wall of that
  storey on the line, named or not. `FS-ATTIC` names only `W-S-E2` on the east line, and its
  joists still land on `W-S-E1` and `W-S-E3` (checked against the resolved joist ends,
  x = 429.8").
- **A floor opening is not a load across its hole:** on a wall across its floor's joists it
  bears only where its trimmers land, at its outline's corners. A stair still counts along
  its whole width.
- **`HeaderStandard.min_bearing_header = "2-2x8"`** removes the 2-2x4 and 2-2x6 candidates.

## 1. WIN-M-LIV-E1 — `W-M-E1`, exterior, BEARING

- RO 27.5", head 82.281" above the main datum; plate underside 105.125" (108 1/8" plate top less
  the double plate). A 2-2x8 leaves 105.125 − 82.281 − 7.25 = 15.59" → head cripples → note f.
- Load: `FS-S-EAST` names `W-M-E1` directly; its bearing refs also name `W-M-C2` (interior) and
  `BM-M-HALL`, so it is a **center-bearing** floor. Above the span, `W-S-E1` stands on the line
  and `W-A-E1` above it carries `RF-HOUSE`. `FS-ATTIC` (center-bearing on `W-S-C1`) lands on
  `W-S-E1` at y 0..67" — the line rule above; `FO-A-STAIR`'s trimmers stand at y 66.3..69.6",
  past the span's 61.75" — so this is **two center-bearing floors**.
- Row: **"Roof, ceiling and two center-bearing floors"**, 50 psf, 36': 2-2x8 = 3'-3" = 39" ×
  0.70 = 27.3" < 27.5" (short by 0.2"), so the solver takes **2-2x10**: 3'-10" = 46" × 0.70 =
  **32.2"** ≥ 27.5" → PASS (27.5 / 32.2 = 0.85), **NJ 3**. A 2-2x10 still leaves 105.125 −
  82.281 − 9.25 = 13.6" of cripples, so note f stands.
- WIN-M-LIV-E2 (under `W-S-E2`) reads the same: 2-2x10, NJ 3. So do the west main windows
  `WIN-M-BED-W1`/`-W2` and `WIN-M-BATH2` (`FS-S-WEST` and `FS-ATTIC` on the x = 0 line).

## 2. WIN-S-BED1 — `W-S-E2`, exterior, BEARING

- RO 27.5", head 204.0", plate underside 225.125": a 2-2x8 leaves 13.9" → cripples → note f.
- Load: `FS-ATTIC` names `W-S-E2` (and `W-S-C1`, interior → center-bearing); `W-A-E2` above
  carries `RF-HOUSE`. One floor.
- Row: "Roof, ceiling and one center-bearing floor", 50 psf, 36': 2-2x8 45" × 0.70 = **31.5"**
  ≥ 27.5", **NJ 2** → PASS, 0.87.

## 3. D-B-SAUNA — `W-B-CS`, interior, BEARING → no row (UNKNOWN)

- RO 26.24". Load: `FS-M-WEST` and `FS-M-EAST` both name `W-B-CS` — two half-decks, **one**
  floor level (center-bearing). Above: `W-M-C1` (on the x = 18' line `FS-S-WEST`/`-EAST` bear
  on, the second floor) → `W-S-C1` (named by `FS-ATTIC`, a third) → `W-A-C1`, which carries
  `RB-HOUSE`, `RF-HOUSE`'s ridge beam. So the span carries the roof and three floors, and is
  interior.
- R602.7 stops at two floors, R602.7(2) has no roof row, and R602.7(1) is for exterior walls.
  **No row.** The span-ladder 2-2x8 is drawn as a placeholder and `structural.header_span` is
  UNKNOWN until a manufacturer's header-guide row (`header_spec` + `published_span`), a door
  move or an engineered item answers it. The same holds for every door in the x = 18' centre
  stack (`D-B-GYM`, `D-M-BED2`, `D-M-STUDY`, `D-S-PLANT`, `D-S-SUITE`, `D-A-HALVES`).

## 4. D-M-LAUN — `W-M-HS3`, interior pocket, BEARING → no row (UNKNOWN)

- `W-M-HS3` was UNKNOWN. Above it, `W-S-SN3` is named in `FO-A-HALL`'s bearing refs, and
  `FO-A-HALL`'s outline (x 120..216") projects onto the door's span, so the wall is BEARING
  (authored so) and the hall opening is a **point load inside the span** → no row.
- The span is the pocket's full framed extent: RO 36" + cavity 38.5" = **74.5"**
  (x 110..184.5"; the resolved header is 77.5", x 108.5..186, on one jack each end).
- Even read as a uniform one-floor load at 36' it has no 2-ply answer: R602.7(2) "One floor
  only" 2-2x12 = 6'-3" = 75" braced, but it carries head cripples, so 75 × 0.70 = 52.5"; a
  3-ply does not fit a 2x4 wall. The ladder's 2-2x12 is drawn as a placeholder.

### 4a. What actually bears on it (2026-11-06, owner asked for an LVL guide row)

Read off the resolved model, not the walk's labels. Neither floor frames onto this line:
`FS-S-WEST`'s trusses (y = 256", 272") and `FS-ATTIC`'s joists both run in x, parallel to it.

- **The `FO-A-HALL` trimmer is a LINE load, not a point.** Its 2-ply 1 3/4 x 11 7/8 LVL pair
  (centres y = 267.75"/269.5", x 120..216") sits on `W-S-SN3`'s plate (both at 228 1/8"),
  i.e. continuously over x 120..184.5" of the span. The walk calls it a point only because
  every `FloorOpening` load is.
- **The real point is `BM-S-BATH-E`'s south end**, hung on that trimmer's west end at
  x = 120" (`attic_studio.py`). The trimmer's own bearing there is `W-S-SN3`, so the
  reaction comes straight down `W-S-SN3` onto this header **10" inside its clear span**
  (west jack face at x = 110"). The beam's comment says it "rides that joist to wherever IT
  bears" — it does, and where the joist bears is this wall.
  - `BM-S-BATH-E`: 51.5" span (y 268..319.5"), `FS-ATTIC` joist ends cut at x = 120"
    (bearing x ≈ 2..120", ~4.9' tributary), R301.5 habitable attic 30 psf + 12 psf dead,
    `W-A-BA-E` ~5' × 8.4 psf = 42 plf, 3 plies × 6.0 = 18 plf:
    w = 42 × 4.9 + 42 + 18 = 266 plf × 4.29' = 1,141 lb → **P ≈ 570 lb** (680 lb at 40 psf).
- **Uniform**, per foot of span: trimmer strip (30+12) × 0.67' = 28; `W-A-HALL-S` on the
  trimmer, ≤ 7.7' × 8.4 psf = 65; `W-S-SN3` 9.0' × 10 psf = 90; the `FS-S-WEST` subfloor
  strip (40+12) × 0.67' = 35; cripples and board over the header ~10; a 2-ply 9 1/2" LVL
  9.6 → **w ≈ 240 plf** (taken over the full 74.5").
  (ASCE 7-16 Table C3.1-1a: 2x4 studs 4 psf, 1/2" gypsum 2.2 psf a face.)

### 4b. The published rows, and why none closes it

- **Uniform part — a row exists.** Boise Cascade EWP, *VERSA-LAM 1.7 2650 Eastern Header
  Guide*, VL 1.7 2650 06/2009 r 07/21/11, p.4, "3½" VERSA-LAM 1.7 2650 Header Look Up
  Tables", **Door and Window Headers, Floor - 1 Story, Floor Load: 40 PSF Live, 12 PSF Dead,
  Flush Joists, Structure Width 24'-0", Clear Span 6'-8" → 7"** (6'-2" is 0.5" short of
  74.5"). The row's floor term alone is 52 × 12' = 624 plf (an interior bearing takes half
  the width whatever its position) against ~240 plf here, 39%. A 2-ply 1 3/4 x 9 1/2"
  substitute ("Double 1¾" VERSA-LAM 1.7 2650 may be substituted") is the `WIN-M-DINING-E`
  member.
- **The point is outside every row read.** The same page: "Tables based upon uniform
  loading applications shown in tables only". p.3 (holes, note 8): "For beams supporting
  concentrated loads ... contact Boise Cascade EWP Engineering." Weyerhaeuser *TJ-9000*
  (May 2015) is the same: p.12 "Table is based on: – Uniform loads", p.16 "Uniform loads
  (beam weight considered)", p.5 "For applications not covered in this brochure, contact
  your Weyerhaeuser representative". LP's LVL guides tabulate uniform loads only as well.
  No maker found publishes a header row for a concentrated load in the span.
- So **no `published_span` is authored**, and `structural.header_span` stays UNKNOWN.
  Quoting the uniform row over a point it excludes would be a PASS off a row that does not
  describe this header.

### 4c. Hand check — engineering, NOT a table read

Clear span L = 74.5", P = 570 lb at a = 10", b = 64.5"; w = 240 plf:

    M  <= w L^2/8 + P a b / L = 240 x 6.21^2 / 8 + 570 x 10 x 64.5 / 74.5 / 12
       =  1,156 + 411 = 1,567 lb-ft
    V  =  240 x 6.21 / 2 + 570 x 64.5 / 74.5 = 745 + 494 = 1,239 lb   (west end)

against the 6'-8" row's own load (624 plf over 80"): 3,467 lb-ft and 2,080 lb, so 45% and
60%. Deflection: 5wL^4/384 + P a (L^2 - a^2)^1.5 / (9√3 L) (a the short side)
= (8.0 + 2.0)E6 / EI against the row's 27.7E6 / EI, 36%. Against the 2-ply 1 3/4 x 9 1/2"
VERSA-LAM itself (p.3: 2 x 5,966 lb-ft, 2 x 3,159 lb allowable) that is 13% and 20%. The
member is not in doubt; the *read* is. Closing it takes one of:

1. **An engineered item** — the maker's sizing software (BC Calc / ForteWEB) or a PE, with
   this load set (`header/D-M-LAUN`, ENGINEERED authority).
2. **Move the door ~12" east** so the west jamb pack (x ≈ 119..122") stands under the
   hanger at x = 120". The point then lands on the jack and the uniform row above closes it
   prescriptively. The sink centre (x = 145.6") stays inside a 122..158" opening, but the
   east jamb would meet `W-M-LS` (axis x = 161") at the doorway — an owner layout call.
3. **A swing door does not help by itself**: a 36" leaf's ~38" RO from x = 110" still has
   the hanger 10" inside it.

## Cross-checks of the table read (not catlin openings)

- R602.7(1) "Roof and ceiling", 50 psf, 36': 2-2x8 = 4'-2" NJ 2 (50 × 0.70 = 35.0").
- R602.7(1) "Roof, ceiling and two center-bearing floors", 50 psf, 36': 2-2x8 = 3'-3" NJ 2.
- R602.7(2) "One floor only", 36': 2-2x8 = 4'-5" NJ 2; "Two floors", 36': 2-2x8 = 3'-1" NJ 2.
- 2015 R602.7(1), 50 psf, 36', one center-bearing floor: 2-2x8 = 4'-1"; 2018: 3'-9".

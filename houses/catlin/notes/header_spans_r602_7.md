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
- The span is the pocket's full framed extent: RO 36" + cavity 38.5" = **74.5"**.
- Even read as a uniform one-floor load at 36' it has no 2-ply answer: R602.7(2) "One floor
  only" 2-2x12 = 6'-3" = 75" braced, but it carries head cripples, so 75 × 0.70 = 52.5"; a
  3-ply does not fit a 2x4 wall. The ladder's 2-2x12 is drawn as a placeholder; **owner
  decision open** (an LVL header-guide row, or a swing door).

## Cross-checks of the table read (not catlin openings)

- R602.7(1) "Roof and ceiling", 50 psf, 36': 2-2x8 = 4'-2" NJ 2 (50 × 0.70 = 35.0").
- R602.7(1) "Roof, ceiling and two center-bearing floors", 50 psf, 36': 2-2x8 = 3'-3" NJ 2.
- R602.7(2) "One floor only", 36': 2-2x8 = 4'-5" NJ 2; "Two floors", 36': 2-2x8 = 3'-1" NJ 2.
- 2015 R602.7(1), 50 psf, 36', one center-bearing floor: 2-2x8 = 4'-1"; 2018: 3'-9".

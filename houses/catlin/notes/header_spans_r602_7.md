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

## 3. D-B-SAUNA — `W-B-CS`, interior, BEARING → past R602.7 (§5 reads it)

- RO 26.24". Load: `FS-M-WEST` and `FS-M-EAST` both name `W-B-CS` — two half-decks, **one**
  floor level (center-bearing). Above: `W-M-C1` (on the x = 18' line `FS-S-WEST`/`-EAST` bear
  on, the second floor) → `W-S-C1` (named by `FS-ATTIC`, a third) → `W-A-C1`, which carries
  `RB-HOUSE`, `RF-HOUSE`'s ridge beam. So the span carries the roof and three floors, and is
  interior.
- R602.7 stops at two floors, R602.7(2) has no roof row, and R602.7(1) is for exterior walls.
  **No row**, for this and every door in the x = 18' centre stack (`D-B-GYM`, `D-M-BED2`,
  `D-M-STUDY`, `D-S-PLANT`, `D-S-SUITE`, `D-A-HALVES`). §5 answers each off Boise's guide.

## 4. D-M-LAUN — `W-M-HS3`, interior pocket, BEARING → Boise's published row (PASS)

Re-worked by hand 2026-11-07, after the owner moved the door 11 1/2" east (the 2026-11-06 read,
when the hanger stood inside the span, is in git history at c47b14082).

### 4a. What bears on it

Neither floor frames onto this line: `FS-S-WEST`'s trusses and `FS-ATTIC`'s joists both run in
x, parallel to it. What comes down is `FO-A-HALL`'s south trimmer, a 2-ply 1 3/4 x 11 7/8 LVL
(y = 267.75"/269.5", x 120..216") lying on `W-S-SN3`'s plate over this wall:

- **Uniform**, per foot: trimmer strip (30+12) x 0.67' = 28; `W-A-HALL-S` on the trimmer,
  <= 7.7' x 8.4 psf = 65; `W-S-SN3` 9.0' x 10 psf = 90; `FS-S-WEST`'s subfloor strip
  (40+12) x 0.67' = 35; cripples and board over the header ~10; the header 6 → **w ≈ 234,
  taken as 240 plf** (ASCE 7-16 Table C3.1-1a: 2x4 studs 4 psf, 1/2" gypsum 2.2 psf a face).
- **The point** is `BM-S-BATH-E`'s south end, hung in the trimmer's west end at x = 120"
  (`attic_studio.py`): 51.5" span (y 268..319.5"), `FS-ATTIC` cut ends at x = 120" (~4.9'
  tributary), 30 psf live + 12 dead, `W-A-BA-E` ~42 plf, 3 plies 18 plf:
  w = 42 x 4.9 + 42 + 18 = 266 plf x 4.29' = 1,141 lb → **P ≈ 570 lb** (680 lb at 40 psf).
  The trimmer bears on `W-S-SN3` there, so P comes straight down onto this wall at x = 120".

### 4b. Where it lands now

RO x = 121 1/2"..157 1/2" (`from_node("N-M-D1", 23 1/2")`), cavity 38 1/2" to x = 196".
Strike end, from the model: king x 118 1/2..120", jack 120..121 1/2", header 120..197 1/2"
bearing on the jack. **The hanger's x = 120" is the king/jack seam: the pack is centred on
it** (and inside the 3-ply beam's 117 3/8..122 5/8" bearing above). P goes down the pack to
the floor; the header's clear span is 121 1/2..196", **L = 74.5" = 6.21'**, uniform only.

**Through the floor (decision 22, 2026-11-22).** `FS-S-WEST`'s trusses run in x at y = 256"/272",
parallel to this line, so nothing in the floor stood between `W-S-SN3`'s plate and this wall's top
plate. Two parts now do:

- **The point.** `P-S-SN3-SQUASH` (2026-11-07 review): a 4x4 block, 11 7/8" (top plate 108 1/8" to
  the 120" datum), at (120", 268 1/2"), clear of both chords (257 3/4" / 270 1/4"), 3" onto this
  wall's plate, centred on the king/jack seam. 570 / (3.5 x 3.5) = 47 psi on its end grain.
- **The uniform part (~240 plf).** `W-S-SN3` is a BEARING wall of continuous 2x6 studs
  (`INT_2X6_BRG_HALF`; it was staggered and "not bearing" until 2026-11-22, which contradicted
  `main.py` calling `W-M-HS3`/`HS4` BEARING for it). Under it, between the chords, lies a 1 1/4"
  LSL rim board on edge, full depth 11 7/8", x 131"..216" (`FS-S-WEST.reinforcements`, a
  `JoistReinforcement` sistered to the y=272 truss at y 269"..270 1/4"): TJ-8000 vertical load
  **5,400 plf** (`library/rim_boards.py`, ESR-1387 Table 4, 1 1/4" 1.3E) against **240 plf**, d/c
  **0.04**; 1.25" of it lies on the 3 1/2" plate. The squash block carries the line to x = 121 3/4",
  the strip from 131": the ladder's 16" module is met (121 3/4 -> 137 3/4). It starts at 131" so
  `ED-M-LAUNDRY-TRACK`'s bar (x = 128.4") keeps its 16" bay. It must go on TrimJoist's layout.
  `structural.stacked_line_ladder` PASSes: "carried by P-S-SN3-SQUASH, sister-0-0 (1.25x11.875 rim,
  TJ-8000 vertical 5,400 plf)". `W-S-SN2` (staggered, now authored NONBEARING) is off the ladder
  on an open-web deck: R502.4 asks parallel *bearing* partitions to be supported.

**R602.6 on the retyped wall.** A bearing 2x6 stud may be bored 40% = 2.20" (5/8" of stud left each
side). The widest bore through `W-S-SN3` is the 1 1/2" vents' 1.90" outside (`PR-S-SUITEBATH-VENT`,
`-LAV-VENT`, `-WC-VENT`): 0.86 of the limit, 1.80" of stud either side; nothing is 2" or larger.
`mep.run_through_stud` PASSes every one (`notes/framing_bore_limits.md` §2).

Pack in bearing on the bottom plate: (570 + header end 745) / (2 x 1.5 x 3.5) = 125 psi
against SPF Fc⊥ 425 psi — 0.29.

The engine reads the same: `resolve/header_loads.py` puts the trimmer's strip on this wall as
`FS-ATTIC` and routes `BM-S-BATH-E`'s hung end through the trimmer's bearing to x = 120",
outside the span (`tests/test_header_spans.py`).

### 4c. The rows

- **R602.7 still has none.** R602.7(2) "One floor only", 36': 2-2x12 = 6'-3" x 0.70 (cripples)
  = 52.5" < 74.5"; a 3-ply does not fit a 2x4 wall.
- **Boise Cascade EWP, *VERSA-LAM 1.7 2650 Header Guide* (Eastern), 06/2009 r 07/21/2011, p.4,
  "3½" VERSA-LAM 1.7 2650 Header Look Up Tables"** (read from the PDF 2026-11-07): Door and
  Window Headers, **Floor - 1 Story, 40 PSF Live, 12 PSF Dead, Flush Joists**. The 6'-8" row
  reads 7" at 24'-0", 28'-0" and 32'-0"; 6'-2" is 0.5" short of 74.5". **Authored at 32'-0"**,
  the widest column. **The house is 36' wide and p.4 publishes no 36' column**, so this is the
  32' row plus a load comparison (§4d), not a literal cell: at 36' the row's own load would be
  52 x 18 + 60 = 996 plf, still 4x this header's 240. The literal 36' read is p.9 "Floor
  Beams", 40+12 psf, 36'-0" structure width, 8'-0" clear span: **3½" x 9½"** (not red, so 2
  trimmer studs, 3" bearing) — a 2-ply 9 1/2" LVL on a doubled jack each end. Owner item
  (`plans/TODO.md`), the `WIN-M-DINING-E` precedent reads the 32' column the same way. Not bolded,
  so single trimmers. Page notes: L/360 live, L/240 total (or 5/16" total for 7" and smaller);
  interior wall 60 plf; "Tables based upon uniform loading applications shown in tables only";
  "Double 1¾" VERSA-LAM 1.7 2650 may be substituted". p.3 publishes no 1 3/4" ply below 9 1/2"
(7 1/4" is a 1 1/2" width), so the member is **2-ply 1 3/4 x 9 1/2 VERSA-LAM**, the
smallest 1 3/4" depth, the `WIN-M-DINING-E` idiom (corrected 2026-11-08 from a 7 1/4" ply).

### 4d. Hand check against the row's own load

Row load at 32': 52 x 16 = 832 + 60 = 892 plf over 6'-8" (6.67'): M = 892 x 6.67² / 8 =
4,956 lb-ft, V = 892 x 6.67 / 2 = 2,973 lb. This header, w = 240 plf over 6.21':

    M = 240 x 6.21^2 / 8 = 1,157 lb-ft   (0.23 of the row)
    V = 240 x 6.21 / 2   =   745 lb      (0.25)
    Δ ∝ w L^4: (240 / 892) x (6.21 / 6.67)^4 = 0.20 of the row's

All under the row; the read is the row and the conditions, not this arithmetic.
`structural.header_prescriptive` grades it (6.21' <= 6.67', PASS) and refuses it while a point
load bears inside the span. `structural.header_span` steps aside for a published row.

## 5. The x = 18' stack, the niche and WIN-S-STUDY3 (2026-11-08)

Boise guide as in §4c, read from the PDF. Every row is 50 psf snow (115%), 15 dead, the 32'
column (the widest; 36' is the same load comparison as §4), not bolded (single trimmers). The
header-type columns the guide publishes for a ridge line are a load comparison: the rows are
trusses on an exterior wall. Member: 2-ply 1 3/4 x 9 1/2, p.3's smallest 1 3/4" depth.

### 5a. The rows

Tributary at x = 18': roof 18' at 15 + 35 psf = 900 plf; floors 18' at 12 + 40 (attic 30 live).

| opening | clear | carries | plf | row (3'-2") | row plf |
|---|---|---|---|---|---|
| D-A-HALVES | 34.2" | ridge + ~60 partition | 960 | p.4 Roof Only: 3 1/2" | 1,250 |
| D-S-PLANT, -SUITE | 32.2", 34.2" | + FS-ATTIC 756, wall ~90 | 1,746 | p.5 Roof Only + 1 Floor (no mid support): 4 3/8" | 2,082 |
| D-M-BED2, -STUDY | 34.2", 32.2" | + FS-S 936, walls ~150 | 2,742 | p.6 Roof + 2 Floors (no mid support): 5 1/4" | 2,994 |
| AO-M-FIRE-NICHE | 34.0" | roof 445 + FS-S-EAST 463 + FS-ATTIC 374 + walls ~190 + ST-S2A | 1,472..1,872 | the same p.6 row | 2,994 |

Row loads: 65 x 18 + 80; + 52 x 16; + 52 x 32 + 160 (two walls). The 2,994 back-checks p.3's
3 1/2 x 5 1/4 (M 3,761 lb-ft <= 3,892; V 3,436 lb <= 3,491) at 3'-2". On BED2/STUDY the floor
term is 1,692 against the row's 1,664; the roof term (900 vs 1,170) covers it. The check grades
span against the row and the load basis, so these numbers are the `condition`, not an input.

**The ledger** (`AO-M-FIRE-NICHE`). `ST-S2A`'s winder box is carried on `W-S-E1` by anchored
rims (`landing-rim-winder*-5`, y 59..105") and on `W-S-SS2` by rims and a stringer ledger: a
strip along the wall, not a point (`resolve/header_loads.py`). The box is ~16 sf x 52 psf = 830
lb plus ~half the flight (30 sf x 52 psf / 2 = 780 lb), split between the two walls, so W-S-E1
sees about 225 plf, at most 400 plf over 48"; 1,872 plf in all, against the row's 2,994. A
stair whose stringers land ACROSS a wall stays a point load.

### 5b. D-B-SAUNA and D-B-GYM: a load table, not a header column

The header-type columns stop at Roof + 2 Floors; this stack carries three floors and 3,258 plf
passes that row's 2,994. So it reads the guide's **p.16 Floor Load Tables (100% Load
Duration)**, the Allowable Total Load in plf, which names no header type. Span is centre to
centre of supports, at the next tabulated span with no interpolation.
`checks/structural/published_line_load.py` reads `PublishedSpan.capacity_plf` against the
derived load; `header_prescriptive` supplies the load, jack count and centre-to-centre span.

Derived line load (`resolve/header_line_load.py`, `typehaus/loads.py`):

| source | D | L | S |
|---|---|---|---|
| roof, 18' at 15 D + 35 S | 270 | | 630 |
| three floors, 18' at 10 D + 40 L each | 540 | 2,160 | |
| walls above, 10 psf x (8.76 + 10 + 10)' | 288 | | |
| **total** | **1,098** | **2,160** | **630** |

D + L = **3,258 plf** governs (D + S 1,728; D + 0.75L + 0.75S 3,190). The floor table is 100%
duration, so the snow case is read conservatively as well. `main_floor_truss_basis.md` §5 reaches
3,205 with 12/15 dead and 30 psf attic live. The full D + L + S sum, 3,888, is not a load
combination.

| | clear | jacks, bearing | c-c | row | d/c |
|---|---|---|---|---|---|
| D-B-SAUNA | 26.24" | 2, 3" | 29.24" = 2.44' | 3 ft: 5,395 plf, min end bearing 2.1" | 0.60 |
| D-B-GYM | 36.0" | 2, 3" | 39" = 3.25' | 4 ft: 3,632 plf, min end bearing 1.9" | 0.90 |

Member: **5 1/4 x 7 VERSA-LAM** (p.3, p.16), 7" deep so its top stands where the old 2-2x8's did
and the ERV duct and condensate line over `D-B-GYM` keep their crossing (a 9 1/2" header reached
both, and p.3 caps a hole at 2"). It fits a 2x6 wall. **Bearing:** the GYM's reaction is
3,258 x 3.25 / 2 = 5,294 lb; the row's end bearing is 1.9" at its full load against 2 jacks x
1 1/2" = 3" (2 x 8.25 in2 of stud on the PT SYP sill, 321 psi against Fc-perp 565). The row also
assumes lateral support along the compression edge: head cripples and the plates above.

### 5c. WIN-S-STUDY3

27.5" RO. Its load is 445 + 374 + 90 = 909 plf. `FO-A-STAIR`'s south trimmer pack (y 66 1/8..69
5/8") brings ~500 lb (a 35 plf strip x 17.8' / 2 = 312, guard ~70, header and flight share ~95)
inside the old span at y 64" +/- 13 3/4". Moved 16" south to y 4'-0" (RO 34 1/4..61 3/4", north
pack to 66 1/4") it lands past the king, on the plate; R602.7(1) "Roof, ceiling and one
center-bearing floor" reads the 2-2x8 at 31.5", NJ 2 (§2). `RL-A-HANDRAIL`'s bottom return moved
to y 32 1/4" on the jack pack, clear of the corner bookcase (30 5/8"), its next bracket at
y 65" on the north pack (both handrail backing blocks retired). `BWP-S-E1-0000` ends at the new south jamb and `-0062` starts at the north jamb: 34.25 +
46.25 = 80.5", the same total.

## Cross-checks of the table read (not catlin openings)

- R602.7(1) "Roof and ceiling", 50 psf, 36': 2-2x8 = 4'-2" NJ 2 (50 × 0.70 = 35.0").
- R602.7(1) "Roof, ceiling and two center-bearing floors", 50 psf, 36': 2-2x8 = 3'-3" NJ 2.
- R602.7(2) "One floor only", 36': 2-2x8 = 4'-5" NJ 2; "Two floors", 36': 2-2x8 = 3'-1" NJ 2.
- 2015 R602.7(1), 50 psf, 36', one center-bearing floor: 2-2x8 = 4'-1"; 2018: 3'-9".

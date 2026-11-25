# Court face: LP SmartSide 38 Series smooth panel (W-B-S2-FR, W-B-S3-FR)

## Wind read (ESR-1301 Table 3A)

`structural.cladding_wind` on `W-B-S2-FR` and `W-B-S3-FR` (material `lp-smartside-smooth-panel`,
`published_cladding`, `basis="ultimate"`). Reproduced by `tests/test_cladding_ultimate_row.py`.

**Demand (worked in `catlin_truss_engineering.md` §2 and `board_batten_girt_span.md` §2).**
V_ult 115 mph, Exposure B, RC II, h = 34.7626 ft above the lowest ground, K_h 0.73071,
q_h = 21.0282 psf. Zone 5 (area 2 ft x 2/3 ft = 1.333 ft^2, under 10 ft^2 so GC_p is flat):

    outward  q_h (1.4 + 0.18) = 33.2246 psf ultimate   ->  0.6 x = 19.9348 psf ASD
    inward   q_h (1.0 + 0.18) = 24.8133 psf ultimate   ->  0.6 x = 14.8880 psf ASD

**The row (ESR-1301, reissued Feb 2026, p.6; APA PR-N124 rev. 2026-07-02 Table 3a).**
"PANEL SIDING INSTALLED VERTICALLY WITH 0.113-INCH NAILS", category 3/8, 7/16 and 19/32:
max wall stud spacing 16 in, fasteners 6 in edges / 12 in field, **71 psf** maximum ultimate wind
pressure, V_ult B 170 / C 140 / D 130. Same category at 6 in field: 133 psf. The only 24 in rows
are 19/32 (190 Series); the 38 Series (3/8) has none. fn 1: HDG plain-shank nail, 0.113 in
minimum shank, "a minimum of 2 inches" into framing; fn 2: studs SG >= 0.42; fn 3: three-second
gust at 30 ft, Zone 5, smallest area. The pressures are ULTIMATE, so the demand is compared at
33.2 psf, not 19.93.

**On-label check (16 in studs).** 33.2 <= 71 psf, d/c 0.47; V_ult 115 <= 170 (B).

**Why this wall is not on-label.** Three departures, none of which the table covers:

1. The girts are 24 in o.c., not 16 in (the row's stud spacing; the 38 Series label rating is
   16 in, CAT 2025 p.35, ESR s.4.3).
2. The girts are 1-1/2 in KDAT strapping over a vented cavity: AI 2024 p.2 "LP does not
   recommend panel siding for use over furring strips/strapping ... LP will NOT warrant for
   Buckling", and a 2-1/2 in 8d box nail bites only the 1-1/2 in girt, not fn 1's 2 in.
3. (Held on the owner's word, not the model) the vertical joints land on joint nailers.

**Off-label estimate (not a code read).**

    nail-governed:  133 / 71 = 1.87 ~ 12/6 field spacing, so 71 psf is fastener-governed.
    PR-N124 fn 2 per-fastener floor, ASD: 71 x 0.6 x (16 x 12 / 144 ft^2) = 56.8 ~ 57 lbf. Matches.
    At 24 in girts, one field nail takes 19.9348 x (24 x 12 / 144 = 2 ft^2) = 39.9 lbf
        -> d/c 39.9 / 56.8 = 0.70  (= 33.2 / (71 x 16/24 = 47.3 psf))
    panel bending, 133 x (16/24)^2 = 59.1 psf ultimate vs 33.2 -> d/c 0.56 (not governing)
    inward 24.8 psf is below both.

**Verdict.** UNKNOWN, by design, on both directions: the row's 16 in spacing and 2 in
penetration drift, and LP's strapping position is off-label. The estimate says it should
generally work (d/c ~0.70 on the nail). The owner accepted it 2026-11-24: the wall is sheltered
under the porch roof and the panel is small and cheap to replace. Caveat the estimate does not
cover: withdrawal goes with embedment, so the 1-1/2 in girt gives at most 3/4 of what a 2 in
embedment gives; the 57 lbf floor assumed 2 in. An NDS 12.2 nail read at the girt's SG (KDAT
southern pine) is the check before anyone leans on the 0.70.

`structural.cladding_fastener` is N/A for this panel: the row's pressure is the nailed
assembly's capacity, so the nail is a condition of the row (graded here), and no concealed-leg
screw or metal flange exists for the NDS screw / AISI pull-through arithmetic.

## Sheet layout and joint battens

Worked by hand from the model's walls, girts and openings (not from the engine's layout), and
pinned by `test_sheet_layout.py::test_catlin_court_face_matches_the_lp_panel_oracle`. Stations
are inches along W-B-S2-FR's axis from its start (x = 118"); the two walls are collinear and
laid as one run.

**Inputs.**

- Run: W-B-S2-FR x 118 to 216 (98"), W-B-S3-FR x 216 to 314 (98"): **196"**, both ends free
  (no through corner), so the walk starts at W-B-S2-FR's end, s = 0.
- Band: the panel's foot stands on the base strip, -102 3/16 (wall base) + 1" (base trim
  rise) + 0.032" (strip) = **-101.1555"**, to -13 7/16", where W-M-S1/S2's cladding begins
  over the court walls: **87.718"**. One 96" sheet stood vertically covers it, so there is
  **no horizontal joint** and no Z-flashing seam (AI 2024 p.2 is for a horizontal seam).
- Sheet 4x8 (48" module; LP's actual 47.81" plus the 1/8" gap is the module). Narrowest rip 12"
  (the house's `SheetLayoutStandard`).
- Girt courses (KDAT 2x4 flat, 3 1/2" tall), bottoms at -99 15/16 (the starter, lifted
  2 1/4" clear of the base metal), -78 3/16, -54 3/16, -30 3/16, -15 3/8; the -54 3/16
  course is broken by WIN-B-SAUNA.
- WIN-B-SAUNA: RO s 43 to 57 (x 161 to 175), z -65 7/16 to -41 7/16, sill ladder
  -68 15/16 to -65 7/16, head ladder -41 7/16 to -37 15/16.
- D-B-SUNKEN: RO 63 5/16" wide, s 106 11/32 to 169 21/32 (x 224.34 to 287.66), head
  -21 1/16, head ladder -21 1/16 to -17 9/16; its foot is below the band.

**Joints.** 48, 96, 144; a fourth at 192 would leave 4" (< 12"), so it comes back to
196 - 12 = **184**. Joints at s **48, 96, 144, 184** (x 166, 214, 262, 302). A nailer fits at
each (none lands within a nailer's half-width of an RO edge or a jamb post), so none moves.
s 48 crosses WIN-B-SAUNA 2" left of its centre; s 144 crosses D-B-SUNKEN over its head.

**Sheets.** Columns 0-48 and 48-96 (both cut round the window, W-B-S2-FR), 96-144 (cut
round the door, across the wall split), 144-184 (door, W-B-S3-FR), 184-196 (12" rip, W-B-S3-FR).
Every column needs its own strip of a sheet: 48 + 48 + 48 + 40, and the 12" rip does not fit
the 40" column's 7 7/8" offcut. **5 sheets**: W-B-S2-FR 2, W-B-S3-FR 2, one across the split.

- Gross 196 x 87.718 = 17,192.7 in2. Window 14 x 24 = 336.0; door 63.3125 x (-21.0625 +
  101.1555 = 80.093) = 5,070.9. Net **11,785.8 in2 = 81.8 ft2**.
- Bought 5 x 32 = 160 ft2: 78.2 ft2 of offcut, 49% of what is bought (the door takes most).

**Joint nailers** (KDAT 2x4 flat, 3 1/2" on the panel, cut between courses; ESR-1301 s.4.3).

| Joint | Pieces (z, in) | Length |
|---|---|---|
| s 48 | -96 7/16 to -78 3/16; -74 11/16 to -68 15/16 (sill ladder); -37 15/16 (head ladder) to -30 3/16; -26 11/16 to -15 3/8 | 18.25 + 5.75 + 7.75 + 11.3125 = 43.0625 |
| s 96 | the four bays between courses, -96 7/16 to -15 3/8 | 18.25 + 20.5 + 20.5 + 11.3125 = 70.5625 |
| s 144 | head ladder top -17 9/16 to top course -15 3/8 | 2.1875 |
| s 184 | as s 96 | 70.5625 |

**13 pieces, 186.375" = 15.53 LF.** No nailer goes under the starter course: it would stand
on the aluminium base strip (AWC DCA6). So the panel's foot, -101.1555 to -99 15/16
(**1.22"**), is bare at joints s 48, 96 and 184 (s 144 starts at the door head):
`structural.sheathing_edge_support` reads it UNKNOWN. The same 1.22" is the whole bottom
edge's overhang below the starter, which is the base detail's question, not the joints'.

**Battens** (LP 440 Series smooth 3.50" x 0.675", 16 ft, PID 46000), vertical joints only,
stopped at an opening (and at any trim hosted on it):

| Joint | Pieces (z, in) | Length |
|---|---|---|
| s 48 | -101.1555 to -65 7/16 (window sill); -41 7/16 (head) to -13 7/16 | 35.718 + 28.000 |
| s 96 | -101.1555 to -13 7/16 | 87.718 |
| s 144 | door head -21 1/16 to -13 7/16 | 7.625 |
| s 184 | -101.1555 to -13 7/16 | 87.718 |

**5 pieces, 246.8" = 20.56 LF**, cut from **2 sticks** (87.718 x 2 in one; 35.718 + 28 +
7.625 in the other). No head trim is hosted on either opening yet; when one is, the batten
stops at it instead of at the RO.

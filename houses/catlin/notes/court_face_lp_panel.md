# Court face: LP SmartSide 38 Series smooth panel (W-B-S2-FR, W-B-S3-FR)

**Decided 2026-11-24 (owner).** The sunken court's house face (behind D-B-SUNKEN and WIN-B-SAUNA)
is LP SmartSide 38 Series 3/8" smooth panel, 4x8 vertical, field-painted Benjamin Moore Potters
Clay (1221 / CC-360), on the house's own EXT_2X6 girt stack (`plan/assemblies/lp_panel.py`,
`materials_lp.py`). It replaces the brick wythe W-B-BRICK on the grade beam W-SG-BRKBM, which
stays one switch away (variant `court-face-brick`, section 6). The study that chose it is
`court_face_cladding_study.md` (option B, re-skinned in LP).

What it removes: the masonry-anchor register item (32 -> 31), the 6 1/2" cavity against the
2024 table's 6 5/8", the ties' unverified friction bound, the beam, its board, bed, slab void and
tread-bed recess, two soft joints, two lintels and six stainless flashings.

**What is off-label, accepted by the owner** (sheltered under the porch roof, small, cheap to
replace; "as long as it should generally work"):

1. The girts stay at 24" o.c.; LP's 38 Series is rated and tabled at 16" (section 1).
2. LP does not recommend panel siding over furring or strapping and will not warrant buckling
   there (AI 2024 p.2). The engine has nothing else to hang it on: the girts are the house's
   rainscreen.
3. The panel's foot overhangs the lifted starter girt by 1.22" over the base Z (section 2).

Each shows as an UNKNOWN, never a PASS: `structural.cladding_wind` (both directions) and
`structural.sheathing_edge_support`. They put two lines on the permit checklist ("Exterior wall
covering — wind pressure", "Wall sheathing joints on framing") in place of the two masonry-veneer
lines brick carried; the checklist had 8 open lines before and after.

**Opening trim.** D-B-SUNKEN is trimmed as D-M-PORCH is: Captivate jamb extension and casing,
the `metal-dark-exterior` wrap, and the dark custom door head (`DOOR_HEAD_CUSTOM`); the panel
butts the casing with LP's 3/16" gap and sealant, so there is no jamb trim. WIN-B-SAUNA takes
the house's generic Z drip head (`OPENING_HEAD_DRIP_FLASHING`), membrane and sill pan. **A
Potters Clay picture-frame of LP trim at the window was not simple:** the engine's window casing
is a palette part with no material, no bill and no casing-material setting, so it would need a
new engine path. The window keeps the dark head, by the owner's rule (only if simple and cheap).

**The tread.** D-B-SUNKEN's foam-bed Trex tread drains off its nose onto the rim slab
(`drain_slab_ref="SL-SG-FLOOR"`): the nose clears the slab's north edge by 0.77" and drops
5.24" to it. The slab now runs north to the curb's coated foam, a 0.69" joint (the coating takes
no depth in the model, so 1/2" off its 1/8" face). The model carries no sealant for that joint;
it is priced below by hand.

## 1. Wind read (ESR-1301 Table 3A)

`structural.cladding_wind` on `W-B-S2-FR` and `W-B-S3-FR` (material `lp-smartside-smooth-panel`,
`published_cladding`, `basis="ultimate"`). Reproduced by `tests/test_cladding_ultimate_row.py`.

**Demand (worked in `catlin_truss_engineering.md` §2 and `board_batten_girt_span.md` §2).**
V_ult 115 mph, Exposure B, RC II, h = 34.7626 ft above the lowest ground, K_h 0.73071,
q_h = 21.0282 psf. Zone 5 (area 2 ft x 2/3 ft = 1.333 ft^2, under 10 ft^2 so GC_p is flat):

    outward  q_h (1.4 + 0.18) = 33.2246 psf ultimate   ->  0.6 x = 19.9348 psf ASD
    inward   q_h (1.0 + 0.18) = 24.8133 psf ultimate   ->  0.6 x = 14.8880 psf ASD

**The row (ESR-1301, reissued Feb 2026, p.6; APA PR-N124 rev. 2026-07-02 Table 3a).**
"PANEL SIDING INSTALLED VERTICALLY WITH 0.113-INCH NAILS", category 3/8, 7/16 and 19/32:
max wall stud spacing 16 in, fasteners 6 in edges / 12 in field, 71 psf maximum ultimate wind
pressure, V_ult B 170 / C 140 / D 130; **at 6 in field, 133 psf, V_ult B 200 / C 180 / D 180**,
the row the court face uses (owner, 2026-11-25: the field is nailed at 6 in). The only 24 in rows
are 19/32 (190 Series); the 38 Series (3/8) has none. fn 1: HDG plain-shank nail, 0.113 in
minimum shank, "a minimum of 2 inches" into framing; fn 2: studs SG >= 0.42; fn 3: three-second
gust at 30 ft, Zone 5, smallest area. The pressures are ULTIMATE, so the demand is compared at
33.2 psf, not 19.93.

**On-label check (16 in studs).** 33.2 <= 133 psf, d/c 0.25; V_ult 115 <= 200 (B).

**Why this wall is not on-label.** Three departures, none of which the table covers:

1. The girts are 24 in o.c., not 16 in (the row's stud spacing; the 38 Series label rating is
   16 in, CAT 2025 p.35, ESR s.4.3).
2. The girts are 1-1/2 in KDAT strapping over a vented cavity: AI 2024 p.2 "LP does not
   recommend panel siding for use over furring strips/strapping ... LP will NOT warrant for
   Buckling", and a 2-1/2 in 8d box nail bites only the 1-1/2 in girt, not fn 1's 2 in.
3. (Held on the owner's word, not the model) the vertical joints land on joint nailers.

**Off-label estimate (not a code read).**

    12 in field: 71 x 0.6 x (16 x 12 / 144 ft^2) = 56.8 lbf ASD per nail (PR-N124 fn 2's floor)
    6 in field: 133 x 0.6 x (16 x 6 / 144 ft^2)  = 53.2 lbf ASD per nail, below 56.8, so the
        6/6 row is not purely nail-governed; 53.2 is the conservative per-nail capacity.
    At 24 in girts, one field nail takes 19.9348 x (24 x 6 / 144 = 1 ft^2) = 19.9 lbf
        -> d/c 19.9 / 53.2 = 0.375  (= 33.2 / (133 x 16/24 = 88.7 psf); the engine prints 0.37)
    withdrawal at 1-1/2 in embedment, at most 3/4 of the row's 2 in -> 0.375 / 0.75 = 0.50
    panel bending, 133 x (16/24)^2 = 59.1 psf ultimate vs 33.2 -> d/c 0.56, governs
    inward 24.8 psf is below all three.

At the 12 in field the nail read 0.70, and 0.94 once embedment was capped at 3/4: too close to
lean on an unread withdrawal value. The 6 in field halves the nail's share, so the estimate is
governed by the panel's bending (0.56), which embedment does not touch. The extra nails ride in
the panel's installed $/SF.

**Verdict.** UNKNOWN, by design, on both directions: the row's 16 in spacing and 2 in
penetration drift, and LP's strapping position is off-label. The estimate says it should
generally work (d/c ~0.56, bending). The owner accepted it 2026-11-24: the wall is sheltered
under the porch roof and the panel is small and cheap to replace.

`structural.cladding_fastener` is N/A for this panel: the row's pressure is the nailed
assembly's capacity, so the nail is a condition of the row (graded here), and no concealed-leg
screw or metal flange exists for the NDS screw / AISI pull-through arithmetic.

## 2. Sheet layout and joint battens

Worked by hand from the model's walls, girts and openings (not from the engine's layout), and
pinned by `test_sheet_layout.py::test_catlin_court_face_matches_the_lp_panel_oracle`. Stations
are inches along W-B-S2-FR's axis from its start (x = 118"); the two walls are collinear and
laid as one run.

**Inputs.**

- Run: W-B-S2-FR x 118 to 216 (98"), W-B-S3-FR x 216 to 314 (98"): **196"**, both ends free
  (no through corner). The layout is **centred** (`SheetLayoutStandard.centre_cladding`, owner
  2026-11-25): equal end columns, for the look.
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
  -21 1/16, head ladder -21 1/16 to -17 9/16; its foot is below the band. Jamb posts (KDAT 2x4
  flat) centred at s 104 19/32 and 171 13/32, from the wall base -102 3/16 to -17 9/16; the
  buck's 3/8" jamb legs inside the RO. Its casing and head trim span s 101.84 to 174.16.

**Joints.** 196 / 48 = 4 modules and 4" over; 4/2 = 2" end columns are under the 12" rip, so
one module goes to the ends: (196 - 3 x 48) / 2 = **26"** each. Joints at s **26, 74, 122,
170** (x 144, 192, 240, 288). s 26 and 74 stand 17" clear of WIN-B-SAUNA's RO either side and
24" from its centre (s 50), so no joint crosses the window. s 122 crosses D-B-SUNKEN over its
head. s 170 is 11/32" past the door's RO edge, under its casing (to s 174.16).

**Sheets.** Columns 0-26 and 26-74 (W-B-S2-FR, the second cut round the window), 74-122
(across the wall split at s 98, cut round the door), 122-170 (door, W-B-S3-FR), 170-196
(W-B-S3-FR). The two 26" end columns cannot share a 47.81" sheet (52"), and their 22" offcuts
fit no other column. **5 sheets**: W-B-S2-FR 2, W-B-S3-FR 2, one across the split.

- Gross 196 x 87.718 = 17,192.7 in2. Window 14 x 24 = 336.0; door 63.3125 x (-21.0625 +
  101.1555 = 80.093) = 5,070.9. Net **11,785.8 in2 = 81.8 ft2**.
- Bought 5 x 32 = 160 ft2: 78.2 ft2 of offcut, 49% of what is bought (the door takes most).

**Joint nailers** (KDAT 2x4 flat, 3 1/2" on the panel, cut between courses; ESR-1301 s.4.3).
s 26 and 74 lie clear of the window, so the -54 3/16 course runs through both.

| Joint | Pieces (z, in) | Length |
|---|---|---|
| s 26 | the four bays between courses, -96 7/16 to -15 3/8 | 18.25 + 20.5 + 20.5 + 11.3125 = 70.5625 |
| s 74 | as s 26 | 70.5625 |
| s 122 | head ladder top -17 9/16 to top course -15 3/8 | 2.1875 |
| s 170 | as s 122 (below it, the jamb post backs the joint) | 2.1875 |

**10 pieces, 145.5" = 12.13 LF.** At s 170 the joint's 7/16" bearing either side (s 169 9/16
to 170 7/16) lies on the jamb post (169 21/32 to 173 5/32) with the buck's jamb leg beside it
(169 9/32 to 169 21/32), from the wall base up; above the head ladder, the nailer. No nailer
goes under the starter course: it would stand on the aluminium base strip (AWC DCA6). So the
panel's foot, -101.1555 to -99 15/16 (**1.22"**), is bare at s 26 and 74 (s 122 starts at the
door head; s 170 sits on the post): `structural.sheathing_edge_support` reads it UNKNOWN. The
same 1.22" is the whole bottom edge's overhang below the starter, which is the base detail's
question, not the joints'.

**Battens** (LP 440 Series smooth 3.50" x 0.675", 16 ft, PID 46000), vertical joints only,
stopped at an opening their 3.50" face touches, over the full height of that opening and the
trim hosted on it:

| Joint | Pieces (z, in) | Length |
|---|---|---|
| s 26 | -101.1555 to -13 7/16 | 87.718 |
| s 74 | -101.1555 to -13 7/16 | 87.718 |
| s 122 | none: the door's custom head and flashing reach the top of the panel | 0 |
| s 170 | none: the batten would sit on the casing; the joint is under it | 0 |

**2 pieces, 175.44" = 14.62 LF**, cut from **1 stick** (87.718 x 2 + kerf in 192"). The two
battens frame WIN-B-SAUNA symmetrically, 48" apart.

## 3. Base and clearances (AI 2024, confirmed for panel)

LP's panel instructions keep the lap siding's clearances: 6" to grade, 1" over a walking surface
(3/8" under its stated conditions), 1" to roofing; every cut edge sealed.

    panel foot           -101.1555"  (wall base -102 3/16 + 1" base trim rise + 0.032" strip)
    court rim / field    -109 7/16"  (SL-SG-FLOOR top, the court's walking surface and grade)
    clearance            8.28"       >= 6" to grade and >= 1" to a walking surface
    curb top             -102 3/16"  the panel laps the 7 1/4" curb's coated foam by 1.03"

The base closes as every house rainscreen base does: the Una-Clad Z, its EPDM strip and the bug
screen. At D-B-SUNKEN, whose opening reaches the curb, all three stop short of the door
(`resolve/rainscreen_closures.base_run_spans`): 4.7" and 22.7" stretches either side, each cut
back 3 5/8" past the RO so no aluminium touches the KDAT jamb strapping. The door's pan laps
over their ends.

At the top of the panel, W-M-S1/S2's BBD75 base screens (the storey above, where the two
cavities meet) graze the LP walls' top girt by 5.6 in3 each. Accepted in the overlap
baseline (owner, 2026-11-25): a sliver of screen against a girt face.

## 4. Winter tension (thermal_break_transfer, the side run)

The house side's sliding load at mu_max 1.00 is the free body's 129,306 lb (house body, section
11l), less the brick's beam that is no longer there (3,994 lb, counted before), shared by two
side lines:

    T = (129,306 - 3,994) / 2 = 62,656 lb per side run        (engine: 62,656.1)

Against the study's 6 #4 (64,800 lb) that read 0.967. Since the structure lane gave W1/E1 W2's
stem steel (free body §15n), each side run carries 4.4 in2 of steel, 0.9 x 4.4 x 60,000 =
237,600 lb: **0.264**. The record is now governed by the court-to-house joint closure, **0.665**
(brick: 0.676, governed by the house slab edge, the beam's board still on it).

## 5. Cost (takeoff, net installed, ESTIMATE rows as priced in prices.toml)

LP default against the `court-face-brick` house, both with the structure lane's steel and heel:
**-$2,839 to -$5,026.** The study read -$2.2k to -$4.3k with its additions.

| Change | Low | High |
|---|---|---|
| brick 88.5 SF out | -1,682 | -2,655 |
| beam SG_VENEER_BEAM_14, 1.0 cy out | -429 | -718 |
| reveal openings 19 -> 16 | -315 | -795 |
| lintels L3x3x1/4, 7.8 LF out | -249 | -513 |
| framed-wall membrane and 2" XPS (GARDEN_FRAMED_2X6's) out | -515 | -1,001 |
| Trex box sides, soft joints, brick flashings, bed stone, the beam's bars | -766 | -1,419 |
| LP panel 84.2 SF in (ESTIMATE) | +286 | +602 |
| panel paint 84.2 SF in (ESTIMATE) | +125 | +372 |
| LP 440 battens, 1 stick (ESTIMATE) | +46 | +130 |
| ccSPF 4" +84 SF, girts, nailers, TimberLOKs, fibreglass for mineral wool, buck rip | +702 | +1,120 |
| rainscreen base Z, bug screens, strips, heads, closures, net | -144 | -348 |
| rim slab to the curb, capillary stone, allowances, sealants | +100 | +199 |
| **total** | **-2,839** | **-5,026** |

Not in the takeoff, added by hand: the 0.69" rim-slab-to-curb joint, ~17 LF of sealant at the
movement-joint rate, **ESTIMATE +$200-425**. The W-M-S1/S2 BBD75 panels above now bill their
base C-closure (+37 LF, +$138-205: their panel end no longer stops on a perforated strip,
because the LP cavity runs on below), included above. Prices are retail and published labour
bands (2026-11-24); no Twin Cities yard quote yet (4x8 smooth panel, KDAT 2x4).

## 6. Switching back to brick

Brick is variant `court-face-brick` (houses/catlin/variants.toml): `sunken_garden.cladding =
"brick"` plus two assembly swaps, `EXT_2X6_LP_PANEL -> GARDEN_FRAMED_2X6` and
`SAUNA_LINER_ON_EXT_2X6_LP -> SAUNA_LINER_ON_GARDEN_FRAMED`. `params/court_face.py` builds the
wythe set (W-B-BRICK, its nodes, reveals, lintels, flashings, soft joints, the veneer slices and
three transitions); `OPTION.has_brick_face` gates the beam side in params/sunken_garden.py
(W-SG-BRKBM, FB-SG-BRKBM, FO-SG-BRKBM, AO-SG-BRKBM-TREAD-BED, N-SG-BMW/BME, the slab's north
edge, `_STONE_FROM`, AN-SG-PLACEMENTS/BLOCKOUTS) and D-B-SUNKEN's trim and tread drain. The
curb coating stays in both. `tests/test_court_face_variants.py` pins that the variant reproduces
main's pre-switch fingerprints, except the 7 court records the structure lane re-derived (free
body §15n).

To make brick the house again:

1. `params/sunken_garden_options.py`: `cladding` default `"brick"`.
2. `plan/storeys/basement.py`: W-B-S2-FR `assembly="SAUNA_LINER_ON_GARDEN_FRAMED"`, W-B-S3-FR
   `assembly="GARDEN_FRAMED_2X6"`.
3. `tasks.toml` (TOML cannot branch): the masonry visit takes back
   `"wall_structure:BASEMENT_BRICK_VENEER:brown-brick"` in `rows`, `"W-B-BRICK"` in
   `element_tags`, the `court` checkpoint ("Court veneer — W-B-BRICK on W-SG-BRKBM"), the
   weeps/soft-joints/anchor and scaffold constraints, and the 132.2 SF (112.5 court + 19.6
   firebox) blend line; the walls visit says "stem and beam blockouts" and "five" boards; the
   mineral-wash visit drops `envelope_layers:lp-panel-paint-exterior` and W-B-S2-FR/S3-FR and
   takes back "W-B-BRICK stays BARE brown". `git show 8609bd036:houses/catlin/tasks.toml` has
   every line.
4. `inspections.toml` `break_blockouts_stripped`: "all five blockouts ... and W-SG-BRKBM's" and
   the beam board's lock-in line (same commit).
5. Swap the variant: rename this one `court-face-lp` with the inverse parameter and swaps, and
   re-point the fixtures in `tests/conftest.py`.

The brick notes are dormant, not retired: `sunken_garden_veneer_beam.md`,
`veneer_opening_detail.md` and `engineering_review_2026-11-22/F_junction_veneer.md` stay the
oracles for the veneer tests, which run on the brick fixture.

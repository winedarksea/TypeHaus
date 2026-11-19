# Exterior door sill beam, joint cover and sunken tread (owner, 2026-11-17)

Hand oracle for `engineering/exterior_door_support.py` (`sill_beam_report`,
`screw_spacing_failures`, `girt_course_connection_report`, `foam_bed_support_report`),
`engineering/sill_seat_rotation.py`, `resolve/girt_sill_connection.py` and
`resolve/exterior_door_cover.py`. Review basis:
`plans/exterior-door-sill-and-approach.md`. It replaces the girt sill course of
`exterior_door_structural_mount.md` (3-screw end blocks, 41 TLOK10s).

Depths are inches outward from the sheathing's outer face; elevations are off the storey datum
(top of joists). Doors: D-M-PORCH and D-S-BALCONY (63 5/16" RO), D-M-ENTRY (38 3/8").

## 1. Geometry

- **One sill package.** ZAI5625FN on the 4 9/16" jamb, frame outer face on the sheathing, sill
  starting 0.020" past the frame's inner face: sill nose 1.0825", XXXXW 6 3/8" → **nose 7.4575"**.
- **Beam.** KDAT 2x6 on edge, RO edge to RO edge, its back on the girt band's outer face (6.0"),
  face **7.5"**: 0.0425" past the nose, so the nose is fully supported; 0.75" proud of the
  board-and-batten face (6.75"). Top at the rough sill (+3/4", the subfloor top), bottom −4 3/4".
  The top is ripped at 1/4"/ft: 1/32" across 1 1/2", top +0.71875" at the face (modelled as the
  beam's `section_ring` since 2026-11-18). The pan runs level over the buck sill, falls across
  the beam and turns down its face to a 1/2" drip at 7.5"+. The pan's fall is read off the
  ripped beam, 0.03125 / 1.5 × 12 = **0.25"/ft**, and graded against
  `opening_flashing_spec.md` §3's 1/4"/ft minimum (`SillCourseFastening.pan_min_fall_per_ft`):
  exactly at it.
- **Seats.** One stack per end, 4 plies of **2x8** KDAT (sheathing to beam back, 6.0"), **10"**
  along the beam (SP's Table 5 end distance, §3), 7 1/4" tall (2x6 until 2026-11-18: the taller
  ply lengthens the rotation couple's arm, §3), top under the 3/8" buck sill (+3/8"), bottom
  −6 7/8": 13/16" over the main-floor walls' starter girt course (top −7.69"); at BALCONY nothing
  stands below it inside the rim's depth (rim bottom −11 7/8", next course −24").
- **Edge member.** An LSL rim board, 1 1/4" × 11 7/8" (Weyerhaeuser TimberStrand 1.3E, the house
  rim; `JoistSpec.edge_rims`, owner 2026-11-18) in place of the edge TJI 230 at all three doors,
  its outer face on the sheathing's back (flush with the stud face, as an end rim's is):
  FS-M-EAST `edge-rim-0-000-0` (PORCH, D-B-SUNKEN's LVL band plies nailed to its inner face),
  FS-M-MECH `edge-rim-0-011-0` (ENTRY, on W-B-N3's mudsill) and FS-S-EAST `edge-rim-0-000-0`
  (BALCONY, on W-M-S2's plates). The SPF web backers and their flange question are gone.
- **Backer behind the rim** (owner, 2026-11-18; `params/sill_seat_backers.py`), so the HeadLOK's
  2.0" of thread embeds (§3): PORCH, D-B-SUNKEN's 1 3/4" LVL plies already nailed to the rim;
  BALCONY, a 10" piece of the 1 1/4" rim stock on the rim's inner face behind each seat (a 2-ply
  rim board), alone in its bay (y 1 3/4"..3", the next line at 8 11/32"); ENTRY, a 10" × 1/2"
  LSL filler behind each seat closing the 1/2" gap to FO-M-ERV-OA's LVL trimmer pack, clear of
  the two 1/2" wall-top blocks at x 70"/96". No hanger, MEP run or ceiling item in any of them.
- **Wood through the foam.** 2 × 10 × 7.25 = **145 in²** a door (110 with the 2x6 seats). The
  retired course had 11 blocks × 3.5² = 134.75 in² at the wide doors and 7 × 12.25 = 85.75 at
  the entry. The foam runs unbroken between the seats.

## 2. Beam

No.2 SPF wet stands in for KDAT SP (lower bound, as `catlin_truss_engineering.md` §4):
Fb' = 875 × C_F 1.3 = **1,137 psi** (C_M 1.0: Fb·C_F ≤ 1,150; C_D 1.0), Fv' = 135 × 0.97 = **131
psi**, E' = 1.4e6 × 0.90 = **1.26e6 psi**. S = 1.5 × 5.5²/6 = 7.5625 in³, I = 20.797 in⁴,
A = 8.25 in². Span between the seats' screw-group centroids (each (3 + 5.625 + 4.3125 + 6.9375)/4
= 4.96875" in from its end, §3): 63.3125 − 9.9375 = **53.375"**; entry 38.375 − 9.9375 =
**28.4375"**. 300 lb point. EI = 1.26e6 × 20.797 = 2.6204e7 lb-in².

| | M = PL/4 | fb / Fb' | fv = 1.5P/A, / Fv' | Δ = PL³/48EI vs 1/8" |
|---|---|---|---|---|
| wide | 4,003.1 lb-in | 529.3 / 1,137 = **0.466** | 54.5 / 131 = **0.416** | 4.5618e7 / 1.2578e9 = **0.0363"** |
| entry | 2,132.8 lb-in | 282.0 / 1,137 = **0.248** | **0.416** | 6.8991e6 / 1.2578e9 = **0.0055"** |

1/8" is the door maker's limit over an unsupported span (Marvin site prep, cited in the review).

## 3. Seat screws, HeadLOK HLGM10 into the LSL rim and its backer (2026-11-18)

**An all-table joint was tried first (owner: "a strong preference to keep it to a table") and
does not exist here.** ESR-1078 (reissued 2026-01) Table 4 is two-member with no gap (note 1)
and every row wants 2 1/2"-5" of main penetration; its one LSL row (LedgerLOK LL358, note 7) is a
1 1/2" side member that may not be thickened (note 5). Laminating the seat ply by ply on LL358s
still leaves the sheathing as an untested third member and the eccentric couple to NDS §12.4.1.
So the lateral value is a house NDS 12.3 calc (a draft check, no seal) and the couple is graded
by §12.4.1, as ESR-1078 §4.1.6 directs; Tables 1B, 2, 3 and 5 are read as published.

**The screw: HeadLOK, not TimberLOK (owner, 2026-11-18).** Same 10" length and 2" thread
(ESR-1078 Table 1B: HLGM10, shank 0.191", root 0.172", F_yb 187,300 psi, allowable tension
1,215 lb, shear 965 lb), but a flat head: Table 3, 1 1/2" side member, W_H **600 lb** at SG 0.55
(the KDAT's SP, as Table 5 reads it) and **400 lb** at SG 0.42 (the house's lower bound), against
TimberLOK's 200 / 110. Its Table 2 floor is **2.0"** of embedded thread, hence the backer (§1).
TimberLOK's 2x6 seats put ~300 lb of tension on a top screw: 2.23 (SP) / 3.75 (G 0.42) of §12.4.1.

**Screw fit** (`catlin_truss_engineering.md` §3.1–§3.3: the sheathing is nailed to the rim, so
it is on the main member's side):

    clamped stack   beam 1.5 + seat 6.0                     = 7.5"
    through         + sheathing 0.5                         = 8.0"
    HLGM10          10", 2" thread → plain shank 8.0" ≥ 7.5"                     ✓ 0.5"
    thread          8.0" to 10.0": starts at the rim's face, 1.25" in the rim, 0.75" in the backer
                    PORCH  LVL ply 1 (1.75", tip 1.0" short of its far face)
                    BALCONY rim-stock backer (1.25", tip 0.5" short)
                    ENTRY  1/2" filler, then 0.25" into the LVL trimmer
    in wood         1.25 + 0.75 = 2.00" ≥ 2.0" (ESR-1078 Table 2)                ✓ exactly
    penetration     2.00" ≥ 6D = 6 × 0.191 = 1.146" (NDS 12.1.4.6)               ✓

**Lateral, NDS 2018 §12.3**, single shear: D 0.172" (root), F_yb 187,300 psi, R_d = 10D + 0.5 =
2.22. Side: the 8" stack at G 0.42, F_es = 16,600 × 0.42^1.84 = 3,364.2 psi. Main: the rim and
backer at G 0.50 (ESR-1387's equivalent SG; Microllam LVL the same), F_em = 4,636.7 psi,
l_m 2.0". R_e = 1.3782, R_t = 0.25.

| Mode | Working | Z, lb |
|---|---|---|
| Im | 0.172 × 2.0 × 4,636.7 / 2.22 | 718.5 |
| Is | 0.172 × 8.0 × 3,364.2 / 2.22 | 2,085.2 |
| II | k1 0.34994 × 2,085.2 | 729.7 |
| IIIm | k2 = −1 + √(4.7565 + 2 × 187,300 × 3.7565 × 0.029584 / (3 × 4,636.7 × 4.0)) = −1 + √(4.7565 + 0.7482) = 1.34621; k2 × 0.172 × 2.0 × 4,636.7 / (3.7565 × 2.22) | 257.5 |
| IIIs | k3 0.86900 × 0.172 × 8.0 × 4,636.7 / (3.3782 × 2.22) | 739.3 |
| IV | 0.029584 / 2.22 × √(2 × 4,636.7 × 187,300 / (3 × 2.3782)) | **207.9** |

**Z = 207.9 (IV), Z' = 0.70 × 207.9 = 145.5 lb** (C_M 0.70, wet KDAT side members). Mode IV does
not see l_m, so the backer's share of it is the IIIm mode it lifts off the governing line
(189.2 on the rim alone, Z' 132.5; the TLOK10's was 190.0). Neither does it see l_s: with the
sheathing on the main side (l_s 7.5") Is, II and IIIs drop to 1,955 / 684 / 694 and Z holds.

**Spacing, ESR-1078 Table 5** (its TimberLOK/OlyLOG/HeadLOK column, SG > 0.50 for the KDAT SP
and the LSL/LVL): end 3", in-row 2 5/8", edges 1 3/4", staggered rows 3/4". The band every
member's edge distances leave is unchanged by the taller seat: beam −3.000..−1.000, seat
−5.125..−1.375, rim and backers −10.125..−1.750, so −3.000..−1.750 and rows at −2.000 and
−2.750. Row 1 at 3, 5.625; row 2 at 4.3125, 6.9375 from each beam end; 10 − 6.9375 = 3.0625 ✓.
The backers are each seat's own 10", so the 3" end distance holds in them too. **8 HLGM10 a door,
24 in all** (24 TLOK10 before).

**Shares, an independent PyNite model** (`Pynite` FEModel3D: the 2x6 beam, E' 1.26e6, I 20.797,
on vertical springs k = 270,000 × 0.191^1.5 = 22,537.9 lb/in at the eight stations, 300 lb
scanned at 1/4"). Load at the beam end, the case that governs the rotation:

| Door | Screw forces, lb (station) | seat Σ |
|---|---|---|
| wide | **123.73 (3.0)** · 66.73 (5.625) · 94.41 (4.3125) · 40.87 (6.9375) / far seat 8.22 · −11.31 · −1.54 · −21.11 | **325.73** |
| entry | **116.33 (3.0)** · 76.83 (5.625) · 95.75 (4.3125) · 59.75 (6.9375) / far seat −8.23 · −13.50 · −10.87 · −16.07 | **348.67** |

The near seat takes more than the 300 lb: the beam levers the far seat up. Worst lateral share
anywhere: **125.34 lb** (wide, load 22 1/4" in, the 6.9375 screw) → 125.34 / 145.5 = **0.861**;
entry 116.33 → **0.800**.

**Rotation.** The reaction stands 0.5 + 6.0 + 0.75 = **7.25"** off the rim face, so a seat rolls
outward about its bottom bearing on the sheathing (the arm is taken to the rim face, as if the
screws' shear acted there: about the sheathing face it is 6.75" less the screws' own arm in the
seat, so 7.25 is an upper bound); the compression resultant is taken 0.4" up
(the compression is ΣT, 611 lb at ENTRY's end load: 76 psi over a 10" × 0.8" block of plywood face). Pivot −6.875 + 0.4 =
−6.475; levers 4.475 (row −2.000) and 3.725 (row −2.750); Σd² = 2 × 4.475² + 2 × 3.725² =
67.8025 in². Tension T = R × 7.25 × d / Σd²; each screw's own lateral share rides with it.

    axial W'   withdrawal 230 lb/in (Table 2, SG 0.50, dry rim and backer) × 2.0" = 460 lb
               pull-through × C_M 0.70: 600 → 420 (SP 0.55), 400 → 280 (G 0.42)
               W' = 420 (SP) or 280 (G 0.42); the screw's own 1,215 / 965 lb never governs
    §12.4.1    Z'α = W' Z' / (W' cos²α + Z' sin²α), tan α = T / Z, graded on √(Z² + T²)

| Door, column | Case | Z | T | √ | cos²α | Z'α | ratio |
|---|---|---|---|---|---|---|---|
| wide, G 0.42 | end load, 3.0 screw, R 325.73, M 2,361.6 | 123.73 | 155.87 | 199.01 | 0.38655 | 280 × 145.5 / (108.23 + 89.26) = 206.29 | **0.965** |
| entry, G 0.42 | end load, 3.0 screw, R 348.67, M 2,527.8 | 116.33 | 166.84 | 203.39 | 0.32713 | 40,740 / (91.60 + 97.90) = 214.99 | **0.946** |
| wide, SP 0.55 | load 22 3/4", 6.9375 screw, R 201.30 | 125.31 | 80.18 | 148.77 | 0.70951 | 61,110 / (297.99 + 42.27) = 179.60 | **0.828** |
| entry, SP 0.55 | end load, 3.0 screw | 116.33 | 166.84 | 203.39 | 0.32713 | 61,110 / (137.39 + 97.90) = 259.71 | **0.783** |

The ¼" scan finds nothing worse; the engine's own scan agrees to the hundredth of a pound
(0.9647 / 0.9460 / 0.8283 / 0.7831). **It passes on both pull-through columns**, the SP reading
the house already takes for `girt_screw/W-A-N1` and Table 5, and the G 0.42 bound.

**Scope of the withdrawal read (review, 2026-11-18).** ESR-1078 §3.2 puts EWP other than glulam
and CLT outside the report, so Table 2 in the LSL rim, the LVL plies and the filler is read at
ESR-1387 Table 2's face-withdrawal SG 0.50, and the 2.0" minimum is met only by summing thread
across pieces held in contact (rim + backer; at ENTRY rim 1.25 + filler 0.5 + 0.25 of LVL, the
last of it the gimlet tip). The tension pulls each backer onto the rim, so the pieces bear
rather than part. Neither reading is load-bearing for the grade: the G 0.42 column is
pull-through in the sawn beam (280 < 460) and does not move, and on the rim's 1.25" alone
(W' 287.5) the SP column rises to 0.953 (wide) / 0.933 (entry), rim + filler at ENTRY
(402.5) 0.797. What the backer buys is ESR's 2.0" minimum, which a single member here cannot
give.

**Accepted as the house reading (owner, 2026-11-18).** ENTRY meets Table 2's 2.0" by the sum,
rim 1 1/4" + filler 1/2" + 1/4" of FO-M-ERV-OA's LVL trimmer, the pieces drawn tight, with the
withdrawal in LSL/LVL read at ESR-1387's SG 0.50. The rim alone passes too (0.933, SP).

**Backer nailing**, the published rows:

- BALCONY: TJ-8000 (March 2025) p.7, *Multiple-member connections for 2-ply rim board*, side
  load, 1 1/4" plies, 10d (0.128-0.131 × 3"), one face, **3 rows** at 12" o.c.: 560 plf on either
  member. The row's 12" o.c. is a maximum: a 10" backer takes 3 rows of 2 (one near each end,
  denser than the row, credited only at it), clinched (note 2; 3" through 2 1/2" of LSL). Capacity
  pro rata, 560 × 10/12 = 467 lb. Demand, the whole wide-door seat reaction as if all of it reached
  the backer: 325.73 / (10/12) = 390.9 plf → **0.70** (2 rows, 370 plf, would be 1.06).
- ENTRY: no published row covers a rim nailed through a filler to a trimmer pack; the pattern is
  borrowed from IRC R602.3(1) item 10, *built-up header (2" to 2" header with 1/2" spacer)*, 16d
  common (3 1/2" × 0.162") at 16" o.c. each edge, face nail, through the rim and filler into the
  LVL trimmer: 2 an edge on a 10" filler, 4 in all. The NDS check carries it: 16d, NDS 12.3, side 1.75" (rim + filler)
  and penetration 1.75" at G 0.50, F_yb 90 ksi, R_d 2.2: Im = Is 597.5 · II 247.5 · IIIm = IIIs
  215.4 · IV 0.026244 / 2.2 × √(2 × 4,636.7 × 90,000 / 6) = **140.7 lb** (dry, C_M 1.0);
  348.67 / 4 = 87.2 lb a nail → **0.62**.
- PORCH: the LVL plies' own band-header fastening (TJ-9000 p.30, 3 rows of 10d at 12", nailed to
  the rim, `sunken_door_band_header.md`); nothing added.

The screws' tension pulls each backer toward the rim, so no nail is in withdrawal.

**Jamb-post variant (rejected, design unchanged).** A girt jamb post's own standoff at the sill is
one 3 1/2" block: a screw needs 3" of end distance each side, so the post cannot take even one
screw to Table 5; the beam would also have to run 3 1/2" past each RO edge in front of the
cladding to reach it.

## 4. Walking joint

Range each way = the catalog's 1/4" movement + 1/4" construction tolerance = **1/2"**. A cover is
fixed on the landing member's inner part (the plank ends keep their 3/4" on its outer part), top
flush with the deck, and slides on a KDAT ledge on the beam face. Its inner edge stands 1/2" off
the pan's 0.020" drip leg on the beam face, so it just meets that leg at the narrowest joint.

- **D-M-PORCH, cover.** Beam face 7.5", FS-SG-PORCH's north joist 9.625": joint 2.125". Ledge
  1 9/16" → 9.0625". Cover edge 7.5 + 0.020 + 0.5 = 8.02". Bearing at the widest:
  9.0625 − (8.02 + 0.5) = **0.5425" ≥ 1/2"**. Ledge to joist at the narrowest:
  9.625 − 0.5 − 9.0625 = **1/16"**. Fixed end 1.5 − 0.75 = 0.75". Cover 0.94" thick (joist top 0
  to deck top 0.94), 2.355" wide, over the full RO. Ledge top at 0, under the drip's foot
  (+0.75 − 1/32 − 1/2 = +0.22). Across the RO the porch planks stop on the joist's outer 3/4"
  (10.375"), so the cover's fixed end has the inner 3/4" (review, 2026-11-18: the planks had
  covered it). TR-SG-SLOT drops 3/4" to sit under the ledge (it filled the ledge's place); water
  through the cover falls past the ledge onto it.
- **D-S-BALCONY, open gap (owner, 2026-11-18).** A 1.0" joint took no cover (one needs ≥ 2.0"), so it
  narrows like ENTRY's: the rear rim oversail goes 1 1/2" → 2 1/8" along the whole edge and the
  planks' tab at the door reaches **7.875"**, **3/8"** off the beam (0.4175" off the nose), 1/8" left
  after the 1/4" movement. The north sister (a 2x12 plus a 5/8" treated ply packer, one 2 1/8"
  ply) runs beam to beam flush with the rim ends, so the tab bears its full depth on it and the rim
  ends are backed: nothing oversails a support. A 300 lb point on the tab's edge lands on that
  doubled joist, a full-span ply graded with the field's joists; no new cantilever arises. The rear
  cladding gap is 1 1/8" (was 1 3/4"): the base flashing's upstand stands that far off the
  cladding against 1/4" movement, and the counterflashing (gap + 1/2" wide) still laps past it. Wahoo publishes no plank-to-wall gap (`plans/TODO.md`).
- **D-M-ENTRY, open gap.** FS-BW-FLOOR's rim moved 1/8" out (inner face 7.875", rim centre
  36'-8 5/8") and the deck edge onto it: **3/8"** off the beam, 0.4175" off the nose, ≤ 1/2".

## 5. D-B-SUNKEN tread

A 1/4" FRP plate under the scalloped Trex spreads the 300 lb over the full 5.5 × 5.5 footprint;
the XPS course is 60 psi, thinned 1/4" so the tread top holds.

    point 300 / 30.25 = 9.917 psi; uniform 70/144 = 0.486; bearing 10.403 psi
    allowable 60 / 3 = 20.0 psi → d/c 0.520   (on 40 psi without the plate: 0.780 at full contact,
    and the scallops need 300 / (40/3 − 0.486) = 23.35 in² of it, unproven)

Without a plate, a profiled board is UNKNOWN unless its contact area is authored.

## 6. Crests (outline rescale and membrane pan, 2026-11-18)

The Endura outlines were digitized with a vertical scale fitted to the 1 3/8" tick (436.4 px/in)
against the drawing's one uniform scale (468.3 px/in; at it the deck measures 5.06°, labelled 5°).
Heights × 0.9319: **ZAI5625FN 1.517" → 1.414"**, ZAI4565FN 1.522" → 1.419". The three framed doors
sit on a self-adhered membrane pan on the subfloor, 1/16" (was SureSill's 3/8" worst case).

| Door | Crest over inside | + 1/4" | Over outside |
|---|---|---|---|
| D-M-ENTRY | 0.75 + 0.0625 + 1.414 − 1.026 (LVP) = **1.201"** | **1.451"** ≤ 1 1/2" R311.3.1 | 2.226" |
| D-M-PORCH | 1.201" | 1.451" | 1.286" |
| D-S-BALCONY | 0.726" over the oak (was 1.142") | 0.976" | 1.285" |
| D-B-SUNKEN | 6.544" (outline only, −0.104") | | 7.294" |

The passive leaf's lower bolt receiver is a cup in a hole drilled into the cap, 5/8" wide and at least
1 3/8" deep (Endura Flip-Lever astragal instructions #211159-FL-I-FP, step 1d; owner, 2026-11-18). From the
cap top at the hole (x 1" off the rear edge, 1.413"; 1.419" on the ZAI4565FN), the hole leaves 0.038"
(0.044") of sill body: in the body to within the outline's ~0.1" accuracy, so it passes on the maker's
instruction. Only a break-through past 0.1" is a conflict. Raising the cap raises the crest one for one.

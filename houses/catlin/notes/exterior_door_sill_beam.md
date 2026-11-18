# Exterior door sill beam, joint cover and sunken tread (owner, 2026-11-17)

Hand oracle for `engineering/exterior_door_support.py` (`sill_beam_report`,
`screw_spacing_failures`, `girt_course_connection_report`, `foam_bed_support_report`),
`resolve/girt_sill_connection.py` and `resolve/exterior_door_cover.py`. Review basis:
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
- **Seats.** One stack per end, 4 plies of 2x6 KDAT (sheathing to beam back, 6.0"), **10"** along
  the beam (9 1/4" until 2026-11-18: SP's Table 5 end distance, §3), 5 1/2" tall, top under the
  3/8" buck sill (+3/8"), bottom −5 1/8".
- **Edge member.** An LSL rim board, 1 1/4" × 11 7/8" (Weyerhaeuser TimberStrand 1.3E, the house
  rim; `JoistSpec.edge_rims`, owner 2026-11-18) in place of the edge TJI 230 at all three doors,
  its outer face on the sheathing's back (flush with the stud face, as an end rim's is):
  FS-M-EAST `edge-rim-0-000-0` (PORCH, D-B-SUNKEN's LVL band plies nailed to its inner face),
  FS-M-MECH `edge-rim-0-011-0` (ENTRY, on W-B-N3's mudsill) and FS-S-EAST `edge-rim-0-000-0`
  (BALCONY, on W-M-S2's plates). The SPF web backers and their flange question are gone.
- **Wood through the foam.** 2 × 10 × 5.5 = **110 in²** a door. The wide doors drop from
  11 blocks × 3.5² = 134.75 in² (−18%); the entry *rises* from 7 × 12.25 = 85.75 in² (+28%).
  The foam now runs unbroken between the seats.

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

## 3. Seat screws, TLOK10 into the LSL rim (2026-11-18)

**An all-table joint was tried first (owner: "a strong preference to keep it to a table") and
does not exist here.** ESR-1078 (reissued 2026-01), read in full:

- Table 4 is two-member, "Gaps are not permitted between the main and side members" (note 1); a
  thicker side member keeps the row only if the main penetration is still met (note 2). Every
  TimberLOK row needs 2 1/2"-5" of main penetration; the rim is 1 1/4".
- Its one LSL row (note 7) is LedgerLOK LL358: a **1 1/2"** side member of SG 0.50 into a
  ≥ 1" LSL rim, through it, Z⊥ 300 lb, with note 5 "side member thickness must not be
  increased". A seat would have to be laminated ply by ply: ply 1 on the rim by note 7, the
  others and the beam by the LL358 1 1/2"-into-1 1/2" through row (Z⊥ 220 lb at G 0.42).
- The 1/2" sheathing between ply 1 and the rim is a third member the row never tested; cutting
  it out behind each seat leaves the stack 1/2" short of the girt face, and a 1/2" packer is the
  same interlayer again. ESR-1387's ledger rows (1/2" lag 610 lb, through-bolt 725 lb in a
  1 1/4" rim) do include a structural panel, but for a 2x ledger only, with the same problem at
  every ply beyond it.
- Each interface also carries the reaction's eccentric moment as withdrawal; LL358 cannot embed
  Table 2's 2" of thread in a 1 1/2" ply or a 1 1/4" rim, so that couple is an NDS §12.4.1
  design either way (ESR-1078 §4.1.6 sends it there).
- Five interfaces of two or more LL358 each, a sheathing cut-out and a packer per seat, against
  four long screws: clearly more parts and labour, still not a table read.

So the NDS 12.3 calc stays the lateral basis, re-run on the rim; it is a draft check (no seal).
ESR-1078's Table 2 embedded thread and Table 5 spacing stay graded as published.

**Screw fit** (`catlin_truss_engineering.md` §3.1–§3.3: the sheathing is nailed to the rim, so
it is on the main member's side):

    clamped stack   beam 1.5 + seat 6.0                     = 7.5"
    through         + sheathing 0.5                         = 8.0"
    TLOK10          10", 2" thread (ESR-1078 Table 1A) → plain shank 8.0" ≥ 7.5"   ✓ 0.5"
    thread          8.0" to 10.0": starts at the rim's face, 1.25" in it, 0.75" past its far
                    face (into the joist bay; at PORCH into the LVL plies, not credited)
    in wood         1.25" ≥ 1 1/4" (ESR-1078 Table 2)                           ✓ exactly
    penetration     1.25" in the rim ≥ 6D = 1.134" (NDS 12.1.4.6)               ✓

**NDS 2018 §12.3**, single shear: D 0.172" root, F_yb 190,600 psi, R_d = 10D + 0.5 = 2.22. Side:
the 8" stack at G 0.42 (SPF, a lower bound for the KDAT SP and the plywood), F_es = 16,600 ×
0.42^1.84 = 3,364.2 psi. Main: the rim at G 0.50 (ESR-1387, equivalent SG for fasteners in the
face), F_em = 16,600 × 0.50^1.84 = 4,636.7 psi, l_m 1.25". R_e = 1.3782, R_t = 0.15625.

| Mode | Working | Z, lb |
|---|---|---|
| Im | D l_m F_em / R_d = 0.172 × 1.25 × 4,636.7 / 2.22 | 449.1 |
| Is | D l_s F_es / R_d, l_s 8.0 | 2,085.2 |
| II | k1 0.35366 × D l_s F_es / R_d | 737.5 |
| IIIm | k2 = −1 + √(2(1 + R_e) + 2F_yb(1 + 2R_e)D²/(3F_em l_m²)) = −1 + √(4.7565 + 1.9491) = 1.58952; k2 D l_m F_em / ((1 + 2R_e) R_d) | **190.0** |
| IIIs | k3 0.86920 × D l_s F_em / ((2 + R_e) R_d) | 739.5 |
| IV | D²/R_d √(2 F_em F_yb / (3(1 + R_e))) | 209.7 |

**Z = 190.0 (IIIm), Z' = 0.70 × 190.0 = 133.0 lb** (C_M 0.70, NDS Table 11.3.3, wet KDAT side
members), authored 133. The TJI backer pair gave 135.

**Spacing, ESR-1078 Table 5, by each member's specific gravity.** The beam and seats are KDAT SP
(G 0.55) and the rim LSL (0.50, read on the stricter side), so every member takes the
**SG > 0.50** column: end 3", in-row 2 5/8", loaded and unloaded edge 1 3/4", rows in line
1 7/8" or 3/4" staggered at half pitch (note 4); rows are spaced on the rim's (main member's)
column. The screw bears up into the beam and seat and down into the rim:

    beam   +0.75 / −4.75    →  −3.000 ≤ z ≤ −1.000
    seat   +0.375 / −5.125  →  −3.375 ≤ z ≤ −1.375
    rim    0 / −11.875      →  −10.125 ≤ z ≤ −1.750
    band   −3.000 … −1.750 = 1 1/4" → rows at −2.000 and −2.750, 1/4" inside each end

Rows staggered by half the in-row spacing, from each beam end: row 1 at 3, 5.625; row 2 at
4.3125, 6.9375; far end 10 − 6.9375 = 3.0625" ✓, which is why the seat is 10". **8 TLOK10 a
door, 24 in all**, unchanged. The rim has no flange, so the 2026-11-18 UNKNOWN is gone.

**Shares.** The spring beam (E' 1.26e6, k = 270,000 × 0.189^1.5 = 22,184.8 lb/in at the eight
stations, 300 lb scanned along it). An independent PyNite model (a beam on vertical springs at
the stations, the load at the engine's worst station and at the ends):

| Door | Load at | Screw forces, lb (station) | Σ | Worst / 133 |
|---|---|---|---|---|
| wide | 41.13" | −33.78 (3.0) · 43.05 (5.625) · 4.61 (4.3125) · 81.61 (6.9375) · −22.06 (60.3125) · 75.52 (57.6875) · 26.71 (59.0) · **124.33 (56.375)** | 300.00 | **0.935** |
| wide | 63.31" (end) | 8.00 · −11.24 · −1.62 · −20.90 · 123.20 · 66.92 · 94.25 · 41.38 | 300.00 | 0.926 |
| entry | 0" (end) | **116.01 (3.0)** · 76.96 · 95.67 · 60.06 · −8.38 · −13.46 · −10.93 · −15.93 | 300.00 | **0.872** |

Σ(F·(x − load)) = 0.000 in each; a ¼" scan finds no worse load. As before, the worst wide case
turns the beam over the far seat and its innermost screw takes the most.

**Not graded: the seat's rotation (owner question, 2026-11-18).** The reaction stands 0.5 + 6.0 +
0.75 = 7.25" off the rim face, so each seat sees about 300 × 7.25 = 2,175 lb-in about its bottom
bearing on the sheathing, resisted by withdrawal of its upper screws in the rim and pull-through
of their heads at the beam face (ESR-1078 Table 3, 1 1/2" side member: W_H 110 lb at G 0.42, the
house's lower bound; 200 lb at the KDAT's SP 0.55; × C_M 0.70 wet, 77 or 140 lb). Withdrawal in the
dry rim is not the weak link (Table 2: 220 lb/in at G 0.50 × 1.25" = 275 lb). A rough couple (the
compression resultant 0.4" over the seat bottom, the rows 2.725" and 1.975" above it, shares
linear in the arm: 2,175 / (2 × 2.725 + 2 × 1.975²/2.725) = 261.6) puts ~260 lb on each top
screw, over either pull-through value; restraint from the beam, the sill fastened on it and the pan is
not credited. The engine reports it UNKNOWN on every door.

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

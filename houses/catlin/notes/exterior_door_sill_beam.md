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
  The top is ripped at 1/4"/ft: 1/32" across 1 1/2". The pan runs level over the buck sill, falls
  across the beam and turns down its face to a 1/2" drip at 7.5"+.
- **Seats.** One stack per end, 4 plies of 2x6 KDAT (sheathing to beam back, 6.0"), 9 1/4" along
  the beam, 5 1/2" tall, top under the 3/8" buck sill (+3/8"), bottom −5 1/8".
- **Wood through the foam.** 2 × 9.25 × 5.5 = **101.75 in²** a door. The wide doors drop from
  11 blocks × 3.5² = 134.75 in² (−24%); the entry *rises* from 7 × 12.25 = 85.75 in² (+19%).
  The foam now runs unbroken between the seats.

## 2. Beam

No.2 SPF wet stands in for KDAT SP (lower bound, as `catlin_truss_engineering.md` §4):
Fb' = 875 × C_F 1.3 = **1,137 psi** (C_M 1.0: Fb·C_F ≤ 1,150; C_D 1.0), Fv' = 135 × 0.97 = **131
psi**, E' = 1.4e6 × 0.90 = **1.26e6 psi**. S = 1.5 × 5.5²/6 = 7.5625 in³, I = 20.797 in⁴,
A = 8.25 in². Span between the seats' screw-group centroids (each 4.59375" in from its end, §3):
63.3125 − 9.1875 = **54.125"**; entry 38.375 − 9.1875 = **29.1875"**. 300 lb point.

| | M = PL/4 | fb / Fb' | fv = 1.5P/A, / Fv' | Δ = PL³/48EI vs 1/8" |
|---|---|---|---|---|
| wide | 4,059.4 lb-in | 536.8 / 1,137 = **0.472** | 54.5 / 131 = **0.416** | **0.0378"** |
| entry | 2,189.1 lb-in | 289.5 / 1,137 = **0.255** | **0.416** | **0.0059"** |

1/8" is the door maker's limit over an unsupported span (Marvin site prep, cited in the review).

## 3. Seat screws, TLOK10

**The main member is the edge TJI, not an LSL rim.** At all three doors the joists run parallel
to the wall, so the edge member is a TJI 230: FS-M-EAST `joist-0-000-0` (PORCH, D-B-SUNKEN's LVL
band plies behind), FS-M-MECH `joist-0-011-0` (ENTRY), FS-S-EAST `joist-0-000-0` (BALCONY). The
LSL rims are at joist ends, on the east and west walls. Each seat's length takes an SPF backer
pair in the web recesses: 2x6 ripped to 31/32", 5 1/2" tall, tight under the 1 1/4" flange.

**Screw fit** (`catlin_truss_engineering.md` §3.1–§3.3: the sheathing is nailed to the edge member,
so it is on the main member's side):

    clamped stack   beam 1.5 + seat 6.0                     = 7.5"
    through         + sheathing 0.5                         = 8.0"
    TLOK10          10", 2" thread (ESR-1078 Table 1A) → plain shank 8.0" ≥ 7.5"   ✓ 0.5"
    thread          8.0" to 10.0": starts at the TJI's face, ends 5/16" short of its far face ✓
    in wood         31/32 outer backer + (2.0 − 1 11/32) inner backer = 1.625" ≥ 1 1/4" ✓
    penetration     2.0" ≥ 6D = 1.134" (NDS 12.1.4.6)                              ✓

ESR-1078 Table 4's lateral values need 5" of main-member penetration and §5.4 leaves NDS
lateral design outside the report, so, as for the retired detail, the house's NDS 12.3 calc is
the lateral basis; the report's 1 1/4" embedded thread and Table 5 spacing are graded as
published.

**NDS 2018 §12.3** (inputs as `exterior_door_structural_mount.md`: D 0.172" root, F_yb 190,600,
G 0.42 every member, F_e 3,364.2 psi, q = 578.65 lb/in, M_y = 161.64 lb-in, R_d 2.22). Main
member wood: [0, 31/32] and [1 11/32, 2.0] past its face (the web a gap).

- IV: h = √(2M_y/q) = 0.7475", inside the outer backer; P = 432.5, Z = 194.8.
- IIIm: h = (y0 − 3/8) − (2.0 − y0) = 2y0 − 2.375. Moments about the hinge,
  q h²/2 − q[(31/32 + h)² − h²]/2 − q[(y0 + h)² − (1 11/32 + h)²]/2 + q[(2.0 + h)² − (y0 + h)²]/2
  = −M_y at y0 = 1.5604", h = 0.7458": 160.9 − 689.6 − 275.5 + 642.6 = −161.6 ✓.
  P = 431.6 lb, **Z = 194.4 (governs)**. Im = q × 1.625/2.22 = 423.6.
- **Z' = 0.70 × 194.4 = 136.1 lb, authored 135** (C_M 0.70, NDS Table 11.3.3).

**Spacing, ESR-1078 Table 5** (SPF, perpendicular to grain): end and in-row 2 5/8", loaded edge
1 3/4", unloaded 1 3/8", 3/4" between staggered rows. The screw bears up into the beam and seat
(loaded edge at their tops) and down into the backer (loaded at its bottom):

    beam   +0.75 / −4.75   →  −3.375 ≤ z ≤ −1.000
    seat   +0.375 / −5.125 →  −3.750 ≤ z ≤ −1.375
    backer −1.25 / −6.75   →  −5.000 ≤ z ≤ −2.625
    band   −3.375 … −2.625 = 3/4" → rows at −2.625 and −3.375, exactly at the minima

Rows staggered by half the in-row spacing, from each beam end: row 1 at 2.625, 5.25; row 2 at
3.9375, 6.5625; far end distance 9.25 − 6.5625 = 2.6875" ✓. The 3/4" is Table 5's staggered value,
which its note 4 allows only at that half-pitch offset; rows in line need 1 3/8". **8 TLOK10 a
door, 24 in all (was 41).** The band is the 2x6 beam's: it has no margin. A 2x8 beam would give
2 3/8".

**The flange decides it (review, 2026-11-18).** The backer's top is the edge TJI's flange
underside. The model reads TJ-4000 p.6's flange band at its thin end, 1 1/4". At its thick end,
1 3/8", the backer sits 1/8" lower and its unloaded edge allows z ≤ −1.375 − 1.375 = −2.75. The
band then shrinks to −3.375 … −2.75 = 5/8", under the staggered 3/4": the top row has only 1 1/4"
to the backer's top. The engine reports this as UNKNOWN, decided by the delivered flange. If
the flange is thick, a 2x8 beam on 7 1/4" seats restores 2 3/8".

**Shares.** The spring beam of the retired detail, E' 1.26e6, k = 270,000 × 0.189^1.5 =
22,185 lb/in, 300 lb scanned along it. An independent PyNite model (the beam on vertical springs
at the eight stations, E' and k as above, the load at the engine's worst station) gives:

| Door | Load at | Screw forces, lb (station) | Σ | Worst / 135 |
|---|---|---|---|---|
| wide | 41.13" | −35.38 (2.625) · 4.19 · 43.83 · 83.58 (6.5625) · **126.29 (56.75)** · 76.04 · 25.82 · −24.37 (60.6875) | 300.00 | **0.936** |
| wide | 63.31" (end) | 7.52 · −1.39 · −10.31 · −19.25 · 43.26 · 67.27 · 92.90 · 120.01 | 300.00 | 0.889 |
| entry | 38.375" (end) | −7.39 · −9.78 · −12.15 · −14.47 · 60.23 · 76.30 · 94.02 · **113.22 (35.75)** | 300.00 | **0.839** |

Σ(F·(x − load)) = 0.000 in each. The worst wide case is not the end: a load inside the span turns
the beam over the far seat and its innermost screw takes the most. The negative shares are the
outer screws holding the beam end down; lateral capacity works both ways.

**Jamb-post variant (rejected, design unchanged).** A girt jamb post's own standoff at the sill is
one 3 1/2" block: a screw needs 2 5/8" of end distance each side (5 1/4"), so the post cannot take
even one screw to Table 5; the beam would also have to run 3 1/2" past each RO edge in front of
the cladding to reach it.

**Open:** TJ-4000 p.28's backer row and nailing are not in the repo, so the backer attachment is
UNKNOWN (`plans/TODO.md`).

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

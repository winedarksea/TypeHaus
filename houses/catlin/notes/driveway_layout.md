# The driveway — hand-worked basis

**House:** catlin
**Structure:** `SL-DW-DRIVE` (`params/driveway.py`) and the `driveway` impervious surface.
**Written:** 2026-09-23; taper and quantities updated 2026-09-30.
**Oracle for:** the `slab:DRIVEWAY_FRC_CLASS5` and `mndot-class-5-base:8.0` takeoff rows and
the C-101 driveway/paving lines; reproduced by `tests/test_catlin_gardens.py`.
**What is asked of the reviewer:** §2's area and §4's joint layout.

---

## 1. Section

`DRIVEWAY_FRC_CLASS5`: 4" EXPOSED_MIX (5,000 psi, 6% air, macro-synthetic fibre 4 pcy, no
mesh) on 8" of MnDOT 3138 Class 5 compacted to 100% standard Proctor, in two lifts. There is
no foam under it. 4" is ACI 332's residential driveway minimum. The walk's section is the
same with a 6" base; the extra 2" is for wheel loads.

## 2. Outline (feet, plan frame)

- `SL-G-FLOOR` runs out to the node line at the door, 67'-2 5/8". (Until 2026-09-23 the
  grade beam `W-GF-N-DR` stood there and its banded face, 67'-2.925", set the edge.)
- K8 joint: 1". So `Y0` = 67 + 3.625/12 = **67.3021**.
- Door jambs x 10'..26' (16'), then a 1:3 taper to x 12'..24' (12') at `Y0 + 6'` = 73.3021,
  then 12' wide to the front lot line at y = 84.5.

| piece | arithmetic | sf |
|---|---|---|
| taper trapezoid | (16 + 12) / 2 × 6.000 | 84.00 |
| 12' run | 12 × (84.5 − 73.3021) = 12 × 11.1979 | 134.38 |
| **total** | | **218.38** |

(The taper area includes the 12 × 6 rectangle plus two ½ × 2 × 6 triangles.)

Concrete at 4": 218.38 / 3 / 27 = **2.70 cy**. Class 5 at 8": 218.38 × 8/12 / 27 =
**5.39 cy** compacted, billed as **218.4 sf** on the `:8.0` row.

## 3. Fall

The slab is modelled flat at −2'-11", 1" under the −2'-10" garage slab so the drive sheds
away from the door. The `driveway` impervious surface falls to −3'-3 1/2" at the lot line:
4.5" over 84.5 − 67.302 = 17.198' (206.4"), so **2.18%**. `code.R401_3_impervious` grades it
against the garage's foundation enclosure, which it abuts.

## 4. Joints

- **K8, at the garage slab edge:** 1" of 40 psi XPS (Foamular 400, ASTM C578 Type VI), topped with
  1/2" of traffic-rated polyurethane sealant. It runs the 16' door width (~16 LF). It is the
  1" gap in the outline and is not an element (see the module docstring).
- **Longitudinal:** one on the centreline, x = 18'. A 12' panel is over ACI 332's
  30 × t = 10' spacing.
- **Transverse sawcuts, ≤ 10' o.c.:** the first at the taper end, y = 73.30, so the taper's
  corners are not re-entrant cracks. The second is at y ≈ 78.90, midway through the 11.20'
  straight run, keeping both straight panels about 5.6' long.
- **East edge, x = 24':** 1/2" isolation to walk A, whose SW corner follows the taper
  (notes/sidewalk_layout.md §2a).

## 5. Paving cap (C-101, display only)

Ord. 23-43 caps driveway and parking paving at the lesser of 15% of the lot and 1,000 sf.
15% of 6,650 sf = **997.5 sf** governs. The drive plus the three `kind="pad"` surfaces is
218.4 + 25 = **243.4 sf**, 3.7% of the lot, under a quarter of the cap. No check grades it.

## Sources

- ACI 332-20, residential concrete: driveway thickness and joint spacing.
- MnDOT Standard Specifications, 3138 (aggregate base, Class 5).
- Saint Paul Ord. 23-43: front-yard driveway width and paving cap.

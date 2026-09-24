# The driveway — hand-worked basis

**House:** catlin
**Structure:** `SL-DW-DRIVE` (`params/driveway.py`) and the `driveway` impervious surface.
**Written:** 2026-09-23, by hand from the outline.
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
- Door jambs x 10'..26' (16'), then a 45° flare to x 12'..24' (12') at `Y0 + 2'` = 69.3021,
  then 12' wide to the front lot line at y = 84.5.

| piece | arithmetic | sf |
|---|---|---|
| flare trapezoid | (16 + 12) / 2 × 2.000 | 28.00 |
| 12' run | 12 × (84.5 − 69.3021) = 12 × 15.1979 | 182.38 |
| **total** | | **210.38** |

(Read the trapezoid as a 12 × 2 rectangle, 24.00 sf, plus two ½ · 2 · 2 triangles, 4.00 sf.)

Concrete at 4": 210.38 / 3 / 27 = **2.60 cy**. Class 5 at 8": 210.38 × 8/12 / 27 =
**5.19 cy** compacted, billed as **210.4 sf** on the `:8.0` row.

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
- **Transverse sawcuts, ≤ 10' o.c.:** the first on the flare line, y = 69.30, so the flare's
  corners are not re-entrant cracks. The second is at y ≈ 77.0, halving the 15.20' run to
  7.6' panels, each about 6 × 7.6.
- **East edge, x = 24':** 1/2" isolation to walk A, whose SW corner follows the flare
  (notes/sidewalk_layout.md §2a).

## 5. Paving cap (C-101, display only)

Ord. 23-43 caps driveway and parking paving at the lesser of 15% of the lot and 1,000 sf.
15% of 6,650 sf = **997.5 sf** governs. The drive plus the three `kind="pad"` surfaces is
210 + 25 = **235 sf**, 3.5% of the lot, under a quarter of the cap. No check grades it.

## Sources

- ACI 332-20, residential concrete: driveway thickness and joint spacing.
- MnDOT Standard Specifications, 3138 (aggregate base, Class 5).
- Saint Paul Ord. 23-43: front-yard driveway width and paving cap.

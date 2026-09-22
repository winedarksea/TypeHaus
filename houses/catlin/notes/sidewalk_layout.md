# The sidewalk and its planting pockets — hand-worked basis

**House:** catlin
**Structure:** `SL-WK-A`..`-E` (`params/landscape_walk.py`), their `FO-WK-*` pockets,
`PB-WK-POCKETS`, and the five `walk *` impervious surfaces.
**Written:** 2026-09-21, by hand from the leg rectangles.
**Oracle for:** the `slab:SIDEWALK_FRC_CLASS5` and `mndot-class-5-base` takeoff rows and
`code.R401_3_impervious` on the five walk surfaces; reproduced by
`tests/test_catlin_gardens.py`.
**What is asked of the reviewer:** §2's areas and §3's pocket count.

> ⚠ Every slab is modelled FLAT at its high edge, -2'-9" (E: -2'-8", flush with
> SL-SG-STAIRPAD). The fall is on the impervious surfaces only. Two joints are therefore
> not flush in the field and are set by the finisher: walk A's far edge meets the driveway
> about 2" high, and walk C meets the paver approach's -3'-0 1/2" east edge about 3" high.
> Grade both by hand at the pour; neither is modelled.

---

## 1. Section

Full: 12 band | 16 pocket | 36 walk | 16 pocket | 12 band = 92" (legs A, B).
One-sided: 36 walk | 16 pocket | 12 band = 64", walk against the house (leg D) — the house
to lot line is 6'-4", so 92" does not fit east of the house anywhere; it does not fit south
of it either, where the court and the porch stair own the ground. C and E are walk only.

Pockets are 16" sonotube voids, drawn as 16-gons (1.3605 sf each), centred 20" in from
each edge (44" off the house on D), 2'-0" in from each leg end and 4'-0" o.c.; control
joints fall on the same stations.

## 2. Legs (feet, plan frame)

| leg | outline | gross sf | pockets | net sf |
|---|---|---|---|---|
| A garage north | x 24.04..37.78 × y 67.33..75.00 | 13.74 × 7.67 = 105.3 | 6 | 97.2 |
| B garage east | x 30.11..37.78 × y 43.02..67.33 | 7.67 × 24.31 = 186.4 | 12 | 170.1 |
| C landing connector | x 30.04..42.04 × y 39.60..43.02, less the 0.50 × 1.08 notch at PT-BW-RNE | 41.04 − 0.54 = 40.5 | 0 | 40.5 |
| D house east | x 36.70..42.04 × y −9.00..39.60 | 5.33 × 48.60 = 259.2 | 10 | 245.6 |
| E stair joint | x 35.29..36.66 × y −9.00..−6.00 | 1.37 × 3.00 = 4.1 | 0 | 4.1 |
| **total** | | **595.5** | **28** | **557.4** |

Concrete at 4": 557.4 / 3 / 27 = **6.88 cy**. Class 5 at 6" bills by the net slab area,
**557.4 sf**. Impervious area counts the GROSS 595.5 sf — the pockets are not subtracted,
which is conservative for the coverage table.

## 3. Pocket stations

- **A** (along x, rows y=69.00 and 73.33): x = 26.04, 30.04, 34.04 → 6, less (30.04, 69.00),
  which sits 1.30' from the leader pocket at TR-G-LEADER-E's foot (31.27, 68.49) against a
  2.0' clear (two radii + 8" web) → 5, plus the leader pocket = **6**.
- **B** (along y, columns x=31.78 and 36.11): y = 45.02 … 65.02 → 6 stations × 2 = **12**.
- **D** (along y, column x=40.37): y = −7, −3, 1, 5, 9, 13, 17, 21, 25, 29, 33, 37 → 12,
  less 13, 17, 21 inside the retired patio's y 10'..22' (± 8") → 9, plus the leader pocket
  at TR-RF-LEADER-E's foot (37.50, 35.50) = **10**.

28 pockets cycle Calamintha, Allium, Sporobolus, Salvia in A-B-D order: **7 of each**.

## 4. Fall (R401.3: 2% within 10' of the foundation)

| surface | near → far | run R401.3 reads | slope |
|---|---|---|---|
| walk A | −33" → −36" | 10.9' | 2.3% |
| walk B | −33" → −36" | outside the 10' band | — |
| walk C | −33" → −36" | 12.0' | 2.1% |
| walk D | −33" → −35" | 7.2' | 2.3% |
| walk E | −32" → −32.75" | 3.0' | 2.1% |

## 5. What is NOT graded here

Joint layout beyond the pocket stations, the pour sequence, the concrete's fibre dosage
(EXPOSED_MIX's 4 pcy macro-synthetic), and the two non-flush joints in the warning above.

## Sources

- IRC 2018 R401.3 — drainage; 2% for impervious surfaces within 10 ft.
- MnDOT Standard Specifications, 3138 (aggregate base, Class 5).

# Finished floor area — hand-worked basis

**House:** catlin
**Written:** 2026-11-11, by hand, from element dimensions.
**Oracle for:** `resolve/finished_area.py`, reproduced by `tests/test_finished_area.py`.
**Why:** the owner wants RM-A-EAST-UNFIN and RM-A-POCKET kept out of the taxed and quoted
square footage. Both stay **conditioned**: they sit inside the hot roof, behind uninsulated
partitions, and hold the air handler, ducts and ERV manifold, so the energy code calls them
indirectly conditioned (`notes/conditioned_floor_area.md` is unchanged). They leave the
*finished* area instead, which is what an assessor counts (ANSI Z765 style).

## 1. Rule

Start from each storey's CFA region (structural face, stair wells out). Cut every room with
no floor finish AND `unpainted=True` (only RM-A-EAST-UNFIN and RM-A-POCKET). Cut the floor
under 5'-0" of clear head. A storey 2' or more under the grade datum is below grade.

The one deliberate difference from Z765 is the measuring line: Z765 measures to the exterior
finish face; this measures to the structural face so it lines up with the CFA.

## 2. The attic strip with 5'-0" of head

RF-HOUSE's deck plane: eave 251.902" at x = −7.25", ridge 363.527" at x = 216", so the slope
is 0.5. Clear head is measured off the storey datum (240", top of joists, the line R304.3 and
`room_head_limited_area_m2` use) to the roof underside, which is the plane less the 13.277"
plumb structure depth:

    240 + 60 + 13.277 = 313.277 = 251.902 + 0.5 (x + 7.25)   ->  x = 115.5"
    mirrored: 432 − 115.5 = 316.5"
    strip x 115.5..316.5 (201") x y 0..432"  = 86,832 in2 = 603.00 sf

(From the subfloor top it would be the guide's 9'-9", 117". The datum reading is 1 1/2"
generous per side and matches the code check.)

## 3. What the strip loses

| cut | inside the strip | in2 | sf |
|---|---|---|---|
| FO-A-HALL (stair well) | 96 x 155 | 14,880.0 | 103.33 |
| FO-A-STAIR (stair well) | x 256.375..316.5 = 60.125 x 36.125 | 2,172.0 | 15.08 |
| RM-A-EAST-UNFIN | 45.5 x 315.25 + 51.75 x 304.625 | 30,108.2 | 209.08 |
| RM-A-POCKET | x 115.5..117.75 = 2.25 x 155.25 | 349.3 | 2.43 |

None of the cuts overlap: EAST-UNFIN starts at y = 110.25", north of FO-A-STAIR's 105.75",
and the pocket stops at x = 117.75", short of FO-A-HALL's 120". The chases stay as floor.

    attic finished = 603.00 − 103.33 − 15.08 − 209.08 − 2.43 = 273.08 sf

Check: attic CFA 1,150.27 − unfinished clear faces (444.61 + 120.48 = 565.09) − 273.08
= 312.10 sf of finished floor under 5'-0".

## 4. The house

No roof comes within 5'-0" of the main, second or basement floors, and none of their rooms
is unfinished (the mechanical rooms all carry a floor finish), so each keeps its CFA row.
Grade is −34" (2'-10" under main): basement −109.44 + 23.62 = −85.8 ≤ −34 is below grade;
main 0 + 23.62 > −34 is not.

| storey | CFA | finished | grade |
|---|---|---|---|
| basement | 1,296.00 | 1,296.00 | below |
| main | 1,226.47 | 1,226.47 | above |
| second | 1,225.59 | 1,225.59 | above |
| attic | 1,150.27 | 273.08 | above |
| **total** | **4,898.33** | **4,021.1** | 2,725.1 above + 1,296.0 below |

The engine reports 273.1 attic and 4,021.1 total.

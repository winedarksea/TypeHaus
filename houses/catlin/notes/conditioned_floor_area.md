# Conditioned floor area — hand-worked basis (2026-10-31)

The oracle for `resolve/conditioned_area.py` and for the MN 1322 R403.5 rate that
`code.N1103_6_whole_house_ventilation` grades. Pinned by `test_whole_house_ventilation.py`;
the method itself by `test_conditioned_floor_area.py` (a synthetic house, same rules).

## 1. The rule (owner, 2026-10-31)

- "Conditioned" includes the basement. Measure each conditioned storey **to the outer face
  of the structure**: studs plus sheathing on a framed wall, the concrete on a foundation
  wall. The 4" ccSPF, the vent gap, the girts, the cladding and the basement's XPS/EPS are
  outboard of that line and are not floor area.
- A volume counts **once, at its lowest floor**. A stair well or an open-to-roof hall is
  deducted on the storey whose deck it is cut in. A chase is decked over or boxed and stays
  floor; so does the tub-deck hole (`FO-M-TUBDK`, the tub stands on it).
- Excluded entirely: the garage (`RM-GARAGE`, `conditioned=False`), the north-entry deck,
  canopy and landing, the sunken garden, porch and balcony, every deck. None is inside the
  house's 36' x 36' footprint, and none is a conditioned Room.

## 2. The structural lines, read off the model

| storey | west / east | south / north | what stands on the line |
|---|---|---|---|
| basement | x = 0 / 36'-0" | y = 0 / 36'-0" | outer face of the 8"/12" concrete (`W-B-W1` 0-8", `W-B-E1` 420-432"); `W-B-S2-FR`/`-S3-FR` sheathing at y = 0; XPS/EPS outboard to y = -6" |
| main, second | x = 0 / 36'-0" | y = 0 / 36'-0" | sheathing outer face (`W-M-S1` sheathing 0-1/2", studs 1/2"-6"); foam to -4", cladding to -7 1/4" |
| attic | x = 0 / 36'-0" | y = 0 / 36'-0" | gables: sheathing outer face (`W-A-S1`, `W-A-N1`). E/W: the rafter plates sit at 1/2"-6"; the floor runs to the second-storey sheathing they bear on (`W-S-E1` sheathing 431 1/2"-432") |

Each storey is therefore 36'-0" x 36'-0" = **1,296.00 sf** gross. (The 1/2" attic strip
under the plates is 2 x 36' x 1/2" / 12 = 3.0 sf, 0.06 cfm.)

## 3. Deductions

| storey | opening | x | y | size | sf |
|---|---|---|---|---|---|
| main | `FO-M-STAIR` (basement stair) | 10'-3 1/4" .. 17'-6" | 26'-0 3/8" .. 35'-4 7/8" | 86 3/4" x 112 1/2" | **67.773** |
| second | `FO-S-STAIR` (main stair) | 10'-3 1/8" .. 17'-8 3/4" | 26'-0 3/8" .. 35'-5 1/2" | 89 5/8" x 113 1/8" | **70.409** |
| attic | `FO-A-STAIR` (second-to-attic flight) | 21'-4 3/8" .. 35'-5 3/8" | 5'-9 5/8" .. 8'-9 3/4" | 169" x 36 1/8" | **42.397** |
| attic | `FO-A-HALL` (well + hall open to the roof) | 10'-0" .. 18'-0" | 22'-6 3/8" .. 35'-5 3/8" | 96" x 155" | **103.333** |

The basement has no well: it is the lowest floor under every stair.

## 4. CFA

| storey | gross | deducted | CFA (sf) |
|---|---|---|---|
| basement | 1,296.000 | 0 | 1,296.000 |
| main | 1,296.000 | 67.773 | 1,228.227 |
| second | 1,296.000 | 70.409 | 1,225.591 |
| attic | 1,296.000 | 145.730 | 1,150.270 |
| **total** | | | **4,900.088** |

The engine reports 1,296 / 1,228 / 1,226 / 1,150, total 4,900.

## 5. The R403.5 rate

Six bedrooms (`RM-M-BED`, `RM-S-BED1`, `-BED2`, `-BED3`, `RM-S-SUITE`, `RM-A-STUDIO`):

    TVR = 0.02 x 4,900.088 + 15 x (6 + 1) = 98.002 + 105 = 203.0 cfm
    CVR = max(203.0 / 2, 40)                                 = 101.5 cfm

Against the ERV's **delivered 203.9 cfm** (`notes/erv_static_budget.md` §10.6, extract side
at 0.441 in. w.g. off the Broan curve): **+0.9 cfm, PASS.** The rated 210 is not what is
graded.

## 6. Sensitivities (none is the graded figure)

| reading | area (sf) | TVR (cfm) | vs 203.9 delivered |
|---|---|---|---|
| finish-face room sum (graded before 2026-10-31) | 4,479 | 194.6 | +9.4 |
| **structural face, wells once (this note)** | **4,900** | **203.0** | **+0.9** |
| same, chases deducted too (main 20.32, second 5.24, attic 6.71) | 4,868 | 202.4 | +1.6 |
| wall centrelines (the 2026-09-09 "205") | ~5,000 | ~205 | -1.1 |
| exterior dimensions, cladding to cladding | 5,455 | 214.1 | -10.2 |

0.9 cfm is the size of the static budget's own chart-reading error (§10.1: the BD8 read
alone is +/-0.5 cfm), and the graded path is conservative (the worst series path is nearer
204.7). Commissioning with a low-flow hood (§8) is still the check that closes it.

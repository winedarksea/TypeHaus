# The bluestem grid and the basin beds — hand-worked counts

**House:** catlin
**Structure:** `PB-S-GRID`, `PB-RG-SLOPE-W`/`-E`, `PB-RG-FLOOR` (`params/landscape_gardens.py`).
**Written:** 2026-09-21, by hand.
**Oracle for:** `resolve/landscape.py::grid_cells` and `accent_type`, and the `planting`
takeoff table; reproduced by `tests/test_catlin_gardens.py`.
**What is asked of the reviewer:** the accent cell list in §2.

> ⚠ 'Moonbeam' is rhizomatous and drifts to about 24" in a 15" cell. Divide it every 3-4
> years or the grid blurs at exactly the accents meant to punctuate it.

---

## 1. Rule

Square grid at spacing s, inset d (default s/2): columns = ⌊(W − 2d)/s⌋ + 1, rows likewise.
The lattice is centred in the bed's bounding box: the slack splits evenly between edges.
Cell (i, j) is an accent when (a·i + b·j) mod `every` = 0; its type is
`type_refs[(i + j) mod n]`.

## 2. PB-S-GRID — south of W-RG-BLOCK

x −6'..42' (W 48'), y −47'-6"..−34'-6" (H 13'), s = 15" = 1.25', ground −3'-4". The bed
stops 1'-0" inside the west, east and rear lot lines.
Columns ⌊46.75/1.25⌋ + 1 = 38; rows ⌊11.75/1.25⌋ + 1 = 10; **380 cells**.

Accents: (i + 3j) mod 9 = 0, i in 0..37. Per row the residue −3j mod 9 cycles 0, 6, 3:
residue 0 takes i = 0, 9, 18, 27, 36 (5), residues 6 and 3 take 4 each. Rows j = 0..9 take
5, 4, 4, 5, 4, 4, 5, 4, 4, 5 = **44 accents** (one in 8.6).

Types `(M, M, M, A, M, M, M, C)[(i + j) mod 8]`:
- Angelina (index 3): (27,0), (0,3), (15,4), (30,5), (3,8), (18,9) → **6**
- Caramel (index 7): (6,1), (21,2), (36,3), (9,6), (24,7) → **5**
- Moonbeam: 44 − 11 = **33**
- 'Jazz': 380 − 44 = **336**

## 3. The basin beds (15" grid)

| bed | outline | cols × rows | cells |
|---|---|---|---|
| PB-RG-SLOPE-W | x −6..−4 × y 47..82 | 1 × ⌊33.75/1.25⌋+1 = 28 | 28 'Jazz', row x = −5 |
| PB-RG-SLOPE-E | x −2.75..−0.75 × y 47..82 | 1 × 28 | 28 'Jazz', row x = −1.75 |
| PB-RG-FLOOR | x −4..−2.75 × y 49..80, d = 6" | 1 × ⌊30/1.25⌋+1 = 25 | 25, row x = −3.375 |

Each row sits on its bed's centre line (2026-11-20; before, the lattice struck from the
bbox corner and the 3" widening left the rows 1.5"–4.5" west). PB-RGE-* mirror these
about x = 18'.

Floor accents: (i + 2j) mod 5 = 0 with i = 0 → j = 0, 5, 10, 15, 20; type
`(IRIS, MILKWEED)[j mod 2]` → iris at 0, 10, 20 (**3**), milkweed at 5, 15 (**2**). The
other 20 cells take the field mix `(OCTOBER SKY, NORTHWIND)[j mod 2]`: even j (2, 4, 6, 8,
12, 14, 16, 18, 22, 24) 'October Sky' **10**, odd j 'Northwind' **10**.

## 4. Totals

Two basins: 'Jazz' 336 + 4 × 28 = **448**; Moonbeam 33; Angelina 6; Caramel 5;
'October Sky' 20; 'Northwind' 20; iris 6; milkweed 4. The whole-house count, pockets,
apples and terrace included, is `test_planting_counts`.

## 5. What is NOT graded here

Plant health, spacing against mature spread (a 15" grid of 18" bluestem touches by design),
and the zone-1/zone-3 moisture split, which is the planting designer's.

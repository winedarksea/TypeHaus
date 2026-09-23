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

Square grid at spacing s, inset s/2: columns = ⌊(W − s)/s⌋ + 1, rows = ⌊(H − s)/s⌋ + 1.
Cell (i, j) is an accent when (a·i + b·j) mod `every` = 0; its type is
`type_refs[(i + j) mod n]`.

## 2. PB-S-GRID — south of W-RG-BLOCK

x 4'..32' (W 28'), y −46'..−34'-6" (H 11.5'), s = 15" = 1.25', ground −3'-4".
Columns ⌊26.75/1.25⌋ + 1 = 22; rows ⌊10.25/1.25⌋ + 1 = 9; **198 cells**.

Accents: (i + 3j) mod 9 = 0, i in 0..21. Per row the residue −3j mod 9 cycles 0, 6, 3, so
rows take 3, 2, 3, 3, 2, 3, 3, 2, 3 = **24 accents** (one in 8.25).

Types `(M, M, M, A, M, M, M, C)[(i + j) mod 8]`:
- Angelina (index 3): (0,3), (15,4), (3,8) → **3**
- Caramel (index 7): (6,1), (21,2), (9,6) → **3**
- Moonbeam: 24 − 6 = **18**
- 'Jazz': 198 − 24 = **174**

## 3. The basin beds (15" grid)

| bed | outline | cols × rows | cells |
|---|---|---|---|
| PB-RG-SLOPE-W | x −6..−4.5 × y 47..82 | 1 × ⌊33.75/1.25⌋+1 = 28 | 28 'Jazz' |
| PB-RG-SLOPE-E | x −2.5..−1 × y 47..82 | 1 × 28 | 28 'Jazz' |
| PB-RG-FLOOR | x −4.5..−2.5 × y 48.5..80.5 | 1 × ⌊30.75/1.25⌋+1 = 25 | 25 |

Floor accents: (i + 2j) mod 5 = 0 with i = 0 → j = 0, 5, 10, 15, 20; type
`(IRIS, MILKWEED)[j mod 2]` → iris at 0, 10, 20 (**3**), milkweed at 5, 15 (**2**). The
other 20 cells take the field mix `(OCTOBER SKY, NORTHWIND)[j mod 2]`: even j (2, 4, 6, 8,
12, 14, 16, 18, 22, 24) 'October Sky' **10**, odd j 'Northwind' **10**.

## 4. Totals

'Jazz' 174 + 56 = **230**; Moonbeam 18; Angelina 3; Caramel 3; 'October Sky' 10;
'Northwind' 10; iris 3; milkweed 2. With 28 pockets and 3 apples: **310 plants**.

## 5. What is NOT graded here

Plant health, spacing against mature spread (a 15" grid of 18" bluestem touches by design),
and the zone-1/zone-3 moisture split, which is the planting designer's.

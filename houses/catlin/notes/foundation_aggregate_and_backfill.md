# Foundation aggregate, the wall drain column and the over-dig — hand-worked basis

**House:** catlin
**Structure:** `FB-B-*` (house beds) and `FB-SG-*` (court beds), their `wall_column`s, the
court rim base course under `SL-SG-FLOOR`, and `EX-HOUSE` (`plan/earthwork.py`).
**Written:** 2026-10-28, by hand, before the takeoff test it oracles was pinned.
**Oracle for:** `resolve/wall_column.py`, `resolve/excavation.py` and `takeoff/excavation.py`,
reported by the takeoff's `[excavation]` rows and graded by `code.R405_1_foundation_drainage`;
reproduced by `tests/test_earthwork.py`.
**Companions:** `notes/sunken_garden_court_free_body.md` — the court's drained stone as a
STRUCTURAL relief; `notes/basement_to_framed_wall_detail.md` — why there is no dimple mat.
**What is asked of the reviewer:** whether §1's verdict on the footing bed holds, and the
arithmetic of §6 (the column) and §7 (the dig).

> ⚠ The side slope (1:1, OSHA Type B), the swell and the shrink are PRESUMED for a clay till.
> The structure is graded on a presumed `GM` (Group I, well drained) soil; the infiltration
> on HSG D till. Those disagree, and this backfill is designed for the till. BLD-12, the
> soils report, settles all of it.
>
> ⚠ A 1:1 slope from the court's -14'-7 7/16" soakaway floor reaches ~16' past the court
> wall at grade, and ~11' past the house. On a 50'-wide lot that is past the side lot lines.
> Expect a steeper cut (Type A, 3/4:1), shoring, or a negotiated temporary easement; the
> modelled quantities are the laid-back case.

---

## 1. The footing bed — keep as designed

| term | working | value |
|---|---|---|
| drained #57, k | published range for open-graded crushed stone, dry to damp | 0.4-0.7 W/m·K |
| moist glacial till, k | published range | 1.2-1.8 W/m·K |
| 7" bed as resistance | 0.178 m / 0.4..0.7 | R(SI) 0.25-0.44 = **R-1.4 to R-2.5 ft²·°F·h/Btu, say R-1 to R-1.5 effective** |
| the clay it replaces | 0.178 m / 1.5 | R(SI) 0.12 = **R-0.7, ~R-0.4 effective** |
| saturated #57, k | water fills the voids | 1.8-2+ W/m·K — **no better than clay** |

"Slight" is the right word. The benefit exists only while the stone is drained: the bed-bottom
tile and `SM-B-RADON` are what earn it, which is why Form-A-Drain was rejected (DESIGN-LOG).
Air convection in #57 is negligible at this size — a porous Rayleigh number of about 1 against
the ~40 onset — as long as the stone is capped and never vented to outdoor air.

The larger real benefits are not thermal: a **capillary break** (rise of inches in stone,
about 20 ft in clay), **frost-heave immunity** (non-frost-susceptible gradation), and a
**stiff working surface**. Stone gets **no `r_per_inch`**: code credits no aggregate, and the
value would leak into the energy checks.

## 2. Wording: seated, not Proctor-compacted

Open-graded #57 is **seated** with a vibratory plate in ≤8" lifts. It is not compacted to a
Proctor density and no density test applies. Before any stone: **proof-roll the native
subgrade**; **over-excavate soft spots and replace them with #57**. `capillary-break-stone`'s
name and the bed comments now say "consolidated/seated"; `prices.toml` says the same.

## 3. Under the slabs

Basement and garage: 4" #57, 10-mil poly, 2" XPS (basement). That meets IRC R506.2.2 and is
the gas-permeable material Minn. R. 1303.2402 subp. 1 requires ("A gas-permeable material
shall be placed on the prepared subgrade under all floor systems" — re-read 2026-10-28; the
rule names no aggregate depth). The court rim gains 4" of #57 (§6c).

## 4. Backfill practice (Twin Cities geotechnical reports, GBA, BSC)

A free-draining zone against the wall; a clay or topsoil cap of about 12"; **no backfill until
the main deck braces the wall tops (IRC R404.1.7)** — a schedule matter, in `tasks.toml`;
lifts ≤8"; only light plates within ~3' of the membrane and XPS. Taking the column to 12"
under grade also keeps frost-susceptible clay off the foam and coating in the frost zone. The
cap falls ≥6" in 10' away from the house (R401.3).

## 5. IRC R405.1 geometry

Stone ≥12" beyond the footing's outside edge, ≥6" above its top, under a filter membrane;
the pipe on ≥2" of stone with ≥6" over it.

| wall | footing past the foam | column width needed | authored |
|---|---|---|---|
| BASEMENT_8 (N, W) | 20" footing on a 12 1/8" band: (20 - 12.19)/2 = 3.9" | 12 + 3.9 = 15.9" | **16"** |
| BASEMENT_12 (E) | (20 - 16.19)/2 = 1.9" | 13.9" | 16" |

**The plan's 12" column did not reach R405.1's 12" past the footing edge** on the
BASEMENT_8 walls (8.1"), so the house columns are 16" wide; the code check reads 12.09" on
N1-N4/W1/W2. The court's 12" columns stand on their heels and are outside R405.1's scope
(they enclose no below-grade space).

The tile: the model's invert sits 2" over the bed floor since 2026-10-28 (`PIPE_BEDDING_M`).
The derived tile band straddles the bed edge; physically the EXTERIOR run lies in the column
foot, with the column as its cover — a remark, not a change to the tile path.

## 6. The drain column, by hand

Elevations: house excavation floor -124 7/16", footing top -109 7/16"; tops 12" under each
wall's strip grade: E, W, N1, S1 -48"; N2-N4 -52"; S4 -49". Main column heights (from the
floor): 76.44" = 6.370', 72.44" = 6.037', 75.44" = 6.287'. Ledge heights (from the footing
top): 61.44" = 5.120', 57.44" = 4.787', 60.44" = 5.037'.

a. **House, 16" (1.333') wide** off the foam face (x/y -4.19"..436.19"); outside corners go
to the first bed by uid; over the 1.9"/3.9" footing ledge the stone starts on the footing.

| bed | main plan (in²) | ledge plan (in²) | working | cf |
|---|---|---|---|---|
| E1 | 16 x 236.19 - 1.9 x 216 = 3368.6 | 1.9 x 216 = 410.4 | 23.39 x 6.370 + 2.85 x 5.120 | 163.6 |
| E2 | same (NE corner) | same | | 163.6 |
| N1 | 220.19 x 16 - 216 x 3.9 = 2680.6 | 842.4 | 18.62 x 6.370 + 5.85 x 5.120 | 148.5 |
| N2 | 96 x 12.1 = 1161.6 | 96 x 3.9 = 374.4 | 8.07 x 6.037 + 2.60 x 4.787 | 61.2 |
| N3 | half of N2 | | | 30.6 |
| N4 | 76.19 x 16 - 72 x 3.9 = 938.2 | 280.8 | 6.515 x 6.037 + 1.95 x 4.787 | 48.7 |
| W1 | 16 x 236.19 - 842.4 = 2936.6 | 842.4 | 20.39 x 6.370 + 5.85 x 5.120 | 159.9 |
| W2 | 220.19 x 16 - 842.4 = 2680.6 | 842.4 | as N1 | 148.5 |
| S1 | 86.19 x 16 + 35.69 x 2.5 = 1468.3 | over FT-SG-W1's heel: 35.69 x 13.5 + 16 x 1.96 = 513.2 | 10.20 x 6.370 + 3.564 x 5.120 | 83.2 |
| S4 | 70.19 x 16 + 89.2 = 1212.3 (SE corner is E1's) | 513.2 | 8.42 x 6.287 + 3.564 x 5.037 | 70.9 |

b. **Court, 12" wide on the heels**, from the heel top -109 7/16" to 12" under each wall's
strip grade, like the house: W -48" (5.120'), E -49" (5.037'), S -52" (4.787').
W2: 12 x 208.31 = 2499.7 in² = 17.36 SF x 5.120 = 88.9 cf; E2 17.36 x 5.037 = 87.4 cf;
S: 228.62 x 12 = 19.05 SF x 4.787 = 91.2 cf. (Authored first as 7'-0" off the bed top, the
top sat at -37 7/16": inside the cap on W and E, and 2 1/2" ABOVE the S wall's -40" grade.
`integrity.excavation` now refuses a column that rises into the cap.)

**Total: 1,346 cf = 49.9 cy of #57** (house 1,079 cf, court 268 cf). The two retired
allowances priced 18.6 + 13.6 = 32.2 cy; the modelled column is ~18 cy more, from the 16"
width, the drop to the excavation floor and the column up to 12" under grade.

c. **Court rim base course:** 94 SF net x 4/12 = 31 cf = **1.2 cy**, billed with the other
`capillary-break-stone` in `[envelope_layers]`.

d. **Geotextile**, soil-side face x the column's full height, plus the top:

| bed | soil face (in) | working | SF |
|---|---|---|---|
| E1, E2, W1 | 236.19 + 16 = 252.19 | 21.02 x 6.370 + 26.24 | 160.1 each |
| N1, W2 | 220.19 | 18.35 x 6.370 + 24.47 | 141.4 each |
| N2 / N3 / N4 | 96 / 48 / 76.19 | x 6.037 + top 10.67 / 5.33 / 8.47 | 59.0 / 29.5 / 46.8 |
| S1 | 105.88 + 16 + 1.96 + 16 = 139.84 | 11.65 x 6.370 + 13.78 | 88.0 |
| S4 | 89.88 + 1.96 + 16 = 107.84 | 8.99 x 6.287 + 12.0 | 68.5 |
| W2 / E2 (court) | 208.31 + 12 + 12 = 232.31 | 19.36 x 5.120 / 5.037 + 17.36 | 116.5 / 114.9 |
| S (court) | 228.62 | 19.05 x 4.787 + 19.05 | 110.2 |

**Total: 1,396 SF.**

## 7. The over-dig, by hand

Working space 2'-0" off the column's outer face (off the bed edge in the court, whose beds
reach 35.69" = 2.974' past the court wall), then 1:1. At height h over a bed's floor the
dig reaches d = 1.333 + 2 + h (house) or 2.974 + 2 + h (court) past the outline. Each side
stops at its own strip grade (§6; court W -36", E -37", S -40"). Integrated in 1" levels:

| piece | working | cf |
|---|---|---|
| perimeter ring | Σ sides L·d + corners d², less the house-S x court-W/E overlap, z from each floor to its top | 18,447 |
| house interior | 1296 SF x 9.5/12 (stone to slab) + 1346.8 SF x 75.44/12 (outline to grade) + sump 2.25 x 1.5 | 9,496 |
| court interior | 524.1 SF x 75.44/12 + 442 SF x 7.5/12 (rim + stone) + 121 SF x 10.5/12 (field) | 3,677 |
| beds below the interiors | house 291.8 SF x 5.5/12 + 49.8 SF x 9.5/12; court inner parts 42.04 x 2 x 46.5/12 + (46.3 x 2 + 102.1 + 33) x 58.5/12 - 11 x 10.5/12 | 1,599 |
| **cut (bank)** | | **33,220 = 1,230 cy** |

Fill = ring less what stands in it: columns 1,346; court beds and footings outside the outline
(W1/E1 31.06 SF x 4.5' x 2 = 279.5, W2/E2 34.2 SF x 5.5' x 2 = 376.2, S 106.2 SF x 5.5' =
584.3) 1,240; house bed/footing overhang 29.1 SF x 1.25' = 36; RG walls and beds, terrace
fill, piers and walk bases ~195. **Fill 18,447 - 2,817 = 15,630 cf = 579 cy.**

Cap = the ring's top 12" under each side's grade, 3,083 cf, less walks, RG walls, terrace
fill and pads in that band (~364; every column stops under it): **2,719 cf = 100.7 cy**.
Native = 15,630 - 2,719 = 12,911 cf = 478 cy; **backfill placed = native + column = 478 +
49.9 = 528 cy**.

Haul-off: spoil for the fill 15,630 / (1 - 0.15) = 18,388 cf bank; (33,220 - 18,388) x 1.30
= **19,282 cf = 714 cy loose**, ~50 tandem loads.

**Against the model** (cut 1,246, fill 577, backfill 513, cap 114.2, haul 738 cy). The FILL
agrees to 0.3% (15,581 cf against 15,630); what differs is how much is dug and how the fill
splits between cap and native, and both have one cause. The model digs each bed's slope as
its own mitred cone, topped at THAT bed's strip grade, and unions them; this hand ring gives
each side its own strip. Where a -36" side meets a -40" one (N1/W1 against N2-N4; the court
W/E against S), the higher side's cone wraps the corner and is dug up to -36" over ground at
-40" — 114 cf of it lies over the lower side's own strip — and the lower side's cap, which
starts 4" deeper, wraps back over the higher side's native. So:
- **cut +1.3%** (gross ring 18,818 cf against 18,447), and **haul +3.3%**, which is that
  difference x 1.30 swell with the fill unchanged;
- **cap +13%** (gross cap band 3,611 cf against 3,083, less 529 cf of obstacles in the band
  against ~364), native and so **backfill -2.9%** by the same yards.
It is a known approximation of a flat per-side grade, not a billing error: ~13 cy moves
between two placement rows priced alike. A cap that followed a graded surface would close
it, and would need the site's grade as a surface rather than as stations.

## 8. What is NOT graded here

The slope's stability (no soils report); shoring; the lot-line conflict above; the garage
trench and the north-entry pier holes (in the residual allowance); the 4" PVC tile's own
bedding beyond the 2" seat; dewatering.

## Sources

- IRC 2018 R405.1 — foundation drainage: 12" beyond the footing, 6" above, filter membrane.
- IRC 2018 R404.1.7 — backfill only after the wall is braced or the floor is in place.
- IRC 2018 R401.3 — grade falls 6" in the first 10'.
- IRC 2018 R506.2.2 — the 4" base course under a slab-on-ground.
- Minn. R. 1303.2402 subp. 1 — gas-permeable material under all floor systems (revisor.mn.gov, read 2026-10-28).
- OSHA 29 CFR 1926 Subpart P, Appendix B — sloping, Type B soil 1:1.
- MnDOT 2025 Average Bid Prices (eDOCS 39047465) — the price floors in `prices.toml [excavation]`.
- Caterpillar Performance Handbook — swell factors, clay natural bed; Peurifoy, *Construction
  Planning, Equipment and Methods* — bank-to-compacted shrinkage for clay.
- Building Science Corporation / Green Building Advisor guidance on drained backfill, caps and
  light compaction near foam.

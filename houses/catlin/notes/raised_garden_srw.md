# Raised-garden SRW apron — the gravity free body, by hand

Worked 2026-09-20, **re-worked 2026-09-21 by the NCMA gravity method on the real unit (Allan
Block AB Classic)**, by hand and separately from `engineering/segmental_wall.py` /
`engineering/srw_gravity.py`. Nothing here is imported from the engine;
`tests/test_segmental_wall.py` reproduces §2–§6 against it.

**Result: still OVER on every leg, but by 18–24%, not by a factor of four.** On the AB Classic
with its 6° setback, Coulomb thrust with wall friction, the vertical thrust component credited
and base friction at tan φ, the 4'-0" free body reads **overturning FS 1.27 (110 pcf) / 1.34
(130 pcf)** against IRC R404.4's 1.5 — failing at both ends of the soil band, so the verdict is
robust. Sliding (1.21 / 1.51) and bearing (2,397 / 1,998 psf against 2,000) straddle the band.
The graded (loose) end reads **sliding d/c 1.24** as the largest ratio. The 2026-09-20 numbers
(FS 0.38 / 0.57, d/c 3.93) were a Rankine EFP on a vertical, solid, 137 pcf stand-in unit with
μ 0.25 (§7), and are retired.

## 1. What is authored

All five legs (`W-RG-BLOCK`, `-WEST`, `-EAST`, `-WEST-BALCONY`, `-EAST-BALCONY`) are one
section. `params/raised_garden.py`, `plan/assemblies.py`, `plan/site.py`:

| term | value | from |
|---|---|---|
| wall top / base | 0'-0" / −4'-0" | six 8" AB courses (`drop_ft` 4'-0") |
| retained `H_r` | 3'-4" = 3.333' | `unbalanced_fill`, authored (**not** `drop_ft`) |
| yard | −3'-4" | the three south-yard grade stations |
| embedment `D` | 8" = 0.667' = one whole course | yard − base |
| free body `H` | 4.000' | `H_r + D` (§2) |
| unit | **Allan Block AB Classic**, 8"H × 12"D × 18"L, 75 lb, **6° setback** | [AB Collection](https://allanblock.com/products/retaining-walls/ab-collection) |
| unit depth `B` | **0.97'** | AB Commercial Installation Manual, gravity sample (p. 11): "Depth of Wall (d) = 0.97 ft" |
| in-place unit weight `γ_w` | **130 pcf**, cores filled with wall rock | same sample: "Wall Density (γw) = 130 lb/ft³"; hollow unit 125 pcf (Table 1.2) |
| batter `ω` | **6°** | AB's lip-and-notch setback for the AB Collection |
| interface shear | **645 lb/ft** | AB Table 1.2 "Unit Shear Strength", a published minimum (ASTM D6916 plot on the [Technical Attributes](https://allanblock.com/PDF/Allan_Block_Technical_Attributes-02-22-2023.pdf) sheet) |
| soil | GM, **k = 40 psf/ft** active | IBC Table 1610.1 (the GM row; 45 until 2026-09-21) |
| soil unit weight `γ_s` | 110–130 pcf, a band | `SOIL_UNIT_WEIGHT_BAND_PCF` |
| levelling pad | 6" MnDOT Class 5 on geotextile, **φ_pad = 36°** authored | AB manual's own "Sand/Gravel 36°" row; 6" crushed stone base per AB |
| allowable bearing | 2,000 psf | IBC Table 1806.2 class 4 (the pad is not declared NFS) |

Manual: [AB Commercial Installation Manual](https://allanblock.com/PDF/ABCommManual.pdf)
(read 2026-09-21), and its gravity chart, Table 1.3, whose AB Collection 6° column is also at
[charts and tables](https://allanblock.com/installation/commercial-installation/charts-and-tables).

**No site φ exists, so it is read back off the code's own EFP.** IBC 1610.1 publishes an
equivalent fluid pressure, not an angle. A Rankine EFP is `k = K_a γ_s`, so at each end of the
band `K_a = k/γ_s` and `sin φ = (1 − K_a)/(1 + K_a)`:

```
γ_s 110:  K_a = 40/110 = 4/11 = 0.36364   sin φ = (7/11)/(15/11) = 7/15    φ = 27.818°
γ_s 130:  K_a = 40/130 = 4/13 = 0.30769   sin φ = (9/13)/(17/13) = 9/17    φ = 31.966°
```

That is AB's own "clay 27°" to "silty sand 32°" — the band the code value already describes.
It is a presumption, stated as one, and it is run at both ends like everything else.

## 2. The method — NCMA/AB gravity, and why the free body is 4'-0" high

The retained soil stands on the whole back face to the base: `H = 3.333 + 0.667 = 4.000'`.
**No passive is credited on the 8" of embedment** (trench backfill; `retaining_basis`'s
convention). AB's chart heights are *exposed* heights with a cap; this free body is the whole
buried-and-exposed height and credits no cap weight.

**Coulomb, with wall friction, on a face leaning back into the fill.** `δ = ⅔φ`, level
backfill (`i = 0`), and AB's form with the back-face angle `β = 90° − ω = 84°`:

```
K_a = [ csc β · sin(β − φ) / ( √sin(β + δ) + √( sin(φ + δ) sin φ / sin β ) ) ]²
```

Checked against AB's own printed sample (φ 30°, δ = 0.66φ = 19.8°, 12° setback, β = 78°):
this form gives **0.2199** against AB's printed 0.2197. So the form and the sign of `ω` are AB's.

**The thrust's direction is derived, not copied.** The back face leans back by `ω`, so it
overhangs the fill; the soil's normal pressure on it points into the wall and *up* by `ω`, and
wall friction (the wedge slides down the face) points *down* the face. Resolving `P_a`, which
acts at `δ` to the face normal:

```
P_h = P_a cos(δ − ω)          P_v = P_a sin(δ − ω)   (downward, onto the unit)
```

AB's sample resolves at `cos δ`/`sin δ` instead, which ignores the face's lean; on a battered
face that overstates the vertical credit and understates the horizontal thrust. This note
takes the geometric resolution, which is the conservative one (§7 prints AB's beside it).

**Sliding** at the base, friction on the unit weight plus the vertical thrust:
`FS = μ (W + P_v) / P_h`, `μ = tan φ_b`, **φ_b = min(φ_pad, φ_soil)** — the unit slides on the
pad, or the pad on the ground, whichever is weaker. Where no pad φ is authored the IBC 1806.2
table coefficient stands in, and the record says so.

**Overturning** about the toe of the base unit:

```
M_o = P_h · H/3
M_r = W (B/2 + (H/2) tan ω) + P_v (B + (H/3) tan ω)
```

— the battered prism's centroid leans back half its height's setback; `P_v` acts on the back
face at `H/3`, which has leaned back `(H/3) tan ω`. **Bearing** from `N = W + P_v`,
`x̄ = (M_r − M_o)/N`, `e = B/2 − x̄`; inside the kern `q = N/B (1 + 6e/B)`, outside it
`q = 2N/(3x̄)`, against 2,000 psf. **Interface shear** at the top of the base course: the
horizontal thrust on the height above it, against AB's 645 lb/ft.

## 3. The arithmetic

Common: `W = γ_w B H = 130 × 0.97 × 4.0 = 504.40 plf`, `tan 6° = 0.105104`,
arms `B/2 + (H/2) tan ω = 0.485 + 0.210208 = 0.695208'` and
`B + (H/3) tan ω = 0.97 + 0.140139 = 1.110139'`. φ_pad 36° exceeds φ_soil at both ends, so
the ground governs the base: `μ = tan φ_soil`.

```
                          γ_s 110 pcf (graded)            γ_s 130 pcf
φ, δ = ⅔φ                 27.818°, 18.545°                31.966°, 21.310°
β + δ, φ + δ              102.545°, 46.364°               105.310°, 53.276°
numerator csc84·sin(β−φ)  1.005508 × 0.830808 = 0.835385  1.005508 × 0.788379 = 0.792722
√sin(β+δ)                 √0.976124 = 0.987990            √0.964509 = 0.982094
√(sin(φ+δ) sinφ / sin84)  √(0.723733 × 0.466667 / 0.994522)
                           = 0.582754                     √(0.801527 × 0.529412 / 0.994522)
                                                           = 0.653204
K_a                       (0.835385 / 1.570744)² = 0.28285 (0.792722 / 1.635298)² = 0.23499
P_a = ½ γ_s K_a H²        ½·110·0.28285·16 = 248.91       ½·130·0.23499·16 = 244.39
δ − ω                     12.545°                          15.310°
P_h = P_a cos(δ−ω)        248.91 × 0.976124 = 242.97      244.39 × 0.964509 = 235.72
P_v = P_a sin(δ−ω)        248.91 × 0.217214 =  54.07      244.39 × 0.264049 =  64.53
N = W + P_v               558.47                          568.93
μ = tan φ_soil            0.527645                        0.624038

sliding   FS = μN/P_h     294.67 / 242.97 = 1.213  ✗      355.03 / 235.72 = 1.506  ✓
          d/c                1.237                           0.996
overturn  M_o = P_h·4/3   323.96                          314.29
          M_r             504.40·0.695208 + 54.07·1.110139 504.40·0.695208 + 64.53·1.110139
                           = 350.66 + 60.02 = 410.68       = 350.66 + 71.64 = 422.30
          FS              1.268  ✗  (d/c 1.183)           1.344  ✗  (d/c 1.116)
bearing   x̄ = (M_r−M_o)/N 86.72/558.47 = 0.1553'          107.99/568.93 = 0.1898'
          e = 0.485 − x̄   0.3297'  > B/6 = 0.1617'        0.2952'  > 0.1617'
          q = 2N/(3x̄)     2,397 psf  ✗ (d/c 1.199)        1,998 psf  ✓ (d/c 0.999)
```

**Overturning fails at both ends, so the verdict is OVER and robust across the band.** Sliding
and bearing each pass at the dense end and fail at the loose end; they could not close the item
even if the soil were measured at 130 pcf. The record prints the loose end (the conservative
one), whose largest ratio is **sliding, d/c 1.24**.

With no pad φ authored (the IBC fallback, μ 0.25): sliding `0.25 × 558.47 / 242.97 = 0.575`.
The pad's φ does not govern here — the ground does — but authoring one is what lets the base
be graded at tan φ at all.

## 4. Base-course embedment

Required `max(6", H/10) = max(6", 4.8") = 6"`; provided 8" — one whole 8" AB course. **d/c
0.75, passes.** Embedment is read to the NEAREST grade station
(`resolve/site_earth.nearest_grade_station`):

| leg | midpoint | nearest station | ground | yard → base |
|---|---|---|---|---|
| `-BLOCK` | (18, -31.33) | (18, -38), 6.7' | -3'-4" | 8" |
| `-WEST` | (4, -20.92) | (-6, -22), 10.1' | -3'-4" | 8" |
| `-EAST` | (32, -20.92) | (41, -18), 9.5' | -3'-4" | 8" |
| `-WEST-BALCONY` | (5.75, -10.5) | (12, -2), 10.6' | -3'-0" | 12" → d/c 6/12 = 0.50 |
| `-EAST-BALCONY` | (30.25, -10.5) | (26, -3), 8.6' | -3'-1" | 11" → d/c 6/11 = 0.545 |

On the returns, 3'-4" retained over 12" (or 11") of ground is taller than the 4'-0" wall; fill
cannot stand above the block, so the free body is **capped at the wall's own 4'-0"** and the
record prints the disagreement. §3 holds on all five legs. The 6" → 8" coursing change moves
nothing here: 4'-0" is six whole 8" courses as it was eight 6" ones.

## 5. Course interface shear

Demand: the horizontal thrust on the 3.333' above the base course,
`½ γ_s K_a (H − 0.667)² cos(δ − ω)`:

```
110:  ½·110·0.28285·3.3333²·0.976124 = 168.7 plf     FS 645/168.7 = 3.82   ✓
130:  ½·130·0.23499·3.3333²·0.964509 = 163.7 plf     FS 3.94               ✓
```

645 lb/ft is AB's published *minimum* at zero normal load (the D6916 plot rises with `N`), so
this is the conservative read. It passes by a wide margin and does not move the verdict.

## 6. Tier independence

Unchanged in its geometry: the court walls retain 9.12', `2 · 9.12 = 18.24'` against a clear
offset of **2.974'**, **d/c 6.13**, graded on the three perimeter legs against the parallel
court wall (`W-RG-BLOCK` ↔ `W-SG-S`, `-WEST` ↔ `W-SG-W2`, `-EAST` ↔ `W-SG-E2`); the balcony
returns butt `W-SG-W1/E1` end-on and print no tier row.

The court wall's active wedge at the apron's founding elevation (5.12' above the court base),
now at `K_a = 40/γ`:

```
γ = 110 pcf:  K_a 0.364, 45°−φ/2 = 31.09°, wedge 58.91°, 5.12/1.658 = 3.09'  → 3.59' from court axis
γ = 130 pcf:  K_a 0.308, 45°−φ/2 = 29.02°, wedge 60.98°, 5.12/1.803 = 2.84'  → 3.34' from court axis
```

The apron's faces are at 3.5' and 4.5'. At the loose end the wedge reaches 1" under the pad; at
the dense end it stops 2" short of it. Either way the court is a closed cast loop graded as one
free body (`retaining_system/W-SG-ARCH`), and what survives is deep-seated slip under both — the
geotechnical engineer's (`sunken_garden_court_free_body.md` §9).

**The apron's weight on its pad is carried onto the court as a strip surcharge**
(`engineering/tier_surcharge.py`), NET of the soil it displaces. On the AB unit it is
`γ_w H = 130 × 4.0 = 520 psf` gross, **80.0 psf net at 110 pcf and 0 at 130 pcf** (a relief,
not credited) — `sunken_garden_court_free_body.md` §4d reworks the court at that. `P_v` (54–65
plf) also lands on the pad and is **not** carried onto the court; it is ~10% of the unit's
weight and is named here as an ungraded remainder.

## 7. Against the retired free body, and AB's own numbers

| term | 2026-09-20 | here | why |
|---|---|---|---|
| unit | generic 12x6x18, solid | AB Classic, filled | the owner's unit |
| γ_w | 137.34 pcf (solid density) | 130 pcf | AB's in-place design value |
| batter | 0° | 6° | AB's setback |
| thrust | Rankine EFP 45 (then 40), horizontal | Coulomb, δ = ⅔φ, inclined | NCMA/AB |
| P_v | not credited | 54–65 plf | wall friction |
| μ | 0.25 (IBC 1806.2 class 4) | tan φ 0.53–0.62 | NCMA base sliding |
| sliding / OT FS | 0.38 / 0.57 | 1.21 / 1.27 (110 pcf) | |

**AB's resolution** (`cos δ`, `sin δ`, §2) on the same inputs: 110 pcf `P_h 236.0`, `P_v 79.2`,
sliding 1.31, overturning 1.39; 130 pcf sliding 1.63, overturning **1.48**. Even AB's more
generous resolution fails overturning at both ends, narrowly at the dense end.

**AB's own chart agrees.** Table 1.3, AB Collection 6°, level backfill: **3'-2"** in clay (27°),
**4'-7"** in silty sand (32°), exposed height including a cap. This site's presumptive φ runs
27.8°–32.0°; the perimeter legs expose 3'-4" (the returns less). At the clay end the chart
refuses 3'-4" outright; at the silty-sand end it allows it. The free body here, which also
charges the buried course and credits no cap, fails at both. A published chart could not close
this item anyway (§9).

## 8. What would close it (the owner's decision)

Required: FS 1.5 on sliding and overturning, bearing within 2,000 psf, at both soil ends.

* **AB Stone, 12° setback — does NOT close by itself.** Same free body, same `B` and `γ_w`
  (AB Stone's own depth and weight would have to be authored), `β = 78°`: 110 pcf `K_a 0.2456`,
  `P_h 214.76`, `P_v 24.64`, **sliding 1.30 ✗**, overturning 1.71, bearing 883 psf; 130 pcf
  sliding 1.65, overturning 1.85. It clears overturning and bearing at both ends; sliding still
  turns on the soil. AB's chart gives it 3'-6" (clay) / 5'-4" (silty sand).
* **A measured soil.** At the dense end (φ 32°, 130 pcf) the AB Classic still reads OT 1.34 —
  no soils report closes the 6° unit at this height.
* **A lower terrace.** On AB Classic at the loose end sliding reaches 1.5 near `H ≈ 3.17'`
  total (1.578 at 3.0', 1.487 at 3.2'; overturning 1.82 at 3.2') — about **2'-6" retained**
  over the 8" course.
* **Geogrid-reinforced SRW**, designed and sealed by the supplier's engineer — new engine scope,
  not graded here.
* **The tier row is independent of all of these.** On the three perimeter legs it is d/c 6.13
  (§6) whatever the unit, and it fails the item on its own. Only the two balcony returns can
  close on a free body alone; the perimeter legs also need the tiered pair resolved — the
  geotechnical engineer's global stability, or the apron ≥ 18.24' off the court.

(Both lines are hand arithmetic by the §2 method, everything else as §3; AB Stone's arms are
`0.485 + 2·0.212557 = 0.910113'` and `0.97 + 1.3333·0.212557 = 1.253409'`.)

## 9. Not graded here

* Global stability of the apron and court on a common failure surface — the geotechnical
  engineer's (§6; `sunken_garden_court_free_body.md` §9).
* The balcony returns' load on `W-SG-W1`/`E1`, and `P_v` onto any court wall (§6).
* Hydrostatic, seismic and frost-heave cases. Every number presumes a drained backfill; the
  assemblies still declare no drainage layer behind the block (AB specifies 12" of wall rock).
* The cap unit — not modelled, its weight not credited.
* A published chart row cannot close any of this. If one is authored on
  `FoundationWall.srw.published` it is refused unless the assembly declares a DRAINAGE layer, a
  batter and a cap are stated, and no taller wall stands within 2H — and the apron fails the last
  guard at every leg.

# Raised-garden SRW apron — the gravity free body, by hand

Worked 2026-09-20, re-worked 2026-09-21 by the NCMA gravity method on the real unit (Allan
Block AB Classic), and **audited the same day** (phase 2, workstream A): geometry traced, the
tier row re-read, the confined backfill checked, AB's 12" of wall rock authored and graded.
By hand and separately from `engineering/segmental_wall.py` / `srw_gravity.py` /
`srw_tiers.py` / `srw_backfill.py`. Nothing here is imported from the engine;
`tests/test_segmental_wall.py` reproduces §2–§8 against it.

**Result: still OVER on every leg, by 4–8%.** The audit took three things off the item and
added nothing to it:

* **The tier row (d/c 6.13) is gone** — the apron and the court walls stand BACK TO BACK
  (§1, §6). The 2H rule is a terrace rule. Its two real consequences are the strip surcharge
  (graded, on the court) and deep-seated slip (the geotechnical engineer's).
* **The confined backfill buys nothing** — the critical wedge fits inside the 2.97' strip
  at the dense end and overshoots it by 0.10–0.14' at the loose end, where no published
  reduction applies anyway (§6b; worth −0.1 to −0.2% even if it did).
* **The wall rock buys 13% of the thrust at the loose end** (§2b, §3b): overturning FS
  1.27 → **1.44** (110 pcf) and 1.34 → **1.43** (130 pcf), sliding 1.21 → **1.38** /
  1.51 → 1.61. Still under IRC R404.4's 1.5 at BOTH ends, so the verdict is robust and OVER.
  The record prints the loose end: **sliding d/c 1.08** governs (was 1.24).

AB's own chart agrees at the clay end and disagrees at the silty-sand end; §7 says exactly why.

## 1. Geometry — the premise everything else rests on

Traced off the resolved model (`resolve` + `resolve/orientation.wall_outward_sign`), feet,
plan x east / y north; the "face" is the exposed face, `−outward_sign × normal(start→end)`,
which is also the direction the retained soil pushes the wall:

| wall | axis | top / base | retains | face points | how the sign is known |
|---|---|---|---|---|---|
| `W-RG-BLOCK` | y −31.333, x 4 → 32 | 0'-0" / −4'-0" | 3'-4" terrace | **south** (yard) | no closed loop: authored direction, the yard station 15 at (18, −38) is south ✓ |
| `W-RG-WEST` | x 4, y −10.5 → −31.333 | 0'-0" / −4'-0" | 3'-4" | **west** | station 13 at (−6, −22) ✓ |
| `W-RG-EAST` | x 32, y −31.333 → −10.5 | 0'-0" / −4'-0" | 3'-4" | **east** | station 14 at (41, −18) ✓ |
| `W-SG-S` | y −27.333, x 8 → 28 | 0'-0" / −9'-1 7/16" | 9.12' | **north** (into the court) | closed loop through `W-SG-ARCH` |
| `W-SG-W2` | x 8, y −11 → −27.333 | same | 9.12' | **east** | closed loop |
| `W-SG-E2` | x 28, y −27.333 → −11 | same | 9.12' | **west** | closed loop |

**The yard** is authored at −3'-4" by three stations outboard of the U (`plan/site.py`).
**The court wall top** is the porch datum, 0'-0" — level with the apron top, so the terrace
between them is a 3'-0"-wide level bed at 0'-0" whose surface is the court's retained
surface. Axis to axis is 4.000'; face to face, net of the wash and the court's dimpleboard,
**2.974'** of terrace (`tier_W-SG-*_clear`).

**So each perimeter leg and its court wall retain ONE terrace from opposite sides: back to
back.** The apron's face looks out at the yard; the court's looks in at the court. The apron
founds at −4'-0", inside the soil the court retains (to −9'-1 7/16"), which is why its pad
bears on the court (§6), and it is not an upper terrace of the court in the sense of any SRW
rule — it does not step up away from the court's face, it steps DOWN away from its back.

Two findings the trace turned up:

* The balcony **returns** (`-WEST-BALCONY`, `-EAST-BALCONY`) resolve facing **south** on the
  same fallback sign, but they retain terrace fill to the south and face north — which is
  why they carry no wash (layer 0 lands in the fill). Their nearest stations (0 at (12, −2),
  1 at (26, −3)) are north, so the engine's facing test would refuse them. It is never
  asked: they meet the court end-on and grade no tier row, so nothing turns on it.
* No leg's sign comes from a closed loop — the U is open at the returns — so every SRW facing
  is the authored direction, trusted only because the grade station its embedment is read to
  lies on that side (`srw_tiers._face`).

### Authored section

All five legs are one section. `params/raised_garden.py`, `plan/assemblies.py`, `plan/site.py`:

| term | value | from |
|---|---|---|
| wall top / base | 0'-0" / −4'-0" | six 8" AB courses (`drop_ft` 4'-0") |
| retained `H_r` | 3'-4" = 3.333' | `unbalanced_fill`, authored (**not** `drop_ft`) |
| yard | −3'-4" | the three south-yard grade stations |
| embedment `D` | 8" = 0.667' = one whole course | yard − base |
| free body `H` | 4.000' | `H_r + D` (§2) |
| unit | **Allan Block AB Classic**, 8"H × 12"D × 18"L, 75 lb, **6° setback** | [AB Collection](https://allanblock.com/products/retaining-walls/ab-collection) |
| unit depth `B` | **0.97'** | [AB Commercial Installation Manual](https://allanblock.com/PDF/ABCommManual.pdf) p.11 gravity sample: "Depth of Wall (d) = 0.97 ft" |
| in-place unit weight `γ_w` | **130 pcf**, cores filled with wall rock | same sample: "Wall Density (γw) = 130 lb/ft³"; hollow unit 125 pcf (Table 1.2) |
| batter `ω` | **6°** | AB's lip-and-notch setback for the AB Collection |
| interface shear | **645 lb/ft** | AB Table 1.2 "Unit Shear Strength", a published minimum |
| **wall rock** | **12" behind the unit, φ_r = 36°** | manual p.22 (gravity Step 4): "Fill the hollow cores and a minimum of 12 in (300 mm) behind the wall with wall rock"; p.20: compactible aggregate 0.25–1.5 in, ≤10% passing #200, ≥120 pcf; p.16 Table 2.1: "Sand/Gravel 36°". Table 3.1 (p.29) gives crushed stone "34° +" — §3b runs it. |
| soil | GM, **k = 40 psf/ft** active | IBC Table 1610.1 (the GM row) |
| soil unit weight `γ_s` | 110–130 pcf, a band | `SOIL_UNIT_WEIGHT_BAND_PCF` |
| levelling pad | 6" MnDOT Class 5 on geotextile, **φ_pad = 36°** | AB's "Sand/Gravel 36°" row |
| allowable bearing | 2,000 psf | IBC Table 1806.2 class 4 |

**No site φ exists, so it is read back off the code's own EFP.** A Rankine EFP is
`k = K_a γ_s`, so at each end of the band `K_a = k/γ_s` and `sin φ = (1 − K_a)/(1 + K_a)`:

```
γ_s 110:  K_a = 40/110 = 0.36364   sin φ = 7/15    φ = 27.818°
γ_s 130:  K_a = 40/130 = 0.30769   sin φ = 9/17    φ = 31.966°
```

That is AB's own "clay 27°" to "silty sand 32°". A presumption, run at both ends.

## 2. The method — NCMA/AB gravity, and why the free body is 4'-0" high

The retained soil stands on the whole back face to the base: `H = 3.333 + 0.667 = 4.000'`.
**No passive is credited on the 8" of embedment** (trench backfill). AB's chart heights are
*exposed* heights with a cap; this free body is the whole buried-and-exposed height and
credits no cap weight.

**Coulomb, with wall friction, on a face leaning back into the fill.** `δ = ⅔φ`, level
backfill, AB's form with `β = 90° − ω = 84°`:

```
K_a = [ csc β · sin(β − φ) / ( √sin(β + δ) + √( sin(φ + δ) sin φ / sin β ) ) ]²
```

Checked against AB's printed sample (φ 30°, δ 0.66φ, 12° setback): **0.2199** against AB's
0.2197, sliding FS 1.91 (AB 1.91).

**The thrust's direction is derived, not copied.** The face leans back by `ω`; the soil's
normal pressure points into the wall and *up* by `ω`, wall friction points *down* the face:

```
P_h = P_a cos(δ − ω)          P_v = P_a sin(δ − ω)   (downward, onto the unit)
```

AB's sample resolves at `cos δ`/`sin δ`, which ignores the lean; this note takes the geometric
resolution, the conservative one (§7 prints AB's beside it).

**Sliding** `FS = μ (W + P_v) / P_h`, `μ = tan min(φ_pad, φ_soil)`. **Overturning** about the
toe:

```
M_o = P_h · H/3
M_r = W (B/2 + (H/2) tan ω) + P_v (B + (H/3) tan ω)
```

**Bearing** from `N = W + P_v`, `x̄ = (M_r − M_o)/N`, `e = B/2 − x̄`; inside the kern
`q = N/B (1 + 6e/B)`, outside `q = 2N/(3x̄)`, against 2,000 psf. **Interface shear**: the
horizontal thrust on the height above the base course, against 645 lb/ft.

### 2b. Two materials behind the face — the trial wedge

With wall rock at the face and native beyond, no closed form applies. The **trial-wedge
(Culmann) method**: a plane through the heel at `ρ` from horizontal cuts a wedge of weight
`W_ρ = γ · ½H² (cot ρ − tan ω)`; with the face reaction at `δ − ω` and the plane's reaction at
`φ` to its normal,

```
P(ρ) = W_ρ sin(ρ − φ) / cos(ρ − φ − (δ − ω))          P_a = max over ρ
```

With one material this is Coulomb exactly (§3's 248.91 / 244.39 plf come back to 0.01 plf).
**Two zones along the plane**: the rock's back boundary is parallel to the face, `t = 12"`
behind it, so the plane leaves the rock at

```
z₁ = t tan ρ / (1 − tan ρ tan ω)          share s = z₁ / H  (of the plane's length)
tan φ_eq = s tan φ_r + (1 − s) tan φ_n
```

**What is credited, and what is not.** The length-weighted `tan φ` assumes a UNIFORM normal
stress along the plane. The rock is the deep end of the plane, under the most overburden, so
it carries more than its length's share — uniform stress under-credits it, and this note takes
the under-credit. `δ` stays **⅔φ of the native** (AB's "0.66φ" of the soil): the unit does
bear on rock, and δ = ⅔·36° = 24° is printed as a sensitivity, not graded. `γ` of the whole
wedge is `γ_s` (AB's rock is ≥ 120 pcf, inside the band).

## 3. The arithmetic — native soil at the face (the pre-audit record)

Common: `W = 130 × 0.97 × 4.0 = 504.40 plf`, `tan 6° = 0.105104`, arms `0.695208'` and
`1.110139'`. φ_pad 36° exceeds φ_soil at both ends, so `μ = tan φ_soil`.

```
                          γ_s 110 pcf (graded)            γ_s 130 pcf
φ, δ = ⅔φ                 27.818°, 18.545°                31.966°, 21.310°
K_a                       0.28285                          0.23499
P_a = ½ γ_s K_a H²        248.91                           244.39
P_h / P_v                 242.97 / 54.07                   235.72 / 64.53
sliding   FS              1.213  ✗                         1.506  ✓
overturn  M_o / M_r       323.96 / 410.68 → FS 1.268 ✗     314.29 / 422.30 → FS 1.344 ✗
bearing   x̄, q           0.1553', 2,397 psf ✗             0.1898', 1,998 psf ✓
critical plane ρ          52.43°, exits 3.077' behind heel 54.88°, exits 2.813'
```

(Full line-by-line of `K_a` as in the 2026-09-21 revision: numerator 0.835385 / 0.792722,
denominator 1.570744 / 1.635298.) This is what the engine grades when `drainage_zone` is
not authored; `tests/test_segmental_wall.py` still pins it.

### 3b. The arithmetic — with the 12" of wall rock (the graded case)

The critical plane, found by scanning `ρ` at 0.001°:

```
                          γ_s 110 pcf (graded)            γ_s 130 pcf
ρ                         52.135°                          54.793°
tan ρ, sin ρ              1.28618, 0.78946                 1.41722, 0.81707
cot ρ − tan ω             0.67239                          0.60050
W_ρ = γ·8·(…)             110 × 5.3792 = 591.71            130 × 4.8040 = 624.52
z₁ = tan ρ/(1−tan ρ tan ω)  1.4872'                        1.6653'
share s = z₁/4            0.3718                           0.4163
tan φ_eq                  .3718×.72654+.6282×.52764        .4163×.72654+.5837×.62404
                          = 0.60160, φ_eq 31.031°          = 0.66671, φ_eq 33.692°
ρ − φ_eq, − (δ − ω)       21.104°, 8.559°                  21.101°, 5.791°
P_a = W sin/cos           591.71 × .36006/.98886 = 215.45  624.52 × .36002/.99490 = 225.99
  (vs native)             −13.4%                           −7.5%
P_h / P_v                 210.31 / 46.80                   217.97 / 59.67
N = W + P_v               551.20                           564.07
sliding   FS = μN/P_h     .527645×551.20/210.31 = 1.383 ✗ .624038×564.07/217.97 = 1.615 ✓
          d/c             1.085                            0.929
overturn  M_o = P_h·4/3   280.41                           290.63
          M_r             350.66 + 46.80×1.110139 = 402.62 350.66 + 59.67×1.110139 = 416.91
          FS              1.436 ✗ (d/c 1.045)              1.435 ✗ (d/c 1.046)
bearing   x̄ = (M_r−M_o)/N 0.2217'                          0.2239'
          q = 2N/(3x̄)     1,657 psf ✓ (d/c 0.83)           1,680 psf ✓ (d/c 0.84)
exits behind the heel     3.110'                           2.822'
```

**Overturning still fails at both ends — OVER, robust across the band.** The record prints
the loose end, whose largest ratio is **sliding, d/c 1.08**.

Sensitivities, all still OVER at both ends:

| variant | 110 pcf sliding / OT | 130 pcf sliding / OT |
|---|---|---|
| φ_r 34° (AB Table 3.1 "crushed stone 34°+") | 1.335 / 1.389 | 1.558 / 1.387 |
| δ on the rock, ⅔·36° = 24° | 1.482 / 1.566 | 1.672 / **1.499** |
| no rock (§3) | 1.213 / 1.268 | 1.506 / 1.344 |

Even crediting δ on the rock the dense end misses overturning by a thousandth and the loose
end misses sliding by 1%. The method does not close the item.

## 4. Base-course embedment

Required `max(6", H/10) = 6"`; provided 8". **d/c 0.75, passes.** Read to the NEAREST grade
station (`resolve/site_earth.nearest_grade_station`):

| leg | midpoint | nearest station | ground | yard → base |
|---|---|---|---|---|
| `-BLOCK` | (18, -31.33) | (18, -38), 6.7' | -3'-4" | 8" |
| `-WEST` | (4, -20.92) | (-6, -22), 10.1' | -3'-4" | 8" |
| `-EAST` | (32, -20.92) | (41, -18), 9.5' | -3'-4" | 8" |
| `-WEST-BALCONY` | (5.75, -10.5) | (12, -2), 10.6' | -3'-0" | 12" → d/c 0.50 |
| `-EAST-BALCONY` | (30.25, -10.5) | (26, -3), 8.6' | -3'-1" | 11" → d/c 0.545 |

On the returns the free body is capped at the wall's own 4'-0" and the record prints the
disagreement. §3/§3b hold on all five legs.

## 5. Course interface shear

Demand: the horizontal thrust on the 3.333' above the base course — with the rock, the
critical wedge at that height (ρ 52.12° / 54.79°):

```
110:  P 145.20 × cos 12.545° = 141.73 plf     FS 645/141.73 = 4.55   ✓
130:  P 154.45 × cos 15.310° = 148.97 plf     FS 4.33               ✓
(native at the face: 168.7 / 163.7 plf, FS 3.82 / 3.94)
```

645 lb/ft is AB's minimum at zero normal load; conservative. Does not move the verdict.

## 6. The tier row — back to back, not a terrace

**What the rule says.** AB Commercial Installation Manual p.60, "Terraces": walls "perform
independently … when the distance between gravity walls is at least two times the height of
the lower wall"; walls closer than that "must also be evaluated for global stability, and the
lower walls must be designed to resist the load of the upper walls." Its figure, and CMHA
SRW-TEC-003 ([Segmental Retaining Wall Global
Stability](https://www.cmha.org/resource/srw-tec-003/)), define the geometry: an upper wall
set back `J` from a lower one, both facing the same way. A municipal adoption of the NCMA
criteria ([Town of Clayton, NC, Segmental Retaining Wall Design, Table 2.1 note
1](https://www.townofclaytonnc.org/DocumentCenter/View/704/Segmental-Block-Retaining-Wall-Design-PDF))
states the consequence directly: within 2H "a surcharge load will be applied to the lower
wall. Design to compensate."

**None of these addresses a back-to-back pair, and none says otherwise.** What the rule
protects against is two things, and both are already where they belong:

1. **The upper wall's load on the lower.** The apron's weight on its pad is carried onto the
   court as a Boussinesq strip surcharge, NET of displaced soil (`engineering/tier_surcharge.py`;
   `sunken_garden_court_free_body.md` §4c/§4d): **80.0 psf net at 110 pcf, 0 at 130**, in the
   court's system FS 1.60. The wall rock does not move it: it replaces soil of the same
   weight band in the court's retained zone. `P_v` (47–60 plf) is still not carried onto the
   court — named, ungraded, ~10% of the unit's weight.
2. **Global stability**, a slip surface under both walls — deep-seated, into the court. Not
   computable on a presumed soil; the geotechnical engineer's (`…court_free_body.md` §9).

So the engine applies the 2H row **only to same-facing pairs** (`srw_tiers.lower_tiers`
derives each face from `outward_sign`; `segmental_wall` drops the row where the faces point
apart). The record prints a BACK TO BACK note naming both interactions. **It is not a pass**:
item 2 stays open, and it is open for the court too.

The court wall's active wedge at the apron's founding elevation, unchanged: 3.09' (110 pcf)
/ 2.84' (130 pcf) from the court axis against the pad at 3.5–4.5' — it reaches 1" under the
pad at the loose end. That is why the surcharge is graded at all.

### 6b. Confined backfill — the strip is narrow, and it does not help

The apron retains a **2.974'**-wide strip against the rigid court stem on a **4.000'** free
body: `b/H = 0.74`.

**Does the wedge even reach the court wall?** The critical plane exits `H cot ρ` behind the heel:

```
            native (§3)                     with rock (§3b)
110 pcf     4 cot 52.43° = 3.077'  > 2.974  4 cot 52.14° = 3.110'  > 2.974   reaches, by 0.10' / 0.14'
130 pcf     4 cot 54.88° = 2.813'  < 2.974  4 cot 54.79° = 2.822'  < 2.974   does not
```

(Measured from the base course's heel. A 6° batter leans the top 0.42' toward the court; the
exit point is set by the heel, so it does not change this.)

**At 130 pcf nothing can be credited** — the court wall does not touch the wedge. **At 110
pcf** the most a PLANAR surface restricted to the strip can remove is the difference between
the free maximum and `P` at the steepest-reaching plane, `ρ_hit = atan(4/2.974) = 53.37°`:
native 248.91 → 248.69 (−0.09%), with rock 215.45 → 215.05 (−0.19%). The Coulomb function is
flat at its peak.

**And no published method credits it here.** Frydman & Keissar (1987, *J. Geotech. Eng.*
113(6), centrifuge, L/H 0.1–1.1), Leshchinsky & Hu (2003) and Lawson & Yee (2005, limit
equilibrium) are for granular fill. [Kniss, Yang, Wright & Zornberg
(2007)](https://sites.utexas.edu/zornberg/files/2022/03/Kniss_Yang_Wright_Zornberg_2007.pdf)
found their finite-element pressures at L/H 0.70 in "good agreement with the recommended
values" (i.e. no reduction for design) and warn the chart "is not appropriate when using
locally, naturally cohesive" soil. The retained soil here is presumed GM, run as clay at the
loose end. **Nothing is credited**; the record prints the check.

## 7. Against AB's own numbers, and AB's Table 1.3

| term | 2026-09-20 | 2026-09-21 | here | why |
|---|---|---|---|---|
| unit | generic, solid | AB Classic | AB Classic | the owner's unit |
| thrust | Rankine EFP | Coulomb, inclined | two-zone trial wedge | wall rock |
| sliding / OT FS (110) | 0.38 / 0.57 | 1.21 / 1.27 | **1.38 / 1.44** | |
| tier row | 6.13 | 6.13 | not applied | back to back (§6) |

**Reproducing AB's method.** AB's own resolution (`cos δ`), δ 0.66φ, `γ_s` 120 (its sample),
d 0.97, 130 pcf, 6°, μ tan φ — the height at which the first FS hits 1.5, by the same
arithmetic as §3:

| soil | this method, total H | AB Table 1.3, exposed incl. cap | ratio |
|---|---|---|---|
| clay 27° | 2.86' (sliding) | **3'-2"** = 3.17' | 1.11 |
| silty sand 32° | 4.12' (overturning) | **4'-7"** = 4.58' | 1.11 |
| sand/gravel 36° | 4.67' (overturning) | 5'-2" = 5.17' | 1.11 |

The chart publishes a uniform ~11% more height than the printed sample method gives, at every
soil. The manual does not itemise its chart basis (it refers to the AB Engineering Manual).
The table is what AB publishes, and the free body is compared against it, not fitted to it.

**Where the free body and AB agree, and where they differ, at each soil end:**

* **Clay end (27°, the loose end here).** AB's chart allows **3'-2"** exposed with a cap.
  The perimeter legs expose **3'-4"** and carry no cap: **the chart refuses this wall too.**
  The free body agrees: it fails sliding and overturning at 110 pcf, with or without the rock.
  At this end the owner's instinct is contradicted by AB itself.
* **Silty-sand end (32°, the dense end here).** AB's chart allows **4'-7"**, so 3'-4" exposed
  is routine *by the chart*, and the owner's instinct matches AB. The free body fails
  overturning at 1.43–1.44 for three stated reasons, largest first:
  1. **Resolution.** `cos(δ − ω)` instead of AB's `cos δ`: at 32°/120 pcf, 4.0' total, AB's
     resolution reads OT **1.58**, this one **1.44** (no rock).
  2. **Unit weight.** The band pairs φ 32° with γ 130 (both read off one EFP); AB's chart
     pairs 32° with 120 or lighter. 130 vs 120 is ~8% more thrust.
  3. **The buried course.** The free body is 4.0' (8" buried + 3'-4"); the chart's height is
     exposed, with the cap's weight on top.
  With AB's resolution at φ 32°/130 pcf the free body reads OT **1.48** — the chart's
  generosity is almost exactly those three choices.

**Which to believe?** The geometric resolution is the statics of a leaning face (§2), and φ is
not measured. A soils report giving φ ≥ 32° at γ ≤ 120 pcf, graded with AB's resolution,
would put this wall on AB's own chart; the engine does not take AB's resolution to get there.

## 8. What would close it (the owner's decision)

Required: FS 1.5 on sliding and overturning, bearing within 2,000 psf, at both soil ends.
Every line below keeps the 12" wall rock of §3b unless it says otherwise.

* **24" of wall rock instead of 12".** Same method, `t = 2.0'`: 110 pcf `P_a` 184.64 (ρ
  52.17°), **sliding 1.594, OT 1.645, bearing 1,276 psf**; 130 pcf `P_a` 208.41 (ρ 54.79°),
  **sliding 1.737, OT 1.536, bearing 1,452 psf. Passes at both ends** — on the same
  length-weighted credit, which AB does not publish as a design basis for a gravity wall.
  Worth putting to AB's engineering department before adopting. (Not authored.)
* **AB Stone, 12° setback, native at the face:** sliding 1.30 ✗ / OT 1.71 at 110 pcf; 1.65 /
  1.85 at 130. With the rock it would improve further; not re-run here.
* **A measured soil.** At φ 32°/130 pcf the AB Classic with 12" rock reads OT 1.43 — a soils
  report closes it only if it also reports a lighter soil or a higher φ.
* **A lower terrace.** Native at the face, sliding reaches 1.5 near `H ≈ 3.17'` total (1.578
  at 3.0', 1.487 at 3.2').
* **Geogrid-reinforced SRW**, designed and sealed by the supplier's engineer.
* **The tier row no longer stands in the way of any of these** (§6).

(AB Stone arms: `0.485 + 2·0.212557 = 0.910113'`, `0.97 + 1.3333·0.212557 = 1.253409'`.)

## 9. Not graded here

* Global stability of the apron and court on a common failure surface — the geotechnical
  engineer's (§6; `sunken_garden_court_free_body.md` §9).
* The balcony returns' load on `W-SG-W1`/`E1`, and `P_v` onto any court wall (§6).
* Hydrostatic, seismic and frost-heave cases. The drained presumption now rests on the
  authored wall rock (`SegmentalWallSpec.drainage_zone`), but **AB's drain pipe is not
  modelled**: manual p.22, "Drain pipe is required for walls over 4 ft (1.2 m) tall or are
  constructed in silty or clay soils" — the clay end of this band. Nor is the wall rock
  billed: it is on the spec, not in an assembly.
* The cap unit — not modelled, its weight not credited.
* A published chart row cannot close any of this; one authored on `srw.published` is refused
  unless drainage (a DRAINAGE layer or the spec's `drainage_zone`), a batter and a cap are
  stated and no taller wall stands within 2H — and the court walls still stand within 2H.

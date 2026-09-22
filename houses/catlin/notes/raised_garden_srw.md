# Raised-garden SRW apron — the gravity free body, by hand

Worked 2026-09-20; re-worked 2026-09-21 by the NCMA gravity method on the real unit, audited
the same day (geometry traced, tier row re-read, confined backfill checked, AB's 12" of wall
rock authored and graded) — and then **the unit changed** (owner, 2026-09-21): **Allan Block
AB Stones, 12° setback**, replacing AB Classic (6°), keeping the 12" wall-rock zone. By hand
and separately from `engineering/segmental_wall.py` / `srw_gravity.py` / `srw_tiers.py` /
`srw_backfill.py`. Nothing here is imported from the engine; `tests/test_segmental_wall.py`
reproduces §2–§8 against it.

**Result: PASSES on all five legs, at both ends of the soil band.**

| | 110 pcf (loose, governs) | 130 pcf |
|---|---|---|
| sliding FS | **1.538** (d/c 0.975) | 1.806 |
| overturning FS | **2.020** | 2.018 |
| toe bearing | 604 psf of 2,000 | 606 psf |
| course interface shear FS | 5.35 | 5.13 |

Only the setback moved. AB publishes AB Stones at the same 8" × 12" × 18", 75 lb as AB
Classic (§1), and AB's own gravity sample is a 12° wall at d 0.97 ft, 130 pcf. Doubling the
lean does two things: it shrinks the wedge (Coulomb on a face at β = 78°) and moves the
unit's weight back over its heel (arm 0.695' → 0.910'). Sliding is the tight row at the
loose end, 2.5% clear; overturning is not close.

**Superseded — AB Classic (6°), same day:** sliding 1.38 / overturning 1.44 at 110 pcf,
1.61 / 1.43 at 130, OVER at both ends (§3c). The tier row (d/c 6.13) was dropped by the
audit, not by this change (§6).

## 1. Geometry — the premise everything else rests on

Traced off the resolved model (`resolve` + `resolve/orientation.wall_outward_sign`), feet,
plan x east / y north; the "face" is the exposed face, `−outward_sign × normal(start→end)`,
which is also the direction the retained soil pushes the wall:

| wall | axis | top / base | retains | face points | how the sign is known |
|---|---|---|---|---|---|
| `W-RG-BLOCK` | y −31.333, x 4 → 32 | 0'-0" / −4'-0" | 3'-4" terrace | **south** (yard) | no closed loop: authored direction, the yard station 15 at (18, −38) is south ✓ |
| `W-RG-WEST` | x 4, y −10.5 → −31.333 | 0'-0" / −4'-0" | 3'-4" | **west** | station 13 at (−6, −22) ✓ |
| `W-RG-EAST` | x 32, y −31.333 → −10.5 | 0'-0" / −4'-0" | 3'-4" | **east** | station 14 at (41, −18) ✓ |
| `W-RG-WEST-BALCONY` / `-EAST-BALCONY` | y −10.5 | 0'-0" / −4'-0" | 3'-0" / 3'-1" | north bench | stations (12, −2) −3'-0" and (26, −3) −3'-1" (§4) |
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

**The batter is on the spec, not in the geometry.** The model draws every leg plumb. At 12°
the top course sits `4.0 × tan 12° = 0.850'` (10.2") back from the base course toward the
terrace — AB's own setback chart says 10.0" at 4 ft (manual p.18, Table 2.2, "AB Stones
only") — against 0.42' on AB Classic. So the level bed at 0'-0" is ~2.1' wide between the
apron's top course and the court face, not the drawn 2.97'. Nothing grades that width; the
pad, and so everything the court sees (§6), is under the base course and does not move.

### Authored section

All five legs are one section. `params/raised_garden.py` (`AB_STONE`), `plan/assemblies.py`,
`plan/site.py`:

| term | value | from |
|---|---|---|
| wall top / base | 0'-0" / −4'-0" | six 8" AB courses (`drop_ft` 4'-0") |
| retained `H_r` | 3'-4" = 3.333' | `unbalanced_fill`, authored (**not** `drop_ft`) |
| yard | −3'-4" | the three south-yard grade stations |
| embedment `D` | 8" = 0.667' = one whole course | yard − base |
| free body `H` | 4.000' | `H_r + D` (§2) |
| unit | **Allan Block AB Stones**, 8"H × 12"D × 18"L, 75 lb, **12° setback** | [AB Collection specifications](https://allanblock.com/installation/commercial-installation/ab-collection); [AB Commercial Installation Manual](https://allanblock.com/PDF/ABCommManual.pdf) p.7 Table 1.1 ("AB Stones 12° … 75 lbs 8 in H x 12 in D x 18 in L") |
| unit depth `B` | **0.97'** | manual p.11 gravity sample — **"Batter = 12°"**, "Depth of Wall (d) = 0.97 ft" |
| in-place unit weight `γ_w` | **130 pcf**, cores filled with wall rock | same sample: "Wall Density (γw) = 130 lb/ft³"; hollow unit 125 pcf (p.9 Table 1.2) |
| batter `ω` | **12°** | Table 1.1; Table 1.3's "12° (Ref) AB Stones only" column |
| interface shear | **645 lb/ft** | p.9 Table 1.2 "Unit Shear Strength", a collection-wide published minimum (one table, no per-unit rows) |
| **wall rock** | **12" behind the unit, φ_r = 36°** | manual p.22 (gravity Step 4): "Fill the hollow cores and a minimum of 12 in (300 mm) behind the wall with wall rock"; p.20: compactible aggregate 0.25–1.5 in, ≤10% passing #200, ≥120 pcf; p.16 Table 2.1: "Sand/Gravel 36°". Table 3.1 (p.29) gives crushed stone "34° +" — §3b runs it. |
| soil | GM, **k = 40 psf/ft** active | IBC Table 1610.1 (the GM row) |
| soil unit weight `γ_s` | 110–130 pcf, a band | `SOIL_UNIT_WEIGHT_BAND_PCF` |
| levelling pad | 6" MnDOT Class 5 on geotextile, **φ_pad = 36°** | AB's "Sand/Gravel 36°" row |
| allowable bearing | 2,000 psf | IBC Table 1806.2 class 4 |

**Is AB Stones the same unit bar the setback?** Checked, not assumed. AB's specification
page and the manual's Table 1.1 give AB Stones and AB Classic the **identical** size, weight
and coverage (8×12×18 in, 75 lb, 1 sq ft); only the setback differs (12° vs 6°). The 0.97 ft
design depth and 130 pcf in-place density come from the one gravity sample AB prints, and
that sample is a **12° wall** — it describes AB Stones more directly than it ever described
AB Classic. Table 1.2 is one table of collection minimums with no per-unit rows, so the
645 lb/ft interface shear is AB's for both. **No difference found.**

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
backfill, AB's form with `β = 90° − ω` (78° here):

```
K_a = [ csc β · sin(β − φ) / ( √sin(β + δ) + √( sin(φ + δ) sin φ / sin β ) ) ]²
```

Checked against AB's printed sample (φ 30°, δ 0.66φ, **12° setback**, 120 pcf, 3.44'):
**0.2199** against AB's 0.2197, sliding FS 1.91 (AB 1.91), overturning 2.60 (AB 2.6).

**The thrust's direction is derived, not copied.** The face leans back by `ω`; the soil's
normal pressure points into the wall and *up* by `ω`, wall friction points *down* the face:

```
P_h = P_a cos(δ − ω)          P_v = P_a sin(δ − ω)   (downward, onto the unit)
```

AB's sample resolves at `cos δ`/`sin δ`, which ignores the lean; this note takes the geometric
resolution, the conservative one (§7 prints AB's beside it). At 12° it matters more: `δ − ω`
is 6.5° at the loose end, so `P_v` is small.

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
P(ρ) = W_ρ sin(ρ − φ) / cos(ρ − φ − (δ − ω))          P_a = max over ρ < 90° − ω
```

With one material this is Coulomb exactly (§3's 216.17 / 206.33 plf come back to 0.01 plf).
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

## 3. The arithmetic — AB Stones, native soil at the face

What the engine grades when `drainage_zone` is not authored. Common: `W = 130 × 0.97 × 4.0 =
504.40 plf`, `tan 12° = 0.212557`, arms `0.485 + 2·0.212557 = 0.910113'` and
`0.97 + 1.3333·0.212557 = 1.253409'`, so `W · 0.910113 = 459.06`. φ_pad 36° exceeds φ_soil
at both ends, so `μ = tan φ_soil`.

```
                          γ_s 110 pcf                      γ_s 130 pcf
K_a  num / den            0.785240 / 1.584347              0.735835 / 1.652040
K_a                       0.24564                          0.19839
P_a = ½ γ_s K_a H²        216.17                           206.33
P_h / P_v                 214.76 / 24.64                   203.61 / 33.38
sliding   FS              1.300  ✗                         1.648  ✓
overturn  M_o / M_r       286.34 / 489.95 → FS 1.711 ✓     271.48 / 500.90 → FS 1.845 ✓
bearing   x̄, q (kern)     0.3849', 883 psf ✓               0.4266', 755 psf ✓
course shear (3.333')     149.14 plf, FS 4.32              141.39 plf, FS 4.56
critical plane ρ          50.08°, exits 3.347'             52.52°, exits 3.067'
```

Without the rock AB Stones straddles the band — sliding fails at the loose end only. The rock
is what closes it.

### 3b. The arithmetic — AB Stones with the 12" of wall rock (the graded case)

The critical plane, found by scanning `ρ` at 0.001°:

```
                          γ_s 110 pcf (graded)             γ_s 130 pcf
ρ                         49.706°                          52.384°
tan ρ, sin ρ              1.17941, 0.76274                 1.29778, 0.79212
cot ρ − tan ω             0.63533                          0.55799
W_ρ = γ·8·(…)             110 × 5.08264 = 559.09           130 × 4.46394 = 580.31
z₁ = tan ρ/(1−tan ρ tan ω)  1.5740'                        1.7921'
share s = z₁/4            0.3935                           0.4480
tan φ_eq                  .3935×.72654+.6065×.52764        .4480×.72654+.5520×.62404
                          = 0.60591, φ_eq 31.212°          = 0.66996, φ_eq 33.821°
ρ − φ_eq, − (δ − ω)       18.494°, 11.948°                 18.563°, 9.253°
P_a = W sin/cos           559.09 × .31720/.97833 = 181.27  580.31 × .31835/.98699 = 187.18
  (vs native, §3)         −16.1%                           −9.3%
P_h / P_v                 180.09 / 20.66                   184.71 / 30.28
N = W + P_v               525.06                           534.68
sliding   FS = μN/P_h     .527645×525.06/180.09 = 1.538 ✓ .624038×534.68/184.71 = 1.806 ✓
          d/c             0.975                            0.830
overturn  M_o = P_h·4/3   240.12                           246.28
          M_r             459.06 + 20.66×1.253409 = 484.96 459.06 + 30.28×1.253409 = 497.02
          FS              2.020 ✓ (d/c 0.743)              2.018 ✓ (d/c 0.743)
bearing   x̄ = (M_r−M_o)/N 0.4663', e 0.0187' (in kern)     0.4689', e 0.0161'
          q = N/B(1+6e/B) 541.30 × 1.1156 = 604 psf ✓      551.22 × 1.0994 = 606 psf ✓
exits behind the heel     3.392'                           3.082'
```

**Passes at both ends.** The record prints the loose end, whose largest ratio is **sliding,
d/c 0.975**. The resultant sits almost at mid-base (e/B 0.02): the 12° lean has put the
unit's weight back over its heel.

Sensitivities (the graded verdict does not rest on the rock's 36° or on δ):

| variant | 110 pcf sliding / OT | 130 pcf sliding / OT |
|---|---|---|
| φ_r 34° (AB Table 3.1 "crushed stone 34°+") | **1.470** ✗ / 1.931 | 1.723 / 1.927 |
| δ on the rock, ⅔·36° = 24° | 1.636 / 2.171 | 1.863 / 2.092 |
| no rock (§3) | **1.300** ✗ / 1.711 | 1.648 / 1.845 |

**One sensitivity fails, and it is named, not hidden: at φ_r 34° the loose end slides at
1.47.** The graded case uses AB's own 36° for its specified wall rock (p.16, p.20); a
crushed-stone rock read at the bottom of Table 3.1's "34° +" band would not clear sliding at
110 pcf. Either the rock is the clean 0.25–1.5 in aggregate AB specifies, or a measured soil
closes it (at 130 pcf it passes at 34°).

### 3c. Superseded — AB Classic (6°), kept as history

Arms `0.695208'` / `1.110139'`, `M_rW` 350.66. `tests/test_segmental_wall.py` still pins it.

```
                    native (110 / 130)                         with 12" rock (110 / 130)
K_a                 0.28285 / 0.23499                          (P/½γH²) —
P_a                 248.91 / 244.39                            215.45 / 225.99   (ρ 52.135 / 54.793)
P_h / P_v           242.97/54.07  /  235.72/64.53              210.31/46.80  /  217.97/59.67
M_r                 410.68 / 422.30                            402.62 / 416.91
sliding FS          1.213 / 1.506                              1.383 / 1.615
overturning FS      1.268 / 1.344                              1.436 / 1.435
x̄, q               0.1553' 2,397 / 0.1898' 1,998              0.2217' 1,657 / 0.2239' 1,680
course shear        168.7 / 163.7                              141.73 / 148.97
exit                3.077' / 2.813'  (ρ 52.43 / 54.88)         3.110' / 2.822'
share, φ_eq (rock)                                             0.3718 31.031° / 0.4163 33.692°
```

Sensitivities with rock: φ_r 34° → 1.335/1.389, 1.558/1.387; 24" of rock → 1.594/1.645,
1.737/1.536. Overturning failed at both ends: OVER, d/c 1.085 (sliding, loose end). Also
pinned: the IBC-coefficient fallback `μ 0.25` → sliding 0.575; a 3.0'/3.2' native terrace →
1.578 / 1.487.

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

**The returns retain to the north bench, not the south yard (2026-09-22).** Each return's
yard face reads the stations above, so its differential is 3'-0" (west) / 3'-1" (east), and
that is what `unbalanced_fill` now says (`params/raised_garden._APRON_RETURN_W/_E`). The old
3'-4" was the south yard's, transcribed onto both returns; on top of 12"/11" of yard → base it
put fill 4"/3" above the wall top, and the free body was capped at 4'-0" with a MISMATCH note.
Nothing graded moves with the fix: `H = H_r + min(yard→base, wall − H_r)` is 3.00 + 1.00 =
3.08 + 0.92 = **4.00'** both ways, so sliding 1.538/1.806, overturning 2.020, bearing
604/606 psf and d/c 0.975 stand, and the embedment row stays 12"/11". That invariance is the
check on the transcription.

* **Since 2026-09-22 an overtopping wall is INCOMPLETE**, not OK: the capped section is one
  neither authored input describes. OVER at both soil ends still stands.
* **Not taken: a seventh course.** `overtopped = retained + grade − top`; the base cancels,
  so a course with the base down fixes nothing, and a course with the top up takes H to
  4.33' and loose-end sliding to ≈1.42 — OVER.
* **Not taken: two `SpotElevation`s on the north bench at −3'-4".** That would make 3'-4"
  true, with a site-wide blast radius (R401.3, drainage arrows, grade profiles).

§3/§3b hold on all five legs. Unchanged by the unit.

## 5. Course interface shear

Demand: the horizontal thrust on the 3.333' above the base course — with the rock, the
critical wedge at that height (ρ 49.68° / 52.37°):

```
110:  P 121.31 × cos 6.545° = 120.52 plf      FS 645/120.52 = 5.35   ✓
130:  P 127.41 × cos 9.310° = 125.73 plf      FS 5.13                ✓
(native at the face: 149.14 / 141.39 plf, FS 4.32 / 4.56; AB Classic with rock 4.55 / 4.33)
```

645 lb/ft is AB's collection minimum at zero normal load; conservative.

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
   court's system FS 1.60. **AB Stones does not move it**: the strip is `γ_w H = 130 × 4.0 =
   520 psf` gross on the same 1'-0" pad under the same base course, and neither term reads the
   setback — so §4d, and the thermal break's §11d demand built on it, stand as they are. (The
   lean does move the resultant on that pad toward the heel, x̄ 0.22' → 0.47' from the toe:
   the real pressure is now nearly uniform where AB Classic's was toe-heavy, so the uniform
   strip §4d assumes describes AB Stones better, not worse.) The wall rock does not move it
   either: it replaces soil of the same weight band. `P_v` (21–30 plf) is still not carried
   onto the court — named, ungraded, ~5% of the unit's weight.
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

**Does the wedge even reach the court wall?** The critical plane exits `H cot ρ` behind the
heel. The 12° lean flattens the plane (ρ ~50° against ~52–55° at 6°), so now it does, at
both ends:

```
            native (§3)                     with rock (§3b)
110 pcf     4 cot 50.08° = 3.347'  > 2.974  4 cot 49.71° = 3.392'  > 2.974   by 0.37' / 0.42'
130 pcf     4 cot 52.52° = 3.067'  > 2.974  4 cot 52.38° = 3.082'  > 2.974   by 0.09' / 0.11'
```

(Measured from the base course's heel; the batter leans the top 0.85' toward the court, and
the exit point is set by the heel.)

The most a PLANAR surface restricted to the strip can remove is the difference between the
free maximum and `P` at the steepest-reaching plane, `ρ_hit = atan(4/2.974) = 53.37°`, with
rock: **110 pcf 181.27 → 177.39 (−2.14%)**, 130 pcf 187.18 → 186.85 (−0.18%). Crediting it
would lift loose-end sliding ~2%; it is not credited, so the verdict is conservative on this
count.

**And no published method credits it here.** Frydman & Keissar (1987, *J. Geotech. Eng.*
113(6), centrifuge, L/H 0.1–1.1), Leshchinsky & Hu (2003) and Lawson & Yee (2005, limit
equilibrium) are for granular fill. [Kniss, Yang, Wright & Zornberg
(2007)](https://sites.utexas.edu/zornberg/files/2022/03/Kniss_Yang_Wright_Zornberg_2007.pdf)
found their finite-element pressures at L/H 0.70 in "good agreement with the recommended
values" (i.e. no reduction for design) and warn the chart "is not appropriate when using
locally, naturally cohesive" soil. The retained soil here is presumed GM, run as clay at the
loose end. **Nothing is credited**; the record prints the check.

## 7. Against AB's own numbers, and AB's Table 1.3

| term | 2026-09-20 | 2026-09-21 a.m. | audit | **now** |
|---|---|---|---|---|
| unit | generic, solid | AB Classic 6° | AB Classic 6° | **AB Stones 12°** |
| thrust | Rankine EFP | Coulomb, inclined | two-zone trial wedge | two-zone trial wedge |
| sliding / OT FS (110) | 0.38 / 0.57 | 1.21 / 1.27 | 1.38 / 1.44 | **1.54 / 2.02** |
| tier row | 6.13 | 6.13 | not applied | not applied |

**Reproducing AB's method** (AB's `cos δ` resolution, δ 0.66φ, γ_s 120, d 0.97, 130 pcf,
μ tan φ, `0.33 H` lever arms as printed) — the total height at which the first FS reaches 1.5,
against Table 1.3 (manual p.10), whose heights are **exposed, including a cap**:

| soil | 12° this method | **Table 1.3 "12° AB Stones only"** | ratio | 6° this method | 6° chart | ratio |
|---|---|---|---|---|---|---|
| clay 27° | 3.28' (sliding) | **3'-6"** = 3.50' | 1.07 | 2.87' | 3'-2" | 1.10 |
| silty sand 32° | 5.52' (OT) | **5'-4"** = 5.33' | 0.97 | 4.15' | 4'-7" | 1.10 |
| sand/gravel 36° | 6.51' (OT) | **5'-10"** = 5.83' | 0.90 | 4.70' | 5'-2" | 1.10 |

(The 6° column re-run here reads 2.87 / 4.15 / 4.70 against the audit's 2.86 / 4.12 / 4.67 —
the audit used ⅓H, this uses AB's printed 0.33H. Neither changes a ratio past 0.01.) **At 12°
AB's chart is not uniformly generous**: it is ~7% over the sample method in clay and 3–10%
UNDER it in the sands — the page states the 12° system reaches "up to 5.5 ft … in good soils"
(p.10), which reads as a cap, not a calculation. The table is what AB publishes; the free body
is compared against it, not fitted to it.

**At each soil end:**

* **Clay end (27°, the loose end here).** Table 1.3 allows **3'-6"** exposed including a cap.
  The perimeter legs expose **3'-4"** with no cap modelled: 2" inside the row as built,
  2" over it if a 4" AB Capstone is added on top. The free body passes at 110 pcf (sliding
  1.54) — on the rock, which the chart also assumes. AB and the free body now agree at this
  end, narrowly, as they should: both put the wall at the edge of gravity-wall range in clay.
* **Silty-sand end (32°).** Table 1.3 allows **5'-4"**; 3'-4" is routine. The free body
  passes wide (OT 2.02).
* **AB's own resolution** at the free body's 4.0', same inputs as §3b: sliding **1.73 / 2.05**,
  OT **2.32 / 2.34** with rock; native, sliding 1.48 / 1.88 and OT 2.02 / 2.16. The geometric resolution
  graded here is the lower one at every term.

## 8. What closed it (the owner's decision, 2026-09-21)

Required: FS 1.5 on sliding and overturning, bearing within 2,000 psf, at both soil ends.

* **Taken: AB Stones (12° setback), keeping the 12" wall rock.** Sliding 1.54 / 1.81,
  overturning 2.02 / 2.02, bearing 604 / 606 psf (§3b). Same unit size, weight, depth, core
  fill and course height, so no other dimension of the apron moved. What it costs is ground:
  AB, p.18: 12° walls "require more space … You may give up ground, but the final factors of
  safety are higher" — 10" of lean at 4 ft, into the planting bed (§1).
* **Not taken, and superseded with AB Classic** (all figures on the 6° unit): 24" of wall rock
  (1.594/1.645, 1.737/1.536 — passed, on a length-weighted credit AB does not publish); a
  lower terrace (sliding 1.5 near `H ≈ 3.17'` native); a measured soil; geogrid SRW sealed by
  the supplier's engineer.
* **What still rests on inputs:** the loose-end sliding margin is 2.5% and holds only with
  the rock at AB's 36° (§3b sensitivities: 1.47 at 34°, 1.30 with no rock). Placing AB's
  specified clean wall rock — not a dirtier "crushed stone" — is part of the design.

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
* The batter's geometry — the model draws the wall plumb; the 12° lean lives on the spec (§1).
* A published chart row cannot close any of this; one authored on `srw.published` is refused
  unless drainage (a DRAINAGE layer or the spec's `drainage_zone`), a batter and a cap are
  stated and no taller wall stands within 2H — and the court walls still stand within 2H.

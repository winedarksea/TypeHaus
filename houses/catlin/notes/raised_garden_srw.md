# Raised-garden SRW apron — the gravity free body, by hand

Worked 2026-09-20, by hand and separately from `engineering/segmental_wall.py`. The arithmetic
is done on the authored geometry below with nothing imported from the engine;
`tests/test_segmental_wall.py` reproduces every number in §3–§6 against the engine.

**Result: all five legs fail sliding and overturning as drawn, and by a lot.** Sliding FS 0.38 and
overturning FS 0.57 against IRC R404.4's 1.5. This is not a borderline, and it does not turn
on the soil band, the unit weight or the batter. Nobody had calculated it before (§8).

**ERRATUM 2026-09-21: GM is 40 psf/ft active (IBC Table 1610.1), not 45.** §3–§8 below were
worked at 45 and stay as worked, as the mechanics oracle for `analyse` at that input. At 40,
by hand on the same section: `Pa = ½·40·4.0² = 320.0 plf`, `M_ot = 320.0·4/3 = 426.67`,
sliding `0.25·549.37/320.0 = 0.429` (d/c **3.49**), overturning `274.68/426.67 = 0.644`,
`x = (274.68 − 426.67)/549.37 = −0.277'`, `e = 0.777'` (d/c 1.55), course shear
`½·40·3.5² = 245.0 plf`. Still OVER on every leg; that is what the catlin records print.

## 1. What is authored

All five legs (`W-RG-BLOCK`, `-WEST`, `-EAST`, `-WEST-BALCONY`, `-EAST-BALCONY`) are the same
section. From `params/raised_garden.py`, `plan/assemblies.py`, `plan/site.py`,
`library/materials.py`:

| term | value | from |
|---|---|---|
| wall top | 0'-0" | `TOP` = court wall top |
| wall base | -4'-0" | `BASE` = `TOP - drop_ft` |
| retained height `H_r` | 3'-4" = 3.333' | `unbalanced_fill`, authored (**not** `drop_ft`) |
| yard | -3'-4" | the three south-yard grade stations |
| embedment `D` | -3'-4" − (-4'-0") = 8" = 0.667' | yard − base |
| unit depth `B` | 12" = 1.0' | `srw-block` STRUCTURE layer |
| batter | none | the model carries none; drawn vertical |
| unit weight `γ_w` | 2200 kg/m³ = 2200 / 16.018 = **137.34 pcf** | `retaining-block` density |
| soil | GM | `Site.soil_class` |
| active EFP `k` | 45 psf/ft | IBC Table 1610.1, GM |
| levelling pad | MnDOT Class 5, **not** declared `non_frost_susceptible` | `FootingBedding` |
| friction `μ` | 0.25 | IBC Table 1806.2 class 4 (the site's own row) |
| allowable bearing | 2,000 psf | IBC Table 1806.2 class 4 |

Two readings are forced by the model and worth saying:

* **μ = 0.25, not 0.35.** Class 5 is a dense-graded base with fines; nobody claims it is clean
  stone, so the interface is the site's own class 4 row. That is the same rule
  `retaining_basis._base_interface` applies to the court footings. Declaring the pad
  `non_frost_susceptible` (a clean, open-graded stone) would earn class 3's 0.35.
* **137 pcf is the SOLID-concrete density.** A real hollow SRW unit with aggregate infill weighs
  less in place (≈120 pcf is typical). 137 is therefore an **upper bound** on resistance: every
  failure below gets worse with a lighter unit, never better.

## 2. The free body, and why it is 4'-0" high

Rankine/EFP gravity wall, rigid, per metre of run. The retained soil stands on the whole back
face down to the base: `H = H_r + D = 3.333 + 0.667 = 4.0'`.

**Passive resistance on the 8" of embedment is NOT credited.** It is trench backfill against the
toe (plan "must not" #6, and `retaining_basis`'s own convention). Crediting nothing in front
while stopping the thrust at the yard would be crediting a balancing pressure on the embedment
by the back door — which is what the plan's headline hand pass did (§7). The consistent free body
runs the active triangle to the base.

The soil unit weight band (`SOIL_UNIT_WEIGHT_BAND_PCF`, 110–130) **does not enter**: the EFP
already carries γ, and a vertical unit with no heel carries no soil weight. Both ends of the band
give identical numbers; the calculation says so rather than printing two equal columns.

## 3. The arithmetic

```
thrust        Pa   = ½ · k · H²          = ½ · 45 · 4.0²      = 360.0 plf
               arm = H / 3               = 1.333 ft
overturning   M_ot = 360.0 · 1.333                             = 480.0 ft-lb/ft
weight        W    = γ_w · B · H          = 137.34 · 1.0 · 4.0  = 549.37 plf
restoring     M_r  = W · B/2             = 549.37 · 0.5        = 274.68 ft-lb/ft

sliding       FS = μ W / Pa   = 0.25 · 549.37 / 360.0  = 0.381   d/c = 1.5/0.381 = 3.93
overturning   FS = M_r / M_ot = 274.68 / 480.0         = 0.572   d/c = 1.5/0.572 = 2.62
```

**Bearing.** The resultant's distance from the toe is `x = (M_r − M_ot) / W =
(274.68 − 480.0) / 549.37 = −0.374 ft` — *in front of* the toe. There is no bearing pressure
to compute: the resultant is off the base and the wall has already rotated. The row is graded as
"resultant on the base" instead: eccentricity from the base centre `e = B/2 − x = 0.5 + 0.374
= 0.874 ft` against `B/2 = 0.5 ft`, **d/c 1.75**. (Where `x > 0` the row is ordinary bearing,
`q = W/B·(1 + 6e/B)` inside the kern and `2W/(3x)` outside it, against 2,000 psf.)

## 4. Base-course embedment

Required `max(6", H/10) = max(6", 4.8") = 6"`; provided 8". **d/c 0.75, passes.** The 2" of extra
drop `params/raised_garden.py` bought is what passes this row, and nothing else.

**The two balcony returns read a different station, and it disagrees with the authored fill.**
Embedment is measured to the NEAREST grade station (`resolve/site_earth.nearest_grade_station`):

| leg | midpoint | nearest station | ground | yard → base |
|---|---|---|---|---|
| `-BLOCK` | (18, -31.33) | (18, -38), 6.7' | -3'-4" | 8" |
| `-WEST` | (4, -20.92) | (-6, -22), 10.1' | -3'-4" | 8" |
| `-EAST` | (32, -20.92) | (41, -18), 9.5' | -3'-4" | 8" |
| `-WEST-BALCONY` | (5.75, -10.5) | (12, -2), 10.6' | -3'-0" | 12" → d/c 6/12 = 0.50 |
| `-EAST-BALCONY` | (30.25, -10.5) | (26, -3), 8.6' | -3'-1" | 11" → d/c 6/11 = 0.545 |

On the returns, 3'-4" retained over 12" (or 11") of ground is 4'-4" (4'-3"), taller than the
4'-0" wall. Fill cannot stand above the block, so the free body is **capped at the wall's own
4'-0"** and the record prints the disagreement. The §3 numbers therefore hold on all five legs.

## 5. Course interface shear

Needs the maker's interface shear capacity, which nothing names (§9). The demand it would be
graded against is the thrust above the top of the base course (one 6" course up):
`½ · 45 · (4.0 − 0.5)² = 275.6 plf`, at FS 1.5 → the unit has to publish ≥ 413 plf at this
normal load. Ungraded until authored; it does not affect the verdict, which is already OVER.

## 6. Tier independence — the number that is the point

The usual screen for two walls to be designed independently is a clear offset of at least twice
the LOWER wall's height. The lower walls are the court walls, which retain `9.12'`
(`unbalanced_fill` on `W-SG-W2/E2/S`).

Clear offset, apron face to court face: axis spacing 4.0' (`_step_out_ft`), minus half the 12"
block (0.5'), minus half the 12" court concrete (0.5'), minus the court's 5/16" dimple board on
its retained face (0.026'): **2.974'**.

```
2 · H_lower = 2 · 9.12 = 18.24'      offset 2.974'      d/c = 18.24 / 2.974 = 6.13
```

Graded on the three perimeter legs, each against the court wall parallel to it (`W-RG-BLOCK` ↔
`W-SG-S`, `-WEST` ↔ `W-SG-W2`, `-EAST` ↔ `W-SG-E2`). The two balcony returns run
perpendicular to every court wall and butt `W-SG-W1/E1`'s outer face end-on; no wall is parallel
to them, so no tier row is printed — the corner they close is the same terrace prism the side
legs' rows already grade.

**What the violation does and does not mean.** The court wall's active wedge, at the apron's
founding elevation (-4'-0", 5.12' above the court base), reaches `5.12 / tan(45° + φ/2)` past the
court wall's back face, where `tan²(45° − φ/2) = K_a = 45/γ`:

```
γ = 110 pcf:  K_a 0.409, 45°−φ/2 = 32.60°, wedge 57.40°, 5.12/1.563 = 3.27'  → 3.77' from court axis
γ = 130 pcf:  K_a 0.346, 45°−φ/2 = 30.47°, wedge 59.53°, 5.12/1.700 = 3.01'  → 3.51' from court axis
```

The apron's faces are at 3.5' and 4.5' from the court axis. **The levelling pad straddles the
wedge boundary at both ends of the band**: the apron is founded on soil the court wall is holding
up.

That is not the classic tiered failure, because the court cannot rotate away the way a free
gravity pair can: it is a closed cast loop, graded as one free body by
`retaining_system/W-SG-ARCH` (base restraint FS 1.628). What survives is a deep-seated slip under
the whole box, which `sunken_garden_court_free_body.md` §9 already lists as open *with or without
the apron*. The honest grading is: the tier row prints 6.13 as a number, the local rows (§3) fail
on their own, and global stability stays a geotechnical deliverable.

**The interaction the court DOES see is now carried (2026-09-20).** The apron's weight on its
pad is delivered to each parallel court wall as a lateral surcharge
(`engineering/tier_surcharge.py`, IBC 2018 §1610.1): a rigid-wall Boussinesq strip, 1'-0" wide,
starting at the court heel's virtual back (a = 0), 4'-0" below the retained surface, at the
block's 549.37 psf **net** of the 4'-0" of soil it displaces (109.4 psf at 110 pcf). Worked by
hand in `sunken_garden_court_free_body.md` §4c: +69.0 plf per wall, and the court loop
1.63 → **1.59**. Gross (not netted) it would be 1.46 — the note argues why net is the right
free body and prints the gross beside it. It is cited on each court record as
`via tiered_retaining/W-RG-BLOCK` (→ `W-SG-S`), `-WEST` (→ `W-SG-W2`), `-EAST` (→ `W-SG-E2`).

**The two balcony returns load nothing graded.** They run east-west at y −11..−10, beyond the
north ends of `W-SG-W2`/`-E2`, and butt `W-SG-W1`/`-E1` end-on; `lower_tiers` reads them as
not parallel to any court wall and no surcharge is carried. Their bearing lands behind
`W-SG-W1`/`E1`, braced walls on Table R404.1.2(8), which has no surcharge column — a small,
named, ungraded load.

## 7. Against the plan's headline numbers

The plan's headline (§1) worked `½·45·3.333² = 250 plf`, `120 pcf · 1.0 · 4.0 = 480 plf`,
`0.35 · 480 = 168` → FS 0.67, `M_r 240 / M_ot 278` → FS 0.86. That arithmetic is right *for its
assumptions*, and three of them disagree with the model:

| term | plan | here | why here |
|---|---|---|---|
| thrust height | 3.333' | 4.0' | no passive on the embedment (§2) |
| μ | 0.35 | 0.25 | the pad is not declared clean stone (§1) |
| γ_w | 120 pcf | 137.34 pcf | the model's own material; an upper bound |

Its own overturning also mixed frames (thrust stopped at the yard, moment taken about a toe 8"
lower). Both readings fail; this one fails by more, and it is the one that credits nothing
the plan says must not be credited.

Sensitivities, same free body:

```
γ_w 120 pcf         W 480.0    sliding 0.25·480/360 = 0.333   overturning 240/480 = 0.500
μ 0.35 (clean pad)  sliding 0.35·549.37/360 = 0.534
batter 9.5°         M_r = W(B/2 + H·tan9.5°/2) = 549.37(0.5 + 0.3347) = 458.5  → OT FS 0.955
```

## 8. What would close it (the owner's decision)

Everything required is FS 1.5 on sliding and overturning, and the resultant on the base.

* **Batter alone does not.** 9.5° (≈1" per 6" course, typical of a lipped unit) takes overturning
  to 0.955 and leaves sliding where it is — EFP publishes no batter reduction, so none is credited.
* **Drainage stone and a cap** do not move the free body at all; they are what a published chart
  *assumes* (§9) and what keeps the EFP from turning hydrostatic.
* **A deeper gravity unit.** Sliding needs `B ≥ 1.5 · 360 / (μ · 137.34 · 4.0)`: **3.93'** at
  μ 0.25, **2.81'** at μ 0.35. Overturning needs `B ≥ √(1.5 · 480 · 2 / (137.34 · 4.0)) = 1.62'`.
  No single SRW unit is 2.8' deep. This is a mass wall, not a unit selection.
* **A lower terrace.** For a 12" unit the sliding limit is `H ≤ μ γ_w B / (1.5 · ½ k)`:
  **1.02'** at μ 0.25, **1.42'** at μ 0.35 total height — i.e. roughly 4"–9" retained over 8" of
  embedment. Overturning alone would allow `H ≤ √(6 γ_w / (3 k)) = 2.47'`.
* **Geogrid-reinforced soil**, designed and sealed by the SRW supplier. The reinforced zone becomes
  the gravity mass (typically ≥ 0.6H deep, ≈2.4' here) — the only one of these that keeps a
  3'-4" terrace on a standard unit.

## 9. Not graded here

* Global stability of the apron and court on a common failure surface, against a measured soil
  profile — the geotechnical engineer's (§6; `sunken_garden_court_free_body.md` §9).
* ~~The surcharge the apron's bearing delivers to the court wall.~~ Carried since 2026-09-20
  on the court's own records (§6, `sunken_garden_court_free_body.md` §4c) — except the two
  balcony returns' load on `W-SG-W1`/`E1`, which stays ungraded (§6).
* The unit, the geogrid and the levelling pad — the SRW supplier's engineer, from product data:
  the interface shear (§5), the in-place unit weight, the batter, the cap.
* Hydrostatic, seismic and frost-heave cases. Every number presumes a drained backfill, and the
  assemblies declare no drainage layer behind the block.
* A published chart row cannot close any of this (plan "must not" #5). If one is authored on
  `FoundationWall.srw.published` it is refused unless the assembly declares a DRAINAGE layer, a
  batter and a cap are stated, and no taller wall stands within 2H — and the apron fails the last
  guard at every leg (the court walls are ≤ 3' away against 2H = 8').

# Rebar layout — hand-worked basis

**House:** catlin.
**Written:** 2026-09-17, by hand, before the layout code (decision #75).
**Oracle for:** `resolve/rebar/detailing.py` (§1, `tests/test_rebar_detailing_oracle.py`) and
the layout of three elements (§2–§4, `tests/test_rebar_layout_oracle.py`).

Conventions, stated once. Lengths are in inches unless marked. **Placed** is the run a bar
covers once; **lap** is the overlap a piece shares with the next; **hook** is bends and tails
past the out-to-out placed dimension; **cut = placed + lap + hook**. Mill stock is 20'-0"
(240") and a run is split when its developed length (placed + hooks) exceeds it:
`n = ceil((L_dev − lap) / (240 − lap))` pieces of equal cut length
`c = (L_dev + (n−1)·lap) / n`, lap carried by every piece but the last. (Equal pieces, not
full stock first: on a run just over stock, a full first piece reaches past the run's end
and leaves a second piece that is nothing but lap.) Spaced bars use the fencepost
`n = ceil(span / s) + 1`, evenly spread between the end bars (spacing is a maximum). Weights are ASTM A615 lb/ft: #3 0.376, #4 0.668, #5 1.043, #6 1.502.

## 1. Development, laps and hooks, #3–#6

ACI 318-19 Table 25.4.2.3, bars #6 and smaller, clear spacing and cover ≥ db:
`ld = fy ψt ψe ψg / (25 λ √f'c) · db`, fy 60,000, λ ψg ψe 1.0 (galvanized is ψe 1.0,
§25.4.2.5), ψt 1.3 for a bar with more than 12" of fresh concrete below it. `ld ≥ 12"`.

```
f'c 5,000:  60,000 / (25 × 70.711) = 33.941 db      f'c 4,000:  60,000 / (25 × 63.246) = 37.947 db
```

Laps (§25.5.2.1): class A 1.0 ld, class B 1.3 ld, both ≥ 12"; an unstated class is B.
Compression lap (§25.5.5.1, fy ≤ 60 ksi): 0.0005 fy db = 30 db, ≥ 12".

| bar | db | ld 5,000 | B 5,000 | B top-cast 5,000 | ld 4,000 | B 4,000 | compression |
|---|---:|---:|---:|---:|---:|---:|---:|
| #3 | 0.375 | 12.73 | 16.55 | 21.51 | 14.23 | 18.50 | 12.00 |
| #4 | 0.500 | 16.97 | 22.06 | 28.68 | 18.97 | 24.67 | 15.00 |
| #5 | 0.625 | 21.21 | 27.58 | 35.85 | 23.72 | 30.83 | 18.75 |
| #6 | 0.750 | 25.46 | 33.09 | 43.02 | 28.46 | 37.00 | 22.50 |

Hooks. The placed run ends at the outside face of the bend, `D/2 + db` past where the arc
begins; the hook allowance is the arc on the bar centreline plus the tail, less that:
`θ (D + db)/2 + ext − (D/2 + db)`.

* Standard 90° (Table 25.3.1): D 6 db, ext 12 db → `(π/2 · 3.5 + 12 − 4) db = 13.498 db`.
* Tie/stirrup 135° (Table 25.3.2, the §25.3.4 seismic hook): D 4 db (#3–#5; 6 db for #6+),
  ext max(6 db, 3").

| bar | std 90° allowance | tie 135°: arc + ext − (D/2+db) | tie 135° allowance |
|---|---:|---|---:|
| #3 | 5.062 | 2.209 + 3.000 − 1.125 | 4.084 |
| #4 | 6.749 | 2.945 + 3.000 − 1.500 | 4.445 |
| #5 | 8.436 | 3.682 + 3.750 − 1.875 | 5.557 |
| #6 | 10.123 | 6.185 + 4.500 − 3.000 | 7.685 |

A circular tie adds a 6" overlap to its two hooks (decision D5): #3 → 2 × 4.084 + 6 = 14.168.

## 2. FT-SG-S — the south retaining footing mat

84" × 240" strip, 12" deep, under `W-SG-S` (axis runs plan +X). Cover 3". Frame (D7):
`x` across the strip, `y` along it. Bar region = outline less 3" all round: **78" × 234"**.

| role | bars | positions | length each | total |
|---|---|---|---:|---:|
| bottom-x #5 @ 12" | ceil((234 − 0.625)/12) + 1 = **21** | pitch 233.375/20 = 11.669" | 78" | 1,638" = 136.50' = **142.37 lb** |
| top-x #5 @ 12" | **21** | same | 78" | 136.50' = **142.37 lb** |
| bottom-y #4 @ 18" | ceil((78 − 0.5)/18) + 1 = **6** | pitch 77.5/5 = 15.5" | 234" | 1,404" = 117.00' = **78.16 lb** |

Heights above the soffit: bottom-x 3.3125 (3 + 0.625/2); bottom-y on top of it, 3.875
(3 + 0.625 + 0.25); top-x 12 − 3.3125 = 8.6875. No run reaches stock; no laps, no hooks.

## 3. W-SG-S — the south retaining stem, as authored in Phase 4

12" wall, 240" axis, concrete 109.4375" tall (−9'-1 7/16" to 0'-0"), cover 3", f'c 5,000,
class B. The concrete layer is mitred at both corners: in wall coordinates (s along the
axis, t positive toward the court) its corners are `(−6,−6) (6,6) (234,6) (246,−6)`, so a
line at offset t spans `s ∈ [t, 240 − t]` for t < 0 and `[t, 240 − t]` for t > 0 alike.
The retained (exterior, dimple-board) face is t = −6. Both corners are L junctions with
reinforced walls (`W-SG-W2`, `W-SG-E2`).

**Verticals #6 @ 10", exterior face.** t = −6 + 3 + 0.375 = −2.625; s ∈ [−2.625, 242.625],
less cover → [0.375, 239.625], less db/2 → centres [0.75, 239.25].
`ceil(238.5/10) + 1 = 25` bars, each 109.4375 − 6 = 103.4375" → 2,585.94" = 215.50' =
**323.67 lb**.

**Horizontals #4 @ 16", both faces** (`layers=2`). Rows: `ceil((109.4375 − 6.5)/16) + 1 = 8`,
the lowest 3.25" above the base (not top-cast), the other seven top-cast.

* Exterior face sits behind the verticals: t = −6 + 3 + 0.75 + 0.25 = −2.0 → s ∈ [1, 239],
  **238"**. Interior face has no verticals: t = 6 − 3.25 = 2.75 → s ∈ [5.75, 234.25],
  **228.5"**.
* Each end hooks 90° into the corner wall: 2 × 6.749 = 13.498. Developed 251.498 / 241.998,
  both over 240 → **2 pieces a run**, each cut `c = (L_dev + lap)/2`. Piece 1's geometric
  length is `c − 6.749`; it laps piece 2 by `lap`; piece 2 runs to the end.

| run | lap | c = cut of each piece | piece 1 placed / lap / hook | piece 2 placed / hook | run cut |
|---|---:|---:|---|---|---:|
| ext, bottom row | 22.062 | (251.498 + 22.062)/2 = 136.780 | 107.969 / 22.062 / 6.749 | 130.031 / 6.749 | 273.560 |
| ext, top-cast ×7 | 28.680 | (251.498 + 28.680)/2 = 140.089 | 104.660 / 28.680 / 6.749 | 133.340 / 6.749 | 280.178 |
| int, bottom row | 22.062 | (241.998 + 22.062)/2 = 132.030 | 103.219 / 22.062 / 6.749 | 125.281 / 6.749 | 264.060 |
| int, top-cast ×7 | 28.680 | (241.998 + 28.680)/2 = 135.339 | 99.910 / 28.680 / 6.749 | 128.590 / 6.749 | 270.678 |

Check a row: ext bottom, piece 1 spans 0 → 130.031, piece 2 spans 107.969 → 238; placed
107.969 + 130.031 = 238 ✓.

Σ = 273.560 + 7 × 280.178 + 264.060 + 7 × 270.678 = 4,393.612" = 366.13' = **244.58 lb**,
**32 pieces**.

**Dowels #6, one at each vertical** (D6). `FT-SG-S` is 12" deep with 3" cover: the foot rests
at 3 + 0.375 = 3.375 above its soffit, so the embedded leg is 12 − 3.375 = **8.625** placed;
lap above the footing top is class B, **33.093**; the foot is a standard 90°, **10.123**.
Cut 51.841 × 25 = 1,296.03" = 108.00' = **162.22 lb**. (An 8 5/8" leg is short of a #6's
hooked development in 12" of footing. Nothing in the engine grades ldh; it is a reviewer's
item, not a layout one.)

## 4. PT-SG-COL — the garden column cage

12" round, 120.9375" tall (−11'-7 7/16" to −1'-6 1/2"), cover 2", `(4) #5` + `#3 @ 10"`.

* **Verticals:** on radius 6 − 2 − 0.375 − 0.3125 = 3.3125, at 45° + k·90°. Each
  120.9375 − 4 = 116.9375" → ×4 = 467.75" = 38.98' = **40.66 lb**.
* **Ties:** centres from 5" to 115.9375", `ceil(110.9375/10) + 1 = 13`, pitch 9.245". Radius
  6 − 2 − 0.1875 = 3.8125; placed 2π × 3.8125 = **23.955**; hooks + overlap **14.168**; cut
  **38.123**. ×13: placed 311.41" (25.95'), hook 184.18" (15.35'), cut 495.59" = 41.30' =
  **15.53 lb**.
* No dowels: `PT-SG-COL` is not a moment column (`balcony_moment_columns.md`).

## Sources

* ACI 318-19 §25.3 (hooks), §25.4.2.3 (development), §25.4.2.5 (coating), §25.5.2.1 and
  §25.5.5.1 (laps).
* ASTM A615/A615M Table 1 (bar mass).
* `notes/sunken_garden_court_free_body.md` §6–§7 (the stem and mat schedules),
  `notes/sunken_garden_piers.md` §4 (the cage).

# Rebar layout — hand-worked basis

**House:** catlin.
**Written:** 2026-09-17, by hand, before the layout code (decision #75).
**Oracle for:** `resolve/rebar/detailing.py` (§1, `tests/test_rebar_detailing_oracle.py`) and
the layout of three elements (§2–§4, `tests/test_rebar_layout_oracle.py`).

Conventions, stated once. Lengths are in inches unless marked. **Placed** is the run a bar
covers once; **lap** is the overlap a piece shares with the next; **hook** is bends and tails
past the out-to-out placed dimension; **cut = placed + lap + hook**. Mill stock is 40'-0"
(480", revised 2026-09-17 from 20': a fabricator cuts #4–#6 from 40' and 60' and laps only
past a handling length). A run is split when its developed length (placed + hooks) exceeds
stock: `n = ceil((L_dev − lap) / (480 − lap))` pieces of equal cut length
`c = (L_dev + (n−1)·lap) / n`; every other run of a role staggers its splices by half a
pitch, one piece more. Spaced bars use the fencepost `n = ceil(span / s) + 1`, evenly spread
between the end bars (spacing is a maximum). Weights are ASTM A615 lb/ft: #3 0.376,
#4 0.668, #5 1.043, #6 1.502.

**Revised 2026-09-17 after review** (decision #75 addendum): 40' stock and staggered laps;
walls lap at the greater of ACI class B and IRC Table R608.5.4(1); A767 ties bend at 6 db;
wall horizontals stop straight at cover and corner/splice bars carry them through a node;
the court stems run continuous from the footing on a 90° foot (#5 @ 7", §3) instead of
lapped #6 dowels, which could not develop in the 12" footing.

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

Wall laps (IRC R404.1.3.3.7.5 → Table R608.5.4(1), Grade 60): #4 30, #5 38, #6 45. A wall
laps at the greater of that and the class B figure above, so the IRC value governs every
wall size here (#3 has no row and stays ACI).

Hooks. The placed run ends at the outside face of the bend, `D/2 + db` past where the arc
begins; the hook allowance is the arc on the bar centreline plus the tail, less that:
`θ (D + db)/2 + ext − (D/2 + db)`.

* Standard 90° (Table 25.3.1): D 6 db, ext 12 db → `(π/2 · 3.5 + 12 − 4) db = 13.498 db`.
* Tie/stirrup 135° (Table 25.3.2, the §25.3.4 seismic hook): ext max(6 db, 3"). D is 4 db
  for #3–#5 in black bar, but **6 db for bar bent before galvanizing** (ASTM A767) — every
  catlin pour — and 6 db for #6+.

| bar | std 90° | tie 135°, A767 (D 6 db): arc + ext − (D/2+db) | tie 135° A767 | tie 135° black (D 4 db) |
|---|---:|---|---:|---:|
| #3 | 5.062 | 3.093 + 3.000 − 1.500 | 4.593 | 4.084 |
| #4 | 6.749 | 4.123 + 3.000 − 2.000 | 5.123 | 4.445 |
| #5 | 8.436 | 5.154 + 3.750 − 2.500 | 6.404 | 5.557 |
| #6 | 10.123 | 6.185 + 4.500 − 3.000 | 7.685 | 7.685 |

A circular A767 tie adds a 6" overlap to its two hooks (decision D5): #3 → 2 × 4.593 + 6 =
15.185.

Hooked development (§25.4.3.1(a)), for a bar hooked into the pour below:
`ldh = fy ψe ψr ψo ψc / (55 λ √f'c) · db^1.5`, ≥ max(8 db, 6"). At f'c 5,000, ψc =
5,000/15,000 + 0.6 = 0.933, ψe 1.0 (zinc), ψr 1.0 (bars ≥ 6 db apart), ψo 1.0 (side cover
≥ 6 db): `60,000 × 0.9333 / (55 × 70.711) = 14.399`.

| bar | db^1.5 | ldh 5,000 |
|---|---:|---:|
| #3 | 0.2296 | 6.00 (floor) |
| #4 | 0.3536 | 6.00 (floor) |
| #5 | 0.4941 | 7.115 |
| #6 | 0.6495 | 9.353 |

## 2. FT-SG-S — the south retaining footing mat

84" × 240" strip, 12" deep, under `W-SG-S` (axis runs plan +X). Cover 3". Frame (D7):
`x` across the strip, `y` along it. Bar region = outline less 3" all round: **78" × 234"**.
FT-SG-W2 and FT-SG-E2 each overlap its ends by 42" × 42"; the larger pour keeps the overlap's
mat, so this one is laid whole and theirs stop at its edge.

| role | bars | positions | length each | total |
|---|---|---|---:|---:|
| bottom-x #5 @ 12" | ceil((234 − 0.625)/12) + 1 = **21** | pitch 233.375/20 = 11.669" | 78" | 1,638" = 136.50' = **142.37 lb** |
| top-x #5 @ 12" | **21** | same | 78" | 136.50' = **142.37 lb** |
| bottom-y #4 @ 18" | ceil((78 − 0.5)/18) + 1 = **6** | pitch 77.5/5 = 15.5" | 234" | 1,404" = 117.00' = **78.16 lb** |

Heights above the soffit: bottom-x 3.3125 (3 + 0.625/2); bottom-y on top of it, 3.875
(3 + 0.625 + 0.25); top-x 12 − 3.3125 = 8.6875. No run reaches stock; no laps, no hooks.

## 3. W-SG-S — the south retaining stem

12" wall, 240" axis, concrete 109.4375" tall (−9'-1 7/16" to 0'-0") on FT-SG-S, cover 3",
f'c 5,000. The concrete layer is mitred at both corners: in wall coordinates (s along the
axis, t positive toward the court) its corners are `(−6,−6) (6,6) (234,6) (246,−6)`, so a
line at offset t spans `s ∈ [t, 240 − t]`. The retained (exterior) face is t = −6. Both
corners are L junctions with reinforced walls; the SW corner's bars belong to W-SG-S (first
by tag), the SE corner's to W-SG-E2.

**Verticals #5 @ 7", exterior face, continuous from the footing.** t = −6 + 3 + 0.3125 =
−2.6875; s ∈ [−2.6875, 242.6875], less cover → [0.3125, 239.6875], less db/2 → centres
[0.625, 239.375]. `ceil(238.75/7) + 1 = 36` bars. The foot rests on FT-SG-S's bottom mat:
3 + 0.625 (#5 bottom-x) + 0.5 (#4 bottom-y) = 4.125 above the soffit, bar centre 4.4375.
The straight leg runs to the wall top less cover, 12 + 109.4375 − 3 = 118.4375: **114.000**
placed; the foot is a standard 90°, **8.436**, turned across the stem toward the court.
Cut 122.436 × 36 = 4,407.70" = 367.31' = **383.10 lb**. No lap: 122" is under stock.

Anchorage: top of footing to the outside of the foot = 12 − 4.125 = **7.875** ≥ ldh #5
**7.115** ✓ (a #6 here needs 9.353 and does not fit — which is why the stem is #5 @ 7").

**Horizontals #4 @ 16", both faces** (`layers=2`). Rows: `ceil((109.4375 − 6.5)/16) + 1 = 8`.
No hooks; each row stops at cover and is one piece.

* Exterior face sits behind the verticals: t = −6 + 3 + 0.625 + 0.25 = −2.125 → s ∈
  [0.875, 239.125], **238.25**. Interior face has no verticals: t = 6 − 3.25 = 2.75 → s ∈
  [5.75, 234.25], **228.5**.
* 8 × 238.25 + 8 × 228.5 = 3,734.0".

**SW corner bars**, one per row per face (16), each an L lapping 30" (IRC #4, which governs
the class B 22.06/28.68) past both walls' bar ends. Outer: the lines at inset 3.875 cross at
s = −2.125 on the mitre; W-SG-S's bar end is at 0.875, 3.0 away, so the leg is 3.0 + 30 =
33.0, and W-SG-W2's is the same by symmetry. Inner (inset 3.25): cross at 2.75, bar end 5.75,
leg 33.0 each. Every corner bar: **66.0** cut = 6.0 placed + 60.0 lap. 16 × 66 = 1,056.0".

Horizontal role: 3,734.0 + 1,056.0 = 4,790.0" = 399.17' = **266.64 lb**, **32 pieces**.

## 4. PT-SG-COL — the garden column cage

12" round, 120.9375" tall (−11'-7 7/16" to −1'-6 1/2"), cover 2", `(4) #5` + `#3 @ 10"`.

* **Verticals:** on radius 6 − 2 − 0.375 − 0.3125 = 3.3125, at 45° + k·90°. Each
  120.9375 − 4 = 116.9375" → ×4 = 467.75" = 38.98' = **40.66 lb**.
* **Ties:** centres from 5" to 115.9375", `ceil(110.9375/10) + 1 = 13`, pitch 9.245". Radius
  6 − 2 − 0.1875 = 3.8125; placed 2π × 3.8125 = **23.955**; A767 hooks + overlap **15.185**;
  cut **39.140**. ×13: cut 508.82" = 42.40' = **15.94 lb**.
* No dowels: `PT-SG-COL` is not a moment column (`balcony_moment_columns.md`).

## Sources

* ACI 318-19 §25.3 (hooks), §25.4.2.3 (development), §25.4.2.5 (coating), §25.4.3.1
  (hooked development), §25.5.2.1 and §25.5.5.1 (laps).
* IRC 2021 R404.1.3.3.7.5 and Table R608.5.4(1) (wall laps); ASTM A767 (bend diameters of
  bar fabricated before galvanizing).
* ASTM A615/A615M Table 1 (bar mass).
* `notes/sunken_garden_court_free_body.md` §6–§7 (the stem and mat schedules),
  `notes/sunken_garden_piers.md` §4 (the cage).

## Addendum 2026-09-22 — the court narrowed to 17'-0"

§2/§3 were worked at a 240" south wall; it is **216"** now, and the layout re-derives by the same
steps: FT-SG-S 19 + 19 #5 at 78" (128.81 lb a face) and 6 #4 at 210" (70.14 lb); W-SG-S 32
verticals (340.54 lb), horizontals 214.25"/204.5" totalling 4,406" (245.27 lb). §4's PT-SG-COL
is RETIRED from the model; its cage stays the oracle for `lay_column`, rebuilt in the test from
this note's own inputs.

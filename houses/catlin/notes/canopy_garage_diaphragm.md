# The canopy braces off the garage — hand-worked basis

**House:** catlin
**Structure:** `RF-BW-CANOPY` delivering into `RF-GARAGE`, `W-G-S`, `W-G-E`, `W-G-W`; the east
supports `PT-BW-RE` / `PT-BW-RNE` in each of the three variants `EAST_POST_SYSTEM` selects
(`steel` | `kdat` | `cast`), their piers `PT-BW-PE` / `PT-BW-PNE` and pads `PD-BW-RE` / `-RNE`.
**Written:** 2026-09-29, by hand (plain arithmetic, no engine import), before
`engineering/roof_lateral.py`, `engineering/diaphragm_delivery.py` and
`engineering/steel_post.py` were encoded.
**Oracle for:** `engineering/roof_lateral.py` (§2), `engineering/diaphragm_delivery.py` (§3,
§4), `engineering/steel_post.py` (§5), the pinned-post pier path of `engineering/roof_moment.py`
/ `column_base.py` (§6) and the cast variant's receiving-line split (§7). Reproduced by
`tests/test_diaphragm_delivery_calcs.py` and `tests/test_steel_post_calcs.py`; the variant
item sets by `tests/test_catlin_east_post_variants.py`.
**Companions:** `entry_column_base_fixity.md` §7 — the wind bands and the cast shafts this
note starts from; `north_entry_canopy_lateral.md` §8 — the collectors, the hold-down
anchorage and the torsion arithmetic, which §7 below re-runs with one more line.
**What is asked of the reviewer:** whether the garage may take the canopy's whole lateral
load (§3-§4), and the §5 section. Every row here is under 0.92; nothing is near a limit
except the canopy deck's boundary at the screen line under the envelope (§4d). The west line,
its band and every head and base: `canopy_west_band.md`.

> ⚠ **The envelope is deliberate and it double-counts on purpose.** The garage path is graded
> at 100% of the delivered load, and `W-BW-SCREEN` and everything downstream of it
> (hold-down, anchorage, `deck_tie/FS-BW-FLOOR`) are ALSO graded at 100% of N-S. No
> stiffness judgement is made across the joint between two separately founded structures,
> and no relief is credited to either path (§8h of the lateral note's convention). If a
> screen row ever goes over, the fallback is a §1604.4 rigidity split with authored SDPWS
> schedules on the garage walls — not a smaller envelope.

> ⚠ **The plan's "about 811 lb E-W / 1,179 lb N-S" carried the 12" round's drag.** A 4" HSS
> catches a third of it. On the 5-1/2" x 11-7/8" glulam headers (2026-09-30) the delivered
> shears are 681.6 / 1,032.1 lb (steel) and 694.6 / 1,045.1 lb (KDAT). §2 works them.

> ⚠ **The west line is re-read in `canopy_west_band.md` (2026-09-30).** The screen stops 2'-4 1/8"
> under its header, the band is braced by CS16 X-straps, and the panel, its hold-down and every
> head and base are graded there. §4 below keeps only the deck-side rows.

---

## 1. Geometry and the three variants

| term | working | value |
|---|---|---|
| canopy footprint | x 4.667 → 31.333, y 37.219 → 43.219 | 26.667' x 6.000' |
| the joint | `CN-BW-JOINT-1..7`, x 6.0 → 30.0 at y 43.219 | 24.0', 7 `LSTA24` @ 4'-0" |
| headers | 5-1/2" x 11-7/8" glulam, y 37.271 → 43.219 (from the south post's face) | 5.948' long |
| header soffit | +7'-4" − 11.875" | +6.3438' |
| pier top (steel, kdat) | `Site.grade` −2'-10" + 3'-0" | +0.1667' (+0'-2") |
| post height | 6.3438 − 0.1667 | **6.1771'** (74.125") |
| pier exposed | 0.1667 − (−2.8333) | 3.000' |
| house-side pad top | −9'-9 7/16" + 12" moment pad… held at `FOOTING_TOP_FT` | −8.9531' |
| garage-side pad top | −7'-0" + 8" | −6.3333' |
| garage wall height | plates 8'-4" | 8.333' |

| variant | above the pier | pier | pad plane | end fixity |
|---|---|---|---|---|
| `steel` | HSS 4x4x1/4 A500 Gr C, 74.125" | 12" round to +0'-2" | house −9'-9 7/16" / garage −7'-0" | pinned-pinned |
| `kdat` (current) | 6x6 KDAT, ACE6Z/AC6Z head, cast-in CBSQ66-SDS2, PVC wrap | **14"** round (the CBSQ's cover) | the same pads | pinned-pinned |
| `cast` | 12" round, full height, one pour | none | −10'-2" (both, as 2026-09-20) | fixed base |

## 2. The demand the canopy delivers (oracles `roof_lateral.py`)

The pressure is §7a's, unchanged: `q_h` 18.335 psf, `G` 0.85, `C_f` 1.80, 0.6 for ASD —
**16.8315 psf** on any projected band. The headers' band grew with the glulam:

```
E-W   slope rise 4.444' x 6.000' + 2 headers 0.98958' x 5.9479'   = 38.439 sf ->  646.98 lb
N-S   gable-end triangle 2.222' x 26.667'                         = 59.259 sf ->  997.4 lb
```

**A pinned post splits its own drag half to the head and half to the base.** A member pinned
at both ends under a uniform load returns `wL/2` to each support; the head half joins the
deck, the base half goes down the pier and never reaches the diaphragm.

```
steel   16.8315 x (4.0/12) x 6.1771  = 34.66 lb per post  ->  17.33 lb head, 17.33 base
kdat    16.8315 x (5.5/12) x 6.1771  = 47.65 lb per post  ->  23.83 lb head, 23.83 base
```

A post framed into a wall (`within_wall`) is not in the sum: its face is the wall's, and
`PT-BW-CW`/`-CNW` stand inside `W-BW-SCREEN`. **The screen's own face is not in the
canopy's demand either**, exactly as §7a never counted it; it is in the landing tie's.

```
                 E-W                               N-S
steel    646.98 + 2(17.33) =  681.6 lb     997.4 + 2(17.33) = 1,032.1 lb
kdat     646.98 + 2(23.83) =  694.6 lb     997.4 + 2(23.83) = 1,045.1 lb
```

## 3. The delivery — joint, receiving roof, receiving lines (oracles `diaphragm_delivery.py`)

### 3a. Open front, SDPWS 4.2.5.2

Only the north edge is supported, so the canopy is an open-front diaphragm. `L'` is its
dimension normal to the open side, `W'` the one along it.

```
L'        6.000' vs 25'                    0.240
L'/W'     6.000 / 26.667 = 0.2250 vs 1.0   0.225   (one-story structure)
```

The deck stays **blocked** (`DiaphragmSpec.blocked`). With pinned east posts there is no second
N-S line on the canopy and the deck does not span — it cantilevers 6' off the joint. The
chord force, the couple's path into the garage and the drift limit are `canopy_west_band.md`
§6.

### 3b. The joint

**Attachment gap identified 2026-10-05 — the delivery is INCOMPLETE.** The numbers below
are nominal product-capacity comparisons, not a verified installed connection.
`CN-BW-JOINT-1..7` were authored at the +7'-4" plate datum and the renderer bent every
LSTA24 lengthwise as a ridge tie. They now mount directly beneath the roof deck, with
their 24" length running north-south across the joint. At station 6 (x = 26') the
structural top plane is +9'-8 3/4", not the plate elevation.

There are **no longitudinal nailing members** under these straps. Their centres are at
y = 43'-2 5/8"; the last canopy truss is at y = 41'-3 1/4", **23 3/8" south** of the
centre. A 12" strap leg cannot reach that truss. The garage gable truss at
y = 43'-3 3/8" crosses the strap but supplies only its chord width along the strap's
length; it does not supply a nine-nail end attachment. The continuous 3/4" sheathing
is not a substitute for those wood members. The modeled garage chord stock is also
SPF, whereas the ESR allowable quoted in the catalog assumes SG >= 0.50.
The current truss-to-truss bay is **24 1/8"**, rather than the older notes' 21 3/8".

Resolve the attachment before crediting the strap line: detail nailing wood on both
sides, its fastening into the diaphragms/framing, the butt/splice location, and the
full product nail schedule (18 common 0.148" x 2 1/2" nails total, nine per member for
the quoted ESR row), with compatible species and end/edge distances. Local strap
nailers are distinct from the garage diaphragm's general panel-edge blocking in §3d.
A longer strap alone still needs wood at both ends. No such members or fastening
have been invented by the visualization correction. `joint_attachment_missing`
keeps `lateral_system/RF-BW-CANOPY` incomplete while retaining the nominal arithmetic.
The published LSTA24 rating is **axial tension**, not a transverse shear rating; the
along-joint comparison below also needs a justified load path. Boundary nailing and
axial strap action must be distinguished in the completed attachment detail.
See [Simpson's LSTA installation guide](https://www.strongtie.com/resources/product-installers-guide/lsta-installation).

The E-W load runs ALONG the joint; the N-S load runs ACROSS it (strap tension). `LSTA24` is
ESR-2105 Table 3's 1,235 lb.

```
                                   steel                    kdat
boundary nailing, E-W   681.6/24.0 = 28.40 plf  0.149   694.6/24.0 = 28.94 plf  0.152
straps, along (E-W)     681.6/7  =  97.37 lb    0.079   99.23 lb                0.080
straps, across (N-S)   1032.1/7  = 147.44 lb    0.119   149.29 lb               0.121
```

**The E-W resultant is not on the joint.** Resultant y from the bands (roof at the footprint
centre 40.219, each post head at its own y):

```
kdat    y_V = (646.98 x 40.219 + 23.83 x 37.500 + 23.83 x 42.479) / 694.6 = 40.203
        e = 43.219 - 40.203 = 3.016'     M = 694.6 x 3.016 = 2,094.5 lb-ft
steel   y_V 40.207, e 3.011', M 2,052.6 lb-ft
```

As a linear couple over the strap stations at 0, ±4, ±8, ±12', Σx² = 448 ft²: worst strap
M x 12 / 448 = 56.10 lb, **0.045** (steel 54.98). The chords' reading of the same couple is
`canopy_west_band.md` §6.

### 3c. Gable frame into `W-G-S` — `CN-BW-GCLIP-1..7`

Seven **LTP4**, Simpson C-C-2019 p. 280, SPF/HF 540 / 450 lb at C_D 1.6, the lower taken:

```
steel   681.6 / 7 = 97.37 lb   vs 450   0.216
kdat    694.6 / 7 = 99.23 lb   vs 450   0.221
```

Nailed to the chord's and the plate's inside faces, not over sheathing, so footnote 3's 0.64
does not apply — and the drawings say so.

### 3d. The receiving roof, `RF-GARAGE`

3/4" Structural I, 8d at 6", **unblocked**, SDPWS Table 4.2A Case 1 at the 15/32" row, ASD
167.5 plf. 24' between `W-G-W` and `W-G-E` on a 24' depth: 1.0 against 3:1. Lever rule on the
N-S resultant's x:

```
kdat    x_V = (997.4 x 18.000 + 2 x 23.83 x 30.000) / 1045.1 = 18.547
        W-G-E 1045.1 x 12.547/24 = 546.4 lb     W-G-W 498.7 lb
        increment 546.4 / 24.0 = 22.76 plf vs 167.5   0.136
steel   x_V 18.403   W-G-E 533.4   W-G-W 498.7    22.22 plf   0.133
```

**No south-bay blocking is required**, so the drift trusses `truss-000`/`-001` are untouched.

### 3e. The receiving lines, IRC R301.1.3

On the **surplus** (provided less required, off `bracing_eval`), SDPWS 4.3A 15/32" 8d at 6",
**182.5 plf** ASD. Required on every garage line is 4.275'.

| line | provided | surplus | steel | kdat |
|---|---:|---:|---|---|
| `W-G-S` (E-W) | 20.417' | 16.142' | 681.6/16.142 = 42.22 plf, 0.231 | 43.03 plf, **0.236** |
| `W-G-E` (N-S) | 24.000' | 19.725' | 533.4/19.725 = 27.04 plf, 0.148 | 27.70 plf, 0.152 |
| `W-G-W` (N-S) | 21.667' | 17.392' | 498.7/17.392 = 28.67 plf, 0.157 | 28.67 plf, 0.157 |

### 3f. `W-G-S` overturning, and the two ends of it

The delivered shear over the whole provided length, times the wall height, NO dead load:

```
steel   v = 681.6 / 20.417 = 33.38 plf    T = 33.38 x 8.333 = 278.2 lb
kdat    v = 34.02 plf                     T = 283.5 lb
```

* **Beside `D-G-SERVICE`** a new **STHD14, `CN-G-BWHD-S-DR`**, cast into `W-GF-S-DR`'s 6" core
  (ESR-2920 6" stem row, 3,065 lb): 278.2 / 3,065 = **0.091** (kdat 0.092).
* **The SE corner needs no device.** R602.10.7 end condition 1: a 144" return on the same post.
* `CN-G-BWHD-SW` is on `W-G-W`. The E-W case reaches `W-G-W` and `W-G-E` as the joint couple,
  ±M / 24' = ±87.3 lb (kdat) on the E-W case — graded, and small (`canopy_west_band.md` §6).
  This line used to say the joint "closes" the couple before the garage sees it; the joint
  hands it on.

## 4. The screen's share — the envelope (steel and kdat)

### 4a-4c. The panel, its hold-down, its anchorage — moved

Read over the chords (`PT-BW-CW`/`-CNW`, 5.4375' out to out) rather than the wall's 6.573' run,
the 6" edge nailing is OVER (1.05); the panel is nailed at 4" edges (265 plf) and reads
**0.725** kdat (steel 1,032.1 / 5.4375 = 189.8, 0.716). The hold-down is a cast-in CBSQ66-SDS2
graded over the FULL frame height, 2,243.5 / 3,060 = **0.733** kdat (steel 2,221.0, 0.726), and
its anchorage is the CBSQ's own cracked row, so the ABU66SS / AB-058-10-SS / ACI Ch. 17 rows
are gone. All of it: `canopy_west_band.md` §4.

### 4d. The canopy deck along the screen line — the closest row on the page

The deck delivers the N-S case along its 6.000' west eave into the header, the collector:

```
steel   1032.1 / 6.000 = 172.01 plf vs 190    0.905
kdat    1045.1 / 6.000 = 174.18 plf           0.917
```

The governing row of the lateral record in both pinned variants.

### 4e. The landing tie

`deck_tie/FS-BW-FLOOR` reads the screen's share (1,045.1 lb of panel load N-S); its **E-W row
governs at 0.966 and does not read the screen's share at all**.

### 4f. The band over the panel — `canopy_west_band.md` §3

The screen stops at +4'-0" and the header's soffit is +6'-4 1/8": the band is braced by a CS16 X
on each face, 707.5 / 1,134 lb, **0.624**, with its plates bearing end-on on the chords (0.396)
and the deck's shear collected into the header by six LTP4 (0.387).

## 5. The steel post (oracles `steel_post.py`)

HSS 4x4x1/4, ASTM A500 Gr C (F_y 50 ksi, square), AISC Manual Table 1-12: A 3.37 in²,
I 7.80 in⁴, r 1.52 in, Z 4.69 in³, design wall t = 0.93 x 0.250 = 0.2325".

> **Worked on the 2026-09-29 geometry** — a 74.75" post under a 4 1/2" 3-ply header. On the
> glulam the post is 74.125" (KL/r 48.77, P_n/Ω 84.80 kip, axial 0.040) and the saddle bolts
> bear in 5 1/2" of 24F-V4 DF at G 0.50; the pure functions below are pinned on the note's own
> inputs, and the `steel` variant's record re-reads both off the model.

```
E7    b/t = (4.0 - 3 x 0.2325)/0.2325 = 14.20  vs  λ_r 1.40 sqrt(29,000/50) = 33.72   0.421
      nonslender, so E7's Q is 1.0 and E3 applies unreduced
E2    KL/r = 1.0 x 74.75 / 1.52 = 49.18  vs 200                                      0.246
E3    F_e = π² 29,000 / 49.18² = 118.35 ksi;   F_y/F_e = 0.4225 <= 2.25
      F_cr = 0.658^0.4225 x 50 = 41.90 ksi;   P_n = 41.90 x 3.37 = 141.19 kip
      P_n / Ω_c (1.67) = 84.54 kip
axial D + S   40 ft² x (10 + 73.7) + post 12.21 lb/ft x 6.229' = 3,424.1 lb       0.041
H1-1b drag    w = 16.83 x 4/12 = 5.61 plf, M = wL²/8 = 27.21 lb-ft
              M_c = 50 x 4.69 / 1.67 / 12 = 11.70 kip-ft
              0.0405/2 + 0.0272/11.70 = 0.023    (D + S taken with the full 0.6W: a bound)
```

**The saddle — two 5/8" HDG through-bolts, NDS 2018 §12.3.1, double shear, steel side
plates**, main member `BM-BW-RE` (3-ply 2x12 SP, l_m 4.5", G 0.55), side plates 1/4"
(F_es 87,000 psi), F_yb 45,000 psi. Uplift is perpendicular to the header's grain:

```
F_e⊥ = 6,100 G^1.45 / sqrt(D) = 6,100 (0.55)^1.45 / sqrt(0.625) = 3,242.8 psi
R_e  = 3,242.8 / 87,000 = 0.03727        K_θ = 1.25 (θ 90°)
k_3  = -1 + sqrt(2(1+R_e)/R_e + 2 F_yb (2+R_e) D² / (3 F_em l_s²)) = 12.170
I_m   D l_m F_em / (4 K_θ)                    = 1,824.1 lb
I_s   2 D l_s F_es / (4 K_θ)                  = 5,437.5
III_s 2 k_3 D l_s F_em / ((2+R_e) 3.2 K_θ)    = 1,513.4   governs
IV    2 D²/(3.2 K_θ) sqrt(2 F_em F_yb/(3(1+R_e))) = 1,891.5
Z' = 1,513.4 x C_D 1.6 x C_M 0.7 = 1,695.0 lb per bolt, 3,390.0 for the pair
uplift 0.6D + 0.6W = 40 x (16.8315 - 6.0) = 433.26 lb                               0.128
```

C_M 0.7 because the header's end is at an eave; the head's lateral is the post's own 17.5
lb of drag and is not a row. **Stainless and galvanized are never mixed at this joint**:
HDG bolts, HDG saddle, and a butyl isolation layer against the KDAT.

**The base — a welded plate on two cast-in 5/8" HDG anchors, ASTM F1554 Gr 36, on levelling
nuts over an open drained gap (no grout).** §8f's 12"-round case applies to the PAIR: at
h_ef 7.891" both cones are bounded by the pier's own 113.1 in², so the group's A_Nc is the
single centre bolt's and ψ_ec is 1.0.

```
breakout, T   φN_cbg 4,528 lb (unreduced reading, §8f)   T = 433.26/0.6 = 722.1 lb   0.159
steel, T      the pair: φN_sa = 0.75 x 2 x 0.226 x 58,000 = 19,662 lb               0.037
shear         the base drag 17.47/0.6 = 29.1 lb — well inside every §8f shear row
```

**The record grades the pair as §8f's single centred bolt**, rows and all: the group's
breakout is the same bounded cone, and one bolt's pullout and steel (57 ksi, the stainless
read) are half the pair's. That is the lower bound, so the rows print one bolt's φN_sa and
the tension row reads 722.1 / 4,528 = 0.159 either way.

The anchors stand in the drained gap and see bending under shear (AISC Design Guide 1 §3.5);
at 29 lb it is not a row, and it is named so the gap is never grouted to "fix" it.

### 5a. The 6x6 KDAT east posts (oracle `wood_roof_post.py`)

The east pair are 6x6 Southern Pine No. 2 KDAT under the glulam header: an `ACE6Z` end cap on
`PT-BW-RE`, an `AC6Z` on `PT-BW-RNE`, `A35Z` angles for the across-beam direction, and cast-in
`CBSQ66-SDS2` bases in 14" piers (2026-09-30; the heads, bases and their lateral rows are
`canopy_west_band.md` §5). The PVC column wrap is a finish, never a brace. The 2018 NDS
Supplement Table 4D's **wet-service Southern Pine timber row** gives F_c 525 psi, F_b 850 psi
and E_min 440,000 psi. The post is 5.5" square and 74.125" long (6.1771').

```
roof share        40 ft² x (10 + 73.7) psf + 6.1771' x 7.87 plf = 3,397 lb  (D + S)
slenderness       K l_u/d = 1.0 x 74.125 / 5.5 = 13.48 < NDS §3.7.1.4's 50
Fc*               525 x C_D 1.15 = 603.75 psi (snow)
FcE               0.822 x 440,000 / 13.48² = 1,990 psi
Cp                r = FcE/Fc* = 3.296, c = 0.8  ->  0.927
axial             Fc' A = 603.75 x 0.927 x 5.5² = 16,937 lb; d/c = 0.201
own drag          16.8315 psf x 5.5/12 x 6.1771 = 47.65 lb, half at each end
bending           w L²/8 = 36.8 lb-ft; f_b = 15.9 psi vs wet Fb x C_D 1.6 = 1,360 psi
interaction       (f_c/Fc' + f_b/Fb') / (1 - f_c/FcE) = 0.225
IRC R507.4        6.177' < 14' 6x6 limit (cross-check; the roof's drift snow needs NDS)
```

**Product and moisture condition.** ESR-2604 §3.2.2 and ESR-3050 §4.1 rate the cap and the base
at wood moisture content ≤ 19%. Install KDAT dry and verify that limit before closing the wrap.
The PVC must be a nonstructural, screw-fastened four-sided jacket with an accessible panel,
open at the bottom above the pier wash and vented at the top below the cap; its top sheds water
outward. Keep the CBSQ's 1" standoff visible and draining. If the wrap cannot dry or permit
inspection, the connectors' published ratings are not earned.

## 6. The pier under a pinned post (oracles the pinned path into `column_base`)

A pinned post hands its base drag to the pier top; the pier adds its own drag over the 3.0'
it stands out of grade. Both go into the soil as a short pole, IBC 1807.3.2.1
non-constrained at S1 150 psf/ft (Table 1806.2 class 4, GM) taken at d/3:

```
steel   P = 17.33 + 16.8315 x 1.0 x 3.0 = 17.33 + 50.49 = 67.82 lb
        M at grade = 17.33 x 3.0 + 50.49 x 1.5 = 127.7 lb-ft    h = 1.883'
        A = 2.34 P / (S1 b),  d = 0.5 A (1 + sqrt(1 + 4.36 h / A)), S1 at d/3  ->  d = 2.422'
kdat    14" pier: P = 23.83 + 16.8315 x (14/12) x 3.0 = 82.74 lb, h = 1.932'  ->  d = 2.478'
```

| pier | shaft embedment (grade to pad top) | steel | kdat |
|---|---:|---|---|
| `PT-BW-PE` on `PD-BW-RE` | 6.120' | 0.396 | 0.405 |
| `PT-BW-PNE` on `PD-BW-RNE` | 3.500' | 0.692 | 0.708 |

The shaft alone; `column_base` basis 4 credits the doweled pad and reads lower. **The pads
leave −10'-2"**: `PD-BW-RE` sits on the house-side plane (`PIER_BOTTOM_FT`), where the house
strip beside it bears, so the 1'-4 9/16" undermining step is gone; `PD-BW-RNE` sits on the
garage plane, so the 3'-2" drop under the stone strip is gone; and `RE`'s lateral capacity no
longer rests on the basement overdig's backfill at all — 2.4' of it is needed against 6.1'.
Both piers keep the moment cage and 12" pad of every other entry pier (14" round in `kdat`,
for the CBSQ's cover), so the switch to `cast` needs no new pad form. Axial is `deck_post`'s tied-column row at d/c ~0.01.

## 7. The cast variant — columns share E-W by rigidity with `W-G-S`

The columns are the 2026-09-20 design unchanged: h 16.5625' from −10'-2", k = 3EI/h³ =
1,567.7 lb/in (gross, §7c), propped heads 96.01 lb each, E-W diaphragm shear 821.3 lb. `W-G-S`
lies on the canopy's north boundary, so it is stationed as a third E-W line. Its stiffness
is SDPWS 4.3-1's shear term on its SURPLUS length (the required 4.275' is spent on the
garage's own wind): `1000 G_a L / h = 1000 x 11 x 16.142 / 8.333 = 21,307 lb/in`. Bending
and anchorage slip are not stated for a prescriptive wall; leaving them out makes the wall
stiffer and the columns' share smaller, **which is why the garage rows keep 100%**.
`W-G-E`/`W-G-W` stand under `RF-GARAGE`, not on the canopy's boundary, and are not stationed.

```
stations  RE 37.500   RNE 42.479   W-G-S 43.219      span 5.719'
tributary 0.4353      0.5000       0.0647            avg drift 0.164"
deck      SDPWS 4.2.2 at 15.4 plf on 5.719 x 26.667  = 0.0318"   ratio 0.19x -> RIGID
rigid     0.0641      0.0641       0.8717
torsion   y_r 42.805, y_V 40.165, e -2.639', M_t 2,167.8 lb-ft, J 1,421,846 lb/in-ft²
          (N-S lines as §8g: panel 9,970.5 at x 6, columns at x 30, x_r 11.742)
          increments RE +12.68, RNE +0.78 lb
E-W top   RE 52.68 + 12.68 = 65.36 lb   M = 65.36 x 16.5625 + 552.7 = 1,635.2 lb-ft
N-S       V 1,189.4, e 8.196', direct 142.28 + torsion 196.24 = 338.52 lb
          M = 338.52 x 16.5625 + 552.7 = 6,159.4 lb-ft   base V 424.0 lb at 14.53'
```

**N-S now governs both cast columns**, because E-W collapsed onto the wall. Embedment, shaft
alone at h = 14.53 − 7.333 = 7.19' above grade: d = **6.59'** against the 8.333' the pad
bottom gives — **0.79** (basis 4's pad credit reads lower). −10'-2" is kept: it is the plane
this variant was designed and drawn on, and a shallower one is a separate decision this note
does not make. The garage rows are graded at 821.3 lb E-W (100%) and 1,189.4 lb N-S (100%);
every one is under its steel value x 1.24, so under 0.28.

**The screen, in `cast`, keeps its share of the canopy's OWN frame** — 82.5% at the cracked
columns, 981 lb, 0.82, as 2026-09-20 — and is not taken at 100% here. The envelope refuses a
stiffness judgement ACROSS the joint; the split between the screen and the cast columns is
inside one structure, stands on §7c's arithmetic, and is the one the columns' own demand
comes from. The §4 envelope applies on an axis where the canopy has no frame of its own,
which is N-S in the two pinned variants.

## 8. Differential movement

The canopy's north line (`RNE`, and `GW` under the west header) bears on the garage's own
−7'-0" plane; its south line (`RE`, `W`) on the house-side −9'-9 7/16" plane. The headers are
simple spans between the two, so a differential between planes rotates each header as a rigid
body and bends nothing. **Tolerance: 3/16"** — L/360 of the 5.719' header, the order the
H2.5ASS truss ties and the LSTA24 strap line take without distress. No settlement is computed
(the soil is presumed); a soils report that predicts more than 3/16" between the two planes
reopens this section. What the design removed is the larger case: before today the north
column sat 3'-2" below the garage strip it lapped.

## 9. What would send us back to B or C — none fires

| trigger | where | today |
|---|---|---|
| landing tie or screen OVER at the envelope | §4, §4e | 0.906 / 0.966, both under |
| `W-G-S` surplus or overturning needs more than a hold-down | §3e, §3f | 0.230 and one STHD14 |
| garage-roof blocking unbuildable round the drift trusses | §3d | none required |

## 10. What is NOT graded here

* The canopy's truss chords (delegated on the truss order, §8b of the lateral note).
* The garage's own wind, which stays prescriptive (R602.10) and is not added to these rows.
* A settlement analysis (§8); the soil is presumed.
* The screen's own face in the canopy's demand (§2 — it is the landing tie's).
* Weld design of the saddle and the base plate, which is the fabricator's shop drawing
  against AWS D1.1; this note fixes the parts and the forces, not the welds.

## Sources

- ASCE 7-16 §26.2, §29.3, §2.4.1.
- AWC SDPWS-2015 §4.2.2, §4.2.5.2, Tables 4.2A and 4.3A, §4.3.2.
- IBC 2018 §1604.4, §1806.2, §1807.3.2.1; IRC 2018 R301.1.3, R602.10.3, R602.10.7.
- AISC 360-16 §B4.1 (Table B4.1a case 6), §E2, §E3, §E7, §H1.1; AISC Manual Table 1-12.
- AWC NDS 2018 §12.3.1 (yield limit equations), Table 12.3.3 notes, §11.3.3 (C_M).
- ACI 318-19 Ch. 17 as in `north_entry_canopy_lateral.md` §8f.
- Simpson Strong-Tie C-C-2019 p. 280, LTP4 row, directions G/H.
- ICC-ES ESR-2105 Table 3 (LSTA24); ESR-2920 (STHD14, 6" ICF stem); ESR-1622 (ABU66SS).
- ASTM A500 Gr C; ASTM A123 (galvanizing after fabrication); ASTM F1554 Gr 36.

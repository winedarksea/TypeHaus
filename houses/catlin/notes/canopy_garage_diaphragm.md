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
except the canopy deck's boundary at the screen line under the envelope (§4d).

> ⚠ **The envelope is deliberate and it double-counts on purpose.** The garage path is graded
> at 100% of the delivered load, and `W-BW-SCREEN` and everything downstream of it
> (hold-down, anchorage, `deck_tie/FS-BW-FLOOR`) are ALSO graded at 100% of N-S. No
> stiffness judgement is made across the joint between two separately founded structures,
> and no relief is credited to either path (§8h of the lateral note's convention). If a
> screen row ever goes over, the fallback is a §1604.4 rigidity split with authored SDPWS
> schedules on the garage walls — not a smaller envelope.

> ⚠ **The plan's "about 811 lb E-W / 1,179 lb N-S" carried the 12" round's drag.** A 4" HSS
> catches a third of it. The delivered shears are 664.3 / 1,032.4 lb (steel) and 677.4 /
> 1,045.5 lb (KDAT). §2 works them.

---

## 1. Geometry and the three variants

| term | working | value |
|---|---|---|
| canopy footprint | x 4.667 → 31.333, y 37.219 → 43.219 | 26.667' x 6.000' |
| the joint | `CN-BW-JOINT-1..7`, x 6.0 → 30.0 at y 43.219 | 24.0', 7 `LSTA24` @ 4'-0" |
| header soffit | +7'-4" − 11.25" | +6.3958' |
| pier top (steel, kdat) | `Site.grade` −2'-10" + 3'-0" | +0.1667' (+0'-2") |
| post height | 6.3958 − 0.1667 | **6.2292'** (74.75") |
| pier exposed | 0.1667 − (−2.8333) | 3.000' |
| house-side pad top | −9'-9 7/16" + 12" moment pad… held at `FOOTING_TOP_FT` | −8.9531' |
| garage-side pad top | −7'-0" + 8" | −6.3333' |
| garage wall height | plates 8'-4" | 8.333' |

| variant | above the pier | pier | pad plane | end fixity |
|---|---|---|---|---|
| `steel` | HSS 4x4x1/4 A500 Gr C, 74.75" | 12" round to +0'-2" | house −9'-9 7/16" / garage −7'-0" | pinned-pinned |
| `kdat` (current) | 6x6 KDAT, as `PT-BW-CW`, with nonstructural PVC wrap | the same pier | the same pads | pinned-pinned |
| `cast` | 12" round, full height, one pour | none | −10'-2" (both, as 2026-09-20) | fixed base |

## 2. The demand the canopy delivers (oracles `roof_lateral.py`)

The pressure is §7a's, unchanged: `q_h` 18.335 psf, `G` 0.85, `C_f` 1.80, 0.6 for ASD —
**16.8315 psf** on any projected band. The roof and header bands are §7a's too:

```
E-W   slope rise 4.444' x 6.000' + 2 headers 0.9375' x 5.719'  = 37.389 sf ->  629.3 lb
N-S   gable-end triangle 2.222' x 26.667'                     = 59.259 sf ->  997.4 lb
```

**A pinned post splits its own drag half to the head and half to the base.** A member pinned
at both ends under a uniform load returns `wL/2` to each support; the head half joins the
deck, the base half goes down the pier and never reaches the diaphragm.

```
steel   16.8315 x (4.0/12) x 6.2292  = 34.95 lb per post  ->  17.47 lb head, 17.47 base
kdat    16.8315 x (5.5/12) x 6.2292  = 48.05 lb per post  ->  24.03 lb head, 24.03 base
```

A post framed into a wall (`within_wall`) is not in the sum: its face is the wall's, and
`PT-BW-CW`/`-CNW` stand inside `W-BW-SCREEN`. **The screen's own face is not in the
canopy's demand either**, exactly as §7a never counted it; it is in the landing tie's
(`deck_tie/FS-BW-FLOOR`, which grades 407.5 lb of it E-W).

```
                 E-W                              N-S
steel    629.3 + 2(17.47) =  664.3 lb     997.4 + 2(17.47) = 1,032.4 lb
kdat     629.3 + 2(24.03) =  677.4 lb     997.4 + 2(24.03) = 1,045.5 lb
```

## 3. The delivery — joint, receiving roof, receiving lines (oracles `diaphragm_delivery.py`)

### 3a. Open front, SDPWS 4.2.5.2

Only the north edge is supported, so the canopy is an open-front diaphragm. `L'` is its
dimension normal to the open side, `W'` the one along it.

```
L'        6.000' vs 25'                    0.240
L'/W'     6.000 / 26.667 = 0.2250 vs 1.0   0.225   (one-story structure)
```

The deck stays **blocked** (`DiaphragmSpec.blocked`): the unit-shear rows below read the
blocked row, and 4.2.5.2's exception for a WSP deck up to 1.5:1 is not needed at 0.225. The
old 4:1 span-to-depth row assumed a 24' span between the screen and the east columns; with
pinned east posts there is no second N-S line on the canopy and the deck does not span —
it cantilevers 6' off the joint. That row is kept only where cast columns stand (§7).

### 3b. The joint

The E-W load runs ALONG the joint (boundary shear in the nailing of the last bay onto
`RF-GARAGE`'s gable frame, and shear in the straps); the N-S load runs ACROSS it (strap
tension). `LSTA24` is ESR-2105 Table 3's 1,235 lb, the §8e read.

```
                                   steel                    kdat
boundary nailing, E-W   664.3/24.0 = 27.68 plf  0.146   677.4/24.0 = 28.22 plf  0.149
                        against the canopy row 190 plf (8d @ 6" boundary, blocked)
straps, along (E-W)     664.3/7  =  94.90 lb    0.077   96.77 lb                0.078
straps, across (N-S)   1032.4/7  = 147.48 lb    0.119   149.35 lb               0.121
```

**The E-W resultant is not on the joint, and the couple it leaves is the rotation 4.2.5.2 is
about.** Resultant y from the bands (roof at the footprint centre 40.219, each post head at
its own y):

```
steel   y_V = (629.3 x 40.219 + 17.47 x 37.500 + 17.47 x 42.479) / 664.3 = 40.207
        e = 43.219 - 40.207 = 3.012'     M = 664.3 x 3.012 = 2,000.8 lb-ft
```

The strap line resists it as a linear couple across its seven stations at x_i = 0, ±4, ±8,
±12' from its centre, Σx² = 448 ft²:

```
worst strap = M x 12 / 448 = 53.59 lb  -> 0.043        (kdat 54.73 lb, 0.044)
```

### 3c. Gable frame into `W-G-S` — new, `CN-BW-GCLIP-1..7`

The E-W load arrives in `RF-GARAGE`'s south gable frame, which bears on `W-G-S`'s plate for
its whole length. It crosses into the wall through seven **LTP4** plates, one per strap
station. Simpson C-C-2019 p. 280, LTP4 with (12) 0.131" x 1 1/2", load directions G / H:
DF/SP 625 / 525, **SPF/HF 540 / 450 lb** at C_D 1.6. The garage frames SPF; the lower
direction is taken so no direction needs knowing.

```
steel   664.3 / 7 = 94.90 lb   vs 450   0.211      (27.7 plf against 112.5 plf of clips)
kdat    677.4 / 7 = 96.77 lb   vs 450   0.215
```

Footnote 3 applies: over 1/2" sheathing with 1 1/2" nails the plate carries 0.64 of the
listed load. These plates land on the chord and the top plate's inside faces, not over
sheathing, so the full value stands — and the drawings say so.

### 3d. The receiving roof, `RF-GARAGE`

`RF-GARAGE` gets a `DiaphragmSpec` of its own: 3/4" Structural I, 8d at 6" boundary and
edges, 12" field, **unblocked** — SDPWS Table 4.2A Case 1, quoted at the 15/32" row, ASD
167.5 plf, `G_a` 7.0 kips/in at the soft end. It spans 24' between `W-G-W` and `W-G-E` on a
24' depth: 1.0 against 3:1 unblocked. The N-S load enters along its south gable as a line
load and is split by the lever rule on the resultant's x:

```
steel   x_V = (997.4 x 18.000 + 2 x 17.47 x 30.000) / 1032.4 = 18.406
        W-G-E  1032.4 x (18.406 - 6)/24 = 533.7 lb     W-G-W  498.7 lb
        unit-shear increment 533.7 / 24.0 = 22.24 plf vs 167.5   0.133
kdat    x_V 18.552   W-G-E 546.8   W-G-W 498.7    22.78 plf   0.136
```

This is the **increment** the canopy adds; the garage's own roof shear is the prescriptive
path's and is not computed here. **No south-bay blocking is required** — at 0.13 unblocked
there is nothing to trade, so the drift trusses `truss-000`/`-001` are untouched, which is
the third of the "back to B or C" triggers and it does not fire.

### 3e. The receiving lines, IRC R301.1.3

Each line keeps its R602.10 grade for the garage's own wind (`structural.braced_wall_panels`,
unchanged). The delivered load is graded on the **surplus** — provided less required, off
`bracing_eval` — at the authored SDPWS 4.3A row, 15/32" with 8d at 6" edges, **182.5 plf**
ASD wind (the screen panel's own row). Required on every garage line is 4.275'
(4.5' x 1.00 x 0.95).

| line | provided | surplus | steel | kdat |
|---|---:|---:|---|---|
| `W-G-S` (E-W) | 20.417' | 16.142' | 664.3/16.142 = 41.15 plf, **0.225** | 41.96 plf, 0.230 |
| `W-G-E` (N-S) | 24.000' | 19.725' | 533.7/19.725 = 27.06 plf, 0.148 | 27.72 plf, 0.152 |
| `W-G-W` (N-S) | 21.667' | 17.392' | 498.7/17.392 = 28.68 plf, 0.157 | 28.68 plf, 0.157 |

### 3f. `W-G-S` overturning, and the two ends of it

The delivered shear spread over the whole provided length, times the wall height, with NO
dead load credited:

```
steel   v = 664.3 / 20.417 = 32.54 plf    T = 32.54 x 8.333 = 271.1 lb
kdat    v = 33.18 plf                     T = 276.5 lb
```

* **Beside `D-G-SERVICE` (station 43", the door's east jamb)** the panel end meets an
  opening, and a CS-WSP line asks nothing there for the garage's own wind — but the canopy's
  increment is outside that prescriptive answer. **A new STHD14, `CN-G-BWHD-S-DR`**, cast
  into `W-GF-S-DR`'s 6" core like `CN-G-BWHD-SW` (ESR-2920 6" stem row, 3,065 lb):
  271.1 / 3,065 = **0.088** (kdat 0.090). Cheap and decisive against a 0.6D argument that
  would rest on a guessed wall weight (7.5 psf gives 189 lb, short of 271).
* **The SE corner needs no device.** It is R602.10.7 end condition 1: `BWP-G-E-0000` is a
  144" return on the same corner post, against the 24" a return needs. Graded as detailing.
* `CN-G-BWHD-SW` is on `W-G-W` and unaffected: the E-W load reaches `W-G-W` only as the
  §3b couple, which the joint closes before the garage sees it.

## 4. The screen's share — the envelope (steel and kdat)

### 4a. The panel at 100% of N-S

```
steel   1032.4 / 6.573 = 157.06 plf vs 182.5     0.861
kdat    1045.5 / 6.573 = 159.06 plf              0.872
aspect  4.083 / 6.573 = 0.621 vs 3.5             0.178   (unchanged)
```

### 4b. Its hold-down (`ABU66SS`, 2,190 lb, no dead load)

```
steel   1032.4 x 4.083 / 6.573 = 641.3 lb    0.293      kdat 649.4 lb, 0.297
```

### 4c. Its anchorage, §8f's arithmetic at the envelope

```
steel   T = (641.3 + 433.2) / 0.6 = 1,790.8 lb / 4,528 = 0.396
        V = 1032.4 / 2 / 0.6     =   860.3 lb / 3,661 = 0.235
        17.8.3   (0.396 + 0.235) / 1.2 = 0.525
kdat    0.398 / 0.238 -> 0.530
```

### 4d. The canopy deck along the screen line — the closest row on the page

If the screen takes the whole N-S case, the deck delivers it along the screen's 6.000' of
boundary:

```
steel   1032.4 / 6.000 = 172.06 plf vs 190    0.906
kdat    1045.5 / 6.000 = 174.25 plf           0.917
```

This is an envelope row over an envelope share and it is the governing row of the lateral
record in both pinned variants. It is the row that would send the design to the §1604.4
fallback if the canopy's demand ever grew by a tenth.

### 4e. The landing tie

`deck_tie/FS-BW-FLOOR` reads the screen's share. Its N-S row rises with it (980.7 → 1,032.4
lb of panel load, about 0.64 → 0.67); its **E-W row governs at 0.966 and does not read the
screen's share at all**, so the landing verdict is unchanged. The fallback trigger does not
fire.

## 5. The steel post (oracles `steel_post.py`)

HSS 4x4x1/4, ASTM A500 Gr C (F_y 50 ksi, square), AISC Manual Table 1-12: A 3.37 in²,
I 7.80 in⁴, r 1.52 in, Z 4.69 in³, design wall t = 0.93 x 0.250 = 0.2325".

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

The east pair are 6x6 Southern Pine No. 2 KDAT on `CCQ46SDS2.5` heads and `ABU66SS`
stainless standoff bases. The PVC column wrap is a finish, never a brace or a larger wood
section. The 2018 NDS Supplement Table 4D's **wet-service Southern Pine timber row** gives
F_c 525 psi, F_b 850 psi and E_min 440,000 psi; the dry row must not be substituted. The
post is 5.5" square and 74.75" long between its pinned connectors (6.2292').

```
roof share        40 ft² x (10 + 73.7) psf + 6.2292' x 7.87 plf = 3,397 lb  (D + S)
slenderness       K l_u/d = 1.0 x 74.75 / 5.5 = 13.59 < NDS §3.7.1.4's 50
Fc*               525 x C_D 1.15 = 603.75 psi (snow)
FcE               0.822 x 440,000 / 13.59² = 1,958 psi
Cp                [(1+r)/(2c)] - sqrt([(1+r)/(2c)]² - r/c) = 0.926,
                  r = FcE/Fc* = 3.244, c = 0.8 (sawn lumber)
axial             Fc' A = 603.75 x 0.926 x 5.5² = 16,910 lb; d/c = 0.201
own drag          16.8315 psf x 5.5/12 x 6.2292 = 48.05 lb, half at each end
bending           w L²/8 = 37.4 lb-ft; f_b = 16.2 psi vs wet Fb x C_D 1.6 = 1,360 psi
interaction       (f_c/Fc' + f_b/Fb') / (1 - f_c/FcE) = 0.226
                  conservative uniaxial screen of NDS §3.9; D + S with full 0.6W
IRC R507.4        6.229' < 14' 6x6 limit (cross-check; the roof's drift snow needs NDS)
```

The head cap has 6,785 lb uplift and 24,065 lb download in ICC-ES ESR-2604 Table 2;
the KDAT's SYP G 0.55 meets §3.2.2's 0.50 minimum. The base's bolted ABU66SS row,
transferred by Simpson L-F-SSNAILS from the ABU66, is 2,190 lb uplift and 18,205 lb
download. Net uplift is 433.3 lb (d/c 0.064 head, 0.198 base); download is 3,397 lb
(0.141 head, 0.187 base). The **stainless 5/8" cast-in base anchor** is separate from the
ABU rating: §8f's 12"-round arithmetic bounds it at 4,528 lb tension and 3,661 lb shear
against 722 lb and 40 lb factored demand (d/c 0.159 and 0.011).

**Product and moisture condition.** ESR-2604 §3.2.2 caps the wood moisture content at 19%
at the head connector. Install KDAT dry and verify that limit before closing the wrap. The
PVC must be a nonstructural, screw-fastened four-sided jacket with an accessible panel,
open at the bottom above the pier wash and vented at the top below the cap; its top sheds
water outward. Keep the `ABU66SS`'s 1" clear standoff visible and draining. These are
detailing requirements, not an assertion that a sealed PVC sleeve keeps wood dry. If the
specified wrap cannot dry or permit inspection, the cap's published rating is not earned.

## 6. The pier under a pinned post (oracles the pinned path into `column_base`)

A pinned post hands its base drag to the pier top; the pier adds its own drag over the 3.0'
it stands out of grade. Both go into the soil as a short pole, IBC 1807.3.2.1
non-constrained at S1 150 psf/ft (Table 1806.2 class 4, GM) taken at d/3:

```
steel   P = 17.47 + 16.8315 x 1.0 x 3.0 = 17.47 + 50.49 = 67.97 lb
        M at grade = 17.47 x 3.0 + 50.49 x 1.5 = 128.2 lb-ft    h = 1.886'
        A = 2.34 P / (S1 b),  d = 0.5 A (1 + sqrt(1 + 4.36 h / A))  ->  d = 2.424'
kdat    P = 74.52 lb, h = 1.984'  ->  d = 2.541'
```

| pier | shaft embedment (grade to pad top) | steel | kdat |
|---|---:|---|---|
| `PT-BW-PE` on `PD-BW-RE` | 6.120' | 0.396 | 0.415 |
| `PT-BW-PNE` on `PD-BW-RNE` | 3.500' | 0.693 | 0.726 |

The shaft alone; `column_base` basis 4 credits the doweled pad and reads lower. **The pads
leave −10'-2"**: `PD-BW-RE` sits on the house-side plane (`PIER_BOTTOM_FT`), where the house
strip beside it bears, so the 1'-4 9/16" undermining step is gone; `PD-BW-RNE` sits on the
garage plane, so the 3'-2" drop under the stone strip is gone; and `RE`'s lateral capacity no
longer rests on the basement overdig's backfill at all — 2.4' of it is needed against 6.1'.
Both piers keep the moment cage and 12" pad of every other entry pier, so the switch to
`cast` needs no new pad form. Axial is `deck_post`'s tied-column row at d/c ~0.01.

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

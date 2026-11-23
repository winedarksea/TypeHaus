# The canopy braces off the garage — hand-worked basis

**House:** catlin. **Current basis:** wind of 2026-10-31 (ridge 11.644'), screen and joints as of 2026-11-14,
**amended 2026-11-18** (§11: the garage's 7/16" ZIP moved the header lines 3/16" out; its rows supersede).
**Written by hand** (plain arithmetic, no engine import).
**Structure:** `RF-BW-CANOPY` (4:12, 26.667' x 6.000', trusses spanning 24' over two 5-1/2" x 11-7/8" treated
glulam headers `BM-BW-RW`/`-RE`, on four 6x6 KDAT posts) delivering into `RF-GARAGE`, `W-G-S`, `W-G-E`,
`W-G-W`. `EAST_POST_SYSTEM = "kdat"` is the built variant for the east pair `PT-BW-RE`/`-RNE` (piers
`PT-BW-PE`/`-PNE`, pads `PD-BW-RE`/`-RNE`); `steel` and `cast` stay as graded alternatives (§5, §7).
**Oracle for:** `engineering/roof_lateral.py` (§2), `engineering/diaphragm_delivery.py` (§3, §4),
`engineering/steel_post.py` (§5), `engineering/wood_roof_post.py` (§5a), the pinned-post pier path of
`roof_moment.py` / `column_base.py` (§6) and the cast variant's receiving-line split (§7). Reproduced by
`tests/test_diaphragm_delivery_calcs.py`, `test_steel_post_calcs.py`, `test_wood_roof_post_calcs.py`,
`test_pier_calcs.py`; the variant item sets by `tests/test_catlin_east_post_variants.py`.
**Companions:** `canopy_west_band.md` (the west line: screen panel, band, every head and base);
`north_entry_canopy_lateral.md` §8 (collectors, hold-down anchorage); `north_entry_piers.md` §10 (the landing
tie, which reads the screen's share); `entry_column_base_fixity.md` §7 (the cast shafts).
**What is asked of the reviewer:** whether the garage may take the canopy's whole lateral load (§3-§4) and §5a.
Every row is under 0.92. **Amended 2026-11-23 (§12): the decks are graded at their SDPWS table allowables, so the deck's boundary at the screen line is 0.496, not 0.908; the N-S chord force and the end-strap couple are new.**

---

## 1. Geometry and the three variants

| term | working | value |
|---|---|---|
| canopy footprint | x 4.667 -> 31.333, y 37.219 -> 43.219 | 26.667' x 6.000' |
| header centres | garage truss lines, x 6.265625' / 29.734375' (§11) | 23.46875' apart |
| headers | 5-1/2" x 11-7/8" glulam, y 37.271 -> 42.708, post face to post face | 5.4375' |
| header soffit | +7'-4" - 11.875" | +6.3438' |
| pier top (steel, kdat) | `Site.grade` -2'-10" + 3'-0" | +0.1667' |
| post height | 6.3438 - 0.1667 | **6.1771'** (74.125") |
| pier exposed | 0.1667 - (-2.8333) | 3.000' |
| house-side pad top | -107.4375" | -8.9531' |
| garage-side pad top | -7'-0" + 8" | -6.3333' |
| shaft, grade to pad top | `PT-BW-PE` / `PT-BW-PNE` | 6.120' / 3.500' |
| garage plate height | 8'-4" | 8.333' |
| ridge / over lowest ground | ridge 11.644', ground (sunken garden) -9.120' | 20.764' |

| variant | above the pier | pier | end fixity |
|---|---|---|---|
| `steel` | HSS 4x4x1/4 A500 Gr C, 74.125" | 12" round | pinned-pinned |
| `kdat` (built) | 6x6 KDAT, ACE6Z head, cast-in CBSTQ66Z-SDS2, PVC wrap | **14"** round (the CBSTQ's cover) | pinned-pinned |
| `cast` | 12" round, full height, one pour, base -10'-2" | none | fixed base |

## 2. The demand the canopy delivers (oracles `roof_lateral.py`)

ASCE 7-16 Exposure B, V 115, K_d 0.85, G 0.85, C_f 1.80, 0.6 for ASD, taken at the ridge:

```
K_z = 2.01 (20.764/1200)^(2/7) = 0.63067    q_h = 0.00256 x 0.63067 x 0.85 x 115² = 18.149 psf
p   = 0.6 x 18.149 x 0.85 x 1.80 = 16.661 psf on any projected band
```

Bands, kdat (headers 2 x 0.98958' x 5.4375' = 10.762 sf):

```
E-W  slope 4.444' x 6.000' = 26.667 sf, + headers 10.762 = 37.429 sf x 16.661 = 623.60 lb
N-S  gable triangle 2.222' x 26.667' = 59.259 sf x 16.661                      = 987.32 lb
```

**A pinned post splits its own drag half to the head and half to the base** (`wL/2` to each support; the head
half joins the deck, the base half goes down the pier):

```
kdat   16.661 x (5.5/12) x 6.1771 = 47.17 lb per post -> 23.585 head, 23.585 base
steel  16.661 x (4.0/12) x 6.1771 = 34.31 lb per post -> 17.15 head, 17.15 base
```

A post framed into a wall (`PT-BW-CW`/`-CNW`, inside `W-BW-SCREEN`) is not in the sum: its face is the wall's.
The screen's own face is not in the canopy's demand either; it is the landing tie's (`north_entry_piers.md` §10).

```
                E-W                                  N-S
kdat    623.60 + 2 x 23.585 =   670.77 lb     987.32 + 2 x 23.585 = 1,034.49 lb
steel   623.60 + 2 x 17.15  =   657.91 lb     987.32 + 2 x 17.15  = 1,021.63 lb
```

## 3. The delivery — joint, receiving roof, receiving lines (oracles `diaphragm_delivery.py`)

### 3a. Open front, SDPWS 4.2.5.2

Only the north edge is supported, so the canopy is an open-front diaphragm. `L'` is its dimension normal to the
open side, `W'` the one along it:

```
L'        6.000' vs 25'                    0.240
L'/W'     6.000 / 26.667 = 0.2250 vs 1.0   0.225   (one-story structure)
```

The deck is blocked. With pinned east posts there is no second N-S line on the canopy: the deck cantilevers 6'
off the joint. The chord force, the couple's path and the drift limit (N/A, earned: SDC A) are
`canopy_west_band.md` §6.

**Capacity of the decks.** Both roof decks are 19/32" Structural I. The canopy's blocked capacity is the
SDPWS Table 4.2A 15/32" row, 8d at 6" boundary and edges, Case 1: 755 plf nominal x 0.92 (SPF, fn. 2) / 2.0 = 347
plf (**347.3 plf since 2026-11-23, §12; it was carried at a deliberate 190 round-down**).
RF-GARAGE is unblocked: 308.2 plf since §12 (Table 4.2C, Case 1; was carried at 167.5). Receiving walls: carried at 182.5 plf (Table 4.3A; the
garage's 7/16" ZIP row at 8d 6" reads 670 x 0.92 / 2 = 308 plf, so the carry is conservative).

### 3b. The joint

Six `LSTA24` strap stations over the canopy's three trusses, `CN-BW-JOINT-1..3, -5..7`, **none at the ridge**: a
flat strap cannot seat on the peak and both sheets' edge nails would land on it. The straps mount to wood under
the deck with their 24" length running N-S. Along-joint E-W shear is carried by **continuous deck panels** nailed
into the receiving gable top chord, not by the straps' axial rating; no sheathing seam is permitted at the gable
line. Stations, x - 18': +/-3.90625 (JOINT-3/-5), +/-7.8125 (-2/-6), and the end straps 1.25" inboard of the
header centrelines, +/-(11.71875 - 0.10417) = +/-11.6146'.

**Wood and cuts.** Interior stations: a bevelled **2-ply SPF 2x6** (3.0" x 5.5") runs between truss faces
immediately under the deck on each side of the garage gable, laminated with 8d HDG nails (two near each end, 12"
o.c.). The two end stations use the canopy's **2-ply SPF 2x8** collector blocks on the south side, flush with the
header's inboard face, so the end straps sit on the block centre. Two plies give the strap's two hole lines one
ply each. The bevel follows the 4:12 roof plane across the member. Nothing cuts or drills the plated trusses and
no fastener goes through a truss plate. Cuts, inches on the project's N-S datum:

| member | south face | north face | clear length |
|---|---:|---:|---:|
| last canopy truss | 495.250 | 496.750 | 1.500 |
| canopy nailer | 496.750 | 518.625 | **21.875** |
| garage gable truss | 518.625 | 520.125 | 1.500 |
| garage nailer | 520.125 | 541.875 | **21.750** |
| next garage truss | 541.875 | 543.375 | 1.500 |

The joint bay is 1'-11 3/8" (truss 3 at y 41.333 to RF-GARAGE's gable truss at 43.281). Its deck lands on the gable
frame, half the bay over 24' at 83.7 psf: 1.948/2 x 24 x 83.7 = 1,956 lb, ~82 plf on W-G-S. The headers do not
reach the garage: the deck oversails 6 1/8" past them and the joint-bay collector blocks span truss face to gable
face, oversailing the beam end by the same 6 1/8" (LS30Z both ends, deck nailed).

Install **six OUTERMOST nails per strap leg**, 12 per strap, in existing holes, one hole line in each ply, directly
into the nailers **before the sheathing**: 0.148" x 2.5" HDG nails. Omit the middle six holes. The selected holes
start at least 4.5" from the centre, so the north group's nearest nail is >= 3" from its wood end (catalog end
distance 2-3/8"). Neither the hole positions nor the 4.5" inset are printed in the catalog: **field-verify them on
the delivered strap**. Simpson C-C-2021 p.269 rates the LSTA24 at 1,235 lb with 18 nails in both the DF/SP and
SPF/HF columns, and its notes reduce the load for fewer fasteners. The whole rating, steel limit included, is
reduced in proportion to the smaller group:

```
T_installed = 1,235 x (12 / 18) = 823.33 lb per strap
```

The same table's 12-nail LSTA15 reads 955 lb SPF/HF, so 823 lb never overstates a 12-nail group in SPF. The
published rating is **axial tension**; no transverse strap shear is credited.

**Fastening into the decks.** Each nailer is nailed to the 19/32" Structural I deck with two staggered rows of 8d
common HDG (0.131" x 2.5") at **3" o.c.**, one row per ply, 1/2" from the outer face, clear of the strap, starting
3/8" from the ends. One **LS30Z** at each nailer end, six 0.148" x 1.5" HDG nails per angle, joins side-grain
faces to the adjacent truss on clear chord wood; the fully nailed deck restrains rotation, as a single LS per
connection requires (Simpson C-C-2026 p.313). Do not load the joint before the deck is fully nailed. The deck is
continuous across the gable, 8d at 6" into its top chord; the first 8' course runs from the first canopy truss
(y 448.000") to the next garage truss (y 542.625"), 94.625". Bevelled SPF 2x4 on-edge blocks, three 8d HDG toenails
each end, back every panel edge in every canopy bay and in RF-GARAGE's first bay. The panel grid is set out from
the ridge at 3'-9" horizontal (45" projects to 47.434" on the 4:12 slope); edge stations x = 6'-9", 10'-6", 14'-3",
18', 21'-9", 25'-6", 29'-3".

**Nailer-to-deck transfer, nail by nail** (NDS 2018 §12.3.1, single shear; only ONE of the two 3" rows credited).
8d common D = 0.131", L = 2.5", F_yb 100,000 psi. Side member: the deck, G 0.50, l_s = 0.59375". Main member: SPF,
G 0.42, l_m = 2.5 - 0.59375 = 1.90625". R_d = K_D = 2.2 (D < 0.17"). F_e = 16,600 G^1.84:

```
F_es = 16,600 x 0.50^1.84 = 4,636.7 psi      F_em = 16,600 x 0.42^1.84 = 3,364.2 psi      R_e = 0.7256
I_m 381.9   I_s 163.9   II 134.1   III_m 143.1   IV 88.9
III_s  k_3 = -1 + sqrt(2(1+R_e)/R_e + 2 F_yb (2+R_e) D²/(3 F_em l_s²)) = 1.7177
       Z = k_3 D l_s F_em / ((2+R_e) R_d) = 74.958 lb  governs;   Z' = Z x C_D 1.6 = 119.933 lb
```

Nails in one row: ceil(usable / 3") + 1, usable = length - 0.75":

```
canopy nailer, SPF   21.875 - 0.75 = 21.125" -> 9 nails x 119.933 = 1,079.395 lb
canopy end block     the same nails into the same species        = 1,079.395 lb
garage nailer, SPF   21.750 - 0.75 = 21.000" -> 8 nails x 119.933 =   959.462 lb
```

**The joint rows, kdat.** The E-W resultant stands south of the joint (y_V from each band at its own centroid:
slope band 26.667 sf at 40.219, headers 10.762 sf at 39.9895, posts at 37.500 and 42.479):

```
y_band = (26.667 x 40.219 + 10.762 x 39.9895) / 37.429 = 40.153
y_V    = (623.60 x 40.153 + 23.585 x (37.500 + 42.479)) / 670.77 = 40.1415;   joint at 43.2188 -> lever 3.0773'
M      = 670.77 x 3.0773 = 2,064.2 lb-ft
Σx²    = 2 (3.90625² + 7.8125² + 11.6146²) = 2 (15.259 + 61.035 + 134.899) = 422.386 ft²;  strap line 23.229'

linear increment      2,064.2 x 11.6146 / 422.386 = 56.76 lb  vs 823.33              0.069
cantilever chord      M / 23.229 = 88.86 lb      (header centres 23.4375': M / 23.4375 = 88.07 lb)
N-S across the strap  1,034.49 / 6 = 172.42 lb  vs 823.33                            0.209
local attachment      172.42 + 88.86 = 261.28 lb
   canopy nailer / SPF block  261.28 / 1,079.395 = 0.242     garage nailer  261.28 / 959.462 = 0.272
along-joint boundary  670.77 / 23.229 = 28.88 plf vs 347.3 (190 before §12)           0.083
end strap, chord + N-S   88.07 + 172.42 = 260.49 lb vs 823.33                        0.316
```

The two chord readings are two bounds on the same couple, not two applied moments: the strap line (23.229') reads
the nailers, the header spacing (23.4375') the end strap and the header chords. The nailers are read nail by
nail, not as a boundary unit shear.

| row | steel | kdat | capacity |
|---|---:|---:|---:|
| E-W deck boundary shear | 28.32 plf | 28.88 plf | 190 plf |
| N-S strap tension | 170.27 lb | 172.42 lb | 823.33 lb |
| E-W linear strap couple | 55.62 lb | 56.76 lb | 823.33 lb |
| end strap, chord + N-S | 256.57 lb | 260.49 lb | 823.33 lb |
| nailer, local attachment (garage) | 257.34 lb (0.268) | 261.28 lb (0.272) | 959.462 lb |

The engineering check requires actual wood on both sides with specific gravity >= 0.42, a declared deck layer
with a published specific gravity, roof-plane contact, penetration, end and edge distances, the reduced schedule
and the continuous-deck declaration. Removing one nailer or lifting it off the roof plane makes the record
INCOMPLETE by connector name.

### 3c. Gable frame into `W-G-S` — `CN-BW-GCLIP-1..7`

Seven **LTP4**, Simpson C-C-2019 p. 280, SPF/HF 540 / 450 lb at C_D 1.6, the lower taken:

```
steel   657.91 / 7 = 93.99 lb   vs 450   0.209
kdat    670.77 / 7 = 95.82 lb   vs 450   0.213
```

Nailed to the chord's and the plate's inside faces, not over sheathing, so footnote 3's 0.64 does not apply; the
drawings say so.

### 3d. The receiving roof, `RF-GARAGE`

Unblocked (167.5 plf, §3a). 24' between `W-G-W` and `W-G-E` on a 24' depth: 1.0 against 3:1. Lever rule on the N-S
resultant's x (walls at x 6 and 30, the 987.32 lb band at x 18, the post drags at x 29.71875):

```
kdat   x_V = (987.32 x 18.000 + 47.17 x 29.71875) / 1,034.49 = 18.5346
       W-G-E 1,034.49 x (18.5346 - 6)/24 = 540.28 lb     W-G-W 1,034.49 - 540.28 = 494.21 lb
       increment 540.28 / 24.0 = 22.51 plf vs 308.2 (167.5 before §12)   0.073
steel  x_V 18.3935   W-G-E 527.56   W-G-W 494.06    21.98 plf   0.131
```

No south-bay blocking is required, so the drift trusses `truss-000`/`-001` are untouched.

### 3e. The receiving lines, IRC R301.1.3

Graded on the **surplus** (provided less required, off `bracing_eval`) against 182.5 plf. Required on every garage
line is 4.5' x 0.70 (eave-to-ridge under 5') x 0.95 (story height) = 2.992'.

| line | provided | surplus | kdat | steel |
|---|---:|---:|---|---|
| `W-G-S` (E-W) | 20.292' | 17.299' | 670.77 / 17.299 = **38.77 plf**, 0.212 | 38.03 plf, 0.208 |
| `W-G-E` (N-S) | 24.000' | 21.008' | 540.28 / 21.008 = **25.72 plf**, 0.141 | 25.11 plf, 0.138 |
| `W-G-W` (N-S) | 21.667' | 18.675' | 494.21 / 18.675 = **26.46 plf**, 0.145 | 26.46 plf, 0.145 |

### 3f. `W-G-S` overturning, and the two ends of it

The delivered shear over the whole provided length times the wall height, no dead load:

```
kdat   v = 670.77 / 20.2917 = 33.06 plf    T = 33.06 x 8.333 = 275.47 lb   vs 2,580   0.107
(vs 3,065, 0.090, while it was an STHD14; HTT4 on SSTB16 since 2026-11-20)
```

* **Beside `D-G-SERVICE`**, an **HTT4, `CN-G-BWHD-S-DR`**, on a cast-in **SSTB16, `CN-G-BWAB-S-DR`** (2026-11-20:
  the STHD14 here was cast at the core's inside face and jogged 2 9/16" to the kings, which no figure prints;
  `sthd_esr2920.md`, "The garage, 2026-11-20"). The tie nails with **(18) 0.148 x 1-1/2 in** to the EAST face of the
  two full-height east kings (x = 119.5 in), in the stud bay and never in the door reveal; the jack occupies
  x = 115..116.5 in, the kings x = 116.5..119.5 in. Rod at **x = 120 13/16, y = 523 1/8 in**: 2" off the core's
  outer face, 4" off its inside, 46 5/16" from the corner (middle, >= 1.5 x 12 5/8). Embedment line at the stem top
  **z = -12 in** (l_e 12 5/8 in a 64 in pour). One **#4 x 50.5-in bar** (2 le = 25 1/4 in each side, C-C-2026
  p. 43) at **z = -16 in**. The 119.5-in west panel starts at the king pack; the two south panels total 243.5 in.
  Continue the scheduled panel-edge nailing onto the full-height kings; keep the wall's sheathing and plate
  collectors. Capacity min(HTT4 2,580 SPF/HF, SSTB16 middle 3,465) = **2,580 lb**.
* **The SE corner needs no device.** R602.10.7 end condition 1: a 144" return on the same post.
* `CN-G-BWHD-SW` is on `W-G-W`. The E-W case reaches `W-G-W` and `W-G-E` as the joint couple, +/-M / 24' =
  +/-2,064.2 / 24 = +/-86.0 lb: graded, and small (4.6 and 4.1 plf; `canopy_west_band.md` §6).

## 4. The screen's share — the envelope

**The envelope is a closed decision (owner, 2026-11-14).** The garage path is graded at 100% of the delivered load,
and `W-BW-SCREEN` with everything downstream of it (hold-down, anchorage, `deck_tie/FS-BW-FLOOR`) is ALSO graded
at 100% of the N-S load. No stiffness judgement is made across the joint between two separately founded
structures, and no relief is credited to either path. Relaxing the screen's 4" edge nailing was considered and
declined: it would need a reviewer to accept the garage as the sole path and saves a few dozen nails. If a screen
row ever goes over, the fallback is a §1604.4 rigidity split with authored SDPWS schedules on the garage walls, not
a smaller envelope.

### 4a-4c. The panel, its hold-down, its anchorage

Read over the chords (`PT-BW-CW`/`-CNW`, 5.4375' out to out), not the wall's 6.542' run: at 6" edges the panel is
over; it is nailed at 4" edges (265 plf). The hold-down is the cast-in CBSTQ66Z-SDS2 under each chord, graded over
the full frame height; its anchorage is the CBSTQ's own cracked row (no ABU66SS, no ACI Ch. 17 row). Full working:
`canopy_west_band.md` §4.

```
panel      1,034.49 / 5.4375 = 190.25 plf vs 265                                     0.718
hold-down  1,034.49 x 8.6825' / 4.979' chord lever = 1,803.9 lb  + uplift 40 x (16.661 - 6.0) = 426.4
           = 2,230.4 lb vs 3,060 (cracked)                                           0.729
base shear one base takes the whole 1,034.49 lb vs 1,270 (CBSTQ F2 along the panel)  0.815
```

(steel: 187.89 plf, 0.709; 2,208.0 lb, 0.722.)

### 4d. The canopy deck along the screen line — the closest row on the page

The deck delivers the N-S case along its 6.000' west eave into the header, the collector:

```
kdat   1,034.49 / 6.000 = 172.42 plf vs 347.3   0.496      steel  1,021.63 / 6.000 = 170.27 plf   0.491
(190 before §12: 0.907 / 0.896)
```

The deck's own row of `lateral_system/RF-BW-CANOPY`; the governing row is now the pier pull-out (§6d of `north_entry_piers.md`).

### 4e. The landing tie

`deck_tie/FS-BW-FLOOR` reads the whole 1,034.49 lb as the screen's N-S share. Its verdicts, worked in
`north_entry_piers.md` §10: N-S 0.761, **E-W 0.786 (governs)**, guard 0.650. The E-W row does not read the screen's
share at all.

### 4f. The band over the panel — `canopy_west_band.md` §3

The screen stops at +4'-0" and the header soffit is +6'-4 1/8": the band is braced by 45.868° KDAT slats on KBS1Z
ends (the corner pair is screwed infill). The bays share the 1,034.49 lb equally, a slat taking 517.25 lb:

```
slat end, KBS1Z      517.25 / cos 45.868° = 742.8 lb vs 993.2 (two KBS1Z each end)   0.748
collector clips      1,034.49 / 6 LTP4 = 172.42 lb vs 450                            0.383
plates, end bearing on a chord   0.392 (top plate), 0.255 (base plate)
```

## 5. The steel post (alternative; oracles `steel_post.py`)

HSS 4x4x1/4, ASTM A500 Gr C (F_y 50 ksi), AISC Manual Table 1-12: A 3.37 in², I 7.80 in⁴, r 1.52 in, Z 4.69 in³,
design wall t = 0.93 x 0.250 = 0.2325". Post 74.125" long.

```
E7    b/t = (4.0 - 3 x 0.2325)/0.2325 = 14.20  vs  1.40 sqrt(29,000/50) = 33.72      0.421
      nonslender: Q = 1.0, E3 unreduced
E2    KL/r = 1.0 x 74.125 / 1.52 = 48.77  vs 200                                     0.244
E3    F_e = π² 29,000 / 48.77² = 120.35 ksi;   F_y/F_e = 0.4154 <= 2.25
      F_cr = 0.658^0.4154 x 50 = 42.02 ksi;   P_n = 42.02 x 3.37 = 141.61 kip
      P_n / Ω_c (1.67) = 84.79 kip
axial D + S   40 ft² x (10 + 73.7) + post 12.21 lb/ft x 6.1771' = 3,423.4 lb         0.040
H1-1b drag    w = 16.661 x 4/12 = 5.554 plf, M = wL²/8 = 26.49 lb-ft
              M_c = 50 x 4.69 / 1.67 / 12 = 11.70 kip-ft
              3.423/84.79/2 + 0.02649/11.70 = 0.0202 + 0.0023 = 0.022   (D + S with the full 0.6W: a bound)
```

**The saddle: two 5/8" HDG through-bolts, NDS 2018 §12.3.1, double shear, steel side plates**, main member
`BM-BW-RE` (5-1/2" 24F-V4 DF glulam, l_m 5.5", G 0.50), side plates 1/4" (F_es 87,000 psi), F_yb 45,000 psi. Uplift
is perpendicular to the header's grain:

```
F_e⊥ = 6,100 G^1.45 / sqrt(D) = 6,100 (0.50)^1.45 / sqrt(0.625) = 2,824.2 psi
R_e  = 2,824.2 / 87,000 = 0.03246        K_θ = 1.25 (θ 90°)
k_3  = -1 + sqrt(2(1+R_e)/R_e + 2 F_yb (2+R_e) D² / (3 F_em l_s²)) = 13.091
I_m   D l_m F_em / (4 K_θ)                       = 1,941.6 lb
I_s   2 D l_s F_es / (4 K_θ)                     = 5,437.5
III_s 2 k_3 D l_s F_em / ((2+R_e) 3.2 K_θ)       = 1,421.1   governs
IV    2 D²/(3.2 K_θ) sqrt(2 F_em F_yb/(3(1+R_e))) = 1,769.3
Z' = 1,421.1 x C_D 1.6 x C_M 0.7 = 1,591.6 lb per bolt, 3,183.3 for the pair
uplift 0.6D + 0.6W = 40 x (16.661 - 6.0) = 426.44 lb                                0.134
```

C_M 0.7 because the header end is at an eave; the head's lateral is the post's own 17.2 lb of drag and is not a
row. Stainless and galvanized are never mixed at this joint: HDG bolts, HDG saddle, a butyl isolation layer against
the KDAT.

**The base: a welded plate on two cast-in 5/8" HDG anchors, ASTM F1554 Gr 36, on levelling nuts over an open
drained gap (no grout).** At h_ef 7.891" both cones are bounded by the pier's own 113.1 in², so the group's A_Nc is
the single centre bolt's and ψ_ec is 1.0 (`north_entry_canopy_lateral.md` §8f):

```
breakout, T   φN_cbg 4,528 lb   T = 426.44/0.6 = 710.7 lb                           0.157
steel, T      the pair: φN_sa = 0.75 x 2 x 0.226 x 58,000 = 19,662 lb               0.036
shear         the base drag 17.15/0.6 = 28.6 lb, well inside every §8f shear row
```

The record grades the pair as §8f's single centred bolt, which is the lower bound; the tension row reads 0.157
either way. The anchors stand in the drained gap and see bending under shear (AISC Design Guide 1 §3.5); at 29 lb it
is not a row, and it is named so the gap is never grouted to "fix" it.

### 5a. The 6x6 KDAT east posts (oracle `wood_roof_post.py`)

The east pair are 6x6 Southern Pine No. 2 KDAT under the glulam header: an `ACE6Z` end cap on `PT-BW-RE` and
`PT-BW-RNE`, `A35Z` angles across the beam, cast-in `CBSTQ66Z-SDS2` bases in 14" piers (heads, bases and their
lateral rows: `canopy_west_band.md` §5). The PVC column wrap is a finish, never a brace. The 2018 NDS Supplement
Table 4D wet-service Southern Pine timber row gives F_c 525 psi, F_b 850 psi, E_min 440,000 psi. The post is 5.5"
square, 74.125" long (6.1771').

```
roof share        40 ft² x (10 + 73.7) psf + 6.1771' x 7.87 plf = 3,397 lb  (D + S);  f_c = 3,397 / 30.25 = 112.3 psi
slenderness       K l_u/d = 1.0 x 74.125 / 5.5 = 13.48 < NDS §3.7.1.4's 50
Fc*               525 x C_D 1.15 = 603.75 psi (snow)
FcE               0.822 x 440,000 / 13.48² = 1,991 psi
Cp                r = FcE/Fc* = 3.298, c = 0.8  ->  0.927
axial             Fc' A = 603.75 x 0.927 x 5.5² = 16,938 lb; d/c = 3,397 / 16,938 = 0.201
own drag          16.661 psf x 5.5/12 x 6.1771 = 47.17 lb, half at each end
bending           w = 7.636 plf, M = wL²/8 = 36.4 lb-ft; f_b = 36.4 x 12 / 27.73 = 15.8 psi vs wet Fb x C_D 1.6 = 1,360
interaction       (f_c/Fc' + f_b/Fb') / (1 - f_c/FcE) = (0.2006 + 0.0116) / 0.9436 = 0.225
IRC R507.4        6.177' < 14' 6x6 limit (cross-check; the roof's drift snow needs NDS)
```

**Product and moisture.** ESR-2604 §3.2.2 and ESR-3050 §4.1 rate the cap and the base at wood moisture content
<= 19%. Install KDAT dry and verify that limit before closing the wrap. The PVC is a nonstructural, screw-fastened
four-sided jacket with an accessible panel, open at the bottom above the pier wash and vented at the top under the
cap; its top sheds water outward. Keep the CBSTQ's 1" standoff visible and draining. If the wrap cannot dry or
permit inspection, the connectors' published ratings are not earned.

## 6. The pier under a pinned post (oracles the pinned path into `column_base`)

A pinned post hands its base drag to the pier top; the pier adds its own drag over the 3.0' it stands out of grade.
Both go into the soil as a short pole, IBC 1807.3.2.1 non-constrained at S1 150 psf/ft (Table 1806.2 class 4, GM)
taken at d/3: `A = 2.34 P / (S1 b)`, `d = 0.5 A (1 + sqrt(1 + 4.36 h / A))`, iterated with S1 at d/3.

```
kdat   14" pier: P = 23.585 + 16.661 x (14/12) x 3.0 = 23.585 + 58.31 = 81.90 lb
       M at grade = 23.585 x 3.0 + 58.31 x 1.5 = 158.22 lb-ft    h = 1.932'     ->  d = 2.468'
steel  12" pier: P = 17.15 + 16.661 x 1.0 x 3.0 = 17.15 + 49.98 = 67.14 lb
       M at grade = 17.15 x 3.0 + 49.98 x 1.5 = 126.43 lb-ft     h = 1.883'     ->  d = 2.412'
```

| pier | shaft embedment (grade to pad top) | steel | kdat |
|---|---:|---|---|
| `PT-BW-PE` on `PD-BW-RE` | 6.120' | 0.394 | 0.403 |
| `PT-BW-PNE` on `PD-BW-RNE` | 3.500' | 0.689 | 0.705 |

The shaft alone; `column_base` basis 4 credits the doweled pad and reads lower. `PD-BW-RE` sits on the house-side
plane where the house strip beside it bears; `PD-BW-RNE` on the garage plane. Both piers keep the moment cage and
12" pad of every entry pier (14" round in `kdat`, for the CBSTQ's cover), so a switch to `cast` needs no new pad
form. Axial is `deck_post`'s tied-column row at d/c ~0.01.

## 7. The cast variant — columns share the load by rigidity with `W-G-S` (alternative)

12" round columns, full height from the shaft base at -10'-2", fixed base, cast one 3/4" pack under the soffit:
shaft **16.4479'**, k = 3EI/h³ with E = 57,000 sqrt(5,000) = 4.0305e6 psi, I = π 6⁴/4 = 1,017.9 in⁴, h = 197.375":
**1,600.7 lb/in** (gross section). The exposed shaft runs grade to eave, 2.8333 + 86.398/12 = **10.0332'**; each
catches 16.661 x 1.0 x 10.0332 = **167.16 lb** at a = 16.4479 - 5.0166 = 11.4313' above its base. The propped
shaft returns to its head and leaves at its base:

```
head  = 167.16 x 11.4313² x (3 x 16.4479 - 11.4313) / (2 x 16.4479³)   = 93.06 lb
M0    = 167.16 x 11.4313 x (16.4479² - 11.4313²) / (2 x 16.4479²)      = 493.9 lb-ft
E-W   623.60 + 2 x 93.06 =   809.72 lb        N-S   987.32 + 186.12 = 1,173.44 lb
```

`W-G-S` lies on the canopy's north boundary, so it is a third E-W line. Its stiffness is SDPWS 4.3-1's shear term
on its surplus length (the required 2.992' is spent on the garage's own wind): 1,000 x 11 x 17.299 / 8.333 =
22,835 lb/in. Bending and anchorage slip are not stated for a prescriptive wall; leaving them out stiffens the wall
and shrinks the columns' share, **which is why the garage rows keep 100%**. `W-G-E`/`W-G-W` stand under
`RF-GARAGE`, not on the canopy's boundary, and are not stationed. The screen panel's stiffness, 9,970.5 lb/in, is
the three-term SDPWS 4.3.2 deflection of `entry_column_base_fixity.md` §7c, taken here as an input.

```
N-S lines  panel 9,970.5 at x 6.19792,  columns 2 x 1,600.7 at x 29.71875   (sum 13,171.8)
   x_r = (9,970.5 x 6.19792 + 3,201.3 x 29.71875) / 13,171.8 = 11.9145'
   x_V = (987.32 x 18.000 + 186.12 x 29.71875) / 1,173.44    = 19.8587'
   e = 19.8587 - 11.9145 = 7.9442'     M_t = 1,173.44 x 7.9442 = 9,322 lb-ft
E-W lines  RE 37.500, RNE 42.479 at 1,600.7 each, W-G-S 43.219 at 22,835  ->  y_r = 42.8219
J = panel 9,970.5 x 5.7166² + columns 3,201.3 x 17.8043² + RE/RNE 1,600.7 (5.3219² + 0.3429²) + W-G-S 22,835 x 0.3971²
  = 325,828 + 1,014,791 + 45,523 + 3,601 = 1,389,743 lb/in-ft²
column  direct 1,600.7/13,171.8 x 1,173.44 = 142.60 + torsion 9,322 x 1,600.7 x 17.8043 / 1,389,743 = 191.16
        -> 333.76 lb each;  the screen panel takes 888.24 - 382.32 = 505.92 lb
M = 333.76 x 16.4479 + 493.9 = 5,983.5 lb-ft         base V 333.76 + (167.16 - 93.06) = 407.86 lb
E-W (rigid deck; y_V 40.116, e 2.706', M_t 2,191.3 lb-ft)
        direct 1,600.7 / 26,036.1 x 809.72 = 49.78;  torsion RE 13.43, RNE 0.87
        RE top 63.21 lb,  M = 63.21 x 16.4479 + 493.9 = 1,533.6 lb-ft   (N-S governs)
```

N-S governs both columns. Embedment, shaft alone, at M/V = 5,983.5 / 407.85 = 14.670' above the shaft base, so h =
14.670 - 7.333 = 7.337' above grade (S1 150 at d/3, b 1.0): d = **6.52'** against the 8.333' from grade to the pad
bottom, **0.78** (basis 4's pad credit reads lower). The garage rows are graded at 809.72 lb E-W and 1,173.44 lb N-S (100%):

```
joint boundary 809.72 / 23.229 = 34.86 plf (0.183)     gable clips 809.72 / 7 = 115.67 lb (0.257)
W-G-S 809.72 / 17.299 = 46.80 plf (0.256)              HTT4 809.72 / 20.2917 x 8.333 = 332.53 lb (0.129; 0.108 vs the STHD14)
RF-GARAGE increment: W-G-E 1,173.44 x (19.8587 - 6)/24 = 677.59 lb -> 28.23 plf (0.169); W-G-W 495.85 lb
joint couple  y_V = 40.116, M = 809.72 x 3.103 = 2,512.7 lb-ft;  nailer 1,173.44/6 + 2,512.7/23.229 = 303.74 lb
              garage nailer 303.74 / 959.462 = 0.317, the largest row
```

**The screen, in `cast`, keeps its rigidity share of the canopy's OWN frame** (505.92 lb above) and is not taken at
100% here. The envelope refuses a stiffness judgement across the joint; the split between the screen and the cast
columns is inside one structure and is where the columns' own demand comes from. The §4 envelope applies on an
axis where the canopy has no frame of its own, which is N-S in the two pinned variants.

## 8. Differential movement

The canopy's north line (`RNE`, and `GW` under the west header) bears on the garage's own -7'-0" plane; its south
line (`RE`, `W`) on the house-side plane. The headers are simple spans between the two, so a differential rotates
each header as a rigid body and bends nothing. **Tolerance: 3/16"**, L/360 of the 5.72' header, the order the
H2.5ASS truss ties and the LSTA24 strap line take without distress. No settlement is computed (the soil is
presumed); a soils report that predicts more than 3/16" between the two planes reopens this section.

## 9. What would send us back to B or C — none fires

| trigger | where | today |
|---|---|---|
| landing tie or screen OVER at the envelope | §4, §4e | 0.496 (deck; 0.907 before §12) / 0.786, both under |
| `W-G-S` surplus or overturning needs more than a hold-down | §3e, §3f | 0.212 and one HTT4 on an SSTB16 (0.107) |
| garage-roof blocking unbuildable round the drift trusses | §3d | none required |

## 10. Not graded here / still open

* The truss fabricator's component drawings (which place the plates every LS30Z must clear) and the project's
  professional engineering review. The canopy's truss chords are delegated on the truss order
  (`canopy_west_band.md` §9); the N-S chord and the 0.03" splice slip the rigid/flexible call assumes stay with the
  truss designer.
* **LSTA24 hole positions** (the outermost-six pattern and its 4.5" inset): field-verify on the delivered strap.
* Settlement (§8) and the soil, which is presumed, not measured: a geotechnical investigation clears it.
* The garage's own wind, which stays prescriptive (R602.10) and is not added to these rows.
* The screen's own face in the canopy's demand (§2): it is the landing tie's.
* Weld design of the steel variant's saddle and base plate, the fabricator's shop drawing against AWS D1.1.
* **ColorGard snow retention** (`CN-BW-SNOW-E-1`): the supplier's drift sizing stays open.

## 11. 2026-11-18 amendment: the header lines 3/16" out

The garage sheathing went 5/8" CDX -> 7/16" ZIP with its face held on the node line, so the plates and the header
centrelines moved 3/16" outward: x 6.265625' / 29.734375', 23.46875' apart. The canopy overhang went to 1'-7 3/16"
to hold the one fascia line, so the footprint is still 26.667' x 6.000'; the ridge is 1/16" higher. Wind and the
screen's own rows: `canopy_west_band.md` §10.

```
§2   ridge over lowest ground 20.7692': K_z 0.63072, q_h 18.151, p = 16.6622 psf; post head half 23.587 lb
     E-W  37.429 x 16.6622 = 623.64 + 47.17 = 670.82 lb      N-S  59.259 x 16.6622 = 987.39 + 47.17 = 1,034.57 lb
§3b  stations x - 18' at i x 23.46875/6: +/-3.911458, +/-7.822917; end straps +/-(11.734375 - 0.104167) = +/-11.630208
     Σx² = 2 (15.2995 + 61.1980 + 135.2617) = 423.519 ft²;  strap line 23.260416'
     M = 670.82 x 3.0774 = 2,064.35 lb-ft
     linear increment   2,064.35 x 11.630208 / 423.519 = 56.69 lb      0.069
     N-S across         1,034.57 / 6 = 172.43 lb                        0.209
     local attachment   172.43 + 2,064.35 / 23.260416 = 172.43 + 88.75 = 261.18 lb
                        canopy nailer 0.242, garage nailer 261.18 / 959.462 = 0.272
     along-joint        670.82 / 23.260416 = 28.84 plf                  0.152
§3d  x_V = (987.39 x 18 + 47.17 x 29.734375) / 1,034.57 = 18.5351
     W-G-E 1,034.57 x 12.5351 / 24 = 540.35 lb (22.51 plf, 0.134);  W-G-W 494.22 lb
§3e  W-G-S 670.82 / 17.299 = 38.78 plf;  W-G-E 540.35 / 21.008 = 25.72;  W-G-W 494.22 / 18.675 = 26.46
§4a  panel 190.27 plf vs 490 (the 7/16" ZIP row, 0.388); hold-down 2,230.5 lb (0.729); base shear 0.815
§4d  1,034.57 / 6.000 = 172.43 plf vs 190                               0.908  (governs)
§7   cast: 987.39 + 2 x 93.07 = 1,173.52 lb N-S. Columns at x 29.734375, panel (k 9,970.5, held) at 6.182292:
     x_r = 11.9066, x_V = 19.8612, M_t = 1,173.52 x 7.9546 = 9,335 lb-ft, J = 1,393,335
     column 1,600.7/13,171.8 x 1,173.52 = 142.61 + 9,335 x 1,600.7 x 17.8278 / 1,393,335 = 191.19 -> 333.80 lb
```

The §7 column holds the panel at 9,970.5 lb/in (G_a 11); the engine at G_a 11 reads 334.33 lb, 0.16% over, as
before. The screen's 7/16" row doubles G_a to 22 (`canopy_west_band.md` §4a), which halves the panel's shear term
and stiffens it, so the engine sheds 0.84 lb off each column: **333.49 lb**. Not re-iterated by hand; the column's
connector ratio (0.247) does not move in its third figure.

Every other §3-§10 figure moves by the p ratio, x 1.00007, inside its printed precision. The receiving walls keep
their carried 182.5 plf.

## 12. 2026-11-23 amendment: tables read at the primary, the N-S chord force, the end-strap couple

Review C-2, C-3, C-8; decisions 18 and 19. Plain arithmetic, no engine import. Reproduced by
`tests/test_diaphragm_delivery_calcs.py`.

**12a. The deck allowables, from AWC SDPWS-2015 with Commentary, Chapter 4 (read 2026-11-23, AWC's own PDF).**
Column B (wind) of Table 4.2A, Blocked WSP, Structural I, 8d common, 2" nominal framing, 3/8" minimum nominal
panel thickness (a 19/32" deck exceeds it), 6" at boundaries and continuous edges, 6" at other edges, Case 1:
**v_w = 755 plf** (Column A seismic 540 x 1.4). Table 4.2C Unblocked, the same grade/nail/thickness, 6" nails,
Case 1: **v_w = 670 plf**. Footnote 2 (G 0.42 SPF): [1 - (0.5 - 0.42)] = 0.92. §4.2.3: divide by 2.0.

```
canopy   755 x 0.92 / 2.0 = 347.3 plf  (the secondary IBC transcription's 372 x 0.92 = 342 differs: 744 there)
garage   670 x 0.92 / 2.0 = 308.2 plf
screen line   172.43 / 347.3 = 0.496        joint nailing 28.84 / 347.3 = 0.083     garage increment 22.51 / 308.2 = 0.073
```

G_a stays at the authored 12 (canopy; the row reads 14 OSB / 11 ply) and 7 (garage; row 8.5 OSB / 7.0 ply): they decide
only the rigid/flexible call, which no ratio reads under the double envelope (C-8). Table 4.3A, same PDF, closes
the reviewer's open question: 7/16" Sheathing, 8d, 6": 670; 4": **980** (the screen's 490 = 980 / 2 is exact); the
garage walls' 182.5 plf carry is a deliberate conservative round-down of the table's 670 x 0.92 / 2 = 308.2 and
is kept (every row on it is under 0.16).

**12b. The N-S chord force.** The screen at 100% closes only as a simple span: the end straps return a couple, and
the deck is a deep beam from the screen to the east end strap with the first and last truss as its chords. The
strap line is x 6.3698..29.6302 = 23.2604'; the chords are the canopy's first and last trusses, y 37.3333' and
41.3333' = **4.000'** apart (the drawing builds these; the garage gable truss at y 43.281 is NOT named as the north
chord because it would carry a canopy force through a nailed deck edge, and the deck stays continuous over it):

```
T = V L / (8 d) = 1,034.565 x 23.2604 / (8 x 4.000) = 752.0 lb      (was 1,034.49 x 24 / (8 x 6) = 517.2: the deck's depth, not the chords')
```

Tension in one chord, compression in the other, on top of gravity; the peak splice carries it in tension; it goes on
EVERY canopy truss (decision 19). The 0.03" splice slip is dropped from the order (C-8): both N-S paths are graded at
100%, the split never enters a ratio; the field survives only for the `cast` variant's deflection.

**12c. The end-strap couple.** V acts at the deck resultant x_V = 18.5346'; the screen panel's line is x 6.1823'; the
lever is 12.3523', M = 1,034.565 x 12.3523 = 12,779 lb-ft, closed by opposite N-S forces at the two end straps:

```
F = M / L_strap = 12,779 / 23.2604 = 549.4 lb     (the review's 517 used V/2)
end strap, F + the E-W chord force 88.0 (added linearly)   637.4 / 823.33 = 0.774     (was 0.316)
(a conservative bound: an elastic distribution over the six straps, M x 11.63 / 423.4 = 351 lb, reads 0.43, or 0.53 with the chord force)
RF-GARAGE torque, M / 24.000' = 532.5 lb on each of W-G-W, W-G-E
  W-G-W  532.5 / 18.675' = 28.51 plf vs 182.5   0.156       W-G-E  532.5 / 21.008' = 25.35 plf   0.139
```

## Sources

- ASCE 7-16 §26.2, §29.3, §2.4.1.
- AWC SDPWS-2015 §4.2.2, §4.2.5.2, Tables 4.2A, 4.2C and 4.3A, §4.3.2.
- IBC 2018 §1604.4, §1806.2, §1807.3.2.1; IRC 2018 R301.1.3, R602.10.3, R602.10.7.
- AISC 360-16 §B4.1 (Table B4.1a case 6), §E2, §E3, §E7, §H1.1; AISC Manual Table 1-12.
- AWC NDS 2018 §12.3.1 (yield limit equations), Table 12.3.3 notes, §11.3.3 (C_M).
- ACI 318-19 Ch. 17 as in `north_entry_canopy_lateral.md` §8f.
- Simpson Strong-Tie C-C-2019 p. 280, LTP4 row, directions G/H; C-C-2021 p. 269 (LSTA).
- ICC-ES ESR-2105 Table 3 (LSTA24); Simpson C-C-2026 p. 63 (HTT4) and p. 43 (SSTB16, 6" stem).
- ASTM A500 Gr C; ASTM A123 (galvanizing after fabrication); ASTM F1554 Gr 36.

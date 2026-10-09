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

> ⚠ **Re-worked 2026-10-08 for the standard-heel trusses.** Both roofs dropped 5.75", so the
> canopy ridge stands 11.917' up, 21.04' over the ground beneath, and `q_h` falls from 18.335
> to 18.217 psf. Every wind number below is the new one. The receiving lines' surplus grew
> too: the garage's eave-to-ridge fell under 5', so R602.10.3(2) item 2 takes x0.70.

> ⚠ **The envelope is deliberate and it double-counts on purpose.** The garage path is graded
> at 100% of the delivered load, and `W-BW-SCREEN` and everything downstream of it
> (hold-down, anchorage, `deck_tie/FS-BW-FLOOR`) are ALSO graded at 100% of N-S. No
> stiffness judgement is made across the joint between two separately founded structures,
> and no relief is credited to either path (§8h of the lateral note's convention). If a
> screen row ever goes over, the fallback is a §1604.4 rigidity split with authored SDPWS
> schedules on the garage walls — not a smaller envelope.

> ⚠ **The plan's "about 811 lb E-W / 1,179 lb N-S" carried the 12" round's drag.** A 4" HSS
> catches a third of it. On the 5-1/2" x 11-7/8" glulam headers (2026-09-30) the delivered
> shears are 677.3 / 1,025.4 lb (steel) and 690.2 / 1,038.4 lb (KDAT). §2 works them.

> ⚠ **The west line is re-read in `canopy_west_band.md` (2026-09-30).** The screen stops 2'-4 1/8"
> under its header, the band is braced by CS16 X-straps, and the panel, its hold-down and every
> head and base are graded there. §4 below keeps only the deck-side rows.

---

## 1. Geometry and the three variants

| term | working | value |
|---|---|---|
| canopy footprint | x 4.667 → 31.333, y 37.219 → 43.219 | 26.667' x 6.000' |
| the joint | `CN-BW-JOINT-1..3, -5..7`, x 6.083 → 29.917 at y 43.219 | 23.833', 6 `LSTA24`, none at the ridge |
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

The pressure is §7a's: `q_h` 18.217 psf at 21.04' (11.917' ridge, −9.120' ground; Exposure B
`K_z` = 2.01 (21.04/1200)^(2/7) = 0.6330, `K_d` 0.85, V 115), `G` 0.85, `C_f` 1.80, 0.6 for
ASD — **16.7232 psf** on any projected band. The headers' band grew with the glulam:

```
E-W   slope rise 4.444' x 6.000' + 2 headers 0.98958' x 5.9479'   = 38.439 sf ->  642.82 lb
N-S   gable-end triangle 2.222' x 26.667'                         = 59.259 sf ->  991.0 lb
```

**A pinned post splits its own drag half to the head and half to the base.** A member pinned
at both ends under a uniform load returns `wL/2` to each support; the head half joins the
deck, the base half goes down the pier and never reaches the diaphragm.

```
steel   16.7232 x (4.0/12) x 6.1771  = 34.43 lb per post  ->  17.22 lb head, 17.22 base
kdat    16.7232 x (5.5/12) x 6.1771  = 47.35 lb per post  ->  23.67 lb head, 23.67 base
```

A post framed into a wall (`within_wall`) is not in the sum: its face is the wall's, and
`PT-BW-CW`/`-CNW` stand inside `W-BW-SCREEN`. **The screen's own face is not in the
canopy's demand either**, exactly as §7a never counted it; it is in the landing tie's.

```
                 E-W                               N-S
steel    642.82 + 2(17.22) =  677.3 lb     991.0 + 2(17.22) = 1,025.4 lb
kdat     642.82 + 2(23.67) =  690.2 lb     991.0 + 2(23.67) = 1,038.4 lb
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

**Attachment completed 2026-10-06, revised the same day; end blocks re-stocked 2026-10-08.**
Six strap stations and the three
canopy trusses. The straps mount directly to wood under the deck, with their 24in length
running north-south. Along-joint E-W shear is carried by **continuous deck panels** nailed
into the receiving gable top chord, not by the straps' axial tension rating. No sheathing
seam is permitted at the garage gable line.

**No strap at the ridge.** `CN-BW-JOINT-4` (x=18ft) is retired: its nailer needed two bevels,
a flat 1-1/4in strap cannot seat on that peak, and both sheets' edge nails would land on it.
The ridge panel edge takes an ordinary panel-edge block in every bay instead. The other tags
keep their numbers.

**Wood and cuts.** Interior stations (x=10, 14, 22, 26ft): a bevelled **2-ply SPF 2x6**
(3.0in x 5.5in) runs between truss faces immediately beneath the deck on each side of the
garage gable, laminated with 8d HDG nails, two near each end and 12in o.c. between. The two
end stations use the canopy's **2-ply SPF 2x10** collector blocks on the south side (§3e of
`canopy_west_band.md`); each 3in block is flush with its header's inboard face, so the end
straps sit on the block centre, 1-1/4in inboard of the header centreline: x=6ft 1-1/4in and
29ft 10-3/4in. Two plies give the strap's two hole lines one ply each, as on the nailers.
The bevel follows the 4:12 roof plane across the member's width. Nothing cuts or drills the
plated trusses, and no fastener goes through a truss plate.

The actual cuts, in inches on the project's north-south datum, are:

| member | south face | north face | clear length |
|---|---:|---:|---:|
| last canopy truss | 494.500 | 496.000 | 1.500 |
| canopy nailer | 496.000 | 518.625 | **22.625** |
| garage gable truss | 518.625 | 520.125 | 1.500 |
| garage nailer | 520.125 | 541.875 | **21.750** |
| next garage truss | 541.875 | 543.375 | 1.500 |

The joint and strap centre stay at y=518.625in. The gable occupies the first 1.5in of the
north leg, so a full nine-nail group at the original butt is unsuitable. Install **six
OUTERMOST nails per strap leg**, 12 total, in existing holes, one hole line in each ply,
directly into the nailers **before installing sheathing**: 0.148in x 2.5in HDG nails. Omit
the middle six holes. The selected holes start at least 4.5in from the centre; the north
group's nearest nail is consequently >=3in from its wood end, exceeding the catalog's
**2-3/8in** end distance. Neither the hole positions nor the 4.5in inset are printed in the
catalog: **field-verify them on the delivered strap**. The hole lines sit 1/2in each side of
the centre, 1in from each ply's outer face, over the >=3/4in edge distance.

[Simpson C-C-2021](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
p.269 rates the LSTA24 at 1,235lb with 18 nails in **both** the DF/SP and SPF/HF columns, and
its general notes reduce the load for fewer fasteners. Conservatively reduce the **whole**
rating, including its steel limit, in proportion to the smaller installed group:

```
T_installed = 1,235 x (12 / 18) = 823.333 lb per strap
```

The same table's 12-nail LSTA15 reads 955lb SPF/HF, so 823lb never overstates a 12-nail group
in SPF. The product's published rating is **axial tension**; no transverse strap shear
capacity is credited.
See also [Simpson's installation guide](https://www.strongtie.com/resources/product-installers-guide/lsta-installation).

**Fastening into the decks.** Nail each nailer to the 3/4in Structural I deck with two
staggered rows of 8d common HDG 0.131in x 2.5in nails at **3in o.c.**, one row per ply, 1/2in
from its outer face and clear of the strap, starting 3/8in from the nailer ends. One
**LS30Z** at each nailer end, six 0.148in x 1.5in HDG nails per angle (three per leg), joins
side-grain faces to the adjacent truss, on clear chord wood. The fully nailed deck restrains
rotation, as required for a single LS per connection (Simpson C-C-2026 p.313). Do not load
the joint before the deck is fully nailed.
Keep the deck continuous across the gable, with 8d at 6in into its top chord. The first
8ft course can run from the first canopy truss (y=447.250in) to the next garage field
truss (y=542.625in): 95.375in, within an 8ft sheet, with its end on that truss. Bevelled
SPF 2x4 **on-edge** blocks, three 8d HDG toenails each end, back every panel edge in every
canopy bay **and in RF-GARAGE's first bay**, where that course ends.
Set the panel grid out from the ridge at **3ft 9in horizontal**: 45in projects to 47.434in
on the 4:12 slope, within a standard 48in sheet. Cut each sheet to fit with 1/8in gaps;
no sheet bends across the ridge. Edge stations are x=6ft 9in, 10ft 6in, 14ft 3in, 18ft,
21ft 9in, 25ft 6in and 29ft 3in.

The nailer-to-deck transfer is read **nail by nail**, NDS 2018 §12.3.1, single shear, and
only ONE of the two 3in rows is credited. 8d common: D = 0.131in, L = 2.5in,
F_yb = 100,000psi (NDS Table I1). Side member: the 3/4in Structural I deck, G = 0.50 (NDS
Table 12.3.3B), l_s = 0.75in. Main member: SPF G = 0.42 for every nailer and both end blocks,
l_m = 2.5 - 0.75 = 1.75in. R_d = K_D = 2.2. F_e = 16,600 G^1.84:

```
F_es = 16,600 x 0.50^1.84 = 4,636.7 psi
SPF  F_em = 16,600 x 0.42^1.84 = 3,364.2 psi; R_e = 0.7256, R_t = 2.3333
     k1 0.6099  k2 0.9296  k3 1.5307
     Im 350.57  Is 207.07  II 126.29  IIIm 132.95  IIIs 84.38  IV 88.93  -> Z = 84.38 lb (IIIs)
Z' = Z x C_D 1.6 (wind): SPF 135.00 lb
```

Nails in one row start 3/8in from each nailer end, at 3in: ceil(usable / 3) + 1.

```
canopy nailer, SPF    22.625 - 0.75 = 21.875in -> 9 nails x 135.00 = 1,215.0 lb
canopy end, SPF block                             9 nails x 135.00 = 1,215.0 lb
garage nailer, SPF    21.750 - 0.75 = 21.000in -> 8 nails x 135.00 = 1,080.0 lb
```

The E-W resultant stands south of the joint. The same bands as §2 give:

```
kdat    y_V = (642.82 x 40.219 + 23.67 x 37.500 + 23.67 x 42.479) / 690.2 = 40.203
        e = 43.219 - 40.203 = 3.016ft; M = 690.2 x 3.016 = 2,081.3 lb-ft
steel   y_V = 40.207; e = 3.012ft; M = 2,039.7 lb-ft
```

The strap stations sit at x - 18ft = +/-4, +/-8 and +/-11.896ft: sum x^2 = 443.02ft^2, and the
strap line spans 23.792ft. A linear distribution's largest axial increment is
M x 11.896 / 443.02 = **55.89lb** (steel 54.77). The cantilever chord reading over the strap
line is M / 23.792 = **87.48lb** (steel 85.73), a hair over the chords' own M / 24 = 86.72lb.
These are two bounds on the same couple, not two applied moments. For local wood/deck
transfer, take the larger, then conservatively add the separate N-S case:

```
local attachment demand = 1,038.35/6 + max(55.89, 87.48) = 173.06 + 87.48 = 260.54 lb
canopy nailer      260.54 / 1,215.0 = 0.214
canopy SPF block   260.54 / 1,215.0 = 0.214   (the same nails into the same species)
garage nailer      260.54 / 1,080.0 = 0.241   (steel 256.64, 0.238; cast 303.37, 0.281)
```

An earlier draft credited one diaphragm boundary row instead (the deck's unit shear times
the SDPWS SPF factor 0.92). That bound read the cast variant at 1.13 for a nailer whose
nails carry four times the demand, so the nails are read directly.

The installed strap rows are:

| row | steel | kdat | capacity |
|---|---:|---:|---:|
| E-W deck boundary shear | 28.47plf | 29.01plf | 190plf |
| N-S strap tension | 170.91lb | 173.06lb | 823.33lb |
| E-W linear strap couple | 54.77lb | 55.89lb | 823.33lb |
| end strap, chord + N-S envelope | 255.89lb | 259.78lb | 823.33lb |

The engineering check requires actual wood on both sides with specific gravity >=0.42, a declared deck layer with a published specific gravity,
roof-plane contact, penetration, end and edge distances, the reduced schedule and the
continuous deck declaration. Removing one nailer or raising it off the roof plane makes the
record INCOMPLETE by connector name. This completes the draft attachment basis; the truss
fabricator's component drawings (which place the plates every LS30Z must clear) and the
project's professional engineering review remain separate requirements.

### 3c. Gable frame into `W-G-S` — `CN-BW-GCLIP-1..7`

Seven **LTP4**, Simpson C-C-2019 p. 280, SPF/HF 540 / 450 lb at C_D 1.6, the lower taken:

```
steel   677.3 / 7 = 96.75 lb   vs 450   0.215
kdat    690.2 / 7 = 98.59 lb   vs 450   0.219
```

Nailed to the chord's and the plate's inside faces, not over sheathing, so footnote 3's 0.64
does not apply — and the drawings say so.

### 3d. The receiving roof, `RF-GARAGE`

3/4" Structural I, 8d at 6", **unblocked**, SDPWS Table 4.2A Case 1 at the 15/32" row, ASD
167.5 plf. 24' between `W-G-W` and `W-G-E` on a 24' depth: 1.0 against 3:1. Lever rule on the
N-S resultant's x:

```
kdat    x_V = (991.0 x 18.000 + 2 x 23.67 x 30.000) / 1038.4 = 18.547
        W-G-E 1038.4 x 12.547/24 = 542.8 lb     W-G-W 495.5 lb
        increment 542.8 / 24.0 = 22.62 plf vs 167.5   0.135
steel   x_V 18.403   W-G-E 529.9   W-G-W 495.5    22.08 plf   0.132
```

**No south-bay blocking is required**, so the drift trusses `truss-000`/`-001` are untouched.

### 3e. The receiving lines, IRC R301.1.3

On the **surplus** (provided less required, off `bracing_eval`), SDPWS 4.3A 15/32" 8d at 6",
**182.5 plf** ASD. Required on every garage line is 2.993' (4.5' x 0.70 eave-to-ridge under 5'
x 0.95 story height; it was 4.275' under the 9.25" heel, when the garage roof stood over 5').

| line | provided | surplus | steel | kdat |
|---|---:|---:|---|---|
| `W-G-S` (E-W) | 20.417' | 17.425' | 677.3/17.425 = 38.87 plf, 0.213 | 39.61 plf, **0.217** |
| `W-G-E` (N-S) | 24.000' | 21.008' | 529.9/21.008 = 25.23 plf, 0.138 | 25.84 plf, 0.142 |
| `W-G-W` (N-S) | 21.667' | 18.675' | 495.5/18.675 = 26.53 plf, 0.145 | 26.53 plf, 0.145 |

### 3f. `W-G-S` overturning, and the two ends of it

The delivered shear over the whole provided length, times the wall height, NO dead load:

```
steel   v = 677.3 / 20.417 = 33.17 plf    T = 33.17 x 8.333 = 276.4 lb
kdat    v = 33.80 plf                     T = 281.7 lb
```

* **Beside `D-G-SERVICE`** a new **STHD14, `CN-G-BWHD-S-DR`**, cast into `W-GF-S-DR`'s 6" core
  (ESR-2920 6" stem row, 3,065 lb): 276.4 / 3,065 = **0.090** (kdat 0.092).
* **The SE corner needs no device.** R602.10.7 end condition 1: a 144" return on the same post.
* `CN-G-BWHD-SW` is on `W-G-W`. The E-W case reaches `W-G-W` and `W-G-E` as the joint couple,
  ±M / 24' = ±86.7 lb (kdat) on the E-W case — graded, and small (`canopy_west_band.md` §6).
  This line used to say the joint "closes" the couple before the garage sees it; the joint
  hands it on.

## 4. The screen's share — the envelope (steel and kdat)

### 4a-4c. The panel, its hold-down, its anchorage — moved

Read over the chords (`PT-BW-CW`/`-CNW`, 5.4375' out to out) rather than the wall's 6.573' run,
the 6" edge nailing is OVER (1.05); the panel is nailed at 4" edges (265 plf) and reads
**0.721** kdat (steel 1,025.4 / 5.4375 = 188.6, 0.712). The hold-down is a cast-in CBSQ66-SDS2
graded over the FULL frame height, 2,227.6 / 3,060 = **0.728** kdat (steel 2,205.2, 0.721), and
its anchorage is the CBSQ's own cracked row, so the ABU66SS / AB-058-10-SS / ACI Ch. 17 rows
are gone. All of it: `canopy_west_band.md` §4.

### 4d. The canopy deck along the screen line — the closest row on the page

The deck delivers the N-S case along its 6.000' west eave into the header, the collector:

```
steel   1025.4 / 6.000 = 170.91 plf vs 190    0.900
kdat    1038.4 / 6.000 = 173.06 plf           0.911
```

The governing row of the lateral record in both pinned variants.

### 4e. The landing tie

`deck_tie/FS-BW-FLOOR` reads the screen's share (1,038.4 lb of panel load N-S); its **E-W row
governs at 0.966 and does not read the screen's share at all**. The N-S row, by
`north_entry_piers.md` §10c's bolt-group arithmetic with this share in place of §10b's 980.74
(and the addendum's 98.94 lb of deck wind at x 7.7917):

```
Fy = 1,038.35 + 98.94 = 1,137.29 lb    M = 1,038.35 (6.0 − 7.5937) + 98.94 (7.7917 − 7.5937) = −1,635.3 lb-ft
W   X −117.14  Y 765.06   765.06/1,480 + 117.14/740 = 0.517 + 0.158 = 0.675
FC  X   58.57  Y 508.71   58.57/518 + 508.71/917    = 0.113 + 0.555 = 0.668
```

### 4f. The band over the panel — `canopy_west_band.md` §3

The screen stops at +4'-0" and the header's soffit is +6'-4 1/8": the band is braced by 45°
KDAT slats on KBS1Z ends, 146.85 / 540 lb, **0.272**, with its plates bearing end-on on the
chords (0.394) and the deck's shear collected into the header by six LTP4 (0.385).

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
H1-1b drag    w = 16.72 x 4/12 = 5.57 plf, M = wL²/8 = 27.04 lb-ft
              M_c = 50 x 4.69 / 1.67 / 12 = 11.70 kip-ft
              0.0405/2 + 0.0270/11.70 = 0.023    (D + S taken with the full 0.6W: a bound)
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
uplift 0.6D + 0.6W = 40 x (16.7232 - 6.0) = 428.93 lb                               0.127
```

C_M 0.7 because the header's end is at an eave; the head's lateral is the post's own 17.4
lb of drag and is not a row. **Stainless and galvanized are never mixed at this joint**:
HDG bolts, HDG saddle, and a butyl isolation layer against the KDAT.

**The base — a welded plate on two cast-in 5/8" HDG anchors, ASTM F1554 Gr 36, on levelling
nuts over an open drained gap (no grout).** §8f's 12"-round case applies to the PAIR: at
h_ef 7.891" both cones are bounded by the pier's own 113.1 in², so the group's A_Nc is the
single centre bolt's and ψ_ec is 1.0.

```
breakout, T   φN_cbg 4,528 lb (unreduced reading, §8f)   T = 428.93/0.6 = 714.9 lb   0.158
steel, T      the pair: φN_sa = 0.75 x 2 x 0.226 x 58,000 = 19,662 lb               0.036
shear         the base drag 17.36/0.6 = 28.9 lb — well inside every §8f shear row
```

**The record grades the pair as §8f's single centred bolt**, rows and all: the group's
breakout is the same bounded cone, and one bolt's pullout and steel (57 ksi, the stainless
read) are half the pair's. That is the lower bound, so the rows print one bolt's φN_sa and
the tension row reads 714.9 / 4,528 = 0.158 either way.

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
own drag          16.7232 psf x 5.5/12 x 6.1771 = 47.35 lb, half at each end
bending           w L²/8 = 36.6 lb-ft; f_b = 15.8 psi vs wet Fb x C_D 1.6 = 1,360 psi
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
steel   P = 17.22 + 16.7232 x 1.0 x 3.0 = 17.22 + 50.17 = 67.39 lb
        M at grade = 17.22 x 3.0 + 50.17 x 1.5 = 126.9 lb-ft    h = 1.883'
        A = 2.34 P / (S1 b),  d = 0.5 A (1 + sqrt(1 + 4.36 h / A)), S1 at d/3  ->  d = 2.415'
kdat    14" pier: P = 23.67 + 16.7232 x (14/12) x 3.0 = 82.20 lb, h = 1.932'  ->  d = 2.471'
```

| pier | shaft embedment (grade to pad top) | steel | kdat |
|---|---:|---|---|
| `PT-BW-PE` on `PD-BW-RE` | 6.120' | 0.395 | 0.404 |
| `PT-BW-PNE` on `PD-BW-RNE` | 3.500' | 0.690 | 0.706 |

The shaft alone; `column_base` basis 4 credits the doweled pad and reads lower. **The pads
leave −10'-2"**: `PD-BW-RE` sits on the house-side plane (`PIER_BOTTOM_FT`), where the house
strip beside it bears, so the 1'-4 9/16" undermining step is gone; `PD-BW-RNE` sits on the
garage plane, so the 3'-2" drop under the stone strip is gone; and `RE`'s lateral capacity no
longer rests on the basement overdig's backfill at all — 2.4' of it is needed against 6.1'.
Both piers keep the moment cage and 12" pad of every other entry pier (14" round in `kdat`,
for the CBSQ's cover), so the switch to `cast` needs no new pad form. Axial is `deck_post`'s tied-column row at d/c ~0.01.

## 7. The cast variant — columns share E-W by rigidity with `W-G-S`

The columns are the 2026-09-20 design unchanged: h 16.5625' from −10'-2", k = 3EI/h³ =
1,567.7 lb/in (gross, §7c). What moved is the wind on them. Their exposed shaft runs from
`Site.grade` to the eave, which fell 5.75" with the standard heel: 7.472 + 2.833 = 10.306'.
So each catches 16.7232 x 1.0 x 10.306 = 172.34 lb at a = 16.5625 − 5.153 = 11.410' above
its base, and the propped shaft returns 94.51 lb to its head and leaves 516.6 lb-ft at its
base. The E-W diaphragm shear is §2's glulam bands plus both heads, 642.82 + 2 x 94.51 =
831.8 lb; N-S is 991.0 + 189.0 = 1,180.0 lb. `W-G-S`
lies on the canopy's north boundary, so it is stationed as a third E-W line. Its stiffness
is SDPWS 4.3-1's shear term on its SURPLUS length (the required 2.993' is spent on the
garage's own wind): `1000 G_a L / h = 1000 x 11 x 17.425 / 8.333 = 23,001 lb/in`. Bending
and anchorage slip are not stated for a prescriptive wall; leaving them out makes the wall
stiffer and the columns' share smaller, **which is why the garage rows keep 100%**.
`W-G-E`/`W-G-W` stand under `RF-GARAGE`, not on the canopy's boundary, and are not stationed.

```
stations  RE 37.500   RNE 42.479   W-G-S 43.219      span 5.719'
tributary 0.4353      0.5000       0.0647            avg drift 0.166"
deck      SDPWS 4.2.2 at 15.6 plf on 5.719 x 26.667  = 0.032"    ratio 0.19x -> RIGID
rigid     0.0600      0.0600       0.8800
torsion   y_r 42.831, y_V 40.167, e -2.665', M_t 2,216.6 lb-ft, J 1,422,139 lb/in-ft²
          (N-S lines as §8g: panel 9,970.5 at x 6, columns at x 30, x_r 11.742)
          increments RE +13.03, RNE +0.86 lb
E-W top   RE 49.89 + 13.03 = 62.92 lb   M = 62.92 x 16.5625 + 516.6 = 1,558.7 lb-ft
N-S       V 1,180.0, e 8.181', direct 141.15 + torsion 194.29 = 335.45 lb
          M = 335.45 x 16.5625 + 516.6 = 6,072.4 lb-ft   base V 413.3 lb at 14.69'
```

**N-S now governs both cast columns**, because E-W collapsed onto the wall. Embedment, shaft
alone at h = 14.69 − 7.333 = 7.36' above grade: d = **6.56'** against the 8.333' the pad
bottom gives — **0.79** (basis 4's pad credit reads lower). −10'-2" is kept: it is the plane
this variant was designed and drawn on, and a shallower one is a separate decision this note
does not make. The garage rows are graded at 831.8 lb E-W (100%) and 1,180.0 lb N-S (100%);
the largest is the garage nailer at 303.37 / 1,080 = 0.281.

The engine's shaft is 16.5104' (198.125", pad top to soffit) where this note keeps 16.5625',
so its heads read 94.28 lb and its N-S column force 335.74 lb, within 0.1% of the above;
`tests/test_pier_calcs.py` pins the hand values at the engine's height: 335.45 x 16.5104 +
515.6 lb-ft of propped drag (a = 11.358') = 6,054.0 lb-ft.

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
| landing tie or screen OVER at the envelope | §4, §4e | 0.911 / 0.966, both under |
| `W-G-S` surplus or overturning needs more than a hold-down | §3e, §3f | 0.217 and one STHD14 |
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

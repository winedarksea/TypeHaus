# The canopy's west band, heads and bases, and the open front — hand-worked basis

**House:** catlin
**Basis:** the design as built on 2026-11-14, under the 2026-10-31 wind: q_h 18.149 psf, p = 16.661 psf
ASD (0.6W), derived once in `canopy_garage_diaphragm.md` §2 and not re-derived here. **Amended 2026-11-18**
(the garage's 7/16" ZIP moved both column lines 3/16" out): §1, §4a and §10 supersede; every other figure below
is the 11-14 value, which §10 moves by x 1.000072.
**Structure:** `RF-BW-CANOPY`'s west line: `W-BW-SCREEN`, the band over it (`SB-BW-BAND`), the chords
`PT-BW-CW`/`-CNW`, the glulam headers `BM-BW-RW`/`-RE`, the heads and bases of all four 6x6 KDAT posts
(`PT-BW-CW`/`-CNW`/`-RE`/`-RNE`, `EAST_POST_SYSTEM = "kdat"`), and the open front's chord and couple.
**Oracle for:** `engineering/lateral_band.py` / `lateral_band_slats.py` (§3-§4), `wood_roof_post.py` /
`wood_roof_post_joints.py` (§5), `open_front.py` (§6), `roof_beam_glulam.py` / `truss_on_beam.py` (§7);
reproduced by `tests/test_canopy_west_band_calcs.py`.
**Companions:** `canopy_garage_diaphragm.md` (the wind, the delivery to the garage, the envelope this note
works inside); `north_entry_canopy_lateral.md` §8 (collectors, torsion, hold-down anchorage);
`north_entry_structure.md` (the bearing map).
**Citations:** older pointers to this note's "2026-10-28 / 10-31 / 11-06 amendments" now mean §5c, §6, §7 and §5f.
**What is asked of the reviewer:** §3b's equal share between the mirrored bays and the mid-band count it
rests on, and §4b's full-height overturning at the chord bases: the judgement and the row nearest its limit
after the deck.

Every demand below is linear in the delivered shear V = 1,034.49 lb (and in p); since 2026-11-18 V = 1,034.57 lb
(§10). The band forces are
P = V / (2 cos θ) = 0.71808 V and v = V tan θ / 2 = 0.51538 V, so a unit test that runs §3 at another V
(`test_slat_braces.py` uses 1,038.35 lb) reproduces the same arithmetic.

> ⚠ **The chord base shear is on ONE base, and that is not conservatism for its own sake.** The base plate
> and the sill bear END-ON against the chords, in compression only, so the panel's in-plane shear reaches
> the chord it pushes against and none of it the other. Share it 50/50 and the row reads 0.41 for a joint
> that does not work that way.

> ⚠ **The overturning lever is the deck to the chord BASES, 8.6825', not the panel's 4.0783'.** The deck
> delivers at the header top and the pinned bases are 1'-3 1/4" below the panel's sill; the couple between
> is all the chords', whatever the panel does inside it.

---

## 1. Geometry

| term | working | value |
|---|---|---|
| column line | garage plate x 6.0 + (7/16" ZIP + half the 5 1/2" plate) | x **6.265625'** (6'-3 3/16"); east line 29.734375' |
| header | 5-1/2" x 11-7/8" glulam, top +7'-4"; glulam faces x 72.4375-77.9375" | soffit **+6.34375'** |
| header length | post face to post face, y 37.2708 to 42.7083 | **5.4375'** (65-1/4"), no tails |
| roof-bearing run | starts 3/4" in at the south, y 37.3333 to 42.7083 | 5.375' |
| chords, centre to centre | `PT-BW-CW` y 37.5000 to `PT-BW-CNW` y 42.4792 | **4.9792'** |
| chords, out to out | 4.9792 + 5.5/12 | 5.4375' |
| clear between chord faces | 4.9792 - 5.5/12 | 4.5208' |
| panel | bottom -0.94" (the deck composite's actual stock), top +4.0000' | h **4.0783'** |
| band | 6.34375 - 4.0000 | **2.34375'** (2'-4 1/8") |
| screen studs | 2x4 KDAT flush with the chords' west faces | axis 1" west of the column line |
| chord bases (CBSTQ66Z-SDS2 seat) | pier top -15.44" less the 3/4" SS316 pack | **-16.19"** (-1.3492') |
| west post | (76.125 + 16.19)/12 | L = 7.6929' (92.315") |
| east post | 6.34375 - 0.1667 (base +2" on a 14" pier, top 3'-0" over grade) | 6.1771' (74.125") |
| truss, both roofs | bearing out to out 359.5625 - 72.4375; bottom chord across the 5 1/2" | 287.125" (23'-11 1/8") |
| standard heel | top-chord plumb 3.5 / cos(atan 4/12) = 3.6893" + 1/4" butt cut, at the OUTSIDE face of bearing | 3.9393" |
| roof plane | deck 91.9393" at the outside face; ridge at x 216": 91.9393 + 143.5625/3 | ridge 139.794", eave (x 56") 86.460" |

## 2. The band between the deck and the panel

The deck bears on the header at +7'-4"; the panel's top plate is at +4'-0". The 2'-4 1/8" between them holds
the band and two 6x6 posts on caps with no lateral row, so the N-S shear has to be carried across it or it
bends each post by about 1,200 lb-ft to reach the panel. `lateral_lines` picks a panel by its plan footprint
alone; `lateral_band` also asks how tall it is, and a band with nothing authored across it is INCOMPLETE by
name (`test_an_unbridged_band_is_incomplete_by_name`).

## 3. The band brace — `SB-BW-BAND`

**Demand.** N-S at the deck: the gable triangle 59.259 sf x 16.661 = 987.32 lb plus each east post's head
half on its 7 1/2" PVC jacket (2026-11-23; it was the bare 5.5" core), 16.661 x 7.5/12 x 6.1771 / 2
= 32.16 lb:

```
V = 987.32 + 2 x 32.16 = 1,051.64 lb        (engine 1,051.72; 100% on this line: the envelope)
```
Rows below that quote 1,034.49 are the 11-22 working and scale by 1.0166.

The garage path (`canopy_garage_diaphragm.md`) is ALSO graded at 100% of V. That is a deliberate double
envelope, confirmed by the owner (2026-11-14), not a sum to be reduced.

### 3a. Geometry and buildable connections

A 2x6 flat sill and top plate and a 6x6 centre post leave two bays W = 24.375", H = 25.125". Each has ONE 6x6
SP No. 2 knee brace running exactly corner to corner, chord to top plate, mirrored to rise inward. It is 5 1/2"
in elevation and 5 1/2" through, equal-width with the 5 1/2"-deep frame, so both faces are flush and take
ER-280 Table 7 type 1, two KBS1Z per end, eight in all.

The 5 1/2" face is what makes the corner work in the **standard open knee** (C-C-2026 p. 325, ER-280 Figure 7).
The clipped end leaves the post and plate at the heels below; each support leg runs from its heel back toward
the corner, so each heel must stand at least the 3" leg from it. A 3 1/2" face puts them at 2.513"/2.438" and
fails; the resolver refuses it.

```
θ = atan(25.125/24.375) = 45.868051°; cos θ = 0.696313, sin θ = 0.717738
length = hypot(24.375, 25.125) = 35.0058"
post heel  = 2.75 / cos θ = 3.94937" up the chord post   margin 0.949" over 3"
plate heel = 2.75 / sin θ = 3.83148" along the top plate margin 0.831" over 3"
included angle, chord: 90 + θ = 135.868°; top: 180 - θ = 134.132°
```

Both are one field bend from the factory 45° (135°): the catalog's one adjustment. The return flanges lie on the
post's and plate's inner faces, clear of the sill and the centre post by the margins above. Two 6x6 blanks about
35" long; eight KBS1Z, twelve 0.131 x 2 1/2" HDG nails each. Specify treated SP No. 2 or better 6x6, KDAT (or
dried to MC <= 19% before the connectors go on).

### 3b. Brace force, type-1 row, buckling, bearing

Mirrored bays with the same joints share V equally, one in tension and one in compression. Each brace crosses
mid-band:

```
V = 1,034.49 lb; h = V/2 = 517.245 lb
v = h tan θ = 517.245 x 25.125/24.375 = 533.16 lb
P = h / cos θ = 742.83 lb
```

ER-280 Table 7 type 1 is the equal-width, **two KBS1Z each end** joint: SPF/HF **1,010 lb** at 45° and **720 lb**
at 30°/60°, MC <= 19%, C_D 1.6 included, for the pair (DF/SP is 1,175 lb for the same row; SPF/HF is the column
recorded). Footnote 3 permits interpolation by brace angle:

```
F1 = 1,010 - (1,010 - 720) x 0.868051/15 = 993.218 lb
ratio = 742.83 / 993.218 = 0.748          (do not double it again)
```

Buckling, NDS §3.7, SP No. 2 6x6 on Table 4D's timbers **wet row**: Fc 525 psi, E_min 440,000 psi, no further
C_M; wind C_D 1.6:

```
Fc* = 525 x 1.6 = 840 psi; l/d = 35.0058/5.5 = 6.3647
FcE = 0.822 x 440,000 / 6.3647² = 8,928.3 psi; r = 10.629
CP = (1+r)/1.6 - √(((1+r)/1.6)² - r/0.8) = 0.98009
capacity = 840 x 0.98009 x 30.25 = 24,904 lb; ratio = 742.83 / 24,904 = 0.030
```

Clipped-end bearing. The compression brace bears on BOTH members it is cut against, whichever carries the
KBS1Z. Envelope: the whole h on the post face, the whole v on the plate face, each 5 1/2" deep. Hankinson
(NDS §3.10.3) on the brace's end grain, Fc* 840 and Fc-perp 375 x 0.67 = 251.25 psi; the member across its grain
at the same 251.25 (Table 4D timbers, conservative for the 2x plate) governs:

```
post:  517.245 / (3.94937 x 5.5 = 21.722 in²) = 23.81 psi; brace Fθ at 45.868° 380.6   0.095
plate: 533.16 / (3.83148 x 5.5 = 21.073 in²) = 25.30 psi; brace Fθ at 44.132° 393.2   0.101
```

Why chord to top rather than sill to centre: it keeps the KBS1Z, and so the tension bay's pull, on the chord
and the header. Sill to centre would hang that pull on the centre post's end ties.

### 3c. The top plate bears END-ON on the chord

A tension bay pulls its chord inward along the whole band, and the chord bears on the panel's double top plate
end. The plate is still the band's bottom chord without a moment connection, in either direction. It is graded
at the whole deck shear, which overstates the band push (517.245 lb) on purpose:

```
area   2 plies x 3.5" x 1.5" = 10.50 in²
f      1,034.49 / 10.50 = 98.52 psi
Fc-perp, Table 4D SP No. 2 timbers 375 x wet C_M 0.67 = 251.25 psi      0.392
```

### 3d. The base plate and sill bear on the far chord

The same way: 3.5 x 1.5 = 5.25 plus the 2x8 `BM-BW-SCSILL` 1.5 x 7.25 = 10.875, total 16.125 in² -> 64.15 psi,
**0.255**.

### 3e. The eave collector

The deck's boundary nailing lands on the trusses and the eave blocking; an H2.5ASS carries about 110 lb of
lateral, so the three heel ties are nowhere near V. Six LTP4Z, `CN-BW-EAVE-1..6` at y 38, 39, 40, 41, 41.75 and
42.375, two per bay, join solid blocking to the glulam top (C-C-2019 p. 280, SPF/HF, the lower direction):

```
1,034.49 / 6 = 172.42 lb vs 450      0.383
```

**Blocking.** Each eave has three solid **2-ply SPF 2x8** blocks (3.0" x 7.25", laminated with 8d common HDG,
two near each end and 12" o.c.), seated on the header between truss faces and bevelled to the deck, each flush
with its header's **inboard** face (x 75.125-78.125" on the west header, mirrored east). The deck over it:

```
outboard face   3.9393 + (75.125 - 72.625)/3 = 4.7727" over the header top
inboard face    3.9393 + (78.125 - 72.625)/3 = 5.7727"
```

A 2x6 (5.50") stops 0.27" short of the deck at the inboard face, so the blank is a 2x8 bevelled to 5.77"/4.77".
The LTP4Z is 3" x 4 1/4" on the header-top line: its upper half is 2 1/8" of block face against 5.77" available,
and its six 0.131 x 1.5" nails land 3.6" or more below the bevelled top. The last block runs to the garage
gable's south face and is the south nailer for the end strap on its line (`canopy_garage_diaphragm.md` §3b),
whose centre it carries (5.5 - 3.0)/2 = 1-1/4" inboard of the header centreline; two plies because that strap
nails two hole lines into it. SPF nails at a lateral G of 0.42. The recipe is `RF-BW-CANOPY.diaphragm` in
`plan/storeys/garage.py`.

**Fastening.** Each LTP4Z takes **12 0.131" x 1.5" HDG nails**, six into the block and six into the glulam,
directly to wood, with no reduction for sheathing. ZMAX with HDG nails because the glulam is treated
(IRC R317.3.1); Simpson publishes no stainless LTP4, so the house's stainless rule yields at these seven plates
(six here and `CN-BW-EAVE-E`, §6). One LS30Z at each block end, six 0.148" x 1.5" HDG nails per angle, on clear
chord or heel wood and never through a truss plate (C-C-2026 p. 313); do not load before the deck nailing is
complete. The deck gets 8d common HDG at 6" boundary spacing; the canopy's panel edges, the ridge included, are
backed by bevelled SPF 2x4 on-edge blocks with three 8d HDG toenails each end
(`canopy_garage_diaphragm.md` §3b). The collector prerequisite reads the actual bevel at each plate.

The deck's own boundary row is the diaphragm note's §4d: 1,034.49 / 6.000 = 172.42 plf vs 190, **0.907**, along
the full 6' eave because the header is the collector. It is the governing row of the record.

### 3f. Vertical equilibrium, chord push, the centre post

Each chord takes h = **517.245 lb** horizontally where the brace centreline meets it, at the sill top,
**+4.125'** (the lowest point of the 3.949" contact, and the one nearest the chord's midspan: the larger
moment). The tension chord is pulled inward onto the plate ends; the compression chord pushes outward and spans
base to head (§5b). Vertical brace forces at the two top landings are +-533.16 lb, equal and opposite.

The compression brace's top end also bears on the centre post, inside 3.949" of the top plate. Take the whole h
there, at the contact centroid 1.975" below the plate, on a pinned 25.125" post:

```
a = 1.97468" = 0.164557', b = 2.09375 - 0.164557 = 1.929193'
M = 517.245 x 0.164557 x 1.929193 / 2.09375 = 78.43 lb-ft
fb = 78.43 x 12 / 27.729 = 33.94 psi vs 850 x 1.6 = 1,360        0.025
top reaction = 517.245 x 1.929193/2.09375 = 476.59 lb on 2 A35Z (695) = 1,390    0.343
```

Its bottom end likewise presses v down onto the sill: bearing on the panel's plate, no screw withdrawal. The
sill still hands the full shear to the panel.

### 3g. Plate screws, NDS §12.4.1

Eight SDWS22400DB per plate retain ER-192's dry-service Z' = 405 x 1.6 = 648 lb and W'p = 425 x 1.6 = 680 lb.
The tension bay's four top screws share its one 533.16 lb landing; the compression bay's end presses its plate
up into the header, bearing only:

```
lateral per screw = 1,034.49/8 = 129.31 lb
withdrawal at top = 533.16/4 = 133.29 lb
resultant = 185.71 lb, α = atan(133.29/129.31) = 45.868°
Z'α = 680 x 648 / (680 cos²α + 648 sin²α) = 664.10 lb; ratio 0.280
sill: withdrawal zero, resultant 129.31 lb, α = 0°, capacity 648 lb; ratio 0.200
```

### 3h. Header couple

Each top landing is the top/centre corner, 2.75" from the band's centre:

```
C = 533.16 x 2 x 2.75/12 = 244.36 lb-ft
head couple = 244.36/4.979167 = 49.08 lb
header-depth couple = 1,034.49 x 0.989583/4.979167 = 205.60 lb
```

The larger, 205.60 lb, rides each chord's head uplift: 426.44 + 205.60 = **632.04 lb**, with no favourable
vertical component credited.

## 4. The panel — `W-BW-SCREEN`

2x4 KDAT studs at 16" o.c., flush with the 6x6 chords' west faces so the ZIP laps them and the west corrugated
plane is the garage's. The **WEST** face is 7/16" taped ZIP (the garage's panel, 2026-11-18) under `corrugated-panel-24`, 8d at 4" edges and 12" field
(`S8ACN`, blocked): it carries the shear alone. The **EAST** face is white painted 3/4" MDO, finish only
(`entry_screen_mdo.md`), so it adds no shear.

### 4a. Unit shear and aspect — SDPWS-2015 Table 4.3A

Wood structural panels - sheathing, **7/16"** (the ZIP, OSB), 8d, 1-3/8" penetration. Read off the published
table (AWC's 2015 SDPWS, Chapter 4, 2026-11-18): v_w nominal by edge spacing 6" / 4" / 3" / 2" is
670 / 980 / 1,260 / 1,640 plf; G_a at 4" is 22 kips/in OSB (15 PLY). ASD is v_w / 2.0 (§4.3.3); KDAT is SYP,
so footnote 3's specific-gravity factor is 1.0, and the framing is dry (fn. 5 does not apply). The wall's own node
run oversails both chords and nothing holds the oversail down, so the panel is read over the chords' out-to-out
length:

```
6" edges   1,034.57 / 5.4375 = 190.27 plf vs 670 / 2 = 335.0     0.568
4" edges   190.27 vs 980 / 2 = 490.0                             0.388   <- authored
aspect     4.0783 / 5.4375 = 0.750 vs 3.5                        0.214
```

The 15/32" row carried until 2026-11-18 quoted 365 / 530 / 685 / 895 plf as nominal: those are half the table's
730 / 1,065 / 1,370 / 1,790, so the old 265 plf (0.718) was read at half capacity. Footnote 2 would lift the 7/16"
row to the 15/32" one (studs at 16" o.c.); it is not taken.

### 4b. The chords' hold-down, full height

The couple the chords take is the deck's shear over the whole frame, header top to the chord bases:

```
H = (88 + 16.19)/12 = 8.6825'
T = 1,034.49 x 8.6825 / 4.9792 = 1,803.9 lb
  + the column's net roof uplift, 40 ft² x (16.661 - 0.6 x 10) = 426.4 lb
  = 2,230.3 lb vs CBSTQ66Z-SDS2 cracked 3,060 (ESR-3050 Table 2)       0.729
```

No screen-wall dead weight is credited against uplift. The cracked value is graded: the wet-service reduction
ESR-3050 §4.1 names does not move it, because the cracked column is the concrete's (uncracked is 4,375) and
0.7 x 4,375 = 3,062 is above it.

### 4c. The base shear, on ONE base

The ⚠ above. F2 along the screen (`Connector.axis = "y"`):

```
1,034.49 / 1,270 = 0.815        (F1 485 would read 2.13: the axis matters)
```

It is the COMPRESSION chord, so no uplift combines with it.

## 5. Heads and bases, all four posts

### 5a. Parts

Both headers end flush on the outer faces of their end posts. **ACE6Z** end caps at all four heads (ESR-2604
§3.1.3 and Table 3, MAX nailing: **1,950 lb uplift / 1,760 lb along the beam**, the lateral PARALLEL to the beam
only, fn. 6). Across the beam, **one A35Z** on each post's inboard face, the only face with soffit over it
(ESR-3096 Table 5, F1 695 / F2 845, the lower taken). The west posts also take one A35Z at the panel's top-plate
end (`CN-BW-PLATE-S/-N`). Bases: **CBSTQ66Z-SDS2** cast in, F2 along y: 12 ga base, 10 ga x 3" straps, W 5 1/2",
D 6 7/8", H 8 3/4", (14) SDS 1/4 x 2; ESR-3050 Table 2, wind and SDC A&B, uplift 4,375 uncracked / **3,060**
cracked; C-C-2026 p. 85 fn. 5, F1 485 / F2 1,270, 3" side cover. No ABU66SS, CCQ cap or anchor bolt stands
anywhere on these posts.

### 5b. Demands

Own drag, 16.661 psf on 5.5" (w = 7.636 plf), half at each end:

```
west   7.636 x 7.6929 / 2 = 29.37 lb        east (7 1/2" jacket, 10.413 plf)  10.413 x 6.1771 / 2 = 32.16 lb
```

The west posts also take the screen's out-of-plane E-W load at the top plate: the panel spans sill to plate and
the band plate to header, so the plate line carries half of each,

```
w = 16.661 x (4.0783/2 + 2.34375/2) = 53.50 plf,  P = 53.50 x 4.5208 / 2 = 120.93 lb per post
a = 4.0000 + 1.3492 = 5.3492' above the base,  b = 7.6929 - 5.3492 = 2.3437'
head across = 29.37 + 120.93 x 5.3492 / 7.6929 = 113.46 lb
base across = 29.37 + 120.93 x 2.3437 / 7.6929 =  66.22 lb
```

on the full solid face. `P` reaches each post through the A35Z at the plate end: 120.93 / 695 = **0.174**.

Head uplift is the net roof uplift, 426.44 lb. On a chord add the band's couple, the larger of the deck's shear
acting a header depth above the top plate (205.60, §3h) and the brace couple on the glulam (49.08): **632.04 lb**,
with nothing favourable credited.

**The band push, N-S, on a chord only.** L = 7.692917'. Its 517.245 lb point load stands at the sill top,
+4.125' (§3f):

```
a = 4.125 + 16.19/12 = 5.474167'; b = L - a = 2.218750'
own drag at each end = 7.63629 x 7.692917 / 2 = 29.373 lb
head along = 29.373 + 517.245 x a/L = 397.43 lb
base along = 29.373 + 517.245 x b/L = 178.55 lb
brace moment = 517.245 x a x b/L = 816.64 lb-ft
own drag moment = 7.63629 x L²/8 = 56.49 lb-ft
N-S moment = 873.13 lb-ft, fb = 873.13 x 12 / (5.5³/6) = 377.85 psi
```

### 5c. Rows (linear interaction)

| row | working | ratio |
|---|---|---|
| ACE6Z uplift + along, CW / CNW | 632.04/1,950 + 397.43/1,760 = 0.3241 + 0.2258 | **0.550** |
| A35Z head across, CW / CNW (one angle each) | 113.46/695 | 0.163 |
| A35Z panel top plate | 120.93/695 | 0.174 |
| CBSTQ base uplift + across | 426.44/3,060 + 66.22/485 = 0.1394 + 0.1365 | 0.276 |
| CBSTQ base uplift + along | 426.44/3,060 + 178.55/1,270 = 0.1394 + 0.1406 | **0.280** |
| NDS column, combined | below | 0.538 |
| ACE6Z, RE / RNE | 426.44/1,950 + 32.16/1,760 = 0.2187 + 0.0183 (jacket, 11-23) | **0.237** |
| A35Z head across, RNE | 23.585/695 | 0.034 |
| CBSTQ base, RE across | 426.44/3,060 + 23.585/485 = 0.1394 + 0.0486 | 0.188 |
| CBSTQ base, RNE along | 426.44/3,060 + 23.585/1,270 = 0.1394 + 0.0186 | 0.158 |
| NDS column, RE, combined | below | 0.225 |

West column (Table 4D wet row, Fc 525 x snow C_D 1.15 = 603.75 psi; Fb 850 x 1.6; E_min 440,000): axial
3,408.5 lb / 30.25 = 112.68 psi; l/d = 92.315/5.5 = 16.785; FcE = 0.822 x 440,000 / 16.785² = 1,283.8 psi;
C_P 0.8769; Fc' = 529.44 psi. Interaction (112.68/529.44 + 377.85/1,360) / (1 - 112.68/1,283.8) = **0.538**,
governed by the N-S push rather than the E-W plate load.

East column: axial 3,396.6 lb -> 112.28 psi; l/d = 74.125/5.5 = 13.477; FcE = 1,991.2 psi; C_P 0.9274;
Fc' = 559.94 psi; M = 7.636 x 6.1771²/8 = 36.4 lb-ft, fb = 15.76 psi.
(112.28/559.94 + 15.76/1,360) / (1 - 112.28/1,991.2) = **0.225**.

The west heads govern at the cap, 0.550, ahead of the column's 0.538; the deck's 0.907 still governs the record.

### 5d. ~~Dry service at the connectors~~ — WET by one exposure rule (2026-11-23, review M2)

The canopy zone takes ONE rule (`engineering/canopy_service.py`): exposed to weather under the open canopy →
WET; under roofing → dry, stated. Every connector here is exposed, so: where the catalog publishes a > 19% column it
is read; otherwise C_M 0.70 on the dry row. ESR-2604 §3.2.2 (ACE6Z), ESR-3096 (A35Z) and ESR-3050 §4.1 (CBSTQ)
cover MC <= 19% only, so their wet values are a reading OUTSIDE the reports, said on the record.

```
KBS1Z slat end   C-C-2026 p. 324, MC > 19%, DF/SP (KDAT SP), type 1: 1,055 @ 45°, 835 @ 30/60
                 at 45.868°: 1,055 - 220 x 0.868/15 = 1,042.3;  755.2 / 1,042.3          = 0.725
SDWS plate screws Z' and W' x C_M 0.70                          top 0.406, sill 0.290
ACE6Z head (CW)  635.5 / (1,950 x 0.70 = 1,365) + 403.5 / (1,760 x 0.70 = 1,232)
                 = 0.4656 + 0.3275                                                         = 0.793
ACE6Z head (RE)                                                                            = 0.339
CBSTQ base       every term x 0.70                       CW along 0.403, RE across 0.294
A35Z             lower of F1/F2 x 0.70                   CW head 0.233, plate 0.249
LTP4Z eave clips DRY — on the nailers under the roof sheathing and roofing                 = 0.390
```

The dry SPF column read 0.760 at the KBS1Z; the wet DF/SP column is the published row for the species and moisture
actually there. The column itself is still graded on Table 4D's wet row.

### 5e. The piers are 14" round under a CBSTQ

ESR-3050 Table 2 fn. 4 wants 3" of side cover. The straps' outer faces stand 2.75 + 0.135 = 2.885" off the axis,
1.5" either side of centre:

```
12" round   corner radius sqrt(2.885² + 1.5²) = 3.252"   cover 6 - 3.252 = 2.75"   short
14" round                                                   cover 7 - 3.252 = 3.75"   OK
```

The 14" cage is (6) #5 at 2" cover (`north_entry_piers.md` §13): 1.86 in² against ACI 318-19 §10.6.1.1's 1.539
(1% of the gross 153.94 in²), its bars on a 4.3125" radius clearing the strap corners by 0.75" at any rotation.

### 5f. The west bases' seat-beam ends

With `axis="y"` the CBSTQ strap leaves sit on the column's E/W faces. `BM-BW-HOUSE-SEAT`/`-GARAGE-SEAT` start
1/8" past the SDS heads (fit-up clearance, not a catalog figure):

```
gap  = 0.1345 (10 ga strap) + 0.190 (SDS head, ESR-2236 Fig. 1 max) + 0.125 = 0.4495"
start x = 78.125 + 0.4495 = 78.5745"                 (heads at 0.172 min: 0.143" gap)
pier bearing at the beam faces, 14" round on x 75.375": 75.375 + sqrt(7² - 1.5²) - 78.5745
        = 82.2124 - 78.5745 = 3.638" >= 3" (R507.5.2); 3.80" on the centreline
pack 3 1/2" from the beam end, x 78.5745-82.0745: corner radius
        sqrt((82.0745 - 75.375)² + 1.75²) = 6.924" < 7"; clear of the strap face (78.2595)
```

The seat beams hang on **LUS26-2Z** (W 3 1/8" on the 3" beam) and `BM-BW-SCSILL` on **LUS28Z** (W 1 9/16" on the
1 1/2" sill), C-C-2026 p. 114. The LUS26-2Z is 3.125 + 2(0.048 + 1.0) = 5.221" flange to flange and clears the
3" CBSTQ strap on the same face by (3.125/2 + 0.048) - 1.5 = 0.110" a side. Demand against allowable:
`north_entry_piers.md` §12. The seat-beam `HETA20Z` pairs at the east piers (E/GE) are trimmed at the beam top
(`AN-BW-HETA-TRIM`); the canopy's own headers carry no HETA in the `kdat` variant.

**The hanger sits on a filler.** The strap is 3" wide and centred on the 5 1/2" face, as is the 3" beam, so the
strap and its SDS heads stand behind the whole beam end and no beam length brings the end inside
0.1345 + 0.190 = 0.3245" of the post face. C-C-2026 p. 22 note m is a MAXIMUM end gap of 1/8". The LUS26-2Z is
therefore nailed over a filler notched round the strap: two strips of 3/8" nominal treated plywood (11/32",
0.344"), each 1 1/4" wide, (5.5 - 3)/2, and as tall as the hanger flange.

```
filler face          0.344" off the post face; SDS heads 0.172-0.190 + strap 0.1345
                     = 0.3065-0.3245"  -> 0.020-0.037" proud of the heads
end gap to hanger    0.4495 - 0.344 = 0.1055" <= 1/8" (C-C-2026 p. 22 note m)       met
beam on the seat     2 - 0.1055 = 1.8945" of the LUS26-2Z's 2" seat (B)
flanges on filler    flange 1" at 1.5625 + 0.048 = 1.6105" to 2.6105" off centre; strip
                     1.5"-2.75": 0.1105" clear of the strap edge, 0.1395" inside the post edge
header nails (16d HDG, 3 1/2", 0.162")  into the post 3.5 - 0.048 - 0.344 = 3.108"
                     >= 10D = 1.62" (NDS 12.3.1 full-penetration lateral design value)
```

The hanger is a tie and locator; gravity bears on the 3 1/2" SS316 pack on the pier (>= 3", R507.5.2). The pack
is cast one 18 ga seat (0.048") under the soffit so the hanger seat bears on it; beyond the seat it carries the
beam on an 18 ga SS316 shim strip 3.5 - 1.8945 = 1.61" long. Simpson publishes no filler installation for the
LUS, so the catalog row is used on the strength of the full nail penetration (§9).

## 6. The open front: chord, couple, drift

The E-W case, `kdat`, at 16.661 psf. The slope band is 26.667 sf at the footprint centroid, y 40.219; each header
band is 2 x 0.98958 x 5.4375 = 10.762 sf at the headers' own centroid, (37.2708 + 42.7083)/2 = y 39.990 (the
bands resolve at their own stations, `RoofWind.member_bands`):

```
slope band   26.667 x 16.661 = 444.29 lb at y 40.219
header bands 10.762 x 16.661 = 179.31 lb at y 39.990
posts        2 x 23.585 = 47.17 lb at y 37.500 and 42.479         total 670.77 lb
y_V = (444.29 x 40.219 + 179.31 x 39.990 + 23.585 x 37.500 + 23.585 x 42.479) / 670.77 = 40.142
e = 43.219 - 40.142 = 3.077'     M = 670.77 x 3.0774 = 2,064.2 lb-ft
chord  M / W' = 2,064.2 / (29.71875 - 6.28125 = 23.4375') = 88.07 lb in each header
  glulam, Table 5A 24F-V4 Ft 1,100 x wet 0.80 x C_D 1.6 = 1,408 psi; 88.07 / 65.31 in² = 1.35 psi   0.001
  end strap (LSTA24): 88.07 + 1,034.49/6 = 88.07 + 172.42 = 260.49 lb vs 823.33 (12/18 nails)        0.316
  chord into the end strap's 2-2x8 block: header and block are two pieces, so a plate joins them
    west, CN-BW-EAVE-5/-6 share it, each also carrying its §3e collector share:
      88.07/2 + 172.42 = 216.45 lb vs LTP4Z 450 (SPF/HF, lower direction)                    0.481
    east, CN-BW-EAVE-E alone (the east header is no collector): 88.07 lb vs 450               0.196
the couple into RF-GARAGE, across ITS 24.000': 2,064.2 / 24.000 = 86.01 lb on each of W-G-W and W-G-E
  W-G-W  86.01 / 18.675' = 4.606 plf vs 182.5  0.025      W-G-E  86.01 / 21.008' = 4.094 plf  0.022
```

The joint is a tie: it hands the couple on, and the rows above are where it goes. `CN-BW-EAVE-5`/`-6` sit at
y 41.75 / 42.375 on the glulam and clear of `CN-BW-CAP-NW`; the joint-bay block still spans truss face to
garage gable, so 6 1/8" of it oversails the beam end, tied by its LS30Z and the deck.

**SDPWS 4.2.5.2's drift limit** is ASCE 7's story drift under SEISMIC forces including torsion. The jurisdiction
profile puts this site in SDC A, which ASCE 7-16 §11.7 designs to §1.4 alone: NOT APPLICABLE, earned. Any other
category and the record is INCOMPLETE.

## 7. The headers, 5-1/2" x 11-7/8" glulam (`roof_beam`)

24F-V4 DF (a 5-1/2" width is Western species), wet, snow C_D 1.15. Half the roof, 80 ft², over the 5.375'
roof-bearing run, on posts 4.9792' apart with 0.1667' (south) and 0.2292' (north) past them:

```
w = 80 / 5.375 x (73.7 + 10) = 1,245.77 plf          (snow 1,096.93, dead 148.84)
R (north post, all loaded) = (1,245.77 x 5.375) x 2.5208 / 4.9792 = 3,390.0 lb
  (2.5208' = the loaded run's centroid, y 40.0208, from the south post)
  + snow off the south overhang  1,096.93 x 0.1667 x 0.0833 / 4.9792 = 3.1  -> 3,393.1 lb
bearing on the 5.5" post end  3,393.1 / 30.25 = 112.2 psi vs 650 x 0.53 = 344.5        0.326
M = 1,245.77 x 4.9792² / 8 - 148.84 x (0.1667² + 0.2292²) / 4 = 3,857.7 lb-ft
fb = 3,857.7 x 12 / 129.26 = 358.1 psi vs 2,400 x 0.80 x 1.15 = 2,208 (C_V capped at 1.0)    0.162
```

Shear (0.161) and deflection (0.053) are the engine's own readings of the same load. The shorter run raises w a
little; bearing on the post is 0.326.

### 7c. The trusses' chord bearing on the header

**Amended 2026-11-23 (review C-4).** The old reading put the beam's uniform load x 2.0' on every truss, which spreads
the deck's 6.0' over the 5.375' bearing run (x 1.116) and puts the drift's average on each truss. Each truss now takes
the load at ITS station, on its own tributary, with NDS 2018 §3.10.4's bearing-area factor.

Trusses at y 37.3333 / 39.3333 / 41.3333; the garage's gable truss stands at 43.2812 and shares the joint bay. Tributary
widths: T1 (37.3333 - 37.2188) + 1.0 = 1.1146'; T2 2.0'; T3 1.0 + (43.2812 - 41.3333)/2 = 1.974'. The drift triangle is
the preferences' own: design snow 73.7 = balanced 42 + a mean surcharge 31.7, slope 50.3 / 9.8 = 5.133 psf/ft, so the
surcharge at a truss is 31.7 + 5.133 (40.219 - y) (the canopy's mid-depth y 40.219):

```
T1  surcharge 46.5   snow 88.5 psf   R = (88.5 + 10) x 1.1146 x 13.333 = 1,464 lb   1,464 / (1.5 x 5.5) = 177.5 psi
T2  surcharge 36.2   snow 78.2 psf   R = (78.2 + 10) x 2.0    x 13.333 = 2,353 lb   2,353 / 8.25       = 285.2 psi
T3  surcharge 26.0   snow 68.0 psf   R = (68.0 + 10) x 1.974  x 13.333 = 2,052 lb   2,052 / 8.25       = 248.8 psi
Fc-perp 650 x C_M 0.53 = 344.5 psi.  C_b = (1.5 + 0.375) / 1.5 = 1.25 where the chord face is >= 3" from the beam
end (T2, T3); T1's chord is flush with the end, C_b 1.0.
T1 177.5 / 344.5 = 0.515    T2 285.2 / 430.6 = 0.662 (governs)    T3 248.8 / 430.6 = 0.578
```

It governs both headers at **0.662** (was 0.877), ahead of the post bearing's 0.326. The fabricator's own chord check
(SPF Fc-perp 425 psi, dry, under the roof) is the supplier's and is in the criteria schedule. A chord that stopped at
the header centreline, 2.75", would read 570.5 / 430.6 = 1.325 on T2
(`test_a_chord_stopped_at_the_header_centreline_is_over`): that is why the heel is at the outside face of bearing and
the bottom chord crosses the full 5 1/2". The beam's own bending, shear and post bearing keep the uniform 80 sf load,
which bounds the three truss lines and the joint bay's strip that lands on the garage gable truss.

## 8. Backups

Two other bracings of the same band are carried as documented backups; neither is built.

* **One 4x6 per bay at c = -6 1/2".** 3 1/2" in elevation, 5 1/2" through, chord to top, two KBS1Z type 1 each
  end at 45°. Each heel needs 3.5/√2 + 3 = 5.47487" along its face, so c <= -6.22487"; length 26.340". P = h √2 =
  517.245 x 1.41421 = 731.5 lb vs 1,010, **0.724**; Table 4B (Fc 1,400 x 0.8, E_min 510,000 x 0.9), l/d 7.5257,
  buckling 32,318 lb (0.023). Push 517.245 lb at +4.666667'.
* **The fourteen-slat chevron.** 2x4 at 2 1/4" clear, west face flush, c_j = -0.375 + 5.3033 j", j = -3...3; j = 0
  is screwed infill and the other six slats a bay take 24 KBS1Z type 2. Four braces cross mid-band:
  P = (V/8) √2 = 129.31 x 1.41421 = 182.87 lb against 540 lb (0.339), buckling 4,901 lb (0.037); chord push
  387.9 lb, centre push 776.0 lb. A corner needs 1.5/√2 + 3 = 4.06" of bearing-face reach, so j = 0 stays unbraced.

## 9. Not graded here / still open

* **The truss end chords (N-S), 764 lb**: the truss order (`rafter/RF-BW-CANOPY`; no splice-slip value is asked for). The truss fabricator's sealed component design and reaction schedule is an external
  deliverable; when it arrives, author `Roof.published_reactions` on both roofs and record the component seal in
  `engineering.toml`. `rafter/*`, `structural.truss_reactions` and `uplift_capacity` stay UNKNOWN until then.
* **The soils report**: 2,000 psf is presumptive and the soil class is presumed, so every record prints it.
* **The seat-beam LUS26-2Z on its 11/32" filler** (§5f): Simpson publishes no filler installation, and the end gap
  is 0.1055", not a rated reading. Gravity does not depend on it (the pack carries the beam). One line to Simpson
  closes it; the fallback is a cast-in `HETA20Z` pair, which is a new embedment 1.83" off the 14" pier's edge at the
  beam faces, against the CBSTQ's cast-in body, and puts a tie on piers the owner chose to leave without one.
* **The CBSTQ66Z-SDS2 download** (19,335 lb): no record grades it.
* **Nail withdrawal at the LTP4Z under the deck's own uplift**: the heel ties carry that.
* **ColorGard snow retention** on the east eave: `north_entry_structure.md` §5.

## 10. 2026-11-18 amendment: the column lines 3/16" out

The garage sheathing went 5/8" CDX -> 7/16" ZIP with its face held on the node line, so the plates, and with
them both header centrelines (decision #108), moved 3/16" outward: x 6.265625' / 29.734375', 23.46875' apart.
The canopy's eave overhang went 1'-7 3/8" -> 1'-7 3/16" so its fascia stays on the garage's line: the canopy is
still **26.667'** across and the header tributary still 80 ft². The trusses grew 3/8" out to out, so the ridge rose
(3/16")/3 = 1/16".

**Wind** (`canopy_garage_diaphragm.md` §2 at the new ridge, 20.764 + 0.0052 = 20.7692'):

```
K_z = 2.01 (20.7692/1200)^(2/7) = 0.63072    q_h = 18.151 psf    p = 0.6 x 18.151 x 0.85 x 1.80 = 16.6622 psf
east post head half   16.6622 x 5.5/12 x 6.1771 / 2 = 23.587 lb
N-S  59.259 sf x 16.6622 = 987.39;  V_y = 987.39 + 2 x 23.587 = 1,034.57 lb    (x 1.000072)
E-W  37.429 sf x 16.6622 = 623.64;  V_x = 670.82 lb
```

**Rows linear in V** (§3-§4) move by x 1.000072 and read as the 11-14 working to its printed figures: P 742.89 lb
(0.748), plates 98.53 / 64.16 psi, clips and deck boundary 172.43 (0.383 / 0.908), screws 185.72 lb (0.280),
centre post 476.63 lb (0.343). Hold-down 1,034.57 x 8.6825 / 4.9792 = 1,804.0 + uplift 40 x (16.6622 - 6) = 426.49
-> **2,230.5 lb (0.729)**; base shear 0.815; chord head 426.49 + 205.61 = 632.10 lb; ACE6Z 0.550, CBSTQ along 0.280,
west column 0.538, east 0.225.

**What moved: the open front (§6).** The resultant's y and the moment are p-scaled; the header spacing is 3/8"
longer:

```
y_V = (444.33 x 40.219 + 179.32 x 39.990 + 23.587 x 37.500 + 23.587 x 42.479) / 670.82 = 40.1416
M = 670.82 x (43.219 - 40.1416) = 2,064.35 lb-ft
chord M / 23.46875 = 87.96 lb (was / 23.4375 = 88.07)
end strap 87.96 + 172.43 = 260.39 lb (0.316); chord into the end block, west 87.96/2 + 172.43 = 216.41 lb (0.481),
east 87.96 lb (0.195); the couple into RF-GARAGE 2,064.35 / 24 = 86.01 lb: W-G-W 4.606 plf, W-G-E 4.094 plf
```

**The headers (§7)** are unchanged: 80 ft², 1,245.77 plf, chord bearing 302.0 psi, **0.877**.

**The panel (§4a)** is the 7/16" ZIP's own row, 490 plf ASD, 0.388.

## Sources

AWC SDPWS-2015 Table 4.3A, §4.2.5.2, §4.3.4; NDS 2018 §3.7, §3.10.3, §12.3.1, §12.4.1 and Supplement Tables 4B, 4D,
5A; IAPMO UES ER-280 Table 7 (KBS1Z) and ER-192 Tables 5, 7 (SDWS22400DB); ICC-ES ESR-2105 Table 3 (LSTA24),
ESR-2604 Table 3 (ACE6Z), ESR-3096 Table 5 (A35), ESR-3050 Table 2 (CBSTQ66Z-SDS2), ESR-2236 Fig. 1; Simpson
C-C-2026 pp. 22 (note m), 85, 114, 313, 324-325 and C-C-2019 p. 280 (LTP4); ACI 318-19 §10.6.1.1; ASCE 7-16 §11.7.

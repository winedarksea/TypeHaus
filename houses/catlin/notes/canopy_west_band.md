# The canopy's west band, its heads and bases, and the open front — hand-worked basis

**House:** catlin
**Structure:** `RF-BW-CANOPY`'s west line — `W-BW-SCREEN`, the band over it (`SB-BW-BAND`),
the chords `PT-BW-CW`/`-CNW`, the glulam headers `BM-BW-RW`/`-RE`; the heads and bases of all
four posts (`PT-BW-CW`/`-CNW`/`-RE`/`-RNE`, `kdat`); the open front's chord and couple.
**Written:** 2026-09-30, by hand, before `engineering/lateral_band.py`, `open_front.py`,
`roof_beam_glulam.py` and `wood_roof_post_joints.py` were encoded. §3 and §5b-c re-worked
2026-10-04 for the slat band, before `lateral_band_slats.py`; the straps it replaced are in §8.
**Oracle for:** `lateral_band.py` / `lateral_band_slats.py` (§3-§4), `wood_roof_post.py` / `wood_roof_post_joints.py` (§5),
`open_front.py` (§6), `roof_beam_glulam.py` (§7); reproduced by
`tests/test_canopy_west_band_calcs.py`.
**Companions:** `canopy_garage_diaphragm.md` — the delivery to the garage and the envelope this
note works inside; its §4f points here. `north_entry_canopy_lateral.md` §8c, corrected by §2.
**What is asked of the reviewer:** §3b's equal share between the mirrored bays and the
mid-band count it rests on, and §4b's full-height overturning at the chord bases. Those are the
judgement and the row nearest its limit after the deck.

> ⚠ **The chord base shear is on ONE base, and that is not conservatism for its own sake.** The
> base plate and the sill bear END-ON against the chords, in compression only, so the panel's
> in-plane shear reaches the chord it pushes against and none of it the other. Share it 50/50
> and the row reads 0.41 for a joint that does not work that way.

> ⚠ **The overturning lever is the deck to the chord BASES, 8.625', not the panel's 4.083'.** The
> deck delivers at the header top and the pinned bases are 1'-3 1/2" below the panel's sill; the
> couple between is all the chords', whatever the panel does inside it.

---

## 1. Geometry

| term | working | value |
|---|---|---|
| chords, centre to centre | `PT-BW-CW` y 37.5000 to `PT-BW-CNW` y 42.4792 | **4.9792'** |
| chords, out to out | 4.9792 + 5.5/12 | 5.4375' |
| clear between chord faces | 4.9792 − 5.5/12 | 4.5208' |
| header | 5-1/2" x 11-7/8" glulam, top +7'-4" | soffit **+6.34375'** |
| panel | base −1" (−0.0833'), `top` 4'-1" | top **+4.0000'**, h 4.0833' |
| band | 6.34375 − 4.0000 | **2.34375'** (2'-4 1/8") |
| chord bases (CBSQ, west) | `BEARING_TOP_FT` | −1.2917' |
| west post | 6.34375 + 1.2917 | 7.6354' |
| east post (`kdat`) | 6.34375 − 0.1667 | 6.1771' |

## 2. What §8c of the lateral note had wrong

It said "every foot of the deck's west boundary lands directly on the panel's top plate". The
top plate is at +4'-0" and the deck bears on the header at +7'-4". Between them, for 2'-4 1/8",
there were only the in-fill slats and the two 6x6s on caps with no lateral row: the N-S shear
had to bend each post by ~1,250 lb-ft to reach the panel. Nothing graded it, because
`lateral_lines` picks a panel by its plan footprint alone. It now also asks how tall it is
(`lateral_band`): a band with nothing authored across it is INCOMPLETE, by name.

## 3. The band brace — 45° slats as knee braces (owner, 2026-10-04)

**Demand.** N-S at the deck, `kdat`: the gable triangle 991.0 lb (§2 of the diaphragm note)
plus each east post's head half, 16.7232 x 5.5/12 x 6.1771 / 2 = 23.67 lb:

```
V = 991.01 + 2 x 23.67 = 1,038.35 lb       (100% on this line: the envelope)
```

**3a. Geometry (`SB-BW-BAND`).** A 5-1/2"-wide frame between the chord faces, flush with the
6x6 and glulam faces. A 2x6 flat SILL on the panel's double top plate (+4'-0" → +4'-1 1/2"); a
2x6 flat TOP PLATE under the glulam soffit (+6'-2 5/8" → +6'-4 1/8"); a 6x6 KDAT CENTRE POST
between them at midspan (y 39.9896). Two bays, each filled with 1-1/2" x 3-1/2" KDAT slats at
45°, 1-1/2" clear square to the slats (the old screen's face and gap), **mirrored: every slat
rises toward the centre post**. Slats are in-plane, butted, flush with the WEST face, with one
KBS1Z at each end on that face.

```
clear between chords     42.2500 − 37.7292 = 4.5208' = 54.250"
bay width W              (54.250 − 5.5) / 2 = 24.375"
bay height H             6.21875 − 4.1250 = 2.09375' = 25.125"
pitch                    3.0" square to the slats = 3.0 / sin 45° = 4.2426" along a plate
centreline (bay frame, u from the chord face toward the centre, z from the sill top)
                         z = u − c,   c_j = (W − H)/2 + j x 4.2426 = −0.375 + 4.2426 j
```

A slat runs from the sill (c > 0) or the chord (c < 0) to the centre post (H + c > W) or the
top plate. Its centreline length is (min(W, H + c) − max(0, c)) x √2. j = ±5 gives 5.00": too
short for a KBS1Z leg at both ends, so the rule drops anything under 8". That leaves
**j = −4 … +4: nine slats a bay, eighteen in all, 36 KBS1Z**:

| j | c | from → to | length |
|---|---|---|---|
| −4 | −17.346 | chord → top plate | 11.00" |
| −3 | −13.103 | chord → top plate | 17.00" |
| −2 | −8.860 | chord → top plate | 23.00" |
| −1 | −4.618 | chord → top plate | 29.00" |
| 0 | −0.375 | chord → centre post | **34.47"** |
| 1 | 3.868 | sill → centre post | 29.00" |
| 2 | 8.110 | sill → centre post | 23.00" |
| 3 | 12.353 | sill → centre post | 17.00" |
| 4 | 16.596 | sill → centre post | 11.00" |

**Connector count review, 2026-10-04.** Keeping only the top-landing slats would connect
four a bay (16 KBS1Z), but only **two** of those cross mid-band. The five-slat calculation
below also needs j = 0, +1, +2, which end on the centre post; removing their end ties
invalidates its force sharing and vertical cancellation. The present bill therefore keeps
36. A smaller connected set needs a separate load-path calculation, including the remaining
butted slats' compression-only action; the existing pass does not establish that 36 is the
minimum possible count.

**Drawn cuts and hardware.** Each slat is the full 1-1/2"-wide diagonal strip clipped to all
four bay faces, with horizontal miters flush to the plates and plumb cuts to the posts.
The j = 0 board also clips both corner long points. Engineering still reads the centreline
length above; takeoff nests the blank spanning the long points, including miter waste.
Each end shows one folded KBS1Z on the flush west face: two 3" legs with two perpendicular
1-1/2" flanges, 16-gauge steel, and twelve open fastener holes. Dimensions and form follow
[ER-280 Table 7 / Figure 7](https://forms.iapmo.org/ues_reports/reports/er_0280.pdf) and
[Simpson C-C-2019 p.296](https://assets.unilogcorp.com/187/ITEM/DOC/Simpson_Strong_Tie_100313582_Specification_Sheet.pdf).
The punching positions and bend radii are not dimensioned there: the holes are illustrative
and sharp folds stand for the bends. This is a dimensioned visualization, not manufacturer
fabrication CAD or confirmation that every flange/fastener fits this flat-plate installation.
In particular, the j = 0 slats meet the centre post near its top: the drawn 3" support legs
extend beyond that post into the plate/header region. Their attachment detail needs review;
the 0.274 connector ratio alone does not resolve that footprint.

**3b. The slats and their ends.** A slat is tension in one direction of push and compression in
the other. The KBS1Z is rated along the brace (the axis it shares with the brace), so each slat
works both ways. **The two bays share V equally**: they are mirror images with the same slats
and the same joints, so a push puts one bay in tension and the other in compression at the same
stiffness. In-plane butt screws were rejected first: ER-192's rows want the screw "straight
into the side grain … at a 90-degree angle" (Table 5 fn. 3), and a 45° butt has no such
screw.

The verticals carry the band's shear only by bending, and a vertical loaded along its length
by its landing slats has **zero shear at mid-band**. So the slats crossing mid-band, z =
12.5625", carry the bay's whole half. Those are c in [−12.5625, 11.8125], i.e. j = −2 … +2,
**five**:

```
V_bay = 1,038.35 / 2 = 519.18 lb
P     = 519.18 / (5 x cos 45°) = 146.85 lb per slat, tension or compression
h     = P cos 45° = 103.84 lb, horizontal (and vertical) at each end
```

KBS1Z, IAPMO UES ER-280 Table 7, connection type 2 (a 2x brace, one connector each end, 12 - 8d
x 1-1/2 or SD9x1-1/2), F1 at 45°, C_D 1.6 included; the catalog's SPF/HF 540 lbf, not the 630
DF/SP row. Dry service at the connectors, as §5d prints for every part here:

```
146.85 / 540 = 0.272
```

Slat compression, NDS §3.7, about the 1-1/2" face (the out-of-plane 3-1/2" is far stiffer); SP
No. 2 2x4, Table 4B, wet (C_M 0.8 on Fc, 0.9 on E_min), C_D 1.6, longest slat 34.47":

```
Fc*   1,450 x 0.8 x 1.6 = 1,856.0 psi      Emin' 510,000 x 0.9 = 459,000
le/d  34.47 / 1.5 = 22.98   FcE = 0.822 x 459,000 / 22.98² = 714.4 psi   α = 0.3849
C_P   (1.3849/1.6) − sqrt((1.3849/1.6)² − 0.3849/0.8) = 0.3478   Fc' = 645.6 psi
      146.85 / (645.6 x 5.25) = 146.85 / 3,389 = 0.043
```

**3c. The top plate bears END-ON on the chord.** A tension bay pulls its chord inward along the
whole band, and the chord bears on the panel's double top plate end. The plate is still the
band's bottom chord without a moment connection, in either direction. It is graded at the whole
deck shear as before, which overstates the band push (519.18 lb) on purpose:

```
area   2 plies x 3.5" x 1.5" = 10.50 in2
f      1,038.35 / 10.50 = 98.89 psi
Fc-perp, Table 4D SP No. 2 timbers 375 x wet C_M 0.67 = 251.25 psi      0.394
```

**3d. The base plate and sill bear on the far chord** the same way: 3.5 x 1.5 = 5.25 plus the
2x8 `BM-BW-SCSILL` 1.5 x 7.25 = 10.875, total 16.125 in2 → 64.39 psi, **0.256**.

**3e. The eave collector.** The deck's boundary nailing lands on the trusses and the eave
blocking; an H2.5ASS carries ~110 lb of lateral, so three heel ties are nowhere near it. Six
LTP4, two per bay, blocking to glulam top, C-C-2019 p. 280 SPF/HF (the lower direction):

**Attachment completed 2026-10-06, revised the same day; re-stocked 2026-10-08.** Each eave
has three solid **2-ply SPF 2x10** blocks (3.0in x 9.25in), laminated with 8d common HDG, two
near each end and 12in o.c., the way the joint nailers are. They seat directly on their header,
run between truss faces, and have a bevelled top touching the roof deck. Each block is flush
with its header's **inboard** face: the west blocks' east faces align with the glulam's east
face and with every LTP4Z upper nailing half; the east blocks' west faces with BM-BW-RE's
west face. Since both roofs went to **standard-heel** trusses (2026-10-08, the top chord
springing straight off the 3.5in bottom chord, 5.75in lower than the old 9.25in energy heel)
the roof plane is 7.0in above the header at its centre, 7.92in at the blocks' inboard faces
and 6.92in at their outboard faces; the 9.25in blank takes that bevel. Under the old heel it
was 12.75in and 13-2/3in, which no 2x12 or 2x14 reached, and that was the only reason these
were 3-1/2x16 LSL. The last block runs to the garage gable's south face and is the south
nailer for the end strap on its line (diaphragm note §3b), whose centre it carries 1-1/4in
inboard of the header centreline: a 3in block flush with the inboard face of a 5-1/2in
glulam centres (5.5 − 3.0) / 2 in from its centreline. Two plies, not one, because that
strap nails two hole lines into the block, which needs the 3in width. SPF nails at a lateral
G of 0.42. The recipe is `RF-BW-CANOPY.diaphragm` in
`plan/storeys/garage.py` and follows the final framing.

**Fastening.** Each LTP4Z receives **12 0.131in x 1.5in HDG nails**, six into the block and
six into the glulam, directly to wood; no intervening sheathing and no reduction for it.
ZMAX with HDG nails because the glulam is treated (IRC R317.3.1); Simpson publishes no
stainless LTP4, so the house's stainless rule yields at these seven plates.
One LS30Z at each block end, six 0.148in x 1.5in HDG nails per angle (three per leg),
attaches side-grain faces to the adjacent truss on clear chord or heel wood, never through a
truss plate. Its 3-3/8in height fits a 2x4 top chord; the fully nailed deck restrains
rotation (C-C-2026 p.313). Do not load before that deck nailing is complete. The deck gets
8d common HDG at 6in boundary spacing. The canopy's panel edges, the ridge included, are
backed by bevelled SPF 2x4 on-edge blocks with three 8d HDG toenails each end. The 3ft 9in
horizontal sheet grid and the remaining blocks are detailed in diaphragm note §3b.

The collector prerequisite reads the actual bevel at each plate, not its bounding-box top.
All six plates, and §6's `CN-BW-EAVE-E`, have both wood faces. End angles, nails and cut stock appear in takeoff.
See [Simpson's LTP4 installation](https://www.strongtie.com/resources/product-installers-guide/ltp4-ltp5-installation)
and C-C-2026 pp.309-310 for direct-to-wood fastening.

```
1,038.35 / 6 = 173.1 lb vs 450      0.385
```

The deck's own boundary row is the diaphragm note's §4d, 1,038.35 / 6.000 = 173.1 plf vs 190,
**0.911** — along the full 6' eave, because the header is the collector; the panel's 5.44' is
no longer the boundary length.

**3f. The verticals take what lands on them.** Five slats land on each side of the centre post
(j = 0 … 4) and five on each chord (j = −4 … 0), each delivering h = 103.84 lb horizontally. That
is applied as a uniform load over H. **On the centre post both bays push the SAME way**, whatever
the push: the tension bay pulls it toward its own chord and the compression bay shoves it the
same way. So it takes both:

```
F      2 x 5 x 103.84 = 1,038.35 lb over 2.09375'
M      1,038.35 x 2.09375 / 8 = 271.76 lb-ft;  6x6 S 27.729 in3 -> f_b 117.61 psi
Fb'    Table 4D SP No. 2 timbers 850 x wet C_M 1.0 x C_D 1.6 = 1,360 psi              0.086
ends   1,038.35 / 2 = 519.18 lb at each plate: two A35Z per end (one each face), the lower
       ESR-3096 Table 5 row F1 695 lb     519.18 / (2 x 695) = 0.374
```

The vertical components on the centre post cancel: the tension bay pulls it down and the
compression bay pushes it up by the same 5 x 103.84.

A **chord** takes only its own bay, 5 x 103.84 = **519.18 lb**. A tension bay pulls it inward
onto the plate ends (§3c). A compression bay pushes it OUTWARD, off the plates, so it spans base
to head. §5b carries that.

**3g. The plates are screwed, and the tension bay is a withdrawal.** The top plate takes V from
the glulam soffit, and the sill hands V to the panel's top plate. The tension bay's four
top-landing slats (j = −4 … −1) pull the top plate DOWN by 4 x 103.84 = 415.34 lb over their
half, and its four sill landings pull the sill UP by the same. Eight SDWS22400DB per plate: up
through the 2x6 into the glulam, and down through the 2x6 into the double top plate. Each is
1-1/2" side member, 2-1/2" into the main, all 2.375" of thread in it. IAPMO UES ER-192: Table 5
DF/SP Z 405 lbf at a 1.5" side member, Table 7 W 179 lbf/in x 2.375 = 425.1, capped at W_max 425.
Both are DF/SP main-member rows (glulam DF 0.50, KDAT SP 0.55). Screws go square into side grain
(fn. 3), C_D 1.6, dry service:

```
lateral     1,038.35 / 8 = 129.79 lb       withdrawal  415.34 / 4 = 103.84 lb (that half's four)
resultant   166.22 lb at alpha = atan(103.84 / 129.79) = 38.66°
NDS §12.4.1 Z'a = W'p Z' / (W'p cos² a + Z' sin² a),  W'p = 425 x 1.6 = 680,  Z' = 405 x 1.6 = 648
            Z'a = 680 x 648 / (680 x 0.6098 + 648 x 0.3902) = 660.1 lb            0.252
```

**3h. The header couple.** The two bays' top landings push the glulam opposite ways, 415.34 lb
each. Their landings stand u = 7.779, 12.022, 16.265, 20.507" from each chord face, centroid
14.143", so 24.375 + 2.75 − 14.143 = 12.982" each side of the centre:

```
couple  415.34 x 2 x 12.982 / 12 = 898.7 lb-ft    / 4.9792' chords = 180.5 lb at a head
vs the deck's own couple through the header depth, 1,038.35 x 0.98958 / 4.9792 = 206.4 lb
```

Both have one sense, so the head row takes the LARGER, **206.4**, and none of either's favourable
half. The straps used to press the header DOWN by 948 lb, and that was never credited. The slats
lift one half and press the other, so there is nothing to credit now either. §5b's 635.3 stands.

## 4. The panel, re-read

**4a. SDPWS-2015 Table 4.3A**, wood structural panels — sheathing, 15/32" with 8d. v_w nominal
by edge spacing 6" / 4" / 3" / 2" is 365 / 530 / 685 / 895 plf; ASD is half. The 182.5 plf the
panel carried is the 6" row and was right as a read. What was wrong was the LENGTH: the wall's
node run, 6.573', oversails both chords, and nothing holds the oversail down. Over the chords'
out-to-out:

```
6" edges   1,038.35 / 5.4375 = 191.0 plf vs 182.5     1.046   OVER
4" edges   191.0 vs 530 / 2 = 265.0                   0.721   <- authored
aspect     4.0833 / 5.4375 = 0.751 vs 3.5             0.215
```

`G_a` stays at the 6" plywood row's 11.0 kips/in, the softer end. `chord_member` is now the
6x6 the chords are (`chord_refs` names them), not a 2-ply 2x4.

**4b. The chords' hold-down, full height.** The couple the chords take is the deck's shear over
the whole frame, header top to the chord bases:

```
H = 7.3333 − (−1.2917) = 8.625'
T = 1,038.35 x 8.625 / 4.9792 = 1,798.6 lb
  + the column's net roof uplift, 40 ft2 x (16.7232 − 0.6 x 10) = 428.9 lb
  = 2,227.6 lb vs CBSQ66-SDS2 cracked 3,060 (ESR-3050 Table 1)       0.728
```

The cracked value is graded. The wet-service reduction ESR-3050 §4.1 names does not move it:
the cracked column is the concrete's (uncracked is 4,375), and 0.7 x 4,375 = 3,062 is above it.

**4c. The base shear, on ONE base** (the ⚠ above), F2 along the screen (`Connector.axis = "y"`):

```
1,038.35 / 1,270 = 0.818        (F1 485 would read 2.14 — the axis matters)
```

It is the COMPRESSION chord, so no uplift combines with it.

## 5. Heads and bases, all four posts

**5a. Parts.** The glulam ENDS on each south post and runs on past each north one: an ACE6Z at
`PT-BW-CW`/`-RE`, an AC6Z at `-CNW`/`-RNE` (ESR-2604 §3.1.3; ACE6 MAX 1,950 / 1,760, AC6 MAX
2,815 / 2,075 lb, lateral PARALLEL to the beam only, fn. 6). Across the beam, an A35Z on each post
face with the soffit over it (ESR-3096 Table 5, F1 695 / F2 845, the lower taken): one at an end
post, two at a through post. Bases: CBSQ66-SDS2, F2 along y. The plan's "2,920 / 2,125" for the
AC6 was not in the report; ESR-2604 Table 3 prints 2,815 / 2,075.

**5b. Demands.** Own drag, 16.7232 psf on 5.5", half at each end:

```
west   16.7232 x 0.4583 x 7.6354 / 2 = 29.26 lb        east  ... x 6.1771 / 2 = 23.67 lb
```

The west posts also take the screen's out-of-plane E-W load at the top plate: the panel spans
sill to plate and the band plate to header, so the plate line carries half of each,

```
w = 16.7232 x (4.0833/2 + 2.34375/2) = 53.74 plf,  P = 53.74 x 4.5208 / 2 = 121.48 lb per post
a = 4.0000 + 1.2917 = 5.2917' above the base,  b = 7.6354 − 5.2917 = 2.3437'
head across = 29.26 + 121.48 x 5.2917 / 7.6354 = 113.45 lb
base across = 29.26 + 121.48 x 2.3437 / 7.6354 =  66.55 lb
```

— on the full solid face; the slats are ~50% open, so this is the conservative end. `P` reaches
each post through an A35Z at the plate end (`CN-BW-PLATE-*`): 121.48 / 695 = **0.175**.

Head uplift is the net roof uplift, 428.9 lb. On a chord, add the band's couple: the larger of
the deck's shear acting a header depth above the top plate, 1,038.35 x 0.98958 / 4.9792 = 206.4,
and the slats' own couple on the glulam (§3h), 180.5. That gives **635.3 lb**, with nothing
favourable credited.

**The band push, N-S, on a chord only.** §3f: the compression bay pushes its chord OUTWARD with
519.18 lb, off the plate ends, so the post spans base to head under it. Its resultant stands at
mid-band, +4.1250 + 2.09375/2 = +5.1719':

```
a = 5.1719 + 1.2917 = 6.4636' above the base,  b = 7.6354 − 6.4636 = 1.1718'
head along = 29.26 + 519.18 x 6.4636 / 7.6354 = 29.26 + 439.50 = 468.76 lb
base along = 29.26 + 519.18 x 1.1718 / 7.6354 = 29.26 +  79.68 = 108.94 lb
M          = 519.18 x 6.4636 x 1.1718 / 7.6354 = 515.00 lb-ft   (a point load: the conservative end)
```

It is the N-S wind, so it meets the head uplift above (the same case's couple) and not the
E-W plate load. A tension bay pulls the chord inward onto the plates instead, a 2.09' span and
a quarter of the moment.

**5c. Rows (linear interaction where two directions meet one part).**

| post | cap | uplift + along | A35 across | base, across (uplift + F1) | base, along (+ F2) |
|---|---|---|---|---|---|
| CW | ACE6Z | 635.3/1,950 + 468.76/1,760 = **0.592** | 113.45/695 = 0.163 | 428.9/3,060 + 66.55/485 = 0.277 | + 108.94/1,270 = 0.226 |
| CNW | AC6Z | 635.3/2,815 + 468.76/2,075 = 0.452 | 56.73/695 = 0.082 | 0.277 | 0.226 |
| RE | ACE6Z | 428.9/1,950 + 23.67/1,760 = 0.233 | 23.67/695 = 0.034 | 428.9/3,060 + 23.67/485 = 0.189 | 0.159 |
| RNE | AC6Z | 428.9/2,815 + 23.67/2,075 = 0.164 | 0.017 | 0.189 | 0.159 |

The column on the west post, the diaphragm note's §5a arithmetic on the longer post:

```
axial    40 x (10 + 73.7) + 7.87 x 7.6354 = 3,408 lb;  f_c = 3,408 / 30.25 = 112.7 psi
         l/d 91.625 / 5.5 = 16.66;  FcE = 0.822 x 440,000 / 16.66² = 1,303 psi;  C_P 0.879
         Fc' = 525 x 1.15 x 0.879 = 530.9 psi                                       0.212
moment   16.7232 x 0.4583 x 7.6354² / 8 + 121.48 x 5.2917 x 2.3437 / 7.6354
         = 55.9 + 197.3 = 253.2 lb-ft;  f_b = 253.2 x 12 / 27.73 = 109.6 psi
§3.9     (112.7 / 530.9 + 109.6 / 1,360) / (1 − 112.7 / 1,303) = 0.2928 / 0.9135      0.321
```

On a chord, the N-S case is larger, and it governs:

```
moment   55.9 + 515.00 = 570.86 lb-ft;  f_b = 570.86 x 12 / 27.73 = 247.0 psi
§3.9     (112.7 / 530.9 + 247.0 / 1,360) / 0.9135 = 0.3939 / 0.9135                   0.431
```

**5d. Dry service at the connectors, wet in the column.** ESR-2604 §3.2.2 and ESR-3050 §4.1 rate
the parts at MC ≤ 19%. The posts are KDAT on 1" drained standoffs under the roof, and the record
prints the condition, exactly as the CCQ it replaced did. The column is graded on Table 4D's wet
row.

**5e. The piers are 14" round under a CBSQ.** ESR-3050 Table 1 fn. 4 wants 3" of side cover. The
straps' outer faces stand 2.75 + 0.135 = 2.885" off the axis, 1.5" either side of centre:

```
12" round   corner radius sqrt(2.885² + 1.5²) = 3.252"   cover 6 − 3.252 = 2.75"   short
14" round                                                   cover 7 − 3.252 = 3.75"   OK
```

The same 8" cage fits a 14" at 3" of cover; turn it so its four #5s sit on the diagonals, where a
bar at (2.34", 2.34") clears the strap zone (|y| ≤ 1.5") by 0.53". The west piers' seat beams gain
an inch of bearing (3 1/4" → 4 1/4"). `deck_post` then reads ACI 318-19 §10.6.1.1's 1% floor on
§10.3.1.2's reduced effective area — half the 153.9 in2 gross, 0.770 in2 against (4) #5's 1.24 —
because each column is at a strength ratio under 0.04 and far larger than its load needs.

## 6. The open front: chord, couple, drift

The E-W case, `kdat`: the slope band 26.667 sf plus both headers 2 x 0.98958 x 5.9479 = 11.772 sf
at 16.7232 psf = 642.82 lb, plus 2 x 23.67 = **690.16 lb**. Its resultant (the diaphragm note's
§3b arithmetic on these bands) stands at y 40.2030, 3.0157' off the joint at 43.2188:

```
M = 690.16 x 3.0157 = 2,081.3 lb-ft
chord force  M / W' = 2,081.3 / 24.000 = 86.7 lb in each header
  glulam, Table 5A 24F-V4 Ft 1,100 x wet 0.80 x C_D 1.6 = 1,408 psi; 86.7 / 65.3 in2 = 1.33 psi   0.001
  end strap (LSTA24): 86.7 + 1,038.4 / 6 = 259.8 lb vs 823.33 (12/18 nails)                 0.316
  chord into the end strap's 2-2x10 block: header and block are two pieces, so a plate joins them
    west, CN-BW-EAVE-5/-6 share it, each also carrying its §3e collector share:
      86.7 / 2 + 173.1 = 216.4 lb vs LTP4Z 450 (SPF/HF, lower direction)                   0.481
    east, CN-BW-EAVE-E alone (the east header is no collector): 86.7 lb vs 450             0.193
the couple into RF-GARAGE: M / 24.000' = 86.7 lb on each of W-G-W and W-G-E, E-W case
  W-G-W  86.7 / 18.675' = 4.64 plf vs 182.5  0.025      W-G-E  86.7 / 21.008' = 4.13 plf  0.023
```

The diaphragm note's §3f said the joint "closes" the couple. It hands it on; the rows above are
where it goes. **SDPWS 4.2.5.2's drift limit** is ASCE 7's story drift under SEISMIC forces
including torsion. The jurisdiction profile puts this site in SDC A, which ASCE 7-16 §11.7
designs to §1.4 alone: NOT APPLICABLE, earned. Any other category and the record is INCOMPLETE.

## 7. The headers, 5-1/2" x 11-7/8" glulam (`roof_beam`)

24F-V4 DF (a 5-1/2" width is Western species), wet, snow C_D 1.15. Half the roof, 80 ft2, over
the header's 5.9479', on posts 4.9792' apart with 0.2292' and 0.7396' past them:

```
w = 80 / 5.9479 x (73.7 + 10) = 1,125.8 plf       (snow 991.3, dead 134.5)
R (north post, all loaded) = 1,125.8 x 16.328 / 4.9792 = 3,692 lb (+5 for the pattern) = 3,697 lb
bearing on the 5.5" post end  3,697 / 30.25 = 122.2 psi vs 650 x 0.53 = 344.5        0.355
M ~ 3,469 lb-ft,  S 129.3 in3 -> 322 psi vs 2,400 x 0.80 x 1.15 x C_V 1.0 = 2,208   0.146
```

C_V (x = 10) is (21/4.979)^0.1 (12/11.875)^0.1 (5.125/5.5)^0.1 = 1.148, capped at 1.0. Bearing
governs at 0.355; the 3-ply 2x12 read 0.71 in bending.

## 8. Alternatives, and why each is not the choice

* **The CS16 X-straps — built until 2026-10-04, the first backup.** A CS16 X on each face, flush
  with the 6x6 and glulam faces, from 1/2" inside the far post's outer face (1" over the panel
  top) to 1" under the header top, 9 1/2" past midspan: θ = atan(3.1667 / 3.4688) = 42.39°.
  It was that steep so six 10d x 2-1/2 HDG fit on the 5.5" post face, a 6.77" crossing; at θ ≈ 26°
  over the posts it was five, and five does not carry the strap. T = 1,038.35 / 0.73855 / 2 =
  703.0 lb per strap against min(1,705 steel; 6 x 189.0 = 1,134), ESR-2105 Table 4 pro-rated,
  **0.620**. Its V tan θ = 948 lb pressed the header DOWN. It loads no post sideways, it is fewer
  parts, and it is the stronger review position. The slats replaced it on looks: the X was the
  only steel on the elevation.
* **Sheathed piers and a slat opening — the second backup.** Sheath full height, deck to header,
  beside each chord, with vertical slats between. The chord bases hold down the OUTER ends only;
  each pier's inner end needs its own hold-down. Full-height piers stand 6.34375 + 0.0833 =
  6.427' tall, so 3.5:1 wants b ≥ 1.836' each, leaving ~1.8' of opening (4.5' today). Then
  v = 1,038.35 / (2 x 1.836) = 282.8 plf against the SDPWS §4.3.4.2 reduction 1.25 − 0.125 x 3.5
  = 0.8125: 3" edges 342.5 x 0.8125 = 278.3, **1.016**; 2" edges 447.5 x 0.8125 = 363.6,
  0.778. Each inner end lifts 519.18 x (7.3333 + 0.0833) / 1.836 = **2,097 lb** into the deck
  framing, with no pier under it. Sheathing only the band's two ends over the full-length panel is
  an FTAO wall whose opening reaches the header. SDPWS §4.3.5.2 wants sheathing above and below
  the opening, and there is none above.
* **Butted slats screwed, no connector.** ER-192 rates an SDWS only "straight into the side grain
  of the wood main member with the screw axis at a 90-degree angle to the wood fibers" (Table 5
  fn. 3), and NDS §12.2 forbids end-grain withdrawal. A 45° butt has neither, so a slat would be
  compression-only.
* **Compression-only slats (the chevron without KBS1Z).** One bay carries a whole push, so its
  slats double to 293.7 lb. Worse, a compression field pushes the header UP by
  V (1 + H/W) ≈ 2,100 lb over one half: PT-BW-CW's head would carry ~2,100 + 429 lb against the
  ACE6Z's 1,950. The chords would also take ~1,038 lb sideways in the band, the post bending §2
  removed. The KBS1Z's rated tension is what lets the bays share and the vertical pushes cancel.
* **Diagonal slats as SDPWS diagonal lumber sheathing** (IRC Method DWB). Gapped boards and no
  studs to lap are outside both rows. §3 does not claim it: each slat is graded as a knee brace on
  its own connector.
* **`PLATE-TOP-0-1` as a moment cross-beam** (a portal). The posts become bending members in
  the frame, and no published moment rating exists for the angles or caps it would lean on.
* **Horizontal slats.** SDPWS's horizontal-lumber row is ~50 plf nominal; gapped boards are
  outside it, and the demand is 191.
* **A heavier panel alone** closes §4a and not §2: the band is still unbridged.
* **TWB12.** A let-in brace for kerfed studs, and the band has none; no tension row fits here.
* **A 12" pier under the CBSQ** — §5e, 1/4" short of the side cover.

## 9. What is NOT graded here

* The truss end chords (N-S) and their splice slip — the truss order (`rafter/RF-BW-CANOPY`).
* The slats' own out-of-plane span (IRC R301.5 fn. f, in-fill; `SC-BW-WEST`'s note).
* Nail withdrawal at the LTP4s under the deck's own uplift — the heel ties carry that.

## Sources

- AWC SDPWS-2015 Table 4.3A, §4.2.5.2, §4.3.4.
- IAPMO UES ER-280 rev. 04/28/2026 Table 7 (KBS1Z), fn. 1-3; IAPMO UES ER-192 rev. 09/08/2026
  Tables 5 and 7 (SDWS22400DB) and fn. 3; both read 2026-10-04. AWC NDS 2018 Supplement Table 4B
  (SP No. 2 2x4); NDS §12.4.1.
- ICC-ES ESR-2105 Table 4 (CS16, §8), Table 3 (LSTA24); ICC-ES ESR-2604 §3.1.3 and Table 3 (AC/ACE);
  ICC-ES ESR-3096 Table 5 (A35); ICC-ES ESR-3050 Table 1, §4.1, fn. 4 (CBSQ); all read 2026-09-30.
- Simpson Strong-Tie C-C-2024, CBSQ lateral F1 485 / F2 1,270; C-C-2019 p. 280 (LTP4).
- AWC NDS 2018 Supplement Tables 4D and 5A; NDS Tables 4.3.8, 5.3.1, §3.9, §3.10, §5.3.6.
- ACI 318-19 §10.3.1.2, §10.6.1.1. ASCE 7-16 §11.7.

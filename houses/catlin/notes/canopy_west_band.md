> **2026-10-26 east-tail amendment:** BM-BW-RE now matches the west's equal 8⅞″
> tails, with paired AC6Z at RE and unchanged roof-bearing datum. Joint couple
> 2,132.02 lb-ft, chord 88.834 lb, end straps 261.893 lb, west/east collector plates
> 217.475/88.834 lb. East south cap combined ratio 0.164. The 2026-10-14 numbers
> below are historical. Hood/apron geometry and open release items:
> [canopy_beam_tail_hoods.md](canopy_beam_tail_hoods.md).

# The canopy's west band, its heads and bases, and the open front — hand-worked basis

**House:** catlin
**Structure:** `RF-BW-CANOPY`'s west line — `W-BW-SCREEN`, the band over it (`SB-BW-BAND`),
the chords `PT-BW-CW`/`-CNW`, the glulam headers `BM-BW-RW`/`-RE`; the heads and bases of all
four posts (`PT-BW-CW`/`-CNW`/`-RE`/`-RNE`, `kdat`); the open front's chord and couple.
**Written:** 2026-09-30, by hand, before `engineering/lateral_band.py`, `open_front.py`,
`roof_beam_glulam.py` and `wood_roof_post_joints.py` were encoded. §3 and §5b-c re-worked
2026-10-04 for the slat band, before `lateral_band_slats.py`; the straps it replaced are in §8.
Re-worked again 2026-10-08 at a 2-1/4" slat gap (§3a: the KBS1Z overlapped at 1-1/2"), and
2026-10-09 with the two corner slats (j = 0) as screwed infill, not braces (§3a-ter).
Re-worked 2026-10-25: one 4x6 per bay, offset −6½″, two KBS1Z per end; §5b-c use the
actual chord landing. Re-worked 2026-10-26: §3 now uses one 6x6 per bay, exactly corner to
corner, on the standard open knee. The 4x6 and the former chevron are backups in §8.
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

### 2026-10-26 §3 re-work — corner-to-corner 6x6 adopted

**3a. Geometry and buildable connections (`SB-BW-BAND`).** The same 2x6 flat sill and top
plate and 6x6 centre post leave two bays W = 24.375″, H = 25.125″. Each has ONE 6x6
SP No. 2 knee brace running exactly corner to corner, chord to top plate, mirrored to rise
inward. It is 5½″ in elevation and 5½″ through, equal-width with the 5½″-deep frame, so
both faces are flush and take ER-280 Table 7 type 1, two KBS1Z per end.

The 5½″ face is what makes the corner work in the **standard open knee** (C-C-2026 p.325,
ER-280 Figure 7). The clipped end leaves the post and plate at the heels below; each
support leg runs from its heel back toward the corner, so each heel must stand at least the
3″ leg from it. A 3½″ face puts them at 2.513″/2.438″ and fails; the resolver refuses it.

```
θ = atan(25.125/24.375) = 45.868051°; cos θ = 0.696313, sin θ = 0.717738
length = hypot(24.375, 25.125) = 35.0058″
post heel  = 2.75 / cos θ = 3.94937″ up the chord post   margin 0.949″ over 3″
plate heel = 2.75 / sin θ = 3.83148″ along the top plate margin 0.831″ over 3″
included angle, chord: 90 + θ = 135.868°; top: 180 − θ = 134.132°
```

Both are one field bend from the factory 45° (135°): the catalog's one adjustment. The
return flanges lie on the post's and plate's inner faces, clear of the sill and the centre
post by the margins above. Two 6x6 blanks about 35″ long; eight KBS1Z, twelve
0.131 × 2½″ HDG nails each. Specify treated SP No. 2 or better 6x6, KDAT (or dried to
MC ≤19% before the connectors go on).

**3b. Brace force, type-1 row, buckling, bearing.** Mirrored bays with the same joints
share V equally, one in tension and one in compression. Each brace crosses mid-band:

```
V = 1,038.3506 lb; h = V/2 = 519.1753 lb
v = h tan θ = 519.1753 × 25.125/24.375 = 535.1499 lb
P = h / cos θ = 745.6061 lb
```

ER-280 Table 7 type 1 is the equal-width, **two KBS1Z each end** joint: SPF/HF **1,010 lb**
at 45° and **720 lb** at 30°/60°, MC ≤19%, C_D 1.6 included, for the pair. Footnote 3
permits interpolation by brace angle:

```
F1 = 1,010 − (1,010 − 720) × 0.868051/15 = 993.2177 lb
ratio = 745.6061 / 993.2177 = 0.751          (do not double it again)
```

Buckling, NDS §3.7, SP No. 2 6x6 on [Table 4D](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-Supplement_20200827_AWCWebsite_Chapter4.pdf)'s
timbers **wet row**: Fc 525 psi, E_min 440,000 psi, no further C_M; wind C_D 1.6:

```
Fc* = 525 × 1.6 = 840 psi; l/d = 35.0058/5.5 = 6.3647
FcE = 0.822 × 440,000 / 6.3647² = 8,928.3 psi; r = 10.629
CP = (1+r)/1.6 − √(((1+r)/1.6)² − r/0.8) = 0.98010
capacity = 840 × 0.98010 × 30.25 = 24,904 lb; ratio = 745.606/24,904 = 0.030
```

Clipped-end bearing. The compression brace bears on BOTH members it is cut against,
whichever carries the KBS1Z. Envelope: the whole h on the post face, the whole v on the
plate face, each 5½″ deep. Hankinson (NDS §3.10.3) on the brace's end grain,
Fc* 840 and Fc⊥ 375 × 0.67 = 251.25 psi; the member across its grain at the same 251.25
(Table 4D timbers, conservative for the 2x plate) governs:

```
post:  519.1753 / (3.94937 × 5.5 = 21.722 in²) = 23.90 psi; brace Fθ at 45.868° 380.6   0.095
plate: 535.1499 / (3.83148 × 5.5 = 21.073 in²) = 25.39 psi; brace Fθ at 44.132° 393.2   0.101
```

Why chord → top rather than sill → centre: it keeps the KBS1Z, and so the tension bay's
pull, on the chord and the header. Sill → centre would hang that pull on the centre post's
end ties.

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

**3f. Vertical equilibrium, chord push, the centre post.** Each chord takes h =
**519.175 lb** horizontally where the brace centreline meets it, at the sill top,
**+4.125′** (the lowest point of the 3.949″ contact, and the one nearest the chord's
midspan: the larger moment). The tension chord is pulled inward onto the plate ends; the
compression chord pushes outward and spans base to head (§5b). Vertical brace forces at
the two top landings are ±535.150 lb, equal and opposite.

The compression brace's top end also bears on the centre post, inside 3.949″ of the top
plate. Take the whole h there, at the contact centroid 1.975″ below the plate, on a pinned
25.125″ post:

```
a = 1.97468″ = 0.164557′, b = 2.09375 − 0.164557 = 1.929193′
M = 519.1753 × 0.164557 × 1.929193 / 2.09375 = 78.72 lb-ft
fb = 78.72 × 12 / 27.729 = 34.07 psi vs 850 × 1.6 = 1,360        0.025
top reaction = 519.1753 × 1.929193/2.09375 = 478.37 lb on 2 A35Z (695) = 1,390    0.344
```

Its bottom end likewise presses v down onto the sill: bearing on the panel's plate, no
screw withdrawal. The sill still hands the full shear to the panel.

**3g. Plate screws, NDS §12.4.1.** Eight SDWS22400DB per plate retain ER-192's dry-service
Z′ = 405 × 1.6 = 648 lb and W′p = 425 × 1.6 = 680 lb. The tension bay's four top screws
share its one 535.150 lb landing; the compression bay's end presses its plate up into the
header, bearing only:

```
lateral per screw = 1,038.3506/8 = 129.7938 lb
withdrawal at top = 535.1499/4 = 133.7875 lb
resultant = 186.4015 lb, α = atan(133.7875/129.7938) = 45.868°
Z′α = 680 × 648 / (680 cos²α + 648 sin²α) = 664.099 lb; ratio 0.281
sill: withdrawal zero, resultant 129.7938 lb, α = 0°, capacity 648 lb; ratio 0.200
```

**3h. Header couple.** Each top landing is the top/centre corner, 2.75″ from the band's
centre:

```
C = 535.1499 × 2 × 2.75/12 = 245.277 lb-ft
head couple = 245.277/4.979167 = 49.26 lb
header-depth couple = 1,038.3506 × 0.989583/4.979167 = 206.367 lb
```

The larger remains 206.367 lb. Head uplift remains 428.928 + 206.367 = **635.295 lb**,
with no favourable vertical component credited.

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

The 2026-10-25 face-membrane removal does not change this demand: no screen-wall dead
weight is credited against uplift. At the current resolved collector/base elevations,
the engine gives 2,226.5 / 3,060 lb (0.728); the rounded hand-work above retains 8.625' height.

The cracked value is graded. The wet-service reduction ESR-3050 §4.1 names does not move it:
the cracked column is the concrete's (uncracked is 4,375), and 0.7 x 4,375 = 3,062 is above it.

**4c. The base shear, on ONE base** (the ⚠ above), F2 along the screen (`Connector.axis = "y"`):

```
1,038.35 / 1,270 = 0.818        (F1 485 would read 2.14 — the axis matters)
```

It is the COMPRESSION chord, so no uplift combines with it.

## 5. Heads and bases, all four posts

**5a. Parts (west revised 2026-10-14).** The west glulam runs past both posts with equal
8⅞″ tails from their centres: AC6Z at `PT-BW-CW` and `-CNW`. The east header ends on its
south post: ACE6Z at `PT-BW-RE`, AC6Z at `-RNE` (ESR-2604 §3.1.3; ACE6 MAX 1,950 / 1,760, AC6 MAX
2,815 / 2,075 lb, lateral PARALLEL to the beam only, fn. 6). Across the beam, an A35Z on each post
face with the soffit over it (ESR-3096 Table 5, F1 695 / F2 845, the lower taken): one at each south
post, two at each north post (the west-tail extension retains this rated schedule). Bases: CBSQ66-SDS2, F2 along y. The plan's "2,920 / 2,125" for the
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
and the slats' own couple on the glulam (§3h), 49.3. That gives **635.3 lb**, with nothing
favourable credited.

**The band push, N-S, on a chord only (2026-10-26).** At the actual composite-stock base
−15.44″, L = 91.565/12 = 7.630417′. Its 519.1753 lb point load stands at the sill top,
+4.125′ (§3f):

```
a = 4.125 + 15.44/12 = 5.411667′; b = L − a = 2.218750′
own drag at each end = 16.7232 × (5.5/12) × L/2 = 29.243 lb
head along = 29.243 + 519.1753 × a/L = 397.454 lb
base along = 29.243 + 519.1753 × b/L = 180.207 lb
brace moment = 519.1753 × a × b/L = 816.97 lb-ft
own drag moment = 16.7232 × (5.5/12) × L²/8 = 55.784 lb-ft
N-S moment = 872.75 lb-ft, fb = 872.75 × 12 / (5.5³/6) = 377.69 psi
```

**5c. Current rows (linear interaction).** Across-beam rows remain the §5b plate calculation;
with actual stock they are head 113.341 lb, base 66.527 lb, plate 121.382 lb. The west heads
carry 635.295 lb uplift and the bases 428.928 lb. Each west post therefore reads:

| row | working | ratio |
|---|---|---|
| AC6Z uplift + along | 635.295/2815 + 397.454/2075 | **0.417** |
| A35Z head across, CW / CNW | 113.341/695 / half that | 0.163 / 0.082 |
| A35Z panel plate | 121.382/695 | 0.175 |
| CBSQ base uplift + across | 428.928/3060 + 66.527/485 | 0.277 |
| CBSQ base uplift + along | 428.928/3060 + 180.207/1270 | **0.282** |

NDS column: axial 3,408.04 lb / 30.25 = 112.66 psi; l/d = 91.565/5.5 = 16.6482;
FcE = 0.822 × 440,000 / 16.6482² = 1304.93 psi; Fc′ = 530.917 psi.
The combined screen is (112.66/530.917 + 377.69/1360) / (1 − 112.66/1304.93)
= **0.536**, governed by the N-S push rather than the E-W plate load. East post rows remain
RE 0.233 at ACE6Z, 0.189 base across, 0.225 column; RNE 0.164 at AC6Z, 0.159 base along.

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

### 2026-10-14 west-tail amendment to §§6–7

The east-header arithmetic above remains current; the west header is now 77½″ long with
8⅞″ tails from both post centres, a 6⅛″ south extension. The roof-bearing run excludes that
extension, so the canopy deck, all three trusses and the roof's 80 sf per header stay fixed.
The tail projects 5½″ beyond the deck edge and stops 1⅞″ short of the modeled house cladding.
Use paired AC6Z at CW, MAX 14 × 16d into each member per assembly, rather than the ACE's
10 + 10 schedule. Other head/base hardware stays as detailed.

The gravity calculation excludes the unloaded extension: the 80 sf remains distributed over
its original 5.9479′ roof-bearing run, so `w = 80 / 5.9479 × 83.7 = 1125.8 plf`. The loaded
south tail remains 2¾″, even though the physical tail is 8⅞″. Extending the physical beam
must not dilute the line load. Both headers retain **0.355 bearing / 0.146 bending** under
the existing distributed roof-load model. This is not a discrete truss-reaction analysis.

The extra exposed header side adds `6.125/12 × 11.875/12 × 16.7232 = 8.447 lb` to the E-W
case. The frame/diaphragm load distribution recalculates the joint couple as
**2,106.7 lb-ft**, delivered E-W
shear **698.61 lb**, and chord force **87.78 lb**. The end-strap combined demand is
`87.78 + 1038.35/6 = 260.84 lb`; west collector plates each take `87.78/2 + 173.06 = 216.95 lb`,
the east plate 87.78 lb; all remain below their existing capacities. The west head ratio
then improved to **0.399** (before the 2026-10-25 brace re-work); all four post records and the canopy lateral record remain OK.

## 8. Alternatives, and why each is not the choice


* **One 4x6 per bay at c = −6½″ — superseded 2026-10-26, retained backup.** 3½″ in
  elevation, 5½″ through, chord → top, two KBS1Z type 1 each end at 45°. Each heel needs
  3.5/√2 + 3 = 5.47487″ along its face: chord margin 1.025″, top margin 0.275″, so
  c ≤ −6.22487″. Length 26.340″ (blank 28.815″). P = 734.2248 lb vs 1,010, **0.727**;
  Table 4B 2"-4" thick, 5"-6" wide row (Fc 1,400 × 0.8, E_min 510,000 × 0.9), l/d 7.5257,
  buckling 32,318 lb (0.023). Push 519.175 lb at +4.666667′; top screws 183.556/663.614
  (0.277), sill 0.200; header couple 735.498 lb-ft (147.7 lb a head); no brace on the
  centre post or sill. Chord rows at that push: AC6Z 0.435, CBSQ along 0.253, column 0.488.
  It was replaced on looks: the diagonal stops short of both corners. A true corner with a
  3½″ face would need an acute inside fold no catalog row covers.
* **The fourteen-slat chevron — superseded 2026-10-25, retained backup.** 2x4 at 2¼″ clear,
  west face flush, c_j = −0.375 + 5.3033j″, j = −3…3. j = 0 is screwed infill; the other
  six slats per bay take 24 KBS1Z type 2. Four braces cross mid-band: P = 183.56 lb,
  540 lb connector capacity (0.340), buckling 4,901 lb (0.037). Three chord and three
  centre landings each bay at h = 129.79 lb give chord push 389.38 lb and centre push
  778.75 lb. The top and sill screw resultants were 162.24 / 659.17 lb (0.246), header
  couple 842.5 lb-ft (169.2 lb/head). These historical ratios assume the former
  mid-band chord push; any restoration must use the actual chord-landing centroid.
  A corner needs 1.5/√2 + 3 = 4.06″ of bearing-face reach, so j = 0 remains unbraced.

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
  (SP No. 2 2x4 and 4x6) and Table 4D (SP No. 2 timbers, wet row: the 6x6 brace); NDS §3.7,
  §3.10.3, §12.4.1. Simpson C-C-2026 pp.324–325 (KBS1Z open knee, 1,010/720 lb SPF/HF).
- ICC-ES ESR-2105 Table 4 (CS16, §8), Table 3 (LSTA24); ICC-ES ESR-2604 §3.1.3 and Table 3 (AC/ACE);
  ICC-ES ESR-3096 Table 5 (A35); ICC-ES ESR-3050 Table 1, §4.1, fn. 4 (CBSQ); all read 2026-09-30.
- Simpson Strong-Tie C-C-2024, CBSQ lateral F1 485 / F2 1,270; C-C-2019 p. 280 (LTP4).
- AWC NDS 2018 Supplement Tables 4D and 5A; NDS Tables 4.3.8, 5.3.1, §3.9, §3.10, §5.3.6.
- ACI 318-19 §10.3.1.2, §10.6.1.1. ASCE 7-16 §11.7.


## 2026-10-15 actual composite thickness addendum

The library's Trex Enhance Basics is 0.94 inch actual instead of 1 inch. Holding the
entry walking surface at 0'-0 raises its supporting wood and pier/chord bases by 0.06 inch.
Reapply §4b to base -15.44 inch: H = (88 + 15.44)/12 = **8.620 ft** rather than 8.625.
The roof, header soffit and panel top stay fixed; the panel's bottom rises 0.005 ft.

For §5b's plate reaction, use panel height **4.078333 ft** (4.083333 - 0.005), band
2.34375 ft and the same 4.520833 ft clear span: P = 16.7232 ×
(4.078333/2 + 2.34375/2) × 4.520833/2 ≈ **121.38 lb** per chord.
At that revision, head uplift stayed **635.295 lb** and band push **389.381 lb**; the same rated hardware
and capacities pass. The tests use these actual-stock values; the earlier worked text
retains the nominal 1-inch board geometry for its dated derivation.

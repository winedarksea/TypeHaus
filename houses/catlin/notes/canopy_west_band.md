# The canopy's west band, its heads and bases, and the open front — hand-worked basis

**House:** catlin
**Structure:** `RF-BW-CANOPY`'s west line — `W-BW-SCREEN`, the band over it (`SB-BW-BAND-*`),
the chords `PT-BW-CW`/`-CNW`, the glulam headers `BM-BW-RW`/`-RE`; the heads and bases of all
four posts (`PT-BW-CW`/`-CNW`/`-RE`/`-RNE`, `kdat`); the open front's chord and couple.
**Written:** 2026-09-30, by hand, before `engineering/lateral_band.py`, `open_front.py`,
`roof_beam_glulam.py` and `wood_roof_post_joints.py` were encoded.
**Oracle for:** `lateral_band.py` (§3-§4), `wood_roof_post.py` / `wood_roof_post_joints.py` (§5),
`open_front.py` (§6), `roof_beam_glulam.py` (§7); reproduced by
`tests/test_canopy_west_band_calcs.py`.
**Companions:** `canopy_garage_diaphragm.md` — the delivery to the garage and the envelope this
note works inside; its §4f points here. `north_entry_canopy_lateral.md` §8c, corrected by §2.
**What is asked of the reviewer:** §3's strap end (six nails on a 6x6 face) and §4e's
full-height overturning at the chord bases — the two rows nearest their limits after the deck.

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

## 3. The band brace

**Demand.** N-S at the deck, `kdat`: the gable triangle 997.4 lb (§2 of the diaphragm note)
plus each east post's head half, 16.8315 x 5.5/12 x 6.1771 / 2 = 23.83 lb:

```
V = 997.4 + 2 x 23.83 = 1,045.06 lb        (100% on this line: the envelope)
```

**Geometry.** A CS16 X on EACH face of the frame, flush with the 6x6 and glulam faces, 1" off
the slats. Each strap runs from 1/2" inside its far post's outer face, 1" over the panel top,
to 1" under the header top, 9 1/2" past midspan (midspan y 39.9896):

```
D1  bottom (y 42.6667, z +4.0833)   top (y 39.1979, z +7.2500)
    run 3.4688'   rise 3.1667'   theta = atan(3.1667 / 3.4688) = 42.39°   cos 0.73855
```

D2 is its mirror. **Why so steep:** at the post end the strap crosses a 5.5" face for only
5.5/cos θ; CS16's two hole rows at 2 1/16" hold about one nail an inch; the far-face crossing
is (42.6667 − 42.2500)/0.73855 = 0.5642' = **6.77"**, which holds six nails with end margin. At
θ ≈ 26° over the posts it was five, and five does not carry the strap.

**Tension.** One strap per face is in tension for each push (the one whose top the deck carries
away from its bottom), so two share it:

```
T = V / cos θ / 2 = 1,045.06 / 0.73855 / 2 = 707.5 lb per strap
```

**Capacity, ESR-2105 Table 4.** CS16: 1,890 lb with 20 - 10d x 2-1/2 common, half each member,
so the row is 189.0 lb a nail at one end; steel 1,705 lb. Six at the post end:

```
min(1,705 ; 6 x 189.0 = 1,134) = 1,134 lb      707.5 / 1,134 = 0.624
```

The header end crosses 11.875" / sin θ = 17.6" of glulam face and takes the same six easily.
SG: KDAT SYP 0.55 and 24F-V4 DF 0.50, both at the row's 0.50. A pro-rated read of the row, not
the row: this is an engineered item, and it says so.

**Vertical component.** V tan θ = 1,045.06 x 0.91291 = 954.0 lb lifts the bottom-end chord at
+4'-1" and presses the header down near midspan. Internal to the frame; §4e carries it.

**3c. The top plate bears END-ON on the chord.** The deck's push arrives at the strap's bottom
end, on the chord; the chord bears on the double top plate's end, which is how the plate is the
band's bottom chord without a moment connection, and in either direction:

```
area   2 plies x 3.5" x 1.5" = 10.50 in2
f      1,045.06 / 10.50 = 99.53 psi
Fc-perp, Table 4D SP No. 2 timbers 375 x wet C_M 0.67 = 251.25 psi      0.396
```

**3d. The base plate and sill bear on the far chord** the same way: 3.5 x 1.5 = 5.25 plus the
2x8 `BM-BW-SCSILL` 1.5 x 7.25 = 10.875, total 16.125 in2 → 64.81 psi, **0.258**.

**3e. The eave collector.** The deck's boundary nailing lands on the trusses and the eave
blocking; an H2.5ASS carries ~110 lb of lateral, so three heel ties are nowhere near it. Six
LTP4, two per bay, blocking to glulam top, C-C-2019 p. 280 SPF/HF (the lower direction):

```
1,045.06 / 6 = 174.2 lb vs 450      0.387
```

The deck's own boundary row is the diaphragm note's §4d, 1,045.06 / 6.000 = 174.2 plf vs 190,
**0.917** — along the full 6' eave, because the header is the collector; the panel's 5.44' is
no longer the boundary length.

## 4. The panel, re-read

**4a. SDPWS-2015 Table 4.3A**, wood structural panels — sheathing, 15/32" with 8d. v_w nominal
by edge spacing 6" / 4" / 3" / 2" is 365 / 530 / 685 / 895 plf; ASD is half. The 182.5 plf the
panel carried is the 6" row and was right as a read. What was wrong was the LENGTH: the wall's
node run, 6.573', oversails both chords, and nothing holds the oversail down. Over the chords'
out-to-out:

```
6" edges   1,045.06 / 5.4375 = 192.2 plf vs 182.5     1.053   OVER
4" edges   192.2 vs 530 / 2 = 265.0                   0.725   <- authored
aspect     4.0833 / 5.4375 = 0.751 vs 3.5             0.215
```

`G_a` stays at the 6" plywood row's 11.0 kips/in, the softer end. `chord_member` is now the
6x6 the chords are (`chord_refs` names them), not a 2-ply 2x4.

**4b. The chords' hold-down, full height.** The couple the chords take is the deck's shear over
the whole frame, header top to the chord bases:

```
H = 7.3333 − (−1.2917) = 8.625'
T = 1,045.06 x 8.625 / 4.9792 = 1,810.3 lb
  + the column's net roof uplift, 40 ft2 x (16.8315 − 0.6 x 10) = 433.3 lb
  = 2,243.5 lb vs CBSQ66-SDS2 cracked 3,060 (ESR-3050 Table 1)       0.733
```

The cracked value is graded. The wet-service reduction ESR-3050 §4.1 names does not move it:
the cracked column is the concrete's (uncracked is 4,375), and 0.7 x 4,375 = 3,062 is above it.

**4c. The base shear, on ONE base** (the ⚠ above), F2 along the screen (`Connector.axis = "y"`):

```
1,045.06 / 1,270 = 0.823        (F1 485 would read 2.15 — the axis matters)
```

It is the COMPRESSION chord, so no uplift combines with it.

## 5. Heads and bases, all four posts

**5a. Parts.** The glulam ENDS on each south post and runs on past each north one: an ACE6Z at
`PT-BW-CW`/`-RE`, an AC6Z at `-CNW`/`-RNE` (ESR-2604 §3.1.3; ACE6 MAX 1,950 / 1,760, AC6 MAX
2,815 / 2,075 lb, lateral PARALLEL to the beam only, fn. 6). Across the beam, an A35Z on each post
face with the soffit over it (ESR-3096 Table 5, F1 695 / F2 845, the lower taken): one at an end
post, two at a through post. Bases: CBSQ66-SDS2, F2 along y. The plan's "2,920 / 2,125" for the
AC6 was not in the report; ESR-2604 Table 3 prints 2,815 / 2,075.

**5b. Demands.** Own drag, 16.8315 psf on 5.5", half at each end:

```
west   16.8315 x 0.4583 x 7.6354 / 2 = 29.45 lb        east  ... x 6.1771 / 2 = 23.83 lb
```

The west posts also take the screen's out-of-plane E-W load at the top plate: the panel spans
sill to plate and the band plate to header, so the plate line carries half of each,

```
w = 16.8315 x (4.0833/2 + 2.34375/2) = 54.09 plf,  P = 54.09 x 4.5208 / 2 = 122.26 lb per post
a = 4.0000 + 1.2917 = 5.2917' above the base,  b = 7.6354 − 5.2917 = 2.3437'
head across = 29.45 + 122.26 x 5.2917 / 7.6354 = 114.18 lb
base across = 29.45 + 122.26 x 2.3437 / 7.6354 =  66.98 lb
```

— on the full solid face; the slats are ~50% open, so this is the conservative end. `P` reaches
each post through an A35Z at the plate end (`CN-BW-PLATE-*`): 122.26 / 695 = **0.176**.

Head uplift is the net roof uplift, 433.3 lb; on a chord add the band's couple, the deck's
shear acting a header depth above the straps' pull: 1,045.06 x 0.98958 / 4.9792 = 207.7 →
**640.9 lb**, with the straps' favourable push-down on the header ignored.

**5c. Rows (linear interaction where two directions meet one part).**

| post | cap | uplift + along | A35 across | base, across (uplift + F1) | base, along (+ F2) |
|---|---|---|---|---|---|
| CW | ACE6Z | 640.9/1,950 + 29.45/1,760 = **0.345** | 114.18/695 = 0.164 | 433.3/3,060 + 66.98/485 = 0.280 | + 29.45/1,270 = 0.165 |
| CNW | AC6Z | 640.9/2,815 + 29.45/2,075 = 0.242 | 57.09/695 = 0.082 | 0.280 | 0.165 |
| RE | ACE6Z | 433.3/1,950 + 23.83/1,760 = 0.236 | 23.83/695 = 0.034 | 433.3/3,060 + 23.83/485 = 0.191 | 0.160 |
| RNE | AC6Z | 433.3/2,815 + 23.83/2,075 = 0.165 | 0.017 | 0.191 | 0.160 |

The column on the west post, the diaphragm note's §5a arithmetic on the longer post:

```
axial    40 x (10 + 73.7) + 7.87 x 7.6354 = 3,408 lb;  f_c = 3,408 / 30.25 = 112.7 psi
         l/d 91.625 / 5.5 = 16.66;  FcE = 0.822 x 440,000 / 16.66² = 1,303 psi;  C_P 0.879
         Fc' = 525 x 1.15 x 0.879 = 530.9 psi                                       0.212
moment   16.8315 x 0.4583 x 7.6354² / 8 + 122.26 x 5.2917 x 2.3437 / 7.6354
         = 56.2 + 198.6 = 254.8 lb-ft;  f_b = 254.8 x 12 / 27.73 = 110.3 psi
§3.9     (112.7 / 530.9 + 110.3 / 1,360) / (1 − 112.7 / 1,303) = 0.2934 / 0.9135      0.321
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
at 16.8315 psf = 646.97 lb, plus 2 x 23.83 = **694.62 lb**. Its resultant (the diaphragm note's
§3b arithmetic on these bands) stands at y 40.2034, 3.0153' off the joint at 43.2188:

```
M = 694.62 x 3.0153 = 2,094.5 lb-ft
chord force  M / W' = 2,094.5 / 24.000 = 87.3 lb in each header
  glulam, Table 5A 24F-V4 Ft 1,100 x wet 0.80 x C_D 1.6 = 1,408 psi; 87.3 / 65.3 in2 = 1.34 psi   0.001
  end strap (LSTA24): 87.3 + 694.62 / 7 = 186.5 lb vs 1,235                                0.151
the couple into RF-GARAGE: M / 24.000' = 87.3 lb on each of W-G-W and W-G-E, E-W case
  W-G-W  87.3 / 17.392' = 5.02 plf vs 182.5  0.027      W-G-E  87.3 / 19.725' = 4.43 plf  0.024
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

* **Diagonal slats as the brace** (IRC Method DWB, or SDPWS diagonal lumber). The gaps between
  slats and the absence of studs and plates to nail them to put the band outside both rows.
  Recorded as the future option: it would want a continuous 1x6 at 45° lapping full-height
  studs at 16", let into plates at each end, which is a different wall.
* **`PLATE-TOP-0-1` as a moment cross-beam** (a portal). The posts become bending members in
  the frame, and no published moment rating exists for the angles or caps it would lean on.
* **Horizontal slats.** SDPWS's horizontal-lumber row is ~50 plf nominal; gapped boards are
  outside it, and the demand is 192.
* **A heavier panel alone** closes §4a and not §2: the band is still unbridged.
* **TWB12.** A let-in brace for kerfed studs, and the band has none; no tension row fits here.
* **A 12" pier under the CBSQ** — §5e, 1/4" short of the side cover.

## 9. What is NOT graded here

* The truss end chords (N-S) and their splice slip — the truss order (`rafter/RF-BW-CANOPY`).
* The slats' own out-of-plane span (IRC R301.5 fn. f, in-fill; `SC-BW-WEST`'s note).
* Nail withdrawal at the LTP4s under the deck's own uplift — the heel ties carry that.

## Sources

- AWC SDPWS-2015 Table 4.3A, §4.2.5.2, §4.3.4.
- ICC-ES ESR-2105 Table 4 (CS16), Table 3 (LSTA24); ICC-ES ESR-2604 §3.1.3 and Table 3 (AC/ACE);
  ICC-ES ESR-3096 Table 5 (A35); ICC-ES ESR-3050 Table 1, §4.1, fn. 4 (CBSQ); all read 2026-09-30.
- Simpson Strong-Tie C-C-2024, CBSQ lateral F1 485 / F2 1,270; C-C-2019 p. 280 (LTP4).
- AWC NDS 2018 Supplement Tables 4D and 5A; NDS Tables 4.3.8, 5.3.1, §3.9, §3.10, §5.3.6.
- ACI 318-19 §10.3.1.2, §10.6.1.1. ASCE 7-16 §11.7.

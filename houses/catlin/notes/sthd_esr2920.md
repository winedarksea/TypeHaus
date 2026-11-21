# Cast-in STHDs against ESR-2920 (hand check, 2026-11-20)

The oracle for `structural.strap_hold_down_embedment` and `resolve/rebar/strap_bars.py`.
Every number below was worked by hand from the plan's coordinates. Units are inches. z is
project-absolute.

## What was read

**ICC-ES ESR-2920**, reissued February 2026. Source:
<https://icc-es.org/wp-content/uploads/report-directory/ESR-2920.pdf>, read 2026-11-20.
The same rows are printed in Simpson C-C-2026 pp. 66-68.

**Table 1** (p. 6). STHD14/STHD14RJ, Wind and SDC A&B, 30 nails, l_e = 14. Values are lbf,
uncracked = cracked:

| stem | midwall | corner | endwall |
|---|---|---|---|
| 6" | 4,935 | 4,935 | 3,065 |
| 8" | 5,285 | 5,285 | 4,410 |

- **fn. 6.** Detached dwellings in SDC C may use the wind/A&B columns. Minnesota is SDC A.
- **fn. 7.** Straps acting together are spaced at least 3 l_e = 42" apart. The midwall
  column assumes 1.5 l_e = 21" of end distance.

**Figure 1** (p. 7). The strap is cast at the face of the stem. The spoon leans across the
stem, 4 3/4"-5 1/4" out from the strap face. Corner and endwall installations need 1/2" of
end distance.

**Rebar** (Figure 1). One #4 bar 3"-5" below the top of the foundation, extending:

- midwall: 2 l_e each side;
- endwall: 2 l_e past the strap;
- corner: around the corner, with a 24" leg for STHD14.

**Report sections:**

- **§3.1.1.** The cast-in part is 2 5/8" wide.
- **§3.2.5.** f'c must be at least 2,500 psi. Catlin's mixes are all 2,500 psi or more.
- **§4.2.** The strap "may be bent one full cycle (bent horizontally 90 degrees then bent
  vertically) to aid wall placement." The #4 bar goes 3"-5" from the top.

**C-C-2026 p. 66:**

- The RJ crosses up to 17" of clear span "without any loss of strap nailing".
- No horizontal cold joint may fall within the embedment depth.

No clear span is printed for the standard strap. Figure 1 draws it over one 2x sill, so it is
read only there: **1 1/2"**. (17 - 13 1/2 = 3 1/2" from the two lengths is arithmetic, not
print; a standard strap over more grades UNKNOWN. Review, 2026-11-20.)

**C-C-2026 p. 68, brick ledge.** An STHD14 set 4" from the inside face, bent straight, needs
an 8" minimum wall (fn. 10: 8" STHD14 loads). No catlin strap uses this detail. Its callout
reads the cycle as "bending the strap straight and aiding for wall placement": both brick
ledge straps rise **plumb** from where they are cast. No Simpson figure shows a jog.

**ICF is not addressed by ESR-2920 or C-C-2026.** The 6" core is read as the stem. The EPS
is formwork and carries nothing. Where the concrete across the strap is under 6", no row
applies and the check FAILs.

## How each strap is read

- **Row.** Concrete **ahead** of where the strap is cast, along the spoon:
  - at least 8" takes the 8" row;
  - at least 6" takes the 6" row.

  A strap cast inside the core instead of at a face has concrete behind it that the tested
  strap did not. The check credits it with nothing, so this reading is conservative.
- **Bent strap.** A strap bent one cycle is measured from where it is **cast**.
- **Allowable.** Cracked, wind/A&B.

## The garage, 2026-11-20 (owner): no STHD at all

Owner: "Drop the corner straps if they are not required by code and do not fit." They are
neither, and the two panel straps became bolted hold-downs. Everything below "The garage:
why every strap was jogged" is the record of why.

### The three corners: not required

- **R602.10.7.** The garage braces by CS-WSP. A line end needs a 24" sheathed return
  (end conditions 1, 4), a panel at the end (3), or an 800 lb hold-down (2, 5). NE, SE and
  NW meet 1/3/4 on their returns; `structural.braced_wall_panels` passes all four garage
  lines without them (the derived straps were never a `hold_down_ref`). Only SW has no
  return: D-G-SERVICE leaves 11".
- **R602.3.5** (2018 IRC, read on UpCodes 2026-11-20). Item 1.1 does not apply (the garage
  roof is 4:12, under 5:12). Item 1.2: net uplift at the wall top, by R802.11, at most
  100 plf. Table R802.11, Exposure B, 24" o.c., the 24' row, 115 mph, under 5:12: **178 lb**
  a truss (`wind_tables.uplift_connection_force_lb("B", 24, 24, 115, 4)`), 178 / 2 ft =
  **89 plf <= 100**. So Table R602.3(1) fastening is the uplift path; no connector is asked
  for at all, and none at a corner.
- The rule that placed them was the house's (`holdowns_per_run_end`, one per exterior
  corner). It now places a strap only where one rises plumb from a Figure 1 entry
  (`joints/strap_corners.plumb_entry_fits`: the catalog spoon, less 3/4" cover, fits ahead of
  the leaf). In the garage 3.44 - 0.75 = 2.69 < 5.25: none. The house's 8" walls: 6 - 0.75 =
  5.25, so all three house corners keep theirs. The bill, S-100, the #4 bars and the check
  all read that one rule.

### The two panel ends: HTT4 on a cast-in SSTB16

Read 2026-11-20 from Simpson C-C-2026 (`out/bw-corner-brace-review/C-C-2026.pdf`):

- **p. 63, HTT4:** (18) 0.148 x 1 1/2 nails, minimum member 1 1/2 x 3 1/2: DF/SP 3,000,
  **SPF/HF 2,580 lb** (160). Anchor 5/8"; CL 1 5/16" (rod centre off the member face);
  W 2 1/2"; L 12 3/8". General note a: no further increase.
- **p. 43, SSTB at stem wall, Wind and SDC A&B:** SSTB16, 6" stem, 5/8", l_e 12 5/8,
  middle / corner / end **3,465** each. Plan views: 1 3/4" minimum to the face, 5" to the end
  at a corner or end, #4 bar 3-5" from the top, 2 l_e each way, a 16" return at a corner.
  fn. 5: middle at 1.5 l_e from the end; 3 l_e between bolts in tension together. p. 42:
  2,500 psi.
- **p. 51, Table 2 (SPF/HF):** the HDUE3 pairs with SSTB16 in a 6" stem. The HTT4 is listed
  there only at 8" (SSTB24) because that table develops the tie's full DF value; here the two
  rows are read separately and the lesser governs. General note d: the anchor is the
  designer's to specify.

Why not the alternatives: a MASA or the 1/2" sill bolts are plate anchorage, not an end-post
hold-down, so they cannot make end condition 2. An HDUE needs a 3" post and the SW end is a
single stud (W-G-S owns the corner pack). A DTT2Z takes a 1/2" rod, and no published 1/2"
anchor row covers a 6" stem.

**Geometry** (garage cores: W-GF-W x 74.5..80.5, W-GF-S y 521.125..527.125; studs 2x6):

| | SW (CN-G-BWHD-SW / -BWAB-SW) | S-DR (CN-G-BWHD-S-DR / -BWAB-S-DR) |
|---|---|---|
| member face | W-G-W end stud, north face y 526.0625 | east king, east face x 119.5 |
| rod | (76.5, 527.375) = face + 1.3125 | (120.8125, 523.125) = face + 1.3125 |
| to the faces | 76.5 - 74.5 = **2.00**; 80.5 - 76.5 = 4.00 | 523.125 - 521.125 = **2.00**; 4.00 |
| tie on the member | x 75.25..77.75 on the stud's 72.44..77.94 | y 521.875..524.375 on 519.06..524.56 |
| end | 527.375 - 521.125 = **6.25** to W-GF-S's outer face: corner (< 1.5 x 12.625 = 18.94), >= 5 | 120.8125 - 74.5 = **46.31**: middle |
| pour | -12 to -76 = 64 >= 12.625 | 64 |
| #4 bar, z -16 | north to 527.375 + 25.25 = 552.625, to the corner y 524.125 (28.5), 16 east to x 93.5 | 120.8125 +/- 25.25 = x 95.5625..146.0625 |

The rod is 2" off the core's outer face because the tie must sit on the stud: the stud's
inside face is 3 7/16" off the core's outer face, so the rod can be at most 3.4375 - 1.25 =
2.19" off it with the 2 1/2" tie still on the stud; 2.00 sits between that and the 1.75
minimum. The garage sill bolts move clear of each seat (`joints/sills`):
SW's W-G-W end bolt from y 524.62 to 530.375, its washer 1/2" past the seat.

**Capacity and demand:**

```
SW     min(HTT4 2,580, SSTB16 corner 3,465) = 2,580 lb   vs 800 (Figure R602.10.7)   0.310
S-DR   min(HTT4 2,580, SSTB16 middle 3,465) = 2,580 lb   vs 275.47 (canopy §3f)      0.107
```

R602.10.7 reads the HTT4's published 2,580 >= 800, so SW keeps end condition 2.
`structural.anchor_rod_hold_down` grades both rows (blocking permit line, "Bolted
hold-downs on cast-in anchors"); `structural.strap_hold_down_embedment` no longer sees the
garage.

Not graded: the SSTB's offset leg is set by the AnchorMate holder and its arrow; the nut is
finger tight plus 1/3-1/2 turn (general note f). ICF is not addressed by C-C-2026: the core is
read as the stem, as for the STHDs above.

## The garage: why every strap was jogged (superseded 2026-11-20)

Take W-GF-E. The core runs x 351.5..357.5 and W-G-E's studs x 354.0625..359.5625.

A strap cast at the stud face x = 354.0625 has:

- 2.5625 of core behind it, toward the room;
- 3.4375 ahead, toward the outside.

The spoon needs at least 4.75 and as much as 5.25. It fits in neither direction. Before this
change the engine drew it bent short to about 2.7, which no row covers.

**The fix:**

1. Cast the strap at the core's **inside face**, x = 351.5. That leaves 6.0 ahead: Figure 1
   exactly, with 6.0 - 5.25 = 0.75 cover past the toe.
2. Jog it flat over the pour top, 2 9/16" outward to the stud face, then up (the implementer read this as §4.2's one cycle; UNKNOWN, see below).
3. The flat leg and the leaf pass the sill's inside edge in S-103's 4"-wide notch. The sill
   runs x 352.31..359.56, so the notch is 354.06 - 352.31 = 1 3/4" deep, as already drawn.

The strap's length above the line drops by the leg: 26.125 - 2.5625 = 23.5625. Thirty nails
still fit on the studs, because the clear span is only the 1 1/2" sill.

### The garage jog (review, 2026-11-20; closed the same day, above)

The check graded all five garage straps **UNKNOWN** and shut the permit gate on that line,
until the owner's decision above removed them.

- **Not printed.** Figure 1 and every C-C-2026 p. 68 detail show the strap rising plumb from
  where it is cast. Simpson's own gloss on §4.2 is "bend the straps to horizontal and back to
  vertical one cycle" (SE blog, 2016-03): the cycle clears the wall as it is set, then the strap
  goes back plumb. Simpson's over-sheathing guidance caps a jog at 5/8".
- **It straightens under load.** The 12 ga leaf, 2 5/8" wide, t = 0.1026:
  Z = 2.625 x 0.1026^2 / 4 = 0.00691 in^3; M_p = 33 ksi x Z = 0.228 k-in.
  The jog yields at T = 0.228 / 2.5625 = **89 lb**, against 800 required at BWHD-SW. Before it
  holds, the leg pulls up into a diagonal. Table 1's 0.118" deflection does not apply.

Options (option 3 and a bolted hold-down for the two panel ends were taken):

1. A hold-down with a published row in a 6" stem (an anchor-rod hold-down on a cast-in rod
   placed under the framing, e.g. SSTB + HDU/DTT). It needs its own reading.
2. An 8" core (BB800) with the brick-ledge detail: STHD14 cast plumb under the stud face, spoon
   straightened (fn. 10). It needs the stud face 4" off the inside face.
3. Drop the three derived garage corner straps (a house rule, `holdowns_per_run_end`; no code
   asks for them), which leaves BWHD-SW and S-DR to solve.
4. Simpson's written acceptance of the jog. The owner prefers not to rely on letters.

## Per strap

### Shared values

| | garage | house (and porch) |
|---|---|---|
| pour top | -12.0 | -13.4375 (porch curb -102.1875) |
| toe = line - 14 | -26.0 | -27.4375 (porch -116.1875) |
| embedment | 14.0 = l_e | 14.0 = l_e |
| first stud | -10.5 | 2.25 |
| clear span | 1.5 | 2.25 + 13.4375 = 15.6875 |

- The garage and porch clear span is 1.5, Figure 1's one sill: the standard strap.
- The house clear span is over that and at most 17, so it takes the **RJ**.
- The porch curb pour is the 7.25 curb plus the 15 footing, cast together
  (`Footing.cast_with_wall`): 22.25 at least 14. Without that it would be 7.25, a cold joint
  inside the embedment, and a FAIL.
- **End distance** = run from the strap centre to the end of the concrete, minus 1.3125.

### Results

| strap | part | behind / ahead | row | end distance | location | allowable | demand / ratio |
|---|---|---|---|---|---|---|---|
| (retired) CN~STHD14~..~02 (garage NE, W-GF-E) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 804.125 - 799.1875 - 1.3125 = 3.625 | corner | UNKNOWN (jog) | none stated |
| (retired) CN~STHD14~..~03 (garage SE, W-GF-S3) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 357.5 - 352.5625 - 1.3125 = 3.625 | corner | UNKNOWN (jog) | none stated |
| (retired) CN~STHD14~..~01 (garage NW, W-GF-N) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 79.4375 - 74.5 - 1.3125 = 3.625 | corner | UNKNOWN (jog) | none stated |
| (retired) CN-G-BWHD-SW (W-GF-W) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 526.0625 - 521.125 - 1.3125 = 3.625 | corner | UNKNOWN (jog); 4,935 if rated | 800 / **0.162** if rated |
| (retired) CN-G-BWHD-S-DR (W-GF-S-DR) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 161.5 - 118 - 1.3125 = 42.19 (at least 21) | midwall | UNKNOWN (jog) | 275.47 (canopy note §3f) / 0.056; not in the model |
| CN~STHD14RJ~..~01, ~02, ~03 (house SW, NW, SE) | STHD14RJ | 2 / 6 (8" wall, leaf at stud face 6") | 6" | 7.5 - 0 - 1.3125 = 6.19 | corner | 4,935 | none stated |
| CN-M-BWHD-NE-E (W-B-E2, 10" wall) | STHD14RJ | 4 / 6 (x 422..432, leaf 426) | 6" | 432 - 401 - 1.3125 = 29.69 | midwall | 4,935 | 800 / **0.162** |
| CN-M-BWHD-NE-N (W-B-N1) | STHD14RJ | 2 / 6 | 6" | 29.69 | midwall | 4,935 | 800 / **0.162** |
| CN-M-HD-ENTRY-E / -W (W-B-N3) | STHD14RJ | 2 / 6 | 6" | 115.7 / 71.3 | midwall | 4,935 | none stated |
| CN-B-HD-PORCH-W (W-B-S3 curb) | STHD14 | 0 / 6 (curb y 0..6, leaf 6) | 6" | 94.3 | midwall | 4,935 | none stated |
| CN-B-HD-PORCH-E (W-B-S3 curb) | STHD14 | 0 / 6 | 6" | 314 - 293.656 - 1.3125 = 19.03 (under 21) | endwall | **3,065** | none stated |

**Porch E end.** The curb ends at W-B-S4. W-B-S4 is a full-height wall with a different pour
top, so it is not credited as continuing concrete.

**Demands.** Only three demands are in the model: the braced-panel `hold_down_ref`s, each at
800 lb (IRC Figure R602.10.7). The canopy chord's 275.47 lb is from the hand note and is
shown here only for comparison.

### Spacing

- ENTRY-E to ENTRY-W: 117 - 72.625 = 44.375, at least 42.
- PORCH-W to PORCH-E: 75.31.
- NE-E and NE-N are on perpendicular lines, about 35" apart. IRC R602.10.1 grades the two plan
  directions separately, so they are not a simultaneous pair. Every corner strap stands
  alone at its corner.

### The No. 4 bar

Placed 4" below the top (z -16 garage, -17.4375 house, -106.1875 curb), on the core's
mid-thickness, with the pour's cover at the ends.

- **Garage NE.** Along x = 354.5 from y = 799.1875 - 28 = 771.1875 to the corner at
  y = 801.125 (W-GF-N2's mid-thickness), then 24" west.
  Length = 29.9375 + 24 = **53.94**. That gives 28 = 2 l_e past the strap, and the 24" leg.
- **NE-E.** 28 south (y 373..401). North to the corner y = 428 (27), then 24 west.
  Length = **79.0**. The north side is 27 + 24 = 51, at least 28.
- **Midwall straps** (S-DR, ENTRY, PORCH-W). 2 x 28 = **56** straight.
- **PORCH-E.** 28 west of the strap, east to the curb end less 3" cover: 28 + 17.34 = **45.3**.

These supersede the 40" bar the service-door note specified. The midwall strap needs 2 l_e
**each side**.

## What changed in the model

1. Every embedment line now sits on the pour top:
   - The house NE pair and the entry pair were at z = +1, so their toes ended 0.44" **above**
     the concrete.
   - The porch pair was 3/4" high, leaving 13.25 embedded.
   - CN-G-BWHD-SW was 3/4" high, also 13.25 embedded.
2. The house and porch leaves moved onto their stud band's inside face. The house leaves had
   been mid-band.
3. The entry pair became STHD14RJ. Derived corners are now sized: STHD14 on a sill, STHD14RJ
   across a band. A derived STHD at a house corner had been a standard strap across 15 11/16"
   of band.
4. The garage straps are cast at the core face and jogged 2 9/16" (UNKNOWN since the review).
5. One derived #4 bar per strap.

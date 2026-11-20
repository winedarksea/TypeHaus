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

## The garage: why every strap is jogged (and why that is UNKNOWN)

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

### Open: the garage jog (review, 2026-11-20)

The check grades all five garage straps **UNKNOWN**, and the permit gate is shut on that line.

- **Not printed.** Figure 1 and every C-C-2026 p. 68 detail show the strap rising plumb from
  where it is cast. Simpson's own gloss on §4.2 is "bend the straps to horizontal and back to
  vertical one cycle" (SE blog, 2016-03): the cycle clears the wall as it is set, then the strap
  goes back plumb. Simpson's over-sheathing guidance caps a jog at 5/8".
- **It straightens under load.** The 12 ga leaf, 2 5/8" wide, t = 0.1026:
  Z = 2.625 x 0.1026^2 / 4 = 0.00691 in^3; M_p = 33 ksi x Z = 0.228 k-in.
  The jog yields at T = 0.228 / 2.5625 = **89 lb**, against 800 required at BWHD-SW. Before it
  holds, the leg pulls up into a diagonal. Table 1's 0.118" deflection does not apply.

Options, none taken:

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
| CN~STHD14~..~02 (garage NE, W-GF-E) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 804.125 - 799.1875 - 1.3125 = 3.625 | corner | UNKNOWN (jog) | none stated |
| CN~STHD14~..~03 (garage SE, W-GF-S3) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 357.5 - 352.5625 - 1.3125 = 3.625 | corner | UNKNOWN (jog) | none stated |
| CN~STHD14~..~01 (garage NW, W-GF-N) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 79.4375 - 74.5 - 1.3125 = 3.625 | corner | UNKNOWN (jog) | none stated |
| CN-G-BWHD-SW (W-GF-W) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 526.0625 - 521.125 - 1.3125 = 3.625 | corner | UNKNOWN (jog); 4,935 if rated | 800 / **0.162** if rated |
| CN-G-BWHD-S-DR (W-GF-S-DR) | STHD14 | 0 / 6.0 (jog 2.5625) | 6" | 161.5 - 118 - 1.3125 = 42.19 (at least 21) | midwall | UNKNOWN (jog) | 275.47 (canopy note §3f) / 0.056; not in the model |
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

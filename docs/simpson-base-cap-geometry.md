# Simpson base, cap and heavy-angle geometry

The procedural meshes use manufacturer dimensions in inches and convert to metres at
the geometry boundary. They represent open steel assemblies, retaining member clearances,
seat height, embedded returns, gauge, and the large leaf outlines. Bend radii, weld beads,
embossing, nail/bolt holes, supplied washers, and fasteners are omitted. Small corner clips
are simplified to 1/8 inch. These are visual models, not fabrication drawings.

The source drawings were checked on 2026-10-04. Simpson hosts the downloadable catalog
pages on its own Widen account, linked from its [catalog page](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog).
The downloads were inspected locally; proprietary CAD assets are not committed.

| Family | Published dimensions represented | Primary drawing |
| --- | --- | --- |
| ABU44 / ABU44Z / ABU44SS | W 3-9/16, L 3, H 5-1/2; standoff pan 16 ga, U strap 12 ga | [C-C-2026 pp. 76–77](https://ssttoolbox.widen.net/view/pdf/7ftb0cfhtp/C-C-2026-p076-077.pdf?t.download=true) |
| ABU66 / ABU66Z / ABU66SS | W 5-1/2, L 5, H 6-1/16; pan 12 ga, strap 10 ga | Same ABU drawing/table |
| CBSQ66-SDS2 / HDG | W1/W2 5-1/2, straps 3 wide, H 8-3/4, embedment D 6-7/8; pan 12 ga, straps 10 ga | [C-C-2026 p. 85](https://ssttoolbox.widen.net/view/pdf/frun6iv5rf/C-C-2026-p084-085.pdf?t.download=true), showing the similar CBSTQ replacement and matching dimensions; existing CBSQ66 designation/dimensions retained |
| PC6Z | W 5-1/2, leaf L 7, beam height 3, post tab 2-5/8 wide × 1-5/8 high; 16 ga | [C-C-2026 p. 97](https://ssttoolbox.widen.net/view/pdf/fmsf4lvvdw/C-C-2026-p097.pdf?t.download=true) |
| CCQ46SDS2.5 / HDG / SS | Beam opening W1 3-5/8, post opening W2 5-1/2, L 11, saddle H 7, post leaves 8-1/2 × 2-1/2; 7 ga | [C-C-2026 pp. 98–99](https://ssttoolbox.widen.net/view/pdf/u4l1un3ze4/C-C-2026-p098-099.pdf?t.download=true) |
| AC6Z | Pair of 18 ga leaves, L 8-1/2, nominal post W 5-1/2, beam leaf height 3, post leaf height 2-1/2, returns 1-1/2 | [C-C-2026 pp. 94–95](https://ssttoolbox.widen.net/view/pdf/k5m48v2eo8/C-C-2026-p094-095.pdf?t.download=true) |
| ACE6Z | End-condition pair, L 6-1/2; same gauge/heights/returns as AC | [ICC-ES ESR-2604, Table 3 and Figure 3](https://www.floridabuilding.org/upload/PR_Tech_Docs/FL10860_R4_AE_ESR-2604.pdf), manufacturer evaluation drawing hosted by Florida Building |
| L50Z | Length 5, unequal legs 2-3/8 and 1-3/8; 16 ga | [C-C-2026 p. 313](https://ssttoolbox.widen.net/view/pdf/hey6zjyspk/C-C-2026-p313.pdf?t.download=true) |
| HL33HDG / HL35HDG | Both legs 3-1/4; lengths 2-1/2 / 5; 7 ga | [C-C-2026 p. 315](https://ssttoolbox.widen.net/view/pdf/kkvkkzhwop/C-C-2026-p315.pdf?t.download=true) |

ABU44R/ABU66R, CCQ44/CCQ66, and the catalog CCQ4.62-5.50SDS size use the corresponding
published clear widths. Coating suffixes select the same shape. Unsupported part codes
return `None`, letting the dispatcher handle its existing marker behavior.

## Local datums and orientation

- Bases: concrete top is z=0, and the wood seat is z=1 inch. The ABU has a U strap with
  a thin bottom and a hollow raised pan. The CBSQ has narrow leaves extending into concrete,
  joined by their embedded bottom return, plus the raised pan.
- Caps: beam soffit is z=0. PC/CCQ bearing steel is below this plane; post leaves extend
  downward and beam leaves upward. CCQ's post leaves are perpendicular to its beam side
  leaves, which preserves the different W1 and W2 openings. Its saddle height includes the
  bearing plate. AC/ACE have direct wood bearing and separate side pieces; `member_width_in`
  can adjust their spacing without changing their manufactured leaf lengths/heights. Beam
  depth never stretches a part. ACE's beam leaf begins at the negative-x post end face.
- Angles: the heel runs along x, centered longitudinally. The horizontal bearing face
  extends in +y at z=0, and the vertical face extends in +z at y=0. Steel occupies the
  negative side of each bearing plane. The resolver rotates this frame to the authored axis.

Nominal steel thicknesses are 7 ga 0.1793, 10 ga 0.1345, 12 ga 0.1046,
16 ga 0.0598, and 18 ga 0.0478 inch. These are nominal sheet gauges; minimum base-metal
thicknesses in evaluation reports are tolerances rather than target visual dimensions.

## Existing metadata mismatches

The library's ABU44/ABU66 sources/insets currently add a 7 ga plate to the manufacturer's
1 inch standoff. The published gauge table instead distinguishes the pan from the U strap,
and Simpson describes its standoff as elevating the wood above concrete; the heavy supplied
washer sits at the anchor beneath the raised seat. This geometry uses the published 1 inch
wood bearing height. See also Simpson's [ABU product page and downloadable installation
drawings](https://strongtie.com.au/products/abu-adjustable-post-base), which independently
identify separate pan/strap thicknesses and the nominal standoff. Catalog/inset corrections
must be assessed separately from the visual mesh.

The existing L50Z source says “5 in legs.” That number is the angle's length along the heel;
the two legs are 2-3/8 and 1-3/8 inches. The geometry follows the manufacturer drawing.

The tests intersect the actual triangle surfaces to measure member openings and the raised
seat, in addition to overall bounding dimensions. They do not load a house or mutate a shared
fixture.

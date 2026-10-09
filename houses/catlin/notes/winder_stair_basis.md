# Catlin winder geometry and construction

ST-S2A retains three winders, 36-inch clear entry/departure widths, sixteen 7½-inch
risers, and twelve 10-inch straight goings on three 1¾ × 11⅞-inch LSL stringers.
The east and north bearing faces stay in place. The turn extends 13¼ inches into the
entering and departing runs: its outside footprint is 49¼ inches square around a
13¼-inch inside well. The attic opening extends west 13¼ inches and south to the next
joist line at y=48 inches. The stair head retains the required 36-inch landing depth.
The flight guard follows the actual open edge; the wall handrail wraps both outer turn
faces. The nearby study window now uses the existing tempered type. The south supply
branch and boot move one inch south to clear the enlarged opening's trimmer.

`WinderTurnSpec` supplies the footprint, clear inside boundary, and four ordered riser
segments, including entry and departure. Finished noses come from physical oak polygons.
The concentric walkline radius is the distance from the turn centre to the widest clear
part of the inside boundary plus 12 inches. Depths are chords between adjacent finished
nosing intersections, including the first winder and the transition to the straight flight.
Minimum clear depths use every vertex of each physical tread clipped between finished
nosings, covering both the inside boundary and any irregular outer edge.
Winder uniformity is checked separately from rectangular tread uniformity.

Walkline depths are 12.837, 12.837, and 12.837 inches; spread is below 0.001 inch.
Minimum clear depths are 6.491, 6.357, and 6.357 inches. These meet the 10-inch, 6-inch,
and ⅜-inch requirements. See the [walkline definition](https://stairways.org/blog/r311-7-4-walkline-2021/)
and [winder tread provisions](https://stairways.org/blog/r311-7-5-2-1-winder-treads-2021/).

Each box has a complete ¾-inch structural plywood deck beneath the exposed oak and next
box. Upper frames bear on preceding plywood, with blocking under rim bearing lines.
Plywood seams and perimeter edges have framing below; support spacing is at most 16 inches.
The first frame bears on structural subfloor at 120¾ inches, rather than the finished floor
at 121½ inches. Its ripped rim height is 6½ inches; the following two are 6¾ inches.
Every departing rim has two separate 1½-inch plies, transferring the upper connection
through the stack. Steel connector plates model straight-stringer attachment to the top
rim. The newel stands outside clear stair width and bears on the sistered floor joist
and solid bay blocking. Upper boxes generate no duplicate landing posts.

`stair_subdeck` belongs to structural framing and sheet goods. It contributes no walking
step, oak millwork, or duplicate sheet-rip quantity. Full 1-inch oak panels include integral
noses and rear fit. Physical polygons and elevations pass to JSON, the viewer, glTF, IFC,
plans, sections, and construction detail A-401.1. Viewer grain and millwork share the nosing
axis. The existing LSL stringer basis remains in `stair_stringer_basis.md`.

| Winder | Previous blank, inches | Physical blank, inches |
| --- | --- | --- |
| W1 | 25.00 × 36.00 | 30.30 × 38.32 |
| W2 | 17.87 × 46.85 | 29.87 × 56.35 |
| W3 | 19.74 × 38.42 | 25.63 × 45.97 |

New dimensions project the complete physical panel along/perpendicular to its nosing,
including the nose once. Rough stock, trim, jointing, and glue-up allowances remain in the
existing millwork calculation. The regenerated schedule is `out/catlin-millwork.csv`.
Review artifacts are `out/catlin-winder-detail.pdf` and
`out/catlin-winder-framing-3d.png`; the detail also belongs to the permit sheet index.

# Catlin winder geometry and construction

ST-S2A retains three winders, 36-inch clear entry/departure widths, sixteen 7½-inch
risers, and twelve 10-inch straight goings on three 1¾ × 11⅞-inch LSL stringers.
The east and north bearing faces stay in place. Since 2026-10-09 the winders are
square-notched around a 12¼-inch corner notch at the newel. The turn is 48¼ inches
square and extends 12¼ inches into the entering and departing runs. A 6-inch narrow end
needs about 19 inches of inside edge at 36 inches clear, so three winders cannot get
meaningfully smaller: a 12-inch notch reaches only 6.15 inches.

FO-A-STAIR is the straight flight only: x 21'-4⅜"..35'-5⅜", y 5'-9⅝"..8'-9⅝". Its
south edge is the flight's own south face. The turn sits under intact FS-ATTIC deck.
Winder 3's walking surface is at 144 inches; the deck framing's underside is at
228⅛ inches. `code.R311_7_2_stair_headroom` measures 7.05 feet over the turn (6'-8"
required). The resolver requires only the straight treads inside the hole
(`resolve/stairs/dispatch.py::_stair_fits_opening`, `winder_support.winder_members_fit_opening`).
The trimmer pack on the south edge absorbs the y=5'-4" joist, which `line_overrides` moves to
y=5'-6" inside the pack band. The stair head retains the required 36-inch landing depth.

One guard line runs on y=5'-9⅝". RL-A-STAIR (42 inches, on the deck) runs from the head
east to x=29'-4½", where W-A-GC-S takes over under the rake. RL-A-FLIGHT-GUARD holds 36
inches over the nosings from the first straight riser (31'-5⅛") to the 25'-5⅛" newel.
RL-A-FLIGHT-SKIRT, an 18¾-inch raked panel from the newel to 23'-8¾", closes the band
between the nosings and the pack. The cap reaches the deck at 25'-8⅛"; the newel sits 3
inches west so the skirt closes to 3⅛ inches of the pack. The wall handrail wraps both
outer turn faces. The newel's sistered joist moved 1 inch east with the departing edge
(`params/second_deck.py`).

`WinderTurnSpec` supplies the footprint, clear inside boundary, and four ordered riser
segments, including entry and departure. Finished noses come from physical oak polygons.
The concentric walkline radius is the distance from the turn centre to the widest clear
part of the inside boundary plus 12 inches. Depths are chords between adjacent finished
nosing intersections, including the first winder and the transition to the straight flight.
Minimum clear depths use every vertex of each physical tread clipped between finished
nosings, covering both the inside boundary and any irregular outer edge.
Winder uniformity is checked separately from rectangular tread uniformity.

Walkline depths are 12.594, 12.469, and 12.595 inches; spread is 0.126 inch.
Minimum clear depths are 6.266, 6.270, and 6.518 inches. These meet the 10-inch, 6-inch,
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
plans, sections, and construction detail S-501.1. Viewer grain and millwork share the nosing
axis. The existing LSL stringer basis remains in `stair_stringer_basis.md`.

| Winder | 49¼" balanced turn, inches | 48¼" notched turn, inches |
| --- | --- | --- |
| W1 | 30.30 × 38.32 | 29.17 × 36.00 |
| W2 | 29.87 × 56.35 | 29.89 × 54.02 |
| W3 | 26.27 × 46.35 | 25.53 × 45.65 |

New dimensions project the complete physical panel along/perpendicular to its nosing,
including the nose once. Rough stock, trim, jointing, and glue-up allowances remain in the
existing millwork calculation. The regenerated schedule is `out/catlin-millwork.csv`.
Review artifacts are `out/catlin-winder-detail.pdf` and
`out/catlin-winder-framing-3d.png`; the detail also belongs to the permit sheet index.

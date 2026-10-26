# W-BW-SCREEN — thin brick and single knee braces

Study: 2026-10-25. [Open the comparison sheet](assets/bw-screen-brace-comparison.svg).

![Current slat band compared with one slender or wider knee brace per side, all with retained thin brick](assets/bw-screen-brace-comparison.png)

The three matched east elevations retain the current brown thin brick with grey joints,
including its +2″ to +47½″ finish field. Brick modules follow the current finish spec:
7⅝″ × 2¼″ faces with ⅜″ joints. Colors are illustrative. The lower wall, posts,
symmetric west header tails, centre post and band plates are identical in all views.
The screen is in true elevation; the landing and five risers project obliquely.
Roof, rails, door and west-face connector details are omitted for clarity.

| Option | Visible arrangement | Assessment |
|---|---|---|
| A — former chevron | Seven 1½″-edge slats per bay, fourteen total | Fine chevron texture; retains the modeled structural scheme |
| B — single slender | One 1½″-edge knee per bay, two total | Much more open; the diagonals look light against the brick |
| C — adopted, single wider | One 3½″-face knee per bay, two total; adopted as 4x6, 5½″ deep | Preferred visually: stronger balance with the brick and 5½″ posts |

**C adopted, 2026-10-25:** one standard 4x6 per bay, with its 3½″ face in elevation and
5½″ depth matching the frame. The built centreline is 45°, chord → top plate at
c = −6½″: 6½″ above the sill at the chord, 18⅝″ from the chord face at the top,
26.34″ long. Two KBS1Z at each end, one on each flush face, use ER-280 Table 7 type 1:
734.2 / 1,010 lb = 0.727 on the conservative SPF/HF row. Eight connectors total.

The sheet records the original visual study: its B/C corner-to-corner envelopes are
not cutting templates. The adopted offset leaves room for the KBS1Z's obtuse-side bend
and 5.475″ heel reach; the top margin is 0.275″. A 4x4's recessed east face remains
refused. The complete updated force path and post/screw rows are in the basis note's
2026-10-25 §3 re-work and §5b-c. Option A is retained there in §8 as the chevron backup.

Source geometry and connection rationale:
[band parameters](../houses/catlin/params/entry_band_brace.py),
[structural basis §3](../houses/catlin/notes/canopy_west_band.md),
[current finish specification](../houses/catlin/plan/entry_screen_finish_spec.py),
and [earlier finish comparison](bw-screen-finish-comparison.md).
The current pattern uses the engine's clipped-slat profile routine and the documented
2¼″ clear gap, rather than the earlier finish sheet's schematic slat spacing.

Regenerate the SVG with `.venv/bin/python scripts/review-bw-screen-braces.py`.

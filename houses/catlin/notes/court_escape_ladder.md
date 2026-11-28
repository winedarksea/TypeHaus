# Court escape ladder (D-B-SUNKEN), hand oracle, 2026-11-27

Independent of `code.R310_1_storey_egress`; every figure is from the authored numbers.

## Why a route is needed
- Court floor `SL-SG-FLOOR` top -109.4375"; site grade -34"; yard -40" (`params/sunken_garden.py`).
  Well depth = 109.4375 - 34 = **75.4375"** to grade (69.4" to the yard). Over R310.3.2.1's 44".
- The court is walled on all sides (W1/E1 tops at 0'-0", columns on the corners); the porch plank
  `FS-SG-PORCH` (top +0.94") roofs the north ~9'. Nothing led up. Minn. R. 1309.0310 amends
  R310.1: the opening must lead to a public way or a yard/court that opens to one.
- Minn. R. 1309.0310 exceptions 2 and 3 exempt a basement sprinklered to IRC P2904 / NFPA 13D.
  Not used: the owner chose the ladder.

## Code read (IRC 2018 R310.3.2.1, UpCodes 2026-11-27)
Area wells for escape doors deeper than 44" take a permanently affixed ladder or steps usable
with the door fully open; they are exempt from R311.7. "Ladders or rungs" need an inside width
>= 12", >= 3" projection from the wall, <= 18" o.c. vertically for the full height. R310.4: any
bar, grille, cover or similar device must release from inside without key, tool or special
knowledge. **Climbing holds alone fail the rung text** (no 12" inside width, no rung; an AHJ
could take them only as an alternate under Minn. R. 1300.0110). Holds are safe as decoration
around a compliant ladder.

## Ladder (Tri-Arc WLA6SS, `plan/court_ladder_types.py`)
- Rise to the plank: 0.94 - (-109.4375) = **110.375"**.
- Rungs 12" first, 12" o.c.: 12, 24, ..., 108" above the floor (9 rungs). Top rung 108": plank
  is 110.375 - 108 = **2.375"** above it (<= 18"). First rung 12" (<= 18"). Spacing 12" (<= 18").
- Rung width 18" inside (21-1/16" overall), 7" stand-off (assumed, confirm): >= 12" and >= 3".
- Top rung is -1.4375" abs, 32.6" above grade; rails run to 122" (+12.56" abs).

## Location
- Host `W-SG-E1` court face (x 26'-6"), left face of the S->N wall, 7" from its south node
  (y -11'-0") so the centre is y = -10'-5". Footprint x 25.792'..26.5', y -11.294'..-9.539'.
- North rail outer edge y = -9.539'; plank edge y = -9.5': 0.46" clear, so no plank notch.
- The BF3 column (x 26.5..27.5, y -10.33..-9.33) is behind the ladder, tangent to the wall face.
- Door swing: D-B-SUNKEN swings IN (leaf bounds y +0.09..0.86 m, x 6.52..7.28 m); the ladder
  is >= 3.0 m south and 6.5 m east of it, so the door opens fully with the ladder in use.
- Headroom under the porch from the door to the ladder: plank 0.94" less 1" board and an 11 7/8"
  joist = -11.9" soffit, 97.5" over the floor.

## Route chain
court floor -> `LAD-SG-ESCAPE` (9 rungs) -> side step north through `RL-SG-PORCH-GATE`
(x 23.28'..26.28' on y -9.281', pushed open from the ladder side onto the plank, self-closing,
no latch; modelled closed so R312 still reads a continuous 42" guard) -> `FS-SG-PORCH` plank
(+0.94") -> east across the guard gap (y -8.77'..-5.48') and E1's 12 1/4" top -> `ST-SG-PORCH`
head (arrival +0.94", x 27.56') -> 5 risers of 6.788" to `SL-SG-STAIRPAD` (-33", 1" over site
grade, 7" over the -40" yard, under R311.7.5.1's 7.75").

## Cost (retail, before tax and labour)
Ladder $241-399 (`prices.toml [placeables]`), wall anchors and the gate leaf with self-closing
hinges unpriced (TBD, no matching product read). Install: a few hours, 4-6 wall anchors.

# Open-web truss geometry — worked by hand

Oracle for `typehaus/resolve/open_web.py` (`OpenWebShape`, `grade_crossing`) and the
`PublishedWebOpenings` rows on `FS-S-WEST` (TrimJoist J12) and `FS-M-NE` (TRIFORCE).
Pinned by `packages/engine/tests/test_open_web_shape.py`. All lengths in inches, runs from the
member's `p0` (its west end), heights above the bottom of the truss.

## 0. What is published and what is assumed

**Published (TrimJoist Load & Opening Charts 2026, DrJ 2205-03, Technical Guide Rev 4), 11 7/8"
J12:** D = 5" round; R1 = 8 x 16 at the centreline of the STOCK length; R2 = 4 x 9; a 12" OSB
TrimEnd each end; stock 4'-24' in 2' steps; an 18" duct chase (24" on the larger series), which
may not move more than 12" off centre; 1 3/4" minimum bearing.

**Assumed until TrimJoist's shop layout arrives** (printed in `OpenWebShape.assumptions`):

1. Warren panel points 24" apart on each chord, so a diagonal spans 12".
2. The trim is split evenly between the two stock ends (the chart does not say which end is cut),
   which puts the chase at the member midpoint.
3. Panel points run out from the chase face; the stock remainder is absorbed in the END
   diagonal at the TrimEnd (12" to 24" wide).
4. R2 (4 x 9) is the rectangular alternative to D in any web pocket.
5. Chase posts are one web thick (1.5") just outside the 18" clear.

Constants: depth 11.875, chords 1.5 (clear window z 1.5 .. 10.375, 8.875 tall), webs 1.5.
A diagonal 12" wide spans 8.875" of height, so the web face stands off its centreline by
0.75" measured square: horizontally 0.75 x sqrt(12^2 + 8.875^2) / 8.875 = 0.75 x 14.925 / 8.875
= **1.261"**. A 13.5"-wide end diagonal: 0.75 x sqrt(13.5^2 + 8.875^2) / 8.875 = **1.365"**.

## 1. An 18' truss (FS-S-WEST, 215.0" = 17'-11")

| step | arithmetic | result |
|---|---|---|
| stock | ceil(215 / 24) x 24 | **216"** (18') |
| trim | 216 - 215 = 1, split | **0.5" each end** (12" limit: fine) |
| TrimEnd left over | 12 - 0.5 | 11.5": blocks [0, 11.5] and [203.5, 215] |
| chase centre | 216 / 2 - 0.5 | **107.5** (the midpoint) |
| chase clear | 107.5 +/- 9 | [98.5, 116.5]; posts [97.0, 98.5] and [116.5, 118.0] |
| R1 | 107.5 +/- 8, 8 tall about mid-depth (5.9375) | [99.5, 115.5] x [1.9375, 9.9375] |
| web run, each side | 97.0 - 11.5 = 118.0 -> 203.5 | **85.5** |
| panel points | floor((85.5 - 12) / 12) = 6, so 7 nodes at 12 k | right 118, 130, 142, 154, 166, 178, 190 |
| end diagonal | 203.5 - 190 | **13.5"** (the remainder: 85.5 - 72 = 13.5) |

Left run is the mirror about 107.5: nodes 97, 85, 73, 61, 49, 37, 25, end vertex 11.5.
Nodes alternate top, bottom, top... starting TOP at the chase face; the right-hand end vertex
(203.5) is therefore on the bottom chord.

Pockets (D openings), right run, listed by the vertex they hang from:

* node 118 (top, post on its left): right triangle on the bottom chord, [118.0, 130 - 1.261] =
  **[118.0, 128.74]**.
* node 130 (bottom): pocket on the TOP chord between nodes 118 and 142, both diagonals inset:
  [118 + 1.261, 142 - 1.261] = **[119.26, 140.74]**.
* node 142 (top): on the bottom chord between 130 and 154: **[131.26, 152.74]**.
* node 190 (top): between 178 and the end vertex 203.5: [178 + 1.261, 203.5 - 1.365] =
  **[179.26, 202.13]**.
* end vertex 203.5 (bottom, TrimEnd on its right): on the top chord [190 + 1.365, 203.5] =
  **[191.37, 203.5]**.

Left run by symmetry: node 97 gives [86.26, 97.0].

Chase in PLAN: this member's `p0` is x = 1.75" (behind the 1 1/4" rim, 1/2" off the sheathing),
so **chase centre x = 109.25"** (9'-1 1/4"), R1 x [101.25, 117.25], posts x [98.75, 100.25] and
[118.25, 119.75]. The 21 full trusses (joists and the FO-S-ERV-CHASE trimmers) all share it.

## 2. A stair-clipped truss (FS-S-WEST, 120.75" = 10'-0 3/4")

Five joist lines clipped at `FO-S-STAIR`'s west header.

| step | arithmetic | result |
|---|---|---|
| stock | ceil(120.75 / 24) x 24 | **144"** (12') |
| trim | 144 - 120.75 = 23.25, split | **11.625" each end**: inside the 12" limit by 3/8" |
| TrimEnd left over | 12 - 11.625 | 0.375": blocks [0, 0.375] and [120.375, 120.75] |
| chase centre | 144 / 2 - 11.625 | **60.375** (the midpoint) |
| chase clear | 60.375 +/- 9 | [51.375, 69.375]; posts [49.875, 51.375], [69.375, 70.875] |
| R1 | 60.375 +/- 8 | [52.375, 68.375] x [1.9375, 9.9375] |
| web run, each side | 49.875 - 0.375 = 49.5 | right 70.875 -> 120.375 |
| panel points | floor((49.5 - 12) / 12) = 3, so 4 nodes | right 70.875, 82.875, 94.875, 106.875 |
| end diagonal | 120.375 - 106.875 | **13.5"** |

Left run: nodes 49.875, 37.875, 25.875, 13.875, end vertex 0.375. First pocket on the left:
the end vertex (top, TrimEnd 3/8" thick on its left) hangs a right triangle on the bottom chord,
[0.375, 13.875 - 1.365] = **[0.375, 12.51]**.

Chase in PLAN: **x = 1.75 + 60.375 = 62.125"** (5'-2 1/8"), R1 x [54.125, 70.125]: 47" west of
the 18' trusses' (109.25"), and a bay-to-bay move of a lane from one to the other crosses a web.

Trimming only the stair end would take 23.25", over the 12" limit, so these five exist only by
trimming BOTH ends of the smallest stock that reaches (12'); longer stock only worsens it.

## 3. Grading a run (`grade_crossing`)

A run's centre must lie in an opening: TrimEnd passes nothing; D takes a round up to 5" (or
R2's 4 x 9 box); R1 takes a round up to 8" or a box up to 16 x 8. The run's whole outline
(an ellipse when round: width along the member = diameter / sin(angle to the truss line)) must
also sit inside the opening polygon, and a D pocket takes ONE run. Worked: a 4" round centred on
a pocket's incentre passes, a 5.5" round fails on size, and the same 4" round 1" from a diagonal
fails on outline.

## 4. FS-M-NE (TRIFORCE OJ, 215" = 17'-11")

Published (U.S. Specifier Guide 2023-05-11, read 2026-11-06): p.19 "Mechanical Clearances",
11 7/8": a 7 1/4" round, 5 3/4" square or 3" x 13" through the diagonal webs; p.4: 2x2
diagonals at "24" o.c. typ.", 14 3/16" at the end post, and ONE 34 1/8" OSB end panel,
trimmable up to 24", at either end (p.19: one round hole <= 1 1/2" in it, else Analyzer). The row
carries the round only and places no OSB panel, so the member is its own length, panel points
are 24" laid symmetric about mid-span (a bottom node at 107.5, so a pocket on the bottom chord is
centred 107.5 +/- 12), and the remainder falls in the two end diagonals. The strongbacks
(`params/main_deck.py`) sit in the two bottom-chord pockets either side of mid-span:
x = 215.25 + 107.5 +/- 12 = 310.75 and 334.75 (A nudged to 309.5 to clear `CD-B-PLAY-SPARE`).
The STATIONS are not TRIFORCE's drawing, so `mep.open_web_panel` reads this deck UNKNOWN.

## 5. What an assumed pitch may claim

Every pocket's station follows the pitch. Where `panel_pitch_assumed` is set, a deck whose runs
each hold their own pocket is UNKNOWN in `mep.open_web_panel`, never a PASS; a FAIL (a run on a
web, two runs in a pocket, a run over D's published size) still fails, since the router is
steered off the assumed webs and the size limits are published.

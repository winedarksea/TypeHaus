# Stair skirts — ST-M2S (2026-10-30)

Model: `TrimStandard.stair_skirt` (`plan/millwork.py`), painted poplar 1x12 (3/4" x 11 1/4").
Derived by `resolve/stairs/skirt.py`; landing base by `resolve/interior_trim_landing.py`.
Billed by the LF in `interior_trim` (`stair skirt`). `tests/test_stair_skirts.py` reproduces
§3–§5.

## 1. Decisions (owner)

- ST-M2S only: the oak U-stair with a level landing. ST-S2A's winders are out of scope.
- The skirt goes up first. Treads, risers and the side stringers butt it, so each moves
  3/4" inboard on a skirted side. The board's back face is the lane edge: 1/4" off W-M-C5's
  paint (a shim gap), 0.02" into W-M-STRW's.
- The landing takes the ordinary 3 1/2" base, not a level skirt.

## 2. Which sides

A lane edge is skirted where a main-floor wall's finish face lies within 1/2" of it, or the
generated well partition does. All four flight sides qualify:

| Board | Side | Backing | Run (y) |
|---|---|---|---|
| skirt-lower-right | east | W-M-C5 (310 → 397) | 310 → 383 1/8 |
| skirt-lower-left | west | W-M-WELL + partition (312 3/8 → 382 3/8) | 312 3/8 → 382 3/8 |
| skirt-upper-left | east | W-M-WELL + partition | 382 3/8 → 312 3/8 |
| skirt-upper-right | west | W-M-STRW (316.355 → 425.49), then the well edge | 396.511 → 312 3/8 |

The well edge (x 123 1/8) backs the board only where it stands in the second floor's depth
(above the joists' underside, 108 1/8"). That carries skirt-upper-right to the stairhead.

## 3. The profile, by hand

R = 120.55315 / 16 = 7.53457", going T = 10", nosing n = 1".

- θ = atan(R/T) = 36.999°. sec θ = √(1 + 0.753457²) = 1.25208.
- The nosing line runs through the tread nosings. At the first riser face it is
  R + n·R/T = 7.53457 + 0.75346 = **8.28803"** over the springing floor.
- The throat line (tread top meets the next riser face) is R(T + n)/T = **8.28803"** below
  the nosing line.
- The bottom edge is 1/2" below that: **8.78803"** under the nosing line.
- The vertical band is 11.25 × 1.25208 = **14.0859"**, so the top edge is
  14.0859 − 8.78803 = **5.2979"** above the nosing line. At the first riser face that is
  8.28803 + 5.2979 = **13.586"** above the floor.
- **Toe.** The top edge drops to the 3 1/2" base where 8.28803 + 0.753457·s + 5.2979 = 3.5,
  so s = −10.0859 / 0.753457 = **−13.386"**. That is 13 3/8" before the first riser face.
- **Foot.** The bottom edge meets the floor at s = (8.78803 − 8.28803) / 0.753457 =
  **+0.664"**. The foot is cut level from the toe to there.
- **Head.** It is cut plumb at the back of the head riser board: the landing edge
  (y 383 1/8) or the stairhead (y 312 3/8). The board is clipped flush with the second floor
  wherever no second-floor wall continues the face. W-S-BA-E1B continues W-M-STRW from
  y 316.24, so the west board steps down to the floor there, and the partition side is
  flush the whole way.

## 4. Cut lengths

The tread and riser stock is 42.4375 − 2 × 0.75 = **40.9375"** (40 15/16"). The stairhead
nosing is the same length. R311.7.1 still passes: 40.94" ≥ 36", with 38.11" clear past the
handrail.

The blank is long point to long point along the rake. For skirt-lower-left (s 0 → 70.0),
with z taken over the floor:

| Corner | s | z | (s + z·tan θ) / sec θ |
|---|---|---|---|
| floor, at the riser | 0 | 0 | 0 |
| top, at the riser | 0 | 13.586 | 8.175 |
| top, at the partition end | 70.0 | 13.586 + 70 × 0.753457 = 66.328 | **95.821** |

The blank is **95.821"**. The model gives 95.821, 98.657, 92.140 and 103.470, which is
32.5 LF over four boards. Two fit an 8' 1x12; the C5 board and the STRW board need a 10'.

## 5. Landing base

The landing walking face is z0 + 8R = 0.94685 + 60.27657 = **61.2234"**. Its ring is the
two decks' union (x 123 1/8 → 212 1/2, y 383 1/8 → 424 5/8), with each side snapped to the
wall face within 1": x 123.145 (STRW), x 212.74 (C5/C5B), y 425.49 (N2). The pieces are
butt-jointed as a room's base is: at an inside corner, the incoming piece runs to the far
face and the outgoing one butts it.

| Piece | From → to | Length | Ends |
|---|---|---|---|
| W-M-C5 | y 383.125 → 397.0 | **13.875"** | butts skirt-lower-right's head; C5B joint |
| W-M-C5B | y 397.0 → 425.49 | **28.490"** | runs to N2's face (inside) |
| W-M-N2 | x 211.99 → 123.145 | 89.595 − 0.75 = **88.845"** | butts C5B; runs to STRW (inside) |
| W-M-STRW | y 424.74 → 396.511 | **28.229"** | butts N2; dies into skirt-upper-right's toe |

There are four pieces, not three: W-M-C5 runs to y 397, past the landing edge. The main-floor
base also breaks at each skirt's footprint, so the base butts a toe that runs past the stair
outline. On catlin, no main-floor base reaches one.

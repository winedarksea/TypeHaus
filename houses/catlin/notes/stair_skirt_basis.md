# Stair skirts — ST-M2S (2026-10-30)

Model: `TrimStandard.stair_skirt` (`plan/millwork.py`), painted poplar 1x12 (3/4" x 11 1/4").
Derived by `resolve/stairs/skirt.py`; landing base by `resolve/interior_trim_landing.py`.
Billed by the LF in `interior_trim` (`stair skirt`). `tests/test_stair_skirts.py` reproduces
§3–§5; `tests/test_stair_framing.py` reproduces §6.

## 1. Decisions (owner)

- ST-M2S only: the oak U-stair with a level landing. ST-S2A's winders are out of scope.
- The skirt goes up before the oak. Its back is **scribed to the wall's finish face**, not
  the authored lane edge, and the treads and risers are cut to the board (owner, 2026-10-30:
  "move the edge to the wall"). Shimming the 1/4" lane gap at W-M-C5 was rejected: a finish
  carpenter nails a skirt tight to the studs and scribes it to the wall (Striegler, FHB), and
  fits the treads within 1/32" of it (WOODWEB). A shimmed board shows a gap along its top
  edge that needs caulk, and it can bow between the shims.
- Two partitions model the well wall: the authored W-M-WELL (the faces, x 165 11/16 and
  170 3/16) and the stair's generated partition (the studs). Since 2026-10-30 both are on
  x 167 15/16, midway between W-M-STRW's MDO and W-M-C5's gypsum, and the lanes are equal.
  The board scribes to the authored wall.
- A wall-carried side stringer stands a flat 2x4 spacer off the studs. There is no ledger
  beside it (§6).
- The landing takes the ordinary 3 1/2" base, not a level skirt.

## 2. Which sides

A lane edge is skirted where a main-floor wall's finish face lies within 1/2" of it, or the
generated well partition does. All four flight sides qualify:

| Board | Side | Backing | Run (y) |
|---|---|---|---|
| skirt-lower-right | east | W-M-C5 (310 → 397) | 310 → 383 1/8 |
| skirt-lower-left | west | W-M-WELL (312 3/8 → 382 3/8) | 312 3/8 → 382 3/8 |
| skirt-upper-left | east | W-M-WELL | 382 3/8 → 312 3/8 |
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

Each tread and riser runs between the two boards. Each board's back is on its wall's face:

| Flight | Faces (x) | Clear | Less 2 × 3/4" |
|---|---|---|---|
| upper | W-M-STRW MDO 123 1/8 → W-M-WELL 165 11/16 | 42.5625 | **41.0625"** (41 1/16") |
| lower | W-M-WELL 170 3/16 → W-M-C5 paint 212 3/4 | 42.5625 | **41.0625"** |

The stairhead nosing is in the upper lane, so it is 41 1/16" too. R311.7.1 passes: 41.06" ≥ 36",
with 38.24" clear past the handrail (41.0625 less the rail's 2.825"). The head landing grades
36" x 41.12". Before the scribe these were 40 15/16" and 38.11"; before the well was centred
(2026-10-30), 41 1/8" upper and 41" lower. The boards move across the
stair and not along it, so the blanks below do not change.

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
two decks' union (x 123 1/8 → 212 3/4, y 383 1/8 → 424 5/8), with each side snapped to the
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

## 6. The wall stringers: a 2x spacer, not a ledger

**Practice.**
- Reis, "Building Squeak-Free Stairs", JLC, Sept 2002: "To allow both drywall and the finish
  skirtboard to drop in behind the tread cutouts, the rough stringers should be indirectly
  bolted to the wall framing, held off by 2-by blocking". He ties them with 6" structural
  screws.
- Striegler, "A Step-by-Step for Trimming Stairs", Fine Homebuilding: the framers "leave a
  space between the outside stringers and the walls for the skirtboards to drop into". The
  skirt is nailed into the studs.
- No source describes a separate ledger standing beside a skirted stringer. The model's
  ledger lapped the C5 skirt by 1/4", and that lap was the only reason for the interference
  pardon, which is now gone.

**Geometry.** The spacer is a flat 2x4 (1 1/2" x 3 1/2") on the stud face, and the stringer
sits on it. The pocket is 1 1/2". It holds the 1/2" board plus the 3/4" skirt = 1 1/4", which
leaves 1/4" of air between the skirt and the stringer. The treads cover that gap: they end
at the skirt and overhang the stringer by 1/4".

| Wall | Stud face | Spacer centre | Stringer centre |
|---|---|---|---|
| W-M-C5 (lower) | 213 1/4 | 213.25 − 0.75 = **212.5** | 213.25 − 2.25 = **211.0** |
| W-M-STRW (upper) | 122 5/8 | 122.625 + 0.75 = **123.375** | 122.625 + 2.25 = **124.875** |

The spacer runs the stringer's bottom edge, starting where that edge leaves the floor. The
model draws a raked member's section plumb. On the lower flight the stringer's top line is
z = 7.4814 + 0.753457·s (s measured from the first riser face, y 312 3/8), and its bottom
edge is 11.25" below that line. The bottom edge clears the 0.94685" floor at
s = (11.25 + 0.94685 − 7.4814) / 0.753457 = **6.258"**, which is y 318.633.

| Spacer | y | Plan | Along the rake (× 1.25208) |
|---|---|---|---|
| W-M-C5 | 318.633 → 382.375 | 63.742" | **79.81"** |
| W-M-STRW | 319.5 (wall end) → 383.125 | 63.625" | **79.66"** |

The spacer is 3 1/2" tall. The stringer's top line stands R − t = 7.5346 − 1 = 6.5346" above
the throat line, and the skirt's bottom edge is 1/2" below the throat. So the spacer's top
runs 11.25 − 3.5 − 6.5346 − 0.5 = **0.715"** below the skirt's bottom edge along its whole
length. A real 2x12 is 11 1/4" deep square to its edge, which is 14.09" plumb, so on site
the gap is wider.

**Fasteners.** One 6" SDWS22 (SDWS22600DB) goes into each stud the spacer crosses. The
stringer and spacer make a 3" stack, which the plain shank spans, and all 3" of thread is in
the stud (ER-192 Table 1).
- W-M-C5: studs at y 320, 336, 352 and 368, so 4 screws.
- W-M-STRW: the corner at 320 and studs at 328, 344, 360 and 376, so 5 screws.
- **9 screws** in all.

The carriage still bears at both ends, so the screws only share the load. The worst case
puts it all on the C5 stringer's 4 screws:
- Tributary width: half the 18.2" clear tread span plus the 1/4" overhang, 9.35".
- Load: 52 psf × 9.35/12 ft × 70/12 ft = 236 lb, which is **59 lb a screw**.
- No Z for the SDWS22's 3" side-member row is transcribed. This is not an engineered item.

`structural.stair_stringer` reads the C5 stringer as carried full length: the spacer covers
it from where its foot leaves the floor to its head. The STRW spacer stops at the wall's end,
6 3/8" short of the stairhead, so that stringer is graded as a span (70" ≤ 72").

**Bill.**
- Lumber: two 2x10 ledgers out (70" and 63 5/8" of plan run), two 2x4 blocking spacers in
  (79.81" and 79.66").
- Hardware: two resolver-emitted LUS out (the stair ledgers on W-M-C5 and W-M-STRW, 9 → 7),
  9 SDWS22600DB in.
- The gypsum is still modelled continuous behind the spacer. On site it stops on the spacer,
  about 2 SF.

**Sequence** (`tasks.toml`, unchanged):
1. Framing: the framer sets the spacer at the stringer's bottom line (it is `blocking`).
2. Drywall: it stops on the spacer.
3. The skirt is scribed to the wall face.
4. The stair crew screws the stringer through the spacer, below the skirt, then sets the
   oak.

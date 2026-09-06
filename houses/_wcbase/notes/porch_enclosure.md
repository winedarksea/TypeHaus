# Porch enclosure — track, panels and the two seasons

**2026-09-03.** The porch's four outdoor curtain rods (`FURN-M-PORCH-ROD-W/-E/-SW/-SE`)
were replaced by four runs of snap-carrier aluminium curtain track carrying two seasonal
panel sets. This note is the part of that decision the model has no field for.

## Why the rods could not work

A rod at 8'-6" under a joist soffit at 9'-4 3/4" leaves a ~10" open band across the whole
opening, and curtain rings leak at the top by construction. A rod is a decoration; the
owner wanted an enclosure, and an enclosure seals at the head.

The rods were also 1 1/8" too high by the time they were replaced. Their comment claimed
8'-6" landed 1 1/2" under a balcony beam soffit of 8'-7 1/2" — true when the beams were
3-2x12, false after the 2026-09-03 glulam swap to 3.5x11.875 dropped that soffit to
8'-4 7/8". `FURN-M-PORCH-ROD-W` was clearing `BM-SG-BLW` by 7/8" and nothing graded it: a
placeable against a beam is as ungraded as a placeable against a column.

## The hardware

One elevation for all four runs, and it is the **balcony joist soffit**:

| quantity | derivation | value |
|---|---|---|
| balcony beam soffit | `_balcony_beam_soffit` = 10.0 − 7.25/12 − 11.875/12 | 8'-4 7/8" |
| **balcony joist soffit** | + 11.875" (the joists bear on TOP of the beams) | **9'-4 3/4"** = 112.75" |

`Mount.elevation` is the body bottom and the extrusion is 1" tall, so the four instances
carry `elevation=inch(111.75)` and the track's top lands flush on the soffit. Head rises
8'-6" → 9'-3 3/4".

Four runs, ~35 lf, two 90° curves at (9'-0", −9'-2") and (27'-0", −9'-2"):

| tag | run |
|---|---|
| `FURN-M-PORCH-TRACK-FW` | x 9'-0" → 17'-10", y −9'-2" |
| `FURN-M-PORCH-TRACK-FE` | x 18'-2" → 27'-0", y −9'-2" |
| `FURN-M-PORCH-TRACK-W` | y −9'-2" → −0'-6", x 9'-0" |
| `FURN-M-PORCH-TRACK-E` | y −9'-2" → −0'-6", x 27'-0" |

8' anodized sticks, splices, end caps and curves, screwed up through the stick's centre
groove — **5 screws per 8', the vinyl spacing, not mesh's 3**, because one set of hardware
carries both panel sets and the winter set is the heavy one. Snap carriers push into the
panel header; panels slide back and stack.

**Two front runs, not one.** `BM-SG-BLC` occupies z 8'-4 7/8"…9'-4 3/4" right across the
curtain plane at x 17'-10 1/4"…18'-1 3/4". A continuous front track would have to drop to
the beam soffit at 8'-4 7/8" — *lower than the rods it replaces* — and hang 9'-8" of track
on drop brackets with no backing. Two runs dying 1/4" off the beam faces put the seam on
`PT-SG-BF2`, which is where a seam belongs.

## The two panel sets

Both hang on the same track, the same carriers and the same snap studs.

- **Summer: no-see-um mesh.** Four panels, ~327 SF (2 × 8'-10" and 2 × 8'-8", all 9'-4").
- **Spring/autumn: 30-ga marine clear vinyl.** Same four openings, for wind chill rather
  than bugs, with YKK marine zippers at the corner joints.

Zippers are **not** the primary closure anywhere. UV and grit make a zipper the wear item,
and replacing one means re-sewing a panel. They survive only where the vinyl set needs a
rigid corner joint, which nothing else makes.

Construction, both sets:

- **Vertical edges:** marine snaps at 12–18" o.c., pulled down top-to-bottom so the webbing
  lies flat against the surface. 32 studs in all, bought with the mesh set.
- **Bottom:** a fibreglass rod in a hem pocket, corner snaps and elastic cords for
  side-to-side tension, and a vinyl floor sweep for the residual ~1".
- **Walk-through:** a magnetic seam in the **east flank at y ≈ −7'-6"**. That is the centre
  of `RL-SG-PORCH`'s 3'-0" guard opening (−6'-0" to −9'-0"), which is the porch's only route
  to grade via `ST-SG-PORCH`. Anywhere else and the enclosure's one opening does not line up
  with the porch's one exit. 8 magnets — the published count is 5 under 8' tall and these
  are 9'-4". Nothing in the engine will ask: `code.R312_1_guard_height` PASSes across that
  gap either way.
- Panels come down in minutes — unsnap, slide the carriers out, pull the rods, machine
  wash, store.

## The north end, and the honest limit

`_y_out_n` (−0'-10") is the porch deck edge; the house cladding face is at −0'-5". The 5"
between them is a deliberate insulation gap, open down to grade for the full 19'. **No
fastener in this whole assembly touches the house wall.** Two closures, both landing on the
garden structure:

1. **Track cantilever.** Each flank run goes past the deck edge to y −0'-6", the last 4"
   carried on a small aluminium outrigger screwed to the side of the rear beam. The beams
   are *not* lengthened — 4" of unsupported aluminium track under a curtain header is
   nothing, and moving a beam re-opens `cantilever.py` and its tests for no gain. Extending
   the beam is the fallback only if the outrigger will not land.
2. **`TR-SG-SLOT`**, ~19 lf of formed closure screwed to the porch deck's north rim,
   cantilevering 4" toward the cladding, sloped south to drain, with a compressible foam or
   brush lip bearing on the cladding without penetrating it. This kills the vertical bug
   path from the garden below.

The flank panels' north vertical edge is a weighted flap that lies against the cladding by
gravity — a sweep, not a fastened seal.

> **State it plainly: this is high bug reduction, not hermetic.** With a designed 5" gap and
> no permission to touch the wall, a contact sweep is the ceiling of what is achievable. It
> is also the correct wind-chill answer, since a compressible seal tolerates the
> differential movement a rigid one would tear itself apart on.

## Clearances — nothing in the engine checks any of these

`structural.member_interference` never sees a placeable. A track buried in a beam or a
column reports 0 FAIL. These numbers exist here and in the source comments and nowhere else.

Front runs (y −9'-2", z 111.75"…112.75"):

- `PT-SG-BF1`/`BF3`, 12" rounds, north face −9'-4" → **2" in y**, 6" in x.
- `PT-SG-BF2`, north face −9'-3 1/4" → 1 1/4" in y, and **no z overlap at all** — its top is
  the beam soffit, 11 7/8" below the track.
- `BM-SG-BLC` faces at x 17'-10 1/4" / 18'-1 3/4"; the runs end 17'-10" / 18'-2" → 1/4" each.
- `RL-SG-PORCH`'s south leg is on −9'-6", z 1"…43" → no z overlap, and the panel plane falls
  4" inboard of the 42" guard.
- `TR-SG-CAP-FRW/FRE` and their butyl sit on the front beams at −9'-6". The bottom-hem snaps
  at −9'-2" are 4" north of that cap. **Do not drift south** — anchoring through that cap is
  the one thing this house does not do.

Flank runs (x 9'-0" / 27'-0"): 6" clear of the rounds and of `RL-SG-PORCH`'s side legs,
9 7/8" clear of `BM-SG-BLW`/`BLE`, well inside the deck edge at 7'-3"/28'-9".

The front line moved from the rods' −9'-1" to −9'-2" for a reason that is not cosmetic:
−110" is the centreline of the first balcony joist behind the front rim
(`_y_balcony_front` −10'-6" + 16"), so the front runs screw straight up into 1 1/2" of
continuous KDAT for their whole length and need no blocking at all.

## Flank blocking — the bug path nobody would have seen

The flanks run **perpendicular** to the E-W balcony joists, so every 16" bay crosses the
curtain plane and is open inside↔outside above the track. Sixteen `JoistReinforcement`
blocks close them (`params/sunken_garden.py`, `_ENCLOSURE_BLOCK_LINES`) — the only
reinforcement on either garden deck answering an *envelope* joint rather than a structural
one. They resolve at the joists' full depth, land flush with the soffit, and inherit
`FS-SG-DECK.top_protection` butyl.

`plies=1` throughout: `_reinforcement_members` lays `range(plies - 1)` sisters, i.e. none.
**The trap** is that one entry lays a block in the bay on *each* side of its line, so the
entries go on every SECOND joist line — lines 1, 3, 5, 7 from the front rim fill bays 1…8
exactly once. Author all eight and every bay gets two blocks, which is a real
`structural.member_interference` FAIL. Lines 1/3/5/7 and not 2/4/6/8 because index 8 is the
rear rim at `max(joist y)` and every authored `at` must sit strictly inside the joist field.

One admitted waste: the line-1 entry's second block lands in bay 0–1, the balcony's front
overhang south of the front track — one per flank, doing nothing for the enclosure.

**8 entries, 16 blocks, 17.3 lf.** `FS-SG-DECK` blocking goes 4 → 20; sisters stay 0.

## Money

| line | where |
|---|---|
| track sticks, curves, splices, end caps, ~72 snap carriers, ~30 SS screws | `[placeables]` `FT-PORCH-TRACK-106` / `-104`, 2 ea each |
| mesh panel set + 32 snap studs, corner snaps, 8 magnets, hem rods, cords | `[allowances]` `porch-enclosure-panels-mesh` |
| 30-ga marine clear vinyl set + YKK corner zips | `[allowances]` `porch-enclosure-panels-vinyl` |
| `TR-SG-SLOT`, 19 lf | `[edge_trim]` `bug_screen` |
| 2x8 flank blocking, 17.3 lf | `[framing]` `2x8` (524 → 548 LF ordered) |
| butyl over those blocks | `[member_protection]` `butyl-tape` (403.5 → 420.8 LF) |

Anchor: Mosquito Curtains' published 3-sided, 39 lf heavy-mesh-plus-track example is $1,075.
Ours is ~35 lf of track but 9'-4" tall rather than ~8', so the areas are close.

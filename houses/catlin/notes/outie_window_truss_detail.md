---
title: "Outie Window in a Truss Wall — detail and build order"
applied_to:
  - detail: outie_window_truss_detail
  - assembly: CATLIN_EXT_2X6
  - assembly: PLANT_EXT_2X6_HUMID
  - transition: TR-CATLIN-FRAMED-OPENING
tags:
  - wall
  - window
  - insulation
  - air-barrier
  - water-management
  - sequencing
source:
  - plan/assemblies.py CATLIN_EXT_2X6
  - resolve/framing/truss_wall.py
  - emit/draw/detail_components/opening.py outie_window_truss
---

# Notes

## What the wall is

`CATLIN_EXT_2X6` is a **Swinburne truss wall** (2026-08-23). Outboard of the 2x6 studs and
their 1/2" plywood sheathing there is 4" of 2 lb closed-cell spray foam, and the cladding
stands off on an **intermittent wooden truss** rather than on furring screwed through boards:

| piece | what it is | where |
|---|---|---|
| block | 2x4 laid flat, long axis vertical, ~8" long | on the sheathing, over a stud, 0 → 1-1/2" |
| tab | 1/2" plywood | against the block's flush side face, 0 → 5" |
| outrigger | KDAT 2x4 **on edge**, 16" o.c. | lap-screwed to the tab, 1-1/2" → 5" |
| cladding | snap-lock standing seam | clipped to the outriggers, 5" → 5-1/2" |

The block is slid sideways so **one side face is flush with the stud's face**. That is the
only block position that lands the outrigger centred on the stud line, and it is what puts
two screws squarely over the stud. Centring the block instead throws the outrigger 3" off the
stud grid and breaks every window alignment below. Blocks go every ~40" up each outrigger.

The inner 1-1/2" of foam is a continuous band crossed by nothing but the blocks and the tabs.
The outer 2-1/2" fills between the outriggers; the 1" in front of it is the drained,
back-vented rainscreen gap the standing-seam clips land in, and it is what the bug screen at
the bottom of the wall closes.

## ** THE WRB IS GONE. THE FOAM IS THE WATER PLANE. **

There is no housewrap and no sheet membrane anywhere in this wall. Closed-cell foam is the
air barrier, the water barrier, the vapour retarder (4" ≈ 0.4 perm, Class II) and the
insulation in one bonded, seamless application. `plan/transitions.py` names `spray-foam-ext`
as the water and thermal continuity face for exactly this reason.

**That makes the build order part of the detail, not a preference.** A sheet WRB can be cut
and taped around an opening after the fact; sprayed foam cannot. So:

1. Frame the wall. Sheathe it. Cut the rough openings.
2. **Set the bucks.** 3/8" plywood lining each RO on all four sides, from the sheathing face
   out to the truss plane (5"), square and plumb. Non-structural — it closes the foam at the
   reveal, gives the reveal a face, and carries the pan and the head flashing.
3. Screw on the blocks. Lap-screw the tabs. Set the field outriggers and the jamb outriggers,
   then the head and sill blocking between them.
4. **Spray the foam** — around the truss, up to and against the bucks, in two lifts of the
   same visit. This is the moment the wall becomes weathertight, and every opening it has to
   seal against must already be framed and bucked.
5. Sill pan, window, head flashing, cladding.

Spraying before the bucks go in leaves a cut edge of foam at every reveal, which is a
discontinuity in the water plane that no sealant closes honestly. Do not do it.

## The window is OUTIE

The unit sits in the **truss plane, 5" outboard of the sheathing** — the same plane the
standing-seam clips land on — with its flanges bearing on the outriggers at the jambs and on
the head and sill blocking. It is not in the stud plane, and no window in this house carries a
depth dimension: the mount plane is derived from the outermost furring layer's outer face, so
it follows the assembly if the assembly ever changes again.

**Jamb bearing.** Outriggers sit on stud lines at 16" o.c., so their faces land 1/4" clear of
a 14", 30" or 38" RO jamb and the flange bears without help. The 18" and 27" RO families do
not reach one, and neither do the doors; those get a **jamb outrigger** over the jack stud,
with its own tab and block over the king beside it. This is derived, not authored:
`resolve/framing/truss_wall.py` adds them, and `structural.truss_wall_opening_support` FAILs
if any RO jamb ends up further than a flange's bearing (1") from wood. That check is what
keeps this paragraph true after the next window moves.

**Wide heads.** A head spanning more than 48" between flanking outriggers doubles up — two
plies of the KDAT 2x4 on edge. The 60" French and slider heads span about 63" and take it.

## Water at the head and the sill

Drawn by the `outie-window-truss` recipe
(`emit/draw/detail_components/opening.py::outie_window_truss`), which is a sibling of the
innie `window-head-jamb-sill` rather than a variant of it — the innie measures both pieces
from the sheathing face, and on this wall neither piece is anywhere near it.

- **Sill pan.** Lies on the sill buck, back dam turned up against the buck's inboard leg,
  running out to the truss plane and turning **down into the rainscreen gap**. It discharges
  *behind* the cladding. An outie pan carried out to a visible drip would put a metal lip
  under every window on the facade, which is not what this house looks like.
- **Head flashing.** Starts on the **foam face** above the head blocking — the foam is the
  water plane, so lapping onto it is what makes the head continuous — turns out over the head
  blocking, laps past the cladding and drips. Sealant at the cladding-to-frame joint sits at
  the truss plane, tucked under the drip.

The buck, the head/sill blocking and the outriggers are **not** drawn as convention linework.
They are resolved members, so the cut carries them as the solids they are; drawing them again
would be a second, disagreeing picture of the same wood.

## Why the change, honestly

Not R-value. By `analysis.assembly_r_value` the wall lands at **R-38.7** against R-36.8 for
the rigid-CI stack it replaced — about +5%, not the step change 4" of foam suggests, because
the outrigger's back 2-1/2" sits inside the foam and the engine parallel-paths it at a 9.4%
framing factor. That is the conservative 1D reading of a 2D detail; the wood is isolated from
the interior by 1-1/2" of foam and the sheathing, and a 2D calculation would be kinder. The
house's own `preferences.toml wall_r = 40` is still not met, exactly as it was not met before.
Code minimum is R-21, so there is no risk in either direction.

The case is **labour and trades**: no 537 eight-inch structural screws, no two-layer board
install, no separate WRB, one sprayer instead of three operations. The bridging improvement is
real but small, and saying so is the point.

**Open question, flagged not decided:** whether the outrigger needs to be KDAT at all. It sits
behind cladding, embedded in closed-cell foam, in a vented cavity — it never sees bulk water
and it never touches concrete. Plain SPF would price it at the ordinary 2x4 rate and save on
the order of $3,000–5,000 across 3,610 LF. `prices.toml` carries the treated spec, which is
the conservative one.

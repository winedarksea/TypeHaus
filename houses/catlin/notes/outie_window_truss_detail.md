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
  - resolve/framing/truss_frame.py
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
| outrigger | KDAT 2x4 **on edge**, 16" o.c. on the stud module | lap-screwed to the tab, 1-1/2" → 5" |
| filler | 1–4 plies of the same 2x4 | only at an RO jamb the grid misses, laminated to the outrigger's face |
| cladding | snap-lock standing seam | clipped to the outriggers, 5" → 5-1/2" |

The **outrigger is on the stud line** — its grid is the wall's own 16" framing module, laid
out from the same station 0 the studs are, with only the strip at each end of a band off it
(exactly as the end stud is). The block is then slid sideways so **one side face is flush
with the outrigger's**, which is the stud's face too: the block laps the stud's whole 1-1/2"
and both its screws land inside that lap. Centring the block instead throws it half off.

That is worth stating flatly because it was WRONG for a day (2026-08-23). The furring layout
started an on-edge strip at half its own width from the band's end rather than on the module,
so every outrigger in the house sat 3/4" off its stud, 806 of 1,285 blocks half-lapped, and
74 were screwed to nothing but 1/2" plywood. It is asserted now —
`packages/engine/tests/test_truss_wall_geometry.py`.

Blocks climb each outrigger at **no more than 40" o.c.**, one at each end of every run and
the rest spread evenly between — a run being a *segment*, so the piece above a window head is
its own stick with its own two. A block whose own elevation falls inside a rough opening it
laps in plan is skipped; the ones above and below it are ordinary wall and stay.

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

**Jamb bearing.** Outriggers sit on stud lines at 16" o.c., so a 14", 30" or 38" RO jamb
lands within a flange's bearing of one and needs no help. The others get one of two things,
and which one is a question of how much room there is:

| gap, RO edge to the nearest outrigger face | what goes in |
|---|---|
| ≤ 1" | nothing — the flange bears on the outrigger already there |
| 1" to 6" | a **filler**: one to four plies of the same 2x4 laminated to that outrigger's face, running the RO height between the sill and head blocking. It takes no block or tab of its own, because the outrigger it is nailed to has one |
| > 6" | a **jamb outrigger** over the jack, half an outrigger plus a tab outboard of the RO edge — the offset that lands its tab exactly ON the edge and its block over the king beyond, instead of half an inch of plywood in front of the glass. It carries its own pack |

Six inches is where a free member's pack stops colliding with the pack next door. Below it a
free outrigger ends up with **neither block nor tab** — which is what happened to 20 of the
21 jamb outriggers this detail first shipped with, every one of them the member a window
hangs its flange on and every one of them fastened to nothing.

All of it is derived, not authored: `resolve/framing/truss_frame.py` places it, and
`structural.truss_wall_opening_support` FAILs if any RO jamb ends up further than a flange's
bearing (1") from wood **that exists at that opening's own elevation** — an outrigger cut
around this very window is not wood at its jamb. That check is what keeps this table true
after the next window moves.

**Wide heads.** A head spanning more than 48" clear between the two jamb supports doubles up
— two plies of the KDAT 2x4 on edge. The 60" French and slider heads span about 60" and take
it. Where a tab genuinely stands in the run (a field outrigger cut at the head has its lowest
tab right there) the blocking is the pieces on either side of it, not one bay at the end.

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

The case is **labour and trades**: no two-layer board install, no separate WRB, one sprayer
instead of three operations, and **1,871 eight-inch structural screws through 4" of foam
replaced by 2,624 four-inch screws into a block bearing on the sheathing** — a shorter, easier
fastener that is not fighting compressible board. (The "537 screws" the first draft of this
note claimed was the ROOF's 10" count, which is untouched and still there.) The bridging
improvement is real but small, and saying so is the point.

**Open question, flagged not decided:** whether the outrigger needs to be KDAT at all. It sits
behind cladding, embedded in closed-cell foam, in a vented cavity — it never sees bulk water
and it never touches concrete. Plain SPF would price it at the ordinary 2x4 rate and save on
the order of $3,000–5,000 across 3,610 LF. `prices.toml` carries the treated spec, which is
the conservative one.

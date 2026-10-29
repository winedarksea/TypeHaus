# Egress door clear width and height — D-M-ENTRY (R311.1, R311.2)

Oracle for `code.R311_1_egress_door`, `code.R311_door_width` and `code.R311_2_door_height`
(`checks/code/mn_residential/egress_door.py`, decision #97, `plans/door-sizing.md`).

## The designated door

`D-M-ENTRY` carries `egress=True` (`plan/storeys/main.py`). It is exterior, side-hinged
(Therma-Tru Smooth-Star 3/0 x 6/8 inswing, composite frame) and opens from `RM-M-MUDROOM`, a
STORAGE room, which R311.1 allows: the egress door need not open from a habitable room. The
garage is detached, so no route to this door passes through it; the route itself is not graded.

## Published figures (they win)

Therma-Tru 2026 Arch 1.29–1.30, "Hinged Clear Opening", single, composite frame:

| slab | clear width at 90° |
|---|---|
| 2/8 | 29-5/16" |
| 2/10 | 31-5/16" |
| 3/0 | **33-5/16"** |

Clear height, 6/8 inswing composite: **79-1/4"** (outswing composite 78-7/16").

R311.2: 32" clear width, 78" clear height.

- Width: 33-5/16" = 33.3125" >= 32" — **PASS**, margin 1.31".
- Height: 79.25" >= 78" — **PASS**, margin 1.25".

A 2/10 slab would give 31-5/16" and FAIL, which is why the opening grew to the 3/0's RO
(38-3/8" x 82-1/2" published, 82-7/8" with the 3/8" pan allowance) rather than stepping down.

## The fallback, worked by hand

Without a published figure, `resolve/door_sizing` estimates the clear width as the leaf less a
flat 2-11/16", read off the same table: every row above is 2-11/16" under its slab
(32 − 29.3125 = 34 − 31.3125 = 36 − 33.3125 = 2.6875").

For a 3/0 leaf: 36" − 2-11/16" = 33-5/16" = 33.3125" — the published figure exactly, so the
estimate and the table agree at this size. A French pair loses it per leaf (5/0: 60 − 5-3/8 =
54-5/8", against the published 56-3/8"; the published figure wins there).

Clear height without a published figure is installed: RO head less the 1" jamb allowance and
the head stop's 13 mm (0.512") projection, less the higher of the threshold top and the floor
build-up. The threshold sits on its seat (`ExteriorDoorSillDesign.seat_height`, 0.5" default)
and stands `threshold_height` (1.5" here) over it, so 2.0" over the RO base; the floor is
0.947" (3/4" subfloor plus 5 mm LVP over the joist-top base). At D-M-ENTRY's 82.875" RO:
82.875 − 1 − 0.512 − 2.0 = 79.363". The published 79.25" is lower and governs; the estimate
lands 0.11" above it.

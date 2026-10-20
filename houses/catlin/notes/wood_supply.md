# Owner wood supply against demand — 2026-10-16

The owner's log pile, and what `haus millwork` asks of it after the red-oak reassignment
(the "white oak" was red oak). Demand is read off `haus millwork houses/catlin`, rough board
feet with its width and length allowances. **Supply is an estimate to replace with the
sawyer's tally**, not a measurement.

## How the gross volume is estimated

International 1/4" log rule, 8' logs, two 4' sections tapering 1/2", small-end diameter
taken as DBH − 2":

    BF = 0.905 × Σ (0.22 D² − 0.71 D)   over D and D + 1/2

Usable is ~75% of gross for heart defects and checking, ~60% for locust (heartwood only, no
sapwood). Large basswood and aspen often have hollow or rotten hearts, so their tally decides
the sauna.

## Supply against demand

| species | logs (DBH) | gross bf | usable bf | demand bf | flag |
|---|---|---|---|---|---|
| red oak | many | unlimited | — | ~1,490 | none; all oak window stools use bought white oak since 2026-10-18 |
| ash | 15", 12", 16" | ~144 | ~108 | ~120 (table 52, counters 46, five living-room stools 22) | **short: source one more ash log.** Boards run to ~11" (quartered ~4–6"), so the counters, table and stools are all glue-ups; the 160 5/8" slab needs a 14'+ log |
| locust | 12", 14" | ~73 | ~44 | ~29 (sauna base 10, five stools 11, bath shelf nosings and face strips 9) | covered without the extra logs: bath shelves use plywood with locust nosings, and all kitchen stools are quartz (2026-10-18). Fallback for the nosings: `cherry-shelf-4q`, then bought white oak |
| elm | 20", 20" | ~218 | ~164 | ~209 (slats 111 on 8/4, mantel 13, posts 85), plus ~28 slat overage | **short: one more elm log.** The slats mill ~25% extra to reject movers; the posts need 10'+ logs; more elm is easy to get |
| cherry | unknown | — | — | suite stools and bedroom-face door casing only | Confirm the stack against the current millwork schedule. Base is bought painted pine (2026-10-19); headboard is bought MDF and S4S poplar (2026-10-20), removing the former ~65 bf wainscot demand. |
| white oak (bought) | — | — | — | ~54 (19 stools, 5/4) | order ~60 bf of 5/4, select heartwood widths of 11"+; includes hall/stair stools since 2026-10-18 for condensation resistance |
| cedar (owner) | "a little" | — | — | ~12 (sauna door casing 10, the stool 2) | clear heartwood, no knots; **confirm "a little" covers three 8' boards**, else the casing goes back to locust (one line in `plan/millwork.py`) |
| basswood | 24", 17", 16" | ~304 | ~228 | ~315 (wall liner 257, bench slats 57) | see below |
| aspen | 16", 12" | ~91 | ~68 | ~79 (the ceiling liner) | see below |
| willow | 14.5" | ~48 | ~36 | none since 2026-10-18 (was the ceiling) | not used in the sauna |
| Douglas fir (bought) | — | — | — | ~25 bearers + ~30 allowance (legs, stretchers, recliner, heater fence) | bought KD 2x4/4x4; off `haus millwork` |
| walnut (bought) | — | — | — | ~79 | bought, priced in `[placeables]` |

## The sauna is about 120 bf short

Since 2026-10-18 the frame is bought Douglas fir and the ceiling is aspen; willow is out.
Basswood and aspen together: ~395 bf gross, ~296 usable, against ~414 of owner-stock demand
(liner 336, bench slats 57, and a ~20 bf margin for picking the clearest slat stock). That
is one more basswood or aspen log of about 24" (~169 gross, ~126 usable), or two of 18–20"
(~63–82 usable each). Allocation by job puts the best wood where skin touches it: the
clearest basswood (mostly off the 24" log) to the bench slats (clear aspen is equal), the
aspen to the ceiling, the rest of the basswood and the new log to the walls.

## What to replace

Every gross and usable figure here, once the sawyer has the logs on the mill. Then set the
ash and locust `max_board_width_in` (`plan/assemblies/materials_hardwood.py`, 11" and 7"
today) to the widest board the tally shows, and `haus millwork` re-plans the glue-ups.

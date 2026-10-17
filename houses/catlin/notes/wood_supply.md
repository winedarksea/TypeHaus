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
| red oak | many | unlimited | — | ~1,496 | none |
| ash | 15", 12", 16" | ~144 | ~108 | ~120 (table 52, counters 46, five living-room stools 22) | **short: source one more ash log.** Boards run to ~11" (quartered ~4–6"), so the counters, table and stools are all glue-ups; the 160 5/8" slab needs a 14'+ log |
| locust | 12", 14" | ~73 | ~44 | ~78 (sauna trim 19, seven stools 14, bath shelves 44) | **needs the owner's extra 2–3 logs.** Without them the bath shelves go to `cherry-shelf-4q`, then bought white oak (one line each in `plan/millwork.py`) |
| elm | 20", 20" | ~218 | ~164 | ~213 (slats 114, mantel 13, posts 85) | tight; the posts need 10'+ logs; more elm is easy to get |
| cherry | unknown | — | — | ~246 (base 175, suite wainscot 65, suite stools 6) | confirm the stack |
| white oak (bought) | — | — | — | ~48 (17 stools, 5/4) | order ~55 bf of 5/4, select widths of 11"+ |
| cedar (owner) | "a little" | — | — | ~2 (the sauna stool) | clear heartwood, no knots |
| basswood | 24", 17", 16" | ~304 | ~228 | ~315 (wall liner 257, deck slats 57) | see below |
| aspen | 16", 12" | ~91 | ~68 | ~25 bearers + ~30 allowance (posts, stretchers, recliner, heater fence) + wall make-up | see below |
| willow | 14.5" | ~48 | ~36 | ~79 (the ceiling liner) | aspen makes up the rest |
| walnut (bought) | — | — | — | ~79 | bought, priced in `[placeables]` |

## The sauna is about 100 bf short

Basswood, aspen and willow together: ~443 bf gross, ~332 usable, against ~471 of demand
(liner 336, deck slats 57, bearers 25, the ~30 bf framing allowance, and a ~20 bf margin for
picking the clearest slat stock). That is one more basswood or aspen log of about 18–20",
which the owner says is available. Allocation by job puts the best wood where skin touches
it: the clearest basswood (mostly off the 24" log) to the deck slats, the rest of the
basswood and the aspen to the walls, the willow to the ceiling only.

## What to replace

Every gross and usable figure here, once the sawyer has the logs on the mill. Then set the
ash and locust `max_board_width_in` (`plan/assemblies/materials_hardwood.py`, 11" and 7"
today) to the widest board the tally shows, and `haus millwork` re-plans the glue-ups.

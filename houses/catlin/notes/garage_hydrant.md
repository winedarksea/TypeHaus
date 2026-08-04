---
title: "Garage Frost-Free Hydrant and Wash-Down Area"
applied_to:
  - fixture: FX-G-HYDRANT
  - fixture_type: FX-HYDRANT-Y34SS
tags:
  - garage
  - plumbing
  - water-supply
  - freeze-protection
  - drainage
source:
  - plan/fixtures.py
  - plan/fixture_types.py
  - plan/mep.py
  - params/foundations.py
---

# Notes

## What this is

A frost-free wall hydrant on the garage's west wall near the NW corner (x 1'-6", y 62'),
for washing a vehicle down and for anything else a hose reaches. It is the project's first
`PipeSystem.WATER_COLD` run — everything authored before it is drain or vent.

## Why there is no floor drain

**Deliberate.** A garage floor drain is a sanitary connection carrying road salt, oil and
whatever came off the vehicle, and most jurisdictions here either prohibit it outright or
require an oil/sand interceptor and a discharge permit that a single-family garage will not
get. The alternatives are worse rather than better: a drain to daylight becomes a frozen
plug by December, and a drain to the sanitary system is the thing the code is objecting to.

So the floor is poured to fall toward the overhead door instead, and the wash water leaves
the building the way it came in — across the apron and into the gravel pit outside the west
wall (`DRW-G-HYDRANT`). The pit is a `Drywell`: 3' of fabric-wrapped washed stone, 3' across,
centred 3' outside the west wall line so the excavation clears the footing.

It was modelled as a locally deepened `FootingBedding` for as long as that was the closest
thing the model had. The stand-in cost something real: a bedding's perimeter bills as
perimeter drain tile, so the sitework take-off was ordering a ring of tile around a soakaway
that has none.

**Consequence to accept:** in deep winter the wash water will not soak away — it will freeze
where it lands. That is the trade the no-floor-drain decision makes, and it is the right one:
a seasonal inconvenience beats a permanent illicit discharge.

## Freeze protection

The hydrant's shutoff valve sits **6'-0" below grade** — `PR-G-HYDRANT-CW` runs at −6'-0"
absolute for its whole 65'-6" length, from the house water entry at (5', 0') out to the
hydrant. That is a different number from `_FROST` (42") in `params/foundations.py`, and the
two are consistent rather than in conflict: 42" is the *footing* frost depth the ICF stem is
set to, and 6'-0" is this fixture's own bury, 2'-6" below the stem bottom and well clear of
the frost line.

The run is deliberately **not** routed up into the garage and back down to the hydrant. A
supply line freezes at its high point, not at its ends, so a run that surfaces anywhere along
its length is not frost-protected no matter how deep both ends are. `mep.hydrant_freeze_depth`
checks both: the bury at the shutoff, and that no point along the run rises above it.

## The pedestal, and why there isn't one (2026-08-03)

There was one: `SL-G-HYDRANT-PED`, an 18" square, 4" thick, poured on top of `SL-G-FLOOR`,
with its own block-out sleeve `SP-G-HYDRANT-PED`. Its job was to put the slab penetration and
its sealant joint **above the wet line** — a garage floor here runs salt slush from December
to March, a sleeve entry at slab level sits in that slush all winter, and the joint is the
first thing to fail.

**Retired by owner decision.** The hydrant does not need a dedicated slab; it stands on the
garage's own floor slab like everything else in the room, and a 4" block in the middle of a
floor that is swept, driven around and poured to fall toward the overhead door is its own
nuisance. What the pedestal was buying is now bought by specification instead: a flexible,
chloride-tolerant sealant at the penetration, on the maintenance list rather than designed
out. **Consequence to accept:** that joint sits in the wet line and will want re-doing
sooner than a joint 4" above it would.

Nothing below grade changed, and that is where the freeze protection actually lives — the
6'-0" bury, `SP-G-HYDRANT` through the slab, and the `DRW-G-HYDRANT` stone the barrel weeps
into when the handle closes. Those are the system; the pedestal never was.

## Where the hydrant sits

On `SL-G-FLOOR` at 0'-0", which is **1'-10" below the `garage` storey datum** — that datum
is the ICF stem top the wood walls bear on, not the floor (→ `CLAUDE.md`). No source file
states the offset. `resolve/placeables.py` measures every mount off the floor of the room the
placeable is in, via `resolve/room_floor.py`, and for `RM-GARAGE` that resolves to the slab.

It measured off the *storey datum* until 2026-08-03, which stood this hydrant — and the
workbench, and every receptacle, switch and light in the garage — a flat 22" higher than
authored. `room_floor_elevation` already existed and already knew the answer; it just lived
in `emit/` and only the two emitters called it, so the viewer drew the floor in the right
place and the things standing on it in the wrong one.

## Specified with the fixture

Both are recorded on `FX-HYDRANT-Y34SS`'s `source` and belong on the plumbing schedule; the
model has no valve or backflow-preventer element, so `mep.hydrant_freeze_depth` reports them
UNKNOWN rather than claiming a review it did not perform.

- **Supplemental epoxy coating** over the buried barrel. The standard finish is not rated for
  chloride immersion and this barrel passes through the salt layer twice a year.
- **Hose-bib vacuum breaker** screwed onto the outlet — required backflow protection for any
  hose connection, and the cheapest part of the whole assembly.
- **Interior shutoff** downstream of the slab penetration, so the run can be isolated without
  digging.

Sealant at the slab penetration is a flexible, chloride-tolerant joint sealant, not a rigid
grout: the barrel and the slab move against each other seasonally. With the pedestal gone
this joint is the only thing between the salt slush and the sleeve — see above.

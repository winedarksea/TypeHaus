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
wall (`FB-G-HYDRANT-PIT`). The pit is modelled as a locally deepened bedding on the garage's
west footing, which is what it physically is: the same washed stone on the same non-woven
geotextile as every other footing bedding on the project, dug 3' further down and given a 4"
sock-wrapped drain tile to daylight. `FootingBedding` is the closest thing the model has to
a drywell, and it already carries undercut / geotextile / `DrainTile`.

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

## The pedestal

`SL-G-HYDRANT-PED` — an 18" square, 4" thick, poured on top of `SL-G-FLOOR`. Its job is to
put the slab penetration and its sealant joint **above the wet line**. A garage floor here
runs salt slush from December to March; a sleeve entry at slab level sits in that slush all
winter, and the joint is the first thing to fail. Four inches is enough to clear it.

It is authored as a `Slab` with `datum="walking_surface"`, not a `Pad`: a `Pad` is an
isolated footing bearing on soil, which is how `structural.frost_depth` reads it — correctly,
since a pad at 0'-0" really would be a footing above the frost line. This is a topping pour
on an existing slab.

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
grout: the pedestal and the slab move against each other seasonally.

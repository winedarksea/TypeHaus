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

A frost-free **yard** hydrant standing on the garage slab at (x 5'-0", y 60'-0"), for
washing a vehicle down and for anything else a hose reaches. It is the project's first
`PipeSystem.WATER_COLD` run — everything authored before it is drain or vent.

It is not a *wall* hydrant, and it does not stand against a wall either — see "Why it
stands in the floor" below. The two south-face hydrants (`FX-M-PORCH-HYD`,
`FX-S-BALC-HYD`) are the wall kind; the difference is the whole design, and
`mep.hydrant_freeze_depth` grades the two families on different rules.

## Why there is no floor drain

**Deliberate.** A garage floor drain is a sanitary connection carrying road salt, oil and
whatever came off the vehicle, and most jurisdictions here either prohibit it outright or
require an oil/sand interceptor and a discharge permit that a single-family garage will not
get. The alternatives are worse rather than better: a drain to daylight becomes a frozen
plug by December, and a drain to the sanitary system is the thing the code is objecting to.

So the floor is poured to fall toward the overhead door instead, and the wash water leaves
the building the way it came in — across the apron, onto the driveway. Nothing catches it
and nothing is meant to.

**`DRW-G-HYDRANT` is not that catch basin.** It is a weep pocket: 1'-6" of fabric-wrapped
washed stone, 1'-6" across, buried on the hydrant's own stack from -5'-6" to -7'-0", taking
the few quarts the Y34 self-drains through the weep hole at its shutoff each time the handle
closes. It is a `Drywell` because that is the model's aggregate-filled-hole type, not
because a soakaway's worth of water reaches it.

**Consequence to accept:** in deep winter the wash water will not soak away — it will freeze
where it lands. That is the trade the no-floor-drain decision makes, and it is the right one:
a seasonal inconvenience beats a permanent illicit discharge.

## Freeze protection

The hydrant's shutoff valve sits **6'-0" below grade** — `PR-G-HYDRANT-CW` runs at −8'-10"
absolute (6'-0" under the −2'-10" grade) for its whole 24'-0" length, from the house's north
foundation at (5', 35'-6") straight north to the hydrant. That is a different number from
`_FROST` (42") in `params/foundations.py`, and the two are consistent rather than in conflict:
42" is the *footing* frost depth the ICF stem is set to, and 6'-0" is this fixture's own bury,
2'-6" below the stem bottom and well clear of the frost line.

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

## Why it stands in the floor (2026-08-15)

It was at (1'-6", 62'), tucked into the NW corner against the west wall, and that position
was not buildable.

The garage footings bear at −4'-2". The shutoff is 6'-0" down. So everything at the valve
sits **22" below the bearing plane**, and IRC P2604.3's 45° influence line then asks for 22"
of lateral clearance from the footing edge before the excavation stops loading the footing.
The weep stone goes deeper still and needs 34". At x = 1'-6" the riser had 8", and the stone
pocket — 2' across and 4' deep, as it then was — **overlapped `FT-GF-W`'s footprint by 4" in
plan and reached 4'-10" below its bearing.** That is a pit dug under the footing edge.

None of it was being caught. `mep.footing_clearance` walks pipe runs, so the pocket was
graded by nothing at all. The riser was graded, and passed, on `SP-GF-W-HYD` — a sleeve
authored at (0'-9.6", 61'-6") that bored `FT-GF-W`'s full 20" width east-west at the 6' bury
while the pipe ran *parallel* to that footing 8" away and never crossed it. The check asked
only that some sleeve on the pour sit within 0.3 m of the encroaching segment; 8.4" is
0.213 m. It drew a real hole through concrete with nothing in it. Deleted.

**There is no wall position in this garage that works.** The footing runs the full perimeter
and the binding constraint is the fixture's own bury, not its plan location: the clear zone
is x ≥ 4'-8", y ≤ 60'-4", which is floor. So the hydrant stands free, as a yard hydrant is
built to.

x = 5'-0" rather than the 4'-8" minimum because it is the line the service runs on — the
service enters the lot at x = 5'-0" and the lateral goes south from here to the house,
through `SP-GF-S-HYD` under the garage footing and `SP-B-N3-HYD` through the basement's north
wall, so standing the fixture on it makes the run dead straight.

The hydrant stands **on the service entry itself**, not at the far end of a line drawn
across the house. That is the ordinary arrangement for a yard hydrant, and it is what makes
the "deliberately not routed up into the garage and back down" argument above cheap to
honour: there is barely any run left to rise.

y = 60'-0" leaves the stone pocket 41" clear of `FT-GF-N` against the 34" it needs.

**Consequence to accept:** the hydrant is a post standing 5' out from the west wall at the
front-left of the north bay, not a fitting on a wall, and it is in the parking area because
every compliant position in this garage is. A bollard or a wheel stop is the mitigation if
it proves to be in the way. Moving it back to the wall is not.

The one crossing that remains is `PR-G-HYDRANT-CW` passing *beneath* `FT-GF-S-DR` at the
service door, and that one is sleeved rather than spaced — being under a footing is not
clearance from it, since the 45° cone opens downward and a pipe on the footing's own
centreline is the worst case in it.

## Where the hydrant sits

On `SL-G-FLOOR` at 0'-0", which is **1'-10" below the `garage` storey datum** — that datum
is the ICF stem top the wood walls bear on, not the floor (→ `CLAUDE.md`). No source file
states the offset. `resolve/placeables.py` measures every mount off the floor of the room the
placeable is in, via `resolve/room_floor.py`, and for `RM-GARAGE` that resolves to the slab.

## Specified with the fixture

The coating is recorded on `FX-HYDRANT-Y34SS`'s `source` and belongs on the plumbing
schedule. `PipeAccessory` is the element, `PA-G-HYD-SEAT` and `PA-G-HYD-VB` are the
instances, and `mep.hydrant_freeze_depth` grades them as a PASS.

- **Supplemental epoxy coating** over the buried barrel. The standard finish is not rated for
  chloride immersion and this barrel passes through the salt layer twice a year.
- **Hose-bib vacuum breaker** screwed onto the outlet (`PA-G-HYD-VB`, ASSE 1011) — required
  backflow protection for a hose connection, and the cheapest part of the whole assembly.
  It answers the *hose thread*, and only that; see below.
- **Interior shutoff** downstream of the slab penetration (`PA-G-HYD-SEAT`), so the run can
  be isolated without digging.

## The weep, and why this is still a Y34

The short version: **the standard draining yard hydrant stays**, and a
dual check on its branch closes the one gap it has.

`PA-G-HYD-VB` protects the hose thread, which is the opening the code names — P2902.3.1
wants a vacuum breaker at every hose connection on a potable line and there is one. A
self-draining yard hydrant has a second opening: the weep at the buried shutoff, which
empties the barrel into `DRW-G-HYDRANT`'s stone every time the handle closes and then sits
in wet stone at -6'-0". A breaker 2'-6" above the slab is nowhere near that path.

**That is a real opening, and it is not a code violation.** Two reasons:

- On a Y34 the drain port is uncovered only when the plunger is seated, and the plunger
  covers it as soon as the valve opens. The weep and the supply are never both connected in
  normal operation. Backsiphonage through the weep needs a worn seat **and** a submerged
  weep **and** negative pressure in the main, all at once.
- Nothing in the IRC or in the Minnesota plumbing code prohibits this fixture or requires a
  listed sanitary one for a single-family yard hydrant. ASSE 1057 "freeze-resistant sanitary
  yard hydrant" exists and some cross-connection-control programmes specify it, but that
  history is agricultural — livestock tanks and chemical mixing, where the hose end is the
  documented failure and a hose-in-tank siphon is the documented mechanism. This one washes
  a car in a garage, and its weep pocket is under the garage slab rather than in a barnyard.

So the fixture is not the thing to change. What is worth having is cheap insurance against
that three-way coincidence, and that is `PA-G-HYD-BFP`: a 3/4" dual check on
`PR-G-HYDRANT-CW` at (5'-0", 3'-0"), in `RM-B-FURNACE` beside `PA-B-MAIN-SHUTOFF`.

It is on the branch rather than at the fixture because the branch is the only place a device
can be reached. The hydrant's own seat is 6'-0" down in the yard; the tee that feeds the
house is at (5', 1') and everything past it is buried. But between its three basement wall
sleeves the run crosses the heated basement exposed at the -6'-0" bury, and -6'-0" absolute
is **3'-0" above the basement floor** — head height in the mechanical room. No `elevation` is
authored on the accessory because a check valve on a pipe sits on the pipe.

A dual check, not an RPZ, because this is a low-hazard residential connection; it matches
`PA-B-BFP-BATH` and `PA-B-BFP-SAUNA`. An AHJ that reads a below-grade weep as a *health*
hazard would want an RPZ, which needs a drain and an annual test. That is a question for
permit review, not something to build for ahead of the answer. -> `plans/TODO.md`.

**How the check reads it.** `mep.backflow_prevention` grades the **connection**: the outlet
and the run that feeds it are one thing, and every guard device on the feed lands in the
fixture's own finding.

    FX-G-HYDRANT's hose thread is protected by PA-G-HYD-VB (screw-on hose-bib vacuum
    breaker, ASSE 1011), and its branch (PR-G-HYDRANT-CW) carries PA-G-HYD-BFP (3/4"
    dual-check backflow preventer, testable)

The two wall hydrants carry no branch device and say so by omission. Nothing in the check
knows what a weep is, and nothing needs to — the rule stopped discarding the rest of the
branch, which is what made the weep's answer invisible. The same pass gave `serves` a
grader it never had: a device naming a tag the model does not contain now FAILs rather than
passing on its own say-so.

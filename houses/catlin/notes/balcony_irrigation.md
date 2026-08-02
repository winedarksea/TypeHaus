---
title: "South-Face Wall Hydrants — Porch and Balcony Irrigation"
applied_to:
  - fixture: FX-M-PORCH-HYD
  - fixture: FX-S-BALC-HYD
  - fixture_type: FX-HYDRANT-SD34
tags:
  - plumbing
  - water-supply
  - freeze-protection
  - envelope
  - thermal-bridge
  - balcony
  - porch
source:
  - plan/fixtures.py
  - plan/mep.py
  - library/placeables/fixtures.py
  - preferences.toml
---

# Notes

## What this is

Two frost-free wall hydrants on the house's south face, one per outdoor room:

| tag | storey | wall | x | handle | serves |
| --- | --- | --- | --- | --- | --- |
| `FX-M-PORCH-HYD` | main | `W-M-S1` | 12'-0" | 2'-0" over the porch deck | the porch, and anything a hose reaches at grade |
| `FX-S-BALC-HYD` | second | `W-S-S1` | 16'-8" | 2'-0" over the balcony deck | the balcony's plants — the irrigation this whole item started as |

Both are on the south face because that is where the outdoor rooms are. The freestanding
sunken-garden structure carries the porch at 0'-0" and the balcony 10' above it, and its
north edge stops 5" short of the house cladding — so a hydrant on this wall is at arm's
length from the deck in front of it.

**There is no north-face hydrant, by decision (2026-08-01).** `FX-G-HYDRANT` already stands
on the garage's west wall at (1'-6", 62'), 26' off the house's north-west corner, and it
reaches everything a third hydrant would have. Adding one would have meant a fourth
envelope penetration for a second hose on the same side of the property.

## Two ways to make a hydrant frost-free, and this is the other one

`FX-G-HYDRANT` is a **yard hydrant**: its seat is 6'-0" down, below the 42" frost line, and
the barrel drains back to it. That is what `mep.hydrant_freeze_depth` grades, and it is the
only strategy available to a hydrant standing in the middle of a garage floor.

These two are **wall hydrants**. The seat is at the *inboard* end of an ~10" barrel, inside
the conditioned envelope, and the barrel pitches outward so it empties itself the moment the
handle closes. There is no bury depth because there is no bury — grading them against 72"
would be measuring them against a strategy they do not use, which is why
`mep.hydrant_freeze_depth` exempts them and hands them to
`mep.exterior_hydrant_protection`.

**They are not winterised.** No shutting down in October, no draining, no remembering. That
was the owner's requirement and it is what picks this fixture class.

## The penetration is the design

A metal tube running from outside air to inside air is a thermal bridge, and on a wall this
good it is *the* thermal bridge. Three things answer it, and all three are billed:

1. **PEX at the seat.** The supply stops being metal the moment it is inboard of the
   hydrant. `PR-M-CW-PORCH-HYD` / `PR-M-CW-BALC-HYD` are PEX; only the barrel legs
   (`PR-M-CW-PORCH-HYD-CU`, `PR-S-CW-BALC-HYD-CU`) are copper, and they are 10" long.
   Continuing in copper inboard would extend the bridge into the room.
2. **A sleeve over the barrel** — 1/2" closed-cell elastomeric, foil-faced. It is authored
   as `PipeRun.insulation` on those two copper legs, which is what puts it in the
   `pipe_insulation` BOM section by the foot.
3. **The hole itself**, sealed: a silicone gasket under the escutcheon, a non-conductive
   plastic mounting bracket (a steel one would short the break the gasket just made), and
   closed-cell spray foam in the 1/4" annulus. Those three ride `install_parts` on
   `PA-M-PORCH-HYD-SEAL` / `PA-S-BALC-HYD-SEAL` and bill individually — nobody stocks them
   as "a hydrant", and the same hydrant through a different wall takes a different kit.

`CATLIN_EXT_2X6` is what makes any of this safe. It carries 4" of continuous exterior
insulation (2" polyiso + 2" EPS) *outboard* of the sheathing, so the stud cavity holding
the seat and its feed sits on the warm side of the whole thermal break. In a cavity-only
wall the same detail freezes.

## Why both are fed from above

A wall hydrant is fed from inside, so the pipe reaching it has to arrive inside the stud
cavity — and on this house a supply cannot get into an exterior cavity from below. The
main-storey stud bay sits at y 1/2"–6" off the sheathing plane, and directly under it stands
`W-B-S1`: 12" of cast concrete spanning y 0"–12". A riser through `SL-M-DECK` into that
cavity would come up through the top of a bearing wall. The same is true of `W-M-C1` over
`W-B-CS` on the centre line.

So both hydrants are fed **out of the second floor's joist space**, which is framed
(`FS-SECOND`, 11 7/8" I-joists at 16" o.c.) and reaches every exterior wall in the building.
One branch does the whole job:

```
PR-B-CW-TRUNK  (5', 1') .. (29', 16')      the 1 1/4" cold trunk, basement ceiling
   |  tee at (6', 16')                      PA-B-HYD-ISO — the one valve that reaches both
PR-B-CW-HYD          -> (6', 13'-4")        lacquered copper, exposed under the deck
PR-B-CW-HYD-RISER    up through SP-M-CW-HYD, inside W-M-BDN1, to 9'-3"   PEX
PR-M-CW-HYD-DIST     south to y=0'-9", then east along one joist bay     PEX
   |-- PR-M-CW-PORCH-HYD   down inside W-M-S1 to 2'-0"     -> PR-M-CW-PORCH-HYD-CU  (barrel)
   `-- PR-M-CW-BALC-HYD    up   inside W-S-S1 to 12'-0"    -> PR-S-CW-BALC-HYD-CU   (barrel)
```

Three numbers in there are not free choices:

- **`SP-M-CW-HYD` at (6', 13'-4")** is over open basement ceiling — `W-B-SA-N`, the sauna's
  north partition, starts at x=8'-10" — so the deck penetration lands in slab rather than on
  a wall below it. Nothing else crosses within 3'.
- **The riser splits at 9'-0"**, the top plate of `W-M-BDN1`. Main-storey partitions stop
  there; the joist bay above runs 9'-0 1/8" to 10'-0". A riser drawn straight from the deck
  to the bay escapes its declared wall by 3", which is exactly what
  `mep.wet_wall_occupancy` caught the first time it was tried.
- **`PR-M-CW-BALC-HYD` splits again at 10'-0"**, the second floor. Below that line the pipe
  is crossing the deck and hosted by nothing; above it, it is inside `W-S-S1`, whose extent
  starts there.

The east–west leg at y=0'-9" runs *along* a joist bay. The leg that gets there from the
riser crosses joists at x=6' and is drilled through their webs — 3/4" PEX in an 11 7/8"
I-joist web, inside every manufacturer's hole chart, and part of why that stretch is PEX
rather than the copper it is downstairs.

## Sizing

2.5 WSFU each (hose bibb, Table 610.3). The cold trunk went 34 → 39 WSFU, against the 64 a
1 1/4" branch carries in Table 610.4's 46–60 psi / <100' column, so the tee cost nothing:
no pipe was upsized and `SP-B-CS2-CW` did not have to grow. `PR-B-CW-HYD` and everything
downstream of it is 3/4" at 5 WSFU.

## What each hydrant carries

Three `PipeAccessory` records apiece, and the reason they are elements rather than a
sentence in this file is that the sentence was the previous state of the art —
`mep.hydrant_freeze_depth` used to emit an UNKNOWN reading *"the model has no valve or
backflow-preventer element, so neither can be evaluated here."*

- `…-SEAT` — `SHUTOFF`. The hydrant's own compression seat at the inboard end of the barrel.
  This is the shutoff; there is no second one at the fixture.
- `…-VB` — `VACUUM_BREAKER`. Integral anti-siphon, ASSE 1052. A hose thread on a potable
  line is the textbook cross-connection and P2902.3.1 is not optional about it;
  `mep.backflow_prevention` grades each hydrant against the breaker on *its own* feed, so
  three hydrants and one breaker would fail two of them.
- `…-SEAL` — `PENETRATION_SEAL`, carrying the three install parts above. This is also the
  element that *declares* the hydrant envelope-protected: it names the fixture in `serves`,
  and that naming is what exempts it from the bury-depth check. Deliberately explicit rather
  than inferred from elevation — a yard hydrant's line crosses a wall too, so geometry alone
  cannot tell the two families apart.

Plus `PA-B-HYD-ISO` in the basement, at the tee. Not a code item — the seats are the
shutoffs — but a hose bib is the thing most likely to need a valve turned off in a hurry,
and that tee is the last point where one valve reaches both.

## Deliberately not done

- **No drainage under either hydrant.** The garage hydrant has `DRW-G-HYDRANT`, a 3' gravel
  drywell, because its barrel weeps 6' underground every time it is shut off and that water
  has to go somewhere. A self-draining wall hydrant weeps out of its own spout onto the deck
  in front of it, which drains already.
- **No hose reel, hanger or splash block** is modeled. They are placeables and nobody has
  chosen them.
- **No freeze alarm or leak sensor.** The house has no `Alarm` for water anywhere yet.

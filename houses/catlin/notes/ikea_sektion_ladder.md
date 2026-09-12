# The IKEA SEKTION ladder, and how this kitchen closes on it

Written 2026-09-11, when the kitchen was retyped from the generic `CASE-*` catalog onto
`library/placeables/sektion.py`. Every later kitchen edit checks against this note: a width
or a height that is not on the ladder below does not get a cabinet, it gets a filler.

## What the house had decided, and what the model said

`plan/products_interior.py` has registered `PROD-IKEA-SEKTION` and `PROD-IKEA-VOXTORP-WH`
since 2026-09-06, and `prices.toml`'s `[placeables]` basis note prices the whole kitchen as
SEKTION boxes with VOXTORP fronts, arguing the Section 232 position that makes SEKTION the
choice: 25% on wooden cabinets from 2025-10-14, the scheduled 50% delayed to 2027-01-01, the
EU cap at 15%, and SEKTION's carcasses manufactured in the US and therefore insulated from
it.

The geometry did not agree. Every kitchen box was a `CASE-*` type on the generic US 3"
module, whose four governing constants were a **13" upper depth, a 42" upper height, a 96"
tall frame and a 12" stacker course**. None of those four is a SEKTION size. The widths
mostly were; the heights and the upper depth were not. So the estimate was priced against
boxes that could not be ordered, and the run arithmetic was defended to the sixteenth of an
inch on the wrong ladder.

## The ladder

Verified 2026-09-11 against ikea.com/us and the IKEA US size guides:

| | values |
|---|---|
| Base frame | 30" high, 24" deep (23 5/8" without the suspension rail), 3/4" sides |
| Base widths | 12 / 15 / 18 / 21 / 24 / 30 / 36 / 38 / 47 |
| Wall heights | 15 / 20 / 30 / 40 |
| Wall depths | 15 / 24 |
| High frames | 80 / 90, in 15" and 24" depths |
| Legs | nominally 4 1/2", adjustable; FÖRBÄTTRA toe kick is a board cut on site |
| Drawer fronts | 5 / 10 / 15; MAXIMERA is the drawer box, low / medium / high |

Sources: [SEKTION base cabinet 36x24x30](https://www.ikea.com/us/en/p/sektion-base-cabinet-white-80265398/),
[SEKTION base cabinets](https://www.ikea.com/us/en/cat/base-cabinets-frame-height-23607/),
[legs, toekicks and plinths](https://www.ikea.com/us/en/cat/frames-rail-legs-toekicks-23615/),
[FÖRBÄTTRA toekick](https://www.ikea.com/us/en/p/foerbaettra-toekick-white-60266817/).

**Every frame height is a multiple of five.** That single fact governs everything below: a
stack of SEKTION frames can only ever total a multiple of five, so any target that is not
one has to be reached by moving the leg or accepting a filler.

## The stack-up: a 3" toe kick

The ceiling is 108" and the counter is 36". IKEA's own 36" counter assumes a 1 1/2" top on a
30" frame over a 4 1/2" leg. This house's top is 3 cm quartz, 1.181" (`plan/countertops.py`),
so the same stack lands at 35 11/16". And nothing closes 108" from a 4 1/2" leg either:
4.5 + 90 + 15 overshoots to 109 1/2, and 4.5 + 80 + 20 stops 3 1/2" short.

The owner's call was to shorten the legs rather than fill at the ceiling. **One leg height
has to serve both runs** or the toe kick steps where the east tall bank meets base `N3`. At
3" both close exactly:

```
tall    3 toe  + 90 frame + 15 top cabinet                   = 108
upper          + 40 wall  + 15 stacker, hung at 53           = 108
base    3 toe  + 30 frame + 1 13/16 build-up + 1.181 quartz  =  35.99
```

So: **a continuous 3" toe kick, and 1 13/16" of build-up between the base carcass top and
the quartz.** The build-up is a 3/4" plywood sub-top plus a 1" strip, invisible under the
stone and ordinary fabrication for a 3 cm top. The legs are screw-adjustable feet behind a
cut board, so the 3" costs a saw cut and nothing else.

Uppers hang at **53"**, not 54". That leaves a 17" backsplash, inside NKBA's range, and puts
the stacker course at **93"** — which still clears `WIN-M-KITCH`'s 78" head by 15".

## The two places the ladder does not close

Both are recorded here rather than quietly absorbed, because a later reader will otherwise
try to "fix" them.

**1. The mixer garage: 2" of scribe at the ceiling.** `FURN-M-KIT-MIXER-GARAGE` stands on
the peninsula's counter at 36" and wants to reach 108" — 72" of cabinet. 72 is not a
multiple of five and no sum of 15/20/30/40 reaches it; the best below is 70. So it is
`SEKT-TW24-40` at 36" under `SEKT-TW24-30` at 76", topping at 106", with a scribed panel
closing the last 2". This is one element against one wall and it is the only filler left at
a ceiling in this kitchen.

**2. The cold bay: 5 3/4" of filler, deliberately split.** The bay between the tall
cabinets is 65 3/4", exactly two Frigidaire column widths (32 7/8" each), which is why the
appliances divide it with no remainder. Two 30" SEKTION frames over them are 60". The pair
is **ganged**, its joint landing on the appliance joint at 30'-1 3/4", so each end of the
bay takes a 2 7/8" scribe against a tall cabinet — rather than one 2 7/8" gap floating
between the two boxes where every eye in the room lands.

## What the retype deleted

* **`FURN-M-KIT-WE3`**, a 12" box hung over `WIN-M-KITCH-N`. Uppers went from 13" deep to
  15", so `FURN-M-KIT-WN1`'s return in the inside corner reaches 2" further west and that
  slot fell from 12 3/8" to 10 3/8". IKEA's narrowest wall cabinet is 12". The 10 3/8" is a
  scribed filler panel built in the plane of the upper fronts, and `LR-M-KIT-N-WE3` still
  lights the corner counter from under it. This restores the kitchen's own stated corner
  rule — the east run claims the inside corner and the north run yields at 33'-4", which is
  what the base run already does.
* **The cold run's stacker course.** Four boxes became two: a 30" frame at 78" lands on 108"
  by itself, so `FURN-M-KIT-OVER-FRIDGE-ST` and `-FREEZER-ST` are gone and there is no
  joint at 8'-0" on that wall at all.
* **Two house-local types**, `FT-KIT-OVER-COLD-3278` and `FT-KIT-MIXER-GARAGE-24`. Both
  existed only because a number was unreachable on the generic catalog.

## Drawers

The TODO that started this asked about MAXIMERA. It is registered as `PROD-IKEA-MAXIMERA`
and it is a **product, not a geometry**: the model has one solid carcass per cabinet and no
drawer vocabulary at all, so which boxes are drawer stacks is prose, recorded in
`prices.toml`'s SEKTION block and beside the instances in `plan/placeables.py`.

MAXIMERA is the full-extension soft-close box; FÖRVARA is the basic one a SEKTION base ships
with if nobody chooses. Fronts sit on the 5/10/15" ladder, so a 30" base is 5+10+15 or
10+10+10 and the fronts line up across a run either way. It fits every base and pantry width
in this kitchen; the two it does not fit are a 12" base and a corner base, and this house
has neither.

## What did NOT change

The north sink run's composition. `5/8" scribe + B15 + DW + SINK-36 + B30 = 105 5/8"`, pantry
wall to corner, with the 36" sink base dead-centred under `WIN-M-KITCH`. Every one of those
widths was already on the SEKTION ladder, so the retype vindicated the arithmetic rather
than moving it. The peninsula is unchanged too: 120" of carcass is composed of SEKTION boxes
behind one continuous top, which is a shop decision, and its 15" oak knee overhang is graded
by `advisory.countertop_overhang` exactly as before.

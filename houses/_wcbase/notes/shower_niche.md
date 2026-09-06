---
title: "Lit Shower Niche — Suite Bath"
applied_to:
  - light_run: LR-S-NICHE
  - luminaire_type: ED-T-LT-NICHE-SNLT
  - device: ED-S-NICHE-PSU
tags:
  - lighting
  - bathroom
  - waterproofing
  - tile
  - low-voltage
source:
  - plan/lighting.py
  - plan/lighting_types.py
  - plan/fixtures.py
---

# Notes

## What this is

A lit niche in the suite bath's tub-shower alcove — `plans/TODO.md` §Plumbing, verbatim:
*"Have lighting in the shower niche of master bedroom, it looks cool,
Schluter®-KERDI-BOARD-SNLT."*

It goes in `W-S-C2C`, the east wall that `FX-S-SUITEBATH-TUBSH`'s alcove backs onto. That is
the only wall of the alcove that is neither the room's glazed south side nor a door, and the
alcove's own footprint (x 15'-2"..17'-8", y 17'-0"..22'-0") is what fixes the rest:

- **x = 17'-9"** — the recess face, 3" proud of the wall centre line.
- **y = 18'-4"..20'-8"** — 2'-4" of tape centred on the alcove's y-midpoint at 19'-6".
- **sill 4'-0", head 5'-0"** — the sill clears the tub deck by 2'-4" and puts a bottle at
  hand height standing up. The tape sits in the head channel and lights the shelf *from
  above* rather than glaring out of it.

## The niche is not an element, and does not need to be

There is no `Niche` in the model and this note is not asking for one. Schluter's
KERDI-BOARD-SNLT is a **prefabricated bonded-waterproof board** with the light channel
moulded into its head — the niche and the luminaire arrive in one box, from one supplier, on
one line of one order. So the board is named on `ED-T-LT-NICHE-SNLT.source` and bills through
the luminaire schedule with the tape it carries. A separate niche element would put the two
halves of one product on two different orders and give the tiler nothing extra.

What a niche *would* add — a void in the wall — is not something the wall model needs
either: at 12" x 28" in a non-bearing face of a 2x6 bearing wall it is blocking between two
studs, not an opening.

## Mark E1, not a new family

`ED-T-LT-NICHE-SNLT` is a variant of mark **E**, the 24V cove tape (`ED-T-LT-STRIP24`):
same tape, same driver family, same per-lineal-foot pricing, same `LuminaireForm.STRIP`. It
is marked **E1** rather than taking the next free letter because the next free letter is
`Q`, which is already the garage shop light, and the E-602 schedule is keyed on the mark.

The one thing it does not share with E is the listing. `wet_rated=True`, not
`damp_rated`: this is inside the tub-shower's own alcove, in the zone water is *directed
at*, which is a different UL listing from a bathroom ceiling can. `electrical.wet_location`
already walks `LightRun`s alongside fixtures (`checks/mep/lighting.py::_lit_elements`), so
it grades this one with no extension.

## Power

24V like every other tape in the house, so it has no branch circuit of its own — its driver
does. 2'-4" at 3 W/ft is 7 W; ×1.25 for continuous load is 9 W, so `ED-T-LT-PSU-60` is the
smallest catalog size and is enormous overhead. That is fine and deliberate: a driver run at
its nameplate cooks, and there is no smaller box in this catalog.

`ED-S-NICHE-PSU` sits in the ceiling at (16'-6", 21'-6") on `CKT-LT-UPPER` — **outside the
shower zone**, above the alcove's north end, where it can be reached for service without
opening tile. Switched with the rest of the room on `ED-S-SUITEBATH-SW`; nothing about a
niche light wants its own switch.

## Waterproofing tie-in — the part that has to be right

The board is the waterproofing. It is not a fixture set into a waterproofed wall; it *is* a
section of the wall's bonded membrane, and everything about the installation follows from
that:

- The SNLT board's flange laps onto the surrounding KERDI membrane (or bonded board) and is
  set in unmodified thinset with a **2" minimum overlap**, sealed with KERDI-BAND at the
  perimeter. Nothing penetrates the membrane inside the niche.
- The **driver lead is the only penetration**, and it exits through the moulded channel at
  the head — above the niche's own back-slope, on the dry side. It is sealed at the exit
  with KERDI-FIX. A lead brought through the *back* of the niche would put a hole in the
  membrane at the lowest point water collects; do not.
- The niche floor is back-sloped to drain into the shower. The board ships that way; do not
  level it out with thinset.
- Blocking between the two studs the niche sits between, top and bottom, before the board
  goes in. The board is not structural.

## Deliberately not done

- **No separate dimmer.** It shares `ED-S-SUITEBATH-SW` with the room's cans and mirror. A
  niche light on its own dimmer is a switch leg nobody will use.
- **No colour tuning.** 3000K fixed, matching every other tape in the house.
- **There is a second niche**, in the hall bath (`RM-S-BATH1`): `LR-S-BATH1-NICHE`, same E1
  SNLT type, stood vertical in `W-S-CH-W`, the alcove's only unglazed interior wall. It does
  **not** share the suite's driver: a 30' 24V home run violates the catalog's per-area-supply
  rule, so it carries its own PSU (`ED-S-BATH1-NICHE-PSU`, CKT-LT-UPPER), switched with
  `ED-S-BATH1-SW`. The waterproofing rules above apply to it unchanged.

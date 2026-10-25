# D-G-SERVICE outswing, and no top landing on ST-G-SERVICE (updated 2026-10-25)

The garage's SW service door now swings OUT onto the north-entry deck, hinged on the west
jamb. The 34" interior garage landing (`FS-BW-GARAGE`, its carriers, header, posts, hangers
and east guard) is gone; `ST-G-SERVICE` rises five risers from the slab to the threshold.

## 1. Code reading (primary text, read 2026-10-13)

**Adoption.** MN Rules 1309.0010 subp. 1 incorporates the **2018 IRC** by reference, as
amended in chapter 1309 (revisor.mn.gov/rules/1309.0010).

**MN amends R311 in three places only** (1309.0311): R311.3.2, R311.7.1 and R311.7.2.
**R311.7.6 is not amended**, so the 2018 IRC text governs. Its exception, verbatim from the
UpCodes Minnesota 2018 IRC viewer (ICC's own site refused the fetch with a 403):

> *"Exception: A floor or landing is not required at the top of an interior flight of
> stairs, including stairs in an enclosed garage, provided that a door does not swing over
> the stairs."*

**Why the exception carries the case on its own:**
- **MN's R311.7.1.1 brings this stair into R311.7.** It reads *"All stairways serving a
  dwelling or accessory structure ... shall comply with this section"*, so the detached
  garage is NOT outside the stair rules. (An earlier draft of this note argued otherwise;
  that argument is withdrawn.)
- **The exception then waives the top landing.** `ST-G-SERVICE` is an interior flight in an
  enclosed garage, and the resolved `swing_clearance` of `D-G-SERVICE` lies entirely on the
  deck side, so no door swings over the stairs.

**R311.3, AHJ CONFIRMATION ITEM.** R311.3 asks for *"a landing or floor on each side of each
exterior door"*. MN's R311.3.2 asks for a floor no more than 7 3/4" below the threshold at a
non-egress door, with an exception only for a stair under 30" on the EXTERIOR side. Read
against this door's interior side (34" to the slab), neither is met. The reading that clears
it:
- R311.1 scopes R311 to *dwellings*.
- MN extended only R311.7 (stairways) to accessory structures, not R311.3.
- So the garage's own door is outside R311.3.
- R311.7.6's exception names exactly this condition, a garage stair rising to a door that
  does not swing over it.

The usual house-to-garage case is the dwelling's door at the head of a garage stair. Confirm
at plan review that the AHJ reads this door the same way. If not, the fallback is the
retired landing (git history before 2026-10-13); the outswing can stay.

The exterior side meets R311.3 regardless: the deck is at the threshold and at least 36" deep.

The engine grades the exception directly: `code.R311_7_6_door_at_stair_head` PASSes this
door/flight pair, and an inswing leaf over the same flight FAILs
(`tests/test_stair_door_at_head.py`).

## 2. Hardware

The selected door is the same **Masonite Premium Flush insulated steel prehung** family,
now nominal **32 × 80 inches**, `DT-EXT-SWING32-G`. Ordinary west hinges; outswing onto
the deck. Model opening/hinge x=83", east jamb x=115", centre x=99". Offset from the
west wall axis is 11". The existing header, raised rough sill and threshold datum remain.

- **Frame-mounted mechanical overhead stop, stop-only, set to 90°**. No closer or hold-open
  requirement. Confirm the stop's template, door/head reinforcement and fasteners with the
  prehanger; attach nothing to the brick. Ordinary hinges, lockset and stop use the existing
  `finish-door-hardware` budget; the separate closer allowance is removed.
- Retain the Schlage F51A LAT 622 lever. Design budgets: 1¾" leaf, 2½" lever projection
  from the leaf face, 2⅜" backset, 4⅛" hingeward lever extent, ⅛" installation allowance.
- The screen assembly stays full thickness: brick face x=76.905", flashing nose x=77.030".
  At 90°, the conservative hardware budget leaves about **2.47"** after installation
  allowance. The regression encloses the continuous sweep from 0° through **91°** (1° stop
  tolerance), including both leaf faces and levers, and requires **¼"** minimum to resolved
  brick, flashing, posts and nearby geometry. This is a design envelope; purchased hinge,
  lever and stop dimensions must be checked against it.
- No screen thinning. Retain its sheathing, packing, drainage, backer, mortar and brick,
  independent post joints and existing flashing. See `plans/bw-screen-finish-comparison.md`
  for the screen finish comparison; `plan/entry_screen_finish_spec.py` owns the budget.
- The rough sill remains at deck datum 0'-0". Require the **leaf bottom at least 1" above
  that rough sill**, established by the purchased sill plus undercut. The resolved east
  HETA20Z deck-tie strap reaches 0.56" above the deck: 1" leaves 0.44" vertically, or
  0.315" after installation allowance, exceeding ¼". This is a supplier release condition,
  **not a verified factory dimension**; rerun the envelope if the unit provides less.
  Leaf/lever sweep checks use this lower bound and the modeled head elevation; the actual
  unit's head/RO still needs the dimensional reconciliation below.

**Procurement hold point — nominal leaf is not the prehung opening.** The
[32in right-hand outswing reference listing, model 26849](https://superarbor.io/products/masonite-32-in-x-80-in-premium-right-hand-outswing-flush-primed-steel-prehung-front-exterior-door-with-no-brickmold)
(read 2026-10-25) describes 1¾" thickness, 33½" unit width and a 34¼" × 81⅛" rough
opening. These are catalog dimensions, not an approved installed shop section. The engine's
32" opening convention does **not** establish a buildable 32" rough opening for that unit.
Before framing/order release, reconcile the actual frame and RO, west hinge axis and handing,
wall/jamb depth, outswing sill/pan, leaf/lever envelope and reinforced stop template with the
supplier. Preserve the east jamb/deck datum x=115"; rerun coordination if approved hinge or
frame dimensions change. No engine-wide opening API change is part of this revision.

This is the **detached garage service door**; a 32" nominal leaf does not establish 32"
clear passage. Retain the plan-review question in §1. The stair remains 36" wide, with its
existing stringer seats, handrail, backing and lighting. The exterior entry guard `RL-BW-ENTRY` terminates 1½" east of the deck edge (x=116½"),
on the top tier: the former post at x=115" collided with the early leaf swing. This
owner-approved adjustment leaves the garage handrail unchanged and keeps the guard end
gap below 4". The longitudinal section moves to
x=99"; deck edge, edge beam and piers retain their existing datums. Minnesota's
[stair provisions](https://www.revisor.mn.gov/rules/1309.0311/) remain the stair-width basis.

## 3. Stringer seat, hand check

Each stringer head seats on the ICF core of the `W-G-S` stem at −1'-0" through a 316
stainless shim pack (`CN-G-STR-SEAT-W/-E` and `-1..3`). That gives the wood-on-concrete standoff and the
capillary break. Since 2026-10-15: 5 stringers (Trex Enhance Basics treads, <=9 inch o.c.), 1 1/2" wide, bearing on the core's 1 3/4" depth.

| | |
|---|---|
| plan area | 3'-0" wide × 3'-8" run ≈ 11.0 ft² |
| load (IRC R301.5 stairs 40 psf live; ~10 psf dead) | 50 psf × 11.0 = 550 lb |
| head reaction, simple span | 275 lb, at most 69 lb per stringer (9 inch tributary width out of 36 inch) |
| worst case: 300 lb tread point load at the top tread | ≈ 300 lb to one head |
| one stringer, governing | 69 + 300 ≈ 369 lb |
| bearing area | 1.5" × 1.75" = 2.63 in² |
| bearing stress | 369 / 2.63 ≈ 140 psi |
| Fc⊥ (SPF, NDS Supplement) | 425 psi, so ratio ≈ 0.33 |

Concrete bearing at this stress is trivial. The concentrated and uniform loads are combined
conservatively.

Positive anchorage against kick-out is not modelled. Provide a field clip angle into the core,
or screw the head riser board through to the stringers; this is an EOR/field item.

## 4. What else moved (see DESIGN-LOG 2026-10-13)

- The deck tie's line 1 had been a stem tie on the carriers. It is now two HL43HDG from
  `BM-BW-FE` into `W-G-S`. `deck_tie/FS-BW-FLOOR` closes at 0.778, down from 0.966
  (`north_entry_piers.md` §10h).
- `ED-G-SW` moved down to 76" and `ED-G-LT3` moved over the flight. `RL-G-SERVICE` and the
  `BK-G-W-RAIL-*` backing were re-stationed onto the new flight.

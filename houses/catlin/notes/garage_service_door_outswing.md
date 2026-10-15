# D-G-SERVICE outswing, and no top landing on ST-G-SERVICE (2026-10-13)

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

- Hinge on the **west** jamb, so the open leaf parks along `W-BW-SCREEN` at x≈6'-7". It stays
  clear of the tier approach and of `D-M-ENTRY`'s sweep (y ≤ 36'-0").
- Surface closer with a **hold-open** arm (parallel-arm, exterior-rated). This is so nobody
  has to lean out over the deck from the top tread to pull the leaf shut. It is spec'd in
  `AN-G-SERVICE-DOOR` and billed as `prices.toml` [allowances]
  `finish-door-closer-hold-open` ($500-1,000 installed).
- The frame's sill stands on the deck at 0'-0", so the outswing leaf clears the boards by the
  sill's height and the flight did not need to re-rise.

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

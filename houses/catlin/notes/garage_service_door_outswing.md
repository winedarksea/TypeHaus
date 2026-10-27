# D-G-SERVICE outswing, and no top landing on ST-G-SERVICE (updated 2026-10-27)

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

## 2. Selected door, jamb and hold-down

Order the stock **MMI Z0364688R** from HD Supply (part 219385, UPC 192269153280):
a nominal 32 × 80 inch six-panel insulated galvanized-steel leaf, primed full-composite
6-9/16 inch frame, compression weatherstrip, non-removable-pin hinges, and fixed composite
sill. Its listed unit is 33.5 × 81 inches and suggested rough opening is 34 × 81.5 inches.
Its price is the `DT-EXT-SWING32-G` row in `prices.toml`. This is the selected standard item; no custom prehanger assembly is specified.
[HD Supply product listing](https://hdsupplysolutions.com/p/doors-00-145-10/mmi-door-6-panel-32-x-80-rh-out-on-6-9-16-primed-composite-frame-p219385)

Keep the east rough-opening edge at x=115 inches and the raised sill/deck datum. Frame
the 34 × 81.5 inch rough opening at x=81..115 inches. The west hinge is on the deck side;
use the factory-set hinge locations. During the normal prehung installation, set the unit
square in the opening, support the factory sill continuously on the KDAT sill, and install
the sloped pan and end dams in the sequence in
[opening_flashing_spec.md](opening_flashing_spec.md) §6. Keep the moving leaf and sweep at
least 1 inch above the deck; cut the five equal stair risers from the installed threshold.
These are ordinary field-fit steps for this stock unit.

**Two widths, on purpose.** `DT-EXT-SWING32-G.width` is the 34-inch framed RO (framing,
plan, IFC); `catalog_dimensions.nominal_width` is the 32-inch leaf. Takeoff bills the leaf,
and `code.R311_door_width`/`R311_2_door_height` grade the leaf (32 × 80), never the RO.
A 32-inch nominal leaf is still not 32 inches of clear passage; see §1.

The clearance regression sweeps the **32-inch leaf** inside the 34-inch RO: leaf faces and
Schlage lever, continuous 0–91°, a 1/8-inch installation allowance and 1/4-inch minimum
clearance, against the brick base and head flashing, screen, deck post and hold-down. The
result turns on the hinge-pivot inset from the west RO edge:

| pivot inset | worst clearance | CN-G-BWHD-S-DR |
|---:|---:|---:|
| 0 (flush) | −0.060 in, brick base: **fails** | 3.373 in |
| 1/2 in | 0.440 in, brick base | 2.873 in |
| 1 in | 0.940 in | 2.374 in |
| 2 in | 1.374 in, hold-down | 1.374 in |

**1/2 inch is the lower bound the brick base needs, not a conservative choice.** Anything
from 1/2 to 2 inches passes; a flush pivot does not. Before setting the stop, measure the
delivered frame's pivot from the RO edge and confirm it falls in that range. The old overlap
came from sweeping the full 34-inch RO as the leaf; `test_catlin_screen_thin_brick.py` pins
the range, the flush failure and that overlap.

Keep the canopy chord connection at the east jamb: stock **Simpson STHD14**,
CN-G-BWHD-S-DR, centered at x=118 inches on the garage face at y=524.75 inches. It is
nailed directly to the two full-height 2×6 east king studs spanning x=116.5..119.5 inches;
the single jack is inboard at x=115..116.5 inches. Install 30 specified 0.148 × 3-1/4 inch
nails. Set the strap at the stem top, z=−12 inches, with 14 inches of embedment into the
continuous 6-inch concrete core and one centered No. 4 × 40 inch bar 4 inches below the
pour top. The calculated delivered tension is 290.372 lb against the documented 3,065 lb
end-wall allowable. See [canopy_garage_diaphragm.md](canopy_garage_diaphragm.md) §3f for
the load path and reinforcement basis. The existing 90° stop-only operation remains.

The separate plan-review question about the stair-to-threshold exception remains in §1.

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

---
title: "Basement winter heat: the unheated rooms and the HPWH's chill"
applied_to:
  - equipment: EQ-B-WH
  - duct_run: DU-B-WH-OUT
  - register: REG-B-WH-IN
tags:
  - hvac
  - water-heater
source:
  - plan/mep_hvac.py
  - plan/mep_hpwh_air.py
---

# Notes

Written 2026-11-09. Winter only. Target about 65 F with the house at 70 F; low 50s is too cold.

`RM-B-FURNACE` and `RM-B-WORKSHOP` have no heat source. A hand-built room model (assumed
U-values; not derived by the engine or measured) put them at about 53-56 F and 57-60 F with the
tank in the furnace room. The largest single term was the tank's chill, about 1,100 Btu/h
averaged, more than the mech room's envelope loss.

Check on that term: 60 gal/day x 8.34 lb/gal x 80 F rise = 40,000 Btu/day delivered; at COP
about 3, two thirds comes out of the air: 26,700 Btu/day, 1,110 Btu/h. The 80 F rise is an
assumption.

**Decision (owner, 2026-11-09).** Move `EQ-B-WH` to the under-stair closet, exhaust ducted
through `W-B-WELL` into the stair, intake drawn from the stair through a grille in the same
wall. No added heater. Layout, Rheem's rules and field holds: `notes/water_service.md` §1.

**Expected, doors closed (workshop / mech), from the same room model:**

| outdoor | workshop | mech |
|---|---|---|
| -15 F | 59 F | 61 F |
| January | 62 F | 64 F |
| March | 64 F | 65 F |

These are estimates on assumed U-values. The closest they come to the target is about 5 F short
at -15 F. The chill now lands in the stair instead of the furnace room. Nothing in the model
grades this; it has not been measured.

## Air connections (2026-11-09, resolves the fit review)

**The ducted top inlet was dropped: it cannot be built here.** Rheem (AP22654 p.15) requires a
12" minimum flex section between the heater and rigid duct, and p.16 holds flex to an inner
bend radius of at least its diameter (8" inner, 12" centreline). Numbers, off the resolved
model (`ST-B2M` members, stringer underside `53.78 + 0.7364 x (373.38 - y)` AFF):

- The adapter axis (159.1", 317.9") is 11 1/4" in plan from the boot in the 321"-335 1/2" bay
  and 6.65" from `W-B-WELL`'s face. Rheem's rigid elbow (SP20890) has no published dimensions.
  Its mouth scales 8-10" off the axis on RH-PIHP-SC-SO p.2, leaving 1-3" of the 12".
- North, the elbow top is 91" (H, published) against a lined soffit of 87.2" at the mouth
  (y=327"): about 4" short. East, the south bay is 5 5/8" clear for an 8" duct.
- The drawing is generic across tank sizes, so only the head module scales. H - A is 16.8" on
  all four sizes.

**What is built, all stock:**

- **Rheem's listing.** p.9 and the spec sheet p.3: "ducted with inlet or outlet duct, any size
  room, air gap under door equal to 18 in2". `D-B-CLOSET`'s undercut went to 3/4", 24 in2 on a
  32" leaf. The louver minimums (1.5 ft2 manual, 3.25 ft2 spec sheet) are for a not-ducted
  closet and do not apply.
- **The real intake is the wall, beyond what Rheem asks** (owner). A door gap alone would draw
  every cfm from the furnace room. `REG-B-WH-IN` is a stock 12x10 return grille on the stair
  face of the 321"-335 1/2" bay, with a sheet-metal sleeve and 2x4 blocks head and sill
  (R302.11 at the bay). About 80 in2 effective against an 8" duct's 50 in2, plus the door's 24:
  roughly three quarters of the intake comes from the stair by area. Neck 70 1/2"-80 1/2",
  under the lined stringer at its north edge (81.8"). There is no closet-side grille: its
  flange would hit that stringer and the tank. The sleeve ends flush with the gypsum.
- **Exhaust.** `SP17829` outlet adapter, one 8" adjustable 90 set full (`SP20890`, or a stock
  8" adjustable, bare on the unit as in p.17's figure), then about 32" of R-6 8" flex to the
  12x10 boot. From a mouth near (134.5", 337"), a 12" centreline bend ends near y=344.8": the
  bay's boot centre, within the scaled port's +-1.5". 10 equivalent feet of fittings plus the
  register and 3' of flex against 125': length is not the limit.
- **Filter.** 6" above the top is 80 3/16". The lined soffit at the tank's north edge is 83.1".

**The boot** is a 12x10 shallow box with an 8" collar, shop-made (fabrication envelope,
`REG-T-HPWH-STAIR-1210`).

**Remaining holds, none a fit condition:**

1. Port positions are scaled (+-1.5"), and SP20890's size is unpublished. Fit the outlet elbow
   to the delivered unit before cutting the boot's bay position; the bay allows y=343-345 1/2".
2. `mep.duct_supports` reads UNKNOWN at (150", 344.5"): the engine's hanger host excludes raked
   members. The strap goes on `stringer-upper-1`'s face, 4 3/4" off the station. No crushed flex.
3. Commissioning: run with the closet door shut. Check the intake does not pull the exhaust
   back in (centres 20 1/2" apart, an authored layout; Rheem p.15 asks only that recirculation
   be reduced), and that compressor noise at the stair grille is acceptable. If not, the
   Tamarack RAPR baffled path (`PROD-AIR-RETURN-GRILLE-12X10`'s note) is the first thing to try.

Moving the air connections transfers roughly 1,100 Btu/h of assumed average extraction to
the stair; the stair heat pump must replace that heat in winter. This improves access to a
heated air volume but does not create heat or prove the two unheated rooms reach 65 F.
The room-temperature estimates above have not been recalculated.

Sources: [AP22654 Rev 01, pp. 9, 15-17](https://media.rheem.com/media/uploads/iat/sites/36/2022/09/AP22654-Rev-01-Manual-THOR-Ph2-UC-Manual_2022-1.pdf)
and [Rheem plug-in specification, pp. 2-3](https://media.rheem.com/blobazrheem/wp-content/uploads/sites/36/2024/12/Plug-in-with-HydroBoost-and-LeakGuard-Spec-Sheet.pdf).

---
title: "Basement winter heat: the unheated rooms and the HPWH's chill"
applied_to:
  - equipment: EQ-B-WH
  - duct_run: DU-B-WH-IN
  - duct_run: DU-B-WH-OUT
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

**Decision (owner, 2026-11-09).** Move `EQ-B-WH` to the under-stair closet and duct both air
connections through `W-B-WELL` into the stair. No added heater. Layout, Rheem's rules and
field holds: `notes/water_service.md` §1.

**Expected, doors closed (workshop / mech), from the same room model:**

| outdoor | workshop | mech |
|---|---|---|
| -15 F | 59 F | 61 F |
| January | 62 F | 64 F |
| March | 64 F | 65 F |

These are estimates on assumed U-values. The closest they come to the target is about 5 F short
at -15 F. The chill now lands in the stair instead of the furnace room. Nothing in the model
grades this; it has not been measured.

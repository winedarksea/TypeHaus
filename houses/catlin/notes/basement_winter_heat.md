---
title: "Basement winter heat: the unheated rooms and the HPWH's chill"
applied_to:
  - equipment: EQ-B-WH
  - duct_run: DU-B-WH-OUT
  - duct_run: DU-B-WH-IN
  - register: REG-B-WH-IN
  - register: REG-B-WH-OUT
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

**Decision (owner, 2026-11-09).** `EQ-B-WH` stands open in `RM-B-WORKSHOP`'s north-east
corner, back on `W-B-CW2`, with BOTH air connections ducted through `W-B-HALL-W` into the
stair hall. No alcove, no new walls, no added heater. (It sat in the under-stair closet for
part of that day, exhaust ducted and intake open; see `DESIGN-LOG.md`.) Layout, Rheem's rules
and field holds: `notes/water_service.md` §1.

**Expected, doors closed (workshop / mech), from the same room model:**

| outdoor | workshop | mech |
|---|---|---|
| -15 F | 59 F | 61 F |
| January | 62 F | 64 F |
| March | 64 F | 65 F |

These are estimates on assumed U-values. The closest they come to the target is about 5 F short
at -15 F. With both connections ducted the whole chill lands in the hall, and none in the
workshop or furnace room; the table is unchanged. Nothing in the model
grades this; it has not been measured.

## Air connections (2026-11-09, both ducted to the hall)

**Rheem allows it** (AP22654 Rev 01, read in full 2026-11-09): p.9 lists "ducted with inlet
and outlet duct: any size room, no additional ventilation needed"; p.15 accepts any split of
length up to Table 1 (8" flex 125 ft, 8" duct allowed, "use the largest duct size possible"),
indoor registers approved for HVAC, never tied to other ductwork, and asks only that
terminations be placed to "reduce recirculation of exhaust into the intake". No dust, lint or
chemical rule bars a workshop: p.7 says "clean dry area" and the checklist "free of flammable
vapors". A ducted inlet keeps shop dust off the filter and evaporator; it is not what Rheem's
wording is about, so keep finishing work and solvent away from the tank anyway.

**What is built, all stock** (`plan/mep_hpwh_air.py`):

- **One bay, two boots.** `W-B-HALL-W`'s only 12"-clear bay north of `D-B-SHOP` is
  170 5/8"-183 1/4" (king to stud). The next bay north is 9.8" (stud to `D-B-BATH`'s pocket
  king) and the pocket cavity is north of that. Both 12x10 boots (`REG-T-HPWH-STAIR-1210`,
  centred at y=177 1/4", clear of the door casing by 1/64") stack in it: exhaust face
  59 5/8"-71 3/8", intake 81 1/8"-92 7/8" on the hall face. Cold exhaust falls away from the
  intake; their offset is vertical only.
- **Exhaust.** `SP17829` side adapter at 65 1/2", 16" of R-6 8" flex on the port axis, one
  60 deg bend (12" centreline, the 8" inner radius p.16 asks), 13" square into the boot: 2.4 ft.
- **Intake.** Rheem's top inlet adapter and `SP20890` elbow (H 91"), outlet centreline 87",
  28" of the same flex on the same plan line, the same bend, into the upper boot: 4.5 ft. The
  flex is the p.15 12" isolation section. Total under 10 ft against 125 ft.
- **The tank is rotated -40 deg** so the side port and the elbow's outlet share one plan line
  (`plan/mep_hvac.py`).
- **Filter.** 6" above the top is 80 3/16"; nothing but the elbow is under 83" over the tank.

**Remaining holds:**

1. Port positions are scaled (+-1.5"), and SP20890's size is unpublished. Fit both on the
   delivered unit; the boots cannot move (y=177 1/4" is pinned by the stud on one side and
   the door casing on the other), so any error is taken up in the flex.
2. Filter service with the inlet adapter fitted is not stated in AP22654 (p.26 lifts it
   out of the top; p.11 and p.17 give 6"). Confirm with the SP21105/AP21365 adapter
   instructions or Rheem before ordering.
3. Commissioning: check the hall grilles' noise and that the exhaust does not short-circuit
   into the intake 10" above it. If it does, turn the exhaust boot's vanes down first.

Moving the air connections transfers roughly 1,100 Btu/h of assumed average extraction to
the stair hall; the stair heat pump must replace that heat in winter. This improves access to a
heated air volume but does not create heat or prove the two unheated rooms reach 65 F.
The room-temperature estimates above have not been recalculated.

Sources: [AP22654 Rev 01, pp. 7-17, 26](https://media.rheem.com/media/uploads/iat/sites/36/2022/09/AP22654-Rev-01-Manual-THOR-Ph2-UC-Manual_2022-1.pdf)
and [Rheem plug-in specification, pp. 2-3](https://media.rheem.com/blobazrheem/wp-content/uploads/sites/36/2024/12/Plug-in-with-HydroBoost-and-LeakGuard-Spec-Sheet.pdf).

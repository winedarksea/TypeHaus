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

Written 2026-11-09; **amended 2026-11-25 (tank in the alcove)**. Winter only. Target about 65 F with the house at 70 F; low 50s is too cold.

`RM-B-FURNACE` and `RM-B-WORKSHOP` have no heat source. A hand-built room model (assumed
U-values; not derived by the engine or measured) put them at about 53-56 F and 57-60 F with the
tank in the furnace room. The largest single term was the tank's chill, about 1,100 Btu/h
averaged, more than the mech room's envelope loss.

Check on that term: 60 gal/day x 8.34 lb/gal x 80 F rise = 40,000 Btu/day delivered; at COP
about 3, two thirds comes out of the air: 26,700 Btu/day, 1,110 Btu/h. The 80 F rise is an
assumption.

**Decision (owner, 2026-11-09).** `EQ-B-WH` stood open in `RM-B-WORKSHOP`'s north-east
corner, back on `W-B-CW2`, with BOTH air connections ducted through `W-B-HALL-W` into the
stair hall. No alcove, no new walls, no added heater.

**2026-11-25 basement replan.** The tank now stands in `RM-B-WH-ALCOVE` at (138 1/2",
246 3/4"), the old stair-foot bath's footprint, back 1/4" off `W-B-BA-N`, open to the workshop
through the 34" doorless `AO-B-WH-ALCOVE` in `W-B-CW2`; both air connections are still ducted
to the stair hall, now through `W-B-BA-E`'s north bay (below). The alcove joins HP2's zone and
has a keyless light. The table below was not recalculated: the tank's intake and exhaust never
touched the workshop's air, so its chill still lands in the hall, but the alcove's own envelope
and the open 34" mouth to the workshop are new, unmodelled terms. (It sat in the under-stair closet for
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

- **One bay, two boots.** `W-B-BA-E`'s north bay is 246 1/8"-259 7/8" clear (stud-001 to the
  end stud), 13 3/4" for the 12" boots (`REG-T-HPWH-STAIR-1210`), which stack in it centred on
  y=21'-0 3/4" (252 3/4") and cut nothing: exhaust face 59 5/8"-71 3/8", intake 81 1/8"-92 7/8"
  on the hall face. Cold exhaust falls away from the intake; their offset is vertical only.
  (Before 2026-11-25: the bay of `W-B-HALL-W` north of `D-B-SHOP`, y=177 1/4".)
- **Exhaust.** `SP17829` side adapter at 65 1/2", about 11" of R-6 8" flex, one 15 deg bend
  (the 8" inner radius p.16 asks), 2 1/2" square into the boot: 1.1 ft.
- **Intake.** Rheem's top inlet adapter and `SP20890` elbow (H 91"), outlet centreline 87",
  about 23" of the same flex, the same bend, into the upper boot: 3.2 ft with the rise. The
  flex is the p.15 12" isolation section. Total under 5 ft against 125 ft. The intake leg stays
  north of `DU-B-ERV-R-PLAY`'s y=19'-7" leg.
- **The tank is rotated +35 deg** so the side port aims 15 deg north of east: each run is one
  straight leg and one 15 deg bend square into its boot (`plan/mep_hvac.py`).
- **Filter (resolved 2026-11-10).** Rheem's Gen 5 Inlet Duct Adapter instructions (AP21628,
  kit SP21105) step 1: "For inlet connection where ducting will cross over air filter of water
  heater, place short length of rigid duct provided between elbow and inlet flange to allow for
  air filter removal". AP22654 asks 6" above for filter maintenance: 80 3/16". The model's
  stack (adapter, spacer, elbow) rises 12 13/16" to the 87" outlet centreline, so the flex's
  underside is 83", 2 13/16" over that line; the elbow top (H 91", 92 1/2" jacketed) leaves
  ~4" under the 8'-0 15/16" ceiling if the delivered spacer runs long. Install the spacer.

**Remaining holds:**

1. Port positions are scaled (+-1.5"), and SP20890's size is unpublished. Fit both on the
   delivered unit; the boots sit in a 13 3/4" bay (stud-001 to the end stud, 1 3/8" to
   spare against the 12" boots), so any error is taken up in the flex.
2. Commissioning: check the hall grilles' noise and that the exhaust does not short-circuit
   into the intake 10" above it (the grilles are fixed-blade returns: hang the exhaust one
   with its blades throwing down).

Moving the air connections transfers roughly 1,100 Btu/h of assumed average extraction to
the stair hall; the stair heat pump must replace that heat in winter. This improves access to a
heated air volume but does not create heat or prove the two unheated rooms reach 65 F.
The room-temperature estimates above have not been recalculated.

Sources: [AP21628 Gen 5 Inlet Duct Adapter](https://images.thdstatic.com/catalog/pdfImages/45/4506e417-9910-4fdf-ab08-774a6a2f8e38.pdf),
[AP22654 Rev 01, pp. 7-17, 26](https://media.rheem.com/media/uploads/iat/sites/36/2022/09/AP22654-Rev-01-Manual-THOR-Ph2-UC-Manual_2022-1.pdf)
and [Rheem plug-in specification, pp. 2-3](https://media.rheem.com/blobazrheem/wp-content/uploads/sites/36/2024/12/Plug-in-with-HydroBoost-and-LeakGuard-Spec-Sheet.pdf).

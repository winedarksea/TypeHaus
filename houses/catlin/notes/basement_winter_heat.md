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

## Air connection review (2026-11-09)

**The location remains conditional.** The routing model now verifies the connections and
framing clearance, but does not establish a constructible inlet fitting assembly or prove
thermal performance. A clean house check alone cannot release this installation.

The original relocation left the inlet at an 81" centreline while assuming a 91" factory
elbow crown in a comment. It also placed the wall grilles by their bottom edges as though
those elevations were their centres. Their shallow neck boxes did not reach the duct ends,
so an implicit boot allowance hid the disconnected geometry.

The revised model:

- Declares separate 8" air-in and air-out adapter stations on the heater. Both use transfer
  air, so no ERV airflow or mini-split duct-system credit is implied. These are dimensioned
  model stations based on scaled drawings, with about ±1.5" field uncertainty.
- Raises the inlet routing envelope to an 87" centreline to expose the factory elbow's
  approximate height. This mitred envelope is **not** the factory fitting's actual shape.
- Aligns grille centres with the duct mouths at 81" and 63" AFF, at y=328.25" and 344.5".
  The 12" openings lie within their individual stud bays; centres are about 24.3" apart
  in three dimensions. This is an authored layout, not a manufacturer separation rule.
- Models each boot as a 12x10x3.5" shallow box with an 8" round collar reaching 6.75"
  behind the grille. The metal collar projects 3.25" past the rectangular box. It is a
  shop design envelope requiring fabrication confirmation, not a catalogued boot.
- Stops the insulated flex at x=163.5". An exact solid intersection check found that
  x=164.5" let the inlet's jacket clip the upper stringer; the longer bare round collar
  bridges the connection without moving the jacket into the flight. The regression test
  checks the emitted ducts, insulation, boxes and collars against actual stair framing,
  rather than the broad vertical bounding box of a raked stringer.

The overlap ratchet retains two reviewed contacts: the inlet jacket laps its own round
boot collar, and the outlet/jacket intersects the heater's simplified full-height footprint
extrusion. That proxy incorrectly carries the HydroBoost lobe above its real 54 5/16" top;
the outlet is at 65 1/2". The detailed product symbol stops the cover at its published height.
These contacts are recorded in the geometry baseline, not excused as framing penetrations.

**Remaining installation holds:**

1. Fit the actual inlet adapter, rigid elbow, insulation and removable filter beneath the
   lined flight. The former 1 3/4" clearance claim omitted the full assembly and uncertainty.
   The short descending inlet offset still lacks a demonstrated fitting layout. The engine
   reports this as an unevaluable fitting pattern; do not treat its mitres as bendable flex.
2. Resolve both short turns using real fittings. Rheem requires flex inner bend radius at
   least its diameter: 8" inner / 12" centreline here, stricter than ADC's generic 8"
   centreline rule. The outlet's first straight is only about 6.6", which cannot seat such
   a bend. Tight turns require rigid elbows, with the manufacturer's minimum 12" flex
   isolation section before rigid duct. The inlet route has no demonstrated space for that
   combination; change the layout if the measured assembly cannot satisfy it.
3. Confirm supports to the protected flight or adjacent framing without crushing the flex.
   The existing house check still has an unresolved outlet hanger location.
4. Confirm the exhaust grille throws down and away from the inlet, clear of the handrail
   and cold-sensitive surfaces. At commissioning, run the HPWH with the closet door shut
   and test intake/exhaust temperatures and airflow with the stair head both cycling and
   operating. Verify that the intake does not pull the cold discharge back in, and that
   filter removal and future tank replacement remain practical.

Rheem allows both air connections to another room with no additional closet ventilation.
Its 8" flexible-duct length limit is 125' for inlet plus outlet, with 5' per bend and per
full-size indoor register; the short run length is not the limiting issue. Its manual
requires separate ductwork, insulated ducts and measures to reduce recirculation. Sources:
[AP22654 Rev 01, pp. 9, 15–17](https://media.rheem.com/media/uploads/iat/sites/36/2022/09/AP22654-Rev-01-Manual-THOR-Ph2-UC-Manual_2022-1.pdf)
and [Rheem plug-in specification, pp. 2–3](https://media.rheem.com/blobazrheem/wp-content/uploads/sites/36/2024/12/Plug-in-with-HydroBoost-and-LeakGuard-Spec-Sheet.pdf).

Moving the air connections transfers roughly 1,100 Btu/h of assumed average extraction to
the stair; the stair heat pump must replace that heat in winter. This improves access to a
heated air volume but does not create heat or prove the two unheated rooms reach 65 F.
The room-temperature estimates above have not been recalculated by this geometry review.

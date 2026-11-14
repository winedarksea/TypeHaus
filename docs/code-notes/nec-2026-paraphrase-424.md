# Electrical rules the engine grades: Article 424, fixed electric space heating (2026 NEC)

> Independent engineering notes for Type:Haus. Not published, endorsed or reviewed by the
> National Fire Protection Association. NFPA 70®, National Electrical Code® and NEC® are
> registered trademarks of NFPA, named here only to identify the code a rule comes from.
> This file contains no code text. Each entry is a summary in our own words, limited to
> what a check needs. It does not substitute for the code: read the edition your
> jurisdiction has adopted before relying on anything here.
>
> Summaries of rules the engine does not grade, and whole code tables, are kept out of
> the public repo; such an entry keeps its citation and Engine note, marked
> *(summary kept local)*.

Continues `nec-2026-paraphrase.md` (same conventions; the owner read all of Article 424 on
2026-11-14, with the end of 422.62). One check grades part of it:
`electrical.space_heat_circuit` (`electrical_space_heat.py`). Tests: `test_nec_printed_rules.py`.

## Catlin, read against these rules

- **What is authored.** Two heating-cable floor zones, `FH-M-BATH2` (Schluter DHEHK12016, 203 W,
  120 V, `CKT-FH-BATH2`, 15 A) and `FH-S-BATH1` (DHEHK12027, 338 W, `CKT-FH-BATH1`, 15 A), each
  under tile in a bathroom and on its own circuit through its thermostat
  (`thermostat_ref`). The dining mat is retired. Also fixed electric heaters:
  `EQ-M-FIREPLACE` (1,500 W, `CKT-FIREPLACE`, 20 A), `EQ-G-HEATER` (1,500 W, `CKT-GAR-HEAT`,
  20 A, cord and plug), `EQ-S-PLANT-HEATER` (1,500 W, `CKT-PLANT-HEAT`, 20 A) and the air
  handler's 4.6 kW heat kit (`EQ-S-HP1-STRIP`, `CKT-HP1-AH`, 35 A). No duct heater, no electric
  boiler, no baseboard or radiant panel. The sauna heater is not in Article 424 as printed.
- **424.5 continuous load (graded).** Every circuit carries 125%: the cables 1.7 A and 2.8 A
  against 15 A; the three 1,500 W heaters 15.6 A against 20 A; the air handler and kit 27.6 A
  against 35 A. All pass.
- **424.4(B) (graded).** No circuit serves two or more heater outlets, so nothing to grade.
- **GFCI (graded): 424.44(E), 424.45(E), 424.99(C)(5).** Cables under a floor covering need GFCI
  in addition to 210.8, whatever the room; both cable circuits state `gfci=True`, and both zones
  are bathrooms anyway. The circuits comment cited the old 424.44(G); it now reads 424.44(E)
  and 424.45(E). The TODO's "GFPE for floor-heating cables" item is closed: the 2026 text asks
  for GFCI protection, not ground-fault equipment protection.
- **424.19-424.20 disconnect (graded, `electrical.space_heat_circuit`).** For fixed heat with no motor over 1/8 hp and no
  supplementary OCPD, a branch breaker may be the disconnect if it is within sight of the heater
  or lockable open (110.25); in a one-family dwelling the service disconnect may be the other
  disconnecting means ((C)(3)). The cable and heater breakers are in the basement panels, out
  of sight of the floors. Owner answer (owner question 1): the floor-heat circuits
  (`CKT-FH-BATH1/2`) pass by breaker lock-off (110.25; the QO1PAF fit on the QO AFCI/GFCI
  breakers is to confirm); the fireplace, garage and plant heaters pass by their factory plug
  (422.33(A), `utilization_connection="cord_and_plug"`); `CKT-HP1-AH` passes via
  `ED-A-HP1-AH-DISC`. All five PASS. The thermostat is a Warmup 7iE, not a 424.20(A)
  disconnect (owner question 2).
- **424.47 label (derived).** A label stating that the circuit supplies space-heating cable
  goes on the panel where it originates, unless the installation is visible and
  distinguishable afterward. The cables lie under tile, so the manufacturer's label belongs on
  `ED-B-PANEL`'s door at slots 29 and 33. Derived per heating-cable circuit at its panel slot;
  not graded.
- **424.38(B)/424.48 placement (not graded).** The authored zones overlap no wall footprint
  (checked: zero area), so no cable runs under or through a wall; cables in walls are not used.
  Some wall-hung furniture overlaps a zone in plan (the floating vanity halves 23 sq in. each,
  toilet-paper and towel holders under 10 sq in.): (B)(5)/(7) concern built-ins with no floor
  clearance, which a floating vanity is not, but the clearance is not graded. Geometry needed:
  each cabinet or built-in's clearance to the floor against the zone.
- **Others.** 424.34 (7 ft factory nonheating leads), 424.35 and 424.45(B) (expansion joints),
  424.46 (inspection before covering) are product or field matters.

## Part I: general

**424.1 Scope.** **424.2
Listing.** **424.3 Reconditioned** *(summary kept local)*
- **Engine:** not graded.

**424.4 Branch circuits.** (A) An individual branch circuit may supply any wattage the circuit is
rated for. (B) A circuit for two or more outlets for fixed heating equipment is 30 A or less. (C)
Other than a dwelling unit, fixed infrared heaters may be on circuits up to 50 A.
**424.5 Continuous load.** Fixed space heating and its associated motors are continuous loads.
**424.8** Heating equipment with a hermetic motor-compressor also follows Article 440 Parts
I-VI (Table 424.8).
- **Engine:** `electrical.space_heat_circuit` (`NEC.SPACE_HEAT_CONTINUOUS`,
  `NEC.SPACE_HEAT_OUTLETS`) grades 125% of the authored `load_va` against the breaker, and the
  30 A cap where a circuit serves two or more heaters or cable zones. 125% of a circuit's
  authored load is the 424.5 reading; `load_va` unset is UNKNOWN. Not graded: 424.4(C).

## Part II: installation

**424.10** **424.11** **424.12** **424.13** *(summary kept local)*
- **Engine:** not graded.

## Part III: control and protection

**424.19 Disconnecting means.** Every heater, its motors and supplementary OCPDs can be
disconnected from all ungrounded conductors at once; heaters from several sources get grouped,
identified disconnects, each opening all its ungrounded conductors. The disconnects are rated
at least 125% of the heaters' and motors' load and lock open (110.25).
- **(A) With supplementary OCPD:** within sight of the supplementary devices (supply side if
  fuses) and either (1) with no motor over 1/8 hp: within sight of the controllers and heater,
  or lockable, or a unit switch under (C); or (2) with such a motor: the disconnect may serve
  heater and motor controller if in sight of both, or a single unit switch may serve both and be out of
  sight of the motor controller.
- **(B) Without supplementary OCPD:** (1) with no motor over 1/8 hp, the branch breaker or switch
  may be the disconnect if within sight of the heater or lockable open; (2) over 1/8 hp, within
  sight of the motor controller or per (A)(2).
- **(C) Unit switches** with a marked off position that open all ungrounded conductors may be
  the disconnect when the other disconnect is provided in: (1) multifamily dwellings, within
  the dwelling or on its floor; (2) two-family dwellings, inside or outside the unit, with a
  per-unit switch or breaker that may also serve general circuits; (3) **one-family dwellings:
  the service disconnect**; (4) other occupancies, a readily accessible branch switch or breaker.
**424.20 Thermostats.** (A) A thermostatic or combination switching device or manual switch is
both controller and disconnect if it has a marked off position, directly opens every
ungrounded conductor in off, cannot re-energize the circuit by itself after being put off, is
placed per 424.19 and is accessible. (B) A thermostat that does not directly interrupt every
ungrounded conductor, or runs a remote-control circuit, need not meet (A) and is never the
disconnect. **424.21** Switches and breakers used as disconnects are the indicating type.
- **Engine:** `electrical.space_heat_circuit` grades 424.19: a DISCONNECT in plan sight of
  every heater, or `Circuit.breaker_lock_off` (110.25), or a cord-and-plug heater passing by its
  factory plug (422.33(A)); else UNKNOWN. A thermostat is never credited (424.20(A)). Catlin:
  thermostat is Warmup 7iE, not a 424.20(A) disconnect; `CKT-HP1-AH` passes via
  `ED-A-HP1-AH-DISC`; floor-heat circuits pass by breaker lock-off and the fireplace, garage and
  plant heaters by their factory plug, all five PASS.

**424.22 Overcurrent protection.** *(summary kept local)*
- **Engine:** not graded (no heater is subdivided or 48 A or more).

## Part IV: marking

**424.28 Nameplate.** **424.29** *(summary kept local)*
- **Engine:** not graded.

## Part V: heating cables

**424.34 Construction.** Factory nonheating leads, if any, are at least 7 ft long. **424.35**
Each unit is marked with its name or symbol, catalog number and volts and watts or amperes.
**424.36 Wiring above heated ceilings:** at least 2 in. above the ceiling, ampacity worked at a
50 degC ambient with 310.15(B)(1) corrections (also corrected if above 2 in. of insulation).
**424.38 Area.** (A) Cable may extend beyond the room it starts in unless (B) bars it. (B) Not
permitted: in closets (except (C)); over the top of walls at the ceiling; over partitions to the
ceiling, except isolated single embedded runs; under or through walls; over cabinets whose
clearance from the ceiling is below the cabinet's smallest horizontal dimension; in tub and
shower walls; under cabinets or built-ins with no clearance to the floor. (C) In closet ceilings
as low-temperature humidity control, only where unobstructed to the floor.
**424.39** Ceiling cables keep 8 in. from boxes for surface luminaires and 2 in. from recessed
luminaires, trims and vents; no ceiling-mounted equipment covers cable. **424.40** Splices only
as the instructions allow.
**424.41 Ceiling cables on dry board, plaster and concrete.** (A) Cables for ceilings only are not
in walls, except one isolated run down to a dropped ceiling. (B) Adjacent runs per the
instructions. (C) Applied only to gypsum board, plaster lath or other fire-resistant material;
metal lath or conductive surfaces are fully separated by plaster. (D) Cables, the splice and 3
in. of nonheating lead are embedded the same way. (E) The whole ceiling surface gets thermally
non-insulating sand plaster, nominally 1/2 in., or an equal identified material. (F) Secured by
approved staples, tape, plaster or spreaders at 16 in. (or 6 ft for cable so identified); staples never straddle the cable on
conductive surfaces. (G) Dry board: the whole ceiling below is gypsum of 1/2 in. or less, the
void between the upper layer and the surface layer fully filled with thermally conductive
nonshrinking material. (H) Free of metal and conductive surfaces. (I) Parallel to joists, with
a 2 1/2 in. clear space under each joist between runs; surface board fastened clear of the
cable. (J) Crosses joists only at the room's ends unless the instructions need otherwise.
**424.42** Finished ceilings are not covered with thermally insulating panels or beams (wood,
fiber, plastic); paint, wallpaper and other approved finishes are allowed. **424.43 Nonheating
leads:** (A) free leads run in Chapter 3 wiring methods or listed means from the junction box
to the ceiling; (B) at least 6 in. of free lead in the junction box, marking visible; (C) excess
leads are secured, never cut, leaving enough to reach the box with 6 in. free.
**424.44 Cables in concrete or poured masonry floors.** (A) Adjacent runs per the instructions.
(B) Secured by nonmetallic frames, spreaders or other approved means while the concrete is
placed. (C) Leads leaving the floor are protected by RMC, IMC, PVC, EMT or other approved means.
(D) Bushings or fittings where leads leave the slab. **(E) GFCI** in addition to 210.8 for
cables in heated floors of bathrooms and kitchens and hydromassage tub locations.
**424.45 Cables under floor coverings.** (A) Cable is identified as suitable. (B) It does not
bridge expansion joints unless provided with fittings for them. (C) Connected to branch-circuit
wiring by the instructed methods. (D) Positioned and secured per the instructions.
**(E) GFCI** protection in addition to 210.8. **(F)** A grounding braid, metal sheath or other
approved means runs the heated length. **424.46** Installation is done with care and inspected
before it is covered. **424.47 Labels.** Cable makers supply labels that the space-heating
installation incorporates electric heating cable; they are fixed to the panelboards where the
circuits originate, per 110.21(B). Ex.: where the installation is visible and distinguishable
afterward. **424.48 Cables in walls.** Where 424.38(B) allows, cables and cable sets may go in,
on or behind walls if identified for walls, GFCI protected, grounded by braid or sheath, AFCI
protected and no higher than 4 ft above the floor (effective January 1, 2026).
- **Engine:** `electrical.space_heat_circuit` reads GFCI from `Circuit.gfci` for each cable
  circuit (`NEC.SPACE_HEAT_GFCI`): PASS when set, UNKNOWN when not (a thermostat's integral GFCI
  is not a field). 424.47 is derived per heating-cable circuit at its panel slot; 424.38(B)
  and 424.48 placement are not graded.

## Parts VI-VIII: duct heaters, resistance boilers, electrode boilers

**Part VI (424.57-424.66)** *(summary kept local)*
- **Engine:** not graded; N/A (none authored).

## Part IX: radiant heating panels and panel sets

**424.90** Scope. **424.92 Markings:** permanent, visible before the trim cover, identified as
suitable, with name or symbol, catalog number and volts and watts or amperes. **424.93
Installation.** (A)(1) Per the instructions. (2) Not in surfaces subject to damage, not through
or above walls, partitions or cupboards that extend to the ceiling, not through thermal
insulation (contact with its surface is fine), not in walls except (C). (3) Panels keep 8 in.
from surface-luminaire boxes and 2 in. from recessed luminaires, trims and vents, unless listed
for less; none under surface-mounted equipment. (4) Covered after inspection only by an
identified surface, secured so fasteners miss the panel; (5) surfaces take paint, wallpaper or
approved finishes. (B) Panel sets: fastened to joist faces or between joists, parallel to
them; fasteners only through the unheated portions, never within 1/4 in. of the element;
installed whole unless identified for field cutting. (C) In walls only if identified for walls,
per the instructions and listing, **GFCI protected**, grounded by braid or sheath, **AFCI
protected**, and no higher than 4 ft above the floor (Ex.: low-voltage panels need no GFCI; effective
January 1, 2026). **424.94** Wiring above heated ceilings is 2 in. above, at a 50 degC ambient.
**424.95** Exterior-wall wiring per 310.14(A)(3); interior-wall wiring behind panels at a 40 degC
ambient with 310.15(B)(1). **424.96** Field-assembled sets connect per the instructions; panels
by an approved wiring method; panel sets by a method identified for them, with leads attached
at install. **424.97** Excess nonheating leads may be cut to length; integral leads are not
subject to 424.5's ampacity rule. **424.98 In concrete or poured masonry:** secured and
identified; no bridging of expansion joints without provision; spaced from embedded metal
(grounded metal-clad panels may touch it); leads protected by RMC, IMC, PVC, EMT or approved
means; bushings where leads leave the slab. **424.99 Under floor coverings:** identified as
suitable; on smooth, flat surfaces; no bridging of expansion joints; connected by Chapter 3
methods; firmly anchored by an identified adhesive or system; covered only by a manufacturer-
approved floor covering; **(C)(5) GFCI** in addition to 210.8; grounding braid or sheath on the
heated portion.
- **Engine:** the GFCI rule is graded only through `FloorHeat` cables above. No panels are
  authored; not graded.

## Part X: low-voltage fixed space-heating equipment

**424.100** **424.101** **424.103** **424.104** *(summary kept local)*
- **Engine:** not graded; none authored.

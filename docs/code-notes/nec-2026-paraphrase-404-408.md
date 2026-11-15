# Electrical rules the engine grades: Articles 404, 406 and 408 (partial) (2026 NEC)

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

Continues `nec-2026-paraphrase.md` (same conventions; the owner read these pages on 2026-11-14).
**Not yet read:** the rest of 406.14; the rest of 408.4 and Article 408 beyond 408.6; the opening
of 406.9(B). 404.9 through 404.30 and 406.9(A) were read later the same day.
**Numbering flag.** Switch marking ((A) Ratings, (B) Off Indication) is printed twice: as
**404.20** in Part II of Article 404 (with 404.26-404.30 following), and on an earlier page under
the running head "406.48" with sections "406.48 Marking" and "406.50 Electronic Control
Switches". The pages do not show which number the earlier page's text really carries, or whether
it is a separate Part of Article 406 or a duplicate; the text is identical. Electronic control
switches were seen only on that page. Both numbers are cited as printed. Tests:
`test_nec_printed_rules.py`.

## Catlin, read against these rules

- **406.9(C)(1) tub and shower zone.** `electrical.bath_receptacle_zone` (advisory) lists every
  receptacle within 3 ft in plan of a tub or shower fixture in the same room. Catlin: two
  UNKNOWNs. (1) **`ED-M-BATH2-TUB-RC`** (the Kohler Bask heater outlet) is sealed in the tub's
  deck box at 8 in. above the floor, 0.1 ft from the tub: it stands inside the zone's footprint
  (the zone includes the space below the tub). No exception covers it: Exception 1 is spa-type
  (680.73), Exception 2 the 210.52(D) bath outlet, 3 weight-supporting ceiling receptacles, 4 a
  bidet-seat outlet. **Owner question 1:** does the AHJ accept the Bask outlet (the maker's
  own installation requires it) or is a 406.9(C) variance needed? Its being sealed inside the deck box behind the
  service leaf is the argument that a fixed barrier separates it. (2)
  `ED-A-STUBATH-GFCI`, 2.2 ft from the studio-bath shower: whether the shower's glass is a
  fixed barrier decides it; the model cannot say. **Owner question 2:** place it beyond 3 ft or
  confirm the barrier. Receptacles in neighbouring rooms are skipped as separated by a wall. The
  main bath's `ED-M-BATH2-RC1` and the washlet outlets passed in plan. Vertical zone (8 ft)
  is not read.
- **404.6(C)/406.9(C)(2) switches in tub or shower spaces.** Not graded: there is no "inside the
  tub or shower space" geometry beyond the fixture footprint; no switch is authored on a shower
  face (switches stand 1-2 ft off the tub or shower in plan beside doors, on the room wall).
- **406.9(B)(1) outdoor receptacles.** Graded by `electrical.outdoor_receptacle_wr`: five PASS
  (GFWT2-W/GFWT1-W WR, 5980-UCL extra-duty in-use); the check is CODE tier with its own blocking
  permit item. Indoor damp rooms are not graded; the order
  list must name WR and extra-duty hood covers.
- **406.11(D) controlled receptacles.** No receptacle is automatically controlled
  (`electrical.controlled_receptacle` N/A): the plant heater is switched by a plug-in Eve Energy
  (Matter over Thread); `ED-S-PLANT-HEAT-RC` is always on. `ED-M-KITCH-UC-RC` and
  `ED-M-CLOSET-RC1` are on plain switches (not automatic control; the exception covers a wall
  switch providing required lighting outlets under 210.70). The garage opener outlet is on a
  GFCI, not a relay.
- **406.10(3)** push-in terminals are for 15 A circuits with 14 AWG solid copper only: a spec
  note for the electrician (the 20 A receptacle circuits are 12 AWG and need side-wire or
  back-wire terminals). Not graded.
- **404.8(C) backfeed sign.** The inverter's load port and the future V2H can energize load-side
  terminals of a switch: where a switch or breaker opens a circuit that equipment can backfeed, a
  "WARNING - LOAD SIDE TERMINALS MAY BE ENERGIZED BY BACKFEED" sign (110.21(B)) belongs on or
  beside it. Candidates: the meter-main's 200 A mains and `CKT-ESS-GRID`'s breaker, with the
  ESS (706.15) and V2H items; see `nec-2026-paraphrase-480-706.md`. Derived at each source
  circuit breaker, with a condition (EG4 grid-port behaviour).
- **408.4(A) directory.** Each panel needs a legible, permanent circuit directory naming
  spares. The panel schedule is authored (`Circuit.description`; spare positions have none), and
  the print set carries it; no check reads it. 408.4(B) is for other than dwellings.
- **408.6 short-circuit rating.** Every panelboard's SCCR at least the available fault
  current. Graded by `electrical.panel_sccr`: label `sccr_a` vs `available_fault_current_a` on
  the meter-main type; QO/Homeline 22 kA authored; UNKNOWN until Xcel's figure; a staged permit
  exclusion (waiting on Xcel's fault current). For one- and two-family dwellings 408.6(1)-(5) apply: the available fault current and
  calculation date are field-marked at the point of supply, and the panelboards' SCCR (from
  their OCPDs) is field-marked. **Owner question 4:** `sccr_a` is authored (22 kA on
  `ED-T-PANEL`/`-2`); only Xcel's available fault current (`available_fault_current_a`) at the
  meter remains.

## Article 404: switches

**404.1** Covers general-use, motor-circuit, isolating and pullout switches, circuit breakers
used as switches and molded-case switches up to 1000 V ac or 1500 V dc; not wireless controls
with no circuit conductors, nor wiring devices (Article 406). **404.2** Switches are listed.
**404.3** Knife switches, butt-contact switches and bolted-pressure switches may be
reconditioned; lighting, dimmer and electronic control switches that are not wiring devices,
and molded-case switches, may not. **404.5** (A) Switches and breakers are externally operable
types in an enclosure for the use, with the 312.9 bending and gutter space (Ex. 1 open-face
panelboard knife switches; Ex. 2 those installed per 110.27(A)(1)-(4)). (B) Enclosures are not
used as junction boxes, gutters or raceways for conductors feeding through or tapping off,
unless they meet 312.11. **404.6** (A) Surface-mounted switches in damp or wet locations are in
weatherproof enclosures (312.4); (B) flush ones take weatherproof covers; **(C)** switches are not in
tub or shower spaces unless part of a listed tub or shower assembly. **404.7** Adjustable
switches are enclosed or in cabinets, with energized parts barriered during adjustment (Ex.:
accessible only to qualified persons with parts within 6 in. covered). **404.8** (A)
Single-throw knife switches do not tend to close by gravity; (B) double-throw may be vertical
or horizontal with a mechanical hold; **(C)** blades and load terminals are de-energized when
open. Ex.: where backfeed is possible, they may be live in the open position with a permanent
sign "WARNING - LOAD SIDE TERMINALS MAY BE ENERGIZED BY BACKFEED" (110.21(B)). **404.9**
General-use and motor-circuit switches, breakers and molded-case switches, in their 404.5
enclosure, indicate on or off where visible at the external operating means; a vertically
operated handle is up for on (Ex. 1: a double-throw one may be on with either handle position;
Ex. 2: busway tap switches with a center-pivoting handle may be open or closed with either end
up, the position clearly indicated and visible from the floor). **404.10 Accessibility.** (A)(1)
Switches and breakers used as switches are readily accessible. **(A)(2) Maximum height:** the
centre of the operating handle's grip, in its highest position, is at most 2.0 m (6 ft 7 in.)
above the floor, finished grade or working platform; except (1) busway fused switches at the
busway's level, with a means to operate them, (2) switches adjacent to the motors or equipment
they supply, which may be higher and accessible by portable means, (3) hookstick isolating
switches. **404.11** A hand-operable breaker, or a power-operated one openable by hand on power
loss, may serve as a switch if it has the right number of poles. **404.12** Metal switch and
breaker enclosures are connected to the EGC per Article 250 Part IV (service equipment: Part V);
nonmetallic enclosures with metal raceway or armored cable follow 314.5 Ex.; nonmetallic boxes
for switches use a wiring method that includes an EGC. **404.13** Knife switches: (A) above 1200 A
at 250 V or less, or 1000 A at 251-1000 V, are isolating switches, not opened under load; (B)
to interrupt over 1200 A (250 V) or 600 A (251-1000 V, ac; 1500 V dc), listed switches or breakers
are used; (C) smaller ratings are general-use. (D) Motor-circuit switches may be knife type.
**404.20 Marking** (Part II): (A) ratings in current, voltage and, if horsepower rated, maximum
horsepower; (B) a switching device with a marked OFF position disconnects all ungrounded
conductors to the load. **404.26** Knife switches of 600-1000 V and over 200 A have renewable or
quick-break auxiliary contacts for breaking current. **404.27** Fused switches do not parallel
fuses except per 240.8. **404.28** Wire-bending space opposite the line and load terminals
meets Table 312.9(B)(2). **404.30** Switches in enclosures with doors or hinged covers are
dead-front unless a tool is needed to reach the interior.
- **Marking and electronic switches (printed 406.48, 406.50; marking also 404.20).** Switches are marked with
  current, voltage and, if horsepower rated, the maximum horsepower. A switching device with a
  marked OFF disconnects every ungrounded conductor to its load. Electronic control switches
  introduce no current on the equipment grounding conductor in normal operation; Ex.: ones that do
  are allowed for applications under 406.30(C) Ex. (that section is unread), and replacement
  or retrofit ones are listed and marked for that use only.
- **Engine.** `NEC.SWITCH_HEIGHT` is now `"404.10(A)(2)"` (it read `"404.8(A)"`, the 2023
  number; in 2026 404.8(A) is the knife-switch rule). `electrical_panel_height` grades handles
  against 79 in. (the code's 6 ft 7 in.; 2.0 m is 78.7 in.), matching. `NEC.SWITCH_BACKFEED_SIGN`
  and `NEC.SWITCH_TUB_SHOWER` are pinned, not graded.

## Article 406: wiring devices

**406.1-406.3** Cover the rating, type and installation of wiring devices; wiring devices are
listed; reconditioned ones are not installed.
**406.9 Damp and wet locations.** (A)(1) Receptacles in damp locations: (a) installations suitable for
wet locations are also suitable for damp; (b) outdoors in a protected location, or elsewhere
damp, the enclosure and cover are weatherproof with the cover closed and no plug inserted;
**(c) all 125 and 250 V nonlocking receptacles in damp locations (a covered porch, say) are listed
weather-resistant type.** (A)(d) hinged hoods of damp-location receptacle covers open 90 degrees or fully. (A)(2)/(B)(3)
Surface-mounted switches in damp or wet locations are in weatherproof enclosures (312.4);
flush ones have weatherproof covers. **(B)(1) Wet-location 15 and 20 A, 125 and 250 V
receptacles:** (a) the enclosure is weatherproof whether or not a plug is inserted; (b) the outlet
box hood is listed and identified as extra-duty (other listed enclosures or assemblies that do
not use a hood need not be); (c) hood covers open at least 90 degrees; Ex.: receptacles
subject to routine high-pressure spray washing may be weatherproof only with the plug removed;
**(d) nonlocking 15 and 20 A 125 and 250 V receptacles are listed weather-resistant type**
(5-15, 5-20, 6-15, 6-20). (B)(2) Other wet-location receptacles are weatherproof with the plug in
or out for unattended products and with the plug removed for attended ones.
**(C) Bathtub and shower spaces.** (1) Receptacles are not inside tubs or showers or within a zone
900 mm (3 ft) horizontally of the outside edge of the tub or stall (including below it) and
2.5 m (8 ft) vertically above the rim or stall threshold; the zone is all-encompassing but stops at
a floor, wall, ceiling, room door, window or fixed barrier. Ex. 1: 680.73. Ex. 2: in a bathroom smaller
than the zone, the 210.52(D) receptacle goes opposite the rim or threshold on the farthest wall.
Ex. 3: listed weight-supporting ceiling receptacles for luminaires, in damp locations per
410.10(D). Ex. 4: in dwellings, one receptacle for an electronic toilet or hygiene device
such as a bidet seat, readily accessible and not between the toilet and the tub or shower.
(2) Switches are not in tub or shower spaces unless part of a listed tub or shower assembly.
**(D)** A flush-mounted outlet box in a finished surface takes a weatherproof faceplate assembly
that seals to the surface.
- **Engine:** `electrical.bath_receptacle_zone` (`NEC.BATH_ZONE`) grades (C)(1) by plan distance
  only: UNKNOWN for a same-room receptacle inside 3 ft, since barriers and exceptions are not
  modelled; Exceptions 2 and 4 are not distinguished. 406.9(B)(1) graded:
  `electrical.outdoor_receptacle_wr` - outdoor (in no room) receptacles WR per
  (A)(1)(c)/(B)(1)(d); an in-use cover per (B)(1)(a)-(b) or UNKNOWN (damp vs wet not modelled);
  indoor damp rooms not graded. Catlin: five PASS (GFWT2-W/GFWT1-W WR, 5980-UCL extra-duty
  in-use); CODE tier, with its own blocking permit item.

**406.10 Terminations.** *(summary kept local)*
- **Engine:** not graded (`NEC.PUSH_IN_TERMINALS`).

**406.11 Rating and type.** (A) Receptacles are marked with the maker's name or identification and
voltage and amperage. (B) Rated at least 15 A 125 V or 15 A 250 V and not usable as
lampholders. (C) Isolated-ground receptacles carry an orange triangle, are used only with
isolated equipment grounding conductors per 250.146(D), and in nonmetallic boxes take nonmetallic faceplates (Ex.: a metal plate if the
box has a feature connecting it to the EGC). **(D) Controlled receptacles:** nonlocking 125 V 15
and 20 A receptacles controlled by an automatic control device, or incorporating control features that
remove power for energy management or building automation, are permanently marked with the Figure
406.11(D) symbol (a power-button circle) and the word "controlled"; on a multi-receptacle device,
the marking says which contact; for automatically controlled receptacles it is on the receptacle
face and visible after installation. Ex.: receptacles controlled by a wall switch providing the
required room lighting outlets under 210.70. (E) A receptacle with a USB charger is listed and
built with the Class 2 circuitry integral.
- **Engine:** `NEC.CONTROLLED_RECEPTACLE`. Graded: `electrical.controlled_receptacle`
  (advisory) - receptacles switched by a smart/occupancy/timer control need
  `controlled_marking`. Catlin: N/A; none is automatically controlled (the plant heater is
  switched by a plug-in Eve Energy; its receptacle is always on).

**406.12 General installation.** **406.14 Mounting (partial).** *(summary kept local)*
- **Engine:** not graded; a new house builds to these without replacements.

## Article 408: switchboards, switchgear and panelboards (partial)

**408.1** Covers equipment to 1000 V ac and 1500 V dc. **408.3** Reconditioned switchboards and
switchgear (and their sections) may be installed, evaluated first if damaged by fire, products of
combustion, corrosion or water; **reconditioned panelboards may not**.
**408.4 Descriptions.** (A) Every circuit and circuit modification has a legible, permanent
description: at each switch or breaker of a switchboard or switchgear; in a directory on the face, inside or
adjacent to a panelboard door; clear, evident and specific to the use of each circuit, spare
positions included; detailed enough not to be confused with another circuit; not dependent on
transient occupancy; clear about abbreviations. (B) Switchboards and panelboards fed by a feeder in
other than one- and two-family dwellings are permanently marked with the source's identity and
location, by a non-handwritten label.
**408.5** Where raceways enter a switchboard or floor-standing panelboard at the bottom, the wiring
space under the busbars is at least 8 in. (insulated) or 10 in. (noninsulated), and raceways rise
no more than 3 in. above the enclosure bottom (Table 408.5). **408.6 Short-circuit rating.** Every
switchboard, switchgear and panelboard is rated at least the available fault current. In
one- and two-family dwellings: (1) the available fault current at the line terminals and the
calculation date are field-marked on the enclosure at the point of supply; (2) the
short-circuit rating of panelboards, at nominal voltage, based on the OCPDs installed, is field-marked; (3) marks follow
110.21(B); (4) the calculation is documented and available to inspectors and installers; (5) after
modifications affecting the fault current, it is verified or recalculated so ratings stay at or above it.
- **Engine:** `NEC.CIRCUIT_DIRECTORY` (408.4(A)), `NEC.SWITCHBOARD_SCCR` (408.6), `NEC.PANELBOARDS`
  (Article 408) name these. 408.6 is graded by `electrical.panel_sccr` (label `sccr_a` vs
  `available_fault_current_a` on the meter-main type; QO/Homeline 22 kA authored; UNKNOWN until
  Xcel's figure; a staged permit exclusion); the rest is not graded.

# Electrical rules the engine grades: interpretation notes (2026 NEC)

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

These notes record how the engine *interprets* each requirement and what it grades, so a
reviewer can compare a check against its stated reading. Section numbers are citations.
The owner read the printed edition on 2026-11-13 and 2026-11-14. Minnesota adopted the 2026 edition without
amendment for permits filed on or after 2026-08-17, so these requirements are enforced as law
where Catlin is built. Section strings live in `typehaus.model.nec.NEC`, and `UNCONFIRMED`
there is empty.

Each rule has an
**Engine** line naming the check id, module or test that grades it, or
saying "not graded". Tests: `test_nec_120_82.py` (load calculation) and
`test_nec_printed_rules.py` (numbering, 210, 705, 250). Article 250 is in
`nec-2026-paraphrase-250.md`, Article 310 in `nec-2026-paraphrase-310.md`, Articles 110
(working space), 240.6 and 625 in `nec-2026-paraphrase-110-240-625.md`, Articles 440 (A/C) in
`nec-2026-paraphrase-440.md`, Article 424 (fixed electric space heating) in
`nec-2026-paraphrase-424.md`, Articles 404, 406 and 408 (partial) in
`nec-2026-paraphrase-404-408.md`, Articles 480 and 706 (batteries, ESS) in
`nec-2026-paraphrase-480-706.md`, Articles 225, 230 and
314 in `nec-2026-paraphrase-230-314.md`, and Article 680 (spas) in
`nec-2026-paraphrase-680.md`, and Articles 690, 705 and 710 (PV, interconnection,
stand-alone) in `nec-2026-paraphrase-690-705-710.md`, and Article 300 (wiring methods,
underground cover, Table 300.7(A); renumbered in 2026) in `nec-2026-paraphrase-300.md`, and
210.13-210.21, 210.52 (tail) to 210.70, Article 410 (start) and 422.11-422.33 in
`nec-2026-paraphrase-210-422-410.md`, and Article 411, 210.70(C), Article 215 and the 225/230
re-read in `nec-2026-paraphrase-411-230.md`, and Article 702 (optional standby), 705 Parts II-III
(microgrid, island mode) and the EV interactive sections in `nec-2026-paraphrase-702-705-island.md`,
and Articles 721.50-723.22 (limited-energy cables) in `nec-2026-paraphrase-722.md`, and the Article 100 lighting-track terms, Article 120 (120.5, 120.41),
215.10-215.18, 225.1-225.10 and the raceway articles 342-366 in `nec-2026-paraphrase-followup.md`,
to keep each file short.

- A major NEC reorg is planned for 2029 so looking forward section numbers may have big changes

## Article 120: load calculations

**120.4 Table of specific-purpose calculations.** *(summary kept local)*
- **Engine:** not graded; no check cites these sections.

**120.6 Noncoincident loads.** When loads won't run at the same time, only the biggest one
counts toward the total, sized with the 120.11(A) motor and combination-load treatment.
There are two grounds: (1) at a feeder or service, the loads are unlikely to operate
together; (2) at any level, listed equipment stops them from operating together.
- **Engine:** `LoadManagement(strategy="noncoincident")` in `takeoff/service_load.py`. The
  group counts at its largest member, and an authored ceiling below that is raised to it.
  Basis (1) needs a `source`; basis (2) needs a `listing`. Findings cite 120.6(1) or (2).
  The largest member is taken at its connected VA plus 25% of its equipment type's
  `largest_motor_va` (120.11(A)). That count can exceed the group's connected sum, and the
  excess then adds to the demand.

**120.7 Power control system (PCS).** A PCS may be used at branch-circuit, feeder or service
level. In a load calculation it must meet (A)-(C).
- **(A)** It complies with Article 130 Part II.
- **(B)** Qualified persons set the control setting, and it is at most 80% of the rating of
  the OCPD the PCS monitors for overload control.
- **(C)** The load is the controlled loads plus the noncontrolled loads. Controlled loads
  follow what the PCS monitors: (1) if only controlled loads, the control setting stands in
  for them; (2) if controlled and noncontrolled loads, the controlled loads' minimum
  operating current (a value of zero or more, at or above their true minimum) stands in.
  Noncontrolled loads follow Parts II-VII.
- **Engine:** `LoadManagement(strategy="pcs")`, graded by `electrical.service_load`. It needs
  a `listing` (130.2 / (A)). Setting at most 80% of the OCPD (B) is graded only when
  `monitored_ocpd_amps` is authored, at 240 V. `max_simultaneous_va` is read as the (C)(1)
  setting. A PCS with `monitors_noncontrolled` counts the group at `min_operating_amps` ×
  240 V (120.7(C)(2)); with none recorded, the credit is refused. Catlin authors no PCS.

**120.10(E) Continuous loads.** A load calculation does not apply 125% to continuous loads.
The multiplier can still come from sizing rules elsewhere.
- **Engine:** consistent: `service_load` applies no continuous-load multiplier. Not graded
  otherwise.

**120.11 Maximum branch-circuit load.**
- **(A) Motor-operated and combination loads.** A circuit with only motors is sized by
  430.22; one with only A/C or refrigeration by 440.6. A circuit with fixed motor-operated
  equipment (motor over 1/8 hp) alongside other loads counts at least 125% of the largest
  motor plus the others per 430.24.
- **Engine:** applied inside 120.6 only (`largest_motor_va`); 430.22 / 440.6 circuit sizing
  is not graded.

**120.13 Dwelling branch circuits.** *(summary kept local)*
- **Engine:** not graded; the engine uses 120.82's 2 VA/sq ft.

**120.14 Other loads, all occupancies.** *(summary kept local)*
- **Engine:** not graded; these are standard-method terms. 120.82(B)(3) counts a dryer's
  nameplate, and Catlin's 830 W heat-pump dryer is authored at that.

**120.16 Additions to existing installations.** *(summary kept local)*
- **Engine:** not graded (new construction).

**120.40 Feeder and service load, general.** The calculated load is at least the sum of the
branch-circuit loads (Part II) after any demand factors Part III or the optional Part IV
permits.
- **Engine:** the 120.82 method is the optional alternative; `electrical.panel_feeder_load`
  applies it per panel as an estimate.

**Table 120.54 Dryer demand factors.** *(summary kept local)*
- **Engine:** not graded; the house has one dryer, which takes 100% (NEC.DRYER_STANDARD is
  unused).

**120.55-120.56 Cooking and kitchen equipment.** *(summary kept local)*
- **Engine:** not graded; the 120.82 method uses nameplates.

**120.57 EVSE load.** Each EVSE counts at its nameplate rating, or at 7,200 W (VA) only
where no nameplate is available. This is not the 2023 "larger of the two".
- **Engine:** `takeoff/service_load.py`: an `ev` circuit counts its authored `load_va`, else
  its devices' VA, else 7,200 VA (`EVSE_DEFAULT_VA`; `ev_default_circuits` and the
  `electrical.service_load` message say so). Catlin's hardwired 40 A charger is authored at
  its 9,600 VA nameplate, so nothing changes.

**120.61 Feeder or service neutral.** *(summary kept local)*
- **Engine:** not graded; no neutral-load calculation. 120.82(A) allows the neutral by this
  section.

**120.82 Optional method, dwelling unit.**
- **(A) Applicability.** A dwelling may use this method in place of the Part III standard
  method if one 3-wire set of service or feeder conductors (120/240 V or 208Y/120 V), with
  an ampacity of 100 or greater, carries its entire load. The total is (B) + (C) + (D), and
  conductors sized this way may use a 120.61 neutral.
- **(B) General loads.** The first 8 kVA at 100% and the rest at 40%, applied to the sum of:
  (1) 2 VA/sq ft (22 VA/m²) of floor area per 120.5(C), for general lighting and general-use
  receptacles; (2) 1,500 VA per 20 A small-appliance circuit and per laundry circuit under
  210.11(C)(1)/(2); (3) the nameplate of (a) appliances that are fastened in place,
  permanently connected or on a dedicated circuit, (b) ranges, wall ovens and cooktops,
  (c) dryers not on the laundry circuit, (d) water heaters; (4) the nameplate of permanently
  connected motors not counted in (3). Heating and cooling aren't explicitly excluded from
  (B); they are counted in (C).
- **(C) Heating and air conditioning: the largest of six.** (1) cooling at 100%; (2) a heat
  pump with no supplemental electric heat at 100%; (3) for central electric heat, the
  heat-pump compressor at 100% plus supplemental heat at 65% (a compressor locked out while
  the supplemental heat runs is left out of the sum); (4) electric space heat at 65% when
  there are fewer than four separately controlled units; (5) electric space heat at 40% with
  four or more; (6) thermal storage, and heat that normally runs continuously at full
  nameplate, at 100%. A system counted under (6) can't also be counted under another item.
- **(D) EVSE.** EVSE at 100%, per 120.57 (nameplate, or 7,200 W where there is none).
- **120.80 Part IV.** Optional feeder and service calculations are permitted per Part IV.
- **Engine:** `takeoff/service_load.py` (`general_demand_va`, `hvac_selection`,
  `service_load_summary`), graded by `electrical.service_load` and
  `electrical.panel_feeder_load`. Notes on the implementation:
  - (B)(2) counts circuits whose description says "small-appliance" or "laundry", never
    fewer than 2 + 1 for the whole dwelling.
  - (C)(3) relief is authored as `Equipment.compressor_lockout_ref` on the heat kit.
    Catlin doesn't claim it (owner, 2026-11-13).
  - (C)(6) is not modelled.
  - (A) below 100 A gives UNKNOWN, because Part III is not implemented.
  - (D) counts the EVSE nameplate per 120.57, else 7,200 VA.

## Article 210: branch circuits

**210.7 Multiple branch circuits.** *(summary kept local)*
- **Engine:** not graded. `electrical.lighting_controls` notes where a switch and its
  luminaire name different circuits.

**210.8 GFCI for personnel.** Protection is a listed Class A GFCI, readily accessible (a
rooftop receptacle needs to be reachable only from the roof). The distance to a receptacle
follows the route an appliance cord would really take: it goes around floors, walls,
ceilings and fixed barriers, and it passes through doors, doorways and windows.
- **(A) Dwellings.** Applies to receptacles rated 125–250 V on single-phase circuits at
  150 V or less to ground, in these locations:

  | Item | Location | Engine |
  |---|---|---|
  | 1 | bathrooms | graded |
  | 2 | garages | graded |
  | 3 | storage or work areas of accessory buildings that aren't habitable | not graded |
  | 4 | outdoors | graded |
  | 5 | crawl spaces at or below grade level | not graded |
  | 6 | basements, finished or unfinished | graded |
  | 7 | kitchens | graded |
  | 8 | anywhere with a sink plus permanent provision for preparing food or drinks, or for cooking | not graded |
  | 9 | within 6 ft of a sink bowl's top inside edge | graded |
  | 10 | boathouses | not graded |
  | 11 | within 6 ft of a tub's or shower stall's outside edge | graded |
  | 12 | laundry areas | graded |
  | 13 | indoor damp locations | not graded |
  | 14 | indoor wet locations | not graded |

  Exempt (none applied by the engine): Ex. 1, snow-melt, de-icing and pipeline-heating
  receptacles that aren't readily accessible; Ex. 2, a receptacle that serves only a
  permanent security system; Ex. 3, a listed weight-supporting ceiling receptacle and its
  fitting for a luminaire or fan, unless that luminaire or fan has a general-purpose
  receptacle of its own; Ex. 4, factory receptacles inside an exhaust fan that isn't readily
  accessible, unless its listing or instructions call for GFCI.
- **(C)** Crawl-space lighting outlets at 120 V or less.
- **(D) Specific appliances**, at 150 V or less to ground and 60 A or less, protected at the
  branch circuit or the outlet. Graded: (6) sump pumps, (7) dishwashers, (8) electric
  ranges, (9) wall ovens, (10) counter-mounted cooking units, (11) clothes dryers at any
  voltage, (12) microwaves. Not graded: (1)–(5), which are automotive vacuums, water coolers
  and bottle fillers, pressure washers, tire inflators and vending machines.
- **(E)** Receptacles required by 210.63.
- **(F) Outdoor outlets, dwellings.** Every outdoor *outlet*, not only receptacles, on a
  single-phase circuit at 150 V or less to ground and 60 A or less, except those exempted by
  (A) Ex. 1. This includes garages with floors at or below grade, accessory buildings and
  boathouses, and equipment that gets replaced must be given GFCI. Ex. 1: lighting outlets,
  other than the crawl-space ones in (C). Ex. 2: listed HVAC equipment. **Ex. 2 expired
  2026-09-01.** Ex. 3: listed HVAC equipment may use a listed Class C SPGFCI instead, and its
  disconnect then carries the Class C SPGFCI warning marking.
- **Engine:** `code.E3902_gfci_locations`, in `checks/mep/electrical_code.py` and
  `electrical_gfci_appliances.py`. The (A) items are graded as the table shows, treating
  a basin or sink-symbol fixture as a sink and excluding toilets and floor drains. (D) is
  graded as listed above, and (F) with Ex. 3. Doors, doorways and windows are cut out of the
  cord-path barrier, but blind niches are not. A storey with no grade datum gives UNKNOWN.
  A Class C SPGFCI passes only for HVAC; the warning marking is noted but not modelled. Not
  graded: the (A) exceptions, (C), (E), and readily-accessible.

**210.11(C) Dwelling-unit circuits.**
- **(1)** At least two 20 A small-appliance circuits for 210.52(B), serving nothing else.
- **(2)** At least one more 120 V 20 A circuit for the 210.52(F) laundry receptacles,
  serving nothing else.
- **(3)** At least one 120 V 20 A circuit for 210.52(D) bathroom receptacles, including
  countertop ones, serving nothing else. Ex.: a 20 A circuit that serves just one bathroom
  may also feed other equipment in that bathroom, per 210.23(B)(1)/(2).
- **(4)** At least one 120 V 20 A circuit for the garage receptacles, including the
  210.52(G)(1) ones, serving nothing else. Other garage receptacles may go on additional
  circuits of 15 A or more. Ex. 1: this circuit may also feed outdoor receptacles. Ex. 2: a
  garage with a single vehicle bay may put other outlets on it, per 210.23(B).
- **Engine:** (3) is `code.NEC_210_11_C3_bathroom_circuit`; (4) is
  `electrical.garage_branch_circuit`. (1) and (2) are not graded; `service_load` counts them.

**210.12 AFCI.** Listed and readily accessible. (A) allows six ways to provide it, the first
being a combination AFCI where the circuit starts.
- **(B) Dwellings.** Every 120 V single-phase 10, 15 or 20 A circuit feeding outlets or
  devices in kitchens, family rooms, dining rooms, living rooms, parlors, libraries, dens,
  bedrooms, sunrooms, recreation rooms, closets, hallways, laundry areas and similar rooms.
  Bathrooms, garages and outdoors are not on the list. Ex. 1: a dedicated fire-alarm circuit
  in metal raceway or armored cable. Ex. 2: a dedicated arc-welder outlet circuit.
- **(E)** Extending or modifying wiring in those rooms requires AFCI, unless the extension
  is no longer than 6 ft and adds no outlets or devices.
- **Engine:** `code.E3902_16_afci` (occupancy table `_AFCI_OCCUPANCIES`; STORAGE stands in
  for closets; STAIR is in scope; a room with a washer or dryer is a laundry area). `Circuit.afci` is one flag, so (A) is not distinguished. The exceptions and
  (E) are not graded.

**210.52 Dwelling receptacle outlets.** Covers 125 V 15 and 20 A receptacles. A receptacle
doesn't count toward the requirement if it is built into a luminaire or appliance, switched
(see 210.70(A)(1) Ex. 1), inside a cabinet, or higher than 5½ ft above the floor. A
baseboard heater's factory receptacles can count for the wall the heater covers, but they
can't be on the heater's circuit.
- **(A)** Kitchens, family rooms, dining rooms, living rooms, parlors, libraries, dens,
  sunrooms, bedrooms, recreation rooms and similar rooms.
  - (1) Along the floor line, no point of a wall space is more than 6 ft from a receptacle.
  - (2) A wall space is any stretch at least 2 ft long, measured around corners, that no
    doorway or similar opening, fireplace, stationary appliance or fixed cabinet
    interrupts. Fixed panels count and sliding panels don't. Fixed dividers such as bar
    counters and railings count too.
  - (3) A floor receptacle counts only if it is within 18 in of the wall.
  - (4) Countertop receptacles don't count toward (A).
  - (5) Under a room-divider counter, no receptacle may be within 24 in of the counter.
- **(B) Small appliances.**
  - (1) In kitchens, pantries, breakfast rooms, dining rooms and similar rooms, the
    210.11(C)(1) circuits feed every (A) wall and floor receptacle, every (C) countertop
    receptacle and the refrigeration equipment. Ex. 1: switched receptacles may be on a
    general-purpose circuit. Ex. 2: a specific appliance may have its own circuit of 15 A
    or more.
  - (2) Those circuits feed nothing else, apart from a clock receptacle and supplemental
    power for gas cooking.
  - (3) A kitchen's countertop receptacles are split over at least two of these circuits.
    The circuits may also serve that kitchen and the other (B)(1) rooms, but no circuit may
    serve two kitchens.
- **(C) Countertops at least 12 in wide** in kitchens, pantries, breakfast rooms, dining
  rooms and similar rooms. They don't count toward (A). A multioutlet assembly counts as one
  receptacle per 12 in.
  - (1) No point along the wall line is more than 24 in from a receptacle in that space.
    Ex. 1: no receptacle is needed behind a range, cooktop or sink set less than 12 in off
    the wall on a straight run, or less than 18 in in a corner. Ex. 2: where a required
    receptacle can't be installed in those areas, it may go as near as practicable,
    keeping the same count and the (C)(3) location rules.
  - (2) Islands and peninsulas don't need receptacles, but any that are installed follow
    (C)(3) and (C)(4). Without one, provisions for adding one later are required.
  - (3) Location: on or above the counter, at most 20 in above it, or in the counter or
    work surface using listed assemblies. A receptacle blocked by a fastened appliance, an
    appliance garage, a sink or a rangetop doesn't count.
  - (4) Below the counter: none on adjacent walls within 24 in of the base cabinets, and
    none under the counter within 24 in of it. Ex.: a receptacle inside a drawer.
- **(D) Bathrooms.** (1) A receptacle within 3 ft of each sink's outside edge. (2) It goes on
  an adjacent wall or partition, on the countertop, or on the side or face of the sink
  cabinet, no more than 12 in below the top of the sink or countertop. (3) Assemblies listed
  for countertops may go in the countertop.
- **(E) Outdoors.** (1) One- and two-family dwellings: one receptacle at the front and one
  at the back, each readily accessible from grade and at most 6½ ft above it. (3) A
  balcony, deck or porch within 4 in (horizontally) of the dwelling unit gets a receptacle
  reachable from it, at most 6½ ft above its walking surface.
- **(F)** A receptacle in every area set aside for laundry equipment.
- **(G)** At least one receptacle in each of the following, on top of any for specific
  equipment (a security-only receptacle doesn't count): (1) every vehicle bay of an
  attached garage, or of a detached garage that has power, at most 5½ ft above the floor;
  (2) every accessory building that has power; (3) every separate unfinished part of a
  basement.
- **(H)** A hallway at least 10 ft long, measured down its centerline without passing
  through a doorway, gets a receptacle.
- **(I)** A foyer larger than 60 sq ft that isn't a hallway gets a receptacle in every wall
  space at least 3 ft wide. Doorways, and windows beside a door that reach the floor, are
  not wall space.
- **Engine:**
  - `electrical.receptacle_spacing`: (A)(1)–(3), with MEDIA taken as the family/recreation
    room, and (C)(1)/(C)(3)/(C)(4) in `checks/mep/electrical_counters.py`. A receptacle counts
    only for the room it is in; stationary appliances and fireplaces break wall space.
  - `electrical.island_receptacle`: (C)(2)-(C)(4), islands and peninsulas, (C)(3) 20 in.
    window; no receptacle -> junction box as provision, else UNKNOWN.
  - `code.E3901_6_bathroom_receptacle`: (D), per bowl (countertop cutout), free-standing
    rejected.
  - `electrical.outdoor_front_back_receptacles`: (E)(1). `electrical.laundry_receptacle`: (F).
    `electrical.hallway_receptacle`: (H).
  - `code.NEC_210_52_E3_balcony_receptacles`: (E)(3), qualifying by the 4 in. distance
    with no door test.
  - `code.NEC_210_52_G_garage_receptacles`: (G)(1).
  - `_counts_toward_210_52` applies the switched and 5½ ft exclusions; (E) keeps its own
    6½ ft.
  - Owner's reading of (C)(1) Ex. 2 (2026-11-13): window glass at the dining counter counts
    as "can't be installed", and the check passes it with an AHJ note.
  - Known gaps, not graded:
    - (A)(2)(iii), (A)(5), multioutlet counting, (B), (G)(2)/(3), (I) (no foyer occupancy).

**210.63 Equipment needing service.** A 125 V 15 or 20 A receptacle, accessible, within
25 ft of the equipment. For HVAC and refrigeration equipment it must be on the same level
  and not on the load side of its disconnect (full text in `nec-2026-paraphrase-210-422-410.md`).
- **Engine:** (A) `electrical.hvac_service_receptacle`; (A) also grades refrigerators
  (`refrigerator` symbol, own outlet via `Appliance.plugs_into` excluded); the ERV is
  ventilation, not graded (AHJ). (B) not applicable to a dwelling.

## 705.12 Load-side source connections

Busbar and feeder currents are the maximum circuit currents from 705.28(A).

- **(A) Feeders.**
  - (1) Ampacity of at least 125% of the source's output current.
  - (2) Downstream of a connection that isn't at the far end, the feeder needs either an
    ampacity of at least the primary OCPD plus 125% of the source current, or an OCPD
    after the connection that is no larger than the feeder's ampacity.
  - (3) Taps: at least ⅓ of the feeder OCPD plus the source OCPDs.
- **(B) Busbars** (no listing for combined sources). Any one of these is enough:
  - (1) 125% of the source output current plus the busbar OCPD does not exceed the bus
    rating.
  - (2) Where the source and the primary feed sit at opposite ends of a bus that carries
    loads: (a) that same sum stays within 120% of the bus rating, and (b) a permanent
    label next to the source OCPD warns against moving it.
  - (3) The sum of every OCPD on the panel, load and supply, not counting the busbar's own,
    stays within the bus ampacity. The busbar OCPD is no larger than the bus, and a label
    is required.
  - (4) A center-fed dwelling panel may take the connection at either end, using the (2)
    arithmetic and the label.
  - (5) Feed-through conductors follow (A).
  - (6) Other arrangements are allowed under engineering supervision.
- **Engine:** `code.NEC_705_12_interconnection`.
  - The source term is 125% of the inverter's `inverter_kw_continuous` output current;
    with no inverter, the breaker rating stands in.
  - It tries (B)(1) first, then (B)(2)(a). A (B)(2)(a) PASS says the opposite-end
    placement and the (b) label are not modelled.
  - (B)(3)–(6) and (A) are not tried.

## 722.15 Separating limited-energy cables

- **(A)** Limited-energy cables keep 2 in away from power, Class 1, non-power-limited fire
  alarm and medium-power broadband conductors, and stay out of their raceway, enclosure or
  box, unless (B)–(K) relaxes it.
- (B)–(K) relax it for: a barrier or listed divider; a raceway inside the enclosure; power
  conductors that are there only to feed the limited-energy equipment, or circuits at 150 V
  or less to ground under conditions; a fixed nonconductor such as tubing; manholes, cable
  trays and functionally associated Class 1 circuits. Under (G), no separation is needed if
  either side runs in a raceway or in metal-sheathed, metal-clad, NM or UF cable (Type AC
  on the power side, Type TC on the limited-energy side).
- **Engine:** structural, and `electrical.limited_energy_wiring` (ADVISORY). `ConduitRun.service`
  is single-valued, so a modeled raceway can't carry both, which (A) forbids without (B)–(K);
  the check flags a data or `power_24` run that names a power circuit. Spacing between cables
  is not graded, and (G) means it rarely binds in a house. The rest of Article 722 is in
  `nec-2026-paraphrase-722.md`.

## 690.12(C) Rapid-shutdown initiation (TIA 26-2, printed)

For one- and two-family dwellings, the initiation device goes in a readily accessible spot
outdoors.
- **Engine:** `code.NEC_690_12_initiation` (2026-11-14): the `rsd_initiator` device lies in no
  room. Catlin's `ED-M-RSD-INIT` stands outdoors beside the meter: PASS. The rest of 690.12
  and 705.10-705.25 are in `nec-2026-paraphrase-690-705-710.md`.

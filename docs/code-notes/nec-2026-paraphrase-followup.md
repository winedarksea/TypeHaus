# Electrical rules the engine grades: follow-up read (2026 NEC)

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

Continues `nec-2026-paraphrase.md` (same conventions). The owner read these printed pages on
2026-11-14; the photographs were transcribed by the assistant, so numbers are as read from the
print and worth a second glance. Pages: Article 100 (the E-F and L definitions, incl. Feeder);
120.1-120.5 and 120.41; 210.19(C)-210.21; 215.10(B)-215.18; 225.1-225.10; the raceway articles
342, 344, 352, 356 (tail), 358, 362 and 366; 410.138-410.154 (Part XIII, lighting track); and
720.32, 721.1, 721.30. Check added: `mep.raceway_use` (`checks/mep/raceway_use.py`).
Tests: `test_nec_followup.py`. Constants: `typehaus.model.nec.NEC`.

## Catlin, read against these pages

- **The laundry track (`ED-M-LAUNDRY-TRACK`) is lighting track and passes 410.10(D)(1).** Article
  100 defines lighting track as a manufactured assembly designed to support and energize
  luminaires that can be readily repositioned along it, its length changeable by adding or
  removing sections; the PureEdge TS24M-2C magnetic rail fits, and 24 V dc exempts nothing
  (410.10(D)(1) has no voltage limit; 411.4(B) is a cap). It stands 1.1 ft in plan from
  `FX-M-BATH2-TUB`, but in `RM-M-LAUNDRY`, behind a wall from the tub's `RM-M-BATH2`. 410.10(D) is
  the area around the tub, so another room is outside it and 410.150(C)(9) does not reach the
  track. The check had measured straight through the wall; it now grades only luminaires in the
  tub's own room (`room_owning`; an unresolved room stays UNKNOWN). Corrected 2026-11-14.
  The rest of 410.150(C), read against the track: (C)(1), (6), (7) not engaged (surface-mounted,
  one 36 in. section inside the room, indoors); (C)(2) damp or wet: only bathrooms and the
  exterior are classed so in the model, and a laundry is not normally a damp location (AHJ's
  call, unmodelled); (C)(8) exempt twice (24 V, and the rail is about 8.5 ft up). (A) is met
  (permanently connected through `ED-M-LAUNDRY-PSU`, only heads on the rail, no receptacle); (D) the
  heads are the rail's own family (`PROD-PUREEDGE-T24M-*`); 410.153 N/A (under 2 A). (B) has a
  gap: the rail's own rating is not authored (below).
- **215.18: every feeder panel holds an SPD.** The meter-main `ED-M-METER` (Type 1,
  `ED-M-SPD`, 230.67) feeds `ED-B-PANEL` and `ED-B-PANEL-2` by feeders, and a third source feeds
  `ED-B-BACKUP-PANEL`. Each holds a plug-on Type 2 SPD breaker (`CKT-SPD`, `CKT-SPD-2`,
  `CKT-SPD-BACKUP`), so 215.18(B) (in or beside the equipment holding the branch OCPDs) is met
  by all three: the existing `code.NEC_215_18_spd` already grades it per panel, three PASS.
  - **The backup panel.** It is fed from the 12kPV's load port, not from the service. Article 100
    (read in print 2026-11-14) defines a feeder as all circuit conductors between the service
    equipment, the source of a separately derived system, or *other power supply source*, and the
    final branch-circuit OCPD. The inverter's load-port conductors to `ED-B-BACKUP-PANEL` are a
    feeder, so 215.18 reaches that panel; `CKT-SPD-BACKUP` already meets it (PASS). The hedge is
    closed. No code change: `code.NEC_215_18_spd` grades every panel holding branch breakers
    without asking where its supply comes from, and `NEC.MICROGRID_CONNECTIONS` (705.60) names
    the same conductors as source output conductors, a second rule on one wire. Its other 215
    clauses (215.2-215.5) wait on the conductor sizes of owner question 2.
  - **Graded:** 215.18(C) Type 1 or 2 and (E) In of 10 kA or more, via `Circuit.spd_type_ref`
    (`CKT-SPD-BACKUP` UNKNOWN, no product). Owner question: confirm each plug-on's marked In
    (and the FS140's, 230.67(E)).
- **225.10 wiring on buildings.** `electrical.outdoor_branch_wiring`: `CKT-GAR-FEEDER` PASS
  (EMT/PVC); the garage's branch circuits stay in their own building. The exposed Class 2 and data runs
  (`CD-M-RSD-INIT`, `CD-M-DATA-PORCH`, `CD-M-DATA-CAM-PORCH`, `CD-M-DATA-CAM-CANOPY`) fall under
  Article 722, not 225.10. `mep.raceway_use` grades 225.10 on any run that appears (EMT and PVC
  pass, ENT is flagged).
- **ENT (362.12): none in earth.** The four derived floor-heat ENT runs
  (`FH-M-BATH2-SENSOR`/`-COLD-LEAD`, `FH-S-BATH1-SENSOR`/`-COLD-LEAD`) all sit in walls and
  floors above grade, concealed and dry or damp (362.10(4)). `mep.raceway_use` PASS.
- **PVC expansion (352.44): none exposed.** The two PVC runs (`CD-B-V2H-SPARE`, `CD-B-V2H-GAP`)
  are indoors, in a wall or in earth. A future exposed run longer than about 5 ft needs an
  expansion fitting at the assumed 130 degF swing (Minnesota roughly -20 to 110 degF surface).
  The check reads the whole exposed length as one straight run (straps are counted at table
  spacing, not placed): conservative, ADVISORY only.
- **Buried EMT (358.10(B)(1)).** `CD-B-GAP-EV` is EMT in earth and under the slab. Galvanized EMT
  there needs corrosion protection that is also approved as suitable for the condition; nothing
  is authored. `electrical.underground_raceway` (UNKNOWN) now cites 358.10(B)(1) instead of "358.10
  unread" (Article 300 owner question 2 in `plans/TODO-nec-2026.md`). The V2H PVC is allowed
  buried by 352.10(H) and needs Schedule 80 where it rises through a damage-prone spot
  (352.10(K)); the model holds only `pvc`, still UNKNOWN.
- **Support spacing is a standing limit.** Tables 344.30(B), 352.30(B), 358.30, 342.30 and
  362.30: `resolve/conduit_fittings.straps_for` counts and bills straps at table spacing, so the
  bill meets them by construction; no strap is placed, so there is nothing further to grade.
- **120.5(C) floor area.** `nec_floor_area_ft2` returns the conditioned floor area, 4,898 ft2,
  measured to the sheathing with the basement in. 120.5(C) reads the OUTSIDE dimensions of each
  floor (cladding side) and leaves out detached garages, open porches and unfinished areas that
  cannot become habitable. The two differ both ways: outboard layers add perhaps 3-5% (a rough
  estimate, not measured); the conditioned unfinished rooms `RM-A-EAST-UNFIN` (445 ft2) and `RM-A-POCKET` (121 ft2)
  are adaptable (the suite is meant to be finished later), so they stay in. At 2 VA/ft2 and the
  40% tier either way is a few hundred VA, under 2 A at 240 V, against 170 A of demand on 200 A
  mains: no change. The engine keeps its CFA; the 120.82 oracle notes already say so.
- **120.41 / 120.82(B)(1).** 2 VA/ft2 (22 VA/m2) is `GENERAL_LIGHTING_VA_PER_FT2`. Pinned in
  `test_nec_followup.py`; `FLOOR_AREA` and `GENERAL_LIGHTING_STANDARD` are anchors, no check reads
  them (the `electrical.service_load` finding states its own basis).
- **210.21(B)(2) cannot be graded.** `CKT-WORKSHOP-240` and `CKT-KETTLE` put two receptacles on a
  circuit (a 20 A circuit with 20 A receptacles caps the cord-and-plug load at 16 A). The authored
  4,800 VA of `CKT-WORKSHOP-240` is a capacity allowance (20 A x 240 V), not a nameplate load, so
  there is nothing to compare; it joins owner question 1 (continuous or not). `electrical.
  single_receptacle_rating` keeps (B)(1) only.

## Article 100 (E-F and L definitions)

- **Feeder:** all circuit conductors between the service equipment, the source of a separately
  derived system, or other power supply source, and the final branch-circuit OCPD (CMP-10).
  Engine: reached by 215.18 on the backup panel (Catlin reading above). **Feeder assembly** is the
  overhead or under-chassis feeder conductors with fittings, or a mobile-home power-supply cord
  assembly: not relevant. **Equipment branch** (a feeder-and-branch system on delayed or manual
  alternate-source connection, mainly 3-phase power equipment, Art. 517), **Exposed** (live parts,
  wiring methods, optical fibre, accidental contact), **Externally operable**, **Fault current**
  and **available fault current**, **Fault-managed power** (Class 4; monitors faults and limits
  fault energy, 726) and **Fault protection device** (network-powered broadband): terms only,
  nothing new to grade. **Essential electrical system, Explosionproof equipment, On-site power
  production facility, Equipment, signal / portable, Equipotential plane, Equipment rack:** not
  used by any Catlin check.

## Article 100 (L definitions)

- **Lighting track (track lighting)** (CMP-18): a manufactured assembly designed to support and
  energize luminaires that can be readily repositioned on it; its length can be altered by adding
  or removing sections. Engine: `bath_luminaire_zone` forms `track`.
- **Limited-energy system:** equipment and cables of an end-to-end system that are power
  restricted or can limit or shut down the source to keep deviations above normal limits from
  becoming a shock or fire hazard. An informational note names Class 2, 3 and 4, PLFA and
  communications. Engine: Article 722 checks (`nec-2026-paraphrase-722.md`).
- **Laundry area:** an area containing or designed to contain a laundry tray, washer or dryer.
  **Kitchen:** an area with a sink and permanent provisions for food preparation and cooking.
  **Lighting outlet; Labeled; Island mode; Inverter output circuit; Inverter utilization output
  circuit** (a multimode or stand-alone inverter to utilization equipment, Article 706). Terms only,
  nothing new to grade; the island-mode and inverter-output terms match
  `nec-2026-paraphrase-702-705-island.md`.

## Article 120

- **120.1** Scope: Parts I-VIII. **120.4** Table 120.4 points to the specific-purpose
  calculations (already in `nec-2026-paraphrase.md`).
- **120.5(A)** Nominal voltages for branch and feeder calculations: 120, 120/240, 208Y/120, 240,
  347, 416Y/240, 480Y/277, 480, 600Y/347 and 600 V. (B) A load may be rounded to the nearest whole
  ampere, fractions under 0.5 dropped. (C) Floor area is taken from the outside dimensions of each
  floor of the building or unit; for a dwelling, detached garages, open porches and unfinished
  areas not adaptable to future habitable or occupiable use are excluded. (D) For dc, VA equals W.
- **120.41** The dwelling minimum unit load is at least 22 VA/m2 (2 VA/ft2). It covers (1)
  general-use receptacles of 20 A or less, including the 210.11(C)(3) and (C)(4) circuits, (2) the
  210.52(E) and (G) outlets, and (3) the 210.70 lighting outlets: no further calculation for
  those. The minimum lighting load is that unit load times the 120.5(C) area. Motors under 1/8 hp
  on a lighting circuit are part of it. 120.42-120.45 are non-dwelling (Table 120.42(A)).
- **Engine:** 120.5(C)'s area and 120.41's unit load are what `service_load_summary` uses
  (Catlin reading above); 120.5(B) rounding is applied to `demand_amps` (the service and
  per-panel feeder demand), to the nearest whole ampere with fractions under 0.5 dropped;
  non-dwelling parts are not applicable.

## 210.19(C)-210.21 (re-read; matches `nec-2026-paraphrase-210-422-410.md`)

- **210.19(C)** A range of 8 3/4 kW or more takes at least a 40 A branch circuit; Ex. 1 taps from a
  circuit of 50 A or less carry at least 20 A; Ex. 2 the range neutral may be 70% of the circuit
  rating, not under 10 AWG. **(D)** Other loads: ampacity enough, not under 14 AWG (tap
  exceptions). **210.20** (A) OCPD at least the noncontinuous load plus 125% of the continuous
  (a 100%-listed assembly is excepted); (B) conductor protection per 240.4; (C) equipment; (D)
  outlet devices per 210.21.
- **210.21(A)** A lampholder on a circuit over 20 A is heavy duty: at least 660 W (admedium) or 750 W
  (other). **(B)(1)** A single receptacle on an individual circuit is rated at least the circuit
  (Ex. 430.81(B), arc welders). **(B)(2)** The total cord-and-plug load on a multi-receptacle circuit
  follows Table 210.21(B)(2): 15 or 20 A circuit with 15 A receptacle 12 A; 20/20 16 A; 30/30
  24 A. **(B)(3)** Receptacle ratings follow Table 210.21(B)(3), or the circuit rating above 50 A (the
  table body and 210.22-210.25 are in `nec-2026-paraphrase-210-422-410.md`). **(B)(4)** A range receptacle may follow the 120.55 single-range
  demand.
- **Engine:** (A) not applicable (no circuit over 20 A feeds a lampholder); (B)(1) graded; (B)(3) graded
  by `electrical.multi_receptacle_rating`; (B)(2) is the gap above. (B)(4): Catlin's range is a 14-50R on 40 A, graded under (B)(1).

## 215.10(B)-215.18 and 225.1-225.10

- **215.10** GFPE for a feeder disconnect of 1000 A and up has exceptions for a continuous
  industrial process, an upstream GFPE and temporary generator feeders of 90 days or less.
  **(B)** A solidly grounded dc feeder disconnect of 1000 A or more above 150 V to ground gets it.
  Catlin: N/A by rating (320 A service).
- **215.11** Autotransformers on feeders. **215.12** Identification: (A) grounded conductor per
  200.7; (B) EGC per 250.119; (C)(1) one voltage system per 310.6(A)(3); (C)(2) more than one
  system, each ungrounded conductor identified by phase or line and system at terminations, the
  means documented or posted at each panelboard; (C)(3) a dc system over 60 V marks polarity,
  red or + for positive and black or - for negative, at 24 in. intervals or less. **215.13** The
  AHJ may require a feeder diagram (area, load before and after demand factors, conductor size
  and type). **215.14** A common neutral serves up to three 3-wire or two 4/5-wire feeders in one
  metal raceway (300.22). **215.15** Barriers in feeder-tap panelboards.
- **215.18 Surge protection.** (A) Where feeders supply dwelling units (and dormitories, guest
  rooms, nursing-home sleeping areas, fire or police sleeping quarters), an SPD is required. (B)
  It sits in or next to the distribution equipment, on the feeder's load side, that holds the
  branch-circuit OCPDs for those spaces. (C) Type 1 or Type 2. (D) It applies when that equipment is
  replaced. (E) In of 10 kA or more. **Engine:** `code.NEC_215_18_spd` grades (B) per panel;
  (C)/(E) graded via `Circuit.spd_type_ref`: QO2175SB 10 kA PASS, HOM2175SB 10 kA PASS,
  `CKT-SPD-BACKUP` UNKNOWN (no product). `NEC.FEEDER_SPD = "215.18"` is confirmed.
- **Not graded, no data:** 215.12 (no conductor colors or dc feeder; the PV dc runs are 690
  circuits, 705.25(B) covers their polarity), 215.13 (a diagram, if the AHJ asks, is `haus
  calcs`' load summary), 215.14 (each feeder has its own neutral), 215.15 (no feeder-tap panel).
- **225.1** Scope: outside branch circuits and feeders, on or between buildings and structures.
  **225.4** Conductors within 10 ft of a building are insulated or covered. **225.6** Overhead
  spans: 10 AWG Cu or 8 AWG Al to 50 ft, 8 Cu or 6 Al longer. No overhead conductor is modelled.
- **225.10 Wiring on buildings.** Permitted methods include auxiliary gutters, busways, cable
  trays, cablebus, EMT, FMC, IMC, LFMC, LFNC, messenger-supported wiring, open wiring on
  insulators, RTRC, RMC, PVC and MC (the transcription trailed off, so ENT is not on the list as
  read). `mep.raceway_use` grades it for drawn exterior power runs.
  `electrical.outdoor_branch_wiring` grades each circuit that leaves its panel's building: a
  drawn EMT/PVC route passes, ENT is UNKNOWN, an undrawn route is UNKNOWN per building, and
  N/A needs every consumer in its panel's building.

## 410.138-410.154 (Part XIII lighting track) and 410.139-410.146

- **410.138-410.146 (read, none applies):** **410.150(A)** **410.153** **410.154** *(summary kept local)*
- **Engine and Catlin:** `electrical.bath_luminaire_zone` grades (C)(9) through 410.10(D)(1)
  (`NEC.LIGHTING_TRACK_LOCATIONS`) for a track in the tub's own room. The laundry rail is the only track. Nothing else is graded:
  (B) needs the rail's rating, authored nowhere (`TrackLightingSpec` holds geometry and the
  product ref only). The load is two 11 W heads, 22 W (0.9 A at 24 V) on a 40 W supply
  (`electrical.point_luminaire_psu` grades the supply at 125%: 27.5 W, PASS), the supply's own
  ceiling 1.7 A at 24 V; so (B) passes if the rail is rated at least 1.7 A (owner question 11(d)).
  410.154 needs fastening points the model lacks (a 36 in. section takes two).

## 720.32, 721.1, 721.30

- **720.32** No box or conduit body is needed where a cable enters or leaves a conduit or tubing
  that only supports or protects it from damage; a fitting on the end(s) protects the cable
  from abrasion. Note only (no such run is modelled with a cable inside).
- **721.1** Scope: power-source requirements for limited-energy systems.
- **721.30 Class 2 and 3 sources.** **(A)** The source is one of: (1) a listed Class 2 or 3
  transformer; (2) a listed Class 2 or 3 power supply; (3) other listed equipment marked as a
  Class 2 or 3 source (thermocouples need no listing; limited-power circuits of listed equipment
  within Chapter 9 Tables 11(A)/(B) are excepted; informational examples are a listed circuit
  card, a listed current-limiting impedance with a non-power-limited transformer or battery, and
  limited circuits of industrial controls); (4) a listed audio/video, IT, communications or
  industrial equipment limited-power source (UL 62368-1, UL 60950-1 and similar); (5) a battery
  source or battery system listed and identified as Class 2. **(B)** The output connections of
  Class 2 or 3 sources are not paralleled or otherwise interconnected unless listed for that.
  **(C)** The supplying equipment is durably marked, plainly visible, to show each circuit that is
  Class 2 or 3. Sources in (A)(3) and (A)(4) carry a label of the maximum voltage and rated current
  per conductor for each connection point (one label if all points are rated alike). The
  informational note ties that rated current to 722.140(B).
- **Catlin.** 411.6(A) (concealed low-voltage lighting wiring) and the PoE bundle arithmetic
  rest on the sources being Class 2. The model records no listing or Class 2 mark:
  `ElectricalDeviceType` has `output_voltage` and `load_va` only, so 721.30(A) and the (C) label
  are not graded. **One field would do it**: a `limited_energy_class` (`"2"`/`"3"`/`None`) beside
  `output_voltage`; a check could then grade (A) from it and derive the (C) label (voltage, and
  amperes per conductor as `load_va / output_voltage`). Cheap but not built; owner question 11(d).
  Two things the data shows: the 200 W driver (`ED-T-LT-PSU-200`, catalog-only, no instance) is
  above the ~100 VA a Class 2 source holds to (Chapter 9 Table 11 unread), so it could not be the
  Class 2 source 411.6(A) names; and 721.30(B) cannot be violated in the model, since `psu_ref`
  (on a device or a `LightRun`) names one supply, so no load is fed by two supplies. A supply
  feeding several loads is not paralleled outputs.

## Raceway articles (all numbered .24 for bends and .30 for support in the 2026 print)

The old `.26` bend numbers in `model/nec.py` (`IMC_BENDS`, `RMC_BENDS`, `PVC_BENDS`, `EMT_BENDS`,
`ENT_BENDS`) were wrong for 2026 and are fixed to `.24`; `mep.conduit_bend_total` cites 300.24
first, then the article's `.24`. Every article caps bends between pull points at 360 degrees and
sets the radius by Chapter 9 Table 2.

| | Article | Use and limits | Support | Size |
|---|---|---|---|---|
| IMC | 342 | in concrete, earth or direct burial or severe corrosion only with approved corrosion protection (342.10(B)); wet-location supports corrosion resistant; dissimilar metals (342.14) | fasten within 3 ft of a box (5 ft where the structure prevents it); spacing 10 ft; with threaded couplings per Table 344.30(B); risers 20 ft; horizontal through framing 10 ft (342.30) | 1/2 to 6 |
| RMC | 344 | same structure; may be the EGC (344.60); bushings (344.46) | Table 344.30(B): 1/2-3/4 in. 10 ft; 1 in. 12 ft; 1 1/4-1 1/2 14 ft; 2-2 1/2 16 ft; 3 and up 20 ft | 1/2 to 6 |
| PVC | 352 | direct burial and encased (352.10(H)); Schedule 80 where subject to physical damage (352.10(K)); not above 50 degC (122 degF) unless listed (352.12(D)); bends with identified equipment | 3 ft of a box; Table 352.30(B): 1/2-1 in. 3 ft; 1 1/4-2 5 ft; 2 1/2-3 6 ft; 3 1/2-5 7 ft; 6 in. 8 ft | 1/2 to 6 |
| LFNC | 356 | bends 360 degrees (356.24(B)) | fastened within 12 in. of a box and at 3 ft intervals for runs over 6 ft | |
| EMT | 358 | in concrete, earth or severe corrosion only per 358.10(B): galvanized or stainless with approved corrosion protection that is also approved for the condition (B)(1); aluminum needs approved supplementary protection (B)(2); not for severe physical damage or luminaire support (conduit bodies excepted); no field threading; reamed | 10 ft and within 3 ft of a box (5 ft where the structure prevents); horizontal through framing 10 ft (358.30); concrete-tight fittings in masonry or concrete; EMT may be the EGC (358.60) | 1/2 (3/8 motor leads) to 6 |
| ENT | 362 | concealed dry or damp (362.10(4)), in or under concrete, slabs on grade on sand with identified fittings; not in direct earth burial, not exposed except per 362.10(1), (5), (8), not in luminaire support, not above 50 degC unless listed, not in direct sun unless resistant (362.12) | 3 ft and within 3 ft of a box; listed cable ties; exceptions of 6 ft to luminaires or equipment in an accessible ceiling, and fishing (362.30) | 1/2 to 2 1/2 |
| Aux. gutter | 366 | no more than 30 ft beyond the equipment they supplement; do not enclose switches or OCPDs | | |

- **PVC expansion (352.44).** A fitting goes where the Table 352.44 growth between secured points
  reaches 1/4 in. The coefficient is 3.38 x 10^-5 in./in./degF; growth in inches per 100 ft is
  0.04056 times the temperature change in degF (50 degF 2.03 in.; 100 degF 4.06; 150 degF 6.08; 200
  degF 8.11). A 130 degF swing grows 1/4 in. in about 4.7 ft; 100 degF in 6.2 ft.
- **Engine:** bends `mep.conduit_bend_total`; use and expansion `mep.raceway_use`; buried EMT
  `electrical.underground_raceway`; fill `mep.raceway_fill` (Ch. 9). Straps, couplings and
  connectors are derived and billed at table spacing (`resolve/conduit_fittings`), never placed,
  so support spacing is a standing limit; bushings, joints and wet-location fittings are not
  graded. Constants: `NEC.EMT_SUPPORT`, `PVC_SUPPORT` and the rows above.

## Still unread

410.154 past "two supports" (the rest of the clause); 300.2-300.3; 300.9(A)(2)-300.21; 300.25(C) onward;
680.27(B)-680.33; 250.64; 250.53(A)(4); 406.9(B) opening, 406.14, 408.4, 406.48-406.50 numbering;
the sauna heater article; 705.3-705.4; 705.81 onward; Table 625.52(B)(1); 230.4(B)-(D); 230.93
onward; minor PV (690.3, .5, .10, .14, .35-.40, .46, .48-.55); 725.127; 445 beyond 445.12;
723.20 body; 724.46. (`plans/TODO-nec-2026.md` keeps the live list.)

# Electrical rules the engine grades: Article 250, grounding and bonding (2026 NEC)

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

Continues `nec-2026-paraphrase.md` (same conventions). The owner read 250.30-250.64 and
250.84-250.94 in print on 2026-11-14, and the other rows here on 2026-11-13. Each rule has an
**Engine** line. The checks are in
`checks/mep/electrical_grounding*.py`; basis and hand oracle in
`houses/catlin/notes/grounding_bonding.md`. 690.47 is now a printed read (2026-11-14), in
`nec-2026-paraphrase-690-705-710.md`.

## Catlin's grounding, as authored (read from `plan/electrical_grounding.py`, 2026-11-14)

- **House electrodes:** `GE-B-UFER` (35 ft of #4 HDG bar in `FT-B-W1`/`FT-B-W2`), rods
  `GE-B-ROD-1`/`-2` (8 ft, 14 ft 4 in. apart, 24 in. below grade), all three bonded to
  the meter-main by `BC-M-GEC-ROD` (#6 Cu) and `BC-M-GEC-UFER` (#2 Cu): each GEC is the sole
  connection to one electrode type, so the 250.66(A)/(B) caps are the whole requirement. No
  metal underground water pipe (the service is PEX). Lightning terminals and the #2 Cu
  counterpoise are bonded in, and the rods and counterpoise stand more than 6 ft from
  the garage rods.
- **Earth contact of the Ufer is open:** the footings sit on 7 in. of washed stone over
  geotextile with 4 in. side foam, which the 250.52(A)(3) note says hinders direct contact.
  `code.NEC_250_52_ufer` returns UNKNOWN for that reason (the AHJ's reading); the rods
  qualify either way, so the electrode system stands without it. No redesign.
- **Two mains, one enclosure:** the meter-main is one Class 320 enclosure holding two 200 A
  mains, each feeding a panel through 4/0 Al SER. 250.64(D) is written for disconnects in
  separate enclosures; if the AHJ treats the compartments as that, (D)(1)'s summed-area basis
  applies (2 x 4/0 Al = 423 kcmil, Table 250.66 row: #2 Cu). The 310.12(A) service-conductor
  size (300 Cu / 400 Al on 320 A; 400 Cu / 600 Al on 400 A) gives #2 Cu or #1/0 Cu (see 310.12
  in `nec-2026-paraphrase-310.md`). Each installed GEC is capped by 250.66(A)/(B) at
  #6/#4, so every basis passes. `SE-M-SERVICE` gives the basis (310.12(A) on 320 A, or the
  summed 2 x 4/0 Al): Table 250.102(C)(1) gives #2 Cu, and the three water bonds and
  `BC-M-GEC-UFER` are now #2 Cu. A lateral over 500 kcmil Al / 350 Cu would raise the water
  bond to 1/0. Both Cu-jumper cells were read from the printed table.
- **Garage:** a separate building with its own pair of 8 ft rods (`GE-G-ROD-1`/`-2`, 16 ft
  apart). Fed by one feeder (`CKT-GAR-FEEDER`, see 225.30 in `nec-2026-paraphrase-230-314.md`);
  GEC #6 on `ED-G-PANEL`'s ground bar (250.32(E): #2 Cu gives #8); neutral isolated there;
  `ED-G-IBT` bonded to the panel; plug-on SPD `CKT-SPD-GAR` (HOM2175SB, house standard, not
  required by 215.18). The old garage SPD (Leviton 51120-1, discontinued, 3 kA) is removed; the
  garage's SPD is now the subpanel's plug-on.

## Separately derived systems and separate buildings

**250.30(B)-(C) Ungrounded separately derived systems.** *(summary kept local)*
- **Engine:** not graded. 250.30(A) (grounded systems) was not among the pages read, and the
  EG4 inverter's islanded output is not modelled as a derived system.

**250.32 Buildings supplied by a feeder or branch circuit.**
- **(A) Electrodes.** The building has its own electrode system and GEC per Part III.
  Ex.: none is needed where a single branch circuit (a multiwire one counts) supplies it
  and that circuit includes an EGC.
- **(B)(1) Grounded systems.** The EGC runs with the supply, to the building disconnect's
  enclosure and the GEC, and sizes per 250.122; the grounded conductor is not connected to
  the EGC or electrodes there. Ex. 1 keeps the old connected-neutral arrangement where it
  already existed and no continuous metal path, no ground-fault protection upstream and no
  EGC run with the supply holds; the neutral is then at least the larger of the 120.61 neutral
  load and the 250.122 EGC. Ex. 2: system bonding jumpers per 250.30(A)(1) Ex. 2.
- **(B)(2) Separately derived source:** with OCPD at the source, follow (B)(1); without it,
  250.30(A).
- **(C) Ungrounded systems.** The same, with the electrodes also tied to the disconnect.
- **(D) Disconnects remote from the building** (225.31(B) Ex. 1-2, 700.12(C)(4), 701.12(C)(3),
  702.12): no grounded-conductor connection to electrodes or metal, EGCs and bonding run
  with the circuit conductors, and EGC-to-GEC joints are made in a box or enclosure at the
  building.
- **(E) GEC size:** per 250.66 on the largest ungrounded supply conductor, with Part III.
- **Engine:** traces crossing circuits and feeders (a PANEL in a non-service building); a
  PANEL naming its feeder (`circuit=`) is traced and the feeder's EGC is graded. A
  feeder or more than one circuit requires a bonded electrode system. Each supply circuit must
  carry `egc_awg` (UNKNOWN if not); the single-circuit exception requires that EGC. The (B)(1) no-neutral-bond rule is read by
  `code.NEC_250_24_neutral_bond`. A multiwire circuit is still counted per circuit.
  Catlin's garage passes on its rod pair.

**250.34-250.36 Generators and impedance-grounded systems.** *(summary kept local)*
- **Engine:** not graded; none applies to a dwelling.

**250.24 Service-supplied systems.** In short: each service bonds its grounded conductor to
a GEC somewhere between the load end of the drop or lateral and the neutral terminal at the
disconnect. An unspliced main bonding jumper (250.28) goes in each service-disconnect
enclosure. The grounded conductor runs to every service disconnect, sized at least per Table
250.102(C)(1). The GEC (250.66) ties the EGCs, the enclosures and the grounded conductor to
the Part III electrodes. Downstream of the service disconnect, the grounded conductor is
never re-bonded to metal or to earth.
- **Engine:** `code.NEC_250_24_neutral_bond` reads `ServiceEntrance.main_bonding_jumper_ref`
  (it must be the service disconnect) and `neutral_isolated_refs` (every panel a circuit names,
  plus outbuilding panels; UNKNOWN if not stated).

**250.28 Main and system bonding jumpers.** A wire, bus or screw of copper, aluminum,
copper-clad aluminum or another corrosion-resistant material. If the jumper is only a
screw, it is green and visible. Sized at least per Table 250.102(C)(1).
- **Engine:** the jumper is read by `code.NEC_250_24_neutral_bond` (see 250.24); 250.28 jumper
  material and size are not graded.

## Part III: grounding electrodes

**250.50 Electrode system.** Every electrode of the 250.52(A)(1)-(7) kinds present at the
building is bonded into one system. If none exists, one or more of (A)(4)-(8) is installed.
Ex.: an existing building's concrete-encased electrode need not join if its rebar can't be
reached without breaking the concrete.
- **Engine:** `code.NEC_250_50_electrode_system` requires every authored electrode, the Ufer
  claimed by a footing bar, and any metal underground water pipe to be bonded to the service.

**250.52(A) Permitted electrodes.**
- (1) Metal underground water pipe in contact with earth for 10 ft or more, electrically
  continuous (bonded around insulating joints). (2) Metal in-ground support structures (piles,
  casings) in vertical contact for 10 ft or more; bond only one of several.
- **(3) Concrete-encased.** At least 20 ft of either (1) bare, zinc-galvanized or other
  conductive-coated rebar of at least 1/2 in., in one continuous length or pieces tied by
  steel wire, welding or the like, or (2) bare copper of 4 AWG or larger. The metal has at
  least 2 in. of concrete round it, lies inside the part of a foundation or footing in direct
  contact with the earth (or in a vertical foundation in contact), and only one of several is
  bonded. The informational note says insulation, vapour barriers and films hinder that contact.
- (4) Ground ring: 20 ft of bare Cu, 2 AWG or larger, round the building in earth contact.
  (5) Rod or pipe: 8 ft or longer; pipe at least trade size 3/4 (galvanized or coated if steel);
  stainless or Cu/zinc-coated steel rods at least 5/8 in. unless listed. (6) Other listed
  electrodes. (7) Plate: 2 sq ft of soil exposure; 1/4 in. iron or steel, or 0.06 in. nonferrous.
  (8) Other underground metal systems or tanks not bonded to a water pipe.
- **(B) Never:** metal gas piping, aluminum, or the pool structures of 680.26(B)(1)-(2).
- **Engine:** `code.NEC_250_52_ufer` grades the bar (20 ft of #4 or larger conductive-coated bar, 2 in. of bottom cover;
  side and top cover are not read) and the earth contact: a wall host is "no"; a footing on a geotextile stone bed or with side foam is
  UNKNOWN ("the AHJ's reading"); otherwise yes. That is the informational note, graded as far as
  the model can go. Rod length and diameter come from `GroundingStandard`; rods, plates, rings,
  (1) water pipe (PEX is not an electrode) and (2)/(6)/(8) are partly or not modelled.

**250.53 Installation.**
- (A) Rods, pipes and plates are free of paint and enamel, and are driven below the permanent
  moisture level where practicable. **(2)** One alone gets a supplemental electrode (any
  250.52(A)(2)-(8) kind) bonded to it, the GEC, the grounded service conductor, a nonflexible
  grounded service raceway or enclosure, or per 250.32(B); no supplement is needed if it
  measures 25 ohm or less. **(3)** Several are at least 6 ft apart (efficiency is best at
  twice the longest rod's length). **(4)** 8 ft in the soil, driven vertically (Ex. 1: rock, at
  up to 45 degrees; Ex. 2: rock, laid in a trench at least 30 in. deep); the top is flush with or
  below grade unless the connection is protected (250.10). **(5)** Plates at least 30 in. deep.
- **(B)** Electrodes of different grounding systems (including strike-termination ones) that
  are rods or plates stand at least 6 ft apart.
- **(C)** Jumpers between electrodes follow 250.64(A), (B) and (E), size per 250.66 and connect
  per 250.70. Rebar is never the conductor between electrodes.
- **(D)** A water-pipe electrode's continuity does not rely on meters or filters, and it is
  supplemented by another 250.52(A)(2)-(8) electrode bonded as in (A)(2) (Ex.: interior water
  piping per 250.68(C)(1)).
- **(E)** The part of a jumper that is the sole link to a rod, pipe or plate is no larger than
  6 Cu or 4 Al. **(F)** A ground ring lies at least 30 in. below grade.
- **Engine:** `code.NEC_250_53_rods` grades 8 ft rods, (A)(4) 8 ft in the soil and top at or
  below site grade (rods are plumb by construction; the Ex. drive angles are not modelled),
  (A)(2) supplement, (A)(3) spacing within a system (`GroundingStandard.min_rod_spacing`), (B)
  6 ft from the rods of another building or use (lightning terminals included), and (D) a
  metal water-pipe electrode's supplement (N/A on a non-metal service). Catlin's rods pass.
  Not graded: (A)(5) plates, (F). The (C)/(E) jumper size is read by `gec_size`.

**250.54 Auxiliary electrodes.** *(summary kept local)*
- **Engine:** not graded; no electrode is authored as auxiliary.

**250.58 Common electrode.** *(summary kept local)*
- **Engine:** not graded as such. The garage's one feeder lands on `ED-G-PANEL`'s ground bar
  and its one rod pair.

**250.60 Strike-termination devices.** Their conductors and driven electrodes do not stand
in for the 250.50 electrodes, but separate electrodes must still be bonded together (see
250.106).
- **Engine:** `code.NEC_250_106_lps_bond` bonds Catlin's `use="lps_terminal"` rods, which are
  not counted as electrodes by 250.50 or 250.53.

**250.62 GEC material.** *(summary kept local)*
- **Engine:** not graded; `gec_size` grades only copper.

**250.64 GEC installation.** Applies at each service, each building supplied by a feeder or
branch circuit, and each derived system.
- **(A) Aluminum or copper-clad aluminum.** No bare or covered conductor under corrosive
  conditions or in contact with concrete; terminations inside enclosures listed for the
  environment may sit within 18 in. of the bottom of the enclosure; outside buildings or
  equipment it is not terminated within 18 in. of earth.
- **(B) Securing and protection.** Exposed conductors are fastened to the surface. A 6 AWG or
  larger one not subject to damage may run along the surface unprotected; if exposed to damage
  it goes in RMC, IMC, Schedule 80 PVC, RTRC-XW, EMT or armor. Smaller than 6 AWG is always
  in one of those. A conductor in earth need not meet 300.7 or 305.15 but is buried or
  protected where damage is possible.
- **(C) Continuous.** One unspliced length, except by irreversible compression connectors or
  exothermic welding, listed connectors at accessible splices, busbar sections, bolted
  structural-metal frames or threaded and welded water-pipe joints.
- **(D) Several disconnects in separate enclosures:** (1) a common GEC sized by 250.66 on the
  summed circular-mil area of each set's largest ungrounded conductor (Table 250.66 Note 1 where
  the conductors meet the drop directly), with taps into each enclosure sized for that
  enclosure's largest conductor and joined to the common GEC without cutting it: exothermic
  weld, a listed connector, or a 1/4 x 2 in. busbar with listed or welded connections; (2)
  individual GECs, each sized for its disconnect's supply conductors, to the grounded
  conductor, the EGC or a supply-side bonding jumper; (3) one connection in a wireway or
  accessible enclosure on the supply side.
- **Engine:** (D)(1)'s summed basis is `ServiceEntrance.disconnect_conductors` and feeds
  `gec_size` and the water bond. (A), (B), (C) and the (D) tap and connection methods are not
  graded. Catlin's two GECs are
  a short bare or insulated copper run each; whether (B) protection is met is a field matter.
  The Al PV down-lead's bimetal transition is authored at 18 in. above grade
  (`GroundingStandard.transition_min_height`), which is the (A) distance; no check reads it.

**Table 250.66** *(full table kept local; the values the engine uses are in its source)*

For parallel sets, use their combined area. Without service-entrance conductors, use the
size the load would call for.

A GEC run that goes to only one electrode type never has to be larger than:
- (A) rod, pipe or plate: 6 Cu (4 Al);
- (B) concrete-encased: 4 Cu;
- (C) ground ring: the ring's own conductor.
- **Engine:** `code.NEC_250_66_gec_size` grades the Table 250.66 Cu row on the service basis
  (250.32(E) for an outbuilding), capped by (A)/(B). Al GECs are graded only against the (A)
  cap. Rings are UNKNOWN. It does not test 'extends on' to another electrode type.

**Table 250.102(C)(1)** *(full table kept local; the values the engine uses are in its source)*

*(summary kept local)*

**250.102(D)-(E) Equipment bonding jumpers.** *(summary kept local)*
- **Engine:** not graded.

## Part V: bonding

**250.84(B) Underground service raceway containing cable.** A metal service raceway holding
metal-sheathed or armored cable bonded to the grounded conductor need not be bonded to it at
the building; the sheath may be insulated from the raceway.

**250.86 Other enclosures and raceways.** Metal enclosures and raceways for other than service
conductors connect to the EGC. Ex. 1: additions to existing open, knob-and-tube or
nonmetallic-sheathed wiring, in runs under 25 ft that are guarded and clear of ground and
grounded metal, with no equipment ground. **Ex. 2:** short sections that support or protect
cable assemblies from damage need not be connected. Ex. 3: metal components isolated in
nonmetallic raceway (18 in. of cover) or 2 in. of concrete.
- **Engine:** `NEC.SLEEVE_BONDING` is Ex. 2; the derived 3/4 in. EMT NM sleeves cite it in
  `resolve/device_drops.py`. Nothing grades it.

**250.90-250.92 Services.** *(summary kept local)*
- **Engine:** not graded.

**250.94(A) Intersystem bonding termination (IBT).** Provided outside the enclosures at the
service or meter equipment, and at the disconnect of any building supplied by a feeder or
branch circuit. It is accessible, has terminals for at least three bonding conductors, and
does not block opening any enclosure. It is mounted securely, at the service, to the service
or meter enclosure, an exposed nonflexible service raceway, a GEC enclosure with at least 6 Cu,
or the building with at least a 6 Cu GEC; at an outbuilding, to its disconnect enclosure, a
6 Cu GEC enclosure or the building with a 6 Cu GEC. It is listed as grounding and bonding or
communications bonding equipment. Ex.: where the 750.48, 750.66, 750.100 or 800.48 bonding
and electrode conductors already exist, no IBT is required but an accessible external means
is.
- **Engine:** `code.NEC_250_94_ibt` requires an IBT at the service and in every building a
  feeder or branch circuit supplies, whether or not a data run enters. It must be bonded into
  that building's system, with three or more `bonding_terminals` (UNKNOWN if unstated) and a #6
  Cu or larger GEC in the system. Accessibility, 'does not block an enclosure' and the Ex. are
  not modelled. Catlin: `ED-M-IBT` and `ED-G-IBT`, both IBTB (5 terminals).

**250.104 Bonding piping and structural metal.**
- (A)(1) Metal water piping in or on the building is bonded to the service equipment
  enclosure, the grounded service conductor, a GEC of sufficient size, or one or more of the
  electrodes in use if their GEC or jumper is of sufficient size. The jumper follows
  250.64(A), (B) and (E), has accessible connection points, and is sized per Table
  250.102(C)(1) on the service conductors, never larger than 3/0 Cu or 250 kcmil Al
  (except under (A)(2)-(3)). (A)(2) In a multiple-occupancy building whose occupancies' water
  piping is isolated from each other, each occupancy's piping may bond to the equipment
  grounding terminal of the panelboard feeding it, sized per 250.102(D).
- (A)(3) A building fed by a feeder or branch circuit bonds its water piping to its
  disconnect enclosure, to the EGC that runs with the supply, or to its electrodes. Sized
  per 250.102(D), and never larger than the largest supply conductor.
- (B) Other metal piping that could become energized, gas piping included, is bonded to the
  EGC of the circuit that could energize it, or to the service or the electrodes. Sized per
  Table 250.122 for that circuit.
- (C) Exposed structural metal that could become energized is bonded, sized per Table
  250.102(C)(1) and capped at 3/0 Cu.
- **Engine:** `code.NEC_250_104_water_bond` checks connectivity, plus the (A)(1) size: Table
  250.102(C)(1) on the service basis with the 3/0 Cu cap, and a FAIL where the bond lands on an
  electrode whose GEC is smaller. (A)(3), (B) and (C) are not graded.

**250.106 Lightning protection.** The lightning system's ground terminals are bonded to the
building's grounding electrode system. NFPA 780 has the details.
- **Engine:** `code.NEC_250_106_lps_bond`.

**250.109, 250.110, 250.112 Equipment grounding.** *(summary kept local)*
- **Engine:** not graded.

## 250.119 (tail), 250.120, 250.122 Equipment grounding conductors (read 2026-11-14)

**250.119(B)(2), (C), (D) (tail).** An EGC is identified by stripping its insulation, green
colour, or green tape or marking that fully encircles it; a conductor of a multiconductor cable
may be re-identified at each end; a flexible cord's EGC is green or green with yellow stripes.

**250.120 Installation.** (A) Joints in EGC raceways, trays and armour are made tight. (B)
Bare or covered aluminium or copper-clad aluminium EGCs stay out of corrosive conditions and
out of contact with concrete, masonry or earth; outdoor terminations are within 18 in. of the
bottom of a listed enclosure, and, externally, are not made within 18 in. of the earth unless in a
listed connector system. (C) An EGC smaller than 6 AWG that does not run with its circuit
conductors is protected by raceway or armour, except in framing hollows where not subject to
damage.

**250.122 Size.** A wire EGC is no smaller than Table 250.122 gives for the OCPD rating (coded
in `model/ampacity.py`: rows of OCPD not exceeding 15, 20, 60, 100, 200 ... 6000 A, copper and
aluminium columns; larger where 250.4(A)(5) or (B)(4) requires). (A) It is never required
larger than the circuit conductors. (B) A non-wire EGC follows 250.4. (C) A sectioned EGC in a
multiconductor cable is allowed if the combined area complies. **(D) Where the ungrounded
conductors are enlarged for any reason other than 310.15(B)/(C) (voltage drop, say), a wire EGC
is enlarged in proportion by circular mils** (a qualified person may instead size it for an
effective fault path). (E) One EGC may serve several circuits in a raceway, sized for the largest
OCPD.
- **Engine:** `electrical.egc_size` grades every circuit's `egc_awg` against the table, capped
  by (A); (D) is ADVISORY where the conductors exceed the breaker's minimum and the EGC is
  smaller than them (Chapter 9 Table 8 not coded). All 41 Catlin circuits PASS.
  `code.NEC_690_45_pv_egc_size` also reads the table for the array's bonds (see
  `nec-2026-paraphrase-690-705-710.md`). The 250.120(B) aluminium rule for the 4/0 Al SER
  feeders' EGC is not graded.

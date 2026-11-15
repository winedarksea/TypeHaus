# Electrical rules the engine grades: Articles 225, 230 and 314 (2026 NEC)

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

Continues `nec-2026-paraphrase.md` (same conventions; the owner read these pages on
2026-11-14, 314.27 on 2026-11-13). Each rule has an
**Engine** line. Tests:
`test_nec_printed_rules.py`, `test_device_boxes.py`.

## Article 225: outside branch circuits and feeders (Parts I-II)

Catlin's garage is a separate building (4 ft gap) supplied from the house panels by branch
circuits, so Part II is the live part. **Facts read from the plan (2026-11-14):** seven
circuits have a consumer in the garage and a panel elsewhere: `CKT-EV-1450` (50 A 2-pole,
hardwired EVSE) and `CKT-GAR-240` (20 A 2-pole, 6-20R, no neutral) from `ED-B-PANEL-2`;
`CKT-LT-GARAGE` (15 A), `CKT-RC-GARAGE` (20 A GFCI), `CKT-GAR-HEAT` (20 A GFCI heater) and
`CKT-LT-MAIN` (20 A, the opener outlet) from `ED-B-PANEL`; `CKT-LT-BACKUP` (15 A, the CO
relay) from the backup panel. Each is its own circuit with its own neutral; the model holds
no multiwire circuit, and none is authored anywhere in the house. Only the EVSE feeder's
raceway is drawn (`CD-B-GARAGE`/`CD-B-GAP-EV`, 1-1/4 in. EMT, up through the slab); the other
six have no modelled route. The garage has no panel, no disconnect and no 225.37 plaque.

**225.19(D)-(E) Overhead conductors.** *(summary kept local)*
- **Engine:** not graded. Catlin has no overhead outside conductors.

**225.20-225.22 Protection and supports.** *(summary kept local)*
- **Engine:** not graded.

**225.24-225.26 Outdoor lamps.** *(summary kept local)*
- **Engine:** not graded. Catlin's garage luminaires are not pendants and no conductor passes
  over them.

**225.27 Raceway seal.** *(summary kept local)*
- **Engine:** not graded. It applies where `CD-B-GAP-EV` and the spare `CD-B-V2H-GAP` rise
  into the garage and where they leave the house through their basement sleeves.

**225.30 Number of supplies.** *(summary kept local)*
- **Engine:** not graded. `code.NEC_250_32_separate_buildings` already traces circuits to a
  building away from its panel, but 225.30's exceptions (uses, listings, management) are not
  authorable, so a count alone would FAIL on facts the model cannot hold. **Catlin: seven
  circuits to one building, no exception evident; an apparent 225.30 violation.** The honest
  fixes are one feeder to a garage subpanel (which then needs 225.31, 225.39(C)/(D) and
  250.32 as a feeder) or a documented (E) reading. Owner decision; the house is not changed.

**225.31 Disconnect.** *(summary kept local)*
- **Engine:** not graded. **Catlin: no disconnect is modelled at the garage**; the circuit
  breakers sit in the basement panels, neither inside nearest the entrance nor outside in
  sight of the garage. Consequence of the 225.30 finding: seven supplies would also need
  seven disconnects.

**225.33-225.34 Number and grouping.** *(summary kept local)*
- **Engine:** not graded. Seven circuits would exceed six if they were one supply.

**225.35 Occupant access.** *(summary kept local)*
- **Engine:** not graded; Catlin is single-occupancy.

**225.36 Type.** *(summary kept local)*
- **Engine:** not graded.

**225.37 Identification.** *(summary kept local)*
- **Engine:** not graded. Catlin's garage circuits come from the dwelling, so Ex. 2 applies.

**225.38 Construction.** *(summary kept local)*
- **Engine:** not graded.

**225.39 Rating.** *(summary kept local)*
- **Engine:** not graded. The garage is not a dwelling, so (D) would govern a feeder: its
  seven breakers total 160 A, over 60 A.

**225.40 OCPD access.** *(summary kept local)*
- **Engine:** not graded; Catlin's breakers are in basement panels reached from the stair.

**225.41 Emergency disconnect, one- and two-family dwellings.** *(summary kept local)*
- **Engine:** not graded. `electrical.service_disconnect_location` returns UNKNOWN for an
  indoor service disconnect because nothing in the model can earn the exception: there is no
  field marking a device as the emergency disconnect, none for its marking, and no
  short-circuit rating or available fault current (`DeviceKind.DISCONNECT` carries none). A
  broad new model was not added. **Catlin: the meter-main is outdoors, so 230.70(A)(1) is met
  and no separate emergency disconnect is required;** its marking (230.70(B)(2)) and the
  (D) directory for the PV/ESS disconnects are derived at the service root, not graded.

## Article 230: services

**230.1-230.2 Scope and listing.** *(summary kept local)*
- **Engine:** not graded; the catalog's listings are authored, not checked against this list.

**230.4 Number of services.** *(summary kept local)*
- **Engine:** not graded. Catlin has one service; PV and ESS tie to a panel's load side.

**230.67 Surge protection.** (A) Every service to a dwelling unit, dormitory, hotel or motel
guest room or suite, nursing-home patient sleeping area, or emergency-station sleeping
quarters gets an SPD. (B) It is part of the service equipment or immediately next to it.
Ex.: a service that supplies only feeders may put the SPD on the load side of each feeder
instead. (C) Type 1 or Type 2. (D) Replacing service equipment brings all of this in. (E)
Nominal discharge current (In) of at least 10 kA.
- **Engine:** `code.NEC_230_67_service_spd` passes a Type 1/2 `spd_class` device within 1.5 m
  of the service device, or an `spd` circuit in it; an SPD only downstream is UNKNOWN (the Ex.
  needs feeder topology). `code.NEC_215_18_spd` asks for one per panel. (E) is graded by `electrical.spd_nominal_discharge`; the FS140 is
  UL 1449 Type 2 per Siemens and publishes no In, so it is UNKNOWN. Not graded: the Type of an
  `spd` circuit, (D).

**230.68 Meter sockets.** *(summary kept local)*
- **Engine:** not graded.

**230.70 Service disconnect.** Opens every ungrounded conductor.
- **(A)(1) One- and two-family dwellings:** a readily accessible outdoor location, on the
  dwelling or within sight of it per 110.29. Ex.: no outdoor requirement where an emergency
  disconnect per 225.41 is installed. (A)(2) Other buildings: readily accessible, outside or
  nearest the entrance inside. (A)(3) Never in a bathroom. There is no 230.85 in 2026.
- **(B) Marking.** "SERVICE DISCONNECT" on or next to each disconnect. One- and two-family
  enclosures also say "EMERGENCY DISCONNECT" on the outside front, white on red, letters at
  least 1/2 in. high. (C) Equipment in hazardous locations follows those rules.
- **(D)** Where other energy-source disconnects (445.18, 480.7, 705.20, 706.15) are not next
  to the service disconnect, a plaque or directory there says where they are.
- **(E)** Replacing a dwelling's service equipment follows (A), (B) and (C); an Ex. exempts
  swapping only sockets, conductors or raceways from (A)(1) and (B)(2).
- **(F)** A remote control device is not itself a service disconnect.
- **Engine:** `electrical.service_disconnect_location` grades (A)(1): the grounding root
  device must stand in no room (outdoors). An indoor one is UNKNOWN: the 225.41 exception
  needs a marked, short-circuit-rated outdoor emergency disconnect the model cannot state.
  Catlin's meter-main is on the west wall's outside face and passes.
  `electrical.service_disconnect_rules` grades (A)(3) (outdoors: not a bathroom, PASS). Not
  graded: within-sight and readily-accessible, (A)(2), (E), (F). The (B)(1)/(B)(2) markings
  and the (D) directory are derived at the service root (`resolve/electrical_labels.py`). See `nec-2026-paraphrase-411-230.md`.

**230.71-230.72 Number and grouping.** *(summary kept local)*
- **Engine:** not graded; 230.71(B)(4) is not graded (no CL320 product chosen). Catlin's
  meter-main holds two 200 A mains, within the six, but (B)
  needs separate enclosures or compartments: see `nec-2026-paraphrase-411-230.md`.

**230.74-230.77 Operation.** *(summary kept local)*
- **Engine:** not graded.

**230.79 Rating.** At least the calculated load (Article 120), and at least: 15 A for one
branch circuit's limited load; 30 A for up to two 2-wire circuits; **100 A for a one-family
dwelling**; 60 A otherwise. **230.80:** several disconnects together are at least that
rating. **230.81:** pressure connectors or clamps, never solder.
- **Engine:** `electrical.service_load` compares the 120.82 demand with the authored
  `service_amps` (Catlin 320 A vs 250.4 A); `electrical.service_disconnect_rules` grades the
  100 A minimum of (C) against the same rating (PASS). 230.80 and 230.81 are not graded.

**230.82 Supply side of the service disconnect.** *(summary kept local)*
- **Engine:** not graded; Catlin's PV and ESS tie to a panel's load side (705.12).

**230.90-230.93 Service overcurrent protection.** *(summary kept local)*
- **Engine:** not graded; Table 310.12(A) service-conductor sizing is unmodelled (see 310.12 in `nec-2026-paraphrase-310.md`).

## Article 314: boxes

**314.15 Damp or wet locations.** *(summary kept local)*
- **Engine:** not graded.

**314.16 Box fill.** The box volume is the sum of its parts: Table 314.16(A) trade-size
volumes, or the marked volume on rings, extensions, covers and other boxes (nonmetallic and
over-table boxes must be marked). A barrier splits the volume; an unmarked one takes 1/2 in³
(metal) or 1 in³ (nonmetallic). Fill (B)(1)-(6) is added together at Table 314.16(B)(4)
volumes; locknuts, wire connectors and bushings are free.
- **(1) Conductors:** one each if it starts outside and terminates or splices inside, one each
  passing through, two for a loop or coil at least twice the 300.16 free length, none for a
  conductor that never leaves. Ex.: EGCs and up to four fixture wires smaller than 14 AWG from
  a domed canopy.
- **(2) Clamps:** one allowance for all internal clamps, at the largest conductor.
- **(3) Support fittings:** one allowance per kind (stud, hickey), at the largest conductor.
- **(4) Devices:** two allowances per yoke or strap, at the largest conductor connected; a
  device wider than 2 in. takes two per gang it needs.
- **(5) EGCs:** one allowance covers up to four, at the largest EGC; each one past four adds
  1/4 of an allowance.
- **(6) Terminal blocks:** one allowance per assembly.
- **Tables.** (A) metal boxes and (B)(4) per-conductor volume, in³: 18 AWG 1.50, 16 1.75,
  14 2.00, 12 2.25, 10 2.50, 8 3.00, 6 5.00. Checked cell by cell against the printed tables
  2026-11-14: every volume the engine holds is right (14 AWG-6 AWG conductors, and the 4 x 1-1/4
  to 4-11/16 x 2-1/8 square and 3 x 2 / 4 x 2-1/8 device rows). It omits the round/octagonal,
  3 x 2 x 1-1/2, 3 x 2 x 2, masonry and FS/FD rows.
- **Engine:** `electrical.box_fill` counts the cable conductors (through-fed, or end-fed for a
  receptacle alone on its circuit), two allowances per gang at the circuit's gauge and one
  allowance for all EGCs (never more than four). (2) is one allowance unless the `BoxRow`
  states `internal_clamps=False` (unset is counted); (3) is `BoxRow.support_fittings`; (5) is
  one allowance up to four EGCs, a quarter for each past four. Not modelled: (6) terminal
  blocks, barriers, loops, 18 and 16 AWG. Adding a clamp allowance to every Catlin box would still pass.

**314.17 Entries.** *(summary kept local)*
- **Engine:** not graded.

**314.19 Flush boxes.** Fully enclose the device on back and sides with substantial support.
Screws that support the box never also hold the device.
**314.20 Flush mounting.** In concrete, tile, gypsum, plaster and other noncombustible
surfaces the box front is set back at most 1/4 in.; in wood or other combustible surfaces
it is flush or proud. **314.21:** gaps around a box in a broken noncombustible surface are at
most 1/8 in. **314.22:** a surface extension is made with one or more extension rings, with
equipment grounding per Article 250 Part VI.
- **Engine:** `device_boxes` seats a flush box's front edge on the finished face (setback 0),
  so 314.20 holds by construction. A box deeper than its cavity FAILs `electrical.box_fill`,
  citing 314.20. Not graded: 314.19, 314.21, 314.22.

**314.23 Support.** *(summary kept local)*
- **Engine:** not graded. Catlin's surface boxes are fastened to concrete under (A); the
  derived 3/4 in. EMT NM sleeve is NM protection (334.15(B)), not box support, and does not
  bring (E)/(F) in. `block_profile` backs a flush box that screws to wood.

**314.24 Box dimensions.** (A) A box with no device is at least 1/2 in. deep inside. (B) With
a device or equipment the depth fits its rear projection and conductor size, counting rings
and raised covers: equipment projecting over 1-7/8 in. needs its depth plus 1/4 in.;
8, 6 or 4 AWG needs 2-1/16 in.; 12 or 10 AWG needs 1-3/16 in. (or the device's depth plus
1/4 in. if it projects over 1 in., with 1/2 in. clear of a conductor entering the rear
centre); 14 AWG or smaller needs 15/16 in.; larger than 4 AWG needs a box identified for it. Ex.: equipment listed
with its box. (C) Side-wired devices keep conductors clear: the device does not pass the
entry's centreline, and 1/2 in. of wall clearance.
- **Engine:** `electrical.box_fill` FAILs a box shallower than the gauge's minimum (14 AWG
  15/16 in., 12 and 10 AWG 1-3/16 in., 8 and 6 AWG 2-1/16 in.), read off the body depth
  without rings (conservative). The device type's `rear_projection` plus 1/4 in. governs
  past 1-7/8 in. (1 in. on 12/10 AWG). Not graded: the listed-box exception, (A), (C), the
  1/2 in. rear-entry clearance.

**314.25 Covers and canopies.** Each finished box has a cover, faceplate, lampholder or
luminaire canopy (conduit bodies a cover), matching machine screws. (A) A metal cover or
plate is connected to the EGC per 250.110. (B) A canopy over a combustible finish is backed
with noncombustible material where 410.23 asks. (C) Cord-pendant covers have bushings.
- **Engine:** `electrical.canopy_covers_box` grades the first rule only: a wall light's
  canopy spans its box face. Not graded: (A) EGC continuity, (B), (C).

**314.27 Outlet boxes.**
- **(A)** Luminaire boxes.
  - Wall-mounted: a luminaire of 6 lb or less may hang from other boxes or plaster rings
    with at least two No. 6 screws. A heavier one needs a box identified for the purpose,
    marked with its limit unless that is 50 lb.
  - Ceiling: every outlet used only for lighting gets a box that can take a luminaire and
    carry at least 50 lb. A heavier luminaire is supported on its own unless the box is
    listed and marked for its weight. Boxes built into listed recessed luminaires are
    exempt.
- **(B)** Paddle fans.
  - (1) A box that is a fan's only support is listed and marked as suitable for that use.
    Above 35 lb it is marked with the weight it carries, and the limit is 70 lb.
  - (2) In a dwelling's living or sleeping areas, a centred ceiling box at a spot where a fan
    is likely or shown is either listed for fan support, or lets a fan be fastened through it
    to framing strong enough to carry one, without taking the box out.
- **(C)** Floor receptacles go in boxes listed for floor use.
- **(D)** Boxes that support other utilization equipment (the printed page stops mid-rule).
- **Engine:** `code.E3905_7_floor_boxes` grades (C), trusting the authored
  `floor_box_listing` string. (A), (B) and (D) are not graded.

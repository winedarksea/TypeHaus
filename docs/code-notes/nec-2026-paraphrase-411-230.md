# Electrical rules the engine grades: Article 411, 210.70(C), Article 215, and a 225/230 re-read (2026 NEC)

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
2026-11-14: 210.63 (tail) to 210.70(B) (a repeat), then 210.70(C) and 215.1-215.10(A);
225.39-225.41; 230.1, 230.2 and 230.4(A); 230.67-230.93 (the page ends inside 230.93);
410.196(D), 410.197, all of Article 411 and 422.1-422.2. Checks added with this read:
`electrical.equipment_space_lighting` (`electrical_space_lighting.py`) and
`electrical.service_disconnect_rules` (`electrical_service.py`); the wording of
`electrical.bath_luminaire_zone` changed. Tests: `test_nec_411_230.py`. Constants:
`typehaus.model.nec.NEC`.

**Verdicts.** The 225.39-225.41 and 230.x sections were already paraphrased in
`nec-2026-paraphrase-230-314.md`; each was read again against this print and **every entry and
every `NEC` string matches**. Three additions the earlier entries lacked are below
(230.71(B)'s five permitted forms, the 230.82 items now numbered, 230.4's six special
conditions). 210.63-210.70(B) matches `nec-2026-paraphrase-210-422-410.md`.

## Catlin, read against these rules

- **The laundry track (`ED-M-LAUNDRY-TRACK`) passes `electrical.bath_luminaire_zone`.** It is
  lighting track (Article 100; `nec-2026-paraphrase-followup.md`) and 410.10(D)(1) names track
  with no voltage limit: Article 411 exempts nothing, and 411.4(B) is a cap (24 V dc is under it,
  supply `PROD-PUREEDGE-PSB-40W-UNI-24VDC-T`). But the track is in `RM-M-LAUNDRY`, behind a wall
  from the tub in `RM-M-BATH2`; 410.10(D) is the area around the tub, so another room is outside
  it. The check read straight-line distance through the wall (1.1 ft in plan); it now grades
  only luminaires in the tub's own room (`room_owning`). 410.150(C)(9) therefore does not reach
  it. A 24 V track in the tub's room would still be UNKNOWN (held for the gate, a violation).
- **Service disconnect: `ED-M-METER`, the Class 320 meter-main, is outdoors.** It is on the
  outside face of the dwelling's west wall `W-M-W1`, 42.875 in. along, on the dwelling unit
  itself, so 230.70(A)(1) is met (`electrical.service_disconnect_location` PASS) and the 225.41
  exception applies: **no separate emergency disconnect is required.** 225.41(A)(2)'s
  short-circuit rating then has no object. Not in a bathroom (230.70(A)(3), PASS) and 320 A
  against the 100 A floor (230.79(C), PASS, `electrical.service_disconnect_rules`). "Readily
  accessible" and "within sight" are not graded; neither is needed on the wall itself.
- **230.71(B): two mains in one meter-main.** `ED-T-METER` is "320 A, two 200 A mains". Two to
  six service disconnects must be separate enclosures, or sit in a switchboard, switchgear,
  metering center or MCC with barriers or separate compartments (the five forms in 230.71(B)).
  The 2026 text allows several disconnects in one enclosure only for *existing* equipment (the
  Exception). Whether Catlin's CL320 is a metering center with each main in its own
  compartment is not stated by the model, so this is not graded (no disconnect count field).
  **Owner question 1.**
- **230.70(B)(1)/(2) and (D) derived; 225.41(B)/(C) not derived (the exception applies).** "SERVICE DISCONNECT" on or next
  to each main, "EMERGENCY DISCONNECT" on the enclosure's front (white on red, 1/2 in.), and the
  plaque or directory at the service for every other-source disconnect that is not next to it
  (the PV disconnect, the ESS disconnect, the V2H spare). Owner question 5 is closed.
- **230.67 SPD.** `ED-M-SPD` (Type 1, Siemens FS140) is 29 in. from the meter-main on the same
  wall: PASS. (E) wants a nominal discharge current In of at least 10 kA; the type's
  `surge_ka = 140` is the surge rating, not In. (E) is graded by `electrical.spd_nominal_discharge`;
  the FS140 is UL 1449 Type 2 per Siemens and publishes no In, so UNKNOWN. **Owner question 2.**
- **230.90 Ex. 5 (310.12 ampacities for a single-phase dwelling service)** is the printed basis
  already used for the 4/0 Al feeders (`nec-2026-paraphrase-310.md`); service-conductor size is
  not modelled, so nothing grades it.
- **230.82:** the supply side holds the meter-main's own contents and the SPD (item 10, a
  Type 1); PV and ESS connect to a panel's load side (705.12). Not graded.
- **Article 411, Catlin's 24 V runs.** The four drivers are 24 V (`ED-T-LT-PSU-60`, `-200`,
  `-96-WE`, `PUREEDGE-40`; 40 to 200 W, so 1.7 to 8.3 A, under 411.4(A)'s 25 A) and the rails,
  covers, shadow gaps and tape runs sit on them: 411.4(B) is met. Not graded: whether each is
  listed as one system or from listed parts (411.2), concealed wiring by a Chapter 3 method or a
  listed Class 2 source per 722.140 (411.6(A); 722.140 is read in `nec-2026-paraphrase-722.md`), and the isolating
  secondary (411.7(B)). **411.6(B) spa:** lighting 10 ft from the water. Catlin has a rough-in
  only (`CKT-SPA`, `ED-B-SPA-DISC`; conditions in `notes/grounding_bonding.md` §10), so no
  distance can be read. It is a gap, not a check. Reading it needs an `EquipmentKind.SPA` with a footprint
  (`nec-2026-paraphrase-680.md`).
- **210.70(C), graded advisory (`electrical.equipment_space_lighting`).** Rooms in scope:
  utility, mechanical, storage or unconditioned rooms holding an `Equipment` (not a duct
  manifold or plenum) or a panel. Result: `RM-A-EAST-UNFIN` (air handler, mixing box, heat
  strip) and `RM-B-ESS` PASS: switched light, a switch within 6 ft of each door, a light within
  6 ft of each machine. `RM-B-FURNACE` (four panels, inverter, ERV) and `RM-B-WORKSHOP` (water
  heater, manifold) PASS too: 3-way pairs at `D-B-FURN` (between them at (4.8, 18.0) ft); a
  door into a room with no other door (the ESS closet's `D-B-ESS`) is not an entry. Not graded: (C)(3), automatic
  control (no occupancy sensor is modelled, so every control reads as manual by absence of
  evidence); an attic or crawl reached by a stair (no door); finished basement rooms (a gym with an
  indoor head is a 210.70(A) room). `RM-M-MECH` holds only duct manifolds.
- **Article 215 feeders (not graded).** Catlin's feeders: the meter-main's two 200 A mains to
  `ED-B-PANEL` (225 A bus) and `ED-B-PANEL-2`; the inverter's load port to `ED-B-BACKUP-PANEL`
  (`CD-B-INV-PANEL`); the garage's one feeder `CKT-GAR-FEEDER` (Article 225); the EV and V2H lines.
  `electrical.panel_feeder_load` estimates 135.7 A and 120.7 A of 120.82 demand on the two
  200 A mains; even at 125% of all of it (the 215.5 and 215.4(A)(1) worst case with every load
  continuous) that is 169.6 A and 150.9 A, under 200 A, so 215.5 is met by hand. It is not a
  check: the model has no continuous-load split and 120.82 is a demand figure. 215.4(A)(2)
  (adjustment and correction), (B) (the neutral no smaller than the 250.122 EGC) and (C) (not
  a 55 A or smaller service) need conductor sizes, which circuits do not carry (open owner
  question in `plans/TODO-nec-2026.md`): a gap. 215.9 (a GFCI on the feeder) and 215.10 (GFPE, 1000 A and
  up; the service is 320 A) are N/A, the second by rating.

## Owner questions

1. Is the CL320 meter-main a metering center with each 200 A main in its own compartment (or
   field-evaluated as one), so 230.71(B)(4) holds? The 2026 text no longer lets two mains share
   one enclosure unless the equipment already existed.
2. What is the FS140's UL 1449 nominal discharge current In (230.67(E): at least 10 kA)? Add it
   to the type next to `surge_ka`.
3. (Closed 2026-11-14: `ED-B-FURNACE-SW3` and `ED-B-WORKSHOP-SW3` form 3-way pairs at `D-B-FURN`;
   `RM-B-FURNACE` and `RM-B-WORKSHOP` PASS 210.70(C)(1).)
4. (Closed 2026-11-14: the laundry track is in another room, outside the tub zone.)
5. (Closed 2026-11-14: labels are derived, not authored; `resolve/electrical_labels.py`.)

## 210.70(C) All occupancies (and the rest of 210.70)

**210.70(A)-(B)** repeat the earlier read. **(C)** Attics, underfloor spaces, utility rooms and
basements that are used for storage or hold equipment needing service have at least one lighting
outlet with a switch or a wall switch. (1) A point of control at each entry. (2) A light for
equipment goes at or near it. (3) Automatic control may not control all the illumination unless
a manual bypass exists.
- **Engine:** `electrical.equipment_space_lighting` (above).

## Article 215 Feeders

- **215.1** **215.4(A)** **215.5** **215.6** **215.7** **215.9** *(summary kept local)*
- **Engine:** not graded (no conductor size, no continuous share). `FEEDER_SPD` (`215.18`) is
  confirmed in print: see `nec-2026-paraphrase-followup.md` (215.10(B)-215.18).

## Article 411 Low-Voltage Lighting

- **411.1** Covers low voltage lighting systems and their associated components. **411.2(A)**
  The luminaires, power supply and fittings, including exposed bare conductors, are listed as
  one system. **(B)** Or an assembly of listed parts: identified luminaires, power supply,
  fittings, and approved flexible cord or cable, or a Chapter 3 method for the secondary.
- **411.3(B)** Reconditioned low-voltage lighting systems, or ones assembled from reconditioned
  parts, are not installed ((A) is reserved).
- **411.4** A system is an isolating power supply, low-voltage luminaires and the associated
  equipment, all identified for the use. **(A)** The supply's output circuits are rated 25 A
  at most under all load conditions. **(B)** Operating voltage at most 30 V ac or 60 V dc; where
  wet contact is likely, 15 V ac or 30 V dc. (680.1 covers pools, fountains and the like.)
- **411.6(A)** Conductors concealed in or through a wall, floor or ceiling are a Chapter 3 method,
  or wiring from a listed Class 2 source installed per 722.140. **(B)** Lighting systems are at
  least 10 ft horizontally from the water's edge of a pool, spa, fountain or similar, unless
  allowed elsewhere in the code.
- **411.7(A)** Secondary circuits are not grounded (Ex.: a listed Class 2 source listed as
  suitable for secondary grounding). **(B)** The secondary is isolated from the branch circuit by
  an isolating transformer. **(C)** Exposed bare conductors and current-carrying parts are
  allowed indoors only; bare conductors are at least 7 ft above the finished floor unless listed
  lower.
- **411.8(A)** A Class 2 supply's conductors and equipment follow 725.127 (unread).
  **(B)** Any other supply is on a 20 A branch circuit at most.
- **Engine:** `electrical.bath_luminaire_zone` cites 411.4(B) beside 410.10(D)(1). Nothing else
  grades Article 411 (above). Unread and referenced: 725.127 (722.140 is read in `nec-2026-paraphrase-722.md`).

## 410.196(D)-410.197, 422.1-422.2

**410.196(D)** **410.197 Germicidal irradiation
systems.** **422.1-422.2** *(summary kept local)*
- **Engine:** not graded (Catlin has no germicidal system; appliance listing is catalog data).

## 225.39-225.41 and 230 re-read: what the earlier entries lacked

- **230.4(A)** **230.71(B)** **230.82** **230.90 Ex. 5** **230.93** *(summary kept local)*

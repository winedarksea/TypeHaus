# Electrical rules the engine grades: Articles 706 and 480 (2026 NEC)

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

Continues `nec-2026-paraphrase.md` (same conventions; the owner read 706.1-706.30(A)(2) and
480.2-480.14 on 2026-11-14). Few checks grade any of it: the model has no ESS disconnect.
The battery voltage is now authored (`battery_nominal_voltage_v`, 51.2 V).

## Catlin, read against these rules

- **The system.** An EG4 12kPV inverter (`EQ-B-ESS-INV`, 8 kW continuous, on `W-B-N4` in
  `RM-B-FURNACE`) and one EG4 WallMount Indoor battery (`EQ-B-ESS-BATT`, 14.3 kWh, 282 lb, in
  the Type X closet `RM-B-ESS`), about 5 ft of DC cable apart, through the sealed
  `W-B-ESS-W`. The inverter's grid port is `CKT-ESS-GRID` (50 A, 2-pole, in `ED-B-PANEL`) and
  its load port feeds `ED-B-BACKUP-PANEL`. The battery type carries `ul_9540_listed=True`,
  declared. **Nominal voltage is authored** (`battery_nominal_voltage_v`, 51.2 V). 14.3 kWh over the 280 Ah in the type's name
  (706.1: kWh = volts x Ah / 1000) is about 51 V, a 48 V-class LFP pack, under 60 V dc.
- **706.15(B) emergency shutdown (the likely real finding).** A dwelling's ESS needs a
  function that stops export to other premises wiring, started from a readily accessible
  device outdoors that shows off/on. The candidate is `ED-M-RSD-INIT`, the PV rapid-shutdown
  initiator beside the meter-main (outdoors, handle about 4 ft 2 in. above grade, lockable,
  NEMA 4X rotary, wired by a Class 2 pair to the inverter). `backup_power.md` section 8 says
  only that "with supported EG4 batteries in closed loop the same switch also opens the ESS
  (706.15)", and that the switch is to be labelled as the PV rapid-shutdown switch. That is
  **unverified**: nothing in the model, nor in EG4 documents cited, states that the loop
  drops the inverter's load-port output (which feeds the backup panel) and the battery's
  contactor. **Owner question 1:** does opening that loop stop all ESS export, and is it
  EG4-supported for the WallMount in closed loop?
- **480.7(B) emergency disconnect (see below).** Read plainly it asks, for a dwelling, an
  outdoor battery disconnect or its remote control labelled EMERGENCY DISCONNECT, with no 60 V
  threshold of its own. Nothing outdoors is so labelled or so wired. **Owner question 2:**
  does the AHJ read (B) as independent of (A)'s 60 V? If yes, can `ED-M-RSD-INIT` be that
  remote control (it would need to open the battery, and carry the EMERGENCY DISCONNECT
  label as well as the PV one)? The label in the notes would then be wrong.
- **706.15(D) battery disconnect.** The battery is separate from the inverter electronics
  and field-serviced, so a disconnect for its ungrounded conductors is wanted within sight of
  it. None is modelled (the DC run is only "flagged" on the battery); whether the WallMount's
  own breaker is that disconnect is **owner question 3**, for EG4's listing. Graded since
  2026-11-14 (UNKNOWN until EG4 answers).
- **706.15(A)-(C) at the inverter.** Not modelled: a lockable AC disconnect (the 50 A
  breaker `CKT-ESS-GRID` is lockable only if a lock-off is fitted), or within sight, and the
  "ENERGY STORAGE SYSTEM DISCONNECT" marking with nominal voltage (the other three items are
  waived for dwellings).
- **706.2 listing.** The TODO's open item (EG4's UL 9540 certificate naming 12kPV plus
  WallMount) is this rule. `code.R327_ess_listing` grades only the declared flag.
- **706.30(A).** Inverter output circuit current is the continuous rating: 8,000 W / 240 V =
  33.3 A on a 50 A breaker. The 705.12 check reads the same inverter output.
- **480.7(A), (G), (F).** At about 51 V no dc disconnect is required and (G)'s plaque duty
  falls away; (F) asks for a label near the battery stating its nominal voltage (the only item
  that applies to a dwelling under 150 V). Derived (the label prints the voltage).
- **480.10.** (C) The battery's working space follows 110.26 from the cabinet edge: the
  authored 3 ft separation zone (`EQ-T-ESS-BATT` `ClearanceZone`, 41 in. front and back) is
  close but is not graded as 110.26. (F) Lighting: an ESS closet light exists on
  `CKT-LT-BACKUP`; its control is not checked. (E) Applies to rooms designated as battery
  rooms; the closet has a 24 in. steel door, and whether the AHJ calls it one is open.

## Article 706: energy storage systems

**706.1 Scope.** **706.2** **706.3** **706.4 Nameplate:** **706.5** **706.6** *(summary kept local)*
- **Engine:** not graded, except `code.R327_ess_listing` (the declared UL 9540 flag).

**706.15 Disconnecting means.** Every ESS can be disconnected from all wiring systems
(power sources, loads, other premises wiring), per 705.20 and (A)-(D).
- **(A)** It opens all ungrounded conductors together. **(B)** Readily accessible, and
  within the ESS, or visible and within 10 ft of it, or lockable open per 110.25 (or the
  enclosure lockable closed). Where the controls are remote and not in sight of the ESS, the
  disconnect is lockable and the control location is marked on it. **Dwellings:** the ESS
  includes an emergency shutdown function that stops export to other premises wiring; its
  initiation device is readily accessible outdoors, shows off or on, and "off" performs the
  shutdown.
- **(C)** Each ESS disconnect shows open or closed and is marked "ENERGY STORAGE SYSTEM
  DISCONNECT" with the nominal output voltage, available fault current, an arc-flash label and
  the calculation date; a one- or two-family dwelling needs only the voltage. Where line and
  load terminals can both be live when open, it carries a shock-hazard warning, per 110.21(B).
- **(D) Separate batteries subject to field servicing:** (1) a disconnect for all ungrounded
  conductors, readily accessible and within sight of the battery; (2) series circuits over 240
  V dc break into segments of 240 V or less; (3) remote-controlled ones are lockable and the
  control location marked; (4) the disconnect carries the nominal battery voltage, fault
  current, arc-flash label and date (a dwelling needs only the voltage).
- **Engine:** (B) graded by `electrical.ess_emergency_shutdown` from the inverter's
  `rsd_shutdown_scope` and the outdoor `rsd_initiator`. (C) marking derived at the battery's
  circuit breaker (words plus nominal output voltage). (D)(1): the same check passes a battery
  whose type states `battery_disconnect_all_ungrounded`, or a `DISCONNECT` on its circuit in
  plan sight; else UNKNOWN. Catlin: UNKNOWN, EG4's manual names "the battery breaker" on the
  cabinet front but not what it opens. The rest is not graded;
  `electrical.service_disconnect_location` and 705.12 do not reach it.

**706.20 Installation.** **706.30 Circuit current.** *(summary kept local)*
- **Engine:** not graded; 705.12 reads `inverter_kw_continuous` for the source current.

## Article 480: stationary batteries

**480.2 Listing.** **480.4** **480.5** **480.6** *(summary kept local)*
- **Engine:** not graded.

**480.7 dc disconnect methods.**
- **(A)** A disconnect for all ungrounded conductors of a stationary battery **over 60 V dc**,
  readily accessible and within sight of the battery.
- **(B) Emergency disconnect.** For one- and two-family dwellings, a disconnecting means or
  its remote control for a stationary battery is at a readily accessible place outdoors, for
  emergency use, labelled "EMERGENCY DISCONNECT". As printed, (B) does not repeat (A)'s 60 V
  condition, where (D) does cross-refer to (A); this is read here as standing alone, which a
  48 V-class battery makes decisive, and is an AHJ question.
- **(C)** Series circuits over 240 V dc nominal, subject to field servicing, break into
  segments of 240 V or less. **(D)** A remote-controlled disconnect under (A) that is out of
  sight of the battery is lockable (110.25) and has the control location marked. **(E)** A dc
  busway may incorporate the disconnect.
- **(F) Notification.** The disconnect is marked in the field; where none is provided, a label
  near the battery says: nominal battery voltage, available fault current, an arc-flash
  label, calculation date. Ex. 1: items (3)-(4) fall away under 150 V dc. **Ex. 2: for a one-
  or two-family dwelling under 150 V dc, only the nominal voltage is needed.**
- **(G)** A facility with utility service and a stationary battery has plaques per 705.10
  (Ex.: where no (A) disconnect is required); stand-alone systems per 710.10.
- **Engine:** (A) is N/A from `battery_nominal_voltage_v` (51.2 V); (B) is met by the
  initiator plus a derived conditional label; (F) prints the voltage.
  `NEC.BATTERY_DISCONNECT`/`BATTERY_EMERGENCY_DISCONNECT` name (A)/(B).

**480.8-480.14.** **480.10** **480.11** **480.12** **480.13** **480.14** *(summary kept local)*
- **Engine:** not graded; the BMS and 12kPV charge control are the manufacturer's.

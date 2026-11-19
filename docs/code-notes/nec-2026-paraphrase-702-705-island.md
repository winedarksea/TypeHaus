# Electrical rules the engine grades: Article 702, Article 705 Parts II-III, EV interactive (2026 NEC)

> Independent engineering notes for Type:Haus. Not published, endorsed or reviewed by the
> National Fire Protection Association. NFPA 70®, National Electrical Code® and NEC® are
> registered trademarks of NFPA, named here only to identify the code a rule comes from.
> This file contains no code text beyond the short label wordings a label must carry. Each
> entry is a summary in our own words, limited to what a check needs. It does not substitute
> for the code: read the edition your jurisdiction has adopted before relying on anything here.
>
> Summaries of rules the engine does not grade, and whole code tables, are kept out of
> the public repo; such an entry keeps its citation and Engine note, marked
> *(summary kept local)*.

Continues `nec-2026-paraphrase-690-705-710.md` (705.1-705.30, 710, all read) and
`nec-2026-paraphrase-110-240-625.md` (625). The owner read these printed pages on 2026-11-14:
702.1-702.12, 705.1-705.2, 705.32-705.81 (705.81 stops after its first words), and 625.44(A)(3)
through 625.52(B)(1). Article 710 is now fully read (710.1-710.15 is all of it).

**Still to read in print:** 705.3-705.4 (if any), the rest of 705.81 and any section after it,
625.52(B)(1)-(4) and its tables. 705.1-705.2, 705.32-705.80 and Articles 702 and 710 are read.

## Catlin, read against these rules (2026-11-14)

- **Which article is the EG4 backup? Both, and the code points that way.** The 12kPV with its
  battery feeds a backup panel through its load port, a permanently installed source that
  carries those loads when the grid fails, so **Article 702 (optional standby)** reaches it:
  702.1 covers permanently installed systems. The same inverter parallels with the utility
  through its grid port, and **702.5(D) sends any system that can run in parallel with the
  normal source to Article 705 Part I or II** (705.1 is the scope: sources in parallel with a
  primary source). Its islanding is **705 Part III** (705.80, 705.81). So the 705.12, 705.20,
  705.28/.30 work in the sister file stands, and 702 adds capacity, transfer, signals and signs.
  An AHJ may call it 705 alone; every requirement below still lands on the same equipment.
- **702.4(A)(3) capacity: graded, advisory (`electrical.standby_capacity`).** The 12kPV's 8 kW
  continuous output covers all seven backup circuits at once (5,649 VA: `CKT-HP3` 1,850, `CKT-WH`
  1,440, `CKT-SUMP` 1,164, `CKT-FRIDGE` 460, `CKT-FREEZER` 340, `CKT-HA` 300 and `CKT-LT-BACKUP`), and the largest
  single one, `CKT-HP3` at 1,850 VA, so the full-load route of 702.4(A)(2)(a) is met. UNKNOWN
  (an owner question): whether the 12kPV is **listed as a PCS** (`EquipmentType.pcs_listed`,
  not stated, never inferred), its control setting (capacity must be at least that), and that
  **reconnection after an overload shutdown is nonautomatic** (the inverter's behaviour). If it
  is not PCS-listed, (A)(3) does not apply and the full-load finding stands alone. The
  sump's 3,500 VA start is inside the inverter's surge rating (`takeoff/backup_calc.py`).
- **705.80 island capacity, report only.** The capacity of an island-mode source is the sum of
  its sources' output maximum currents: today the one inverter, 8,000 W / 240 V = 33.3 A,
  33 A rounded by 705.28(A). Its PV and battery are dc behind the inverter and add nothing
  at the ac output. A V2H charger on the backup side would add its own output current.
- **705.60: the load-port conductors are source output conductors.** `CD-B-INV-BACKUP` carries
  33 A from the inverter to `ED-B-BACKUP-PANEL`, so 705.28(B) wants 41.25 A of ampacity and
  705.30(B) an OCPD of at least 41.25 A. `ED-T-BACKUP-PANEL` states no bus rating and no main,
  and no conductor size is authored: **neither is graded**, and whether the 12kPV's output has
  its own OCPD or the panel needs a main breaker is an owner question (`plans/TODO-nec-2026.md`, 705.60).
- **705.40 loss of primary source, report only.** A listed interactive inverter may simply
  cease exporting when the primary source opens, and need not open all ungrounded
  conductors; it may resume when the source is restored. The 12kPV's product record cites UL
  1741 SA/SB, so `CKT-ESS-GRID` is not asked to open automatically. 705.2 wants the
  interactive equipment listed for the function or field-labelled: the listing is declared
  nowhere, so the claim rests on the product record.
- **705.70 / 705.76 microgrid, report only.** The notes call the backup a microgrid. If it is
  one, Part II wants a microgrid interconnect device between it and the utility (the 12kPV's
  internal relay is typical, listed or field-labelled, and with OCPDs protecting from every
  source), and a control system coordinating different sources if there are several. One
  inverter needs no coordination; **a V2H charger on the same backup would be a second source
  and brings 705.76**, which is why `backup_power.md` section 10 keeps V2H as a separate system.
- **702.5 transfer and 702.7 signs: not modelled; 702.6 signals graded (below).** The 12kPV's internal transfer
  relay is the interconnection equipment (702.5(A): listed, preventing any inadvertent
  interconnection; ties to the earlier 705.20(F) owner question). No meter-mounted transfer
  switch is used (702.5(B) n/a). 702.6 wants an audible and visual signal, where practicable,
  for malfunction and for carrying load: the inverter display and the Home Assistant monitoring
  are the likely means, not authored. **702.7(A)(1): a dwelling gets a permanent placard at the
  225.41 / 230.70(A)(2) disconnect (the meter-main) or an approved visible spot saying where
  each permanently installed standby source's disconnect is.** Fold it into the label owner question, the
  label set (690.12(D) building label, the (D)(2) switch wording, the 705.10 plaque, the
  705.12(B)(2)(b) warning): one placard can serve 705.10 and 702.7(A)(1) together.
- **702.7(B) grounding warning, an owner question.** If removing the grounding or bonding
  connection in the normal source's equipment would cut the electrode-conductor connection to
  the alternate source's grounded conductor, a warning sign goes there. Whether the 12kPV bonds its
  load-port neutral to ground in island mode (a separately derived system, 250.30) or leaves it to
  the service bonding is not authored; ask EG4.
- **Not applicable now:** 702.10-702.12 (no generator or inlet; the 12kPV's GEN port would bring
  702.7(C)'s sign, 702.11 and 702.12 if one is connected); 705.32 (no ground-fault protection of
  equipment under 230.95/215.10 is authored; not read here); 705.45 (a single-phase 120/240 V
  service, no multiphase system); Article 710 (the house is utility-connected, not stand-alone).
- **V2H and EVSE, 625.46-625.52 (not graded; no bidirectional equipment is authored).** The
  hardwired Grizzl-E (`ED-G-EV-1450`) is one-way, so 625.46 (no backfeed through the vehicle on
  loss of the primary source), 625.48 and 625.49 have nothing to grade; the empty
  `CD-B-V2H-SPARE` raceway is the future. A bidirectional EVSE must be listed and marked for it
  (UL 9741 in the note, UL 1741 for the supply side); as standby it follows 702, as a source 705
  (so 705.12/.28/.30 and 705.40 again, and 705.76 beside the 12kPV); one with a receptacle as its
  export point follows 625.60; a second feeder for it is allowed (625.47). **625.50 coupling
  height: graded.** `electrical.evse_circuit` covers 625.40, .41, .43(C), .50 and .54, reading
  625.50 from `ApplianceType.connector_holster_height` (42 in. above the garage floor, a
  reversible default; PASS): indoors the coupling means is at least 18 in. above the floor,
  outdoors 24 in. above grade, unless listed and marked for the place.

## Article 702: optional standby systems

**702.1 Scope; 702.3.** **702.3** *(summary kept local)*
- **Engine:** not graded.

**702.4 Capacity and rating.** (A)(1) With manual or nonautomatic load connection, the source has
adequate capacity for everything run at once, and the user chooses the loads. (A)(2) With
automatic load connection, either (a) the source can carry the full load connected automatically,
or (b) the source's capacity is managed by an EMS, per 130.30 or a PCS control setting per
130.70. **(A)(3) For one- and two-family dwellings, a multimode inverter system listed as a PCS
for overload control has capacity at least the PCS control setting and no less than the largest
single utilization equipment on it; after an overload shutdown, reconnection is nonautomatic.**
The notes: multimode inverters often work mostly interactively and can give standby continuity
within their capacity, are listed to hold voltage and frequency, and a PCS stops them safely in
overload; a PCS typically controls loads at branch, feeder or both levels.
- **Engine:** `electrical.standby_capacity` (advisory) grades (A)(2)(a) and the capacity half of
  (A)(3) from `takeoff/backup_calc.py`'s circuits and the inverter's `inverter_kw_continuous`;
  the PCS listing, setting and nonautomatic reconnection are UNKNOWN. (A)(1) is not graded.
  (A)(3) is N/A where the inverter's `pcs_functions` (published) lack overload control;
  Catlin's 12kPV lists export/import limiting and ESS modes.

**702.5 Interconnection or transfer equipment.** *(summary kept local)*
- **Engine:** not graded.

**702.6 Signals.** Where practicable, audible and visual signals show (A) a malfunction of the
standby source and (B) that it is carrying load (not for portable sources).
- **Engine:** `electrical.standby_capacity` reads the inverter's published `standby_signals`:
  all four (each condition, audible and visual) PASS, fewer or none stated UNKNOWN ("where
  practicable" and an added annunciator are the AHJ's). Catlin: UNKNOWN; the 12kPV manual
  publishes a red fault LED only (ESS manual §16.1, QSG §11.3), no buzzer and no off-grid
  indicator, so a Home Assistant alert is the likely answer.

**702.7 Signs.** **(A)(1) At a one- or two-family dwelling,** permanent placards, labels or
directories at the disconnects required by 225.41 and 230.70(A)(2), or at an approved readily
visible spot, say where each permanently installed on-site standby source's disconnect is, or
the means to shut down the prime mover per 445.19(C). (A)(2) Otherwise, at the service equipment
or an approved visible spot: the type and location of each on-site source. **(B)** Where removing
the grounding or bonding connection in the normal source's equipment interrupts the electrode
conductor's tie to the alternate source's grounded conductor, the equipment carries: "WARNING:
SHOCK HAZARD EXISTS IF GROUNDING ELECTRODE CONDUCTOR OR BONDING JUMPER CONNECTION IN THIS EQUIPMENT
IS REMOVED WHILE ALTERNATE SOURCE(S) IS ENERGIZED." (110.21(B) applies). **(C)** A power inlet for
a temporary portable generator carries a sign naming the derived-system type the transfer
equipment wiring supports: "FOR CONNECTION OF A SEPARATELY DERIVED (BONDED NEUTRAL) SYSTEM ONLY"
or "FOR CONNECTION OF A NONSEPARATELY DERIVED (FLOATING NEUTRAL) SYSTEM ONLY".
- **Engine:** (A)(1) derived on the 705.10 placard; (B) and (C) not modelled.

**702.10-702.12 Wiring, portable and outdoor generators.** *(summary kept local)*
- **Engine:** not graded; Catlin has no generator or inlet.

## Article 705 Part I (rest), Part II and Part III

**705.1 / 705.2.** **705.2** *(summary kept local)*
- **Engine:** not graded; the listing is on the product record, not a field.

**705.32 Ground-fault protection of equipment.** *(summary kept local)*
- **Engine:** not graded; none is authored.

**705.40 Loss of primary source.** *(summary kept local)*
- **Engine:** not graded (the 12kPV is described as UL 1741 listed on its product record).

**705.45 Unbalanced interconnections.** *(summary kept local)*
- **Engine:** not graded; Catlin's service is single-phase.

**705.50** **705.60** **705.65** **705.70 Microgrid interconnect devices:** **705.76 Microgrid control systems** *(summary kept local)*
- **Engine:** not graded.

**705.80** **705.81** *(summary kept local)*
- **Engine:** not graded; see the Catlin findings.

## Article 625 (detail beyond `nec-2026-paraphrase-110-240-625.md`)

**625.44 (A)(3)-(5), (B), (C).** *(summary kept local)*
- **Engine:** not graded. `CKT-EV-1450` is hardwired and fixed ((C)); `CKT-GAR-240`'s 6-20R is a
  (B) configuration.

**625.46 / 625.47 / 625.48 / 625.49 / 625.50 / 625.52.** 625.46: means ensure that, on loss of
the utility or other system's voltage, no energy is backfed through the vehicle and its supply
equipment to the premises wiring unless 625.48 permits. 625.47: more than one feeder or branch
circuit may serve equipment identified for it. 625.48: EVSE or WPTE with power export, in an
interactive system serving as optional standby, a power production source or a bidirectional feed,
is listed and marked for it; as optional standby, Article 702 applies; as a production source,
Article 705; EVPE whose export is a receptacle follows 625.60 (notes: UL 1741, UL 9741, SAE J3072).
625.49: export-capable and bidirectional EVSE may be part of an interconnected system in island
mode. **625.50:** the EVSE is listed for the electrical coupling of its connector (conductive or
inductive) to the vehicle; unless specifically listed and marked for the place, the coupling
means is stored or located at least 450 mm (18 in.) above the floor indoors, or 600 mm (24 in.)
above grade outdoors; not for portable EVSE built under 625.44(A). **625.52 Ventilation:** (A)
none is required where vehicle storage batteries are used, or the equipment is listed for indoor
charging without ventilation; (B) where listed as needing it, mechanical ventilation (a fan) with
supply and exhaust, permanent, intake from and vent directly to outdoors, positive-pressure
systems only in buildings or areas designed and approved for it, sized by 625.52(B)(1)-(4)
(Tables 625.52(B)(1)(1) and (2) per vehicle charged at once: not read).
- **Engine:** 625.50 graded by `electrical.evse_circuit` from
  `ApplianceType.connector_holster_height`; the rest not graded.

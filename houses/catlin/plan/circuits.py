"""Catlin panel schedule — every branch circuit in ED-B-PANEL (plans/electrical_notes.md).

NOT ``# haus: editable``: circuits are schedule data, not geometry — nothing here can be
dragged. Devices/equipment reference these tags via their ``circuit=`` field (the editable
files), and ``electrical.circuit_refs`` reconciles the two directions.

Conventions:
- ``poles=2`` is a 240V circuit; ``poles=1`` is 120V.
- ``gfci=True`` is protection at the *breaker* (plans/TODO.md: GFCI at breaker, not outlet).
- ``backup=True`` marks the circuits behind the smart-relay backup subsystem (Shelly Pro
  4PM in ED-B-BACKUP-ENCL) — the backup loads named in electrical_notes.md lines 9-29.
- ``load_va`` is authored where the devices carry no typed load (equipment, lighting
  allowances); circuits whose receptacle types carry ``load_va`` leave it None and the
  panel-schedule takeoff sums the device types.
"""

from __future__ import annotations

from typehaus import Circuit

_PANEL = "ED-B-PANEL"

CIRCUITS = (
    # --- 240V dedicated loads (electrical_notes.md line 4) ---------------------------
    Circuit(uid="CKT001AAAA", tag="CKT-RANGE", panel_ref=_PANEL, breaker_amps=50, poles=2,
            nema="14-50R", load_va=12000, description="Kitchen range"),
    Circuit(uid="CKT002AAAA", tag="CKT-DRYER", panel_ref=_PANEL, breaker_amps=30, poles=2,
            nema="14-30R", description="Dryer"),
    Circuit(uid="CKT003AAAA", tag="CKT-EV-1450", panel_ref=_PANEL, breaker_amps=50, poles=2,
            nema="14-50R", description="EV charging, NEMA 14-50 (garage)"),
    Circuit(uid="CKT004AAAA", tag="CKT-EV-620", panel_ref=_PANEL, breaker_amps=20, poles=2,
            nema="6-20R", description="EV charging, NEMA 6-20 (garage)"),
    Circuit(uid="CKT005AAAA", tag="CKT-SPA", panel_ref=_PANEL, breaker_amps=50, poles=2,
            gfci=True, load_va=11500, description="Hot tub (sunken garden)"),
    # 50A/2p GFCI per notes/sauna_shower_basement_detail.md ("240V, 50A GFCI breaker and
    # wiring to sauna heater (max 10.5 kW)"). Was 30A, which only carries ~5.5 kW continuous
    # — half what RM-B-SAUNA's 513 cf heated volume needs. EQ-B-SAUNA-HTR is 9 kW = 37.5A,
    # 46.9A at the 125% continuous factor, so 50A is the breaker and 10.5 kW the headroom.
    Circuit(uid="CKT006AAAA", tag="CKT-SAUNA", panel_ref=_PANEL, breaker_amps=50, poles=2,
            gfci=True, load_va=9000, description="Sauna heater (EQ-B-SAUNA-HTR)"),
    Circuit(uid="CKT007AAAA", tag="CKT-WH-240", panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=4500, description="Water heater, 240V tank (EQ-B-WH2)"),
    Circuit(uid="CKT008AAAA", tag="CKT-ERV", panel_ref=_PANEL, breaker_amps=15, poles=2,
            load_va=200, description="ERV"),
    Circuit(uid="CKT009AAAA", tag="CKT-MINI-1", panel_ref=_PANEL, breaker_amps=25, poles=2,
            load_va=4800, description="Minisplit, large (upstairs zone)"),
    Circuit(uid="CKT010AAAA", tag="CKT-MINI-2", panel_ref=_PANEL, breaker_amps=15, poles=2,
            backup=True, load_va=1500, description="Minisplit, small deep-cold (basement)"),
    Circuit(uid="CKT011AAAA", tag="CKT-KETTLE", panel_ref=_PANEL, breaker_amps=20, poles=2,
            nema="6-20R", load_va=3840, description="Kitchen kettle outlet (6-20R half)"),
    # PV backfeed lands at the opposite end of the bus from the main (120% rule headroom
    # is why the panel is 225A on a 200A service). Source, not load: load_va stays 0.
    Circuit(uid="CKT012AAAA", tag="CKT-PV", panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=0, description="PV backfeed, rooftop array via ED-A-PV-JB"),
    Circuit(uid="CKT013AAAA", tag="CKT-SPARE-240", panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=0, description="Spare 2-pole (conduit stubbed for future 240V)"),

    # --- 120V backup subsystem (electrical_notes.md lines 9-29) ----------------------
    Circuit(uid="CKT014AAAA", tag="CKT-WH-HP", panel_ref=_PANEL, breaker_amps=15, poles=1,
            backup=True, load_va=500,
            description="Heat pump water heater, Rheem 120V (EQ-B-WH, compressor only)"),
    Circuit(uid="CKT015AAAA", tag="CKT-SUMP", panel_ref=_PANEL, breaker_amps=20, poles=1,
            backup=True, load_va=1000, description="Sump pump"),
    Circuit(uid="CKT016AAAA", tag="CKT-FRIDGE", panel_ref=_PANEL, breaker_amps=20, poles=1,
            backup=True, load_va=800,
            description="Kitchen outlet 1: fridge + freezer + PoE WiFi"),
    Circuit(uid="CKT017AAAA", tag="CKT-HA", panel_ref=_PANEL, breaker_amps=15, poles=1,
            backup=True, load_va=300, description="Basement outlet 1: HA server + router"),
    Circuit(uid="CKT018AAAA", tag="CKT-LT-BACKUP", panel_ref=_PANEL, breaker_amps=15, poles=1,
            backup=True, load_va=100,
            description="Basement + kitchen lighting (LED, backup light)"),
    Circuit(uid="CKT019AAAA", tag="CKT-BACKUP-FEED", panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=200, description="Backup enclosure feed (DIN relays, 24V PSU, UPS)"),

    # --- general-use 120V ------------------------------------------------------------
    Circuit(uid="CKT020AAAA", tag="CKT-KITCH-SA1", panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, load_va=1500, description="Kitchen small-appliance 1 (counter west)"),
    Circuit(uid="CKT021AAAA", tag="CKT-KITCH-SA2", panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, load_va=1500, description="Kitchen small-appliance 2 (counter east)"),
    Circuit(uid="CKT022AAAA", tag="CKT-DISHWASHER", panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1200, description="Dishwasher + disposer (sink base)"),
    Circuit(uid="CKT023AAAA", tag="CKT-LAUNDRY", panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500, description="Laundry receptacle (washer)"),
    Circuit(uid="CKT024AAAA", tag="CKT-LT-MAIN", panel_ref=_PANEL, breaker_amps=15, poles=1,
            load_va=600, description="General lighting — main storey"),
    Circuit(uid="CKT025AAAA", tag="CKT-LT-UPPER", panel_ref=_PANEL, breaker_amps=15, poles=1,
            load_va=600, description="General lighting — second + attic"),
    Circuit(uid="CKT026AAAA", tag="CKT-RC-MAIN", panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500, description="General receptacles — main storey"),
    Circuit(uid="CKT027AAAA", tag="CKT-RC-SECOND", panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500, description="General receptacles — second storey"),
    Circuit(uid="CKT028AAAA", tag="CKT-RC-BSMT", panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, load_va=1500,
            description="General receptacles — basement + spa convenience"),
    Circuit(uid="CKT029AAAA", tag="CKT-RC-ATTIC", panel_ref=_PANEL, breaker_amps=15, poles=1,
            load_va=1000, description="General receptacles — attic rooms"),
    Circuit(uid="CKT030AAAA", tag="CKT-RC-GARAGE", panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, load_va=1500, description="Garage general receptacles"),
)

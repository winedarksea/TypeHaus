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
- ``slot`` is the physical breaker position: odd numbers run down the left column, even
  down the right, and a 2-pole breaker takes ``slot`` and ``slot + 2`` (same column).
  PV backfeeds at the bottom of the bus (40/42), opposite the main (120% rule).
  HONEST STATE: 13 two-pole + 22 one-pole = 48 spaces against ED-T-PANEL's 42, so the
  last six 120V circuits sit in slots 43-48 past the enclosure and
  ``electrical.panel_spaces`` FAILS until the panel is swapped for a 54-space unit.
"""

from __future__ import annotations

from typehaus import Circuit, LoadManagement

_PANEL = "ED-B-PANEL"

CIRCUITS = (
    # --- 240V dedicated loads (electrical_notes.md line 4) ---------------------------
    Circuit(uid="CKT001AAAA", tag="CKT-RANGE", slot=1, panel_ref=_PANEL, breaker_amps=50, poles=2,
            nema="14-50R", load_va=12000, description="Kitchen range"),
    Circuit(uid="CKT002AAAA", tag="CKT-DRYER", slot=5, panel_ref=_PANEL, breaker_amps=30, poles=2,
            nema="14-30R", description="Dryer"),
    # The two EV circuits author their load_va explicitly (same figures the receptacle
    # types carry: 240x40 and 240x16 continuous) because LOAD_MANAGEMENTS below reads the
    # managed group's connected load off the *circuits*, not the devices.
    Circuit(uid="CKT003AAAA", tag="CKT-EV-1450", slot=9, panel_ref=_PANEL, breaker_amps=50, poles=2,
            nema="14-50R", load_va=9600,
            description="EV charging, NEMA 14-50 (garage) — Emporia Vue managed"),
    Circuit(uid="CKT004AAAA", tag="CKT-EV-620", slot=13, panel_ref=_PANEL, breaker_amps=20, poles=2,
            nema="6-20R", load_va=3840,
            description="EV charging, NEMA 6-20 (garage) — Emporia Vue managed"),
    Circuit(uid="CKT005AAAA", tag="CKT-SPA", slot=17, panel_ref=_PANEL, breaker_amps=50, poles=2,
            gfci=True, load_va=11500, description="Hot tub (sunken garden)"),
    # 50A/2p GFCI per notes/sauna_shower_basement_detail.md ("240V, 50A GFCI breaker and
    # wiring to sauna heater (max 10.5 kW)"). Was 30A, which only carries ~5.5 kW continuous
    # — half what RM-B-SAUNA's 513 cf heated volume needs. EQ-B-SAUNA-HTR is 9 kW = 37.5A,
    # 46.9A at the 125% continuous factor, so 50A is the breaker and 10.5 kW the headroom.
    Circuit(uid="CKT006AAAA", tag="CKT-SAUNA", slot=21, panel_ref=_PANEL, breaker_amps=50, poles=2,
            gfci=True, load_va=9000, description="Sauna heater (EQ-B-SAUNA-HTR)"),
    Circuit(uid="CKT007AAAA", tag="CKT-WH-240", slot=25, panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=4500, description="Water heater, 240V tank (EQ-B-WH2)"),
    Circuit(uid="CKT008AAAA", tag="CKT-ERV", slot=2, panel_ref=_PANEL, breaker_amps=15, poles=2,
            load_va=200, description="ERV"),
    Circuit(uid="CKT009AAAA", tag="CKT-MINI-1", slot=6, panel_ref=_PANEL, breaker_amps=25, poles=2,
            load_va=4800, description="Minisplit, large (upstairs zone)"),
    Circuit(uid="CKT010AAAA", tag="CKT-MINI-2", slot=10, panel_ref=_PANEL, breaker_amps=15, poles=2,
            backup=True, load_va=1500, description="Minisplit, small deep-cold (basement)"),
    Circuit(uid="CKT011AAAA", tag="CKT-KETTLE", slot=14, panel_ref=_PANEL, breaker_amps=20, poles=2,
            nema="6-20R", load_va=3840, description="Kitchen kettle outlet (6-20R half)"),
    # PV backfeed lands at the opposite end of the bus from the main (120% rule headroom
    # is why the panel is 225A on a 200A service). Source, not load: load_va stays 0.
    Circuit(uid="CKT012AAAA", tag="CKT-PV", slot=40, panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=0, description="PV backfeed, rooftop array via ED-A-PV-JB"),
    Circuit(uid="CKT013AAAA", tag="CKT-SPARE-240", slot=18, panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=0, description="Spare 2-pole (conduit stubbed for future 240V)"),

    # --- electric space heating (2026-07-25) -----------------------------------------
    #
    # Supplemental only: the minisplits do the heating work and these five take the chill
    # off specific surfaces. None of them is sized to carry a room.
    #
    # The three floor zones are 120V mat at 12 W/ft2 over the polygons authored in
    # storeys/main.py and storeys/second.py, so each circuit's VA is that zone's area x 12.
    # 15A rather than 20A because these are 4-6A loads: 12/2 to a 5A mat is wire nobody
    # needs, and a 15A GFCI breaker is the same part. Each zone keeps its own circuit — a
    # shared one would put two rooms' floors behind one 5 mA trip, and the two main-storey
    # stats are 23' apart across the centre bearing wall anyway.
    #
    # GFCI on all three: NEC 424.44(G) requires it for heating cable in the floor of a
    # bathroom or kitchen, which covers CKT-FH-BATH2 and CKT-FH-BATH1 outright. The
    # dining zone is in RM-M-LIVING and outside the letter of that rule, but mat
    # manufacturers require Class A protection on every mat regardless, and it would be a
    # strange schedule that protected two identical mats and not the third.
    #
    # Was CKT-FH-SAUNA until 2026-07-25 — RM-B-SAUNA has no floor heat (see the note in
    # storeys/basement.py), so that zone, its circuit and its stat are all gone.
    Circuit(uid="CKT031AAAA", tag="CKT-FH-BATH2", slot=29, panel_ref=_PANEL, breaker_amps=15, poles=1,
            gfci=True, load_va=498,
            description="Radiant floor heat — main bath (FH-M-BATH2, 41.5 ft2)"),
    Circuit(uid="CKT032AAAA", tag="CKT-FH-DINING", slot=31, panel_ref=_PANEL, breaker_amps=15, poles=1,
            gfci=True, load_va=696,
            description="Radiant floor heat — under the dining table (FH-M-DINING, 58.0 ft2)"),
    Circuit(uid="CKT033AAAA", tag="CKT-FH-BATH1", slot=33, panel_ref=_PANEL, breaker_amps=15, poles=1,
            gfci=True, load_va=509,
            description="Radiant floor heat — NW bathroom (FH-S-BATH1, 42.4 ft2)"),
    # 1,500 W at 120V = 12.5A, and both of these run long enough to be continuous loads:
    # 12.5 x 1.25 = 15.6A, which fits the 16A a 20A breaker allows and does *not* fit a
    # 15A one (12A). That is why these two are 20A where the mats are 15A.
    #
    # Neither is GFCI. Both are hard-wired equipment, and NEC 210.8(A) protects
    # *receptacles* — the garage rule in (A)(2) included. Cord-and-plug versions of either
    # would need it, which is the reason both are modeled as Equipment with the circuit on
    # the placeable rather than as a receptacle with something plugged into it.
    Circuit(uid="CKT034AAAA", tag="CKT-FIREPLACE", slot=35, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500,
            description="Electric fireplace, living room SE corner (EQ-M-FIREPLACE)"),
    Circuit(uid="CKT035AAAA", tag="CKT-GAR-HEAT", slot=37, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500,
            description="Garage bench heater, 1.5 kW fan-forced (EQ-G-HEATER)"),

    # --- 120V backup subsystem (electrical_notes.md lines 9-29) ----------------------
    Circuit(uid="CKT014AAAA", tag="CKT-WH-HP", slot=39, panel_ref=_PANEL, breaker_amps=15, poles=1,
            backup=True, load_va=500,
            description="Heat pump water heater, Rheem 120V (EQ-B-WH, compressor only)"),
    Circuit(uid="CKT015AAAA", tag="CKT-SUMP", slot=41, panel_ref=_PANEL, breaker_amps=20, poles=1,
            backup=True, load_va=1000, description="Sump pump"),
    Circuit(uid="CKT016AAAA", tag="CKT-FRIDGE", slot=22, panel_ref=_PANEL, breaker_amps=20, poles=1,
            backup=True, load_va=800,
            description="Kitchen outlet 1: fridge + freezer + PoE WiFi"),
    Circuit(uid="CKT017AAAA", tag="CKT-HA", slot=24, panel_ref=_PANEL, breaker_amps=15, poles=1,
            backup=True, load_va=300, description="Basement outlet 1: HA server + router"),
    # load_va is None on all three lighting circuits since the lighting plan went in: the
    # luminaires carry real typed loads now, so the panel-schedule takeoff sums the
    # fixtures actually on each circuit instead of repeating a placeholder allowance.
    Circuit(uid="CKT018AAAA", tag="CKT-LT-BACKUP", slot=26, panel_ref=_PANEL, breaker_amps=15, poles=1,
            backup=True,
            description="Basement + kitchen lighting (LED, backup light)"),
    Circuit(uid="CKT019AAAA", tag="CKT-BACKUP-FEED", slot=28, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=200, description="Backup enclosure feed (DIN relays, 24V PSU, UPS)"),

    # --- general-use 120V ------------------------------------------------------------
    Circuit(uid="CKT020AAAA", tag="CKT-KITCH-SA1", slot=30, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, load_va=1500, description="Kitchen small-appliance 1 (counter west)"),
    Circuit(uid="CKT021AAAA", tag="CKT-KITCH-SA2", slot=32, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, load_va=1500, description="Kitchen small-appliance 2 (counter east)"),
    Circuit(uid="CKT022AAAA", tag="CKT-DISHWASHER", slot=34, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1200, description="Dishwasher + disposer (sink base)"),
    Circuit(uid="CKT023AAAA", tag="CKT-LAUNDRY", slot=36, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500, description="Laundry receptacle (washer)"),
    Circuit(uid="CKT024AAAA", tag="CKT-LT-MAIN", slot=38, panel_ref=_PANEL, breaker_amps=15, poles=1,
            description="General lighting — main storey, porch and garage"),
    Circuit(uid="CKT025AAAA", tag="CKT-LT-UPPER", slot=43, panel_ref=_PANEL, breaker_amps=15, poles=1,
            description="General lighting — second + attic"),
    Circuit(uid="CKT026AAAA", tag="CKT-RC-MAIN", slot=44, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500, description="General receptacles — main storey"),
    Circuit(uid="CKT027AAAA", tag="CKT-RC-SECOND", slot=45, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500, description="General receptacles — second storey"),
    Circuit(uid="CKT028AAAA", tag="CKT-RC-BSMT", slot=46, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, load_va=1500,
            description="General receptacles — basement + spa convenience"),
    Circuit(uid="CKT029AAAA", tag="CKT-RC-ATTIC", slot=47, panel_ref=_PANEL, breaker_amps=15, poles=1,
            load_va=1000, description="General receptacles — attic rooms"),
    Circuit(uid="CKT030AAAA", tag="CKT-RC-GARAGE", slot=48, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, load_va=1500, description="Garage general receptacles"),
)

# --- Load management (NEC 625.42) ------------------------------------------------------
#
# The open decision in plans/TODO.md — "service load exceeds the service" — is settled
# here with an EMS rather than a service upgrade. Unmanaged, the 220.82 estimate lands at
# 223.7A against the 200A service; the two EV circuits contribute 13,440 VA (56.0A) of
# that, so everything else in the house is 167.7A and the headroom left for EV charging is
# 32.3A (7,752 VA).
#
# The Emporia Vue's dynamic load management watches the whole-panel CTs and throttles the
# 14-50 EVSE, so the pair is capped at 5,760 VA — 24A at 240V, both EV circuits together.
# That is the largest round setting that stays clearly inside the 32.3A headroom (it lands
# the estimate near 192A, ~8A of margin for the loads this house has not authored yet) and
# it is above the 6A/1.4 kW floor an EVSE must never be throttled below, so a car still
# charges at ~24A whenever nothing else is competing for the service.
LOAD_MANAGEMENTS = (
    LoadManagement(uid="EMSEV0AAAA", tag="LM-EV",
                   managed_circuits=("CKT-EV-1450", "CKT-EV-620"),
                   max_simultaneous_va=5760, strategy="ems",
                   source="Emporia Vue dynamic load management (NEC 625.42 EMS)"),
)

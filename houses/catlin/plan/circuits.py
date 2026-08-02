"""Catlin panel schedule — every branch circuit in ED-B-PANEL (plans/electrical_notes.md).

NOT ``# haus: editable``: circuits are schedule data, not geometry — nothing here can be
dragged. Devices/equipment reference these tags via their ``circuit=`` field (the editable
files), and ``electrical.circuit_refs`` reconciles the two directions.

Conventions:
- ``poles=2`` is a 240V circuit; ``poles=1`` is 120V.
- ``gfci=True`` is protection at the *breaker* (plans/TODO.md: GFCI at breaker, not outlet).
- ``backup_tier`` places a circuit on the backup microgrid (notes/backup_power.md).
  ALWAYS_ON rides the EG4's load output through the whole outage; SHED sits behind a
  Shelly Pro 4PM relay or a relay-driven contactor in ED-B-BACKUP-ENCL and drops when the
  battery is low and the sun is not out. Every tiered circuit is homed to
  ``ED-B-BACKUP-PANEL``, the 12-space subpanel on the inverter's dedicated load output —
  which is what makes the tier physical rather than a label.
- ``duty_cycle`` is the authored average-draw fraction the autonomy calc multiplies the
  connected VA by (→ takeoff/backup_calc.py). Estimates, each with its basis in a comment;
  a tiered circuit without one is reported as an unknown contributor, never as zero.
- ``source=True`` marks a power-source interconnection — excluded from the 220.82 load
  summary and counted by the 705.12 busbar check instead.
- ``load_va`` is authored where the devices carry no typed load (equipment, lighting
  allowances); circuits whose receptacle types carry ``load_va`` leave it None and the
  panel-schedule takeoff sums the device types.
- ``slot`` is the physical breaker position: odd numbers run down the left column, even
  down the right, and a 2-pole breaker takes ``slot`` and ``slot + 2`` (same column).
  The ESS grid port backfeeds at the bottom of the bus (40/42), opposite the main (120%
  rule); ``code.NEC_705_12_interconnection`` now grades that arithmetic instead of this
  comment asserting it.
  HONEST STATE (2026-08-02, the backup-microgrid refactor): ED-B-PANEL carries 15 two-pole
  + 16 one-pole = 46 spaces of the 54 ED-T-PANEL holds — eight spaces freed by moving the
  six backup circuits (7 poles) and retiring CKT-BACKUP-FEED (1 pole) to the subpanel, so
  eight are now spare. ED-B-BACKUP-PANEL carries 1 two-pole + 5 one-pole = 7 of its 12.
  ``electrical.panel_spaces`` reconciles both.
"""

from __future__ import annotations

from typehaus import BackupTier, Circuit, LoadManagement

_PANEL = "ED-B-PANEL"
# The backup subpanel on the EG4 12kPV's dedicated load output (plan/electrical.py). The
# tiered circuits live here rather than in ED-B-PANEL because that is physically what a
# hybrid inverter's load port is: a separate bus that stays energized when the grid does
# not. Slot numbering is the same convention — odd left, even right.
_BACKUP_PANEL = "ED-B-BACKUP-PANEL"

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
    # The three Gree heat-pump systems (plan/electrical.py). A multi's indoor heads are fed
    # from the outdoor unit, so System 2's three heads add no circuits; System 1's ducted
    # air handler does get its own, because a ducted blower is fed at the unit.
    Circuit(uid="CKT009AAAA", tag="CKT-HP1", slot=6, panel_ref=_PANEL, breaker_amps=25, poles=2,
            load_va=4800, description="Heat pump 1 outdoor, Vireo GEN3 (EQ-M-HP1-OD)"),
    # uids CKT036/037, not CKT031/032: those two were already spent on the radiant-floor
    # circuits below, so this pair was a straight duplicate from the day it was authored
    # (found 2026-08-01). Nothing references a Circuit by uid — devices name the tag — so
    # renumbering the newer pair is the whole fix.
    Circuit(uid="CKT036AAAA", tag="CKT-HP1-AH", slot=50, panel_ref=_PANEL, breaker_amps=15, poles=2,
            load_va=1000,
            description="Heat pump 1 indoor, concealed ducted air handler (EQ-S-HP1-AH)"),
    Circuit(uid="CKT037AAAA", tag="CKT-HP2", slot=49, panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=6000,
            description="Heat pump 2 outdoor, Multi Ultra 3-port (EQ-M-HP2-OD; feeds its 3 heads)"),
    # System 3 is the one on the backup microgrid: a true-VFD compressor soft-starts, which
    # is what makes it carryable by the battery inverter at all. Lives on the subpanel with
    # the rest of the backup program — see the microgrid block below.
    # GFCI at the breaker (2026-08-01, code.E3902_gfci_locations): ED-M-LIVING-KET1 sits
    # 3.2' from the kitchen sink. E3902.10 reaches it even though it is 240V — the section
    # covers receptacles from 125V through 250V at 50A or less, not just the 125V ones — and
    # a 2-pole GFCI breaker is the only place to put protection on a 6-20R.
    Circuit(uid="CKT011AAAA", tag="CKT-KETTLE", slot=14, panel_ref=_PANEL, breaker_amps=20, poles=2,
            nema="6-20R", gfci=True, load_va=3840,
            description="Kitchen kettle outlet (6-20R half)"),
    # The EG4 12kPV's grid port, at the opposite end of the bus from the main (120% rule
    # headroom is why the panel is 225A on a 200A service). Both the PV array and the
    # battery reach the service through this one breaker now — the array no longer
    # backfeeds on its own, it lands on the inverter's MPPTs (EQ-B-ESS-INV).
    #
    # 50A: the 12kPV puts out 8,000 W continuous at 240V = 33.3A, x125% = 41.7A, and 50A is
    # the next standard size (datasheet 2026-08-02; grid passthrough is rated 80A, which is
    # the pass-through capability, not the backfeed). The 705.12 ceiling on this bus is
    # 225 x 1.2 - 200 = 70A, so 50A leaves 20A for a future second source (V2H).
    #
    # source=True is what excludes it from the 220.82 load summary and includes it in the
    # 705.12 busbar check — the string-matching on "pv "/"backfeed" that used to do the
    # first half is gone.
    Circuit(uid="CKT012AAAA", tag="CKT-ESS-GRID", slot=40, panel_ref=_PANEL, breaker_amps=50,
            poles=2, source=True, load_va=0,
            description="EG4 12kPV grid port — PV + battery interconnection (EQ-B-ESS-INV)"),
    Circuit(uid="CKT013AAAA", tag="CKT-SPARE-240", slot=18, panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=0, description="Spare 2-pole (conduit stubbed for future 240V)"),

    # --- electric space heating (2026-07-25) -----------------------------------------
    #
    # Supplemental only: the three heat-pump systems do the heating work and these five take the chill
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
    # AFCI too (2026-08-01): this mat is in RM-M-LIVING, and E3902.16 covers the 120V 15/20A
    # circuits *supplying outlets or devices* in a living room — a heating mat is a device.
    # The two bath mats are not: E3902.16's room list stops at the bathroom door.
    Circuit(uid="CKT032AAAA", tag="CKT-FH-DINING", slot=31, panel_ref=_PANEL, breaker_amps=15, poles=1,
            gfci=True, afci=True, load_va=696,
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
            afci=True, load_va=1500,
            description="Electric fireplace, living room SE corner (EQ-M-FIREPLACE)"),
    Circuit(uid="CKT035AAAA", tag="CKT-GAR-HEAT", slot=37, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500,
            description="Garage infrared heater lamp, 1.5 kW (EQ-G-HEATER)"),

    # --- the backup microgrid (notes/backup_power.md) ---------------------------------
    #
    # Every circuit below is homed to ED-B-BACKUP-PANEL, the 12-space subpanel on the
    # EG4 12kPV's dedicated load output. Two tiers:
    #
    #   ALWAYS_ON  rides the whole outage — the food, the network, and enough light to
    #              live in the two rooms that matter.
    #   SHED       is dropped by a relay (or a relay-driven contactor, for the 2-pole and
    #              over-16A ones) when the battery is low and the sun is not out.
    #
    # ``duty_cycle`` on each is an ESTIMATE with its basis stated, authored 2026-08-02 for
    # the autonomy calc. They are the least certain numbers in this file and the ones the
    # 48-hour verdict is most sensitive to — revise them against real metering, not vibes.
    #
    # CKT-BACKUP-FEED is retired in the same change: the DIN gear it fed is now downstream
    # of the inverter's load output like everything else on this bus, and a circuit whose
    # only job was to feed the backup enclosure from the *grid* side is exactly backwards.

    # -- ALWAYS_ON --
    # 800 VA is the *circuit allowance*, not the draw, and the gap between those two is
    # the whole reason duty_cycle exists. A current-generation fridge averages ~60 W over
    # its cycle and a chest freezer ~45 W; the PoE AP adds ~15 W that never stops. 120 W of
    # 800 VA = 0.15. Still the largest always-on term, and the one most worth metering.
    Circuit(uid="CKT016AAAA", tag="CKT-FRIDGE", slot=2, panel_ref=_BACKUP_PANEL,
            breaker_amps=20, poles=1, backup_tier=BackupTier.ALWAYS_ON, afci=True,
            load_va=800, duty_cycle=0.15,
            description="Kitchen outlet 1: fridge + freezer + PoE WiFi"),
    # 300 VA is again an outlet allowance. The real load is a router (~12 W) and a small
    # always-on HA server (~28 W) — 40 W of 300 VA = 0.13. Not a duty cycle in the
    # compressor sense: this load never cycles off, the allowance is simply generous.
    Circuit(uid="CKT017AAAA", tag="CKT-HA", slot=4, panel_ref=_BACKUP_PANEL,
            breaker_amps=15, poles=1, backup_tier=BackupTier.ALWAYS_ON, gfci=True,
            load_va=300, duty_cycle=0.13,
            description="Basement outlet 1: HA server + router"),
    # load_va is None: the luminaires carry real typed loads and the panel-schedule takeoff
    # sums the fixtures actually on the circuit (558 VA today). 0.15 is about five hours of
    # the twenty-four with roughly two thirds of those fixtures lit — an outage evening in
    # the kitchen and the mechanical room while the rest of the house stays dark.
    Circuit(uid="CKT018AAAA", tag="CKT-LT-BACKUP", slot=6, panel_ref=_BACKUP_PANEL,
            breaker_amps=15, poles=1, backup_tier=BackupTier.ALWAYS_ON, afci=True,
            duty_cycle=0.15,
            description="Basement + kitchen lighting (LED, backup light)"),

    # -- SHED --
    # 2-pole, so it switches through a relay-driven contactor rather than a Pro 4PM channel
    # (takeoff/electrical.py::RELAY_CHANNEL_AMPS). 0.4: a modulating 9K head holding one
    # room in shoulder weather runs most of the time at a fraction of nameplate; this is
    # the term that decides whether the shed tier is affordable at all.
    Circuit(uid="CKT010AAAA", tag="CKT-HP3", slot=1, panel_ref=_BACKUP_PANEL,
            breaker_amps=15, poles=2, backup_tier=BackupTier.SHED, load_va=1500,
            duty_cycle=0.4,
            description="Heat pump 3 outdoor, Sapphire R32 VFD (EQ-M-HP3-OD; shed tier)"),
    # Compressor only — no resistance element reaches the backup bus, by design. A HPWH
    # makes a household day of hot water in three to four hours of compressor run, so
    # 0.15 of twenty-four.
    Circuit(uid="CKT014AAAA", tag="CKT-WH-HP", slot=5, panel_ref=_BACKUP_PANEL,
            breaker_amps=15, poles=1, backup_tier=BackupTier.SHED, load_va=500,
            duty_cycle=0.15,
            description="Heat pump water heater, Rheem 120V (EQ-B-WH, compressor only)"),
    # GFCI at the breaker (2026-08-01): RM-B-FURNACE is unfinished below-grade space under
    # E3902.11, and the 2020 cycle removed the old sump-pump exception. 0.05 is a pump that
    # runs a minute or two an hour in wet weather — the peak matters here, not the average,
    # which is why it is on the shed tier despite the small energy number.
    Circuit(uid="CKT015AAAA", tag="CKT-SUMP", slot=7, panel_ref=_BACKUP_PANEL,
            breaker_amps=20, poles=1, backup_tier=BackupTier.SHED, gfci=True,
            load_va=1000, duty_cycle=0.05, description="Sump pump"),

    # --- general-use 120V ------------------------------------------------------------
    #
    # ``afci=True`` on every circuit below (2026-08-01, code.E3902_16_afci): each one reaches
    # a room on E3902.16's list and each is a 120V 15/20A branch circuit, which is the whole
    # of what the section covers. The 240V loads — range, dryer, the three heat pumps, the
    # kettle, the PV backfeed — are outside it and stay as they are.
    #
    # Where a circuit is both GFCI and AFCI, that is one dual-function breaker, not two
    # devices, so the two flags cost no panel spaces between them.
    Circuit(uid="CKT020AAAA", tag="CKT-KITCH-SA1", slot=30, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1500,
            description="Kitchen small-appliance 1 (counter west)"),
    Circuit(uid="CKT021AAAA", tag="CKT-KITCH-SA2", slot=32, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1500,
            description="Kitchen small-appliance 2 (counter east)"),
    # GFCI here as well: ED-M-LIVING-KDW1 is 2.7' from the kitchen sink (E3902.10), which is
    # the ordinary place a dishwasher receptacle lands and the ordinary reason its breaker
    # is dual-function.
    Circuit(uid="CKT022AAAA", tag="CKT-DISHWASHER", slot=34, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1200,
            description="Dishwasher + disposer (sink base)"),
    # E3902.9 puts the laundry-area receptacle on GFCI outright, no distance test.
    Circuit(uid="CKT023AAAA", tag="CKT-LAUNDRY", slot=36, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1500,
            description="Laundry receptacle (washer)"),
    Circuit(uid="CKT024AAAA", tag="CKT-LT-MAIN", slot=38, panel_ref=_PANEL, breaker_amps=15, poles=1,
            afci=True, description="General lighting — main storey, porch and garage"),
    Circuit(uid="CKT025AAAA", tag="CKT-LT-UPPER", slot=43, panel_ref=_PANEL, breaker_amps=15, poles=1,
            afci=True, description="General lighting — second + attic"),
    # The two storey receptacle circuits stay non-GFCI at the breaker on purpose: each reaches
    # a whole floor, and putting thirty outlets behind one 5 mA trip is not how any of this
    # gets built. The handful of outlets that *are* in an E3902 location — a bath, a mudroom
    # sink, a wet bar — are GFCI *devices* instead (plan/electrical.py, plan/mep.py).
    Circuit(uid="CKT026AAAA", tag="CKT-RC-MAIN", slot=44, panel_ref=_PANEL, breaker_amps=20, poles=1,
            afci=True, load_va=1500, description="General receptacles — main storey"),
    Circuit(uid="CKT027AAAA", tag="CKT-RC-SECOND", slot=45, panel_ref=_PANEL, breaker_amps=20, poles=1,
            afci=True, load_va=1500, description="General receptacles — second storey"),
    Circuit(uid="CKT028AAAA", tag="CKT-RC-BSMT", slot=46, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1500,
            description="General receptacles — basement + spa convenience"),
    Circuit(uid="CKT029AAAA", tag="CKT-RC-ATTIC", slot=47, panel_ref=_PANEL, breaker_amps=15, poles=1,
            afci=True, load_va=1000, description="General receptacles — attic rooms"),
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

"""Catlin's backup-microgrid circuits — every circuit homed to ED-B-BACKUP-PANEL.

Split out of plan/circuits.py (AGENTS.md, files under 500 lines), which splices this tuple
into ``CIRCUITS`` at the same place, so the schedule's order is unchanged. Same conventions
as that file's docstring. NOT ``# haus: editable``: circuits are schedule data.
"""

from __future__ import annotations

from typehaus import BackupTier, Circuit

# The backup subpanel on the EG4 12kPV's dedicated load output (plan/electrical.py) — a
# separate bus that stays energized when the grid does not, which is why tiered circuits
# live here rather than in ED-B-PANEL. Slot numbering: same convention, odd left/even right.
_BACKUP_PANEL = "ED-B-BACKUP-PANEL"

BACKUP_CIRCUITS = (
    # --- the backup microgrid (notes/backup_power.md) ---------------------------------
    # Every circuit below is homed to ED-B-BACKUP-PANEL, the 12-space subpanel on the
    # EG4 12kPV's dedicated load output. Two tiers: ALWAYS_ON rides the whole outage
    # (food, network, two basement cans + the kitchen tape, the alarms, the sump); SURPLUS
    # runs on battery only on solar surplus, through a relay (or a relay-driven contactor for
    # 2-pole/over-16A loads) that Home Assistant commands (notes/backup_power.md §5).
    #
    # ``duty_cycle`` on each is an ESTIMATE with its basis stated per circuit — the numbers
    # the bridge verdict is most sensitive to; revise against real metering.
    #
    # CKT-BACKUP-FEED (retired): its DIN gear is downstream of the inverter's load output like
    # everything else on this bus, so a circuit feeding it from the grid side was backwards.

    # -- ALWAYS_ON --
    # 800 VA is the *circuit allowance*, not the draw — the gap is why duty_cycle exists.
    # The fridge averages ~60W and the upright freezer column beside it ~45W: 105W of 800VA
    # = 0.13, still the largest always-on term and the one most worth metering.
    Circuit(uid="CKT016AAAA", tag="CKT-FRIDGE", slot=2, panel_ref=_BACKUP_PANEL,
            breaker_amps=20, poles=1, backup_tier=BackupTier.ALWAYS_ON, afci=True,
            conductor_awg="12", egc_awg="12",
            load_va=800, duty_cycle=0.13,
            description="Kitchen outlet 1: fridge + freezer"),
    # 300 VA is an outlet allowance; the real load is a router (~12W), an always-on HA server
    # (~28W), and a PoE switch feeding 3 APs, the doorbell and 2 cameras (E-603, through an
    # 88% supply) — ~133W of 300VA = 0.44. Per-device PoE draw is scheduled on E-603
    # (→ takeoff/data.py) since a PoE device names no circuit of its own.
    # On battery HA turns off the doorbell's, the cameras' (owner, 2026-10-30) and two of the
    # three APs' ports (2026-11-02): backup_shed_poe subtracts their E-603 watts / 0.88.
    # ED-M-KITCH-AP, the central main-floor AP, stays live. ED-B-UTIL-RC1's spare half on
    # this circuit is the outage charging point (plan/electrical.py).
    Circuit(uid="CKT017AAAA", tag="CKT-HA", slot=4, panel_ref=_BACKUP_PANEL,
            breaker_amps=15, poles=1, backup_tier=BackupTier.ALWAYS_ON, gfci=True,
            conductor_awg="14", egc_awg="14",
            load_va=300, duty_cycle=0.44,
            backup_shed_poe=("ED-M-DOORBELL", "ED-M-CAM-PORCH", "ED-BW-CAM-CANOPY",
                             "ED-M-PORCH-AP", "ED-A-STUDIO-AP"),
            description="Basement outlet 1: HA server + router + PoE switch; outage charging"),
    # Since 2026-11-02 only the furnace-room cans (by the panels, the ESS closet and the sump),
    # the ESS closet light, the kitchen under-cabinet tape and every alarm; the rest went to
    # CKT-LT-BSMT / CKT-LT-MAIN. The alarms stay on one unswitched branch (Kidde interconnect,
    # R314.4) that rides the outage (the ESS closet's two). load_va is None: the takeoff sums
    # the devices (95 VA, the alarms at 0). duty_cycle 0.40 is a blend, ~38 W of 95 VA:
    # - lights: cans 13 W + the tape's two 30 VA TRADFRIs (their rating, errs heavy; the tape
    #   draws 25 W, split over two drivers 2026-11-08) for ~5 h of 24 = 15.2 W; the closet
    #   light ~0.2 W;
    # - the two interconnect relays at their 13.2 VA rating, always energised;
    # - 12 alarms' standby, ~0.75 W each = 9.0 W. AN ESTIMATE: Kidde publishes only a 120 V /
    #   80 mA maximum. Meter it. (AL-G-HEAT left for the garage subpanel, 2026-11-14.)
    Circuit(uid="CKT018AAAA", tag="CKT-LT-BACKUP", slot=6, panel_ref=_BACKUP_PANEL,
            breaker_amps=15, poles=1, backup_tier=BackupTier.ALWAYS_ON, afci=True,
            conductor_awg="14", egc_awg="14",
            duty_cycle=0.40,
            description="Furnace-room + kitchen task light + interconnected alarms"),

    # The sump rides ALWAYS_ON since 2026-10-30: the long stormy night is exactly when it
    # must run. One pump, SM-B-RADON's Zoeller M53 (plan/mep_drainage.py; SM-B-SOUTH retired
    # 2026-11-02): 9.7 A running, so load_va = 9.7 x 120 = 1,164; x0.025 is a minute or two
    # an hour in wet weather (29 W). start_va 3,500 is the M98 (1/2 hp)'s published 29.2 A, so
    # an upsize stays covered (the M53's own is 25.9 A).
    # Published starts run ~3x running, not 6x.
    # GFCI at the DEVICE (2026-10-27): ED-B-SUMP-RC is an audible-alarm GFCI, so a trip is
    # heard (2026 NEC 210.8(A)(6) basements; (D)(6) accepts GFCI at the outlet); the breaker
    # is not GFCI.
    Circuit(uid="CKT015AAAA", tag="CKT-SUMP", slot=7, panel_ref=_BACKUP_PANEL,
            breaker_amps=20, poles=1, backup_tier=BackupTier.ALWAYS_ON,
            conductor_awg="12", egc_awg="12",
            load_va=1164, start_va=3500, duty_cycle=0.025,
            description="Sump pump (SM-B-RADON)"),

    # -- SURPLUS --
    # Never counted against battery autonomy; on battery it runs only on PV surplus with the
    # battery near full (notes/backup_power.md §5). duty_cycle feeds only the surplus-hours
    # figure.
    # HP3: one 9K head blowing into the open stair. load_va 1,850 is NEEP 393164's maximum
    # input (17 F). At that maximum a cold morning is ~38 kWh/day if it were the only heat,
    # which no battery carries; on battery it is surplus heat only. 0.4: a modulating head
    # holding the stair runs most of the time at a fraction of maximum. start_va = load_va:
    # an inverter compressor has no inrush. 2-pole, so a relay-driven contactor switches it
    # (takeoff/electrical.py::RELAY_CHANNEL_AMPS); HA's own command to the unit goes first.
    # Class A 2-pole GFCI for 210.8(F), as CKT-HP1 says; in the backup panel's own line.
    Circuit(uid="CKT010AAAA", tag="CKT-HP3", slot=1, panel_ref=_BACKUP_PANEL,
            breaker_amps=15, poles=2, gfci=True, backup_tier=BackupTier.SURPLUS, load_va=1850,
            conductor_awg="14", egc_awg="14",
            start_va=1850, duty_cycle=0.4,
            description="Heat pump 3 outdoor, Sapphire R32 VFD (EQ-M-HP3-OD; surplus tier)"),
    # The element-free 120 V plug-in HPWH (EQ-B-WH, Rheem PROPH80 T0 RH120-M, owner
    # 2026-10-31). Retagged from CKT-WH-240 (uid kept). load_va 1,440 = ENERGY STAR's 12.0 A
    # maximum x 120 V; 15 A is Rheem's minimum breaker. A Shelly Pro 4PM channel switches it.
    # duty 0.05: the 395 W average compressor draw for ~4.5 h a day (12 GPH recovery) =
    # 74 W. DEDICATED, not the unit's shared-circuit feature: on the backup panel there is
    # no second load to share with. Slot 9, 1-pole; 11 is spare.
    Circuit(uid="CKT007AAAA", tag="CKT-WH", slot=9, panel_ref=_BACKUP_PANEL,
            breaker_amps=15, poles=1, backup_tier=BackupTier.SURPLUS, load_va=1440,
            conductor_awg="14", egc_awg="14",
            duty_cycle=0.05,
            description="Water heater, Rheem ProTerra Plug-in 80 gal HPWH, 120 V, no element "
                        "(EQ-B-WH; surplus tier)"),

    # The backup panel's SPD (2026 NEC 215.18(B): fed from the inverter's load-output feeder,
    # it holds branch OCPDs; see CKT-SPD in plan/circuits.py). Slots 8/10 of the five spares.
    # Not a backup load, so no tier and no duty cycle.
    Circuit(tag="CKT-SPD-BACKUP", slot=8, panel_ref=_BACKUP_PANEL, breaker_amps=20, poles=2,
            load_va=0, spd=True,
            description="Type 2 surge protective device, backup panel (NEC 215.18)"),
)

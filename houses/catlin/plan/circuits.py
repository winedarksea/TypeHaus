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
  rule); ``code.NEC_705_12_interconnection`` grades that arithmetic.
  As of 2026-08-07 (CKT-DISPOSAL split): ED-B-PANEL carries 14 two-pole + 17 one-pole =
  45 of ED-T-PANEL's 54 spaces (nine spare); ED-B-BACKUP-PANEL carries 1 two-pole +
  5 one-pole = 7 of its 12. ``electrical.panel_spaces`` reconciles both against
  ``test_catlin_panel_spaces_fits_the_54_space_enclosure``. Count from the loaded plan,
  not by hand — a hand count has been wrong here before.
"""

from __future__ import annotations

from typehaus import BackupTier, Circuit, LoadManagement

_PANEL = "ED-B-PANEL"
# The backup subpanel on the EG4 12kPV's dedicated load output (plan/electrical.py) — a
# separate bus that stays energized when the grid does not, which is why tiered circuits
# live here rather than in ED-B-PANEL. Slot numbering: same convention, odd left/even right.
_BACKUP_PANEL = "ED-B-BACKUP-PANEL"

CIRCUITS = (
    # --- 240V dedicated loads (electrical_notes.md line 4) ---------------------------
    Circuit(uid="CKT001AAAA", tag="CKT-RANGE", slot=1, panel_ref=_PANEL, breaker_amps=50, poles=2,
            nema="14-50R", load_va=12000, description="Kitchen range"),
    # load_va is the *nameplate*, 830 W (LG DLHC5502V ventless heat-pump dryer, see
    # ED-M-LAUNDRY-DR1 in plan/electrical.py) — not the 5,000 VA the 14-30R receptacle
    # type carries. 220.82(B)(3) counts a dryer's nameplate rating; 220.54's 5,000 VA
    # minimum belongs to the standard method, not this one. The 30A branch stays as
    # deliberate provision for a future vented dryer.
    Circuit(uid="CKT002AAAA", tag="CKT-DRYER", slot=5, panel_ref=_PANEL, breaker_amps=30, poles=2,
            nema="14-30R", load_va=830, description="Dryer"),
    # The two EV circuits author load_va explicitly (same figures as their receptacle
    # types) because LOAD_MANAGEMENTS below reads the managed group's load off the
    # *circuits*, not the devices.
    Circuit(uid="CKT003AAAA", tag="CKT-EV-1450", slot=9, panel_ref=_PANEL, breaker_amps=50, poles=2,
            nema="14-50R", load_va=9600,
            description="EV charging, NEMA 14-50 (garage) — Emporia Vue managed"),
    Circuit(uid="CKT004AAAA", tag="CKT-EV-620", slot=13, panel_ref=_PANEL, breaker_amps=20, poles=2,
            nema="6-20R", load_va=3840,
            description="EV charging, NEMA 6-20 (garage) — Emporia Vue managed"),
    Circuit(uid="CKT005AAAA", tag="CKT-SPA", slot=17, panel_ref=_PANEL, breaker_amps=50, poles=2,
            gfci=True, load_va=11500, description="Hot tub (sunken garden)"),
    # 50A/2p GFCI per notes/sauna_shower_basement_detail.md (max 10.5 kW). Was 30A (only
    # ~5.5 kW continuous, half what the 513 cf sauna needs); EQ-B-SAUNA-HTR is 9 kW =
    # 37.5A, 46.9A at the 125% continuous factor, so 50A is the breaker.
    Circuit(uid="CKT006AAAA", tag="CKT-SAUNA", slot=21, panel_ref=_PANEL, breaker_amps=50, poles=2,
            gfci=True, load_va=9000, description="Sauna heater (EQ-B-SAUNA-HTR)"),
    # CKT-WH-240 moved to the backup subpanel 2026-08-15 — see the SHED tier below. Slot 25
    # is a spare on the main panel now.
    Circuit(uid="CKT008AAAA", tag="CKT-ERV", slot=2, panel_ref=_PANEL, breaker_amps=15, poles=2,
            load_va=200, description="ERV"),
    # The three Gree heat-pump systems (plan/electrical.py). A multi's indoor heads are fed
    # from the outdoor unit, so System 2's three heads add no circuits; System 1's ducted
    # air handler does get its own, because a ducted blower is fed at the unit.
    # 25A is unchanged and still correct: the FXU24HP230V1R32AO's MCA is 21 A and its maximum
    # overcurrent device is 25 A, the same pair of numbers the VIR24 carried. `load_va` is
    # MCA x 240 V (21 x 240 = 5,040), which is the conservative reading — MCA already carries
    # the 125% on the compressor, so this over-states the running load rather than under-stating
    # it in the 220.82 summary. Nothing in checks/ compares breaker_amps to load_va; this
    # arithmetic is held correct by hand, and saying so is part of keeping it that way.
    Circuit(uid="CKT009AAAA", tag="CKT-HP1", slot=6, panel_ref=_PANEL, breaker_amps=25, poles=2,
            load_va=5040, description="Heat pump 1 outdoor, FLEXX Ultra 24k (EQ-M-HP1-OD)"),
    # uids CKT036/037, not CKT031/032: those were already spent on the radiant-floor
    # circuits below (a duplicate found 2026-08-01). Devices name the tag, not the uid,
    # so renumbering this pair was the whole fix.
    # ** 15A -> 35A ON THE FLEXX ULTRA RETYPE, AND IT ABSORBED CKT-HP1-STRIP. ** The air
    # handler now carries the 4.6 kW factory heat kit (EQ-S-HP1-STRIP, FLEXA2LHTR05KWD) inside
    # its own cabinet, staged off its own 24 VAC board, so the kit is fed from the unit and not
    # from a circuit of its own. 4,600 W / 240 V = 19.2 A for the elements plus ~3 A of blower
    # = 22.2 A, x125% continuous = 27.7 A; the kit's published MCA is 29.9 A and its maximum
    # overcurrent device 35 A, which is the breaker. load_va 5,300 = 4,600 + ~700 of blower.
    Circuit(uid="CKT036AAAA", tag="CKT-HP1-AH", slot=50, panel_ref=_PANEL, breaker_amps=35, poles=2,
            load_va=5300,
            description="Heat pump 1 indoor, ducted air handler + 4.6 kW heat kit (EQ-S-HP1-AH, EQ-S-HP1-STRIP)"),
    Circuit(uid="CKT037AAAA", tag="CKT-HP2", slot=49, panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=6000,
            description="Heat pump 2 outdoor, Multi Ultra 3-port (EQ-M-HP2-OD; feeds its 3 heads)"),
    # System 3 (below, backup microgrid) is a true-VFD compressor that soft-starts, which
    # is what makes it carryable by the battery inverter at all.
    # GFCI at the breaker (2026-08-01, code.E3902_gfci_locations): ED-M-LIVING-KET1 sits
    # 3.2' from the kitchen sink. E3902.10 reaches it despite being 240V (it covers 125V
    # through 250V receptacles at 50A or less), and a 2-pole GFCI breaker is the only
    # place to protect a 6-20R.
    Circuit(uid="CKT011AAAA", tag="CKT-KETTLE", slot=14, panel_ref=_PANEL, breaker_amps=20, poles=2,
            nema="6-20R", gfci=True, load_va=3840,
            description="Kitchen kettle outlet (6-20R half)"),
    # The EG4 12kPV's grid port, at the opposite end of the bus from the main (120% rule
    # headroom is why the panel is 225A on a 200A service). Both PV and battery reach the
    # service through this one breaker — the array lands on the inverter's MPPTs
    # (EQ-B-ESS-INV) rather than backfeeding on its own.
    #
    # 50A: 8,000 W continuous at 240V = 33.3A, x125% = 41.7A, next standard size up
    # (datasheet 2026-08-02; the 80A grid-passthrough rating is pass-through capability,
    # not backfeed). The 705.12 ceiling on this bus is 225x1.2-200=70A, so 50A leaves 20A
    # for a future second source (V2H).
    #
    # source=True excludes it from the 220.82 load summary and includes it in the 705.12
    # busbar check.
    Circuit(uid="CKT012AAAA", tag="CKT-ESS-GRID", slot=40, panel_ref=_PANEL, breaker_amps=50,
            poles=2, source=True, load_va=0,
            description="EG4 12kPV grid port — PV + battery interconnection (EQ-B-ESS-INV)"),
    # CKT-HP1-STRIP IS DELETED, AND SLOT 18 IS A SPARE 2-POLE AGAIN. It existed from
    # 2026-08-15 to today to feed a generic 2 kW inline duct heater — a part that answered a
    # design-temperature shortfall the FLEXX Ultra retype removes, and that could never have
    # been interlocked with the EQ-T-GREE-DUC24 it was drawn against, because that machine had
    # no aux-heat terminal. The replacement is a FACTORY kit inside the air handler's cabinet,
    # fed and staged from the unit, so it rides CKT-HP1-AH above. The panel gets back the
    # spare 2-pole it lost on 2026-08-15.

    # --- electric space heating (2026-07-25) -----------------------------------------
    # Supplemental only — the three heat-pump systems do the heating work, these five
    # take the chill off specific surfaces. The three floor zones are 120V mat at
    # 12 W/ft2 over polygons in storeys/main.py and storeys/second.py, so each circuit's
    # VA is zone area x 12. 15A (not 20A) since these are 4-6A loads, each zone on its own
    # circuit (not shared, to avoid two rooms behind one 5 mA GFCI trip).
    #
    # GFCI on all three: NEC 424.44(G) requires it for bath/kitchen floor heating cable
    # (CKT-FH-BATH2/BATH1 outright); the dining zone (RM-M-LIVING) is outside the letter
    # of that rule but mat manufacturers require Class A protection regardless.
    #
    # Was CKT-FH-SAUNA until 2026-07-25 — RM-B-SAUNA has no floor heat (storeys/
    # basement.py), so that zone, circuit and stat are all gone.
    # 203 VA, not the 498 this carried until 2026-08-29, and NOT because the zone shrank —
    # it grew. 498 described a "41.5 ft2" zone that had not existed for some time (the
    # polygon was 6.7 ft2 when the drop-in bath pass found it), so the panel was carrying a
    # load two and a half times the mat's. FH-M-BATH2 is now 17.85 ft2 of authored zone
    # heated by one Schluter DHEHK12016 cable — 16.0 ft2, 120 V, 203 W, 1.7 A as purchased —
    # and this is that nameplate rather than `area x 12`, because heating cable is sold in
    # fixed lengths and cannot be cut. NEC 220.51 counts fixed electric space heating at
    # 100% of connected load, so VA = W here. ** The 295 VA this gives back is real
    # capacity: the service was at 7.9 A of margin. ** 15 A stays despite a 1.7 A load — the
    # thermostat is a 15 A device with an integral Class A GFCI and its own box, and a
    # dedicated home run is what Schluter recommends. NEC 424.44(G) is what makes the GFCI
    # mandatory; this mat is the ONLY heat in RM-M-BATH2 (no supply register), so the
    # circuit is not optional comfort.
    Circuit(uid="CKT031AAAA", tag="CKT-FH-BATH2", slot=29, panel_ref=_PANEL, breaker_amps=15, poles=1,
            gfci=True, load_va=203,
            description="Radiant floor heat — main bath, sole heat source "
                        "(FH-M-BATH2, 17.85 ft2, Schluter DHEHK12016)"),
    # AFCI too (2026-08-01): this mat is in RM-M-LIVING, and E3902.16 covers the 120V 15/20A
    # circuits *supplying outlets or devices* in a living room — a heating mat is a device.
    # The two bath mats are not: E3902.16's room list stops at the bathroom door.
    Circuit(uid="CKT032AAAA", tag="CKT-FH-DINING", slot=31, panel_ref=_PANEL, breaker_amps=15, poles=1,
            gfci=True, afci=True, load_va=696,
            description="Radiant floor heat — under the dining table (FH-M-DINING, 58.0 ft2)"),
    Circuit(uid="CKT033AAAA", tag="CKT-FH-BATH1", slot=33, panel_ref=_PANEL, breaker_amps=15, poles=1,
            # 338 VA, not 509: the zone lost its east lobe to RM-S-BATH1's 48" vanity on
            # 2026-08-30 and the wattage is now a purchased nameplate (Schluter DHEHK12027,
            # 26.7 ft2 / 338 W / 2.8 A) rather than a stale area times 12. The old 509 was
            # doubly wrong — the polygon never enclosed the 42.4 ft2 it was derived from.
            # NEC 220.51 counts fixed electric space heating at 100%, so this 171 VA comes
            # straight off the service demand.
            gfci=True, load_va=338,
            description="Radiant floor heat — NW bathroom, sole heat source "
                        "(FH-S-BATH1, 27.31 ft2, Schluter DHEHK12027)"),
    # 1,500W at 120V=12.5A, continuous: 12.5x1.25=15.6A fits a 20A breaker's 16A but not
    # a 15A one's 12A — why these two are 20A where the mats are 15A.
    #
    # Neither is GFCI: both are hard-wired equipment, and NEC 210.8(A) (garage rule
    # (A)(2) included) protects *receptacles*, not fixed wiring. Cord-and-plug versions
    # would need it — the reason both are modeled as Equipment on their own circuit.
    Circuit(uid="CKT034AAAA", tag="CKT-FIREPLACE", slot=35, panel_ref=_PANEL, breaker_amps=20, poles=1,
            afci=True, load_va=1500,
            description="Electric fireplace, living room SE corner (EQ-M-FIREPLACE)"),
    Circuit(uid="CKT035AAAA", tag="CKT-GAR-HEAT", slot=37, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=1500,
            description="Garage infrared heater lamp, 1.5 kW (EQ-G-HEATER)"),

    # --- the backup microgrid (notes/backup_power.md) ---------------------------------
    # Every circuit below is homed to ED-B-BACKUP-PANEL, the 12-space subpanel on the
    # EG4 12kPV's dedicated load output. Two tiers: ALWAYS_ON rides the whole outage
    # (food, network, enough light for two rooms); SHED drops via relay (or a
    # relay-driven contactor for 2-pole/over-16A loads) when the battery is low and the
    # sun isn't out.
    #
    # ``duty_cycle`` on each is an ESTIMATE (basis stated per circuit, authored
    # 2026-08-02) for the autonomy calc — the least certain numbers here and the ones the
    # 48-hour verdict is most sensitive to; revise against real metering, not vibes.
    #
    # CKT-BACKUP-FEED (retired same change): its DIN gear is now downstream of the
    # inverter's load output like everything else on this bus, so a circuit feeding the
    # backup enclosure from the *grid* side was backwards.

    # -- ALWAYS_ON --
    # 800 VA is the *circuit allowance*, not the draw — the gap is why duty_cycle exists.
    # Fridge averages ~60W, chest freezer ~45W: 105W of 800VA = 0.13, still the largest
    # always-on term and the one most worth metering.
    #
    # The ~15W PoE allowance this circuit used to carry moved to CKT-HA on 2026-08-02: the
    # access points are fed by the switch in ED-B-NET-PATCH, not a kitchen receptacle.
    Circuit(uid="CKT016AAAA", tag="CKT-FRIDGE", slot=2, panel_ref=_BACKUP_PANEL,
            breaker_amps=20, poles=1, backup_tier=BackupTier.ALWAYS_ON, afci=True,
            load_va=800, duty_cycle=0.13,
            description="Kitchen outlet 1: fridge + freezer"),
    # 300 VA is again an outlet allowance; the real load is a router (~12W), an always-on
    # HA server (~28W), and a PoE switch feeding 3 APs (~45W + conversion loss) — ~90W of
    # 300VA = 0.30. Not a duty cycle in the compressor sense (this load never cycles off,
    # the allowance is just generous). Per-device PoE draw is scheduled on E-603
    # (→ takeoff/data.py) since a PoE device names no circuit of its own.
    Circuit(uid="CKT017AAAA", tag="CKT-HA", slot=4, panel_ref=_BACKUP_PANEL,
            breaker_amps=15, poles=1, backup_tier=BackupTier.ALWAYS_ON, gfci=True,
            load_va=300, duty_cycle=0.30,
            description="Basement outlet 1: HA server + router + PoE switch"),
    # load_va is None: the luminaires carry real typed loads and the panel-schedule takeoff
    # sums the fixtures actually on the circuit (782 VA today, 558 before 2026-08-24). 0.15
    # is about five hours of the twenty-four with roughly two thirds of those fixtures lit —
    # an outage evening in the kitchen and the mechanical room while the rest of the house
    # stays dark.
    #
    # ** 224 VA of that is the kitchen's under-cabinet task light, and 200 of the 224 is a
    # RATING, not a load. ** ED-M-KITCH-LT-PSU is an ED-T-LT-PSU-200 driving 8'-11" of
    # 5 W/ft tape — 44.6 W, 55.7 W at the sizing factor — but per plan/lighting_types.py a
    # PSU's load_va is the supply's rating, so it sums here at 200. That is what took
    # battery-only always-on autonomy from 46.3 h to 41.3 h (test_backup_calc.py). The
    # overstatement is left in: a backup calculation is supposed to err heavy.
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
    # ONE circuit for the whole 80-gal ProTerra (EQ-B-WH), moved here from the main panel
    # 2026-08-15 — replacing the old two-tank split, which modelled one product's single
    # power whip as two appliances on two panels. `load_va=4500` is the nameplate (what
    # the breaker/schedule/220.82 estimate size against, since a resistance-element call
    # can happen whenever `LM-WH` below hasn't forced Heat-Pump-Only mode, which is what
    # actually governs the ~500W backup-event draw — see EQ-T-WATER-HEATER's note in
    # plan/mep.py). `duty_cycle=0.15`: a HPWH makes a household day of hot water in 3-4
    # hours of compressor run.
    # Slot 9 (not 5): a 2-pole breaker occupies slot and slot+2 in the same column
    # (electrical.panel_spaces); 5+7 collides with CKT-SUMP at slot 7, 9+11 is clear.
    Circuit(uid="CKT007AAAA", tag="CKT-WH-240", slot=9, panel_ref=_BACKUP_PANEL,
            breaker_amps=30, poles=2, backup_tier=BackupTier.SHED, load_va=4500,
            duty_cycle=0.15,
            description="Water heater, Rheem ProTerra 80gal hybrid HPWH (EQ-B-WH; "
                        "EcoNet-automated to Heat-Pump-Only on backup)"),
    # GFCI at the breaker (2026-08-01): RM-B-FURNACE is unfinished below-grade space under
    # E3902.11 (the 2020 cycle removed the old sump-pump exception). 0.05 is a pump
    # running a minute or two an hour in wet weather — the peak matters, not the average,
    # hence the shed tier despite the small energy number.
    Circuit(uid="CKT015AAAA", tag="CKT-SUMP", slot=7, panel_ref=_BACKUP_PANEL,
            breaker_amps=20, poles=1, backup_tier=BackupTier.SHED, gfci=True,
            load_va=1000, duty_cycle=0.05, description="Sump pump"),

    # --- general-use 120V ------------------------------------------------------------
    # ``afci=True`` on every circuit below (2026-08-01, code.E3902_16_afci): each reaches
    # a room on E3902.16's list as a 120V 15/20A branch circuit. The 240V loads (range,
    # dryer, heat pumps, kettle, PV backfeed) are outside the section's scope.
    # GFCI+AFCI on one circuit is a single dual-function breaker, costing one panel space.
    Circuit(uid="CKT020AAAA", tag="CKT-KITCH-SA1", slot=30, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1500,
            description="Kitchen small-appliance 1 (counter west)"),
    Circuit(uid="CKT021AAAA", tag="CKT-KITCH-SA2", slot=32, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1500,
            description="Kitchen small-appliance 2 (counter east)"),
    # GFCI here too: ED-M-LIVING-KDW1 is ~11" from the kitchen sink (E3902.10; was 2.7'
    # before the 2026-08-26 sink/dishwasher re-composition moved both into the same base).
    Circuit(uid="CKT022AAAA", tag="CKT-DISHWASHER", slot=34, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1200,
            description="Dishwasher (sink base)"),
    # The disposer came off CKT-DISHWASHER (2026-08-07): a shared 20A branch is legal, but
    # a 3/4 HP motor's locked-rotor inrush on top of a dishwasher's heater is a nuisance
    # trip waiting to happen. Its own circuit is the cheap fix while the wall is open.
    # GFCI for the same E3902.10 reason (ED-M-LIVING-KDS1 sits under the sink).
    #
    # The 120V branch feeds the motor; the wall control is a 24V loop through a
    # contactor — see APPL-M-DISP's `install_parts` in plan/placeables.py.
    Circuit(uid="CKT038AAAA", tag="CKT-DISPOSAL", slot=39, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1000,
            description="Food waste disposer (sink base)"),
    # E3902.9 puts the laundry-area receptacle on GFCI outright, no distance test.
    Circuit(uid="CKT023AAAA", tag="CKT-LAUNDRY", slot=36, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=1500,
            description="Laundry receptacle (washer)"),
    Circuit(uid="CKT024AAAA", tag="CKT-LT-MAIN", slot=38, panel_ref=_PANEL, breaker_amps=15, poles=1,
            afci=True, description="General lighting — main storey, porch and garage"),
    Circuit(uid="CKT025AAAA", tag="CKT-LT-UPPER", slot=43, panel_ref=_PANEL, breaker_amps=15, poles=1,
            afci=True, description="General lighting — second + attic"),
    # The two storey receptacle circuits stay non-GFCI at the breaker on purpose: each
    # reaches a whole floor, and thirty outlets behind one 5 mA trip is not buildable.
    # The handful in an E3902 location (bath, mudroom sink, wet bar) are GFCI *devices*
    # instead (plan/electrical.py, plan/mep.py).
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
    # ADDED 2026-08-29 with the attic guest bath. NEC 210.11(C)(3) / IRC E3901.6 wants a
    # dedicated 20A circuit for bathroom receptacles, and ** THE ENGINE HAS NO E3901 RULE **,
    # so this is judgement rather than a finding — taken anyway, because it is cheap in exactly
    # the two currencies that are scarce here. It costs one of nine spare 1-pole spaces (let
    # `electrical.panel_spaces` reconcile the count; do not hand-count), and it adds 0 VA to the
    # 220.82 summary because bathroom branch circuits are not in 220.82(B)(1)'s list — which
    # matters when `electrical.service_load` has 7.9A of margin against the 200A service.
    Circuit(tag="CKT-BATH-ATTIC", slot=41, panel_ref=_PANEL, breaker_amps=20, poles=1,
            gfci=True, afci=True, load_va=0,
            description="Attic guest bath receptacle"),
    # FX-M-BATH2-TUB's Bask heated surface (2026-08-29). Kohler's spec sheet lists the
    # REQUIRED service as a dedicated 120 V / 15 A circuit on a Class A GFCI, and that is
    # what this is — not a judgement call the way CKT-BATH-ATTIC above was. The bath is
    # cord-and-plug and factory-wired; the electrician owes it a GFCI-protected 15 A
    # grounded outlet behind the bath (ED-M-BATH2-TUB-RC), nothing more.
    #
    # ** 15 A IS THE MANUFACTURER'S NUMBER, NOT THE LOAD. ** The heater draws 1.1 A / 65 W —
    # less than a light bulb. `load_va` is that 65, because the 220.82 summary has to see
    # what the house actually draws, and sizing it at the breaker would invent 1,735 VA of
    # demand out of a required circuit rating. `electrical.service_load` has 7.9 A of margin
    # against the 200 A service and 65 VA is 0.3 A of it.
    #
    # GFCI AT THE BREAKER, not a GFCI device, and here that is not just the house convention
    # (plans/TODO.md): the outlet this circuit feeds is sealed inside SL-M-TUBDK's deck box
    # behind the bath. A GFCI receptacle there could not be tested or reset without pulling
    # a panel off the knee wall, which is the exact failure mode the breaker convention
    # exists to avoid. No AFCI: 210.12 exempts bathrooms.
    #
    # Slot 27 is one of the ten spare 1-pole spaces; count from the loaded plan
    # (`electrical.panel_spaces`), never by hand.
    Circuit(tag="CKT-BATH2-TUB", slot=27, panel_ref=_PANEL, breaker_amps=15, poles=1,
            gfci=True, load_va=65,
            description="Bask heated surface — RM-M-BATH2 drop-in bath (FX-M-BATH2-TUB)"),
)

# --- Load management (NEC 625.42 / 220.82) ---------------------------------------------
# Settles plans/TODO.md's "service load exceeds the service" with management rather than
# a service upgrade (re-affirmed 2026-08-15). Three groups; LM-WH joined 2026-08-15 when
# the two-tank water-heater model (plan/mep.py's note) was corrected to the single
# ProTerra it should always have been.
#
# What each lever is worth (from `haus schedule` / takeoff/electrical.py::
# service_load_summary, not authored here):
#
#   unmanaged                                                     246.4A
#   LM-EV: EV pair capped 5,760 -> 5,600 VA, credited at 100%     -32.7A  ->  213.7A
#   LM-WELLNESS: spa + sauna one at a time, 9,000 VA excess *40%  -15.0A  ->  198.7A
#   LM-WH: ProTerra forced Heat-Pump-Only near peak, 4,000 VA *40% -6.7A  ->  192.1A
#
# 7.9A of margin against the 200A service — still not slack; the answer past that is the
# 400A service this pass deliberately did not buy.
#
# Credit sizing: a managed group's connected excess is removed from the 220.82 term it was
# counted in. The EV pair (continuous) is credited at 100%; spa/sauna and the water heater
# are fixed appliances under (B)(3), reached through the 40% remainder factor, so their
# excess is worth 40 cents on the dollar. Crediting any at 100% would overstate the saving.
LOAD_MANAGEMENTS = (
    # Emporia Vue watches the whole-panel CTs and throttles the 14-50 EVSE. 5,600 VA =
    # 23.3A at 240V across both EV circuits — above the 6A/1.4kW floor an EVSE must never
    # be throttled below, so this is the guaranteed floor, not the rate it charges at.
    LoadManagement(uid="EMSEV0AAAA", tag="LM-EV",
                   managed_circuits=("CKT-EV-1450", "CKT-EV-620"),
                   max_simultaneous_va=5600, strategy="ems",
                   source="Emporia Vue dynamic load management (NEC 625.42 EMS)"),
    # Spa + sauna, interlocked so only one heats at a time: 11,500 VA is the spa (the
    # larger), so the group never draws more than the tub alone does. The two largest
    # fixed appliances in the house (11.5kVA + 9kVA vs a 12kVA range), 40' apart, so this
    # is contactor-based priority shedding on the Emporia controller, not a mechanical
    # interlock.
    LoadManagement(uid="EMSWL0AAAA", tag="LM-WELLNESS",
                   managed_circuits=("CKT-SPA", "CKT-SAUNA"),
                   max_simultaneous_va=11500, strategy="ems",
                   source="Emporia contactor-based priority shed, spa vs sauna (NEC 220.82 "
                          "connected-load management)"),
    # CKT-WH-240's own governor, not a panel-level EMS: ESPHome's `esphome-econet`
    # bridges the Rheem ProTerra's EcoNet API to Home Assistant, forcing Heat-Pump-Only
    # mode (compressor only) whenever the house is on battery or near the 200A peak. 500VA
    # is the compressor's steady-state ceiling in that mode (datasheet figure, see
    # EQ-T-WATER-HEATER's note in plan/mep.py); 4,500VA nameplate is what the breaker and
    # 220.82 base case assume otherwise. A single-circuit "group" is correct here — one
    # appliance governing its own two internal loads, not a simplification of two tanks.
    # System 1's aux heat against System 1's compressor — an OUTDOOR THERMOSTAT LOCKOUT, and
    # the reason the 4.6 kW kit does not need a service upgrade to sit in this panel.
    #
    # ** THE 220.82(C) ARITHMETIC IS WHY THIS EXISTS. ** The kit is 4,600 W. Dropped into the
    # heat-pump term at 100% alongside the outdoor unit it lands the house at 210.6 A against
    # a 200 A service — `electrical.service_load` says so, and it is right to. But the two are
    # NON-COINCIDENT loads (NEC 220.60): the FLEXX Ultra covers its zone unaided to its -22 F
    # lockout (EQ-T-GREE-FLEXX-ULTRA-24-OD makes 21,000 Btu/h at -15 F against a 15,164 Btu/h
    # block load), so the kit is backup for the hours BELOW that lockout — the hours the
    # compressor is off. An outdoor thermostat enabling the elements only under the
    # compressor's own cut-out is the control that makes that a fact rather than an intention.
    #
    # 5,740 VA is the larger of the two states, not the larger of the two circuits: the blower
    # runs in both. Compressor 5,040 + blower ~700 = 5,740; elements 4,600 + blower ~700 =
    # 5,300. So the group's connected 10,340 VA never all arrives, and 4,600 of it — exactly
    # the elements — is what the credit removes.
    #
    # WHAT IT COSTS, said plainly: the kit is locked out during defrost too, so the discharge
    # runs cool for the two to four minutes of a defrost cycle rather than being tempered by
    # resistance heat. That is the trade for not upsizing the service, and it is the standard
    # cold-climate arrangement, not a compromise invented here.
    LoadManagement(uid="EMSHP0AAAA", tag="LM-HP1-AUX",
                   managed_circuits=("CKT-HP1", "CKT-HP1-AH"),
                   max_simultaneous_va=5740, strategy="interlock",
                   source="Outdoor-thermostat lockout on the FLEXX Ultra's 24 VAC aux-heat "
                          "output: the 4.6 kW heat kit is enabled only below the -22 F "
                          "compressor lockout, so elements and compressor are non-coincident "
                          "loads (NEC 220.60)"),
    LoadManagement(uid="EMSWH0AAAA", tag="LM-WH",
                   managed_circuits=("CKT-WH-240",),
                   max_simultaneous_va=500, strategy="ems",
                   source="ESPHome esphome-econet -> Home Assistant automation, forcing "
                          "Rheem EcoNet Heat-Pump-Only mode on battery or near peak demand"),
)

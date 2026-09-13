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
  ED-B-PANEL is feeder 1 of the Class 320 service and ED-B-PANEL-2 is feeder 2
  (plan/mep_electrical.py). Slots 1/5/9/13 of ED-B-PANEL-2 carry CKT-SPA, CKT-SAUNA,
  CKT-EV-1450 and CKT-EV-620, which moved off ED-B-PANEL on 2026-09-12 — their old slots
  9, 13, 17 and 21 there are spares now. ED-B-BACKUP-PANEL carries 2 two-pole + 4 one-pole
  = 8 of its 12. Counts per panel come from `electrical.panel_spaces`, not from here.
  ``electrical.panel_spaces`` reconciles both against
  ``test_catlin_panel_spaces_fits_the_54_space_enclosure``. Count from the loaded plan,
  not by hand — a hand count has been wrong here before.
"""

from __future__ import annotations

from typehaus import BackupTier, Circuit

_PANEL = "ED-B-PANEL"
# The backup subpanel on the EG4 12kPV's dedicated load output (plan/electrical.py) — a
# separate bus that stays energized when the grid does not, which is why tiered circuits
# live here rather than in ED-B-PANEL. Slot numbering: same convention, odd left/even right.
_BACKUP_PANEL = "ED-B-BACKUP-PANEL"
# Feeder 2 of the Class 320 service (plan/mep_electrical.py, ED-T-PANEL-2): a second 200 A
# main out of the meter-main, carrying the wellness and EV loads. Same slot convention.
_PANEL_2 = "ED-B-PANEL-2"

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
    # types), so the schedule reads the same number the conductors are sized for whether or
    # not a device happens to be placed on the circuit.
    Circuit(uid="CKT003AAAA", tag="CKT-EV-1450", slot=9, panel_ref=_PANEL_2, breaker_amps=50, poles=2,
            nema="14-50R", load_va=9600,
            description="EV charging, NEMA 14-50 (garage)"),
    Circuit(uid="CKT004AAAA", tag="CKT-EV-620", slot=13, panel_ref=_PANEL_2, breaker_amps=20, poles=2,
            nema="6-20R", load_va=3840,
            description="EV charging, NEMA 6-20 (garage)"),
    Circuit(uid="CKT005AAAA", tag="CKT-SPA", slot=1, panel_ref=_PANEL_2, breaker_amps=50, poles=2,
            gfci=True, load_va=11500, description="Hot tub (sunken garden)"),
    # 50A/2p GFCI per notes/sauna_shower_basement_detail.md (max 10.5 kW). EQ-B-SAUNA-HTR
    # is 9 kW = 37.5A, 46.9A at the 125% continuous factor, so 50A is the breaker.
    # ** 50 A / 9000 VA -> 60 A / 10500 VA, 2026-09-06, and the driver is the heater, not
    # the circuit. ** plan/electrical.py's EQ-T-SAUNA-HEATER note carries the finding: 9 kW
    # covers 283-494 cf on every manufacturer's own table and RM-B-SAUNA is 555. NEC
    # 424.3(B) makes fixed electric space heating a continuous load at 125%, so
    # 10500 / 240 = 43.75 A x 1.25 = ** 54.7 A **, which 50 A will not carry. 60 A does.
    #
    # ** PULL #6 THHN IN CONDUIT, AND DO NOT BELIEVE THE "#8 AWG" SEVERAL RETAILERS AND AT
    # LEAST ONE MANUFACTURER'S OWN SHEET PRINT FOR THIS CIRCUIT. ** NEC 334.80 forces NM-B
    # to the 60 C ampacity column, which makes #8 NM-B a 40 A conductor — below even the
    # 46.9 A the ORIGINAL 9 kW needed. #6 in conduit also keeps both breaker ratings open,
    # so a future change costs a breaker rather than a re-pull.
    #
    # ** GFCI IS OFF, DELIBERATELY, AND THE MANUAL GOES TO PLAN REVIEW. ** The NEC does not
    # require it here: 210.8(A) governs receptacles, 210.8(D)'s appliance list does not
    # include sauna heaters, and Article 680 is pools and spas. The manufacturers advise
    # against it in writing — HUUM's manual says verbatim "It is recommended to connect the
    # unit to the mains without an earth-leakage circuit breaker" — because moisture absorbed
    # into the magnesium-oxide fill of the sheathed elements causes nuisance trips. The fix
    # is a 2-4 hour DRY BURN-IN before final inspection. If the AHJ insists anyway, take a
    # 30 mA GFPE, which catches a real fault without the nuisance trips. ** The sauna LIGHTS
    # are a different question and DO need GFCI ** under 210.8(A)(5), which is why lights and
    # heater are on separate circuits.
    Circuit(uid="CKT006AAAA", tag="CKT-SAUNA", slot=5, panel_ref=_PANEL_2, breaker_amps=60, poles=2,
            gfci=False, load_va=10500, description="Sauna heater (EQ-B-SAUNA-HTR), 10.5 kW"),
    # CKT-WH-240 moved to the backup subpanel — see the SHED tier below. Slot 25 is a
    # spare on the main panel now.
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
    # circuits below. Devices name the tag, not the uid, so renumbering this pair was
    # the whole fix.
    # ** 15A -> 35A ON THE FLEXX ULTRA RETYPE, AND IT ABSORBED CKT-HP1-STRIP. ** The air
    # handler now carries the 4.6 kW factory heat kit (EQ-S-HP1-STRIP, FLEXA2LHTR05KWD) inside
    # its own cabinet, staged off its own 24 VAC board, so the kit is fed from the unit and not
    # from a circuit of its own. 4,600 W / 240 V = 19.2 A for the elements plus ~3 A of blower
    # = 22.2 A, x125% continuous = 27.7 A; the kit's published MCA is 29.9 A and its maximum
    # overcurrent device 35 A, which is the breaker. load_va 5,300 = 4,600 + ~700 of blower.
    #
    # ** THE OUTDOOR-THERMOSTAT AUX-HEAT LOCKOUT IS A CONTROL SETTING, NOT A CREDIT. ** The
    # FLEXX Ultra's 24 VAC aux output is set to enable the elements only BELOW the -22 F
    # compressor lockout (the outdoor unit makes 21,000 Btu/h at -15 F against a 15,164
    # Btu/h block load, so the kit is backup for the hours the compressor is off), and
    # defrost therefore runs unheated — two to four minutes of cool discharge, the standard
    # cold-climate arrangement. It used to be authored as LM-HP1-AUX and credited 4,600 VA
    # under 220.82(C)/220.60, which is what kept the house inside a 200 A service. With the
    # Class 320 service (2026-09-12) it buys nothing and is just how the unit is set up.
    Circuit(uid="CKT036AAAA", tag="CKT-HP1-AH", slot=50, panel_ref=_PANEL, breaker_amps=35, poles=2,
            load_va=5300,
            description="Heat pump 1 indoor, ducted air handler + 4.6 kW heat kit (EQ-S-HP1-AH, EQ-S-HP1-STRIP)"),
    Circuit(uid="CKT037AAAA", tag="CKT-HP2", slot=49, panel_ref=_PANEL, breaker_amps=30, poles=2,
            load_va=6000,
            description="Heat pump 2 outdoor, Multi Ultra 3-port (EQ-M-HP2-OD; feeds its 3 heads)"),
    # System 3 (below, backup microgrid) is a true-VFD compressor that soft-starts, which
    # is what makes it carryable by the battery inverter at all.
    # GFCI at the breaker (code.E3902_gfci_locations): ED-M-LIVING-KET1 sits
    # 3.2' from the kitchen sink. E3902.10 reaches it despite being 240V (it covers 125V
    # through 250V receptacles at 50A or less), and a 2-pole GFCI breaker is the only
    # place to protect a 6-20R.
    Circuit(uid="CKT011AAAA", tag="CKT-KETTLE", slot=14, panel_ref=_PANEL, breaker_amps=20, poles=2,
            nema="6-20R", gfci=True, load_va=3840,
            description="Kitchen kettle outlet (6-20R half)"),
    # The EG4 12kPV's grid port, at the opposite end of the bus from the main (120% rule
    # headroom is why the panel is a 225A bus on a 200A main). Both PV and battery reach the
    # service through this one breaker — the array lands on the inverter's MPPTs
    # (EQ-B-ESS-INV) rather than backfeeding on its own.
    #
    # 50A: 8,000 W continuous at 240V = 33.3A, x125% = 41.7A, next standard size up
    # (the 80A grid-passthrough rating is pass-through capability, not backfeed). The
    # 705.12 ceiling on this bus is 225x1.2-200=70A, so 50A leaves 20A
    # for a future second source (V2H).
    #
    # source=True excludes it from the 220.82 load summary and includes it in the 705.12
    # busbar check.
    Circuit(uid="CKT012AAAA", tag="CKT-ESS-GRID", slot=40, panel_ref=_PANEL, breaker_amps=50,
            poles=2, source=True, load_va=0,
            description="EG4 12kPV grid port — PV + battery interconnection (EQ-B-ESS-INV)"),
    # CKT-HP1-STRIP IS DELETED, AND SLOT 18 IS A SPARE 2-POLE AGAIN: the aux heat is now a
    # FACTORY kit inside the air handler's cabinet, fed and staged from the unit, so it
    # rides CKT-HP1-AH above rather than a circuit of its own.

    # --- service surge protection ------------------------------------------------------
    # ** NEC 2023 230.67 requires an SPD on the service of a dwelling unit ** — Type 1 or
    # Type 2, and 230.67(C) says it is installed at the service equipment or immediately
    # adjacent. This is the panel-mounted Type 2 answer: a 2-pole plug-on breaker in
    # ED-B-PANEL, not a nipple-coupled enclosure beside it, because the west wall at x=10"
    # is already full — ED-B-BACKUP-PANEL at y=27', ED-B-PANEL at 29', ED-B-NET-PATCH at
    # 31' and the ERV duct crossing at 31'-4" leave no clear bay. A plug-on breaker also
    # gives the shortest possible lead length, which is what actually decides let-through
    # voltage; every inch of conductor adds to the clamped voltage the house sees.
    #
    # Slot 10 (with 12) was one of the nine spares. It is high in the right-hand column,
    # near the main, which is the short-lead position.
    #
    # `source=False`, `load_va=0`: an SPD is neither a load nor a power source. It draws
    # only its indicator LED, so 220.82 counts nothing and the 705.12 busbar check must
    # NOT see it as a backfeed the way CKT-ESS-GRID is seen.
    #
    # NOT on the backup panel: 230.67 is about the SERVICE, so the device belongs on the
    # service bus. The EG4's load output is protected by the inverter's own surge stage.
    # A second SPD at ED-B-BACKUP-PANEL is a defensible upgrade and is deliberately not
    # authored here — one device, on the bus the code names.
    #
    # ** NOTHING GRADES THIS. ** No check encodes 230.67 (grep `NEC 230` in checks/ — no
    # hits), so this comment and the circuit row are the only record that the requirement
    # was met. If the SPD is ever value-engineered out, it comes out of a code article,
    # not out of a nice-to-have.
    Circuit(tag="CKT-SPD", slot=10, panel_ref=_PANEL, breaker_amps=20, poles=2,
            load_va=0,
            description="Type 2 surge protective device, service panel (NEC 230.67)"),

    # --- electric space heating --------------------------------------------------------
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
    # RM-B-SAUNA has no floor heat (storeys/basement.py), so that zone, circuit and stat
    # are all gone.
    # FH-M-BATH2 is 17.85 ft2 of authored zone heated by one Schluter DHEHK12016 cable —
    # 16.0 ft2, 120 V, 203 W, 1.7 A as purchased — and this is that nameplate rather than
    # `area x 12`, because heating cable is sold in fixed lengths and cannot be cut. NEC
    # 220.51 counts fixed electric space heating at 100% of connected load, so VA = W
    # here. 15 A stays despite a 1.7 A load — the
    # thermostat is a 15 A device with an integral Class A GFCI and its own box, and a
    # dedicated home run is what Schluter recommends. NEC 424.44(G) is what makes the GFCI
    # mandatory; this mat is the ONLY heat in RM-M-BATH2 (no supply register), so the
    # circuit is not optional comfort.
    Circuit(uid="CKT031AAAA", tag="CKT-FH-BATH2", slot=29, panel_ref=_PANEL, breaker_amps=15, poles=1,
            gfci=True, load_va=203,
            description="Radiant floor heat — main bath, sole heat source "
                        "(FH-M-BATH2, 17.85 ft2, Schluter DHEHK12016)"),
    # AFCI too: this mat is in RM-M-LIVING, and E3902.16 covers the 120V 15/20A
    # circuits *supplying outlets or devices* in a living room — a heating mat is a device.
    # The two bath mats are not: E3902.16's room list stops at the bathroom door.
    Circuit(uid="CKT032AAAA", tag="CKT-FH-DINING", slot=31, panel_ref=_PANEL, breaker_amps=15, poles=1,
            gfci=True, afci=True, load_va=696,
            description="Radiant floor heat — under the dining table (FH-M-DINING, 58.0 ft2)"),
    Circuit(uid="CKT033AAAA", tag="CKT-FH-BATH1", slot=33, panel_ref=_PANEL, breaker_amps=15, poles=1,
            # 338 VA: the wattage is a purchased nameplate (Schluter DHEHK12027, 26.7 ft2 /
            # 338 W / 2.8 A) rather than a stale area times 12. NEC 220.51 counts fixed
            # electric space heating at 100%, so this comes straight off the service demand.
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
            # ** IT LEFT THE SE CORNER 2026-09-06. ** EQ-M-FIREPLACE is now in the brick
            # surround in the pier between WIN-M-LIV-E1 and WIN-M-LIV-E2 (W-M-FIRE-*,
            # plan/storeys/main.py). The unit is a real product now — an Amantii
            # BI-30-XTRASLIM — and it is still 120 V / 1,500 W / 12.5 A, so everything above
            # holds unchanged: same breaker, same slot, same pole count, same load. A 240 V
            # unit would have moved all four (and the ServicePort, and the panel balance);
            # plan/electrical.py's EQ-T-FIREPLACE-EL note says why none exists at this size.
            description="Electric fireplace, living room east wall, in the brick "
                        "surround between WIN-M-LIV-E1 and WIN-M-LIV-E2 (EQ-M-FIREPLACE)"),
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
    # can happen at any time). ** THE ESPHome/EcoNet Heat-Pump-Only AUTOMATION IS A BACKUP
    # RESERVE MEASURE, NOT A LOAD-MANAGEMENT CREDIT. ** It belongs with `backup_tier=SHED`:
    # on battery it holds the tank at the compressor's ~500 W instead of 4,500 W, which is
    # what governs the backup-event draw (see EQ-T-WATER-HEATER's note in plan/mep_hvac.py).
    # It buys nothing in the 220.82 calculation and never did — an unlisted software
    # governor is not a PCS (2026 NEC 130.2). `duty_cycle=0.15`: a HPWH makes a household
    # day of hot water in 3-4 hours of compressor run.
    # Slot 9 (not 5): a 2-pole breaker occupies slot and slot+2 in the same column
    # (electrical.panel_spaces); 5+7 collides with CKT-SUMP at slot 7, 9+11 is clear.
    # `backup_va=500`: the compressor's steady-state ceiling in Heat-Pump-Only mode
    # (datasheet figure). It is what the ESPHome/EcoNet automation holds the tank to while
    # the house is on battery, and the number the inverter is sized against — the SHED
    # tier's peak is over 8 kW without it. Authored on the circuit, not as a
    # `LoadManagement`: it is a backup reserve, not a 220.82 credit.
    Circuit(uid="CKT007AAAA", tag="CKT-WH-240", slot=9, panel_ref=_BACKUP_PANEL,
            breaker_amps=30, poles=2, backup_tier=BackupTier.SHED, load_va=4500,
            backup_va=500, duty_cycle=0.15,
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
    # The garage's exterior linear runs landed here on 2026-09-11: LR-G-EAVE-W/-E (24'-0"
    # each, in the two eave soffits) and LR-G-GABLE-N (16'-0" over D-G-OVERHEAD), 64 LF of
    # ED-T-LT-LINEAR-EXT at 2.5 W/ft. They are on this circuit rather than CKT-RC-GARAGE for
    # the same reason ED-G-LT1/2/3 are: a tool tripping a garage GFCI must not take the
    # lights with it. The panel schedule derives their VA from the resolved run length
    # (takeoff/electrical._connected_va), so no `load_va` is authored here — an authored
    # value preempts the derivation and would freeze the thirty-eight fixtures against a
    # number nobody re-adds when a can moves.
    Circuit(uid="CKT024AAAA", tag="CKT-LT-MAIN", slot=38, panel_ref=_PANEL, breaker_amps=15, poles=1,
            afci=True,
            description="General lighting — main storey, porch and garage (incl. the garage's exterior linear runs)"),
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
    # dedicated 20A circuit for bathroom receptacles, and ** THE ENGINE HAS NO E3901
    # BRANCH-CIRCUIT RULE ** (it does now grade E3901.6's other half, the receptacle a basin
    # must have, as code.E3901_6_bathroom_receptacle — 210.11(C)(3) is the part nothing
    # encodes), so this is judgement rather than a finding — taken anyway, because it is cheap in exactly
    # the two currencies that are scarce here. It costs one of nine spare 1-pole spaces (let
    # `electrical.panel_spaces` reconcile the count; do not hand-count), and it adds 0 VA to the
    # 220.82 summary because bathroom branch circuits are not in 220.82(B)(1)'s list — which
    # mattered when the margin was 7.9 A against a 200 A service, and is simply free now
    # that the Class 320 service leaves 52.6 A (267.4 A of 320 A).
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
    # demand out of a required circuit rating. `electrical.service_load` has 52.6 A of margin
    # against the 320 A service and 65 VA is 0.3 A of it.
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
    # ------------------------------------------------------------------------------------
    # THE TWO WASHLET CIRCUITS (2026-09-06)
    # ------------------------------------------------------------------------------------
    # Both main-floor bowls were bought WASHLET+-ready — FX-TOTO-SP-WH on a DuoFit carrier
    # (the frame was chosen over a Geberit *for* this), FX-TOTO-CARLYLE-II's AT40 suffix IS
    # the readiness — and `[allowances] plumbing-bidet-seats` has been buying two TOTO
    # WASHLET S5 seats since the fixtures were selected. ** THE ELECTRICAL FOR THEM EXISTED
    # NOWHERE. ** Each bath had exactly one receptacle, a 44" vanity outlet on CKT-RC-MAIN,
    # and two 1.4 kW seats on a general storey circuit is ~23 A on a 20 A breaker before
    # anything else is plugged in. Nothing reported it: the engine has no E3901 branch-circuit
    # rule (see CKT-BATH-ATTIC above) and nothing ties a Product to a device.
    #
    # ** TWO CIRCUITS, NOT ONE, AND DO NOT GANG THEM LATER. ** An instantaneous seat draws
    # 1.2-1.4 kW the whole time it is heating and both baths are used at the same hour of the
    # morning; one 20 A circuit carrying both is a nuisance-trip design, and it is what
    # notes/interior_selections.md has asked against since the seats were specified.
    # Slots 25 and 28 are two of the eleven spare 1-pole spaces (count from the loaded plan
    # via `electrical.panel_spaces`, never by hand) and are deliberately in different panel
    # ROWS so an electrician can land them on opposite bus legs — the engine models no legs,
    # so that is an instruction to the field, not a modelled fact.
    #
    # ** GFCI AT THE DEVICE, NOT THE BREAKER. ** The house convention for an outlet a person
    # actually uses (ED-M-BATH2-RC1's note): a washlet's own leakage trips a Class A GFCI
    # from time to time, and a reset in the basement for a toilet seat is the failure mode
    # the convention exists to avoid. Contrast CKT-BATH2-TUB, which IS breaker-protected
    # because its outlet is sealed inside the tub deck. No AFCI: 210.12 exempts bathrooms.
    #
    # ** load_va IS 0, AND THE NAMEPLATE IS RECORDED HERE SO THE ZERO IS A DECISION AND NOT
    # AN OMISSION. ** Each seat is ~1,400 VA at the top of the researched 1.2-1.4 kW band,
    # but only while the instantaneous heater is running — seconds per use, a few times a
    # day, and never a load the house sits at. Two readings of 220.82 are available and this
    # is the one taken (owner's call, 2026-09-06): a bathroom RECEPTACLE circuit is not in
    # 220.82(B)(1)'s list and 220.82(B)(1)'s own 3 VA/ft2 term is deemed to cover general
    # receptacle outlets already, which is exactly the reasoning CKT-BATH-ATTIC above is
    # authored on. The other reading is 220.82(B)(3)'s "located on a specific circuit" limb,
    # which would take the nameplate — the same limb that put 65 VA on CKT-BATH2-TUB, though
    # that one is a fixed appliance rather than something plugged into a bathroom outlet.
    #
    # ** WHAT THE OTHER READING COSTS, MEASURED RATHER THAN ESTIMATED: ** at load_va=1400 on
    # both, `electrical.service_load` goes 267.4 A -> 272.1 A against the 320 A service —
    # 2 x 1,400 VA through 220.82(B)'s 40% remainder factor, 4.7 A of a 52.6 A margin.
    # It still PASSES. So this zero is not load-hiding to make a check go green; it is a
    # coincidence judgement, and the revert is two numbers. ** Revisit it if anything with a
    # real duty cycle ever joins these circuits ** — they are 20 A and they feed one outlet
    # each today, and that is the assumption the zero rests on.
    Circuit(tag="CKT-WASHLET-BATH1", slot=25, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=0,
            description="Bidet seat — RM-M-BATH1 water closet (FX-M-BATH1-WC, WASHLET S5)"),
    Circuit(tag="CKT-WASHLET-BATH2", slot=28, panel_ref=_PANEL, breaker_amps=20, poles=1,
            load_va=0,
            description="Bidet seat — RM-M-BATH2 water closet (FX-M-BATH2-WC, WASHLET S5)"),
)

# --- Load management: NONE, and deliberately (2026-09-12) ------------------------------
# This house authors no ``LoadManagement`` at all, and ``plan/manifest.py`` passes none.
#
# Until 2026-09-12 four groups (LM-EV, LM-WELLNESS, LM-WH, LM-HP1-AUX) credited 18,240 VA
# and were the only reason the 220.82 demand fit a 200 A service. Three of them rested on
# software — Emporia PowerSmart throttling, an ESPHome/EcoNet automation, an Emporia
# contactor shed — and under the 2026 NEC (MN adopted it for permits filed on or after
# 2026-08-17) a controller that limits load in a service calculation has to be a POWER
# CONTROL SYSTEM: 130.2 requires the listing, 120.7 sets the setpoint at <= 80% of the
# monitored OCPD, and 625.42(A) points EV supply equipment at the same Part II. Emporia's
# gear carries UL 61010-2-030 / 2808 / 2594 / 2231 / 991 and no UL 3141, so none of those
# three credits was ever earnable. (The fourth, LM-HP1-AUX, was earnable — 220.82(C)(2)/(4)
# credits an interlock between a compressor and its supplemental heat directly — but with
# no service constraint left to satisfy it buys nothing.)
#
# The answer was the service, not a $2-3k listed PCS: a Class 320 HDLB meter-main with two
# 200 A mains. ** 267.4 A of unmanaged 220.82 demand against 320 A **, no software in the
# calculation at all. See DESIGN-LOG.md "Electrical service" for the derivation, the three
# options priced, and why there is no such thing as a 225 A service.
#
# Re-adding a group is a real decision, not a tidy-up: the engine now refuses a credit
# whose basis does not hold (takeoff/electrical.py::_credit_refusal), so a ``pcs`` without
# a ``listing`` FAILs `electrical.service_load` rather than quietly saving amps.

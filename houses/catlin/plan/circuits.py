"""Catlin panel schedule — every branch circuit in ED-B-PANEL.

NOT ``# haus: editable``: circuits are schedule data, not geometry — nothing here can be
dragged. Devices/equipment reference these tags via their ``circuit=`` field (the editable
files), and ``electrical.circuit_refs`` reconciles the two directions.

Conventions:
- ``poles=2`` is a 240V circuit; ``poles=1`` is 120V.
- ``gfci=True`` is protection at the *breaker* (plans/TODO.md: GFCI at breaker, not outlet).
- ``backup_tier`` places a circuit on the backup microgrid (notes/backup_power.md).
  ALWAYS_ON rides the EG4's load output through the whole outage; SURPLUS sits behind a
  Shelly Pro 4PM relay or a relay-driven contactor in ED-B-BACKUP-ENCL and runs on battery
  only on solar surplus. Every tiered circuit is homed to
  ``ED-B-BACKUP-PANEL``, the 12-space subpanel on the inverter's dedicated load output —
  which is what makes the tier physical rather than a label.
- ``duty_cycle`` is the authored average-draw fraction the autonomy calc multiplies the
  connected VA by (→ takeoff/backup_calc.py). Estimates, each with its basis in a comment;
  a tiered circuit without one is reported as an unknown contributor, never as zero.
- ``source=True`` marks a power-source interconnection — excluded from the 120.82 load
  summary and counted by the 705.12 busbar check instead.
- ``load_va`` is authored where the devices carry no typed load (equipment, lighting
  allowances); circuits whose receptacle types carry ``load_va`` leave it None and the
  panel-schedule takeoff sums the device types.
- ``conductor_awg``/``egc_awg`` (copper, 60 °C column unless ``termination_temp_c``) are the
  engine's proposal pending electrician review (2026-11-14), sized to the breaker by 240.4(D).
- ``slot`` is the physical breaker position: odd numbers run down the left column, even
  down the right, and a 2-pole breaker takes ``slot`` and ``slot + 2`` (same column).
  The ESS grid port backfeeds at the bottom of the bus (51/53, the last row of the top-fed
  can), opposite the main (120% rule); ``code.NEC_705_12_interconnection`` grades it.
  ED-B-PANEL is feeder 1 of the Class 320 service and ED-B-PANEL-2 is feeder 2
  (plan/mep_electrical.py). Slots 1/5/9/17 of ED-B-PANEL-2 carry CKT-SPA, CKT-SAUNA,
  CKT-GAR-FEEDER (the garage subpanel ED-G-PANEL, plan/circuits_garage.py) and
  CKT-WORKSHOP-240, respectively, and slot 2 its SPD. ED-B-BACKUP-PANEL carries 2 two-pole
  + 5 one-pole = 9 of its 12. Counts per panel come from `electrical.panel_spaces`, not from here.
  ``electrical.panel_spaces`` reconciles both against
  ``test_catlin_panel_spaces_fits_the_54_space_enclosure``. Count from the loaded plan,
  not by hand — a hand count has been wrong here before.
"""

from __future__ import annotations

from plan.circuits_240v import DEDICATED_240V_CIRCUITS
from plan.circuits_backup import BACKUP_CIRCUITS
from plan.circuits_garage import GARAGE_CIRCUITS
from typehaus import Circuit

_PANEL = "ED-B-PANEL"
# Feeder 2 of the Class 320 service (plan/mep_electrical.py, ED-T-PANEL-2): a second 200 A
# main out of the meter-main, carrying the wellness and EV loads. Same slot convention.
_PANEL_2 = "ED-B-PANEL-2"

CIRCUITS = (
    *DEDICATED_240V_CIRCUITS,
    # --- surge protection: one SPD per feeder panel ----------------------------------------
    # ** 2026 NEC 230.67 requires an SPD for a dwelling's service, and the outdoor CL320
    # meter-main is the service disconnect (230.70(A)(1); 230.85 is gone), so every panel
    # here is a FEEDER panel. ** Where the service supplies only feeders, the 230.67(B)
    # Exception puts an SPD on the load side of EACH feeder, and 215.18(B) wants one in or
    # next to each feeder-supplied panel holding branch OCPDs (NFPA 70 A2025 CMP-10 second
    # draft; MN DLI NEC FAQ rev. 2026-10-05 #8). Three SPDs, then: ED-B-PANEL (this one),
    # ED-B-PANEL-2 and ED-B-BACKUP-PANEL (owner, 2026-11-07; the last in circuits_backup.py).
    # Each is a 2-pole plug-on Type 2 breaker, not a nipple-coupled enclosure: the west wall
    # at x=10" has no clear bay, and a plug-on gives the shortest lead, which is what decides
    # let-through voltage. Slot 10 (with 12) is high in the right column, by the main.
    # `source=False`, `load_va=0`: neither a load nor a source, so 120.82 counts nothing and
    # the 705.12 busbar check must NOT see a backfeed.
    #
    # `spd=True` is what `code.NEC_215_18_spd` and the price row read. If an SPD is ever
    # value-engineered out, it comes out of a code article, not out of a nice-to-have.
    Circuit(tag="CKT-SPD", slot=10, panel_ref=_PANEL, breaker_amps=20, poles=2,
            load_va=0, spd=True, spd_type_ref="ED-T-SPD-QO2175SB",
            description="Type 2 surge protective device, feeder panel 1 "
                        "(NEC 230.67(B) Ex., 215.18)"),
    # Feeder 2's SPD: slot 2 is the top of ED-B-PANEL-2's empty right column, beside the
    # main, for the short lead. A Homeline plug-on, as CKT-SPD is a QO one.
    Circuit(tag="CKT-SPD-2", slot=2, panel_ref=_PANEL_2, breaker_amps=20, poles=2,
            load_va=0, spd=True, spd_type_ref="ED-T-SPD-HOM2175SB",
            description="Type 2 surge protective device, feeder panel 2 "
                        "(NEC 230.67(B) Ex., 215.18)"),

    # --- electric space heating --------------------------------------------------------
    # Supplemental only — the three heat-pump systems do the heating work, these five
    # take the chill off specific surfaces. The three floor zones are 120V mat at
    # 12 W/ft2 over polygons in storeys/main.py and storeys/second.py, so each circuit's
    # VA is zone area x 12. 15A (not 20A) since these are 4-6A loads, each zone on its own
    # circuit (not shared, to avoid two rooms behind one 5 mA GFCI trip).
    #
    # GFCI on all three: 2026 NEC 424.44(E) and 424.45(E) require it for floor heating cable
    # (CKT-FH-BATH2/BATH1 outright); the dining zone (RM-M-LIVING) is outside the letter
    # of that rule but mat manufacturers require Class A protection regardless.
    #
    # RM-B-SAUNA has no floor heat (storeys/basement.py), so that zone, circuit and stat
    # are all gone.
    # FH-M-BATH2 is 17.85 ft2 of authored zone heated by one Schluter DHEHK12016 cable —
    # 16.0 ft2, 120 V, 203 W, 1.7 A as purchased — and this is that nameplate rather than
    # `area x 12`, because heating cable is sold in fixed lengths and cannot be cut. NEC
    # 120.51 (was 220.51) counts fixed electric space heating at 100% of load, so VA = W
    # here. 15 A stays despite a 1.7 A load — the
    # thermostat is a 15 A device with an integral Class A GFCI and its own box, and a
    # dedicated home run is what Schluter recommends. NEC 424.45(E) is what makes the GFCI
    # mandatory; this mat is the ONLY heat in RM-M-BATH2 (no supply register), so the
    # circuit is not optional comfort.
    Circuit(uid="CKT031AAAA", tag="CKT-FH-BATH2", slot=29, panel_ref=_PANEL, breaker_amps=15, poles=1,
            conductor_awg="14", egc_awg="14",
            gfci=True, breaker_lock_off=True, load_va=203,
            description="Radiant floor heat — main bath, sole heat source "
                        "(FH-M-BATH2, 17.85 ft2, Schluter DHEHK12016)"),
    # 424.19(B)(1) disconnect: a breaker lock-off fixed in place (owner, 2026-11-14). Square D
    # QO1PAF's fit on the QO GFCI/AFCI breaker is for the electrician to confirm.
    # (The dining mat and its slot-31 circuit are retired: no slab left to embed it in, decision #112.)
    Circuit(uid="CKT033AAAA", tag="CKT-FH-BATH1", slot=33, panel_ref=_PANEL, breaker_amps=15, poles=1,
            conductor_awg="14", egc_awg="14",
            # 338 VA: the wattage is a purchased nameplate (Schluter DHEHK12027, 26.7 ft2 /
            # 338 W / 2.8 A) rather than a stale area times 12. NEC 120.51 counts fixed
            # electric space heating at 100%, so this comes straight off the service demand.
            gfci=True, breaker_lock_off=True, load_va=338,
            description="Radiant floor heat — NW bathroom, sole heat source "
                        "(FH-S-BATH1, 26.815 ft2, Schluter DHEHK12027)"),
    # 1,500W at 120V=12.5A, continuous: 12.5x1.25=15.6A fits a 20A breaker's 16A but not
    # a 15A one's 12A — why these two are 20A where the mats are 15A.
    #
    # ** 20 A IS COMPELLED, NOT CHOSEN, AND TWO SECTIONS SAY SO. ** NEC 422.10(A) sizes the
    # branch circuit for a continuous-duty appliance at 125% of its rating: 12.5 x 1.25 =
    # 15.6 A, so a 15 A circuit is NON-COMPLIANT here rather than merely tight. And
    # 210.23(B)(2) caps a fastened-in-place appliance at 50% of a shared circuit's rating —
    # 12.5 / 20 = 62.5% — so this circuit may share with nothing, which is what "dedicated"
    # means on the panel schedule. The half of this the file used to carry was the first
    # sentence only.
    #
    # ** THE WIRE IS #12, AND IT IS SAID HERE BECAUSE THE SCHEMA CANNOT SAY IT. ** `Circuit`
    # has no conductor field and the model's docstring declares wire routing a non-goal, so
    # the only places a builder meets the gauge are this comment, the circuit description
    # and tasks.toml. `prices.toml`'s `[conductors]` rate "1" already buys 12/2 NM-B for a
    # 20 A circuit, so the bill and the note agree; nothing derives one from the other.
    #
    # ** NEITHER IS GFCI, AND THE CORD-AND-PLUG CLAUSE IS ONLY TRUE OF THE GARAGE. ** Both
    # are hard-wired equipment, and NEC 210.8(A) protects *receptacles*, not fixed wiring.
    # A cord-and-plug version in the GARAGE would need GFCI under 210.8(A)(2). A cord-and-plug
    # version in the LIVING ROOM would not: 210.8(A) does not list living rooms, and
    # 210.8(D)'s appliance list does not name room heaters. This file claimed the requirement
    # for both until 2026-09-20, which mattered the moment the fireplace cavity gained a
    # receptacle beside its J-box — that outlet is not a GFCI outlet.
    Circuit(uid="CKT034AAAA", tag="CKT-FIREPLACE", slot=35, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            afci=True, load_va=1500,
            # ** IT LEFT THE SE CORNER 2026-09-06. ** EQ-M-FIREPLACE is now in the brick
            # surround in the pier between WIN-M-LIV-E1 and WIN-M-LIV-E2 (W-M-FIRE-*,
            # plan/storeys/main.py). The unit is a real product now — an Amantii
            # BI-30-XTRASLIM — and it is still 120 V / 1,500 W / 12.5 A, so everything above
            # holds unchanged: same breaker, same slot, same pole count, same load. A 240 V
            # unit would have moved all four (and the ServicePort, and the panel balance);
            # plan/electrical.py's EQ-T-FIREPLACE-EL note says why none exists at this size.
            # ** THE POCKET IS 11 1/2" DEEP SINCE 2026-09-20 AND CARRIES TWO OUTLETS. ** The
            # recess behind the brick (AO-M-FIRE-NICHE, plan/storeys/main.py) was deepened to
            # open the appliance field past the one sole-source brand, and the cavity now
            # holds a recessed receptacle as well as the hardwire J-box — both on this one
            # circuit, so neither the load nor the breaker moves and a future replacement of
            # either kind lands in a box that already exists.
            # 2026-10-16: the surround moved 16" south (centre y=7'-4") onto the LVP; the
            # run lengthens nothing material and the circuit is unchanged.
            description="Electric fireplace, living room east wall, in the brick "
                        "surround between WIN-M-LIV-E1 and WIN-M-LIV-E2 (EQ-M-FIREPLACE). "
                        "DEDICATED, #12 Cu (12/2 NM-B): NEC 422.10(A) puts the continuous "
                        "load at 15.6 A and 210.23(B)(2) forbids sharing. Feeds BOTH the "
                        "cavity J-box and ED-M-FIRE-RC, so a hardwire or a cord-and-plug "
                        "appliance can be set in the pocket without a rewire"),
    # CKT-GAR-HEAT, CKT-LT-GARAGE and CKT-RC-GARAGE: plan/circuits_garage.py (2026-11-14).
    # RM-S-PLANT's fan heater (2026-11-12): 12.5 A does not belong on CKT-RC-SECOND.
    Circuit(tag="CKT-PLANT-HEAT", slot=41, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            load_va=1500, afci=True,
            description="Plant room 1500 W / 120 V fan heater (EQ-S-PLANT-HEATER), dedicated, "
                        "on always-on ED-S-PLANT-HEAT-RC (WR GFCI); Home Assistant switches the "
                        "heater through its plug-in Eve Energy (Matter)"),

    *BACKUP_CIRCUITS,
    *GARAGE_CIRCUITS,

    # --- general-use 120V ------------------------------------------------------------
    # ``afci=True`` on every circuit below (2026-08-01, code.E3902_16_afci): each reaches
    # a room on NEC 210.12(B)'s list as a 120V 15/20A branch circuit. The 240V loads (range,
    # dryer, heat pumps, kettle, PV backfeed) are outside the section's scope.
    # GFCI+AFCI on one circuit is a single dual-function breaker, costing one panel space.
    # 210.52(B)(1) puts every dining wall and counter receptacle on these two as well:
    # RC15/RC16/RC18 (ash counter) on SA1, RC2/RC3/RC7 (dining walls) on SA2 (2026-11-13).
    Circuit(uid="CKT020AAAA", tag="CKT-KITCH-SA1", slot=30, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            gfci=True, afci=True, load_va=1500,
            description="Kitchen small-appliance 1 (counter west + dining counter)"),
    Circuit(uid="CKT021AAAA", tag="CKT-KITCH-SA2", slot=32, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            gfci=True, afci=True, load_va=1500,
            description="Kitchen small-appliance 2 (counter east + pantry + dining walls)"),
    # GFCI here too: ED-M-LIVING-KDW1 is ~11" from the kitchen sink (210.8(A)(9); was 2.7'
    # before the 2026-08-26 sink/dishwasher re-composition moved both into the same base).
    Circuit(uid="CKT022AAAA", tag="CKT-DISHWASHER", slot=34, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            gfci=True, afci=True, load_va=1200,
            description="Dishwasher (sink base)"),
    # The disposer came off CKT-DISHWASHER (2026-08-07): a shared 20A branch is legal, but
    # a 3/4 HP motor's locked-rotor inrush on top of a dishwasher's heater is a nuisance
    # trip waiting to happen. Its own circuit is the cheap fix while the wall is open.
    # GFCI for the same 210.8(A)(9) reason (ED-M-LIVING-KDS1 sits under the sink).
    #
    # The 120V branch feeds the motor; the wall control is a 24V loop through a
    # contactor — see APPL-M-DISP's `install_parts` in plan/placeables.py.
    Circuit(uid="CKT038AAAA", tag="CKT-DISPOSAL", slot=39, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            gfci=True, afci=True, load_va=1000,
            description="Food waste disposer (sink base)"),
    # 210.8(A)(12) puts the laundry-area receptacle on GFCI outright, no distance test.
    Circuit(uid="CKT023AAAA", tag="CKT-LAUNDRY", slot=36, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            gfci=True, afci=True, load_va=1500,
            description="Laundry receptacle (washer)"),
    # No `load_va`: the panel schedule sums the fixtures on the circuit, and an authored value
    # would freeze them against a number nobody re-adds when a can moves.
    # ** 20 A SINCE 2026-10-28 (12 AWG). ** The garage's lights left for CKT-LT-GARAGE on
    # 2026-10-31 and its opener outlet on 2026-11-14 (the garage subpanel).
    # The kitchen cans and the pantry PSU joined from CKT-LT-BACKUP on 2026-11-02:
    # ~1,277 VA of 1,920 continuous.
    Circuit(uid="CKT024AAAA", tag="CKT-LT-MAIN", slot=38, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            afci=True,
            description="General lighting — main storey incl. kitchen and porch"),
    Circuit(uid="CKT025AAAA", tag="CKT-LT-UPPER", slot=43, panel_ref=_PANEL, breaker_amps=15, poles=1,
            conductor_awg="14", egc_awg="14",
            afci=True, description="General lighting — second + attic"),
    # The basement's lighting off the backup tier: the T8 strips and gym fan (2026-10-31), then
    # (2026-11-02) the gym, stair, bath and Play-N cans, sconces and PSUs, the sauna PSU and the
    # under-stair closet light, and the stair-head can its 3-way shares. ~802 VA of 1,440. Only the furnace-room cans and the
    # ESS closet light stay on CKT-LT-BACKUP. Slot 26 was spare.
    Circuit(uid="J3RFM1RVCW", tag="CKT-LT-BSMT", slot=26, panel_ref=_PANEL, breaker_amps=15,
            conductor_awg="14", egc_awg="14",
            poles=1, afci=True, description="Basement lighting (all but the furnace room), gym fan"),
    # The two storey receptacle circuits stay non-GFCI at the breaker on purpose: each
    # reaches a whole floor, and thirty outlets behind one 5 mA trip is not buildable.
    # The handful in a 210.8(A) location (mudroom sink, wet bar) are GFCI *devices* instead
    # (plan/electrical.py, plan/mep.py). Bathroom receptacles are on CKT-BATH-RC below.
    Circuit(uid="CKT026AAAA", tag="CKT-RC-MAIN", slot=44, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            afci=True, load_va=1500, description="General receptacles — main storey"),
    Circuit(uid="CKT027AAAA", tag="CKT-RC-SECOND", slot=45, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            afci=True, load_va=1500, description="General receptacles — second storey"),
    Circuit(uid="CKT028AAAA", tag="CKT-RC-BSMT", slot=46, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            gfci=True, afci=True, load_va=1500,
            description="General receptacles — basement + spa convenience"),
    Circuit(uid="CKT029AAAA", tag="CKT-RC-ATTIC", slot=47, panel_ref=_PANEL, breaker_amps=15, poles=1,
            conductor_awg="14", egc_awg="14",
            afci=True, load_va=1000,
            description="General receptacles — attic rooms + radon fan box, MN 1303.2402 subp. 6"),
    # ** EVERY BATHROOM VANITY RECEPTACLE, ONE CIRCUIT (owner, 2026-11-07). ** NEC
    # 210.11(C)(3): a 20 A circuit for bathroom receptacles feeding no other outlets
    # (210.23(B) Ex.), which may serve several bathrooms; `code.NEC_210_11_C3_bathroom_circuit`
    # grades it. These outlets
    # rode the storey circuits until now, and CKT-BATH-ATTIC is retired into this (slot 41
    # free). Eight outlets in seven bathrooms: ED-M-BATH1-RC1, ED-M-BATH2-RC1,
    # ED-M-BATH2-MIRROR-PLUG, ED-S-BATH1-RC-MIRROR, ED-S-SUITEBATH-RC1, ED-S-VANITY-RC1,
    # ED-B-BATH-RC1, ED-A-STUBATH-GFCI; plus ED-M-BATH2-MIRROR-HALO, the cord-and-plug
    # MHAP4236 (modelled as a light) in that mirror plug. Not here: ED-M-BATH2-TUB-RC
    # (CKT-BATH2-TUB) and the two washlet outlets, each on its own dedicated circuit.
    # GFCI AT THE DEVICE (reset in the room): GFCI guide-light vanity outlets; the mirror plug
    # behind the glass rides ED-M-BATH2-RC1's load side (gfci_ref). No AFCI: 2026 210.12(B)
    # does not list bathrooms. Not on backup (backup_power.md §5).
    # load_va 116 is the MHAP4236; receptacles are in 120.82(B)(1)'s VA/ft2 term, and
    # load_va overrides device summation, so never add 116 twice.
    Circuit(tag="CKT-BATH-RC", slot=31, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12",
            load_va=116,
            description="Bathroom vanity receptacles, every bathroom (receptacles only, "
                        "NEC 210.11(C)(3))"),
    # FX-M-BATH2-TUB's Bask heated surface (2026-08-29). Kohler's spec sheet lists the
    # REQUIRED service as a dedicated 120 V / 15 A circuit on a Class A GFCI, and that is
    # what this is — a manufacturer's requirement, not 210.11(C)(3). The bath is
    # cord-and-plug and factory-wired; the electrician owes it a GFCI-protected 15 A
    # grounded outlet behind the bath (ED-M-BATH2-TUB-RC), nothing more.
    #
    # ** 15 A IS THE MANUFACTURER'S NUMBER, NOT THE LOAD. ** The heater draws 0.5 A / 65 W (K-1130-W1) —
    # less than a light bulb. `load_va` is that 65, because the 120.82 summary has to see
    # what the house actually draws, and sizing it at the breaker would invent 1,735 VA of
    # demand out of a required circuit rating. `electrical.service_load` has 69.6 A of margin
    # against the 320 A service (250.4 A, 2026-11-07) and 65 VA is 0.3 A of it.
    #
    # GFCI AT THE BREAKER, not a GFCI device, and here that is not just the house convention
    # (plans/TODO.md): the outlet this circuit feeds is sealed inside SL-M-TUBDK's deck box
    # behind the bath. A GFCI receptacle there could not be tested or reset without pulling
    # a panel off the knee wall, which is the exact failure mode the breaker convention
    # exists to avoid. No AFCI: 210.12 does not list bathroom receptacle outlets.
    #
    # Slot 27 is one of the ten spare 1-pole spaces; count from the loaded plan
    # (`electrical.panel_spaces`), never by hand.
    Circuit(tag="CKT-BATH2-TUB", slot=27, panel_ref=_PANEL, breaker_amps=15, poles=1,
            conductor_awg="14", egc_awg="14",
            gfci=True, load_va=65,
            description="Bask heated surface — RM-M-BATH2 drop-in bath (FX-M-BATH2-TUB)"),
    # ------------------------------------------------------------------------------------
    # THE TWO WASHLET CIRCUITS (2026-09-06)
    # ------------------------------------------------------------------------------------
    # Both main-floor bowls were bought WASHLET+-ready — FX-TOTO-AP-WH on a DuoFit carrier
    # (the frame was chosen over a Geberit *for* this), FX-TOTO-CARLYLE-II's AT40 suffix IS
    # the readiness — and `[allowances] plumbing-bidet-seats` has been buying two TOTO
    # WASHLET S5 seats since the fixtures were selected. ** THE ELECTRICAL FOR THEM EXISTED
    # NOWHERE. ** Each bath had exactly one receptacle, a 44" vanity outlet on CKT-RC-MAIN,
    # and two 1.4 kW seats on a general storey circuit is ~23 A on a 20 A breaker before
    # anything else is plugged in. Nothing reported it: nothing ties a Product to a device.
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
    # because its outlet is sealed inside the tub deck. No AFCI: 210.12(B) does not list
    # bathrooms.
    #
    # ** load_va IS THE PUBLISHED NAMEPLATE, 1,271 VA (2026-11-14; was 0). ** TOTO spec sheet
    # SS-02276 v.02 (WASHLET S5, SW3445; the elongated SW3446 is the same seat): AC 120 V
    # 60 Hz, 1,271 W power consumption, 1,425 W maximum, 3.9 ft cord. The old 0 was the
    # owner's 2026-09-06 coincidence reading of 120.82(B)(1); the nameplate reading of
    # 120.82(B)(3) was measured then at +4.7 A of 320 A. Not continuous: the heater runs
    # seconds per use. Revisit if anything with a real duty cycle joins these circuits.
    Circuit(tag="CKT-WASHLET-BATH1", slot=25, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12", load_va=1271, continuous_va=0,
            description="Bidet seat — RM-M-BATH1 water closet (FX-M-BATH1-WC, WASHLET S5)"),
    Circuit(tag="CKT-WASHLET-BATH2", slot=28, panel_ref=_PANEL, breaker_amps=20, poles=1,
            conductor_awg="12", egc_awg="12", load_va=1271, continuous_va=0,
            description="Bidet seat — RM-M-BATH2 water closet (FX-M-BATH2-WC, WASHLET S5)"),
)

# --- Load management: NONE, and deliberately (2026-09-12) ------------------------------
# This house authors no ``LoadManagement`` at all, and ``plan/manifest.py`` passes none.
#
# Until 2026-09-12 four groups (LM-EV, LM-WELLNESS, LM-WH, LM-HP1-AUX) credited 18,240 VA
# and were the only reason the 120.82 demand fit a 200 A service. Three of them rested on
# software — Emporia PowerSmart throttling, an ESPHome/EcoNet automation, an Emporia
# contactor shed — and under the 2026 NEC (MN adopted it for permits filed on or after
# 2026-08-17) a controller that limits load in a service calculation has to be a POWER
# CONTROL SYSTEM: 130.2 requires the listing, 120.7 sets the setpoint at <= 80% of the
# monitored OCPD, and 625.42(A) points EV supply equipment at the same Part II. Emporia's
# gear carries UL 61010-2-030 / 2808 / 2594 / 2231 / 991 and no UL 3141, so none of those
# three credits was ever earnable. (The fourth, LM-HP1-AUX, was the compressor/supplemental
# interlock; 2026 120.82(C)(3) keeps it as `compressor_lockout_ref`, and catlin doesn't claim it.)
#
# The answer was the service, not a $2-3k listed PCS: a Class 320 HDLB meter-main with two
# 200 A mains. ** 250.4 A of unmanaged 120.82 demand against 320 A ** (2026-11-07; feeders
# ED-B-PANEL 135.7 A, ED-B-PANEL-2 120.7 A), no software in the calculation at all. The route
# back to 200 A is measured in plans/cost-options.md. See DESIGN-LOG.md "Electrical service"
# for the derivation, the three options priced, and why there is no 225 A service.
#
# Re-adding a group is a real decision, not a tidy-up: the engine now refuses a credit
# whose basis does not hold (takeoff/electrical.py::_credit_refusal), so a ``pcs`` without
# a ``listing`` FAILs `electrical.service_load` rather than quietly saving amps.

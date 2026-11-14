"""Catlin's 240 V dedicated-load circuits (range through ESS grid port), both feeder panels.

Split out of plan/circuits.py (AGENTS.md, files under 500 lines), which splices this tuple
into ``CIRCUITS`` at the same place, so the schedule's order is unchanged. Same conventions
as that file's docstring. NOT ``# haus: editable``: circuits are schedule data.
"""

from __future__ import annotations

from typehaus import Circuit

_PANEL = "ED-B-PANEL"
_PANEL_2 = "ED-B-PANEL-2"

DEDICATED_240V_CIRCUITS = (
    # --- 240V dedicated loads ---------------------------------------------------------
    # LG LSIL6336FE nameplate: 11.9 kW at 240 V, 40 A minimum circuit (LG spec sheet,
    # plan/appliance_types.py). A 14-50R is permitted on a 40 A circuit (NEC Table
    # 210.21(B)(3)). 120.82(B)(3) counts the nameplate, not the breaker.
    # 2-pole GFCI breaker (owner, 2026-11-07): 2026 NEC 210.8(D)(8) lists electric ranges,
    # and the 14-50R is a 125-250 V kitchen receptacle under 210.8(A)(7) besides.
    Circuit(uid="CKT001AAAA", tag="CKT-RANGE", slot=1, panel_ref=_PANEL, breaker_amps=40, poles=2,
            conductor_awg="8", egc_awg="10",
            nema="14-50R", gfci=True, load_va=11900, description="Kitchen range"),
    # LG's WKHC252HBA spec sheet gives the dryer as 830 W at 240 V and requires a 15 A
    # circuit. Keep the 14-30R for its specified four-wire dryer cord, but protect this
    # appliance circuit at 15 A. load_va is its nameplate, not the receptacle's rating;
    # 120.82(B)(3) counts a dryer's nameplate rating, while 120.54's 5,000 VA minimum is
    # for the standard method.
    # 2-pole GFCI breaker (owner, 2026-11-07): 2026 NEC 210.8(D)(11) lists clothes dryers,
    # and the 14-30R is a 125-250 V laundry-area receptacle under 210.8(A)(12).
    Circuit(uid="CKT002AAAA", tag="CKT-DRYER", slot=5, panel_ref=_PANEL, breaker_amps=15, poles=2,
            conductor_awg="10", egc_awg="10",
            nema="14-30R", gfci=True, load_va=830, description="Dryer"),
    # load_va is explicit so the schedule reads the figure the conductors are sized for.
    # CKT-EV-1450 feeds a HARDWIRED Grizzl-E (owner, 2026-10-30): no receptacle, so 210.8(A)(2)
    # and 625.54 do not apply and the charger's CCID protects; 40 A charge, 125% = 50 A plain.
    Circuit(uid="CKT003AAAA", tag="CKT-EV-1450", slot=9, panel_ref=_PANEL_2, breaker_amps=50, poles=2,
            conductor_awg="6", egc_awg="10", continuous_va=9600,  # EV: continuous in full (owner)
            # Buried leg CD-B-GAP-EV is a wet location (300.7(B), 310.10(C)): dual-rated wire,
            # Southwire SIMpull THHN/THWN-2 (SPEC 10000: "THWN-2: Wet locations not to exceed 90° C").
            conductor_insulation="THHN/THWN-2",
            load_va=9600, description="EV charging, hardwired Grizzl-E 40 A (garage)"),
    # The garage's 240 V point (backup EV charging, tools): one 6-20R, two hots + ground, no
    # neutral. 2-pole GFCI (210.8(A)(2) reaches 125-250 V garage receptacles); no AFCI.
    # Not a 210.52(G)(1) outlet, so the 120 V bay receptacles are on CKT-RC-GARAGE instead.
    Circuit(uid="CKT004AAAA", tag="CKT-GAR-240", slot=13, panel_ref=_PANEL_2, breaker_amps=20,
            conductor_awg="12", egc_awg="12",
            poles=2, nema="6-20R", gfci=True, load_va=3840,
            description="Garage 240 V receptacle (6-20R; backup EV charging, tools)"),
    # 2,500 VA (owner, 2026-11-14; was the breaker's 4,800, which is capacity, not load): the
    # computers, at most 1,000 W continuous, plus one 1,500 W bench tool at a time (a heat
    # gun or shop vac, 12.5 A on the 5-20R, under its 16 A 210.21(B)(2) cap). 125%: 11.5 A.
    # Common-trip 2-pole GFCI protects both voltages; supply two hots, neutral and ground.
    Circuit(uid="CKT039AAAA", tag="CKT-WORKSHOP-240", slot=17, panel_ref=_PANEL_2,
            breaker_amps=20, poles=2, gfci=True, load_va=2500, continuous_va=1000,
            conductor_awg="12", egc_awg="12", nema="5-20R/6-20R",
            description="Workshop electronics, 120/240 V receptacle (computers + bench tools)"),
    # Rough-in only (owner, 2026-11-14): breaker, CD-B-SPA and ED-B-SPA-DISC are built; no tub is
    # set at construction. 11.5 kW stays in the service calc. What a tub must meet:
    # notes/grounding_bonding.md section 10. Not continuous (owner).
    Circuit(uid="CKT005AAAA", tag="CKT-SPA", slot=1, panel_ref=_PANEL_2, breaker_amps=50, poles=2,
            conductor_awg="6", egc_awg="10", continuous_va=0,
            gfci=True, spa=True, rough_in_only=True, load_va=11500,
            description="Hot tub rough-in (sunken garden), no tub installed"),
    # 50A/2p GFCI per notes/sauna_shower_basement_detail.md (max 10.5 kW). EQ-B-SAUNA-HTR
    # is 9 kW = 37.5A, 46.9A at the 125% continuous factor, so 50A is the breaker.
    # ** 50 A / 9000 VA -> 60 A / 10500 VA, 2026-09-06, and the driver is the heater, not
    # the circuit. ** plan/electrical.py's EQ-T-SAUNA-HEATER note carries the finding: 9 kW
    # covers 283-494 cf on every manufacturer's own table and RM-B-SAUNA is 555. 2026 NEC
    # 424.5 makes fixed electric space heating a continuous load at 125%, so
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
    # 30 mA GFPE, which catches a real fault without the nuisance trips. The sauna LIGHTS are
    # on a separate circuit (CKT-LT-BSMT); 2026 210.8(A)(6) (basements) reaches receptacles,
    # not them, so their protection follows the luminaire listing.
    Circuit(uid="CKT006AAAA", tag="CKT-SAUNA", slot=5, panel_ref=_PANEL_2, breaker_amps=60, poles=2,
            conductor_awg="6", egc_awg="10", continuous_va=0,  # not continuous (owner)
            gfci=False, load_va=10500, description="Sauna heater (EQ-B-SAUNA-HTR), 10.5 kW"),
    # CKT-WH (was CKT-WH-240) is on the backup subpanel — see the SURPLUS tier below. Slot 25
    # is a spare on the main panel now.
    Circuit(uid="CKT008AAAA", tag="CKT-ERV", slot=2, panel_ref=_PANEL, breaker_amps=15, poles=2,
            conductor_awg="14", egc_awg="14",
            load_va=200, description="ERV"),
    # The three Gree heat-pump systems (plan/electrical.py). A multi's indoor heads are fed
    # from the outdoor unit, so System 2's three heads add no circuits; System 1's ducted
    # air handler does get its own, because a ducted blower is fed at the unit.
    # 25A is unchanged and still correct: the FXU24HP230V1R32AO's MCA is 21 A and its maximum
    # overcurrent device is 25 A, the same pair of numbers the VIR24 carried. `load_va` is
    # MCA x 240 V (21 x 240 = 5,040), which is the conservative reading — MCA already carries
    # the 125% on the compressor, so this over-states the running load rather than under-stating
    # it in the 120.82 summary. Nothing in checks/ compares breaker_amps to load_va; this
    # arithmetic is held correct by hand, and saying so is part of keeping it that way.
    #
    # ** 2-POLE CLASS A GFCI ON ALL THREE OUTDOOR UNITS (owner, 2026-11-07). ** 2026 NEC
    # 210.8(F) reaches outdoor outlets to 60 A, listed HVAC included from 2026-09-01 (MN DLI
    # NEC FAQ rev. 2026-10-05 #4). The owner chose Ex. 3's listed Class C SPGFCI first, but
    # no Class C panel breaker at 15/25/30 A was found (Square D, Eaton, Siemens, GE,
    # Leviton; UL KCYC page; 2026-11-07) — only Littelfuse's industrial SB6100. So Class A,
    # no disconnect label: QO225GFI / QO230GFI (Class A 6 mA; rexelusa.com, 2026-11-07).
    # Swap to gfci_class="C" + the ED-M-HPn-DISC label the day one is listed.
    Circuit(uid="CKT009AAAA", tag="CKT-HP1", slot=6, panel_ref=_PANEL, breaker_amps=25, poles=2,
            conductor_awg="10", egc_awg="10",
            gfci=True, load_va=5040,
            description="Heat pump 1 outdoor, FLEXX Ultra 24k (EQ-M-HP1-OD)"),
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
    # as an interlock, which is what kept the house inside a 200 A service. The printed 2026
    # 120.82(C)(3) does drop a compressor prevented from running with the supplemental heat
    # (`Equipment.compressor_lockout_ref`), but a reconfigurable thermostat lockout is a weak
    # "prevented" and 320 A doesn't need it: not claimed (owner, 2026-11-13).
    Circuit(uid="CKT036AAAA", tag="CKT-HP1-AH", slot=50, panel_ref=_PANEL, breaker_amps=35, poles=2,
            conductor_awg="8", egc_awg="10",
            load_va=5300,
            description="Heat pump 1 indoor, ducted air handler + 4.6 kW heat kit (EQ-S-HP1-AH, EQ-S-HP1-STRIP)"),
    # Slot 40 since 2026-11-14: it gave 49/51 to CKT-ESS-GRID, the bus's last row (705.12(B)(2)).
    Circuit(uid="CKT037AAAA", tag="CKT-HP2", slot=40, panel_ref=_PANEL, breaker_amps=30, poles=2,
            conductor_awg="10", egc_awg="10",
            gfci=True, load_va=6000,
            description="Heat pump 2 outdoor, Multi Ultra 4-port (EQ-M-HP2-OD; feeds 3 heads, one port unused)"),
    # System 3 (below, backup microgrid) is a true-VFD compressor that soft-starts, which
    # is what makes it carryable by the battery inverter at all.
    # GFCI at the breaker (code.E3902_gfci_locations): ED-M-LIVING-KET1 sits 3.2' from the
    # kitchen sink, and 2026 NEC 210.8(A) covers 125-250 V receptacles, 240 V ones included
    # ((A)(7) kitchen, (A)(9) sink). A 2-pole GFCI breaker is the only place to protect a 6-20R.
    # SEVERIN WK 3422 selected 2026-10-25: published 3,000 W nameplate.
    # The old 3,840 was the breaker (20 A x 240 V), not a load. Run time (~5 min/day)
    # earns nothing in 120.82; only a 120 V kettle on a small-appliance circuit leaves the count.
    Circuit(uid="CKT011AAAA", tag="CKT-KETTLE", slot=14, panel_ref=_PANEL, breaker_amps=20, poles=2,
            conductor_awg="12", egc_awg="12", continuous_va=0,  # not continuous (owner)
            nema="6-20R", gfci=True, load_va=3000,
            description="SEVERIN WK 3422 tea maker via UK adapter (6-20R half)"),
    # The EG4 12kPV's grid port, at the opposite end of the bus from the main (120% rule
    # headroom is why the panel is a 225A bus on a 200A main). Slots 51/53 are the last row
    # of a top-fed 54-space can, nothing beyond it; at 40/42 rows 22-26 held breakers below. Both PV and battery reach the
    # service through this one breaker — the array lands on the inverter's MPPTs
    # (EQ-B-ESS-INV) rather than backfeeding on its own.
    #
    # 50A: 8,000 W continuous at 240V = 33.3A, x125% = 41.7A, next standard size up
    # (the 80A grid-passthrough rating is pass-through capability, not backfeed). The
    # 705.12 ceiling on this bus is 225x1.2-200=70A, so 50A leaves 20A
    # for a future second source (V2H).
    #
    # source=True excludes it from the 120.82 load summary and includes it in the 705.12
    # busbar check.
    Circuit(uid="CKT012AAAA", tag="CKT-ESS-GRID", slot=51, panel_ref=_PANEL, breaker_amps=50,
            # #6 Cu: EG4 publishes no terminal temperature (ESS User Manual v1.0 §10.2: GRID
            # takes up to 4 AWG), so 110.14(C)(1)(a)'s 60 °C column: 55 A >= 50 A.
            conductor_awg="6", egc_awg="10",
            poles=2, source=True, load_va=0,
            description="EG4 12kPV grid port — PV + battery interconnection (EQ-B-ESS-INV)"),
    # CKT-HP1-STRIP IS DELETED, AND SLOT 18 IS A SPARE 2-POLE AGAIN: the aux heat is now a
    # FACTORY kit inside the air handler's cabinet, fed and staged from the unit, so it
    # rides CKT-HP1-AH above rather than a circuit of its own.

)

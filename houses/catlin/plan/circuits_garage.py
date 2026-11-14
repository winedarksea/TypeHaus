"""Catlin's garage: one feeder from ED-B-PANEL-2 and the circuits of its subpanel ED-G-PANEL.

Spliced into ``CIRCUITS`` by plan/circuits.py; same conventions as that file's docstring.
NOT ``# haus: editable``: circuits are schedule data.

** ONE SUPPLY (owner, 2026-11-14). ** The garage is a separate building, and seven house
circuits reached it: 225.30 allows one feeder or branch circuit, and a plain EVSE is not a
listed power-transfer system needing more than one (225.30(A)). So the EV circuit moved into
the subpanel with everything else; a separate EV branch beside the feeder would be a second
supply. The subpanel's 100 A main is the 225.31 disconnect, inside where the feeder rises.

Six garage loads before -> five breakers here:
- CKT-LT-GARAGE now also feeds the opener outlet (was CKT-LT-MAIN) and the heat alarm (was
  CKT-LT-BACKUP: a backup circuit could not stay a second supply). 15 -> 20 A for the 20 A
  opener duplex (Table 210.21(B)(3)).
- CKT-RC-GARAGE stays alone: 210.11(C)(4) bars other outlets.
- CKT-GAR-HEAT stays alone: the wall-bracketed 12.5 A heater is fastened in place, over
  210.23(B)(2)'s 50% share of a 20 A circuit.
- CKT-GAR-240 stays alone: a 2-pole 6-20R, no neutral.
- CKT-EV-1450 unchanged but for its panel.

Feeder load, 215.2 without demand factors (conservative): EV 9,600 x 1.25 + heater 1,500 x
1.25 + lighting ~1,000 x 1.25 + 6-20R 3,840 + receptacles 1,500 + opener ~500 = 20,965 VA,
87 A at 240 V. 90 A on #2 Cu, the 60 C column's 95 A (110.14(C)(1)(a): HOM290 publishes no
terminal temperature), within both the breaker's AWG 4-2/0 and the panel lugs' 6-1 Cu. 100 A
would want #1 Cu, 41% of the 1 1/4" Sch 80 leg's area (40% allowed).
"""

from __future__ import annotations

from typehaus import Circuit

_PANEL_2 = "ED-B-PANEL-2"
_GARAGE = "ED-G-PANEL"
# Buried legs are a wet location (300.7(B), 310.10(C)): dual-rated wire, Southwire SIMpull
# THHN/THWN-2 (SPEC 10000: "THWN-2: Wet locations not to exceed 90° C").
_WET = "THHN/THWN-2"

GARAGE_CIRCUITS = (
    # The feeder: Homeline HOM290 (90 A 2P, 10 kA; data sheet 2025-07-15) in slot 9/11,
    # CKT-EV-1450's old space. load_va 0: the subpanel's own circuits carry the load, and
    # `electrical.panel_feeder_load` rolls them up into ED-B-PANEL-2. EGC #8 Cu (250.122,
    # 90 A); the garage neutral is isolated (SE-M-SERVICE.neutral_isolated_refs).
    Circuit(tag="CKT-GAR-FEEDER", slot=9, panel_ref=_PANEL_2, breaker_amps=90, poles=2,
            conductor_awg="2", egc_awg="8", conductor_insulation=_WET, load_va=0,
            description="Feeder to the garage subpanel ED-G-PANEL (90 A, #2 Cu + #8 EGC, "
                        "CD-B-GARAGE / CD-B-GAP-EV)"),
    # Square D HOM2175SB plug-on Type 2 SPD beside the main, as in the other three panels.
    # 215.18(A) reaches feeders to dwelling units and the garage is not one: this is the
    # house standard, and it guards the EVSE. Removable without a code finding.
    Circuit(tag="CKT-SPD-GAR", slot=2, panel_ref=_GARAGE, breaker_amps=20, poles=2,
            load_va=0, spd=True, spd_type_ref="ED-T-SPD-HOM2175SB",
            description="Type 2 surge protective device, garage subpanel"),
    # Hardwired Grizzl-E (owner, 2026-10-30): no receptacle, so 210.8(A)(2) and 625.54 do not
    # apply and the charger's CCID protects; 40 A charge, 125% = 50 A plain. The breaker is
    # now in sight of the charger.
    Circuit(uid="CKT003AAAA", tag="CKT-EV-1450", slot=1, panel_ref=_GARAGE, breaker_amps=50,
            poles=2, conductor_awg="6", egc_awg="10",
            continuous_va=9600,  # EV: continuous in full (owner)
            load_va=9600, description="EV charging, hardwired Grizzl-E 40 A (garage)"),
    # One 6-20R, two hots + ground, no neutral. 2-pole GFCI (210.8(A)(2) reaches 125-250 V
    # garage receptacles); not a 210.52(G)(1) outlet.
    Circuit(uid="CKT004AAAA", tag="CKT-GAR-240", slot=5, panel_ref=_GARAGE, breaker_amps=20,
            conductor_awg="12", egc_awg="12",
            poles=2, nema="6-20R", gfci=True, load_va=3840,
            description="Garage 240 V receptacle (6-20R; backup EV charging, tools)"),
    # The 210.11(C)(4) circuit: 120 V, 20 A, the two bay receptacles ED-G-RC-W/-E only.
    Circuit(uid="CKT030AAAA", tag="CKT-RC-GARAGE", slot=6, panel_ref=_GARAGE, breaker_amps=20,
            poles=1, conductor_awg="12", egc_awg="12",
            gfci=True, load_va=1500, description="Garage general receptacles"),
    # 424.19: the heater's cord and plug is its disconnect (owner, 2026-11-14).
    Circuit(uid="CKT035AAAA", tag="CKT-GAR-HEAT", slot=8, panel_ref=_GARAGE, breaker_amps=20,
            poles=1, conductor_awg="12", egc_awg="12",
            load_va=1500, gfci=True,
            description="Garage DR-238 carbon radiant heater, 1500 W / 120 V (EQ-G-HEATER), "
                        "dedicated GFCI-protected ED-G-HEATER-RC; retain factory cord and plug"),
    # Shop lights, door sconces, the six Class 2 eave/gable drivers (summed at their 96 VA),
    # the opener's outlet behind ED-G-GDO-GFCI and the AL-G-HEAT detector on its unswitched
    # hot. No load_va: the takeoff sums the devices. No AFCI: a garage is not on 210.12's list.
    Circuit(uid="GWECBY2WVZ", tag="CKT-LT-GARAGE", slot=9, panel_ref=_GARAGE, breaker_amps=20,
            poles=1, conductor_awg="12", egc_awg="12",
            description="Garage lighting — shop lights, door sconces, eave + gable linear "
                        "drivers, opener outlet, heat alarm"),
)

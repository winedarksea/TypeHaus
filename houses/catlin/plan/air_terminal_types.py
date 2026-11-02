"""Catlin's air terminals and outdoor hoods, at their submittal sizes (2026-10-31).

One white powder-coated family: 100 mm steel disc valves on the ERV, aluminium grilles and
registers on System 1. Every type is a performance spec plus a basis of design "or equal"
(``product_ref`` -> plan/products_air.py). The rule for the geometry: ``footprint``/``height``
is the published FACE (a wall type authors (face width, projection) and the face height in
``height``), and ``neck`` is the part in the cavity. Sources, what is unverified, and the fit
sign-off: notes/air_distribution_products.md. Loss curves feed `mep.erv_static_budget`
(notes/erv_static_budget.md §5 and §10).

NOT ``# haus: editable``: catalog definitions, nothing placed. The library's generic
REG-T-ERV-*/REG-T-HP-*/hood rows stay for other houses.
"""

from __future__ import annotations

from typehaus import (
    EquipmentType,
    RegisterType,
    Service,
    ServicePort,
    TerminalNeck,
    TerminalNeckInlet,
    ft,
    inch,
)

from plan.plant_supply_terminal import PLANT_SUPPLY_NECK

_NOTE = "notes/air_distribution_products.md"


def _port(tag: str, service: Service, z=None) -> ServicePort:
    return ServicePort(tag=tag, service=service,
                       position=(ft(0), ft(0), ft(0) if z is None else z))


# Trox LVS 100 at +5 mm (fully open), PD-02/2022: 8 / 19 / 33 Pa at 10 / 15 / 20 L/s. The
# two lowest points are that curve's own K (8 Pa / 21.2 cfm^2) below its published range,
# where most of this house's terminals run. The supply pattern publishes no curve that was
# read; it is held to the same ceiling.
_VALVE_PA = ((5.0, 0.45), (10.0, 1.8), (21.2, 8.0), (31.8, 19.0), (42.4, 33.0))
# Trox LVS 125 at +5 mm, same sheet: 9 / 15 / 24 / 35 Pa at 15 / 20 / 25 / 30 L/s; the two
# lowest points are its own K below the published range.
_VALVE_125_PA = ((10.0, 0.9), (20.0, 3.6), (31.8, 9.0), (42.4, 15.0), (53.0, 24.0),
                 (63.6, 35.0))
# Valve plus an open single-blade damper, C 0.20 on the 4in velocity pressure (ASHRAE
# Fundamentals Ch. 21, CD9-1 at 0 deg): 0.04 Pa at 10 cfm.
_PLANT_PA = ((5.0, 0.46), (10.0, 1.84), (21.2, 8.2), (31.8, 19.4), (42.4, 33.7))
# A floor grille on a boot publishes no curve: the derived K 5 of the note's §5.
_FLOOR_GRILLE_PA = ((10.0, 1.0), (20.0, 4.0), (30.0, 9.0))

_VALVE_NECK = TerminalNeck(width=inch(4), height=inch(4), depth=inch(2.9375),
                           part="100 mm valve collar in a 4in snap-lock collar")
_OBD_NECK_1206 = TerminalNeck(width=inch(12), height=inch(6), depth=inch(2.6875),
                              part="opposed-blade damper and register box")
_OBD_NECK_0806 = TerminalNeck(width=inch(8), height=inch(6), depth=inch(2.6875),
                              part="opposed-blade damper and register box")

AIR_REGISTER_TYPES = (
    RegisterType(tag="REG-T-ERV-VALVE-SUP",
                 name="ERV supply disc valve, 100 mm, white steel, ceiling collar",
                 footprint=(inch(5.0625), inch(5.0625)), height=inch(1), plan_symbol="register",
                 ventilation_terminal=True, product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_VALVE_PA, neck=_VALVE_NECK,
                 source=f"Face 5 1/16in round (Vents AM 100 VR); run near fully open, "
                        f"balanced at the plenum collar dampers. {_NOTE} §2.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    # The house's one 30 cfm terminal (REG-B-SUP2, PLAY's outdoor-air supply, R303.1 Exc. 1):
    # a 100 mm valve loses 17 Pa there and governed the whole machine, so it takes the
    # 125 mm valve on a 4x5 increaser — 8 Pa (notes/erv_static_budget.md §10).
    RegisterType(tag="REG-T-ERV-VALVE-SUP-125",
                 name="ERV supply disc valve, 125 mm, white steel, ceiling collar, 4x5in "
                      "increaser",
                 footprint=(inch(6.375), inch(6.375)), height=inch(1), plan_symbol="register",
                 ventilation_terminal=True, product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_VALVE_125_PA,
                 neck=TerminalNeck(width=inch(5), height=inch(5), depth=inch(2.9375),
                                   part="125 mm valve collar on a 4x5in increaser"),
                 source=f"Same family at 125 mm: face 162 mm (Trox LVS 125 table), spigot "
                        f"124 mm into a 5in collar. {_NOTE} §2.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    RegisterType(tag="REG-T-ERV-VALVE-EXH",
                 name="ERV extract disc valve, 100 mm, white steel, ceiling collar",
                 footprint=(inch(5.0625), inch(5.0625)), height=inch(1), plan_symbol="register",
                 ventilation_terminal=True, product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_VALVE_PA, neck=_VALVE_NECK,
                 source=f"Extract pattern of the supply valve; pull it from the collar to "
                        f"clean, lock ring holds the setting. {_NOTE} §2.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # Wall type: (face width, projection), face height in `height`. 1 3/4in is the AM 100's
    # published overall height, so A117 sec. 307.2's 4in at REG-A-STUBATH-EXH holds on it.
    RegisterType(tag="REG-T-ERV-VALVE-EXH-WALL",
                 name="ERV extract disc valve, 100 mm, white steel, sidewall collar",
                 footprint=(inch(5.0625), inch(1.75)), height=inch(5.0625),
                 plan_symbol="register", ventilation_terminal=True,
                 product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_VALVE_PA, neck=_VALVE_NECK,
                 source=f"Same valve in a wall collar; no maker sells a sidewall-specific "
                        f"collar, the ceiling collar is screwed to the stud-bay blocking. "
                        f"{_NOTE} §2.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # A disc valve cannot sit in a floor. Long side along the joist bay.
    RegisterType(tag="REG-T-ERV-EXH-FLOOR",
                 name="ERV extract floor grille, 2 1/4x10 aluminium, on a 4in-round boot",
                 footprint=(inch(12), inch(3.5)), height=inch(1), plan_symbol="register",
                 ventilation_terminal=True, product_ref="PROD-AIR-FLOOR-GRILLE-2X10",
                 static_loss_pa_at_cfm=_FLOOR_GRILLE_PA,
                 neck=TerminalNeck(width=inch(10), height=inch(2.25), depth=inch(5),
                                   part="2 1/4x10x4 stamped 90-degree boot"),
                 source=f"Face 12 x 3 1/2in outside (Ferguson 412-AH listing, 2026-10-31); "
                        f"the boot's 5in height is unpublished, an estimate. Loss: derived K 5 "
                        f"(erv_static_budget §5). {_NOTE} §3.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # RM-S-PLANT is held at 75 F / 70% RH and slightly negative (notes/plant_room.md): its
    # extract is RH-controlled. The 4in 24 VAC damper sits on DU-M-ERV-R-PLANT's start
    # collar in RM-M-MECH, reachable without an access panel in the humid liner.
    RegisterType(tag="REG-T-ERV-PLANT-EXH",
                 name="Plant-room extract disc valve, 100 mm, RH-controlled 4in damper at "
                      "the plenum",
                 footprint=(inch(5.0625), inch(1.75)), height=inch(5.0625),
                 plan_symbol="register", ventilation_terminal=True,
                 product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_PLANT_PA, neck=_VALVE_NECK,
                 source=f"notes/plant_room.md — dedicated dampered extract off EQ-B-ERV; "
                        f"damper PROD-AIR-DAMPER-4-24V at the level-2 plenum. A stainless "
                        f"valve was looked for and not found retail; the powder-coated steel "
                        f"valve is cleaned yearly. {_NOTE} §7.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    RegisterType(tag="REG-T-HP-SIDE-1206",
                 name="Heat-pump supply, 12x6 aluminium double-deflection sidewall with OBD",
                 footprint=(inch(13.75), inch(1)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-SIDEWALL-DD-OBD", neck=_OBD_NECK_1206,
                 source=f"TRUaire A220VO 12X06 face 13 3/4 x 7 3/4in. Double deflection: the "
                        f"vertical blades aim, the horizontal set the spread. {_NOTE} §4.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    RegisterType(tag="REG-T-HP-STAIR-SIDE",
                 name="Stair supply A220VO 12x6 with TH-HP-STAIR-BOX-01 and 4in branch",
                 footprint=(inch(13.75), inch(1)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-SIDEWALL-DD-OBD",
                 neck=TerminalNeck(width=inch(12), height=inch(6), depth=inch(4),
                     part="TH-HP-STAIR-BOX-01 12x6x4 register box with centred 4in back collar",
                     product_ref="PROD-AIR-STAIR-REGISTER-BOX",
                     inlet=TerminalNeckInlet(position=(inch(0), inch(4), inch(0)),
                         section="round", width=inch(4), height=inch(4), normal=(0, 1))),
                 source="50 cfm through 4in galvanized branch to the trunk. "
                        "notes/stair_supply_connection.md; grille retains OBD and westward throw.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    RegisterType(tag="REG-T-HP-STUDY-SIDE",
                 name="Study heat-pump supply, 8x6 aluminium double-deflection sidewall with "
                      "OBD",
                 footprint=(inch(9.75), inch(1)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-SIDEWALL-DD-OBD", neck=_OBD_NECK_0806,
                 source=f"TRUaire A220VO 08X06, face 9 3/4 x 7 3/4in; notes/system1_study_"
                        f"supply.md keeps the Titus 300R 8x6 throw basis. {_NOTE} §4.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    RegisterType(tag="REG-T-HP-FLOOR-0612",
                 name="Heat-pump supply, 6x12 aluminium floor register with damper",
                 footprint=(inch(13.375), inch(7.375)), height=inch(1), plan_symbol="register",
                 product_ref="PROD-AIR-FLOOR-REG-6X12",
                 neck=TerminalNeck(width=inch(12), height=inch(6), depth=inch(2),
                                   part="multi-shutter damper below the flange"),
                 source=f"Face 7 3/8 x 13 3/8in and 2in damper depth are planning figures, "
                        f"not published at this size. {_NOTE} §4.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    # One assembly allowance: grille, collar, motorized damper (including actuator), boot.
    RegisterType(tag="REG-T-HP-CEIL-DAMPERED",
                 name="Plant supply A220V 12x6 / ZD12X6TZ / TH-HP-PLANT-BOOT-01 assembly",
                 footprint=(inch(13.75), inch(7.75)), height=inch(1), plan_symbol="register",
                 product_ref="PROD-AIR-PLANT-GRILLE-12X6", neck=PLANT_SUPPLY_NECK,
                 source=f"75 cfm, RH interlocked; westward throw. Motor actuator west of the "
                        f"damper, removable service cassette. {_NOTE} §7; notes/plant_supply_connection.md.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    # The only filter in System 1. 12x28x1 is not a stocked size and no stocked size fits
    # EQ-S-ERV-MIX's 12 x 29 opening under Manual D's 300 fpm (12x24x1: 347 fpm at 650 cfm),
    # so the 28x12 grille stays and the filter is ordered as a custom size.
    RegisterType(tag="REG-T-HP-RET-FILTER",
                 name="Heat-pump return, 28x12 aluminium hinged filter-back grille",
                 footprint=(inch(30.625), inch(14.625)), height=inch(1),
                 plan_symbol="register", product_ref="PROD-AIR-FILTER-RETURN-28X12",
                 filter_nominal_size="28x12x1", filter_merv=13, service_face="bottom",
                 neck=TerminalNeck(width=inch(28), height=inch(12), depth=inch(1.75),
                                   part="1in filter rack"),
                 source=f"Face estimated off H&C 673 30x12 (32 5/8in overall); 28 x 12in duct "
                        f"size, 336 in2, 279 fpm at 650 cfm. {_NOTE} §5.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    RegisterType(tag="REG-T-TRANSFER-PAIR-1210",
                 name="Transfer grille pair, 12x10 aluminium return grilles through the wall",
                 footprint=(inch(13.75), inch(1)), height=inch(11.75), plan_symbol="register",
                 product_ref="PROD-AIR-RETURN-GRILLE-12X10",
                 neck=TerminalNeck(width=inch(12), height=inch(10), depth=inch(5.5),
                                   part="12x10 sheet-metal sleeve through the stud bay"),
                 source=f"Two grilles back to back on a lined sleeve; 12in fits a 14 1/2in "
                        f"bay without cutting a stud. Face estimated at +1 3/4in. {_NOTE} §6.",
                 ports=()),
)

# 8in hoods, 1/4in screen. Curves are RenewAire's FA8 chart end points (0.34 in. w.g.
# intake and 0.215 exhaust at 400 cfm) scaled as Q^2; the discharge row adds the BD8
# inline damper (0.5 in. w.g. at 830 cfm, same scaling). A 12 x 12 x 12 box is kept as the
# envelope: the FA8's plate is unpublished and the FML8's is 9 x 9.
AIR_HOOD_TYPES = (
    EquipmentType(tag="EQ-T-ERV-HOOD-8",
                  name="Exterior intake hood, 8in round, 1/4in screen, no damper",
                  footprint=(inch(12), inch(12)), height=inch(12), plan_symbol="erv",
                  duct_ports=1, port_diameter=inch(8), product_ref="PROD-AIR-HOOD-8",
                  static_loss_pa_at_cfm=((100.0, 5.3), (150.0, 11.9), (210.0, 23.3),
                                         (250.0, 33.1), (400.0, 84.7)),
                  ports=(_port("duct", Service.OUTDOOR_AIR, inch(6)),),
                  source=f"RenewAire FA8-P, supply-mode chart. {_NOTE} §8."),
    EquipmentType(tag="EQ-T-ERV-HOOD-8-EXH",
                  name="Exterior discharge hood, 8in round, 1/4in screen, inline BD8 "
                       "backdraft damper",
                  footprint=(inch(12), inch(12)), height=inch(12), plan_symbol="erv",
                  duct_ports=1, port_diameter=inch(8), product_ref="PROD-AIR-HOOD-8",
                  static_loss_pa_at_cfm=((100.0, 5.2), (150.0, 11.6), (210.0, 22.7),
                                         (250.0, 32.2), (400.0, 82.5)),
                  ports=(_port("duct", Service.EXHAUST_AIR, inch(6)),),
                  source=f"RenewAire FA8-P exhaust-mode chart plus BD8. {_NOTE} §8."),
)

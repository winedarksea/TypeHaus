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
from typehaus.model import ProductPart

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
# Same conservative K=5 allowance as the floor boot; no measured curve for this box.
_SUITEBATH_BOOT_REFERENCE_CFM = 20.0
_SUITEBATH_BOOT_REFERENCE_LOSS_PA = 4.0

_VALVE_NECK = TerminalNeck(section="round", width=inch(4), height=inch(4), depth=inch(2.9375),
                           part="100 mm valve collar in a 4in snap-lock collar")
_OBD_NECK_1206 = TerminalNeck(section="rectangular",
                              width=inch(12), height=inch(6), depth=inch(2.6875),
                              part="opposed-blade damper and register box")
_OBD_NECK_0806 = TerminalNeck(section="rectangular",
                              width=inch(8), height=inch(6), depth=inch(2.6875),
                              part="opposed-blade damper and register box")

AIR_REGISTER_TYPES = (
    RegisterType(tag="REG-T-ERV-VALVE-SUP",
                 face_style="disc_valve",
                 name="ERV supply disc valve, 100 mm, white steel, ceiling collar",
                 footprint=(inch(5.0625), inch(5.0625)), height=inch(1), plan_symbol="register",
                 ventilation_terminal=True, product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_VALVE_PA, neck=_VALVE_NECK,
                 source=f"Face 5 1/16in round (Vents AM 100 VR); run near fully open, "
                        f"balanced at the plenum collar dampers. {_NOTE} §2.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    # The house's one 30 cfm terminal (REG-B-SUP2, PLAY's outdoor-air supply, R303.1 Exc. 1):
    # a 100 mm valve loses 17 Pa there and governed the whole machine, so it takes the
    # 125 mm valve on a 4x5 increaser — 8 Pa (notes/erv_static_budget.md §10). On the wall
    # since 2026-11-10, like both basement supplies: (face width, projection), height.
    RegisterType(tag="REG-T-ERV-VALVE-SUP-125-WALL",
                 face_style="disc_valve",
                 name="ERV supply disc valve, 125 mm, white steel, sidewall collar, 4x5in "
                      "increaser",
                 footprint=(inch(6.375), inch(1.75)), height=inch(6.375),
                 plan_symbol="register", ventilation_terminal=True,
                 product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_VALVE_125_PA,
                 neck=TerminalNeck(section="round",
                                   width=inch(5), height=inch(5), depth=inch(2.9375),
                                   part="125 mm valve collar on a 4x5in increaser"),
                 source=f"Same family at 125 mm: face 162 mm (Trox LVS 125 table), spigot "
                        f"124 mm into a 5in collar, screwed to the stud-bay blocking. {_NOTE} §2.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    RegisterType(tag="REG-T-ERV-VALVE-SUP-WALL",
                 face_style="disc_valve",
                 name="ERV supply disc valve, 100 mm, white steel, sidewall collar",
                 footprint=(inch(5.0625), inch(1.75)), height=inch(5.0625),
                 plan_symbol="register", ventilation_terminal=True,
                 product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_VALVE_PA, neck=_VALVE_NECK,
                 source=f"The supply valve in a wall collar, as REG-T-ERV-VALVE-EXH-WALL. "
                        f"{_NOTE} §2.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    RegisterType(tag="REG-T-ERV-VALVE-EXH",
                 face_style="disc_valve",
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
                 face_style="disc_valve",
                 name="ERV extract disc valve, 100 mm, white steel, sidewall collar",
                 footprint=(inch(5.0625), inch(1.75)), height=inch(5.0625),
                 plan_symbol="register", ventilation_terminal=True,
                 product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_VALVE_PA, neck=_VALVE_NECK,
                 source=f"Same valve in a wall collar; no maker sells a sidewall-specific "
                        f"collar, the ceiling collar is screwed to the stud-bay blocking. "
                        f"{_NOTE} §2.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # Same removable valve; a dimensioned bottom-entry box replaces the implicit elbow.
    # A 1.5D round elbow cannot turn inside this 5 1/2in staggered wall cavity.
    RegisterType(tag="REG-T-ERV-SUITEBATH-WALL",
                 face_style="disc_valve",
                 name="Suite bath 100 mm extract valve on TH-ERV-SUITEBATH-BOOT-01",
                 footprint=(inch(5.0625), inch(1.75)), height=inch(5.0625),
                 plan_symbol="register", ventilation_terminal=True,
                 product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=tuple(
                     (cfm, pa + _SUITEBATH_BOOT_REFERENCE_LOSS_PA
                      * (cfm / _SUITEBATH_BOOT_REFERENCE_CFM) ** 2) for cfm, pa in _VALVE_PA),
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(4), height=inch(8), depth=inch(5.25),
                     part="TH-ERV-SUITEBATH-BOOT-01 4x8x5-1/4in bottom-entry valve box",
                     product_ref="PROD-AIR-SUITEBATH-BOOT"),
                 parts=(ProductPart(role="fitting", product_ref="PROD-AIR-SUITEBATH-BOOT"),),
                 source="notes/suitebath_extract.md: 26ga sealed box, 4in bottom inlet, "
                        "100 mm front collar. Valve curve plus estimated K=5 boot loss; "
                        "balance to 20 cfm on commissioning.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # A disc valve cannot sit in a floor. Long side along the joist bay.
    RegisterType(tag="REG-T-ERV-EXH-FLOOR",
                 face_opening=(inch(10), inch(2.25)),
                 face_style="rectangular_grille",
                 name="ERV extract floor grille, 2 1/4x10 aluminium, on a 4in-round boot",
                 footprint=(inch(12), inch(3.5)), height=inch(1), plan_symbol="register",
                 ventilation_terminal=True, product_ref="PROD-AIR-FLOOR-GRILLE-2X10",
                 static_loss_pa_at_cfm=_FLOOR_GRILLE_PA,
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(10), height=inch(2.25), depth=inch(5),
                                   part="2 1/4x10x4 stamped 90-degree boot"),
                 source=f"Face 12 x 3 1/2in outside (Ferguson 412-AH listing, 2026-10-31); "
                        f"the boot's 5in height is unpublished, an estimate. Loss: derived K 5 "
                        f"(erv_static_budget §5). {_NOTE} §3.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # RM-S-PLANT is held at 75 F / 70% RH and slightly negative (notes/plant_room.md): its
    # extract is RH-controlled. Since 2026-11-11 the run is a rectangular stack up W-S-PS1,
    # so the 4in 24 VAC damper sits in the stack boot's 4in collar behind the valve,
    # reached by pulling the valve.
    RegisterType(tag="REG-T-ERV-PLANT-EXH",
                 face_style="disc_valve",
                 name="Plant-room extract disc valve, 100 mm, RH-controlled 4in damper at "
                      "the plenum",
                 footprint=(inch(5.0625), inch(1.75)), height=inch(5.0625),
                 plan_symbol="register", ventilation_terminal=True,
                 product_ref="PROD-AIR-DISC-VALVE-100",
                 parts=(ProductPart(role="fitting", product_ref="PROD-AIR-DAMPER-4-24V"),),
                 static_loss_pa_at_cfm=_PLANT_PA, neck=_VALVE_NECK,
                 source=f"notes/plant_room.md — dedicated dampered extract off EQ-B-ERV; "
                        f"damper PROD-AIR-DAMPER-4-24V in the boot collar behind the valve. A stainless "
                        f"valve was looked for and not found retail; the powder-coated steel "
                        f"valve is cleaned yearly. {_NOTE} §7.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    RegisterType(tag="REG-T-HP-SIDE-1206",
                 face_opening=(inch(12), inch(6)),
                 face_style="rectangular_grille", double_deflection=True,
                 name="Heat-pump supply, 12x6 aluminium double-deflection sidewall with OBD",
                 footprint=(inch(13.75), inch(1)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-SIDEWALL-DD-OBD", neck=_OBD_NECK_1206,
                 source=f"TRUaire A220VO 12X06 face 13 3/4 x 7 3/4in. Double deflection: the "
                        f"vertical blades aim, the horizontal set the spread. {_NOTE} §4.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    RegisterType(tag="REG-T-HP-STAIR-SIDE",
                 face_opening=(inch(12), inch(6)),
                 face_style="rectangular_grille", double_deflection=True,
                 name="Stair supply A220VO 12x6 with TH-HP-STAIR-BOX-01 and 4in branch",
                 footprint=(inch(13.75), inch(1)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-SIDEWALL-DD-OBD",
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(12), height=inch(6), depth=inch(4),
                     part="TH-HP-STAIR-BOX-01 12x6x4 register box with centred 4in back collar",
                     product_ref="PROD-AIR-STAIR-REGISTER-BOX",
                     inlet=TerminalNeckInlet(position=(inch(0), inch(4), inch(0)),
                         section="round", width=inch(4), height=inch(4), normal=(0, 1))),
                 source="50 cfm through 4in galvanized branch to the trunk. "
                        "notes/stair_supply_connection.md; grille retains OBD and westward throw.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    RegisterType(tag="REG-T-HP-STUDY-SIDE",
                 face_opening=(inch(8), inch(6)),
                 face_style="rectangular_grille", double_deflection=True,
                 name="Study heat-pump supply, 8x6 aluminium double-deflection sidewall with "
                      "OBD",
                 footprint=(inch(9.75), inch(1)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-SIDEWALL-DD-OBD", neck=_OBD_NECK_0806,
                 source=f"TRUaire A220VO 08X06, face 9 3/4 x 7 3/4in; notes/system1_study_"
                        f"supply.md keeps the Titus 300R 8x6 throw basis. {_NOTE} §4.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    RegisterType(tag="REG-T-HP-FLOOR-0612",
                 face_opening=(inch(12), inch(6)),
                 face_style="rectangular_grille",
                 name="Heat-pump supply, 6x12 aluminium floor register with damper",
                 footprint=(inch(13.375), inch(7.375)), height=inch(1), plan_symbol="register",
                 product_ref="PROD-AIR-FLOOR-REG-6X12",
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(12), height=inch(6), depth=inch(2),
                                   part="multi-shutter damper below the flange"),
                 source=f"Face 7 3/8 x 13 3/8in and 2in damper depth are planning figures, "
                        f"not published at this size. {_NOTE} §4.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    # RM-S-PLANT's supply (2026-11-12): A220V 12x6 (no OBD: the take-off's locked collar
    # damper balances, the motorised one isolates) on the stock 6x12x6 end boot, with the 6" 24 VAC
    # RH damper in the boot's collar behind the grille, reached by pulling it, as at
    # REG-T-ERV-PLANT-EXH. One allowance buys the grille, the damper and the labour.
    RegisterType(tag="REG-T-HP-PLANT-SIDE",
                 face_opening=(inch(12), inch(6)),
                 face_style="rectangular_grille", double_deflection=True,
                 name="Plant supply, A220V 12x6 aluminium double-deflection sidewall with "
                      "RH-interlocked 6in damper",
                 footprint=(inch(13.75), inch(1)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-PLANT-GRILLE-12X6",
                 parts=(ProductPart(role="fitting", product_ref="PROD-AIR-DAMPER-6-24V"),),
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(12), height=inch(6), depth=inch(2.6875),
                                   part="register box on the stock 6x12x6 end boot"),
                 source=f"75 cfm, RH interlocked, throws west. A220V 12X06 face 13 3/4 x 7 3/4in. "
                        f"{_NOTE} §4, §7; notes/plant_supply_connection.md.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    # The hall filter, 455 cfm (750 - ERV 100 - suite 80 - BED3 80 - east room 35). Stock
    # 12x24x1 MERV 13 (owner, 2026-11-12): 288 in2, 228 fpm. 14x25x1 is the larger stock size
    # but cannot stand here: the soffit's north end and the FS-ATTIC joists leave 12.5" clear in
    # y (13 11/16" bay less SF-S-DUCT's 2 1/8" end), so 12" is the ceiling on the short side.
    # The neck is the 1" rack plus the shop filter box up to DU-S-HP-RET's underside (15 1/8"):
    # a 24x12 duct does not fit its 14 1/4" bay, so the box is a boot, not a drawn run.
    RegisterType(tag="REG-T-HP-RET-FILTER",
                 face_opening=(inch(24), inch(12)),
                 face_style="rectangular_grille",
                 name="Heat-pump return, 24x12 aluminium hinged filter-back grille",
                 footprint=(inch(26.625), inch(14.625)), height=inch(1),
                 plan_symbol="register", product_ref="PROD-AIR-FILTER-RETURN-12X24",
                 filter_nominal_size="12x24x1", filter_merv=13, service_face="bottom",
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(24), height=inch(12), depth=inch(15.125),
                                   part="1in filter rack and shop filter box"),
                 source=f"Face estimated off H&C 673 (+2 5/8in); 24 x 12in duct size, 288 in2, "
                        f"228 fpm at 455 cfm. {_NOTE} §5.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # RM-S-SUITE's ducted return (2026-11-09): its own filter, since it lands in the plenum
    # behind REG-T-HP-RET-FILTER's. 12x12x1 is stocked; a locked balancing damper rides at the
    # boot, reached through the hinged face.
    RegisterType(tag="REG-T-HP-RET-FILTER-1212",
                 face_opening=(inch(12), inch(12)),
                 face_style="rectangular_grille",
                 name="Heat-pump return, 12x12 aluminium hinged filter-back grille",
                 footprint=(inch(14.625), inch(14.625)), height=inch(1),
                 plan_symbol="register", product_ref="PROD-AIR-FILTER-RETURN-12X12",
                 filter_nominal_size="12x12x1", filter_merv=13, service_face="bottom",
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(12), height=inch(12), depth=inch(1.75),
                                   part="1in filter rack"),
                 source=f"Face estimated as the 24x12's (+2 5/8in); 144 in2, 80 fpm at 80 cfm. "
                        f"{_NOTE} §5.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # RM-A-EAST-UNFIN's return (2026-11-12): the same stock 12x12x1 on the south face of
    # EQ-S-ERV-MIX, so the hinged face opens to the front, not the bottom. A locked balancing
    # damper sits in the stub, set to 35 cfm. No neck: the plenum is the host.
    RegisterType(tag="REG-T-HP-RET-FILTER-1212-WALL",
                 face_opening=(inch(12), inch(12)),
                 face_style="rectangular_grille",
                 name="Heat-pump return, 12x12 aluminium hinged filter-back grille, wall face",
                 footprint=(inch(14.625), inch(1)), height=inch(14.625),
                 plan_symbol="register", product_ref="PROD-AIR-FILTER-RETURN-12X12",
                 filter_nominal_size="12x12x1", filter_merv=13, service_face="front",
                 source=f"The 12x12's face turned to a wall; 144 in2, 35 fpm at 35 cfm. {_NOTE} §5.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    RegisterType(tag="REG-T-TRANSFER-MUD-1210",
                 face_opening=(inch(12), inch(10)),
                 face_style="rectangular_grille",
                 name="Transfer grille, 12x10 aluminium, over the stair-side panel cutout",
                 footprint=(inch(13.75), inch(1)), height=inch(11.75), plan_symbol="register",
                 product_ref="PROD-AIR-RETURN-GRILLE-12X10",
                 source=f"One stair-side grille over a 12x10 cut in the painted 1/2in MDO; "
                        f"open coat nook behind. No sleeve. "
                        f"Face estimated at +1 3/4in. {_NOTE} §6.",
                 ports=()),
    # EQ-B-WH's two grilles (2026-11-09): indoor register approved for HVAC (AP22654
    # p.15); 12in fits W-B-HALL-W's 12 1/2in bay. Same grille as the transfer pair, one face.
    RegisterType(tag="REG-T-HPWH-STAIR-1210",
                 face_opening=(inch(12), inch(10)),
                 face_style="rectangular_grille",
                 name="HPWH stair grille, 12x10 aluminium return grille on an 8in boot",
                 footprint=(inch(13.75), inch(1)), height=inch(11.75), plan_symbol="register",
                 product_ref="PROD-AIR-RETURN-GRILLE-12X10",
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(12), height=inch(10), depth=inch(3.5),
                                   part="12x10 shallow boot with projecting rear 8in collar",
                                   inlet=TerminalNeckInlet(
                                       position=(inch(0), inch(6.75), inch(0)),
                                       section="round", width=inch(8), height=inch(8),
                                       normal=(0.0, 1.0))),
                 source=f"Face estimated at +1 3/4in. 120 in2 gross. Boot box 3 1/2in deep "
                        f"with an 8in rear collar reaching 6 3/4in behind the grille; "
                        f"shop design envelope, not a manufacturer submittal. {_NOTE} §6.",
                 ports=()),
    # D-S-BATH1's sealed door (2026-11-03): one grille per face of W-S-BD-N's west bay,
    # offset in height on a lined bay. The bath face's only clear patch is 7 1/4 x 7 1/8 in.
    # between the SEKTION rail backing and the top plate, so 6x6 is the size.
    RegisterType(tag="REG-T-TRANSFER-0606",
                 face_opening=(inch(6), inch(6)),
                 face_style="rectangular_grille",
                 name="Transfer grille, 6x6 aluminium return grille, one face of a lined bay",
                 footprint=(inch(7.75), inch(0.75)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-RETURN-GRILLE-6X6",
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(6), height=inch(6), depth=inch(1.5),
                                   part="6x6 sheet-metal collar into the lined bay"),
                 source=f"Face estimated at +1 3/4in. ~24 in2 effective (steel 170 6x6 listing), "
                        f"against 10.8 in2 for 20 cfm at 3 Pa. {_NOTE} §6.",
                 ports=()),
)

# 8in hoods, 1/4in screen. Curves are RenewAire's FA8 chart end points (0.34 in. w.g.
# intake and 0.215 exhaust at 400 cfm) scaled as Q^2. No backdraft damper on either: Broan
# forbids one on the discharge (AI manual 2.4, it freezes; the ERV's motorized port dampers
# close it), so the BD8 was dropped 2026-11-05 (C4 E3). A 12 x 12 x 12 box is kept as the
# clearance envelope: the FA8's plate is unpublished and the FML8's is 9 x 9.
# The dedicated hood symbol estimates the folded shell from RenewAire's product photo.
AIR_HOOD_TYPES = (
    EquipmentType(tag="EQ-T-ERV-HOOD-8",
                  name="Exterior intake hood, 8in round, 1/4in screen, no damper",
                  footprint=(inch(12), inch(12)), height=inch(12),
                  plan_symbol="renewaire-fa8-wall-hood",
                  duct_ports=1, port_diameter=inch(8), product_ref="PROD-AIR-HOOD-8",
                  static_loss_pa_at_cfm=((100.0, 5.3), (150.0, 11.9), (210.0, 23.3),
                                         (250.0, 33.1), (400.0, 84.7)),
                  ports=(_port("duct", Service.OUTDOOR_AIR, inch(6)),),
                  source=f"RenewAire FA8-P, supply-mode chart. {_NOTE} §8."),
    EquipmentType(tag="EQ-T-ERV-HOOD-8-EXH",
                  name="Exterior discharge hood, 8in round, 1/4in screen, no damper",
                  footprint=(inch(12), inch(12)), height=inch(12),
                  plan_symbol="renewaire-fa8-wall-hood",
                  duct_ports=1, port_diameter=inch(8), product_ref="PROD-AIR-HOOD-8",
                  static_loss_pa_at_cfm=((100.0, 3.3), (150.0, 7.5), (210.0, 14.8),
                                         (250.0, 20.9), (400.0, 53.6)),
                  ports=(_port("duct", Service.EXHAUST_AIR, inch(6)),),
                  source=f"RenewAire FA8-P exhaust-mode chart. {_NOTE} §8."),
)

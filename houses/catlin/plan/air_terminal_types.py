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
# The VRF drawing dimensions the disc. The installed relief shown in the mesh is
# an estimate for a valve set open, inside the 1 3/4" fit envelope (re-read 2026-11-21:
# AM-VR H 1 3/4" / H1 2 1/16" gives a 5/16" rim; LVS 125 L1 9 mm, +5 mm open setting; plus
# the formed disc's own dome, about 3/8"). notes/air_distribution_products.md.
_AM100_DISC = inch(2.9375)
_AM100_FACE_PROJECTION = inch(1.0)
_LVS125_DISC = inch(3.94)  # estimated from the proportions of the LVS 125 drawing
_LVS125_FACE_PROJECTION = inch(0.9)


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
# A floor grille on a boot publishes no curve: the derived K 5 of the note's §5.
_FLOOR_GRILLE_PA = ((10.0, 1.0), (20.0, 4.0), (30.0, 9.0))
# Same conservative K=5 allowance as the floor boot; no measured curve for this box.
_SUITEBATH_BOOT_REFERENCE_CFM = 20.0
_SUITEBATH_BOOT_REFERENCE_LOSS_PA = 4.0

_VALVE_NECK = TerminalNeck(section="round", width=inch(4), height=inch(4), depth=inch(2.9375),
                           part="100 mm valve collar in a 4in snap-lock collar")
_OBD_NECK_1206 = TerminalNeck(section="rectangular",
                              width=inch(12), height=inch(6), depth=inch(2.6875),
                              part="opposed-blade damper and register box",
                              separate_boot=True)
_OBD_NECK_0806 = TerminalNeck(section="rectangular",
                              width=inch(8), height=inch(6), depth=inch(2.6875),
                              part="opposed-blade damper and register box",
                              separate_boot=True)

AIR_REGISTER_TYPES = (
    RegisterType(tag="REG-T-ERV-VALVE-SUP",
                 face_style="disc_valve",
                 face_projection=_AM100_FACE_PROJECTION, disc_diameter=_AM100_DISC,
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
                 face_projection=_LVS125_FACE_PROJECTION, disc_diameter=_LVS125_DISC,
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
                 face_projection=_AM100_FACE_PROJECTION, disc_diameter=_AM100_DISC,
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
                 face_projection=_AM100_FACE_PROJECTION, disc_diameter=_AM100_DISC,
                 name="ERV extract disc valve, 100 mm, white steel, ceiling collar",
                 footprint=(inch(5.0625), inch(5.0625)), height=inch(1), plan_symbol="register",
                 ventilation_terminal=True, product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=_VALVE_PA, neck=_VALVE_NECK,
                 source=f"Extract pattern of the supply valve; pull it from the collar to "
                        f"clean, lock ring holds the setting. {_NOTE} §2.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # Use the AM 100's overall height as the conservative wall projection for
    # clearance checks. The modeled trim uses the installed relief above.
    RegisterType(tag="REG-T-ERV-VALVE-EXH-WALL",
                 face_style="disc_valve",
                 face_projection=_AM100_FACE_PROJECTION, disc_diameter=_AM100_DISC,
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
                 face_projection=_AM100_FACE_PROJECTION, disc_diameter=_AM100_DISC,
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
                     product_ref="PROD-AIR-SUITEBATH-BOOT", entry="bottom"),
                 parts=(ProductPart(role="fitting", product_ref="PROD-AIR-SUITEBATH-BOOT"),),
                 source="notes/suitebath_extract.md: 26ga sealed box, 4in bottom inlet, "
                        "100 mm front collar. Valve curve plus estimated K=5 boot loss; "
                        "balance to 20 cfm on commissioning.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # The same box turned over: a stack head for a riser dropping in a wall (REG-M-RET-STUDY).
    RegisterType(tag="REG-T-ERV-STACK-TOP-WALL",
                 face_style="disc_valve",
                 face_projection=_AM100_FACE_PROJECTION, disc_diameter=_AM100_DISC,
                 name="100 mm extract valve on TH-ERV-STACK-TOP-BOOT-01",
                 footprint=(inch(5.0625), inch(1.75)), height=inch(5.0625),
                 plan_symbol="register", ventilation_terminal=True,
                 product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=tuple(
                     (cfm, pa + _SUITEBATH_BOOT_REFERENCE_LOSS_PA
                      * (cfm / _SUITEBATH_BOOT_REFERENCE_CFM) ** 2) for cfm, pa in _VALVE_PA),
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(4), height=inch(8), depth=inch(5.25),
                     part="TH-ERV-STACK-TOP-BOOT-01 4x8x5-1/4in top-entry valve box",
                     product_ref="PROD-AIR-STACK-TOP-BOOT", entry="top"),
                 parts=(ProductPart(role="fitting", product_ref="PROD-AIR-STACK-TOP-BOOT"),),
                 source="TH-ERV-SUITEBATH-BOOT-01 inverted (notes/suitebath_extract.md): valve "
                        "curve plus the same estimated K=5 box loss.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # The bottom-entry box 9in deep: the riser stands in the 2x6 leaf behind the 2x4 furring.
    RegisterType(tag="REG-T-ERV-STUBATH-WALL",
                 face_style="disc_valve",
                 face_projection=_AM100_FACE_PROJECTION, disc_diameter=_AM100_DISC,
                 name="100 mm extract valve on TH-ERV-STUBATH-BOOT-01",
                 footprint=(inch(5.0625), inch(1.75)), height=inch(5.0625),
                 plan_symbol="register", ventilation_terminal=True,
                 product_ref="PROD-AIR-DISC-VALVE-100",
                 static_loss_pa_at_cfm=tuple(
                     (cfm, pa + _SUITEBATH_BOOT_REFERENCE_LOSS_PA
                      * (cfm / _SUITEBATH_BOOT_REFERENCE_CFM) ** 2) for cfm, pa in _VALVE_PA),
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(4), height=inch(7), depth=inch(9),
                     part="TH-ERV-STUBATH-BOOT-01 4x7x9in bottom-entry valve box",
                     product_ref="PROD-AIR-STUBATH-BOOT", entry="bottom"),
                 parts=(ProductPart(role="fitting", product_ref="PROD-AIR-STUBATH-BOOT"),),
                 source="TH-ERV-SUITEBATH-BOOT-01 at 9in deep, 7in tall (notes/suitebath_extract.md): "
                        "valve curve plus the same estimated K=5 box loss.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    # A disc valve cannot sit in a floor. Long side along the joist bay.
    RegisterType(tag="REG-T-ERV-EXH-FLOOR",
                 face_opening=(inch(10), inch(2.25)),
                 face_style="cast_scroll_grille", face_projection=inch(0.1875),
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
    RegisterType(tag="REG-T-HP-SIDE-1206",
                 face_opening=(inch(12), inch(6)),
                 face_style="rectangular_grille", double_deflection=True,
                 name="Heat-pump supply, 12x6 aluminium double-deflection sidewall with OBD",
                 footprint=(inch(13.75), inch(1)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-SIDEWALL-DD-OBD", neck=_OBD_NECK_1206,
                 source=f"TRUaire A220VO 12X06 face 13 3/4 x 7 3/4in. Double deflection: the "
                        f"vertical blades aim, the horizontal set the spread. {_NOTE} §4.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    # RM-S-SUITE's supply (owner, 2026-11-19): a fixed laser-cut face throws straight, no aim;
    # a jet this near the ceiling stays attached to it. The louver fits inside the 6in box.
    RegisterType(tag="REG-T-HP-SUITE-CHEVRON",
                 face_opening=(inch(12), inch(6)),
                 face_style="laser_cut_chevron", face_projection=inch(0.1875),
                 face_material_ref="reggio-sun-gold",
                 name="Suite heat-pump supply, Reggio Chevron 6x12 Sun Gold sidewall, louver "
                      "damper",
                 footprint=(inch(14), inch(1)), height=inch(8), plan_symbol="register",
                 product_ref="PROD-AIR-CHEVRON-1206-SG", neck=_OBD_NECK_1206,
                 parts=(ProductPart(role="fitting", product_ref="PROD-AIR-LOUVER-814"),),
                 source=f"Reggio Chevron 6x12 duct, 8 x 14in overall; free area unpublished "
                        f"(need >= 29 in2). 814-BL louver 2 5/16in deep. {_NOTE} §4.",
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
                                   part="multi-shutter damper below the flange",
                                   separate_boot=True),
                 source=f"Face 7 3/8 x 13 3/8in and 2in damper depth are planning figures, "
                        f"not published at this size. {_NOTE} §4.",
                 ports=(_port("supply", Service.SUPPLY_AIR),)),
    # The hall filter, 455 cfm (750 - ERV 100 - suite 80 - BED3 80 - east room 35). Stock
    # 12x24x1 MERV 13 (owner, 2026-11-12): 288 in2, 228 fpm. 14x25x1 is the larger stock size
    # but cannot stand here: the soffit's north end and the FS-ATTIC joists leave 12.5" clear in
    # y (13 11/16" bay less SF-S-DUCT's 2 1/8" end), so 12" is the ceiling on the short side.
    # The neck is the 1" rack plus the shop filter box, 25 1/8" up to DU-S-HP-RET's top in the
    # FS-ATTIC bay; the 12x10 run enters its east face, top-aligned (a side inlet, not a drop).
    RegisterType(tag="REG-T-HP-RET-FILTER",
                 face_opening=(inch(24), inch(12)),
                 face_style="rectangular_grille",
                 name="Heat-pump return, 24x12 aluminium hinged filter-back grille",
                 footprint=(inch(26.625), inch(14.625)), height=inch(1),
                 plan_symbol="register", product_ref="PROD-AIR-FILTER-RETURN-12X24",
                 filter_nominal_size="12x24x1", filter_merv=13, service_face="bottom",
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(24), height=inch(12), depth=inch(25.125),
                                   part="1in filter rack and shop filter box, 12x10 east inlet",
                                   inlet=TerminalNeckInlet(
                                       position=(inch(12), inch(0.5), inch(20.125)),
                                       section="rectangular", width=inch(12), height=inch(10),
                                       normal=(1.0, 0.0))),
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
    # RM-S-PLANT's transfer pair (2026-11-12): two lined 10x6 sleeves through W-S-C1, high and
    # low in one bay. The plant face carries the damper, the study face a plain grille. ~42 in2
    # free each, ~13 cfm wide open by buoyancy at 5 F (notes/plant_room_moisture_budget.md §4).
    RegisterType(tag="REG-T-XFER-PLANT-1006",
                 face_opening=(inch(10), inch(6)),
                 face_style="rectangular_grille",
                 name="Plant transfer, 10x6 steel return grille with OBD on a lined sleeve",
                 footprint=(inch(11.75), inch(0.75)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-RETURN-GRILLE-10X6-OBD",
                 parts=(ProductPart(role="fitting", product_ref="PROD-AIR-XFER-SLEEVE-10X6"),),
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(10), height=inch(6), depth=inch(3.625),
                                   part="10x6 lined sleeve, flange taped to the membrane"),
                 source=f"Face estimated at +1 3/4in. {_NOTE} §6; notes/plant_room.md.",
                 ports=(_port("return", Service.RETURN_AIR),)),
    RegisterType(tag="REG-T-XFER-STUDY-1006",
                 face_opening=(inch(10), inch(6)),
                 face_style="rectangular_grille",
                 name="Plant transfer, 10x6 steel return grille, Study 2 face of the sleeve",
                 footprint=(inch(11.75), inch(0.75)), height=inch(7.75), plan_symbol="register",
                 product_ref="PROD-AIR-RETURN-GRILLE-10X6",
                 neck=TerminalNeck(section="rectangular",
                                   width=inch(10), height=inch(6), depth=inch(3.625),
                                   part="the plant face's sleeve, from the study side"),
                 source=f"Face estimated at +1 3/4in. {_NOTE} §6.",
                 ports=(_port("return", Service.RETURN_AIR),)),
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

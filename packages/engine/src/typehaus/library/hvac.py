"""Reusable ventilation duct, terminal, and accessory catalog."""

from __future__ import annotations

from typehaus import DuctProductType, EquipmentType, RegisterType, Service, ServicePort
from typehaus.quantities import ft, inch

_SOURCE = (
    "Reusable commodity ventilation component; dimensions and pressure data are technical "
    "preset values."
)


def _port(tag: str, service: Service, z=None) -> ServicePort:
    return ServicePort(tag=tag, service=service, position=(ft(0), ft(0), ft(0) if z is None else z))


def _register(tag: str, name: str, footprint, height, ports, **facts) -> RegisterType:
    return RegisterType(
        tag=tag,
        name=name,
        footprint=footprint,
        height=height,
        plan_symbol="register",
        ports=ports,
        source=_SOURCE,
        **facts,
    )


ALL_REGISTER_TYPES = (
    _register(
        "REG-T-ERV-SUP",
        "ERV fresh-air supply diffuser, 4in round collar",
        (inch(7), inch(7)),
        inch(1),
        (_port("supply", Service.SUPPLY_AIR),),
        ventilation_terminal=True,
        static_loss_pa_at_cfm=((10.0, 1.0), (20.0, 4.0), (30.0, 9.0)),
    ),
    _register(
        "REG-T-ERV-EXH",
        "ERV stale-air extract diffuser, 4in round collar",
        (inch(7), inch(7)),
        inch(1),
        (_port("return", Service.RETURN_AIR),),
        ventilation_terminal=True,
        static_loss_pa_at_cfm=((10.0, 1.0), (20.0, 4.0), (30.0, 9.0)),
    ),
    _register(
        "REG-T-ERV-EXH-WALL",
        "ERV stale-air extract diffuser, 4in round collar, sidewall",
        (inch(7), inch(1)),
        inch(7),
        (_port("return", Service.RETURN_AIR),),
        ventilation_terminal=True,
        static_loss_pa_at_cfm=((10.0, 1.0), (20.0, 4.0), (30.0, 9.0)),
    ),
    _register(
        "REG-T-ERV-SAUNA-SUP",
        "Sauna fresh-air supply, 4x4, adjustable damper",
        (inch(4), inch(4)),
        inch(1),
        (_port("supply", Service.SUPPLY_AIR),),
        ventilation_terminal=True,
        static_loss_pa_at_cfm=((10.0, 1.6), (20.0, 6.5), (30.0, 14.6)),
    ),
    _register(
        "REG-T-ERV-SAUNA-EXH",
        "Sauna stale-air extract, 4x4, adjustable damper",
        (inch(4), inch(4)),
        inch(1),
        (_port("return", Service.RETURN_AIR),),
        ventilation_terminal=True,
        static_loss_pa_at_cfm=((10.0, 1.6), (20.0, 6.5), (30.0, 14.6)),
    ),
    _register(
        "REG-T-HP-SUP",
        "Heat-pump supply register, 12x6",
        (inch(12), inch(6)),
        inch(1),
        (_port("supply", Service.SUPPLY_AIR),),
    ),
    _register(
        "REG-T-HP-SUP-SIDE",
        "Heat-pump supply register, 12x6, sidewall double-deflection",
        (inch(12), inch(1)),
        inch(6),
        (_port("supply", Service.SUPPLY_AIR),),
    ),
    _register(
        "REG-T-TRANSFER-1210",
        "Passive transfer louver, 12x10 face (10x8 free opening)",
        (inch(12), inch(1)),
        inch(10),
        (),
    ),
)

ALL_DUCT_PRODUCT_TYPES = (
    DuctProductType(
        tag="DUCT-T-GALV-4",
        name="4in galvanized snap-lock round duct, 26 ga",
        material="galvanized",
        nominal_diameter=inch(4),
        bore_diameter=inch(4),
        roughness_m=0.0000914,
        max_cfm=50.0,
        bend_equivalent_length=inch(30),
        source=_SOURCE,
    ),
    DuctProductType(
        tag="DUCT-T-SEMIRIGID-4",
        name="4in semi-rigid aluminium duct",
        material="semi_rigid",
        nominal_diameter=inch(4),
        bore_diameter=inch(3.8),
        roughness_m=0.0009144,
        max_cfm=40.0,
        bend_equivalent_length=inch(42),
        source=_SOURCE,
    ),
    DuctProductType(
        tag="DUCT-T-GALV-6",
        name="6in galvanized round duct, 26 ga",
        material="galvanized",
        nominal_diameter=inch(6),
        bore_diameter=inch(6),
        roughness_m=0.0000914,
        max_cfm=250.0,
        bend_equivalent_length=inch(54),
        source=_SOURCE,
    ),
    DuctProductType(
        tag="DUCT-T-GALV-8",
        name="8in galvanized round duct, 26 ga",
        material="galvanized",
        nominal_diameter=inch(8),
        bore_diameter=inch(8),
        roughness_m=0.0000914,
        max_cfm=440.0,
        bend_equivalent_length=inch(78),
        source=_SOURCE,
    ),
    DuctProductType(
        tag="DUCT-T-FLEX-6",
        name="6in insulated flexible duct, R-8 jacket",
        material="flex",
        nominal_diameter=inch(6),
        bore_diameter=inch(6),
        roughness_m=0.0009144,
        max_cfm=250.0,
        bend_equivalent_length=inch(84),
        source=_SOURCE,
    ),
)


#: **The shared plenums state a COUNT and no layout, and that is deliberate.**
#: ``EquipmentType.collars()`` reads an EXACT port at ``port_diameter`` as a dimensioned
#: branch collar, and ``mep.erv_manifold_ports`` then grades each radial against the collar
#: it lands on rather than against a tally. Nothing in this file may claim that: a collar
#: layout is a SHOP DRAWING for one fabricated box, and a reusable catalog part has no shop
#: drawing behind it. A house that has one authors the dimensioned type locally — catlin
#: does, in ``plan/mep_erv_types.py`` — and inherits the positional verdict by doing so.
def _equipment(
    tag: str, name: str, footprint, height, port: ServicePort, duct_ports: int
) -> EquipmentType:
    return EquipmentType(
        tag=tag,
        name=name,
        footprint=footprint,
        height=height,
        plan_symbol="erv",
        ports=(port,),
        source=_SOURCE,
        duct_ports=duct_ports,
        port_diameter=inch(4),
        static_loss_pa_at_cfm=((60.0, 0.5), (120.0, 1.8), (210.0, 5.5)),
    )


ALL_VENTILATION_EQUIPMENT_TYPES = (
    _equipment(
        "EQ-T-ERV-MANIFOLD-6",
        "Fabricated air plenum, 8in inlet, 6 x 4in dampered ports",
        (inch(24), inch(8)),
        inch(8),
        _port("trunk", Service.SUPPLY_AIR, inch(4)),
        6,
    ),
    _equipment(
        "EQ-T-ERV-MANIFOLD-10",
        "Fabricated air plenum, 8in inlet, 10 x 4in dampered ports",
        (inch(34), inch(8)),
        inch(8),
        _port("trunk", Service.RETURN_AIR, inch(4)),
        10,
    ),
    _equipment(
        "EQ-T-ERV-MANIFOLD-6-EXH",
        "Fabricated air plenum, 8in inlet, 6 x 4in dampered ports, extract",
        (inch(24), inch(8)),
        inch(8),
        _port("trunk", Service.RETURN_AIR, inch(4)),
        6,
    ),
    EquipmentType(
        tag="EQ-T-ERV-HOOD-6",
        name="Exterior ventilation hood, 6in round, bird screen + backdraft damper",
        footprint=(inch(12), inch(12)),
        height=inch(12),
        plan_symbol="erv",
        duct_ports=1,
        port_diameter=inch(6),
        ports=(_port("duct", Service.OUTDOOR_AIR, inch(6)),),
        source=_SOURCE,
    ),
    EquipmentType(
        tag="EQ-T-ERV-HOOD-6-EXH",
        name="Exterior ventilation hood, 6in round, discharge, bird screen + backdraft damper",
        footprint=(inch(12), inch(12)),
        height=inch(12),
        plan_symbol="erv",
        duct_ports=1,
        port_diameter=inch(6),
        ports=(_port("duct", Service.EXHAUST_AIR, inch(6)),),
        source=_SOURCE,
    ),
)

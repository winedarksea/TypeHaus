"""Ordinary electrical-device catalog shared by house plans."""

from __future__ import annotations

from typehaus import ElectricalDeviceType, Service, ServicePort
from typehaus.quantities import ft, inch

_P120 = (ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),)
_P240 = (ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),)
_SOURCE = (
    "Commodity electrical device class; final selection must meet the governing electrical code."
)


def _device(tag: str, name: str, footprint, height, ports, **facts) -> ElectricalDeviceType:
    return ElectricalDeviceType(
        tag=tag, name=name, footprint=footprint, height=height, ports=ports, source=_SOURCE, **facts
    )


ALL_ELECTRICAL_DEVICE_TYPES = (
    _device("ED-T-SWITCH", "Wall switch", (inch(4), inch(2)), inch(2), _P120),
    _device("ED-T-RECEPTACLE", "Receptacle", (inch(4), inch(2)), inch(2), _P120),
    _device(
        "ED-T-JBOX",
        "NEMA 3R weatherproof junction box",
        (inch(6), inch(6)),
        inch(4),
        _P120,
        plan_symbol="junction-box",
    ),
    _device("ED-T-RECEPTACLE-GFCI", "GFCI receptacle", (inch(4), inch(2)), inch(2), _P120),
    _device(
        "ED-T-RECEPTACLE-WR-GFCI",
        "WR GFCI receptacle, in-use cover, non-metallic gasketed box",
        (inch(4.5), inch(3)),
        inch(3),
        _P120,
        nema="5-20R",
    ),
    _device(
        "ED-T-RECEPTACLE-240",
        "240V appliance receptacle, NEMA 14-50",
        (inch(4), inch(4)),
        inch(4),
        _P240,
    ),
    _device(
        "ED-T-RECEPTACLE-520S",
        "NEMA 5-20R single receptacle, 20A",
        (inch(4), inch(2)),
        inch(2),
        _P120,
    ),
    _device(
        "ED-T-RECEPTACLE-620",
        "NEMA 5-20R/6-20R duplex kettle outlet",
        (inch(4), inch(4)),
        inch(4),
        (
            ServicePort(tag="power-120", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),
            ServicePort(tag="power-240", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),
        ),
    ),
    _device(
        "ED-T-METER",
        "Class 320 meter-main, 320A continuous, two 200A mains outdoors",
        (inch(20), inch(8)),
        inch(36),
        _P240,
        service_amps=320,
        plan_symbol="meter",
    ),
    _device(
        "ED-T-DISCONNECT-3R",
        "NEMA 3R disconnect, 240V",
        (inch(6.5), inch(3.25)),
        inch(9.5),
        _P240,
        plan_symbol="disconnect",
    ),
    _device(
        "ED-T-EV-620",
        "EV receptacle, NEMA 6-20R",
        (inch(4), inch(4)),
        inch(4),
        _P240,
        nema="6-20R",
        load_va=3840,
    ),
    _device(
        "ED-T-EV-1450",
        "EV receptacle, NEMA 14-50R",
        (inch(4), inch(4)),
        inch(4),
        _P240,
        nema="14-50R",
        load_va=9600,
    ),
    _device(
        "ED-T-RECEPTACLE-1430",
        "Dryer receptacle, NEMA 14-30R",
        (inch(4), inch(4)),
        inch(4),
        _P240,
        nema="14-30R",
        load_va=5000,
    ),
    _device(
        "ED-T-PV-JB",
        "PV junction box, NEMA 3R",
        (inch(6), inch(6)),
        inch(4),
        _P240,
        plan_symbol="junction-box",
    ),
    _device(
        "ED-T-FLOOR-STAT", "Radiant floor thermostat, 120V", (inch(4), inch(2)), inch(4), _P120
    ),
    _device(
        "ED-T-NET-ENCLOSURE",
        "Structured media enclosure, 28in (router + PoE switch + patch)",
        (inch(15), inch(4)),
        inch(28),
        (
            ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),
            ServicePort(tag="data", service=Service.DATA, position=(ft(0), ft(0), ft(0))),
        ),
        ifc_entity="IfcCommunicationsAppliance",
        ifc_predefined_type="NETWORKHUB",
    ),
    _device(
        "ED-T-AP-CEILING",
        "Wireless access point, ceiling, PoE 802.3af",
        (inch(8), inch(8)),
        inch(2),
        (ServicePort(tag="data", service=Service.DATA, position=(ft(0), ft(0), ft(0))),),
        poe_watts=15.0,
        ifc_entity="IfcCommunicationsAppliance",
        ifc_predefined_type="NETWORKAPPLIANCE",
    ),
    _device(
        "ED-T-AP-WALL",
        "Wireless access point, wall, PoE 802.3af",
        (inch(8), inch(2)),
        inch(8),
        (ServicePort(tag="data", service=Service.DATA, position=(ft(0), ft(0), ft(0))),),
        poe_watts=15.0,
        ifc_entity="IfcCommunicationsAppliance",
        ifc_predefined_type="NETWORKAPPLIANCE",
    ),
    _device(
        "ED-T-DATA-JACK",
        "Data outlet, single-gang RJ45 (Cat 6A)",
        (inch(2.75), inch(2)),
        inch(4.5),
        (ServicePort(tag="data", service=Service.DATA, position=(ft(0), ft(0), ft(0))),),
        ifc_entity="IfcCommunicationsAppliance",
        ifc_predefined_type="NETWORKAPPLIANCE",
    ),
    _device(
        "ED-T-AP-OUTDOOR",
        "Wireless access point, outdoor wet-rated, PoE 802.3af",
        (inch(9), inch(9)),
        inch(3),
        (ServicePort(tag="data", service=Service.DATA, position=(ft(0), ft(0), ft(0))),),
        poe_watts=15.0,
        ifc_entity="IfcCommunicationsAppliance",
        ifc_predefined_type="NETWORKAPPLIANCE",
    ),
    _device(
        "ED-T-SWITCH-DIM",
        "Wall dimmer, 120V LED-rated",
        (inch(4), inch(2)),
        inch(2),
        _P120,
        control="dimmer",
    ),
    _device(
        "ED-T-SWITCH-TIMER",
        "Wall timer switch, smart, 120V",
        (inch(4), inch(2)),
        inch(2),
        _P120,
        control="timer",
    ),
)


# --- panelboards ---------------------------------------------------------------------------
#
# A ladder of load centres by bus rating, deliberately NOT in ALL_ELECTRICAL_DEVICE_TYPES: a
# house opts in to the one it installs (``*PANEL_TYPES`` or a single row), because a panel
# nobody placed has no business in a catalog. ``service_amps`` is the panel's OWN main —
# ``code.NEC_705_12_interconnection`` reads it before the service size, so a feeder panel
# must state it. ``bus_amps`` is stated only where it exceeds the main (a backfed bus).
_PANEL_SOURCE = ("UL 67 panelboard / load centre class (NEC 408); spaces and bus rating per "
                 "the selected product's label")


def _panel(tag: str, name: str, width, height, *, spaces: int, main: int,
           bus: int | None = None) -> ElectricalDeviceType:
    return ElectricalDeviceType(
        tag=tag, name=name, footprint=(width, inch(4)), height=height, plan_symbol="panel",
        spaces=spaces, service_amps=main, bus_amps=bus, source=_PANEL_SOURCE,
        ports=(ServicePort(tag="service", service=Service.POWER_240,
                           position=(ft(0), ft(0), ft(0))),))


PANEL_TYPES = (
    _panel("ED-T-PANEL-100A", "100A load centre, 20 spaces", inch(14), ft(2),
           spaces=20, main=100),
    _panel("ED-T-PANEL-200A", "200A main, 200A bus, 20 spaces", inch(16), ft(2, 6),
           spaces=20, main=200, bus=200),
    _panel("ED-T-PANEL-225A", "225A bus, 200A main, 54 spaces", inch(20), ft(3),
           spaces=54, main=200, bus=225),
)

_PANEL_BY_TAG = {t.tag: t for t in PANEL_TYPES}


def panel_type(row: str, /, **update) -> ElectricalDeviceType:
    """The library panel row ``row``, with ``update`` (a house's own tag, name, ports)
    applied — keyword arguments because the editable dialect has no dict or ``model_copy``."""
    return _PANEL_BY_TAG[row].model_copy(update=update)

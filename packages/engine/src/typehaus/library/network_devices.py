"""Provisional UniFi references for ceiling, wall and sheltered porch APs."""

from typehaus import ElectricalDeviceType, Service, ServicePort
from typehaus.model import ModelRepresentation
from typehaus.quantities import mm

U6_PRO_DIAMETER = mm(197)
U6_PRO_THICKNESS = mm(35)
U6_PRO_SOURCE = (
    "Provisional geometry reference: Ubiquiti UniFi U6 Pro (U6-Pro), "
    "https://techspecs.ui.com/unifi/wifi/u6-pro (read 2026-11-16): "
    "diameter 197 x 35 mm, ceiling/wall mount, polycarbonate, SUS304 mount, "
    "IP54, -30..60 C, 13 W maximum. Retain 15 W per AP as a conservative PoE "
    "design allowance pending final radio selection. Porch use assumes a sheltered "
    "soffit; IP54 is not a general exposed wet-location specification. "
    "Profile/ring proportions approximated from manufacturer images."
)


def _access_point_type(tag: str, mounting: str, *, wall: bool = False) -> ElectricalDeviceType:
    return ElectricalDeviceType(
        tag=tag, name=f"Ubiquiti UniFi U6 Pro reference, {mounting}, PoE",
        footprint=(U6_PRO_DIAMETER, U6_PRO_THICKNESS if wall else U6_PRO_DIAMETER),
        height=U6_PRO_DIAMETER if wall else U6_PRO_THICKNESS,
        source=U6_PRO_SOURCE,
        ports=(ServicePort(tag="data", service=Service.DATA,
                           position=(mm(0), mm(0), mm(0))),),
        poe_watts=15.0,
        ifc_entity="IfcCommunicationsAppliance", ifc_predefined_type="NETWORKAPPLIANCE",
        model_representation=ModelRepresentation(
            symbol="unifi-u6-pro-wall" if wall else "unifi-u6-pro-ceiling"),
    )


ACCESS_POINT_DEVICE_TYPES = (
    _access_point_type("ED-T-AP-CEILING", "ceiling"),
    _access_point_type("ED-T-AP-WALL", "wall", wall=True),
    _access_point_type("ED-T-AP-OUTDOOR", "sheltered porch ceiling"),
)

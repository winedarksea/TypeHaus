"""Installation setout in each product's local frame (+y toward its back).

These are chosen wall connection stations, not the basin outlet inside the trap. Cabinet
chases and cut-to-fit trap tubes connect the purchased basin to these installation points.
"""

from typehaus.model import PortCertainty, Service, ServicePort, inch

TRAP_STUB_AFF_IN = 20.0
SUPPLY_STUB_AFF_IN = 24.0
SUPPLY_HALF_SPACING_IN = 3.0


def lav_ports(depth_in, *, base_in=0, certainty=PortCertainty.EXACT):
    return tuple(ServicePort(
        tag=f"LAV-{service.value.upper()}", service=service,
        position=(inch(x), inch(depth_in / 2), inch(z - base_in)),
        connection_size=inch(size), direction=(0, 1, 0), certainty=certainty,
        notes="House wall-stub setout; fit trap and faucet connectors within cabinet chase.",
    ) for service, x, z, size in (
        (Service.DRAIN, 0, TRAP_STUB_AFF_IN, 1.5),
        (Service.WATER_HOT, -SUPPLY_HALF_SPACING_IN, SUPPLY_STUB_AFF_IN, 0.5),
        (Service.WATER_COLD, SUPPLY_HALF_SPACING_IN, SUPPLY_STUB_AFF_IN, 0.5),
    ))

"""Rough-in stations for the water closets, showers and tubs, in each product's local frame.

+y toward the product's back, z from its body base (``resolve/mep_sleeves.expected_port_point``).
A floor bowl's base is the finished floor, so its flange is z=0. Valve inlets are an allowance:
no Delta R10000-UNBX rough-in sheet has been read, so they stay APPROXIMATE (hot on the left
facing the valve, the way the body is marked).
"""

from typehaus.model import PortCertainty, Service, ServicePort, inch

#: Finished wall to closet-flange centre, every TOTO floor bowl in the house.
WC_ROUGH_IN_IN = 12.0
VALVE_HALF_SPACING_IN = 2.0


def floor_wc_ports(depth_in: float) -> tuple[ServicePort, ...]:
    """Flange and supply stop for a floor bowl whose tank back stands at the finished wall."""
    back_in = depth_in / 2
    return (
        ServicePort(tag="WC-DRAIN", service=Service.DRAIN,
                    position=(inch(0), inch(back_in - WC_ROUGH_IN_IN), inch(0)),
                    connection_size=inch(3), direction=(0, 0, -1), certainty=PortCertainty.EXACT,
                    notes='Closet flange at the finished floor, the 12" published rough-in off '
                          "the wall the tank back stands at."),
        ServicePort(tag="WC-WATER_COLD", service=Service.WATER_COLD,
                    position=(inch(-6), inch(back_in), inch(8)),
                    connection_size=inch(0.5), direction=(0, 1, 0),
                    notes='Angle stop allowance, 6" left of centre and 8" AFF; TOTO publishes '
                          "no inlet station for these bowls."),
    )


def valve_ports(centre_in: tuple[float, float, float], wall: tuple[float, float],
                note: str) -> tuple[ServicePort, ...]:
    """Hot and cold inlets of a valve body at ``centre_in``; ``wall`` points from the room into
    the valve's wall (product frame). Hot sits on the left of a person facing the valve."""
    (x, y, z), (nx, ny) = centre_in, wall
    left = (-ny, nx)  # facing +n, left is +90 degrees from it
    return tuple(
        ServicePort(tag=tag, service=service,
                    position=(inch(x + side * left[0] * VALVE_HALF_SPACING_IN),
                              inch(y + side * left[1] * VALVE_HALF_SPACING_IN), inch(z)),
                    connection_size=inch(0.5), direction=(nx, ny, 0),
                    notes=f"R10000-UNBX valve-body allowance; no Delta rough-in sheet read; {note}")
        for tag, service, side in (("VALVE-HOT", Service.WATER_HOT, 1),
                                   ("VALVE-COLD", Service.WATER_COLD, -1)))


def floor_drain_port(x_in: float, y_in: float, z_in: float = 0.0, *,
                     size_in: float = 2.0, exact: bool = False, note: str) -> ServicePort:
    return ServicePort(tag="DRAIN", service=Service.DRAIN,
                       position=(inch(x_in), inch(y_in), inch(z_in)),
                       connection_size=inch(size_in), direction=(0, 0, -1),
                       certainty=PortCertainty.EXACT if exact else PortCertainty.APPROXIMATE,
                       notes=note)

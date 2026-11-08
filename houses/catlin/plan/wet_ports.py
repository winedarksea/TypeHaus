"""Rough-in stations for the water closets, showers and tubs, in each product's local frame.

+y toward the product's back, z from its body base (``resolve/mep_sleeves.expected_port_point``).
A floor bowl's base is the finished floor, so its flange is z=0. Valve inlets follow Delta's
R10000-UNBX sheets for side and depth; their spacing is undimensioned, so they stay APPROXIMATE.
"""

from typehaus.model import PortCertainty, Service, ServicePort, inch

#: Finished wall to closet-flange centre, every TOTO floor bowl in the house.
WC_ROUGH_IN_IN = 12.0
#: Undimensioned (DSP-B-R10000 Rev L p.1 scales ~1 3/4"); ±2" kept as the allowance.
VALVE_HALF_SPACING_IN = 2.0
#: Inlet hub centre behind the finished face: scaled, bounded by the published 2 3/4" ±1/4"
#: finished wall to stringer (M&I 50353 Rev L p.2 step 1B).
VALVE_HUB_DEPTH_IN = 1.75
_DELTA = ("Delta M&I 50353 Rev L p.2 fig. 2A + DSP-B-R10000 Rev L p.1, "
          "media.deltafaucet.com, read 2026-11-07")


def floor_wc_ports(depth_in: float, supply_left_in: float, supply_aff_in: float,
                   wall_gap_in: float, *, source: str, stop_note: str = "",
                   floor_stop: tuple[float, float, float] | None = None,
                   ) -> tuple[ServicePort, ...]:
    """Flange and supply stop for a floor bowl whose tank back stands ``wall_gap_in`` off the
    finished wall, the gap the TOTO sheet draws: the flange stays at the 12" rough-in and the
    stop on the wall face, both ``wall_gap_in`` behind the china.

    The stop is EXACT as house setout, like ``lav_ports``: TOTO prints a suggested station
    ("Supply as Req'd"), and the house adopts it unless the type says otherwise.
    ``floor_stop`` = (left of centre, proud of the wall, AFF) is a floor-fed stop instead:
    TOTO's station is a wall supply's, so the plumber's riser setout governs, approximate.
    """
    wall_in = depth_in / 2 + wall_gap_in
    if floor_stop is not None:
        left_in, proud_in, aff_in = floor_stop
        cold = ServicePort(
            tag="WC-WATER_COLD", service=Service.WATER_COLD,
            position=(inch(-left_in), inch(wall_in - proud_in), inch(aff_in)),
            connection_size=inch(0.5), direction=(0, 0, -1),
            notes=f'Floor-fed angle stop {left_in}" left of centre, {proud_in}" off the wall, '
                  f'{aff_in}" AFF: house riser setout, clear of the wall base and the china. '
                  f"{source} draws a wall supply only.{stop_note}")
    else:
        cold = ServicePort(
            tag="WC-WATER_COLD", service=Service.WATER_COLD,
            position=(inch(-supply_left_in), inch(wall_in), inch(supply_aff_in)),
            connection_size=inch(0.5), direction=(0, 1, 0), certainty=PortCertainty.EXACT,
            notes=f'Angle stop {supply_left_in}" left of centre, {supply_aff_in}" AFF, '
                  f"house setout ({source}).{stop_note}")
    return (
        ServicePort(tag="WC-DRAIN", service=Service.DRAIN,
                    position=(inch(0), inch(wall_in - WC_ROUGH_IN_IN), inch(0)),
                    connection_size=inch(3), direction=(0, 0, -1), certainty=PortCertainty.EXACT,
                    notes='Closet flange at the finished floor, the 12" published rough-in off '
                          f'the finished wall; the tank back stands {wall_gap_in}" off it.'),
        cold,
    )


def valve_ports(centre_in: tuple[float, float, float], wall: tuple[float, float],
                note: str) -> tuple[ServicePort, ...]:
    """Hot and cold inlets of a valve body whose finished-face centre is ``centre_in``; ``wall``
    points from the room into the valve's wall (product frame). Facing the valve, hot is on
    the left and its side hub points left, cold the mirror (50353 fig. 2A)."""
    (x, y, z), (nx, ny) = centre_in, wall
    left = (-ny, nx)  # facing +n, left is +90 degrees from it
    x, y = x + nx * VALVE_HUB_DEPTH_IN, y + ny * VALVE_HUB_DEPTH_IN
    return tuple(
        ServicePort(tag=tag, service=service,
                    position=(inch(x + side * left[0] * VALVE_HALF_SPACING_IN),
                              inch(y + side * left[1] * VALVE_HALF_SPACING_IN), inch(z)),
                    connection_size=inch(0.5), direction=(side * left[0], side * left[1], 0),
                    notes='R10000-UNBX side hub, 1 3/4" behind the finished face; spacing '
                          f"undimensioned ({_DELTA}); {note}")
        for tag, service, side in (("VALVE-HOT", Service.WATER_HOT, 1),
                                   ("VALVE-COLD", Service.WATER_COLD, -1)))


def floor_drain_port(x_in: float, y_in: float, z_in: float = 0.0, *,
                     size_in: float = 2.0, exact: bool = False, note: str) -> ServicePort:
    return ServicePort(tag="DRAIN", service=Service.DRAIN,
                       position=(inch(x_in), inch(y_in), inch(z_in)),
                       connection_size=inch(size_in), direction=(0, 0, -1),
                       certainty=PortCertainty.EXACT if exact else PortCertainty.APPROXIMATE,
                       notes=note)

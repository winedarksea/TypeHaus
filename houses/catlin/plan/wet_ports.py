"""Water-closet and floor-drain stations in each product's local frame.

+y toward the product's back, z from its body base (``resolve/mep_sleeves.expected_port_point``).
A floor bowl's base is the finished floor, so its flange is z=0. Shower valve stations now
come from the shared ShowerAssemblySpec in plan/shower_assemblies.py.
"""

from typehaus.model import PortCertainty, Service, ServicePort, inch

#: Finished wall to closet-flange centre, every TOTO floor bowl in the house.
WC_ROUGH_IN_IN = 12.0


def floor_wc_ports(depth_in: float, wall_gap_in: float, *, source: str, stop_note: str = "",
                   wall_stop: tuple[float, float] | None = None,
                   floor_stop: tuple[float, float, float] | None = None,
                   ) -> tuple[ServicePort, ...]:
    """Flange and supply stop for a floor bowl whose tank back stands ``wall_gap_in`` off the
    finished wall, the gap the TOTO sheet draws: the flange stays at the 12" rough-in and the
    stop on the wall face, both ``wall_gap_in`` behind the china.

    Exactly one stop. ``wall_stop`` = (left of centre, AFF) is EXACT as house setout, like
    ``lav_ports``: TOTO prints a suggested station ("Supply as Req'd") and the house adopts
    it. ``floor_stop`` = (left of centre, proud of the wall, AFF) is a floor-fed stop:
    TOTO's station is a wall supply's, so the plumber's riser setout governs, approximate.
    """
    if (wall_stop is None) == (floor_stop is None):
        raise ValueError("give exactly one of wall_stop and floor_stop")
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
        left_in, aff_in = wall_stop
        cold = ServicePort(
            tag="WC-WATER_COLD", service=Service.WATER_COLD,
            position=(inch(-left_in), inch(wall_in), inch(aff_in)),
            connection_size=inch(0.5), direction=(0, 1, 0), certainty=PortCertainty.EXACT,
            notes=f'Angle stop {left_in}" left of centre, {aff_in}" AFF, '
                  f"house setout ({source}).{stop_note}")
    return (
        ServicePort(tag="WC-DRAIN", service=Service.DRAIN,
                    position=(inch(0), inch(wall_in - WC_ROUGH_IN_IN), inch(0)),
                    connection_size=inch(3), direction=(0, 0, -1), certainty=PortCertainty.EXACT,
                    notes='Closet flange at the finished floor, the 12" published rough-in off '
                          f'the finished wall; the tank back stands {wall_gap_in}" off it.'),
        cold,
    )


def floor_drain_port(x_in: float, y_in: float, z_in: float = 0.0, *,
                     size_in: float = 2.0, exact: bool = False, note: str) -> ServicePort:
    return ServicePort(tag="DRAIN", service=Service.DRAIN,
                       position=(inch(x_in), inch(y_in), inch(z_in)),
                       connection_size=inch(size_in), direction=(0, 0, -1),
                       certainty=PortCertainty.EXACT if exact else PortCertainty.APPROXIMATE,
                       notes=note)

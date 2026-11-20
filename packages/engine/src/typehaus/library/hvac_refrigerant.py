"""Refrigerant connections and published piping limits for the Gree types (decision #139).

Ports are flare connections; stations are schematic readings (``APPROXIMATE``) because no
submittal in the repo dimensions them. Limits are the submittals' piping tables as read in
``houses/catlin/notes/heat_pump_ground_pad.md``; an unread figure stays ``None``.
"""

from __future__ import annotations

from typehaus import RefrigerantLimits, Service, ServicePort, ft, inch

_HEAD_NOTE = ("Flared {size} in. {line} line at the left-rear knockout (viewed from the "
              "front); station schematic, the submittal draws the piping exit only.")


def head_refrigerant_ports(width_in: float, depth_in: float, liquid_in: float,
                           vapor_in: float) -> tuple[ServicePort, ...]:
    """A wall head's pair at its left-rear corner (viewed from the front, local -x), leaving
    through the wall behind (+y). Heads pipe either side; left is this catalog's reading."""
    x = -(width_in / 2.0 - 3.0)
    return tuple(ServicePort(
        tag=tag, service=service, position=(inch(x + dx), inch(depth_in / 2.0), inch(2.0)),
        connection_size=inch(size), direction=(0, 1, 0),
        notes=_HEAD_NOTE.format(size=size, line=tag),
    ) for tag, service, size, dx in (("liquid", Service.REFRIGERANT_LIQUID, liquid_in, 1.5),
                                     ("vapor", Service.REFRIGERANT_VAPOR, vapor_in, 0.0)))


def outdoor_refrigerant_ports(width_in: float, depth_in: float, liquid_in: float,
                              vapor_in: float, letters: tuple[str, ...] = ()
                              ) -> tuple[ServicePort, ...]:
    """Service valves on the outdoor unit's +x (service) end, one pair per port letter.

    A single-port unit's pair is ``liquid``/``vapor``; a multi's ``liquid-A``/``vapor-A``.
    """
    rows = letters or ("",)
    out: list[ServicePort] = []
    for index, letter in enumerate(rows):
        suffix = f"-{letter}" if letter else ""
        z = 4.0 + 3.0 * index
        for tag, service, size, dy in (("liquid", Service.REFRIGERANT_LIQUID, liquid_in, -1.0),
                                       ("vapor", Service.REFRIGERANT_VAPOR, vapor_in, 1.0)):
            out.append(ServicePort(
                tag=f"{tag}{suffix}", service=service,
                position=(inch(width_in / 2.0), inch(-depth_in / 4.0 + dy), inch(z)),
                connection_size=inch(size), direction=(1, 0, 0),
                notes=f"Flared {size} in. service valve{' ' + letter if letter else ''}; "
                      "station schematic, verify on the delivered unit."))
    return tuple(out)


FXU24_LIMITS = RefrigerantLimits(
    max_total=ft(164), max_per_port=ft(164), max_rise_od_above=ft(49),
    max_rise_od_below=ft(49), precharged_length=ft(31), charge_oz_per_ft=0.323,
    source="Gree FXU24 submittal (GREE_FXU24_230V_R32_SUB_01272026), piping: 3/8 x 3/4 in., "
           "164 ft max length, 49 ft max height difference, 31 ft precharged, 0.323 oz/ft "
           "added beyond it. Minimum length not read.")

MUL30_LIMITS = RefrigerantLimits(
    max_total=ft(263), max_per_port=ft(82), max_rise_od_above=ft(82),
    max_rise_od_below=ft(82), precharged_length=ft(131),
    source="Gree Multi R32 MUL30 submittal / IOM S3, piping: 1/4 x 3/8 in. per port, 263 ft "
           "total, 82 ft per port, 82 ft height difference, 131 ft precharged. Minimum per "
           "port and the added-charge rate not read.")

SAPPHIRE9_LIMITS = RefrigerantLimits(
    source="Gree Sapphire R32 9k: piping table not yet read into the repo (lengths, rise, "
           "precharge unknown).")

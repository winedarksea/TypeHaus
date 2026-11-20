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
    max_total=ft(164), max_per_port=ft(164), min_per_port=ft(10), max_rise_od_above=ft(49),
    max_rise_od_below=ft(49), precharged_length=ft(31), charge_oz_per_ft=0.323,
    source="Gree FXU24 submittal (GREE_FXU24_230V_R32_SUB_01272026) p.2, piping: 3/8 x 3/4 in., "
           "Pipe Length (Min - Max) 10 - 164 ft, 49 ft max elevation, 31 ft precharged, "
           "0.323 oz/ft added beyond it.")

MUL30_LIMITS = RefrigerantLimits(
    max_total=ft(263), max_per_port=ft(82), min_per_port=ft(10), max_rise_od_above=ft(82),
    max_rise_od_below=ft(82), precharged_length=ft(131), charge_oz_per_ft=0.2,
    source="Gree MUL30 submittal (GREE_MUL30HP_230V_R32_SUB_04022026) p.3, piping: 1/4 x 3/8 "
           "in. per port, Pipe Length (Min - Max) 10 - 263 ft, 82 ft to the furthest indoor "
           "unit, 82 ft max elevation, 131 ft precharged, 0.2 oz/ft added. The 10 ft minimum "
           "is read per port (the stricter reading). The Multi R32 service manual p.17 agrees "
           "but prints 82.02 ft as the total length, read here as a misprint.")

SAPPHIRE9_LIMITS = RefrigerantLimits(
    max_total=ft(131), max_per_port=ft(131), min_per_port=ft(10), max_rise_od_above=ft(82),
    max_rise_od_below=ft(82), precharged_length=ft(25), charge_oz_per_ft=0.2,
    source="Gree SAP09 submittal (GREE_SAP09HP_230V_R32_AH_AO_SUB_07302025) p.2, piping: "
           "1/4 x 1/2 in. flared, Pipe Length (Min - Max) 10 - 131 ft, 82 ft max elevation, "
           "25 ft precharged, 0.2 oz/ft added. Service manual (SAP09-24) p.3 and Appendix 2 "
           "agree (24.6 ft standard, 3 m minimum).")

"""Where a window unit sits inside its flashed rough opening."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowSeat:
    """The unit's envelope inside the RO, derived from the buck, membrane and sill pan.

    ``width_m``/``height_m``/``sill_m`` on the opening stay the rough opening; the product
    is drawn this far inside it, so it never shares space with the flashing it sits on.
    """

    #: Each jamb: buck + jamb membrane + shim space.
    jamb_inset_m: float
    #: Unit bottom above the RO bottom: buck + the pan's high point (at the back dam).
    sill_rise_m: float
    #: Head: buck + head membrane + shim space.
    head_drop_m: float
    #: The unit's interior face as a signed wall-normal offset: the back dam's front face.
    inner_m: float

"""Where a window unit sits inside its flashed rough opening."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typehaus.quantities import Length
    from typehaus.resolve.model import ResolvedOpening


@dataclass(frozen=True)
class WindowSeat:
    """The unit's envelope inside the RO, derived from the buck, membrane and sill pan.

    ``width_m``/``height_m``/``sill_m`` on the opening stay the rough opening; the product
    is drawn this far inside it, so it never shares space with the flashing it sits on.
    """

    #: Each jamb: buck + jamb membrane + shim space, or half the slack around a sized unit.
    jamb_inset_m: float
    #: Unit bottom above the RO bottom: buck + the pan's high point (at the back dam).
    sill_rise_m: float
    #: Head: buck + head membrane + shim space, or all the slack above a sized unit.
    head_drop_m: float
    #: The unit's interior face as a signed wall-normal offset: the back dam's front face.
    inner_m: float
    #: The signed mount plane when a profiled metal trim kit terminates the reveal.
    outer_m: float | None = None


def orderable_size(available_m: float, step: Length | None) -> float:
    """The largest product size on ``step`` that fits; never rounds up past the envelope."""
    if step is None:
        return available_m
    # The epsilon keeps an exact multiple from flooring one step short on float noise.
    return math.floor(available_m / step.meters + 1e-9) * step.meters


def window_frame_dimensions(opening: ResolvedOpening) -> tuple[float, float, float] | None:
    """Frame width, height and bottom above the floor; None means no resolved seat.

    The rough opening remains the framing contract. A manually flashed opening cannot
    claim a product size until its installation detail supplies a seat.
    """
    seat = getattr(opening, "window_seat", None)
    if getattr(opening, "kind", "window") != "window" or seat is None:
        return None
    return (opening.width_m - 2 * seat.jamb_inset_m,
            opening.height_m - seat.sill_rise_m - seat.head_drop_m,
            opening.sill_m + seat.sill_rise_m)

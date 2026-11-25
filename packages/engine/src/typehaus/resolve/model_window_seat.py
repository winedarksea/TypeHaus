"""Where a window unit sits inside its flashed rough opening."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from typehaus.model.enums import LayerFunction

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
    #: The signed plane the unit's outer face stands on: the mount plane, or proud of it.
    outer_m: float | None = None
    #: The product's ``WindowType.frame_depth`` back from ``outer_m``; None draws to the dam.
    frame_depth_m: float | None = None
    #: What terminates the reveal outside the unit: ``"metal_trim"`` (a profiled metal kit's
    #: jamb, sill and head), ``"casing"`` (an outie under any other skin: a picture-frame
    #: casing on the cladding) or ``"veneer"`` (a separate wythe's reveal, hand-flashed).
    mount: str | None = None
    #: How far the unit stands proud of the mount plane because the plane sits closer to the
    #: back dam than the product is deep. A misfit for the supplier to confirm, not a choice.
    proud_m: float = 0.0

    @property
    def metal_trim(self) -> bool:
        return self.mount == "metal_trim"


_SKIN = (LayerFunction.CLADDING.value, LayerFunction.FINISH.value)


def mount_layer_index(layers) -> int | None:
    """The outermost layer that is neither cladding nor finish: the window mount plane.

    The last thing a flange can bear on before the skin goes over it, so the stool's return
    (``millwork.interior_return_m``) and a veneer-backed seat read one plane.
    """
    index = None
    for position, layer in enumerate(layers):
        if layer.function not in _SKIN:
            index = position
    return index


def frame_mount(frame, metal_wall: bool) -> str | None:
    """How a flashed unit is mounted, or None for one drawn from its back dam out.

    An outie stands on its buck at ``frame.mount`` whatever the skin (its pan drains there,
    and the stool's return reads that plane), so it is mounted under LP as under metal.
    """
    if frame is None:
        return None
    return "metal_trim" if metal_wall else "casing" if frame.outie else None


def mount_seat(seat: WindowSeat, frame, depth_m: float | None, mount: str) -> WindowSeat:
    """The unit's outer face on ``frame.mount``, its interior face never in the back dam.

    A product deeper than mount plane to dam stands proud by the shortfall, at its true depth.
    """
    sign = frame.outward[0] * -frame.along[1] + frame.outward[1] * frame.along[0]
    proud = 0.0 if depth_m is None else max(0.0, sign * seat.inner_m + depth_m - frame.mount)
    return replace(seat, outer_m=sign * (frame.mount + proud), frame_depth_m=depth_m,
                   mount=mount, proud_m=proud)


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

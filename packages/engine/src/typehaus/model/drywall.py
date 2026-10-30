"""Drywall accessories, declared once and derived from the host faces (decision #103).

The ``TrimStandard`` / ``BoxStandard`` pattern: one house-level element names the bead for
each kind of board edge, ``resolve/drywall_trims.py`` finds the edges, and
``takeoff/drywall_trims.py`` bills them by the LF. Inside corners are paper tape and stay in
the board's labour rate, so they have no field here.
"""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Angle, Length, deg, ft


class PlasterInProfile(HausModel):
    """A plaster-in LED wall-washer: an aluminium channel set in a slot cut through the
    ceiling (or soffit) board, flanges mudded flush, tape tilted toward the washed wall.

    ``aperture`` is the slot cut through the board, ``depth`` how far the channel stands
    above the board's room face, ``flange`` each mudded wing's width on the face. The wall
    offsets bound the distance from the slot centre (the run's path) to the washed face.
    """

    material_ref: str
    aperture: Length
    depth: Length
    flange: Length
    tilt: Angle = deg(45)
    wall_offset_min: Length
    wall_offset_max: Length


@register_element
class DrywallStandard(Element):
    """The house's drywall accessories, one material per edge kind (decision #103).

    One per plan (a second is an ``integrity.drywall_standard`` error). Without one, the
    window returns bill the library's generic beads and nothing else is derived.
    ``led_profile`` makes every light run set into a gypsum ceiling or soffit plaster-in.
    """

    outside_corner_ref: str
    termination_ref: str
    door_bead_ref: str
    tile_reveal_ref: str
    window_corner_ref: str
    window_frame_ref: str
    # The window-return corner bead's nose radius (a bullnose); None is a square bead. A
    # fabricated stool's shoulder notch takes it, so the stone seats against the bead.
    window_corner_radius: Length | None = None
    led_profile: PlasterInProfile | None = None
    stock_length: Length = ft(10)

    def material_refs(self) -> tuple[str, ...]:
        refs = (self.outside_corner_ref, self.termination_ref, self.door_bead_ref,
                self.tile_reveal_ref, self.window_corner_ref, self.window_frame_ref,
                *((self.led_profile.material_ref,) if self.led_profile else ()))
        return tuple(dict.fromkeys(refs))


register_constructor("DrywallStandard", DrywallStandard)
register_constructor("PlasterInProfile", PlasterInProfile)

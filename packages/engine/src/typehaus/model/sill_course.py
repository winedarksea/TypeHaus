"""A door's girt sill beam: the beam, seats and screws that carry its approach."""

from __future__ import annotations

from pydantic import Field

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class SillCourseFastening(HausModel):
    """How a girt band's sill beam under a DOOR hangs on the floor edge behind it.

    A ``course_stock`` beam on edge, outboard of the girt band (back on its outer face), on one
    ``seat_width`` block stack back to the sheathing at each end; each seat takes ``seat_rows``
    staggered rows of ``screws_per_row``, laid out to the screw's published spacing
    (``hardware/catalog.FastenerSpacing``) and graded on ``lateral_wet_lb``. The screw
    (``fastener_part``) crosses the sheathing into the floor's LSL edge rim.
    ``course_modulus_psi`` feeds the screw-share solve (``engineering/exterior_door_support.py``);
    ``course_fall_per_ft`` is the fall ripped across the beam's top.
    """

    fastener_part: str = Field(min_length=1)
    fastener_length_in: float = Field(gt=0)
    course_modulus_psi: float = Field(gt=0)
    source: str = Field(min_length=1)
    course_stock: str = Field(min_length=1)
    seat_width: Length
    seat_rows: int = Field(default=2, ge=1)
    screws_per_row: int = Field(default=2, ge=1)
    # The seat joint's own wet Z' (house NDS calc), and the beam's allowables.
    lateral_wet_lb: float = Field(gt=0)
    lateral_source: str = Field(min_length=1)
    course_bending_psi: float = Field(gt=0)
    course_shear_psi: float = Field(gt=0)
    # The door maker's limit over the sill's unsupported span.
    course_deflection_limit: Length = inch(0.125)
    course_fall_per_ft: Length = inch(0.25)


register_constructor("SillCourseFastening", SillCourseFastening)

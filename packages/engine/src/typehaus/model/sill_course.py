"""A door's girt sill course: the beam, blocks, screws and backer that carry its approach."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class SillCourseFastening(HausModel):
    """How a girt band's sill course under a DOOR hangs on the floor edge behind it.

    ``layout="blocks"``: a ``course_stock`` course in the girt plane on an end block (one row
    of ``end_screws`` at ``end_screw_pitch``) at each end and one-screw blocks at
    ``block_spacing``. ``layout="end_seats"``: a ``course_stock`` beam on edge, outboard of the
    girt band (back on its outer face), on one ``seat_width`` block stack back to the sheathing
    at each end; each seat takes ``seat_rows`` staggered rows of ``screws_per_row``, laid out to
    the screw's published spacing (``hardware/catalog.FastenerSpacing``) and graded on
    ``lateral_wet_lb``. The screw (``fastener_part``) crosses the sheathing into the floor's
    edge member; at an I-joist, into a derived backer pair of ``backer_stock`` ripped to the
    web recess. ``course_modulus_psi`` feeds the screw-share solve
    (``engineering/exterior_door_support.py``).
    """

    layout: Literal["blocks", "end_seats"] = "blocks"
    block_spacing: Length | None = None
    end_screws: int | None = Field(default=None, ge=1)
    end_screw_pitch: Length | None = None
    fastener_part: str = Field(min_length=1)
    fastener_length_in: float = Field(gt=0)
    backer_stock: str = Field(min_length=1)
    backer_material_ref: str = Field(min_length=1)
    course_modulus_psi: float = Field(gt=0)
    source: str = Field(min_length=1)
    course_stock: str = "2x4"
    seat_width: Length | None = None
    seat_rows: int = Field(default=2, ge=1)
    screws_per_row: int = Field(default=2, ge=1)
    # The seat joint's own wet Z' (house NDS calc), and the beam's allowables.
    lateral_wet_lb: float | None = Field(default=None, gt=0)
    lateral_source: str | None = None
    course_bending_psi: float | None = Field(default=None, gt=0)
    course_shear_psi: float | None = Field(default=None, gt=0)
    # The door maker's limit over the sill's unsupported span.
    course_deflection_limit: Length = inch(0.125)
    course_fall_per_ft: Length = inch(0.25)

    @model_validator(mode="after")
    def layout_fields(self):
        if self.layout == "blocks":
            if None in (self.block_spacing, self.end_screws, self.end_screw_pitch):
                raise ValueError("a blocked sill course names its block spacing and end screws")
        elif None in (self.seat_width, self.lateral_wet_lb, self.lateral_source,
                      self.course_bending_psi, self.course_shear_psi):
            raise ValueError("an end-seat sill beam names its seat width, its joint's lateral "
                             "value and source, and its bending and shear allowables")
        return self


register_constructor("SillCourseFastening", SillCourseFastening)

"""A door's girt sill beam: the beam, seats and screws that carry its approach."""

from __future__ import annotations

from pydantic import Field

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class SillCourseFastening(HausModel):
    """How a girt band's sill beam under a DOOR hangs on the floor edge behind it.

    A ``course_stock`` beam on edge, outboard of the girt band (back on its outer face), on one
    ``seat_width`` stack of ``seat_stock`` plies back to the sheathing at each end; each seat
    takes ``seat_rows`` staggered rows of ``screws_per_row``, laid out to the screw's published
    spacing (``hardware/catalog.FastenerSpacing``). The screw (``fastener_part``) crosses the
    sheathing into the floor's LSL edge rim and the backer behind it. Its lateral share is
    graded on ``lateral_wet_lb``; the seat's rotation under the beam's eccentric reaction puts
    each screw in combined lateral and withdrawal (NDS 12.4.1), the axial value the least of
    ``withdrawal_lb_per_in`` x embedded thread and each ``pull_through_lb`` column x
    ``pull_through_wet_factor``, about a compression resultant ``seat_bearing_inset`` off the
    seat's bearing edge (``engineering/sill_seat_rotation.py``). ``course_modulus_psi`` feeds the
    screw-share solve; ``course_fall_per_ft`` is the fall ripped across the beam's top.
    """

    fastener_part: str = Field(min_length=1)
    fastener_length_in: float = Field(gt=0)
    course_modulus_psi: float = Field(gt=0)
    source: str = Field(min_length=1)
    course_stock: str = Field(min_length=1)
    seat_width: Length
    seat_stock: str | None = None  # None: the course stock
    fastener_diameter_in: float = Field(gt=0)
    seat_rows: int = Field(default=2, ge=1)
    screws_per_row: int = Field(default=2, ge=1)
    # The seat joint's own wet Z' (house NDS calc), and the beam's allowables.
    lateral_wet_lb: float = Field(gt=0)
    lateral_source: str = Field(min_length=1)
    course_bending_psi: float = Field(gt=0)
    # The axial side of the rotation couple: ESR Table 2 per inch at the rim's SG, and each
    # Table 3 head pull-through column read, as (label, lb).
    withdrawal_lb_per_in: float = Field(gt=0)
    pull_through_lb: tuple[tuple[str, float], ...] = Field(min_length=1)
    pull_through_wet_factor: float = Field(default=1.0, gt=0, le=1)
    axial_source: str = Field(min_length=1)
    seat_bearing_inset: Length = inch(0.4)
    course_shear_psi: float = Field(gt=0)
    # The door maker's limit over the sill's unsupported span.
    course_deflection_limit: Length = inch(0.125)
    course_fall_per_ft: Length = inch(0.25)
    # The least outward fall the pan may take across the beam's top.
    pan_min_fall_per_ft: Length = inch(0.25)


register_constructor("SillCourseFastening", SillCourseFastening)

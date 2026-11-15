"""A door's girt sill course: the blocks, screws and backer that carry its approach."""

from __future__ import annotations

from pydantic import Field

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class SillCourseFastening(HausModel):
    """How a girt band's sill course under a DOOR hangs on the floor edge behind it.

    An end block centred in from each free course end takes ``end_screws`` in one row along
    the course at ``end_screw_pitch``; interior blocks take one screw each, evenly spaced at
    no more than ``block_spacing``. The screw (``fastener_part``) crosses the sheathing into
    the floor's edge member; at an I-joist it crosses a derived backer pair of
    ``backer_stock`` ripped to the web recess. ``course_modulus_psi`` is the course's E for
    the screw-share solve (``engineering/exterior_door_support.py``).
    """

    block_spacing: Length
    end_screws: int = Field(ge=1)
    end_screw_pitch: Length
    fastener_part: str = Field(min_length=1)
    fastener_length_in: float = Field(gt=0)
    backer_stock: str = Field(min_length=1)
    backer_material_ref: str = Field(min_length=1)
    course_modulus_psi: float = Field(gt=0)
    source: str = Field(min_length=1)


register_constructor("SillCourseFastening", SillCourseFastening)

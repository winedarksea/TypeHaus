"""Purchased fascia-mount geometry; lengths are catalog facts, contours may be illustrative."""

from typing import Literal

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class FasciaMountSpec(HausModel):
    straight_product: str
    inside_corner_product: str
    outside_corner_product: str
    pocket_width: Length
    overall_height: Length
    flange_height: Length
    flange_width: Length
    wall_thickness: Length
    corner_wing_length: Length
    inside_corner_envelope: Length
    display_corner_hole_inset: Length
    # Outside corner: each inboard pocket wall jogs out at 45 deg to a flange this far past
    # the mounting-face corner, leaving the post's inboard corner open (product drawing).
    display_corner_jog: Length
    mounting_hole_spacing: tuple[Length, Length]
    mounting_hole_top_drop: Length
    # The mounting fastener: a through-bolt (nut on the band's back face) or a structural
    # wood screw into backing. bolt_* size whichever it is.
    fastener: Literal["through_bolt", "wood_screw"]
    fastener_product: str
    bolt_diameter: Length
    bolt_length: Length
    post_tube_length: Length  # the stocked post, cut to fit
    post_screw_diameter: Length
    post_screw_length: Length
    washer_diameter: Length
    rear_washer_diameter: Length
    # Undimensioned hardware contours are deliberately labelled display dimensions.
    display_washer_thickness: Length
    display_head_width: Length
    display_head_height: Length
    insert_thickness: Length
    foot_block_fascia_screw_length: Length
    foot_block_product: str
    display_foot_block_width: Length
    display_foot_block_thickness: Length
    bottom_clearance: Length
    source: str

    @model_validator(mode="after")
    def validate_mount_dimensions(self):
        for name in type(self).model_fields:
            value = getattr(self, name)
            dimensions = value if isinstance(value, tuple) else (value,)
            if any(isinstance(dimension, Length) and dimension.meters <= 0
                   for dimension in dimensions):
                raise ValueError(f"{name} must be positive")
        if self.flange_height > self.overall_height:
            raise ValueError("fascia flange cannot exceed the overall bracket height")
        return self

"""Resolved dimensions for hinged plan glyphs, shared by drawings and model JSON."""

from dataclasses import dataclass

from typehaus.resolve.door_sizing import CASED_DOOR_DEFAULTS
from typehaus.resolve.geometry_door_products import finish_faces


@dataclass(frozen=True)
class DoorPlanDimensions:
    hinge_half_m: float
    leaf_width_m: float
    leaf_thickness_m: float
    jamb_thickness_m: float
    frame_normal_low_m: float
    frame_normal_high_m: float
    leaf_normal_m: float


def door_plan_dimensions(opening, wall) -> DoorPlanDimensions:
    """Keep the established sweep anchors; frame depth stays relative to the wall axis.

    The allowance contains shims as well as jamb stock, so only the stock is outlined.
    Product-less glyphs use the existing schematic cased-door dimensions.
    """
    defaults = CASED_DOOR_DEFAULTS
    sizing, product = opening.sizing, opening.cased_product
    allowance = sizing.jamb_allowance_m if sizing else defaults.jamb_allowance_m
    hinge_half = sizing.rough_w_m / 2 - allowance if sizing else opening.width_m / 2
    faces = (product.finish_faces_m if product else finish_faces(wall))
    if faces is None:
        faces = (-wall.thickness_m / 2, wall.thickness_m / 2)
    placement = opening.doorway.exterior_placement if opening.doorway else None
    if placement:
        faces = (placement.frame_inner_m, placement.frame_outer_m)
    return DoorPlanDimensions(
        hinge_half_m=hinge_half,
        leaf_width_m=sizing.leaf_w_m if sizing else opening.width_m,
        leaf_thickness_m=product.leaf_thickness_m if product else defaults.leaf_thickness_m,
        jamb_thickness_m=(product.jamb_thickness_m if product
                          else min(defaults.jamb_thickness_m, allowance)),
        frame_normal_low_m=min(faces), frame_normal_high_m=max(faces),
        leaf_normal_m=placement.leaf_normal_m if placement else 0.0,
    )

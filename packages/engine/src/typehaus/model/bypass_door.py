"""A purchased bypass (by-pass sliding) door set: track, hangers, guide and pulls.

``DoorType.width`` is the set's nominal width (two leaves, as on a 48" track) and ``height``
the leaf. The set's published numbers size the finished opening (``resolve/door_sizing``)
and draw the track, the two lanes, the floor guide and the cup pulls
(``resolve/geometry_bypass_doors``).
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class BypassDoorSpec(HausModel):
    """Published dimensions of a two-leaf bypass set."""

    track_width: Length  # across the wall
    track_height: Length
    # Centre to centre of the two leaves' lanes.
    lane_pitch: Length
    # The leaf's gap over the finished floor.
    floor_clearance: Length
    # Finished opening height = leaf height + this, off the finished floor.
    head_over_leaf: Length
    # The two closed leaves lap this much at the centre: finished width = nominal - overlap.
    overlap: Length
    # The thickest leaf the hangers take.
    door_thickness: Length
    # The floor guide, straddling both lanes: along the wall, across it, tall.
    guide_width: Length
    guide_depth: Length
    guide_height: Length
    pull_diameter: Length
    # Pull centre above the leaf's bottom edge.
    pull_height: Length
    product_ref: str | None = None
    source: str

    @model_validator(mode="after")
    def _lanes_clear_each_other(self) -> BypassDoorSpec:
        if self.lane_pitch.meters < self.door_thickness.meters:
            raise ValueError("bypass_door: lane_pitch is narrower than the door thickness; "
                             "the closed leaves would collide")
        return self


register_constructor("BypassDoorSpec", BypassDoorSpec)

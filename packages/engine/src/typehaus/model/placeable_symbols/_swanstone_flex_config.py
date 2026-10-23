"""BATH2 visualization dimensions, inches; fabrication details remain preliminary.

SS-3636: Swan SF03636MD specification. Flex: SHDR-22327200-01 manual.
The post, channels and internal pan contours are visualization allowances, not shop drawings.
Local -x is the tub/north side, -y the entrance/west side at Catlin's -90° rotation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SwanstoneFlexDimensions:
    pan_width: float = 36.0
    pan_depth: float = 36.0
    pan_height: float = 5.5
    threshold_height: float = 4.5
    threshold_depth: float = 2.75
    minimum_flat_threshold: float = 1.375
    interior_width: float = 33.5
    interior_depth: float = 32.0
    floor_thickness: float = 0.5
    drain_floor_height: float = 0.75
    basin_edge_height: float = 2.25
    drain_diameter: float = 3.0
    finished_floor_datum: float = 1.5
    ceiling_datum: float = 106.0
    deck_datum: float = 22.75
    front_height: float = 72.0
    front_minimum_width: float = 32.0
    front_maximum_width: float = 36.0
    door_swing_radius: float = 22.875
    post_width: float = 1.5
    wall_panel_thickness: float = 0.5
    rail_width: float = 0.875
    channel_width: float = 0.625
    front_glass_thickness: float = 0.25
    north_glass_thickness: float = 0.375
    seal_width: float = 0.125
    handle_height: float = 8.0
    handle_projection: float = 1.0
    handle_center_height: float = 36.0
    basin_segments: int = 32
    swing_segments: int = 36

    @property
    def model_height(self) -> float:
        return self.ceiling_datum - self.finished_floor_datum

    @property
    def finished_opening(self) -> float:
        # The post sits on the deck, outside the pan; its inside face is the pan edge.
        return self.pan_width - self.wall_panel_thickness


BATH2_SHOWER = SwanstoneFlexDimensions()

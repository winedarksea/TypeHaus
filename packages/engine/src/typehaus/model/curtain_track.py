"""A ceiling or wall curtain track, drawn with its curtains OPEN in folded stacks.

The type's W x D x H envelope is the CLOSED curtain (run x rail-plus-folds x full drop), so
placeable collision grades furniture against where the curtain closes. The generated model
draws only the rail and the open stacks inside that envelope.
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch

STACK_TOLERANCE_M = 1e-6


class CurtainStack(HausModel):
    """One open stack: its station from the run's start (local -x end) and stacked width."""

    start: Length
    width: Length


class CurtainTrackSpec(HausModel):
    stacks: tuple[CurtainStack, ...] = ()
    # False draws the rail alone (a per-run switch for the 3D look).
    show_curtains: bool = True
    # Fabric top above the rail's underside: the heading rises around the rail to hide it.
    heading_rise: Length = inch(0.5)
    fold_pitch: Length = inch(4)
    fold_depth: Length = inch(3.5)
    rail_width: Length = inch(1)
    rail_height: Length = inch(0.75)
    # Bare outdoor channel hardware; interior VIDGA rails retain their existing model.
    outdoor_hardware: bool = False
    rail_wall_thickness: Length = inch(0.0625)
    carrier_slot_width: Length = inch(0.25)
    stock_length: Length = inch(84)
    mounting_end_inset: Length = inch(6)
    mounting_screws_per_stock: int = 5
    splice_length: Length = inch(1.5)
    end_stop_length: Length = inch(0.25)

    @model_validator(mode="after")
    def _validate(self) -> CurtainTrackSpec:
        for name in ("heading_rise", "fold_pitch", "fold_depth", "rail_width", "rail_height"):
            if getattr(self, name).meters <= 0:
                raise ValueError(f"curtain track {name} must be positive")
        if self.outdoor_hardware:
            for name in ("rail_wall_thickness", "carrier_slot_width", "stock_length",
                         "mounting_end_inset", "splice_length", "end_stop_length"):
                if getattr(self, name).meters <= 0:
                    raise ValueError(f"curtain track {name} must be positive")
            if self.mounting_screws_per_stock < 2:
                raise ValueError("outdoor track needs at least two screws per stock length")
            if 2 * self.mounting_end_inset.meters >= self.stock_length.meters:
                raise ValueError("track mounting insets must leave room between screws")
            if 2 * self.rail_wall_thickness.meters >= min(
                    self.rail_height.meters,
                    self.rail_width.meters - self.carrier_slot_width.meters):
                raise ValueError("track walls must leave an open channel and retaining lips")
        if self.heading_rise.meters > self.rail_height.meters:
            raise ValueError("curtain heading cannot rise above the rail top")
        ordered = sorted(self.stacks, key=lambda s: s.start.meters)
        for stack in ordered:
            if stack.start.meters < 0 or stack.width.meters <= 0:
                raise ValueError("curtain stack needs a non-negative start and positive width")
        for first, second in zip(ordered, ordered[1:], strict=False):
            if first.start.meters + first.width.meters > second.start.meters + STACK_TOLERANCE_M:
                raise ValueError("curtain stacks overlap")
        return self

    def check_fits(self, run_m: float, depth_m: float) -> None:
        """Stacks inside the run, rail and folds inside the envelope depth."""
        for stack in self.stacks:
            if stack.start.meters + stack.width.meters > run_m + STACK_TOLERANCE_M:
                raise ValueError("curtain stack runs past the end of the track")
        required_depth = max(self.fold_depth.meters if self.show_curtains else 0,
                             self.rail_width.meters)
        if required_depth > depth_m + STACK_TOLERANCE_M:
            raise ValueError("curtain folds are deeper than the track's footprint")


register_constructor("CurtainStack", CurtainStack)
register_constructor("CurtainTrackSpec", CurtainTrackSpec)

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

    @model_validator(mode="after")
    def _validate(self) -> CurtainTrackSpec:
        for name in ("heading_rise", "fold_pitch", "fold_depth", "rail_width", "rail_height"):
            if getattr(self, name).meters <= 0:
                raise ValueError(f"curtain track {name} must be positive")
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
        if max(self.fold_depth.meters, self.rail_width.meters) > depth_m + STACK_TOLERANCE_M:
            raise ValueError("curtain folds are deeper than the track's footprint")


register_constructor("CurtainStack", CurtainStack)
register_constructor("CurtainTrackSpec", CurtainTrackSpec)

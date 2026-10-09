"""Authored winder boundaries and the stock carrying their finish panels."""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, Point2D, inch


class WinderTurnSpec(HausModel):
    """Local (run, cross-run) geometry, with riser segments ordered inside to outside.

    There are n + 1 riser segments for n treads. The last belongs to the straight
    flight or arrival floor. The inner boundary is the actual edge of the clear stair.
    """

    footprint: tuple[Point2D, ...]
    inner_boundary: tuple[Point2D, ...]
    riser_lines: tuple[tuple[Point2D, Point2D], ...]


class WinderFramingSpec(HausModel):
    """A complete structural deck per tier; oak is a separate finish order."""

    subdeck_thickness: Length = inch(0.75)
    subdeck_material: str = "plywood-subfloor"
    rim_profile: str = "2x8"
    support_spacing: Length = inch(16)
    departing_rim_plies: int = 2


register_constructor("WinderTurnSpec", WinderTurnSpec)
register_constructor("WinderFramingSpec", WinderFramingSpec)

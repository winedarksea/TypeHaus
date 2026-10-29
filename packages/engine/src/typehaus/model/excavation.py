"""The over-dig around a foundation: working space, side slope, backfill and cap.

Resolved by ``resolve/excavation.py`` into cut, fill and haul-off volumes and the terraced
backfill solids that draw them; billed in the takeoff's ``excavation`` section.
"""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, inch


class SideSlope(HausModel):
    """Horizontal run per unit of rise of the cut face, and what that rests on.

    ``vertical_toe`` is an unsupported vertically sided lower portion: the face stands plumb
    that high off the floor before laying back. A bed whose dig (floor to strip grade) is
    deeper than ``vertical_toe_max_depth`` lays back from its floor instead (OSHA 1926
    Subpart P App. B, Type A: 3 1/2' only where the dig is 8' or less).
    """

    h_per_v: float
    basis: str
    vertical_toe: Length = inch(0)
    vertical_toe_max_depth: Length | None = None


class SoilFactor(HausModel):
    """A bulking or shrinkage fraction with its source (``0.30`` = 30%)."""

    fraction: float
    source: str


@register_element
class Excavation(Element):
    """One hole, dug for the beds it ``hosts`` (``FootingBedding`` tags).

    ``working_space`` is measured out from the drain column's outer face (the bed's edge
    where there is no column) at the excavation floor; the face then lays back at
    ``side_slope``. The top ``cap_thickness`` of the backfill is ``cap_material``; the rest
    is native spoil placed in ``lift``-thick lifts. ``swell`` is bank-to-loose (haul-off),
    ``shrink`` bank-to-compacted (spoil needed per yard of fill). Neither is defaulted.
    """

    hosts: tuple[str, ...]
    working_space: Length
    side_slope: SideSlope
    swell: SoilFactor
    shrink: SoilFactor
    cap_thickness: Length
    cap_material: str
    lift: Length
    #: Drawing resolution of the terraced fill: one level prism per step at most.
    draw_step: Length = inch(12)


for _name, _obj in (("SideSlope", SideSlope), ("SoilFactor", SoilFactor),
                    ("Excavation", Excavation)):
    register_constructor(_name, _obj)

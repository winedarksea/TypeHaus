"""Roof-plan locating and overall dimension tiers (D1-004's roof-plan part).

Every station is read off the resolved roof footprints: each corner of each footprint, plus
each gable's ridge line where the plan draws it. One chain per axis spans ALL the roofs,
struck from the common south-west corner of their union, so separate roofs (house, garage,
canopy) are located relative to one another and the chain sums to the overall.

These are ROOF-EDGE references, not wall-face ones: the wall-face-to-edge overhang strings
inside the footprint stay as they were, and the overall here reads edge to edge of the roofs
(G-002 says so), where the floor-plan overalls read face of sheathing.
"""

from __future__ import annotations

from typehaus.emit.draw.structural_dimensions import Tier
from typehaus.resolve.model import ResolvedModel, ResolvedRoof

ROOF_LOCATING = "ROOF EDGES + RIDGES"
ROOF_OVERALL = "O/A ROOF EDGE"
#: Forms whose ridge the plan draws mid-footprint; a shed's high edge is a footprint edge.
RIDGE_FORMS = frozenset({"gable", "hip"})


def footprint_box(roof: ResolvedRoof) -> tuple[float, float, float, float]:
    """``(minx, maxx, miny, maxy)``, metres."""
    xs = [point[0] for point in roof.footprint]
    ys = [point[1] for point in roof.footprint]
    return min(xs), max(xs), min(ys), max(ys)


def ridge_line(roof: ResolvedRoof) -> tuple[tuple[float, float], tuple[float, float]]:
    """The ridge as the plan draws it: mid-footprint, along ``ridge_direction``."""
    minx, maxx, miny, maxy = footprint_box(roof)
    if roof.ridge_direction == "x":
        return (minx, (miny + maxy) / 2), (maxx, (miny + maxy) / 2)
    return ((minx + maxx) / 2, miny), ((minx + maxx) / 2, maxy)


def roof_tiers(model: ResolvedModel) -> list[Tier | None]:
    """Roof edges and ridges located, then the roofs' overall extent, inner to outer."""
    xs: list[float] = []
    ys: list[float] = []
    for roof in model.roofs:
        xs.extend(point[0] for point in roof.footprint)
        ys.extend(point[1] for point in roof.footprint)
        if roof.form in RIDGE_FORMS:
            ridge_x, ridge_y = ridge_line(roof)[0]
            # A ridge along x is located by its y, and vice versa.
            (ys if roof.ridge_direction == "x" else xs).append(
                ridge_y if roof.ridge_direction == "x" else ridge_x)
    if not xs:
        return []
    overall = (min(xs), max(xs)), (min(ys), max(ys))
    return [Tier(ROOF_LOCATING, tuple(xs), tuple(ys)),
            Tier(ROOF_OVERALL, overall[0], overall[1])]

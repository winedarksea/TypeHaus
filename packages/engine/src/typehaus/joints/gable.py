"""Gable-end wall ties — the leg of the uplift chain that had nothing at all.

Every other link was derived and billed: rafter to plate, plate to stud, stud to sill, sill
to pour. The gable end had none, and no check graded one. That is not an oversight anyone
would notice by reading the take-off, because the reason it was missed is the reason it
matters: **no rafter bears on a gable end**, so every bearing rule in this package looks
straight past it. It is the classic out-of-plane wind failure in a house that has everything
else tied.

A gable end is derived, never named. Four questions, and a wall has to answer yes to all:

* it stands on the roof's own storey and its midpoint is **inside the roof's footprint** —
  which is what keeps the breezeway canopy from claiming the garage's walls, since the two
  gable roofs share a storey and only one of them is over those walls;
* it is **exterior** — a weather skin and studs, the same test the stud-plate ties use.
  Without it the attic's interior partitions, which run the same direction and rise to the
  same 9.22 m, would each be handed a row of ties;
* it is **not itself a bearing ref** — an eave wall is tied by the bearing rule already, and
  a second connection at a joint that has one is the double-billing this package exists to
  avoid;
* it runs **perpendicular to the bearing lines**. That is what "gable end" means
  geometrically, and it is the only one of the four that reads off the roof rather than the
  wall.

This catches both shapes in one rule without knowing which it is looking at: catlin's house
roof is rafters on a ridge beam, where the gable wall climbs to the ridge and the ties follow
its raking plate; the garage is trussed, where the wall stops at plate height and the
gable-end truss sits on it. Both are "the exterior wall across the end of the span".
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.hardware.config import FT_TO_M, GableEndTieRules
from typehaus.hardware.plan_geometry import point_in_ring
from typehaus.joints.model import axis_of
from typehaus.resolve.model import ResolvedModel


@dataclass(frozen=True)
class GableEnd:
    """One gable-end wall, and the stations its ties take along the top plate."""

    wall_tag: str
    roof_tag: str
    storey: str
    #: One station per tie, in metres from the wall axis's start. Ends included: a run is a
    #: fencepost count, and a gable end with one tie in the middle is a hinge.
    stations_m: tuple[float, ...]
    p0: tuple
    p1: tuple
    #: The plate the tie lands on — the wall's own top.
    z_m: float
    axis: str
    length_m: float


def _is_exterior_framed_wall(wall) -> bool:
    """A wall with a weather skin *and* studs. Same test ``stud_plate_tie_rows`` applies."""
    return (any(layer.function == "cladding" for layer in wall.layers)
            and any(member.category == "stud" for member in wall.members))


def _bearing_direction(model: ResolvedModel, refs) -> tuple[float, float] | None:
    """The unit direction of the roof's bearing lines, from whichever refs are walls.

    ``None`` when no ref resolves to a wall — catlin's breezeway canopy bears on two beams,
    and a roof with no bearing WALL has no wall across the end of its span to tie.
    """
    for ref in refs:
        wall = model.wall(ref)
        if wall is None:
            continue
        (x0, y0), (x1, y1) = wall.axis
        run = math.hypot(x1 - x0, y1 - y0)
        if run > 1e-9:
            return ((x1 - x0) / run, (y1 - y0) / run)
    return None


def gable_end_ties(model: ResolvedModel, rules: GableEndTieRules) -> list[GableEnd]:
    """Every gable-end wall in the model, with its ties located along the top plate."""
    pitch_m = max(rules.tie_pitch_ft, 0.5) * FT_TO_M
    elements = {element.tag: element
                for storey in model.plan.storeys
                for element in model.plan.storey_elements(storey.tag)}

    found: list[GableEnd] = []
    claimed: set[str] = set()
    for roof in sorted(model.roofs, key=lambda r: r.tag):
        if roof.form != "gable":
            continue
        element = elements.get(roof.tag)
        refs = tuple(getattr(element, "bearing_refs", ()) or ())
        direction = _bearing_direction(model, refs)
        if direction is None:
            continue
        for wall in model.walls:
            if wall.storey != roof.storey or wall.is_foundation or wall.tag in refs:
                continue
            if wall.tag in claimed or not _is_exterior_framed_wall(wall):
                continue
            (x0, y0), (x1, y1) = wall.axis
            length_m = math.hypot(x1 - x0, y1 - y0)
            if length_m < 1e-9:
                continue
            midpoint = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
            if not point_in_ring(midpoint, roof.footprint):
                continue
            # Perpendicular to the bearing lines, within ~5 degrees. A dot product, so a
            # wall at any angle answers honestly rather than only the axis-aligned ones.
            along = ((x1 - x0) / length_m, (y1 - y0) / length_m)
            if abs(along[0] * direction[0] + along[1] * direction[1]) > 0.09:
                continue
            count = max(rules.minimum_ties_per_wall,
                        int(math.floor(length_m / pitch_m + 1e-9)) + 1)
            claimed.add(wall.tag)
            found.append(GableEnd(
                wall_tag=wall.tag, roof_tag=roof.tag, storey=wall.storey,
                stations_m=tuple(
                    (length_m / 2.0 if count == 1 else index * length_m / (count - 1))
                    for index in range(count)),
                p0=wall.axis[0], p1=wall.axis[1],
                z_m=wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m,
                axis=axis_of(wall.axis[0], wall.axis[1]), length_m=length_m))
    return found

"""Does a placeable's *body* actually stand in a neighbour's clear floor space?

A clearance zone is authored as a plan polygon, so a purely 2D overlap test calls every
object in plan-overlap an obstruction — a ceiling light at 8', a switch plate at 4' and a
flush floor register all "block" the floor beside a bed even though none of them costs it a
usable inch. Obstruction is a three-dimensional question, and the built environment already
publishes the answers: ICC A117.1-2017 (the accessibility standard IBC Chapter 11 adopts by
reference) states how much headroom clear floor space needs, how far a wall-mounted object
may reach into a circulation path, and how proud of the floor something may sit before it
counts as a change in level at all.

Every threshold here is one of those published limits, quoted in the comment beside it. The
test is deliberately about geometry, never about domain: an electrical device that genuinely
projects into the space still reports, and a body whose height is unknown reports rather than
being assumed clear, so a missing type dimension surfaces instead of silently passing.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.quantities import Length, inch, m


@dataclass(frozen=True)
class ClearFloorSpaceObstructionThresholds:
    """The published vertical limits that decide whether a body occupies clear floor space.

    Authored in inches because that is the unit A117.1 states first; the soft-metric figures
    the standard prints alongside them (2030 mm, 685 mm, 100 mm, 6.4 mm) are the same limits
    rounded, and rounding them back would move the threshold.
    """

    minimum_headroom_over_clear_floor_space: Length
    lowest_leading_edge_of_a_protruding_object: Length
    maximum_protrusion_into_a_circulation_path: Length
    maximum_untreated_change_in_level: Length
    source: str


CLEAR_FLOOR_SPACE_OBSTRUCTION_THRESHOLDS = ClearFloorSpaceObstructionThresholds(
    # A117.1 307.4 Vertical Clearance: "Vertical clearance shall be 80 inches (2030 mm)
    # minimum." A body whose lowest point is at or above the headroom a person is entitled to
    # is, by definition, out of the way of the floor beneath it.
    minimum_headroom_over_clear_floor_space=inch(80),
    # A117.1 307.2 Protrusion Limits: "Objects with leading edges more than 27 inches
    # (685 mm) and not more than 80 inches (2030 mm) above the floor shall protrude 4 inches
    # (100 mm) maximum horizontally into a circulation path." Kept as a named threshold
    # because it is the *height band the standard polices*; below 27" an object is
    # cane-detectable and §307.2 stops limiting projection at all, which is why a body inside
    # the 4" allowance is clear at any height (→ ``clear_floor_space_obstruction``).
    lowest_leading_edge_of_a_protruding_object=inch(27),
    maximum_protrusion_into_a_circulation_path=inch(4),
    # A117.1 303.2 Vertical: "Changes in level of 1/4 inch (6.4 mm) maximum in height shall be
    # permitted to be vertical." 305.2 Floor Surfaces holds a clear floor space to Section 303,
    # so a body no more proud of the floor than an untreated level change is part of the floor
    # rather than an obstacle standing on it.
    maximum_untreated_change_in_level=inch(0.25),
    source="ICC A117.1-2017 §303.2, §305.2, §307.2, §307.4",
)


@dataclass(frozen=True)
class PlaceableBodyProfile:
    """One placeable's solid, measured against the floor of the storey it stands on.

    ``body_height_m`` is ``None`` when the product type states no height — an honest "unknown",
    not a zero. ``horizontal_projection_from_wall_m`` is ``None`` for anything that is not
    wall-mounted, because A117.1's protrusion allowance is about reaching *off a wall* into a
    path, not about a body standing on the floor.
    """

    base_above_storey_floor_m: float
    body_height_m: float | None
    horizontal_projection_from_wall_m: float | None = None


@dataclass(frozen=True)
class ClearFloorSpaceObstruction:
    """Whether the body obstructs, plus the cited sentence explaining why or why not."""

    obstructs: bool
    reason: str


def clear_floor_space_obstruction(
    body: PlaceableBodyProfile,
    thresholds: ClearFloorSpaceObstructionThresholds = CLEAR_FLOOR_SPACE_OBSTRUCTION_THRESHOLDS,
) -> ClearFloorSpaceObstruction:
    """Classify one body against the clear floor space it overlaps in plan.

    The clauses below are mutually exclusive for real geometry, so their order only decides
    which sentence a reader gets; each names the section it rests on so the claim is checkable.
    """
    if body.body_height_m is None:
        # Never assume "short enough". An unstated height is a data gap, and reporting it keeps
        # the gap visible instead of quietly suppressing a real conflict.
        return ClearFloorSpaceObstruction(
            True, "its type states no height, so its body cannot be shown to clear the space")
    base_m = body.base_above_storey_floor_m
    top_m = base_m + body.body_height_m
    headroom_m = thresholds.minimum_headroom_over_clear_floor_space.meters
    if base_m >= headroom_m:
        return ClearFloorSpaceObstruction(False, (
            f"its lowest point is {_inches(base_m)} above the floor, at or above the "
            f"{_inches(headroom_m)} of headroom A117.1 §307.4 requires, so the floor beneath "
            "it stays clear"))
    level_change_m = thresholds.maximum_untreated_change_in_level.meters
    if top_m <= level_change_m:
        return ClearFloorSpaceObstruction(False, (
            f"it stands {_inches(top_m)} proud of the floor, within the "
            f"{_inches(level_change_m)} vertical change in level A117.1 §303.2 permits "
            "untreated, so it is floor rather than obstacle"))
    protrusion_m = body.horizontal_projection_from_wall_m
    lowest_edge_m = thresholds.lowest_leading_edge_of_a_protruding_object.meters
    protrusion_limit_m = thresholds.maximum_protrusion_into_a_circulation_path.meters
    # The allowance is applied at *any* mounting height, not only in the 27"–80" band §307.2
    # polices. 4" is the projection the standard tolerates where a walking person can strike
    # it face-on; the same 4" lower down, where a cane finds it and §307.2 imposes no limit at
    # all, cannot be worse. Restricting the allowance to the band it is quoted from made every
    # receptacle at 16"-18" AFF an "obstruction" of the floor beside a bed — a 2" cover plate
    # costing a room no usable inch, reported often enough to train the reader to skip the
    # check. A body that genuinely reaches into the room (a low bench, a radiator) projects
    # well past 4" and still reports.
    if protrusion_m is not None and protrusion_m <= protrusion_limit_m:
        return ClearFloorSpaceObstruction(False, (
            f"it is wall-mounted with its leading edge {_inches(base_m)} above the floor and "
            f"projects {_inches(protrusion_m)}, within the {_inches(protrusion_limit_m)} "
            f"A117.1 §307.2 allows an object to protrude into a circulation path (the limit "
            f"is stated for leading edges above {_inches(lowest_edge_m)}; below that the "
            "standard sets no limit at all)"))
    return ClearFloorSpaceObstruction(True, (
        f"its body occupies {_inches(base_m)}–{_inches(top_m)} above the floor"))


def _inches(meters: float) -> str:
    """Render a threshold comparison in the unit the cited standard states it in."""
    return f'{m(meters).inches:g}"'

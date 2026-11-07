"""R311.3's interior side: the threshold's rise over the finished floor inside the door.

Minn. R. 1309.0311 subp. 1: R311.3.1 holds the required egress door's floor or landing to
1.5" below the top of the threshold on both sides (7.75" applies only to the exterior side
of a door that does not swing over it); MN R311.3.2 holds every other exterior door to 7.75".
The floor is read off the doorway assembly's ``adjacent_floors``, never assumed.
"""

from __future__ import annotations

from typehaus.quantities import inch

EGRESS_INTERIOR_STEP = inch(1.5)
OTHER_INTERIOR_STEP = inch(7.75)


def interior_step_verdict(ctx, opening, threshold_m: float, egress: bool):
    """``(result, text)``: result is ``"pass"``, ``"fail"`` or ``"unknown"``."""
    assembly = getattr(opening, "doorway", None)
    placement = assembly.exterior_placement if assembly else None
    if placement is None:
        return "unknown", "no doorway assembly names the interior floor"
    interior = assembly.adjacent_floors[1 if placement.outward_sign < 0 else 0]
    if interior is None or interior.surface_m is None:
        stair = _flight_to_threshold(ctx, opening)
        if stair is not None:
            # No floor inside: the flight rises to the threshold, which R311.7.6's
            # exception governs (code.R311_7_6_door_at_stair_head grades the swing).
            return "pass", (f"{stair} rises to the threshold with no top landing "
                            "(R311.7.6 exception, code.R311_7_6_door_at_stair_head)")
        return "unknown", "interior finished floor is missing"
    step = threshold_m - interior.surface_m
    limit = (EGRESS_INTERIOR_STEP if egress else OTHER_INTERIOR_STEP).meters
    rule = "R311.3.1, egress" if egress else "MN R311.3.2"
    text = (f'threshold {step / .0254:.2f}" over the interior floor '
            f'({rule}: <= {limit / .0254:.2f}")')
    return ("pass" if step <= limit + 1e-6 else "fail"), text


def _flight_to_threshold(ctx, opening):
    """The flight with no floor opening whose head is this door, or None."""
    from typehaus.checks.code.mn_residential.stair_arrival import _door_at_head
    from typehaus.resolve.stairs.walkline import stair_walk_stations

    for stair in ctx.model.stairs:
        if getattr(ctx.plan.by_tag(stair.tag), "floor_opening", None):
            continue
        route = stair_walk_stations(stair)
        door = _door_at_head(ctx.model, stair, route) if len(route) >= 2 else None
        if door is not None and door.tag == opening.tag:
            return stair.tag
    return None

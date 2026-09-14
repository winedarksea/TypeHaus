"""Sill-plate joints: mudsill anchors, embedded holdowns, and the tie plate above them.

All three read the resolved *construction returns* — a framed wall stacked on a concrete
wall produces a return, and the return is the plate. Following the model rather than
searching for "walls that look like sills" is what keeps the anchors on the plate the
resolver actually generated.

The three are one family and one seam. A wall on concrete is a **sill**: its plate is
anchored through to the pour by a mudsill anchor, and a tie plate there would be a second
connection at a joint that already has one. A wall on a framed floor band is the case the
tie plate is for. :func:`tie_plate_stations` and :func:`mudsill_anchor_stations` therefore
partition the walls between them and never both fire on one plate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.hardware.config import FT_TO_M, SillPlateAnchorRules, UpliftTieRules
from typehaus.hardware.plan_geometry import centerline_endpoints, merge_coincident_points
from typehaus.joints.model import axis_of
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel


@dataclass(frozen=True)
class Station:
    """One located part along a run: where it is, what it sits on, which way it points."""

    run_tag: str
    storey: str
    point_m: tuple
    z_m: float
    axis: str


def sill_plate_returns(model: ResolvedModel, category: str) -> list:
    return [ret for ret in model.construction_returns if ret.takeoff_category == category]


def _anchors_on_run(length_m: float, pitch_m: float, minimum: int) -> int:
    """The count on one plate run: pitch, fencepost, never below the code minimum.

    Stated once because :func:`mudsill_anchor_stations` and ``takeoff/anchors.py``'s row
    must agree exactly — a station list one part longer than the order is a drawing that
    shows hardware nobody bought.
    """
    return max(minimum, int(math.floor(length_m / pitch_m + 1e-9)) + 1)


def mudsill_anchor_stations(model: ResolvedModel, rules: SillPlateAnchorRules,
                            sill_category: str) -> list:
    """Every MASA along every wood sill plate landing on concrete.

    The count per run is the rule ``takeoff/anchors.mudsill_anchor_rows`` bills; the
    *placement* is these evenly spread end to end, which is what a fencepost count means on
    the ground. A one-anchor run takes it at the midpoint rather than at an end, because a
    plate piece short enough to want one anchor wants it in the middle.
    """
    pitch_m = rules.mudsill_anchor_pitch_ft * FT_TO_M
    found: list[Station] = []
    for ret in sill_plate_returns(model, sill_category):
        start, end = centerline_endpoints(list(ret.outline))
        count = _anchors_on_run(ret.length_m, pitch_m, rules.minimum_anchors_per_run)
        axis = axis_of(start, end)
        for index in range(count):
            fraction = 0.5 if count == 1 else index / (count - 1)
            found.append(Station(
                run_tag=ret.tag, storey=ret.storey,
                point_m=(start[0] + (end[0] - start[0]) * fraction,
                         start[1] + (end[1] - start[1]) * fraction),
                # The pour top: the underside of the plate the anchor comes up through.
                z_m=ret.z0_m, axis=axis))
    return found


def strap_holdown_locations(model: ResolvedModel, rules: SillPlateAnchorRules,
                            sill_category: str) -> tuple[list, list]:
    """``(sill runs, merged end locations)`` — the geometry behind the holdown count.

    Kept apart from the row so the pour-day handoff list can hand a crew the *places*, not
    just the number. Run ends that meet at a corner or a plate butt joint are one location,
    not two, so the endpoints are merged before anything is counted.
    """
    returns = sill_plate_returns(model, sill_category)
    if not returns:
        return [], []
    endpoints: list = []
    for ret in returns:
        endpoints.extend(centerline_endpoints(list(ret.outline)))
    return returns, merge_coincident_points(
        endpoints, rules.coincident_end_tolerance_in * M_PER_IN)


def strap_holdown_stations(model: ResolvedModel, rules: SillPlateAnchorRules,
                           sill_category: str) -> list:
    """``holdowns_per_run_end`` located at each distinct sill-run end.

    A location taking two straps gets two entries, so the list and the order are the same
    number. They are co-located: both are cast at the one end, on opposite faces of the
    plate, and the model has nothing to say about which face is which.
    """
    returns, locations = strap_holdown_locations(model, rules, sill_category)
    if not returns:
        return []
    # Every run shares one pour top in practice; take the lowest, which is the pour a
    # strap at a corner between two runs is actually cast into.
    z_m = min(ret.z0_m for ret in returns)
    by_point = {}
    for ret in returns:
        start, end = centerline_endpoints(list(ret.outline))
        for point in (start, end):
            by_point[point] = (ret.tag, ret.storey, axis_of(start, end), ret.z0_m)
    found: list[Station] = []
    for point in locations:
        run_tag, storey, axis, run_z = min(
            (entry for key, entry in by_point.items()
             if abs(key[0] - point[0]) <= rules.coincident_end_tolerance_in * M_PER_IN
             and abs(key[1] - point[1]) <= rules.coincident_end_tolerance_in * M_PER_IN),
            default=("", "", "x", z_m))
        for _ in range(rules.holdowns_per_run_end):
            found.append(Station(run_tag=run_tag, storey=storey,
                                 point_m=(point[0], point[1]), z_m=run_z, axis=axis))
    return found


def tie_plate_walls(model: ResolvedModel) -> list:
    """Every framed wall standing on a framed floor band.

    The sill-on-concrete case is already anchored (:func:`mudsill_anchor_stations`); this is
    the joint *above* it, where a wall's bottom plate meets the rim and band of the floor it
    stands on and nothing but the nailing holds the two together laterally. The walls are
    exactly the upper halves of the resolved stack edges, so the rule follows the model's own
    account of what stands on what.
    """
    foundations = {wall.tag for wall in model.walls if wall.is_foundation}
    # Only the framed-on-framed stack edges. A wall standing on concrete is a sill, and its
    # plate is already anchored through to the pour by the mudsill anchors — a tie plate
    # there would be a second connection at a joint that has one, which is exactly the
    # double-billing ``Material.exposed_fastener`` exists to prevent elsewhere.
    stacked_above = {edge.upper_wall for edge in model.stack_edges
                     if edge.lower_wall not in foundations}
    return [wall for wall in model.walls
            if wall.tag in stacked_above and not wall.is_foundation
            and any(member.category == "stud" for member in wall.members)]


def tie_plate_stations(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """LTP4s along the bottom plate of every wall :func:`tie_plate_walls` returns."""
    pitch_m = rules.tie_plate_pitch_ft * FT_TO_M
    found: list[Station] = []
    for wall in tie_plate_walls(model):
        (x0, y0), (x1, y1) = wall.axis
        length_m = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        count = max(rules.minimum_tie_plates_per_wall, int(length_m / pitch_m) + 1)
        axis = axis_of(wall.axis[0], wall.axis[1])
        for index in range(count):
            fraction = 0.5 if count == 1 else index / (count - 1)
            found.append(Station(
                run_tag=wall.tag, storey=wall.storey,
                point_m=(x0 + (x1 - x0) * fraction, y0 + (y1 - y0) * fraction),
                z_m=wall.z0_m, axis=axis))
    return found

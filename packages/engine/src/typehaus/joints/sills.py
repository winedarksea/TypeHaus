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

A non-bearing, unbraced partition on a slab is pinned (:func:`partition_pin_stations`),
not cast-in: the slab is poured after the footings and a MASA needs a form board. Derived
STHDs land only at exterior foundation corners; every other holdown is authored.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.hardware.config import FT_TO_M, SillPlateAnchorRules, UpliftTieRules
from typehaus.hardware.plan_geometry import centerline_endpoints
from typehaus.joints.model import axis_of
from typehaus.model.braced_wall import BracedWallPanel
from typehaus.model.enums import ConnectorKind
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.partition import bearing_ref_tags, is_clad, is_interior_partition


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


def _upper_wall(model: ResolvedModel, ret):
    walls = {wall.tag: wall for wall in model.walls}
    return next((walls[tag] for tag in ret.element_tags[1:] if tag in walls), None)


def _on_foundation_wall(model: ResolvedModel, ret) -> bool:
    return bool(ret.element_tags) and any(
        wall.tag == ret.element_tags[0] and wall.is_foundation for wall in model.walls)


def _is_pinned_partition(model: ResolvedModel, ret, bearing: frozenset, braced: set) -> bool:
    """A non-bearing, unbraced partition on a slab: pinned, never cast-in.

    The slab is the second pour, after the bearing walls' footings, so a MASA has no form
    board to nail to and a plate that carries nothing has nothing for it to resist.
    """
    if _on_foundation_wall(model, ret):
        return False
    upper = _upper_wall(model, ret)
    return (upper is not None and upper.tag not in braced
            and is_interior_partition(model, upper, bearing))


def _split_returns(model: ResolvedModel, category: str) -> tuple[list, list]:
    """``(cast-in anchored, pinned)`` sill returns."""
    if model.plan is None:
        return sill_plate_returns(model, category), []
    bearing = bearing_ref_tags(model.plan)
    braced = {panel.wall_ref for panel in model.plan.all_elements()
              if isinstance(panel, BracedWallPanel)}
    anchored, pinned = [], []
    for ret in sill_plate_returns(model, category):
        (pinned if _is_pinned_partition(model, ret, bearing, braced) else anchored).append(ret)
    return anchored, pinned


def anchored_sill_returns(model: ResolvedModel, category: str) -> list:
    """The sill runs that take MASA: foundation walls, and bearing/braced walls on footings."""
    return _split_returns(model, category)[0]


def pinned_partition_returns(model: ResolvedModel, category: str) -> list:
    return _split_returns(model, category)[1]


def _anchors_on_run(length_m: float, pitch_m: float, minimum: int) -> int:
    """The count on one plate run: pitch, fencepost, never below the code minimum.

    Stated once because :func:`mudsill_anchor_stations` and ``takeoff/anchors.py``'s row
    must agree exactly — a station list one part longer than the order is a drawing that
    shows hardware nobody bought.
    """
    return max(minimum, int(math.floor(length_m / pitch_m + 1e-9)) + 1)


def _stations_on(returns: list, pitch_m: float, minimum: int, end_m: float) -> list:
    """Parts spread evenly between ``end_m`` in from each end of every run.

    A one-part run takes it at the midpoint. The inset shrinks on a run too short for it,
    so two parts never cross.
    """
    found: list[Station] = []
    for ret in returns:
        start, end = centerline_endpoints(list(ret.outline))
        count = _anchors_on_run(ret.length_m, pitch_m, minimum)
        inset = min(end_m, ret.length_m / 4.0) / ret.length_m if ret.length_m > 0 else 0.0
        axis = axis_of(start, end)
        for index in range(count):
            fraction = 0.5 if count == 1 else inset + (1 - 2 * inset) * index / (count - 1)
            found.append(Station(
                run_tag=ret.tag, storey=ret.storey,
                point_m=(start[0] + (end[0] - start[0]) * fraction,
                         start[1] + (end[1] - start[1]) * fraction),
                # The pour top: the underside of the plate the part comes up through.
                z_m=ret.z0_m, axis=axis))
    return found


def mudsill_anchor_stations(model: ResolvedModel, rules: SillPlateAnchorRules,
                            sill_category: str) -> list:
    """Every MASA along every cast-in-anchored sill plate."""
    return _stations_on(anchored_sill_returns(model, sill_category),
                        rules.mudsill_anchor_pitch_ft * FT_TO_M,
                        rules.minimum_anchors_per_run, rules.end_distance_in * M_PER_IN)


def partition_pin_stations(model: ResolvedModel, rules: SillPlateAnchorRules,
                           sill_category: str) -> list:
    """Powder-actuated pins along every non-bearing partition plate on the slab."""
    return _stations_on(pinned_partition_returns(model, sill_category),
                        rules.partition_pin_pitch_in * M_PER_IN,
                        rules.minimum_anchors_per_run, rules.end_distance_in * M_PER_IN)


def _exterior_corner_runs(model: ResolvedModel, sill_category: str) -> list:
    """Anchored sill runs on a foundation wall under a clad (envelope) wall."""
    return [ret for ret in anchored_sill_returns(model, sill_category)
            if _on_foundation_wall(model, ret)
            and (upper := _upper_wall(model, ret)) is not None and is_clad(upper)]


def _authored_embedded_holdowns(model: ResolvedModel) -> list:
    """Plan points of every authored cast-in strap holdown (an STHD by its size)."""
    return [(element.position.x.meters, element.position.y.meters)
            for element in model.plan.all_elements()
            if getattr(element, "kind", None) is ConnectorKind.HOLD_DOWN
            and getattr(element, "position", None) is not None
            and str(getattr(element, "size", "") or "").upper().startswith("STHD")]


def strap_holdown_locations(model: ResolvedModel, rules: SillPlateAnchorRules,
                            sill_category: str) -> tuple[list, list]:
    """``(exterior sill runs, corner locations)`` — the geometry behind the holdown count.

    A corner is a run end shared, at the same pour top, by two runs that are not
    collinear. A butt joint on a straight line is not a corner, and two ends at different
    pour tops (a curb beside a full-height wall) are not one joint. An authored STHD near
    the corner (a braced-panel end) stands the derived one down.
    """
    returns = _exterior_corner_runs(model, sill_category)
    if not returns:
        return [], []
    tol = rules.coincident_end_tolerance_in * M_PER_IN
    ends = []
    for ret in returns:
        start, end = centerline_endpoints(list(ret.outline))
        ends.extend((point, axis_of(start, end), ret.z0_m) for point in (start, end))
    authored = _authored_embedded_holdowns(model)
    standdown = rules.authored_holdown_standdown_in * M_PER_IN
    corners: list = []
    for point, axis, z in ends:
        if any(math.dist(point, kept) <= tol for kept in corners):
            continue
        if any(math.dist(point, other) <= standdown for other in authored):
            continue
        if any(other_axis != axis and math.dist(point, other) <= tol and abs(z - oz) <= tol
               for other, other_axis, oz in ends):
            corners.append(point)
    return returns, corners


def strap_holdown_stations(model: ResolvedModel, rules: SillPlateAnchorRules,
                           sill_category: str) -> list:
    """``holdowns_per_run_end`` at each exterior foundation corner."""
    returns, locations = strap_holdown_locations(model, rules, sill_category)
    tol = rules.coincident_end_tolerance_in * M_PER_IN
    found: list[Station] = []
    runs = [(ret, centerline_endpoints(list(ret.outline))) for ret in returns]
    for point in locations:
        ret, ends = next((ret, ends) for ret, ends in runs
                         if any(math.dist(point, p) <= tol for p in ends))
        end_axis = axis_of(*ends)
        for _ in range(rules.holdowns_per_run_end):
            found.append(Station(run_tag=ret.tag, storey=ret.storey,
                                 point_m=(point[0], point[1]), z_m=ret.z0_m, axis=end_axis))
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

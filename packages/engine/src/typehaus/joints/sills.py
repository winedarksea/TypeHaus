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
from dataclasses import dataclass, replace

from typehaus.hardware.catalog import ROLE_MUDSILL_ANCHOR, ROLE_SILL_ANCHOR_BOLT
from typehaus.hardware.config import FT_TO_M, SillPlateAnchorRules, UpliftTieRules
from typehaus.hardware.connector_dimensions import LATERAL_TIE_PLATE_DIMENSIONS
from typehaus.hardware.plan_geometry import centerline_endpoints
from typehaus.joints.model import axis_of
from typehaus.model.braced_wall import BracedWallPanel
from typehaus.model.enums import ConnectorKind
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.ties import EMBEDDED_STRAPS
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.partition import bearing_ref_tags, is_clad, is_interior_partition
from typehaus.resolve.sill_bearing import band_centre_ends, bolt_offset_m, stud_band

#: A derived STHD draws as the STHD14 (``tie_mesh``'s representative).
_STRAP_HALF_WIDTH_M = EMBEDDED_STRAPS["STHD14"].width_in / 2.0 * M_PER_IN


@dataclass(frozen=True)
class Station:
    """One located part along a run: where it is, what it sits on, which way it points."""

    run_tag: str
    storey: str
    point_m: tuple
    z_m: float
    axis: str
    role: str = ROLE_MUDSILL_ANCHOR
    outward_xy: tuple | None = None


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


#: MASAZ (ESR-2555) is published for 2x4 and 2x6 sills; a wider plate takes cast-in bolts.
_MASA_MAX_SILL_M = 5.625 * M_PER_IN


def sill_anchor_role(ret) -> str:
    return ROLE_MUDSILL_ANCHOR if ret.thickness_m <= _MASA_MAX_SILL_M else ROLE_SILL_ANCHOR_BOLT


def _stations_on(returns: list, pitch_m: float, minimum: int, end_m: float,
                 model=None) -> list:
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
        role = sill_anchor_role(ret) if model is not None else ROLE_MUDSILL_ANCHOR
        # A bolt sits in the plate's middle third and the core, not on its centreline.
        off = bolt_offset_m(model, ret) if role == ROLE_SILL_ANCHOR_BOLT else 0.0
        nx, ny = (-(end[1] - start[1]) / ret.length_m * off,
                  (end[0] - start[0]) / ret.length_m * off) if off else (0.0, 0.0)
        for index in range(count):
            fraction = 0.5 if count == 1 else inset + (1 - 2 * inset) * index / (count - 1)
            found.append(Station(
                run_tag=ret.tag, storey=ret.storey,
                point_m=(start[0] + (end[0] - start[0]) * fraction + nx,
                         start[1] + (end[1] - start[1]) * fraction + ny),
                # The pour top: the underside of the plate the part comes up through.
                z_m=ret.z0_m, axis=axis, role=role))
    return found


def mudsill_anchor_stations(model: ResolvedModel, rules: SillPlateAnchorRules,
                            sill_category: str) -> list:
    """Every MASA along every cast-in-anchored sill plate."""
    returns = anchored_sill_returns(model, sill_category)
    found = _stations_on(returns, rules.mudsill_anchor_pitch_ft * FT_TO_M,
                         rules.minimum_anchors_per_run, rules.end_distance_in * M_PER_IN,
                         model=model)
    if model.plan is None:
        return found
    return _snap_to_blocking(model, _clear_of_straps(model, rules, sill_category, found))


#: Half a MASA's 3" width, or of a bolt's 3"x3" washer.
_ANCHOR_HALF_WIDTH_M = 1.5 * M_PER_IN
#: A 12 ga strap leaf (0.105") with a hair of clearance.
_LEAF_M = 0.125 * M_PER_IN
#: An anchor this close across a strap's run stands on the same sill.
_SAME_SILL_M = 6.0 * M_PER_IN
#: R403.1.6: an anchor within 12" of each plate end. A move past it is not made; the clash shows.
_CODE_END_M = 12.0 * M_PER_IN


def _authored_strap_frames(model: ResolvedModel) -> list:
    """``(point, axis)`` of each authored STHD: its own axis, else its framed wall's."""
    out = []
    for element in model.plan.all_elements() if model.plan is not None else ():
        if getattr(element, "kind", None) is not ConnectorKind.HOLD_DOWN \
                or getattr(element, "position", None) is None \
                or not str(getattr(element, "size", "") or "").upper().startswith("STHD"):
            continue
        axis = (element.axis or "").lstrip("-") or next(
            (axis_of(*w.axis[:2]) for tag in element.connects
             if (w := model.wall(tag)) is not None and not w.is_foundation), None)
        if axis:
            out.append((element.position.xy_m, axis))
    return out


def _clear_of_straps(model: ResolvedModel, rules: SillPlateAnchorRules, sill_category: str,
                     found: list) -> list:
    """An anchor that would foul a corner STHD's leaf moves just clear of it.

    On the strap's own sill it moves past the strap, away from the nearer sill end; on the
    crossing sill its washer edge moves off the leaf.
    """
    _, corners = _corner_points(model, rules, sill_category)
    standdown = rules.authored_holdown_standdown_in * M_PER_IN
    straps = [(t.point_m, t.axis) for t in strap_holdown_stations(model, rules, sill_category)
              if t.outward_xy] + [(p, axis) for p, axis in _authored_strap_frames(model)
                                  if any(math.dist(p, c) <= standdown for c in corners)]
    ends = [(p, axis_of(*line)) for ret in anchored_sill_returns(model, sill_category)
            for line in (centerline_endpoints(list(ret.outline)),) for p in line]
    clear = _STRAP_HALF_WIDTH_M + _ANCHOR_HALF_WIDTH_M
    off_leaf = _ANCHOR_HALF_WIDTH_M + _LEAF_M
    out = []
    for station in found:
        for point, strap_axis in straps:
            d = (1.0, 0.0) if strap_axis == "x" else (0.0, 1.0)
            n = (-d[1], d[0])
            rel = (station.point_m[0] - point[0], station.point_m[1] - point[1])
            along, across = rel[0] * d[0] + rel[1] * d[1], rel[0] * n[0] + rel[1] * n[1]
            if abs(along) >= clear:
                continue
            if station.axis == strap_axis and abs(across) < _SAME_SILL_M:
                end = min((e for e, e_axis in ends if e_axis == strap_axis),
                          key=lambda e: math.dist(e, point), default=None)
                if end is None:
                    continue
                inward = 1.0 if (point[0] - end[0]) * d[0] + (point[1] - end[1]) * d[1] > 0 \
                    else -1.0
                step, axis = inward * clear - along, d
                at = (station.point_m[0] - end[0]) * d[0] + (station.point_m[1] - end[1]) * d[1]
                if abs(at + step) > _CODE_END_M:
                    continue
            elif (station.axis != strap_axis and station.role == ROLE_SILL_ANCHOR_BOLT
                  and abs(across) < off_leaf):
                step, axis = math.copysign(off_leaf, across) - across, n
            else:
                continue
            station = replace(station, point_m=(station.point_m[0] + axis[0] * step,
                                                station.point_m[1] + axis[1] * step))
        out.append(station)
    return out


#: Minn. R. 1309.0404, Table R404.1(1) footnote f: "Blocking shall be installed within 8
#: inches of an anchor bolt location."
_BLOCK_TO_ANCHOR_M = 8.0 * M_PER_IN


def _snap_to_blocking(model: ResolvedModel, found: list) -> list:
    """Add an anchor at each wall-top block station with none within 8".

    Added, not moved: moving one strands a plate end or opens the pitch. The takeoff counts
    these stations, so the order still matches the drawing.
    """
    from typehaus.joints.wall_top import along_wall, parallel_runs

    walls = {wall.tag: wall for wall in model.walls}
    found = list(found)
    for run in parallel_runs(model):
        wall = walls[run.wall_tag]
        # Return tags are a construction KIND, shared by every sill, so an anchor is placed
        # on this wall by where it stands: on its axis band, inside its length.
        length = math.hypot(wall.axis[1][0] - wall.axis[0][0], wall.axis[1][1] - wall.axis[0][1])
        mine = []
        for s in found:
            along, offset = along_wall(wall, s.point_m)
            if offset <= wall.thickness_m / 2.0 and 0 <= along <= length:
                mine.append((along, s))
        if not mine:
            continue
        for block in run.stations:
            along, near = min(mine, key=lambda m: abs(m[0] - block.along_m))
            if abs(along - block.along_m) <= _BLOCK_TO_ANCHOR_M:
                continue
            shift = block.along_m - along
            (ax, ay), (bx, by) = wall.axis[0][:2], wall.axis[1][:2]
            found.append(Station(
                run_tag=near.run_tag, storey=near.storey,
                point_m=(near.point_m[0] + (bx - ax) / (length or 1.0) * shift,
                         near.point_m[1] + (by - ay) / (length or 1.0) * shift),
                z_m=near.z_m, axis=near.axis, role=near.role))
    return found


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


def _corner_points(model: ResolvedModel, rules: SillPlateAnchorRules,
                   sill_category: str) -> tuple[list, list]:
    """``(exterior sill runs, every corner)``, before any authored strap stands one down."""
    returns = _exterior_corner_runs(model, sill_category)
    tol = rules.coincident_end_tolerance_in * M_PER_IN
    ends = []
    for ret in returns:
        start, end = band_centre_ends(model, ret)
        ends.extend((point, axis_of(start, end), ret.z0_m) for point in (start, end))
    corners: list = []
    for point, axis, z in ends:
        if any(math.dist(point, kept) <= tol for kept in corners):
            continue
        if any(other_axis != axis and math.dist(point, other) <= tol and abs(z - oz) <= tol
               for other, other_axis, oz in ends):
            corners.append(point)
    return returns, corners


def strap_holdown_locations(model: ResolvedModel, rules: SillPlateAnchorRules,
                            sill_category: str) -> tuple[list, list]:
    """``(exterior sill runs, corner locations)`` — the geometry behind the holdown count.

    A corner is a run end shared, at the same pour top, by two runs that are not
    collinear. A butt joint on a straight line is not a corner, and two ends at different
    pour tops (a curb beside a full-height wall) are not one joint. An authored STHD near
    the corner (a braced-panel end) stands the derived one down.
    """
    returns, corners = _corner_points(model, rules, sill_category)
    authored = _authored_embedded_holdowns(model)
    standdown = rules.authored_holdown_standdown_in * M_PER_IN
    return returns, [point for point in corners
                     if not any(math.dist(point, other) <= standdown for other in authored)]


def _span(polygon, axis: tuple) -> tuple[float, float]:
    offsets = [p[0] * axis[0] + p[1] * axis[1] for p in polygon]
    return min(offsets), max(offsets)


def _centre(polygon, axis: tuple) -> float:
    return sum(_span(polygon, axis)) / 2.0


def _inside_corner(model: ResolvedModel, ret, ends, other) -> tuple | None:
    """``(point, outward)``: the strap on ``ret``'s stud-band inside face, inside the corner.

    Across the run the leaf lies on the band's interior face; along it the strap's centre
    stands half its width past the perpendicular band's interior face (S-103's notched sill).
    """
    band, perp = stud_band(model, ret), stud_band(model, other)
    run = math.dist(*ends)
    if band is None or perp is None or run <= 0.0:
        return None
    d = ((ends[1][0] - ends[0][0]) / run, (ends[1][1] - ends[0][1]) / run)
    n = (-d[1], d[0])
    s_n = 1.0 if _centre(perp, n) > _centre(band, n) else -1.0
    s_d = 1.0 if _centre(band, d) > _centre(perp, d) else -1.0
    across = _span(band, n)[1 if s_n > 0 else 0]
    along = _span(perp, d)[1 if s_d > 0 else 0] + s_d * _STRAP_HALF_WIDTH_M
    point = (d[0] * along + n[0] * across, d[1] * along + n[1] * across)
    return point, (-s_n * n[0], -s_n * n[1])


def strap_holdown_stations(model: ResolvedModel, rules: SillPlateAnchorRules,
                           sill_category: str) -> list:
    """``holdowns_per_run_end`` at each exterior foundation corner, inside the corner."""
    returns, locations = strap_holdown_locations(model, rules, sill_category)
    tol = rules.coincident_end_tolerance_in * M_PER_IN
    found: list[Station] = []
    runs = [(ret, band_centre_ends(model, ret)) for ret in returns]
    for point in locations:
        at = [(ret, ends) for ret, ends in runs if any(math.dist(point, p) <= tol for p in ends)]
        ret, ends = at[0]
        end_axis = axis_of(*ends)
        other = next((o for o, o_ends in at if axis_of(*o_ends) != end_axis), None)
        placed = _inside_corner(model, ret, ends, other) if other is not None else None
        xy, outward = placed if placed is not None else ((point[0], point[1]), None)
        for _ in range(rules.holdowns_per_run_end):
            found.append(Station(run_tag=ret.tag, storey=ret.storey, point_m=xy,
                                 z_m=ret.z0_m, axis=end_axis, outward_xy=outward))
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


def split_segments(segments, excluded_start, excluded_end):
    """Subtract one opening interval from a set of along-wall segments."""
    remaining = []
    for start, end in segments:
        if excluded_end <= start or excluded_start >= end:
            remaining.append((start, end))
        else:
            if start < excluded_start:
                remaining.append((start, excluded_start))
            if excluded_end < end:
                remaining.append((excluded_end, end))
    return remaining


def tie_plate_stations(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """LTP4s along the bottom plate, excluding bodies that cross an opening.

    Framing can retain a sole plate across a doorway; that temporary board is not a
    reason to put permanent steel in the passage. Raised openings only exclude a plate
    when their actual vertical void reaches its body.
    """
    pitch_m = rules.tie_plate_pitch_ft * FT_TO_M
    half_width_m = LATERAL_TIE_PLATE_DIMENSIONS.width_in * M_PER_IN / 2
    half_height_m = LATERAL_TIE_PLATE_DIMENSIONS.height_in * M_PER_IN / 2
    openings_by_wall: dict[str, list] = {}
    for opening in model.openings:
        if opening.depth_m is None:
            openings_by_wall.setdefault(opening.host_wall, []).append(opening)
    found: list[Station] = []
    for wall in tie_plate_walls(model):
        (x0, y0), (x1, y1) = wall.axis
        length_m = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        # Split the usable centreline at jambs, allowing the full plate body to clear.
        # Spacing across a void is meaningless; each solid segment needs its own ties.
        usable_segments = [(0.0, length_m)]
        for opening in openings_by_wall.get(wall.tag, ()):
            if not (
                wall.base_ref_z_m + opening.sill_m < wall.z0_m + half_height_m - 1e-9
                and wall.base_ref_z_m + opening.sill_m + opening.height_m
                > wall.z0_m - half_height_m + 1e-9
            ):
                continue
            excluded_start = opening.center_along_m - opening.width_m / 2 - half_width_m
            excluded_end = opening.center_along_m + opening.width_m / 2 + half_width_m
            usable_segments = split_segments(usable_segments, excluded_start, excluded_end)
        axis = axis_of(wall.axis[0], wall.axis[1])
        for segment_start, segment_end in usable_segments:
            segment_length = segment_end - segment_start
            count = max(rules.minimum_tie_plates_per_wall,
                        math.ceil(segment_length / pitch_m) + 1)
            for index in range(count):
                along_m = (segment_start + segment_end) / 2 if count == 1 else (
                    segment_start + segment_length * index / (count - 1))
                fraction = along_m / length_m if length_m else 0.5
                found.append(Station(
                    run_tag=wall.tag, storey=wall.storey,
                    point_m=(x0 + (x1 - x0) * fraction, y0 + (y1 - y0) * fraction),
                    z_m=wall.z0_m, axis=axis))
    return found

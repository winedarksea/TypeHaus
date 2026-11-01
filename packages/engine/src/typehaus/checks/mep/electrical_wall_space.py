"""Electrical wall-space interpretation and coverage on a room's perimeter.

A roof bearing plate closes the room graph without establishing that NEC wall space
exists there. Keep that uncertainty local to electrical checks, not room/trim geometry.
All returned intervals are linear metres in [0, perimeter], split at the ring seam.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.refs import FollowRoof
from typehaus.resolve.intervals import Interval, merge, subtract
from typehaus.resolve.model import ResolvedModel, ResolvedRoom
from typehaus.resolve.room_perimeter import merged_intervals, perimeter_length
from typehaus.resolve.room_walls import bounding_wall_arcs

MAX_RECEPTACLE_REACH_M = 6 * 0.3048
MIN_WALL_SPACE_M = 2 * 0.3048
DISTANCE_TOLERANCE_M = 1e-9
# Preserve the existing projection tolerance at doorway/cabinet ends.
DEVICE_STATION_TOLERANCE_M = 0.05


#: A wall must stand this far into the room's clear face to be traced (excludes slivers
#: where a bounding wall's face meets the ring).
_INSIDE_WALL_MIN_M2 = 1e-4


def floor_line_ring(model: ResolvedModel, room: ResolvedRoom) -> list:
    """``clear_face``, traced round any wall standing inside it (NEC 210.52(A)(1)).

    An open plan can hold a wall within the room's ring (catlin's W-M-C5 in RM-M-LIVING);
    its faces are wall space along the floor line. A wall joined to the ring becomes a
    notch; a freestanding one (a hole) or one splitting the room is left as it was.
    """
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient

    from typehaus.resolve.overlay import difference, intersection, union_all

    ring = [tuple(point) for point in room.clear_face]
    if len(ring) < 3:
        return ring
    area = Polygon(ring)
    if not area.is_valid:
        return ring
    x0, y0, x1, y1 = area.bounds
    inside = []
    for wall in model.walls:
        if wall.storey != room.storey:
            continue
        points = [p for layer in wall.layers if layer.polygon for p in layer.polygon]
        if not points or (max(p[0] for p in points) <= x0 or min(p[0] for p in points) >= x1
                          or max(p[1] for p in points) <= y0
                          or min(p[1] for p in points) >= y1):
            continue
        body = union_all([Polygon(layer.polygon) for layer in wall.layers
                          if layer.polygon and len(layer.polygon) >= 3])
        if not body.is_empty and intersection(body, area).area > _INSIDE_WALL_MIN_M2:
            inside.append(body)
    if not inside:
        return ring
    cut = difference(area, union_all(inside))
    if cut.geom_type != "Polygon" or cut.is_empty or Polygon(cut.exterior).equals(area):
        return ring  # split, emptied, or only holes: the ring stands
    sign = 1.0 if area.exterior.is_ccw else -1.0
    return [tuple(point) for point in orient(cut, sign).exterior.coords[:-1]]


def facing_well_intervals(plan, ring: list, storey_tag: str,
                          ledge_m: float) -> list[Interval]:
    """Ring intervals within ``ledge_m`` of a well the face looks onto.

    ``room_perimeter.floor_opening_intervals`` with one filter: an edge counts only where the
    floor strip in front of it (its room side, ``ledge_m`` deep) meets the well, so a well
    behind a wall (W-M-C5's other face) breaks nothing.
    """
    import math

    from shapely.geometry import LineString, Point, Polygon

    wells = [Polygon([point.xy_m for point in element.outline])
             for element in plan.storey_elements(storey_tag)
             if element.element_kind == "FloorOpening" and element.purpose.value != "chase"]
    wells = [well for well in wells if well.is_valid and not well.is_empty]
    if not wells or len(ring) < 3:
        return []
    side = 1.0 if Polygon(ring).exterior.is_ccw else -1.0
    out: list[Interval] = []
    start = 0.0
    for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if length <= 0:
            continue
        tx, ty = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        nx, ny = -ty * side * ledge_m, tx * side * ledge_m  # toward the room
        strip = Polygon([a, b, (b[0] + nx, b[1] + ny), (a[0] + nx, a[1] + ny)])
        edge = LineString([a, b])
        for well in wells:
            if not strip.intersects(well):
                continue
            hit = edge.intersection(well.buffer(ledge_m))
            for piece in getattr(hit, "geoms", (hit,)):
                if piece.is_empty or piece.length <= 0:
                    continue
                offsets = [edge.project(Point(c)) for c in piece.coords]
                out.append((start + min(offsets), start + max(offsets)))
        start += length
    return out


@dataclass(frozen=True)
class UncertainWallSpace:
    intervals: tuple[Interval, ...]
    hosts: tuple[str, ...]
    reasons: tuple[str, ...]


def uncertain_wall_space(model: ResolvedModel, room: ResolvedRoom,
                         ring: list) -> UncertainWallSpace:
    """Plate-only roof edges and unresolvable boundary runs, never a height exemption."""
    perimeter = perimeter_length(ring)
    authored = model.plan.by_tag(room.tag)
    ceiling = getattr(authored, "ceiling", None)
    if isinstance(ceiling, FollowRoof) and not any(
        roof.tag == ceiling.roof_ref for roof in model.roofs
    ):
        return UncertainWallSpace(((0.0, perimeter),), (ceiling.roof_ref,),
                                  ("roof-following ceiling geometry is unresolved",))

    required: list[Interval] = []
    uncertain: list[Interval] = []
    hosts: set[str] = set()
    reasons: set[str] = set()
    for wall, interval in bounding_wall_arcs(model, room, ring):
        assembly = model.plan.library.resolve_assembly(wall.assembly)
        framing = [layer.framing for layer in assembly.layers
                   if layer.framing is not None] if assembly else []
        plate_only = bool(framing) and all(spec.wall_frame == "plate" for spec in framing)
        if assembly is None:
            uncertain.append(interval)
            hosts.add(wall.tag)
            reasons.add("boundary assembly is unresolved")
        elif isinstance(ceiling, FollowRoof) and plate_only:
            uncertain.append(interval)
            hosts.add(wall.tag)
            reasons.add("roof-to-floor rafter plate requires an electrical "
                        "wall-space interpretation")
        else:
            required.append(interval)

    # Shared-run touch bands overlap at corners. A plate is uncertain only where no
    # actual wall supports the same boundary; the overlap must not erase gable coverage.
    uncertain = [piece for lo, hi in uncertain for piece in subtract(lo, hi, required)]
    missing = subtract(0.0, perimeter, required + uncertain)
    if missing:
        uncertain.extend(missing)
        reasons.add("room boundary has no resolved wall host")
    return UncertainWallSpace(tuple(merge(uncertain)), tuple(sorted(hosts)),
                              tuple(sorted(reasons)))


def _split_at_seam(lo: float, hi: float, perimeter: float) -> list[Interval]:
    length = hi - lo
    if length <= DISTANCE_TOLERANCE_M:
        return []
    start = lo % perimeter
    end = start + length
    if end <= perimeter:
        return [(start, end)]
    return [(a, b) for a, b in ((start, perimeter), (0.0, end - perimeter))
            if b - a > DISTANCE_TOLERANCE_M]


def uncovered_wall_intervals(perimeter: float, positions: list[float],
                             breaks: list[Interval]) -> list[Interval]:
    """Uncovered wall portions, including endpoint gaps and cyclic coverage.

    Receptacles beyond a break cannot serve the next wall space. Retaining complete
    gaps lets callers intersect alternative interpretations instead of guessing from
    a gap midpoint that might fall on the uncertain side of a corner.
    """
    if perimeter < MIN_WALL_SPACE_M - DISTANCE_TOLERANCE_M:
        return []
    cuts = merged_intervals(breaks, perimeter)
    positions = sorted(position % perimeter for position in positions)
    if not cuts:
        if not positions:
            return [(0.0, perimeter)]
        gaps = []
        for left, right in zip(positions, positions[1:] + [positions[0] + perimeter],
                               strict=True):
            gaps.extend(_split_at_seam(left + MAX_RECEPTACLE_REACH_M,
                                       right - MAX_RECEPTACLE_REACH_M, perimeter))
        return merge(gaps)

    gaps = []
    for index, (_, start) in enumerate(cuts):
        end = cuts[index + 1][0] if index + 1 < len(cuts) else cuts[0][0] + perimeter
        if end - start < MIN_WALL_SPACE_M - DISTANCE_TOLERANCE_M:
            continue
        wrapped = [position + perimeter
                   if position < start - DEVICE_STATION_TOLERANCE_M else position
                   for position in positions]
        coverage = [(position - MAX_RECEPTACLE_REACH_M, position + MAX_RECEPTACLE_REACH_M)
                    for position in wrapped
                    if start - DEVICE_STATION_TOLERANCE_M <= position
                    <= end + DEVICE_STATION_TOLERANCE_M]
        for lo, hi in subtract(start, end, coverage):
            gaps.extend(_split_at_seam(lo, hi, perimeter))
    return merge(gaps)


def definite_coverage_gaps(perimeter: float, positions: list[float],
                           breaks: list[Interval], uncertain: tuple[Interval, ...]
                           ) -> list[Interval]:
    """Known-wall gaps common to both including and excluding uncertain boundaries."""
    included = uncovered_wall_intervals(perimeter, positions, breaks)
    if not uncertain:
        return included
    excluded = uncovered_wall_intervals(perimeter, positions, breaks + list(uncertain))
    common = [(max(a, c), min(b, d)) for a, b in included for c, d in excluded
              if min(b, d) - max(a, c) > DISTANCE_TOLERANCE_M]
    return merge([piece for lo, hi in common for piece in subtract(lo, hi, list(uncertain))])

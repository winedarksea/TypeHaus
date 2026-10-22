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

"""Local opening headers bridge support gaps and seat on real bearing material."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon

from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.intervals import merge, subtract


@dataclass(frozen=True)
class OpeningHeaderSupportRules:
    wall_seat_m: float = inch(1.5).meters


SUPPORT_RULES = OpeningHeaderSupportRules()
_EPS = 1e-9


@dataclass(frozen=True)
class OpeningHeaderRun:
    start_m: float
    end_m: float
    profile: str

    @property
    def width_m(self) -> float:
        return cross_section(self.profile).width_m


def header_blocking_spans(model, coord: float, z0: float, z1: float,
                          axis_i: int, perp_i: int, block_width: float = 0.0):
    """Actual header intervals occupying a blocking station in this floor band."""
    spans = []
    for floor in model.floors:
        for member in floor.members:
            if member.category != "header" or member.z1_m <= z0 or member.z0_m >= z1:
                continue
            ring, _z0, _z1 = member_footprint(member)
            axis = [p[axis_i] for p in ring]
            if max(axis) <= coord - block_width / 2 + _EPS \
                    or min(axis) >= coord + block_width / 2 - _EPS:
                continue
            perps = [p[perp_i] for p in ring]
            spans.append((min(perps), max(perps)))
    return spans


def edge_header_runs(model, opening, carriers, *, across: int, edge: float,
                     sign: float, finished_lo: float, finished_hi: float,
                     setback: float, profile_for_span: Callable[[float], str],
                     rules: OpeningHeaderSupportRules = SUPPORT_RULES
                     ) -> tuple[OpeningHeaderRun, ...]:
    """Subtract axis support; extend each remaining gap only enough to obtain a seat.

    Full support and no support retain their historical framing. Partial support uses
    top-plate footprints, rather than a mitred finish's bounding box, for its seats.
    """
    gaps = subtract(finished_lo, finished_hi, [(c[1], c[2]) for c in carriers])
    if not gaps:
        return ()
    if gaps == [(finished_lo, finished_hi)]:
        lo, hi = finished_lo - setback, finished_hi + setback
        return (OpeningHeaderRun(lo, hi, profile_for_span(hi - lo)),)

    # An island shorter than two seats cannot separate two boards without overlap.
    joined_gaps = []
    for low, high in gaps:
        if joined_gaps and low - joined_gaps[-1][1] < 2 * rules.wall_seat_m - _EPS:
            joined_gaps[-1] = (joined_gaps[-1][0], high)
        else:
            joined_gaps.append((low, high))
    gaps = joined_gaps

    while True:
        runs = [_seated_run(model, opening, carriers, gap, across, edge, sign,
                            finished_lo, finished_hi, setback, profile_for_span, rules)
                for gap in gaps]
        # Two seats sharing a tiny support island must be one board, not intersecting
        # headers. Recompute its section and outer seats after joining those gaps.
        joined = []
        for gap, run in zip(gaps, runs, strict=True):
            if joined and run.start_m < joined[-1][1].end_m - _EPS:
                previous_gap, previous_run = joined.pop()
                joined.append(((previous_gap[0], gap[1]), OpeningHeaderRun(
                    previous_run.start_m, run.end_m, run.profile)))
            else:
                joined.append((gap, run))
        if len(joined) == len(gaps):
            return tuple(runs)
        gaps = [gap for gap, _run in joined]


def _seated_run(model, opening, carriers, gap, across, edge, sign, finished_lo,
                finished_hi, setback, profile_for_span, rules) -> OpeningHeaderRun:
    low, high = gap
    low_terminal = abs(low - finished_lo) < _EPS
    high_terminal = abs(high - finished_hi) < _EPS
    estimated_span = high - low + (setback if low_terminal else rules.wall_seat_m)
    estimated_span += setback if high_terminal else rules.wall_seat_m
    profile = profile_for_span(estimated_span)
    visited = set()
    while profile not in visited:
        visited.add(profile)
        width = cross_section(profile).width_m
        band = sorted((edge, edge + sign * width))
        seats = _bearing_seats(model, opening, carriers, across, *band)
        start = low - setback if low_terminal else _seat_end(
            seats, low, rules.wall_seat_m, at_low_end=True)
        end = high + setback if high_terminal else _seat_end(
            seats, high, rules.wall_seat_m, at_low_end=False)
        sized = profile_for_span(end - start)
        if sized == profile:
            return OpeningHeaderRun(start, end, profile)
        profile = sized
    raise ValueError("local header section and bearing seats do not converge")


def _seat_end(seats, boundary: float, seat: float, *, at_low_end: bool) -> float:
    candidates = []
    for axis_lo, axis_hi, seat_lo, seat_hi in seats:
        if not axis_lo - _EPS <= boundary <= axis_hi + _EPS:
            continue
        end = min(boundary, seat_hi) if at_low_end else max(boundary, seat_lo)
        candidate = end - seat if at_low_end else end + seat
        if seat_lo - _EPS <= candidate <= seat_hi + _EPS:
            candidates.append(candidate)
    if not candidates:
        raise ValueError("partial opening support has no full-width wall seat at "
                         f"{boundary / inch(1).meters:.3f} in")
    return max(candidates) if at_low_end else min(candidates)


def _bearing_seats(model, opening, carriers, across, band_lo, band_hi):
    from typehaus.resolve.floors import _bearing_axis

    along = 1 - across
    seats = []
    for tag in opening.bearing_refs:
        axis = _bearing_axis(model, tag)
        if axis is None or abs(axis[0][across] - axis[1][across]) > _EPS:
            continue
        lo, hi = sorted((axis[0][along], axis[1][along]))
        if not any(abs(c[0] - axis[0][across]) < _EPS
                   and abs(c[1] - lo) < _EPS and abs(c[2] - hi) < _EPS for c in carriers):
            continue
        wall = model.wall(tag)
        if wall is not None:
            top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
            plates = [member for member in wall.members
                      if member.category == "plate" and abs(member.z1_m - top) < _EPS]
            polygons = [Polygon(member_footprint(member)[0]) for member in plates]
            if not plates and not wall.members:
                polygons = [Polygon(layer.polygon) for layer in wall.depth_layers()
                            if layer.function == LayerFunction.STRUCTURE.value]
        else:
            polygons = [Polygon(solid.outline) for solid in model.solids if solid.tag == tag]
        for polygon in polygons:
            for start, end in _full_width_spans(polygon, across, band_lo, band_hi):
                seats.append((lo, hi, start, end))
    return seats


def _full_width_spans(polygon: Polygon, across: int, band_lo: float,
                      band_hi: float) -> list[tuple[float, float]]:
    """Intersection of both sides of a rectangular header seat with its bearing body."""
    along = 1 - across
    bounds = polygon.bounds
    low, high = bounds[along], bounds[along + 2]
    spans = [(low, high)]
    for offset in (band_lo, band_hi):
        a, b = ((offset, low), (offset, high)) if across == 0 else (
            (low, offset), (high, offset))
        intersection = polygon.intersection(LineString((a, b)))
        covered = []
        for part in getattr(intersection, "geoms", (intersection,)):
            if part.geom_type != "LineString" or part.is_empty:
                continue
            coordinates = [point[along] for point in part.coords]
            covered.append((min(coordinates), max(coordinates)))
        spans = [(max(a0, b0), min(a1, b1)) for a0, a1 in spans for b0, b1 in covered
                 if min(a1, b1) > max(a0, b0) + _EPS]
    return merge(spans)

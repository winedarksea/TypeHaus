"""Complete girt support after opening packs move blocks off their usual stud grid."""

from collections.abc import Callable, Iterable

_SPACING_TOLERANCE_M = 1e-9


def complete_support_stations(stations: Iterable[float], *, spacing: float, face: float,
                              verticals: tuple[tuple[float, float, float], ...],
                              z0: float, bounds: tuple[float, float],
                              in_void: Callable[[float], bool]) -> list[float]:
    """Add an actual stud anchor only where snapping stretched a bay past its limit.

    Doubled opening packs can move two neighboring module blocks away from each
    other. The additional block must land on real framing, clear of the opening.
    """
    stations = sorted(set(stations))
    half = face / 2
    limit = spacing + face
    index = 0
    while index + 1 < len(stations):
        low, high = stations[index:index+2]
        if high - low <= limit + _SPACING_TOLERANCE_M:
            index += 1
            continue
        candidates = [center for center, bottom, top in verticals
                      if bottom < z0 + face and top > z0
                      and low + face <= center <= high - face
                      and bounds[0] + half <= center <= bounds[1] - half
                      and not in_void(center)]
        if not candidates:
            index += 1  # The structural support check reports a gap with no valid anchor.
            continue
        center = min(candidates, key=lambda center: abs(center - (low + high)/2))
        stations.insert(index + 1, center)
    return stations


def land_free_ends(stations: list[float], *, reach: float, face: float, lap: float,
                   verticals: tuple[tuple[float, float, float], ...], z0: float,
                   bounds: tuple[float, float], free: tuple[bool, bool],
                   in_void: Callable[[float], bool]) -> list[float]:
    """Move a free course end's block inward onto the nearest stud when it laps none.

    A course cut by a rake starts wherever the rake crosses it, so its end block can land
    between studs (decision #109 moved every catlin gable's by 2"). The girt end then
    cantilevers past the block; a block already on that stud absorbs it.
    """
    half = face / 2
    out = sorted(stations)
    for end, sign in ((0, 1.0), (-1, -1.0)):
        if not out or not free[end]:
            continue
        station = out[end]
        if abs(station - (bounds[end] + sign * half)) > _SPACING_TOLERANCE_M:
            continue
        at_height = [c for c, bottom, top in verticals if bottom < z0 + face and top > z0]
        if any(abs(c - station) <= half - lap + 1e-6 for c in at_height):
            continue
        inward = [c for c in at_height
                  if 0 < sign * (c - station) <= reach
                  and bounds[0] + half <= c <= bounds[1] - half and not in_void(c)]
        if not inward:
            continue
        target = min(inward, key=lambda c: abs(c - station))
        out.pop(end)
        if not any(abs(s - target) < face for s in out):
            out.append(target)
        out.sort()
    return out

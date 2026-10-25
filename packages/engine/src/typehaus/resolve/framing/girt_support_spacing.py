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
